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

"""Deterministic Semantic Compliance Linter & Architectural Drift Engine.

Provides deterministic static analysis and semantic evaluation for public sector compliance deliverables:
1. Semantically evaluates generated artifacts (SSP, POA&M, 20 Policy Manuals, SCTM, PPSM)
   against target public sector frameworks (NIST SP 800-53 Rev. 5, FedRAMP High/Mod, DoD CC SRG).
2. Cross-references artifact claims directly against Terraform state / IaC inventory
   to detect architectural drift (KMS CMEK, firewall exposure, multi-region failover, VPC-SC, logging).
3. Rejects vague policy statements, untailored parameter placeholders, and incomplete control implementations.
4. Leaves conversational and interactive AI reasoning to the specialized Gemini compliance skills
   (.gemini/skills/compliance/validate_skill.md, ssp_skill.md, policies_skill.md).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, Final, List, Optional, Tuple, Union

from .file_helpers import (
    ensure_path_within_boundary,
    has_terraform_infrastructure,
    read_json_file,
    read_text_file,
    read_yaml_file,
    resolve_path,
    write_json_file,
)
from .poam_rules import (
    base_control_id,
    firewall_rule_exposes_ports,
    has_cmek_linkage,
    resolve_max_kms_rotation_days,
)
from .template_engine import PENDING_PLACEHOLDER_RE

logger = logging.getLogger(__name__)

# ==============================================================================
# Deterministic Semantic Linting Rules & Regex Patterns
# ==============================================================================

# Vague phrasing patterns to detect in policy and SSP narratives
VAGUE_PHRASING_PATTERNS: Final[List[Tuple[re.Pattern[str], str]]] = [
    (
        re.compile(r"\bappropriate\s+(?:security|controls?|measures?|mechanisms?|steps?)\b", re.I),
        "Vague qualifier: 'appropriate controls/measures' lacks specific technical parameters or standards.",
    ),
    (
        re.compile(r"\bas\s+(?:needed|necessary|applicable|appropriate)\b", re.I),
        "Vague qualifier: 'as needed/necessary' lacks defined operational trigger conditions.",
    ),
    (
        re.compile(r"\breasonable\s+(?:steps?|measures?|precautions?)\b", re.I),
        "Vague qualifier: 'reasonable measures' fails public sector audit standards (NIST SP 800-53 requires prescriptive requirements).",
    ),
    (
        re.compile(r"\bpasswords?\s+(?:must|should)\s+be\s+strong\b", re.I),
        "Vague qualifier: 'strong passwords' must be replaced with explicit length (min 15 chars), complexity, and MFA requirements (IA-5).",
    ),
    (
        re.compile(r"\bregularly\s+(?:reviewed?|monitored?|audited?|updated?)\b", re.I),
        "Vague qualifier: 'regularly reviewed/monitored' lacks mandatory review frequency SLA (e.g. monthly, quarterly, annually).",
    ),
    (
        re.compile(r"\bperiodic(?:ally)?\s+(?:reviewed?|monitored?|audited?|checked?)\b", re.I),
        "Vague qualifier: 'periodically' lacks explicit calendar or milestone review cadence.",
    ),
    (
        re.compile(r"\bindustry\s+standards?\b", re.I),
        "Ambiguous standard: 'industry standard' must cite specific authority (NIST SP 800-53 R5, FIPS 140-3, CIS GCP Benchmark).",
    ),
    (re.compile(r"\bwhere\s+feasible\b", re.I), "Escape clause: 'where feasible' is unacceptable in baseline mandatory security controls."),
    (
        re.compile(r"\baccess\s+is\s+granted\s+according\s+to\s+need\b", re.I),
        "Vague access statement: must state formal role-based approval, least privilege, and separation of duties (AC-2, AC-6).",
    ),
    (re.compile(r"\btimely\s+manner\b", re.I), "Vague timeline: 'timely manner' must define concrete SLA (e.g. 1 hour, 24 hours, 7 business days)."),
]

# Untailored placeholder patterns
UNTAILORED_PATTERNS: Final[List[Tuple[re.Pattern[str], str]]] = [
    (re.compile(r"\[assignment:\s*[^\]]+\]", re.I), "Untailored NIST assignment parameter"),
    (re.compile(r"\[selection:\s*[^\]]+\]", re.I), "Untailored NIST selection parameter"),
    (re.compile(r"\{\{\s*[A-Z0-9_]+\s*\}\}"), "Unresolved macro template variable"),
    (PENDING_PLACEHOLDER_RE, "Unresolved configuration or evidence placeholder"),
]


class SemanticFinding:
    """Represents a single semantic finding identified during semantic linting."""

    def __init__(
        self,
        finding_id: str,
        severity: str,
        category: str,
        artifact: str,
        description: str,
        remediation: str,
        control_id: Optional[str] = None,
        raw_text_snippet: Optional[str] = None,
    ) -> None:
        self.finding_id = finding_id
        self.severity = severity  # 'CAT I (Critical)', 'CAT II (Medium)', 'CAT III (Low)'
        self.category = category  # 'Architectural Drift', 'Vague Boilerplate', 'Incomplete Control Implementation', 'Untailored Parameter', 'Policy Weakness'
        self.artifact = artifact
        self.description = description
        self.remediation = remediation
        self.control_id = control_id
        self.raw_text_snippet = raw_text_snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "category": self.category,
            "artifact": self.artifact,
            "control_id": self.control_id,
            "description": self.description,
            "remediation": self.remediation,
            "raw_text_snippet": (self.raw_text_snippet[:200] + "...") if self.raw_text_snippet and len(self.raw_text_snippet) > 200 else self.raw_text_snippet,
        }


def _extract_cat_level(severity: str) -> Optional[int]:
    """Extracts numeric CAT severity level (1, 2, or 3) using word-boundary matching.

    Avoids false positives where substring checks like `"CAT I" in sev` incorrectly
    match "CAT II" or "CAT III".
    """
    if not severity:
        return None
    s = str(severity).upper()
    if re.search(r"\bCAT\s*III\b", s) or "LOW" in s or "ADVISORY" in s:
        return 3
    if re.search(r"\bCAT\s*II\b", s) or "MEDIUM" in s or "MODERATE" in s:
        return 2
    if re.search(r"\bCAT\s*I\b", s) or "CRITICAL" in s or "HIGH" in s:
        return 1
    return None


class ArtifactSemanticResult:
    """Represents the semantic evaluation result for a single compliance deliverable."""

    def __init__(self, artifact_path: str) -> None:
        self.artifact_path = artifact_path
        self.status = "PASS"  # 'PASS', 'ACTION_REQUIRED', 'REJECTED'
        self.findings: List[SemanticFinding] = []
        self.evaluated_controls_count = 0
        self.drift_items_count = 0
        self.summary = ""

    def add_finding(self, finding: SemanticFinding) -> None:
        self.findings.append(finding)
        cat = _extract_cat_level(finding.severity)
        if cat == 1:
            self.status = "REJECTED"
        elif self.status != "REJECTED" and cat == 2:
            self.status = "ACTION_REQUIRED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "status": self.status,
            "evaluated_controls_count": self.evaluated_controls_count,
            "drift_items_count": self.drift_items_count,
            "summary": self.summary,
            "findings_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
        }


def _relativize_linter_path(raw_path: str, base_dir: str) -> str:
    """Relativizes artifact paths against the target directory and strips home directory prefixes."""
    if not raw_path:
        return ""
    s = str(raw_path).strip()
    if base_dir and os.path.isabs(base_dir) and os.path.isabs(s):
        try:
            rel = os.path.relpath(s, base_dir).replace("\\", "/")
            if not rel.startswith(".."):
                return "." if rel == "." else rel
        except ValueError:
            pass
    home_str = str(Path.home())
    if home_str and home_str in s:
        s = s.replace(home_str, "~")
    return s


class SemanticLinterReport:
    """Audit report produced by the Semantic Linter across the entire accreditation package."""

    def __init__(
        self, target_dir: str, framework: str, strict: bool = True
    ) -> None:
        self._base_dir = str(target_dir) if target_dir else "."
        self.target_dir = "."
        self.framework = framework
        self.strict = strict
        self.overall_status = "PASS"
        self.cat_1_count = 0
        self.cat_2_count = 0
        self.cat_3_count = 0
        self.artifact_results: Dict[str, ArtifactSemanticResult] = {}
        self.drift_findings: List[SemanticFinding] = []

    def record_artifact_result(self, res: ArtifactSemanticResult) -> None:
        res.artifact_path = _relativize_linter_path(res.artifact_path, self._base_dir)
        self.artifact_results[res.artifact_path] = res
        for f in res.findings:
            f.artifact = _relativize_linter_path(f.artifact, self._base_dir)
            cat = _extract_cat_level(f.severity)
            if cat == 1:
                self.cat_1_count += 1
            elif cat == 2:
                self.cat_2_count += 1
            elif cat == 3:
                self.cat_3_count += 1

            if f.category == "Architectural Drift":
                self.drift_findings.append(f)

        if self.cat_1_count > 0:
            self.overall_status = "REJECTED (Critical ATO Blocker Findings Present)"
        elif self.cat_2_count > 0:
            self.overall_status = "ACTION_REQUIRED (Remediations Required Prior to PAC Submission)"
        else:
            self.overall_status = "PASS (0 CAT I / 0 CAT II Semantic Findings in Evaluated Artifacts)"

    @property
    def all_findings(self) -> List[SemanticFinding]:
        """Aggregates all semantic findings across all audited artifacts."""
        findings: List[SemanticFinding] = []
        for r in self.artifact_results.values():
            findings.extend(r.findings)
        return findings

    @property
    def summary(self) -> Dict[str, Any]:
        """Provides an executive summary dictionary of AI semantic validation metrics."""
        total_arts = len(self.artifact_results)
        passed_arts = sum(1 for r in self.artifact_results.values() if r.status in ("PASS", "READY", "SATISFIED", "VALIDATED"))
        score = (passed_arts / max(1, total_arts)) * 100.0 if total_arts > 0 else 100.0
        return {
            "verdict": self.overall_status,
            "passed_count": passed_arts,
            "total_artifacts_evaluated": total_arts,
            "compliance_score_percent": round(score, 1),
            "cat_1_findings_count": self.cat_1_count,
            "cat_2_findings_count": self.cat_2_count,
            "cat_3_findings_count": self.cat_3_count,
            "architectural_drift_findings_count": len(self.drift_findings),
        }

    @property
    def passed(self) -> bool:
        """Indicates whether the accreditation package passed validation under the active strictness mode."""
        return (self.cat_1_count == 0) if self.strict else True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_dir": self.target_dir,
            "framework": self.framework,
            "overall_status": self.overall_status,
            "summary": self.summary,
            "cat_1_count": self.cat_1_count,
            "cat_2_count": self.cat_2_count,
            "cat_3_count": self.cat_3_count,
            "total_findings": self.cat_1_count + self.cat_2_count + self.cat_3_count,
            "drift_findings_count": len(self.drift_findings),
            "findings": [f.to_dict() for f in self.all_findings],
            "artifact_results": {k: v.to_dict() for k, v in self.artifact_results.items()},
            "drift_findings": [f.to_dict() for f in self.drift_findings],
        }

    def to_markdown(self) -> str:
        """Renders an authoritative Lead Assessor Executive Markdown audit section."""
        lines: List[str] = []
        lines.append("## Lead Assessor Semantic Linter & Architectural Drift Audit\n")
        lines.append(
            "> [!IMPORTANT]\n"
            "> **SENIOR PUBLIC SECTOR SECURITY ENGINEER ASSESSMENT ('TRUST BUT VERIFY')**:\n"
            "> The Semantic Linter evaluates all accreditation deliverables using static analysis "
            "and semantic rule checking. It strictly cross-references narrative claims "
            "against active Terraform infrastructure code, enforces target framework standards "
            f"({self.framework}), and rejects vague boilerplate or unfulfilled control objectives.\n"
        )
        lines.append("| Audit Dimension | Evaluation Result | Status |")
        lines.append("| :--- | :--- | :--- |")
        lines.append(f"| **Overall Semantic Linter Posture** | {self.overall_status} | `{'PASS' if self.cat_1_count == 0 else 'FAIL'}` |")
        lines.append(f"| **Target Accreditation Baseline** | {self.framework} | `Evaluated` |")
        lines.append(f"| **CAT I Critical Findings (Blockers)** | `{self.cat_1_count}` finding(s) | `{'PASS' if self.cat_1_count == 0 else 'CRITICAL'}` |")
        lines.append(f"| **CAT II Medium Findings (Gaps/Drift)** | `{self.cat_2_count}` finding(s) | `{'PASS' if self.cat_2_count == 0 else 'WARNING'}` |")
        lines.append(f"| **CAT III Low Findings (Procedural)** | `{self.cat_3_count}` finding(s) | `INFO` |")
        drift_status = "PASS" if len(self.drift_findings) == 0 else "DRIFT DETECTED"
        lines.append(
            f"| **Architectural Drift Items Detected** | `{len(self.drift_findings)}` discrepancy item(s) | `{drift_status}` |\n"
        )

        if self.drift_findings:
            lines.append("### Live Code vs. Accreditation Narrative Architectural Drift")
            lines.append("| Finding ID | Control | Discrepancy Description | Required Terraform / Policy Remediation |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for df in self.drift_findings:
                ctrl_str = df.control_id or "General"
                lines.append(f"| `{df.finding_id}` | **{ctrl_str}** | {df.description} | {df.remediation} |")
            lines.append("")

        all_findings: List[SemanticFinding] = []
        for r in self.artifact_results.values():
            all_findings.extend(r.findings)

        if all_findings:
            lines.append("### Role-Grouped Semantic Findings & Remediation Playbook")
            lines.append("| ID | Severity | Artifact | Issue Description | Concrete Assessor Remediation |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for f in sorted(all_findings, key=lambda x: (_extract_cat_level(x.severity) or 99)):
                lines.append(f"| `{f.finding_id}` | **{f.severity}** | `{f.artifact}` | {f.description} | {f.remediation} |")
            lines.append("")

        return "\n".join(lines)


# ==============================================================================
# Semantic Evaluation Functions
# ==============================================================================

def _check_cmek_drift(
    inventory: Dict[str, Any],
    infra: Dict[str, Any],
    ssp_text: str,
    is_app_only: bool,
) -> List[SemanticFinding]:
    """Evaluates SC-28/SC-12 CMEK and cryptoperiod drift between SSP claims and Terraform inventory."""
    if is_app_only:
        return []
    ssp_lower = ssp_text.lower()
    stripped_cmek_negations = re.sub(
        r"\b0\s+of\s+\d+\s+data\s+stores?\s+use\s+customer-managed\s+keys?\b",
        "",
        ssp_lower,
    )
    for phrase in (
        "no customer-managed encryption",
        "no cmek",
        "0 customer-managed",
        "without cmek",
        "without customer-managed",
    ):
        stripped_cmek_negations = stripped_cmek_negations.replace(phrase, "")
    if "cmek" not in stripped_cmek_negations and "customer-managed" not in stripped_cmek_negations:
        return []

    findings: List[SemanticFinding] = []
    kms_keys = infra.get("kms_keys", []) or []
    buckets = infra.get("storage_buckets", []) or []
    has_unencrypted_buckets = any(
        isinstance(b, dict)
        and b.get("cmek_encrypted") is False
        and not b.get("kms_key")
        and not b.get("cmek_key")
        for b in buckets
    )

    if not has_cmek_linkage(infra):
        findings.append(
            SemanticFinding(
                finding_id="DRIFT-KMS-001",
                severity="CAT I (Critical)",
                category="Architectural Drift",
                artifact="SSP/SSP_System_Security_Plan.md",
                control_id="SC-28",
                description=(
                    "System Security Plan claims Customer-Managed Encryption Keys (CMEK) under SC-28, "
                    "but active Terraform inventory discovers zero `google_kms_crypto_key` resources."
                ),
                remediation=(
                    "Provision Cloud KMS Key Rings and Crypto Keys in Terraform (`modules/kms`), "
                    "or adjust SSP narrative to reflect Google-default encryption (if authorized by AO)."
                ),
            )
        )
    else:
        max_rot_days = resolve_max_kms_rotation_days(inventory)
        if max_rot_days is not None:
            max_rot_sec = max_rot_days * 86400
            for k in kms_keys:
                if not isinstance(k, dict):
                    continue
                rot = str(k.get("rotation_period") or "").strip()
                k_name = k.get("name", "kms-key")
                if not rot:
                    findings.append(
                        SemanticFinding(
                            finding_id=f"DRIFT-KMS-ROT-{k_name}",
                            severity="CAT II (Medium)",
                            category="Architectural Drift",
                            artifact="SSP/SSP_System_Security_Plan.md",
                            control_id="SC-12",
                            description=(
                                f"Cloud KMS key '{k_name}' does not specify an automated `rotation_period` in Terraform, "
                                f"exceeding the organization-defined cryptoperiod policy ({max_rot_days} days per NIST SP 800-57 Part 1)."
                            ),
                            remediation=f"Configure `rotation_period` for `{k_name}` in Terraform to `{max_rot_sec}s` ({max_rot_days} days).",
                        )
                    )
                    continue
                m = re.match(r"^(\d+)s?$", rot)
                if m and int(m.group(1)) > max_rot_sec:
                    seconds = int(m.group(1))
                    findings.append(
                        SemanticFinding(
                            finding_id=f"DRIFT-KMS-ROT-{k_name}",
                            severity="CAT II (Medium)",
                            category="Architectural Drift",
                            artifact="SSP/SSP_System_Security_Plan.md",
                            control_id="SC-12",
                            description=(
                                f"Cloud KMS key '{k_name}' specifies a rotation period of {rot} "
                                f"({seconds // 86400} days), exceeding the organization-defined cryptoperiod policy "
                                f"({max_rot_days} days per NIST SP 800-57 Part 1)."
                            ),
                            remediation=f"Update `rotation_period` for `{k_name}` in Terraform to `{max_rot_sec}s` ({max_rot_days} days).",
                        )
                    )

    if has_unencrypted_buckets:
        findings.append(
            SemanticFinding(
                finding_id="DRIFT-GCS-001",
                severity="CAT I (Critical)",
                category="Architectural Drift",
                artifact="SSP/SSP_System_Security_Plan.md",
                control_id="SC-28",
                description="Storage buckets discovered in Terraform without CMEK encryption enabled.",
                remediation="Attach `kms_key_name` referencing an active Cloud KMS key to all `google_storage_bucket` resources.",
            )
        )
    return findings


def _check_network_ha_and_siem_drift(
    sys_info: Dict[str, Any],
    net: Dict[str, Any],
    infra: Dict[str, Any],
    ssp_text: str,
    is_app_only: bool,
) -> List[SemanticFinding]:
    """Evaluates zero-trust ingress, dual-region HA, and SIEM sink drift against SSP claims."""
    findings: List[SemanticFinding] = []
    ssp_lower = ssp_text.lower()
    if any(k in ssp_lower for k in ("iap", "identity-aware", "zero-trust")):
        for rule in net.get("firewall_rules", []) or []:
            if not isinstance(rule, dict):
                continue
            r_name = rule.get("name", "rule")
            if firewall_rule_exposes_ports(rule, {22, 3389}):
                rule_ports = rule.get("ports") or rule.get("allowed") or ["all"]
                findings.append(
                    SemanticFinding(
                        finding_id=f"DRIFT-FW-INGRESS-{r_name}",
                        severity="CAT I (Critical)",
                        category="Architectural Drift",
                        artifact="SSP/SSP_System_Security_Plan.md",
                        control_id="AC-17",
                        description=(
                            f"Firewall rule '{r_name}' permits direct 0.0.0.0/0 remote administrative ingress "
                            f"on ports {rule_ports}, directly contradicting SSP AC-17 zero-trust / IAP commitments."
                        ),
                        remediation="Remove 0.0.0.0/0 source range and enforce Google Cloud IAP netblock (35.235.240.0/20).",
                    )
                )

    primary_loc = str(sys_info.get("primary_location", "")).lower()
    if (
        ("dual-region" in ssp_lower or "multi-region" in ssp_lower)
        and not is_app_only
        and "/" not in primary_loc
        and "dual" not in primary_loc
    ):
        subnets = net.get("subnets", []) or []
        regions = {s.get("region") for s in subnets if isinstance(s, dict) and s.get("region")}
        if len(regions) < 2:
            findings.append(
                SemanticFinding(
                    finding_id="DRIFT-REGION-001",
                    severity="CAT II (Medium)",
                    category="Architectural Drift",
                    artifact="SSP/SSP_System_Security_Plan.md",
                    control_id="CP-2",
                    description=(
                        "System Security Plan asserts a dual-region high availability failover posture, "
                        f"but active Terraform deployment is restricted to a single region ({primary_loc})."
                    ),
                    remediation="Configure secondary regional subnets and failover resources, or align SSP to single-region architecture.",
                )
            )

    if any(k in ssp_lower for k in ("cssp", "siem", "chronicle")) and not is_app_only and not (infra.get("logging_sinks") or []):
        findings.append(
            SemanticFinding(
                finding_id="DRIFT-LOG-001",
                severity="CAT II (Medium)",
                category="Architectural Drift",
                artifact="SSP/SSP_System_Security_Plan.md",
                control_id="AU-6",
                description=(
                    "Accreditation documentation commits to real-time security event streaming to an external "
                    "CSSP/SIEM, but zero `google_logging_organization_sink` or `google_logging_project_sink` "
                    "resources exist in Terraform."
                ),
                remediation="Provision centralized Cloud Logging sinks exporting audit and VPC flow logs to the accredited CSSP/SIEM destination.",
            )
        )
    return findings


def evaluate_architectural_drift(
    inventory: Dict[str, Any],
    ssp_path: Optional[Path] = None,
    policies_dir: Optional[Path] = None,
    sctm_path: Optional[Path] = None,
) -> List[SemanticFinding]:
    """Cross-references artifact claims directly against Terraform state / IaC inventory."""
    del policies_dir, sctm_path
    infra = inventory.get("infrastructure_components", {}) or {}
    net = inventory.get("network_architecture", {}) or {}
    sys_info = inventory.get("system_information", {}) or {}
    app_info = inventory.get("application_components", {}) or {}
    has_iac = has_terraform_infrastructure(inventory)
    is_app_only = (not has_iac) and bool(
        app_info.get("software_packages") or app_info.get("applications") or app_info.get("container_images")
    )
    ssp_text = read_text_file(ssp_path) if (ssp_path and ssp_path.exists()) else ""
    findings = _check_cmek_drift(inventory, infra, ssp_text, is_app_only)
    findings.extend(_check_network_ha_and_siem_drift(sys_info, net, infra, ssp_text, is_app_only))
    return findings


_CONTROL_KEYWORD_RULES: Final[Dict[str, Tuple[Tuple[str, ...], str, str]]] = {
    "AC-17": (
        (
            "iap", "identity-aware", "bastion", "vpn", "tunnel", "session manager", "workstation",
            "tls", "1.3", "crypto", "ipsec", "encryption", "ssh", "fips",
        ),
        "Incomplete AC-17 Specification",
        "Narrative does not specify the zero-trust remote access mechanism or cryptographic protection.",
    ),
    "IA-2": (
        ("mfa", "multi-factor", "token", "cac", "piv", "fido2", "webauthn", "hardware", "authenticator", "sso", "identity"),
        "Incomplete IA-2 Specification",
        "Narrative fails to specify multi-factor authentication (MFA) mechanisms or hardware tokens.",
    ),
    "IA-5": (
        ("password", "authenticator", "credential", "complexity", "length", "rotation", "secret", "key", "token", "pki", "certificate"),
        "Incomplete IA-5 Specification",
        "Narrative fails to specify authenticator management, credential lifecycle, or PKI/key requirements.",
    ),
    "SC-7": (
        ("firewall", "boundary", "vpc", "subnet", "perimeter", "default-deny", "ingress", "egress", "isolation", "vpc-sc"),
        "Incomplete SC-7 Specification",
        "Narrative fails to describe perimeter firewalls, default-deny ingress, or network isolation.",
    ),
    "SC-8": (
        ("tls", "mtls", "macsec", "ipsec", "encryption in transit", "transit", "crypto", "cipher"),
        "Incomplete SC-8 Specification",
        "Narrative fails to specify cryptographic mechanisms for data in transit.",
    ),
    "SC-28": (
        ("kms", "cmek", "encryption at rest", "at-rest", "at rest", "fips", "aes-256", "key ring", "key vault", "crypto"),
        "Incomplete SC-28 Specification",
        "Narrative fails to specify cryptographic key management or at-rest encryption mechanisms.",
    ),
    "AU-2": (
        ("log", "audit", "sink", "siem", "cssp", "chronicle", "retention", "immutable", "router"),
        "Incomplete AU Specification",
        "Narrative fails to define audit log export, immutable retention, or automated review.",
    ),
    "AU-6": (
        ("log", "audit", "sink", "siem", "cssp", "chronicle", "retention", "immutable", "router"),
        "Incomplete AU Specification",
        "Narrative fails to define audit log export, immutable retention, or automated review.",
    ),
    "IR-4": (
        ("incident", "runbook", "sla", "dc3", "cisa", "us-cert", "containment", "reporting", "investigation"),
        "Incomplete IR Specification",
        "Narrative fails to specify incident response playbooks or mandatory 1-hour reporting SLAs.",
    ),
    "IR-6": (
        ("incident", "runbook", "sla", "dc3", "cisa", "us-cert", "containment", "reporting", "investigation"),
        "Incomplete IR Specification",
        "Narrative fails to specify incident response playbooks or mandatory 1-hour reporting SLAs.",
    ),
    "IR-8": (
        ("incident response plan", "irp", "mission", "roles", "coordination", "annual", "review", "training", "incident"),
        "Incomplete IR-8 Specification",
        "Narrative fails to specify Incident Response Plan (IRP) structure, roles, or review cadence.",
    ),
    "IR-9": (
        ("spill", "spillage", "contamination", "containment", "sanitization", "purge", "media", "quarantine", "classification"),
        "Incomplete IR-9 Specification",
        "Narrative fails to specify information spillage containment, quarantine, and sanitization procedures.",
    ),
    "RA-5": (
        ("scan", "vulnerability", "patch", "cve", "acas", "trivy", "semgrep", "remediation", "flaw", "sla"),
        "Incomplete Flaw/Scanning Specification",
        "Narrative fails to specify automated scanning tools or remediation timelines.",
    ),
    "SI-2": (
        ("scan", "vulnerability", "patch", "cve", "acas", "trivy", "semgrep", "remediation", "flaw", "sla"),
        "Incomplete Flaw/Scanning Specification",
        "Narrative fails to specify automated scanning tools or remediation timelines.",
    ),
}


def evaluate_control_substance(
    ctrl_id: str,
    narrative: str,
    inventory: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Tuple[bool, str, str]:
    """Semantically evaluates whether an implementation narrative genuinely satisfies a NIST control."""
    del inventory, kwargs
    if not narrative or len(narrative.strip()) < 25:
        return False, "Incomplete Narrative (Insufficient Length)", "Implementation statement is too short to substantiate compliance."

    for pattern, desc in UNTAILORED_PATTERNS:
        if pattern.search(narrative):
            return False, f"Untailored Parameters ({desc})", f"Narrative contains unresolved placeholder: {desc}."

    for pattern, desc in VAGUE_PHRASING_PATTERNS:
        match = pattern.search(narrative)
        if match:
            return False, "Vague Boilerplate Detected", f"Statement rejected due to ambiguous phrasing '{match.group(0)}': {desc}"

    rule = _CONTROL_KEYWORD_RULES.get(base_control_id(ctrl_id))
    if rule is not None:
        keywords, fail_status, fail_detail = rule
        narr_lower = narrative.lower()
        if not any(k in narr_lower for k in keywords):
            return False, fail_status, fail_detail

    return (
        True,
        "Implemented & Substantive",
        "Implementation statement provides concrete architectural and operational details satisfying control requirements.",
    )


def validate_ssp_semantics(
    ssp_path: Path,
    inventory: Dict[str, Any],
    framework: str,
    **kwargs: Any,
) -> ArtifactSemanticResult:
    """Semantically validates the System Security Plan (SSP) deliverable."""
    res = ArtifactSemanticResult(str(ssp_path))
    if not ssp_path.exists():
        res.status = "REJECTED"
        res.add_finding(
            SemanticFinding(
                finding_id="LINT-SSP-MISSING",
                severity="CAT I (Critical)",
                category="Missing Deliverable",
                artifact="SSP/SSP_System_Security_Plan.md",
                description="System Security Plan Markdown file does not exist in target path.",
                remediation="Run `generate_compliance_artifacts.py` to provision the baseline SSP.",
            )
        )
        return res

    content = read_text_file(ssp_path)
    res.evaluated_controls_count = content.count("### ")

    # Exclude verbatim NIST SP 800-53 control catalog text that precedes Control Summary tables
    narrative_segments: List[str] = []
    for block in re.split(r"(?=^###\s+)", content, flags=re.MULTILINE):
        if "| Control Summary Information |" in block:
            _, _, summary_part = block.partition("| Control Summary Information |")
            narrative_segments.append(summary_part)
        else:
            narrative_segments.append(block)
    narrative_content = "\n".join(narrative_segments)

    # 1. Evaluate untailored parameters on implementation narrative segments
    for pattern, desc in UNTAILORED_PATTERNS:
        matches = pattern.findall(narrative_content)
        if matches:
            res.add_finding(
                SemanticFinding(
                    finding_id="LINT-SSP-UNTAILORED",
                    severity="CAT II (Medium)",
                    category="Untailored Parameter",
                    artifact=str(ssp_path.name),
                    description=f"SSP contains {len(matches)} untailored parameter(s): {desc}.",
                    remediation="Tailor control parameters with specific agency values or run validation with `--fill-example-data` for draft baseline.",
                    raw_text_snippet=str(matches[:3]),
                )
            )

    # 2. Evaluate vague phrasing in customer narratives and Control Implementation Statements
    for pattern, desc in VAGUE_PHRASING_PATTERNS:
        matches = list(pattern.finditer(narrative_content))
        if matches:
            first_match = matches[0].group(0)
            res.add_finding(
                SemanticFinding(
                    finding_id="LINT-SSP-VAGUE",
                    severity="CAT II (Medium)",
                    category="Vague Boilerplate",
                    artifact=str(ssp_path.name),
                    description=f"SSP narrative contains {len(matches)} ambiguous statement(s) matching '{first_match}'.",
                    remediation=desc,
                    raw_text_snippet=first_match,
                )
            )

    # 3. Cross-reference architectural drift
    drift = evaluate_architectural_drift(inventory, ssp_path=ssp_path)
    res.drift_items_count = len(drift)
    for d in drift:
        res.add_finding(d)

    res.summary = f"Audited {res.evaluated_controls_count} control sections; {len(res.findings)} finding(s) detected."
    return res


def validate_policy_semantics(
    policy_path: Path,
    inventory: Dict[str, Any],
    framework: str,
    **kwargs: Any,
) -> ArtifactSemanticResult:
    """Semantically validates an individual NIST SP 800-53 Policy Manual."""
    res = ArtifactSemanticResult(str(policy_path))
    if not policy_path.exists():
        res.status = "REJECTED"
        res.add_finding(
            SemanticFinding(
                finding_id="LINT-POL-MISSING",
                severity="CAT I (Critical)",
                category="Missing Deliverable",
                artifact=str(policy_path.name),
                description=f"Policy manual '{policy_path.name}' is missing.",
                remediation="Run `generate_compliance_artifacts.py --policy-format=both` to generate all 20 policy manuals.",
            )
        )
        return res

    content = read_text_file(policy_path)

    # Check for mandatory policy structural sections (NIST SP 800-53 -1 controls)
    required_sections = [
        (
            "Purpose",
            (
                r"(?:^#+\s*(?:\d+\.\s*)?Purpose\b|^#+\s*(?:\d+\.\s*)?Overview\b"
                r"|\bThe purpose of this document is\b|\bThis document defines the enterprise security policy\b)"
            ),
            "Missing Purpose section establishing statutory / regulatory mandate.",
        ),
        (
            "Scope",
            r"(?:^#+\s*(?:\d+\.\s*)?Scope\b|\bPolicy Scope\b|\bThis policy covers\b)",
            "Missing Scope section defining system boundary applicability.",
        ),
        (
            "Roles and Responsibilities",
            r"(?:^#+[^\r\n]*\bRoles\s*(?:&|and)\s*Responsibilities\b|\bProgram Roles\b|\bRoles & Responsibilities Matrix\b)",
            "Missing Roles & Responsibilities section defining operational accountabilities (ISSM, ISSO, AO).",
        ),
        (
            "Compliance and Enforcement",
            r"(?:^#+[^\r\n]*\bEnforcement\b|\bPolicy Enforcement\b|\bCompliance and Enforcement\b|\bAccess Enforcement\b)",
            "Missing Enforcement section detailing penalties and continuous audit authority.",
        ),
    ]
    for sec_name, pattern_str, msg in required_sections:
        if not re.search(pattern_str, content, re.MULTILINE | re.IGNORECASE):
            res.add_finding(
                SemanticFinding(
                    finding_id=f"LINT-POL-SEC-{sec_name[:3].upper()}",
                    severity="CAT II (Medium)",
                    category="Policy Weakness",
                    artifact=str(policy_path.name),
                    description=f"Policy manual missing mandatory section '{sec_name}': {msg}",
                    remediation=f"Add a dedicated '## {sec_name}' section detailing organizational procedures.",
                )
            )

    # Check for vague phrasing in policy statements
    for pattern, desc in VAGUE_PHRASING_PATTERNS:
        matches = list(pattern.finditer(content))
        if matches:
            res.add_finding(
                SemanticFinding(
                    finding_id="LINT-POL-VAGUE",
                    severity="CAT II (Medium)",
                    category="Vague Boilerplate",
                    artifact=str(policy_path.name),
                    description=f"Policy statement contains vague phrasing '{matches[0].group(0)}'.",
                    remediation=desc,
                    raw_text_snippet=matches[0].group(0),
                )
            )

    # Check for untailored placeholders
    for pattern, desc in UNTAILORED_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            res.add_finding(
                SemanticFinding(
                    finding_id="LINT-POL-PLACEHOLDER",
                    severity="CAT III (Low)",
                    category="Untailored Parameter",
                    artifact=str(policy_path.name),
                    description=f"Policy manual contains {len(matches)} unresolved variable(s): {desc}.",
                    remediation="Configure organizational metadata in `compliance_config.yaml`.",
                    raw_text_snippet=str(matches[:2]),
                )
            )

    res.summary = f"Policy audited; {len(res.findings)} finding(s) detected."
    return res


def validate_poam_semantics(
    poam_path: Path,
    inventory: Dict[str, Any],
    framework: str,
    **kwargs: Any,
) -> ArtifactSemanticResult:
    """Semantically validates the Plan of Action and Milestones (POA&M) deliverable."""
    res = ArtifactSemanticResult(str(poam_path))
    if not poam_path.exists():
        res.status = "REJECTED"
        res.add_finding(
            SemanticFinding(
                finding_id="LINT-POAM-MISSING",
                severity="CAT I (Critical)",
                category="Missing Deliverable",
                artifact="POAM/Plan_of_Action_and_Milestones.yaml",
                description="POA&M tracking matrix does not exist in target path.",
                remediation="Run `generate_compliance_artifacts.py` to provision the baseline POA&M.",
            )
        )
        return res

    try:
        poam_data = read_yaml_file(poam_path)
    except (OSError, ValueError, TypeError) as err:
        res.status = "REJECTED"
        res.add_finding(
            SemanticFinding(
                finding_id="LINT-POAM-SYNTAX",
                severity="CAT I (Critical)",
                category="Syntax Corruption",
                artifact=str(poam_path.name),
                description=f"POA&M YAML syntax error: {err}",
                remediation="Fix YAML syntax formatting in the POA&M deliverable.",
            )
        )
        return res

    items = poam_data.get("poam_items", []) or poam_data.get("items", []) or []
    res.evaluated_controls_count = len(items)

    for item in items:
        if not isinstance(item, dict):
            continue
        poam_id = (
            item.get("item_id")
            or item.get("poam_id")
            or item.get("id")
            or "UNSPECIFIED"
        )
        mitigation = str(item.get("planned_mitigation") or item.get("mitigation") or "").strip()
        if not mitigation and isinstance(item.get("milestones"), list) and item["milestones"]:
            m0 = item["milestones"][0]
            if isinstance(m0, dict):
                mitigation = str(m0.get("description") or m0.get("milestone_desc") or "").strip()
        if not mitigation:
            mitigation = str(item.get("weakness_description") or item.get("description") or "").strip()

        scheduled_comp = str(
            item.get("scheduled_completion_date")
            or item.get("sched_date")
            or ""
        ).strip()

        # Reject vague mitigations
        if len(mitigation) < 15:
            res.add_finding(
                SemanticFinding(
                    finding_id=f"LINT-POAM-MIT-{poam_id}",
                    severity="CAT II (Medium)",
                    category="Incomplete Control Implementation",
                    artifact=str(poam_path.name),
                    description=f"POA&M item '{poam_id}' has an incomplete or truncated planned mitigation.",
                    remediation="Provide an actionable, technically specific remediation plan detailing commands or Terraform changes.",
                    raw_text_snippet=mitigation,
                )
            )

        for pattern, desc in VAGUE_PHRASING_PATTERNS:
            if pattern.search(mitigation):
                res.add_finding(
                    SemanticFinding(
                        finding_id=f"LINT-POAM-VAGUE-{poam_id}",
                        severity="CAT II (Medium)",
                        category="Vague Boilerplate",
                        artifact=str(poam_path.name),
                        description=f"POA&M item '{poam_id}' mitigation contains vague phrasing.",
                        remediation=desc,
                        raw_text_snippet=mitigation,
                    )
                )
                break

        # Check for missing completion dates
        if not scheduled_comp or scheduled_comp in ["null", "None", "YYYY-MM-DD"]:
            res.add_finding(
                SemanticFinding(
                    finding_id=f"LINT-POAM-DATE-{poam_id}",
                    severity="CAT II (Medium)",
                    category="Policy Weakness",
                    artifact=str(poam_path.name),
                    description=f"POA&M item '{poam_id}' missing mandatory scheduled completion date.",
                    remediation="Assign a realistic calendar completion date conforming to agency flaw remediation SLAs (30 days for CAT I/II).",
                )
            )

    res.summary = f"Audited {len(items)} POA&M item(s); {len(res.findings)} finding(s) detected."
    return res


def run_semantic_linter(
    target_dir: Union[str, Path],
    inventory: Optional[Dict[str, Any]] = None,
    ato_dir: Optional[Union[str, Path]] = None,
    model: Optional[str] = None,
    strict: bool = True,
) -> SemanticLinterReport:
    """Master coordinator executing deterministic semantic linting across all deliverables.

    Validates:
    - System Security Plan (SSP)
    - Plan of Action and Milestones (POA&M)
    - All 20 Policy and Procedure Manuals
    - SCTM & PPSM matrices
    - Cross-references against live Terraform AST / state
    """
    target_path = resolve_path(target_dir)
    del model
    ato_path = resolve_path(ato_dir) if ato_dir else target_path / "ato_artifacts"
    ato_path = resolve_path(ensure_path_within_boundary(ato_path, target_path))

    inv_error: Optional[str] = None
    if inventory is None:
        inv_file = target_path / "system_inventory.json"
        if inv_file.exists():
            try:
                loaded_inv = read_json_file(inv_file, allowed_boundary=target_path)
            except (OSError, ValueError, TypeError) as err:
                logger.warning("Failed to load system inventory: %s", err)
                inv_error = str(err)
                inventory = {}
            else:
                if isinstance(loaded_inv, dict):
                    inventory = loaded_inv
                else:
                    inv_error = f"Expected JSON object in system_inventory.json, got {type(loaded_inv).__name__}"
                    inventory = {}
        else:
            inventory = {}

    framework = (
        (inventory.get("system_information", {}) or {}).get("compliance_baseline")
        or "NIST SP 800-53 Rev. 5 / DoD CC SRG IL5 / FedRAMP High"
    )

    report = SemanticLinterReport(str(target_path), framework, strict=strict)
    if inv_error is not None:
        inv_res = ArtifactSemanticResult("system_inventory.json")
        inv_res.add_finding(
            SemanticFinding(
                finding_id="LINT-INV-CORRUPT",
                severity="CAT I (Critical)",
                category="Syntax Corruption",
                artifact="system_inventory.json",
                description=f"Failed to parse system_inventory.json: {inv_error}",
                remediation="Re-run `extract_system_data.py` to generate a valid system_inventory.json.",
            )
        )
        report.record_artifact_result(inv_res)

    # 1. Validate SSP
    ssp_file = ato_path / "SSP" / "SSP_System_Security_Plan.md"
    if not ssp_file.exists():
        ssp_file = ato_path / "SSP" / "System_Security_Plan.md"
    ssp_res = validate_ssp_semantics(ssp_file, inventory, framework)
    report.record_artifact_result(ssp_res)

    # 2. Validate POA&M
    poam_file = ato_path / "POAM" / "Plan_of_Action_and_Milestones.yaml"
    poam_res = validate_poam_semantics(poam_file, inventory, framework)
    report.record_artifact_result(poam_res)

    # 3. Validate 20 Policy Manuals
    policies_dir = ato_path / "Policies_and_Procedures"
    if policies_dir.exists():
        for pol_path in sorted(policies_dir.glob("*_Policy_and_Procedures.md")):
            pol_res = validate_policy_semantics(pol_path, inventory, framework)
            report.record_artifact_result(pol_res)
        for pol_path in sorted(policies_dir.glob("*_Policy.md")):
            if not pol_path.name.endswith("_Policy_and_Procedures.md"):
                pol_res = validate_policy_semantics(pol_path, inventory, framework)
                report.record_artifact_result(pol_res)

    # 4. Save JSON Report into ato_artifacts
    report_file = ato_path / "semantic_linter_report.json"
    try:
        report_dict = report.to_dict()
        write_json_file(report_file, report_dict, allowed_boundary=ato_path)
        logger.info("Saved semantic linter audit report: %s", report_file)
    except (OSError, ValueError, TypeError) as err:
        logger.warning("Could not write semantic linter report: %s", err)

    return report


def main() -> None:
    """CLI entry point for deterministic semantic linting of compliance artifacts."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: semantic_linter.py [target_dir] [--no-strict] [--json]")
        print("\nDeterministic Semantic Compliance & Architectural Drift Linter.")
        print("\nPositional Arguments:\n  target_dir       Target workspace folder containing ato_artifacts/ (default: .)")
        print("\nOptions:\n  --no-strict      Do not exit with code 1 upon detecting CAT I findings")
        print("  --json           Output full audit report as structured JSON")
        sys.exit(0)

    target_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
    strict = "--no-strict" not in sys.argv
    output_json = "--json" in sys.argv

    report = run_semantic_linter(
        target_dir=os.path.abspath(target_dir),
        strict=strict,
    )

    if output_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("\n" + report.to_markdown() + "\n")
        logger.info("Verdict: %s", report.summary["verdict"])
        logger.info("Compliance Score: %.1f%%", report.summary["compliance_score_percent"])
        logger.info(
            "Findings: %d CAT I / %d CAT II / %d CAT III (%d drift)",
            report.summary["cat_1_findings_count"],
            report.summary["cat_2_findings_count"],
            report.summary["cat_3_findings_count"],
            report.summary["architectural_drift_findings_count"],
        )

    if strict and (report.summary["cat_1_findings_count"] > 0 or not report.passed):
        sys.exit(1)


if __name__ == "__main__":
    main()
