#!/usr/bin/env python3
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

"""Operator placeholder hydration for Incident Response runbooks and policy manuals.

Incident Response runbooks ship with bracketed operator tokens such as
``[KMS_PROJECT_ID]`` or ``[SOURCE_IP]`` embedded in copy/paste ``gcloud`` and
``kubectl`` command examples. Two very different kinds of token are mixed
together in those templates, and conflating them is what makes the delivered
runbook useless at 03:00 during a live incident:

DERIVABLE
    The value is a static property of the accredited environment and was
    already discovered by ``extract_system_data.py`` (project IDs, KMS key
    rings, key names, KMS locations, storage bucket names, service account
    emails, the organization domain and the organization ID). Leaving these
    un-hydrated forces a responder to go hunting for data the tool already
    holds. These are substituted with the real discovered value.

RUNTIME
    The value is only knowable during the incident itself (the attacker's
    source IP, the name of the Pod that was compromised, the version number of
    a key that has not been created yet). These must never be guessed. They are
    rewritten into an unmistakable operator fill-in marker of the form
    ``<SOURCE_IP: fill in ...>`` so that no responder can mistake them for a
    real value, and so that a stray copy/paste fails loudly instead of acting
    on the wrong resource.

Fail-closed behaviour
    A DERIVABLE token whose value is genuinely absent from the inventory
    renders as ``[NOT DETERMINED FROM SOURCE]``. The engine never synthesises a
    plausible-looking project ID, key name, service account email or domain:
    fabricated evidence in an ATO package is an accreditation fraud risk.

Only tokens on the two explicit allow-lists below are touched. Bracketed
citation shorthand that legitimately appears in NIST source text (``[PRIVACT]``,
``[EVIDACT]``, ``[COOP]``, ``[OMB M-19-23]``) and blank-template scaffolding
(``IR-[XYZ]-00[X]``) are left byte-for-byte alone.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Emitted whenever a DERIVABLE token cannot be resolved from the inventory.
NOT_DETERMINED: str = "[NOT DETERMINED FROM SOURCE]"

# Matches a bracketed SCREAMING_SNAKE_CASE operator token, e.g. "[KMS_PROJECT_ID]".
OPERATOR_TOKEN_RE: re.Pattern[str] = re.compile(r"\[([A-Z][A-Z0-9_]{2,})\]")

# A conservative shape check for cloud resource identifiers read verbatim out of
# Terraform. This deliberately does NOT enforce the strict GCP length rules: the
# value is transcribed from source, never generated, so rejecting a short but
# real identifier would silently drop true evidence. It exists purely to reject
# unresolved HCL interpolation, template residue and obvious junk.
_IDENTIFIER_RE: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9._:-]{1,62}$")

# RFC 1035-shaped DNS name with at least one dot and a alphabetic TLD.
_DOMAIN_RE: re.Pattern[str] = re.compile(
    r"^(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)

# Service account email shape: <account-id>@<project>.iam.gserviceaccount.com
# (or a Google-managed *.gserviceaccount.com variant).
_SA_EMAIL_RE: re.Pattern[str] = re.compile(
    r"^[a-z0-9][a-z0-9._+-]{0,63}@[a-z0-9][a-z0-9.-]{0,62}\.gserviceaccount\.com$"
)

# Numeric GCP organization / folder ID.
_NUMERIC_ID_RE: re.Pattern[str] = re.compile(r"^[0-9]{4,32}$")

# Project component of a fabricated service account email. extract_system_data
# historically defaulted the project segment to the literal string "workload"
# when the Terraform resource declared no project. Propagating that into a
# runbook would put an invented principal into an accreditation artifact.
_FABRICATED_SA_PROJECTS: Tuple[str, ...] = ("workload", "project", "example", "changeme")

# Parses "projects/<p>/locations/<l>/keyRings/<kr>[/cryptoKeys/<k>[/cryptoKeyVersions/<v>]]".
_KMS_PATH_RE: re.Pattern[str] = re.compile(
    r"projects/(?P<project>[^/\s]+)"
    r"/locations/(?P<location>[^/\s]+)"
    r"/keyRings/(?P<key_ring>[^/\s]+)"
    r"(?:/cryptoKeys/(?P<crypto_key>[^/\s]+))?"
)

# Parses the project segment of any "projects/<p>/..." self link.
_PROJECT_PATH_RE: re.Pattern[str] = re.compile(r"projects/(?P<project>[a-z0-9][a-z0-9.:-]{1,62})")

# ------------------------------------------------------------------------------
# Token allow-lists
# ------------------------------------------------------------------------------

# DERIVABLE tokens -> the human-readable label used in the provenance table.
# Every entry here MUST be resolvable from system_inventory.json or fail closed.
DERIVABLE_TOKENS: Dict[str, str] = {
    "PROJECT_ID": "GCP project ID",
    "KMS_PROJECT_ID": "Cloud KMS project ID",
    "KEYRING_NAME": "Cloud KMS key ring",
    "KEY_NAME": "Cloud KMS crypto key",
    "LOCATION": "Cloud KMS key location",
    "BUCKET_NAME": "Cloud Storage bucket",
    "SA_EMAIL": "Service account email",
    "ORGANIZATION_DOMAIN": "Organization DNS domain",
    "ORG_ID": "GCP organization ID",
}

# RUNTIME tokens -> the fill-in instruction rendered inside the marker.
# These identify the object that is compromised (or not yet created) during the
# incident. They are unknowable at generation time and are never guessed.
RUNTIME_TOKENS: Dict[str, str] = {
    "SOURCE_IP": "fill in the attacker source IP from the SCC finding or VPC Flow Logs",
    "POD_NAME": "fill in the compromised Pod name from the SCC finding or `kubectl get pods`",
    "NAMESPACE": "fill in the Kubernetes namespace of the compromised Pod",
    "NODE_NAME": "fill in the GKE node hosting the Pod from `kubectl get pod -o wide`",
    "INSTANCE_NAME": "fill in the compromised VM name from the alert",
    "INSTANCE_ID": "fill in the numeric instance ID from the Cloud Logging entry",
    "ZONE": "fill in the zone of the compromised VM from `gcloud compute instances list`",
    "DISK_NAME": "fill in the disk attached to the compromised VM",
    "TIMESTAMP": "fill in a UTC timestamp, e.g. 20260101t0000z",
    "VERSION": "fill in the CryptoKeyVersion number from the audit log resourceName",
    "NEW_VERSION": "fill in the version number returned by the preceding versions create call",
    "NEW_KEY_RESOURCE_PATH": "fill in the full resource path of the key version created above",
    "KEY_ID": "fill in the key ID from the preceding keys list output",
    "COMPROMISED_IDENTITY_EMAIL": "fill in the principalEmail of the compromised identity from the alert",
}

# Token that a runbook template may carry to receive the provenance table.
CONTEXT_BLOCK_TOKEN: str = "{{ DISCOVERED_ENVIRONMENT_CONTEXT }}"

#: Signatures of warnings already emitted in this process. Hydration runs once
#: per generated document (30+ per package), so an un-deduplicated warning would
#: bury the rest of the pipeline log and train operators to ignore it.
_WARNED_SIGNATURES: set = set()


def _warn_once(signature: str, message: str, *args: Any) -> None:
    """Emits a warning at most once per process for a given signature.

    Args:
        signature: Stable key identifying this warning instance.
        message: printf-style log message.
        *args: Arguments interpolated into ``message``.

    Returns:
        None.
    """
    if signature in _WARNED_SIGNATURES:
        return
    _WARNED_SIGNATURES.add(signature)
    logger.warning(message, *args)


def reset_hydration_warnings() -> None:
    """Clears the emitted-warning registry.

    Exposed for tests and for callers that process several targets in one
    process and need each target's diagnostics reported independently.

    Returns:
        None.
    """
    _WARNED_SIGNATURES.clear()


# ------------------------------------------------------------------------------
# Value validation helpers
# ------------------------------------------------------------------------------
def _is_plausible_identifier(value: Any) -> bool:
    """Reports whether a value looks like a real cloud resource identifier.

    Rejects unresolved HCL interpolation (``${var.x}``), template residue
    (``[CONFIG_REQUIRED: ...]``), redaction markers and anything containing
    whitespace. This is a fabrication guard, not a GCP naming-rule validator:
    accepted values are copied verbatim from the inventory.

    Args:
        value: Candidate value taken from the system inventory.

    Returns:
        True if the value may be emitted into a deliverable, False otherwise.
    """
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    if not candidate:
        return False
    if any(marker in candidate for marker in ("${", "var.", "local.", "[", "]", "{", "}")):
        return False
    if "REDACTED" in candidate.upper() or "NOT DETERMINED" in candidate.upper():
        return False
    return bool(_IDENTIFIER_RE.match(candidate))


def _sorted_unique(values: Iterable[str]) -> List[str]:
    """Deduplicates and sorts candidate values for deterministic selection.

    Determinism matters: the same Terraform must always yield the same runbook
    bytes, otherwise diffing successive ATO package revisions is impossible.

    Args:
        values: Raw candidate strings, possibly with duplicates.

    Returns:
        A sorted list of unique, stripped, non-empty strings.
    """
    return sorted({v.strip() for v in values if isinstance(v, str) and v.strip()})


def _parse_kms_path(raw: Any) -> Dict[str, str]:
    """Extracts the project / location / key ring / key parts of a KMS resource path.

    Args:
        raw: A candidate KMS resource path, or any other value.

    Returns:
        A dictionary with any of the keys ``project``, ``location``, ``key_ring``
        and ``crypto_key`` that could be parsed. Empty if ``raw`` is not a KMS path.
    """
    if not isinstance(raw, str) or "keyRings/" not in raw:
        return {}
    match = _KMS_PATH_RE.search(raw)
    if not match:
        return {}
    return {key: value for key, value in match.groupdict().items() if value}


# ------------------------------------------------------------------------------
# Inventory resolvers
# ------------------------------------------------------------------------------
def collect_kms_facts(inventory: Dict[str, Any]) -> Dict[str, List[str]]:
    """Collects Cloud KMS project, location, key ring and key candidates.

    Handles both inventory shapes emitted by the extractor: a ``kms_keys`` entry
    whose ``name`` is a bare key name plus a ``key_ring`` full resource path, and
    an entry whose ``name`` is itself a full ``projects/.../cryptoKeys/...`` path.

    Args:
        inventory: Parsed ``system_inventory.json`` contents.

    Returns:
        A dictionary mapping ``kms_projects``, ``kms_locations``, ``key_rings``
        and ``key_names`` to deterministically sorted candidate lists.
    """
    infra = inventory.get("infrastructure_components") or {}
    projects: List[str] = []
    locations: List[str] = []
    key_rings: List[str] = []
    key_names: List[str] = []

    for entry in infra.get("kms_keys") or []:
        if isinstance(entry, dict):
            raw_name = entry.get("name")
            raw_ring = entry.get("key_ring") or entry.get("keyring")
            raw_location = entry.get("location")
        else:
            raw_name = entry
            raw_ring = None
            raw_location = None

        parsed_name = _parse_kms_path(raw_name)
        parsed_ring = _parse_kms_path(raw_ring)

        for parsed in (parsed_ring, parsed_name):
            if parsed.get("project") and _is_plausible_identifier(parsed["project"]):
                projects.append(parsed["project"])
            if parsed.get("location") and _is_plausible_identifier(parsed["location"]):
                locations.append(parsed["location"])
            if parsed.get("key_ring") and _is_plausible_identifier(parsed["key_ring"]):
                key_rings.append(parsed["key_ring"])
            if parsed.get("crypto_key") and _is_plausible_identifier(parsed["crypto_key"]):
                key_names.append(parsed["crypto_key"])

        # A bare key name (not a resource path) is the crypto key itself.
        if not parsed_name and _is_plausible_identifier(raw_name):
            key_names.append(str(raw_name).strip())
        # A bare key ring name likewise.
        if not parsed_ring and _is_plausible_identifier(raw_ring):
            key_rings.append(str(raw_ring).strip())
        if _is_plausible_identifier(raw_location):
            locations.append(str(raw_location).strip())

    return {
        "kms_projects": _sorted_unique(projects),
        "kms_locations": _sorted_unique(locations),
        "key_rings": _sorted_unique(key_rings),
        "key_names": _sorted_unique(key_names),
    }


#: Inventory keys, in precedence order, that may carry an explicitly configured
#: project ID. An explicit value always wins over one inferred from a self link.
_EXPLICIT_PROJECT_KEYS: Tuple[str, ...] = (
    "project_id",
    "gcp_project_id",
    "prod_project_id",
    "service_project_id",
    "host_project_id",
)


def _explicit_project_id(inventory: Dict[str, Any]) -> Optional[str]:
    """Returns the operator-configured project ID, if one was supplied.

    Args:
        inventory: Parsed ``system_inventory.json`` contents.

    Returns:
        The first plausible explicitly-configured project ID, or None.
    """
    sys_info = inventory.get("system_information") or {}
    for key in _EXPLICIT_PROJECT_KEYS:
        value = sys_info.get(key)
        if _is_plausible_identifier(value):
            return str(value).strip()
    return None


def collect_project_ids(inventory: Dict[str, Any]) -> List[str]:
    """Collects every GCP project ID observed anywhere in the inventory.

    Explicitly configured project IDs are preferred, but project segments parsed
    out of real resource self links (compute instance links, KMS key ring paths,
    logging sink destinations) are equally authoritative: they were transcribed
    from the Terraform, not invented.

    Args:
        inventory: Parsed ``system_inventory.json`` contents.

    Returns:
        A deterministically sorted list of unique project IDs. Empty if none
        could be established.
    """
    infra = inventory.get("infrastructure_components") or {}
    found: List[str] = []

    explicit = _explicit_project_id(inventory)
    if explicit:
        found.append(explicit)

    path_carrying_fields = (
        ("compute_instances", ("self_link", "project")),
        ("kms_keys", ("key_ring", "name", "project")),
        ("logging_sinks", ("destination", "project")),
        ("service_accounts", ("email", "project")),
        ("storage_buckets", ("project",)),
        ("gke_clusters", ("self_link", "project")),
    )
    for collection_name, fields in path_carrying_fields:
        for entry in infra.get(collection_name) or []:
            if not isinstance(entry, dict):
                continue
            for field in fields:
                raw = entry.get(field)
                if not isinstance(raw, str):
                    continue
                if field == "project":
                    if _is_plausible_identifier(raw):
                        found.append(raw.strip())
                    continue
                match = _PROJECT_PATH_RE.search(raw)
                if match and _is_plausible_identifier(match.group("project")):
                    found.append(match.group("project"))

    return _sorted_unique(found)


def collect_bucket_names(inventory: Dict[str, Any]) -> List[str]:
    """Collects Cloud Storage bucket names discovered in the Terraform.

    Args:
        inventory: Parsed ``system_inventory.json`` contents.

    Returns:
        A deterministically sorted list of unique bucket names.
    """
    infra = inventory.get("infrastructure_components") or {}
    names: List[str] = []
    for entry in infra.get("storage_buckets") or []:
        raw = entry.get("name") if isinstance(entry, dict) else entry
        if _is_plausible_identifier(raw):
            names.append(str(raw).strip())
    return _sorted_unique(names)


def collect_service_account_emails(inventory: Dict[str, Any]) -> List[str]:
    """Collects fully-qualified service account emails discovered in the Terraform.

    An email is only accepted if it is genuinely present (or reconstructable
    from an account ID plus a project recorded *on that same service account*).
    A service account whose project is unknown yields nothing: synthesising
    ``sa-x@<some-other-project>.iam.gserviceaccount.com`` would put a principal
    into an accreditation artifact that does not exist.

    Args:
        inventory: Parsed ``system_inventory.json`` contents.

    Returns:
        A deterministically sorted list of unique service account emails.
    """
    infra = inventory.get("infrastructure_components") or {}
    emails: List[str] = []
    for entry in infra.get("service_accounts") or []:
        if not isinstance(entry, dict):
            continue
        raw_email = entry.get("email")
        if isinstance(raw_email, str) and _SA_EMAIL_RE.match(raw_email.strip()):
            project_part = raw_email.strip().split("@", 1)[1].split(".", 1)[0]
            if project_part in _FABRICATED_SA_PROJECTS:
                logger.warning(
                    "Discarding service account email %r: its project segment %r is a "
                    "known extractor placeholder, not a discovered project.",
                    raw_email.strip(),
                    project_part,
                )
                continue
            emails.append(raw_email.strip())
            continue
        account_id = entry.get("account_id")
        project = entry.get("project")
        if _is_plausible_identifier(account_id) and _is_plausible_identifier(project):
            emails.append(f"{str(account_id).strip()}@{str(project).strip()}.iam.gserviceaccount.com")
    return _sorted_unique(emails)


def collect_service_account_ids(inventory: Dict[str, Any]) -> List[str]:
    """Collects bare service account IDs, used only for operator guidance.

    These are reported in the provenance table when no fully-qualified email is
    derivable, so a responder still knows which service accounts exist without
    the engine inventing an email address for them.

    Args:
        inventory: Parsed ``system_inventory.json`` contents.

    Returns:
        A deterministically sorted list of unique service account IDs.
    """
    infra = inventory.get("infrastructure_components") or {}
    ids: List[str] = []
    for entry in infra.get("service_accounts") or []:
        if not isinstance(entry, dict):
            continue
        account_id = entry.get("account_id") or entry.get("resource_name")
        if _is_plausible_identifier(account_id):
            ids.append(str(account_id).strip())
    return _sorted_unique(ids)


def resolve_organization_domain(inventory: Dict[str, Any]) -> Optional[str]:
    """Resolves the organization's DNS domain, or None if none was configured.

    An explicit configuration key is required. The organization *display name*
    (``system_information.organization``, e.g. "Enterprise Public Sector Agency")
    is deliberately NOT machine-mangled into a domain: turning "Dept of X" into
    "deptofx.gov" invents an identity provider namespace, which is fabrication.
    The display name is only accepted when it already *is* a valid DNS domain,
    which happens when the foundation config supplies ``organization.domain_name``.

    Args:
        inventory: Parsed ``system_inventory.json`` contents.

    Returns:
        The lower-cased domain, or None if no domain is available.
    """
    sys_info = inventory.get("system_information") or {}
    for key in ("organization_domain", "domain_name", "organization_domain_name"):
        value = sys_info.get(key)
        if isinstance(value, str) and _DOMAIN_RE.match(value.strip().lower()):
            return value.strip().lower()

    display_name = sys_info.get("organization")
    if isinstance(display_name, str) and _DOMAIN_RE.match(display_name.strip().lower()):
        return display_name.strip().lower()

    _warn_once(
        "organization_domain",
        "No organization DNS domain is available in the inventory; "
        "[ORGANIZATION_DOMAIN] will fail closed as %s. Set organization.domain_name "
        "in the foundation configuration to hydrate it.",
        NOT_DETERMINED,
    )
    return None


def resolve_organization_id(inventory: Dict[str, Any]) -> Optional[str]:
    """Resolves the numeric GCP organization ID, or None if it was not discovered.

    Args:
        inventory: Parsed ``system_inventory.json`` contents.

    Returns:
        The organization ID as a string, or None.
    """
    sys_info = inventory.get("system_information") or {}
    for key in ("org_id", "organization_id", "gcp_org_id"):
        value = sys_info.get(key)
        if value is None:
            continue
        candidate = str(value).strip()
        if _NUMERIC_ID_RE.match(candidate):
            return candidate
    return None


# ------------------------------------------------------------------------------
# Operator context
# ------------------------------------------------------------------------------
class OperatorContext:
    """Resolved DERIVABLE values plus the alternatives they were chosen from.

    Attributes:
        values: Token name -> chosen value, or None when it failed closed.
        candidates: Token name -> every candidate discovered, sorted.
        notes: Token name -> extra operator guidance (e.g. discovered account IDs
            when no fully-qualified service account email was derivable).
    """

    def __init__(
        self,
        values: Dict[str, Optional[str]],
        candidates: Dict[str, List[str]],
        notes: Dict[str, str],
    ) -> None:
        """Initializes the resolved operator context.

        Args:
            values: Token name -> chosen value or None.
            candidates: Token name -> full sorted candidate list.
            notes: Token name -> supplementary operator guidance.
        """
        self.values: Dict[str, Optional[str]] = values
        self.candidates: Dict[str, List[str]] = candidates
        self.notes: Dict[str, str] = notes

    def rendered(self, token: str) -> str:
        """Returns the string to substitute for a DERIVABLE token.

        Args:
            token: The bare token name, e.g. ``"KEY_NAME"``.

        Returns:
            The discovered value, or ``[NOT DETERMINED FROM SOURCE]``.
        """
        value = self.values.get(token)
        return value if value else NOT_DETERMINED

    def has_any_resolved(self) -> bool:
        """Reports whether at least one DERIVABLE token resolved to a real value.

        Returns:
            True if any token has a non-empty discovered value.
        """
        return any(bool(v) for v in self.values.values())


def build_operator_context(
    inventory: Dict[str, Any],
    tokens: Optional[List[str]] = None,
) -> OperatorContext:
    """Resolves every DERIVABLE operator token from the system inventory.

    Where several candidates exist (multiple buckets, multiple KMS keys) the
    first in sorted order is selected so the output is byte-stable across runs,
    and the full alternative list is retained for the provenance table.

    One cross-token consistency rule applies. ``[SA_EMAIL]`` and ``[PROJECT_ID]``
    appear together in the IAM runbook as
    ``gcloud iam service-accounts disable [SA_EMAIL] --project=[PROJECT_ID]``.
    Choosing each independently can name a project that the selected service
    account does not live in, which produces a command that simply fails and
    wastes a responder's time. When a document uses both tokens and no project ID
    was explicitly configured, ``[PROJECT_ID]`` is therefore taken from the
    project segment of the selected service account email. That value is still
    real, discovered data -- it is only the tie-break that changes.

    Args:
        inventory: Parsed ``system_inventory.json`` contents.
        tokens: Optional list of DERIVABLE token names the target document
            actually uses, from :func:`find_operator_tokens`. Used only to apply
            the cross-token consistency rule above.

    Returns:
        An OperatorContext holding the chosen values, all candidates and notes.

    Raises:
        TypeError: If ``inventory`` is not a dictionary.
    """
    if not isinstance(inventory, dict):
        raise TypeError(f"inventory must be a dict, got {type(inventory).__name__}")

    kms = collect_kms_facts(inventory)
    projects = collect_project_ids(inventory)
    buckets = collect_bucket_names(inventory)
    sa_emails = collect_service_account_emails(inventory)
    domain = resolve_organization_domain(inventory)
    org_id = resolve_organization_id(inventory)

    candidates: Dict[str, List[str]] = {
        "PROJECT_ID": projects,
        "KMS_PROJECT_ID": kms["kms_projects"],
        "KEYRING_NAME": kms["key_rings"],
        "KEY_NAME": kms["key_names"],
        "LOCATION": kms["kms_locations"],
        "BUCKET_NAME": buckets,
        "SA_EMAIL": sa_emails,
        "ORGANIZATION_DOMAIN": [domain] if domain else [],
        "ORG_ID": [org_id] if org_id else [],
    }
    values: Dict[str, Optional[str]] = {
        token: (options[0] if options else None) for token, options in candidates.items()
    }

    notes: Dict[str, str] = {}
    token_set = set(tokens or [])
    explicit_project = _explicit_project_id(inventory)
    if explicit_project:
        values["PROJECT_ID"] = explicit_project
    elif {"PROJECT_ID", "SA_EMAIL"} <= token_set and values["SA_EMAIL"]:
        sa_project = values["SA_EMAIL"].split("@", 1)[1].split(".", 1)[0]
        if _is_plausible_identifier(sa_project) and values["PROJECT_ID"] != sa_project:
            values["PROJECT_ID"] = sa_project
            notes["PROJECT_ID"] = (
                "Selected to match the project of the example service account so the "
                "combined command is internally consistent."
            )
    if not values["SA_EMAIL"]:
        account_ids = collect_service_account_ids(inventory)
        if account_ids:
            notes["SA_EMAIL"] = (
                "Service accounts were discovered but no project was recorded for them, "
                "so a fully-qualified email cannot be derived without inventing one. "
                "Discovered account IDs: " + ", ".join(f"`{a}`" for a in account_ids)
            )
    if not values["ORGANIZATION_DOMAIN"]:
        notes["ORGANIZATION_DOMAIN"] = (
            "No DNS domain is configured. Set `organization.domain_name` in the "
            "foundation configuration; the organization display name is deliberately "
            "not converted into a domain because that would be fabricated evidence."
        )
    if not values["ORG_ID"]:
        notes["ORG_ID"] = (
            "No numeric organization ID is configured. Set `organization.org_id` in the "
            "foundation configuration."
        )

    unresolved = sorted(token for token, value in values.items() if not value)
    if unresolved:
        _warn_once(
            "unresolved:" + ",".join(unresolved),
            "Runbook hydration failed closed for %d operator token(s): %s. "
            "These render as %s rather than a fabricated value.",
            len(unresolved),
            ", ".join(unresolved),
            NOT_DETERMINED,
        )

    return OperatorContext(values=values, candidates=candidates, notes=notes)


# ------------------------------------------------------------------------------
# Rendering
# ------------------------------------------------------------------------------
def render_runtime_marker(token: str) -> str:
    """Renders an unmistakable operator fill-in marker for a RUNTIME token.

    Angle brackets are used rather than square brackets so the marker cannot be
    confused with a hydrated value or with the ``[NOT DETERMINED FROM SOURCE]``
    fail-closed marker, and so a stray copy/paste into a shell is a syntax error
    rather than a command that silently targets the wrong resource.

    Args:
        token: The bare token name, e.g. ``"SOURCE_IP"``.

    Returns:
        A marker of the form ``<SOURCE_IP: fill in ...>``.
    """
    guidance = RUNTIME_TOKENS.get(token, "fill in during the incident")
    return f"<{token}: {guidance}>"


def find_operator_tokens(content: str) -> Tuple[List[str], List[str]]:
    """Finds which allow-listed operator tokens a template actually uses.

    Args:
        content: Raw template text, before any substitution.

    Returns:
        A tuple of (derivable token names, runtime token names), each sorted in
        the canonical allow-list order rather than order of appearance so the
        rendered provenance table is byte-stable.
    """
    if not isinstance(content, str):
        return ([], [])
    present = {match.group(1) for match in OPERATOR_TOKEN_RE.finditer(content)}
    derivable = [token for token in DERIVABLE_TOKENS if token in present]
    runtime = [token for token in RUNTIME_TOKENS if token in present]
    return (derivable, runtime)


def render_discovered_context_block(
    context: OperatorContext,
    tokens: Optional[List[str]] = None,
) -> str:
    """Renders the Markdown provenance table describing every hydrated value.

    The table makes it impossible for a reader to mistake a hydrated value for
    "the only" resource of that kind: every alternative discovered in the
    Terraform is listed alongside the selected example.

    Args:
        context: The resolved operator context.
        tokens: Optional subset of DERIVABLE token names to document. Defaults to
            every DERIVABLE token. Pass the result of :func:`find_operator_tokens`
            to scope the table to the placeholders a given runbook actually uses.

    Returns:
        A Markdown fragment. Never empty -- if nothing resolved, it says so.
    """
    selected = [t for t in DERIVABLE_TOKENS if t in tokens] if tokens is not None else list(DERIVABLE_TOKENS)
    if not selected:
        return (
            "## Discovered Environment Context\n\n"
            "This runbook contains no environment-specific placeholders that the "
            "compliance engine can pre-fill from the discovered Terraform inventory.\n"
        )

    lines: List[str] = []
    lines.append("## Discovered Environment Context")
    lines.append("")
    lines.append(
        "The command examples in this runbook have been pre-filled from the Terraform "
        "inventory discovered by the compliance engine. Where more than one resource of "
        "a kind exists, the first in sorted order was selected as the example and the "
        "alternatives are listed below."
    )
    lines.append("")
    lines.append("> [!CAUTION]")
    lines.append(
        "> These are **examples drawn from the discovered inventory**, not a statement "
        "of incident scope. Confirm every value against the actual finding before "
        "running any command, especially `disable`, `delete` and `destroy` operations. "
        "Values shown as `[NOT DETERMINED FROM SOURCE]` could not be derived and must "
        "be supplied by the responder. Values shown as `<TOKEN: fill in ...>` are only "
        "knowable during the incident and were deliberately left un-filled."
    )
    lines.append("")
    lines.append("| Placeholder | Value used in examples | Source | Other discovered values |")
    lines.append("| :--- | :--- | :--- | :--- |")

    any_resolved = False
    for token in selected:
        label = DERIVABLE_TOKENS[token]
        options = context.candidates.get(token) or []
        chosen = context.rendered(token)
        if options:
            any_resolved = True
            value_cell = f"`{chosen}`"
            others = options[1:]
            others_cell = ", ".join(f"`{o}`" for o in others) if others else "_(none)_"
        else:
            value_cell = f"`{NOT_DETERMINED}`"
            others_cell = "_(none discovered)_"
        note = context.notes.get(token)
        if note:
            others_cell = f"{others_cell}<br/>{note}" if options and options[1:] else note
        lines.append(f"| `[{token}]` | {value_cell} | {label} | {others_cell} |")

    lines.append("")
    if not any_resolved:
        lines.append("> [!WARNING]")
        lines.append(
            "> None of the environment values referenced by this runbook could be "
            "derived from the discovered inventory. Every placeholder below must be "
            "supplied manually by the responder."
        )
        lines.append("")
    return "\n".join(lines)


def hydrate_operator_placeholders(
    content: str,
    inventory: Dict[str, Any],
    context: Optional[OperatorContext] = None,
) -> str:
    """Substitutes DERIVABLE and RUNTIME operator tokens in template content.

    Tokens outside the two explicit allow-lists are left untouched, so bracketed
    legal citations that occur verbatim in NIST source text (``[PRIVACT]``,
    ``[EVIDACT]``, ``[COOP]``) and blank-template scaffolding survive unchanged.

    Args:
        content: Raw template text, before ``{{ }}`` macro rendering.
        inventory: Parsed ``system_inventory.json`` contents.
        context: Optional pre-built OperatorContext, to avoid re-resolving the
            inventory once per document.

    Returns:
        The content with allow-listed operator tokens substituted.

    Raises:
        TypeError: If ``content`` is not a string.
    """
    if not isinstance(content, str):
        raise TypeError(f"content must be a str, got {type(content).__name__}")
    if not content:
        return content

    resolved = context if context is not None else build_operator_context(inventory)

    def _replace(match: "re.Match[str]") -> str:
        token = match.group(1)
        if token in DERIVABLE_TOKENS:
            return resolved.rendered(token)
        if token in RUNTIME_TOKENS:
            return render_runtime_marker(token)
        return match.group(0)

    return OPERATOR_TOKEN_RE.sub(_replace, content)
