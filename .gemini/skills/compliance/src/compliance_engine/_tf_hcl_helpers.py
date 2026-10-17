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

"""Terraform HCL2 helper primitives, variable resolution, and expression utilities."""

import ipaddress
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Dict, Final, List, Optional, Sequence, Tuple, Union

from . import hcl_parser as hcl2
from .audit_log import AuditEvent, audit_operation
from .file_helpers import (
    is_sensitive_key,
    run_bounded_command,
    scrub_sensitive_data,
)

LarkError = hcl2.LarkError

_PORTLESS_FIREWALL_PROTOCOLS: Final[frozenset] = frozenset(
    {"icmp", "icmpv6", "ipv6-icmp", "esp", "ah", "gre"}
)

logger = logging.getLogger("extract_system_data")

MAX_SUBPROCESS_OUTPUT_BYTES: int = 5 * 1024 * 1024
SUBPROCESS_RETRY_BASE_SECONDS: float = 1.0

GENERIC_VAR_NAMES = {
    "name", "id", "type", "description", "tags", "labels", "prefix", "suffix",
    "vpc_id", "subnet_id", "network_id",
}

_EXACT_VAR_REF = re.compile(r"^(?:\$\{\s*)?var\.([a-zA-Z0-9_-]+)(?:\s*\})?$")
_REF_TAIL = re.compile(r"[A-Za-z0-9_-]+(?=\s*[\}\)]|$)")
_BARE_REF_PREFIX = re.compile(r"^(?:var|local|each|count|self)\.")


def _sanitized_path_env(base_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Builds an environment whose PATH contains only trusted absolute directories."""
    safe_env = dict(os.environ if base_env is None else base_env)
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
        try:
            candidate = Path(entry).resolve()
        except OSError:
            continue
        if cwd is not None and (candidate == cwd or cwd in candidate.parents):
            continue
        trusted.append(entry)

    safe_env["PATH"] = os.pathsep.join(trusted)
    return safe_env


def _find_trusted_binary(name: str) -> Optional[str]:
    """Resolves an executable on the filtered PATH used by :func:`safe_run_command`."""
    return shutil.which(name, path=_sanitized_path_env().get("PATH", os.defpath))


def safe_run_command(
    cmd: Sequence[str],
    cwd: Optional[str] = None,
    timeout: int = 30,
    retries: int = 1,
    env: Optional[Dict[str, str]] = None,
) -> "subprocess.CompletedProcess[str]":
    """Runs an external command with a filtered PATH and rejects oversized output."""
    if not cmd or not cmd[0]:
        raise ValueError("Empty command")
    if retries < 0:
        raise ValueError(f"retries must be non-negative, got {retries}")

    safe_env = _sanitized_path_env(env)
    argv: List[str] = [str(arg) for arg in cmd]
    if not os.path.isabs(argv[0]):
        resolved = shutil.which(argv[0], path=safe_env.get("PATH", os.defpath))
        if not resolved:
            raise FileNotFoundError(f"Binary not found: {argv[0]}")
        argv[0] = resolved

    with audit_operation(event_type=AuditEvent.EXTERNAL_COMMAND, obj=argv[0]):
        return run_bounded_command(
            argv,
            timeout=timeout,
            env=safe_env,
            cwd=cwd,
            max_output_bytes=MAX_SUBPROCESS_OUTPUT_BYTES,
            attempts=retries + 1,
            retry_base_seconds=SUBPROCESS_RETRY_BASE_SECONDS,
        )


def is_valid_cidr(cidr: Any) -> bool:
    """Validates that a string is a legitimate IPv4 or IPv6 CIDR range."""
    if not isinstance(cidr, str):
        return False
    cidr = cidr.strip()
    if (
        not cidr
        or "/" not in cidr
        or any(
            tok in cidr
            for tok in ("${", "try(", "lookup(", "each.", "var.", "local.")
        )
        or "null" in cidr.lower()
    ):
        return False
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except (ValueError, AttributeError):
        return False


def _literal_cidrs(value: Any) -> List[str]:
    """Returns the literal IP ranges in a Terraform range-list attribute."""
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple)) else [value]
    ranges: List[str] = []
    for item in items:
        if not isinstance(item, str):
            continue
        candidate = item.strip()
        if not candidate or "${" in candidate or ("." not in candidate and ":" not in candidate):
            continue
        try:
            ipaddress.ip_network(candidate, strict=False)
        except ValueError:
            continue
        ranges.append(candidate)
    return ranges


def is_valid_resource_name(name: Any) -> bool:
    """Checks if a string is a valid human-readable resource name."""
    if not isinstance(name, str):
        return False
    name = name.strip()
    if (
        not name
        or len(name) < 2
        or any(
            tok in name
            for tok in ("${", "var.", "local.", "each.", "try(", "lookup(", ".")
        )
        or name.startswith(("-", "_"))
        or name.endswith(("-", "_"))
    ):
        return False
    return name.lower() not in {
        "vpc", "network", "firewall", "default", "main", "this",
        "subnets", "null", "none", "try", "lookup", "config", "unresolved",
    }


def _eval_coalesce_match(m: Any, merged_vars: Dict[str, Any]) -> str:
    """Evaluates a coalesce(a, b, ...) expression against merged_vars."""
    args = [arg.strip() for arg in m.group(1).split(",")]
    for arg in args:
        if (arg.startswith('"') and arg.endswith('"')) or (
            arg.startswith("'") and arg.endswith("'")
        ):
            lit = arg[1:-1].strip()
            if lit:
                return lit
        clean_arg = arg.replace("var.", "").replace("local.", "")
        val = (
            merged_vars.get(clean_arg)
            or merged_vars.get(f"var.{clean_arg}")
            or merged_vars.get(f"local.{clean_arg}")
        )
        if val and not str(val).startswith("${"):
            return str(val)
    for arg in args:
        parts = arg.split(".")
        if len(parts) >= 2:
            middle = [
                p for p in parts
                if p not in ("var", "local", "each", "value", "name", "id", "config")
            ]
            if middle:
                return middle[-1].replace("_", "-")
    return ""


def _eval_var_ref_match(m: Any, merged_vars: Dict[str, Any]) -> str:
    """Evaluates a ${var.xyz} reference against merged_vars."""
    raw = m.group(0)
    key = m.group(1)
    val = (
        merged_vars.get(key)
        or merged_vars.get(f"var.{key}")
        or merged_vars.get(f"local.{key}")
    )
    if val is not None and isinstance(val, (str, int, float, bool)):
        return str(val)
    parts = key.split(".")
    curr: Any = merged_vars
    for p in parts:
        curr = curr[p] if isinstance(curr, dict) and p in curr else None
        if curr is None:
            break
    if curr is not None and isinstance(curr, (str, int, float, bool)):
        return str(curr)
    if len(parts) >= 2:
        middle = [
            p for p in parts
            if p not in ("var", "local", "each", "value", "name", "id", "self_link", "config")
        ]
        if middle:
            return middle[-1].replace("_", "-")
    return raw


def clean_interpolated_string(
    s: Any, resolved_vars: Optional[Dict[str, Any]] = None, default_val: str = ""
) -> str:
    """Attempts to resolve or sanitize an HCL interpolated string like ${var.xyz}."""
    if not isinstance(s, str):
        return default_val if s is None else str(s)
    s = s.strip()
    if not s:
        return default_val
    if s.startswith("var.") or s.startswith("local."):
        s = "${" + s + "}"
    if not ("${" in s or "try(" in s or "lookup(" in s):
        return s

    merged_vars: Dict[str, Any] = {
        "var.resource_prefix": "gcp",
        "var.management_subnet": "management-subnet",
        "var.workstation_subnet": "workstation-subnet",
        "var.tenant_subnet": "tenant-subnet",
        "var.spoke_subnet": "spoke-subnet",
    }
    if resolved_vars:
        for k, v in resolved_vars.items():
            if isinstance(v, (str, int, float, bool)):
                merged_vars[k] = v
                merged_vars[f"var.{k}"] = v
                merged_vars[f"local.{k}"] = v

    def _repl_substr(m: Any) -> str:
        var_k = m.group(1)
        raw_val = merged_vars.get(var_k) or merged_vars.get(f"var.{var_k}")
        if raw_val is None:
            return m.group(0)
        start, length = int(m.group(2)), int(m.group(3))
        return str(raw_val)[start : start + length]

    s = re.sub(
        r"\$\{\s*substr\(\s*(?:var\.)?([a-zA-Z0-9_]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\s*\}",
        _repl_substr,
        s,
    )
    s = re.sub(
        r"\$\{\s*coalesce\(([^)]+)\)\s*\}",
        lambda m: _eval_coalesce_match(m, merged_vars),
        s,
    )
    resolved = re.sub(
        r"\$\{(?:var|local|each|count)?\.?([a-zA-Z0-9_.-]+)\}",
        lambda m: _eval_var_ref_match(m, merged_vars),
        s,
    )
    if "${" in resolved:
        resolved = re.sub(r"\$\{[^}]*?(?:var|local)\.([a-zA-Z0-9_.-]+)\}", r"\1", resolved)
        resolved = re.sub(r"\$\{.*?\}", "", resolved)
    resolved = re.sub(r"[-_]{2,}", "-", resolved).strip(" -_.,")
    if resolved in ("try", "lookup", "null", "None", ""):
        return default_val
    return scrub_sensitive_data(resolved) if resolved else default_val


def _resolve_local_sa_email_ref(
    rel_file: str,
    proj: Optional[str],
    sa_list: List[Dict[str, Any]],
) -> str:
    """Resolves a local.sa_email reference against discovered service accounts."""
    rel_parent = Path(rel_file).parent.name if rel_file else ""
    file_sas = [
        s for s in sa_list
        if s.get("file") == rel_file
        or (rel_file and s.get("file") and Path(str(s.get("file"))).parent == Path(str(rel_file)).parent)
        or (
            rel_parent
            and s.get("file")
            and (rel_parent in str(s.get("file")) or str(s.get("file")).split("/")[0] in rel_parent)
        )
    ]
    if file_sas and file_sas[0].get("email"):
        return f"serviceAccount:{file_sas[0]['email']}"
    sa_acc_id = file_sas[0].get("account_id") if file_sas else "workload-service-account"
    sa_proj = (file_sas[0].get("project") if file_sas else None) or proj
    if sa_proj:
        return f"serviceAccount:{sa_acc_id}@{sa_proj}.iam.gserviceaccount.com"
    return f"serviceAccount:{sa_acc_id} (project not declared)"


def _resolve_iam_sa_or_identity_ref(
    mem: str,
    rel_file: str,
    proj: Optional[str],
    sa_list: List[Dict[str, Any]],
) -> Optional[str]:
    """Resolves service account, service identity, or local.sa_email IAM references."""
    sa_res_match = re.search(r"google_service_account\.([a-zA-Z0-9_-]+)\.(?:email|member)", mem)
    if sa_res_match:
        sa_res_name = sa_res_match.group(1)
        matched_sa = next((s for s in sa_list if s.get("resource_name") == sa_res_name), None)
        if matched_sa and matched_sa.get("email") and "${" not in str(matched_sa["email"]):
            return f"serviceAccount:{matched_sa['email']}"
        sa_acc_id = matched_sa.get("account_id") if matched_sa else sa_res_name.replace("_", "-")
        sa_proj = (matched_sa.get("project") if matched_sa else None) or proj
        if sa_proj and "${" not in str(sa_proj) and "var." not in str(sa_proj):
            return f"serviceAccount:{sa_acc_id}@{sa_proj}.iam.gserviceaccount.com"
        return f"serviceAccount:{sa_acc_id} (project not declared)"

    psi_match = re.search(
        r"google_project_service_identity\.([a-zA-Z0-9_-]+)\.(?:member|email)", mem
    )
    if psi_match:
        psi_name = psi_match.group(1)
        matched_psi = next((s for s in sa_list if s.get("resource_name") == psi_name), None)
        svc = (matched_psi.get("service") if matched_psi else None) or psi_name
        return f"serviceAccount:google_project_service_identity.{psi_name} ({svc})"

    res_attr_match = re.search(
        r"((?:data\.)?google_[a-z0-9_]+\.[a-zA-Z0-9_-]+)\.(?:member|email)\b", mem
    )
    if res_attr_match:
        return f"serviceAccount:{res_attr_match.group(1)}"

    if "local.sa_email" in mem:
        return _resolve_local_sa_email_ref(rel_file, proj, sa_list)

    return None


def _resolve_each_value_iam_principal(
    res_name: str, body: str, role_val: str, rel_file: str
) -> Optional[str]:
    """Resolves for_each=${each.value} IAM principals based on role and resource context."""
    if "cryptoKeyEncrypterDecrypter" in role_val or "kms" in rel_file:
        return "CMEK Key Encrypter/Decrypter Service Agents (Storage, BigQuery, Pub/Sub, Cloud SQL)"
    if "impersonator" in res_name or "impersonators" in body or "serviceusage.serviceUsageConsumer" in role_val:
        return "Deployment & CI/CD Pipeline Impersonators"
    if "imageUser" in role_val:
        return "Compute Image User Service Accounts"
    return None


def _substitute_iam_project_tokens(
    mem: str, vars_dict: Dict[str, Any]
) -> Tuple[str, Optional[str]]:
    """Substitutes project_number / data.google_project.*.number tokens and extracts project_id."""
    pnum = str(vars_dict.get("project_number") or "<PROJECT_NUMBER>")
    if "var.project_number" in mem or "${project_number}" in mem:
        mem = re.sub(r"\$\{(?:var\.)?project_number\}", pnum, mem)
    if "data.google_project." in mem and ".number" in mem:
        mem = re.sub(r"\$\{\s*data\.google_project\.[a-zA-Z0-9_-]+\.number\s*\}", pnum, mem)
        mem = re.sub(r"\bdata\.google_project\.[a-zA-Z0-9_-]+\.number\b", pnum, mem)

    proj = (
        vars_dict.get("project_id")
        or vars_dict.get("main_project_id")
        or vars_dict.get("prod_project_id")
        or vars_dict.get("service_project_id")
    )
    if proj and ("${" in str(proj) or "var." in str(proj) or "local." in str(proj)):
        proj = None
    return mem, str(proj) if proj else None


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
    """Resolves raw or interpolated IAM principal expressions to clean identifiers."""
    del res_type
    if not mem or not isinstance(mem, str):
        return None
    mem = mem.strip(' "\'\t\r\n')
    if not mem:
        return None

    vars_dict = resolved_vars or {}
    sa_list = service_accounts or []

    if "${each.value.member}" in mem or mem == "${each.value}":
        return _resolve_each_value_iam_principal(res_name, body, role_val, rel_file)

    pnum = str(vars_dict.get("project_number") or "<PROJECT_NUMBER>")
    if "secretmanager_sa" in mem:
        return f"serviceAccount:service-{pnum}@gcp-sa-secretmanager.iam.gserviceaccount.com"

    mem, proj = _substitute_iam_project_tokens(mem, vars_dict)

    sa_resolved = _resolve_iam_sa_or_identity_ref(mem, rel_file, proj, sa_list)
    if sa_resolved is not None:
        return sa_resolved

    if ".svc.id.goog[" in mem and "${" in mem:
        proj_label = str(proj) if proj else "<PROJECT_ID>"
        mem = re.sub(r"\$\{[^}]+\}(?=\.svc\.id\.goog\[)", proj_label, mem)

    if "${" in mem:
        mem = clean_interpolated_string(mem, vars_dict, default_val=mem)
    if "${" in mem:
        mem = re.sub(r"\$\{([^}]+)\}", r"\1", mem).replace("var.", "").replace("local.", "")
    if "${" in mem or "each.value" in mem:
        return None
    if mem.strip().lower() in ("member", "email", "terraform.tfplan"):
        return None
    return mem


def classify_resource_category(resource_type: str) -> str:
    """Classifies a Terraform resource type into a GCP infrastructure category string."""
    rt = resource_type.lower()
    if rt.startswith("kubernetes_"):
        clean_name = rt.replace("kubernetes_", "").replace("_", " ").title()
        return f"Kubernetes {clean_name} Resource"
    clean_name = (
        resource_type.replace("google-beta_", "").replace("google_", "").replace("_", " ").title()
    )
    return f"Google Cloud {clean_name}"


class HclBlock(str):
    """String wrapper for HCL block content with attached AST dictionary."""

    parsed: Dict[str, Any]

    def __new__(
        cls,
        content: str,
        parsed: Optional[Dict[str, Any]] = None,
    ) -> "HclBlock":
        obj = super().__new__(cls, content)
        obj.parsed = parsed or {}
        return obj


def _hcl_val_to_str(val: Any, indent: int = 0) -> str:
    """Converts a parsed python-hcl2 dictionary structure back to a formatted HCL string."""
    if isinstance(val, str):
        return f'"{val}"'
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, list):
        if not val:
            return "[]"
        if isinstance(val[0], dict):
            return "\n".join(_hcl_val_to_str(v, indent) for v in val)
        return "[" + ", ".join(_hcl_val_to_str(v, indent) for v in val) + "]"
    if isinstance(val, dict):
        pad = "  " * indent
        inner = "\n".join(f"{pad}{k} = {_hcl_val_to_str(v, indent + 1)}" for k, v in val.items())
        return f"{{\n{inner}\n{pad}}}"
    return str(val)


def _dict_to_hcl_body_str(d: Dict[str, Any]) -> str:
    """Recursively serializes a python-hcl2 AST resource/module dictionary to string format."""
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
    """Extracts scalar items from a bracketed HCL list string, preserving quoted strings."""
    items: List[str] = []
    for item_match in re.finditer(
        r'"((?:[^"\\]|\\.)*)"|\'([^\']*)\'|([a-zA-Z0-9_.-]+)', list_str
    ):
        if item_match.group(1) is not None:
            items.append(item_match.group(1).replace(r'\"', '"').replace(r"\\", "\\"))
        elif item_match.group(2) is not None:
            items.append(item_match.group(2))
        elif item_match.group(3) is not None:
            items.append(item_match.group(3))
    return items


def _coerce_hcl_ast_scalar(val: Any) -> Any:
    """Coerces string-wrapped numeric and boolean interpolations emitted by python-hcl2."""
    if not isinstance(val, str):
        return val
    m_num = re.match(r"^\$\{\s*(-?[0-9]+(?:\.[0-9]+)?)\s*\}$", val)
    if m_num:
        num_str = m_num.group(1)
        return float(num_str) if "." in num_str else int(num_str)
    if val.strip() in ("${true}", "${ true }"):
        return True
    if val.strip() in ("${false}", "${ false }"):
        return False
    return val.replace(r'\"', '"').replace(r"\\", "\\")


def _parse_tfvars_via_hcl_ast(content: str, parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts variables and locals from an AST-parsed HCL dictionary."""
    vars_dict: Dict[str, Any] = {}
    for k, val in parsed.items():
        is_explicit_list = bool(
            isinstance(val, list)
            and re.search(rf"^\s*{re.escape(str(k))}\s*=\s*\[", content, re.MULTILINE)
        )
        extracted_val = (
            val[0] if isinstance(val, list) and len(val) == 1 and not is_explicit_list else val
        )
        extracted_val = _coerce_hcl_ast_scalar(extracted_val)
        if k == "variable" and isinstance(val, list):
            for var_item in val:
                if not isinstance(var_item, dict):
                    continue
                for var_name, var_attrs in var_item.items():
                    if not (isinstance(var_attrs, dict) and "default" in var_attrs):
                        continue
                    def_val = var_attrs["default"]
                    if isinstance(def_val, list) and len(def_val) == 1:
                        var_block_m = re.search(
                            rf'variable\s+"{re.escape(str(var_name))}"\s*\{{([^}}]*)\}}',
                            content,
                        )
                        is_def_list = bool(
                            var_block_m and re.search(r"default\s*=\s*\[", var_block_m.group(1))
                        )
                        if not is_def_list:
                            def_val = def_val[0]
                    def_val = _coerce_hcl_ast_scalar(def_val)
                    vars_dict[var_name] = (
                        "[REDACTED_SENSITIVE]"
                        if is_sensitive_key(var_name)
                        else scrub_sensitive_data(def_val)
                    )
        elif k == "locals" and isinstance(val, list):
            for loc_item in val:
                if isinstance(loc_item, dict):
                    for lk, lv in loc_item.items():
                        l_val = lv[0] if isinstance(lv, list) and len(lv) == 1 else lv
                        vars_dict[lk] = (
                            "[REDACTED_SENSITIVE]"
                            if is_sensitive_key(lk)
                            else scrub_sensitive_data(l_val)
                        )
                        vars_dict[f"local.{lk}"] = vars_dict[lk]
        else:
            vars_dict[k] = (
                "[REDACTED_SENSITIVE]"
                if is_sensitive_key(k)
                else scrub_sensitive_data(extracted_val)
            )
    return scrub_sensitive_data(vars_dict)


def _parse_tfvars_regex_fallback(content: str) -> Dict[str, Any]:
    """Line-oriented scalar/list/heredoc/variable fallback parser for tfvars."""
    vars_dict: Dict[str, Any] = {}
    for m in re.finditer(
        r'^[ \t]*([a-zA-Z0-9_-]+)[ \t]*=[ \t]*"((?:[^"\\\n]|\\.)*)"', content, re.MULTILINE
    ):
        k = m.group(1)
        raw_val = m.group(2).replace(r'\"', '"').replace(r"\\", "\\")
        vars_dict[k] = "[REDACTED_SENSITIVE]" if is_sensitive_key(k) else scrub_sensitive_data(raw_val)
    for m in re.finditer(
        r'^[ \t]*([a-zA-Z0-9_-]+)[ \t]*=[ \t]*<<-?([A-Za-z0-9_]+)[ \t]*\n([\s\S]{0,65536}?)\n[ \t]*\2[ \t]*$',
        content,
        re.MULTILINE,
    ):
        k = m.group(1)
        vars_dict[k] = "[REDACTED_SENSITIVE]" if is_sensitive_key(k) else scrub_sensitive_data(m.group(3))
    for m in re.finditer(
        r'^[ \t]*([a-zA-Z0-9_-]+)[ \t]*=[ \t]*(true|false)\b',
        content,
        re.MULTILINE | re.IGNORECASE,
    ):
        vars_dict[m.group(1)] = m.group(2).lower() == "true"
    for m in re.finditer(
        r'^[ \t]*([a-zA-Z0-9_-]+)[ \t]*=[ \t]*(-?[0-9]+(?:\.[0-9]+)?)\b', content, re.MULTILINE
    ):
        num_str = m.group(2)
        vars_dict[m.group(1)] = float(num_str) if "." in num_str else int(num_str)
    for m in re.finditer(
        r'^[ \t]*([a-zA-Z0-9_-]+)[ \t]*=[ \t]*\[([^\]]*)\]', content, re.MULTILINE
    ):
        k = m.group(1)
        items = _parse_hcl_list_items(m.group(2))
        vars_dict[k] = (
            ["[REDACTED_SENSITIVE]" for _ in items]
            if is_sensitive_key(k)
            else [scrub_sensitive_data(item) for item in items]
        )
    for m in re.finditer(r'variable\s+"([a-zA-Z0-9_-]+)"\s*\{([^}]*)\}', content):
        v_name, block = m.group(1), m.group(2)
        if "sensitive = true" in block.lower() or "sensitive=true" in block.lower() or is_sensitive_key(v_name):
            vars_dict[v_name] = "[REDACTED_SENSITIVE]"
            continue
        default_match = re.search(
            r'default\s*=\s*("((?:[^"\\]|\\.)*)"|([a-zA-Z0-9_\-\.]+))', block
        )
        if default_match and v_name not in vars_dict:
            v_val = (
                default_match.group(2).replace(r'\"', '"').replace(r"\\", "\\")
                if default_match.group(2) is not None
                else default_match.group(3)
            )
            if v_val is not None:
                if str(v_val).lower() == "true":
                    vars_dict[v_name] = True
                elif str(v_val).lower() == "false":
                    vars_dict[v_name] = False
                else:
                    vars_dict[v_name] = scrub_sensitive_data(v_val)
    return scrub_sensitive_data(vars_dict)


def parse_tfvars_content(content: str, strict: bool = False) -> Dict[str, Any]:
    """Parses HCL / Terraform variable assignments from .tfvars or variables.tf."""
    if not content or not content.strip():
        return {}
    try:
        parsed = hcl2.loads(content)
        if isinstance(parsed, dict):
            return _parse_tfvars_via_hcl_ast(content, parsed)
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
    return _parse_tfvars_regex_fallback(content)


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
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return body[start + 1 : i]
    return None


def _lookup_attr_in_dict(target_dict: Dict[str, Any], attr_name: str) -> Any:
    """Looks up an attribute (with optional dot notation) inside an HCL AST dictionary."""
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
                return None
        return curr

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
                return blk_val[attr_name]
            if isinstance(blk_val, list) and blk_val and isinstance(blk_val[0], dict) and attr_name in blk_val[0]:
                return blk_val[0][attr_name]
    return val


def extract_hcl_attr(
    body: Union[str, Dict[str, Any]],
    attr_name: str,
    default: Any = None,
    vars_dict: Optional[Dict[str, Any]] = None,
) -> Any:
    """Extracts a scalar or structured attribute value from an HCL body (dict or str)."""
    target_dict: Optional[Dict[str, Any]] = None
    if isinstance(body, dict):
        target_dict = body
    elif hasattr(body, "parsed") and isinstance(getattr(body, "parsed", None), dict):
        target_dict = getattr(body, "parsed")

    if target_dict is not None:
        val = _lookup_attr_in_dict(target_dict, attr_name)
        if val is not None:
            if isinstance(val, list) and len(val) == 1:
                val = val[0]
            if isinstance(val, str):
                m_var = _EXACT_VAR_REF.match(val)
                if m_var and vars_dict and m_var.group(1) in vars_dict:
                    return scrub_sensitive_data(vars_dict[m_var.group(1)])
            return scrub_sensitive_data(val)
        if isinstance(body, dict):
            return default

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
    if not m:
        return default
    if m.group(2) is not None:
        val = m.group(2).replace(r'\"', '"').replace(r"\\", "\\")
    else:
        raw_val = m.group(3)
        if raw_val.lower() in ("true", "yes"):
            return True
        if raw_val.lower() in ("false", "no"):
            return False
        if raw_val.isdigit():
            return int(raw_val)
        val = raw_val

    if isinstance(val, str):
        m_var = _EXACT_VAR_REF.match(val)
        if m_var and vars_dict and m_var.group(1) in vars_dict:
            return scrub_sensitive_data(vars_dict[m_var.group(1)])
    return scrub_sensitive_data(val)


def _resolve_ast_variables(
    node: Any, vars_dict: Optional[Dict[str, Any]], _depth: int = 0
) -> Any:
    """Substitutes known ``var.*`` references throughout a parsed HCL AST."""
    if not vars_dict or _depth > 24:
        return node
    if isinstance(node, str):
        m = _EXACT_VAR_REF.match(node.strip())
        if m and m.group(1) in vars_dict:
            return vars_dict[m.group(1)]
        return node
    if isinstance(node, dict):
        return {k: _resolve_ast_variables(v, vars_dict, _depth + 1) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_ast_variables(v, vars_dict, _depth + 1) for v in node]
    return node


def _resolved_asset_name(
    raw: Any,
    res_name: str,
    vars_dict: Optional[Dict[str, Any]],
    fallback: str,
) -> str:
    """Resolves a raw asset identifier into a human-readable name."""
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


def _asset_identifier(
    body: Union[Dict[str, Any], str],
    keys: Sequence[str],
    res_name: str,
    vars_dict: Optional[Dict[str, Any]],
    fallback: str,
) -> str:
    """Reads a resource identifier from either body shape and resolves it."""
    raw: Any = None
    for key in keys:
        raw = body.get(key) if isinstance(body, dict) else extract_hcl_attr(body, key, vars_dict=vars_dict)
        if raw:
            break
    return _resolved_asset_name(raw, res_name, vars_dict, fallback)


def _resolve_optional_attr(
    raw_val: Any,
    vars_dict: Optional[Dict[str, Any]],
    default_val: Optional[str] = None,
) -> Optional[str]:
    """Resolves a string attribute against vars_dict without fabricating defaults."""
    if raw_val is None:
        return default_val
    raw_str = str(raw_val).strip()
    if not raw_str or raw_str.lower() in ("null", "none"):
        return default_val
    v_dict = vars_dict or {}
    m_exact = _EXACT_VAR_REF.match(raw_str)
    if m_exact:
        var_name = m_exact.group(1)
        if var_name not in v_dict or v_dict[var_name] in (None, "", "null", "none"):
            return default_val
        return str(v_dict[var_name]).strip()
    var_refs = re.findall(r"\bvar\.([a-zA-Z0-9_-]+)\b", raw_str)
    if var_refs and any(v not in v_dict or v_dict[v] in (None, "", "null", "none") for v in var_refs):
        return default_val
    if any(tok in raw_str for tok in ("${", "var.", "local.", "each.", "try(", "lookup(")):
        cleaned = clean_interpolated_string(raw_str, v_dict, default_val="")
        if not cleaned or any(tok in cleaned for tok in ("${", "var.", "local.", "each.", "try(", "lookup(")):
            return default_val
        tails = {t.lower() for t in _REF_TAIL.findall(raw_str)}
        if cleaned.strip().lower() in tails and cleaned.strip() not in {str(v) for v in v_dict.values()}:
            return default_val
        return cleaned
    return raw_str


def _resolved_cmek_name(raw_cmek: Any, resolved_vars: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Resolves a CMEK key attribute only when it references a KMS key or a non-null literal/default."""
    if not raw_cmek:
        return None
    raw_str = str(raw_cmek).strip()
    if not raw_str or raw_str.lower() in ("null", "none", "false", "${null}"):
        return None
    v_dict = resolved_vars or {}
    m_kms = re.search(r"(?:data\.)?google_kms_crypto_key\.([a-zA-Z0-9_-]+)", raw_str)
    if m_kms:
        return m_kms.group(1)
    m_mod = re.search(
        r"module\.([a-zA-Z0-9_-]+)\.keys(?:\.([a-zA-Z0-9_-]+)|\[\"([^\"]+)\"\])",
        raw_str,
    )
    if m_mod:
        return m_mod.group(2) or m_mod.group(3) or m_mod.group(1)
    m_mod_generic = re.search(r"module\.([a-zA-Z0-9_-]+)\.(?:key_ids|keys)\b", raw_str)
    if m_mod_generic:
        return m_mod_generic.group(1)
    return _resolve_optional_attr(raw_str, v_dict, default_val=None)


def _text_attr_tristate(body: Any, attr: str) -> Optional[bool]:
    """Reads a boolean Terraform attribute from raw text without guessing."""
    match = re.search(
        r"\b" + re.escape(attr) + r"\s*=\s*(true|false)\b",
        str(body),
        re.IGNORECASE,
    )
    if match:
        return match.group(1).lower() == "true"
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


def _extract_balanced_hcl_blocks(
    content: str, keyword: str, labels_count: int
) -> List[Any]:
    """Extracts top-level balanced-brace HCL blocks when AST parsing is unavailable."""
    clean = re.sub(r"/\*[\s\S]*?\*/", "", content)
    clean = re.sub(r"(?m)^[ \t]*(?:#|//)[^\n]*$", "", clean)
    if labels_count == 2:
        pat = rf'(?m)^[ \t]*{re.escape(keyword)}[ \t]+"([^"\n]+)"[ \t]+"([^"\n]+)"[ \t]*\{{'
    elif labels_count == 1:
        pat = rf'(?m)^[ \t]*{re.escape(keyword)}[ \t]+"([^"\n]+)"[ \t]*\{{'
    else:
        pat = rf"(?m)^[ \t]*{re.escape(keyword)}[ \t]*\{{"
    results: List[Any] = []
    for m in re.finditer(pat, clean):
        start = m.end()
        depth, pos, in_str, esc = 1, start, False, False
        while pos < len(clean) and depth > 0:
            ch = clean[pos]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            pos += 1
        if depth == 0:
            body_str = clean[start : pos - 1]
            if labels_count == 2:
                results.append((m.group(1), m.group(2), body_str))
            elif labels_count == 1:
                results.append((m.group(1), body_str))
            else:
                results.append(body_str)
    return results


def _scan_hcl_rhs_expression(clean: str, start_idx: int) -> Tuple[str, int]:
    """Scans a balanced RHS HCL expression starting at start_idx."""
    n = len(clean)
    j = start_idx
    edepth = 0
    ein_str = False
    eesc = False
    while j < n:
        ech = clean[j]
        if ein_str:
            if eesc:
                eesc = False
            elif ech == "\\":
                eesc = True
            elif ech == '"':
                ein_str = False
        elif ech == '"':
            ein_str = True
        elif ech in "{([":
            edepth += 1
        elif ech in "})]":
            if edepth == 0:
                break
            edepth -= 1
        elif ech == "\n" and edepth == 0:
            if not clean[j + 1 :].lstrip(" \t").startswith(("?", ":")):
                break
        j += 1
    return " ".join(clean[start_idx:j].split()), j


def _extract_hcl_local_assignments(lbody: str) -> Dict[str, str]:
    """Extracts top-level local variable assignments (including multiline expressions) from a locals block."""
    clean = re.sub(r"/\*[\s\S]*?\*/", "", lbody)
    clean = re.sub(r"(?m)^[ \t]*(?:#|//)[^\n]*$", "", clean)
    result: Dict[str, str] = {}
    depth, in_str, esc, n, i, line_start = 0, False, False, len(clean), 0, True
    while i < n:
        ch = clean[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str, line_start = True, False
        elif ch in "{([":
            depth, line_start = depth + 1, False
        elif ch in "})]":
            depth, line_start = max(0, depth - 1), False
        elif ch == "\n":
            line_start = True
        elif line_start and depth == 0 and not ch.isspace():
            m = re.match(r"^([a-zA-Z0-9_]+)[ \t]*=[ \t]*", clean[i:])
            if m:
                expr_val, next_i = _scan_hcl_rhs_expression(clean, i + m.end())
                result[m.group(1)] = expr_val
                i = next_i
                continue
            line_start = False
        elif not ch.isspace():
            line_start = False
        i += 1
    return result


def _extract_top_level_meta_arg(body: str, attr_name: str) -> Optional[str]:
    """Extracts a top-level count or for_each expression from a raw resource body."""
    return _extract_hcl_local_assignments(body).get(attr_name)


def _is_falsy_hcl_val(val: Any) -> bool:
    """Returns True if an evaluated HCL default or argument is empty/null/false/zero."""
    if val in (None, False, 0, "0", "false", "null", "none", "", {}, [], (), "{}", "[]", "toset([])", "tomap({})"):
        return True
    if isinstance(val, str):
        return val.strip() in ("{}", "[]", "toset([])", "tomap({})", "${{}}", "${[]}", "${false}", "${null}", "${0}")
    return False
