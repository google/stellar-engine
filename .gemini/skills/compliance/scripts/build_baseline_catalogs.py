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

"""Deterministically generate normalized baseline JSON files from official OSCAL profiles,
NIST SP 800-53 Rev 5 catalog, DISA CSP SRG V1R7 Table D-1, and CNSSI No. 1253 (2022).

Never hand-types control lists or parameter values. Records full provenance and SHA-256 digests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

RETRIEVAL_DATE = "2026-10-15"

_INSERT_PARAM_RE = re.compile(r"\{\{\s*insert:\s*param,\s*([^\s}]+)\s*\}\}")
_MD_ESCAPE_RE = re.compile(r"\\([*\[\]&])")
_WHITESPACE_RUN_RE = re.compile(r"\s*\n+\s*|\s{2,}")


def sha256_file(path: Path) -> str:
    """Compute hex SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_oscal_prose(text: Optional[str]) -> str:
    """Unescape OSCAL Markdown backslash escapes and collapse multi-line whitespace."""
    if not text:
        return ""
    cleaned = _MD_ESCAPE_RE.sub(r"\1", str(text))
    cleaned = _WHITESPACE_RUN_RE.sub(" ", cleaned)
    return cleaned.strip()


def resolve_param_inserts(
    text: str,
    param_values: Dict[str, str],
    param_labels: Dict[str, str],
) -> str:
    """Recursively resolve OSCAL ``{{ insert: param, <id> }}`` references."""
    current = clean_oscal_prose(text)
    for _ in range(6):
        def _repl(match: re.Match[str]) -> str:
            pid = match.group(1).strip()
            if pid in param_values and param_values[pid]:
                return param_values[pid]
            lbl = param_labels.get(pid, pid)
            lbl_clean = re.sub(r"^organization-defined\s+", "", lbl, flags=re.IGNORECASE)
            return f"organization-defined {lbl_clean}"

        updated = _INSERT_PARAM_RE.sub(_repl, current)
        if updated == current:
            break
        current = clean_oscal_prose(updated)
    return current


def from_oscal_id(oscal_cid: str) -> str:
    """Convert OSCAL control id (e.g. 'ac-2.1') to canonical NIST ID ('AC-2(1)')."""
    m = re.match(r"^([a-z]{2})-0*(\d+)(?:\.0*(\d+))?$", oscal_cid.strip().lower())
    if not m:
        raise ValueError(f"Unrecognized OSCAL control ID: {oscal_cid!r}")
    fam, num, enh = m.groups()
    return f"{fam.upper()}-{int(num)}" + (f"({int(enh)})" if enh else "")


def to_oscal_id(ctrl_id: str) -> str:
    """Convert canonical NIST ID ('AC-2(1)') to OSCAL control id ('ac-2.1')."""
    m = re.match(r"^([A-Z]{2})-0*(\d+)(?:\(0*(\d+)\))?$", ctrl_id.strip().upper())
    if not m:
        raise ValueError(f"Unrecognized NIST control ID: {ctrl_id!r}")
    fam, num, enh = m.groups()
    return f"{fam.lower()}-{int(num)}" + (f".{int(enh)}" if enh else "")


def ctrl_sort_key(ctrl_id: str) -> Tuple[str, int, int]:
    """Return canonical sort key (family, base_num, enhancement_num)."""
    m = re.match(r"^([A-Z]{2})-(\d+)(?:\((\d+)\))?$", ctrl_id)
    if not m:
        return (ctrl_id, 0, 0)
    return (m.group(1), int(m.group(2)), int(m.group(3) or 0))


def param_to_ctrl_id(param_id: str) -> str:
    """Map an OSCAL/ODP param-id ('ac-01_odp.05', 'ac-02.02_odp.01') to canonical control ID."""
    m = re.match(r"^([a-z]{2})-0*(\d+)(?:\.0*(\d+))?_(?:odp|prm)(?:[._]\d+)?$", param_id.strip().lower())
    if not m:
        raise ValueError(f"Cannot map param_id to control: {param_id!r}")
    fam, num, enh = m.groups()
    return f"{fam.upper()}-{int(num)}" + (f"({int(enh)})" if enh else "")


def load_nist_catalog(refdata_dir: Path) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
    """Load NIST SP 800-53 Rev 5.2.0 catalog metadata and parameter slots per control."""
    cat_path = refdata_dir / "nist_800_53_r5_catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))["catalog"]
    controls: Dict[str, Dict[str, Any]] = {}
    param_labels: Dict[str, str] = {}

    def collect_raw_labels(c: Dict[str, Any]) -> None:
        for p in c.get("params", []):
            pid = p["id"]
            if "_prm" in pid:
                continue
            lbl = clean_oscal_prose(p.get("label"))
            if lbl:
                param_labels[pid] = lbl
        for sub in c.get("controls", []):
            collect_raw_labels(sub)

    for grp in cat["groups"]:
        for ctrl in grp.get("controls", []):
            collect_raw_labels(ctrl)

    def walk(c: Dict[str, Any], family_id: str, parent_title: Optional[str] = None) -> None:
        cid = from_oscal_id(c["id"])
        props = {p["name"]: p.get("value") for p in c.get("props", [])}
        params = []
        for p in c.get("params", []):
            pid = p["id"]
            if "_prm" in pid:
                continue
            p_label = clean_oscal_prose(p.get("label"))
            if not p_label and "select" in p:
                choices = [
                    resolve_param_inserts(str(ch), {}, param_labels)
                    for ch in p["select"].get("choice", [])
                ]
                how_many = p["select"].get("how-many", "one")
                p_label = f"Selection ({how_many}): " + "; ".join(choices)
            p_label = resolve_param_inserts(p_label or "parameter", {}, param_labels)
            param_labels[pid] = p_label
            params.append({
                "param_id": pid,
                "label": p_label,
            })
        controls[cid] = {
            "control_id": cid,
            "oscal_id": c["id"],
            "family": family_id.upper(),
            "title": c["title"],
            "full_title": f"{parent_title} | {c['title']}" if parent_title else c["title"],
            "withdrawn": props.get("status") == "withdrawn",
            "catalog_params": params,
        }
        for sub in c.get("controls", []):
            walk(sub, family_id, c["title"])

    for grp in cat["groups"]:
        fam = grp["id"]
        for ctrl in grp.get("controls", []):
            walk(ctrl, fam, None)
    return controls, param_labels


def extract_fedramp_resolved_metadata(
    resolved_cat_path: Path,
    catalog_param_labels: Dict[str, str],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
    """Extract parameter labels and FedRAMP additional guidance from a FedRAMP resolved profile catalog."""
    cat = json.loads(resolved_cat_path.read_text(encoding="utf-8"))["catalog"]
    param_meta: Dict[str, Dict[str, Any]] = {}
    guidance_by_ctrl: Dict[str, str] = {}

    def walk(c: Dict[str, Any]) -> None:
        cid = from_oscal_id(c["id"])
        for p in c.get("params", []):
            pid = p["id"]
            if "_prm" in pid:
                continue
            label = clean_oscal_prose(p.get("label"))
            if not label:
                for pr in p.get("props", []):
                    if pr.get("name") == "alt-label":
                        label = clean_oscal_prose(pr.get("value"))
                        break
            if label:
                label = resolve_param_inserts(label, {}, catalog_param_labels)
            sp80053a_label = None
            for pr in p.get("props", []):
                if pr.get("name") == "label" and pr.get("class") == "sp800-53a":
                    sp80053a_label = clean_oscal_prose(pr.get("value"))
                    break
            guidelines = [
                resolve_param_inserts(g.get("prose", ""), {}, catalog_param_labels)
                for g in p.get("guidelines", [])
                if g.get("prose")
            ]
            param_meta[pid] = {
                "control_id": cid,
                "label": label or None,
                "sp800_53a_label": sp80053a_label,
                "guideline": " ".join(guidelines) if guidelines else None,
            }

        fr_parts: List[str] = []

        def collect_fr_parts(parts: List[Dict[str, Any]]) -> None:
            for pt in parts:
                pid_str = pt.get("id", "")
                if "_fr" in pid_str:
                    prose = clean_oscal_prose(pt.get("prose", ""))
                    title = clean_oscal_prose(pt.get("title", ""))
                    if prose:
                        prose_resolved = resolve_param_inserts(prose, {}, catalog_param_labels)
                        fr_parts.append(f"{title}: {prose_resolved}" if title else prose_resolved)
                collect_fr_parts(pt.get("parts", []))

        collect_fr_parts(c.get("parts", []))
        if fr_parts:
            guidance_by_ctrl[cid] = " ".join(fr_parts)
        for sub in c.get("controls", []):
            walk(sub)

    for grp in cat["groups"]:
        for ctrl in grp.get("controls", []):
            walk(ctrl)
    return param_meta, guidance_by_ctrl


def _extract_profile_control_ids(prof_obj: Dict[str, Any]) -> List[str]:
    """Extracts sorted normalized control IDs from an OSCAL profile imports block."""
    control_ids: List[str] = []
    for imp in prof_obj.get("imports", []):
        for inc in imp.get("include-controls", []):
            for wid in inc.get("with-ids", []):
                control_ids.append(from_oscal_id(wid))
    return sorted(set(control_ids), key=ctrl_sort_key)


def _extract_set_param_values(sp: Dict[str, Any], raw_val_map: Dict[str, str], merged_labels: Dict[str, str], resolve: bool) -> List[str]:
    """Collects cleaned or resolved parameter constraint and value strings from one set-parameter entry."""
    vals: List[str] = []
    for c in sp.get("constraints", []):
        desc = c.get("description")
        if desc:
            vals.append(resolve_param_inserts(desc, raw_val_map, merged_labels) if resolve else clean_oscal_prose(desc))
    for v in sp.get("values", []):
        if v:
            vals.append(resolve_param_inserts(str(v), raw_val_map, merged_labels) if resolve else clean_oscal_prose(str(v)))
    return vals


def _build_fedramp_raw_val_map(raw_set_params: List[Dict[str, Any]], merged_labels: Dict[str, str]) -> Dict[str, str]:
    """Builds and iteratively resolves the raw parameter-value lookup map for a FedRAMP profile."""
    raw_val_map: Dict[str, str] = {}
    for sp in raw_set_params:
        pid = sp["param-id"]
        if "_prm" in pid:
            continue
        raw_val_map[pid] = "; ".join(_extract_set_param_values(sp, {}, merged_labels, resolve=False))
    for _ in range(4):
        for pid in list(raw_val_map.keys()):
            raw_val_map[pid] = resolve_param_inserts(raw_val_map[pid], raw_val_map, merged_labels)
    return raw_val_map


def _build_fedramp_parameters(
    raw_set_params: List[Dict[str, Any]],
    control_ids: List[str],
    param_meta: Dict[str, Dict[str, Any]],
    raw_val_map: Dict[str, str],
    merged_labels: Dict[str, str],
    level: str,
    prof_name: str,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[Dict[str, Any]]], Dict[str, str]]:
    """Builds parameters, parameters_by_control, and formatted_rows for a FedRAMP profile."""
    parameters: Dict[str, Dict[str, Any]] = {}
    params_by_control: Dict[str, List[Dict[str, Any]]] = {cid: [] for cid in control_ids}
    source_str = f"FedRAMP Rev 5 {level.title()} Baseline Profile ({prof_name})"
    for sp in raw_set_params:
        pid = sp["param-id"]
        if "_prm" in pid:
            continue
        cid = param_to_ctrl_id(pid)
        values = _extract_set_param_values(sp, raw_val_map, merged_labels, resolve=True)
        p_info = param_meta.get(pid, {})
        entry = {
            "param_id": pid,
            "control_id": cid,
            "label": p_info.get("label"),
            "sp800_53a_label": p_info.get("sp800_53a_label"),
            "value": "; ".join(values),
            "raw_values": values,
            "source": source_str,
        }
        parameters[pid] = entry
        params_by_control.setdefault(cid, []).append(entry)

    formatted_rows: Dict[str, str] = {}
    for cid, plist in params_by_control.items():
        if plist:
            chunks = [
                f"`{p['param_id']}`" + (f" ({p['label']})" if p.get("label") else "") + f": {p['value']}"
                for p in plist
            ]
            formatted_rows[cid] = "; ".join(chunks)
    return parameters, params_by_control, formatted_rows


def normalize_fedramp_profile(
    level: str,
    refdata_dir: Path,
    catalog_param_labels: Dict[str, str],
) -> Dict[str, Any]:
    """Normalize a FedRAMP Rev 5 OSCAL profile + resolved catalog."""
    prof_path = refdata_dir / f"FedRAMP_rev5_{level}-baseline_profile.json"
    res_path = refdata_dir / f"FedRAMP_rev5_{level}-baseline-resolved-profile_catalog.json"
    prof_obj = json.loads(prof_path.read_text(encoding="utf-8"))["profile"]
    meta = prof_obj.get("metadata", {})
    param_meta, guidance_by_ctrl = extract_fedramp_resolved_metadata(res_path, catalog_param_labels)

    merged_labels = dict(catalog_param_labels)
    for pid, pinfo in param_meta.items():
        if pinfo.get("label"):
            merged_labels[pid] = pinfo["label"]

    control_ids = _extract_profile_control_ids(prof_obj)
    raw_set_params = prof_obj.get("modify", {}).get("set-parameters", [])
    raw_val_map = _build_fedramp_raw_val_map(raw_set_params, merged_labels)
    parameters, params_by_control, formatted_rows = _build_fedramp_parameters(
        raw_set_params, control_ids, param_meta, raw_val_map, merged_labels, level, prof_path.name
    )
    allowed = set(control_ids)
    filtered_guidance = {
        cid: resolve_param_inserts(g, raw_val_map, merged_labels)
        for cid, g in sorted(guidance_by_ctrl.items(), key=lambda kv: ctrl_sort_key(kv[0]))
        if cid in allowed
    }

    return {
        "regime_id": f"fedramp_{level.lower()}",
        "display_name": f"FedRAMP {level.title()}",
        "framework": "FedRAMP Rev. 5",
        "impact_level": level.title(),
        "fips_199_impacts": {
            "confidentiality": level.title(),
            "integrity": level.title(),
            "availability": level.title(),
        },
        "provenance": {
            "profile_file": prof_path.name,
            "profile_sha256": sha256_file(prof_path),
            "profile_url": (
                "https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/"
                f"383977291aad960b0811faf6ebf5a893b0811f7f/baselines/rev5/json/{prof_path.name}"
            ),
            "resolved_catalog_file": res_path.name,
            "resolved_catalog_sha256": sha256_file(res_path),
            "resolved_catalog_url": (
                "https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/"
                f"383977291aad960b0811faf6ebf5a893b0811f7f/baselines/rev5/json/{res_path.name}"
            ),
            "upstream_repo": "https://github.com/OSCAL-Foundation/fedramp-resources",
            "upstream_commit": "383977291aad960b0811faf6ebf5a893b0811f7f",
            "version": meta.get("version"),
            "oscal_version": meta.get("oscal-version"),
            "last_modified": meta.get("last-modified"),
            "retrieved_at": RETRIEVAL_DATE,
            "license": "CC0-1.0 / U.S. Government Public Domain (17 U.S.C. 105)",
        },
        "control_count": len(control_ids),
        "base_control_count": sum(1 for c in control_ids if "(" not in c),
        "enhancement_count": sum(1 for c in control_ids if "(" in c),
        "parameter_count": len(parameters),
        "controls_with_parameters_count": len(formatted_rows),
        "control_ids": control_ids,
        "parameters": parameters,
        "parameters_by_control": {k: v for k, v in params_by_control.items() if v},
        "guidance_by_control": filtered_guidance,
        "formatted_parameter_rows": formatted_rows,
    }


def normalize_nist_profile(
    level: str,
    refdata_dir: Path,
    nist_cat: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Normalize a NIST SP 800-53B OSCAL profile (LOW, MODERATE, HIGH, PRIVACY)."""
    prof_path = refdata_dir / f"NIST_SP-800-53_rev5_{level}-baseline_profile.json"
    prof_obj = json.loads(prof_path.read_text(encoding="utf-8"))["profile"]
    meta = prof_obj.get("metadata", {})

    control_ids: List[str] = []
    for imp in prof_obj.get("imports", []):
        for inc in imp.get("include-controls", []):
            for wid in inc.get("with-ids", []):
                control_ids.append(from_oscal_id(wid))
    control_ids = sorted(set(control_ids), key=ctrl_sort_key)

    parameters: Dict[str, Dict[str, Any]] = {}
    odp_placeholders_by_control: Dict[str, List[Dict[str, str]]] = {}
    formatted_rows: Dict[str, str] = {}
    total_slots = 0
    for cid in control_ids:
        c_meta = nist_cat.get(cid, {})
        slots = c_meta.get("catalog_params", [])
        if slots:
            odp_placeholders_by_control[cid] = []
            chunks = []
            for s in slots:
                total_slots += 1
                clean_lbl = re.sub(r"^organization-defined\s+", "", s["label"], flags=re.IGNORECASE).strip()
                marker = f"[CONFIG_REQUIRED: Organization-defined {clean_lbl} ({s['param_id']})]"
                entry = {
                    "param_id": s["param_id"],
                    "control_id": cid,
                    "label": clean_lbl,
                    "value": marker,
                    "source": f"NIST SP 800-53B {level.title()} Baseline Profile ({prof_path.name})",
                }
                parameters[s["param_id"]] = entry
                odp_placeholders_by_control[cid].append(entry)
                chunks.append(f"`{s['param_id']}` ({clean_lbl}): {marker}")
            formatted_rows[cid] = "; ".join(chunks)

    return {
        "regime_id": f"fisma_{level.lower()}" if level != "PRIVACY" else "nist_privacy_overlay",
        "display_name": f"FISMA {level.title()}" if level != "PRIVACY" else "NIST SP 800-53B Privacy Baseline",
        "framework": "NIST SP 800-53B",
        "impact_level": level.title(),
        "fips_199_impacts": (
            {
                "confidentiality": level.title(),
                "integrity": level.title(),
                "availability": level.title(),
            }
            if level != "PRIVACY"
            else None
        ),
        "provenance": {
            "profile_file": prof_path.name,
            "profile_sha256": sha256_file(prof_path),
            "profile_url": (
                "https://raw.githubusercontent.com/usnistgov/oscal-content/"
                f"78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/{prof_path.name}"
            ),
            "catalog_file": "nist_800_53_r5_catalog.json",
            "catalog_sha256": sha256_file(refdata_dir / "nist_800_53_r5_catalog.json"),
            "upstream_repo": "https://github.com/usnistgov/oscal-content",
            "upstream_commit": "78650f02ad9321bb7b817846f8fbd4f2bcd620de",
            "version": meta.get("version"),
            "oscal_version": meta.get("oscal-version"),
            "last_modified": meta.get("last-modified"),
            "retrieved_at": RETRIEVAL_DATE,
            "license": "CC0-1.0 / U.S. Government Public Domain (17 U.S.C. 105)",
        },
        "control_count": len(control_ids),
        "base_control_count": sum(1 for c in control_ids if "(" not in c),
        "enhancement_count": sum(1 for c in control_ids if "(" in c),
        "parameter_count": 0,
        "organization_defined_slot_count": total_slots,
        "controls_with_parameters_count": len(formatted_rows),
        "control_ids": control_ids,
        "parameters": parameters,
        "parameters_by_control": odp_placeholders_by_control,
        "guidance_by_control": {},
        "formatted_parameter_rows": formatted_rows,
    }


# DISA Cloud Service Provider (CSP) SRG V1R7 (30 June 2026) Appendix D Table D-1
DISA_CSP_SRG_V1R7_TABLE_D1: Dict[str, Dict[str, Any]] = {
    "AC-7": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "EXPLICIT_SRG",
        "srg_parameter_value": (
            "For privileged users, DoW requires an account lock after three unsuccessful attempts "
            "for Impact Levels 2/4/5 and after five unsuccessful attempts for accounts using a SIPR token. "
            "All levels must be configured to require an administrator unlock the account. "
            "For nonprivileged users, if rate limiting, DoW will allow 10 attempts with the account "
            "automatically unlocked after 30 minutes. If rate limiting is not used, normal DSPAV will be required."
        ),
        "srg_page": "p. 114",
    },
    "AU-5(1)": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "USE_FEDRAMP",
        "srg_parameter_value": "CSP/CSO may use FedRAMP value.",
        "srg_page": "p. 114",
    },
    "CM-7(5)": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 114",
    },
    "IA-5(1)": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 114",
    },
    "PE-15": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 114",
    },
    "PS-3(4)": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "EXPLICIT_SRG",
        "srg_parameter_value": (
            "All information systems. Users: U.S. citizens, U.S. nationals, or U.S. persons, foreign personnel "
            "as allowed by current DoW polices with AO approval. Administrators: U.S. citizens, U.S. nationals, "
            "or U.S. persons. Refer to Section 5.5.2, CSP Personnel Requirements, for more information."
        ),
        "srg_page": "pp. 114-115",
    },
    "MA-5(1)": {
        "levels": ["IL4"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 115",
    },
    "MA-5(2)": {"levels": ["IL6"], "rule": "CONTROL_ADDITION_ONLY", "srg_parameter_value": None, "srg_page": "p. 115"},
    "MA-5(3)": {"levels": ["IL6"], "rule": "CONTROL_ADDITION_ONLY", "srg_parameter_value": None, "srg_page": "p. 115"},
    "MA-5(4)": {"levels": ["IL6"], "rule": "CONTROL_ADDITION_ONLY", "srg_parameter_value": None, "srg_page": "p. 115"},
    "MA-5(5)": {"levels": ["IL4", "IL5", "IL6"], "rule": "CONTROL_ADDITION_ONLY", "srg_parameter_value": None, "srg_page": "p. 115"},
    "MA-6": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "USE_FEDRAMP",
        "srg_parameter_value": "CSP/CSO may use FedRAMP value.",
        "srg_page": "p. 115",
    },
    "PS-4": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "USE_FEDRAMP",
        "srg_parameter_value": "CSP/CSO may use FedRAMP value.",
        "srg_page": "p. 115",
    },
    "SA-4(5)": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 115",
    },
    "SA-9(1)": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 115",
    },
    "SA-9(3)": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 115",
    },
    "SA-9(5)": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "EXPLICIT_SRG",
        "srg_parameter_value": (
            "SA-9 (5)-1 [information processing, information or data, AND system services]. "
            "SA-9 (5)-2 [U.S./U.S. Territories or geographic locations where there is U.S. jurisdiction]. "
            "SA-9 (5)-3 [all data, systems, or services]."
        ),
        "srg_page": "p. 115",
    },
    "SA-9(6)": {"levels": ["IL4", "IL5", "IL6"], "rule": "CONTROL_ADDITION_ONLY", "srg_parameter_value": None, "srg_page": "p. 115"},
    "SA-9(7)": {"levels": ["IL4", "IL5", "IL6"], "rule": "CONTROL_ADDITION_ONLY", "srg_parameter_value": None, "srg_page": "p. 115"},
    "SA-9(8)": {"levels": ["IL4", "IL5", "IL6"], "rule": "CONTROL_ADDITION_ONLY", "srg_parameter_value": None, "srg_page": "p. 115"},
    "SC-12(6)": {"levels": ["IL4", "IL5", "IL6"], "rule": "CONTROL_ADDITION_ONLY", "srg_parameter_value": None, "srg_page": "p. 115"},
    "SC-17": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "EXPLICIT_SRG",
        "srg_parameter_value": "DODI 8520.02, Public Key Infrastructure (PKI) and Public Key Enabling (PKE).",
        "srg_page": "p. 115",
    },
    "SC-18": {"levels": ["IL4", "IL5", "IL6"], "rule": "CONTROL_ADDITION_ONLY", "srg_parameter_value": None, "srg_page": "p. 115"},
    "SC-18(2)": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 115",
    },
    "SC-18(3)": {
        "levels": ["IL5", "IL6"],
        "rule": "EXPLICIT_SRG",
        "srg_parameter_value": (
            "Supplemental guidance: For the protection of the infrastructure supporting a CSO, CSPs are required "
            "to apply this control to their organizational IT systems and the infrastructure supporting their CSO(s). "
            "For the protection of Mission Owners, their end users, and networks, CSP CSOs must not support the "
            "downloading of mobile code, which is deemed unacceptable to DoW. "
            "Refer to Section 5.11, Mobile Code, for more information."
        ),
        "srg_page": "p. 115",
    },
    "SC-18(4)": {
        "levels": ["IL5", "IL6"],
        "rule": "EXPLICIT_SRG",
        "srg_parameter_value": (
            "Software applications such as but not limited to email, scriptable document/file editing applications "
            "that support documents with embedded code (e.g., Microsoft Office applications/documents), etc. "
            "Prompting the user for permission."
        ),
        "srg_page": "p. 115",
    },
    "SC-24": {
        "levels": ["IL4", "IL5", "IL6"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 115",
    },
    "SC-46": {
        "levels": ["CDS"],
        "rule": "DSPAV",
        "srg_parameter_value": "DSPAV must be used.",
        "srg_page": "p. 115",
    },
}


def _apply_srg_table_d1_overrides(
    srg_ctrls: Set[str],
    base_profile: Dict[str, Any],
    fallback_profile: Optional[Dict[str, Any]],
    cnssi_pvs: Dict[str, str],
    parameters: Dict[str, Dict[str, Any]],
    params_by_control: Dict[str, List[Dict[str, Any]]],
    formatted_rows: Dict[str, str],
    base_label: str,
) -> Dict[str, Dict[str, Any]]:
    """Applies DISA CSP SRG V1R7 Table D-1 parameter rules to parameters and formatted_rows."""
    dod_overrides: Dict[str, Dict[str, Any]] = {}
    for cid in sorted(srg_ctrls, key=ctrl_sort_key):
        spec = DISA_CSP_SRG_V1R7_TABLE_D1[cid]
        rule = spec["rule"]
        src_str = f"DISA Cloud Service Provider SRG V1R7 (30 June 2026) Appendix D Table D-1 ({spec['srg_page']})"
        if rule == "EXPLICIT_SRG":
            val = spec["srg_parameter_value"]
            dod_overrides[cid] = {"control_id": cid, "rule": rule, "value": val, "source": src_str}
            formatted_rows[cid] = f"DISA CSP SRG V1R7 Table D-1: {val}"
            pid = f"{to_oscal_id(cid)}_srg_d1"
            p_entry = {"param_id": pid, "control_id": cid, "label": "DISA CSP SRG V1R7 Table D-1 parameter", "value": val, "source": src_str}
            parameters[pid] = p_entry
            params_by_control[cid] = [p_entry]
        elif rule == "USE_FEDRAMP":
            if cid in base_profile["formatted_parameter_rows"]:
                fr_row = base_profile["formatted_parameter_rows"][cid]
                src_label = base_label
            elif fallback_profile is not None:
                fr_row = fallback_profile["formatted_parameter_rows"].get(cid, "")
                src_label = "FedRAMP High"
                if cid in fallback_profile["parameters_by_control"]:
                    params_by_control[cid] = list(fallback_profile["parameters_by_control"][cid])
                    for pe in fallback_profile["parameters_by_control"][cid]:
                        parameters[pe["param_id"]] = pe
            else:
                fr_row, src_label = "", base_label
            dod_overrides[cid] = {"control_id": cid, "rule": rule, "value": f"CSP/CSO may use FedRAMP value ({src_label}): {fr_row}", "source": src_str}
            formatted_rows[cid] = fr_row
        elif rule == "DSPAV":
            cpv = cnssi_pvs.get(cid)
            val = (
                f"[CONFIG_REQUIRED: DoD organization-defined parameter value per DoW RMF TAG DSPAV "
                f"(https://rmfks.osd.mil); CNSSI No. 1253 (2022) Appendix D parameter value: {cpv}]"
                if cpv
                else "[CONFIG_REQUIRED: DoD organization-defined parameter value per DoW RMF TAG DSPAV — https://rmfks.osd.mil ]"
            )
            dod_overrides[cid] = {"control_id": cid, "rule": rule, "value": val, "cnssi_1253_fallback": cpv, "source": src_str}
            formatted_rows[cid] = val
            pid = f"{to_oscal_id(cid)}_dspav"
            p_entry = {"param_id": pid, "control_id": cid, "label": "DoW RMF TAG DSPAV parameter", "value": val, "source": src_str}
            parameters[pid] = p_entry
            params_by_control[cid] = [p_entry]
        elif rule == "CONTROL_ADDITION_ONLY" and fallback_profile is not None:
            cpv = cnssi_pvs.get(cid)
            if cpv:
                val = f"CNSSI No. 1253 (2022) Appendix D: {cpv}"
                dod_overrides[cid] = {
                    "control_id": cid,
                    "rule": "CNSSI_1253_PV",
                    "value": val,
                    "source": "DISA CSP SRG V1R7 Table D-1 + CNSSI No. 1253 (29 July 2022) Appendix D",
                }
                formatted_rows[cid] = val
                pid = f"{to_oscal_id(cid)}_cnssi1253"
                p_entry = {
                    "param_id": pid,
                    "control_id": cid,
                    "label": "CNSSI No. 1253 (2022) Appendix D parameter",
                    "value": val,
                    "source": "CNSSI No. 1253 (29 July 2022) Appendix D",
                }
                parameters[pid] = p_entry
                params_by_control[cid] = [p_entry]
    return dod_overrides


def build_dod_il4_baseline(
    fr_mod: Dict[str, Any],
    fr_high: Dict[str, Any],
    cnssi_pvs: Dict[str, str],
    refdata_dir: Path,
) -> Dict[str, Any]:
    """Build normalized DoD IL4 baseline (FedRAMP Moderate + DISA CSP SRG V1R7 Table D-1 IL4 overlay)."""
    srg_il4_ctrls = {cid for cid, spec in DISA_CSP_SRG_V1R7_TABLE_D1.items() if "IL4" in spec["levels"]}
    fr_mod_set = set(fr_mod["control_ids"])
    il4_additions = sorted(srg_il4_ctrls - fr_mod_set, key=ctrl_sort_key)
    all_il4_ctrls = sorted(fr_mod_set | srg_il4_ctrls, key=ctrl_sort_key)

    parameters: Dict[str, Dict[str, Any]] = dict(fr_mod["parameters"])
    params_by_control: Dict[str, List[Dict[str, Any]]] = {
        cid: list(entries) for cid, entries in fr_mod["parameters_by_control"].items()
    }
    guidance_by_control: Dict[str, str] = dict(fr_mod.get("guidance_by_control", {}))
    guidance_by_control["SA-9(8)"] = (
        "CNSSI 1253 Guidance: Refer to CNSSP No. 32 for cloud processing and storage location requirements "
        "within U.S. jurisdiction."
    )
    formatted_rows: Dict[str, str] = dict(fr_mod["formatted_parameter_rows"])
    dod_overrides = _apply_srg_table_d1_overrides(
        srg_il4_ctrls, fr_mod, fr_high, cnssi_pvs, parameters, params_by_control, formatted_rows, "FedRAMP Moderate"
    )

    srg_txt_path = refdata_dir / "U_Cloud_Service_Provider_V1R7_SRG.txt"
    return {
        "regime_id": "dod_il4",
        "display_name": "DoD IL4",
        "framework": "DISA Cloud Service Provider SRG V1R7 (DoD IL4)",
        "impact_level": "IL4",
        "fips_199_impacts": {
            "confidentiality": "Moderate",
            "integrity": "Moderate",
            "availability": "Moderate",
            "supported_categorizations": ["MMx (Moderate/Moderate/x)"],
        },
        "provenance": {
            "base_profile": fr_mod["provenance"],
            "overlay_document": "DISA Cloud Service Provider (CSP) Security Requirements Guide (SRG) Version 1, Release 7 (30 June 2026)",
            "overlay_url": "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_Cloud_Computing_Y26M06_SRG.zip",
            "overlay_extracted_text_sha256": sha256_file(srg_txt_path),
            "cnssi_1253_document": "CNSSI No. 1253, Categorization and Control Selection for National Security Systems (29 July 2022)",
            "cnssi_1253_url": "https://www.cnss.gov/CNSS/issuances/Instructions.cfm",
            "cnssi_1253_pdf_sha256": sha256_file(refdata_dir / "CNSSI_1253_2022.pdf"),
            "retrieved_at": RETRIEVAL_DATE,
            "license": "U.S. Government Public Domain (17 U.S.C. 105)",
        },
        "control_count": len(all_il4_ctrls),
        "base_control_count": sum(1 for c in all_il4_ctrls if "(" not in c),
        "enhancement_count": sum(1 for c in all_il4_ctrls if "(" in c),
        "parameter_count": len(parameters),
        "controls_with_parameters_count": len(formatted_rows),
        "fedramp_moderate_base_count": len(fr_mod_set),
        "srg_table_d1_il4_total_controls": len(srg_il4_ctrls),
        "srg_table_d1_il4_additions": il4_additions,
        "srg_table_d1_excluded_il5_il6_only": ["MA-5(2)", "MA-5(3)", "MA-5(4)", "SC-18(3)", "SC-18(4)", "SC-46"],
        "control_ids": all_il4_ctrls,
        "parameters": parameters,
        "parameters_by_control": {k: v for k, v in params_by_control.items() if v},
        "guidance_by_control": guidance_by_control,
        "dod_parameter_overrides": dod_overrides,
        "formatted_parameter_rows": formatted_rows,
    }


def build_dod_il5_baseline(
    fr_high: Dict[str, Any],
    cnssi_pvs: Dict[str, str],
    refdata_dir: Path,
) -> Dict[str, Any]:
    """Build normalized DoD IL5 baseline (FedRAMP High + DISA CSP SRG V1R7 Table D-1 IL5 + CNSSI 1253 HHx '+' & Privacy)."""
    g2c_class = json.loads((refdata_dir / "il5_control_classification.json").read_text(encoding="utf-8"))
    existing_611 = {item["control_id"] for item in g2c_class}
    cnssi_parsed = json.loads((refdata_dir / "cnssi_1253_2022_parsed.json").read_text(encoding="utf-8"))["controls"]
    srg_il5_ctrls = {cid for cid, spec in DISA_CSP_SRG_V1R7_TABLE_D1.items() if "IL5" in spec["levels"]}
    cnssi_plus_hhx = {
        cid
        for cid, c in cnssi_parsed.items()
        if any(c["baselines"].get(col) == "+" for col in ("C_H", "I_H", "privacy"))
    }
    cnssi_priv_x = {cid for cid, c in cnssi_parsed.items() if c["baselines"].get("privacy") in ("X", "+")}
    missing_d1 = srg_il5_ctrls - existing_611
    missing_cnssi_plus = cnssi_plus_hhx - existing_611
    missing_cnssi_priv = cnssi_priv_x - existing_611
    all_il5_ctrls = sorted(existing_611 | missing_d1 | missing_cnssi_plus | missing_cnssi_priv, key=ctrl_sort_key)

    parameters: Dict[str, Dict[str, Any]] = dict(fr_high["parameters"])
    params_by_control: Dict[str, List[Dict[str, Any]]] = {
        cid: list(entries) for cid, entries in fr_high["parameters_by_control"].items()
    }
    guidance_by_control: Dict[str, str] = dict(fr_high.get("guidance_by_control", {}))
    guidance_by_control["SA-9(8)"] = (
        "CNSSI 1253 Guidance: Refer to CNSSP No. 32 for cloud processing and storage location requirements "
        "within U.S. jurisdiction."
    )
    formatted_rows: Dict[str, str] = dict(fr_high["formatted_parameter_rows"])
    dod_overrides = _apply_srg_table_d1_overrides(
        srg_il5_ctrls, fr_high, None, cnssi_pvs, parameters, params_by_control, formatted_rows, "FedRAMP High"
    )

    fr_high_set = set(fr_high["control_ids"])
    for cid in all_il5_ctrls:
        if cid in dod_overrides:
            continue
        cpv = cnssi_pvs.get(cid)
        if not cpv:
            continue
        if cid not in fr_high_set:
            val = f"CNSSI No. 1253 (2022) Appendix D: {cpv}"
            dod_overrides[cid] = {
                "control_id": cid,
                "rule": "CNSSI_1253_PV",
                "value": val,
                "source": "CNSSI No. 1253 (29 July 2022) Appendix D Table D-1..D-20",
            }
            formatted_rows[cid] = val
            pid = f"{to_oscal_id(cid)}_cnssi1253"
            p_entry = {
                "param_id": pid,
                "control_id": cid,
                "label": "CNSSI No. 1253 (2022) Appendix D parameter",
                "value": val,
                "source": "CNSSI No. 1253 (29 July 2022) Appendix D Table D-1..D-20",
            }
            parameters[pid] = p_entry
            params_by_control[cid] = [p_entry]
        elif cid == "AC-2(13)":
            val = "CNSSI No. 1253 (2022) Table D-1: 30 minutes (FedRAMP High: one (1) hour)"
            dod_overrides[cid] = {
                "control_id": cid,
                "rule": "CNSSI_1253_STRICTER",
                "value": val,
                "source": "CNSSI No. 1253 (29 July 2022) Appendix D Table D-1 (p. D-5)",
            }
            formatted_rows[cid] = val
            pid = "ac-02.13_odp.01"
            p_entry = {
                "param_id": pid,
                "control_id": cid,
                "label": "time period",
                "value": val,
                "source": "CNSSI No. 1253 (29 July 2022) Appendix D Table D-1 (p. D-5)",
            }
            parameters[pid] = p_entry
            params_by_control[cid] = [p_entry]

    srg_txt_path = refdata_dir / "U_Cloud_Service_Provider_V1R7_SRG.txt"
    return {
        "regime_id": "dod_il5",
        "display_name": "DoD IL5",
        "framework": "DISA Cloud Service Provider SRG V1R7 + CNSSI No. 1253 (DoD IL5)",
        "impact_level": "IL5",
        "fips_199_impacts": {
            "confidentiality": "High",
            "integrity": "High",
            "availability": "High",
            "supported_categorizations": ["HHx (High/High/x)"],
        },
        "provenance": {
            "base_profile": fr_high["provenance"],
            "overlay_document": "DISA Cloud Service Provider (CSP) Security Requirements Guide (SRG) Version 1, Release 7 (30 June 2026)",
            "overlay_url": "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_Cloud_Computing_Y26M06_SRG.zip",
            "overlay_extracted_text_sha256": sha256_file(srg_txt_path),
            "cnssi_1253_document": "CNSSI No. 1253, Categorization and Control Selection for National Security Systems (29 July 2022)",
            "cnssi_1253_url": "https://www.cnss.gov/CNSS/issuances/Instructions.cfm",
            "cnssi_1253_pdf_sha256": sha256_file(refdata_dir / "CNSSI_1253_2022.pdf"),
            "retrieved_at": RETRIEVAL_DATE,
            "license": "U.S. Government Public Domain (17 U.S.C. 105)",
        },
        "control_count": len(all_il5_ctrls),
        "base_control_count": sum(1 for c in all_il5_ctrls if "(" not in c),
        "enhancement_count": sum(1 for c in all_il5_ctrls if "(" in c),
        "parameter_count": len(parameters),
        "controls_with_parameters_count": len(formatted_rows),
        "fedramp_high_base_count": len(fr_high_set),
        "srg_table_d1_il5_total_controls": len(srg_il5_ctrls),
        "srg_table_d1_il5_missing_at_head": sorted(missing_d1, key=ctrl_sort_key),
        "cnssi_1253_hhx_plus_missing_at_head": sorted(missing_cnssi_plus, key=ctrl_sort_key),
        "cnssi_1253_privacy_missing_at_head": sorted(missing_cnssi_priv, key=ctrl_sort_key),
        "control_ids": all_il5_ctrls,
        "parameters": parameters,
        "parameters_by_control": {k: v for k, v in params_by_control.items() if v},
        "guidance_by_control": guidance_by_control,
        "dod_parameter_overrides": dod_overrides,
        "formatted_parameter_rows": formatted_rows,
    }


def build_dod_il2_baseline(
    fr_mod: Dict[str, Any],
    refdata_dir: Path,
) -> Dict[str, Any]:
    """Build normalized DoD IL2 baseline (FedRAMP Moderate + 0 DISA CSP SRG V1R7 Table D-1 additions)."""
    all_il2_ctrls = list(fr_mod["control_ids"])
    parameters: Dict[str, Dict[str, Any]] = dict(fr_mod["parameters"])
    params_by_control: Dict[str, List[Dict[str, Any]]] = {
        cid: list(entries) for cid, entries in fr_mod["parameters_by_control"].items()
    }
    guidance_by_control: Dict[str, str] = dict(fr_mod.get("guidance_by_control", {}))
    formatted_rows: Dict[str, str] = dict(fr_mod["formatted_parameter_rows"])
    srg_txt_path = refdata_dir / "U_Cloud_Service_Provider_V1R7_SRG.txt"

    return {
        "regime_id": "dod_il2",
        "display_name": "DoD IL2",
        "framework": "DISA Cloud Service Provider SRG V1R7 (DoD IL2)",
        "impact_level": "IL2",
        "fips_199_impacts": {
            "confidentiality": "Low",
            "integrity": "Low",
            "availability": "Low",
            "supported_categorizations": ["LLx (Low/Low/x)", "MMx (Moderate/Moderate/x)"],
        },
        "provenance": {
            "base_profile": fr_mod["provenance"],
            "overlay_document": "DISA Cloud Service Provider (CSP) Security Requirements Guide (SRG) Version 1, Release 7 (30 June 2026)",
            "overlay_url": "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_Cloud_Computing_Y26M06_SRG.zip",
            "overlay_extracted_text_sha256": sha256_file(srg_txt_path),
            "retrieved_at": RETRIEVAL_DATE,
            "license": "U.S. Government Public Domain (17 U.S.C. 105)",
        },
        "control_count": len(all_il2_ctrls),
        "base_control_count": sum(1 for c in all_il2_ctrls if "(" not in c),
        "enhancement_count": sum(1 for c in all_il2_ctrls if "(" in c),
        "parameter_count": len(parameters),
        "controls_with_parameters_count": len(formatted_rows),
        "fedramp_moderate_base_count": len(all_il2_ctrls),
        "srg_table_d1_il2_additions": [],
        "control_ids": all_il2_ctrls,
        "parameters": parameters,
        "parameters_by_control": {k: v for k, v in params_by_control.items() if v},
        "guidance_by_control": guidance_by_control,
        "dod_parameter_overrides": {},
        "formatted_parameter_rows": formatted_rows,
    }


def build_dod_il6_baseline(
    fr_high: Dict[str, Any],
    dod_il5: Dict[str, Any],
    cnssi_pvs: Dict[str, str],
    refdata_dir: Path,
) -> Dict[str, Any]:
    """Build normalized DoD IL6 baseline (DoD IL5 + DISA CSP SRG V1R7 Table D-1 IL6 + CNSSI 1253 Classified Overlay)."""
    srg_il6_ctrls = {cid for cid, spec in DISA_CSP_SRG_V1R7_TABLE_D1.items() if "IL6" in spec["levels"]}
    il5_set = set(dod_il5["control_ids"])
    il6_additions = sorted(srg_il6_ctrls - il5_set, key=ctrl_sort_key)
    all_il6_ctrls = sorted(il5_set | srg_il6_ctrls, key=ctrl_sort_key)

    parameters: Dict[str, Dict[str, Any]] = dict(dod_il5["parameters"])
    params_by_control: Dict[str, List[Dict[str, Any]]] = {
        cid: list(entries) for cid, entries in dod_il5["parameters_by_control"].items()
    }
    guidance_by_control: Dict[str, str] = dict(dod_il5.get("guidance_by_control", {}))
    formatted_rows: Dict[str, str] = dict(dod_il5["formatted_parameter_rows"])
    dod_overrides: Dict[str, Dict[str, Any]] = dict(dod_il5.get("dod_parameter_overrides", {}))

    for cid in il6_additions:
        spec = DISA_CSP_SRG_V1R7_TABLE_D1[cid]
        if spec["rule"] == "CONTROL_ADDITION_ONLY":
            cpv = cnssi_pvs.get(cid)
            if cpv:
                val = f"CNSSI No. 1253 (2022) Appendix D: {cpv}"
                dod_overrides[cid] = {
                    "control_id": cid,
                    "rule": "CNSSI_1253_PV",
                    "value": val,
                    "source": "DISA CSP SRG V1R7 Table D-1 + CNSSI No. 1253 (29 July 2022) Appendix D",
                }
                formatted_rows[cid] = val
                pid = f"{to_oscal_id(cid)}_cnssi1253"
                p_entry = {
                    "param_id": pid,
                    "control_id": cid,
                    "label": "CNSSI No. 1253 (2022) Appendix D parameter",
                    "value": val,
                    "source": "CNSSI No. 1253 (29 July 2022) Appendix D",
                }
                parameters[pid] = p_entry
                params_by_control[cid] = [p_entry]

    srg_txt_path = refdata_dir / "U_Cloud_Service_Provider_V1R7_SRG.txt"
    return {
        "regime_id": "dod_il6",
        "display_name": "DoD IL6",
        "framework": "DISA Cloud Service Provider SRG V1R7 + CNSSI No. 1253 Classified Overlay (DoD IL6)",
        "impact_level": "IL6",
        "fips_199_impacts": {
            "confidentiality": "High",
            "integrity": "High",
            "availability": "High",
            "supported_categorizations": ["HHx (High/High/x) / Classified SECRET (SSx)"],
        },
        "provenance": {
            "base_profile": fr_high["provenance"],
            "overlay_document": "DISA Cloud Service Provider (CSP) Security Requirements Guide (SRG) Version 1, Release 7 (30 June 2026)",
            "overlay_url": "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/U_Cloud_Computing_Y26M06_SRG.zip",
            "overlay_extracted_text_sha256": sha256_file(srg_txt_path),
            "cnssi_1253_document": "CNSSI No. 1253, Categorization and Control Selection for National Security Systems (29 July 2022)",
            "cnssi_1253_url": "https://www.cnss.gov/CNSS/issuances/Instructions.cfm",
            "cnssi_1253_pdf_sha256": sha256_file(refdata_dir / "CNSSI_1253_2022.pdf"),
            "retrieved_at": RETRIEVAL_DATE,
            "license": "U.S. Government Public Domain (17 U.S.C. 105)",
        },
        "control_count": len(all_il6_ctrls),
        "base_control_count": sum(1 for c in all_il6_ctrls if "(" not in c),
        "enhancement_count": sum(1 for c in all_il6_ctrls if "(" in c),
        "parameter_count": len(parameters),
        "controls_with_parameters_count": len(formatted_rows),
        "dod_il5_base_count": len(il5_set),
        "srg_table_d1_il6_total_controls": len(srg_il6_ctrls),
        "srg_table_d1_il6_additions_over_il5": il6_additions,
        "control_ids": all_il6_ctrls,
        "parameters": parameters,
        "parameters_by_control": {k: v for k, v in params_by_control.items() if v},
        "guidance_by_control": guidance_by_control,
        "dod_parameter_overrides": dod_overrides,
        "formatted_parameter_rows": formatted_rows,
    }


CJIS_V6_PARAMETER_OVERRIDES: List[Dict[str, str]] = [
    {
        "control_id": "AC-7",
        "param_id": "ac-07_cjis",
        "label": "unsuccessful logon attempts",
        "value": (
            "five (5) consecutive invalid logon attempts by a user (locking the account for a minimum of "
            "ten [10] minutes or until unlocked by an administrator per FBI CJIS Security Policy Section 5.5 / AC-7)"
        ),
    },
    {
        "control_id": "AC-11",
        "param_id": "ac-11_odp.02",
        "label": "time period",
        "value": (
            "maximum thirty (30) minutes of inactivity for CJI access sessions (fifteen [15] minutes "
            "recommended in shared environments) per FBI CJIS Security Policy Section 5.5 / AC-11"
        ),
    },
    {
        "control_id": "AU-11",
        "param_id": "au-11_odp",
        "label": "time period",
        "value": (
            "minimum one (1) year (365 days) or longer per FBI CJIS Security Policy Section 5.4 / AU-11 "
            "and [CONFIG_REQUIRED: State CJIS Systems Agency (CSA) audit retention schedule]"
        ),
    },
    {
        "control_id": "IA-2",
        "param_id": "ia-02_cjis",
        "label": "multi-factor authentication requirement",
        "value": (
            "NIST SP 800-63B Authenticator Assurance Level 2 (AAL2) phishing-resistant multi-factor "
            "authentication (MFA) for all local, network, and remote access to Criminal Justice Information "
            "(CJI) per FBI CJIS Security Policy Section 5.6 / IA-2"
        ),
    },
    {
        "control_id": "IA-5",
        "param_id": "ia-05_cjis",
        "label": "authenticator management requirement",
        "value": (
            "AAL2 multi-factor authenticators and minimum 8-character password / passphrase policies "
            "verified against compromised credential lists per FBI CJIS Security Policy Section 5.6 / IA-5"
        ),
    },
    {
        "control_id": "IR-6",
        "param_id": "ir-06_odp.01",
        "label": "time period",
        "value": (
            "within one (1) hour of discovery to the [CONFIG_REQUIRED: State CJIS Systems Agency (CSA) "
            "Information Security Officer (ISO)] and FBI CJIS Division ISO per FBI CJIS Security Policy Section 5.3 / IR-6"
        ),
    },
    {
        "control_id": "PS-3",
        "param_id": "ps-03_odp.01",
        "label": "conditions requiring rescreening",
        "value": (
            "state of residency and national fingerprint-based criminal history record check (CHRI) via FBI "
            "IAFIS/NGI prior to granting unescorted physical or logical access to Criminal Justice Information "
            "(CJI), adjudicated by the [CONFIG_REQUIRED: State CJIS Systems Agency (CSA)] per FBI CJIS Security "
            "Policy Section 5.12 / PS-3"
        ),
    },
    {
        "control_id": "PS-3",
        "param_id": "ps-03_odp.02",
        "label": "frequency",
        "value": (
            "prior to initial CJI access and re-vetted per [CONFIG_REQUIRED: State CJIS Systems Agency (CSA) "
            "personnel rescreening frequency] and continuous criminal history rap-back monitoring where implemented"
        ),
    },
    {
        "control_id": "SC-8",
        "param_id": "sc-08_odp",
        "label": "transmission confidentiality and integrity",
        "value": (
            "confidentiality AND integrity using minimum TLS 1.2 (FIPS 140-2 / FIPS 140-3 validated cryptography, "
            "minimum 128-bit encryption) for all CJI transmitted outside physically secure locations per FBI CJIS "
            "Security Policy Section 5.10.1.2 / SC-8"
        ),
    },
    {
        "control_id": "SC-13",
        "param_id": "sc-13_odp.02",
        "label": "types of cryptography",
        "value": (
            "FIPS 140-2 or FIPS 140-3 validated cryptographic modules (minimum AES-128 for transit, AES-256 / "
            "FIPS 197 for CJI at rest with Customer-Managed Encryption Keys [CMEK]) per FBI CJIS Security Policy Section 5.10 / SC-13"
        ),
    },
    {
        "control_id": "SC-28",
        "param_id": "sc-28_odp.01",
        "label": "protection of information at rest",
        "value": (
            "confidentiality AND integrity of Criminal Justice Information (CJI) at rest using FIPS 140-2 / "
            "FIPS 140-3 validated AES-256 encryption with agency-controlled Customer-Managed Encryption Keys "
            "(CMEK) per FBI CJIS Security Policy Section 5.10.1.2.1 / SC-28"
        ),
    },
]


def build_cjis_baseline(
    fr_mod: Dict[str, Any],
    nist_mod: Dict[str, Any],
) -> Dict[str, Any]:
    """Build normalized CJIS baseline (NIST SP 800-53B / FedRAMP Moderate 323 controls + FBI CJIS v5.9.4/v6.0 overrides)."""
    all_cjis_ctrls = list(fr_mod["control_ids"])
    parameters: Dict[str, Dict[str, Any]] = dict(fr_mod["parameters"])
    params_by_control: Dict[str, List[Dict[str, Any]]] = {
        cid: list(entries) for cid, entries in fr_mod["parameters_by_control"].items()
    }
    formatted_rows: Dict[str, str] = dict(fr_mod["formatted_parameter_rows"])
    cjis_overrides: Dict[str, List[Dict[str, Any]]] = {}

    src_str = "FBI CJIS Security Policy v5.9.4 / v6.0 (CJISD-ITS-DOC-08140, NIST SP 800-53 Rev. 5 Harmonized)"
    for ov in CJIS_V6_PARAMETER_OVERRIDES:
        cid = ov["control_id"]
        pid = ov["param_id"]
        entry = {
            "param_id": pid,
            "control_id": cid,
            "label": ov["label"],
            "value": ov["value"],
            "source": src_str,
        }
        parameters[pid] = entry
        cjis_overrides.setdefault(cid, []).append(entry)

    for cid, ov_entries in cjis_overrides.items():
        existing = [e for e in params_by_control.get(cid, []) if e["param_id"] not in {x["param_id"] for x in ov_entries}]
        merged_list = existing + ov_entries
        params_by_control[cid] = merged_list
        chunks = []
        for p in merged_list:
            lbl = f" ({p['label']})" if p.get("label") else ""
            chunks.append(f"`{p['param_id']}`{lbl}: {p['value']}")
        formatted_rows[cid] = "; ".join(chunks)

    return {
        "regime_id": "cjis",
        "display_name": "CJIS",
        "framework": "FBI CJIS Security Policy v5.9.4 / v6.0 (NIST SP 800-53 Rev. 5 Moderate Harmonized)",
        "impact_level": "Moderate",
        "fips_199_impacts": {
            "confidentiality": "Moderate",
            "integrity": "Moderate",
            "availability": "Moderate",
        },
        "provenance": {
            "nist_800_53b_moderate_profile": nist_mod["provenance"],
            "fedramp_moderate_harmonized_profile": fr_mod["provenance"],
            "overlay_document": src_str,
            "overlay_url": "https://le.fbi.gov/cjis-division/cjis-security-policy-resource-center",
            "retrieved_at": RETRIEVAL_DATE,
            "license": "U.S. Government Public Domain (17 U.S.C. 105)",
        },
        "control_count": len(all_cjis_ctrls),
        "base_control_count": sum(1 for c in all_cjis_ctrls if "(" not in c),
        "enhancement_count": sum(1 for c in all_cjis_ctrls if "(" in c),
        "parameter_count": len(parameters),
        "controls_with_parameters_count": len(formatted_rows),
        "control_ids": all_cjis_ctrls,
        "parameters": parameters,
        "parameters_by_control": {k: v for k, v in params_by_control.items() if v},
        "guidance_by_control": {},
        "cjis_parameter_overrides": cjis_overrides,
        "formatted_parameter_rows": formatted_rows,
    }


def _default_output_dir() -> Path:
    skill_root = Path(__file__).resolve().parents[1]
    if (skill_root / "config").is_dir():
        return skill_root / "config" / "baselines"
    return Path(__file__).resolve().parent / "baselines"


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point to build normalized baseline catalogs."""
    parser = argparse.ArgumentParser(
        description="Build normalized compliance baseline JSON catalogs from official OSCAL and DoD SRG/CNSSI sources."
    )
    parser.add_argument(
        "--refdata-dir",
        type=Path,
        required=False,
        default=Path(__file__).resolve().parents[2] / "refdata",
        help="Directory containing upstream OSCAL profiles, catalogs, SRG text, and CNSSI 1253 files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=False,
        default=_default_output_dir(),
        help="Output directory for generated baseline JSON files and MANIFEST.json.",
    )
    parser.add_argument(
        "--include-privacy",
        action="store_true",
        help="Also emit the optional nist_800_53b_privacy.json baseline file.",
    )
    args = parser.parse_args(argv)

    refdata_dir: Path = args.refdata_dir.resolve()
    out_dir: Path = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    nist_cat, catalog_param_labels = load_nist_catalog(refdata_dir)
    cnssi_pvs_raw = json.loads((refdata_dir / "cnssi_1253_pvs_clean.json").read_text(encoding="utf-8"))
    cnssi_pvs = {
        k: clean_oscal_prose(v["clean_pv"] if isinstance(v, dict) else str(v))
        for k, v in cnssi_pvs_raw.items()
        if (v.get("clean_pv") if isinstance(v, dict) else v)
    }

    fr_low = normalize_fedramp_profile("LOW", refdata_dir, catalog_param_labels)
    fr_mod = normalize_fedramp_profile("MODERATE", refdata_dir, catalog_param_labels)
    fr_high = normalize_fedramp_profile("HIGH", refdata_dir, catalog_param_labels)

    nist_low = normalize_nist_profile("LOW", refdata_dir, nist_cat)
    nist_mod = normalize_nist_profile("MODERATE", refdata_dir, nist_cat)
    nist_high = normalize_nist_profile("HIGH", refdata_dir, nist_cat)

    dod_il2 = build_dod_il2_baseline(fr_mod, refdata_dir)
    dod_il4 = build_dod_il4_baseline(fr_mod, fr_high, cnssi_pvs, refdata_dir)
    dod_il5 = build_dod_il5_baseline(fr_high, cnssi_pvs, refdata_dir)
    dod_il6 = build_dod_il6_baseline(fr_high, dod_il5, cnssi_pvs, refdata_dir)
    cjis = build_cjis_baseline(fr_mod, nist_mod)

    outputs: Dict[str, Dict[str, Any]] = {
        "fedramp_rev5_low.json": fr_low,
        "fedramp_rev5_moderate.json": fr_mod,
        "fedramp_rev5_high.json": fr_high,
        "nist_800_53b_low.json": nist_low,
        "nist_800_53b_moderate.json": nist_mod,
        "nist_800_53b_high.json": nist_high,
        "dod_il2.json": dod_il2,
        "dod_il4.json": dod_il4,
        "dod_il5.json": dod_il5,
        "dod_il6.json": dod_il6,
        "cjis.json": cjis,
    }
    if args.include_privacy:
        outputs["nist_800_53b_privacy.json"] = normalize_nist_profile("PRIVACY", refdata_dir, nist_cat)
    else:
        priv_path = out_dir / "nist_800_53b_privacy.json"
        if priv_path.exists():
            priv_path.unlink()

    manifest: Dict[str, Any] = {"generated_at": RETRIEVAL_DATE, "files": {}}
    for filename, payload in outputs.items():
        for cid, row_str in payload["formatted_parameter_rows"].items():
            if "{{" in row_str or "}}" in row_str or "\n" in row_str or "\\" in row_str:
                raise ValueError(f"Unresolved token or escape in {filename} {cid}: {row_str!r}")
        out_path = out_dir / filename
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        manifest["files"][filename] = {
            "regime_id": payload["regime_id"],
            "display_name": payload["display_name"],
            "control_count": payload["control_count"],
            "base_control_count": payload["base_control_count"],
            "enhancement_count": payload["enhancement_count"],
            "controls_with_parameters_count": len(payload["formatted_parameter_rows"]),
            "sha256": sha256_file(out_path),
        }
        print(
            f"Wrote {filename:30s}: controls={payload['control_count']:3d} "
            f"(base={payload['base_control_count']:3d}, enh={payload['enhancement_count']:3d}), "
            f"param_rows={len(payload['formatted_parameter_rows']):3d}"
        )

    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
