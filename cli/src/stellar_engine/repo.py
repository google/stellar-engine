# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Reads deployment facts from the Stellar Engine repository.

The CLI never duplicates lists that already live in the repository, such as
the roles granted by `setIAM.sh` or the APIs enabled by `enableServices.sh`.
This module parses those files so that the CLI and the manual flow in
`docs/ddg.md` always agree.
"""

import dataclasses
import enum
import functools
import json
import pathlib
import re

import hcl2
from packaging import version
import yaml

from stellar_engine import naming
from stellar_engine import paths
from stellar_engine.render import hcl

_SERVICES_RE = re.compile(r'^list_of_services="([^"]+)"', re.MULTILINE)
_PREFIX_LIMIT_RE = re.compile(r"length\(var\.prefix\),\s*0\)\s*<=\s*(\d+)")
_TENANT_KEY_LIMIT_RE = re.compile(r"length\(k\)\s*(<=?)\s*(\d+)")
# An object type attribute with a string default, such as a field of the
# Stage 0 `groups` or `project_deletion_policies` type.
_OPTIONAL_DEFAULT_RE = re.compile(
    r'([\w-]+)\s*=\s*optional\(string,\s*"([^"]+)"\)'
)
# python-hcl2 returns a conditional such as `cond ? {} : { ... }` as one
# expression string, so the map literal in its else branch is parsed again.
_CONDITIONAL_MAP_RE = re.compile(
    r"^\$\{.*?\?\s*\{\}\s*:\s*(\{.*\})\}$", re.DOTALL
)
_HOLDER_KEY_RE = re.compile(
    r"^(?:\$\{\(local\.principals\.(?P<group>[\w-]+)\)\}"
    r"|\$\{\(module\.(?P<module>[\w-]+)\.iam_email\)\}"
    r"|(?P<user>user):\$\{var\.bootstrap_user\}"
    r"|(?P<domain>domain):\$\{var\.organization\.domain\})$"
)
_VERSION_FLOOR_RE = re.compile(r">=\s*([0-9.]+)")
# `local._org_policies_raw` in `0-bootstrap/organization.tf` decodes every
# `*_policy.yaml` file of the plain directory with `yamldecode`, and renders
# the files of the templated directory with `templatefile` first.
_ORG_POLICY_DIR = "data/org-policies"
_TEMPLATED_ORG_POLICY_DIR = "data/custom-org-policies"
_ORG_POLICY_GLOB = "*_policy.yaml"
# A top-level key of a templated policy file. Template directives such as
# `%{ if ... ~}` and indented rules never match.
_TEMPLATED_KEY_RE = re.compile(r"^([A-Za-z0-9_.]+):")
# A template directive on its own line, such as `%{ if ... ~}`.
_DIRECTIVE_RE = re.compile(
    r"^\s*%\{~?\s*(?P<keyword>if|else|endif|for|endfor)\b(?P<rest>.*?)~?\}"
)
# The regime condition of the templated policy files, such as
# `!contains(["FEDRAMP_MODERATE"], regime)`.
_REGIME_CONDITION_RE = re.compile(
    r"^\s*(?P<negated>!?)\s*contains\(\s*\[(?P<regimes>[^\]]*)\]\s*,"
    r"\s*regime\s*\)\s*$"
)
# Constraints that `data/custom-constraint-policies` defines.
CUSTOM_CONSTRAINT_PREFIX = "custom."
# Stage 0 writes `local.tfvars` to `0-bootstrap.auto.tfvars.json` and
# `local.tfvars_globals` to `0-globals.auto.tfvars.json` in
# `outputs-files.tf`; `fast/stage-links.sh` links both into Stage 1. Stage 0
# reads no output files.
_AUTO_TFVARS_LOCALS = {
    paths.BOOTSTRAP: (),
    paths.RESMAN: ("tfvars", "tfvars_globals"),
}


# `module "billing-export-project"` in `0-bootstrap/billing.tf` has
# `count = local.billing_mode == "org" ? 1 : 0`.
BILLING_EXPORT_MODULE = "billing-export-project"
_PROJECT_MODULE_SOURCE = "modules/project"
# The Stage 0 file and module label of each project that Stage 0 creates.
_STAGE0_PROJECT_MODULES = (
    ("automation.tf", "automation-project"),
    ("log-export.tf", "log-export-project"),
    ("billing.tf", BILLING_EXPORT_MODULE),
)
# The Stage 0 file and resource type of the Assured Workloads workload,
# which the API only creates for a caller that can use the billing account.
_WORKLOAD_FILE = "organization.tf"
WORKLOAD_RESOURCE = "google_assured_workloads_workload"
# The workload `count` expression skips one regime, such as
# `var.assured_workloads.regime != "COMPLIANCE_REGIME_UNSPECIFIED" ? 1 : 0`.
_WORKLOAD_COUNT_RE = re.compile(
    r'var\.assured_workloads\.regime\s*!=\s*\\?"(?P<regime>[A-Z0-9_]+)\\?"'
)
# Workload arguments that the Assured Workloads API never returns, so an
# imported workload reads them as unset. The provider marks them ForceNew and
# its import tests ignore them, so an import plans a replacement unless the
# workload `lifecycle.ignore_changes` lists each one that Stage 0 sets.
WORKLOAD_INPUT_ONLY = (
    "billing_account",
    "provisioned_resources_parent",
    "resource_settings",
)
# The Stage 0 module that creates a budget on the billing account when the
# `billing_budget_amount` variable is set.
BUDGET_MODULE = "billing-account-budget"
# Newer Stage 0 versions declare this object variable and pass one of its
# keys to the `deletion_policy` of each project module.
PROJECT_DELETION_POLICIES = "project_deletion_policies"
_DELETION_POLICY_REF_RE = re.compile(
    rf"^\$\{{var\.{PROJECT_DELETION_POLICIES}\.(?P<key>[A-Za-z_][\w-]*)\}}$"
)


class RepoError(Exception):
    """Raised when the repository layout does not match expectations."""


@dataclasses.dataclass(frozen=True)
class Stage0Project:
    """A project that a Stage 0 `modules/project` call creates.

    Attributes:
        module: Module label, such as `automation-project`.
        name: Project name, the ID suffix after `<prefix>-prod-`.
        address: Address of the module's `google_project` resource, which
            an import block adopts.
        count: The module `count` expression, or None when it has none.
    """

    module: str
    name: str
    address: str
    count: str | None = None


# The billing answers for which Stage 0 creates the billing export project,
# as `billing_export_created` reads them, for messages about the rule.
BILLING_EXPORT_CONDITION = (
    "billing.no_iam is false and billing.is_org_level is true"
)


def billing_export_created(*, no_iam: bool, is_org_level: bool) -> bool:
    """Returns whether Stage 0 creates the billing export project.

    Mirrors `local.billing_mode` in `0-bootstrap/billing.tf`, which is "org"
    only when Stage 0 manages billing IAM on an organization-level account.

    Args:
        no_iam: The `billing_account.no_iam` value.
        is_org_level: The `billing_account.is_org_level` value.
    """
    return not no_iam and is_org_level


def billing_iam_on_account(*, no_iam: bool, is_org_level: bool) -> bool:
    """Returns whether Stage 0 grants roles on the billing account itself.

    Mirrors `local.billing_mode == "resource"` in `0-bootstrap/billing.tf`,
    whose `google_billing_account_iam_member` resources need Billing Account
    Administrator whatever resources exist already.

    Args:
        no_iam: The `billing_account.no_iam` value.
        is_org_level: The `billing_account.is_org_level` value.
    """
    return not no_iam and not is_org_level


def _sets_argument(value) -> bool:
    """Returns whether an HCL argument sets a value other than empty.

    An empty string reads back as unset, so it never forces a new resource.
    """
    if value is None or value == []:
        return False
    return not (isinstance(value, str) and hcl.unquote(value) == "")


def stage0_project_created(
    project: Stage0Project, *, no_iam: bool, is_org_level: bool
) -> bool:
    """Returns whether Stage 0 creates a project for these billing answers.

    Args:
        project: A Stage 0 project from `Repo.stage0_projects`.
        no_iam: The `billing_account.no_iam` value.
        is_org_level: The `billing_account.is_org_level` value.
    """
    if project.module == BILLING_EXPORT_MODULE:
        return billing_export_created(no_iam=no_iam, is_org_level=is_org_level)
    return True


@dataclasses.dataclass(frozen=True)
class AssuredWorkload:
    """The Assured Workloads workload that Stage 0 creates.

    Attributes:
        address: Address of the workload resource, which an import block
            adopts, such as `google_assured_workloads_workload.primary[0]`.
        skipped_regime: The regime for which the resource `count` is 0,
            or None when the resource has no `count`.
        replaced_on_import: Input-only arguments that Stage 0 sets without
            listing them in `lifecycle.ignore_changes`, so an import of a
            pre-created workload plans a replacement.
    """

    address: str
    skipped_regime: str | None = None
    replaced_on_import: tuple[str, ...] = ()

    def created(self, regime: str) -> bool:
        """Returns whether Stage 0 creates the workload for a regime.

        Args:
            regime: Assured Workloads regime, such as `IL5`.
        """
        return regime != self.skipped_regime


class BillingResourceKind(enum.StrEnum):
    """Kinds of Stage 0 resource that need billing access at creation."""

    PROJECT = "project"
    WORKLOAD = "Assured Workloads workload"


@dataclasses.dataclass(frozen=True)
class BillingResource:
    """A Stage 0 resource whose creation needs access to the billing account.

    A deployer without that access needs someone who has it to create the
    resource first, so Stage 0 imports it instead.

    Attributes:
        kind: Kind of resource.
        address: Address of the resource, the key of its entry in
            `imports.0-bootstrap`.
        name: Project ID, or the display name of the workload.
        create: What to create, as a sentence fragment that names the
            attributes the import must match.
        import_id: The import ID of the entry, with a placeholder for a
            part that only exists after creation.
    """

    kind: BillingResourceKind
    address: str
    name: str
    create: str
    import_id: str


@dataclasses.dataclass(frozen=True)
class OrgPolicyScan:
    """Organization policies sorted by whether Stage 0 imports them.

    Attributes:
        kept: Policies that Stage 0 declares and imports on its final
            apply.
        custom: Policies of custom constraints, which Stage 0 never
            imports.
        undeclared: Policies that Stage 0 does not manage.
    """

    kept: tuple[str, ...]
    custom: tuple[str, ...]
    undeclared: tuple[str, ...]


def _templated_keys(text, regime):
    """Returns the top-level keys of a templated policy file for a regime.

    Args:
        text: Content of a `data/custom-org-policies` file.
        regime: Regime that `templatefile` renders the file for, or None to
            keep the keys of every regime.

    Returns:
        The set of top-level keys that the rendered file contains.
    """
    keys = set()
    # One entry per open directive: True or False when the regime decides
    # the branch, None when it does not.
    stack = []
    for line in text.splitlines():
        directive = _DIRECTIVE_RE.match(line)
        if directive is None:
            key = _TEMPLATED_KEY_RE.match(line)
            if key and False not in stack:
                keys.add(key.group(1))
            continue
        keyword = directive.group("keyword")
        if keyword == "if":
            stack.append(_regime_branch(directive.group("rest"), regime))
        elif keyword == "for":
            stack.append(None)
        elif keyword == "else" and stack and stack[-1] is not None:
            stack[-1] = not stack[-1]
        elif keyword in ("endif", "endfor") and stack:
            stack.pop()
    return keys


def _regime_branch(condition, regime):
    """Returns whether a template condition holds for a regime, or None."""
    match = _REGIME_CONDITION_RE.match(condition)
    if regime is None or match is None:
        return None
    regimes = set(re.findall(r'"([^"]*)"', match.group("regimes")))
    return (regime in regimes) != bool(match.group("negated"))


def _counted(body):
    return "" if body.get("count") is None else "[0]"


class HolderKind(enum.StrEnum):
    """Kinds of principal that Stage 0 binds to organization roles."""

    GROUP = "group"
    SERVICE_ACCOUNT = "serviceAccount"
    BOOTSTRAP_USER = "bootstrapUser"
    DOMAIN = "domain"


@dataclasses.dataclass(frozen=True)
class Holder:
    """A principal that Stage 0 binds to an organization role.

    Attributes:
        kind: Kind of principal.
        key: Group key such as `gcp-devops`, or service account name such as
            `bootstrap-0`. None for the bootstrap user and the domain.
    """

    kind: HolderKind
    key: str | None = None


def _load_hcl(path):
    with path.open(encoding="utf-8") as handle:
        return hcl2.load(handle)


def _locals(path):
    """Returns the locals that an HCL file declares, merged across blocks.

    Args:
        path: Path of a Terraform file.

    Returns:
        Local name to its value, as python-hcl2 returns it.
    """
    values = {}
    for block in _load_hcl(path).get("locals", []):
        values.update(block)
    return values


def _resources(path, resource_type):
    """Returns the resources of one type that an HCL file declares.

    Args:
        path: Path of a Terraform file.
        resource_type: Resource type, such as `google_project`.

    Returns:
        A list of the unquoted resource name and its parsed body, in file
        order.
    """
    return [
        (hcl.unquote(name), body)
        for block in _load_hcl(path).get("resource", [])
        for kind, bodies in block.items()
        if hcl.unquote(kind) == resource_type
        for name, body in bodies.items()
    ]


def _modules(path):
    """Returns the module calls that an HCL file declares.

    Args:
        path: Path of a Terraform file.

    Returns:
        A list of the unquoted module label and its parsed body, in file
        order.
    """
    return [
        (hcl.unquote(label), body)
        for block in _load_hcl(path).get("module", [])
        for label, body in block.items()
    ]


def _variables(path):
    """Returns the variables that an HCL file declares.

    Args:
        path: Path of a Terraform file.

    Returns:
        The unquoted variable name to its parsed body.
    """
    return {
        hcl.unquote(name): body
        for block in _load_hcl(path).get("variable", [])
        for name, body in block.items()
    }


@functools.cache
def _stage_variables(root, stage):
    return _variables(paths.stage_dir(root, stage) / "variables.tf")


def _literal_map(value, name):
    """Returns a parsed HCL map, unwrapping a `cond ? {} : {...}` value.

    Raises:
        RepoError: If the value is neither a map nor that conditional.
    """
    if isinstance(value, dict):
        return value
    match = _CONDITIONAL_MAP_RE.match(value) if isinstance(value, str) else None
    if not match:
        raise RepoError(f"Cannot read local.{name} as a map")
    return hcl2.loads(f"value = {match.group(1)}")["value"]


def find_root(start=None):
    """Finds the Stellar Engine repository root.

    Args:
        start: Directory to start searching from. Defaults to the current
            working directory, then the location of this package.

    Returns:
        The repository root path.

    Raises:
        RepoError: If no directory containing `fast/stages-aw` is found.
    """
    candidates = [pathlib.Path(start) if start else pathlib.Path.cwd()]
    candidates.append(pathlib.Path(__file__).resolve())
    for candidate in candidates:
        for directory in [candidate, *candidate.parents]:
            if (directory / paths.STAGES_DIR).is_dir():
                return directory
    raise RepoError(
        "Cannot find the Stellar Engine repository root. Run the command "
        "from inside a checkout or pass --repo."
    )


@dataclasses.dataclass(frozen=True)
class Repo:
    """Read-only view of the deployment facts stored in the repository.

    Attributes:
        root: Path of the repository root.
    """

    root: pathlib.Path

    @property
    def bootstrap_dir(self):
        """Returns the Stage 0 bootstrap directory."""
        return paths.stage_dir(self.root, paths.BOOTSTRAP)

    @property
    def _bootstrap_variables(self):
        return self.stage_variables(paths.BOOTSTRAP)

    def stage_variables(self, stage):
        """Returns the variable blocks a stage declares in `variables.tf`.

        Args:
            stage: Stage directory name, such as `1-resman`.

        Returns:
            Variable name to its parsed block body, as python-hcl2 returns
            it.
        """
        return _stage_variables(self.root, stage)

    def stage_variable_names(self, stage):
        """Returns the names of the variables a stage declares.

        Args:
            stage: Stage directory name, such as `1-resman`.
        """
        return frozenset(self.stage_variables(stage))

    def required_roles(self):
        """Returns the organization roles that `setIAM.sh` grants.

        Returns:
            Role names in file order, for example `roles/owner`.
        """
        path = self.bootstrap_dir / "setIAM.yaml.sample"
        policy = json.loads(path.read_text(encoding="utf-8"))
        return [binding["role"] for binding in policy["bindings"]]

    def required_apis(self):
        """Returns the APIs that `enableServices.sh` enables.

        Returns:
            Fully qualified service names such as `iam.googleapis.com`.

        Raises:
            RepoError: If the service list cannot be found in the script.
        """
        script = (self.bootstrap_dir / "enableServices.sh").read_text(
            encoding="utf-8"
        )
        match = _SERVICES_RE.search(script)
        if not match:
            raise RepoError("Cannot find list_of_services in enableServices.sh")
        return [f"{name}.googleapis.com" for name in match.group(1).split()]

    def prefix_max_length(self):
        """Returns the prefix length limit from the Stage 0 validation block.

        Raises:
            RepoError: If the validation block cannot be found.
        """
        text = (self.bootstrap_dir / "variables.tf").read_text(encoding="utf-8")
        match = _PREFIX_LIMIT_RE.search(text)
        if not match:
            raise RepoError("Cannot find the prefix length validation")
        return int(match.group(1))

    def tenant_key_max_length(self):
        """Returns the tenant key length limit from the Stage 1 validation.

        The `tenants` variable in `1-resman/variables.tf` writes the limit
        as `length(k) < 7`, so the strict bound is converted to the longest
        allowed key length.

        Raises:
            RepoError: If the validation block cannot be found.
        """
        text = (
            paths.stage_dir(self.root, paths.RESMAN) / "variables.tf"
        ).read_text(encoding="utf-8")
        match = _TENANT_KEY_LIMIT_RE.search(text)
        if not match:
            raise RepoError("Cannot find the tenant key length validation")
        limit = int(match.group(2))
        return limit if match.group(1) == "<=" else limit - 1

    def default_groups(self):
        """Returns the default group names from the Stage 0 `groups` type.

        Returns:
            A mapping of group key to group name, for example
            `{"gcp-support": "gcp-devops"}`.
        """
        group_type = self._bootstrap_variables["groups"]["type"]
        return dict(_OPTIONAL_DEFAULT_RE.findall(group_type))

    def regime_names(self):
        """Returns the compliance regimes in the Stage 0 `regime_mapping`."""
        default = self._bootstrap_variables["regime_mapping"].get("default", {})
        return sorted(hcl.unquote(name) for name in default)

    def log_sink_names(self):
        """Returns the default organization log sink names."""
        default = self._bootstrap_variables["log_sinks"].get("default", {})
        return sorted(hcl.unquote(name) for name in default)

    def custom_role_ids(self):
        """Returns the organization custom role IDs that Stage 0 creates.

        A role file without a `name` key falls back to its file name, which
        matches how the organization module names it.
        """
        role_ids = []
        for path in sorted(
            (self.bootstrap_dir / "data/custom-roles").glob("*.yaml")
        ):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            role_ids.append(data.get("name") or path.stem)
        return role_ids

    def custom_constraint_names(self):
        """Returns the organization custom constraint names Stage 0 creates."""
        names = []
        directory = self.bootstrap_dir / "data/custom-constraint-policies"
        for path in sorted(directory.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            names.extend(data)
        return names

    def declared_org_policies(self, regime=None):
        """Returns the constraints of the organization policies Stage 0 sets.

        The names are the top-level keys of the `*_policy.yaml` files in
        `data/org-policies` and `data/custom-org-policies`, the files that
        `local._org_policies_raw` in `organization.tf` loads. A templated
        file can omit a key for some regimes through a
        `contains([...], regime)` condition, so pass the regime to drop
        those keys the way `templatefile` does. A key behind any other
        condition counts for every regime.

        Args:
            regime: Assured Workloads regime, such as `FEDRAMP_MODERATE`.
                None returns the keys of every regime.

        Returns:
            Sorted unique constraint names, such as
            `iam.allowedPolicyMemberDomains`.
        """
        names = set()
        for path in sorted(
            (self.bootstrap_dir / _ORG_POLICY_DIR).glob(_ORG_POLICY_GLOB)
        ):
            names.update(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        for path in sorted(
            (self.bootstrap_dir / _TEMPLATED_ORG_POLICY_DIR).glob(
                _ORG_POLICY_GLOB
            )
        ):
            names.update(
                _templated_keys(path.read_text(encoding="utf-8"), regime)
            )
        return sorted(names)

    def scan_org_policies(self, existing, regime=None):
        """Sorts existing organization policies by whether Stage 0 imports them.

        These are the rules of `0-bootstrap/import.sh`. Stage 0 imports
        each existing policy that it declares, so its final apply adopts
        the policy instead of failing to create it. A policy of a custom
        constraint that Stage 0 declares is skipped, because Stage 0
        creates that constraint in the same apply, and preflight reports a
        custom constraint that already exists. Any other policy, custom or
        not, is undeclared.

        Args:
            existing: Constraint names of the policies set on the
                organization.
            regime: Assured Workloads regime whose templated policies
                count as declared. None counts the policies of every
                regime.

        Returns:
            An `OrgPolicyScan` with sorted unique names.
        """
        declared = set(self.declared_org_policies(regime))
        kept, custom, undeclared = set(), set(), set()
        for name in existing:
            if name not in declared:
                undeclared.add(name)
            elif name.startswith(CUSTOM_CONSTRAINT_PREFIX):
                custom.add(name)
            else:
                kept.add(name)
        return OrgPolicyScan(
            tuple(sorted(kept)),
            tuple(sorted(custom)),
            tuple(sorted(undeclared)),
        )

    def _module_names(self, filename):
        """Maps each module in a Stage 0 file to its `name` argument."""
        return {
            label: hcl.unquote(body["name"])
            for label, body in _modules(self.bootstrap_dir / filename)
            if "name" in body
        }

    def automation_service_accounts(self):
        """Maps Stage 0 automation service account modules to their names.

        Returns:
            For example `{"automation-tf-bootstrap-sa": "bootstrap-0"}`. The
            account email is `<prefix>-prod-<name>@<prefix>-prod-iac-core-0`.
        """
        return {
            module: name
            for module, name in self._module_names("automation.tf").items()
            if module.endswith("-sa")
        }

    def stage0_project_names(self):
        """Returns the names of the projects Stage 0 can create.

        The project ID is `<prefix>-prod-<name>`. The billing export project
        is included even though Stage 0 only creates it for some billing
        answers; see `stage0_project_created`.
        """
        return [project.name for project in self.stage0_projects()]

    def stage0_projects(self):
        """Returns the projects Stage 0 can create, with their addresses.

        Each address comes from the stage code: the `modules/project` call
        in `0-bootstrap` whose `name` is a Stage 0 project name, indexed
        `[0]` when the module or the module's `google_project` resource has
        a `count`.

        Returns:
            A tuple of `Stage0Project`: the automation, log export and
            billing export projects, in that order.

        Raises:
            RepoError: If a Stage 0 project has no project module.
        """
        return self._stage0_projects

    def created_stage0_projects(self, *, no_iam: bool, is_org_level: bool):
        """Returns the projects Stage 0 creates for these billing answers.

        Args:
            no_iam: The `billing_account.no_iam` value.
            is_org_level: The `billing_account.is_org_level` value.

        Returns:
            A list of `Stage0Project`, in `stage0_projects` order.

        Raises:
            RepoError: If a Stage 0 project has no project module.
        """
        return [
            project
            for project in self.stage0_projects()
            if stage0_project_created(
                project, no_iam=no_iam, is_org_level=is_org_level
            )
        ]

    @functools.cached_property
    def _assured_workload(self):
        found = _resources(
            self.bootstrap_dir / _WORKLOAD_FILE, WORKLOAD_RESOURCE
        )
        if len(found) != 1:
            raise RepoError(
                f"Expected one {WORKLOAD_RESOURCE} in 0-bootstrap/"
                f"{_WORKLOAD_FILE}, found {len(found)}"
            )
        name, body = found[0]
        count = body.get("count")
        skipped = None
        if count is not None:
            match = _WORKLOAD_COUNT_RE.search(str(count))
            if match is None:
                raise RepoError(f"Cannot read the count of {WORKLOAD_RESOURCE}")
            skipped = match.group("regime")
        ignored = {
            hcl.unquote(str(field))
            for lifecycle in body.get("lifecycle", [])
            for field in lifecycle.get("ignore_changes", [])
        }
        replaced = tuple(
            field
            for field in WORKLOAD_INPUT_ONLY
            if _sets_argument(body.get(field)) and field not in ignored
        )
        return AssuredWorkload(
            address=f"{WORKLOAD_RESOURCE}.{name}{_counted(body)}",
            skipped_regime=skipped,
            replaced_on_import=replaced,
        )

    def assured_workload(self):
        """Returns the Assured Workloads workload that Stage 0 creates.

        Returns:
            An `AssuredWorkload` read from the single
            `google_assured_workloads_workload` resource in
            `0-bootstrap/organization.tf`.

        Raises:
            RepoError: If the file declares no such resource or more than
                one, or its `count` does not compare the regime.
        """
        return self._assured_workload

    def billing_resources(
        self,
        *,
        prefix: str,
        regime: str,
        location: str,
        no_iam: bool,
        is_org_level: bool,
        org_id: str | None = None,
    ):
        """Returns the Stage 0 resources that need billing access to create.

        Each Stage 0 project links to the billing account, and the Assured
        Workloads API only creates a workload for a caller that can use the
        billing account. A deployer without that access needs someone who
        has it to create these resources, and Stage 0 imports them.

        Args:
            prefix: Deployment prefix.
            regime: Assured Workloads regime, such as `IL5`.
            location: Assured Workloads location, such as `us-east4`.
            no_iam: The `billing_account.no_iam` value.
            is_org_level: The `billing_account.is_org_level` value.
            org_id: Numeric organization ID for the workload import ID, or
                None for a placeholder.

        Returns:
            A list of `BillingResource`: the Stage 0 projects that these
            billing answers create, in `stage0_projects` order, then the
            workload unless the regime skips it.

        Raises:
            RepoError: If the stage code does not match expectations.
        """
        resources = []
        for project in self.created_stage0_projects(
            no_iam=no_iam, is_org_level=is_org_level
        ):
            project_id = naming.stage0_project_id(prefix, project.name)
            resources.append(
                BillingResource(
                    kind=BillingResourceKind.PROJECT,
                    address=project.address,
                    name=project_id,
                    create=(
                        f"project {project_id} linked to the billing account"
                    ),
                    import_id=project_id,
                )
            )
        workload = self.assured_workload()
        if workload.created(regime):
            name = naming.workload_folder_name(prefix)
            org = org_id or "<org_id>"
            resources.append(
                BillingResource(
                    kind=BillingResourceKind.WORKLOAD,
                    address=workload.address,
                    name=name,
                    create=(
                        f"{regime} workload {name} in {location} with the "
                        "billing account, violation notifications enabled, "
                        f"and a consumer folder named {name}"
                    ),
                    import_id=(
                        f"organizations/{org}/locations/{location}/"
                        "workloads/<workload_id>"
                    ),
                )
            )
        return resources

    def project_deletion_policy_keys(self):
        """Maps each Stage 0 project module to its deletion policy key.

        A Stage 0 version that declares the `project_deletion_policies`
        variable passes `var.project_deletion_policies.<key>` as the
        `deletion_policy` of each project module. Older versions declare no
        such variable, so the CLI cannot keep a project on destroy there.

        Returns:
            Module label to variable key, such as
            `{"automation-project": "automation"}`, empty when Stage 0 does
            not declare the variable.

        Raises:
            RepoError: If a Stage 0 project has no project module.
        """
        if PROJECT_DELETION_POLICIES not in self.stage_variable_names(
            paths.BOOTSTRAP
        ):
            return {}
        keys = {}
        for module, body in self._stage0_module_bodies.items():
            match = _DELETION_POLICY_REF_RE.match(
                str(body.get("deletion_policy", ""))
            )
            if match:
                keys[module] = match.group("key")
        return keys

    def stage0_deletion_policies(self):
        """Returns the deletion policy of each Stage 0 project by default.

        This is the policy without a tfvars value: the default of the
        `project_deletion_policies` key that the module reads, a literal
        `deletion_policy` of the module, or else the `deletion_policy`
        default of `modules/project`. Terraform also uses the module default
        for a key without a default, because that variable is not nullable.

        Returns:
            Module label to policy, such as `{"automation-project":
            "DELETE"}`, in `stage0_projects` order.

        Raises:
            RepoError: If a Stage 0 project has no project module, or
                `modules/project` declares no `deletion_policy` default.
        """
        keys = self.project_deletion_policy_keys()
        key_defaults = {}
        if keys:
            variable = self.stage_variables(paths.BOOTSTRAP)[
                PROJECT_DELETION_POLICIES
            ]
            key_defaults = dict(
                _OPTIONAL_DEFAULT_RE.findall(str(variable.get("type", "")))
            )
        policies = {}
        for module, body in self._stage0_module_bodies.items():
            literal = hcl.unquote(body.get("deletion_policy"))
            if module in keys:
                policy = key_defaults.get(keys[module])
            elif isinstance(literal, str) and "${" not in literal:
                policy = literal
            else:
                policy = None
            policies[module] = policy or self._project_module_deletion_policy
        return policies

    @functools.cached_property
    def _project_module_deletion_policy(self):
        variables = _variables(self.root / "modules/project/variables.tf")
        default = hcl.unquote(
            variables.get("deletion_policy", {}).get("default")
        )
        if isinstance(default, str):
            return default
        raise RepoError("modules/project declares no deletion_policy default")

    @functools.cached_property
    def _stage0_module_bodies(self):
        """Maps each Stage 0 project module label to its parsed body.

        Raises:
            RepoError: If a Stage 0 project has no project module.
        """
        bodies = {}
        for filename, module in _STAGE0_PROJECT_MODULES:
            body = dict(_modules(self.bootstrap_dir / filename)).get(module)
            source = hcl.unquote(body.get("source", "")) if body else ""
            if body is None or not str(source).endswith(_PROJECT_MODULE_SOURCE):
                raise RepoError(f"No Stage 0 project module {module}")
            bodies[module] = body
        return bodies

    @functools.cached_property
    def _stage0_projects(self):
        resource_index = ""
        for name, body in _resources(
            self.root / "modules/project/main.tf", "google_project"
        ):
            if name == "project":
                resource_index = _counted(body)
        projects = []
        for module, body in self._stage0_module_bodies.items():
            count = body.get("count")
            projects.append(
                Stage0Project(
                    module=module,
                    name=hcl.unquote(body["name"]),
                    address=(
                        f"module.{module}{_counted(body)}."
                        f"google_project.project{resource_index}"
                    ),
                    count=None if count is None else str(count),
                )
            )
        return tuple(projects)

    def authoritative_bindings(self):
        """Returns the principals Stage 0 keeps on each authoritative role.

        Stage 0 removes every other principal from these roles on its first
        apply, as defined in `organization-iam.tf`. Roles in
        `iam_delete_roles` keep no principal at all.

        Returns:
            A dict of role to a set of `Holder` values.

        Raises:
            RepoError: If a binding refers to an unknown principal or service
                account, or a binding local is not a map.
        """
        local_values = _locals(self.bootstrap_dir / "organization-iam.tf")
        accounts = self.automation_service_accounts()
        bindings = {}
        for name, value in local_values.items():
            if not name.endswith("_bindings"):
                continue
            for key, body in _literal_map(value, name).items():
                holder = self._holder(hcl.unquote(key), accounts)
                roles = body.get("authoritative", [])
                if not isinstance(roles, list):
                    raise RepoError(f"Cannot read the roles of {key}")
                for role in roles:
                    bindings.setdefault(hcl.unquote(role), set()).add(holder)
        for role in local_values.get("iam_delete_roles", []):
            bindings[hcl.unquote(role)] = set()
        return bindings

    @staticmethod
    def _holder(key, accounts):
        """Returns the Holder for an `organization-iam.tf` binding key."""
        match = _HOLDER_KEY_RE.match(key)
        if not match:
            raise RepoError(f"Unknown principal {key}")
        if match.group("group"):
            return Holder(HolderKind.GROUP, match.group("group"))
        if match.group("module"):
            module = match.group("module")
            if module not in accounts:
                raise RepoError(f"Unknown service account {module}")
            return Holder(HolderKind.SERVICE_ACCOUNT, accounts[module])
        if match.group("user"):
            return Holder(HolderKind.BOOTSTRAP_USER)
        return Holder(HolderKind.DOMAIN)

    def authoritative_org_roles(self):
        """Returns organization roles that Stage 0 manages authoritatively."""
        return sorted(self.authoritative_bindings())

    def auto_tfvars_keys(self, stage):
        """Returns the variables a stage receives from `*.auto.tfvars.json`.

        Terraform loads `*.auto.tfvars.json` files after `terraform.tfvars`,
        so these keys override anything the rendered tfvars sets. They are
        the keys of the Stage 0 locals that `outputs-files.tf` writes.

        Args:
            stage: Stage directory name, such as `1-resman`.

        Returns:
            A frozenset of variable names, empty for Stage 0.

        Raises:
            RepoError: If the stage is unknown or a local is not a map.
        """
        if stage not in _AUTO_TFVARS_LOCALS:
            raise RepoError(f"Unknown stage {stage}")
        local_values = _locals(self.bootstrap_dir / "outputs.tf")
        keys = set()
        for name in _AUTO_TFVARS_LOCALS[stage]:
            value = local_values.get(name)
            if not isinstance(value, dict):
                raise RepoError(f"Cannot read local.{name} in outputs.tf")
            keys.update(hcl.unquote(key) for key in value)
        return frozenset(keys)

    def min_terraform_version(self):
        """Returns the highest Terraform `required_version` floor of modules.

        Stages pull in many modules, so the effective minimum is the highest
        `>=` constraint declared under `modules/*/versions.tf`.

        Raises:
            RepoError: If no module declares a `>=` constraint.
        """
        floors = []
        for path in (self.root / "modules").glob("*/versions.tf"):
            for block in _load_hcl(path).get("terraform", []):
                constraint = hcl.unquote(block.get("required_version", ""))
                floors.extend(
                    version.Version(found)
                    for found in _VERSION_FLOOR_RE.findall(constraint)
                )
        if not floors:
            raise RepoError("No module declares a required_version floor")
        return str(max(floors))
