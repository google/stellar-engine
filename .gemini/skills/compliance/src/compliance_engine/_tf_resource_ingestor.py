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

"""Terraform HCL2 and plan/state JSON resource classification and ingestion."""

import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Callable, Dict, Final, List, Optional, Sequence, Set, Tuple, Type, Union

from . import hcl_parser as hcl2
from ._tf_hcl_helpers import (
    GENERIC_VAR_NAMES,
    HclBlock,
    LarkError,
    _BARE_REF_PREFIX,
    _EXACT_VAR_REF,
    _PORTLESS_FIREWALL_PROTOCOLS,
    _asset_identifier,
    _dict_to_hcl_body_str,
    _extract_balanced_hcl_blocks,
    _extract_hcl_local_assignments,
    _extract_top_level_meta_arg,
    _find_trusted_binary,
    _is_falsy_hcl_val,
    _literal_cidrs,
    _parse_hcl_list_items,
    _resolve_ast_variables,
    _resolve_optional_attr,
    _resolved_asset_name,
    _resolved_cmek_name,
    _text_attr_tristate,
    classify_resource_category,
    clean_interpolated_string,
    extract_hcl_attr,
    is_valid_cidr,
    is_valid_resource_name,
    parse_tfvars_content,
    resolve_iam_principal,
    safe_run_command,
)
from .file_helpers import (
    NOT_DETERMINED,
    ensure_path_within_boundary,
    is_ignored_traversal_dir,
    is_sensitive_key,
    read_json_file,
    read_text_file,
    resolve_local_child_module_dir,
    resolve_module_root,
    scrub_sensitive_data,
    summarize_kms_protection,
)

logger = logging.getLogger("extract_system_data")

TERRAFORM_PLAN_FLAGS: Final[Tuple[str, ...]] = ("-input=false", "-lock=false", "-refresh=false", "-no-color")

_TERRAFORM_CREDENTIAL_ENV_VARS: Final[frozenset] = frozenset({
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_CREDENTIALS",
    "GOOGLE_CLOUD_KEYFILE_JSON",
    "GCLOUD_KEYFILE_JSON",
    "GOOGLE_OAUTH_ACCESS_TOKEN",
    "GOOGLE_IMPERSONATE_SERVICE_ACCOUNT",
    "GOOGLE_BACKEND_CREDENTIALS",
    "GOOGLE_BACKEND_IMPERSONATE_SERVICE_ACCOUNT",
    "CLOUDSDK_AUTH_ACCESS_TOKEN",
    "CLOUDSDK_AUTH_ACCESS_TOKEN_FILE",
    "CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE",
    "CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_PROFILE",
    "ARM_CLIENT_ID",
    "ARM_CLIENT_SECRET",
    "ARM_CLIENT_CERTIFICATE_PATH",
    "ARM_CLIENT_CERTIFICATE_PASSWORD",
    "ARM_ACCESS_KEY",
    "ARM_SAS_TOKEN",
    "ARM_OIDC_TOKEN",
    "TFE_TOKEN",
    "ATLAS_TOKEN",
    "VAULT_TOKEN",
})
_TERRAFORM_CREDENTIAL_ENV_PREFIXES: Final[Tuple[str, ...]] = ("TF_TOKEN_",)
_EXTERNAL_TOOL_ERRORS: Final[Tuple[Type[BaseException], ...]] = (OSError, ValueError, MemoryError, subprocess.SubprocessError)


def _esd_attr(name: str, default: Any) -> Any:
    """Resolves a symbol via extract_system_data if loaded so monkeypatches work."""
    mod = sys.modules.get("compliance_engine.extract_system_data") or sys.modules.get("extract_system_data")
    return getattr(mod, name, default) if mod is not None else default


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
    if networks:
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
    return " / ".join(auth_items) if auth_items else "Not determined from IaC"


def derive_encryption_summary(
    kms_keys: List[Dict[str, Any]],
    storage_buckets: List[Dict[str, Any]],
    databases: Optional[List[Dict[str, Any]]] = None,
    compute_instances: Optional[List[Dict[str, Any]]] = None,
    gke_clusters: Optional[List[Dict[str, Any]]] = None,
    cloud_run_services: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Dynamically derives cryptographic protection architecture description."""
    has_hsm = any(k.get("protection_level") == "HSM" for k in kms_keys)
    has_external = any(
        str(k.get("protection_level") or "").upper() in ("EXTERNAL", "EXTERNAL_VPC")
        for k in kms_keys
    )
    has_software = any(k.get("protection_level") == "SOFTWARE" for k in kms_keys)
    has_cmek = (
        len(kms_keys) > 0
        or any(b.get("cmek_encrypted") or b.get("kms_key") for b in (storage_buckets or []))
        or any(d.get("cmek_key") or d.get("kms_key") for d in (databases or []))
        or any(vm.get("kms_key") for vm in (compute_instances or []))
        or any(c.get("kms_key") for c in (gke_clusters or []))
        or any(cr.get("cmek_key") or cr.get("kms_key") for cr in (cloud_run_services or []))
    )
    if has_hsm or has_external or has_software:
        return summarize_kms_protection(kms_keys)
    if has_cmek:
        return f"Customer-managed encryption keys referenced (protection level {NOT_DETERMINED})"
    return "Google default encryption at rest (no customer-managed keys discovered)"


def _scan_yaml_iam_personas_and_groups(target_dir_str: str) -> List[Dict[str, Any]]:
    """Extracts IAM persona and group role entries from YAML configurations in target_dir."""
    matrix: List[Dict[str, Any]] = []
    yaml_config_paths: List[str] = []
    for root, dirs, files in os.walk(target_dir_str, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not is_ignored_traversal_dir(d))
        for filename in sorted(files):
            if filename.endswith((".yaml", ".yml")) and any(
                k in filename.lower() for k in ("iam", "group", "permission", "persona", "service_account")
            ):
                ypath = os.path.join(root, filename)
                if not os.path.islink(ypath):
                    yaml_config_paths.append(ypath)

    for ypath in yaml_config_paths:
        try:
            ytext = read_text_file(ypath, allowed_boundary=target_dir_str)
            rel_p = os.path.relpath(ypath, target_dir_str)
            persona_blocks = re.findall(
                r"(?<![a-zA-Z0-9_])([a-zA-Z0-9_]{0,128}_roles):[ \t]*\n((?:[ \t]*-[ \t]*[^\n]+(?:\n|$))+)",
                ytext,
            )
            for persona_key, roles_block in persona_blocks:
                persona_name = persona_key.replace("_roles", "").replace("_", " ").title()
                group_key = f"gcp-{persona_key.replace('_roles', '').replace('_', '-')}"
                roles = [r.strip(' -"\'\t\r\n:') for r in roles_block.splitlines() if r.strip(' -"\'\t\r\n:')]
                if roles:
                    matrix.append({
                        "principal": f"`{group_key}` ({persona_name})",
                        "roles": [r.replace("roles/", "") for r in roles],
                        "file": rel_p,
                    })

            groups_match = re.search(r"groups:\s*\n((?:\s*[a-zA-Z0-9_]+:\s*[^\n]+\n)+)", ytext)
            if groups_match:
                for g_line in groups_match.group(1).splitlines():
                    if ":" in g_line:
                        g_name = g_line.split(":")[1].strip(' "\'')
                        matrix.append({
                            "principal": f"`{g_name}`",
                            "roles": [f"Configured in {rel_p}"],
                            "file": rel_p,
                        })
        except (OSError, UnicodeDecodeError, ValueError) as err:
            logger.debug("Failed to parse IAM config %s: %s", ypath, err)
    return matrix


def derive_iam_roles_matrix(
    target_dir: Optional[Union[str, Path]],
    iam_bindings: Optional[List[Dict[str, Any]]] = None,
    existing_matrix: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Derives structured IAM persona roles matrix across YAMLs and bindings."""
    matrix: List[Dict[str, Any]] = list(existing_matrix) if existing_matrix else []
    if not matrix and target_dir and os.path.isdir(str(target_dir)):
        matrix.extend(_scan_yaml_iam_personas_and_groups(str(target_dir)))

    if iam_bindings:
        by_principal: Dict[str, List[str]] = {}
        by_principal_files: Dict[str, List[str]] = {}
        for b in iam_bindings:
            p = b.get("principal")
            r = b.get("role")
            f = str(b.get("file") or "").strip()
            if p and r and str(p).lower() not in ("member", "email", "terraform.tfplan"):
                by_principal.setdefault(p, []).append(r.replace("roles/", ""))
                if f and f != "terraform.tfplan":
                    files_for_p = by_principal_files.setdefault(p, [])
                    if f not in files_for_p:
                        files_for_p.append(f)
        for p, r_list in by_principal.items():
            if not any(entry.get("principal") == p for entry in matrix):
                src_files = by_principal_files.get(p) or ["main.tf"]
                matrix.append({
                    "principal": p,
                    "roles": sorted(list(set(r_list))),
                    "file": ", ".join(src_files),
                })
    return matrix


def infer_enabled_services_from_components(tf_data: Dict[str, Any]) -> None:
    """Ensures baseline GCP service APIs are recorded based on component inventory."""
    key_to_service = (
        ("storage_buckets", "storage.googleapis.com"),
        ("kms_keys", "cloudkms.googleapis.com"),
        ("gke_clusters", "container.googleapis.com"),
        ("logging_sinks", "logging.googleapis.com"),
        ("secrets", "secretmanager.googleapis.com"),
        ("pubsub_topics", "pubsub.googleapis.com"),
        ("artifact_registries", "artifactregistry.googleapis.com"),
        ("cloud_run_services", "run.googleapis.com"),
        ("cloud_functions", "cloudfunctions.googleapis.com"),
        ("assured_workloads", "assuredworkloads.googleapis.com"),
        ("dataproc_clusters", "dataproc.googleapis.com"),
        ("service_perimeters", "accesscontextmanager.googleapis.com"),
        ("binary_authorization", "binaryauthorization.googleapis.com"),
    )
    if tf_data["compute_instances"] or tf_data["networks"]:
        tf_data["services"].add("compute.googleapis.com")
    for comp_key, svc_api in key_to_service:
        if tf_data.get(comp_key):
            tf_data["services"].add(svc_api)
    if tf_data["databases"]:
        if any("bigquery" in d.get("type", "") for d in tf_data["databases"]):
            tf_data["services"].add("bigquery.googleapis.com")
        if any("sql" in d.get("type", "") for d in tf_data["databases"]):
            tf_data["services"].add("sqladmin.googleapis.com")
    if tf_data["iam_bindings"] or tf_data["service_accounts"]:
        tf_data["services"].add("iam.googleapis.com")


def _redact_tf_sensitive_values(values: Any, sensitive_mask: Any) -> Any:
    """Recursively redacts values marked sensitive by Terraform JSON plan/state masks."""
    if sensitive_mask is True:
        return "[REDACTED_SENSITIVE]"
    if isinstance(values, dict) and isinstance(sensitive_mask, dict):
        return {k: _redact_tf_sensitive_values(v, sensitive_mask.get(k)) for k, v in values.items()}
    if isinstance(values, list) and isinstance(sensitive_mask, list):
        return [
            _redact_tf_sensitive_values(v, sensitive_mask[idx] if idx < len(sensitive_mask) else False)
            for idx, v in enumerate(values)
        ]
    return values


def _extract_state_direct_resources(
    resources_list: List[Any], modules_used: Set[str]
) -> List[Dict[str, Any]]:
    """Extracts managed resources from a raw terraform.tfstate resources array."""
    collected: List[Dict[str, Any]] = []
    for r in resources_list:
        res_mode = r.get("mode", "managed")
        if res_mode != "managed":
            continue
        res_type = r.get("type", "")
        res_name = r.get("name", "")
        res_mod = r.get("module", "")
        if res_mod:
            modules_used.add(res_mod)
        for inst in r.get("instances", []):
            attrs = dict(inst.get("attributes") or {})
            for sens_path in inst.get("sensitive_attributes") or []:
                if isinstance(sens_path, list) and sens_path and isinstance(sens_path[0], dict):
                    if sens_path[0].get("type") == "get_attr" and sens_path[0].get("value") in attrs:
                        attrs[sens_path[0]["value"]] = "[REDACTED_SENSITIVE]"
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
                "values": scrub_sensitive_data(attrs),
            })
    return collected


def _extract_resource_change_entries(rc_list: List[Any]) -> List[Dict[str, Any]]:
    """Extracts managed non-delete resource_changes entries from Terraform plan JSON."""
    collected: List[Dict[str, Any]] = []
    for rc in rc_list:
        res_mode = rc.get("mode", "managed")
        if res_mode != "managed":
            continue
        change = rc.get("change", {})
        if (change.get("actions") or []) == ["delete"]:
            continue
        res_type, res_name = rc.get("type", ""), rc.get("name", "")
        after = change.get("after")
        if after is None:
            after = change.get("before") or {}
        clean_after = _redact_tf_sensitive_values(after, change.get("after_sensitive"))
        collected.append({
            "address": rc.get("address", f"{res_type}.{res_name}"),
            "type": res_type,
            "name": res_name,
            "mode": res_mode,
            "provider": rc.get("provider_name", "google"),
            "values": scrub_sensitive_data(clean_after) if isinstance(clean_after, dict) else {},
        })
    return collected


def extract_resources_from_tf_json(
    tf_json: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Optional[str], Dict[str, str], Set[str]]:
    """Recursively extracts resources, Terraform engine version, and provider versions."""
    collected: List[Dict[str, Any]] = []
    modules_used: Set[str] = set()
    tf_version = tf_json.get("terraform_version")
    provider_versions: Dict[str, str] = {}

    if isinstance(tf_json.get("configuration"), dict):
        p_cfg = tf_json["configuration"].get("provider_config", {})
        if isinstance(p_cfg, dict):
            for pk, pv in p_cfg.items():
                if isinstance(pv, dict) and pv.get("version_constraint"):
                    provider_versions[str(pv.get("name") or pk)] = str(pv["version_constraint"])

    def _walk_module(mod: Dict[str, Any]) -> None:
        if mod.get("address"):
            modules_used.add(mod["address"])
        for r in mod.get("resources", []):
            if r.get("mode", "managed") != "managed":
                continue
            clean_vals = _redact_tf_sensitive_values(r.get("values") or {}, r.get("sensitive_values"))
            collected.append({
                "address": r.get("address", f"{r.get('type')}.{r.get('name')}"),
                "type": r.get("type", ""),
                "name": r.get("name", ""),
                "mode": r.get("mode", "managed"),
                "provider": r.get("provider_name", "google"),
                "values": scrub_sensitive_data(clean_vals) if isinstance(clean_vals, dict) else {},
            })
        for child in mod.get("child_modules", []):
            _walk_module(child)

    for top_key in ("planned_values", "values"):
        if not collected and isinstance(tf_json.get(top_key), dict):
            rm = tf_json[top_key].get("root_module")
            if isinstance(rm, dict):
                _walk_module(rm)

    if not collected and isinstance(tf_json.get("resources"), list):
        collected = _extract_state_direct_resources(tf_json["resources"], modules_used)
    if not collected and isinstance(tf_json.get("resource_changes"), list):
        collected = _extract_resource_change_entries(tf_json["resource_changes"])

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
        "unparsed_terraform_files": [],
        "conditional_resources_undetermined": [],
        "modules_used": set(modules_used) if modules_used else set(),
        "all_resources": [],
        "terraform_engine_version": engine_version,
        "provider_versions": dict(provider_versions) if provider_versions else {},
        "ids_solution": "[CONFIG_REQUIRED: IDS/IPS Solution]",
        "connectivity_summary": "Not determined from IaC",
        "authentication_summary": "Not determined from IaC",
        "encryption_summary": "Not determined from IaC",
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
        tf_data["kms_keys"],
        tf_data["storage_buckets"],
        databases=tf_data.get("databases"),
        compute_instances=tf_data.get("compute_instances"),
        gke_clusters=tf_data.get("gke_clusters"),
        cloud_run_services=tf_data.get("cloud_run_services"),
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


def _ingest_vpc_and_subnet_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests google_project_service, google_compute_network, and google_compute_subnetwork."""
    if res_type == "google_project_service":
        svc = body.get("service") if isinstance(body, dict) else extract_hcl_attr(body, "service", vars_dict=vars_dict)
        if svc:
            tf_data["services"].add(str(svc))
    elif res_type == "google_compute_network":
        if "modules/fabric/" in rel_file:
            return
        raw_net = (body.get("name") if isinstance(body, dict) else extract_hcl_attr(body, "name", vars_dict=vars_dict)) or res_name
        net_name = clean_interpolated_string(raw_net, vars_dict) if vars_dict else str(raw_net)
        if is_valid_resource_name(net_name):
            tf_data["networks"].add(net_name)
    elif res_type == "google_compute_subnetwork":
        if "modules/fabric/" in rel_file:
            return
        if isinstance(body, dict):
            cidr = body.get("ip_cidr_range")
            sec_ranges = body.get("secondary_ip_range") or []
            if isinstance(sec_ranges, list):
                for sr in sec_ranges:
                    if isinstance(sr, dict) and is_valid_cidr(sr.get("ip_cidr_range")):
                        tf_data["subnets"].add(str(sr["ip_cidr_range"]))
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


def _extract_firewall_rule_entries(
    body: Dict[str, Any],
) -> Tuple[str, List[str], List[str], List[Dict[str, Any]]]:
    """Extracts action, protocols, ports, and structured entries from a firewall dict body."""
    allow_rules = list(body.get("allow") or [])
    deny_rules = list(body.get("deny") or [])
    if not allow_rules and not deny_rules and isinstance(body.get("dynamic"), list):
        for dyn in body["dynamic"]:
            if isinstance(dyn, dict):
                for key, target_list in (("allow", allow_rules), ("deny", deny_rules)):
                    if key in dyn:
                        d_c = dyn[key].get("content", dyn[key]) if isinstance(dyn[key], dict) else dyn[key]
                        if isinstance(d_c, dict):
                            target_list.append(d_c)
    action = "ALLOW" if allow_rules else ("DENY" if deny_rules else "ALLOW")
    rules = allow_rules if allow_rules else deny_rules
    protos: List[str] = []
    ports_list: List[str] = []
    entries: List[Dict[str, Any]] = []
    for r in rules:
        if isinstance(r, dict):
            proto = r.get("protocol", "tcp")
            entry_protos = [str(p) for p in proto] if isinstance(proto, (list, tuple, set)) else [str(proto)]
            protos.extend(entry_protos)
            ports = r.get("ports")
            if all(p.lower() in _PORTLESS_FIREWALL_PROTOCOLS for p in entry_protos):
                ports = []
            elif ports in (None, "", [], ()):
                ports = ["all"]
            if not isinstance(ports, (list, tuple, set)):
                ports = [ports]
            ports_list.extend([str(p) for p in ports])
            entries.append({"protocol": "/".join(entry_protos), "ports": [str(p) for p in ports]})
    return action, protos, ports_list, entries


def _ingest_firewall_dict(
    res_name: str, body: Dict[str, Any], tf_data: Dict[str, Any], vars_dict: Dict[str, Any]
) -> None:
    """Ingests a structured dict google_compute_firewall resource."""
    fw_name = _resolved_asset_name(body.get("name"), res_name, vars_dict, "firewall-rule")
    raw_net = body.get("network")
    fw_net = str(raw_net) if raw_net else "custom-vpc"
    if "${" in fw_net or _BARE_REF_PREFIX.match(fw_net):
        fw_net = _resolved_asset_name(fw_net, "", vars_dict, "custom-vpc")
    if "/" in fw_net:
        fw_net = fw_net.split("/")[-1]
    direction = body.get("direction", "INGRESS")
    action, protos, ports_list, entries = _extract_firewall_rule_entries(body)
    undetermined = "Not determined from IaC"
    proto_str = "/".join(sorted(set(protos))) if protos else undetermined
    if not ports_list and protos and all(p.lower() in _PORTLESS_FIREWALL_PROTOCOLS for p in protos):
        ports_str = "N/A"
    else:
        ports_str = ",".join(ports_list) if ports_list else undetermined
    fw_record: Dict[str, Any] = {
        "name": fw_name,
        "network": fw_net,
        "direction": direction,
        "protocol": proto_str,
        "ports": ports_str,
        "action": action,
        "source_ranges": _literal_cidrs(body.get("source_ranges")),
        "destination_ranges": _literal_cidrs(body.get("destination_ranges")),
    }
    if action == "ALLOW" and entries:
        fw_record["allowed"] = entries
    tf_data["firewall_rules"].append(fw_record)


def _ingest_firewall_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests google_compute_firewall resources from structured dicts or HCL text."""
    del res_type
    if "modules/fabric/" in rel_file:
        return
    if isinstance(body, dict):
        _ingest_firewall_dict(res_name, body, tf_data, vars_dict)
        return

    raw_net = extract_hcl_attr(body, "network", vars_dict=vars_dict)
    fw_net = _resolved_asset_name(raw_net, "", vars_dict, "custom-vpc") if raw_net else "custom-vpc"
    if "/" in fw_net:
        fw_net = fw_net.split("/")[-1]
    proto = clean_interpolated_string(
        extract_hcl_attr(body, "protocol", vars_dict=vars_dict) or "tcp", vars_dict, default_val="tcp"
    )
    p_m = re.search(r"ports\s*=\s*\[([^\]]+)\]", body)
    ports = clean_interpolated_string(
        p_m.group(1).replace('"', "").strip() if p_m else "all", vars_dict, default_val="all"
    )
    dir_m = clean_interpolated_string(
        extract_hcl_attr(body, "direction", vars_dict=vars_dict) or "INGRESS", vars_dict, default_val="INGRESS"
    )
    if "${" in dir_m or "each.value" in dir_m:
        dir_m = "INGRESS"
    if "${" in proto or "rule.value" in proto:
        proto = "tcp"
    has_allow = re.search(r'\ballow"?\s*\{', body) is not None
    has_deny = re.search(r'\bdeny"?\s*\{', body) is not None
    src_m = re.search(r"source_ranges\s*=\s*\[([^\]]*)\]", body)
    dst_m = re.search(r"destination_ranges\s*=\s*\[([^\]]*)\]", body)
    tf_data["firewall_rules"].append({
        "name": _asset_identifier(body, ("name",), res_name, vars_dict, "firewall-rule"),
        "network": fw_net,
        "direction": dir_m,
        "protocol": proto,
        "ports": ports,
        "action": "DENY" if (has_deny and not has_allow) else "ALLOW",
        "source_ranges": _literal_cidrs(_parse_hcl_list_items(src_m.group(1)) if src_m else None),
        "destination_ranges": _literal_cidrs(_parse_hcl_list_items(dst_m.group(1)) if dst_m else None),
    })


def _ingest_storage_bucket_dict(
    res_name: str, body: Dict[str, Any], rel_file: str, tf_data: Dict[str, Any], vars_dict: Dict[str, Any]
) -> None:
    """Ingests a structured dict google_storage_bucket resource."""
    b_name = _resolved_asset_name(body.get("name") or body.get("bucket"), res_name, vars_dict, "storage-bucket")
    raw_loc = body.get("location") or vars_dict.get("location") or vars_dict.get("region")
    loc = clean_interpolated_string(raw_loc, vars_dict, default_val="") if raw_loc else None
    if loc and ("${" in loc or "var." in loc or "local." in loc):
        loc = None
    enc = body.get("encryption") or []
    enc_dict = enc[0] if isinstance(enc, list) and enc else (enc if isinstance(enc, dict) else {})
    cmek_key = _resolved_cmek_name(
        enc_dict.get("default_kms_key_name") or body.get("kms_key_name"), vars_dict
    )
    vers = body.get("versioning") or []
    vers_dict = vers[0] if isinstance(vers, list) and vers else (vers if isinstance(vers, dict) else {})
    tf_data["storage_buckets"].append({
        "name": b_name,
        "location": loc,
        "storage_class": body.get("storage_class", "STANDARD"),
        "cmek_encrypted": bool(cmek_key),
        "kms_key": cmek_key,
        "versioning": bool(vers_dict.get("enabled", False)) if vers_dict else False,
        "uniform_bucket_level_access": bool(body.get("uniform_bucket_level_access", False)),
        "file": rel_file,
    })


def _ingest_storage_bucket_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests google_storage_bucket resources."""
    del res_type
    if "modules/fabric/" in rel_file:
        return
    if isinstance(body, dict):
        _ingest_storage_bucket_dict(res_name, body, rel_file, tf_data, vars_dict)
        return
    b_name = _asset_identifier(body, ("name", "bucket"), res_name, vars_dict, "storage-bucket")
    if not is_valid_resource_name(b_name) or "${" in b_name or "var." in b_name:
        return
    raw_loc = extract_hcl_attr(body, "location", vars_dict=vars_dict) or vars_dict.get("location") or vars_dict.get("region")
    loc = clean_interpolated_string(raw_loc, vars_dict, default_val="") if raw_loc else None
    if loc and ("${" in loc or "var." in loc or "local." in loc):
        loc = None
    raw_cmek = (
        extract_hcl_attr(body, "encryption.default_kms_key_name", vars_dict=vars_dict)
        or extract_hcl_attr(body, "default_kms_key_name", vars_dict=vars_dict)
        or extract_hcl_attr(body, "kms_key_name", vars_dict=vars_dict)
    )
    cmek_key = _resolved_cmek_name(raw_cmek, vars_dict)
    tf_data["storage_buckets"].append({
        "name": b_name,
        "location": loc,
        "storage_class": "STANDARD",
        "cmek_encrypted": bool(cmek_key),
        "kms_key": cmek_key,
        "versioning": _text_attr_tristate(body, "versioning"),
        "uniform_bucket_level_access": _text_attr_tristate(body, "uniform_bucket_level_access"),
        "file": rel_file,
    })


def _extract_vm_boot_disk_dict(
    boot_disk: Any, vars_dict: Dict[str, Any]
) -> Tuple[Optional[str], bool, Optional[str]]:
    """Extracts (kms_key, csek_bool, image) from a structured VM boot_disk block."""
    bd0 = (
        (boot_disk[0] if isinstance(boot_disk[0], dict) else {})
        if isinstance(boot_disk, list) and boot_disk
        else (boot_disk if isinstance(boot_disk, dict) else {})
    )
    if not bd0:
        return None, False, None
    kms_key = _resolved_cmek_name(bd0.get("kms_key_self_link"), vars_dict)
    csek = bool(
        bd0.get("disk_encryption_key_raw")
        or bd0.get("disk_encryption_key_rsa")
        or bd0.get("disk_encryption_key_sha256")
    )
    init_p = bd0.get("initialize_params")
    img = None
    if isinstance(init_p, list) and init_p and isinstance(init_p[0], dict):
        img = init_p[0].get("image")
    elif isinstance(init_p, dict):
        img = init_p.get("image")
    return kms_key, csek, img


def _ingest_compute_instance_dict(
    res_name: str, body: Dict[str, Any], rel_file: str, tf_data: Dict[str, Any], vars_dict: Dict[str, Any]
) -> None:
    """Ingests a structured dict google_compute_instance resource."""
    vm_name = _resolved_asset_name(body.get("name"), res_name, vars_dict, "compute-instance")
    m_type = _resolve_optional_attr(body.get("machine_type"), vars_dict, default_val=NOT_DETERMINED)
    zone = _resolve_optional_attr(body.get("zone") or vars_dict.get("zone"), vars_dict, default_val=None)
    network_ip, subnetwork, has_pub_ip = None, "", False
    nics = body.get("network_interface") or []
    if isinstance(nics, list) and nics and isinstance(nics[0], dict):
        nic0 = nics[0]
        network_ip = nic0.get("network_ip")
        raw_sub = nic0.get("subnetwork", "")
        subnetwork = _resolved_asset_name(raw_sub, "", vars_dict, "") if raw_sub else ""
        if "/" in subnetwork:
            subnetwork = subnetwork.split("/")[-1]
        has_pub_ip = bool(nic0.get("access_config"))

    shielded = body.get("shielded_instance_config")
    s_dict = (
        (shielded[0] if isinstance(shielded[0], dict) else {})
        if isinstance(shielded, list) and shielded
        else (shielded if isinstance(shielded, dict) else {})
    )
    is_shielded = bool(s_dict["enable_secure_boot"]) if "enable_secure_boot" in s_dict else None
    kms_key, csek, img = _extract_vm_boot_disk_dict(body.get("boot_disk"), vars_dict)
    raw_p_id = (
        body.get("project")
        or vars_dict.get("project_id")
        or vars_dict.get("main_project_id")
        or vars_dict.get("project")
        or ""
    )
    p_id = _resolve_optional_attr(raw_p_id, vars_dict, default_val="") or ""
    zone_seg = zone or "unspecified"
    tf_data["compute_instances"].append({
        "name": vm_name,
        "machine_type": m_type,
        "zone": zone,
        "network_ip": network_ip,
        "subnetwork": subnetwork,
        "image": img,
        "kms_key": kms_key,
        "customer_supplied_key": csek,
        "has_public_ip": has_pub_ip,
        "shielded_vm": is_shielded,
        "self_link": f"projects/{p_id}/zones/{zone_seg}/instances/{vm_name}" if p_id else f"zones/{zone_seg}/instances/{vm_name}",
        "file": rel_file,
    })


def _ingest_compute_instance_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests google_compute_instance and google_compute_instance_from_template."""
    del res_type
    if "modules/fabric/compute-vm" in rel_file or "recipes/" in rel_file:
        return
    if isinstance(body, dict):
        _ingest_compute_instance_dict(res_name, body, rel_file, tf_data, vars_dict)
        return

    vm_name = _asset_identifier(body, ("name",), res_name, vars_dict, "compute-instance")
    if not vm_name or vm_name.startswith("${") or vm_name in ("default", "instance"):
        return
    m_type = _resolve_optional_attr(
        extract_hcl_attr(body, "machine_type", vars_dict=vars_dict), vars_dict, default_val=NOT_DETERMINED
    )
    zone = _resolve_optional_attr(
        extract_hcl_attr(body, "zone", vars_dict=vars_dict) or vars_dict.get("zone"), vars_dict, default_val=None
    )
    net_ip = extract_hcl_attr(body, "network_ip", vars_dict=vars_dict)
    if net_ip in ("try", "lookup", "None", "") or not net_ip or str(net_ip).startswith("${"):
        net_ip = None
    raw_subnet = extract_hcl_attr(body, "subnetwork", vars_dict=vars_dict)
    subnet = _resolved_asset_name(raw_subnet, "", vars_dict, "workload-subnet") if raw_subnet else "workload-subnet"
    img = _resolve_optional_attr(extract_hcl_attr(body, "image", vars_dict=vars_dict), vars_dict, default_val=None)
    kms_key = _resolved_cmek_name(extract_hcl_attr(body, "kms_key_self_link", vars_dict=vars_dict), vars_dict)
    csek = bool(extract_hcl_attr(body, "disk_encryption_key_raw", vars_dict=vars_dict))
    has_pub_ip = "access_config" in body
    is_shielded = None
    if "enable_secure_boot" in body:
        match = re.search(r"enable_secure_boot\s*=\s*(true|false)", body, re.IGNORECASE)
        if match:
            is_shielded = match.group(1).lower() == "true"
    raw_p_id = (
        vars_dict.get("project_id")
        or vars_dict.get("main_project_id")
        or vars_dict.get("prod_project_id")
        or vars_dict.get("service_project_id")
        or ""
    )
    p_id = _resolve_optional_attr(raw_p_id, vars_dict, default_val="") or ""
    zone_seg = zone or "unspecified"
    tf_data["compute_instances"].append({
        "name": vm_name,
        "machine_type": m_type,
        "zone": zone,
        "network_ip": net_ip,
        "subnetwork": subnet,
        "image": img,
        "kms_key": kms_key,
        "customer_supplied_key": csek,
        "has_public_ip": has_pub_ip,
        "shielded_vm": is_shielded,
        "self_link": f"projects/{p_id}/zones/{zone_seg}/instances/{vm_name}" if p_id else f"zones/{zone_seg}/instances/{vm_name}",
        "file": rel_file,
    })


def _ingest_kms_key_dict(
    res_type: str, res_name: str, body: Dict[str, Any], rel_file: str, tf_data: Dict[str, Any], vars_dict: Dict[str, Any]
) -> None:
    """Ingests a structured dict google_kms_crypto_key resource."""
    key_name = _resolved_asset_name(body.get("name") or body.get("description"), res_name, vars_dict, "kms-key")
    kr = _resolved_asset_name(body.get("key_ring") or res_name, res_name, vars_dict, res_name)
    if "/" in kr:
        kr = kr.split("/")[-1]
    vt = body.get("version_template") or []
    vt_dict = vt[0] if isinstance(vt, list) and vt else (vt if isinstance(vt, dict) else {})
    prot = vt_dict.get("protection_level") or body.get("protection_level") or "SOFTWARE"
    tf_data["kms_keys"].append({
        "type": res_type,
        "name": key_name,
        "key_ring": kr,
        "protection_level": prot,
        "algorithm": vt_dict.get("algorithm") or None,
        "purpose": body.get("purpose", "ENCRYPT_DECRYPT"),
        "rotation_period": body.get("rotation_period") or None,
        "file": rel_file,
    })


def _ingest_kms_key_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests google_kms_crypto_key resources."""
    if "modules/fabric/kms" in rel_file:
        return
    if isinstance(body, dict):
        _ingest_kms_key_dict(res_type, res_name, body, rel_file, tf_data, vars_dict)
        return

    raw_key = extract_hcl_attr(body, "name", vars_dict=vars_dict) or extract_hcl_attr(body, "description", vars_dict=vars_dict) or res_name
    prot_raw = extract_hcl_attr(body, "protection_level", vars_dict=vars_dict)
    if not prot_raw:
        prot_m = re.search(r'protection_level\s*=\s*"?(HSM|SOFTWARE|EXTERNAL[A-Z_]*)"?', str(body), re.IGNORECASE)
        prot_raw = prot_m.group(1) if prot_m else "SOFTWARE"
    prot_upper = str(prot_raw).upper()
    prot = (
        "HSM"
        if "HSM" in prot_upper
        else ("EXTERNAL_VPC" if "EXTERNAL_VPC" in prot_upper else ("EXTERNAL" if "EXTERNAL" in prot_upper else "SOFTWARE"))
    )
    kr = clean_interpolated_string(extract_hcl_attr(body, "key_ring", vars_dict=vars_dict) or res_name, vars_dict, default_val=res_name)
    purp = extract_hcl_attr(body, "purpose", vars_dict=vars_dict) or "ENCRYPT_DECRYPT"
    rot = extract_hcl_attr(body, "rotation_period", vars_dict=vars_dict) or None

    if "${each." in str(raw_key):
        keys_list = vars_dict.get("keys") or vars_dict.get("var.keys") or []
        if isinstance(keys_list, list) and keys_list:
            for subk in keys_list:
                tf_data["kms_keys"].append({
                    "type": res_type,
                    "name": re.sub(r"\$\{each\.(?:value|key)\}", str(subk), raw_key),
                    "key_ring": kr,
                    "protection_level": prot,
                    "purpose": purp,
                    "rotation_period": rot,
                    "file": rel_file,
                })
            return

    if raw_key.startswith("${") and ("var.keyring" in raw_key or "each.key" in raw_key or "each.value" in raw_key):
        return
    tf_data["kms_keys"].append({
        "type": res_type,
        "name": clean_interpolated_string(raw_key, vars_dict, default_val=res_name),
        "key_ring": kr,
        "protection_level": prot,
        "purpose": purp,
        "rotation_period": rot,
        "file": rel_file,
    })


def _ingest_bigquery_or_spanner_dict(
    res_type: str, res_name: str, body: Dict[str, Any], rel_file: str, tf_data: Dict[str, Any], vars_dict: Dict[str, Any]
) -> None:
    """Ingests structured BigQuery dataset or Spanner instance dict."""
    if res_type == "google_bigquery_dataset":
        ds_id = _resolved_asset_name(body.get("dataset_id") or body.get("name"), res_name, vars_dict, "bigquery-dataset")
        enc = body.get("default_encryption_configuration") or []
        enc_dict = enc[0] if isinstance(enc, list) and enc and isinstance(enc[0], dict) else (enc if isinstance(enc, dict) else {})
        raw_kms = enc_dict.get("kms_key_name") or body.get("kms_key_name") or body.get("encryption_key")
        loc = _resolve_optional_attr(
            body.get("location") or vars_dict.get("location") or vars_dict.get("region"), vars_dict, default_val=None
        )
        tf_data["databases"].append({
            "type": res_type,
            "name": ds_id,
            "database_version": "Serverless Enterprise",
            "tier": "Enterprise Cloud Data Warehouse",
            "region": loc,
            "private_network": "Google Private Backbone / PSC",
            "cmek_key": _resolved_cmek_name(raw_kms, vars_dict),
            "require_ssl": True,
            "backup_enabled": True,
            "has_public_ip": False,
            "file": rel_file,
        })
    else:
        db_name = _resolved_asset_name(body.get("name") or body.get("display_name"), res_name, vars_dict, "spanner-instance")
        reg = _resolve_optional_attr(body.get("config") or body.get("region") or vars_dict.get("region"), vars_dict, default_val=None)
        pu = body.get("processing_units") or body.get("num_nodes")
        tf_data["databases"].append({
            "type": res_type,
            "name": db_name,
            "database_version": "CLOUD_SPANNER",
            "tier": f"{pu} PU/Nodes" if pu else "Managed Spanner Instance",
            "region": reg,
            "private_network": "Google Private Backbone / PSC",
            "cmek_key": _resolved_cmek_name(body.get("kms_key_name"), vars_dict),
            "require_ssl": True,
            "backup_enabled": True,
            "has_public_ip": False,
            "file": rel_file,
        })


def _ingest_redis_dict(
    res_type: str, res_name: str, body: Dict[str, Any], rel_file: str, tf_data: Dict[str, Any], vars_dict: Dict[str, Any]
) -> None:
    """Ingests structured Memorystore Redis dict."""
    db_name = _resolved_asset_name(body.get("name"), res_name, vars_dict, "memorystore-redis")
    p_net = body.get("authorized_network")
    if p_net and ("${" in str(p_net) or _BARE_REF_PREFIX.match(str(p_net))):
        p_net = _resolved_asset_name(str(p_net), "", vars_dict, "") or "VPC network (reference resolved at apply time)"
    if p_net and "/" in str(p_net):
        p_net = str(p_net).split("/")[-1]
    tf_data["databases"].append({
        "type": res_type,
        "name": db_name,
        "database_version": _resolve_optional_attr(body.get("redis_version"), vars_dict, default_val="REDIS_7_0"),
        "tier": _resolve_optional_attr(body.get("tier"), vars_dict, default_val="STANDARD_HA"),
        "region": _resolve_optional_attr(body.get("region") or vars_dict.get("region"), vars_dict, default_val=None),
        "private_network": p_net,
        "cmek_key": _resolved_cmek_name(body.get("customer_managed_key"), vars_dict),
        "require_ssl": str(body.get("transit_encryption_mode") or "").upper() == "SERVER_AUTHENTICATION",
        "backup_enabled": bool(body.get("persistence_config")),
        "has_public_ip": False,
        "file": rel_file,
    })


def _resolve_sql_dict_ip_and_ssl(
    ip_dict: Dict[str, Any], body: Dict[str, Any], res_type: str, vars_dict: Dict[str, Any]
) -> Tuple[Optional[str], bool, bool]:
    """Resolves (private_network, require_ssl, has_public_ip) from a Cloud SQL / AlloyDB dict."""
    p_net = ip_dict.get("private_network") or ip_dict.get("network") or body.get("network")
    if p_net and ("${" in str(p_net) or _BARE_REF_PREFIX.match(str(p_net))):
        p_net = _resolved_asset_name(str(p_net), "", vars_dict, "") or "VPC network (reference resolved at apply time)"
    if p_net and "/" in str(p_net):
        p_net = str(p_net).split("/")[-1]
    ssl_mode = str(ip_dict.get("ssl_mode") or "").upper()
    req_ssl = (
        ssl_mode in ("ENCRYPTED_ONLY", "TRUSTED_CLIENT_CERTIFICATE_REQUIRED")
        if ssl_mode
        else bool(ip_dict.get("require_ssl", False))
    )
    has_pub = bool(ip_dict.get("ipv4_enabled", res_type == "google_sql_database_instance"))
    return p_net, req_ssl, has_pub


def _ingest_sql_or_alloydb_dict(
    res_type: str, res_name: str, body: Dict[str, Any], rel_file: str, tf_data: Dict[str, Any], vars_dict: Dict[str, Any]
) -> None:
    """Ingests structured Cloud SQL or AlloyDB dict."""
    db_name = _resolved_asset_name(body.get("name") or body.get("cluster_id"), res_name, vars_dict, "database-instance")
    db_ver = _resolve_optional_attr(body.get("database_version"), vars_dict, default_val=NOT_DETERMINED)
    reg = _resolve_optional_attr(body.get("region") or body.get("location") or vars_dict.get("region"), vars_dict, default_val=None)
    settings = body.get("settings") or []
    s_dict = settings[0] if isinstance(settings, list) and settings else (settings if isinstance(settings, dict) else {})
    tier = _resolve_optional_attr(s_dict.get("tier"), vars_dict, default_val=NOT_DETERMINED)
    ip_cfg = s_dict.get("ip_configuration") or body.get("network_config") or []
    ip_dict = ip_cfg[0] if isinstance(ip_cfg, list) and ip_cfg else (ip_cfg if isinstance(ip_cfg, dict) else {})
    p_net, req_ssl, has_pub = _resolve_sql_dict_ip_and_ssl(ip_dict, body, res_type, vars_dict)
    bkp_cfg = s_dict.get("backup_configuration") or body.get("automated_backup_policy") or []
    bkp_dict = bkp_cfg[0] if isinstance(bkp_cfg, list) and bkp_cfg else (bkp_cfg if isinstance(bkp_cfg, dict) else {})
    enc_cfg = body.get("encryption_config") or []
    enc_dict = enc_cfg[0] if isinstance(enc_cfg, list) and enc_cfg else (enc_cfg if isinstance(enc_cfg, dict) else {})
    cmek = _resolved_cmek_name(body.get("encryption_key_name") or enc_dict.get("kms_key_name"), vars_dict)
    tf_data["databases"].append({
        "type": res_type,
        "name": db_name,
        "database_version": db_ver,
        "tier": tier,
        "region": reg,
        "private_network": p_net,
        "cmek_key": cmek,
        "require_ssl": req_ssl,
        "backup_enabled": bool(bkp_dict.get("enabled", False)),
        "has_public_ip": has_pub,
        "file": rel_file,
    })


def _resolve_db_text_ssl_and_backup(
    res_type: str, body: Union[HclBlock, str]
) -> Tuple[Optional[bool], Optional[bool], bool]:
    """Resolves (require_ssl, backup_enabled, has_public_ip) from raw database HCL text."""
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
    ipv4_flag = _text_attr_tristate(body, "ipv4_enabled")
    if ipv4_flag is None:
        ipv4_flag = res_type == "google_sql_database_instance"
    return req_ssl, bkp_enabled, bool(ipv4_flag) or "authorized_networks" in body


def _ingest_database_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests Cloud SQL, AlloyDB, BigQuery, Cloud Spanner, and Memorystore Redis resources."""
    if "modules/fabric/" in rel_file:
        return
    if isinstance(body, dict):
        if res_type in ("google_bigquery_dataset", "google_spanner_instance"):
            _ingest_bigquery_or_spanner_dict(res_type, res_name, body, rel_file, tf_data, vars_dict)
        elif res_type == "google_redis_instance":
            _ingest_redis_dict(res_type, res_name, body, rel_file, tf_data, vars_dict)
        else:
            _ingest_sql_or_alloydb_dict(res_type, res_name, body, rel_file, tf_data, vars_dict)
        return

    raw_name = extract_hcl_attr(body, "name", vars_dict=vars_dict) or extract_hcl_attr(body, "dataset_id", vars_dict=vars_dict) or res_name
    if raw_name.startswith("${") and ("var.id" in raw_name or "local.prefix" in raw_name or "each.key" in raw_name):
        return
    db_name = _resolved_asset_name(raw_name, res_name, vars_dict, "database-instance")
    raw_ver = extract_hcl_attr(body, "database_version", vars_dict=vars_dict) or extract_hcl_attr(body, "redis_version", vars_dict=vars_dict)
    if res_type == "google_spanner_instance":
        db_ver: Optional[str] = "CLOUD_SPANNER"
    elif res_type == "google_redis_instance":
        db_ver = _resolve_optional_attr(raw_ver, vars_dict, default_val="REDIS_7_0")
    elif res_type == "google_bigquery_dataset":
        db_ver = "Serverless Enterprise"
    else:
        db_ver = _resolve_optional_attr(raw_ver, vars_dict, default_val=NOT_DETERMINED)

    tier = _resolve_optional_attr(
        extract_hcl_attr(body, "tier", vars_dict=vars_dict),
        vars_dict,
        default_val="STANDARD_HA" if res_type == "google_redis_instance" else NOT_DETERMINED,
    )
    raw_reg = extract_hcl_attr(body, "region", vars_dict=vars_dict) or extract_hcl_attr(body, "location", vars_dict=vars_dict) or vars_dict.get("region")
    reg = _resolve_optional_attr(raw_reg, vars_dict, default_val=None)
    p_net = extract_hcl_attr(body, "private_network", vars_dict=vars_dict) or extract_hcl_attr(body, "authorized_network", vars_dict=vars_dict)
    if p_net:
        if "psa_private_network" in str(p_net):
            p_net = "Private VPC / Private Service Connect (PSC)"
        else:
            p_clean = clean_interpolated_string(str(p_net), vars_dict)
            p_net = None if ("var." in p_clean or "local." in p_clean or "${" in p_clean or not is_valid_resource_name(p_clean)) else p_clean
    raw_cmek = (
        extract_hcl_attr(body, "encryption_key_name", vars_dict=vars_dict)
        or extract_hcl_attr(body, "kms_key_name", vars_dict=vars_dict)
        or extract_hcl_attr(body, "customer_managed_key", vars_dict=vars_dict)
    )
    req_ssl, bkp_enabled, has_pub = _resolve_db_text_ssl_and_backup(res_type, body)
    tf_data["databases"].append({
        "type": res_type,
        "name": db_name,
        "database_version": db_ver,
        "tier": tier,
        "region": reg,
        "private_network": p_net,
        "cmek_key": _resolved_cmek_name(raw_cmek, vars_dict),
        "require_ssl": req_ssl,
        "backup_enabled": bkp_enabled,
        "has_public_ip": has_pub,
        "file": rel_file,
    })


def _ingest_gke_cluster_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests google_container_cluster resources."""
    del res_type
    if isinstance(body, dict):
        c_name = _resolved_asset_name(body.get("name"), res_name, vars_dict, "gke-cluster")
        loc = _resolve_optional_attr(body.get("location") or vars_dict.get("location") or vars_dict.get("region"), vars_dict, default_val=None)
        m_ver = _resolve_optional_attr(body.get("min_master_version") or body.get("master_version"), vars_dict, default_val=None)
        p_cfg = body.get("private_cluster_config") or []
        p_dict = p_cfg[0] if isinstance(p_cfg, list) and p_cfg else (p_cfg if isinstance(p_cfg, dict) else {})
        db_enc = body.get("database_encryption") or []
        db_enc_dict = db_enc[0] if isinstance(db_enc, list) and db_enc else (db_enc if isinstance(db_enc, dict) else {})
        tf_data["gke_clusters"].append({
            "name": c_name,
            "master_version": m_ver,
            "master_ipv4_cidr_block": _resolve_optional_attr(p_dict.get("master_ipv4_cidr_block"), vars_dict, default_val=None),
            "location": loc,
            "private_cluster": bool(p_dict.get("enable_private_nodes", False)),
            "private_endpoint": bool(p_dict.get("enable_private_endpoint", False)),
            "workload_identity": bool(body.get("workload_identity_config")),
            "kms_key": _resolved_cmek_name(db_enc_dict.get("key_name") or body.get("kms_key"), vars_dict),
            "file": rel_file,
        })
        return

    cluster_name = _asset_identifier(body, ("name",), res_name, vars_dict, "gke-cluster")
    m_ver = _resolve_optional_attr(
        extract_hcl_attr(body, "min_master_version", vars_dict=vars_dict) or extract_hcl_attr(body, "master_version", vars_dict=vars_dict),
        vars_dict,
        default_val=None,
    )
    cidr = _resolve_optional_attr(extract_hcl_attr(body, "master_ipv4_cidr_block", vars_dict=vars_dict), vars_dict, default_val=None)
    raw_loc = extract_hcl_attr(body, "location", vars_dict=vars_dict) or vars_dict.get("location") or vars_dict.get("region")
    kms_key = _resolved_cmek_name(
        extract_hcl_attr(body, "database_encryption.key_name", vars_dict=vars_dict) or extract_hcl_attr(body, "key_name", vars_dict=vars_dict),
        vars_dict,
    )
    tf_data["gke_clusters"].append({
        "name": cluster_name,
        "master_version": m_ver,
        "master_ipv4_cidr_block": cidr,
        "location": _resolve_optional_attr(raw_loc, vars_dict, default_val=None),
        "private_cluster": _text_attr_tristate(body, "enable_private_nodes"),
        "private_endpoint": _text_attr_tristate(body, "enable_private_endpoint"),
        "workload_identity": "workload_identity_config" in body,
        "kms_key": kms_key,
        "file": rel_file,
    })


def _ingest_service_account_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests google_service_account, google_project_service_identity, and google_service_account_key."""
    if res_type == "google_service_account":
        if "modules/fabric/" in rel_file:
            return
        if isinstance(body, dict):
            raw_acct = body.get("account_id")
            if isinstance(raw_acct, str) and ("${" in raw_acct or "var." in raw_acct):
                acct_id = _resolve_optional_attr(raw_acct, vars_dict, default_val=None) or _resolved_asset_name(
                    None, res_name, vars_dict, "service-account"
                )
            else:
                acct_id = _resolved_asset_name(raw_acct, res_name, vars_dict, "service-account")
            disp = _resolve_optional_attr(body.get("display_name"), vars_dict, default_val=acct_id) or acct_id
            sa_record: Dict[str, Any] = {
                "resource_name": res_name,
                "account_id": acct_id,
                "display_name": disp,
                "file": rel_file,
            }
            sa_project = _resolve_optional_attr(body.get("project"), vars_dict, default_val=None)
            raw_email = _resolve_optional_attr(body.get("email"), vars_dict, default_val=None)
            if raw_email:
                sa_record["email"] = raw_email
            elif sa_project and is_valid_resource_name(sa_project):
                sa_record["email"] = f"{acct_id}@{sa_project}.iam.gserviceaccount.com"
            else:
                logger.debug("Service account %r declares no resolved project; omitting email.", acct_id)
            if sa_project and is_valid_resource_name(sa_project):
                sa_record["project"] = sa_project
            tf_data["service_accounts"].append(sa_record)
        else:
            raw_acct = extract_hcl_attr(body, "account_id", vars_dict=vars_dict) or res_name
            acct_id = _resolve_optional_attr(raw_acct, vars_dict, default_val=res_name) or res_name
            if not is_valid_resource_name(acct_id) or "${" in acct_id or (vars_dict and "var." in acct_id):
                return
            disp = _resolve_optional_attr(extract_hcl_attr(body, "display_name", vars_dict=vars_dict), vars_dict, default_val=acct_id) or acct_id
            sa_record = {"resource_name": res_name, "account_id": acct_id, "display_name": disp, "file": rel_file}
            sa_project = _resolve_optional_attr(extract_hcl_attr(body, "project", vars_dict=vars_dict), vars_dict, default_val=None)
            if sa_project and is_valid_resource_name(sa_project):
                sa_record["project"] = sa_project
                sa_record["email"] = f"{acct_id}@{sa_project}.iam.gserviceaccount.com"
            tf_data["service_accounts"].append(sa_record)
    elif res_type == "google_project_service_identity":
        svc = body.get("service") if isinstance(body, dict) else extract_hcl_attr(body, "service", vars_dict=vars_dict)
        svc_clean = _resolve_optional_attr(svc, vars_dict, default_val=res_name) or res_name
        sa_record = {
            "resource_name": res_name,
            "account_id": res_name,
            "display_name": f"Google-Managed Service Identity ({svc_clean})",
            "service": svc_clean,
            "file": rel_file,
        }
        raw_proj = body.get("project") if isinstance(body, dict) else extract_hcl_attr(body, "project", vars_dict=vars_dict)
        sa_proj = _resolve_optional_attr(raw_proj, vars_dict, default_val=None)
        if sa_proj and is_valid_resource_name(sa_proj):
            sa_record["project"] = sa_proj
        tf_data["service_accounts"].append(sa_record)
    elif res_type == "google_service_account_key":
        sa_id = _asset_identifier(body, ("service_account_id",), res_name, vars_dict, "service-account-key")
        tf_data["service_account_keys"].append({"service_account": sa_id, "name": res_name, "file": rel_file})


def _ingest_iam_binding_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests google_*_iam_member and google_*_iam_binding resources."""
    if "modules/fabric/" in rel_file:
        return
    res_scope = res_type.split("_iam_")[0].replace("google_", "")
    if isinstance(body, dict):
        role_val = body.get("role", "Custom Role")
        members: List[Any] = []
        if body.get("member"):
            members.append(body["member"])
        if isinstance(body.get("members"), list):
            members.extend(body["members"])
        body_text = ""
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
        members_match = re.search(r"members\s*=\s*\[([^\]]+)\]", body)
        if members_match:
            members = [m.strip(' "\'\n\r\t') for m in members_match.group(1).split(",") if m.strip(' "\'\n\r\t')]
        else:
            member_match = re.search(r'member\s*=\s*"([^"]+)"', body)
            mem_val = member_match.group(1) if member_match else extract_hcl_attr(body, "member", vars_dict=vars_dict)
            if mem_val:
                members.append(mem_val)
        body_text = body

    for mem in members:
        resolved_mem = resolve_iam_principal(
            mem=mem,
            body=body_text,
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


def _ingest_cloud_run_or_function_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests Cloud Run and Cloud Functions resources."""
    if res_type in ("google_cloud_run_service", "google_cloud_run_v2_service"):
        if "modules/fabric/" in rel_file:
            return
        cr_name = _asset_identifier(body, ("name",), res_name, vars_dict, "cloud-run-service")
        raw_loc = (
            (body.get("location") if isinstance(body, dict) else extract_hcl_attr(body, "location", vars_dict=vars_dict))
            or vars_dict.get("location")
            or vars_dict.get("region")
        )
        cr_loc = clean_interpolated_string(raw_loc, vars_dict, default_val="") if raw_loc else None
        if cr_loc and ("${" in cr_loc or "var." in cr_loc or "local." in cr_loc):
            cr_loc = None
        cr_img = (
            (body.get("image") if isinstance(body, dict) else extract_hcl_attr(body, "image", vars_dict=vars_dict))
            or extract_hcl_attr(body, "template.containers.image", vars_dict=vars_dict)
            or extract_hcl_attr(body, "template.spec.containers.image", vars_dict=vars_dict)
        )
        raw_kms = (
            extract_hcl_attr(body, "template.encryption_key", vars_dict=vars_dict)
            or (body.get("encryption_key") if isinstance(body, dict) else extract_hcl_attr(body, "encryption_key", vars_dict=vars_dict))
            or (body.get("kms_key") if isinstance(body, dict) else None)
        )
        if not isinstance(cr_img, str) or not cr_img or "${" in cr_img or "local." in cr_img or "var." in cr_img:
            cr_img = "us-docker.pkg.dev/cloudrun/container/workload:latest"
        tf_data["cloud_run_services"].append({
            "name": cr_name,
            "location": cr_loc,
            "image": cr_img,
            "kms_key": _resolved_cmek_name(raw_kms, vars_dict),
            "file": rel_file,
        })
    elif res_type in ("google_cloudfunctions_function", "google_cloudfunctions2_function"):
        fn_name = _asset_identifier(body, ("name",), res_name, vars_dict, "cloud-function")
        fn_rt = (
            extract_hcl_attr(body, "build_config.runtime", vars_dict=vars_dict)
            or (body.get("runtime") if isinstance(body, dict) else extract_hcl_attr(body, "runtime", vars_dict=vars_dict))
            or "python311"
        )
        tf_data["cloud_functions"].append({"name": fn_name, "runtime": fn_rt, "file": rel_file})


def _ingest_serverless_and_security_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    vars_dict: Dict[str, Any],
) -> None:
    """Ingests logging sinks, secrets, PubSub, serverless, perimeter, and VPN resources."""
    if "google_logging" in res_type and "sink" in res_type:
        sink_name = _asset_identifier(body, ("name",), res_name, vars_dict, "logging-sink")
        dest = body.get("destination", "") if isinstance(body, dict) else (extract_hcl_attr(body, "destination", vars_dict=vars_dict) or "")
        tf_data["logging_sinks"].append({"name": sink_name, "destination": str(dest), "file": rel_file})
    elif res_type == "google_secret_manager_secret":
        tf_data.setdefault("secrets", []).append(res_name)
    elif res_type == "google_pubsub_topic":
        tf_data.setdefault("pubsub_topics", []).append(res_name)
    elif res_type == "google_artifact_registry_repository":
        tf_data.setdefault("artifact_registries", []).append(res_name)
    elif res_type in (
        "google_cloud_run_service", "google_cloud_run_v2_service",
        "google_cloudfunctions_function", "google_cloudfunctions2_function",
    ):
        _ingest_cloud_run_or_function_resource(res_type, res_name, body, rel_file, tf_data, vars_dict)
    elif res_type == "google_compute_router_nat":
        tf_data["nat_gateways"].append({"name": _asset_identifier(body, ("name",), res_name, vars_dict, "cloud-nat"), "file": rel_file})
    elif res_type in ("google_compute_global_forwarding_rule", "google_compute_forwarding_rule"):
        tf_data["forwarding_rules"].append({"name": _asset_identifier(body, ("name",), res_name, vars_dict, "forwarding-rule"), "file": rel_file})
    elif res_type == "google_compute_security_policy":
        tf_data["security_policies"].append({"name": _asset_identifier(body, ("name",), res_name, vars_dict, "security-policy"), "file": rel_file})
        tf_data["ids_solution"] = "Google Cloud Armor security policy"
    elif res_type == "google_access_context_manager_service_perimeter":
        tf_data["service_perimeters"].append({"name": _asset_identifier(body, ("title", "name"), res_name, vars_dict, "service-perimeter"), "file": rel_file})
    elif res_type == "google_binary_authorization_policy":
        tf_data["binary_authorization"].append({"name": res_name, "file": rel_file})
    elif res_type == "google_dataproc_cluster":
        tf_data["dataproc_clusters"].append({"name": _asset_identifier(body, ("name",), res_name, vars_dict, "dataproc-cluster"), "file": rel_file})
    elif res_type == "google_assured_workloads_workload":
        tf_data["assured_workloads"].append(rel_file)
    elif res_type in (
        "google_compute_vpn_gateway", "google_compute_ha_vpn_gateway",
        "google_compute_vpn_tunnel", "google_compute_interconnect_attachment",
    ):
        gw_name = _asset_identifier(body, ("name",), res_name, vars_dict, "boundary-connection")
        peer_ip = (
            (body.get("peer_ip") or body.get("peer_gcp_gateway"))
            if isinstance(body, dict)
            else (extract_hcl_attr(body, "peer_ip", vars_dict=vars_dict) or extract_hcl_attr(body, "peer_gcp_gateway", vars_dict=vars_dict))
        )
        peer_asn = body.get("peer_asn") if isinstance(body, dict) else extract_hcl_attr(body, "peer_asn", vars_dict=vars_dict)
        if isinstance(peer_ip, str) and ("${" in peer_ip or _BARE_REF_PREFIX.match(peer_ip)):
            peer_ip = _resolved_asset_name(peer_ip, "", vars_dict, "") or "Peer gateway (reference resolved at apply time)"
        tf_data.setdefault("boundary_connections", []).append({
            "name": gw_name, "type": res_type, "peer_ip": peer_ip, "peer_asn": peer_asn, "file": rel_file,
        })


_RESOURCE_HANDLERS: Final[Dict[str, Callable[..., None]]] = {
    "google_project_service": _ingest_vpc_and_subnet_resource,
    "google_compute_network": _ingest_vpc_and_subnet_resource,
    "google_compute_subnetwork": _ingest_vpc_and_subnet_resource,
    "google_compute_firewall": _ingest_firewall_resource,
    "google_storage_bucket": _ingest_storage_bucket_resource,
    "google_compute_instance": _ingest_compute_instance_resource,
    "google_compute_instance_from_template": _ingest_compute_instance_resource,
    "google_kms_crypto_key": _ingest_kms_key_resource,
    "google_sql_database_instance": _ingest_database_resource,
    "google_alloydb_cluster": _ingest_database_resource,
    "google_bigquery_dataset": _ingest_database_resource,
    "google_spanner_instance": _ingest_database_resource,
    "google_redis_instance": _ingest_database_resource,
    "google_container_cluster": _ingest_gke_cluster_resource,
    "google_service_account": _ingest_service_account_resource,
    "google_project_service_identity": _ingest_service_account_resource,
    "google_service_account_key": _ingest_service_account_resource,
}

_IAM_RESOURCE_PREFIXES: Final[Tuple[str, ...]] = (
    "google_project_iam_",
    "google_organization_iam_",
    "google_folder_iam_",
    "google_storage_bucket_iam_",
    "google_kms_crypto_key_iam_",
    "google_kms_key_ring_iam_",
    "google_service_account_iam_",
)


def classify_and_ingest_resource(
    res_type: str,
    res_name: str,
    body: Union[Dict[str, Any], HclBlock, str],
    rel_file: str,
    tf_data: Dict[str, Any],
    resolved_vars: Optional[Dict[str, Any]] = None,
) -> None:
    """Classifies and ingests a single infrastructure resource into tf_data."""
    vars_dict = resolved_vars or {}
    tf_data["all_resources"].append({
        "type": res_type,
        "name": res_name,
        "category": classify_resource_category(res_type),
        "file": rel_file,
    })
    handler = _RESOURCE_HANDLERS.get(res_type)
    if handler is not None:
        handler(res_type, res_name, body, rel_file, tf_data, vars_dict)
    elif res_type.startswith(_IAM_RESOURCE_PREFIXES):
        _ingest_iam_binding_resource(res_type, res_name, body, rel_file, tf_data, vars_dict)
    else:
        _ingest_serverless_and_security_resource(res_type, res_name, body, rel_file, tf_data, vars_dict)


def ingest_terraform_json(
    tf_json: Dict[str, Any],
    user_config: Optional[Dict[str, Any]] = None,
    target_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Ingests and translates HashiCorp Terraform JSON output into system components."""
    resources, tf_ver, prov_versions, modules_used = extract_resources_from_tf_json(tf_json)
    tf_data = init_empty_tf_data(
        user_config=user_config,
        engine_version=tf_ver,
        provider_versions=prov_versions,
        modules_used=modules_used,
    )
    for item in resources:
        classify_and_ingest_resource(
            res_type=item.get("type", ""),
            res_name=item.get("name", ""),
            body=item.get("values") or {},
            rel_file="terraform.tfplan",
            tf_data=tf_data,
            resolved_vars={},
        )
    return finalize_terraform_data(tf_data, target_dir)


def _terraform_env(sandbox_dir: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """Returns a sandboxed process environment without credential variables for Terraform."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _TERRAFORM_CREDENTIAL_ENV_VARS
        and not key.startswith(_TERRAFORM_CREDENTIAL_ENV_PREFIXES)
        and not is_sensitive_key(key)
    }
    base_tmp = (
        Path(sandbox_dir).resolve()
        if sandbox_dir is not None
        else Path(tempfile.gettempdir()).resolve() / f"compliance-tf-sandbox-{os.getpid()}"
    )
    env["HOME"] = str(base_tmp)
    env["TF_CLI_CONFIG_FILE"] = str(base_tmp / ".terraformrc")
    env["CLOUDSDK_CONFIG"] = str(base_tmp / "gcloud")
    env["GOOGLE_APPLICATION_CREDENTIALS"] = ""
    env["TF_INPUT"] = "0"
    env["TF_IN_AUTOMATION"] = "1"
    env["CHECKPOINT_DISABLE"] = "1"
    return env


def _has_target_terraform_plugins(workspace_dir: Path) -> bool:
    """Returns True when a workspace contains bundled provider binaries under .terraform/."""
    tf_dir = workspace_dir / ".terraform"
    if not tf_dir.exists() or tf_dir.is_symlink():
        return False
    return any((tf_dir / sub).exists() and any((tf_dir / sub).rglob("*")) for sub in ("providers", "plugins"))


def _terraform_show_json(
    tf_bin: str,
    cwd: Path,
    plan_file: Optional[Path] = None,
    sandbox_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Runs ``terraform show -json`` on a plan file, or on the current state."""
    run_cmd = _esd_attr("safe_run_command", safe_run_command)
    cmd = [tf_bin, "show", "-json", "-no-color"]
    if plan_file is not None:
        cmd.append(str(plan_file))
    if sandbox_dir is not None:
        res = run_cmd(cmd, cwd=str(cwd), timeout=30, env=_terraform_env(sandbox_dir))
    else:
        with tempfile.TemporaryDirectory(prefix="compliance-tfenv-") as tmp_env:
            res = run_cmd(cmd, cwd=str(cwd), timeout=30, env=_terraform_env(tmp_env))
    if res.returncode != 0 or not res.stdout.strip():
        return None
    data = json.loads(res.stdout)
    return data if isinstance(data, dict) else None


def _discover_configured_terraform_json(
    target_path: Path,
    user_config: Dict[str, Any],
    allow_terraform_plan: bool,
    tf_bin: Optional[str],
    trust_target_plugins: bool,
) -> Optional[Dict[str, Any]]:
    """Checks explicit terraform_plan_path and terraform_state_path from user_config."""
    for cand_p in (user_config.get("terraform_plan_path"), user_config.get("terraform_state_path")):
        if not cand_p:
            continue
        p = Path(cand_p)
        resolved_p = p if p.is_absolute() else (target_path / p)
        if not resolved_p.is_file():
            resolved_p = target_path / "terraform" / p
        if not resolved_p.is_file():
            continue
        if resolved_p.is_symlink():
            logger.warning("Skipping symlinked Terraform plan/state file: '%s'", resolved_p)
            continue
        if str(resolved_p).endswith(".json"):
            try:
                data = read_json_file(str(resolved_p), allowed_boundary=target_path)
                if isinstance(data, dict):
                    logger.info("Ingesting user-configured Terraform JSON: '%s'", resolved_p)
                    return data
            except (OSError, ValueError, PermissionError) as err:
                logger.warning("Failed to load user-configured Terraform JSON '%s': %s", resolved_p, err)
        elif not allow_terraform_plan:
            logger.warning(
                "Configured plan '%s' is a binary Terraform plan. Rendering it runs Terraform, "
                "which requires --allow-terraform-plan; or supply 'terraform show -json' output.",
                resolved_p,
            )
        elif tf_bin:
            if _has_target_terraform_plugins(resolved_p.parent) and not trust_target_plugins:
                logger.warning(
                    "Refusing to run Terraform in '%s': target contains provider plugins under "
                    ".terraform/ (set COMPLIANCE_TRUST_TERRAFORM_PLUGINS=1 only for trusted operator workspaces).",
                    resolved_p.parent,
                )
                continue
            try:
                ensure_path_within_boundary(resolved_p, allowed_boundary=target_path)
                plan_data = _terraform_show_json(tf_bin, resolved_p.parent, resolved_p)
                if plan_data:
                    logger.info("Rendered binary plan '%s' via 'terraform show -json'", resolved_p)
                    return plan_data
            except _EXTERNAL_TOOL_ERRORS as err:
                logger.warning("Failed running 'terraform show -json' on '%s': %s", resolved_p, err)
    return None


def _discover_standard_terraform_json(target_path: Path, search_dirs: Sequence[Path]) -> Optional[Dict[str, Any]]:
    """Searches standard JSON plan/state filenames in search_dirs."""
    candidate_names = (
        "tfplan.json", "plan.json", "terraform_plan.json",
        "terraform.tfstate", "state.json", "terraform_state.json",
    )
    for s_dir in search_dirs:
        for fname in candidate_names:
            c_file = s_dir / fname
            if c_file.is_symlink():
                logger.warning("Skipping symlinked Terraform JSON candidate: '%s'", c_file)
                continue
            if not c_file.is_file():
                continue
            try:
                data = read_json_file(str(c_file), allowed_boundary=target_path)
                if isinstance(data, dict) and any(
                    k in data for k in ("planned_values", "values", "resources", "format_version")
                ):
                    logger.info("Auto-discovered Terraform JSON plan/state at '%s'", c_file)
                    return data
            except (OSError, ValueError, PermissionError) as err:
                logger.debug("Candidate file '%s' is not valid Terraform JSON: %s", c_file, err)
    return None


def _generate_terraform_json_via_cli(
    tf_bin: str,
    binary_plans: Sequence[Path],
    initialized_dirs: Sequence[Path],
    trust_target_plugins: bool,
) -> Optional[Dict[str, Any]]:
    """Renders binary plans or executes terraform plan/show in initialized workspaces."""
    run_cmd = _esd_attr("safe_run_command", safe_run_command)
    for b_file in binary_plans:
        if _has_target_terraform_plugins(b_file.parent) and not trust_target_plugins:
            logger.warning("Refusing to run Terraform on '%s': target contains provider plugins under .terraform/.", b_file)
            continue
        try:
            data = _terraform_show_json(tf_bin, b_file.parent, b_file)
            if data:
                logger.info("Rendered binary plan '%s' via 'terraform show -json'", b_file)
                return data
        except _EXTERNAL_TOOL_ERRORS as err:
            logger.warning("Failed running 'terraform show -json' on '%s': %s", b_file, err)

    for s_dir in initialized_dirs:
        if _has_target_terraform_plugins(s_dir) and not trust_target_plugins:
            logger.warning(
                "Refusing to run Terraform in '%s': target contains provider plugins under "
                ".terraform/ (set COMPLIANCE_TRUST_TERRAFORM_PLUGINS=1 only for trusted operator workspaces).",
                s_dir,
            )
            continue
        try:
            data = _terraform_show_json(tf_bin, s_dir)
            if data and (data.get("values") or data.get("resources")):
                logger.info("Rendered Terraform state JSON via 'terraform show -json' in '%s'", s_dir)
                return data
        except _EXTERNAL_TOOL_ERRORS as err:
            logger.warning("Could not render Terraform state in '%s': %s", s_dir, err)

        with tempfile.TemporaryDirectory(prefix="compliance-tfplan-") as plan_dir:
            plan_path = Path(plan_dir)
            plan_file = plan_path / "plan.tfplan"
            try:
                plan_cmd = run_cmd(
                    [tf_bin, "plan", *TERRAFORM_PLAN_FLAGS, f"-out={plan_file}"],
                    cwd=str(s_dir),
                    timeout=45,
                    retries=0,
                    env=_terraform_env(plan_path),
                )
                if plan_cmd.returncode == 0 and plan_file.is_file():
                    data = _terraform_show_json(tf_bin, s_dir, plan_file, sandbox_dir=plan_path)
                    if data:
                        logger.info("Generated Terraform plan JSON in '%s'", s_dir)
                        return data
                else:
                    stderr_lines = (plan_cmd.stderr or "").strip().splitlines()
                    logger.warning(
                        "'terraform plan' in '%s' exited with status %s: %s",
                        s_dir,
                        plan_cmd.returncode,
                        stderr_lines[0] if stderr_lines else "no error output",
                    )
            except _EXTERNAL_TOOL_ERRORS as err:
                logger.warning("Plan generation in '%s' failed: %s", s_dir, err)
    return None


def discover_or_generate_terraform_json(
    target_dir: Union[str, Path],
    user_config: Optional[Dict[str, Any]] = None,
    allow_terraform_plan: bool = False,
) -> Optional[Dict[str, Any]]:
    """Finds Terraform plan/state JSON, and runs Terraform only when allowed."""
    target_path = Path(target_dir).resolve()
    user_config = user_config or {}
    if allow_terraform_plan:
        warn_msg = (
            "WARNING: --allow-terraform-plan is enabled. Running 'terraform show/plan' "
            "evaluates target configuration and may load provider plugins; never use this "
            "flag on untrusted workspaces."
        )
        logger.warning(warn_msg)
        print(warn_msg, file=sys.stderr)
    find_bin = _esd_attr("_find_trusted_binary", _find_trusted_binary)
    tf_bin = find_bin("terraform") if allow_terraform_plan else None
    trust_target_plugins = os.environ.get("COMPLIANCE_TRUST_TERRAFORM_PLUGINS", "").strip().lower() in (
        "1", "true", "yes", "on"
    )

    configured = _discover_configured_terraform_json(
        target_path, user_config, allow_terraform_plan, tf_bin, trust_target_plugins
    )
    if configured is not None:
        return configured

    search_dirs = [target_path]
    if (target_path / "terraform").is_dir() and not (target_path / "terraform").is_symlink():
        search_dirs.append(target_path / "terraform")

    standard = _discover_standard_terraform_json(target_path, search_dirs)
    if standard is not None:
        return standard

    binary_plans = [
        s_dir / b_name
        for s_dir in search_dirs
        for b_name in ("tfplan", ".tfplan", "plan.binary")
        if (s_dir / b_name).is_file() and not (s_dir / b_name).is_symlink()
    ]
    initialized_dirs = [
        s_dir
        for s_dir in search_dirs
        if any(s_dir.glob("*.tf"))
        and ((s_dir / ".terraform").is_dir() or (s_dir / ".terraform.lock.hcl").is_file())
    ]
    if not binary_plans and not initialized_dirs:
        return None
    if not allow_terraform_plan:
        logger.info(
            "Terraform plan files or an initialized workspace were found, but Terraform is only "
            "run with --allow-terraform-plan; using static HCL parsing."
        )
        return None
    if not tf_bin:
        logger.warning("--allow-terraform-plan was given, but no terraform binary is on the trusted PATH.")
        return None
    return _generate_terraform_json_via_cli(tf_bin, binary_plans, initialized_dirs, trust_target_plugins)


def _resolve_child_module_var(
    vname: str,
    subattr: Optional[str],
    passed_keys: Set[str],
    mod_body: Union[Dict[str, Any], HclBlock, str],
    child_vars: Dict[str, Dict[str, Any]],
    resolved_vars: Dict[str, Any],
) -> Tuple[str, Any]:
    """Returns ('resolved'|'unresolved', value) for a child module variable."""
    if vname in passed_keys:
        raw_passed = extract_hcl_attr(mod_body, vname, vars_dict=resolved_vars)
        if isinstance(raw_passed, str):
            m_var = _EXACT_VAR_REF.match(raw_passed.strip())
            if m_var:
                r_vname = m_var.group(1)
                if r_vname not in resolved_vars:
                    return ("unresolved", None)
                raw_passed = resolved_vars[r_vname]
            elif any(r_v not in resolved_vars for r_v in re.findall(r"\bvar\.([a-zA-Z0-9_-]+)\b", raw_passed)):
                return ("unresolved", None)
        if subattr:
            return ("resolved", raw_passed.get(subattr) if isinstance(raw_passed, dict) else None)
        return ("resolved", raw_passed)

    if vname in child_vars:
        vmeta = child_vars[vname]
        if not vmeta.get("has_default", False):
            return ("unresolved", None)
        def_val = vmeta.get("default")
        if subattr:
            return ("resolved", def_val.get(subattr) if isinstance(def_val, dict) else None)
        return ("resolved", def_val)
    return ("unresolved", None)


def _eval_cff_collection_condition(
    expr_str: str,
    resolve_fn: Callable[[str, Optional[str]], Tuple[str, Any]],
) -> Optional[str]:
    """Evaluates known CFF nested comprehension conditions before general local expansion."""
    if "subnet_iam" in expr_str:
        _, sub_val = resolve_fn("subnets", None)
        if not isinstance(sub_val, list) or not any(
            isinstance(s, dict) and (s.get("iam") or s.get("iam_bindings") or s.get("iam_bindings_additive"))
            for s in sub_val
        ):
            return "inactive"
    if "key_iam" in expr_str:
        _, keys_val = resolve_fn("keys", None)
        if not isinstance(keys_val, dict) or not any(
            isinstance(k, dict) and (k.get("iam") or k.get("iam_bindings") or k.get("iam_bindings_additive"))
            for k in keys_val.values()
        ):
            return "inactive"
    if "attached_disks_regional" in expr_str or "disk_regional_schedule_attachments" in expr_str:
        _, disks_val = resolve_fn("attached_disks", None)
        if not isinstance(disks_val, list) or not any(isinstance(d, dict) and d.get("replica_zones") for d in disks_val):
            return "inactive"
    if "attached_disks_zonal" in expr_str or "disk_zonal_schedule_attachments" in expr_str:
        _, disks_val = resolve_fn("attached_disks", None)
        if _is_falsy_hcl_val(disks_val):
            return "inactive"
    if "boot_disk.snapshot_schedule" in expr_str:
        _, bd_val = resolve_fn("boot_disk", None)
        if isinstance(bd_val, dict):
            return "inactive" if _is_falsy_hcl_val(bd_val.get("snapshot_schedule")) else "active"
    return None


def _unwrap_hcl_expr_string(raw_expr: Any) -> str:
    """Normalizes a raw HCL count/for_each expression into an unwrapped string."""
    if isinstance(raw_expr, dict) and "_comprehension" in raw_expr:
        expr_str = "{" + str(raw_expr["_comprehension"]) + "}"
    else:
        expr_str = str(raw_expr).strip()
    if expr_str.startswith("${") and expr_str.endswith("}"):
        expr_str = expr_str[2:-1].strip()
    while expr_str.startswith("(") and expr_str.endswith(")"):
        inner = expr_str[1:-1].strip()
        pdepth = 0
        balanced = True
        for ch in inner:
            if ch == "(":
                pdepth += 1
            elif ch == ")":
                pdepth -= 1
                if pdepth < 0:
                    balanced = False
                    break
        if balanced and pdepth == 0:
            expr_str = inner
        else:
            break
    return expr_str


def _expand_child_locals(expr_str: str, child_locals: Dict[str, str]) -> str:
    """Expands local.* references up to 3 hops."""
    expanded = expr_str
    for _ in range(3):
        local_refs = set(re.findall(r"\blocal\.([a-zA-Z0-9_]+)\b", expanded))
        if not local_refs:
            break
        changed = False
        for lref in local_refs:
            if lref in child_locals:
                lval = child_locals[lref].strip()
                m_lfor = re.match(r"^[\{\[]\s*for\s+[a-zA-Z0-9_,\s]+\s+in\s+([^:]+):", lval)
                if m_lfor:
                    lval = m_lfor.group(1).strip()
                expanded = re.sub(rf"\blocal\.{re.escape(lref)}\b", f"({lval})", expanded)
                changed = True
        if not changed:
            break
    return expanded


def _find_top_level_ternary(expanded: str) -> Tuple[int, int]:
    """Finds top-level '?' and ':' indices in expanded HCL expression, or (-1, -1)."""
    q_idx, c_idx, depth, in_str = -1, -1, 0, False
    for idx, ch in enumerate(expanded):
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch in "{([":
                depth += 1
            elif ch in "})]":
                depth = max(0, depth - 1)
            elif ch == "?" and depth == 0 and q_idx == -1:
                q_idx = idx
            elif ch == ":" and depth == 0 and q_idx != -1 and c_idx == -1:
                c_idx = idx
                break
    return q_idx, c_idx


def _eval_atomic_condition_clause(
    clause: str, resolve_fn: Callable[[str, Optional[str]], Tuple[str, Any]]
) -> Optional[bool]:
    """Evaluates a single atomic boolean clause in a ternary condition."""
    c_vars = re.findall(r"\bvar\.([a-zA-Z0-9_]+)(?:\.([a-zA-Z0-9_]+))?", clause)
    if not c_vars:
        return None
    st_vals = [resolve_fn(v, sub or None) for v, sub in c_vars]
    if any(st == "unresolved" for st, _ in st_vals):
        return None
    falsy = all(_is_falsy_hcl_val(val) for _, val in st_vals)
    eq_null = bool(re.search(r"==\s*(?:null|false|0|\"\")", clause) or re.search(r"!\s*var\.", clause))
    neq_null = bool(re.search(r"!=\s*(?:null|false|0|\"\")", clause) or re.search(r"==\s*true\b", clause))
    if eq_null and not neq_null:
        return falsy
    return not falsy


def _eval_ternary_child_condition(
    expanded: str,
    q_idx: int,
    c_idx: int,
    resolve_fn: Callable[[str, Optional[str]], Tuple[str, Any]],
    mod_body: Union[Dict[str, Any], HclBlock, str],
    child_vars: Dict[str, Dict[str, Any]],
    child_locals: Dict[str, str],
    resolved_vars: Dict[str, Any],
) -> str:
    """Evaluates a top-level ternary cond ? true_part : false_part in a child resource condition."""
    cond_part = expanded[:q_idx].strip()
    true_part = expanded[q_idx + 1 : c_idx].strip()
    false_part = expanded[c_idx + 1 :].strip()
    and_clauses = [cl.strip() for cl in cond_part.split("&&") if cl.strip()]
    clause_results = [_eval_atomic_condition_clause(cl, resolve_fn) for cl in and_clauses]
    if any(r is False for r in clause_results):
        cond_truth = False
    elif any(r is None for r in clause_results):
        return "undetermined"
    else:
        cond_truth = all(r is True for r in clause_results)
    return _evaluate_child_resource_condition(
        true_part if cond_truth else false_part, None, mod_body, child_vars, child_locals, resolved_vars
    )


def _evaluate_child_resource_condition(
    count_expr: Any,
    foreach_expr: Any,
    mod_body: Union[Dict[str, Any], HclBlock, str],
    child_vars: Dict[str, Dict[str, Any]],
    child_locals: Dict[str, str],
    resolved_vars: Dict[str, Any],
) -> str:
    """Evaluates a child-module resource's count/for_each into 'active', 'inactive', or 'undetermined'."""
    if count_expr is None and foreach_expr is None:
        return "active"
    raw_expr = count_expr if count_expr is not None else foreach_expr
    if isinstance(raw_expr, list) and len(raw_expr) == 1:
        raw_expr = raw_expr[0]
    if raw_expr in (0, "0", False, "false", {}, [], (), "{}", "[]", "toset([])", "tomap({})"):
        return "inactive"
    if raw_expr in (1, "1", True, "true"):
        return "active"

    expr_str = _unwrap_hcl_expr_string(raw_expr)
    if isinstance(mod_body, dict):
        passed_keys = set(mod_body.keys())
    elif hasattr(mod_body, "parsed") and isinstance(getattr(mod_body, "parsed", None), dict):
        passed_keys = set(getattr(mod_body, "parsed").keys())
    else:
        passed_keys = set(re.findall(r"(?m)^[ \t]*([a-zA-Z0-9_-]+)[ \t]*=", str(mod_body)))
    passed_keys -= {"source", "version", "providers", "depends_on", "count", "for_each"}

    def _resolve_var(vname: str, subattr: Optional[str] = None) -> Tuple[str, Any]:
        return _resolve_child_module_var(vname, subattr, passed_keys, mod_body, child_vars, resolved_vars)

    cff_status = _eval_cff_collection_condition(expr_str, _resolve_var)
    if cff_status is not None:
        return cff_status

    m_for_raw = re.match(r"^[\{\[]\s*for\s+[a-zA-Z0-9_,\s]+\s+in\s+([^:]+):", expr_str)
    if m_for_raw:
        return _evaluate_child_resource_condition(
            m_for_raw.group(1).strip(), None, mod_body, child_vars, child_locals, resolved_vars
        )

    expanded = _expand_child_locals(expr_str, child_locals)
    q_idx, c_idx = _find_top_level_ternary(expanded)
    if q_idx != -1 and c_idx != -1:
        return _eval_ternary_child_condition(
            expanded, q_idx, c_idx, _resolve_var, mod_body, child_vars, child_locals, resolved_vars
        )

    var_matches = re.findall(r"\bvar\.([a-zA-Z0-9_]+)(?:\.([a-zA-Z0-9_]+))?", expanded)
    if not var_matches:
        return "inactive" if _is_falsy_hcl_val(expanded) else "active"

    non_vpc_create = [(v, s) for v, s in var_matches if v != "vpc_create"]
    if non_vpc_create:
        var_matches = non_vpc_create

    resolved_items = [_resolve_var(v, sub or None) for v, sub in var_matches]
    if any(st == "unresolved" for st, _ in resolved_items):
        return "undetermined"
    return "inactive" if all(_is_falsy_hcl_val(val) for _, val in resolved_items) else "active"


def _merge_user_config_into_resolved_vars(
    user_config: Optional[Dict[str, Any]], resolved_vars: Dict[str, Any]
) -> None:
    """Applies user_config scalar and dict keys into resolved_vars with highest precedence."""
    if not user_config:
        return
    for k, v in user_config.items():
        if isinstance(v, (str, int, float, bool, list)):
            resolved_vars[k] = v
        elif isinstance(v, dict):
            for sub_k, sub_v in v.items():
                resolved_vars[f"{k}.{sub_k}"] = sub_v
                if sub_k not in resolved_vars and isinstance(sub_v, (str, int, float, bool, list)):
                    resolved_vars[sub_k] = sub_v


def _collect_tf_variables_and_overrides(
    target_dir: str,
    target_boundary: Path,
    user_config: Optional[Dict[str, Any]],
    tf_data: Dict[str, Any],
) -> Tuple[List[Tuple[str, str, str]], Dict[str, Any]]:
    """Discovers .tf files and resolves variable defaults, .tfvars, and user_config overrides."""
    resolved_vars: Dict[str, Any] = {}
    tf_defaults: Dict[str, Any] = {}
    tfvars_overrides: Dict[str, Any] = {}
    root_tfvars_dirs = {str(target_boundary), str(target_boundary / "terraform")}
    discovered_tf_files: List[Tuple[str, str, str]] = []

    for root, dirs, files in os.walk(target_dir, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not is_ignored_traversal_dir(d))
        is_root_module_dir = os.path.abspath(root) in root_tfvars_dirs
        for filename in sorted(files):
            filepath = os.path.join(root, filename)
            if os.path.islink(filepath):
                try:
                    ensure_path_within_boundary(filepath, allowed_boundary=target_boundary, allow_symlinks=True)
                except (ValueError, PermissionError):
                    logger.warning("Skipping symlink file outside target boundary: %s", filepath)
                    if filename.endswith(".tf"):
                        tf_data["unparsed_terraform_files"].append({
                            "path": os.path.relpath(filepath, target_dir),
                            "error": "Symbolic link to a file outside the target folder; not read.",
                        })
                    continue

            if filename.endswith(".tf"):
                discovered_tf_files.append((root, filename, os.path.abspath(filepath)))
                try:
                    var_content = read_text_file(filepath, allowed_boundary=target_boundary)
                    for vk, vv in parse_tfvars_content(var_content).items():
                        if vk not in GENERIC_VAR_NAMES or is_root_module_dir or vk not in tf_defaults:
                            tf_defaults[vk] = vv
                except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
                    logger.debug("Failed reading variable definitions in %s: %s", filepath, err)
            elif filename.endswith(".tfvars") and is_root_module_dir and (
                filename == "terraform.tfvars" or filename.endswith(".auto.tfvars")
            ):
                try:
                    tfvars_overrides.update(parse_tfvars_content(read_text_file(filepath, allowed_boundary=target_boundary)))
                except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
                    logger.debug("Failed reading tfvars in %s: %s", filepath, err)
            elif filename.endswith(".tfvars.json") and is_root_module_dir and (
                filename == "terraform.tfvars.json" or filename.endswith(".auto.tfvars.json")
            ):
                try:
                    jdata = read_json_file(filepath, allowed_boundary=target_boundary)
                    if isinstance(jdata, dict):
                        for jk, jv in jdata.items():
                            tfvars_overrides[jk] = "[REDACTED_SENSITIVE]" if is_sensitive_key(jk) else jv
                except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, PermissionError) as err:
                    logger.debug("Failed reading tfvars.json in %s: %s", filepath, err)

    resolved_vars.update(tf_defaults)
    resolved_vars.update(tfvars_overrides)
    _merge_user_config_into_resolved_vars(user_config, resolved_vars)
    return discovered_tf_files, resolved_vars


def _extract_balanced_resource_or_module_blocks(
    content: str, header_re: str, two_labels: bool
) -> List[Any]:
    """Extracts balanced-brace resource or module blocks from raw HCL content."""
    out: List[Any] = []
    for match in re.finditer(header_re, content):
        block_start = match.end()
        depth, pos = 1, block_start
        while pos < len(content) and depth > 0:
            if content[pos] == "{":
                depth += 1
            elif content[pos] == "}":
                depth -= 1
            pos += 1
        if depth == 0:
            body_text = content[block_start : pos - 1]
            if two_labels:
                out.append((match.group(1), match.group(2), HclBlock(body_text, parsed=None)))
            else:
                out.append((match.group(1), HclBlock(body_text, parsed=None)))
    return out


def _ingest_data_kms_crypto_keys(
    parsed_hcl: Optional[Dict[str, Any]],
    content: str,
    rel_file: str,
    resolved_vars: Dict[str, Any],
    tf_data: Dict[str, Any],
) -> None:
    """Ingests data.google_kms_crypto_key references from parsed AST or raw HCL text."""
    if parsed_hcl and isinstance(parsed_hcl, dict) and "data" in parsed_hcl:
        for d_entry in parsed_hcl.get("data", []):
            if not isinstance(d_entry, dict):
                continue
            d_named = d_entry.get("google_kms_crypto_key")
            if not isinstance(d_named, dict):
                continue
            for dn, d_body in d_named.items():
                if not isinstance(d_body, dict):
                    continue
                resolved_d = _resolve_ast_variables(d_body, resolved_vars)
                k_name = _resolved_asset_name(
                    extract_hcl_attr(resolved_d, "name", default=dn, vars_dict=resolved_vars), dn, resolved_vars, dn
                )
                kr = _resolved_asset_name(
                    extract_hcl_attr(resolved_d, "key_ring", default="kms-keyring", vars_dict=resolved_vars),
                    "kms-keyring",
                    resolved_vars,
                    "kms-keyring",
                )
                tf_data["kms_keys"].append({
                    "type": "data.google_kms_crypto_key",
                    "name": k_name,
                    "key_ring": kr,
                    "protection_level": "Not determined from IaC (existing key data source)",
                    "rotation_period": None,
                    "file": rel_file,
                })
    elif parsed_hcl is None:
        for d_match in re.finditer(r'data\s+"google_kms_crypto_key"\s+"([^"]+)"\s*\{', content):
            tf_data["kms_keys"].append({
                "type": "data.google_kms_crypto_key",
                "name": d_match.group(1),
                "key_ring": "kms-keyring",
                "protection_level": "Not determined from IaC (existing key data source)",
                "rotation_period": None,
                "file": rel_file,
            })


def _ingest_cff_firewall_module(
    body: HclBlock, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> None:
    """Ingests net-vpc-firewall module rules."""
    raw_mod_net = extract_hcl_attr(body, "network", vars_dict=resolved_vars)
    mod_net = _resolved_asset_name(raw_mod_net, "", resolved_vars, "custom-vpc") if raw_mod_net else "custom-vpc"
    parsed_rule_maps = False
    for direction, input_key in (("INGRESS", "ingress_rules"), ("EGRESS", "egress_rules")):
        rules_input = extract_hcl_attr(body, input_key, vars_dict=resolved_vars)
        if not isinstance(rules_input, dict):
            continue
        parsed_rule_maps = True
        for r_name, r_cfg in rules_input.items():
            if not isinstance(r_cfg, dict):
                continue
            rule_specs = r_cfg.get("rules")
            if not isinstance(rule_specs, list) or not rule_specs:
                rule_specs = [{"protocol": "all"}]
            protos: List[str] = []
            ports: List[str] = []
            for spec in rule_specs:
                if not isinstance(spec, dict):
                    continue
                protos.append(str(spec.get("protocol") or "all"))
                spec_ports = spec.get("ports")
                if spec_ports in (None, "", [], ()):
                    ports.append("all")
                elif isinstance(spec_ports, (list, tuple)):
                    ports.extend(str(p) for p in spec_ports)
                else:
                    ports.append(str(spec_ports))
            src_ranges = r_cfg.get("source_ranges")
            dst_ranges = r_cfg.get("destination_ranges")
            if direction == "INGRESS" and src_ranges is None and r_cfg.get("sources") is None:
                src_ranges = ["0.0.0.0/0"]
            if direction == "EGRESS" and dst_ranges is None:
                dst_ranges = ["0.0.0.0/0"]
            tf_data["firewall_rules"].append({
                "name": r_name,
                "network": mod_net,
                "direction": direction,
                "protocol": "/".join(sorted(set(protos))) or "all",
                "ports": ",".join(ports) or "all",
                "action": "DENY" if r_cfg.get("deny", direction == "EGRESS") else "ALLOW",
                "source_ranges": _literal_cidrs(src_ranges),
                "destination_ranges": _literal_cidrs(dst_ranges),
            })
    if not parsed_rule_maps:
        for r_match in re.finditer(r'(?<![a-zA-Z0-9_-])([a-zA-Z0-9_-]+)\s*=\s*\{[^}]*deny\s*=\s*(true|false)', str(body)):
            tf_data["firewall_rules"].append({
                "name": r_match.group(1),
                "network": mod_net,
                "direction": "Not determined from IaC",
                "protocol": "Not determined from IaC",
                "ports": "Not determined from IaC",
                "action": "DENY" if r_match.group(2) == "true" else "ALLOW",
                "source_ranges": [],
                "destination_ranges": [],
            })


def _ingest_cff_vpc_or_vpn_module(
    mod_name: str, src_dir: str, mod_name_low: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> bool:
    """Ingests net-vpc and net-vpn-ha CFF modules; returns True if matched."""
    if src_dir == "net-vpc" or (
        not src_dir and "vpc" in mod_name_low and not any(x in mod_name_low for x in ("firewall", "peering", "vpc-sc", "vpc_sc"))
    ):
        raw_v = extract_hcl_attr(body, "name", vars_dict=resolved_vars) or mod_name
        v_name = _resolved_asset_name(raw_v, str(mod_name), resolved_vars, str(mod_name))
        if is_valid_resource_name(v_name):
            tf_data["networks"].add(v_name)
        elif str(mod_name).lower() == "vpc" or v_name.lower() == "vpc":
            tf_data["networks"].add("vpc")
        subnets_input = extract_hcl_attr(body, "subnets", vars_dict=resolved_vars)
        if isinstance(subnets_input, list):
            for s in subnets_input:
                if isinstance(s, dict):
                    c = s.get("ip_cidr_range")
                    if is_valid_cidr(c) and str(c) not in tf_data["subnets"]:
                        tf_data["subnets"].add(str(c))
                    if isinstance(s.get("secondary_ip_range"), dict):
                        for sec_c in s["secondary_ip_range"].values():
                            if is_valid_cidr(sec_c) and str(sec_c) not in tf_data["subnets"]:
                                tf_data["subnets"].add(str(sec_c))
        for c_m in re.finditer(r'ip_cidr_range\s*=\s*"([^"]+)"', str(body)):
            if is_valid_cidr(c_m.group(1)):
                tf_data["subnets"].add(c_m.group(1))
        return True

    if "net-vpn" in src_dir or (not src_dir and "vpn" in mod_name_low):
        gw_name = _asset_identifier(body, ("name",), str(mod_name), resolved_vars, "boundary-connection")
        peer_asn = (
            extract_hcl_attr(body, "router_asn", vars_dict=resolved_vars)
            or extract_hcl_attr(body, "peer_external_gateway.asn", vars_dict=resolved_vars)
        )
        peer_ips = _literal_cidrs(re.findall(r'ip_address\s*=\s*"([^"]+)"', str(body)))
        tf_data["boundary_connections"].append({
            "name": gw_name,
            "type": "module_net_vpn_ha",
            "peer_ip": ", ".join(peer_ips) if peer_ips else "Not determined from IaC",
            "peer_asn": peer_asn,
            "file": rel_file,
        })
        return True
    return False


def _extract_kms_keys_from_text(body_str: str, kr_name: str, rel_file: str, tf_data: Dict[str, Any]) -> None:
    """Fallback text scanner for keys = { ... } inside a CFF kms module block."""
    keys_block_m = re.search(r"keys\s*=\s*\{", body_str)
    if not keys_block_m:
        return
    brace_start = keys_block_m.end() - 1
    brace_depth = 0
    keys_content = ""
    for idx in range(brace_start, len(body_str)):
        if body_str[idx] == "{":
            brace_depth += 1
        elif body_str[idx] == "}":
            brace_depth -= 1
            if brace_depth == 0:
                keys_content = body_str[brace_start + 1 : idx]
                break
    sub_idx = 0
    while sub_idx < len(keys_content):
        key_header_m = re.search(r'(?:\"([^\"]+)\"|(?<![a-zA-Z0-9_-])([a-zA-Z0-9_-]+))\s*=\s*\{', keys_content[sub_idx:])
        if not key_header_m:
            break
        k_name = key_header_m.group(1) or key_header_m.group(2)
        k_start = sub_idx + key_header_m.end() - 1
        k_depth = 0
        k_block = ""
        for k_i in range(k_start, len(keys_content)):
            if keys_content[k_i] == "{":
                k_depth += 1
            elif keys_content[k_i] == "}":
                k_depth -= 1
                if k_depth == 0:
                    k_block = keys_content[k_start : k_i + 1]
                    sub_idx = k_i + 1
                    break
        else:
            sub_idx = len(keys_content)
        if k_name and is_valid_resource_name(k_name) and k_name not in ("keys", "keyring", "iam", "labels"):
            prot = "HSM" if re.search(r'protection_level\s*=\s*"?HSM', str(k_block), re.IGNORECASE) else "SOFTWARE"
            rot_m = re.search(r'rotation_period\s*=\s*"([^"]+)"', k_block)
            tf_data["kms_keys"].append({
                "type": "module_kms_crypto_key",
                "name": k_name,
                "key_ring": kr_name,
                "protection_level": prot,
                "rotation_period": rot_m.group(1) if rot_m else None,
                "file": rel_file,
            })


def _ingest_cff_gke_module(
    mod_name: str, src_dir: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> None:
    """Ingests gke-cluster CFF module."""
    c_name = _asset_identifier(body, ("name",), str(mod_name), resolved_vars, "gke-cluster")
    loc = (
        _resolve_optional_attr(extract_hcl_attr(body, "location", vars_dict=resolved_vars), resolved_vars, default_val=None)
        or _resolve_optional_attr(resolved_vars.get("region"), resolved_vars, default_val=None)
    )
    m_cidr = _resolve_optional_attr(
        extract_hcl_attr(body, "private_cluster_config.master_ipv4_cidr_block", vars_dict=resolved_vars)
        or extract_hcl_attr(body, "vpc_config.master_ipv4_cidr_block", vars_dict=resolved_vars),
        resolved_vars,
        default_val=None,
    )
    is_fabric_gke = "gke-cluster" in src_dir
    mod_priv_nodes = _text_attr_tristate(body, "private_nodes")
    mod_priv_endpoint = _text_attr_tristate(body, "disable_public_endpoint")
    if mod_priv_endpoint is None:
        mod_priv_endpoint = _text_attr_tristate(body, "enable_private_endpoint")
    mod_wif = _text_attr_tristate(body, "workload_identity")
    if is_fabric_gke:
        mod_priv_nodes = True if mod_priv_nodes is None else mod_priv_nodes
        mod_wif = True if mod_wif is None else mod_wif
    tf_data["gke_clusters"].append({
        "name": c_name,
        "master_version": None,
        "master_ipv4_cidr_block": m_cidr,
        "location": loc,
        "private_cluster": mod_priv_nodes,
        "private_endpoint": mod_priv_endpoint,
        "workload_identity": mod_wif,
        "file": rel_file,
    })


def _ingest_cff_kms_module(
    mod_name: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> None:
    """Ingests kms CFF module keys and IAM bindings."""
    raw_kr = extract_hcl_attr(body, "keyring", vars_dict=resolved_vars)
    if isinstance(raw_kr, dict) and raw_kr.get("name"):
        kr_name = _resolved_asset_name(raw_kr.get("name"), f"{mod_name}-kr", resolved_vars, f"{mod_name}-kr")
    else:
        kr_m = re.search(r'name\s*=\s*"([^"]+)"', str(body))
        kr_name = kr_m.group(1) if kr_m else f"{mod_name}-kr"
    keys_attr = extract_hcl_attr(body, "keys", vars_dict=resolved_vars)
    ingested_mod_keys = False
    if isinstance(keys_attr, dict):
        for k_name, k_cfg in keys_attr.items():
            if not is_valid_resource_name(str(k_name)) or str(k_name) in ("keys", "keyring", "iam", "labels"):
                continue
            prot, rot = "SOFTWARE", None
            if isinstance(k_cfg, dict):
                rot = k_cfg.get("rotation_period")
                vt = k_cfg.get("version_template")
                vt0 = vt[0] if isinstance(vt, list) and vt else vt
                raw_prot = (vt0.get("protection_level") if isinstance(vt0, dict) else None) or k_cfg.get("protection_level")
                if raw_prot and "HSM" in str(raw_prot).upper():
                    prot = "HSM"
            tf_data["kms_keys"].append({
                "type": "module_kms_crypto_key",
                "name": str(k_name),
                "key_ring": kr_name,
                "protection_level": prot,
                "rotation_period": rot,
                "file": rel_file,
            })
            ingested_mod_keys = True
    body_str = str(body)
    if not ingested_mod_keys:
        _extract_kms_keys_from_text(body_str, kr_name, rel_file, tf_data)
    iam_attr = extract_hcl_attr(body, "iam", vars_dict=resolved_vars)
    if isinstance(iam_attr, dict):
        for role_k, mem_list in iam_attr.items():
            if not isinstance(mem_list, list):
                continue
            for raw_m in mem_list:
                resolved_mem = resolve_iam_principal(
                    mem=str(raw_m),
                    body=body_str,
                    rel_file=rel_file,
                    res_type="google_kms_key_ring_iam_binding",
                    res_name=str(mod_name),
                    role_val=str(role_k),
                    resolved_vars=resolved_vars,
                    service_accounts=tf_data.get("service_accounts", []),
                )
                if resolved_mem and "${" not in resolved_mem:
                    tf_data["iam_bindings"].append({
                        "principal": resolved_mem,
                        "role": str(role_k),
                        "scope": "kms_key_ring",
                        "file": rel_file,
                    })


def _ingest_cff_gke_or_kms_module(
    mod_name: str, src_dir: str, mod_name_low: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> bool:
    """Ingests gke-cluster and kms CFF modules; returns True if matched."""
    if "gke-cluster" in src_dir or (not src_dir and "gke" in mod_name_low and "nodepool" not in mod_name_low):
        _ingest_cff_gke_module(mod_name, src_dir, body, rel_file, resolved_vars, tf_data)
        return True
    if src_dir == "kms" or (not src_dir and "kms" in mod_name_low):
        _ingest_cff_kms_module(mod_name, body, rel_file, resolved_vars, tf_data)
        return True
    return False


def _ingest_cff_cloudsql_or_bq_module(
    mod_name: str, src_dir: str, mod_name_low: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> bool:
    """Ingests cloudsql and bigquery CFF modules; returns True if matched."""
    if "cloudsql" in src_dir or (not src_dir and "sql" in mod_name_low):
        db_name = _resolved_asset_name(
            extract_hcl_attr(body, "name", vars_dict=resolved_vars), str(mod_name), resolved_vars, "database-instance"
        )
        db_ver = _resolve_optional_attr(
            extract_hcl_attr(body, "database_version", vars_dict=resolved_vars), resolved_vars, default_val=NOT_DETERMINED
        )
        tier = _resolve_optional_attr(
            extract_hcl_attr(body, "tier", vars_dict=resolved_vars), resolved_vars, default_val=NOT_DETERMINED
        )
        reg = (
            _resolve_optional_attr(
                extract_hcl_attr(body, "region", vars_dict=resolved_vars) or extract_hcl_attr(body, "location", vars_dict=resolved_vars),
                resolved_vars,
                default_val=None,
            )
            or _resolve_optional_attr(resolved_vars.get("region"), resolved_vars, default_val=None)
        )
        p_net = extract_hcl_attr(body, "private_network", vars_dict=resolved_vars) or extract_hcl_attr(
            body, "network_config.network", vars_dict=resolved_vars
        )
        if p_net:
            if "psa_private_network" in str(p_net):
                p_net = "Private VPC / Private Service Connect (PSC)"
            else:
                p_clean = clean_interpolated_string(str(p_net), resolved_vars)
                p_net = None if ("var." in p_clean or "local." in p_clean or "${" in p_clean or not is_valid_resource_name(p_clean)) else p_clean
        cmek = extract_hcl_attr(body, "encryption_key_name", vars_dict=resolved_vars) or extract_hcl_attr(
            body, "cmek_key", vars_dict=resolved_vars
        )
        mod_ssl_m = re.search(r'mode\s*=\s*"([A-Z_]+)"', str(body))
        mod_req_ssl = mod_ssl_m.group(1).upper() in ("ENCRYPTED_ONLY", "TRUSTED_CLIENT_CERTIFICATE_REQUIRED") if mod_ssl_m else None
        mod_bkp = _text_attr_tristate(body, "enabled") if "backup_configuration" in str(body) else False
        tf_data["databases"].append({
            "type": "module_cloudsql_database_instance",
            "name": db_name,
            "database_version": db_ver,
            "tier": tier,
            "region": reg,
            "private_network": p_net,
            "cmek_key": _resolved_cmek_name(cmek, resolved_vars) if cmek else None,
            "require_ssl": mod_req_ssl,
            "backup_enabled": mod_bkp,
            "has_public_ip": False,
            "file": rel_file,
        })
        return True

    if "bigquery" in src_dir or (not src_dir and ("bigquery" in mod_name_low or "bq" in mod_name_low)):
        ds_id = _resolved_asset_name(
            extract_hcl_attr(body, "id", vars_dict=resolved_vars) or extract_hcl_attr(body, "dataset_id", vars_dict=resolved_vars),
            str(mod_name),
            resolved_vars,
            str(mod_name),
        )
        loc = (
            _resolve_optional_attr(extract_hcl_attr(body, "location", vars_dict=resolved_vars), resolved_vars, default_val=None)
            or _resolve_optional_attr(resolved_vars.get("region"), resolved_vars, default_val=None)
        )
        raw_cmek = extract_hcl_attr(body, "encryption_key", vars_dict=resolved_vars) or extract_hcl_attr(
            body, "kms_key", vars_dict=resolved_vars
        )
        tf_data["databases"].append({
            "type": "google_bigquery_dataset",
            "name": ds_id,
            "location": loc,
            "cmek_key": _resolved_cmek_name(raw_cmek, resolved_vars) if raw_cmek else None,
            "file": rel_file,
        })
        return True
    return False


def _ingest_cff_compute_vm_module(
    mod_name: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> None:
    """Ingests compute-vm CFF module."""
    raw_vm = extract_hcl_attr(body, "name", vars_dict=resolved_vars) or mod_name
    vm_name = _resolved_asset_name(raw_vm, str(mod_name), resolved_vars, "compute-instance")
    if vm_name in ("vm", "instance", "name", ""):
        vm_name = f"{mod_name}-instance" if mod_name not in ("vm", "instance") else "compute-instance"
    raw_mtype = extract_hcl_attr(body, "instance_type", vars_dict=resolved_vars) or extract_hcl_attr(
        body, "machine_type", vars_dict=resolved_vars
    )
    m_type = _resolve_optional_attr(raw_mtype, resolved_vars, default_val=NOT_DETERMINED)
    raw_zone = extract_hcl_attr(body, "zone", vars_dict=resolved_vars) or resolved_vars.get("zone")
    if raw_zone:
        zone = _resolve_optional_attr(raw_zone, resolved_vars, default_val="Not determined from IaC") or "Not determined from IaC"
    else:
        reg_clean = _resolve_optional_attr(
            resolved_vars.get("region") or resolved_vars.get("default_region"), resolved_vars, default_val=""
        ) or ""
        zone = f"{reg_clean}-a" if reg_clean else "Not determined from IaC"
    net_ip = extract_hcl_attr(body, "network_ip", vars_dict=resolved_vars)
    if net_ip in ("try", "lookup", "None", "") or not net_ip or str(net_ip).startswith("${"):
        net_ip = None
    raw_subnet = extract_hcl_attr(body, "subnetwork", vars_dict=resolved_vars)
    subnet = _resolved_asset_name(raw_subnet, "", resolved_vars, "") if raw_subnet else ""
    raw_img = extract_hcl_attr(body, "image", vars_dict=resolved_vars) or extract_hcl_attr(
        body, "boot_disk.initialize_params.image", vars_dict=resolved_vars
    )
    img = _resolved_asset_name(raw_img, "", resolved_vars, "Not determined from IaC") if raw_img else "Not determined from IaC"
    raw_kms = (
        extract_hcl_attr(body, "kms_key_self_link", vars_dict=resolved_vars)
        or extract_hcl_attr(body, "kms_key", vars_dict=resolved_vars)
        or extract_hcl_attr(body, "encryption.kms_key_self_link", vars_dict=resolved_vars)
    )
    shielded_tri = _text_attr_tristate(body, "enable_secure_boot")
    if shielded_tri is None and "shielded_config" in str(body):
        shielded_tri = True
    nat_tri = _text_attr_tristate(body, "nat")
    has_pub_ip = True if (nat_tri is True or "access_config" in str(body)) else False
    raw_pid = (
        extract_hcl_attr(body, "project_id", vars_dict=resolved_vars)
        or resolved_vars.get("project_id")
        or resolved_vars.get("prod_project_id")
        or resolved_vars.get("service_project_id")
    )
    p_id = _resolve_optional_attr(raw_pid, resolved_vars, default_val="") or ""
    self_link = f"projects/{p_id}/zones/{zone}/instances/{vm_name}" if p_id and zone != "Not determined from IaC" else None
    tf_data["compute_instances"].append({
        "name": vm_name,
        "machine_type": m_type,
        "zone": zone,
        "network_ip": net_ip,
        "subnetwork": subnet,
        "image": img,
        "kms_key": _resolved_cmek_name(raw_kms, resolved_vars) if raw_kms else None,
        "has_public_ip": has_pub_ip,
        "shielded_vm": shielded_tri,
        "self_link": self_link,
        "file": rel_file,
    })


def _ingest_cff_db_or_vm_module(
    mod_name: str, src_dir: str, mod_name_low: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> bool:
    """Ingests cloudsql, bigquery, and compute-vm CFF modules; returns True if matched."""
    if _ingest_cff_cloudsql_or_bq_module(mod_name, src_dir, mod_name_low, body, rel_file, resolved_vars, tf_data):
        return True
    if "compute-vm" in src_dir or (not src_dir and "vm" in mod_name_low):
        _ingest_cff_compute_vm_module(mod_name, body, rel_file, resolved_vars, tf_data)
        return True
    return False


def _ingest_cff_gcs_or_cloud_run_module(
    mod_name: str, src_dir: str, mod_name_low: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> bool:
    """Ingests gcs and cloud-run CFF modules; returns True if matched."""
    if src_dir == "gcs" or (not src_dir and "bucket" in mod_name_low):
        b_name = _resolved_asset_name(
            extract_hcl_attr(body, "name", vars_dict=resolved_vars), str(mod_name), resolved_vars, str(mod_name)
        )
        if is_valid_resource_name(b_name) and not b_name.startswith("${"):
            b_loc = (
                _resolve_optional_attr(extract_hcl_attr(body, "location", vars_dict=resolved_vars), resolved_vars, default_val=None)
                or _resolve_optional_attr(resolved_vars.get("region"), resolved_vars, default_val=None)
            )
            raw_cmek = (
                extract_hcl_attr(body, "encryption_key", vars_dict=resolved_vars)
                or extract_hcl_attr(body, "encryption.default_kms_key_name", vars_dict=resolved_vars)
                or extract_hcl_attr(body, "kms_key", vars_dict=resolved_vars)
            )
            cmek = _resolved_cmek_name(raw_cmek, resolved_vars) if raw_cmek else None
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
        return True

    if "cloud-run" in src_dir or (not src_dir and "cloud_run" in mod_name_low):
        cr_name = _resolved_asset_name(
            extract_hcl_attr(body, "name", vars_dict=resolved_vars), str(mod_name), resolved_vars, str(mod_name)
        )
        cr_loc = (
            _resolve_optional_attr(
                extract_hcl_attr(body, "region", vars_dict=resolved_vars) or extract_hcl_attr(body, "location", vars_dict=resolved_vars),
                resolved_vars,
                default_val=None,
            )
            or _resolve_optional_attr(resolved_vars.get("region"), resolved_vars, default_val=None)
        )
        cr_ingress = _resolve_optional_attr(
            extract_hcl_attr(body, "ingress", vars_dict=resolved_vars), resolved_vars, default_val=NOT_DETERMINED
        )
        raw_cmek = extract_hcl_attr(body, "encryption_key", vars_dict=resolved_vars)
        tf_data["cloud_run_services"].append({
            "type": "google_cloud_run_v2_service",
            "name": cr_name,
            "location": cr_loc,
            "ingress": cr_ingress,
            "cmek_key": _resolved_cmek_name(raw_cmek, resolved_vars) if raw_cmek else None,
            "file": rel_file,
        })
        return True
    return False


def _ingest_cff_project_or_sa_module(
    mod_name: str, src_dir: str, mod_name_low: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> bool:
    """Ingests project-factory and iam-service-account CFF modules; returns True if matched."""
    if "project" in src_dir or (not src_dir and "project" in mod_name_low):
        svcs = extract_hcl_attr(body, "services", vars_dict=resolved_vars)
        if isinstance(svcs, list):
            for s in svcs:
                if str(s).strip().endswith(".googleapis.com"):
                    tf_data["services"].add(str(s).strip())
        return True
    if "iam-service-account" in src_dir or (not src_dir and ("service-account" in mod_name_low or mod_name_low == "sa")):
        sa_name = _resolved_asset_name(
            extract_hcl_attr(body, "name", vars_dict=resolved_vars), str(mod_name), resolved_vars, str(mod_name)
        )
        prefix = extract_hcl_attr(body, "prefix", vars_dict=resolved_vars) or ""
        full_sa_name = f"{prefix}-{sa_name}" if prefix and not sa_name.startswith(f"{prefix}-") else sa_name
        pid = (
            extract_hcl_attr(body, "project_id", vars_dict=resolved_vars)
            or resolved_vars.get("project_id")
            or resolved_vars.get("main_project_id")
            or ""
        )
        tf_data["service_accounts"].append({
            "name": full_sa_name,
            "email": f"{full_sa_name}@{pid}.iam.gserviceaccount.com" if pid else f"{full_sa_name}@iam.gserviceaccount.com",
            "description": extract_hcl_attr(body, "description", vars_dict=resolved_vars) or "Managed Service Account",
            "file": rel_file,
        })
        return True
    return False


def _ingest_cff_storage_serverless_iam_module(
    mod_name: str, src_dir: str, mod_name_low: str, body: HclBlock, rel_file: str, resolved_vars: Dict[str, Any], tf_data: Dict[str, Any]
) -> None:
    """Ingests gcs, cloud-run, project, iam-service-account, secret-manager, pubsub, and logging-bucket modules."""
    if _ingest_cff_gcs_or_cloud_run_module(mod_name, src_dir, mod_name_low, body, rel_file, resolved_vars, tf_data):
        return
    if _ingest_cff_project_or_sa_module(mod_name, src_dir, mod_name_low, body, rel_file, resolved_vars, tf_data):
        return
    if "secret-manager" in src_dir or (not src_dir and "secret" in mod_name_low):
        tf_data.setdefault("secrets", [])
        sec_input = extract_hcl_attr(body, "secrets", vars_dict=resolved_vars)
        if isinstance(sec_input, dict):
            for sec_k in sec_input:
                if is_valid_resource_name(str(sec_k)):
                    tf_data["secrets"].append(str(sec_k))
        elif is_valid_resource_name(str(mod_name)):
            tf_data["secrets"].append(str(mod_name))
    elif "pubsub" in src_dir or (not src_dir and "pubsub" in mod_name_low):
        tf_data.setdefault("pubsub_topics", [])
        t_name = _resolved_asset_name(
            extract_hcl_attr(body, "name", vars_dict=resolved_vars), str(mod_name), resolved_vars, str(mod_name)
        )
        if is_valid_resource_name(t_name):
            tf_data["pubsub_topics"].append(t_name)
    elif "logging-bucket" in src_dir or (not src_dir and "logging" in mod_name_low and "bucket" in mod_name_low):
        b_id = _resolved_asset_name(
            extract_hcl_attr(body, "id", vars_dict=resolved_vars), str(mod_name), resolved_vars, str(mod_name)
        )
        dest_parent = extract_hcl_attr(body, "parent", vars_dict=resolved_vars) or ""
        sink_dest = (
            f"logging.googleapis.com/projects/{dest_parent}/locations/global/buckets/{b_id}"
            if dest_parent
            else f"logging_bucket/{b_id}"
        )
        tf_data["logging_sinks"].append({"name": b_id, "destination": sink_dest, "file": rel_file})


def _ingest_cff_module_block(
    mod_name: str,
    src: str,
    src_dir: str,
    mod_name_low: str,
    body: HclBlock,
    rel_file: str,
    resolved_vars: Dict[str, Any],
    tf_data: Dict[str, Any],
) -> None:
    """Dispatches recognized Cloud Foundation Fabric module blocks to specialized handlers."""
    if "net-vpc-firewall" in src or src_dir == "net-vpc-firewall" or "firewall" in mod_name_low:
        _ingest_cff_firewall_module(body, resolved_vars, tf_data)
    elif _ingest_cff_vpc_or_vpn_module(mod_name, src_dir, mod_name_low, body, rel_file, resolved_vars, tf_data):
        return
    elif _ingest_cff_gke_or_kms_module(mod_name, src_dir, mod_name_low, body, rel_file, resolved_vars, tf_data):
        return
    elif _ingest_cff_db_or_vm_module(mod_name, src_dir, mod_name_low, body, rel_file, resolved_vars, tf_data):
        return
    else:
        _ingest_cff_storage_serverless_iam_module(mod_name, src_dir, mod_name_low, body, rel_file, resolved_vars, tf_data)


def _collect_child_module_metadata(
    child_mod_dir: Path,
    rel_file: str,
    target_boundary: Path,
    module_boundary: Path,
    external_module_files: Set[str],
    tf_data: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, str], List[Tuple[Path, str, Optional[Dict[str, Any]], Optional[str]]]]:
    """Reads and parses child module .tf files to collect variable defaults, locals, and file records."""
    hcl2_mod = _esd_attr("hcl2", hcl2)
    child_vars: Dict[str, Dict[str, Any]] = {}
    child_locals: Dict[str, str] = {}
    child_file_records: List[Tuple[Path, str, Optional[Dict[str, Any]], Optional[str]]] = []

    for c_file in sorted(child_mod_dir.glob("*.tf")):
        if c_file.is_symlink():
            continue
        try:
            c_rel_label = str(c_file.resolve().relative_to(module_boundary))
        except ValueError:
            c_rel_label = f"{rel_file} -> {c_file.name}"
        try:
            c_content = read_text_file(c_file, allowed_boundary=child_mod_dir)
        except (OSError, ValueError, PermissionError) as read_err:
            logger.warning("Failed reading child module Terraform file %s: %s", c_file, read_err)
            tf_data["unparsed_terraform_files"].append({"path": c_rel_label, "error": str(read_err)[:300]})
            continue
        try:
            c_file.resolve().relative_to(target_boundary)
        except ValueError:
            external_module_files.add(c_rel_label)

        c_parsed, c_parse_err = None, None
        if hcl2_mod:
            try:
                c_parsed = hcl2_mod.loads(c_content)
            except (LarkError, KeyError, ValueError, TypeError) as p_err:
                c_parse_err = " ".join(str(p_err).split())[:300]

        if isinstance(c_parsed, dict):
            for v_entry in c_parsed.get("variable", []):
                if isinstance(v_entry, dict):
                    for vn, vb in v_entry.items():
                        vb_dict = vb[0] if isinstance(vb, list) and len(vb) == 1 else vb
                        has_def = isinstance(vb_dict, dict) and "default" in vb_dict
                        def_val = vb_dict.get("default") if isinstance(vb_dict, dict) else None
                        if isinstance(def_val, list) and len(def_val) == 1:
                            def_val = def_val[0]
                        child_vars[vn] = {"has_default": has_def, "default": def_val}
            for lbody in _extract_balanced_hcl_blocks(c_content, "locals", 0):
                child_locals.update(_extract_hcl_local_assignments(lbody))
        else:
            for vn, vbody in _extract_balanced_hcl_blocks(c_content, "variable", 1):
                def_str = _extract_top_level_meta_arg(vbody, "default")
                if def_str is not None:
                    parsed_def: Any = def_str.strip('"')
                    if def_str in ("null", "None"):
                        parsed_def = None
                    elif def_str.lower() in ("true", "false"):
                        parsed_def = def_str.lower() == "true"
                    elif def_str in ("{}", "[]"):
                        parsed_def = {} if def_str == "{}" else []
                    child_vars[vn] = {"has_default": True, "default": parsed_def}
                else:
                    child_vars[vn] = {"has_default": False, "default": None}
            for lbody in _extract_balanced_hcl_blocks(c_content, "locals", 0):
                child_locals.update(_extract_hcl_local_assignments(lbody))

        child_file_records.append((c_file, c_content, c_parsed, c_parse_err))
    return child_vars, child_locals, child_file_records


def _extract_child_file_resource_tuples(
    c_parsed: Optional[Dict[str, Any]],
    bal_resources: List[Any],
    bal_map: Dict[Tuple[str, str], str],
) -> List[Tuple[str, str, Any, Any]]:
    """Extracts (res_type, res_name, count_expr, foreach_expr) tuples from a child module file."""
    c_resources: List[Tuple[str, str, Any, Any]] = []
    if c_parsed and isinstance(c_parsed, dict) and "resource" in c_parsed:
        for cr_entry in c_parsed.get("resource", []):
            if isinstance(cr_entry, dict):
                for crt, cnamed_map in cr_entry.items():
                    if isinstance(cnamed_map, dict):
                        for crn, cr_body in cnamed_map.items():
                            raw_b = bal_map.get((crt, crn), "")
                            c_exp = (
                                _extract_top_level_meta_arg(raw_b, "count")
                                if raw_b
                                else (cr_body.get("count") if isinstance(cr_body, dict) else None)
                            )
                            fe_exp = (
                                _extract_top_level_meta_arg(raw_b, "for_each")
                                if raw_b
                                else (cr_body.get("for_each") if isinstance(cr_body, dict) else None)
                            )
                            c_resources.append((crt, crn, c_exp, fe_exp))
    elif c_parsed is None:
        for crt, rn, raw_b in bal_resources:
            c_resources.append((crt, rn, _extract_top_level_meta_arg(raw_b, "count"), _extract_top_level_meta_arg(raw_b, "for_each")))
    return c_resources


def _resolve_and_ingest_child_module_hcl(
    mod_name: str,
    body: HclBlock,
    child_mod_dir: Path,
    rel_file: str,
    target_boundary: Path,
    module_boundary: Path,
    external_module_files: Set[str],
    resolved_vars: Dict[str, Any],
    tf_data: Dict[str, Any],
) -> Set[str]:
    """Resolves and ingests child module resources while evaluating count/for_each conditions."""
    child_ingested_types: Set[str] = set()
    try:
        child_vars, child_locals, child_file_records = _collect_child_module_metadata(
            child_mod_dir, rel_file, target_boundary, module_boundary, external_module_files, tf_data
        )
        for c_file, c_content, c_parsed, c_parse_err in child_file_records:
            try:
                c_rel_label = str(c_file.resolve().relative_to(module_boundary))
            except ValueError:
                c_rel_label = f"{rel_file} -> {c_file.name}"
            bal_resources = _extract_balanced_hcl_blocks(c_content, "resource", 2)
            bal_map = {(rt, rn): rbody for rt, rn, rbody in bal_resources}

            if c_parsed is None and c_parse_err:
                clean_c = re.sub(r"(?m)^[ \t]*(?:#|//)[^\n]*$", "", re.sub(r"/\*[\s\S]*?\*/", "", c_content))
                has_res_decl = bool(re.search(r'(?m)^[ \t]*resource[ \t]+"[^"\n]+"[ \t]+"[^"\n]+"[ \t]*\{', clean_c))
                total_blocks = len(bal_resources) + sum(
                    len(_extract_balanced_hcl_blocks(c_content, kw, cnt))
                    for kw, cnt in (("variable", 1), ("output", 1), ("data", 2), ("locals", 0), ("terraform", 0))
                )
                if (has_res_decl and len(bal_resources) == 0) or (clean_c.strip() and total_blocks == 0):
                    logger.warning("Failed parsing child module Terraform file %s: %s", c_file, c_parse_err)
                    if not any(u.get("path") == c_rel_label for u in tf_data["unparsed_terraform_files"]):
                        tf_data["unparsed_terraform_files"].append({"path": c_rel_label, "error": c_parse_err})
                    continue

            c_resources = _extract_child_file_resource_tuples(c_parsed, bal_resources, bal_map)
            for crt, crn, c_exp, fe_exp in c_resources:
                status = _evaluate_child_resource_condition(c_exp, fe_exp, body, child_vars, child_locals, resolved_vars)
                cr_alias = f"{mod_name}.{crn}" if crn != "default" else str(mod_name)
                if status == "inactive":
                    continue
                if status == "undetermined":
                    cond_raw = str(c_exp if c_exp is not None else fe_exp)
                    cond_clean = re.sub(r"\$\{|\}", "", cond_raw).replace("var.", "").replace("local.", "")
                    if not any(r.get("name") == cr_alias and r.get("type") == crt for r in tf_data["conditional_resources_undetermined"]):
                        tf_data["conditional_resources_undetermined"].append({
                            "type": crt,
                            "name": cr_alias,
                            "category": classify_resource_category(crt),
                            "file": f"{rel_file} -> {c_file.name}",
                            "condition": cond_clean,
                        })
                    continue
                child_ingested_types.add(crt)
                if not any(r.get("name") in (cr_alias, str(mod_name)) and r.get("type") == crt for r in tf_data["all_resources"]):
                    tf_data["all_resources"].append({
                        "type": crt,
                        "name": cr_alias,
                        "category": classify_resource_category(crt),
                        "file": f"{rel_file} -> {c_file.name}",
                    })
    except (OSError, ValueError, PermissionError) as child_err:
        logger.warning("Failed scanning child module %s: %s", child_mod_dir, child_err)
    return child_ingested_types


_PRIMARY_MODULE_RESOURCE_TYPES: Final[Dict[str, Tuple[str, str]]] = {
    "net-vpc-firewall": ("google_compute_firewall", "firewall_rules"),
    "net-vpc": ("google_compute_network", "networks"),
    "net-vpn": ("google_compute_vpn_gateway", "boundary_connections"),
    "gke-cluster": ("google_container_cluster", "gke_clusters"),
    "kms": ("google_kms_key_ring", "kms_keys"),
    "cloudsql": ("google_sql_database_instance", "databases"),
    "bigquery": ("google_bigquery_dataset", "databases"),
    "compute-vm": ("google_compute_instance", "compute_instances"),
    "gcs": ("google_storage_bucket", "storage_buckets"),
    "cloud-run": ("google_cloud_run_v2_service", "cloud_run_services"),
    "iam-service-account": ("google_service_account", "service_accounts"),
    "secret-manager": ("google_secret_manager_secret", "secrets"),
    "pubsub": ("google_pubsub_topic", "pubsub_topics"),
    "logging-bucket": ("google_logging_project_bucket_config", "logging_sinks"),
}


def _ingest_tf_provider_requirements(parsed_hcl: Dict[str, Any], tf_data: Dict[str, Any]) -> None:
    """Extracts required_version and required_providers from a parsed terraform block."""
    for tf_entry in parsed_hcl.get("terraform", []):
        if not isinstance(tf_entry, dict):
            continue
        req_v = tf_entry.get("required_version")
        if isinstance(req_v, list) and req_v:
            req_v = req_v[0]
        if req_v and not tf_data.get("terraform_engine_version"):
            tf_data["terraform_engine_version"] = str(req_v)
        req_provs = tf_entry.get("required_providers", {})
        if isinstance(req_provs, list):
            prov_dict: Dict[str, Any] = {}
            for pe in req_provs:
                if isinstance(pe, dict):
                    prov_dict.update(pe)
            req_provs = prov_dict
        if isinstance(req_provs, dict):
            for p_name, p_val in req_provs.items():
                if isinstance(p_val, list) and p_val and isinstance(p_val[0], dict):
                    p_ver = p_val[0].get("version")
                elif isinstance(p_val, dict):
                    p_ver = p_val.get("version")
                elif isinstance(p_val, str):
                    p_ver = p_val
                else:
                    p_ver = None
                if isinstance(p_ver, list) and p_ver:
                    p_ver = p_ver[0]
                if p_ver:
                    tf_data["provider_versions"][p_name] = str(p_ver)


def _ingest_tf_file_metadata(
    content: str,
    rel_file: str,
    parsed_hcl: Optional[Dict[str, Any]],
    tf_data: Dict[str, Any],
) -> None:
    """Ingests googleapis.com services, IDS/IPS hints, Assured Workloads, and provider versions."""
    for m in re.finditer(r"(?<![a-z0-9_-])([a-z0-9_-]{1,63}\.googleapis\.com)", content):
        tf_data["services"].add(m.group(1))
    for m in re.finditer(r'service\s*=\s*"([^"]+)"', content):
        if m.group(1).endswith(".googleapis.com"):
            tf_data["services"].add(m.group(1))

    if any(k in content.lower() for k in ("palo_alto", "panos", "paloalto")):
        tf_data["ids_solution"] = "Palo Alto VM-Series Next-Generation Firewall (NGFW) & IDS/IPS"
    elif "google_cloud_ids_endpoint" in content or "cloud_ids" in content:
        tf_data["ids_solution"] = "Google Cloud IDS / Cloud Armor / Security Command Center"
    elif "fortigate" in content or "fortinet" in content:
        tf_data["ids_solution"] = "Fortinet FortiGate Next-Generation Firewall (NGFW) & IDS/IPS"

    if "google_assured_workloads_workload" in content or "assuredworkloads" in content:
        tf_data["assured_workloads"].append(rel_file)

    if parsed_hcl and isinstance(parsed_hcl, dict) and "terraform" in parsed_hcl:
        _ingest_tf_provider_requirements(parsed_hcl, tf_data)


def _ingest_file_modules(
    modules: List[Tuple[str, HclBlock]],
    filepath: str,
    rel_file: str,
    target_boundary: Path,
    module_boundary: Path,
    external_module_files: Set[str],
    resolved_vars: Dict[str, Any],
    tf_data: Dict[str, Any],
) -> None:
    """Processes module blocks and child module HCL resolution for a single .tf file."""
    for mod_name, body in modules:
        tf_data["modules_used"].add(mod_name)
        src = str(extract_hcl_attr(body, "source", vars_dict=resolved_vars) or "")
        src_dir = src.split("?")[0].split("//")[-1].rstrip("/").rsplit("/", 1)[-1].lower()
        mod_name_low = str(mod_name).lower() if isinstance(mod_name, str) else ""

        _ingest_cff_module_block(mod_name, src, src_dir, mod_name_low, body, rel_file, resolved_vars, tf_data)

        child_mod_dir = resolve_local_child_module_dir(
            current_file_dir=os.path.dirname(filepath),
            source=src,
            target_boundary=target_boundary,
            module_root=module_boundary,
        )
        child_ingested_types: Set[str] = set()
        if child_mod_dir is not None:
            child_ingested_types = _resolve_and_ingest_child_module_hcl(
                mod_name, body, child_mod_dir, rel_file, target_boundary,
                module_boundary, external_module_files, resolved_vars, tf_data
            )

        for mod_key, (primary_rt, _) in _PRIMARY_MODULE_RESOURCE_TYPES.items():
            if mod_key in src_dir or (not src_dir and mod_key in mod_name_low):
                if primary_rt not in child_ingested_types and not any(
                    r.get("name") == str(mod_name) and r.get("type") == primary_rt
                    for r in tf_data["all_resources"]
                ):
                    tf_data["all_resources"].append({
                        "type": primary_rt,
                        "name": str(mod_name),
                        "category": classify_resource_category(primary_rt),
                        "file": rel_file,
                    })
                break


def _scan_single_tf_file(
    filepath: str,
    rel_file: str,
    target_boundary: Path,
    module_boundary: Path,
    external_module_files: Set[str],
    ast_failures: Set[str],
    resolved_vars: Dict[str, Any],
    tf_data: Dict[str, Any],
) -> None:
    """Parses and ingests resources, data blocks, modules, and metadata from a single .tf file."""
    hcl2_mod = _esd_attr("hcl2", hcl2)
    content = read_text_file(filepath, allowed_boundary=target_boundary)
    parsed_hcl = None
    parse_failure_err = None
    if hcl2_mod:
        try:
            parsed_hcl = hcl2_mod.loads(content)
        except (LarkError, KeyError, ValueError, TypeError) as parse_err:
            parse_failure_err = " ".join(str(parse_err).split())[:300]
            ast_failures.add(rel_file)
            logger.debug(
                "HCL AST parse failed for %s: %s; attempting balanced-brace regex fallback",
                filepath,
                parse_failure_err,
            )

    resources: List[Tuple[str, str, Union[Dict[str, Any], HclBlock]]] = []
    if parsed_hcl and isinstance(parsed_hcl, dict) and "resource" in parsed_hcl:
        for r_entry in parsed_hcl.get("resource", []):
            if isinstance(r_entry, dict):
                for rt, named_map in r_entry.items():
                    if isinstance(named_map, dict):
                        for rn, r_body in named_map.items():
                            if isinstance(r_body, dict):
                                resources.append((rt, rn, _resolve_ast_variables(r_body, resolved_vars)))
    elif parsed_hcl is None:
        resources = _extract_balanced_resource_or_module_blocks(
            content, r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', two_labels=True
        )

    for res_type, res_name, body in resources:
        classify_and_ingest_resource(res_type, res_name, body, rel_file, tf_data, resolved_vars)

    _ingest_data_kms_crypto_keys(parsed_hcl, content, rel_file, resolved_vars, tf_data)

    modules: List[Tuple[str, HclBlock]] = []
    if parsed_hcl and isinstance(parsed_hcl, dict) and "module" in parsed_hcl:
        for m_entry in parsed_hcl.get("module", []):
            if isinstance(m_entry, dict):
                for mn, m_body in m_entry.items():
                    if isinstance(m_body, dict):
                        modules.append((mn, HclBlock(_dict_to_hcl_body_str(m_body), parsed=m_body)))
    elif parsed_hcl is None:
        modules = _extract_balanced_resource_or_module_blocks(content, r'module\s+"([^"]+)"\s*\{', two_labels=False)

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

    _ingest_file_modules(
        modules, filepath, rel_file, target_boundary, module_boundary,
        external_module_files, resolved_vars, tf_data
    )
    _ingest_tf_file_metadata(content, rel_file, parsed_hcl, tf_data)


def deep_scan_tf_files(
    target_dir: str,
    user_config: Optional[Dict[str, Any]] = None,
    module_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Scans Terraform files (.tf) to discover cloud resources and architecture."""
    tf_data = init_empty_tf_data(user_config=user_config)
    module_boundary, module_boundary_label = resolve_module_root(Path(target_dir), module_root)
    external_module_files: Set[str] = set()
    ast_failures: Set[str] = set()
    scanned_files: Set[str] = set()
    scanned_dirs: Set[str] = set()
    target_boundary = Path(target_dir).resolve()

    discovered_tf_files, resolved_vars = _collect_tf_variables_and_overrides(
        target_dir, target_boundary, user_config, tf_data
    )

    for _root, _filename, filepath in discovered_tf_files:
        if filepath in scanned_files:
            continue
        scanned_files.add(filepath)
        scanned_dirs.add(os.path.dirname(filepath))
        rel_file = os.path.relpath(filepath, target_dir)
        try:
            _scan_single_tf_file(
                filepath, rel_file, target_boundary, module_boundary,
                external_module_files, ast_failures, resolved_vars, tf_data
            )
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.warning("Failed to read Terraform file %s: %s", filepath, err)
            tf_data["unparsed_terraform_files"].append({"path": rel_file, "error": str(err)[:300]})

    logger.info(
        "Recursively discovered %d Terraform (.tf) files across %d folder paths in workspace.",
        len(scanned_files),
        len(scanned_dirs),
    )
    tf_data["terraform_files_scanned"] = sorted(os.path.relpath(f, target_dir) for f in scanned_files)
    tf_data["external_module_files"] = sorted(external_module_files)
    tf_data["terraform_ast_failures"] = sorted(ast_failures)
    tf_data["module_read_boundary"] = module_boundary_label
    return finalize_terraform_data(tf_data, target_dir)
