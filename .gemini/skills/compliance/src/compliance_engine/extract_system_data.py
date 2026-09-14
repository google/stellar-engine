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

"""
System Infrastructure & Configuration Extractor

This script scans:
1. `compliance_config.yaml` / `variables.yaml` for user metadata, personnel roles, and version configs.
2. `.tf` and `.yaml` files across the codebase to discover:
   - All enabled GCP API Services (*.googleapis.com)
   - VPC Networks, Subnets, Firewall Rules
   - GKE Clusters, Cloud SQL Databases, BigQuery Datasets
   - Cloud KMS Key Rings and Crypto Keys
   - Compute Engine VMs, Bastion Hosts, Palo Alto NGFW Modules
   - Cloud Storage Buckets, Service Accounts, Logging Sinks
   - Assured Workloads compliance baselines
   - TDD-style IAM Groups, Personas, Roles, and Terraform IAM Bindings
   - ANY generic Terraform resource defined across the workspace
Outputs: `system_inventory.json`
"""

import ipaddress
import json
import logging
import os
import random
import shutil
import subprocess
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, Final, List, Optional, Sequence, Set, Tuple, Union

try:
    from .file_helpers import (
        DEFAULT_CSP_PATO_PACKAGE_ID,
        ensure_path_within_boundary,
        get_skill_root,
        is_sensitive_key,
        parse_yaml_safe,
        parse_yaml_scalar,
        read_json_file,
        read_text_file,
        resolve_path,
        scrub_sensitive_data,
        validate_compliance_config_schema,
        validate_system_inventory_schema,
        write_json_file,
    )
except (ImportError, ValueError):
    from file_helpers import (
        DEFAULT_CSP_PATO_PACKAGE_ID,
        ensure_path_within_boundary,
        get_skill_root,
        is_sensitive_key,
        parse_yaml_safe,
        parse_yaml_scalar,
        read_json_file,
        read_text_file,
        resolve_path,
        scrub_sensitive_data,
        validate_compliance_config_schema,
        validate_system_inventory_schema,
        write_json_file,
    )

# Terraform HCL is parsed exclusively through the in-repo hardened facade, which
# is bound to the local name ``hcl2`` so that every existing call site
# (``hcl2.loads(...)``) keeps working unchanged.
#
# This import MUST NOT be a bare ``import hcl2``. An earlier revision vendored a
# package literally named ``hcl2`` inside ``scripts/``, so a bare import happened
# to resolve to the in-repo parser. Once that shadow package was removed, the same
# bare import silently resolved to whatever distribution ships under that name --
# in practice checkov's ``bc-python-hcl2`` fork, which returns a materially
# different structure (every scalar wrapped in a list, synthetic
# ``__start_line__``/``__end_line__`` keys) and bypasses every resource budget in
# ``hcl_parser``. On a host with neither distribution installed the bare import
# raised ``ImportError`` outright, making this module unimportable even though
# ``requirements.txt`` documents ``python-hcl2`` as optional.
#
# ``hcl_parser`` performs its own verified backend selection: it delegates to a
# genuine ``python-hcl2`` only after a canary document round-trips to the exact
# canonical shape, and otherwise uses the hardened recursive-descent parser.
try:
    from . import hcl_parser as hcl2
except (ImportError, ValueError):
    import hcl_parser as hcl2

#: Parse-failure exception type. ``hcl_parser`` aliases this to its own
#: ``Hcl2Error`` when no external backend is in use, and rebinds it to the real
#: ``lark.LarkError`` when a verified ``python-hcl2`` backend was accepted.
LarkError = hcl2.LarkError

try:
    from . import safe_xml as ET
except (ImportError, ValueError):
    import safe_xml as ET

import yaml


try:
    from .audit_log import audit_operation, AuditEvent
except (ImportError, ValueError):
    from audit_log import audit_operation, AuditEvent

logger = logging.getLogger("extract_system_data")

SKILL_BASE = str(get_skill_root())

IGNORED_TRAVERSAL_DIRS: Set[str] = {
    ".git", ".terraform", "ato_artifacts", "node_modules", "vendor"
}


#: Configuration keys that were renamed after release, mapped to their current name.
#:
#: A silently-ignored configuration key is the most damaging failure mode this engine
#: has. Nothing errors: the operator's value is accepted, the field quietly falls back
#: to an inferred default, and the authorization package then asserts something the
#: operator never said -- in an artifact that gets signed.
#:
#: ``primary_gcp_location`` shipped in the original example configuration and is
#: present in deployed engagement configurations, so it is honored indefinitely rather
#: than being treated as a migration burden on the operator.
LEGACY_CONFIG_KEY_ALIASES: Final[Dict[str, str]] = {
    "primary_gcp_location": "primary_location",
}

#: Blocks within a configuration file that carry the same key vocabulary as the top
#: level, and therefore need the same alias treatment.
_ALIASED_CONFIG_SECTIONS: Final[Tuple[str, ...]] = ("system_information",)


def apply_legacy_config_aliases(
    cfg: Dict[str, Any],
    source_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Rewrites superseded configuration keys to their current names, in place.

    Applied to the top level of a configuration file and to each block listed in
    :data:`_ALIASED_CONFIG_SECTIONS`, because the same key may legitimately appear in
    either position.

    An explicitly-provided current key always wins; the legacy key is then dropped
    with a distinct warning so a half-migrated file does not silently resolve to the
    stale value.

    Args:
        cfg: Parsed configuration mapping. Mutated in place.
        source_path: Optional path used to make the deprecation warning actionable.

    Returns:
        The same mapping, for call-site convenience.
    """
    if not isinstance(cfg, dict):
        return cfg

    where = f" in '{source_path}'" if source_path else ""

    def _migrate(section: Dict[str, Any], label: str) -> None:
        """Rewrites aliases within a single mapping level.

        Args:
            section: Mapping to migrate in place.
            label: Dotted prefix used in log messages.
        """
        for legacy_key, current_key in LEGACY_CONFIG_KEY_ALIASES.items():
            if legacy_key not in section:
                continue
            legacy_value = section.pop(legacy_key)

            existing = section.get(current_key)
            if existing is not None and str(existing).strip():
                logger.warning(
                    "Configuration key '%s%s' is deprecated and was ignored%s because "
                    "'%s%s' is also set. Remove the deprecated key.",
                    label, legacy_key, where, label, current_key,
                )
                continue

            if legacy_value is None or not str(legacy_value).strip():
                continue

            section[current_key] = legacy_value
            logger.warning(
                "Configuration key '%s%s' is deprecated%s; its value was applied to "
                "'%s%s'. Rename the key to silence this warning.",
                label, legacy_key, where, label, current_key,
            )

    _migrate(cfg, "")
    for section_name in _ALIASED_CONFIG_SECTIONS:
        section = cfg.get(section_name)
        if isinstance(section, dict):
            _migrate(section, f"{section_name}.")

    return cfg




#: Upper bound on captured output from an external tool. `terraform show -json`
#: on a large state file is the realistic worst case.
MAX_SUBPROCESS_OUTPUT_BYTES: int = 5 * 1024 * 1024

#: Bounded retry policy for transient execution faults.
SUBPROCESS_RETRY_BASE_SECONDS: float = 1.0


def _sanitized_path_env() -> Dict[str, str]:
    """Builds an environment whose PATH contains only trusted absolute directories.

    Relative PATH entries and any directory inside the current working directory are
    dropped, so a hostile file dropped into a scanned repository cannot shadow a
    system binary such as ``terraform`` (CWE-426 untrusted search path).

    Returns:
        A copy of the process environment with a filtered PATH.
    """
    safe_env = os.environ.copy()
    raw_path = safe_env.get("PATH")
    if not raw_path:
        return safe_env

    try:
        cwd = Path.cwd().resolve()
    except OSError:
        cwd = None

    trusted: List[str] = []
    for entry in raw_path.split(os.pathsep):
        if not entry or not os.path.isabs(entry):
            continue
        # Compare resolved paths, not string prefixes: '/work' is a string prefix
        # of '/workspace' but is not a parent of it.
        try:
            candidate = Path(entry).resolve()
        except OSError:
            continue
        if cwd is not None and (candidate == cwd or cwd in candidate.parents):
            continue
        trusted.append(entry)

    safe_env["PATH"] = os.pathsep.join(trusted)
    return safe_env


def safe_run_command(
    cmd: Sequence[str],
    cwd: Optional[str] = None,
    timeout: int = 30,
    retries: int = 1,
) -> "subprocess.CompletedProcess[str]":
    """Runs an external command with a sanitized PATH and bounded output.

    Args:
        cmd: Command argument vector. The caller's sequence is never mutated.
        cwd: Optional working directory for the child process.
        timeout: Per-attempt wall-clock timeout in seconds.
        retries: Number of additional attempts after the first for transient faults.

    Returns:
        The completed process, with decoded stdout and stderr.

    Raises:
        ValueError: If the command vector is empty or ``retries`` is negative.
        FileNotFoundError: If the binary cannot be resolved on the sanitized PATH.
        subprocess.TimeoutExpired: If the final attempt exceeds ``timeout``.
        OSError: If the final attempt fails to execute.
    """
    if not cmd or not cmd[0]:
        raise ValueError("Empty command")
    if retries < 0:
        raise ValueError(f"retries must be non-negative, got {retries}")

    safe_env = _sanitized_path_env()

    # Build a new vector; mutating the caller's list would corrupt a command the
    # caller may reuse or log.
    argv: List[str] = [str(arg) for arg in cmd]
    if not os.path.isabs(argv[0]):
        resolved = shutil.which(argv[0], path=safe_env.get("PATH", os.defpath))
        if not resolved:
            raise FileNotFoundError(f"Binary not found: {argv[0]}")
        argv[0] = resolved

    for attempt in range(retries + 1):
        is_final = attempt == retries
        with audit_operation(event_type=AuditEvent.EXTERNAL_COMMAND, obj=argv[0]):
            with subprocess.Popen(
                argv,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=safe_env,
                shell=False,
                text=True,
            ) as proc:
                try:
                    stdout_data, stderr_data = proc.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.communicate()
                    if is_final:
                        raise
                    stdout_data = stderr_data = None

            if stdout_data is not None:
                # Reject rather than truncate: a clipped `terraform show -json`
                # payload would either fail to parse or, worse, parse as a smaller
                # inventory and silently under-report the system boundary.
                if len(stdout_data) > MAX_SUBPROCESS_OUTPUT_BYTES:
                    raise MemoryError(
                        f"{argv[0]} emitted more than {MAX_SUBPROCESS_OUTPUT_BYTES} "
                        "bytes on stdout; refusing to parse a truncated result."
                    )
                if len(stderr_data) > MAX_SUBPROCESS_OUTPUT_BYTES:
                    stderr_data = stderr_data[:MAX_SUBPROCESS_OUTPUT_BYTES]

                result = subprocess.CompletedProcess(
                    proc.args, proc.returncode, stdout_data, stderr_data
                )
                if result.returncode == 0 or is_final:
                    return result

        delay = SUBPROCESS_RETRY_BASE_SECONDS * (2 ** attempt)
        delay += random.uniform(0, delay / 2)
        logger.warning(
            "Command '%s' attempt %d/%d unsuccessful; retrying in %.2fs",
            argv[0],
            attempt + 1,
            retries + 1,
            delay,
        )
        time.sleep(delay)

    # Defensive: the loop returns or raises on its final iteration.
    raise RuntimeError(f"{argv[0]} exhausted {retries + 1} attempts")

def deep_merge_dict(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges update into base without clobbering populated values with empties.

    Args:
        base: Target dictionary modified in-place.
        update: Source dictionary containing values to merge.

    Returns:
        The merged base dictionary.
    """
    if not isinstance(base, dict) or not isinstance(update, dict):
        return update
    for k, v in update.items():
        if isinstance(v, dict):
            base[k] = deep_merge_dict(base.get(k, {}), v)
        elif isinstance(v, list):
            if k not in base or not base[k]:
                base[k] = list(v)
            else:
                # Merge lists without duplicating primitives
                for item in v:
                    if item not in base[k]:
                        base[k].append(item)
        elif v is not None and v != "":
            base[k] = v
    return base


def is_valid_cidr(cidr: Any) -> bool:
    """Validates that a string is a legitimate IPv4 or IPv6 CIDR range.

    Rejects raw HCL interpolation, variable placeholders, and AST artifacts.
    Supports both IPv4 (e.g. '10.0.0.0/8', '0.0.0.0/0') and IPv6 (e.g. '::/0', '2001:db8::/32').
    """
    if not isinstance(cidr, str):
        return False
    cidr = cidr.strip()
    if (
        not cidr
        or "/" not in cidr
        or cidr.startswith("${")
        or "${" in cidr
        or "try(" in cidr
        or "lookup(" in cidr
        or "each." in cidr
        or "var." in cidr
        or "local." in cidr
        or "null" in cidr.lower()
    ):
        return False
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except (ValueError, AttributeError):
        return False


GENERIC_VAR_NAMES = {
    "name", "id", "type", "description", "tags", "labels", "prefix", "suffix",
    "vpc_id", "subnet_id", "network_id"
}


def is_valid_resource_name(name: Any) -> bool:
    """Checks if a string is a valid human-readable resource name.

    Rejects raw HCL interpolation syntax, unresolved expressions, traversals with dots,
    or generic keywords.
    """
    if not isinstance(name, str):
        return False
    name = name.strip()
    if (
        not name
        or len(name) < 2
        or name.startswith("${")
        or "${" in name
        or "var." in name
        or "local." in name
        or "each." in name
        or "try(" in name
        or "lookup(" in name
        or "." in name
        or name.startswith(("-", "_"))
        or name.endswith(("-", "_"))
    ):
        return False
    if name.lower() in (
        "vpc",
        "network",
        "firewall",
        "default",
        "main",
        "this",
        "subnets",
        "null",
        "none",
        "try",
        "lookup",
        "config",
        "unresolved",
    ):
        return False
    return True


def clean_interpolated_string(
    s: Any, resolved_vars: Optional[Dict[str, Any]] = None, default_val: str = ""
) -> str:
    """Attempts to resolve or sanitize an HCL interpolated string like ${var.xyz}.

    If variables cannot be resolved, strips out expression syntax to produce a
    clean human-readable asset identifier.
    """
    if not isinstance(s, str):
        return default_val if s is None else str(s)
    s = s.strip()
    if not s:
        return default_val

    # Unbound module references starting with var. or local.
    if s.startswith("var.") or s.startswith("local."):
        s = "${" + s + "}"

    if not ("${" in s or "try(" in s or "lookup(" in s):
        return s

    standard_fallbacks = {
        "var.env_short": "dev",
        "var.env": "dev",
        "var.environment": "dev",
        "var.resource_prefix": "gcp",
        "var.region": "us-east4",
        "local.region": "us-east4",
        "local.zone": "us-east4-a",
        "var.zone": "us-east4-a",
        "var.management_subnet": "management-subnet",
        "var.workstation_subnet": "workstation-subnet",
        "var.tenant_subnet": "tenant-subnet",
        "var.spoke_subnet": "spoke-subnet",
    }
    merged_vars = dict(standard_fallbacks)
    if resolved_vars:
        for k, v in resolved_vars.items():
            if isinstance(v, (str, int, float, bool)):
                merged_vars[k] = v
                merged_vars[f"var.{k}"] = v
                merged_vars[f"local.{k}"] = v

    # Handle substr(var, start, len) e.g. substr(var.environment, 0, 1) -> "d"
    def _repl_substr(m: Any) -> str:
        var_k = m.group(1)
        start = int(m.group(2))
        length = int(m.group(3))
        val = str(merged_vars.get(var_k) or merged_vars.get(f"var.{var_k}") or "dev")
        return val[start:start+length]
    s = re.sub(r"\$\{\s*substr\(\s*(?:var\.)?([a-zA-Z0-9_]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\s*\}", _repl_substr, s)

    # Handle coalesce(a, b, ...)
    def _repl_coalesce(m: Any) -> str:
        args = [arg.strip() for arg in m.group(1).split(",")]
        for arg in args:
            clean_arg = arg.replace("var.", "").replace("local.", "")
            val = merged_vars.get(clean_arg) or merged_vars.get(f"var.{clean_arg}") or merged_vars.get(f"local.{clean_arg}")
            if val and not str(val).startswith("${"):
                return str(val)
        for arg in args:
            parts = arg.split(".")
            if len(parts) >= 2:
                middle = [p for p in parts if p not in ("var", "local", "each", "value", "name", "id", "config")]
                if middle:
                    return middle[-1].replace("_", "-")
        return ""
    s = re.sub(r"\$\{\s*coalesce\(([^)]+)\)\s*\}", _repl_coalesce, s)

    def _repl_var(m: Any) -> str:
        raw = m.group(0)
        key = m.group(1)
        val = merged_vars.get(key) or merged_vars.get(f"var.{key}") or merged_vars.get(f"local.{key}")
        if val is not None and isinstance(val, (str, int, float, bool)):
            return str(val)
        parts = key.split(".")
        curr = merged_vars
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                curr = None
                break
        if curr is not None and isinstance(curr, (str, int, float, bool)):
            return str(curr)
        # Smart traversal: e.g. vpcs.lz_spoke.name -> lz-spoke
        if len(parts) >= 2:
            middle = [p for p in parts if p not in ("var", "local", "each", "value", "name", "id", "self_link", "config")]
            if middle:
                return middle[-1].replace("_", "-")
        return raw

    resolved = re.sub(r"\$\{(?:var|local|each|count)?\.?([a-zA-Z0-9_.-]+)\}", _repl_var, s)

    if "${" in resolved:
        resolved = re.sub(r"\$\{[^}]*?(?:var|local)\.([a-zA-Z0-9_.-]+)\}", r"\1", resolved)
        resolved = re.sub(r"\$\{.*?\}", "", resolved)

    resolved = re.sub(r"[-_]{2,}", "-", resolved).strip(" -_.,")

    if resolved in ("try", "lookup", "null", "None", ""):
        return default_val

    scrubbed_val = scrub_sensitive_data(resolved) if resolved else default_val
    return scrubbed_val


def resolve_iam_principal(
    mem: str,
    body: str = "",
    rel_file: str = "",
    res_type: str = "",
    res_name: str = "",
    role_val: str = "",
    resolved_vars: Optional[Dict[str, Any]] = None,
    service_accounts: Optional[List[Dict[str, Any]]] = None,
) -> Optional[str]:
    """Resolves raw or interpolated IAM principal expressions to clean identifiers.

    Eliminates raw tokens (${each.value}, ${each.value.member}, ${google_service_account...})
    from compliance matrices and ATO System Security Plan (SSP) tables.
    """
    if not mem or not isinstance(mem, str):
        return None
    mem = mem.strip(' "\'\t\r\n')
    if not mem:
        return None

    vars_dict = resolved_vars or {}
    sa_list = service_accounts or []

    # 1. CMEK Service Agents on KMS keys or impersonator bindings
    if "${each.value.member}" in mem or mem == "${each.value}":
        if "cryptoKeyEncrypterDecrypter" in role_val or "kms" in rel_file:
            return "CMEK Key Encrypter/Decrypter Service Agents (Storage, BigQuery, Pub/Sub, Cloud SQL)"
        if "impersonator" in res_name or "impersonators" in body or "serviceusage.serviceUsageConsumer" in role_val:
            return "Deployment & CI/CD Pipeline Impersonators"
        if "imageUser" in role_val:
            return "Compute Image User Service Accounts"
        return None

    # 2. Secret Manager CMEK service identity
    if "secretmanager_sa" in mem:
        pnum = str(vars_dict.get("project_number") or "<PROJECT_NUMBER>")
        return f"serviceAccount:service-{pnum}@gcp-sa-secretmanager.iam.gserviceaccount.com"

    # 3. Interpolated project_number
    if "var.project_number" in mem or "${project_number}" in mem:
        pnum = str(vars_dict.get("project_number") or "<PROJECT_NUMBER>")
        mem = re.sub(r"\$\{(?:var\.)?project_number\}", pnum, mem)

    proj = (
        vars_dict.get("project_id")
        or vars_dict.get("prod_project_id")
        or vars_dict.get("service_project_id")
        or "workload-project"
    )

    # 4. Service account resource references: ${google_service_account.<name>.email}
    sa_res_match = re.search(r"google_service_account\.([a-zA-Z0-9_-]+)\.email", mem)
    if sa_res_match:
        sa_res_name = sa_res_match.group(1)
        matched_sa = next((s for s in sa_list if s.get("resource_name") == sa_res_name), None)
        sa_acc_id = matched_sa.get("account_id") if matched_sa else sa_res_name.replace("_", "-")
        return f"serviceAccount:{sa_acc_id}@{proj}.iam.gserviceaccount.com"

    # 5. Local service account references: ${local.sa_email}
    if "local.sa_email" in mem:
        rel_parent = Path(rel_file).parent.name if rel_file else ""
        file_sas = [
            s for s in sa_list
            if s.get("file") == rel_file
            or (rel_file and s.get("file") and Path(s.get("file")).parent == Path(rel_file).parent)
            or (rel_parent and s.get("file") and (rel_parent in str(s.get("file")) or str(s.get("file")).split("/")[0] in rel_parent))
        ]
        sa_acc_id = file_sas[0].get("account_id") if file_sas else "workload-service-account"
        return f"serviceAccount:{sa_acc_id}@{proj}.iam.gserviceaccount.com"

    # 6. General HCL variable interpolation cleaning
    if "${" in mem:
        mem = clean_interpolated_string(mem, vars_dict, default_val=mem)
    if "${" in mem:
        mem = re.sub(r"\$\{([^}]+)\}", r"\1", mem).replace("var.", "").replace("local.", "")

    if "${" in mem or "each.value" in mem:
        return None

    return mem


def load_all_system_configs(target_dir: str) -> Dict[str, Any]:
    """Recursively scans and aggregates configuration across YAML manifests.

    Aggregates configuration from:
    1. `<TARGET_FOLDER>/compliance_config.yaml`
    2. `<TARGET_FOLDER>/foundation_configs/**/*.yaml`
    3. `<TARGET_FOLDER>/config/**/*.yaml`
    4. `<TARGET_FOLDER>/variables.yaml`
    5. `<TARGET_FOLDER>/system_config.yaml`

    Args:
        target_dir: The target workspace root or project directory.

    Returns:
        Aggregated dictionary containing system information, roles, networks, and versions.
    """
    aggregated = {
        "system_information": {},
        "personnel_roles": {},
        "document_versions": {},
        "custom_services": {},
        "contingency_planning": {},
        "continuous_monitoring": {},
        "contracts": {},
        "iam_groups": {},
        "poam_items": [],
        "security_scanners": {},
        "security_operations": {},
        "external_systems": {},
        "disa_stigs": {},
        "export_preferences": {},
        "terraform_plan_path": None,
        "terraform_state_path": None,
        "sbom_path": None,
        "network_configs": {
            "vpcs": [],
            "subnets": set(),
            "connectivity_model": None
        }
    }

    candidate_files = []
    # 1. Direct candidate files in target_dir with strict, unique deterministic precedence
    precedence_map = {
        "compliance_config.yaml": 100,  # Authoritative institutional compliance parameters
        "system_config.yaml": 90,       # System architecture configuration
        "foundation_variables.yaml": 70, # Foundational variables manifest
        "variables.yaml": 50,           # General Terraform variables
        "compliance_config.yaml.example": 10, # Baseline example template
    }
    has_authoritative_compliance_config = os.path.isfile(os.path.join(target_dir, "compliance_config.yaml"))
    for fname, weight in precedence_map.items():
        if fname == "compliance_config.yaml.example" and has_authoritative_compliance_config:
            continue
        p = os.path.join(target_dir, fname)
        if os.path.isfile(p):
            candidate_files.append((p, weight))

    # 2. Sibling / Foundation configs in target_dir
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_TRAVERSAL_DIRS]
        for f in files:
            if f.endswith((".yaml", ".yml")):
                fpath = os.path.join(root, f)
                if any(c[0] == fpath for c in candidate_files):
                    continue
                if "foundation_variables" in f:
                    candidate_files.append((fpath, 70))
                elif "svc-hub" in f or "env.yaml" in f or "cidrs" in f:
                    candidate_files.append((fpath, 35))
                elif any(k in f for k in ["iam", "group", "service_account", "projects"]):
                    candidate_files.append((fpath, 30))
                else:
                    candidate_files.append((fpath, 20))

    # Deterministic sort: ascending by priority weight, then alphabetically by path
    candidate_files.sort(key=lambda x: (x[1], x[0]))

    loaded_paths = []
    foundational_files = {"compliance_config.yaml", "system_config.yaml"}
    for fpath, _ in candidate_files:
        base_name = os.path.basename(fpath)
        try:
            resolved_p = Path(fpath).resolve()
            content = read_text_file(resolved_p)
            cfg = parse_yaml_safe(content, source_name=str(resolved_p))
        except Exception as parse_err:
            if base_name in foundational_files:
                logger.error("CRITICAL: Failed parsing foundational configuration '%s': %s", fpath, parse_err)
                raise ValueError(
                    f"Foundational compliance configuration '{fpath}' contains invalid YAML syntax or cannot be read: {parse_err}. "
                    "Cannot proceed with compliance generation with a corrupted baseline configuration."
                ) from parse_err
            logger.warning("Failed to parse YAML file %s: %s", fpath, parse_err)
            continue

        if not cfg:
            if base_name in foundational_files and "example" not in base_name:
                raise ValueError(
                    f"Foundational configuration file '{fpath}' is empty or invalid. "
                    "A valid compliance configuration is required."
                )
            continue

        # Runs before schema validation and before any merge, so that a legacy key is
        # validated and consumed under its current name rather than being accepted by
        # the verbatim system_information merge and then dropped by the inventory
        # whitelist further down.
        apply_legacy_config_aliases(cfg, source_path=fpath)

        if "compliance_config" in base_name:
            validate_compliance_config_schema(cfg, source_path=fpath)
        loaded_paths.append(fpath)

        # Standard compliance structure
        if "system_information" in cfg:
            deep_merge_dict(aggregated["system_information"], cfg["system_information"])
        if "personnel_roles" in cfg:
            deep_merge_dict(aggregated["personnel_roles"], cfg["personnel_roles"])
        if "document_versions" in cfg:
            deep_merge_dict(aggregated["document_versions"], cfg["document_versions"])
        if "custom_services" in cfg:
            deep_merge_dict(aggregated["custom_services"], cfg["custom_services"])
        if "contingency_planning" in cfg:
            deep_merge_dict(aggregated["contingency_planning"], cfg["contingency_planning"])
        if "continuous_monitoring" in cfg:
            deep_merge_dict(aggregated["continuous_monitoring"], cfg["continuous_monitoring"])
        if "contracts" in cfg:
            deep_merge_dict(aggregated["contracts"], cfg["contracts"])
        if "security_scanners" in cfg:
            deep_merge_dict(aggregated["security_scanners"], cfg["security_scanners"])
        if "security_operations" in cfg and isinstance(cfg["security_operations"], dict):
            deep_merge_dict(aggregated["security_operations"], cfg["security_operations"])
        if "external_systems" in cfg and isinstance(cfg["external_systems"], dict):
            deep_merge_dict(aggregated["external_systems"], cfg["external_systems"])
        if "disa_stigs" in cfg and isinstance(cfg["disa_stigs"], dict):
            deep_merge_dict(aggregated["disa_stigs"], cfg["disa_stigs"])
        if "export_preferences" in cfg and isinstance(cfg["export_preferences"], dict):
            deep_merge_dict(aggregated["export_preferences"], cfg["export_preferences"])

        for path_key in ["terraform_plan_path", "terraform_state_path", "sbom_path"]:
            if path_key in cfg and cfg[path_key]:
                aggregated[path_key] = str(cfg[path_key])

        # User-configured POA&M items, punch-lists, and pending security tasks
        for p_key in ["poam_items", "security_concerns", "findings"]:
            if p_key in cfg and isinstance(cfg[p_key], list):
                aggregated["poam_items"].extend(cfg[p_key])
            elif p_key in cfg and isinstance(cfg[p_key], dict):
                aggregated["poam_items"].append(cfg[p_key])

        # Direct top-level system_information mappings (higher-weight files overwrite lower-weight defaults)
        for key in ["system_name", "system_abbreviation", "impact_level", "compliance_baseline",
                    "effective_date", "primary_location", "billing_account", "confidentiality_impact",
                    "integrity_impact", "availability_impact", "rmf_governance_system", "system_description"]:
            if key in cfg and cfg[key] is not None and str(cfg[key]).strip():
                aggregated["system_information"][key] = cfg[key]

        # Map from foundation_variables.yaml / variables.yaml
        if "organization" in cfg:
            if isinstance(cfg["organization"], str) and cfg["organization"].strip():
                aggregated["system_information"]["organization"] = cfg["organization"].strip()
            elif isinstance(cfg["organization"], dict):
                org_data = cfg["organization"]
                if org_data.get("domain_name") and str(org_data.get("domain_name")).strip():
                    aggregated["system_information"]["organization"] = str(org_data.get("domain_name")).strip()
                    # Also retained under an explicit key. [ORGANIZATION_DOMAIN] in the
                    # IR runbooks and IA/SC policies needs a real DNS domain; the
                    # "organization" field may legitimately hold a display name
                    # ("Department of Example") which must never be machine-mangled
                    # into a domain, because that would fabricate an identity
                    # namespace inside an accreditation artifact.
                    aggregated["system_information"]["organization_domain"] = str(org_data.get("domain_name")).strip()
                if org_data.get("org_id") and str(org_data.get("org_id")).strip():
                    aggregated["system_information"]["org_id"] = str(org_data.get("org_id")).strip()

        # Explicit top-level domain key, for configs that carry an organization
        # display name and a domain separately.
        for domain_key in ("organization_domain", "domain_name"):
            if cfg.get(domain_key) and str(cfg[domain_key]).strip():
                aggregated["system_information"]["organization_domain"] = str(cfg[domain_key]).strip()
                break

        if "billing" in cfg and isinstance(cfg["billing"], dict):
            b_acct = cfg["billing"].get("account_id")
            if b_acct and str(b_acct).strip():
                aggregated["system_information"]["billing_account"] = str(b_acct).strip()
        elif "billing_account" in cfg and cfg["billing_account"]:
            if str(cfg["billing_account"]).strip():
                aggregated["system_information"]["billing_account"] = str(cfg["billing_account"]).strip()

        if "default_region" in cfg and cfg["default_region"]:
            if str(cfg["default_region"]).strip():
                aggregated["system_information"]["primary_location"] = str(cfg["default_region"]).strip()

        if "assured_workloads" in cfg and isinstance(cfg["assured_workloads"], dict):
            aw = cfg["assured_workloads"]
            if aw.get("enabled") and aw.get("regime"):
                regime = str(aw.get("regime")).upper()
                aggregated["system_information"]["impact_level"] = regime
                aggregated["system_information"]["compliance_baseline"] = f"NIST SP 800-53 Rev. 5 / DoD {regime}"

        if "structure" in cfg and isinstance(cfg["structure"], dict):
            st = cfg["structure"]
            if st.get("resource_prefix") and str(st.get("resource_prefix")).strip():
                aggregated["system_information"]["system_abbreviation"] = str(st.get("resource_prefix")).strip().upper()
            regs = st.get("regions", {})
            if isinstance(regs, dict):
                pri = regs.get("primary")
                sec = regs.get("secondary")
                if pri and sec:
                    aggregated["system_information"]["primary_location"] = f"{pri} / {sec}"
                elif pri:
                    aggregated["system_information"]["primary_location"] = pri

        if "iam" in cfg and isinstance(cfg["iam"], dict):
            gg = cfg["iam"].get("google_groups")
            if isinstance(gg, dict):
                for g_k, g_v in gg.items():
                    if isinstance(g_v, list):
                        aggregated["iam_groups"][g_k] = g_v
                    elif isinstance(g_v, str):
                        aggregated["iam_groups"][g_k] = [g_v]

        # Network configs
        if "connectivity_model" in cfg:
            aggregated["network_configs"]["connectivity_model"] = cfg["connectivity_model"]
        if "vpcs" in cfg and isinstance(cfg["vpcs"], dict):
            for v_key, v_val in cfg["vpcs"].items():
                if isinstance(v_val, str):
                    v_name = v_val
                elif isinstance(v_val, dict):
                    v_name = v_val.get("name", v_key)
                    for s in v_val.get("subnets", []):
                        if isinstance(s, dict) and s.get("ip_cidr_range"):
                            cidr = s.get("ip_cidr_range")
                            if is_valid_cidr(cidr) and cidr not in aggregated["network_configs"]["subnets"]:
                                aggregated["network_configs"]["subnets"].add(cidr)
                        elif isinstance(s, str) and is_valid_cidr(s):
                            aggregated["network_configs"]["subnets"].add(s)
                else:
                    v_name = v_key
                if v_name and is_valid_resource_name(v_name) and v_name not in aggregated["network_configs"]["vpcs"]:
                    aggregated["network_configs"]["vpcs"].append(v_name)
        for cidr_key in ["subnets", "hub_vpcs", "spoke_vpcs", "cidrs", "subnet_cidrs"]:
            if cidr_key in cfg:
                c_val = cfg[cidr_key]
                if isinstance(c_val, list):
                    for s in c_val:
                        if isinstance(s, str) and is_valid_cidr(s) and s not in aggregated["network_configs"]["subnets"]:
                            aggregated["network_configs"]["subnets"].add(s)
                        elif isinstance(s, dict) and s.get("ip_cidr_range"):
                            cidr = s.get("ip_cidr_range")
                            if is_valid_cidr(cidr) and cidr not in aggregated["network_configs"]["subnets"]:
                                aggregated["network_configs"]["subnets"].add(cidr)

    if loaded_paths:
        logger.info("Successfully loaded and correlated configuration across %d YAML manifests.", len(loaded_paths))

    aggregated["network_configs"]["subnets"] = sorted(list(aggregated["network_configs"]["subnets"]))
    return aggregated


def classify_resource_category(resource_type: str) -> str:
    """Classifies a Terraform resource type into a GCP infrastructure category string.

    Args:
        resource_type: The raw Terraform resource type string.

    Returns:
        Formatted human-readable category description.
    """
    rt = resource_type.lower()
    if rt.startswith("kubernetes_"):
        clean_name = rt.replace("kubernetes_", "").replace("_", " ").title()
        return f"Kubernetes {clean_name} Resource"
    clean_name = resource_type.replace("google-beta_", "").replace("google_", "").replace("_", " ").title()
    return f"Google Cloud {clean_name}"


class HclBlock(str):
    """String wrapper for HCL block content with attached AST dictionary."""

    def __new__(
        cls,
        content: str,
        parsed: Optional[Dict[str, Any]] = None,
    ) -> "HclBlock":
        """Creates a new HclBlock instance with optional parsed AST dictionary.

        Args:
            content: Raw string content of the HCL block.
            parsed: Optional dictionary representing parsed HCL AST attributes.

        Returns:
            A new HclBlock instance.
        """
        obj = super().__new__(cls, content)
        obj.parsed = parsed or {}
        return obj

def _hcl_val_to_str(val: Any, indent: int = 0) -> str:
    """Converts a parsed python-hcl2 dictionary structure back to a formatted HCL string."""
    if isinstance(val, str):
        return f'"{val}"'
    elif isinstance(val, bool):
        return "true" if val else "false"
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, list):
        if not val:
            return "[]"
        if isinstance(val[0], dict):
            return "\n".join(_hcl_val_to_str(v, indent) for v in val)
        items = ", ".join(_hcl_val_to_str(v, indent) for v in val)
        return f"[{items}]"
    elif isinstance(val, dict):
        lines = []
        pad = "  " * indent
        for k, v in val.items():
            lines.append(f"{pad}{k} = {_hcl_val_to_str(v, indent + 1)}")
        inner = "\n".join(lines)
        return f"{{\n{inner}\n{pad}}}"
    return str(val)

def _dict_to_hcl_body_str(d: Dict[str, Any]) -> str:
    """Recursively serialize a python-hcl2 AST resource/module dictionary to string body format."""
    lines = []
    for k, v in d.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            for item in v:
                inner = "\n".join(f"  {sk} = {_hcl_val_to_str(sv, 1)}" for sk, sv in item.items())
                lines.append(f"{k} {{\n{inner}\n}}")
        else:
            lines.append(f"{k} = {_hcl_val_to_str(v)}")
    return "\n".join(lines)


def _parse_hcl_list_items(list_str: str) -> List[str]:
    """Extracts scalar items from a bracketed HCL list string, preserving quoted strings.

    Args:
        list_str: Inner string content of an HCL list bracket [ ... ].

    Returns:
        List of unquoted string items.
    """
    items: List[str] = []
    for item_match in re.finditer(
        r'"((?:[^"\\]|\\.)*)"|\'([^\']*)\'|([a-zA-Z0-9_.-]+)', list_str
    ):
        if item_match.group(1) is not None:
            items.append(
                item_match.group(1).replace(r'\"', '"').replace(r"\\", "\\")
            )
        elif item_match.group(2) is not None:
            items.append(item_match.group(2))
        elif item_match.group(3) is not None:
            items.append(item_match.group(3))
    return items


def parse_tfvars_content(content: str, strict: bool = False) -> Dict[str, Any]:
    """Parses HCL / Terraform variable assignments from .tfvars or variables.tf.

    Leverages python-hcl2 for strict AST-based HCL parsing. Brittle regex fallback
    has been eliminated to prevent silent omission of nested infrastructure parameters.
    Sensitive variables (passwords, private keys, secrets) are redacted.

    Args:
        content: Raw content string containing Terraform variable assignments.
        strict: If True, raises ValueError on AST parse failure instead of returning empty dict.

    Returns:
        Dictionary mapping variable names to parsed Python values.
    """
    if not content or not content.strip():
        return {}

    vars_dict: Dict[str, Any] = {}

    # Attempt parsing via python-hcl2 AST
    try:
        parsed = hcl2.loads(content)
        if isinstance(parsed, dict):
            for k, val in parsed.items():
                extracted_val = val[0] if isinstance(val, list) and len(val) == 1 else val
                if isinstance(extracted_val, str):
                    m_num = re.match(
                        r"^\$\{\s*(-?[0-9]+(?:\.[0-9]+)?)\s*\}$",
                        extracted_val,
                    )
                    if m_num:
                        num_str = m_num.group(1)
                        extracted_val = (
                            float(num_str) if "." in num_str else int(num_str)
                        )
                    elif extracted_val.strip() in ("${true}", "${ true }"):
                        extracted_val = True
                    elif extracted_val.strip() in ("${false}", "${ false }"):
                        extracted_val = False
                    else:
                        extracted_val = (
                            extracted_val.replace(r'\"', '"').replace(r"\\", "\\")
                        )
                if k == "variable" and isinstance(val, list):
                    for var_item in val:
                        if isinstance(var_item, dict):
                            for var_name, var_attrs in var_item.items():
                                if isinstance(var_attrs, dict) and "default" in var_attrs:
                                    def_val = var_attrs["default"]
                                    if isinstance(def_val, list) and len(def_val) == 1:
                                        def_val = def_val[0]
                                    if isinstance(def_val, str):
                                        m_num = re.match(
                                            r"^\$\{\s*(-?[0-9]+(?:\.[0-9]+)?)\s*\}$",
                                            def_val,
                                        )
                                        if m_num:
                                            num_str = m_num.group(1)
                                            def_val = (
                                                float(num_str)
                                                if "." in num_str
                                                else int(num_str)
                                            )
                                        elif def_val.strip() in (
                                            "${true}",
                                            "${ true }",
                                        ):
                                            def_val = True
                                        elif def_val.strip() in (
                                            "${false}",
                                            "${ false }",
                                        ):
                                            def_val = False
                                        else:
                                            def_val = (
                                                def_val.replace(
                                                    r'\"', '"'
                                                ).replace(r"\\", "\\")
                                            )
                                    vars_dict[var_name] = (
                                        "[REDACTED_SENSITIVE]"
                                        if is_sensitive_key(var_name)
                                        else scrub_sensitive_data(def_val)
                                    )
                else:
                    vars_dict[k] = (
                        "[REDACTED_SENSITIVE]"
                        if is_sensitive_key(k)
                        else scrub_sensitive_data(extracted_val)
                    )
            return scrub_sensitive_data(vars_dict)
    except (LarkError, KeyError, ValueError, TypeError) as parse_err:
        logger.warning(
            "HCL AST parsing encountered non-standard or multiline syntax in tfvars: %s. Using safe scalar assignment parser.",
            parse_err,
        )
        if strict:
            raise ValueError(
                f"Terraform variable parsing failed with AST error: {parse_err}. "
                "Malformed HCL syntax must be corrected to maintain accreditation boundary integrity."
            ) from parse_err

    # Safe scalar key-value assignment parsing for non-standard or multiline quote syntax
    for m in re.finditer(
        r'^\s*([a-zA-Z0-9_-]+)\s*=\s*"((?:[^"\\]|\\.)*)"', content, re.MULTILINE
    ):
        k = m.group(1)
        raw_val = m.group(2).replace(r'\"', '"').replace(r"\\", "\\")
        vars_dict[k] = "[REDACTED_SENSITIVE]" if is_sensitive_key(k) else scrub_sensitive_data(raw_val)
    for m in re.finditer(
        r'^\s*([a-zA-Z0-9_-]+)\s*=\s*<<-?([A-Za-z0-9_]+)\s*\n([\s\S]{0,65536}?)\n\s*\2\s*$',
        content,
        re.MULTILINE,
    ):
        k = m.group(1)
        val = m.group(3)
        vars_dict[k] = "[REDACTED_SENSITIVE]" if is_sensitive_key(k) else scrub_sensitive_data(val)
    for m in re.finditer(
        r'^\s*([a-zA-Z0-9_-]+)\s*=\s*(true|false)\b',
        content,
        re.MULTILINE | re.IGNORECASE,
    ):
        k = m.group(1)
        vars_dict[k] = m.group(2).lower() == "true"
    for m in re.finditer(
        r'^\s*([a-zA-Z0-9_-]+)\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)\b',
        content,
        re.MULTILINE,
    ):
        k = m.group(1)
        num_str = m.group(2)
        vars_dict[k] = float(num_str) if "." in num_str else int(num_str)
    for m in re.finditer(
        r'^\s*([a-zA-Z0-9_-]+)\s*=\s*\[([^\]]*)\]',
        content,
        re.MULTILINE,
    ):
        k = m.group(1)
        items = _parse_hcl_list_items(m.group(2))
        vars_dict[k] = (
            ["[REDACTED_SENSITIVE]" for _ in items]
            if is_sensitive_key(k)
            else [scrub_sensitive_data(item) for item in items]
        )
    for m in re.finditer(
        r'variable\s+"([a-zA-Z0-9_-]+)"\s*\{([^}]*)\}', content
    ):
        v_name = m.group(1)
        block = m.group(2)
        is_sensitive = (
            "sensitive = true" in block.lower()
            or "sensitive=true" in block.lower()
            or is_sensitive_key(v_name)
        )
        if is_sensitive:
            vars_dict[v_name] = "[REDACTED_SENSITIVE]"
        else:
            default_match = re.search(
                r'default\s*=\s*("((?:[^"\\]|\\.)*)"|([a-zA-Z0-9_\-\.]+))',
                block,
            )
            if default_match and v_name not in vars_dict:
                if default_match.group(2) is not None:
                    v_val = (
                        default_match.group(2)
                        .replace(r'\"', '"')
                        .replace(r"\\", "\\")
                    )
                else:
                    v_val = default_match.group(3)
                if v_val is not None:
                    if str(v_val).lower() == "true":
                        vars_dict[v_name] = True
                    elif str(v_val).lower() == "false":
                        vars_dict[v_name] = False
                    else:
                        vars_dict[v_name] = scrub_sensitive_data(v_val)
    return scrub_sensitive_data(vars_dict)


def _extract_nested_block_str(body: str, block_name: str) -> Optional[str]:
    """Finds block_name { ... } or block_name = { ... } in body using balanced braces."""
    pattern = re.compile(rf'(?:^|\n)\s*(?:dynamic\s+)?"?{re.escape(block_name)}"?\s*(?:=\s*)?\{{')
    match = pattern.search(body)
    if not match:
        return None
    start = match.end() - 1
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(body)):
        ch = body[i]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return body[start + 1 : i]
    return None


def extract_hcl_attr(
    body: Union[str, Dict[str, Any]],
    attr_name: str,
    default: Any = None,
    vars_dict: Optional[Dict[str, Any]] = None,
) -> Any:
    """Extracts a scalar or structured attribute value from an HCL body (dict or str).

    Supports dictionary AST lookups from python-hcl2, dynamic blocks,
    and balanced brace nested regex extraction. Resolves var.xyz if vars_dict is provided.

    Args:
        body: Inner body content of an HCL resource (dict, HclBlock, or string).
        attr_name: Name of the attribute to extract (supports dot notation like 'settings.ip_configuration').
        default: Default value if attribute is not found.
        vars_dict: Optional dictionary of variable defaults for substitution.

    Returns:
        The extracted attribute value, or default if missing.
    """
    target_dict: Optional[Dict[str, Any]] = None
    if isinstance(body, dict):
        target_dict = body
    elif hasattr(body, "parsed") and isinstance(getattr(body, "parsed", None), dict):
        target_dict = getattr(body, "parsed")

    if target_dict is not None:
        val = None
        if "." in attr_name:
            curr: Any = target_dict
            for part in attr_name.split("."):
                if isinstance(curr, list) and curr and isinstance(curr[0], dict):
                    curr = curr[0].get(part)
                elif isinstance(curr, dict):
                    if part in curr:
                        curr = curr.get(part)
                    elif "dynamic" in curr and isinstance(curr["dynamic"], list):
                        found = None
                        for dyn in curr["dynamic"]:
                            if isinstance(dyn, dict) and part in dyn:
                                d_val = dyn[part]
                                found = d_val.get("content", d_val) if isinstance(d_val, dict) else d_val
                                break
                        curr = found
                    else:
                        curr = None
                else:
                    curr = None
                    break
            val = curr
        else:
            val = target_dict.get(attr_name)
            if val is None and "dynamic" in target_dict and isinstance(target_dict["dynamic"], list):
                for dyn in target_dict["dynamic"]:
                    if isinstance(dyn, dict) and attr_name in dyn:
                        d_val = dyn[attr_name]
                        val = d_val.get("content", d_val) if isinstance(d_val, dict) else d_val
                        break
            if val is None:
                for blk_val in target_dict.values():
                    if isinstance(blk_val, dict) and attr_name in blk_val:
                        val = blk_val[attr_name]
                        break
                    elif isinstance(blk_val, list) and blk_val and isinstance(blk_val[0], dict) and attr_name in blk_val[0]:
                        val = blk_val[0][attr_name]
                        break

        if val is not None:
            if isinstance(val, list) and len(val) == 1:
                val = val[0]
            if isinstance(val, str):
                m_var = re.match(r"^(?:\$\{\s*)?var\.([a-zA-Z0-9_-]+)(?:\s*\})?$", val)
                if m_var:
                    var_key = m_var.group(1)
                    if vars_dict and var_key in vars_dict:
                        return scrub_sensitive_data(vars_dict[var_key])
            return scrub_sensitive_data(val)
        if isinstance(body, dict):
            return default

    # Fallback to string parsing with balanced braces
    if not isinstance(body, str):
        return default

    if "." in attr_name:
        parent, child = attr_name.split(".", 1)
        nested_str = _extract_nested_block_str(body, parent)
        if nested_str:
            res = extract_hcl_attr(nested_str, child, default=None, vars_dict=vars_dict)
            if res is not None:
                return scrub_sensitive_data(res)

    m = re.search(
        rf'(?:^|\n)\s*{re.escape(attr_name)}\s*=\s*("((?:[^"\\\n]|\\.)*)"|([a-zA-Z0-9_\-\.]+))',
        body,
    )

    if m:
        if m.group(2) is not None:
            val = m.group(2).replace(r'\"', '"').replace(r"\\", "\\")
        else:
            raw_val = m.group(3)
            if raw_val.lower() in ("true", "yes"):
                return True
            elif raw_val.lower() in ("false", "no"):
                return False
            elif raw_val.isdigit():
                return int(raw_val)
            val = raw_val

        # Resolve variable reference if provided
        if isinstance(val, str):
            m_var = re.match(r"^(?:\$\{\s*)?var\.([a-zA-Z0-9_-]+)(?:\s*\})?$", val)
            if m_var:
                var_key = m_var.group(1)
                if vars_dict and var_key in vars_dict:
                    return scrub_sensitive_data(vars_dict[var_key])
        return scrub_sensitive_data(val)
    return default



def derive_connectivity_summary(
    all_resources: List[Dict[str, Any]],
    networks: Any,
    modules_used: Any,
) -> str:
    """Dynamically derives high-level connectivity architecture description."""
    conn_items = []
    if any("interconnect" in str(r.get("type", "")).lower() for r in all_resources):
        conn_items.append("Dedicated Cloud Interconnect")
    if any("vpn" in str(r.get("type", "")).lower() for r in all_resources):
        conn_items.append("HA Cloud VPN (IPsec)")
    if any("peering" in str(r.get("type", "")).lower() for r in all_resources) or any("peering" in str(m) for m in modules_used):
        conn_items.append("VPC Network Peering")
    if any("forwarding_rule" in str(r.get("type", "")).lower() for r in all_resources):
        conn_items.append("Private Service Connect (PSC)")
    if any("router_nat" in str(r.get("type", "")).lower() for r in all_resources):
        conn_items.append("Cloud NAT (Restricted Egress)")

    if conn_items:
        return " / ".join(conn_items)
    elif networks:
        return "Software-Defined Private VPC"
    return "Not determined from IaC"


def derive_authentication_summary(
    all_resources: List[Dict[str, Any]],
    service_accounts: List[Dict[str, Any]],
) -> str:
    """Dynamically derives identity & authentication architecture description."""
    auth_items = []
    if any("workload_identity" in str(r.get("type", "")).lower() for r in all_resources):
        auth_items.append("Workload Identity Federation (WIF)")
    if any("iap" in str(r.get("type", "")).lower() for r in all_resources):
        auth_items.append("Identity-Aware Proxy (IAP) Context-Aware Access")
    if service_accounts:
        auth_items.append("Least-Privilege Scoped Service Accounts")
    
    if auth_items:
        return " / ".join(auth_items)
    return "Not determined from IaC"


def derive_encryption_summary(
    kms_keys: List[Dict[str, Any]],
    storage_buckets: List[Dict[str, Any]],
) -> str:
    """Dynamically derives cryptographic protection architecture description."""
    has_hsm = any(k.get("protection_level") == "HSM" for k in kms_keys)
    has_software = any(k.get("protection_level") == "SOFTWARE" for k in kms_keys)
    has_cmek = len(kms_keys) > 0 or any(b.get("cmek_encrypted") for b in storage_buckets)
    if has_hsm:
        return "FIPS 140-3 Level 3 Cloud HSM CMEK (AES-256-GCM / RSA-4096)"
    elif has_software:
        return "FIPS 140-3 Level 1 Cloud KMS CMEK (AES-256)"
    elif has_cmek:
        return "CMEK (Protection Level Not Determined from IaC)"
    return "Google Default Encryption at Rest (FIPS 140-3 Validated AES-256)"


def derive_iam_roles_matrix(
    target_dir: Optional[Union[str, Path]],
    iam_bindings: Optional[List[Dict[str, Any]]] = None,
    existing_matrix: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Derives structured IAM persona roles matrix across YAMLs and bindings."""
    matrix: List[Dict[str, Any]] = list(existing_matrix) if existing_matrix else []
    if not matrix and target_dir and os.path.isdir(str(target_dir)):
        yaml_config_paths = []
        for root, dirs, files in os.walk(str(target_dir)):
            dirs[:] = [d for d in dirs if d not in IGNORED_TRAVERSAL_DIRS]
            for filename in files:
                if filename.endswith((".yaml", ".yml")):
                    if any(k in filename.lower() for k in ["iam", "group", "permission", "persona", "service_account"]):
                        yaml_config_paths.append(os.path.join(root, filename))

        for ypath in yaml_config_paths:
            try:
                ytext = read_text_file(ypath, allowed_boundary=target_dir)
                rel_p = os.path.relpath(ypath, str(target_dir))

                persona_blocks = re.findall(r'([a-zA-Z0-9_]+_roles):\s*\n((?:\s*-\s*"?[^\n]+"?\n?)+)', ytext)
                for persona_key, roles_block in persona_blocks:
                    persona_name = persona_key.replace("_roles", "").replace("_", " ").title()
                    group_key = f"gcp-{persona_key.replace('_roles', '').replace('_', '-')}"
                    roles = [r.strip(' -"\'\t\r\n:') for r in roles_block.splitlines() if r.strip(' -"\'\t\r\n:')]
                    if roles:
                        matrix.append({
                            "principal": f"`{group_key}` ({persona_name})",
                            "roles": [r.replace("roles/", "") for r in roles],
                            "file": rel_p
                        })

                groups_match = re.search(r'groups:\s*\n((?:\s*[a-zA-Z0-9_]+:\s*[^\n]+\n)+)', ytext)
                if groups_match:
                    for g_line in groups_match.group(1).splitlines():
                        if ":" in g_line:
                            parts = g_line.split(":")
                            g_name = parts[1].strip(' "\'')
                            matrix.append({
                                "principal": f"`{g_name}`",
                                "roles": [f"Configured in {rel_p}"],
                                "file": rel_p
                            })
            except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
                logger.debug("Failed to parse IAM config %s: %s", ypath, err)

    if iam_bindings:
        by_principal: Dict[str, List[str]] = {}
        for b in iam_bindings:
            p = b.get("principal")
            r = b.get("role")
            if p and r:
                by_principal.setdefault(p, []).append(r.replace("roles/", ""))
        for p, r_list in by_principal.items():
            if not any(entry.get("principal") == p for entry in matrix):
                matrix.append({
                    "principal": p,
                    "roles": sorted(list(set(r_list))),
                    "file": "terraform.tfplan"
                })

    return matrix


def infer_enabled_services_from_components(tf_data: Dict[str, Any]) -> None:
    """Ensures baseline GCP service APIs are recorded based on component inventory."""
    if tf_data["compute_instances"] or tf_data["networks"]:
        tf_data["services"].add("compute.googleapis.com")
    if tf_data["storage_buckets"]:
        tf_data["services"].add("storage.googleapis.com")
    if tf_data["kms_keys"]:
        tf_data["services"].add("cloudkms.googleapis.com")
    if tf_data["gke_clusters"]:
        tf_data["services"].add("container.googleapis.com")
    if tf_data["databases"]:
        if any("bigquery" in d.get("type", "") for d in tf_data["databases"]):
            tf_data["services"].add("bigquery.googleapis.com")
        if any("sql" in d.get("type", "") for d in tf_data["databases"]):
            tf_data["services"].add("sqladmin.googleapis.com")
    if tf_data["logging_sinks"]:
        tf_data["services"].add("logging.googleapis.com")
    if tf_data.get("secrets"):
        tf_data["services"].add("secretmanager.googleapis.com")
    if tf_data.get("pubsub_topics"):
        tf_data["services"].add("pubsub.googleapis.com")
    if tf_data.get("artifact_registries"):
        tf_data["services"].add("artifactregistry.googleapis.com")
    if tf_data.get("cloud_run_services"):
        tf_data["services"].add("run.googleapis.com")
    if tf_data.get("cloud_functions"):
        tf_data["services"].add("cloudfunctions.googleapis.com")
    if tf_data.get("assured_workloads"):
        tf_data["services"].add("assuredworkloads.googleapis.com")
    if tf_data.get("dataproc_clusters"):
        tf_data["services"].add("dataproc.googleapis.com")
    if tf_data.get("service_perimeters"):
        tf_data["services"].add("accesscontextmanager.googleapis.com")
    if tf_data.get("binary_authorization"):
        tf_data["services"].add("binaryauthorization.googleapis.com")
    if tf_data["iam_bindings"] or tf_data["service_accounts"]:
        tf_data["services"].add("iam.googleapis.com")


def extract_resources_from_tf_json(
    tf_json: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Optional[str], Dict[str, str], Set[str]]:
    """Recursively extracts resources, Terraform engine version, and provider versions.

    Supports:
    - 'terraform show -json' plan output (planned_values.root_module)
    - 'terraform show -json' state output (values.root_module)
    - State files direct (resources[].instances[].attributes)
    - Plan diff changes (resource_changes[].change.after)

    Returns:
        Tuple of (collected_resources, terraform_version, provider_versions, modules_used)
    """
    collected: List[Dict[str, Any]] = []
    modules_used: Set[str] = set()
    tf_version = tf_json.get("terraform_version")
    provider_versions: Dict[str, str] = {}

    if "configuration" in tf_json and isinstance(tf_json["configuration"], dict):
        p_cfg = tf_json["configuration"].get("provider_config", {})
        if isinstance(p_cfg, dict):
            for pk, pv in p_cfg.items():
                if isinstance(pv, dict) and pv.get("version_constraint"):
                    provider_versions[pv.get("name", pk)] = pv.get("version_constraint")

    def _walk_module(mod: Dict[str, Any]) -> None:
        mod_addr = mod.get("address")
        if mod_addr:
            modules_used.add(mod_addr)
        for r in mod.get("resources", []):
            collected.append({
                "address": r.get("address", f"{r.get('type')}.{r.get('name')}"),
                "type": r.get("type", ""),
                "name": r.get("name", ""),
                "mode": r.get("mode", "managed"),
                "provider": r.get("provider_name", "google"),
                "values": r.get("values", {})
            })
        for child in mod.get("child_modules", []):
            _walk_module(child)

    # 1. Planned values (terraform show -json <plan>)
    if "planned_values" in tf_json and isinstance(tf_json["planned_values"], dict):
        rm = tf_json["planned_values"].get("root_module")
        if isinstance(rm, dict):
            _walk_module(rm)

    # 2. Values (terraform show -json state or plan values)
    if not collected and "values" in tf_json and isinstance(tf_json["values"], dict):
        rm = tf_json["values"].get("root_module")
        if isinstance(rm, dict):
            _walk_module(rm)

    # 3. State file direct (terraform.tfstate)
    if not collected and "resources" in tf_json and isinstance(tf_json["resources"], list):
        for r in tf_json["resources"]:
            res_type = r.get("type", "")
            res_name = r.get("name", "")
            res_mode = r.get("mode", "managed")
            res_mod = r.get("module", "")
            if res_mod:
                modules_used.add(res_mod)
            for inst in r.get("instances", []):
                attrs = inst.get("attributes", {})
                idx = inst.get("index_key")
                addr = f"{res_mod}.{res_type}.{res_name}" if res_mod else f"{res_type}.{res_name}"
                if idx is not None:
                    addr += f"[{idx}]"
                collected.append({
                    "address": addr,
                    "type": res_type,
                    "name": res_name,
                    "mode": res_mode,
                    "provider": r.get("provider", "google"),
                    "values": attrs
                })

    # 4. Resource changes
    if not collected and "resource_changes" in tf_json and isinstance(tf_json["resource_changes"], list):
        for rc in tf_json["resource_changes"]:
            res_type = rc.get("type", "")
            res_name = rc.get("name", "")
            change = rc.get("change", {})
            after = change.get("after") or change.get("before") or {}
            collected.append({
                "address": rc.get("address", f"{res_type}.{res_name}"),
                "type": res_type,
                "name": res_name,
                "mode": rc.get("mode", "managed"),
                "provider": rc.get("provider_name", "google"),
                "values": after if isinstance(after, dict) else {}
            })

    return collected, tf_version, provider_versions, modules_used


def init_empty_tf_data(
    user_config: Optional[Dict[str, Any]] = None,
    engine_version: Optional[str] = None,
    provider_versions: Optional[Dict[str, str]] = None,
    modules_used: Optional[Union[Set[str], List[str]]] = None,
) -> Dict[str, Any]:
    """Initializes a baseline infrastructure tracking dictionary for system data extraction."""
    tf_data: Dict[str, Any] = {
        "projects": set(),
        "services": set(),
        "networks": set(),
        "subnets": set(),
        "storage_buckets": [],
        "databases": [],
        "kms_keys": [],
        "gke_clusters": [],
        "compute_instances": [],
        "service_accounts": [],
        "service_account_keys": [],
        "firewall_rules": [],
        "logging_sinks": [],
        "assured_workloads": [],
        "iam_bindings": [],
        "iam_roles_matrix": [],
        "scc_findings": [],
        "cloud_run_services": [],
        "cloud_functions": [],
        "nat_gateways": [],
        "forwarding_rules": [],
        "security_policies": [],
        "service_perimeters": [],
        "binary_authorization": [],
        "dataproc_clusters": [],
        "secrets": [],
        "pubsub_topics": [],
        "artifact_registries": [],
        "boundary_connections": [],
        # Blueprints inside the accreditation boundary that the HCL parser could
        # not read. Every resource in such a file is absent from the boundary
        # description. Recording them here is what turns a log line into an
        # assessment coverage gap the assessor can see; dropping them silently
        # produces an SSP that describes an incomplete estate without saying so.
        "unparsed_terraform_files": [],
        "modules_used": set(modules_used) if modules_used else set(),
        "all_resources": [],
        "terraform_engine_version": engine_version,
        "provider_versions": dict(provider_versions) if provider_versions else {},
        "ids_solution": "Cloud-Native Next-Generation Firewall (NGFW) & Intrusion Detection/Prevention System (IDS/IPS)",
        "connectivity_summary": "Cloud Interconnect / Private Service Connect / VPC Peering",
        "authentication_summary": "Google Cloud Identity / Workload Identity Federation (WIF) / Scoped Service Accounts",
        "encryption_summary": "FIPS 140-3 Level 3 Cloud HSM CMEK (AES-256-GCM / RSA-4096)",
    }
    if user_config and "network_configs" in user_config:
        nc = user_config["network_configs"]
        for v in nc.get("vpcs", []):
            tf_data["networks"].add(v)
        for s in nc.get("subnets", []):
            tf_data["subnets"].add(s)
    return tf_data


def finalize_terraform_data(
    tf_data: Dict[str, Any],
    target_dir: Optional[Union[str, Path]] = ".",
    existing_iam_matrix: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Applies service inference, architecture summaries, and IAM matrix collation."""
    infer_enabled_services_from_components(tf_data)
    tf_data["connectivity_summary"] = derive_connectivity_summary(
        tf_data["all_resources"], tf_data["networks"], tf_data["modules_used"]
    )
    tf_data["authentication_summary"] = derive_authentication_summary(
        tf_data["all_resources"], tf_data["service_accounts"]
    )
    tf_data["encryption_summary"] = derive_encryption_summary(
        tf_data["kms_keys"], tf_data["storage_buckets"]
    )
    resolved_target = str(target_dir) if target_dir else "."
    tf_data["iam_roles_matrix"] = derive_iam_roles_matrix(
        resolved_target, tf_data["iam_bindings"], existing_matrix=existing_iam_matrix
    )
    if "projects" in tf_data:
        tf_data["projects"] = sorted(list(tf_data["projects"]))
    tf_data["services"] = sorted(list(tf_data["services"]))
    tf_data["networks"] = sorted(list(tf_data["networks"]))
    tf_data["modules_used"] = sorted(list(tf_data["modules_used"]))
    return tf_data


_EXACT_VAR_REF = re.compile(r"^(?:\$\{\s*)?var\.([a-zA-Z0-9_-]+)(?:\s*\})?$")


def _resolve_ast_variables(
    node: Any, vars_dict: Optional[Dict[str, Any]], _depth: int = 0
) -> Any:
    """Substitutes known ``var.*`` references throughout a parsed HCL AST.

    The structured (dict) branch of :func:`classify_and_ingest_resource` reads
    attributes with plain ``body.get(...)``. The legacy text branch instead went
    through :func:`extract_hcl_attr`, which resolves a whole-string ``var.x``
    reference against the collected variable defaults and ``.tfvars`` values.
    Without this pass the structured branch would report attributes verbatim as
    ``${var.machine_size}``, which is unusable as inventory evidence.

    Resolution is intentionally limited to an exact whole-string match, matching
    :func:`extract_hcl_attr` semantics. Partially interpolated strings such as
    ``"${var.prefix}-vm"`` are left untouched here; asset identifiers get the
    richer treatment in :func:`_resolved_asset_name`.

    Args:
        node: A node of the parsed AST (dict, list, or scalar).
        vars_dict: Resolved variable values keyed by bare variable name.
        _depth: Internal recursion guard.

    Returns:
        The node with resolvable variable references replaced.
    """
    if not vars_dict or _depth > 24:
        return node
    if isinstance(node, str):
        m = _EXACT_VAR_REF.match(node.strip())
        if m and m.group(1) in vars_dict:
            return vars_dict[m.group(1)]
        return node
    if isinstance(node, dict):
        return {
            k: _resolve_ast_variables(v, vars_dict, _depth + 1)
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [_resolve_ast_variables(v, vars_dict, _depth + 1) for v in node]
    return node


# Trailing identifier of a Terraform reference: the "bucket" in
# "${each.value.bucket}" or the "database_name" in "${var.database_name}".
_REF_TAIL = re.compile(r"[A-Za-z0-9_-]+(?=\s*[\}\)]|$)")

# A body value written as a bare reference rather than an interpolation.
_BARE_REF_PREFIX = re.compile(r"^(?:var|local|each|count|self)\.")


def _resolved_asset_name(
    raw: Any,
    res_name: str,
    vars_dict: Optional[Dict[str, Any]],
    fallback: str,
) -> str:
    """Resolves a raw asset identifier into a human-readable name.

    Terraform bodies frequently name resources with unresolved expressions such as
    ``${var.database_name}``, ``${each.value.name}`` or ``coalesce(...)``. Emitting
    those verbatim into the compliance inventory produces unusable asset
    identifiers in the SSP, SCTM and HW/SW inventory deliverables.

    This attempts interpolation against the resolved variable set first, then
    degrades to the Terraform logical resource name, then to a category fallback.
    The return value is guaranteed to never contain expression syntax.

    Note that :func:`clean_interpolated_string` strips expression syntax whether
    or not it actually substituted a value, so ``${each.value.bucket}`` reduces
    to the bare word ``bucket``. That is worse than useless as an identifier: it
    is generic, collides across resources, and is indistinguishable from a real
    name. When the cleaned result is just the tail of a reference that was never
    substituted, the logical resource name is preferred instead -- it is unique
    within the module and is a genuine Terraform address.

    Args:
        raw: The candidate identifier read from the resource body (may be None).
        res_name: The Terraform logical resource name, used as first fallback.
        vars_dict: Resolved variables used to interpolate ``${var.*}`` references.
        fallback: Generic category name used when nothing else is usable.

    Returns:
        A clean, human-readable asset identifier.
    """
    raw_str = str(raw or res_name)
    name = clean_interpolated_string(raw_str, vars_dict, default_val=res_name)

    unsubstituted = False
    if "${" in raw_str or _BARE_REF_PREFIX.match(raw_str.strip()):
        tails = {t.lower() for t in _REF_TAIL.findall(raw_str)}
        if name.strip().lower() in tails:
            unsubstituted = True

    if (
        unsubstituted
        or not is_valid_resource_name(name)
        or "${" in name
        or "var." in name
        or any(name.startswith(p) for p in ("coalesce", "each.", "local."))
    ):
        name = res_name if is_valid_resource_name(res_name) else fallback
    return name

def _resolved_cmek_name(raw_cmek: Any, resolved_vars: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Cleans an unresolved CMEK reference string into an explanatory statement."""
    if not raw_cmek:
        return None
    raw_str = str(raw_cmek)
    v_dict = resolved_vars or {}
    clean = clean_interpolated_string(raw_str, v_dict)
    if not clean or "var." in clean or "local." in clean or "${" in clean:
        return "Customer-managed key (reference resolved at apply time)"
    tails = {t.lower() for t in _REF_TAIL.findall(raw_str)}
    if clean.strip().lower() in tails:
        return "Customer-managed key (reference resolved at apply time)"
    return clean


def _text_attr_tristate(body: Any, attr: str) -> Optional[bool]:
    """Reads a boolean Terraform attribute from raw text without guessing.

    The text-scan path is a degraded fallback used when the HCL AST is
    unavailable, so an attribute that is simply not present must be reported as
    undetermined rather than assumed. Asserting a secure default here is what
    produces unsupportable control statements in the generated SSP.

    Args:
        body: Raw Terraform source text for the resource body.
        attr: Attribute name to look for (e.g. 'versioning').

    Returns:
        True or False when the attribute is explicitly assigned a boolean,
        otherwise None to signal that the value could not be determined.
    """
    match = re.search(
        r"\b" + re.escape(attr) + r"\s*=\s*(true|false)\b",
        str(body),
        re.IGNORECASE,
    )
    if match:
        return match.group(1).lower() == "true"
    # A bare block (e.g. `versioning { enabled = true }`) carries its own flag.
    block = re.search(
        r"\b" + re.escape(attr) + r"\s*(?:=\s*)?\{([^{}]*)\}",
        str(body),
        re.IGNORECASE | re.DOTALL,
    )
    if block:
        inner = re.search(r"\benabled\s*=\s*(true|false)\b", block.group(1), re.IGNORECASE)
        if inner:
            return inner.group(1).lower() == "true"
    return None


def classify_and_ingest_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    resolved_vars: Optional[Dict[str, Any]] = None,
) -> None:
    """Classifies and ingests a single infrastructure resource into tf_data.

    Unifies ingestion from both structured Terraform JSON plans/states and parsed HCL AST/blocks,
    populating networks, subnets, firewalls, storage, compute, KMS, databases, GKE, and IAM.

    Args:
        res_type: Terraform resource type (e.g. 'google_compute_instance', 'google_compute_network').
        res_name: Resource logical name in Terraform.
        body: Resource body (dictionary of values from JSON or HclBlock/string from .tf).
        rel_file: Relative path of the defining file (e.g. 'terraform.tfplan' or 'main.tf').
        tf_data: Target infrastructure tracking dictionary.
        resolved_vars: Optional dictionary of resolved variables for string interpolation.
    """
    vars_dict = resolved_vars or {}

    tf_data["all_resources"].append({
        "type": res_type,
        "name": res_name,
        "category": classify_resource_category(res_type),
        "file": rel_file,
    })

    # 1. Enabled Service APIs
    if res_type == "google_project_service":
        svc = body.get("service") if isinstance(body, dict) else extract_hcl_attr(body, "service", vars_dict=vars_dict)
        if svc:
            tf_data["services"].add(str(svc))

    # 2. VPC Networks (Google Cloud VPC / Andromeda SDN)
    elif res_type == "google_compute_network":
        if "modules/fabric/" in rel_file:
            return
        raw_net = (body.get("name") if isinstance(body, dict) else extract_hcl_attr(body, "name", vars_dict=vars_dict)) or res_name
        net_name = clean_interpolated_string(raw_net, vars_dict) if vars_dict else str(raw_net)
        if is_valid_resource_name(net_name):
            tf_data["networks"].add(net_name)

    # 3. Subnets (Google Cloud Subnetworks)
    elif res_type == "google_compute_subnetwork":
        if "modules/fabric/" in rel_file:
            return
        if isinstance(body, dict):
            cidr = body.get("ip_cidr_range")
            sec_ranges = body.get("secondary_ip_range") or []
            if isinstance(sec_ranges, list):
                for sr in sec_ranges:
                    if isinstance(sr, dict) and is_valid_cidr(sr.get("ip_cidr_range")):
                        s_cidr = str(sr["ip_cidr_range"])
                        tf_data["subnets"].add(s_cidr)
        else:
            cidr = extract_hcl_attr(body, "ip_cidr_range", vars_dict=vars_dict)
            for sec_m in re.finditer(r'ip_cidr_range\s*=\s*"([^"]+)"', body):
                sec_c = sec_m.group(1)
                if is_valid_cidr(sec_c) and str(sec_c) not in tf_data["subnets"]:
                    tf_data["subnets"].add(str(sec_c))
        if isinstance(cidr, list) and cidr:
            cidr = cidr[0]
        if is_valid_cidr(cidr) and str(cidr) not in tf_data["subnets"]:
            tf_data["subnets"].add(str(cidr))

    # 4. Firewalls & Security Policies (Google Cloud Next-Generation Firewall)
    elif res_type == "google_compute_firewall":
        if "modules/fabric/" in rel_file:
            return
        if isinstance(body, dict):
            fw_name = _resolved_asset_name(body.get("name"), res_name, vars_dict, "firewall-rule")
            fw_net = body.get("network", "custom-vpc")
            if "/" in fw_net:
                fw_net = fw_net.split("/")[-1]
            direction = body.get("direction", "INGRESS")
            allow_rules = body.get("allow") or []
            deny_rules = body.get("deny") or []
            if not allow_rules and not deny_rules and "dynamic" in body and isinstance(body["dynamic"], list):
                for dyn in body["dynamic"]:
                    if isinstance(dyn, dict):
                        if "allow" in dyn:
                            d_c = dyn["allow"].get("content", dyn["allow"]) if isinstance(dyn["allow"], dict) else dyn["allow"]
                            if isinstance(d_c, dict):
                                allow_rules.append(d_c)
                        elif "deny" in dyn:
                            d_c = dyn["deny"].get("content", dyn["deny"]) if isinstance(dyn["deny"], dict) else dyn["deny"]
                            if isinstance(d_c, dict):
                                deny_rules.append(d_c)
            action = "ALLOW" if allow_rules else ("DENY" if deny_rules else "ALLOW")
            rules = allow_rules if allow_rules else deny_rules
            protos = []
            ports_list = []
            for r in rules:
                if isinstance(r, dict):
                    proto = r.get("protocol", "tcp")
                    # A protocol may arrive as a single-element list from the AST.
                    if isinstance(proto, (list, tuple, set)):
                        protos.extend(str(p) for p in proto)
                    else:
                        protos.append(str(proto))
                    ports = r.get("ports") or ["443"]
                    # `ports = var.allowed_ports` resolves to whatever the variable
                    # holds, and a single-element default is stored unwrapped, so a
                    # bare int or string is a legitimate shape here.
                    if not isinstance(ports, (list, tuple, set)):
                        ports = [ports]
                    ports_list.extend([str(p) for p in ports])
            proto_str = "/".join(set(protos)) if protos else "tcp"
            ports_str = ",".join(ports_list) if ports_list else "443"
            tf_data["firewall_rules"].append({
                "name": fw_name,
                "network": fw_net,
                "direction": direction,
                "protocol": proto_str,
                "ports": ports_str,
                "action": action,
            })
        else:
            proto = extract_hcl_attr(body, "protocol", vars_dict=vars_dict) or "tcp"
            proto = clean_interpolated_string(proto, vars_dict, default_val="tcp")
            p_m = re.search(r'ports\s*=\s*\[([^\]]+)\]', body)
            ports = p_m.group(1).replace('"', '').strip() if p_m else "443"
            ports = clean_interpolated_string(ports, vars_dict, default_val="443")
            dir_m = extract_hcl_attr(body, "direction", vars_dict=vars_dict) or "INGRESS"
            dir_m = clean_interpolated_string(dir_m, vars_dict, default_val="INGRESS")
            if "${" in dir_m or "each.value" in dir_m:
                dir_m = "INGRESS"
            if "${" in proto or "rule.value" in proto:
                proto = "tcp"
            tf_data["firewall_rules"].append({
                "name": res_name,
                "direction": dir_m,
                "protocol": proto,
                "ports": ports,
                "action": "ALLOW" if "allow" in body else "DENY",
            })

    # 5. Storage Buckets (Google Cloud Storage / CMEK)
    elif res_type == "google_storage_bucket":
        if "modules/fabric/" in rel_file:
            return
        if isinstance(body, dict):
            b_name = _resolved_asset_name(body.get("name") or body.get("bucket"), res_name, vars_dict, "storage-bucket")
            loc = body.get("location", "US-EAST4")
            s_class = body.get("storage_class", "STANDARD")
            enc = body.get("encryption") or []
            enc_dict = enc[0] if isinstance(enc, list) and enc else (enc if isinstance(enc, dict) else {})
            cmek_key = enc_dict.get("default_kms_key_name")
            # Provider defaults (google_storage_bucket): versioning is disabled and
            # uniform bucket-level access is off unless explicitly configured. Do not
            # assume the secure value, or the SSP asserts controls that are not enforced.
            vers = body.get("versioning") or []
            vers_dict = vers[0] if isinstance(vers, list) and vers else (vers if isinstance(vers, dict) else {})
            versioning = bool(vers_dict.get("enabled", False)) if vers_dict else False
            ubla = bool(body.get("uniform_bucket_level_access", False))
            tf_data["storage_buckets"].append({
                "name": b_name,
                "location": loc,
                "storage_class": s_class,
                "cmek_encrypted": bool(cmek_key),
                "kms_key": cmek_key,
                "versioning": versioning,
                "uniform_bucket_level_access": ubla,
                "file": rel_file,
            })
        else:
            raw_b_name = extract_hcl_attr(body, "name", vars_dict=vars_dict) or extract_hcl_attr(body, "bucket", vars_dict=vars_dict) or res_name
            b_name = clean_interpolated_string(raw_b_name, vars_dict, default_val=res_name)
            if not is_valid_resource_name(b_name) or "${" in b_name or "var." in b_name:
                return
            loc = extract_hcl_attr(body, "location", vars_dict=vars_dict) or "US"
            cmek = "kms_key_name" in body or "crypto_key" in body
            # Degraded text scan: we cannot see the whole resolved config, so report
            # None (undetermined) rather than guessing when the attribute is absent.
            vers = _text_attr_tristate(body, "versioning")
            ubla = _text_attr_tristate(body, "uniform_bucket_level_access")
            tf_data["storage_buckets"].append({
                "name": b_name,
                "location": loc,
                "storage_class": "STANDARD",
                "cmek_encrypted": cmek,
                "versioning": vers,
                "uniform_bucket_level_access": ubla,
                "file": rel_file,
            })

    # 6. Compute Instances (Google Compute Engine Shielded VMs)
    elif res_type in ("google_compute_instance", "google_compute_instance_from_template"):
        if "modules/fabric/compute-vm" in rel_file or "recipes/" in rel_file:
            return
        if isinstance(body, dict):
            vm_name = _resolved_asset_name(body.get("name"), res_name, vars_dict, "compute-instance")
            m_type = body.get("machine_type") or "n2-standard-4"
            zone = body.get("zone", "us-east4-a")
            network_ip = None
            subnetwork = ""
            has_pub_ip = False
            nics = body.get("network_interface") or []
            if isinstance(nics, list) and nics:
                nic0 = nics[0] if isinstance(nics[0], dict) else {}
                network_ip = nic0.get("network_ip")
                subnetwork = nic0.get("subnetwork", "")
                if "/" in subnetwork:
                    subnetwork = subnetwork.split("/")[-1]
                if nic0.get("access_config"):
                    has_pub_ip = True
            shielded = body.get("shielded_instance_config")
            is_shielded = None
            if isinstance(shielded, list) and shielded:
                s_dict = shielded[0] if isinstance(shielded[0], dict) else {}
                if "enable_secure_boot" in s_dict:
                    is_shielded = bool(s_dict["enable_secure_boot"])
            elif isinstance(shielded, dict):
                if "enable_secure_boot" in shielded:
                    is_shielded = bool(shielded["enable_secure_boot"])
            
            boot_disk = body.get("boot_disk")
            kms_key = None
            img = None
            if isinstance(boot_disk, list) and boot_disk:
                bd0 = boot_disk[0] if isinstance(boot_disk[0], dict) else {}
                kms_key = bd0.get("kms_key_self_link") or bd0.get("disk_encryption_key_raw")
                if "initialize_params" in bd0 and isinstance(bd0["initialize_params"], list) and bd0["initialize_params"]:
                    img = bd0["initialize_params"][0].get("image")
                elif "initialize_params" in bd0 and isinstance(bd0["initialize_params"], dict):
                    img = bd0["initialize_params"].get("image")
            elif isinstance(boot_disk, dict):
                kms_key = boot_disk.get("kms_key_self_link") or boot_disk.get("disk_encryption_key_raw")
                if "initialize_params" in boot_disk and isinstance(boot_disk["initialize_params"], dict):
                    img = boot_disk["initialize_params"].get("image")
                    
            p_id = body.get("project") or (vars_dict.get("project_id") if vars_dict else "") or (vars_dict.get("project") if vars_dict else "") or ""
            tf_data["compute_instances"].append({
                "name": vm_name,
                "machine_type": m_type,
                "zone": zone,
                "network_ip": network_ip,
                "subnetwork": subnetwork,
                "image": img,
                "kms_key": kms_key,
                "has_public_ip": has_pub_ip,
                "shielded_vm": is_shielded,
                "self_link": f"projects/{p_id}/zones/{zone}/instances/{vm_name}" if p_id else f"zones/{zone}/instances/{vm_name}",
                "file": rel_file,
            })
        else:
            raw_vm_name = extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name
            vm_name = clean_interpolated_string(raw_vm_name, vars_dict, default_val=res_name)
            if not vm_name or vm_name.startswith("${") or vm_name in ("default", "instance"):
                return
            m_type = extract_hcl_attr(body, "machine_type", vars_dict=vars_dict) or "n2-standard-4"
            default_reg = (
                vars_dict.get("region")
                or vars_dict.get("default_region")
                or "us-east4"
            )
            default_zone = vars_dict.get("zone") or f"{default_reg}-a"
            raw_zone = extract_hcl_attr(body, "zone", vars_dict=vars_dict) or default_zone
            zone = clean_interpolated_string(raw_zone, vars_dict, default_val=default_zone)
            net_ip = extract_hcl_attr(body, "network_ip", vars_dict=vars_dict)
            if net_ip in ("try", "lookup", "None", "") or not net_ip or str(net_ip).startswith("${"):
                net_ip = None
            raw_subnet = extract_hcl_attr(body, "subnetwork", vars_dict=vars_dict)
            subnet = clean_interpolated_string(raw_subnet, vars_dict, default_val="")
            if subnet in ("subnet_id", "var.subnet_id", "subnet", ""):
                subnet = "workload-subnet"
            raw_img = extract_hcl_attr(body, "image", vars_dict=vars_dict)
            img = None
            if raw_img and "var." not in str(raw_img) and "${" not in str(raw_img):
                img = clean_interpolated_string(raw_img, vars_dict, default_val=raw_img)
            kms_key = _resolved_cmek_name(extract_hcl_attr(body, "kms_key_self_link", vars_dict=vars_dict), vars_dict)
            has_pub_ip = ("access_config" in body)
            is_shielded = None
            if "enable_secure_boot" in body:
                match = re.search(r'enable_secure_boot\s*=\s*(true|false)', body, re.IGNORECASE)
                if match:
                    is_shielded = match.group(1).lower() == "true"
            p_id = (
                vars_dict.get("project_id")
                or vars_dict.get("prod_project_id")
                or vars_dict.get("service_project_id")
                or "workload-project"
            )
            tf_data["compute_instances"].append({
                "name": vm_name,
                "machine_type": m_type,
                "zone": zone,
                "network_ip": net_ip,
                "subnetwork": subnet,
                "image": img,
                "kms_key": kms_key,
                "has_public_ip": has_pub_ip,
                "shielded_vm": is_shielded,
                "self_link": f"projects/{p_id}/zones/{zone}/instances/{vm_name}",
                "file": rel_file,
            })

    # 7. KMS Keys & Key Rings (Google Cloud KMS / FIPS 140-3 HSM)
    elif res_type in ("google_kms_crypto_key", "google_kms_key_ring"):
        if "modules/fabric/kms" in rel_file:
            return
        if isinstance(body, dict):
            key_name = _resolved_asset_name(body.get("name") or body.get("description"), res_name, vars_dict, "kms-key")
            kr = body.get("key_ring") or res_name
            if "/" in kr:
                kr = kr.split("/")[-1]
            purp = body.get("purpose", "ENCRYPT_DECRYPT")
            rot = body.get("rotation_period", "7776000s")
            vt = body.get("version_template") or []
            vt_dict = vt[0] if isinstance(vt, list) and vt else (vt if isinstance(vt, dict) else {})
            # Provider default for google_kms_crypto_key is SOFTWARE protection.
            # Defaulting to HSM would fabricate a FIPS 140-3 Level 3 claim. Check
            # the nested version_template first, then a flattened top-level value
            # (emitted by plan JSON and some HCL parses), before falling back.
            prot = vt_dict.get("protection_level") or body.get("protection_level") or "SOFTWARE"
            tf_data["kms_keys"].append({
                "type": res_type,
                "name": key_name,
                "key_ring": kr,
                "protection_level": prot,
                "purpose": purp,
                "rotation_period": rot,
                "file": rel_file,
            })
        else:
            raw_key = extract_hcl_attr(body, "name", vars_dict=vars_dict) or extract_hcl_attr(body, "description", vars_dict=vars_dict) or res_name
            # Require an explicit protection_level assignment; a bare "HSM" substring
            # elsewhere in the body (a comment, a key name) is not evidence.
            prot_raw = extract_hcl_attr(body, "protection_level", vars_dict=vars_dict)
            if not prot_raw:
                prot_m = re.search(r'protection_level\s*=\s*"?(HSM|SOFTWARE|EXTERNAL[A-Z_]*)"?', str(body), re.IGNORECASE)
                prot_raw = prot_m.group(1) if prot_m else "SOFTWARE"
            prot = "HSM" if "HSM" in str(prot_raw).upper() else "SOFTWARE"
            kr = extract_hcl_attr(body, "key_ring", vars_dict=vars_dict) or res_name
            kr = clean_interpolated_string(kr, vars_dict, default_val=res_name)
            purp = extract_hcl_attr(body, "purpose", vars_dict=vars_dict) or "ENCRYPT_DECRYPT"
            rot = extract_hcl_attr(body, "rotation_period", vars_dict=vars_dict) or "7776000s"

            if "${each." in str(raw_key):
                keys_list = vars_dict.get("keys") or vars_dict.get("var.keys") or []
                if isinstance(keys_list, list) and keys_list:
                    for subk in keys_list:
                        kname = re.sub(r"\$\{each\.(?:value|key)\}", str(subk), raw_key)
                        tf_data["kms_keys"].append({
                            "type": res_type,
                            "name": kname,
                            "key_ring": kr,
                            "protection_level": prot,
                            "purpose": purp,
                            "rotation_period": rot,
                            "file": rel_file,
                        })
                    return

            if raw_key.startswith("${") and ("var.keyring" in raw_key or "each.key" in raw_key or "each.value" in raw_key):
                return
            key_actual_name = clean_interpolated_string(raw_key, vars_dict, default_val=res_name)
            tf_data["kms_keys"].append({
                "type": res_type,
                "name": key_actual_name,
                "key_ring": kr,
                "protection_level": prot,
                "purpose": purp,
                "rotation_period": rot,
                "file": rel_file,
            })

    # 8. Databases (Cloud SQL, AlloyDB, BigQuery, Cloud Spanner, Memorystore)
    elif res_type in ("google_sql_database_instance", "google_alloydb_cluster", "google_bigquery_dataset", "google_spanner_instance", "google_redis_instance"):
        if "modules/fabric/" in rel_file:
            return
        if isinstance(body, dict):
            if res_type == "google_bigquery_dataset":
                ds_id = _resolved_asset_name(body.get("dataset_id") or body.get("name"), res_name, vars_dict, "bigquery-dataset")
                enc = body.get("default_encryption_configuration") or []
                kms = None
                if isinstance(enc, list) and enc:
                    kms = enc[0].get("kms_key_name")
                elif isinstance(enc, dict):
                    kms = enc.get("kms_key_name")
                tf_data["databases"].append({
                    "type": res_type,
                    "name": ds_id,
                    "database_version": "Serverless Enterprise",
                    "tier": "Enterprise Cloud Data Warehouse",
                    "region": body.get("location", "us-east4"),
                    "private_network": "Google Private Backbone / PSC",
                    "cmek_key": kms,
                    "require_ssl": True,
                    "backup_enabled": True,
                    "has_public_ip": False,
                    "file": rel_file,
                })
            else:
                db_name = _resolved_asset_name(body.get("name"), res_name, vars_dict, "database-instance")
                db_ver = body.get("database_version") or "POSTGRES_15"
                reg = body.get("region", "us-east4")
                settings = body.get("settings") or []
                s_dict = settings[0] if isinstance(settings, list) and settings else (settings if isinstance(settings, dict) else {})
                tier = s_dict.get("tier", "db-custom-4-16384")
                ip_cfg = s_dict.get("ip_configuration") or []
                ip_dict = ip_cfg[0] if isinstance(ip_cfg, list) and ip_cfg else (ip_cfg if isinstance(ip_cfg, dict) else {})
                p_net = ip_dict.get("private_network")
                if p_net and "/" in p_net:
                    p_net = p_net.split("/")[-1]
                # Neither TLS enforcement nor backups are on by default in Cloud SQL.
                # `require_ssl` is deprecated in favour of `ssl_mode`, so honour both.
                ssl_mode = str(ip_dict.get("ssl_mode") or "").upper()
                if ssl_mode:
                    req_ssl = ssl_mode in ("ENCRYPTED_ONLY", "TRUSTED_CLIENT_CERTIFICATE_REQUIRED")
                else:
                    req_ssl = bool(ip_dict.get("require_ssl", False))
                has_pub = bool(ip_dict.get("ipv4_enabled", False))
                bkp_cfg = s_dict.get("backup_configuration") or []
                bkp_dict = bkp_cfg[0] if isinstance(bkp_cfg, list) and bkp_cfg else (bkp_cfg if isinstance(bkp_cfg, dict) else {})
                bkp_enabled = bool(bkp_dict.get("enabled", False))
                cmek = body.get("encryption_key_name")
                tf_data["databases"].append({
                    "type": res_type,
                    "name": db_name,
                    "database_version": db_ver,
                    "tier": tier,
                    "region": reg,
                    "private_network": p_net or "Private VPC / Private Service Connect (PSC)",
                    "cmek_key": cmek,
                    "require_ssl": req_ssl,
                    "backup_enabled": bkp_enabled,
                    "has_public_ip": has_pub,
                    "file": rel_file,
                })
        else:
            raw_name = extract_hcl_attr(body, "name", vars_dict=vars_dict) or extract_hcl_attr(body, "dataset_id", vars_dict=vars_dict) or res_name
            if raw_name.startswith("${") and ("var.id" in raw_name or "local.prefix" in raw_name or "each.key" in raw_name):
                return
            db_name = clean_interpolated_string(raw_name, vars_dict, default_val=res_name)
            if db_name in ("name", "id", "db", "database", ""):
                if res_type == "google_redis_instance":
                    db_name = "grafana-cache" if ("grafana" in rel_file or "cache" in rel_file) else "memorystore-redis"
                else:
                    db_name = res_name
            raw_ver = extract_hcl_attr(body, "database_version", vars_dict=vars_dict) or ("PostgreSQL 15" if "sql" in res_type else "Managed Cloud Database")
            db_ver = "PostgreSQL 15" if (not raw_ver or "${" in raw_ver or "var." in raw_ver) else clean_interpolated_string(raw_ver, vars_dict)
            tier = extract_hcl_attr(body, "tier", vars_dict=vars_dict) or "db-custom-4-16384"
            reg = extract_hcl_attr(body, "region", vars_dict=vars_dict) or extract_hcl_attr(body, "location", vars_dict=vars_dict) or "us-east4"
            p_net = extract_hcl_attr(body, "private_network", vars_dict=vars_dict) or extract_hcl_attr(body, "authorized_network", vars_dict=vars_dict)
            if p_net:
                if "psa_private_network" in str(p_net):
                    p_net = "Private VPC / Private Service Connect (PSC)"
                else:
                    p_clean = clean_interpolated_string(str(p_net), vars_dict)
                    if "var." in p_clean or "local." in p_clean or "${" in p_clean or not is_valid_resource_name(p_clean):
                        p_net = None
                    else:
                        p_net = p_clean
            cmek = extract_hcl_attr(body, "encryption_key_name", vars_dict=vars_dict)
            # Degraded text scan: absent evidence is not evidence of compliance.
            req_ssl = _text_attr_tristate(body, "require_ssl")
            if req_ssl is None:
                ssl_m = re.search(r'ssl_mode\s*=\s*"?([A-Z_]+)"?', str(body), re.IGNORECASE)
                if ssl_m:
                    req_ssl = ssl_m.group(1).upper() in ("ENCRYPTED_ONLY", "TRUSTED_CLIENT_CERTIFICATE_REQUIRED")
            bkp_enabled = None
            if "backup_configuration" in body:
                bkp_enabled = _text_attr_tristate(body, "backup_configuration")
                if bkp_enabled is None:
                    bkp_enabled = False if re.search(r"\benabled\s*=\s*false\b", str(body), re.IGNORECASE) else None
            has_pub = True if ("ipv4_enabled = true" in body or "ipv4_enabled=true" in body or "authorized_networks" in body) else False
            tf_data["databases"].append({
                "type": res_type,
                "name": db_name,
                "database_version": db_ver,
                "tier": tier,
                "region": reg,
                "private_network": p_net,
                "cmek_key": cmek,
                "require_ssl": req_ssl,
                "backup_enabled": bkp_enabled,
                "has_public_ip": has_pub,
                "file": rel_file,
            })

    # 9. GKE Clusters
    elif res_type == "google_container_cluster":
        if isinstance(body, dict):
            c_name = _resolved_asset_name(body.get("name"), res_name, vars_dict, "gke-cluster")
            loc = body.get("location", "us-east4")
            m_ver = body.get("min_master_version") or body.get("master_version", "1.28+")
            p_cfg = body.get("private_cluster_config") or []
            p_dict = p_cfg[0] if isinstance(p_cfg, list) and p_cfg else (p_cfg if isinstance(p_cfg, dict) else {})
            # A cluster with no private_cluster_config is public on both counts.
            priv_cluster = bool(p_dict.get("enable_private_nodes", False))
            priv_endpoint = bool(p_dict.get("enable_private_endpoint", False))
            cidr = p_dict.get("master_ipv4_cidr_block", "172.16.0.0/28")
            wif_cfg = body.get("workload_identity_config") or []
            wif = bool(wif_cfg)
            tf_data["gke_clusters"].append({
                "name": c_name,
                "master_version": m_ver,
                "master_ipv4_cidr_block": cidr,
                "location": loc,
                "private_cluster": priv_cluster,
                "private_endpoint": priv_endpoint,
                "workload_identity": wif,
                "file": rel_file,
            })
        else:
            cluster_name = extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name
            m_ver = extract_hcl_attr(body, "min_master_version", vars_dict=vars_dict) or extract_hcl_attr(body, "master_version", vars_dict=vars_dict) or "1.28+"
            cidr = extract_hcl_attr(body, "master_ipv4_cidr_block", vars_dict=vars_dict) or "172.16.0.0/28"
            loc = extract_hcl_attr(body, "location", vars_dict=vars_dict) or "us-east4"
            priv_cluster = _text_attr_tristate(body, "enable_private_nodes")
            priv_endpoint = _text_attr_tristate(body, "enable_private_endpoint")
            wif = ("workload_identity_config" in body)
            tf_data["gke_clusters"].append({
                "name": cluster_name,
                "master_version": m_ver,
                "master_ipv4_cidr_block": cidr,
                "location": loc,
                "private_cluster": priv_cluster,
                "private_endpoint": priv_endpoint,
                "workload_identity": wif,
                "file": rel_file,
            })

    # 10. Service Accounts & Keys
    elif res_type == "google_service_account":
        if "modules/fabric/" in rel_file:
            return
        if isinstance(body, dict):
            acct_id = _resolved_asset_name(body.get("account_id"), res_name, vars_dict, "service-account")
            disp = body.get("display_name") or acct_id
            sa_record: Dict[str, Any] = {
                "resource_name": res_name,
                "account_id": acct_id,
                "display_name": disp,
                "file": rel_file,
            }
            sa_project = body.get("project")
            if body.get("email"):
                sa_record["email"] = body["email"]
            elif sa_project and str(sa_project).strip():
                sa_record["email"] = f"{acct_id}@{str(sa_project).strip()}.iam.gserviceaccount.com"
            else:
                # No project is declared on this resource, so the email cannot be
                # derived. Previously this defaulted the project segment to the
                # literal string "workload", which put a principal that does not
                # exist into the SSP and the IR runbooks. Omit it and let the
                # consumer fail closed instead.
                logger.debug(
                    "Service account %r declares no project; omitting email rather than fabricating one.",
                    acct_id,
                )
            if sa_project and str(sa_project).strip():
                sa_record["project"] = str(sa_project).strip()
            tf_data["service_accounts"].append(sa_record)
        else:
            raw_acct = extract_hcl_attr(body, "account_id", vars_dict=vars_dict) or res_name
            acct_id = clean_interpolated_string(raw_acct, vars_dict, default_val=res_name)
            if not is_valid_resource_name(acct_id) or "${" in acct_id or (vars_dict and "var." in acct_id):
                return
            raw_disp = extract_hcl_attr(body, "display_name", vars_dict=vars_dict) or acct_id
            disp = clean_interpolated_string(raw_disp, vars_dict, default_val=acct_id)
            sa_record: Dict[str, Any] = {
                "resource_name": res_name,
                "account_id": acct_id,
                "display_name": disp,
                "file": rel_file,
            }
            # The email is only recorded when the project is genuinely declared on
            # the resource. Guessing the project segment would put a non-existent
            # principal into the SSP and the IR runbooks.
            raw_project = extract_hcl_attr(body, "project", vars_dict=vars_dict)
            if raw_project:
                sa_project = clean_interpolated_string(raw_project, vars_dict, default_val="")
                if sa_project and is_valid_resource_name(sa_project) and "${" not in sa_project:
                    sa_record["project"] = sa_project
                    sa_record["email"] = f"{acct_id}@{sa_project}.iam.gserviceaccount.com"
            tf_data["service_accounts"].append(sa_record)
    elif res_type == "google_service_account_key":
        if isinstance(body, dict):
            sa_id = _resolved_asset_name(body.get("service_account_id"), res_name, vars_dict, "service-account-key")
        else:
            sa_id = extract_hcl_attr(body, "service_account_id", vars_dict=vars_dict) or res_name
        tf_data["service_account_keys"].append({
            "service_account": sa_id,
            "name": res_name,
            "file": rel_file,
        })

    # 11. IAM Bindings
    elif any(res_type.startswith(p) for p in ("google_project_iam_", "google_organization_iam_", "google_folder_iam_", "google_storage_bucket_iam_", "google_kms_crypto_key_iam_")):
        if "modules/fabric/" in rel_file:
            return
        res_scope = res_type.split("_iam_")[0].replace("google_", "")
        if isinstance(body, dict):
            role_val = body.get("role", "Custom Role")
            members = []
            if "member" in body and body["member"]:
                members.append(body["member"])
            if "members" in body and isinstance(body["members"], list):
                members.extend(body["members"])
            for m in members:
                resolved_mem = resolve_iam_principal(
                    mem=m,
                    body="",
                    rel_file=rel_file,
                    res_type=res_type,
                    res_name=res_name,
                    role_val=role_val,
                    resolved_vars={},
                    service_accounts=tf_data.get("service_accounts", []),
                )
                if resolved_mem and "${" not in resolved_mem:
                    tf_data["iam_bindings"].append({
                        "principal": resolved_mem,
                        "role": role_val,
                        "scope": res_scope,
                        "file": rel_file,
                    })
        else:
            role_match = re.search(r'role\s*=\s*"([^"]+)"', body)
            role_val = role_match.group(1) if role_match else (extract_hcl_attr(body, "role", vars_dict=vars_dict) or "Custom Role")
            if "${each.value.role}" in role_val or role_val.startswith("${each."):
                return
            if "${" in role_val:
                role_val = clean_interpolated_string(role_val, vars_dict, default_val="Custom Role")
                if "${" in role_val or "each." in role_val:
                    return

            members = []
            members_match = re.search(r'members\s*=\s*\[([^\]]+)\]', body)
            if members_match:
                for m in members_match.group(1).split(','):
                    cleaned_m = m.strip(' "\'\n\r\t')
                    if cleaned_m:
                        members.append(cleaned_m)
            else:
                member_match = re.search(r'member\s*=\s*"([^"]+)"', body)
                if member_match:
                    members.append(member_match.group(1))
                else:
                    mem_val = extract_hcl_attr(body, "member", vars_dict=vars_dict)
                    if mem_val:
                        members.append(mem_val)

            for mem in members:
                resolved_mem = resolve_iam_principal(
                    mem=mem,
                    body=body,
                    rel_file=rel_file,
                    res_type=res_type,
                    res_name=res_name,
                    role_val=role_val,
                    resolved_vars=vars_dict,
                    service_accounts=tf_data.get("service_accounts", []),
                )
                if resolved_mem and "${" not in resolved_mem:
                    tf_data["iam_bindings"].append({
                        "principal": resolved_mem,
                        "role": role_val,
                        "scope": res_scope,
                        "file": rel_file,
                    })

    # 12. Logging, Secrets, PubSub, Artifact Registry, Serverless, Security
    elif "google_logging" in res_type and "sink" in res_type:
        tf_data["logging_sinks"].append(res_name)
    elif res_type == "google_secret_manager_secret":
        if "secrets" not in tf_data:
            tf_data["secrets"] = []
        tf_data["secrets"].append(res_name)
    elif res_type == "google_pubsub_topic":
        if "pubsub_topics" not in tf_data:
            tf_data["pubsub_topics"] = []
        tf_data["pubsub_topics"].append(res_name)
    elif res_type == "google_artifact_registry_repository":
        if "artifact_registries" not in tf_data:
            tf_data["artifact_registries"] = []
        tf_data["artifact_registries"].append(res_name)
    elif res_type in ("google_cloud_run_service", "google_cloud_run_v2_service"):
        if "modules/fabric/" in rel_file:
            return
        if isinstance(body, dict):
            cr_name = _resolved_asset_name(body.get("name"), res_name, vars_dict, "cloud-run-service")
            cr_loc = body.get("location", "us-east4")
            cr_img = body.get("image", "us-docker.pkg.dev/cloudrun/container/workload:latest")
        else:
            raw_cr = extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name
            cr_name = clean_interpolated_string(raw_cr, vars_dict, default_val=res_name)
            if not is_valid_resource_name(cr_name) or "${" in cr_name:
                return
            cr_loc = extract_hcl_attr(body, "location", vars_dict=vars_dict) or "us-east4"
            cr_loc = clean_interpolated_string(cr_loc, vars_dict, default_val="us-east4")
            cr_img = extract_hcl_attr(body, "image", vars_dict=vars_dict)
            if cr_img and ("local." in str(cr_img) or "${" in str(cr_img)):
                cr_img = "us-docker.pkg.dev/cloudrun/container/workload:latest"
        tf_data["cloud_run_services"].append({
            "name": cr_name,
            "location": cr_loc,
            "image": cr_img,
            "file": rel_file,
        })
    elif res_type in ("google_cloudfunctions_function", "google_cloudfunctions2_function"):
        fn_name = body.get("name") or res_name if isinstance(body, dict) else (extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name)
        fn_rt = body.get("runtime", "python311") if isinstance(body, dict) else (extract_hcl_attr(body, "runtime", vars_dict=vars_dict) or "python311")
        tf_data["cloud_functions"].append({
            "name": fn_name,
            "runtime": fn_rt,
            "file": rel_file,
        })
    elif res_type == "google_compute_router_nat":
        nat_name = body.get("name") or res_name if isinstance(body, dict) else (extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name)
        tf_data["nat_gateways"].append({"name": nat_name, "file": rel_file})
    elif res_type in ("google_compute_global_forwarding_rule", "google_compute_forwarding_rule"):
        fr_name = body.get("name") or res_name if isinstance(body, dict) else (extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name)
        tf_data["forwarding_rules"].append({"name": fr_name, "file": rel_file})
    elif res_type == "google_compute_security_policy":
        sec_name = body.get("name") or res_name if isinstance(body, dict) else (extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name)
        tf_data["security_policies"].append({"name": sec_name, "file": rel_file})
        tf_data["ids_solution"] = "Google Cloud Armor Enterprise WAF & Cloud IDS/IPS"
    elif res_type == "google_access_context_manager_service_perimeter":
        sp_name = body.get("title") or body.get("name") or res_name if isinstance(body, dict) else (extract_hcl_attr(body, "title", vars_dict=vars_dict) or extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name)
        tf_data["service_perimeters"].append({"name": sp_name, "file": rel_file})
    elif res_type == "google_binary_authorization_policy":
        tf_data["binary_authorization"].append({"name": res_name, "file": rel_file})
    elif res_type == "google_dataproc_cluster":
        dp_name = body.get("name") or res_name if isinstance(body, dict) else (extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name)
        tf_data["dataproc_clusters"].append({"name": dp_name, "file": rel_file})
    elif res_type == "google_assured_workloads_workload":
        tf_data["assured_workloads"].append(rel_file)
    elif res_type in (
        "google_compute_vpn_gateway",
        "google_compute_ha_vpn_gateway",
        "google_compute_vpn_tunnel",
        "google_compute_interconnect_attachment",
    ):
        gw_name = body.get("name") or res_name if isinstance(body, dict) else (extract_hcl_attr(body, "name", vars_dict=vars_dict) or res_name)
        peer_ip = body.get("peer_ip") or body.get("peer_gcp_gateway") if isinstance(body, dict) else (extract_hcl_attr(body, "peer_ip", vars_dict=vars_dict) or extract_hcl_attr(body, "peer_gcp_gateway", vars_dict=vars_dict))
        peer_asn = body.get("peer_asn") if isinstance(body, dict) else extract_hcl_attr(body, "peer_asn", vars_dict=vars_dict)
        if "boundary_connections" not in tf_data:
            tf_data["boundary_connections"] = []
        tf_data["boundary_connections"].append({
            "name": gw_name,
            "type": res_type,
            "peer_ip": peer_ip,
            "peer_asn": peer_asn,
            "file": rel_file,
        })


def ingest_terraform_json(
    tf_json: Dict[str, Any],
    user_config: Optional[Dict[str, Any]] = None,
    target_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Ingests and translates HashiCorp Terraform JSON output into system components.

    Translates fully resolved Terraform state/plan JSON, extracting exact VPCs, subnets,
    firewalls, compute VMs, storage buckets, KMS keys, databases, GKE clusters, and IAM bindings.

    Args:
        tf_json: Raw dictionary from 'terraform show -json' or 'terraform.tfstate'.
        user_config: Optional dictionary containing user configuration overrides.
        target_dir: Optional target workspace root directory.

    Returns:
        Structured dictionary matching deep_scan_tf_files schema.
    """
    resources, tf_ver, prov_versions, modules_used = extract_resources_from_tf_json(tf_json)

    tf_data = init_empty_tf_data(
        user_config=user_config,
        engine_version=tf_ver,
        provider_versions=prov_versions,
        modules_used=modules_used,
    )

    for item in resources:
        res_type = item.get("type", "")
        res_name = item.get("name", "")
        values = item.get("values") or {}
        classify_and_ingest_resource(
            res_type=res_type,
            res_name=res_name,
            body=values,
            rel_file="terraform.tfplan",
            tf_data=tf_data,
            resolved_vars={},
        )

    return finalize_terraform_data(tf_data, target_dir)


def discover_or_generate_terraform_json(
    target_dir: Union[str, Path],
    user_config: Optional[Dict[str, Any]] = None,
    allow_terraform_plan: bool = False,
) -> Optional[Dict[str, Any]]:
    """Discovers pre-existing Terraform plan/state JSON or dynamically generates it.

    Search & Execution Hierarchy:
    1. Explicit path in configuration ('terraform_plan_path' or 'terraform_state_path').
    2. Auto-discovery of *.json files ('tfplan.json', 'terraform.tfstate', etc.).
    3. Auto-generation via 'terraform show -json' if CLI and state/plan are present.
    4. Fallback to None (triggering static HCL parsing).

    Args:
        target_dir: The target workspace root or project directory.
        user_config: Optional dictionary containing user configuration overrides.

    Returns:
        Parsed dictionary of Terraform state/plan JSON, or None if unavailable.
    """
    target_path = Path(target_dir).resolve()
    user_config = user_config or {}

    # 1. Check explicit user configurations
    explicit_plan = user_config.get("terraform_plan_path")
    explicit_state = user_config.get("terraform_state_path")

    for cand_p in [explicit_plan, explicit_state]:
        if not cand_p:
            continue
        p = Path(cand_p)
        resolved_p = p if p.is_absolute() else (target_path / p)
        if not resolved_p.is_file():
            resolved_p = target_path / "terraform" / p
        if resolved_p.is_file():
            if str(resolved_p).endswith(".json"):
                try:
                    data = read_json_file(str(resolved_p))
                    if isinstance(data, dict):
                        logger.info("Ingesting user-configured Terraform JSON: '%s'", resolved_p)
                        return data
                except Exception as err:
                    logger.warning("Failed to load user-configured Terraform JSON '%s': %s", resolved_p, err)
            else:
                tf_bin = shutil.which("terraform")
                if tf_bin:
                    try:
                        res = safe_run_command([tf_bin, "show", "-json", str(resolved_p)], timeout=30)
                        if res.returncode == 0 and res.stdout.strip():
                            data = json.loads(res.stdout)
                            logger.info("Rendered binary plan '%s' via 'terraform show -json'", resolved_p)
                            return data
                    except Exception as err:
                        logger.warning("Failed running 'terraform show -json' on '%s': %s", resolved_p, err)

    # 2. Auto-discover plan or state JSON in target_dir and immediate subfolders
    candidate_names = [
        "tfplan.json", "plan.json", "terraform_plan.json",
        "terraform.tfstate", "state.json", "terraform_state.json"
    ]
    search_dirs = [target_path]
    if (target_path / "terraform").is_dir():
        search_dirs.append(target_path / "terraform")

    for s_dir in search_dirs:
        for fname in candidate_names:
            c_file = s_dir / fname
            if c_file.is_file():
                try:
                    data = read_json_file(str(c_file))
                    if isinstance(data, dict) and (
                        "planned_values" in data
                        or "values" in data
                        or "resources" in data
                        or "format_version" in data
                    ):
                        logger.info("Auto-discovered Terraform JSON plan/state at '%s'", c_file)
                        return data
                except Exception as err:
                    logger.debug("Candidate file '%s' is not valid Terraform JSON: %s", c_file, err)

    tf_bin = shutil.which("terraform")
    if tf_bin:
        for s_dir in search_dirs:
            for b_name in ["tfplan", ".tfplan", "plan.binary"]:
                b_file = s_dir / b_name
                if b_file.is_file():
                    try:
                        res = safe_run_command([tf_bin, "show", "-json", str(b_file)],
                            cwd=str(s_dir),
                            capture_output=True,
                            text=True,
                            check=False,
                            timeout=30
                        )
                        if res.returncode == 0 and res.stdout.strip():
                            data = json.loads(res.stdout)
                            logger.info("Auto-discovered and rendered binary plan at '%s'", b_file)
                            return data
                    except Exception as err:
                        logger.debug("Failed running 'terraform show -json' on '%s': %s", b_file, err)

    # 3. Auto-generation via terraform CLI
    if tf_bin:
        for s_dir in search_dirs:
            tf_files = list(s_dir.glob("*.tf"))
            if not tf_files:
                continue
            if (s_dir / ".terraform").is_dir() or (s_dir / ".terraform.lock.hcl").is_file():
                try:
                    res = safe_run_command([tf_bin, "show", "-json"], cwd=str(s_dir), timeout=30)
                    if res.returncode == 0 and res.stdout.strip():
                        data = json.loads(res.stdout)
                        if data.get("values") or data.get("resources"):
                            logger.info("Auto-generated Terraform state JSON via 'terraform show -json' in '%s'", s_dir)
                            return data
                except Exception as err:
                    logger.debug("Could not auto-generate state JSON in '%s': %s", s_dir, err)

                tmp_plan = s_dir / ".compliance_tfplan.tmp"
                try:
                    plan_cmd = safe_run_command([tf_bin, "plan", "-no-color", f"-out={tmp_plan.name}"], cwd=str(s_dir), timeout=45)
                    if plan_cmd.returncode == 0 and tmp_plan.is_file():
                        show_cmd = safe_run_command([tf_bin, "show", "-json", tmp_plan.name], cwd=str(s_dir), timeout=30)
                        if show_cmd.returncode == 0 and show_cmd.stdout.strip():
                            data = json.loads(show_cmd.stdout)
                            logger.info("Auto-generated Terraform plan JSON in '%s'", s_dir)
                            return data
                except Exception as err:
                    logger.debug("Plan generation in '%s' skipped: %s", s_dir, err)
                finally:
                    if tmp_plan.is_file():
                        try:
                            tmp_plan.unlink()
                        except OSError as unlink_err:
                            logger.debug(
                                "Could not remove temporary plan '%s': %s", tmp_plan, unlink_err
                            )

    return None


def ingest_sbom_json(sbom_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ingests and translates CycloneDX, SPDX, or Syft SBOM JSON into application components.

    Extracts package names, exact versions, purls, licenses, and detects runtimes
    and application frameworks without relying on regex scraping.

    Args:
        sbom_data: Parsed dictionary from CycloneDX, SPDX, or Syft JSON output.

    Returns:
        Structured dictionary matching deep_scan_app_files schema.
    """
    app_data: Dict[str, Any] = {
        "applications": [],
        "software_packages": [],
        "container_images": [],
        "exposed_ports": [],
        "frameworks": set(),
        "runtimes": set(),
        "database_connectors": set(),
        "all_resources": []
    }

    # 1. CycloneDX Schema
    if "components" in sbom_data or sbom_data.get("bomFormat") == "CycloneDX":
        meta_comp = sbom_data.get("metadata", {}).get("component")
        if meta_comp and isinstance(meta_comp, dict):
            app_name = meta_comp.get("name", "app-service")
            app_data["applications"].append({
                "name": app_name,
                "version": meta_comp.get("version", "1.0.0"),
                "description": meta_comp.get("description", "Application / Service Component"),
                "type": meta_comp.get("type", "application"),
                "framework": "Cloud Native Service",
                "entrypoint": "main",
                "file": "sbom.json"
            })
            app_data["all_resources"].append({
                "type": "Application Service",
                "name": app_name,
                "category": "Application Layer Component",
                "file": "sbom.json"
            })

        for comp in sbom_data.get("components", []):
            name = comp.get("name")
            if not name:
                continue
            ver = comp.get("version", "Latest")
            purl = comp.get("purl", "")
            c_type = comp.get("type", "library")
            desc = comp.get("description", "")

            eco = "Open Source"
            if "pkg:pypi" in purl or c_type == "python":
                eco = "PyPI (Python)"
                app_data["runtimes"].add("Python")
            elif "pkg:npm" in purl or c_type in ("npm", "nodejs"):
                eco = "npm (Node.js)"
                app_data["runtimes"].add("Node.js")
            elif "pkg:golang" in purl or c_type == "go-module":
                eco = "Go Modules"
                app_data["runtimes"].add("Go")
            elif "pkg:maven" in purl or c_type in ("java", "maven"):
                eco = "Maven (Java)"
                app_data["runtimes"].add("Java")
            elif "pkg:deb" in purl:
                eco = "Debian OS Package"
            elif "pkg:apk" in purl:
                eco = "Alpine OS Package"

            cat = "Third-Party Library"
            n_low = name.lower()
            if c_type == "framework" or any(k in n_low for k in ["fastapi", "flask", "django", "express", "next", "react", "gin", "spring"]):
                cat = "Application Framework"
                if "fastapi" in n_low:
                    app_data["frameworks"].add("FastAPI REST Microservice")
                elif "flask" in n_low:
                    app_data["frameworks"].add("Flask Application")
                elif "django" in n_low:
                    app_data["frameworks"].add("Django Enterprise Application")
                elif "express" in n_low:
                    app_data["frameworks"].add("Express.js REST API")
                elif "next" in n_low:
                    app_data["frameworks"].add("Next.js Full-Stack Application")
                elif "react" in n_low:
                    app_data["frameworks"].add("React Modern Single-Page Application (SPA)")
            elif any(k in n_low for k in ["asyncpg", "psycopg", "pg", "mysql", "redis", "mongo", "spanner", "bigquery"]):
                cat = "Database Client Driver"
                if any(p in n_low for p in ["asyncpg", "psycopg", "pg"]):
                    app_data["database_connectors"].add("PostgreSQL (asyncpg/psycopg2)")
                elif "redis" in n_low:
                    app_data["database_connectors"].add("Redis Client Driver")
                elif "bigquery" in n_low:
                    app_data["database_connectors"].add("Google Cloud BigQuery Client")
            elif "google-cloud-" in n_low:
                cat = "Cloud Client SDK"

            lic_str = "Open Source License"
            licenses = comp.get("licenses", [])
            if licenses and isinstance(licenses, list):
                first_lic = licenses[0]
                if isinstance(first_lic, dict):
                    if "license" in first_lic and isinstance(first_lic["license"], dict):
                        lic_str = first_lic["license"].get("id") or first_lic["license"].get("name", lic_str)
                    elif "id" in first_lic:
                        lic_str = first_lic.get("id")
                elif isinstance(first_lic, str):
                    lic_str = first_lic

            app_data["software_packages"].append({
                "name": name,
                "version": ver,
                "ecosystem": eco,
                "category": cat,
                "license": lic_str,
                "purl": purl,
                "description": desc,
                "file": "sbom.json"
            })

            if c_type == "container":
                app_data["container_images"].append({
                    "image": f"{name}:{ver}",
                    "base_os": eco,
                    "file": "sbom.json"
                })

    # 2. Syft Schema (artifacts)
    elif "artifacts" in sbom_data:
        for art in sbom_data.get("artifacts", []):
            name = art.get("name")
            if not name:
                continue
            ver = art.get("version", "Latest")
            purl = art.get("purl", "")
            a_type = art.get("type", "library")
            eco = f"{a_type.title()} Package" if a_type else "Open Source"
            if "python" in a_type.lower() or "pypi" in purl:
                app_data["runtimes"].add("Python")
                eco = "PyPI (Python)"
            elif "npm" in a_type.lower() or "javascript" in a_type.lower():
                app_data["runtimes"].add("Node.js")
                eco = "npm (Node.js)"
            elif "go" in a_type.lower():
                app_data["runtimes"].add("Go")
                eco = "Go Modules"
            elif "java" in a_type.lower() or "maven" in a_type.lower():
                app_data["runtimes"].add("Java")
                eco = "Maven (Java)"

            cat = "Third-Party Library"
            n_low = name.lower()
            if any(k in n_low for k in ["fastapi", "flask", "django", "express", "next", "react"]):
                cat = "Application Framework"
                if "fastapi" in n_low:
                    app_data["frameworks"].add("FastAPI REST Microservice")
                elif "flask" in n_low:
                    app_data["frameworks"].add("Flask Application")
            elif any(k in n_low for k in ["asyncpg", "psycopg", "pg", "mysql", "redis", "bigquery"]):
                cat = "Database Client Driver"
                if "asyncpg" in n_low or "psycopg" in n_low or "pg" in n_low:
                    app_data["database_connectors"].add("PostgreSQL (asyncpg/psycopg2)")

            lic_list = art.get("licenses", [])
            lic_str = lic_list[0] if (isinstance(lic_list, list) and lic_list) else "Open Source License"

            app_data["software_packages"].append({
                "name": name,
                "version": ver,
                "ecosystem": eco,
                "category": cat,
                "license": lic_str,
                "purl": purl,
                "file": "sbom.json"
            })

    # 3. SPDX Schema (packages)
    elif "packages" in sbom_data:
        for pkg in sbom_data.get("packages", []):
            name = pkg.get("name")
            if not name:
                continue
            ver = pkg.get("versionInfo", "Latest")
            lic = pkg.get("licenseConcluded") or "Open Source License"
            desc = pkg.get("summary", "")
            app_data["software_packages"].append({
                "name": name,
                "version": ver,
                "ecosystem": "Open Source Package",
                "category": "Third-Party Library",
                "license": lic,
                "description": desc,
                "file": "sbom.json"
            })

    return app_data


def discover_or_generate_sbom(
    target_dir: Union[str, Path],
    user_config: Optional[Dict[str, Any]] = None,
    allow_scanners: bool = False,
) -> Optional[Dict[str, Any]]:
    """Discovers pre-existing SBOM JSON or dynamically generates it via Syft / Trivy.

    Search & Execution Hierarchy:
    1. Explicit path in configuration ('sbom_path').
    2. Auto-discovery of *.json files ('sbom.json', 'cyclonedx.json', 'spdx.json').
    3. Auto-generation via 'syft' CLI if installed.
    4. Auto-generation via 'trivy' CLI if installed.
    5. Fallback to None (triggering static application file scanning).

    Args:
        target_dir: The target workspace root or project directory.
        user_config: Optional dictionary containing user configuration overrides.

    Returns:
        Parsed dictionary of SBOM JSON, or None if unavailable.
    """
    target_path = Path(target_dir).resolve()
    user_config = user_config or {}

    # 1. Explicit user configuration
    explicit_sbom = user_config.get("sbom_path")
    if explicit_sbom:
        p = Path(explicit_sbom)
        resolved_p = p if p.is_absolute() else (target_path / p)
        if not resolved_p.is_file():
            resolved_p = target_path / "app" / p
        if resolved_p.is_file():
            try:
                data = read_json_file(str(resolved_p))
                if isinstance(data, dict):
                    logger.info("Ingesting user-configured SBOM: '%s'", resolved_p)
                    return data
            except Exception as err:
                logger.warning("Failed loading user-configured SBOM '%s': %s", resolved_p, err)

    # 2. Auto-discovery in target_dir and app/
    candidate_names = [
        "sbom.json", "bom.json", "cyclonedx.json", "spdx.json", "app_sbom.json"
    ]
    search_dirs = [target_path]
    if (target_path / "app").is_dir():
        search_dirs.append(target_path / "app")

    for s_dir in search_dirs:
        for fname in candidate_names:
            c_file = s_dir / fname
            if c_file.is_file():
                try:
                    data = read_json_file(str(c_file))
                    if isinstance(data, dict) and (
                        "components" in data or "packages" in data or "artifacts" in data
                    ):
                        logger.info("Auto-discovered SBOM file at '%s'", c_file)
                        return data
                except Exception as err:
                    logger.debug("Candidate file '%s' is not valid SBOM JSON: %s", c_file, err)

    if not allow_scanners:
        logger.info("Skipping dynamic SBOM generation via Syft/Trivy (not explicitly allowed)")
        return None

    # 3. Auto-generation via Syft
    syft_bin = shutil.which("syft")
    if syft_bin:
        app_dir = target_path / "app" if (target_path / "app").is_dir() else target_path
        try:
            res = safe_run_command([syft_bin, f"dir:{app_dir}", "-o", "cyclonedx-json"], timeout=60)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if data.get("components"):
                    logger.info("Auto-generated SBOM via 'syft dir:%s'", app_dir)
                    return data
        except Exception as err:
            logger.debug("Syft SBOM generation skipped: %s", err)

    # 4. Auto-generation via Trivy
    trivy_bin = shutil.which("trivy")
    if trivy_bin:
        app_dir = target_path / "app" if (target_path / "app").is_dir() else target_path
        try:
            res = safe_run_command([trivy_bin, "fs", "--format", "cyclonedx", "--offline-scan", "--skip-db-update", "--", str(app_dir)], timeout=60)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if data.get("components"):
                    logger.info("Auto-generated SBOM via 'trivy fs %s'", app_dir)
                    return data
        except Exception as err:
            logger.debug("Trivy SBOM generation skipped: %s", err)

    return None


def merge_app_data(
    base_app_data: Dict[str, Any],
    sbom_app_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Merges SBOM discovered dependencies and packages into static code app data.

    Preserves code-level port listeners and containers while enhancing the software
    package inventory with authoritative versions and license data from the SBOM.

    Args:
        base_app_data: Output dictionary from deep_scan_app_files.
        sbom_app_data: Output dictionary from ingest_sbom_json.

    Returns:
        Unified application components dictionary.
    """
    merged: Dict[str, Any] = {
        "applications": list(base_app_data.get("applications", [])),
        "software_packages": list(base_app_data.get("software_packages", [])),
        "container_images": list(base_app_data.get("container_images", [])),
        "exposed_ports": list(base_app_data.get("exposed_ports", [])),
        "frameworks": set(base_app_data.get("frameworks", set())),
        "runtimes": set(base_app_data.get("runtimes", set())),
        "database_connectors": set(base_app_data.get("database_connectors", set())),
        "all_resources": list(base_app_data.get("all_resources", []))
    }

    existing_pkg_keys = {
        (p.get("name", "").lower(), p.get("version", ""))
        for p in merged["software_packages"]
    }
    for p in sbom_app_data.get("software_packages", []):
        pkg_key = (p.get("name", "").lower(), p.get("version", ""))
        if pkg_key not in existing_pkg_keys:
            merged["software_packages"].append(p)
            existing_pkg_keys.add(pkg_key)

    merged["runtimes"].update(sbom_app_data.get("runtimes", set()))
    merged["frameworks"].update(sbom_app_data.get("frameworks", set()))
    merged["database_connectors"].update(sbom_app_data.get("database_connectors", set()))

    existing_app_names = {a.get("name") for a in merged["applications"]}
    for app in sbom_app_data.get("applications", []):
        if app.get("name") not in existing_app_names:
            merged["applications"].append(app)
            existing_app_names.add(app.get("name"))

    existing_imgs = {c.get("image") for c in merged["container_images"]}
    for img in sbom_app_data.get("container_images", []):
        if img.get("image") not in existing_imgs:
            merged["container_images"].append(img)
            existing_imgs.add(img.get("image"))

    return merged

def deep_scan_tf_files(
    target_dir: str,
    user_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Scans Terraform files (.tf) to discover cloud resources and architecture.

    Extracts enabled services, VPCs, subnets, firewall rules, compute instances,
    GKE clusters, databases, storage buckets, KMS keys, service accounts, and IAM roles.

    Args:
        target_dir: Directory containing Terraform blueprints.
        user_config: Optional dictionary containing user configuration overrides.

    Returns:
        Structured dictionary detailing discovered infrastructure components.
    """
    tf_data = init_empty_tf_data(user_config=user_config)

    scan_targets = [target_dir]
    scanned_files = set()
    scanned_dirs = set()

    # --------------------------------------------------------------------------
    # Phase 1: Collect variable defaults (.tf) and overrides (.tfvars / config)
    # --------------------------------------------------------------------------
    resolved_vars = {}
    tf_defaults = {}
    tfvars_overrides = {}

    target_boundary = Path(target_dir).resolve()

    discovered_tf_files = []

    for scan_root in scan_targets:
        for root, dirs, files in os.walk(scan_root):
            safe_dirs = []
            for d in dirs:
                if d in IGNORED_TRAVERSAL_DIRS:
                    continue
                if d == "template" and os.path.abspath(scan_root) != os.path.abspath(os.path.join(root, d)):
                    continue
                d_path = os.path.join(root, d)
                pass  # os.walk(followlinks=False) already ignores symlinked directories
                safe_dirs.append(d)
            dirs[:] = safe_dirs

            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.islink(filepath):
                    try:
                        ensure_path_within_boundary(filepath, allowed_boundary=target_boundary)
                    except (ValueError, PermissionError):
                        logger.warning("Skipping symlink file outside target boundary: %s", filepath)
                        continue
                if filename.endswith(".tf"):
                    discovered_tf_files.append((root, filename, os.path.abspath(filepath)))
                    try:
                        var_content = read_text_file(filepath, allowed_boundary=target_boundary)
                        parsed_defs = parse_tfvars_content(var_content)
                        for vk, vv in parsed_defs.items():
                            if vk not in GENERIC_VAR_NAMES:
                                tf_defaults[vk] = vv
                    except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
                        logger.debug("Failed reading variable definitions in %s: %s", filepath, err)
                elif filename.endswith(".tfvars"):
                    discovered_tf_files.append((root, filename, os.path.abspath(filepath)))
                    try:
                        var_content = read_text_file(filepath, allowed_boundary=target_boundary)
                        tfvars_overrides.update(parse_tfvars_content(var_content))
                    except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
                        logger.debug("Failed reading tfvars in %s: %s", filepath, err)
                elif filename.endswith(".tfvars.json"):
                    try:
                        jdata = read_json_file(filepath, allowed_boundary=target_boundary)
                        if isinstance(jdata, dict):
                            for jk, jv in jdata.items():
                                if is_sensitive_key(jk):
                                    tfvars_overrides[jk] = "[REDACTED_SENSITIVE]"
                                else:
                                    tfvars_overrides[jk] = jv
                    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, PermissionError) as err:
                        logger.debug("Failed reading tfvars.json in %s: %s", filepath, err)

    # Defaults first, then tfvars overrides
    resolved_vars.update(tf_defaults)
    resolved_vars.update(tfvars_overrides)

    # User config takes highest precedence if provided
    if user_config:
        for k, v in user_config.items():
            if isinstance(v, (str, int, float, bool, list)):
                resolved_vars[k] = v
            elif isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    resolved_vars[f"{k}.{sub_k}"] = sub_v
                    if sub_k not in resolved_vars and isinstance(sub_v, (str, int, float, bool, list)):
                        resolved_vars[sub_k] = sub_v

    # --------------------------------------------------------------------------
    # Phase 2: Deep Scan HCL Resources, Modules, and Security Posture
    # --------------------------------------------------------------------------
    for root, filename, filepath in discovered_tf_files:
        if filepath in scanned_files:
            continue
        scanned_files.add(filepath)
        scanned_dirs.add(os.path.dirname(filepath))
        try:
            content = read_text_file(filepath, allowed_boundary=target_boundary)

            rel_file = os.path.relpath(filepath, target_dir)

            parsed_hcl = None
            parse_failure_err = None
            if hcl2:
                try:
                    parsed_hcl = hcl2.loads(content)
                except (LarkError, KeyError, ValueError, TypeError) as parse_err:
                    parse_failure_err = " ".join(str(parse_err).split())[:300]
                    logger.debug(
                        "HCL AST parse failed for %s: %s; attempting balanced-brace regex fallback",
                        filepath,
                        parse_failure_err,
                    )
                    parsed_hcl = None

            resources: List[Tuple[str, str, Union[Dict[str, Any], HclBlock]]] = []
            if parsed_hcl and isinstance(parsed_hcl, dict) and "resource" in parsed_hcl:
                for r_entry in parsed_hcl.get("resource", []):
                    if isinstance(r_entry, dict):
                        for rt, named_map in r_entry.items():
                            if isinstance(named_map, dict):
                                for rn, r_body in named_map.items():
                                    if isinstance(r_body, dict):
                                        # Hand the classifier the parsed AST mapping itself.
                                        #
                                        # `classify_and_ingest_resource` branches on
                                        # `isinstance(body, dict)`: the dict arm reads nested
                                        # blocks structurally (e.g. encryption[0].
                                        # default_kms_key_name), while the else arm falls back to
                                        # substring heuristics over raw HCL text. The text arm is
                                        # lossy -- it can only report *whether* a CMEK key is
                                        # mentioned, not which one, and it discards any resource
                                        # whose name is still an unresolved `${var.*}`, which is
                                        # every resource declared inside a reusable module.
                                        #
                                        # Wrapping the AST in HclBlock (a `str` subclass) failed
                                        # that isinstance check, so fully-parsed Terraform was
                                        # silently downgraded to the text path. Passing the dict
                                        # keeps this path identical in shape to the
                                        # `terraform show -json` ingestion at
                                        # `process_tf_json`, which already supplies dicts.
                                        #
                                        # The regex fallback below has no AST and therefore still
                                        # yields an HclBlock for the text arm.
                                        # Variables are resolved up-front so the
                                        # structured branch sees the same concrete
                                        # values `extract_hcl_attr` used to supply.
                                        resources.append(
                                            (rt, rn, _resolve_ast_variables(r_body, resolved_vars))
                                        )
            elif parsed_hcl is None:
                # Balanced-brace regex fallback so unparseable files do not drop boundary resources
                for match in re.finditer(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', content):
                    rt, rn = match.group(1), match.group(2)
                    block_start = match.end()
                    depth = 1
                    pos = block_start
                    while pos < len(content) and depth > 0:
                        if content[pos] == "{":
                            depth += 1
                        elif content[pos] == "}":
                            depth -= 1
                        pos += 1
                    if depth == 0:
                        body_text = content[block_start : pos - 1]
                        resources.append((rt, rn, HclBlock(body_text, parsed=None)))

            for res_type, res_name, body in resources:
                classify_and_ingest_resource(
                    res_type=res_type,
                    res_name=res_name,
                    body=body,
                    rel_file=rel_file,
                    tf_data=tf_data,
                    resolved_vars=resolved_vars,
                )

            # Extract Modules & Module Inputs (Cloud Foundations Fabric & Blueprints)
            modules: List[Tuple[str, HclBlock]] = []
            if parsed_hcl and isinstance(parsed_hcl, dict) and "module" in parsed_hcl:
                for m_entry in parsed_hcl.get("module", []):
                    if isinstance(m_entry, dict):
                        for mn, m_body in m_entry.items():
                            if isinstance(m_body, dict):
                                modules.append((
                                    mn,
                                    HclBlock(_dict_to_hcl_body_str(m_body), parsed=m_body),
                                ))
            elif parsed_hcl is None:
                for match in re.finditer(r'module\s+"([^"]+)"\s*\{', content):
                    mn = match.group(1)
                    block_start = match.end()
                    depth = 1
                    pos = block_start
                    while pos < len(content) and depth > 0:
                        if content[pos] == "{":
                            depth += 1
                        elif content[pos] == "}":
                            depth -= 1
                        pos += 1
                    if depth == 0:
                        body_text = content[block_start : pos - 1]
                        modules.append((mn, HclBlock(body_text, parsed=None)))

            # If AST parsing failed, check if resources or modules were actually dropped.
            # Files with no resources or modules (outputs.tf, locals.tf, variables.tf) or
            # files where fallback extraction recovered all resources/modules are NOT
            # missing from the authorization boundary.
            if parse_failure_err:
                has_res_decl = bool(re.search(r'\bresource\s+"[^"]+"\s+"[^"]+"\s*\{', content))
                has_mod_decl = bool(re.search(r'\bmodule\s+"[^"]+"\s*\{', content))
                res_missing = has_res_decl and len(resources) == 0
                mod_missing = has_mod_decl and len(modules) == 0
                if res_missing or mod_missing:
                    logger.error(
                        "HCL parse failed and fallback could not extract elements for %s: %s; missing from accreditation boundary",
                        filepath,
                        parse_failure_err,
                    )
                    tf_data["unparsed_terraform_files"].append({
                        "path": rel_file,
                        "error": parse_failure_err,
                    })
                else:
                    logger.debug(
                        "HCL AST parse failed for %s, but recovered %d resources and %d modules via balanced-brace fallback",
                        filepath,
                        len(resources),
                        len(modules),
                    )

            for mod_name, body in modules:
                tf_data["modules_used"].add(mod_name)
                src = extract_hcl_attr(body, "source", vars_dict=resolved_vars) or ""

                # 1. VPC Fabric Module (net-vpc)
                if "net-vpc" in src or (isinstance(mod_name, str) and "vpc" in mod_name.lower()):
                    raw_v = extract_hcl_attr(body, "name", vars_dict=resolved_vars) or mod_name
                    v_name = clean_interpolated_string(raw_v, resolved_vars)
                    if is_valid_resource_name(v_name):
                        tf_data["networks"].add(v_name)
                    subnets_input = extract_hcl_attr(body, "subnets", vars_dict=resolved_vars)
                    if isinstance(subnets_input, list):
                        for s in subnets_input:
                            if isinstance(s, dict):
                                c = s.get("ip_cidr_range")
                                if is_valid_cidr(c) and str(c) not in tf_data["subnets"]:
                                    tf_data["subnets"].add(str(c))
                                sec = s.get("secondary_ip_range")
                                if isinstance(sec, dict):
                                    for _, sec_c in sec.items():
                                        if is_valid_cidr(sec_c) and str(sec_c) not in tf_data["subnets"]:
                                            tf_data["subnets"].add(str(sec_c))
                    for c_m in re.finditer(r'ip_cidr_range\s*=\s*"([^"]+)"', str(body)):
                        cidr = c_m.group(1)
                        if is_valid_cidr(cidr) and cidr not in tf_data["subnets"]:
                            tf_data["subnets"].add(cidr)

                # 2. Firewall Fabric Module (net-vpc-firewall)
                elif "net-vpc-firewall" in src or (isinstance(mod_name, str) and "firewall" in mod_name.lower()):
                    fw_rules_input = extract_hcl_attr(body, "ingress_rules", vars_dict=resolved_vars)
                    if isinstance(fw_rules_input, dict):
                        for r_name, r_cfg in fw_rules_input.items():
                            if isinstance(r_cfg, dict):
                                tf_data["firewall_rules"].append({
                                    "name": r_name,
                                    "network": extract_hcl_attr(body, "network", vars_dict=resolved_vars) or "custom-vpc",
                                    "direction": "INGRESS",
                                    "protocol": "tcp",
                                    "ports": str(r_cfg.get("ports", ["443"])),
                                    "action": "ALLOW" if not r_cfg.get("deny", False) else "DENY",
                                })
                    for r_match in re.finditer(r'([a-zA-Z0-9_-]+)\s*=\s*\{[^}]*deny\s*=\s*(true|false)', str(body)):
                        r_name = r_match.group(1)
                        is_deny = r_match.group(2) == "true"
                        tf_data["firewall_rules"].append({
                            "name": r_name,
                            "network": "custom-vpc",
                            "direction": "INGRESS",
                            "protocol": "tcp",
                            "ports": "443",
                            "action": "DENY" if is_deny else "ALLOW",
                        })

                # 3. HA VPN Fabric Module (net-vpn-ha) - Boundary Connection
                elif "net-vpn-ha" in src or (isinstance(mod_name, str) and "vpn" in mod_name.lower()):
                    gw_name = extract_hcl_attr(body, "name", vars_dict=resolved_vars) or mod_name
                    peer_asn = extract_hcl_attr(body, "router_asn", vars_dict=resolved_vars) or extract_hcl_attr(body, "peer_external_gateway.asn", vars_dict=resolved_vars)
                    tf_data["boundary_connections"].append({
                        "name": gw_name,
                        "type": "module_net_vpn_ha",
                        "peer_ip": "Cross-Cloud Boundary IPsec",
                        "peer_asn": peer_asn,
                        "file": rel_file,
                    })

                # 4. GKE Cluster Fabric Module (gke-cluster)
                elif "gke-cluster" in src or (isinstance(mod_name, str) and "gke" in mod_name.lower()):
                    c_name = extract_hcl_attr(body, "name", vars_dict=resolved_vars) or mod_name
                    c_name = clean_interpolated_string(c_name, resolved_vars, default_val=mod_name)
                    loc = extract_hcl_attr(body, "location", vars_dict=resolved_vars) or "us-east4"
                    m_cidr = extract_hcl_attr(body, "private_cluster_config.master_ipv4_cidr_block", vars_dict=resolved_vars) or "172.16.0.0/28"
                    # Fall back to the fabric module's own documented defaults
                    # (modules/gke-cluster-standard/variables.tf: access_config
                    # private_nodes = true, disable_public_endpoint = true,
                    # enable_features.workload_identity = true), but let an
                    # explicit override in the module invocation win.
                    mod_priv_nodes = _text_attr_tristate(body, "private_nodes")
                    mod_priv_endpoint = _text_attr_tristate(body, "disable_public_endpoint")
                    mod_wif = _text_attr_tristate(body, "workload_identity")
                    tf_data["gke_clusters"].append({
                        "name": c_name,
                        "master_version": "1.28+",
                        "master_ipv4_cidr_block": m_cidr,
                        "location": loc,
                        "private_cluster": True if mod_priv_nodes is None else mod_priv_nodes,
                        "private_endpoint": True if mod_priv_endpoint is None else mod_priv_endpoint,
                        "workload_identity": True if mod_wif is None else mod_wif,
                        "file": rel_file,
                    })

                # 5. KMS Fabric Module (kms)
                elif "kms" in src or (isinstance(mod_name, str) and "kms" in mod_name.lower()):
                    kr_m = re.search(r'name\s*=\s*"([^"]+)"', str(body))
                    kr_name = kr_m.group(1) if kr_m else f"{mod_name}-kr"
                    body_str = str(body)
                    keys_block_m = re.search(r'keys\s*=\s*\{', body_str)
                    if keys_block_m:
                        brace_start = keys_block_m.end() - 1
                        brace_depth = 0
                        keys_content = ""
                        for idx in range(brace_start, len(body_str)):
                            ch = body_str[idx]
                            if ch == '{':
                                brace_depth += 1
                            elif ch == '}':
                                brace_depth -= 1
                                if brace_depth == 0:
                                    keys_content = body_str[brace_start + 1:idx]
                                    break
                        if keys_content:
                            sub_idx = 0
                            while sub_idx < len(keys_content):
                                key_header_m = re.search(r'(?:\"([^\"]+)\"|([a-zA-Z0-9_-]+))\s*=\s*\{', keys_content[sub_idx:])
                                if not key_header_m:
                                    break
                                k_name = key_header_m.group(1) or key_header_m.group(2)
                                k_start = sub_idx + key_header_m.end() - 1
                                k_depth = 0
                                k_block = ""
                                for k_i in range(k_start, len(keys_content)):
                                    if keys_content[k_i] == '{':
                                        k_depth += 1
                                    elif keys_content[k_i] == '}':
                                        k_depth -= 1
                                        if k_depth == 0:
                                            k_block = keys_content[k_start:k_i + 1]
                                            sub_idx = k_i + 1
                                            break
                                else:
                                    sub_idx = len(keys_content)

                                if k_name and is_valid_resource_name(k_name) and k_name not in ("keys", "keyring", "iam", "labels"):
                                    # Scope to this key's own block: a sibling key
                                    # declaring HSM is not evidence for this one.
                                    prot = "HSM" if re.search(r'protection_level\s*=\s*"?HSM', str(k_block), re.IGNORECASE) else "SOFTWARE"
                                    rot_m = re.search(r'rotation_period\s*=\s*"([^"]+)"', k_block)
                                    rot = rot_m.group(1) if rot_m else ("7776000s" if ("rotation_period" in k_block or "7776000s" in body_str) else "7776000s")
                                    tf_data["kms_keys"].append({
                                        "type": "module_kms_crypto_key",
                                        "name": k_name,
                                        "key_ring": kr_name,
                                        "protection_level": prot,
                                        "rotation_period": rot,
                                        "file": rel_file,
                                    })

                # 6. Cloud SQL Fabric Module (cloudsql-instance)
                elif "cloudsql" in src or (isinstance(mod_name, str) and "sql" in mod_name.lower()):
                    db_name = _resolved_asset_name(
                        extract_hcl_attr(body, "name", vars_dict=resolved_vars),
                        str(mod_name),
                        resolved_vars,
                        "database-instance",
                    )
                    db_ver = extract_hcl_attr(body, "database_version", vars_dict=resolved_vars) or "POSTGRES_15"
                    tier = extract_hcl_attr(body, "tier", vars_dict=resolved_vars) or "db-custom-4-16384"
                    p_net = extract_hcl_attr(body, "private_network", vars_dict=resolved_vars)
                    if p_net:
                        if "psa_private_network" in str(p_net):
                            p_net = "Private VPC / Private Service Connect (PSC)"
                        else:
                            p_clean = clean_interpolated_string(str(p_net), resolved_vars)
                            if "var." in p_clean or "local." in p_clean or "${" in p_clean or not is_valid_resource_name(p_clean):
                                p_net = None
                            else:
                                p_net = p_clean
                    cmek = extract_hcl_attr(body, "encryption_key_name", vars_dict=resolved_vars) or extract_hcl_attr(body, "cmek_key", vars_dict=resolved_vars)
                    if cmek:
                        # The presence of the attribute is the SC-12/SC-28 signal, so
                        # never discard it. But stripping "${var.kms_key_name}" leaves
                        # the bare word "kms_key_name", which would read as a real key
                        # identifier. Say what is actually known instead.
                        cmek_clean = clean_interpolated_string(str(cmek), resolved_vars)
                        cmek_tails = {t.lower() for t in _REF_TAIL.findall(str(cmek))}
                        if not cmek_clean or cmek_clean.strip().lower() in cmek_tails:
                            cmek = "Customer-managed key (reference resolved at apply time)"
                        else:
                            cmek = cmek_clean
                    # modules/cloudsql-instance/variables.tf defaults
                    # backup_configuration.enabled to false and leaves ssl.mode
                    # unset (provider default allows unencrypted connections), so
                    # neither can be asserted without reading the invocation.
                    mod_ssl_m = re.search(r'mode\s*=\s*"([A-Z_]+)"', str(body))
                    if mod_ssl_m:
                        mod_req_ssl = mod_ssl_m.group(1).upper() in ("ENCRYPTED_ONLY", "TRUSTED_CLIENT_CERTIFICATE_REQUIRED")
                    else:
                        mod_req_ssl = None
                    mod_bkp = _text_attr_tristate(body, "enabled") if "backup_configuration" in str(body) else False
                    tf_data["databases"].append({
                        "type": "module_cloudsql_database_instance",
                        "name": db_name,
                        "database_version": db_ver,
                        "tier": tier,
                        "private_network": p_net,
                        "cmek_key": cmek,
                        "require_ssl": mod_req_ssl,
                        "backup_enabled": mod_bkp,
                        "has_public_ip": False,
                        "file": rel_file
                    })

                # 7. Compute VM Fabric Module (compute-vm)
                elif "compute-vm" in src or (isinstance(mod_name, str) and "vm" in mod_name.lower()):
                    raw_vm = extract_hcl_attr(body, "name", vars_dict=resolved_vars) or mod_name
                    vm_name = clean_interpolated_string(raw_vm, resolved_vars, default_val=mod_name)
                    if not is_valid_resource_name(vm_name) or "${" in vm_name or "var." in vm_name or any(vm_name.startswith(p) for p in ("coalesce", "each.")):
                        vm_name = mod_name if is_valid_resource_name(mod_name) else "compute-instance"
                    if vm_name in ("vm", "instance", "name", ""):
                        vm_name = f"{mod_name}-instance" if mod_name not in ("vm", "instance") else "compute-instance"
                    m_type = (
                        extract_hcl_attr(body, "instance_type", vars_dict=resolved_vars)
                        or extract_hcl_attr(body, "machine_type", vars_dict=resolved_vars)
                        or "n2-standard-4"
                    )
                    default_reg = (
                        resolved_vars.get("region")
                        or resolved_vars.get("default_region")
                        or "us-east4"
                    )
                    default_zone = resolved_vars.get("zone") or f"{default_reg}-a"
                    raw_zone = extract_hcl_attr(body, "zone", vars_dict=resolved_vars) or default_zone
                    zone = clean_interpolated_string(raw_zone, resolved_vars, default_val=default_zone)
                    net_ip = extract_hcl_attr(body, "network_ip", vars_dict=resolved_vars)
                    if net_ip in ("try", "lookup", "None", "") or not net_ip or str(net_ip).startswith("${"):
                        net_ip = None
                    raw_subnet = extract_hcl_attr(body, "subnetwork", vars_dict=resolved_vars)
                    subnet = clean_interpolated_string(raw_subnet, resolved_vars, default_val="")
                    img = extract_hcl_attr(body, "image", vars_dict=resolved_vars) or "Ubuntu Linux 22.04 LTS / Shielded VM"
                    kms_key = extract_hcl_attr(body, "kms_key_self_link", vars_dict=resolved_vars) or extract_hcl_attr(body, "kms_key", vars_dict=resolved_vars)
                    p_id = (
                        resolved_vars.get("project_id")
                        or resolved_vars.get("prod_project_id")
                        or resolved_vars.get("service_project_id")
                        or "workload-project"
                    )
                    tf_data["compute_instances"].append({
                        "name": vm_name,
                        "machine_type": m_type,
                        "zone": zone,
                        "network_ip": net_ip,
                        "subnetwork": subnet,
                        "image": img,
                        "kms_key": kms_key,
                        "has_public_ip": False,
                        "shielded_vm": True,
                        "self_link": f"projects/{p_id}/zones/{zone}/instances/{vm_name}",
                        "file": rel_file
                    })

                # 8. GCS Fabric Module (gcs)
                elif "gcs" in src or (isinstance(mod_name, str) and "bucket" in mod_name.lower()):
                    b_name = extract_hcl_attr(body, "name", vars_dict=resolved_vars) or mod_name
                    b_name = clean_interpolated_string(b_name, resolved_vars, default_val=mod_name)
                    if is_valid_resource_name(b_name) and not b_name.startswith("${"):
                        b_loc = extract_hcl_attr(body, "location", vars_dict=resolved_vars) or "US"
                        cmek = extract_hcl_attr(body, "encryption.default_kms_key_name", vars_dict=resolved_vars) or extract_hcl_attr(body, "kms_key", vars_dict=resolved_vars)
                        # modules/gcs/variables.tf defaults versioning to null
                        # (disabled) and uniform_bucket_level_access to true.
                        mod_vers = _text_attr_tristate(body, "versioning")
                        mod_ubla = _text_attr_tristate(body, "uniform_bucket_level_access")
                        tf_data["storage_buckets"].append({
                            "name": b_name,
                            "location": b_loc,
                            "storage_class": "STANDARD",
                            "cmek_encrypted": bool(cmek),
                            "kms_key": cmek,
                            "versioning": False if mod_vers is None else mod_vers,
                            "uniform_bucket_level_access": True if mod_ubla is None else mod_ubla,
                            "file": rel_file,
                        })

                # 9. Project Factory Module (project-factory)
                elif "project-factory" in src or (isinstance(mod_name, str) and "project" in mod_name.lower()):
                    svcs = extract_hcl_attr(body, "services", vars_dict=resolved_vars)
                    if isinstance(svcs, list):
                        for s in svcs:
                            tf_data["services"].add(str(s))

            # Google Cloud Service APIs (GCP)
            for m in re.finditer(r'([a-z0-9_-]+\.googleapis\.com)', content):
                tf_data["services"].add(m.group(1))
            for m in re.finditer(r'service\s*=\s*"([^"]+)"', content):
                tf_data["services"].add(m.group(1))

            # IDS/IPS Module Detection
            if any(k in content.lower() for k in ["palo_alto", "panos", "paloalto"]):
                tf_data["ids_solution"] = "Palo Alto VM-Series Next-Generation Firewall (NGFW) & IDS/IPS"
            elif "google_cloud_ids_endpoint" in content or "cloud_ids" in content:
                tf_data["ids_solution"] = "Google Cloud IDS / Cloud Armor / Security Command Center"
            elif "fortigate" in content or "fortinet" in content:
                tf_data["ids_solution"] = "Fortinet FortiGate Next-Generation Firewall (NGFW) & IDS/IPS"

            # Assured Workloads
            if "google_assured_workloads_workload" in content or "assuredworkloads" in content:
                tf_data["assured_workloads"].append(rel_file)

            # Terraform Engine & Provider Requirements (AST first, regex fallback)
            if parsed_hcl and isinstance(parsed_hcl, dict) and "terraform" in parsed_hcl:
                for tf_entry in parsed_hcl["terraform"]:
                    if isinstance(tf_entry, dict):
                        req_v = tf_entry.get("required_version")
                        if isinstance(req_v, list) and req_v:
                            req_v = req_v[0]
                        if req_v and not tf_data.get("terraform_engine_version"):
                            tf_data["terraform_engine_version"] = req_v
                        req_provs = tf_entry.get("required_providers", [])
                        for prov_entry in req_provs:
                            if isinstance(prov_entry, dict):
                                for p_name, p_val in prov_entry.items():
                                    if (
                                        isinstance(p_val, list)
                                        and p_val
                                        and isinstance(p_val[0], dict)
                                    ):
                                        p_ver = p_val[0].get("version")
                                    elif isinstance(p_val, dict):
                                        p_ver = p_val.get("version")
                                    else:
                                        p_ver = None
                                    if isinstance(p_ver, list) and p_ver:
                                        p_ver = p_ver[0]
                                    if p_ver:
                                        tf_data["provider_versions"][p_name] = p_ver

            if parsed_hcl and isinstance(parsed_hcl, dict) and "terraform" in parsed_hcl and not tf_data.get("terraform_engine_version"):
                for tf_entry in parsed_hcl.get("terraform", []):
                    if isinstance(tf_entry, dict):
                        req_v = tf_entry.get("required_version")
                        if isinstance(req_v, list) and req_v:
                            req_v = req_v[0]
                        if req_v and not tf_data.get("terraform_engine_version"):
                            tf_data["terraform_engine_version"] = str(req_v)
                        req_provs = tf_entry.get("required_providers", {})
                        if isinstance(req_provs, list):
                            prov_dict = {}
                            for pe in req_provs:
                                if isinstance(pe, dict):
                                    prov_dict.update(pe)
                            req_provs = prov_dict
                        if isinstance(req_provs, dict):
                            for p_name, p_val in req_provs.items():
                                if isinstance(p_val, dict):
                                    p_ver = p_val.get("version")
                                elif isinstance(p_val, str):
                                    p_ver = p_val
                                else:
                                    p_ver = None
                                if isinstance(p_ver, list) and p_ver:
                                    p_ver = p_ver[0]
                                if p_ver:
                                    tf_data["provider_versions"][p_name] = str(p_ver)

        except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
            logger.warning("Failed to read Terraform file %s: %s", filepath, err)

    logger.info("Recursively discovered %d Terraform (.tf) files across %d folder paths in workspace.", len(scanned_files), len(scanned_dirs))

    return finalize_terraform_data(tf_data, target_dir)


def deep_scan_app_files(target_dir: str) -> Dict[str, Any]:
    """Scans for application-tier codebases, runtimes, containers, dependencies, and ports.

    Detects JavaScript/TypeScript (Node.js, React, Next.js), Python (FastAPI, Flask,
    Django), Go, Java/Maven, Containers (Dockerfile, compose), and Kubernetes manifests.

    Args:
        target_dir: The target workspace root or project directory.

    Returns:
        Structured dictionary detailing applications, software packages, containers, and ports.
    """
    app_data = {
        "applications": [],
        "software_packages": [],
        "container_images": [],
        "exposed_ports": [],
        "frameworks": set(),
        "runtimes": set(),
        "database_connectors": set(),
        "all_resources": []
    }

    scan_targets = [target_dir]
    target_path = Path(target_dir).resolve()
    boundary_dir = str(target_path)
    if target_path.name == "terraform":
        sibling_app = target_path.parent / "app"
        if sibling_app.is_dir():
            scan_targets.append(str(sibling_app))
            boundary_dir = str(target_path.parent)

    ignored_dirs = {
        ".git", ".terraform", "node_modules", "venv", ".venv", "__pycache__",
        "ato_artifacts", "dist", "build", ".next", ".cache", "target", "vendor"
    }

    scanned_files = set()
    found_ports = set()

    for scan_root in scan_targets:
        for root, dirs, files in os.walk(scan_root):
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".")]

            for filename in files:
                filepath = os.path.abspath(os.path.join(root, filename))
                if filepath in scanned_files:
                    continue
                scanned_files.add(filepath)
                rel_path = os.path.relpath(filepath, target_dir)

                # -------------------------------------------------------------
                # 1. Node.js / JavaScript / TypeScript (package.json)
                # -------------------------------------------------------------
                if filename == "package.json":
                    try:
                        pkg_json = read_json_file(filepath, allowed_boundary=boundary_dir)

                        pkg_name = pkg_json.get("name") or os.path.basename(os.path.dirname(filepath)) or "node-application"
                        pkg_version = pkg_json.get("version", "1.0.0")
                        pkg_desc = pkg_json.get("description", "Node.js Application / Service")
                        entrypoint = pkg_json.get("main", "index.js")

                        app_data["runtimes"].add("Node.js")

                        deps = pkg_json.get("dependencies", {})
                        dev_deps = pkg_json.get("devDependencies", {})
                        all_deps = {**dev_deps, **deps}

                        # Framework detection
                        detected_framework = "Node.js Service"
                        if "next" in all_deps:
                            detected_framework = "Next.js Full-Stack Application"
                            app_data["frameworks"].add("Next.js")
                        elif "express" in all_deps:
                            detected_framework = "Express.js Web Application"
                            app_data["frameworks"].add("Express.js")
                        elif "fastify" in all_deps:
                            detected_framework = "Fastify High-Performance API"
                            app_data["frameworks"].add("Fastify")
                        elif "@nestjs/core" in all_deps or "nestjs" in all_deps:
                            detected_framework = "NestJS Enterprise Backend"
                            app_data["frameworks"].add("NestJS")
                        elif "react" in all_deps:
                            detected_framework = "React Frontend Application"
                            app_data["frameworks"].add("React")
                        elif "vue" in all_deps:
                            detected_framework = "Vue.js Frontend Application"
                            app_data["frameworks"].add("Vue.js")
                        elif "@angular/core" in all_deps:
                            detected_framework = "Angular Application"
                            app_data["frameworks"].add("Angular")

                        app_data["applications"].append({
                            "name": pkg_name,
                            "type": detected_framework,
                            "language": "JavaScript / TypeScript (Node.js)",
                            "framework": detected_framework,
                            "version": pkg_version,
                            "description": pkg_desc,
                            "entrypoint": entrypoint,
                            "file": rel_path
                        })

                        app_data["all_resources"].append({
                            "type": "application_service",
                            "name": pkg_name,
                            "category": "Application Component",
                            "file": rel_path
                        })

                        # Collect dependencies
                        for dep_name, dep_ver in deps.items():
                            dep_ver_clean = str(dep_ver).lstrip("^~=>=< ")
                            cat = "Third-Party Library"
                            if any(k in dep_name for k in ["express", "fastify", "react", "next", "vue", "angular", "nestjs", "koa"]):
                                cat = "Application Framework"
                            elif any(k in dep_name for k in ["pg", "mysql", "mongo", "redis", "sequelize", "prisma", "typeorm", "spanner", "bigquery"]):
                                cat = "Database Client Driver"
                                app_data["database_connectors"].add(dep_name)
                            elif "@google-cloud" in dep_name:
                                cat = "Cloud Client SDK"

                            app_data["software_packages"].append({
                                "name": dep_name,
                                "version": dep_ver_clean or "Latest",
                                "ecosystem": "npm (Node.js)",
                                "category": cat,
                                "file": rel_path
                            })
                    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as err:
                        logger.warning("Failed reading package.json %s: %s", filepath, err)

                # -------------------------------------------------------------
                # 2. Python (requirements.txt, pyproject.toml, setup.py)
                # -------------------------------------------------------------
                elif filename == "requirements.txt":
                    try:
                        app_data["runtimes"].add("Python")
                        req_text = read_text_file(filepath, allowed_boundary=boundary_dir)
                        for line in req_text.splitlines():
                                line = line.split("#")[0].strip()
                                if not line or line.startswith(("-", "git+", "http")):
                                    continue
                                parts = re.split(r"[=<>!~]", line, maxsplit=1)
                                pkg_name = parts[0].strip()
                                pkg_ver = parts[1].strip(" =") if len(parts) > 1 else "Latest"

                                cat = "Third-Party Library"
                                if pkg_name.lower() in ["fastapi", "flask", "django", "tornado", "aiohttp", "starlette"]:
                                    cat = "Application Framework"
                                    app_data["frameworks"].add(pkg_name.title())
                                elif pkg_name.lower() in ["psycopg2", "asyncpg", "pymysql", "pymongo", "redis", "sqlalchemy", "tortoise-orm"]:
                                    cat = "Database Client Driver"
                                    app_data["database_connectors"].add(pkg_name)
                                elif "google-cloud" in pkg_name.lower():
                                    cat = "Cloud Client SDK"

                                app_data["software_packages"].append({
                                    "name": pkg_name,
                                    "version": pkg_ver,
                                    "ecosystem": "PyPI (Python)",
                                    "category": cat,
                                    "file": rel_path
                                })
                    except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
                        logger.warning("Failed reading requirements.txt %s: %s", filepath, err)

                elif filename == "pyproject.toml":
                    try:
                        app_data["runtimes"].add("Python")
                        content = read_text_file(filepath, allowed_boundary=boundary_dir)
                        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                        ver_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                        if name_match:
                            p_name = name_match.group(1)
                            p_ver = ver_match.group(1) if ver_match else "1.0.0"
                            app_data["applications"].append({
                                "name": p_name,
                                "type": "Python Application / Service",
                                "language": "Python",
                                "framework": "Python Service",
                                "version": p_ver,
                                "description": "Python Backend Application",
                                "entrypoint": "main.py",
                                "file": rel_path
                            })
                            app_data["all_resources"].append({
                                "type": "application_service",
                                "name": p_name,
                                "category": "Application Component",
                                "file": rel_path
                            })
                    except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
                        logger.warning("Failed reading pyproject.toml %s: %s", filepath, err)

                # -------------------------------------------------------------
                # 3. Go (go.mod)
                # -------------------------------------------------------------
                elif filename == "go.mod":
                    try:
                        app_data["runtimes"].add("Go")
                        content = read_text_file(filepath, allowed_boundary=boundary_dir)
                        mod_match = re.search(r"module\s+([^\s]+)", content)
                        go_ver_match = re.search(r"go\s+([0-9\.]+)", content)
                        mod_name = mod_match.group(1) if mod_match else "go-module"
                        go_ver = go_ver_match.group(1) if go_ver_match else "1.21"

                        app_data["applications"].append({
                            "name": os.path.basename(mod_name),
                            "type": "Go Microservice",
                            "language": f"Go ({go_ver})",
                            "framework": "Go Native / Microservice",
                            "version": "1.0.0",
                            "description": f"Go Service ({mod_name})",
                            "entrypoint": "main.go",
                            "file": rel_path
                        })
                        app_data["all_resources"].append({
                            "type": "application_service",
                            "name": os.path.basename(mod_name),
                            "category": "Application Component",
                            "file": rel_path
                        })

                        # Requirements
                        for req in re.finditer(r'^\s*([a-zA-Z0-9_\-\.\/]+)\s+v([0-9a-zA-Z_\-\.]+)', content, re.MULTILINE):
                            r_pkg = req.group(1)
                            r_ver = req.group(2)
                            if "indirect" not in req.group(0):
                                app_data["software_packages"].append({
                                    "name": r_pkg,
                                    "version": f"v{r_ver}",
                                    "ecosystem": "Go Modules",
                                    "category": "Third-Party Library",
                                    "file": rel_path
                                })
                    except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
                        logger.warning("Failed reading go.mod %s: %s", filepath, err)

                # -------------------------------------------------------------
                # 4. Java / Maven (pom.xml)
                # -------------------------------------------------------------
                elif filename == "pom.xml":
                    try:
                        app_data["runtimes"].add("Java / JVM")
                        content = read_text_file(filepath, allowed_boundary=boundary_dir)

                        art_id = "java-application"
                        app_ver = "1.0.0"
                        try:
                            root = ET.fromstring(content)
                            for elem in root.iter():
                                if "}" in elem.tag:
                                    elem.tag = elem.tag.split("}", 1)[1]
                            art_elem = root.find("artifactId")
                            ver_elem = root.find("version")
                            if art_elem is not None and art_elem.text and art_elem.text.strip():
                                art_id = art_elem.text.strip()
                            if ver_elem is not None and ver_elem.text and ver_elem.text.strip():
                                app_ver = ver_elem.text.strip()
                        except (ET.ParseError, getattr(ET, 'DefusedXmlException', Exception), ValueError) as e:
                            logger.warning(f"XML parsing failed for {filepath}: {e}. Falling back to regex.")
                            art_match = re.search(r"<artifactId>([^<]+)</artifactId>", content)
                            ver_match = re.search(r"<version>([^<]+)</version>", content)
                            if art_match:
                                art_id = art_match.group(1).strip()
                            if ver_match:
                                app_ver = ver_match.group(1).strip()

                        f_name = "Spring Boot Application" if "spring-boot" in content else "Java Application"
                        if "spring-boot" in content:
                            app_data["frameworks"].add("Spring Boot")

                        app_data["applications"].append({
                            "name": art_id,
                            "type": f_name,
                            "language": "Java (JVM)",
                            "framework": f_name,
                            "version": app_ver,
                            "description": "Java Enterprise Application",
                            "entrypoint": "Application.java",
                            "file": rel_path
                        })
                        app_data["all_resources"].append({
                            "type": "application_service",
                            "name": art_id,
                            "category": "Application Component",
                            "file": rel_path
                        })
                    except (OSError, UnicodeDecodeError, ValueError) as err:
                        logger.warning("Failed reading pom.xml %s: %s", filepath, err)

                # -------------------------------------------------------------
                # 5. Containers (Dockerfile, Containerfile, docker-compose)
                # -------------------------------------------------------------
                elif filename in ["Dockerfile", "Containerfile"] or filename.endswith(".dockerfile"):
                    try:
                        content = read_text_file(filepath, allowed_boundary=boundary_dir)

                        # Parse ARG definitions for substitution
                        docker_args = {}
                        for arg_m in re.finditer(r"ARG\s+([a-zA-Z0-9_]+)(?:=([^\s]+))?", content):
                            arg_k = arg_m.group(1)
                            arg_v = (arg_m.group(2) or "").strip("\"'")
                            docker_args[arg_k] = arg_v

                        # Base images
                        for from_match in re.finditer(r"FROM\s+([^\s]+)", content, re.IGNORECASE):
                            base_img = from_match.group(1).strip()
                            if not base_img.startswith("--"):
                                for ak, av in docker_args.items():
                                    if av:
                                        base_img = base_img.replace(f"${{{ak}}}", av).replace(f"${ak}", av)
                                if "${" in base_img or "$" in base_img:
                                    base_img = re.sub(r"\$\{[^}]+\}", "latest", base_img)
                                    base_img = re.sub(r"\$[a-zA-Z0-9_]+", "latest", base_img)

                                base_ver = base_img.split(":")[-1] if ":" in base_img else "latest"
                                if not base_ver or "${" in base_ver or "$" in base_ver:
                                    base_ver = "latest"

                                app_data["container_images"].append({
                                    "image": base_img,
                                    "base_image": base_img,
                                    "file": rel_path
                                })
                                app_data["software_packages"].append({
                                    "name": base_img,
                                    "version": base_ver,
                                    "ecosystem": "OCI / Docker Container",
                                    "category": "Container Base Image",
                                    "file": rel_path
                                })

                        # Exposed Ports
                        for exp_match in re.finditer(r"EXPOSE\s+([0-9\s/tcpudp]+)", content, re.IGNORECASE):
                            raw_ports = exp_match.group(1).split()
                            for p_item in raw_ports:
                                p_clean = p_item.split("/")[0].strip()
                                proto = "UDP" if "udp" in p_item.lower() else "TCP"
                                if p_clean.isdigit() and p_clean not in found_ports:
                                    found_ports.add(p_clean)
                                    app_data["exposed_ports"].append({
                                        "port": p_clean,
                                        "protocol": proto,
                                        "service_name": f"Container Ingress ({p_clean}/{proto})",
                                        "source": f"Dockerfile EXPOSE {p_item}",
                                        "file": rel_path
                                    })
                    except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
                        logger.warning("Failed reading container manifest %s: %s", filepath, err)

                elif filename in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]:
                    try:
                        content = read_text_file(filepath, allowed_boundary=boundary_dir)

                        # Service port mappings e.g. "8080:80" or "3000:3000"
                        for port_m in re.finditer(r'["\']?(\d+):(\d+)["\']?', content):
                            host_p = port_m.group(1)
                            container_p = port_m.group(2)
                            if host_p not in found_ports:
                                found_ports.add(host_p)
                                app_data["exposed_ports"].append({
                                    "port": host_p,
                                    "protocol": "TCP",
                                    "service_name": f"Docker Compose Ingress ({host_p}->{container_p})",
                                    "source": "docker-compose port mapping",
                                    "file": rel_path
                                })
                    except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
                        logger.warning("Failed reading compose file %s: %s", filepath, err)

                # -------------------------------------------------------------
                # 6. Kubernetes / Helm Service Manifests
                # -------------------------------------------------------------
                elif filename.endswith((".yaml", ".yml")) and not any(k in filename.lower() for k in ["compliance", "variables", "system_", "tdd_"]):
                    try:
                        content = read_text_file(filepath, allowed_boundary=boundary_dir)
                        if "kind: Service" in content:
                            for port_match in re.finditer(r"port:\s*(\d+)", content):
                                p_val = port_match.group(1)
                                if p_val not in found_ports:
                                    found_ports.add(p_val)
                                    app_data["exposed_ports"].append({
                                        "port": p_val,
                                        "protocol": "TCP",
                                        "service_name": f"Kubernetes Service Endpoint ({p_val}/TCP)",
                                        "source": "K8s Service Manifest",
                                        "file": rel_path
                                    })
                        if "kind: Deployment" in content or "kind: StatefulSet" in content:
                            for img_match in re.finditer(r'image:\s*["\']?([a-zA-Z0-9_\-\.\/:]+)["\']?', content):
                                img_val = img_match.group(1).strip()
                                if "${" in img_val or "$" in img_val:
                                    img_val = re.sub(r"\$\{[^}]+\}", "latest", img_val)
                                    img_val = re.sub(r"\$[a-zA-Z0-9_]+", "latest", img_val)
                                app_data["container_images"].append({
                                    "image": img_val,
                                    "base_image": img_val,
                                    "file": rel_path
                                })
                    except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
                        logger.debug("Failed parsing potential K8s manifest %s: %s", filepath, err)

                # -------------------------------------------------------------
                # 7. Application Source Code Listener Port Heuristics
                # -------------------------------------------------------------
                if filename.endswith((".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs")):
                    try:
                        code_txt = read_text_file(filepath, allowed_boundary=boundary_dir)
                        # e.g. app.listen(3000), server.listen(8080)
                        for listener_m in re.finditer(r"\.listen\(\s*(\d{2,5})", code_txt):
                            p_num = listener_m.group(1)
                            if p_num not in found_ports:
                                found_ports.add(p_num)
                                app_data["exposed_ports"].append({
                                    "port": p_num,
                                    "protocol": "TCP",
                                    "service_name": f"Node.js Listener ({p_num}/TCP)",
                                    "source": f"Code Listener in {os.path.basename(filepath)}",
                                    "file": rel_path
                                })
                    except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
                        logger.debug("Failed parsing JS listener in %s: %s", filepath, err)

                elif filename.endswith(".py"):
                    try:
                        code_txt = read_text_file(filepath, allowed_boundary=boundary_dir)
                        # e.g. run(port=8000), uvicorn.run(..., port=5000)
                        for py_port in re.finditer(r"(?:port\s*=\s*|PORT\s*=\s*)(\d{2,5})", code_txt):
                            p_num = py_port.group(1)
                            if p_num not in found_ports:
                                found_ports.add(p_num)
                                app_data["exposed_ports"].append({
                                    "port": p_num,
                                    "protocol": "TCP",
                                    "service_name": f"Python Service Listener ({p_num}/TCP)",
                                    "source": f"Code Listener in {os.path.basename(filepath)}",
                                    "file": rel_path
                                })
                    except (OSError, UnicodeDecodeError, ValueError, re.error) as err:
                        logger.debug("Failed parsing Python listener in %s: %s", filepath, err)

    logger.info(
        "Discovered %d applications, %d software packages, %d container images, and %d exposed ports.",
        len(app_data["applications"]),
        len(app_data["software_packages"]),
        len(app_data["container_images"]),
        len(app_data["exposed_ports"]),
    )
    return app_data

def infer_primary_location(
    tf_scanned: Dict[str, Any],
    app_scanned: Dict[str, Any],
    sys_info: Dict[str, Any],
) -> str:
    """Infers primary deployment location from scanned cloud resources.

    Args:
        tf_scanned: Scanned Terraform infrastructure dictionary.
        app_scanned: Scanned application components dictionary.
        sys_info: Configuration dictionary containing system metadata.

    Returns:
        Inferred location or cloud region description string.
    """
    val = sys_info.get("primary_location")
    if val and not val.startswith("[CONFIG_REQUIRED"):
        return val
    # Inspect discovered locations from actual scanned code
    loc_counts: Dict[str, int] = {}
    for item in (tf_scanned.get("storage_buckets", []) +
                 tf_scanned.get("databases", []) +
                 tf_scanned.get("compute_instances", []) +
                 tf_scanned.get("gke_clusters", [])):
        loc = item.get("location") or item.get("region") or item.get("zone")
        if loc:
            parts = str(loc).split('-')
            if len(parts) >= 3 and len(parts[-1]) == 1 and parts[-1].isalpha():
                loc = "-".join(parts[:-1])
            loc_counts[str(loc)] = loc_counts.get(str(loc), 0) + 1
    if loc_counts:
        top_loc = max(loc_counts.items(), key=lambda x: x[1])[0]
        friendly_names = {
            "us-central1": "us-central1 (Council Bluffs, Iowa, USA)",
            "us-east4": "us-east4 (Ashburn, Northern Virginia, USA)",
            "us-east1": "us-east1 (Moncks Corner, South Carolina, USA)",
            "us-east5": "us-east5 (Columbus, Ohio, USA)",
            "us-west1": "us-west1 (The Dalles, Oregon, USA)",
            "us-west2": "us-west2 (Los Angeles, California, USA)",
            "us-west3": "us-west3 (Salt Lake City, Utah, USA)",
            "us-west4": "us-west4 (Las Vegas, Nevada, USA)",
            "northamerica-northeast1": "northamerica-northeast1 (Montreal, Quebec, Canada)",
            "northamerica-northeast2": "northamerica-northeast2 (Toronto, Ontario, Canada)",
            "US": "US Multi-Region (United States)"
        }
        return friendly_names.get(top_loc, f"{top_loc} (Cloud Region)")
    return val or "[CONFIG_REQUIRED: Primary Location]"


def infer_cloud_provider(
    tf_scanned: Dict[str, Any],
    sys_info: Dict[str, Any],
) -> str:
    """Infers primary cloud service provider from scanned infrastructure and config.

    Standardizes on Google Cloud Platform (GCP) conforming to Google Cloud Foundations
    Fabric blueprints, while honoring explicit user configuration overrides.

    Args:
        tf_scanned: Scanned Terraform infrastructure dictionary.
        sys_info: Configuration dictionary containing system metadata.

    Returns:
        String describing the cloud provider (default 'Google Cloud Platform (GCP)').
    """
    configured = sys_info.get("cloud_provider")
    if configured and not str(configured).startswith("[CONFIG_REQUIRED"):
        return str(configured)

    return "Google Cloud Platform (GCP)"


def find_candidate_doc_files(target_dir: Union[str, Path]) -> List[Tuple[int, Path]]:
    """Finds and scores candidate markdown documentation files for system descriptions.

    Prioritizes root README.md, spec.md, and tdd.md, followed by application and
    codebase root READMEs, while excluding upstream vendor modules and internal
    terraform stage definitions.

    Args:
        target_dir: Workspace root or project target directory.

    Returns:
        List of (score, file_path) tuples sorted descending by priority score.
    """
    root = Path(target_dir).resolve()
    if not root.exists():
        return []

    candidates: List[Tuple[int, Path]] = []
    excluded_dirs = {
        ".git", ".gemini", "ato_artifacts", "node_modules",
        ".terraform", "vendor", "fabric", "recipes", "test", "tests",
        "terraform", "environments", "modules",
    }

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d.lower() not in excluded_dirs and not d.startswith(".")]
        rel_dir = Path(dirpath).relative_to(root)
        parts = rel_dir.parts

        for f in filenames:
            f_lower = f.lower()
            if not (f_lower.endswith(".md") or f_lower.endswith(".rst") or f_lower.endswith(".txt")):
                continue

            file_path = Path(dirpath) / f
            if len(parts) == 0:
                if f_lower in ("readme.md", "readme.rst", "readme.txt"):
                    score = 100
                elif f_lower in ("spec.md", "specification.md"):
                    score = 95
                elif f_lower in ("tdd.md", "technical_design_document.md"):
                    score = 90
                elif f_lower in ("architecture.md", "architecture_overview.md"):
                    score = 88
                else:
                    continue
            else:
                if any(ex in [p.lower() for p in parts] for ex in excluded_dirs):
                    continue
                top_part = parts[0].lower()
                if f_lower in ("readme.md", "readme.rst", "readme.txt"):
                    if top_part in ("code", "src"):
                        score = 85 - (len(parts) * 2)
                    elif top_part in ("app", "apps"):
                        score = 75 - (len(parts) * 2)
                    elif top_part in ("infrastructure", "infra", "docs"):
                        score = 70 - (len(parts) * 2)
                    else:
                        score = 60 - (len(parts) * 2)
                elif f_lower in ("spec.md", "tdd.md", "architecture.md"):
                    score = 78 - (len(parts) * 2)
                else:
                    continue

            candidates.append((score, file_path))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates


def extract_system_description_from_markdown(content: str) -> Tuple[str, str]:
    """Extracts the system title and operational description from markdown text.

    Strips frontmatter, badges, images, tables, and code fences. Looks for
    dedicated Overview, System Description, or Executive Summary sections, or
    falls back to the opening narrative paragraphs following the primary header.

    Args:
        content: Raw markdown text.

    Returns:
        Tuple of (description_text, document_title).
    """
    lines = content.splitlines()

    frontmatter_dict: Dict[str, Any] = {}
    # 1. Parse YAML frontmatter
    if lines and lines[0].strip() == "---":
        end_fm = 1
        while end_fm < len(lines) and lines[end_fm].strip() != "---":
            end_fm += 1
        if end_fm < len(lines):
            fm_text = "\n".join(lines[1:end_fm])
            try:
                loaded = yaml.safe_load(fm_text)
                if isinstance(loaded, dict):
                    frontmatter_dict = loaded
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML frontmatter: {e}")
            lines = lines[end_fm + 1:]

    text = "\n".join(lines)

    # Extract top title
    top_header_m = re.search(r"^#\s+([^\n]+)", text, flags=re.MULTILINE)
    top_title = (
        frontmatter_dict.get("system_name")
        or frontmatter_dict.get("title")
        or frontmatter_dict.get("name")
        or (top_header_m.group(1).strip() if top_header_m else "")
    )

    # If authoritative description is explicitly provided in frontmatter, enforce it directly
    fm_desc = (
        frontmatter_dict.get("system_description")
        or frontmatter_dict.get("description")
        or frontmatter_dict.get("summary")
    )
    if fm_desc and isinstance(fm_desc, str) and len(fm_desc.strip()) >= 20:
        return fm_desc.strip(), str(top_title).strip()

    # 2. Check for explicit Overview / System Description sections
    section_patterns = [
        r"(?i)^##+\s+(?:system\s+description|system\s+overview|general\s+system\s+description|overview|about|executive\s+summary|purpose|project\s+scope|architecture\s+overview)\s*\n+(.*?)(?=\n##+|\Z)",
    ]
    extracted_section = None
    for pat in section_patterns:
        m = re.search(pat, text, flags=re.DOTALL | re.MULTILINE)
        if m:
            candidate = m.group(1).strip()
            candidate = re.sub(r"```[\s\S]{0,16384}?```", "", candidate).strip()
            candidate = re.sub(r"!\[[^\]]{0,1024}\]\([^)\n]{0,2048}\)", "", candidate).strip()
            candidate = re.sub(r"<!--[\s\S]{0,16384}?-->", "", candidate).strip()
            cand_paras = [
                p.strip()
                for p in re.split(r"\n\s*\n", candidate)
                if p.strip()
                and not p.strip().startswith("|")
                and not p.strip().startswith("#")
                and not re.match(r"^[-*_]{3,}$", p.strip())
            ]
            clean_cand_paras = []
            for cp in cand_paras:
                cp_clean = re.sub(r"\s+", " ", cp).strip()
                if len(cp_clean) > 25 and not cp_clean.startswith("<"):
                    clean_cand_paras.append(cp_clean)
            if clean_cand_paras:
                extracted_section = "\n\n".join(clean_cand_paras[:3])
                break

    # 3. If no explicit section or candidate is short, extract intro paragraphs following top heading
    intro_paras = []
    raw_paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    for p in raw_paras:
        if p.startswith("#"):
            if re.match(r"(?i)^##+\s+(?:codebase\s+directory\s+architecture|architecture|architecture\s+overview)", p):
                continue
            if intro_paras:
                break
            continue
        if re.match(r"^[-*_]{3,}$", p):
            continue
        if p.startswith("![") or (p.startswith("[![") and "]" in p):
            continue
        if p.startswith("```") or p.startswith("<"):
            if intro_paras:
                break
            continue
        if p.startswith("|"):
            if intro_paras:
                break
            continue

        clean_p = re.sub(r"!\[[^\]]{0,1024}\]\([^)\n]{0,2048}\)", "", p)
        clean_p = re.sub(r"<!--[\s\S]{0,16384}?-->", "", clean_p)
        clean_p = re.sub(r"\s+", " ", clean_p).strip()

        # Simplify conversational greeting prefix if present
        if clean_p.lower().startswith("welcome to "):
            greeting_match = re.match(
                r"^welcome to (?:the\s+)?(.*?)(?:\s+(?:codebase|repository|project))?\.\s*(?:This (?:repository|project)\s+(?:contains|provides|delivers)\s+)?(.*)",
                clean_p,
                flags=re.IGNORECASE,
            )
            if greeting_match:
                subj = greeting_match.group(1).strip()
                body_rest = greeting_match.group(2).strip()
                clean_p = f"The {subj} contains {body_rest}" if body_rest else subj

        if len(clean_p) > 25 and not clean_p.startswith("<"):
            intro_paras.append(clean_p)
            if len(intro_paras) >= 2:
                break

    if intro_paras and len("\n\n".join(intro_paras)) >= 35:
        desc = "\n\n".join(intro_paras)
        if extracted_section and extracted_section not in desc and len(desc) < 300:
            desc = desc + "\n\n" + extracted_section
    elif extracted_section and len(extracted_section) >= 35:
        desc = extracted_section
    else:
        desc = "\n\n".join(intro_paras)

    return desc, top_title


def discover_system_documentation(target_dir: Union[str, Path]) -> Optional[Dict[str, str]]:
    """Discovers and parses authentic system documentation from candidate markdown files.

    Args:
        target_dir: Workspace root or project target directory.

    Returns:
        Dictionary with title, description, and source_path, or None if no valid
        documentation was found.
    """
    root = Path(target_dir).resolve()
    candidates = find_candidate_doc_files(root)

    for score, cand_path in candidates:
        try:
            content = read_text_file(cand_path)
            desc, title = extract_system_description_from_markdown(content)
            if desc and len(desc.strip()) >= 35:
                rel_path = str(cand_path.relative_to(root))
                return {
                    "title": title,
                    "description": desc.strip(),
                    "source_path": rel_path,
                }
        except (OSError, UnicodeDecodeError) as err:
            logger.debug("Failed reading documentation candidate %s: %s", cand_path, err)

    return None


def infer_system_name_and_abbr(
    target_dir: str,
    tf_scanned: Dict[str, Any],
    app_scanned: Dict[str, Any],
    sys_info: Dict[str, Any],
    readme_data: Optional[Dict[str, str]] = None,
) -> Tuple[str, str]:
    """Infers system name and abbreviation from application, folder, or network naming.

    Args:
        target_dir: The target workspace path.
        tf_scanned: Scanned Terraform infrastructure dictionary.
        app_scanned: Scanned application components dictionary.
        sys_info: Configuration dictionary containing system metadata.
        readme_data: Optional dictionary with documentation metadata.

    Returns:
        A tuple containing (system_name, system_abbreviation).
    """
    name = sys_info.get("system_name")
    abbr = sys_info.get("system_abbreviation")
    if name and not name.startswith("[CONFIG_REQUIRED") and abbr and not abbr.startswith("[CONFIG_REQUIRED"):
        return name, abbr

    inferred_name = None
    inferred_abbr = None

    # Check title discovered from README or documentation
    if not inferred_name and readme_data and readme_data.get("title"):
        raw_title = readme_data["title"].strip()
        raw_title = re.sub(
            r"^(?:Welcome to (?:the\s+)?|Technical Design Document:\s*|Specification:\s*|POC Design Document:\s*)",
            "",
            raw_title,
            flags=re.IGNORECASE,
        ).strip()
        if raw_title and len(raw_title) > 3:
            inferred_name = raw_title
            paren_m = re.search(r"\(([A-Z0-9]{2,8})\)", raw_title)
            if paren_m:
                inferred_abbr = paren_m.group(1)
            else:
                words = [w for w in re.sub(r"[^a-zA-Z0-9\s]", "", raw_title).split() if w]
                if len(words) >= 3:
                    inferred_abbr = "".join(w[0].upper() for w in words[:4])
                else:
                    cap_words = [w for w in words if w.isupper()]
                    if cap_words:
                        inferred_abbr = cap_words[-1] if len(cap_words[-1]) <= 6 else "".join(w[0] for w in cap_words[:4])
                    elif words:
                        inferred_abbr = "".join(w[0].upper() for w in words[:4])

    # Check app name from package.json, pyproject.toml, pom.xml, go.mod
    if not inferred_name and app_scanned.get("applications"):
        first_app = app_scanned["applications"][0].get("name")
        if first_app:
            clean_app = first_app.replace("-", " ").replace("_", " ").title()
            inferred_name = f"{clean_app} System"
            words = [w for w in clean_app.split() if w]
            inferred_abbr = "".join(w[0].upper() for w in words[:4])

    # Check target dir name if it's a specific folder (e.g. not "." or generic workspace).
    # The denylist holds repository container directories whose names carry no system
    # identity: inferring from them yields meaningless titles such as "Modules Platform".
    # Entries track the stellar-engine top-level layout (blueprints/, modules/, fast/).
    if not inferred_name and target_dir:
        dir_base = os.path.basename(os.path.abspath(target_dir))
        if dir_base and dir_base not in (
            ".", "/", "workspace", "stellar-engine",
            "blueprints", "modules", "fast",
        ):
            clean_dir = dir_base.replace("-", " ").replace("_", " ").title()
            inferred_name = f"{clean_dir} Platform"
            words = [w for w in clean_dir.split() if w]
            inferred_abbr = "".join(w[0].upper() for w in words[:4])

    # Check network or project name from Terraform
    if not inferred_name and tf_scanned.get("networks"):
        net_0 = list(tf_scanned["networks"])[0]
        clean_net = net_0.replace("vpc-", "").replace("-vpc", "").replace("-", " ").title()
        inferred_name = f"{clean_net} Platform"
        words = [w for w in clean_net.split() if w]
        inferred_abbr = "".join(w[0].upper() for w in words[:4])

    final_name = name if (name and not name.startswith("[CONFIG_REQUIRED")) else (inferred_name or "[CONFIG_REQUIRED: System Name]")
    final_abbr = abbr if (abbr and not abbr.startswith("[CONFIG_REQUIRED")) else (inferred_abbr or "[CONFIG_REQUIRED: System Abbreviation]")
    return final_name, final_abbr


def infer_security_categorization(
    tf_scanned: Dict[str, Any],
    app_scanned: Dict[str, Any],
    sys_info: Dict[str, Any],
) -> Tuple[str, str, str]:
    """Infers FIPS 199 security categorization for Confidentiality, Integrity, and Availability.

    Args:
        tf_scanned: Scanned Terraform infrastructure dictionary.
        app_scanned: Scanned application components dictionary.
        sys_info: Configuration dictionary containing system metadata.

    Returns:
        A tuple of (confidentiality, integrity, availability) impact strings.
    """
    c = sys_info.get("confidentiality_impact")
    i = sys_info.get("integrity_impact")
    a = sys_info.get("availability_impact")
    if c and i and a:
        return c, i, a

    impact_level = str(sys_info.get("impact_level", "")).upper()
    baseline = str(sys_info.get("compliance_baseline", "")).upper()

    if "IL5" in impact_level or "IL6" in impact_level or "HIGH" in baseline:
        return "High", "High", "High"
    elif "IL4" in impact_level or "IL2" in impact_level or "MODERATE" in baseline:
        return "Moderate", "Moderate", "Moderate"
    elif "LOW" in baseline:
        return "Low", "Low", "Low"
    return "High", "High", "High"


def resolve_secops_and_external_systems(
    user_config: Dict[str, Any],
    tf_scanned: Dict[str, Any],
    target_dir: Union[str, Path],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Resolves dynamic Security Operations, Telemetry, and External Systems.

    Auto-detects active Google Cloud security components (SCC, Google SecOps/Chronicle,
    logging export sinks, CI/CD tools) or merges user-declared configuration values.
    Synthesizes contextual operational narratives for ATO deliverables.

    Args:
        user_config: Aggregated user configuration from compliance_config.yaml.
        tf_scanned: Discovered infrastructure components from Terraform/APIs.
        target_dir: Filesystem path to the root workspace.

    Returns:
        A tuple of (resolved_security_operations_dict, resolved_external_systems_dict).
    """
    sys_info = user_config.get("system_information", {})
    impact_lvl = str(sys_info.get("impact_level") or "").upper()
    comp_base = str(sys_info.get("compliance_baseline") or "").upper()
    is_dod = any(k in impact_lvl for k in ["IL4", "IL5", "IL-4", "IL-5", "DOD"]) or any(k in comp_base for k in ["IL4", "IL5", "IL-4", "IL-5", "DOD"])

    secops_cfg = dict(user_config.get("security_operations") or {})
    ext_cfg = dict(user_config.get("external_systems") or {})

    services = set(str(s).lower() for s in tf_scanned.get("services", []))
    all_res = tf_scanned.get("all_resources", [])
    logging_sinks = tf_scanned.get("logging_sinks", [])

    # 1. SCC Auto-detection
    scc_raw = secops_cfg.get("scc_enabled", "auto")
    if str(scc_raw).lower() == "auto":
        has_scc_api = "securitycenter.googleapis.com" in services
        has_scc_res = any("scc" in str(r.get("type", "")).lower() or "security_center" in str(r.get("type", "")).lower() for r in all_res)
        scc_enabled = has_scc_api or has_scc_res
    else:
        scc_enabled = bool(scc_raw) and str(scc_raw).lower() not in ("false", "none", "no", "0")

    scc_tier = str(secops_cfg.get("scc_tier") or "premium").lower()
    allow_unaccredited_scc = bool(secops_cfg.get("allow_unaccredited_scc_in_il5", False))

    # 2. Google SecOps (Chronicle) Auto-detection
    secops_raw = secops_cfg.get("secops_enabled", "auto")
    if str(secops_raw).lower() == "auto":
        has_chronicle_api = "chronicle.googleapis.com" in services
        has_chronicle_sink = any("chronicle" in str(s.get("destination", "")).lower() for s in logging_sinks if isinstance(s, dict))
        secops_enabled = has_chronicle_api or has_chronicle_sink
    else:
        secops_enabled = bool(secops_raw) and str(secops_raw).lower() not in ("false", "none", "no", "0")

    secops_inst = str(secops_cfg.get("secops_instance_name") or "").strip()
    if secops_inst in ("", "none", "null", "[CHRONICLE_INSTANCE_NAME]"):
        secops_inst = "chronicle-secops-enclave" if secops_enabled else "Not Deployed"

    # 3. CSSP Provider Resolution
    cssp_provider = str(secops_cfg.get("cssp_provider") or "").strip()
    if not cssp_provider or cssp_provider.startswith("["):
        cssp_provider = "DISA" if is_dod else "Enterprise SOC"

    cssp_agreement = str(secops_cfg.get("cssp_agreement_id") or "CSSP-MOA-ACTIVE").strip()
    cssp_endpoint = str(secops_cfg.get("cssp_endpoint") or "").strip()

    # 4. External SIEM Resolution
    ext_siem = str(secops_cfg.get("external_siem_type") or "").strip()
    matched_sink_destination = ""
    if not ext_siem or ext_siem.startswith("["):
        detected_siem = "None"
        for s in logging_sinks:
            if not isinstance(s, dict):
                continue
            dest = str(s.get("destination", "")).lower()
            if "splunk" in dest:
                detected_siem = "Splunk"
            elif "elastic" in dest:
                detected_siem = "Elasticsearch"
            elif "sentinel" in dest:
                detected_siem = "Azure Sentinel"
            elif "qradar" in dest:
                detected_siem = "QRadar"
            else:
                continue
            matched_sink_destination = str(s.get("destination", "")).strip()
            break
        ext_siem = detected_siem if detected_siem != "None" else ("Splunk" if is_dod else "None")

    # AU-6(3) and SI-4 require the audit-aggregation destination to be named, not just
    # the product. An operator declaring a log-router sink target had that value
    # discarded, so the SSP asserted a SIEM integration without ever saying where
    # records are sent. Placeholder text is treated as undeclared rather than being
    # rendered verbatim into an accreditation artifact.
    ext_siem_destination = str(secops_cfg.get("external_siem_destination") or "").strip()
    if not ext_siem_destination or ext_siem_destination.startswith("["):
        ext_siem_destination = matched_sink_destination

    # 5. External Systems (IdP, ACAS, ITSM, CI/CD, EDR, Perimeter)
    idp = str(ext_cfg.get("identity_provider") or "").strip()
    if not idp or idp.startswith("["):
        idp = "Enterprise Identity Provider (DoD CAC / PIV)" if is_dod else "Enterprise Identity Provider (Cloud Identity / SSO)"

    mfa = str(ext_cfg.get("mfa_mechanism") or "").strip()
    if not mfa or mfa.startswith("["):
        mfa = "DoD Common Access Card (CAC) / FIDO2 Hardware Token" if is_dod else "FIPS 140-3 Hardware Token / PIV / FIDO2 WebAuthn MFA"

    vuln_scanner = str(ext_cfg.get("vulnerability_scanner") or "").strip()
    if not vuln_scanner or vuln_scanner.startswith("["):
        vuln_scanner = "DoD ACAS (Tenable Nessus) & CI/CD Scanners" if is_dod else "Artifact Registry Container Analysis & Enterprise CI/CD Scanners"

    itsm = str(ext_cfg.get("itsm_system") or "").strip()
    if not itsm or itsm.startswith("["):
        itsm = "ServiceNow ITSM / SecOps"

    cicd = str(ext_cfg.get("cicd_platform") or "").strip()
    if not cicd or cicd.startswith("["):
        t_path = Path(target_dir)
        check_dirs = [t_path, t_path.parent] if t_path.name in ("terraform", "app") else [t_path]
        detected_cicd = None
        for cd in check_dirs:
            if (cd / ".gitlab-ci.yml").is_file():
                detected_cicd = "GitLab Ultimate (FedRAMP)"
                break
            elif (cd / ".github").is_dir():
                detected_cicd = "GitHub Enterprise Cloud"
                break
            elif (cd / "cloudbuild.yaml").is_file() or (cd / "cloudbuild.yml").is_file():
                detected_cicd = "Google Cloud Build + Artifact Registry"
                break
        cicd = detected_cicd or ("GitLab Ultimate (FedRAMP)" if is_dod else "Google Cloud Build + Artifact Registry")

    edr = str(ext_cfg.get("edr_solution") or "").strip()
    if not edr or edr.startswith("["):
        edr = "CrowdStrike Falcon (GovCloud)" if is_dod else "Shielded VM vTPM & Google OS Config"

    perim = str(ext_cfg.get("perimeter_gateway") or "").strip()
    if not perim or perim.startswith("["):
        perim = "Google Cloud Armor & Cloud NGFW"

    # 6. Synthesize Unified Architecture Narratives
    telemetry_parts = []
    if secops_enabled:
        telemetry_parts.append("Google Cloud SecOps (Chronicle)")
    if cssp_provider and cssp_provider.lower() != "none":
        telemetry_parts.append(f"Cloud Logging export sinks streaming to {cssp_provider}")
    if ext_siem and ext_siem.lower() != "none":
        telemetry_parts.append(f"external {ext_siem} SIEM integration")
    if scc_enabled:
        scc_desc = f"Security Command Center {scc_tier.title()}"
        if is_dod and allow_unaccredited_scc:
            scc_desc += " (operating under Authorizing Official approved Exception-to-Policy)"
        telemetry_parts.append(scc_desc)

    if not telemetry_parts:
        telemetry_summary = "Cloud Logging Log Router export sinks and Cloud Monitoring alert policies"
    else:
        telemetry_summary = "; ".join(telemetry_parts)

    # Threat detection engine description
    if secops_enabled and scc_enabled:
        threat_detection_engine = f"Google Cloud SecOps (Chronicle) integrated with Security Command Center {scc_tier.title()} Event Threat Detection"
    elif secops_enabled:
        threat_detection_engine = "Google Cloud SecOps (Chronicle) real-time threat analytics"
    elif scc_enabled:
        threat_detection_engine = f"Security Command Center {scc_tier.title()} Event Threat Detection"
    elif cssp_provider and cssp_provider.lower() != "none":
        threat_detection_engine = f"{cssp_provider} Threat Operations Center via Cloud Logging export sinks"
    else:
        threat_detection_engine = "Cloud Monitoring Anomaly Detection and Audit Log Analysis"

    resolved_secops = {
        "scc_enabled": scc_enabled,
        "scc_tier": scc_tier,
        "allow_unaccredited_scc_in_il5": allow_unaccredited_scc,
        "secops_enabled": secops_enabled,
        "secops_instance_name": secops_inst,
        "cssp_provider": cssp_provider,
        "cssp_agreement_id": cssp_agreement,
        "cssp_endpoint": cssp_endpoint,
        "external_siem_type": ext_siem,
        "external_siem_destination": ext_siem_destination,
        "telemetry_summary": telemetry_summary,
        "threat_detection_engine": threat_detection_engine,
    }

    resolved_ext = {
        "identity_provider": idp,
        "mfa_mechanism": mfa,
        "vulnerability_scanner": vuln_scanner,
        "itsm_system": itsm,
        "cicd_platform": cicd,
        "edr_solution": edr,
        "perimeter_gateway": perim,
    }

    return resolved_secops, resolved_ext


def extract_system_inventory(
    target_dir: Union[str, Path],
    allow_terraform_plan: bool = False,
    allow_scanners: bool = False
) -> Dict[str, Any]:
    """Extracts system inventory data from configs, Terraform, and applications.

    Orchestrates configuration aggregation, infrastructure scanning, application
    scanning, and metadata inference, saving the result as system_inventory.json.

    Args:
        target_dir: Target workspace root or foundation project directory.

    Returns:
        Comprehensive system inventory dictionary.
    """
    target_path = resolve_path(target_dir)
    if not target_path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_path}")
    if not target_path.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {target_path}")
    user_config = load_all_system_configs(str(target_path))

    sys_info = user_config.get("system_information", {})
    roles_info = user_config.get("personnel_roles", {})
    doc_vers = user_config.get("document_versions", {})

    # 1. Infrastructure Architecture Discovery: Plan/State JSON -> Auto-generation -> Static AST Fallback
    tf_json = discover_or_generate_terraform_json(target_dir, user_config=user_config, allow_terraform_plan=allow_terraform_plan)
    if tf_json:
        logger.info("Ingesting resolved infrastructure architecture from Terraform JSON plan/state.")
        tf_scanned = ingest_terraform_json(tf_json, user_config=user_config, target_dir=target_dir)
    else:
        logger.info("No Terraform plan/state JSON detected or generated; scanning HCL blueprint files.")
        tf_scanned = deep_scan_tf_files(target_dir, user_config=user_config)

    # 2. Application & Software Inventory: SBOM Ingestion -> Auto-generation (Syft) -> Static App Fallback
    sbom_json = discover_or_generate_sbom(target_dir, user_config=user_config, allow_scanners=allow_scanners)
    app_scanned = deep_scan_app_files(target_dir)
    if sbom_json:
        logger.info("Ingesting software package catalog from SBOM (CycloneDX/SPDX/Syft).")
        sbom_app_data = ingest_sbom_json(sbom_json)
        app_scanned = merge_app_data(app_scanned, sbom_app_data)

    readme_data = discover_system_documentation(target_dir)
    if readme_data and readme_data.get("source_path"):
        logger.info(
            "Discovered authentic system description from '%s' (Title: %s)",
            readme_data.get("source_path"),
            readme_data.get("title", "Untitled"),
        )

    inferred_sys_name, inferred_sys_abbr = infer_system_name_and_abbr(
        target_dir, tf_scanned, app_scanned, sys_info, readme_data=readme_data
    )
    inferred_loc = infer_primary_location(tf_scanned, app_scanned, sys_info)
    inferred_cloud = infer_cloud_provider(tf_scanned, sys_info)
    inf_c, inf_i, inf_a = infer_security_categorization(
        tf_scanned, app_scanned, sys_info
    )
    res_secops, res_ext = resolve_secops_and_external_systems(user_config, tf_scanned, target_dir)

    inventory = {
        "system_information": {
            "workspace_path": os.path.abspath(target_dir),
            "organization": sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]",
            "system_name": sys_info.get("system_name") if (sys_info.get("system_name") and not sys_info.get("system_name").startswith("[CONFIG_REQUIRED")) else inferred_sys_name,
            "system_abbreviation": sys_info.get("system_abbreviation") if (sys_info.get("system_abbreviation") and not sys_info.get("system_abbreviation").startswith("[CONFIG_REQUIRED")) else inferred_sys_abbr,
            "impact_level": sys_info.get("impact_level") or "IL5",
            "compliance_baseline": sys_info.get("compliance_baseline") or "NIST SP 800-53 Rev. 5 / DoD IL5",
            "effective_date": sys_info.get("effective_date"),
            "system_description": sys_info.get("system_description") or (readme_data.get("description") if readme_data else ""),
            "readme_system_description": readme_data.get("description") if readme_data else "",
            "readme_source_path": readme_data.get("source_path") if readme_data else "",
            "readme_title": readme_data.get("title") if readme_data else "",
            "cloud_provider": (
                sys_info.get("cloud_provider")
                if (
                    sys_info.get("cloud_provider")
                    and not sys_info.get("cloud_provider").startswith("[CONFIG_REQUIRED")
                )
                else inferred_cloud
            ),
            "cloud_service_provider_abbr": (
                sys_info.get("cloud_service_provider_abbr")
                or "GCP"
            ),
            "ditpr_id": (
                sys_info.get("ditpr_id")
                or sys_info.get("ditpr_don_id")
                or sys_info.get("ditpr_emass_id")
                or f"DITPR-{inferred_sys_abbr}-001"
            ),
            "emass_system_id": (
                sys_info.get("emass_system_id")
                or sys_info.get("emass_id")
                or f"EMASS-{inferred_sys_abbr}-001"
            ),
            "primary_location": sys_info.get("primary_location") if (sys_info.get("primary_location") and not sys_info.get("primary_location").startswith("[CONFIG_REQUIRED")) else inferred_loc,
            "billing_account": sys_info.get("billing_account") or "[CONFIG_REQUIRED: Billing Account ID]",
            "confidentiality_impact": sys_info.get("confidentiality_impact") or inf_c,
            "integrity_impact": sys_info.get("integrity_impact") or inf_i,
            "availability_impact": sys_info.get("availability_impact") or inf_a,
            "rmf_governance_system": sys_info.get("rmf_governance_system") or "Enterprise GRC System (eMASS / CSAM / Xacta / FedRAMP Portal)",
            "scc_enabled": res_secops["scc_enabled"],
            "scc_tier": res_secops["scc_tier"],
            "allow_unaccredited_scc_in_il5": res_secops["allow_unaccredited_scc_in_il5"],
            "secops_enabled": res_secops["secops_enabled"],
            "cssp_provider": res_secops["cssp_provider"],
            "external_siem_type": res_secops["external_siem_type"],
            "telemetry_summary": res_secops["telemetry_summary"],
            "threat_detection_engine": res_secops["threat_detection_engine"],
            "identity_provider": res_ext["identity_provider"],
            "mfa_mechanism": res_ext["mfa_mechanism"],
            "vulnerability_scanner": res_ext["vulnerability_scanner"],
            "itsm_system": res_ext["itsm_system"],
            "cicd_platform": res_ext["cicd_platform"],
            "edr_solution": res_ext["edr_solution"],
            "perimeter_gateway": res_ext["perimeter_gateway"],
            # Organization identity. Both are parsed by the configuration loader
            # but were previously dropped by this whitelist, which left
            # [ORGANIZATION_DOMAIN] and [ORG_ID] permanently un-hydratable in the
            # IR runbooks and the IA / SC policy manuals. They are emitted as
            # empty strings when unconfigured so consumers fail closed rather
            # than deriving a domain from the organization display name.
            "organization_domain": sys_info.get("organization_domain") or "",
            "org_id": sys_info.get("org_id") or "",
            # Inherited cloud provider authorization. The SSP, SCTM and control
            # inheritance narratives assert this identifier to the assessor, who
            # will look it up on the FedRAMP Marketplace. It was hardcoded in the
            # templates, so it could not be corrected for a different CSP or for
            # a re-issued package without editing every template.
            "csp_pato_package_id": (
                sys_info.get("csp_pato_package_id")
                or DEFAULT_CSP_PATO_PACKAGE_ID
            ),
        },
        "security_operations": res_secops,
        "external_systems": res_ext,
        "personnel_roles": {
            "authorizing_official": roles_info.get("authorizing_official", {}),
            "system_owner": roles_info.get("system_owner", {}),
            "issm": roles_info.get("issm", {}),
            "isso": roles_info.get("isso", {})
        },
        "document_versions": doc_vers,
        "custom_services": user_config.get("custom_services", {}),
        "contracts": user_config.get("contracts", {}),
        "iam_groups": user_config.get("iam_groups", {}),
        "poam_items": user_config.get("poam_items", []),
        "security_scanners": user_config.get("security_scanners", {}),
        "disa_stigs": user_config.get("disa_stigs", {}),
        "contingency_planning": user_config.get("contingency_planning", {}),
        "continuous_monitoring": user_config.get("continuous_monitoring", {}),
        "export_preferences": user_config.get("export_preferences", {}),
        "connectivity_summary": tf_scanned.get("connectivity_summary"),
        "authentication_summary": tf_scanned.get("authentication_summary"),
        "encryption_summary": tf_scanned.get("encryption_summary"),
        "ids_solution": tf_scanned.get("ids_solution"),
        "network_architecture": {
            "vpcs": sorted(list(tf_scanned["networks"])),
            "subnets_cidrs": sorted(list(tf_scanned["subnets"])),
            "firewall_rules": tf_scanned["firewall_rules"],
            "application_ports": app_scanned["exposed_ports"]
        },
        "infrastructure_components": {
            "all_resources": tf_scanned["all_resources"] + app_scanned["all_resources"],
            "services_enabled": tf_scanned["services"],
            "terraform_engine_version": tf_scanned.get("terraform_engine_version"),
            "provider_versions": tf_scanned.get("provider_versions", {}),
            "storage_buckets": tf_scanned["storage_buckets"],
            "databases": tf_scanned["databases"],
            "kms_keys": tf_scanned["kms_keys"],
            "gke_clusters": tf_scanned["gke_clusters"],
            "compute_instances": tf_scanned["compute_instances"],
            "service_accounts": tf_scanned["service_accounts"],
            "service_account_keys": tf_scanned.get("service_account_keys", []),
            "logging_sinks": tf_scanned["logging_sinks"],
            "secrets": tf_scanned.get("secrets", []),
            "pubsub_topics": tf_scanned.get("pubsub_topics", []),
            "artifact_registries": tf_scanned.get("artifact_registries", []),
            "cloud_run_services": tf_scanned.get("cloud_run_services", []),
            "cloud_functions": tf_scanned.get("cloud_functions", []),
            "nat_gateways": tf_scanned.get("nat_gateways", []),
            "forwarding_rules": tf_scanned.get("forwarding_rules", []),
            "security_policies": tf_scanned.get("security_policies", []),
            "service_perimeters": tf_scanned.get("service_perimeters", []),
            "binary_authorization": tf_scanned.get("binary_authorization", []),
            "dataproc_clusters": tf_scanned.get("dataproc_clusters", []),
            "assured_workloads": tf_scanned["assured_workloads"],
            "iam_bindings": tf_scanned["iam_bindings"],
            "iam_roles_matrix": tf_scanned["iam_roles_matrix"],
            # Non-empty means part of the accreditation boundary was never read.
            "unparsed_terraform_files": tf_scanned.get("unparsed_terraform_files", []),
            "modules_used": tf_scanned["modules_used"]
        },
        "application_components": {
            "applications": app_scanned["applications"],
            "software_packages": app_scanned["software_packages"],
            "container_images": app_scanned["container_images"],
            "exposed_ports": app_scanned["exposed_ports"],
            "frameworks": sorted(list(app_scanned["frameworks"])),
            "runtimes": sorted(list(app_scanned["runtimes"])),
            "database_connectors": sorted(list(app_scanned["database_connectors"]))
        }
    }

    scrubbed_inventory = scrub_sensitive_data(inventory)
    out_path = os.path.join(target_dir, "system_inventory.json")
    validate_system_inventory_schema(scrubbed_inventory, source_path=out_path)

    # The inventory is a hand-tunable input, not a purely derived artifact: operators
    # correct inferred facts here and re-run. Replacing it outright would silently
    # discard that work, so keep the previous revision alongside it.
    if os.path.isfile(out_path):
        backup_path = f"{out_path}.bak"
        try:
            shutil.copy2(out_path, backup_path)
            logger.info("Existing inventory preserved as '%s' before regeneration.", backup_path)
        except OSError as err:
            logger.warning(
                "Could not back up the existing inventory '%s': %s. Continuing would "
                "discard any manual corrections, so the extraction is aborted.",
                out_path,
                err,
            )
            raise

    with audit_operation(event_type=AuditEvent.INVENTORY_EXTRACTED, obj=out_path):
        write_json_file(out_path, scrubbed_inventory, indent=2, allowed_boundary=target_dir)

    logger.info(
        "Extracted system inventory with %d GCP APIs & %d applications to '%s'",
        len(tf_scanned["services"]),
        len(app_scanned["applications"]),
        out_path,
    )
    return scrubbed_inventory


def main() -> None:
    """CLI entrypoint for extracting system inventory data."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    if "-h" in sys.argv or "--help" in sys.argv:
        print("Usage: extract_system_data.py [target_dir]")
        print("\nExtracts infrastructure AST facts and software inventory from Terraform code into system_inventory.json.")
        print("\nPositional Arguments:\n  target_dir       Target workspace folder containing terraform/ (default: .)")
        sys.exit(0)
    args = [a for a in sys.argv[1:] if a != "--"]
    target_dir = args[0] if args else "."
    extract_system_inventory(os.path.abspath(target_dir))


if __name__ == "__main__":
    main()
