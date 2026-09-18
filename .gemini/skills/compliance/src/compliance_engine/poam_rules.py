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

import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

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


def normalize_poam_item(
    raw: Dict[str, Any],
    sys_abbr: str = "SYS",
    counter: int = 1,
    eff_date: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Standardizes a raw POA&M item into a canonical dictionary structure.

    Args:
        raw: Dictionary containing raw finding or concern attributes.
        sys_abbr: System abbreviation prefix for POA&M identifier generation.
        counter: Sequence index for unique ID assignment.
        eff_date: ISO date string for milestone calculation reference.

    Returns:
        A canonical dictionary formatted for Excel/YAML POA&M generation, or None
        if the input is invalid.
    """
    if not isinstance(raw, dict):
        return None

    today_dt = datetime.now()
    if not eff_date:
        eff_date = today_dt.strftime("%Y-%m-%d")
    try:
        base_dt = datetime.strptime(eff_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        base_dt = today_dt

    sched_base = max(today_dt, base_dt)
    date_90d = (sched_base + timedelta(days=90)).strftime("%Y-%m-%d")

    control = (
        raw.get("control_identifier")
        or raw.get("control")
        or "CA-05 Plan of Action and Milestones"
    )
    item_id = raw.get("item_id") or f"POAM-{sys_abbr}-{counter:03d}"
    w_name = str(raw.get("weakness_name") or "").strip()
    raw_desc = str(raw.get("desc") or raw.get("weakness_description") or "").strip()
    if w_name and raw_desc and w_name != raw_desc:
        desc = f"{w_name}: {raw_desc}" if w_name not in raw_desc else raw_desc
    else:
        desc = raw_desc or w_name or str(raw.get("title") or "").strip() or "Identified security concern or pending remediation"
    aps = raw.get("aps") or raw.get("control_enhancement") or (control.split()[0] if control else "CA-05")
    checks = raw.get("checks") or raw.get("cci") or "NIST-SP-800-53"
    raw_status = str(raw.get("status") or "Ongoing").strip()
    status_map = {
        "OPEN": "Ongoing",
        "ONGOING": "Ongoing",
        "IN PROGRESS": "Ongoing",
        "IN_PROGRESS": "Ongoing",
        "COMPLETED": "Completed",
        "CLOSED": "Completed",
        "RISK ACCEPTED": "Risk Accepted",
        "RISK_ACCEPTED": "Risk Accepted",
    }
    status = status_map.get(raw_status.upper(), raw_status.title())
    sched_date = raw.get("scheduled_completion_date") or raw.get("sched_date") or raw.get("target_date")
    if sched_date:
        if status == "Ongoing":
            try:
                s_dt = datetime.strptime(str(sched_date)[:10], "%Y-%m-%d")
            except (ValueError, TypeError) as err:
                # Do not emit an unusable date into the deliverable; fall back to the
                # same default used for a missing date so the POA&M stays actionable.
                logger.warning(
                    "POA&M finding %r has an unparseable scheduled completion date %r (%s); "
                    "substituting the default 90-day milestone %s.",
                    raw.get("item_id") or raw.get("finding_id") or counter,
                    sched_date,
                    err,
                    date_90d,
                )
                sched_date = date_90d
            else:
                if s_dt <= today_dt:
                    sched_date = date_90d
    else:
        sched_date = date_90d

    # Handle milestones structure (list of milestones or single string)
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

    m_status_map = {
        "OPEN": "Open",
        "ONGOING": "Ongoing",
        "IN PROGRESS": "Ongoing",
        "IN_PROGRESS": "Ongoing",
        "COMPLETED": "Completed",
        "CLOSED": "Closed",
    }
    m_status = m_status_map.get(raw_m_status.upper(), raw_m_status.title())

    source = (
        raw.get("source_of_weakness")
        or raw.get("source")
        or "Security Assessment & Continuous Monitoring"
    )
    raw_sev = str(raw.get("severity_risk_level") or raw.get("severity") or "Low").strip()
    sev_map = {
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
        "NONE": "None"
    }
    severity = sev_map.get(raw_sev.upper(), raw_sev.title())
    threat = raw.get("threat") or ("Moderate" if severity in {"High", "Very High"} else "Low")
    likelihood = raw.get("likelihood") or ("Moderate" if severity in {"High", "Very High"} else "Low")
    impact = raw.get("impact") or ("High" if severity in {"High", "Very High"} else "Moderate" if severity == "Moderate" else "Low")
    residual = raw.get("residual") or "Low"

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
        "check_id": str(raw.get("check_id") or "")
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

        sched_base = max(datetime.now(), base_dt)
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
    # 1. Unencrypted Storage Buckets (SC-28)
    SecurityConcernRule(
        rule_id="UNENCRYPTED_STORAGE",
        control="SC-28 Protection of Information at Rest (CMEK Hardening)",
        aps="SC-28(1)",
        checks="SRG-OS-000480",
        severity="Moderate",
        threat="Low",
        likelihood="Low",
        impact="Moderate",
        source="Security Assessment & Configuration Inspection",
        sched_days=60,
        eval_fn=lambda inv: [b.get("name") for b in inv.get("infrastructure_components", {}).get("storage_buckets", []) if b.get("cmek_encrypted") is False],
        desc_fn=lambda names: f"Enforce FIPS 140-3 CMEK encryption across standard Cloud Storage buckets: {', '.join(names[:3])}.",
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
            if (str(fw.get("direction", "")).upper() in ("INGRESS", "") and any(r in {"0.0.0.0/0", "::/0"} for r in fw.get("source_ranges", [])) and any(p in str(fw.get("ports", "")) for p in {"22", "3389", "80"}))
        ],
        desc_fn=lambda names: f"Restrict broad 0.0.0.0/0 ingress on non-HTTPS ports for firewall rules: {', '.join(names)}.",
        milestone_desc="Confine ingress rules to authorized management ranges (e.g. Cloud IAP 35.235.240.0/20) or authorized private interconnects."
    ),

    # 3. Unassigned Mandatory Personnel Governance Roles (PL-02, AC-02)
    SecurityConcernRule(
        rule_id="MISSING_ROLES",
        control="PL-02 / AC-02 Formal Cybersecurity Roles Appointment",
        aps="PL-02(1)",
        checks="NIST-PL-02",
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

    # 4. Software Cloud KMS Keys in IL5 / High Baseline (SC-12, SC-13)
    SecurityConcernRule(
        rule_id="SOFTWARE_KMS_IN_IL5",
        control="SC-12 / SC-13 Cloud HSM Hardware Cryptographic Key Enforcement",
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
            if (k.get("protection_level") or "").upper() == "SOFTWARE" and any(b in str(inv.get("system_information", {}).get("impact_level", "")).upper() or b in str(inv.get("system_information", {}).get("compliance_baseline", "")).upper() for b in {"IL5", "IL6", "DOD IL5", "FEDRAMP HIGH"})
        ],
        desc_fn=lambda keys: f"Upgrade Cloud KMS keys ({', '.join(keys[:2])}) from SOFTWARE to FIPS 140-3 Level 3 Cloud HSM.",
        milestone_desc="Provision FIPS 140-3 Level 3 HSM key ring in Cloud KMS and update Terraform CMEK references."
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
        aps="CP-09(1)",
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
        eval_fn=lambda inv: [c.get("name") for c in inv.get("infrastructure_components", {}).get("gke_clusters", []) if c.get("private_cluster") is False or c.get("private_endpoint") is False],
        desc_fn=lambda clusters: f"GKE cluster(s) {', '.join(clusters[:2])} have public control plane endpoints exposed.",
        milestone_desc="Configure private_cluster_config with enable_private_nodes = true and enable_private_endpoint = true."
    ),

    # 11. GKE Clusters without Workload Identity (AC-02, IA-02)
    SecurityConcernRule(
        rule_id="GKE_NO_WIF",
        control="AC-02 / IA-02 GKE Workload Identity Federation Enforcement",
        aps="IA-02(1)",
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

    # 12. Static Downloadable Service Account Keys (AC-02, IA-05)
    SecurityConcernRule(
        rule_id="STATIC_SA_KEYS",
        control="AC-02 / IA-05 Deprecate Static Long-Lived Service Account Keys",
        aps="IA-05(1)",
        checks="SRG-OS-000104",
        severity="High",
        threat="Moderate",
        likelihood="Moderate",
        impact="High",
        source="Identity & Access Governance Review",
        sched_days=30,
        eval_fn=lambda inv: [k.get("name", "key") for k in inv.get("infrastructure_components", {}).get("service_account_keys", [])],
        desc_fn=lambda keys: f"Static service account key resource(s) detected ({', '.join(keys[:2])}), introducing exfiltration risks.",
        milestone_desc="Delete static key resources and migrate workloads to Workload Identity Federation (WIF) or short-lived OAuth tokens."
    ),

    # 13. Unverified Asset Properties (CA-2 / RA-5)
    SecurityConcernRule(
        rule_id="DATA_GAP",
        control="CA-2 / RA-5 Continuous Monitoring Data Gaps",
        aps="CA-2(1)",
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


try:
    from .security_scanner_bridge import scan_and_derive_poam_items
except (ImportError, ValueError):
    try:
        from security_scanner_bridge import scan_and_derive_poam_items
    except ImportError:
        scan_and_derive_poam_items = None


def derive_poam_findings(
    inventory: Dict[str, Any],
    eff_date: Optional[str] = None,
    target_dir: Optional[str] = None,
    run_scanners: bool = True,
) -> List[Dict[str, Any]]:
    """Derives canonical POA&M items grounded strictly in architecture and telemetry.

    Ingests findings from:
    1. User-specified items or security concerns in configuration.
    2. Real scanner telemetry (Checkov IaC, Semgrep SAST, Trivy, SARIF, and SCC).
    3. Real IaC architectural security gaps detected across code.

    Returns an empty list if the system has no active deficiencies and no user-defined
    items. Never generates artificial filler or mock operational milestones.

    Args:
        inventory: Complete system inventory dictionary.
        eff_date: Optional ISO date string for effective authorization date.
        target_dir: Optional filesystem path to project root for live scanner runs.
        run_scanners: Whether to execute external static security scanners.

    Returns:
        List of standardized POA&M dictionaries ready for spreadsheet and YAML hydration.
    """
    if not eff_date:
        eff_date = (
            inventory.get("system_information", {}).get("effective_date")
            or datetime.now().strftime("%Y-%m-%d")
        )
    try:
        base_dt = datetime.strptime(eff_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        base_dt = datetime.now()

    sys_abbr = inventory.get("system_information", {}).get("system_abbreviation") or "SYS"
    items = []
    item_counter = 1

    # 1. Ingest User-Configured POA&M Items / Security Concerns / Findings
    user_items = (
        inventory.get("poam_items")
        or inventory.get("security_concerns")
        or inventory.get("findings")
        or []
    )
    for raw in user_items:
        normalized = normalize_poam_item(raw, sys_abbr=sys_abbr, counter=item_counter, eff_date=eff_date)
        if normalized:
            items.append(normalized)
            item_counter += 1

    # 2. Ingest Live Scanner Telemetry (Checkov IaC, Semgrep SAST, SARIF)
    target_path = target_dir or inventory.get("system_information", {}).get("workspace_path")
    raw_scanner_cfg = inventory.get("security_scanners", {})
    scanner_cfg = dict(raw_scanner_cfg) if isinstance(raw_scanner_cfg, dict) else {}
    sys_info_dict = inventory.get("system_information", {}) or {}
    if "impact_level" not in scanner_cfg:
        scanner_cfg["impact_level"] = inventory.get("impact_level") or sys_info_dict.get("impact_level")
    if "system_information" not in scanner_cfg:
        scanner_cfg["system_information"] = sys_info_dict
    if "project_id" not in scanner_cfg:
        scanner_cfg["project_id"] = inventory.get("project_id") or sys_info_dict.get("project_id")
    scanner_enabled = scanner_cfg.get("enabled", True)

    if target_path and os.path.isdir(target_path) and scanner_enabled and run_scanners and scan_and_derive_poam_items:
        scanner_findings = scan_and_derive_poam_items(target_path, sys_abbr=sys_abbr, eff_date=eff_date, config=scanner_cfg)
        for sf in scanner_findings:
            sf["item_id"] = f"POAM-{sys_abbr}-{item_counter:03d}"
            sf["milestone_id"] = f"M-{item_counter:03d}-1"
            items.append(sf)
            item_counter += 1

    # 2b. Blueprints inside the boundary that could not be parsed.
    #
    # A parse failure previously produced only a log line. Every resource in the
    # affected file was then absent from the SSP, the SCTM and the architecture
    # reconciliation, with nothing anywhere in the package indicating that part
    # of the boundary had never been read. Silence here reads to an Authorizing
    # Official as an assessed-and-clean boundary.
    include_unparsed = True
    comp_cfg = inventory.get("compliance_config") or {}
    if "include_unparsed_blueprints_in_poam" in comp_cfg:
        include_unparsed = bool(comp_cfg["include_unparsed_blueprints_in_poam"])
    elif "include_unparsed_blueprints_in_poam" in inventory:
        include_unparsed = bool(inventory["include_unparsed_blueprints_in_poam"])
    elif "include_unparsed_blueprints_in_poam" in sys_info_dict:
        include_unparsed = bool(sys_info_dict["include_unparsed_blueprints_in_poam"])

    if include_unparsed:
        unparsed = (
            (inventory.get("infrastructure_components") or {}).get("unparsed_terraform_files")
            or []
        )
        for entry in unparsed:
            if not isinstance(entry, dict):
                continue
            rel_path = str(entry.get("path") or "").strip()
            if not rel_path:
                continue
            diagnostic = " ".join(str(entry.get("error") or "").split())[:300]
            title = (
                f"Terraform blueprint '{rel_path}' could not be parsed; its resources "
                f"are absent from the authorization boundary."
            )
            desc = (
                f"{title} The infrastructure-as-code discovery engine failed to build "
                f"an abstract syntax tree for this file, so any project, network, "
                f"service account, key, or firewall rule it declares is missing from "
                f"the System Security Plan, the SCTM, and the architecture "
                f"reconciliation. The boundary described in this package is therefore "
                f"incomplete by an unknown amount."
            )
            if diagnostic:
                desc = f"{desc} Parser diagnostic: {diagnostic}"
            items.append({
                "control": (
                    "CA-02 / RA-05 Security Assessment and Vulnerability Monitoring "
                    "(Authorization Boundary Discovery Gap)"
                ),
                "item_id": f"POAM-{sys_abbr}-{item_counter:03d}",
                "title": title,
                "desc": desc,
                "aps": "CA-02 / RA-05",
                "checks": "CA-02 / RA-05",
                "status": "Ongoing",
                "sched_date": (base_dt + timedelta(days=30)).strftime("%Y-%m-%d"),
                "milestone_id": f"M-{item_counter:03d}-1",
                "milestone_desc": (
                    f"Resolve the parse failure in '{rel_path}' (or confirm the file is "
                    f"outside the authorization boundary), re-run discovery, and verify "
                    f"the resources it declares appear in the SSP and SCTM."
                ),
                "milestone_status": "Open",
                "source": "IaC Discovery Engine",
                "severity": "Moderate",
                "threat": "Low",
                "likelihood": "Low",
                "impact": "Moderate",
                "residual": "Moderate",
            })
            item_counter += 1

    # 3. Ingest Pre-Recorded Scanner Findings (e.g. Cloud Security Command Center)
    scc_findings = inventory.get("scc_findings") or []
    for scc in scc_findings:
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

    # Clean system = empty list. Zero fake filler.
    if not items:
        return []

    # 5. Consolidate items sharing the same check or weakness across multiple locations
    return consolidate_poam_items(items, sys_abbr=sys_abbr)


def consolidate_poam_items(
    items: List[Dict[str, Any]],
    sys_abbr: str = "SYS",
) -> List[Dict[str, Any]]:
    """Groups and consolidates POA&M items that describe the same underlying weakness or check.

    Consolidates findings sharing the same check/rule identifier (e.g. Checkov, Semgrep,
    CVE, or exact weakness title) into a unified item with an itemized breakdown of all
    affected code locations and resources. Renumbers items with sequential identifiers.

    Args:
        items: List of normalized POA&M finding dictionaries.
        sys_abbr: System abbreviation for sequential item ID generation.

    Returns:
        Deduplicated and consolidated list of POA&M items.
    """
    if not items:
        return []

    # Map groups preserving encounter order
    groups: Dict[str, List[Dict[str, Any]]] = {}
    group_order: List[str] = []

    for item in items:
        rule_id = str(item.get("rule_id") or "").strip()
        check_id = str(item.get("check_id") or "").strip()
        chk = str(item.get("checks") or "").strip()
        ctrl = str(item.get("control") or "").strip()
        title = str(item.get("title") or item.get("weakness_name") or item.get("desc") or "").strip()
        first_line = title.split("\n")[0].strip()
        norm_title = re.sub(r"\s*\(\d+\s+affected\s+[^)]+\)", "", first_line).strip()
        norm_title = re.sub(r"\s*across\s+\d+\s+affected\s+[^\n]*", "", norm_title).strip()

        # Check for bracketed check ID in title, e.g. [CKV_GCP_74] or [CVE-2023-1234]
        bracket_match = re.match(r"^\[([A-Za-z0-9_\-]+)\]", norm_title)

        if check_id:
            key = f"CHECK:{check_id}"
        elif bracket_match:
            key = f"CHECK:{bracket_match.group(1)}"
        elif chk.startswith(("CKV_", "CVE-", "CWE-", "GHSA-", "AVD-", "SCC-", "scc-")):
            key = f"CHECK:{chk}"
        elif rule_id:
            key = f"RULE:{rule_id}"
        else:
            # Group by control + normalized first line of description/title
            key = f"CTRL:{ctrl}:{norm_title}"

        if key not in groups:
            groups[key] = []
            group_order.append(key)
        groups[key].append(item)

    consolidated: List[Dict[str, Any]] = []
    counter = 1

    for key in group_order:
        cluster = groups[key]
        if len(cluster) == 1:
            it = dict(cluster[0])
            it["item_id"] = f"POAM-{sys_abbr}-{counter:03d}"
            it["milestone_id"] = f"M-{counter:03d}-1"
            consolidated.append(it)
            counter += 1
            continue

        # Merge multiple items representing the same check/weakness
        base = dict(cluster[0])

        # Highest severity
        best_sev = "Low"
        best_w = -1
        for it in cluster:
            s = str(it.get("severity") or "Low").strip()
            w = SEVERITY_ORDER.get(s.upper(), 1)
            if w > best_w:
                best_w = w
                best_sev = s

        # Earliest scheduled completion date
        sched_dates = [str(it.get("sched_date") or "").strip() for it in cluster if it.get("sched_date")]
        valid_dates = [d for d in sched_dates if len(d) >= 10 and d[0].isdigit()]
        target_date = min(valid_dates) if valid_dates else base.get("sched_date", "")

        # Status: Ongoing if any is ongoing
        has_ongoing = any(str(it.get("status", "")).lower() in ("ongoing", "open", "in progress") for it in cluster)
        status = "Ongoing" if has_ongoing else base.get("status", "Ongoing")

        # Collect unique bullet points across all items
        seen_bullets = set()
        bullets = []
        for it in cluster:
            raw_desc = str(it.get("desc") or "")
            lines = raw_desc.splitlines()
            item_has_bullets = False
            for line in lines:
                s_line = line.strip()
                if s_line.startswith("- ") or s_line.startswith("* "):
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

        total_count = len(bullets)
        base_title = base.get("title") or base.get("weakness_name") or base.get("desc", "").splitlines()[0]
        clean_title = re.sub(r"\s*across\s+\d+\s+affected\s+[^\n]*", "", base_title).strip()
        clean_title = re.sub(r"\s*\(\d+\s+affected\s+[^)]+\)", "", clean_title).strip()
        clean_title = clean_title.rstrip(":")

        if total_count > 1:
            short_title = f"{clean_title} ({total_count} affected locations)"
            bullet_lines = []
            max_disp = 25
            for b in bullets[:max_disp]:
                bullet_lines.append(f"  - {b}")
            if total_count > max_disp:
                bullet_lines.append(f"  - ... and {total_count - max_disp} additional affected locations.")
            desc = f"{clean_title} across {total_count} affected locations:\n" + "\n".join(bullet_lines)
            m_desc = f"Remediate {total_count} affected locations across codebase. Verify configuration compliance across all affected modules."
        else:
            short_title = base_title
            desc = base.get("desc") or clean_title
            m_desc = base.get("milestone_desc") or f"Remediate finding: {clean_title}"

        base["item_id"] = f"POAM-{sys_abbr}-{counter:03d}"
        base["title"] = short_title
        base["weakness_name"] = short_title
        base["desc"] = desc
        base["weakness_description"] = desc
        base["severity"] = best_sev
        base["threat"] = "Moderate" if best_sev in ("High", "Very High") else "Low"
        base["likelihood"] = "Moderate" if best_sev in ("High", "Very High") else "Low"
        base["impact"] = "High" if best_sev in ("High", "Very High") else "Moderate" if best_sev in ("Moderate", "Medium") else "Low"
        base["status"] = status
        base["sched_date"] = target_date
        base["milestone_id"] = f"M-{counter:03d}-1"
        base["milestone_desc"] = m_desc
        consolidated.append(base)
        counter += 1

    return consolidated


generate_canonical_poam_items = derive_poam_findings

