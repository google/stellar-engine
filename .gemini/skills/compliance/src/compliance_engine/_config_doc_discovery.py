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

"""Configuration aggregation, documentation discovery, and metadata inference helpers."""

import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, Final, List, Optional, Tuple, Union

from ._tf_hcl_helpers import is_valid_cidr, is_valid_resource_name
from .file_helpers import (
    NOT_DETERMINED,
    Regime,
    YamlBudgetError,
    classify_regime,
    derive_fips_199_impacts,
    ensure_path_within_boundary,
    is_dod_regime,
    is_ignored_traversal_dir,
    parse_yaml_safe,
    read_text_file,
    resolve_default_csp_pato_package_id,
    validate_compliance_config_schema,
)

logger = logging.getLogger("extract_system_data")

LEGACY_CONFIG_KEY_ALIASES: Final[Dict[str, str]] = {
    "primary_gcp_location": "primary_location",
}
_ALIASED_CONFIG_SECTIONS: Final[Tuple[str, ...]] = ("system_information",)

_LICENSE_BOILERPLATE_RE = re.compile(
    r"(?i)(?:copyright\s+\d{4}\s+google\s+llc"
    r"|licensed\s+under\s+the\s+apache\s+license"
    r"|apache\.org/licenses/license-2\.0"
    r"|unless\s+required\s+by\s+applicable\s+law\s+or\s+agreed\s+to\s+in\s+writing"
    r"|without\s+warranties\s+or\s+conditions\s+of\s+any\s+kind"
    r"|see\s+the\s+license\s+for\s+the\s+specific\s+language\s+governing\s+permissions)",
)
_TUTORIAL_STEP_RE = re.compile(
    r"(?i)(?:cp\s+terraform\.tfvars"
    r"|with\s+your\s+(?:main|core)\s+gcp\s+project\s+id"
    r"|terraform\s+init\b"
    r"|terraform\s+apply\b"
    r"|update\s+the\s+variables\s+in\s+the\s+variables\.tf"
    r"|you\s+should\s+see\s+this\s+readme\s+and\s+some\s+terraform\s+files)",
)


def apply_legacy_config_aliases(
    cfg: Dict[str, Any],
    source_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Rewrites superseded configuration keys to their current names, in place."""
    if not isinstance(cfg, dict):
        return cfg
    where = f" in '{source_path}'" if source_path else ""

    def _migrate(section: Dict[str, Any], label: str) -> None:
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


def deep_merge_dict(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges update into base without clobbering populated values with empties."""
    if not isinstance(base, dict) or not isinstance(update, dict):
        return update
    for k, v in update.items():
        if isinstance(v, dict):
            base[k] = deep_merge_dict(base.get(k, {}), v)
        elif isinstance(v, list):
            if k not in base or not base[k] or not isinstance(base[k], list):
                base[k] = list(v)
            else:
                for item in v:
                    if item not in base[k]:
                        base[k].append(item)
        elif v is not None and v != "":
            base[k] = v
    return base


def _discover_candidate_config_files(target_dir: str) -> List[Tuple[str, int]]:
    """Discovers YAML configuration files in target_dir ordered by deterministic weight."""
    candidate_files: List[Tuple[str, int]] = []
    precedence_map = {
        "compliance_config.yaml": 100,
        "system_config.yaml": 90,
        "foundation_variables.yaml": 70,
        "variables.yaml": 50,
        "compliance_config.yaml.example": 10,
    }
    auth_cfg_path = os.path.join(target_dir, "compliance_config.yaml")
    has_auth_cfg = not os.path.islink(auth_cfg_path) and os.path.isfile(auth_cfg_path)
    for fname, weight in precedence_map.items():
        if fname == "compliance_config.yaml.example" and has_auth_cfg:
            continue
        p = os.path.join(target_dir, fname)
        if os.path.islink(p):
            logger.warning("Skipping symlinked configuration file: %s", p)
            continue
        if os.path.isfile(p):
            candidate_files.append((p, weight))

    allowed_cfg_subtrees = {"foundation_configs", "config"}
    for root, dirs, files in os.walk(target_dir, followlinks=False):
        rel_root = os.path.relpath(root, target_dir)
        if rel_root == ".":
            dirs[:] = sorted(d for d in dirs if not is_ignored_traversal_dir(d) and d in allowed_cfg_subtrees)
        else:
            dirs[:] = sorted(d for d in dirs if not is_ignored_traversal_dir(d))
        for f in sorted(files):
            if not f.endswith((".yaml", ".yml")):
                continue
            if rel_root == "." and f not in precedence_map and "foundation_variables" not in f:
                continue
            if f == "compliance_config.yaml.example" and has_auth_cfg:
                continue
            fpath = os.path.join(root, f)
            if os.path.islink(fpath):
                logger.warning("Skipping symlinked configuration file: %s", fpath)
                continue
            if any(c[0] == fpath for c in candidate_files):
                continue
            if "foundation_variables" in f:
                candidate_files.append((fpath, 70))
            elif "svc-hub" in f or "env.yaml" in f or "cidrs" in f:
                candidate_files.append((fpath, 35))
            elif any(k in f for k in ("iam", "group", "service_account", "projects")):
                candidate_files.append((fpath, 30))
            else:
                candidate_files.append((fpath, 20))
    candidate_files.sort(key=lambda x: (x[1], x[0]))
    return candidate_files


def _validate_and_merge_config_paths(
    cfg: Dict[str, Any], aggregated: Dict[str, Any], target_boundary: Path
) -> None:
    """Merges standard sections and validates configured file paths against target_boundary."""
    for sec_key in (
        "system_information", "personnel_roles", "document_versions", "custom_services",
        "contingency_planning", "continuous_monitoring", "contracts", "security_scanners",
        "security_operations", "external_systems", "disa_stigs", "export_preferences",
    ):
        if sec_key in cfg and isinstance(cfg[sec_key], dict):
            deep_merge_dict(aggregated[sec_key], cfg[sec_key])

    for path_key in ("terraform_plan_path", "terraform_state_path", "sbom_path"):
        if path_key in cfg and cfg[path_key]:
            raw_path_val = str(cfg[path_key])
            cand_p = Path(raw_path_val)
            resolved_cand = cand_p if cand_p.is_absolute() else (target_boundary / cand_p)
            try:
                ensure_path_within_boundary(resolved_cand, allowed_boundary=target_boundary, allow_symlinks=False)
                aggregated[path_key] = raw_path_val
            except (ValueError, PermissionError, OSError) as bound_err:
                logger.warning(
                    "Rejecting configured %s '%s' outside target boundary '%s': %s",
                    path_key, raw_path_val, target_boundary, bound_err,
                )
                aggregated[path_key] = None

    for sys_path_key in (
        "terraform_plan_path", "terraform_state_path", "sbom_path",
        "architecture_doc_path", "existing_policies_dir",
    ):
        sys_val = aggregated["system_information"].get(sys_path_key)
        if sys_val:
            cand_p = Path(str(sys_val))
            resolved_cand = cand_p if cand_p.is_absolute() else (target_boundary / cand_p)
            try:
                ensure_path_within_boundary(resolved_cand, allowed_boundary=target_boundary, allow_symlinks=False)
            except (ValueError, PermissionError, OSError) as bound_err:
                logger.warning(
                    "Rejecting system_information.%s '%s' outside target boundary '%s': %s",
                    sys_path_key, sys_val, target_boundary, bound_err,
                )
                aggregated["system_information"].pop(sys_path_key, None)


def _merge_org_and_billing_keys(cfg: Dict[str, Any], sys_info: Dict[str, Any]) -> None:
    """Merges organization, billing, region, and Assured Workloads regime keys into sys_info."""
    org = cfg.get("organization")
    if isinstance(org, str) and org.strip():
        sys_info["organization"] = org.strip()
    elif isinstance(org, dict):
        if org.get("domain_name") and str(org.get("domain_name")).strip():
            dom = str(org["domain_name"]).strip()
            sys_info["organization"] = dom
            sys_info["organization_domain"] = dom
        if org.get("org_id") and str(org.get("org_id")).strip():
            sys_info["org_id"] = str(org["org_id"]).strip()

    for domain_key in ("organization_domain", "domain_name"):
        if cfg.get(domain_key) and str(cfg[domain_key]).strip():
            sys_info["organization_domain"] = str(cfg[domain_key]).strip()
            break

    if isinstance(cfg.get("billing"), dict) and cfg["billing"].get("account_id"):
        if str(cfg["billing"]["account_id"]).strip():
            sys_info["billing_account"] = str(cfg["billing"]["account_id"]).strip()
    elif cfg.get("billing_account") and str(cfg["billing_account"]).strip():
        sys_info["billing_account"] = str(cfg["billing_account"]).strip()

    if cfg.get("default_region") and str(cfg["default_region"]).strip():
        sys_info["primary_location"] = str(cfg["default_region"]).strip()

    aw = cfg.get("assured_workloads")
    if isinstance(aw, dict) and aw.get("enabled") and aw.get("regime"):
        regime = str(aw.get("regime")).upper()
        classified = classify_regime(regime)
        label = regime if classified == Regime.UNKNOWN else classified.value
        sys_info["impact_level"] = regime
        sys_info["compliance_baseline"] = f"NIST SP 800-53 Rev. 5 / {label}"


def _merge_top_level_and_org_keys(cfg: Dict[str, Any], aggregated: Dict[str, Any]) -> None:
    """Merges top-level switches, POA&M lists, and system_information scalar/org keys."""
    for flag_key in ("include_unparsed_blueprints_in_poam", "include_scanner_failures_in_poam"):
        if isinstance(cfg.get(flag_key), bool):
            aggregated[flag_key] = cfg[flag_key]
    for p_key in ("poam_items", "security_concerns", "findings"):
        if isinstance(cfg.get(p_key), list):
            aggregated["poam_items"].extend(cfg[p_key])
        elif isinstance(cfg.get(p_key), dict):
            aggregated["poam_items"].append(cfg[p_key])

    sys_info = aggregated["system_information"]
    for key in (
        "system_name", "system_abbreviation", "impact_level", "compliance_baseline",
        "effective_date", "primary_location", "billing_account", "confidentiality_impact",
        "integrity_impact", "availability_impact", "rmf_governance_system", "system_description",
    ):
        if key in cfg and cfg[key] is not None and str(cfg[key]).strip():
            sys_info[key] = cfg[key]

    _merge_org_and_billing_keys(cfg, sys_info)


def _merge_network_and_structure_keys(cfg: Dict[str, Any], aggregated: Dict[str, Any]) -> None:
    """Merges structure, IAM group, VPC, and subnet CIDR keys from cfg into aggregated."""
    sys_info = aggregated["system_information"]
    st = cfg.get("structure")
    if isinstance(st, dict):
        if st.get("resource_prefix") and str(st.get("resource_prefix")).strip():
            sys_info["system_abbreviation"] = str(st.get("resource_prefix")).strip().upper()
        regs = st.get("regions", {})
        if isinstance(regs, dict):
            pri, sec = regs.get("primary"), regs.get("secondary")
            if pri and sec:
                sys_info["primary_location"] = f"{pri} / {sec}"
            elif pri:
                sys_info["primary_location"] = pri

    if isinstance(cfg.get("iam"), dict) and isinstance(cfg["iam"].get("google_groups"), dict):
        for g_k, g_v in cfg["iam"]["google_groups"].items():
            if isinstance(g_v, list):
                aggregated["iam_groups"][g_k] = g_v
            elif isinstance(g_v, str):
                aggregated["iam_groups"][g_k] = [g_v]

    net_cfg = aggregated["network_configs"]
    if "connectivity_model" in cfg:
        net_cfg["connectivity_model"] = cfg["connectivity_model"]
    if isinstance(cfg.get("vpcs"), dict):
        for v_key, v_val in cfg["vpcs"].items():
            if isinstance(v_val, str):
                v_name = v_val
            elif isinstance(v_val, dict):
                v_name = v_val.get("name", v_key)
                for s in v_val.get("subnets", []):
                    cidr = s.get("ip_cidr_range") if isinstance(s, dict) else s
                    if is_valid_cidr(cidr):
                        net_cfg["subnets"].add(cidr)
            else:
                v_name = v_key
            if v_name and is_valid_resource_name(v_name) and v_name not in net_cfg["vpcs"]:
                net_cfg["vpcs"].append(v_name)

    for cidr_key in ("subnets", "hub_vpcs", "spoke_vpcs", "cidrs", "subnet_cidrs"):
        c_val = cfg.get(cidr_key)
        if isinstance(c_val, list):
            for s in c_val:
                cidr = s.get("ip_cidr_range") if isinstance(s, dict) else s
                if is_valid_cidr(cidr):
                    net_cfg["subnets"].add(cidr)


def load_all_system_configs(target_dir: str) -> Dict[str, Any]:
    """Recursively scans and aggregates configuration across YAML manifests."""
    aggregated: Dict[str, Any] = {
        "system_information": {}, "personnel_roles": {}, "document_versions": {},
        "custom_services": {}, "contingency_planning": {}, "continuous_monitoring": {},
        "contracts": {}, "iam_groups": {}, "poam_items": [], "security_scanners": {},
        "security_operations": {}, "external_systems": {}, "disa_stigs": {},
        "export_preferences": {}, "terraform_plan_path": None, "terraform_state_path": None,
        "sbom_path": None,
        "network_configs": {"vpcs": [], "subnets": set(), "connectivity_model": None},
    }
    target_boundary = Path(target_dir).resolve()
    candidate_files = _discover_candidate_config_files(target_dir)
    loaded_paths = []
    foundational_files = {"compliance_config.yaml", "system_config.yaml"}

    for fpath, _ in candidate_files:
        base_name = os.path.basename(fpath)
        try:
            resolved_p = ensure_path_within_boundary(
                fpath, allowed_boundary=target_boundary, allow_symlinks=False
            )
            content = read_text_file(resolved_p, allowed_boundary=target_boundary)
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

        apply_legacy_config_aliases(cfg, source_path=fpath)
        if "compliance_config" in base_name:
            validate_compliance_config_schema(cfg, source_path=fpath)
        loaded_paths.append(fpath)
        _validate_and_merge_config_paths(cfg, aggregated, target_boundary)
        _merge_top_level_and_org_keys(cfg, aggregated)
        _merge_network_and_structure_keys(cfg, aggregated)

    if loaded_paths:
        logger.info("Successfully loaded and correlated configuration across %d YAML manifests.", len(loaded_paths))
    aggregated["network_configs"]["subnets"] = sorted(list(aggregated["network_configs"]["subnets"]))
    return aggregated


def infer_primary_location(
    tf_scanned: Dict[str, Any],
    app_scanned: Dict[str, Any],
    sys_info: Dict[str, Any],
) -> str:
    """Infers primary deployment location from scanned cloud resources."""
    del app_scanned
    val = sys_info.get("primary_location")
    if val and not str(val).startswith("[CONFIG_REQUIRED"):
        return str(val)
    loc_counts: Dict[str, int] = {}
    for item in (
        tf_scanned.get("storage_buckets", [])
        + tf_scanned.get("databases", [])
        + tf_scanned.get("compute_instances", [])
        + tf_scanned.get("gke_clusters", [])
        + tf_scanned.get("cloud_run_services", [])
    ):
        loc = item.get("location") or item.get("region") or item.get("zone")
        if not loc or not isinstance(loc, str):
            continue
        loc_str = loc.strip()
        if (
            not loc_str
            or loc_str.lower() in ("none", "null", "not determined from iac", NOT_DETERMINED.lower())
            or loc_str.startswith("[")
            or any(tok in loc_str for tok in ("${", "var.", "local."))
        ):
            continue
        parts = loc_str.split("-")
        if len(parts) >= 3 and len(parts[-1]) == 1 and parts[-1].isalpha():
            loc_str = "-".join(parts[:-1])
        norm_loc = "US" if loc_str.upper() == "US" else loc_str.lower()
        loc_counts[norm_loc] = loc_counts.get(norm_loc, 0) + 1
    if loc_counts:
        top_loc = sorted(loc_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
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
            "US": "US Multi-Region (United States)",
        }
        return friendly_names.get(top_loc, f"{top_loc} (Cloud Region)")
    return val or "[CONFIG_REQUIRED: Primary Location]"


def infer_cloud_provider(tf_scanned: Dict[str, Any], sys_info: Dict[str, Any]) -> str:
    """Infers primary cloud service provider from scanned infrastructure and config."""
    del tf_scanned
    configured = sys_info.get("cloud_provider")
    if configured and not str(configured).startswith("[CONFIG_REQUIRED"):
        return str(configured)
    return "Google Cloud Platform (GCP)"


def _score_doc_candidate(parts: Tuple[str, ...], f_lower: str) -> Optional[int]:
    """Computes the priority score for a documentation file path."""
    if len(parts) == 0:
        if f_lower in ("readme.md", "readme.rst", "readme.txt"):
            return 100
        if f_lower in ("spec.md", "specification.md"):
            return 95
        if f_lower in ("tdd.md", "technical_design_document.md"):
            return 90
        if f_lower in ("architecture.md", "architecture_overview.md"):
            return 88
        return None
    top_part = parts[0].lower()
    if f_lower in ("readme.md", "readme.rst", "readme.txt"):
        base = 85 if top_part in ("code", "src") else (75 if top_part in ("app", "apps") else (70 if top_part in ("infrastructure", "infra", "docs") else 60))
        return base - (len(parts) * 2)
    if f_lower in ("spec.md", "tdd.md", "architecture.md"):
        return 78 - (len(parts) * 2)
    return None


def find_candidate_doc_files(target_dir: Union[str, Path]) -> List[Tuple[int, Path]]:
    """Finds and scores candidate markdown documentation files for system descriptions."""
    root = Path(target_dir).resolve()
    if not root.exists():
        return []
    candidates: List[Tuple[int, Path]] = []
    excluded_dirs = {
        ".git", ".gemini", "ato_artifacts", "node_modules", ".terraform",
        "vendor", "fabric", "recipes", "test", "tests", "terraform", "environments", "modules",
    }
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(
            d for d in dirnames
            if d.lower() not in excluded_dirs and not is_ignored_traversal_dir(d) and not d.startswith(".")
        )
        parts = Path(dirpath).relative_to(root).parts
        if parts and any(p.lower() in excluded_dirs for p in parts):
            continue
        for f in sorted(filenames):
            f_lower = f.lower()
            if not f_lower.endswith((".md", ".rst", ".txt")):
                continue
            file_path = Path(dirpath) / f
            if file_path.is_symlink():
                continue
            score = _score_doc_candidate(parts, f_lower)
            if score is not None:
                candidates.append((score, file_path))
    candidates.sort(key=lambda x: (-x[0], str(x[1])))
    return candidates


def _clean_prose_paragraph(raw_para: str) -> str:
    """Strips markdown images, HTML comments, <br> tags, license boilerplate, and tutorial steps."""
    cp_clean = re.sub(r"!\[[^\]]{0,1024}\]\([^)\n]{0,2048}\)", "", raw_para)
    cp_clean = re.sub(r"<!--[\s\S]{0,16384}?-->", "", cp_clean)
    cp_clean = re.sub(r"<br\s*/?>", " ", cp_clean, flags=re.IGNORECASE)
    cp_clean = re.sub(r"\s+", " ", cp_clean).strip()
    if _LICENSE_BOILERPLATE_RE.search(cp_clean) or _TUTORIAL_STEP_RE.search(cp_clean):
        return ""
    return cp_clean


def _extract_explicit_markdown_section(text: str) -> Optional[str]:
    """Extracts narrative prose from dedicated Overview/Introduction/Blueprint sections."""
    pat = (
        r"(?i)^##+\s+(?:system\s+description|system\s+overview|general\s+system\s+description"
        r"|overview|about|executive\s+summary|purpose|project\s+scope|architecture\s+overview"
        r"|introduction[^\n]*|[^\n]*blueprint)\s*\n+(.*?)(?=\n##+|\Z)"
    )
    for m in re.finditer(pat, text, flags=re.DOTALL | re.MULTILINE):
        candidate = re.sub(r"```[\s\S]{0,16384}?```", "", m.group(1).strip()).strip()
        cand_paras = [
            p.strip() for p in re.split(r"\n\s*\n", candidate)
            if p.strip()
            and not p.strip().startswith(("|", "#"))
            and not re.match(r"^[-*_]{3,}$", p.strip())
        ]
        clean_cand_paras = [
            cp_clean for cp in cand_paras
            if (cp_clean := _clean_prose_paragraph(cp)) and len(cp_clean) > 25 and not cp_clean.startswith("<")
        ]
        if clean_cand_paras:
            return "\n\n".join(clean_cand_paras[:3])
    return None


def _extract_intro_markdown_paragraphs(text: str) -> List[str]:
    """Extracts up to 2 introductory prose paragraphs from markdown text."""
    intro_paras: List[str] = []
    prose_text = re.sub(r"```[\s\S]{0,16384}?```", "", text)
    raw_paras = [p.strip() for p in re.split(r"\n\s*\n", prose_text) if p.strip()]
    skip_section = False
    for p in raw_paras:
        if p.startswith("#"):
            skip_section = bool(
                re.match(
                    r"(?i)^##+\s+(?:how\s+to\s+deploy|deployment\s+steps|prerequisites|pre-requisite"
                    r"|requirements|variables|outputs|verification\s+of|table\s+creation\s+notes)",
                    p,
                )
            )
            continue
        if skip_section or re.match(r"^[-*_]{3,}$", p) or p.startswith("![") or (p.startswith("[![") and "]" in p):
            continue
        if p.startswith(("```", "<", "|")):
            if intro_paras:
                break
            continue
        clean_p = _clean_prose_paragraph(p)
        if not clean_p:
            continue
        if clean_p.lower().startswith("welcome to "):
            gm = re.match(
                r"^welcome to (?:the\s+)?(.*?)(?:\s+(?:codebase|repository|project))?\.\s*"
                r"(?:This (?:repository|project)\s+(?:contains|provides|delivers)\s+)?(.*)",
                clean_p,
                flags=re.IGNORECASE,
            )
            if gm:
                subj, body_rest = gm.group(1).strip(), gm.group(2).strip()
                clean_p = f"The {subj} contains {body_rest}" if body_rest else subj
        if len(clean_p) > 25 and not clean_p.startswith("<"):
            intro_paras.append(clean_p)
            if len(intro_paras) >= 2:
                break
    return intro_paras


def extract_system_description_from_markdown(content: str) -> Tuple[str, str]:
    """Extracts the system title and operational description from markdown text."""
    lines = content.splitlines()
    frontmatter_dict: Dict[str, Any] = {}
    if lines and lines[0].strip() == "---":
        end_fm = 1
        while end_fm < len(lines) and lines[end_fm].strip() != "---":
            end_fm += 1
        if end_fm < len(lines):
            fm_text = "\n".join(lines[1:end_fm])
            try:
                frontmatter_dict = parse_yaml_safe(fm_text, source_name="Markdown front matter")
            except YamlBudgetError:
                raise
            except ValueError as e:
                logger.warning("Failed to parse YAML frontmatter: %s", e)
            lines = lines[end_fm + 1 :]

    text = "\n".join(lines)
    for hook_re in (
        r"<!--\s*BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK\s*-->[\s\S]*?<!--\s*END OF PRE-COMMIT-TERRAFORM DOCS HOOK\s*-->",
        r"<!--\s*BEGIN[_\s]+TF_?DOCS\s*-->[\s\S]*?<!--\s*END[_\s]+TF_?DOCS\s*-->",
        r"<!--\s*BEGIN[_\s]+TOC\s*-->[\s\S]*?<!--\s*END[_\s]+TOC\s*-->",
    ):
        text = re.sub(hook_re, "", text, flags=re.IGNORECASE)
    text = re.sub(r"/\*[\s\S]{0,4096}?\*/", "", text)

    top_header_m = re.search(r"^#\s+([^\n]+)", text, flags=re.MULTILINE)
    top_title = (
        frontmatter_dict.get("system_name")
        or frontmatter_dict.get("title")
        or frontmatter_dict.get("name")
        or (top_header_m.group(1).strip() if top_header_m else "")
    )
    fm_desc = (
        frontmatter_dict.get("system_description")
        or frontmatter_dict.get("description")
        or frontmatter_dict.get("summary")
    )
    if fm_desc and isinstance(fm_desc, str) and len(fm_desc.strip()) >= 20:
        return fm_desc.strip(), str(top_title).strip()

    text = re.sub(r"(?m)^(#+\s+[^\n]+)\n(?!\n)", r"\1\n\n", text)
    extracted_section = _extract_explicit_markdown_section(text)
    intro_paras = _extract_intro_markdown_paragraphs(text)

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
    """Discovers and parses authentic system documentation from candidate markdown files."""
    root = Path(target_dir).resolve()
    for _score, cand_path in find_candidate_doc_files(root):
        try:
            content = read_text_file(cand_path, allowed_boundary=root)
            desc, title = extract_system_description_from_markdown(content)
            if desc and len(desc.strip()) >= 35:
                return {
                    "title": title,
                    "description": desc.strip(),
                    "source_path": str(cand_path.relative_to(root)),
                }
        except YamlBudgetError:
            raise
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.debug("Failed reading documentation candidate %s: %s", cand_path, err)
    return None


def _abbr_from_words(raw_title: str) -> Optional[str]:
    """Derives an uppercase system abbreviation from a title string."""
    paren_m = re.search(r"\(([A-Z0-9]{2,8})\)", raw_title)
    if paren_m:
        return paren_m.group(1)
    words = [w for w in re.sub(r"[^a-zA-Z0-9\s]", "", raw_title).split() if w]
    if len(words) >= 3:
        return "".join(w[0].upper() for w in words[:4])
    cap_words = [w for w in words if w.isupper()]
    if cap_words:
        return cap_words[-1] if len(cap_words[-1]) <= 6 else "".join(w[0] for w in cap_words[:4])
    return "".join(w[0].upper() for w in words[:4]) if words else None


def infer_system_name_and_abbr(
    target_dir: str,
    tf_scanned: Dict[str, Any],
    app_scanned: Dict[str, Any],
    sys_info: Dict[str, Any],
    readme_data: Optional[Dict[str, str]] = None,
) -> Tuple[str, str]:
    """Infers system name and abbreviation from application, folder, or network naming."""
    name = sys_info.get("system_name")
    abbr = sys_info.get("system_abbreviation")
    if name and not name.startswith("[CONFIG_REQUIRED") and abbr and not abbr.startswith("[CONFIG_REQUIRED"):
        return name, abbr

    inferred_name = None
    inferred_abbr = None
    if readme_data and readme_data.get("title"):
        raw_title = re.sub(
            r"^(?:Welcome to (?:the\s+)?|Technical Design Document:\s*|Specification:\s*|POC Design Document:\s*)",
            "",
            readme_data["title"].strip(),
            flags=re.IGNORECASE,
        ).strip()
        if len(raw_title) > 3:
            inferred_name = raw_title
            inferred_abbr = _abbr_from_words(raw_title)

    if not inferred_name and app_scanned.get("applications"):
        first_app = app_scanned["applications"][0].get("name")
        if first_app:
            clean_app = first_app.replace("-", " ").replace("_", " ").title()
            inferred_name = f"{clean_app} System"
            inferred_abbr = "".join(w[0].upper() for w in clean_app.split() if w)[:4]

    if not inferred_name and target_dir:
        dir_base = os.path.basename(os.path.abspath(target_dir))
        if dir_base and dir_base not in (".", "/", "workspace", "stellar-engine", "blueprints", "modules", "fast"):
            clean_dir = dir_base.replace("-", " ").replace("_", " ").title()
            inferred_name = f"{clean_dir} Platform"
            inferred_abbr = "".join(w[0].upper() for w in clean_dir.split() if w)[:4]

    if not inferred_name and tf_scanned.get("networks"):
        net_0 = sorted(tf_scanned["networks"])[0]
        clean_net = net_0.replace("vpc-", "").replace("-vpc", "").replace("-", " ").title()
        inferred_name = f"{clean_net} Platform"
        inferred_abbr = "".join(w[0].upper() for w in clean_net.split() if w)[:4]

    final_name = name if (name and not name.startswith("[CONFIG_REQUIRED")) else (inferred_name or "[CONFIG_REQUIRED: System Name]")
    final_abbr = abbr if (abbr and not abbr.startswith("[CONFIG_REQUIRED")) else (inferred_abbr or "[CONFIG_REQUIRED: System Abbreviation]")
    return final_name, final_abbr


def infer_security_categorization(
    tf_scanned: Dict[str, Any],
    app_scanned: Dict[str, Any],
    sys_info: Dict[str, Any],
) -> Tuple[str, str, str]:
    """Infers FIPS 199 security categorization for Confidentiality, Integrity, and Availability."""
    del tf_scanned, app_scanned
    return derive_fips_199_impacts(sys_info)


def _infer_regime_from_target_path(
    raw_target_dir: Union[str, Path], resolved_target_path: Path
) -> Tuple[Optional[str], Optional[str]]:
    """Infers impact_level and compliance_baseline from the blueprint path when unconfigured."""
    for candidate_path in (Path(os.path.abspath(str(raw_target_dir))), resolved_target_path):
        parts_lower = [p.lower() for p in candidate_path.parts]
        if "fedramp-high" in parts_lower or "fedramp_high" in parts_lower:
            return "FedRAMP High", "NIST SP 800-53 Rev. 5 / FedRAMP High"
        if "fedramp-moderate" in parts_lower or "fedramp_moderate" in parts_lower:
            return "FedRAMP Moderate", "NIST SP 800-53 Rev. 5 / FedRAMP Moderate"
        if "fedramp-low" in parts_lower or "fedramp_low" in parts_lower:
            return "FedRAMP Low", "NIST SP 800-53 Rev. 5 / FedRAMP Low"
        if "fisma-high" in parts_lower or "fisma_high" in parts_lower:
            return "FISMA High", "NIST SP 800-53B Rev. 5 / FISMA High"
        if "fisma-moderate" in parts_lower or "fisma_moderate" in parts_lower:
            return "FISMA Moderate", "NIST SP 800-53B Rev. 5 / FISMA Moderate"
        if "fisma-low" in parts_lower or "fisma_low" in parts_lower:
            return "FISMA Low", "NIST SP 800-53B Rev. 5 / FISMA Low"
        if "il6" in parts_lower or "il-6" in parts_lower:
            return "IL6", "NIST SP 800-53 Rev. 5 / DoD IL6"
        if "il4" in parts_lower or "il-4" in parts_lower:
            return "IL4", "NIST SP 800-53 Rev. 5 / DoD IL4"
        if "il2" in parts_lower or "il-2" in parts_lower:
            return "IL2", "NIST SP 800-53 Rev. 5 / DoD IL2"
        if "il5" in parts_lower or "il-5" in parts_lower:
            return "IL5", "NIST SP 800-53 Rev. 5 / DoD IL5"
        if "cjis" in parts_lower:
            return "CJIS", "NIST SP 800-53 Rev. 5 / CJIS Security Policy"
        if "stateramp" in parts_lower or "govramp" in parts_lower:
            return "GovRAMP High", "NIST SP 800-53 Rev. 5 / GovRAMP"
    return None, None


def _detect_external_siem_from_sinks(logging_sinks: List[Any], is_dod: bool) -> Tuple[str, str]:
    """Detects external SIEM type and sink destination from logging_sinks."""
    for s in logging_sinks:
        if not isinstance(s, dict):
            continue
        dest = str(s.get("destination", "")).lower()
        for keyword, label in (
            ("splunk", "Splunk"),
            ("elastic", "Elasticsearch"),
            ("sentinel", "Azure Sentinel"),
            ("qradar", "QRadar"),
        ):
            if keyword in dest:
                return label, str(s.get("destination", "")).strip()
    return ("[CONFIG_REQUIRED: External SIEM]" if is_dod else "None"), ""


def _resolve_external_system_integrations(
    ext_cfg: Dict[str, Any], target_dir: Union[str, Path], is_dod: bool
) -> Dict[str, Any]:
    """Resolves external system integrations (IdP, MFA, vulnerability scanner, ITSM, CI/CD, EDR)."""
    def _cfg_or_default(key: str, default: str) -> str:
        val = str(ext_cfg.get(key) or "").strip()
        return default if (not val or val.startswith("[")) else val

    default_idp = (
        "Enterprise Identity Provider (DoD CAC / PIV)"
        if is_dod
        else "Enterprise Identity Provider (Cloud Identity / SSO)"
    )
    cicd = str(ext_cfg.get("cicd_platform") or "").strip()
    if not cicd or cicd.startswith("["):
        t_path = Path(target_dir)
        check_dirs = [t_path, t_path.parent] if t_path.name in ("terraform", "app") else [t_path]
        detected_cicd = None
        for cd in check_dirs:
            if (cd / ".gitlab-ci.yml").is_file():
                detected_cicd = "GitLab CI"
                break
            if (cd / ".github").is_dir():
                detected_cicd = "GitHub Actions"
                break
            if (cd / "cloudbuild.yaml").is_file() or (cd / "cloudbuild.yml").is_file():
                detected_cicd = "Google Cloud Build + Artifact Registry"
                break
        cicd = detected_cicd or "[CONFIG_REQUIRED: CI/CD Platform]"

    return {
        "identity_provider": _cfg_or_default("identity_provider", default_idp),
        "mfa_mechanism": _cfg_or_default("mfa_mechanism", "[CONFIG_REQUIRED: MFA Mechanism]"),
        "vulnerability_scanner": _cfg_or_default("vulnerability_scanner", "[CONFIG_REQUIRED: Vulnerability Scanner]"),
        "itsm_system": _cfg_or_default("itsm_system", "[CONFIG_REQUIRED: ITSM System]"),
        "cicd_platform": cicd,
        "edr_solution": _cfg_or_default("edr_solution", "[CONFIG_REQUIRED: Endpoint Detection and Response]"),
        "perimeter_gateway": _cfg_or_default("perimeter_gateway", "[CONFIG_REQUIRED: Perimeter Gateway]"),
    }


def _summarize_secops_telemetry(
    secops_enabled: bool,
    scc_enabled: bool,
    scc_tier: str,
    is_dod: bool,
    allow_unaccredited_scc: bool,
    cssp_provider: str,
    ext_siem: str,
) -> Tuple[str, str]:
    """Builds telemetry_summary and threat_detection_engine descriptions."""
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

    telemetry_summary = (
        "; ".join(telemetry_parts)
        if telemetry_parts
        else "Cloud Logging Log Router export sinks and Cloud Monitoring alert policies"
    )
    if secops_enabled and scc_enabled:
        threat_engine = (
            f"Google Cloud SecOps (Chronicle) integrated with "
            f"Security Command Center {scc_tier.title()} Event Threat Detection"
        )
    elif secops_enabled:
        threat_engine = "Google Cloud SecOps (Chronicle) real-time threat analytics"
    elif scc_enabled:
        threat_engine = f"Security Command Center {scc_tier.title()} Event Threat Detection"
    elif cssp_provider and cssp_provider.lower() != "none":
        threat_engine = f"{cssp_provider} Threat Operations Center via Cloud Logging export sinks"
    else:
        threat_engine = "Cloud Monitoring Anomaly Detection and Audit Log Analysis"
    return telemetry_summary, threat_engine


def resolve_secops_and_external_systems(
    user_config: Dict[str, Any],
    tf_scanned: Dict[str, Any],
    target_dir: Union[str, Path],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Resolves dynamic Security Operations, Telemetry, and External Systems."""
    is_dod = is_dod_regime(user_config.get("system_information", {}))
    secops_cfg = dict(user_config.get("security_operations") or {})
    ext_cfg = dict(user_config.get("external_systems") or {})
    services = {str(s).lower() for s in tf_scanned.get("services", [])}
    all_res = tf_scanned.get("all_resources", [])
    logging_sinks = tf_scanned.get("logging_sinks", [])

    scc_raw = secops_cfg.get("scc_enabled", "auto")
    if str(scc_raw).lower() == "auto":
        scc_enabled = "securitycenter.googleapis.com" in services or any(
            "scc" in str(r.get("type", "")).lower() or "security_center" in str(r.get("type", "")).lower()
            for r in all_res
        )
    else:
        scc_enabled = bool(scc_raw) and str(scc_raw).lower() not in ("false", "none", "no", "0")
    scc_tier = str(secops_cfg.get("scc_tier") or "premium").lower()
    allow_unaccredited_scc = bool(secops_cfg.get("allow_unaccredited_scc_in_il5", False))

    secops_raw = secops_cfg.get("secops_enabled", "auto")
    if str(secops_raw).lower() == "auto":
        secops_enabled = "chronicle.googleapis.com" in services or any(
            "chronicle" in str(s.get("destination", "")).lower() for s in logging_sinks if isinstance(s, dict)
        )
    else:
        secops_enabled = bool(secops_raw) and str(secops_raw).lower() not in ("false", "none", "no", "0")

    secops_inst = str(secops_cfg.get("secops_instance_name") or "").strip()
    if secops_inst in ("", "none", "null", "[CHRONICLE_INSTANCE_NAME]"):
        secops_inst = "chronicle-secops-enclave" if secops_enabled else "Not Deployed"

    cssp_provider = str(secops_cfg.get("cssp_provider") or "").strip()
    if not cssp_provider or cssp_provider.startswith("["):
        cssp_provider = "DISA" if is_dod else "Enterprise SOC"

    ext_siem = str(secops_cfg.get("external_siem_type") or "").strip()
    detected_siem, matched_dest = _detect_external_siem_from_sinks(logging_sinks, is_dod)
    if not ext_siem or ext_siem.startswith("["):
        ext_siem = detected_siem
    ext_siem_dest = str(secops_cfg.get("external_siem_destination") or "").strip()
    if not ext_siem_dest or ext_siem_dest.startswith("["):
        ext_siem_dest = matched_dest

    telemetry_summary, threat_engine = _summarize_secops_telemetry(
        secops_enabled, scc_enabled, scc_tier, is_dod, allow_unaccredited_scc, cssp_provider, ext_siem
    )

    resolved_secops = {
        "scc_enabled": scc_enabled,
        "scc_tier": scc_tier,
        "allow_unaccredited_scc_in_il5": allow_unaccredited_scc,
        "secops_enabled": secops_enabled,
        "secops_instance_name": secops_inst,
        "cssp_provider": cssp_provider,
        "external_siem_type": ext_siem,
        "external_siem_destination": ext_siem_dest,
        "telemetry_summary": telemetry_summary,
        "threat_detection_engine": threat_engine,
    }
    resolved_ext = _resolve_external_system_integrations(ext_cfg, target_dir, is_dod)
    return resolved_secops, resolved_ext


def _assemble_system_inventory_dict(
    user_config: Dict[str, Any],
    tf_scanned: Dict[str, Any],
    app_scanned: Dict[str, Any],
    readme_data: Optional[Dict[str, str]],
    inferred_meta: Tuple[str, str, str, str, str, str, str],
    res_secops: Dict[str, Any],
    res_ext: Dict[str, Any],
) -> Dict[str, Any]:
    """Assembles the raw system_inventory dictionary prior to sensitive-data scrubbing."""
    inferred_sys_name, inferred_sys_abbr, inferred_loc, inferred_cloud, inf_c, inf_i, inf_a = inferred_meta
    sys_info = user_config.get("system_information", {})
    roles_info = user_config.get("personnel_roles", {})

    def _non_req(key: str, fallback: str) -> str:
        val = sys_info.get(key)
        return val if (val and not str(val).startswith("[CONFIG_REQUIRED")) else fallback

    return {
        "system_information": {
            "organization": sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]",
            "system_name": _non_req("system_name", inferred_sys_name),
            "system_abbreviation": _non_req("system_abbreviation", inferred_sys_abbr),
            "impact_level": sys_info.get("impact_level") or "IL5",
            "compliance_baseline": sys_info.get("compliance_baseline") or "NIST SP 800-53 Rev. 5 / DoD IL5",
            "effective_date": sys_info.get("effective_date"),
            "system_description": sys_info.get("system_description") or (readme_data.get("description") if readme_data else ""),
            "readme_system_description": readme_data.get("description") if readme_data else "",
            "readme_source_path": readme_data.get("source_path") if readme_data else "",
            "readme_title": readme_data.get("title") if readme_data else "",
            "cloud_provider": _non_req("cloud_provider", inferred_cloud),
            "cloud_service_provider_abbr": sys_info.get("cloud_service_provider_abbr") or "GCP",
            "ditpr_id": sys_info.get("ditpr_id") or sys_info.get("ditpr_don_id") or sys_info.get("ditpr_emass_id") or "[CONFIG_REQUIRED: DITPR ID]",
            "emass_system_id": sys_info.get("emass_system_id") or sys_info.get("emass_id") or "[CONFIG_REQUIRED: eMASS System ID]",
            "primary_location": _non_req("primary_location", inferred_loc),
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
            "organization_domain": sys_info.get("organization_domain") or "",
            "org_id": sys_info.get("org_id") or "",
            "prepared_by": sys_info.get("prepared_by") or "",
            "csp_pato_package_id": resolve_default_csp_pato_package_id(sys_info),
        },
        "security_operations": res_secops,
        "external_systems": res_ext,
        "personnel_roles": {
            "authorizing_official": roles_info.get("authorizing_official", {}),
            "system_owner": roles_info.get("system_owner", {}),
            "issm": roles_info.get("issm", {}),
            "isso": roles_info.get("isso", {}),
        },
        "document_versions": user_config.get("document_versions", {}),
        "custom_services": user_config.get("custom_services", {}),
        "contracts": user_config.get("contracts", {}),
        "iam_groups": user_config.get("iam_groups", {}),
        "poam_items": user_config.get("poam_items", []),
        "include_unparsed_blueprints_in_poam": bool(user_config.get("include_unparsed_blueprints_in_poam", True)),
        "include_scanner_failures_in_poam": bool(user_config.get("include_scanner_failures_in_poam", False)),
        "provenance": {
            "module_root": tf_scanned.get("module_read_boundary", "target"),
            "external_module_files": list(tf_scanned.get("external_module_files", [])),
        },
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
            "application_ports": app_scanned["exposed_ports"],
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
            "unparsed_terraform_files": tf_scanned.get("unparsed_terraform_files", []),
            "conditional_resources_undetermined": tf_scanned.get("conditional_resources_undetermined", []),
            "modules_used": tf_scanned["modules_used"],
        },
        "application_components": {
            "applications": app_scanned["applications"],
            "software_packages": app_scanned["software_packages"],
            "container_images": app_scanned["container_images"],
            "exposed_ports": app_scanned["exposed_ports"],
            "frameworks": sorted(list(app_scanned["frameworks"])),
            "runtimes": sorted(list(app_scanned["runtimes"])),
            "database_connectors": sorted(list(app_scanned["database_connectors"])),
        },
    }
