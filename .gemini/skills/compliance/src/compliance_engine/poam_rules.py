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
Plan of Action and Milestones (POA&M) Rules & Normalization Engine
=================================================================
Decouples vulnerability evaluations, user-defined security concerns,
and scanner telemetry from Excel spreadsheet hydration.

Enables data-driven POA&M generation grounded in:
1. User-defined security concerns, punch-lists, and pending ATO items (compliance_config.yaml).
2. Live scanner findings (Security Command Center / vulnerability telemetry).
3. Code-grounded architectural checks (declarative rules evaluated against IaC resources).

NEVER fabricates synthetic filler items or fake milestones when a system is clean.
"""

import contextlib
import contextvars
import dataclasses
import logging
import os
from pathlib import Path
import re
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, Iterator, List, Mapping, Optional, Set, Tuple, Union

from .file_helpers import compute_poam_target_date, current_utc_datetime, is_high_baseline_regime, resolve_path
from .security_scanner_bridge import (
    SCANNERS_OFF,
    ScannerPolicy,
    isolated_scan_workspace,
    scan_and_derive_poam_items,
)

logger = logging.getLogger(__name__)

_CONTROL_ID_TOKEN_RE = re.compile(
    r"\b([A-Za-z]{2})\s*-\s*0*(\d+)(?:\s*\(\s*0*(\d+)\s*\))?",
)


def normalize_control_id(ctrl_id: Any) -> str:
    """Normalizes a NIST SP 800-53 control identifier (e.g., 'AC-02(01)' -> 'AC-2(1)')."""
    raw = str(ctrl_id or "").strip()
    if not raw:
        return ""
    raw = re.sub(r"^\[r5\]\s*", "", raw, flags=re.IGNORECASE)
    m = _CONTROL_ID_TOKEN_RE.search(raw)
    if not m:
        return raw.upper()
    family = m.group(1).upper()
    num = str(int(m.group(2)))
    enh = m.group(3)
    if enh is not None:
        return f"{family}-{num}({int(enh)})"
    return f"{family}-{num}"


def base_control_id(ctrl_id: Any) -> str:
    """Returns the normalized base control (enhancement dropped): 'IA-02(01)' -> 'IA-2'."""
    return normalize_control_id(ctrl_id).split("(", 1)[0]


def extract_normalized_control_ids(text: Any, include_base_control: bool = True) -> List[str]:
    """Extracts all normalized NIST control IDs from a string (e.g. 'AC-02 / IA-05(1)')."""
    raw = str(text or "")
    results: List[str] = []
    for m in _CONTROL_ID_TOKEN_RE.finditer(raw):
        family = m.group(1).upper()
        num = str(int(m.group(2)))
        enh = m.group(3)
        base = f"{family}-{num}"
        if enh is not None:
            full = f"{base}({int(enh)})"
            if full not in results:
                results.append(full)
            if include_base_control and base not in results:
                results.append(base)
        else:
            if base not in results:
                results.append(base)
    return results


def has_cmek_linkage(infra: Mapping[str, Any]) -> bool:
    """True when the inventory evidences Cloud KMS keys, a KMS module, or explicit CMEK bindings."""
    if not isinstance(infra, Mapping):
        return False
    if infra.get("kms_keys"):
        return True
    for mod in infra.get("modules_used") or []:
        mod_l = str(mod or "").strip().lower()
        if mod_l == "kms" or mod_l.endswith("/kms") or "cloud-kms" in mod_l or mod_l.startswith("module.kms"):
            return True
    unresolved_placeholder = "customer-managed key (reference resolved at apply time)"
    for cat in ("storage_buckets", "databases", "compute_instances", "gke_clusters", "cloud_run_services", "cloud_functions"):
        for item in infra.get(cat) or []:
            if not isinstance(item, Mapping):
                continue
            if item.get("cmek_encrypted") is True:
                return True
            for attr in ("cmek_key", "kms_key", "encryption_key_name"):
                val = str(item.get(attr) or "").strip()
                if not val:
                    continue
                val_l = val.lower()
                if (
                    val_l != unresolved_placeholder
                    and not val.startswith("[CONFIG_REQUIRED")
                    and not val.startswith("[NOT DETERMINED")
                ):
                    return True
    return False


def _policy_sources(inventory: Mapping[str, Any]) -> Tuple[Mapping[str, Any], ...]:
    if not isinstance(inventory, Mapping):
        return ()
    sources: List[Mapping[str, Any]] = []
    for k in ("compliance_config", "system_information", "security_operations"):
        val = inventory.get(k)
        if isinstance(val, Mapping):
            sources.append(val)
    sources.append(inventory)
    return tuple(sources)


def resolve_max_kms_rotation_days(inventory: Mapping[str, Any]) -> Optional[int]:
    """Returns organization-defined cryptoperiod threshold in days (SP 800-57 Pt 1), or None when unset."""
    for src in _policy_sources(inventory):
        raw_days = src.get("max_kms_rotation_days")
        if raw_days is not None and not isinstance(raw_days, bool):
            try:
                days = int(raw_days)
                if days > 0:
                    return days
            except (ValueError, TypeError):
                pass
        if src.get("require_kms_rotation") is True:
            return 365
    return None


def requires_cloud_hsm_keys(inventory: Mapping[str, Any]) -> bool:
    """True when organizational policy explicitly requires Cloud HSM (Level 3) keys over SOFTWARE keys."""
    for src in _policy_sources(inventory):
        if src.get("require_cloud_hsm_keys") is True:
            return True
    return False


_PUBLIC_SOURCES: frozenset = frozenset({"0.0.0.0/0", "::/0", "*"})
# Protocols without port numbers: a rule for these never exposes a TCP/UDP service.
_PORTLESS_PROTOCOLS: frozenset = frozenset({"icmp", "icmpv6", "ipv6-icmp", "esp", "ah", "gre", "sctp", "1", "47", "50", "51", "58"})
# Protocols for which a missing port list means every port.
_ALL_PORT_PROTOCOLS: frozenset = frozenset({"tcp", "udp", "all", "*", "6", "17"})
_FULL_RANGE_TOKENS: frozenset = frozenset({"all", "*", "any", "0-65535", "1-65535"})


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _split_tokens(values: Any, separators: str = r"[,;]") -> List[str]:
    tokens: List[str] = []
    for item in _as_list(values):
        tokens.extend(t.strip() for t in re.split(separators, str(item)) if t.strip())
    return tokens


def is_public_ingress_allow_rule(fw: Any) -> bool:
    """True for an enabled INGRESS ALLOW rule whose sources include 0.0.0.0/0, ::/0 or *."""
    if not isinstance(fw, dict) or bool(fw.get("disabled")):
        return False
    action = str(fw.get("action") or "ALLOW").strip().upper()
    if action in ("DENY", "DROP", "REJECT") or "DENY" in str(fw.get("type") or "").upper():
        return False
    if str(fw.get("direction") or "INGRESS").strip().upper() not in ("INGRESS", "INBOUND", ""):
        return False
    sources = fw.get("source_ranges")
    if sources is None:
        sources = fw.get("sources")
    return any(str(src).strip() in _PUBLIC_SOURCES for src in _as_list(sources))


def _protocol_port_tokens(protocols: List[str], ports: Any) -> List[str]:
    """Port tokens one (protocol, ports) entry contributes; portless protocols add none."""
    protos = [p.lower() for p in protocols if p]
    if protos and all(p in _PORTLESS_PROTOCOLS for p in protos):
        return []
    tokens = _split_tokens(ports)
    if not tokens and (not protos or any(p in _ALL_PORT_PROTOCOLS for p in protos)):
        # GCP applies an entry without ports to every port of the protocol.
        return ["all"] if protos else []
    return tokens


def firewall_rule_exposes_ports(
    fw: Mapping[str, Any],
    target_ports: Optional[Iterable[int]] = None,
) -> List[int]:
    """Returns the sorted ``target_ports`` a public INGRESS ALLOW rule exposes.

    A structured ``allowed`` list ([{protocol|IPProtocol, ports}]) is authoritative
    when present; otherwise the flat ``protocol`` / ``ports`` fields are used.
    """
    if not is_public_ingress_allow_rule(fw):
        return []
    ports_to_check: Set[int] = set(target_ports) if target_ports is not None else {22, 80, 3389}
    if not ports_to_check:
        return []

    raw_tokens: List[str] = []
    allowed_field = fw.get("allowed")
    if isinstance(allowed_field, list) and allowed_field:
        for entry in allowed_field:
            if isinstance(entry, dict):
                proto = entry.get("protocol") or entry.get("IPProtocol") or "tcp"
                raw_tokens.extend(_protocol_port_tokens(_split_tokens(proto, r"[/,;]"), entry.get("ports")))
    else:
        raw_tokens.extend(_protocol_port_tokens(_split_tokens(fw.get("protocol"), r"[/,;]"), fw.get("ports")))

    exposed: Set[int] = set()
    for tok in raw_tokens:
        clean_tok = re.sub(r"^(?:tcp|udp)[:/]\s*|/(?:tcp|udp)$", "", tok.strip().lower()).strip()
        if clean_tok in _FULL_RANGE_TOKENS:
            return sorted(ports_to_check)
        lo_s, sep, hi_s = clean_tok.partition("-")
        if sep and lo_s.strip().isdigit() and hi_s.strip().isdigit():
            lo, hi = int(lo_s), int(hi_s)
            exposed.update(p for p in ports_to_check if lo <= p <= hi)
        elif clean_tok.isdigit() and int(clean_tok) in ports_to_check:
            exposed.add(int(clean_tok))
    return sorted(exposed)


SEVERITY_ORDER: Dict[str, int] = {
    "CRITICAL": 5,
    "VERY HIGH": 5,
    "VERY_HIGH": 5,
    "HIGH": 4,
    "MODERATE": 3,
    "MEDIUM": 3,
    "MOD": 3,
    "LOW": 2,
    "VERY LOW": 1,
    "VERY_LOW": 1,
    "INFORMATIONAL": 0,
    "INFO": 0,
    "NONE": 0,
}


_POAM_STATUS_MAP: Dict[str, str] = {
    "OPEN": "Ongoing",
    "ONGOING": "Ongoing",
    "IN PROGRESS": "Ongoing",
    "IN_PROGRESS": "Ongoing",
    "DELAYED": "Delayed",
    "OVERDUE": "Delayed",
    "PAST DUE": "Delayed",
    "PAST_DUE": "Delayed",
    "COMPLETED": "Completed",
    "CLOSED": "Completed",
    "RISK ACCEPTED": "Risk Accepted",
    "RISK_ACCEPTED": "Risk Accepted",
}

_MILESTONE_STATUS_MAP: Dict[str, str] = {
    "OPEN": "Open",
    "ONGOING": "Ongoing",
    "IN PROGRESS": "Ongoing",
    "IN_PROGRESS": "Ongoing",
    "COMPLETED": "Completed",
    "CLOSED": "Closed",
}

_SEVERITY_LABEL_MAP: Dict[str, str] = {
    "CRITICAL": "Very High",
    "VERY HIGH": "Very High",
    "VERY_HIGH": "Very High",
    "HIGH": "High",
    "MEDIUM": "Moderate",
    "MODERATE": "Moderate",
    "MOD": "Moderate",
    "LOW": "Low",
    "VERY LOW": "Very Low",
    "VERY_LOW": "Very Low",
    "NONE": "None",
}


def _normalize_poam_dates_and_milestones(
    raw: Dict[str, Any],
    counter: int,
    today_dt: datetime,
    date_90d: str,
) -> Tuple[str, str, str, str, str]:
    """Resolves (status, sched_date, milestone_id, milestone_desc, milestone_status) for a POA&M item."""
    raw_status = str(raw.get("status") or "Ongoing").strip()
    status = _POAM_STATUS_MAP.get(raw_status.upper(), raw_status.title())
    sched_date = raw.get("scheduled_completion_date") or raw.get("sched_date") or raw.get("target_date")
    if sched_date:
        try:
            s_dt = datetime.strptime(str(sched_date)[:10], "%Y-%m-%d")
        except (ValueError, TypeError) as err:
            logger.warning(
                "POA&M finding %r has an unparseable scheduled completion date %r (%s); "
                "substituting the default 90-day milestone %s.",
                raw.get("item_id") or raw.get("finding_id") or counter,
                sched_date,
                err,
                date_90d,
            )
            sched_str = date_90d
        else:
            sched_str = str(sched_date)[:10]
            if s_dt <= today_dt:
                logger.info("POA&M finding %r is past its scheduled completion date %s.", raw.get("item_id") or counter, sched_str)
    else:
        sched_str = date_90d

    m_list = raw.get("milestones", [])
    if isinstance(m_list, list) and m_list and isinstance(m_list[0], dict):
        first_m = m_list[0]
        m_id = first_m.get("milestone_id") or f"M-{counter:03d}-1"
        m_desc = first_m.get("description") or first_m.get("milestone_desc") or "Execute remediation action."
        raw_m_status = str(first_m.get("status") or first_m.get("milestone_status") or "Open").strip()
    else:
        m_id = raw.get("milestone_id") or f"M-{counter:03d}-1"
        m_desc = raw.get("milestone_desc") or "Execute remediation action and verify control compliance."
        raw_m_status = str(raw.get("milestone_status") or "Open").strip()

    m_status = _MILESTONE_STATUS_MAP.get(raw_m_status.upper(), raw_m_status.title())
    return status, sched_str, m_id, m_desc, m_status


def _normalize_poam_risk_ratings(raw: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    """Resolves (severity, threat, likelihood, impact, residual) for a POA&M item."""
    raw_sev = str(raw.get("severity_risk_level") or raw.get("severity") or "Low").strip()
    severity = _SEVERITY_LABEL_MAP.get(raw_sev.upper(), raw_sev.title())
    high_set = {"High", "Very High"}
    threat = raw.get("threat") or ("Moderate" if severity in high_set else "Low")
    likelihood = raw.get("likelihood") or ("Moderate" if severity in high_set else "Low")
    if raw.get("impact"):
        impact = str(raw["impact"])
    elif severity in high_set:
        impact = "High"
    elif severity == "Moderate":
        impact = "Moderate"
    else:
        impact = "Low"
    residual = raw.get("residual") or "Low"
    return severity, threat, likelihood, impact, residual


def normalize_poam_item(
    raw: Dict[str, Any],
    sys_abbr: str = "SYS",
    counter: int = 1,
    eff_date: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Standardizes a raw POA&M item into a canonical dictionary structure."""
    if not isinstance(raw, dict):
        return None

    today_dt = current_utc_datetime().replace(tzinfo=None)
    eff_str = eff_date or today_dt.strftime("%Y-%m-%d")
    try:
        base_dt = datetime.strptime(eff_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        base_dt = today_dt
    date_90d = compute_poam_target_date(90, base_dt)

    control = raw.get("control_identifier") or raw.get("control") or "CA-05 Plan of Action and Milestones"
    item_id = raw.get("item_id") or f"POAM-{sys_abbr}-{counter:03d}"
    w_name = str(raw.get("weakness_name") or "").strip()
    raw_desc = str(raw.get("desc") or raw.get("weakness_description") or "").strip()
    if w_name and raw_desc and w_name != raw_desc:
        desc = f"{w_name}: {raw_desc}" if w_name not in raw_desc else raw_desc
    else:
        desc = raw_desc or w_name or str(raw.get("title") or "").strip() or "Identified security concern or pending remediation"
    aps = raw.get("aps") or raw.get("control_enhancement") or (control.split()[0] if control else "CA-05")
    checks = raw.get("checks") or raw.get("cci") or "NIST-SP-800-53"
    status, sched_date, m_id, m_desc, m_status = _normalize_poam_dates_and_milestones(raw, counter, today_dt, date_90d)
    source = raw.get("source_of_weakness") or raw.get("source") or "Security Assessment & Continuous Monitoring"
    severity, threat, likelihood, impact, residual = _normalize_poam_risk_ratings(raw)
    raw_title = raw.get("weakness_name") or raw.get("title")
    title = raw_title if raw_title else desc.split("\n")[0].strip()

    return {
        "control": control,
        "item_id": item_id,
        "title": title,
        "weakness_name": title,
        "desc": desc,
        "weakness_description": desc,
        "aps": aps,
        "checks": checks,
        "status": status,
        "sched_date": sched_date,
        "original_sched_date": sched_date,
        "milestone_id": m_id,
        "milestone_desc": m_desc,
        "milestone_status": m_status,
        "source": source,
        "severity": severity,
        "threat": threat,
        "likelihood": likelihood,
        "impact": impact,
        "residual": residual,
        "rule_id": str(raw.get("rule_id") or ""),
        "check_id": str(raw.get("check_id") or ""),
    }


class SecurityConcernRule:
    """Declarative definition of a potential architectural security gap."""

    def __init__(
        self,
        rule_id: str,
        control: str,
        aps: str,
        checks: str,
        severity: str,
        threat: str,
        likelihood: str,
        impact: str,
        source: str,
        sched_days: int,
        eval_fn: Callable[[Dict[str, Any]], List[Any]],
        desc_fn: Callable[[List[Any]], str],
        milestone_desc: Union[str, Callable[[List[Any]], str]],
    ) -> None:
        """Initializes a declarative architectural security gap rule.

        Args:
            rule_id: Unique rule identifier string.
            control: NIST SP 800-53 control identifier and title.
            aps: Auto-provisioning system or control enhancement identifier.
            checks: Associated STIG check or CCI identifier.
            severity: Severity rating (e.g., 'High', 'Moderate', 'Low').
            threat: Threat level assessment string.
            likelihood: Likelihood evaluation string.
            impact: Impact rating evaluation string.
            source: Source of weakness attribution string.
            sched_days: Days from effective date until scheduled remediation.
            eval_fn: Callable predicate returning matching non-compliant resource list.
            desc_fn: Callable generating specific weakness description from matches.
            milestone_desc: Action milestone description string or callable.
        """
        self.rule_id = rule_id
        self.control = control
        self.aps = aps
        self.checks = checks
        self.severity = severity
        self.threat = threat
        self.likelihood = likelihood
        self.impact = impact
        self.source = source
        self.sched_days = sched_days
        self.eval_fn = eval_fn
        self.desc_fn = desc_fn
        self.milestone_desc = milestone_desc

    def evaluate(
        self,
        inventory: Dict[str, Any],
        sys_abbr: str,
        counter: int,
        base_dt: datetime,
    ) -> Optional[Dict[str, Any]]:
        """Evaluates this rule against the system inventory.

        Args:
            inventory: Full architecture and infrastructure inventory dictionary.
            sys_abbr: System abbreviation for finding identification.
            counter: Numeric sequence counter for POA&M item numbering.
            base_dt: Baseline datetime for milestone scheduling calculations.

        Returns:
            A normalized POA&M item dictionary if violations were found, else None.
        """
        matches = self.eval_fn(inventory)
        if not matches:
            return None

        sched_base = max(current_utc_datetime().replace(tzinfo=None), base_dt)
        target_date = (sched_base + timedelta(days=self.sched_days)).strftime("%Y-%m-%d")
        desc = self.desc_fn(matches)
        m_desc = (
            self.milestone_desc(matches)
            if callable(self.milestone_desc)
            else self.milestone_desc
        )

        title = desc.split("\n")[0].strip()
        return {
            "control": self.control,
            "item_id": f"POAM-{sys_abbr}-{counter:03d}",
            "title": title,
            "weakness_name": title,
            "desc": desc,
            "weakness_description": desc,
            "aps": self.aps,
            "checks": self.checks,
            "status": "Ongoing",
            "sched_date": target_date,
            "milestone_id": f"M-{counter:03d}-1",
            "milestone_desc": m_desc,
            "milestone_status": "Open",
            "source": self.source,
            "severity": self.severity,
            "threat": self.threat,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "residual": "Low",
            "rule_id": self.rule_id,
            "check_id": ""
        }


# ==============================================================================
# Declarative Catalog of IaC Architecture Security Rules
# ==============================================================================

# Attributes whose value the extractor reports as tri-state. A True means the
# control is enforced, a False means it is not (and is reported by the specific
# rule for that control), and an explicit None means the IaC did not say. Only
# the last case belongs to DATA_GAP, so that a single asset is never reported
# twice for the same attribute.
_TRISTATE_ATTRS_BY_GROUP = {
    "storage_buckets": ("Storage Bucket", ["cmek_encrypted", "versioning", "uniform_bucket_level_access"]),
    "compute_instances": ("Compute Instance", ["shielded_vm"]),
    "databases": ("Database", ["require_ssl", "backup_enabled"]),
    "gke_clusters": ("GKE Cluster", ["private_cluster", "private_endpoint"]),
    "kms_keys": ("KMS Key", ["protection_level"]),
}


def _find_unverified_assets(inv: Dict[str, Any]) -> List[str]:
    """Lists assets whose security posture the IaC did not determine.

    Args:
        inv: The extracted system inventory.

    Returns:
        Labels of the form '<Asset Type> <name>' for each asset carrying at
        least one attribute that is present but explicitly null. Attributes
        absent from the record entirely are ignored: the extractor never
        offered an opinion on them, so they are not an unresolved gap.
    """
    gaps = []
    components = inv.get("infrastructure_components", {}) or {}
    for group_key, (label, attrs) in _TRISTATE_ATTRS_BY_GROUP.items():
        for item in components.get(group_key, []) or []:
            if not isinstance(item, dict):
                continue
            if any(attr in item and item.get(attr) is None for attr in attrs):
                gaps.append(f"{label} {item.get('name', 'unknown')}")
    return gaps


IAC_SECURITY_RULES = [
    # 1. Storage Buckets Without Customer-Managed Encryption Keys (SC-12 / SC-28)
    SecurityConcernRule(
        rule_id="STORAGE_WITHOUT_CMEK",
        control="SC-12 / SC-28 Storage Buckets Without Customer-Managed Encryption Keys (CMEK)",
        aps="SC-28(1)",
        checks="SRG-OS-000480",
        severity="Moderate",
        threat="Low",
        likelihood="Low",
        impact="Moderate",
        source="Security Assessment & Configuration Inspection",
        sched_days=60,
        eval_fn=lambda inv: [
            b.get("name")
            for b in inv.get("infrastructure_components", {}).get("storage_buckets", [])
            if b.get("cmek_encrypted") is False
        ],
        desc_fn=lambda names: (
            "Configure customer-managed encryption keys (CMEK) in Cloud KMS for Cloud Storage "
            f"buckets currently using Google-managed default encryption: {', '.join(names[:3])}."
        ),
        milestone_desc="Configure Cloud KMS CMEK key ring and enforce storage CMEK binding policy in Terraform."
    ),

    # 2. Insecure Firewall Ingress Rules (SC-07)
    SecurityConcernRule(
        rule_id="OPEN_INGRESS",
        control="SC-07 Boundary Protection & Unrestricted Ingress Remediation",
        aps="SC-07(5)",
        checks="SRG-NET-000019",
        severity="High",
        threat="Moderate",
        likelihood="Moderate",
        impact="High",
        source="Network Security Architecture Review",
        sched_days=30,
        eval_fn=lambda inv: [
            fw.get("name") or f"rule-port-{fw.get('ports', '')}"
            for fw in inv.get("network_architecture", {}).get("firewall_rules", [])
            if firewall_rule_exposes_ports(fw, {22, 80, 3389})
        ],
        desc_fn=lambda names: (
            f"Restrict broad 0.0.0.0/0 ingress on non-HTTPS ports for firewall rules: {', '.join(names)}."
        ),
        milestone_desc=(
            "Confine ingress rules to authorized management ranges "
            "(e.g. Cloud IAP 35.235.240.0/20) or authorized private interconnects."
        ),
    ),

    # 3. Unassigned Mandatory Personnel Governance Roles (PL-02, PM-02)
    SecurityConcernRule(
        rule_id="MISSING_ROLES",
        control="PL-02 / PM-02 Formal Cybersecurity Roles Appointment",
        aps="PM-2",
        checks="NIST-PM-02",
        severity="Moderate",
        threat="Low",
        likelihood="Low",
        impact="Moderate",
        source="Governance & Policy Compliance Review",
        sched_days=30,
        eval_fn=lambda inv: (
            [
                title for key, title in [("system_owner", "System Owner"), ("issm", "ISSM"), ("isso", "ISSO"), ("authorizing_official", "Authorizing Official")]
                if key not in inv.get("personnel_roles", {}) or not str(inv.get("personnel_roles", {}).get(key, {}).get("name", "")).strip()
            ] if inv.get("personnel_roles") else []
        ),
        desc_fn=lambda roles: f"Formal designation and clearance verification required for unassigned security roles: {', '.join(roles)}.",
        milestone_desc="Appoint cleared personnel and populate organizational rosters in compliance configuration."
    ),

    # 4. Software Cloud KMS Keys when Organization Policy Requires Cloud HSM (SC-12, SC-13)
    SecurityConcernRule(
        rule_id="SOFTWARE_KMS_IN_IL5",
        control="SC-12 / SC-13 Cloud HSM Hardware Cryptographic Key Policy",
        aps="SC-13",
        checks="SRG-OS-000185",
        severity="Moderate",
        threat="Low",
        likelihood="Low",
        impact="Moderate",
        source="Cryptographic Protection Baseline Audit",
        sched_days=90,
        eval_fn=lambda inv: [
            k.get("name") for k in inv.get("infrastructure_components", {}).get("kms_keys", [])
            if (k.get("protection_level") or "").upper() == "SOFTWARE"
            and is_high_baseline_regime(inv.get("system_information", {}))
            and requires_cloud_hsm_keys(inv)
        ],
        desc_fn=lambda keys: (
            "Organizational cryptographic policy recommends upgrading Cloud KMS keys "
            f"({', '.join(keys[:2])}) from SOFTWARE (FIPS 140-3 Level 1 BoringCrypto) "
            "to Cloud HSM (FIPS 140-2 Level 3)."
        ),
        milestone_desc="Provision Cloud HSM (FIPS 140-2 Level 3) keys in Cloud KMS where required by organizational policy."
    ),

    # 5. Database without Enforced SSL/TLS Client Encryption (SC-08, SC-13)
    SecurityConcernRule(
        rule_id="DB_SSL_DISABLED",
        control="SC-08 / SC-13 Enforce TLS Encryption on Database Connections",
        aps="SC-08(1)",
        checks="SRG-APP-000442",
        severity="Moderate",
        threat="Low",
        likelihood="Moderate",
        impact="High",
        source="Infrastructure-as-Code Static Security Audit",
        sched_days=30,
        eval_fn=lambda inv: [db.get("name") for db in inv.get("infrastructure_components", {}).get("databases", []) if db.get("require_ssl") is False],
        desc_fn=lambda dbs: f"Database instance(s) {', '.join(dbs[:3])} do not enforce SSL/TLS client certificate encryption.",
        milestone_desc="Configure require_ssl = true / ssl_mode = ENCRYPTED_ONLY in database network settings."
    ),

    # 6. Database Instances with Disabled Automated Backups (CP-09)
    SecurityConcernRule(
        rule_id="DB_NO_BACKUP",
        control="CP-09 Information System Backup Automated Implementation",
        aps="CP-9",
        checks="SRG-APP-000516",
        severity="Moderate",
        threat="Low",
        likelihood="Low",
        impact="High",
        source="Contingency Planning Architecture Review",
        sched_days=30,
        eval_fn=lambda inv: [db.get("name") for db in inv.get("infrastructure_components", {}).get("databases", []) if db.get("backup_enabled") is False],
        desc_fn=lambda dbs: f"Database instance(s) {', '.join(dbs[:3])} have automated backup configuration disabled.",
        milestone_desc="Enable automated daily backups and point-in-time recovery in database Terraform configuration."
    ),

    # 7. Database Instances with Direct Public IP Enabled (AC-03, SC-07)
    SecurityConcernRule(
        rule_id="DB_PUBLIC_IP",
        control="AC-03 / SC-07 Disable Public IP on Database Instances",
        aps="SC-07(5)",
        checks="SRG-APP-000516",
        severity="High",
        threat="Moderate",
        likelihood="Moderate",
        impact="High",
        source="Network Security Architecture Review",
        sched_days=30,
        eval_fn=lambda inv: [db.get("name") for db in inv.get("infrastructure_components", {}).get("databases", []) if db.get("has_public_ip") is True],
        desc_fn=lambda dbs: f"Database instance(s) {', '.join(dbs[:3])} have direct public IPv4 allocation enabled.",
        milestone_desc="Disable ipv4_enabled and confine all database traffic to private VPC peering or Private Service Connect."
    ),

    # 8. Compute Instances with Direct External Public IPs (AC-03, SC-07)
    SecurityConcernRule(
        rule_id="VM_PUBLIC_IP",
        control="AC-03 / SC-07 Remove Direct Public IPs from Compute Workloads",
        aps="SC-07(5)",
        checks="SRG-OS-000480",
        severity="High",
        threat="Moderate",
        likelihood="Moderate",
        impact="High",
        source="Infrastructure-as-Code Static Security Audit",
        sched_days=30,
        eval_fn=lambda inv: [vm.get("name") for vm in inv.get("infrastructure_components", {}).get("compute_instances", []) if vm.get("has_public_ip") is True],
        desc_fn=lambda vms: f"Compute instance(s) {', '.join(vms[:3])} possess direct external public IPs, exposing workloads to Internet attack surfaces.",
        milestone_desc="Remove public IP / external access configurations from network interfaces and route outbound egress through Cloud NAT / NAT Gateways."
    ),

    # 9. Compute Instances without Shielded VM Integrity (SI-07)
    SecurityConcernRule(
        rule_id="VM_UNSHIELDED",
        control="SI-07 Software, Firmware, and Information Integrity (Shielded VM)",
        aps="SI-07(1)",
        checks="SRG-OS-000480",
        severity="Moderate",
        threat="Low",
        likelihood="Low",
        impact="Moderate",
        source="Platform Integrity Security Review",
        sched_days=60,
        eval_fn=lambda inv: [vm.get("name") for vm in inv.get("infrastructure_components", {}).get("compute_instances", []) if vm.get("shielded_vm") is False],
        desc_fn=lambda vms: f"Compute instance(s) {', '.join(vms[:3])} do not enable Shielded VM vTPM and integrity monitoring.",
        milestone_desc="Enable shielded_instance_config with Secure Boot, vTPM, and integrity monitoring enabled."
    ),

    # 10. GKE Clusters with Public Endpoints (AC-03, SC-07)
    SecurityConcernRule(
        rule_id="GKE_PUBLIC_ENDPOINT",
        control="AC-03 / SC-07 Enforce Private Cluster and Private Endpoint on GKE",
        aps="SC-07(5)",
        checks="SRG-APP-000516",
        severity="High",
        threat="Moderate",
        likelihood="Moderate",
        impact="High",
        source="Kubernetes Architecture Security Review",
        sched_days=30,
        eval_fn=lambda inv: [
            c.get("name")
            for c in inv.get("infrastructure_components", {}).get("gke_clusters", [])
            if c.get("private_cluster") is False or c.get("private_endpoint") is False
        ],
        desc_fn=lambda clusters: f"GKE cluster(s) {', '.join(clusters[:2])} have public control plane endpoints exposed.",
        milestone_desc="Configure private_cluster_config with enable_private_nodes = true and enable_private_endpoint = true."
    ),

    # 11. GKE Clusters without Workload Identity (IA-09, IA-05)
    SecurityConcernRule(
        rule_id="GKE_NO_WIF",
        control="IA-09 / IA-05 GKE Workload Identity Federation Enforcement",
        aps="IA-9",
        checks="SRG-APP-000516",
        severity="Moderate",
        threat="Low",
        likelihood="Low",
        impact="Moderate",
        source="Kubernetes IAM Assessment",
        sched_days=60,
        eval_fn=lambda inv: [c.get("name") for c in inv.get("infrastructure_components", {}).get("gke_clusters", []) if c.get("workload_identity") is False],
        desc_fn=lambda clusters: f"GKE cluster(s) {', '.join(clusters[:2])} do not enable Workload Identity for pod service account federation.",
        milestone_desc="Configure workload_identity_config with workload_pool set to ${project_id}.svc.id.goog."
    ),

    # 12. Static Downloadable Service Account Keys (AC-02, IA-05(2))
    SecurityConcernRule(
        rule_id="STATIC_SA_KEYS",
        control="AC-02 / IA-05(2) Deprecate Static Long-Lived Service Account Keys",
        aps="IA-05(2)",
        checks="SRG-OS-000104",
        severity="High",
        threat="Moderate",
        likelihood="Moderate",
        impact="High",
        source="Identity & Access Governance Review",
        sched_days=30,
        eval_fn=lambda inv: [
            k.get("name", "key")
            for k in inv.get("infrastructure_components", {}).get("service_account_keys", [])
        ],
        desc_fn=lambda keys: (
            f"Static service account key resource(s) detected ({', '.join(keys[:2])}), "
            "introducing exfiltration risks."
        ),
        milestone_desc=(
            "Delete static key resources and migrate workloads to Workload Identity Federation (WIF) "
            "or short-lived OAuth tokens."
        ),
    ),

    # 13. Unverified Asset Properties (CA-7 / CM-8)
    SecurityConcernRule(
        rule_id="DATA_GAP",
        control="CA-07 / CM-08 Continuous Monitoring Data Gaps",
        aps="CA-7",
        checks="SRG-OS-000480",
        severity="Low",
        threat="Low",
        likelihood="Low",
        impact="Low",
        source="Infrastructure Architecture Completeness Review",
        sched_days=180,
        eval_fn=lambda inv: _find_unverified_assets(inv),
        desc_fn=lambda gaps: f"Security posture could not be definitively verified from IaC for: {', '.join(gaps[:3])}.",
        milestone_desc="Update Terraform definitions to explicitly configure missing properties or allow runtime state ingestion."
    )
]


def _scanner_report_config(inventory: Dict[str, Any]) -> Dict[str, Any]:
    """Report options taken from the target configuration (never scanner enablement).

    ``include_scanner_failures_in_poam`` is documented under ``security_scanners``;
    the top-level key is still accepted for older configurations.
    """
    raw = inventory.get("security_scanners")
    scanner_cfg = raw if isinstance(raw, dict) else {}
    if "include_scanner_failures_in_poam" in scanner_cfg:
        include_failures = bool(scanner_cfg["include_scanner_failures_in_poam"])
    else:
        include_failures = bool(inventory.get("include_scanner_failures_in_poam", False))
    sarif_reports = [str(p) for p in scanner_cfg.get("sarif_reports", []) or [] if isinstance(p, str)]
    sys_info = inventory.get("system_information", {}) or {}
    return {
        "include_scanner_failures_in_poam": include_failures,
        # Still requires COMPLIANCE_ALLOW_LIVE_CLOUD_TELEMETRY in the operator environment.
        "query_live_cloud_telemetry": bool(scanner_cfg.get("query_live_cloud_telemetry", False)),
        "ingest_sarif": True,
        "sarif_reports": sarif_reports,
        "impact_level": inventory.get("impact_level") or sys_info.get("impact_level"),
        "system_information": sys_info,
        "project_id": inventory.get("project_id") or sys_info.get("project_id"),
    }


def collect_scanner_items(
    inventory: Dict[str, Any],
    target_dir: Union[str, Path],
    scanner_policy: ScannerPolicy = SCANNERS_OFF,
    eff_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Runs the operator-approved scanners on a private copy and reads target SARIF.

    The scan root is always ``target_dir``; inventory keys (workspace_path,
    security_scanners.enabled / run_*) are not consulted.
    """
    target = str(resolve_path(target_dir))
    if not os.path.isdir(target):
        return []
    sys_abbr = (inventory.get("system_information", {}) or {}).get("system_abbreviation") or "SYS"
    cfg = _scanner_report_config(inventory)
    for name in ("checkov", "semgrep", "trivy"):
        cfg[f"run_{name}"] = scanner_policy.enabled(name)
    if scanner_policy.semgrep_config:
        cfg["_operator_semgrep_config"] = scanner_policy.semgrep_config
    with isolated_scan_workspace(target, scanner_policy.run_live) as scan_copy:
        return scan_and_derive_poam_items(
            target,
            sys_abbr=sys_abbr,
            eff_date=eff_date,
            config=cfg,
            scan_root=str(scan_copy) if scan_copy else None,
        )


@dataclasses.dataclass(frozen=True)
class _PoamRun:
    target_dir: str
    scanner_items: Tuple[Dict[str, Any], ...]


_ACTIVE_RUN: contextvars.ContextVar[Optional[_PoamRun]] = contextvars.ContextVar("poam_run", default=None)


@contextlib.contextmanager
def poam_run(
    inventory: Dict[str, Any],
    target_dir: Union[str, Path],
    scanner_policy: ScannerPolicy = SCANNERS_OFF,
    eff_date: Optional[str] = None,
) -> Iterator[str]:
    """Collects scanner and SARIF findings once; every derive_poam_findings call for
    the same target inside the block reuses them (one scan per generate run)."""
    target = str(resolve_path(target_dir))
    items = collect_scanner_items(inventory, target, scanner_policy, eff_date)
    token = _ACTIVE_RUN.set(_PoamRun(target_dir=target, scanner_items=tuple(items)))
    try:
        yield target
    finally:
        _ACTIVE_RUN.reset(token)


def active_poam_target() -> Optional[str]:
    """The target directory of the enclosing :func:`poam_run`, or None."""
    run = _ACTIVE_RUN.get()
    return run.target_dir if run else None


def _collect_unparsed_blueprint_poam_items(
    inventory: Dict[str, Any],
    sys_abbr: str,
    base_dt: datetime,
    start_idx: int,
) -> List[Dict[str, Any]]:
    """Derives POA&M items for unparsed Terraform files inside the authorization boundary."""
    sys_info_dict = inventory.get("system_information", {}) or {}
    comp_cfg = inventory.get("compliance_config") or {}
    if "include_unparsed_blueprints_in_poam" in comp_cfg:
        include_unparsed = bool(comp_cfg["include_unparsed_blueprints_in_poam"])
    elif "include_unparsed_blueprints_in_poam" in inventory:
        include_unparsed = bool(inventory["include_unparsed_blueprints_in_poam"])
    elif "include_unparsed_blueprints_in_poam" in sys_info_dict:
        include_unparsed = bool(sys_info_dict["include_unparsed_blueprints_in_poam"])
    else:
        include_unparsed = True
    if not include_unparsed:
        return []

    unparsed = (inventory.get("infrastructure_components") or {}).get("unparsed_terraform_files") or []
    results: List[Dict[str, Any]] = []
    idx = start_idx
    for entry in unparsed:
        if not isinstance(entry, dict):
            continue
        rel_path = str(entry.get("path") or "").strip()
        if not rel_path:
            continue
        diagnostic = " ".join(str(entry.get("error") or "").split())[:300]
        title = (
            f"Terraform blueprint '{rel_path}' could not be parsed; its resources "
            "are absent from the authorization boundary."
        )
        desc = (
            f"{title} The infrastructure-as-code discovery engine failed to build "
            "an abstract syntax tree for this file, so any project, network, "
            "service account, key, or firewall rule it declares is missing from "
            "the System Security Plan, the SCTM, and the architecture "
            "reconciliation. The boundary described in this package is therefore "
            "incomplete by an unknown amount."
        )
        if diagnostic:
            desc = f"{desc} Parser diagnostic: {diagnostic}"
        results.append({
            "control": (
                "CA-02 / RA-05 Security Assessment and Vulnerability Monitoring "
                "(Authorization Boundary Discovery Gap)"
            ),
            "item_id": f"POAM-{sys_abbr}-{idx:03d}",
            "title": title,
            "desc": desc,
            "aps": "CA-02 / RA-05",
            "checks": "CA-02 / RA-05",
            "status": "Ongoing",
            "sched_date": compute_poam_target_date(30, base_dt),
            "milestone_id": f"M-{idx:03d}-1",
            "milestone_desc": (
                f"Resolve the parse failure in '{rel_path}' (or confirm the file is "
                "outside the authorization boundary), re-run discovery, and verify "
                "the resources it declares appear in the SSP and SCTM."
            ),
            "milestone_status": "Open",
            "source": "IaC Discovery Engine",
            "severity": "Moderate",
            "threat": "Low",
            "likelihood": "Low",
            "impact": "Moderate",
            "residual": "Moderate",
        })
        idx += 1
    return results


def derive_poam_findings(
    inventory: Dict[str, Any],
    eff_date: Optional[str] = None,
    *,
    target_dir: Optional[Union[str, Path]],
    scanner_policy: Optional[ScannerPolicy] = None,
) -> List[Dict[str, Any]]:
    """Derives canonical POA&M items grounded strictly in architecture and telemetry."""
    if not eff_date:
        eff_date = (
            inventory.get("system_information", {}).get("effective_date")
            or current_utc_datetime().replace(tzinfo=None).strftime("%Y-%m-%d")
        )
    try:
        base_dt = datetime.strptime(eff_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        base_dt = current_utc_datetime().replace(tzinfo=None)

    sys_abbr = inventory.get("system_information", {}).get("system_abbreviation") or "SYS"
    items: List[Dict[str, Any]] = []
    item_counter = 1

    # 1. Ingest User-Configured POA&M Items / Security Concerns / Findings
    user_items = inventory.get("poam_items") or inventory.get("security_concerns") or inventory.get("findings") or []
    for raw in user_items:
        normalized = normalize_poam_item(raw, sys_abbr=sys_abbr, counter=item_counter, eff_date=eff_date)
        if normalized:
            items.append(normalized)
            item_counter += 1

    # 2. Scanner telemetry scoped to the target directory.
    scanner_findings: List[Dict[str, Any]] = []
    if target_dir is not None:
        resolved_target = str(resolve_path(target_dir))
        run = _ACTIVE_RUN.get()
        if run is not None and scanner_policy is None and run.target_dir == resolved_target:
            scanner_findings = [dict(item) for item in run.scanner_items]
        else:
            scanner_findings = collect_scanner_items(inventory, resolved_target, scanner_policy or SCANNERS_OFF, eff_date)
    for sf in scanner_findings:
        sf["item_id"] = f"POAM-{sys_abbr}-{item_counter:03d}"
        sf["milestone_id"] = f"M-{item_counter:03d}-1"
        items.append(sf)
        item_counter += 1

    # 2b. Blueprints inside the boundary that could not be parsed.
    unparsed_items = _collect_unparsed_blueprint_poam_items(inventory, sys_abbr, base_dt, item_counter)
    items.extend(unparsed_items)
    item_counter += len(unparsed_items)

    # 3. Ingest Pre-Recorded Scanner Findings (e.g. Cloud Security Command Center)
    for scc in inventory.get("scc_findings") or []:
        normalized = normalize_poam_item(scc, sys_abbr=sys_abbr, counter=item_counter, eff_date=eff_date)
        if normalized:
            items.append(normalized)
            item_counter += 1

    # 4. Evaluate Declarative IaC Architecture Rules against discovered components
    for rule in IAC_SECURITY_RULES:
        gap_item = rule.evaluate(inventory, sys_abbr, item_counter, base_dt)
        if gap_item:
            items.append(gap_item)
            item_counter += 1

    if not items:
        return []
    return consolidate_poam_items(items, sys_abbr=sys_abbr)


def _poam_group_key(item: Dict[str, Any]) -> str:
    """Computes the consolidation key for a POA&M item."""
    rule_id = str(item.get("rule_id") or "").strip()
    check_id = str(item.get("check_id") or "").strip()
    chk = str(item.get("checks") or "").strip()
    ctrl = str(item.get("control") or "").strip()
    title = str(item.get("title") or item.get("weakness_name") or item.get("desc") or "").strip()
    first_line = title.split("\n")[0].strip()
    norm_title = re.sub(r"(?<!\s)\s*\(\d+\s+affected\s+[^)(]+\)", "", first_line).strip()
    norm_title = re.sub(r"(?<!\s)\s*across\s+\d+\s+affected\s+[^\n]*", "", norm_title).strip()
    bracket_match = re.match(r"^\[([A-Za-z0-9_\-]+)\]", norm_title)
    if check_id:
        return f"CHECK:{check_id}"
    if bracket_match:
        return f"CHECK:{bracket_match.group(1)}"
    if chk.startswith(("CKV_", "CVE-", "CWE-", "GHSA-", "AVD-", "SCC-", "scc-")):
        return f"CHECK:{chk}"
    if rule_id:
        return f"RULE:{rule_id}"
    return f"CTRL:{ctrl}:{norm_title}"


def _collect_cluster_bullets(cluster: List[Dict[str, Any]]) -> List[str]:
    """Collects unique location/finding bullets across a POA&M cluster."""
    seen_bullets: Set[str] = set()
    bullets: List[str] = []
    for it in cluster:
        raw_desc = str(it.get("desc") or "")
        item_has_bullets = False
        for line in raw_desc.splitlines():
            s_line = line.strip()
            if s_line.startswith(("- ", "* ")):
                content = s_line.lstrip("-* ").strip()
                if content and content not in seen_bullets:
                    seen_bullets.add(content)
                    bullets.append(content)
                item_has_bullets = True
        if not item_has_bullets:
            clean_desc = raw_desc.strip()
            if clean_desc and clean_desc not in seen_bullets:
                seen_bullets.add(clean_desc)
                bullets.append(clean_desc)
    return bullets


def _merge_poam_group(cluster: List[Dict[str, Any]], counter: int, sys_abbr: str) -> Dict[str, Any]:
    """Merges a cluster of 2+ POA&M items sharing the same weakness signature."""
    base = dict(cluster[0])
    best_sev = max(
        (str(it.get("severity") or "Low").strip() for it in cluster),
        key=lambda s: SEVERITY_ORDER.get(s.upper(), 1),
    )
    valid_dates = [
        str(it["sched_date"]).strip()
        for it in cluster
        if it.get("sched_date") and len(str(it["sched_date"]).strip()) >= 10 and str(it["sched_date"]).strip()[0].isdigit()
    ]
    target_date = min(valid_dates) if valid_dates else base.get("sched_date", "")
    has_ongoing = any(str(it.get("status", "")).lower() in ("ongoing", "open", "in progress") for it in cluster)
    status = "Ongoing" if has_ongoing else base.get("status", "Ongoing")

    bullets = _collect_cluster_bullets(cluster)
    total_count = len(bullets)
    base_title = base.get("title") or base.get("weakness_name") or base.get("desc", "").splitlines()[0]
    clean_title = re.sub(r"(?<!\s)\s*across\s+\d+\s+affected\s+[^\n]*", "", base_title).strip()
    clean_title = re.sub(r"(?<!\s)\s*\(\d+\s+affected\s+[^)(]+\)", "", clean_title).strip().rstrip(":")

    if total_count > 1:
        short_title = f"{clean_title} ({total_count} affected locations)"
        bullet_lines = [f"  - {b}" for b in bullets[:25]]
        if total_count > 25:
            bullet_lines.append(f"  - ... and {total_count - 25} additional affected locations.")
        desc = f"{clean_title} across {total_count} affected locations:\n" + "\n".join(bullet_lines)
        m_desc = f"Remediate {total_count} affected locations across codebase. Verify configuration compliance across all affected modules."
    else:
        short_title = base_title
        desc = base.get("desc") or clean_title
        m_desc = base.get("milestone_desc") or f"Remediate finding: {clean_title}"

    is_high = best_sev in ("High", "Very High")
    base.update({
        "item_id": f"POAM-{sys_abbr}-{counter:03d}",
        "title": short_title,
        "weakness_name": short_title,
        "desc": desc,
        "weakness_description": desc,
        "severity": best_sev,
        "threat": "Moderate" if is_high else "Low",
        "likelihood": "Moderate" if is_high else "Low",
        "impact": "High" if is_high else ("Moderate" if best_sev in ("Moderate", "Medium") else "Low"),
        "status": status,
        "sched_date": target_date,
        "milestone_id": f"M-{counter:03d}-1",
        "milestone_desc": m_desc,
    })
    return base


def consolidate_poam_items(
    items: List[Dict[str, Any]],
    sys_abbr: str = "SYS",
) -> List[Dict[str, Any]]:
    """Groups and consolidates POA&M items that describe the same underlying weakness or check."""
    if not items:
        return []
    groups: Dict[str, List[Dict[str, Any]]] = {}
    group_order: List[str] = []
    for item in items:
        key = _poam_group_key(item)
        if key not in groups:
            groups[key] = []
            group_order.append(key)
        groups[key].append(item)

    consolidated: List[Dict[str, Any]] = []
    for counter, key in enumerate(group_order, 1):
        cluster = groups[key]
        if len(cluster) == 1:
            it = dict(cluster[0])
            it["item_id"] = f"POAM-{sys_abbr}-{counter:03d}"
            it["milestone_id"] = f"M-{counter:03d}-1"
            consolidated.append(it)
        else:
            consolidated.append(_merge_poam_group(cluster, counter, sys_abbr))
    return consolidated
