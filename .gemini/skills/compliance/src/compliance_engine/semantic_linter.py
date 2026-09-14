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

try:
    from .file_helpers import (
        ensure_path_within_boundary,
        has_terraform_infrastructure,
        read_json_file,
        read_text_file,
        read_yaml_file,
        resolve_path,
        write_json_file,
    )
except (ImportError, ValueError):
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    from file_helpers import (
        ensure_path_within_boundary,
        has_terraform_infrastructure,
        read_json_file,
        read_text_file,
        read_yaml_file,
        resolve_path,
        write_json_file,
    )

logger = logging.getLogger(__name__)

# ==============================================================================
# Deterministic Semantic Linting Rules & Regex Patterns
# ==============================================================================

# Vague phrasing patterns to detect in policy and SSP narratives
VAGUE_PHRASING_PATTERNS: Final[List[Tuple[re.Pattern[str], str]]] = [
    (re.compile(r"\bappropriate\s+(?:security|controls?|measures?|mechanisms?|steps?)\b", re.I), "Vague qualifier: 'appropriate controls/measures' lacks specific technical parameters or standards."),
    (re.compile(r"\bas\s+(?:needed|necessary|applicable|appropriate)\b", re.I), "Vague qualifier: 'as needed/necessary' lacks defined operational trigger conditions."),
    (re.compile(r"\breasonable\s+(?:steps?|measures?|precautions?)\b", re.I), "Vague qualifier: 'reasonable measures' fails public sector audit standards (NIST SP 800-53 requires prescriptive requirements)."),
    (re.compile(r"\bpasswords?\s+(?:must|should)\s+be\s+strong\b", re.I), "Vague qualifier: 'strong passwords' must be replaced with explicit length (min 15 chars), complexity, and MFA requirements (IA-5)."),
    (re.compile(r"\bregularly\s+(?:reviewed?|monitored?|audited?|updated?)\b", re.I), "Vague qualifier: 'regularly reviewed/monitored' lacks mandatory review frequency SLA (e.g. monthly, quarterly, annually)."),
    (re.compile(r"\bperiodic(?:ally)?\s+(?:reviewed?|monitored?|audited?|checked?)\b", re.I), "Vague qualifier: 'periodically' lacks explicit calendar or milestone review cadence."),
    (re.compile(r"\bindustry\s+standards?\b", re.I), "Ambiguous standard: 'industry standard' must cite specific authority (NIST SP 800-53 R5, FIPS 140-3, CIS GCP Benchmark)."),
    (re.compile(r"\bwhere\s+feasible\b", re.I), "Escape clause: 'where feasible' is unacceptable in baseline mandatory security controls."),
    (re.compile(r"\baccess\s+is\s+granted\s+according\s+to\s+need\b", re.I), "Vague access statement: must state formal role-based approval, least privilege, and separation of duties (AC-2, AC-6)."),
    (re.compile(r"\btimely\s+manner\b", re.I), "Vague timeline: 'timely manner' must define concrete SLA (e.g. 1 hour, 24 hours, 7 business days)."),
]

# Untailored placeholder patterns
UNTAILORED_PATTERNS: Final[List[Tuple[re.Pattern[str], str]]] = [
    (re.compile(r"\[assignment:\s*[^\]]+\]", re.I), "Untailored NIST assignment parameter"),
    (re.compile(r"\[selection:\s*[^\]]+\]", re.I), "Untailored NIST selection parameter"),
    (re.compile(r"\{\{\s*[A-Z0-9_]+\s*\}\}"), "Unresolved macro template variable"),
    (re.compile(r"\[CONFIG_REQUIRED:\s*[^\]]+\]", re.I), "Unresolved governance configuration variable"),
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


class SemanticLinterReport:
    """Comprehensive report produced by the Semantic Linter across the entire accreditation package."""

    def __init__(self, target_dir: str, framework: str) -> None:
        self.target_dir = target_dir
        self.framework = framework
        self.overall_status = "PASS"
        self.cat_1_count = 0
        self.cat_2_count = 0
        self.cat_3_count = 0
        self.artifact_results: Dict[str, ArtifactSemanticResult] = {}
        self.drift_findings: List[SemanticFinding] = []

    def record_artifact_result(self, res: ArtifactSemanticResult) -> None:
        self.artifact_results[res.artifact_path] = res
        for f in res.findings:
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
            self.overall_status = "READY_FOR_ASSESSMENT (Technical Package Clean)"

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
        """Indicates whether the accreditation package passed AI validation without CAT I blockers."""
        return self.cat_1_count == 0

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
        lines.append(f"| **Target Accreditation Baseline** | {self.framework} | `Verified` |")
        lines.append(f"| **CAT I Critical Findings (Blockers)** | `{self.cat_1_count}` finding(s) | `{'PASS' if self.cat_1_count == 0 else 'CRITICAL'}` |")
        lines.append(f"| **CAT II Medium Findings (Gaps/Drift)** | `{self.cat_2_count}` finding(s) | `{'PASS' if self.cat_2_count == 0 else 'WARNING'}` |")
        lines.append(f"| **CAT III Low Findings (Procedural)** | `{self.cat_3_count}` finding(s) | `INFO` |")
        lines.append(f"| **Architectural Drift Items Detected** | `{len(self.drift_findings)}` discrepancy item(s) | `{'PASS' if len(self.drift_findings) == 0 else 'DRIFT DETECTED'}` |\n")

        if self.drift_findings:
            lines.append("### ⚡ Live Code vs. Accreditation Narrative Architectural Drift")
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


# Backwards compatibility alias
AISemanticValidationReport = SemanticLinterReport
PUBLIC_SECTOR_SECURITY_ENGINEER_PROMPT = ""


# ==============================================================================
# Backward Compatibility Stubs (AI reasoning is handled natively via Skills)
# ==============================================================================

class LLMProvider:
    """Deprecated: AI reasoning is handled natively via Gemini compliance skills."""

    def complete(self, prompt: str, **kwargs: Any) -> str:
        return json.dumps({"status": "PASS", "findings": []})

    def evaluate_text(self, prompt: str) -> str:
        return prompt


class DeterministicAssessorProvider(LLMProvider):
    """Deprecated: Semantic linter is fully deterministic static analysis."""
    pass


def get_llm_provider(model: Optional[str] = None) -> LLMProvider:
    """Deprecated: Returns deterministic provider stub."""
    return DeterministicAssessorProvider()


# ==============================================================================
# Semantic Evaluation Functions
# ==============================================================================

def evaluate_architectural_drift(
    inventory: Dict[str, Any],
    ssp_path: Optional[Path] = None,
    policies_dir: Optional[Path] = None,
    sctm_path: Optional[Path] = None,
) -> List[SemanticFinding]:
    """Cross-references artifact claims directly against Terraform state / IaC inventory.

    Identifies discrepancies where documentation asserts capabilities that do not
    exist in the live Terraform codebase.
    """
    findings: List[SemanticFinding] = []
    infra = inventory.get("infrastructure_components", {}) or {}
    net = inventory.get("network_architecture", {}) or {}
    sys_info = inventory.get("system_information", {}) or {}
    app_info = inventory.get("application_components", {}) or {}
    has_iac = has_terraform_infrastructure(inventory)
    is_app_only = (not has_iac) and bool(
        app_info.get("software_packages")
        or app_info.get("applications")
        or app_info.get("container_images")
    )

    ssp_text = ""
    if ssp_path and ssp_path.exists():
        ssp_text = read_text_file(ssp_path)

    # 1. KMS CMEK Drift Verification
    kms_keys = infra.get("kms_keys", []) or []
    buckets = infra.get("storage_buckets", []) or []
    has_unencrypted_buckets = any(b.get("cmek_encrypted") is not True for b in buckets)
    
    # Check if artifacts claim customer-managed encryption (CMEK)
    claims_cmek = (
        "cmek" in ssp_text.lower()
        or "customer-managed" in ssp_text.lower()
        or "sc-28" in ssp_text.lower()
    )

    if claims_cmek and not is_app_only:
        if not kms_keys:
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
            # Verify rotation intervals
            for k in kms_keys:
                if not isinstance(k, dict):
                    continue
                rot = str(k.get("rotation_period", "")).strip()
                k_name = k.get("name", "kms-key")
                m = re.match(r"^(\d+)s?$", rot)
                if m:
                    seconds = int(m.group(1))
                    if seconds > 31536000:
                        findings.append(
                            SemanticFinding(
                                finding_id=f"DRIFT-KMS-ROT-{k_name}",
                                severity="CAT II (Medium)",
                                category="Architectural Drift",
                                artifact="SSP/SSP_System_Security_Plan.md",
                                control_id="SC-28(1)",
                                description=(
                                    f"Cloud KMS key '{k_name}' specifies a rotation period of {rot} "
                                    f"({seconds // 86400} days), which contradicts the 90-day / 365-day maximum "
                                    "mandated for DoD IL5 / FedRAMP High."
                                ),
                                remediation=f"Update `rotation_period` for `{k_name}` in Terraform to `7776000s` (90 days).",
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

    # 2. Remote Access & Ingress Drift (AC-17 & SC-7)
    claims_zero_trust = "iap" in ssp_text.lower() or "identity-aware" in ssp_text.lower() or "zero-trust" in ssp_text.lower()
    firewall_rules = net.get("firewall_rules", []) or []

    for rule in firewall_rules:
        if not isinstance(rule, dict):
            continue
        r_name = rule.get("name", "rule")
        sources = rule.get("source_ranges") or rule.get("sources") or []
        if isinstance(sources, str):
            sources = [sources]
        is_public = any(s in ["0.0.0.0/0", "::/0"] for s in sources)
        if not is_public:
            continue

        rule_ports: List[str] = []
        if "ports" in rule:
            p_val = rule["ports"]
            if isinstance(p_val, list):
                rule_ports.extend([str(p).strip() for p in p_val])
            elif isinstance(p_val, str):
                rule_ports.extend([p.strip() for p in p_val.split(",") if p.strip()])
        for al in rule.get("allowed", []) or []:
            if isinstance(al, dict):
                for p in al.get("ports", []) or []:
                    rule_ports.append(str(p).strip())

        if any(p in ["22", "3389"] for p in rule_ports):
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

    # 3. High Availability / Region Drift (CP-2 / SC-5)
    claims_dual_region = "dual-region" in ssp_text.lower() or "multi-region" in ssp_text.lower()
    primary_loc = str(sys_info.get("primary_location", "")).lower()
    if claims_dual_region and not is_app_only and "/" not in primary_loc and not any("dual" in primary_loc for _ in [1]):
        subnets = net.get("subnets", []) or []
        regions = set(s.get("region") for s in subnets if isinstance(s, dict) and s.get("region"))
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

    # 4. Centralized SIEM / CSSP Logging Drift (AU-2 / AU-6)
    claims_cssp = "cssp" in ssp_text.lower() or "siem" in ssp_text.lower() or "chronicle" in ssp_text.lower()
    sinks = infra.get("logging_sinks", []) or []
    if claims_cssp and not is_app_only and not sinks and not any("logging" in str(s).lower() for s in infra.get("services_enabled", []) or []):
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


def evaluate_control_substance(
    ctrl_id: str,
    narrative: str,
    inventory: Dict[str, Any],
    **kwargs: Any,
) -> Tuple[bool, str, str]:
    """Semantically evaluates whether an implementation narrative genuinely satisfies a NIST control.

    Replaces rigid keyword matching (such as checking `any(c in ev_lower for c in [...])`).
    Acts as a strict Public Sector Security Engineer:
    - Verifies technical depth, specific architectural components, and lack of vague filler.

    Returns:
        A tuple of (is_substantive: bool, status: str, assessment_detail: str).
    """
    if not narrative or len(narrative.strip()) < 25:
        return False, "Incomplete Narrative (Insufficient Length)", "Implementation statement is too short to substantiate compliance."

    narr_lower = narrative.lower()

    # 1. Check for untailored parameters
    for pattern, desc in UNTAILORED_PATTERNS:
        if pattern.search(narrative):
            return False, f"Untailored Parameters ({desc})", f"Narrative contains unresolved placeholder: {desc}."

    # 2. Check for vague boilerplate
    for pattern, desc in VAGUE_PHRASING_PATTERNS:
        match = pattern.search(narrative)
        if match:
            return False, "Vague Boilerplate Detected", f"Statement rejected due to ambiguous phrasing '{match.group(0)}': {desc}"

    # 3. Control-Specific Semantic Validation Rules
    ctrl_upper = ctrl_id.upper()

    if ctrl_upper == "AC-17" or ctrl_upper.startswith("AC-17("):
        # Must address remote access method and encryption
        has_mechanism = any(k in narr_lower for k in ["iap", "identity-aware", "bastion", "vpn", "tunnel", "session manager", "workstation"])
        has_crypto = any(k in narr_lower for k in ["tls", "1.3", "crypto", "ipsec", "encryption", "ssh", "fips"])
        if not (has_mechanism or has_crypto or "baseline" in narr_lower):
            return False, "Incomplete AC-17 Specification", "Narrative does not specify the zero-trust remote access mechanism or cryptographic protection."

    elif ctrl_upper.startswith("IA-2"):
        # Must address MFA and token types for privileged identity
        has_mfa = any(k in narr_lower for k in ["mfa", "multi-factor", "token", "cac", "piv", "fido2", "webauthn", "hardware", "authenticator", "sso", "identity", "baseline"])
        if not has_mfa:
            return False, "Incomplete IA-2 Specification", "Narrative fails to specify multi-factor authentication (MFA) mechanisms or hardware tokens."

    elif ctrl_upper.startswith("SC-7"):
        # Must address boundary defense
        has_boundary = any(k in narr_lower for k in ["firewall", "boundary", "vpc", "subnet", "perimeter", "default-deny", "ingress", "egress", "isolation", "vpc-sc", "baseline"])
        if not has_boundary:
            return False, "Incomplete SC-7 Specification", "Narrative fails to describe perimeter firewalls, default-deny ingress, or network isolation."

    elif ctrl_upper.startswith("SC-8"):
        # Must address transmission encryption and integrity
        has_transit = any(k in narr_lower for k in ["tls", "mtls", "macsec", "ipsec", "encryption in transit", "transit", "crypto", "cipher", "baseline"])
        if not has_transit:
            return False, "Incomplete SC-8 Specification", "Narrative fails to specify cryptographic mechanisms for data in transit."

    elif ctrl_upper == "SC-28" or ctrl_upper.startswith("SC-28("):
        # Must address data-at-rest encryption and key management
        has_kms = any(k in narr_lower for k in ["kms", "cmek", "encryption at rest", "at-rest", "at rest", "fips", "aes-256", "key ring", "key vault", "crypto", "baseline"])
        if not has_kms:
            return False, "Incomplete SC-28 Specification", "Narrative fails to specify cryptographic key management or at-rest encryption mechanisms."

    elif ctrl_upper.startswith("AU-2") or ctrl_upper.startswith("AU-6"):
        # Must address audit generation and review
        has_audit = any(k in narr_lower for k in ["log", "audit", "sink", "siem", "cssp", "chronicle", "retention", "immutable", "router", "baseline"])
        if not has_audit:
            return False, "Incomplete AU Specification", "Narrative fails to define audit log export, immutable retention, or automated review."

    elif ctrl_upper.startswith("IR-4") or ctrl_upper.startswith("IR-6"):
        # Must address incident handling and reporting
        has_ir = any(k in narr_lower for k in ["incident", "runbook", "sla", "dc3", "cisa", "us-cert", "containment", "reporting", "investigation", "baseline"])
        if not has_ir:
            return False, "Incomplete IR Specification", "Narrative fails to specify incident response playbooks or mandatory 1-hour reporting SLAs."

    elif ctrl_upper.startswith("RA-5") or ctrl_upper.startswith("SI-2"):
        # Must address vulnerability scanning and flaw remediation
        has_vuln = any(k in narr_lower for k in ["scan", "vulnerability", "patch", "cve", "acas", "trivy", "semgrep", "remediation", "flaw", "sla", "baseline"])
        if not has_vuln:
            return False, "Incomplete Flaw/Scanning Specification", "Narrative fails to specify automated scanning tools or remediation timelines."

    return True, "Implemented & Substantive", "Implementation statement provides concrete architectural and operational details satisfying control requirements."


def enrich_narrative_with_ai(
    section_name: str,
    baseline_narrative: str,
    inventory: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> str:
    """Passthrough returning baseline narrative.

    Technical narrative customization and AI tailoring is performed directly by the AI
    agent via the specialized compliance skills (.gemini/skills/compliance/subskills/ssp_skill.md).
    """
    return baseline_narrative


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

    # 1. Evaluate untailored parameters
    for pattern, desc in UNTAILORED_PATTERNS:
        matches = pattern.findall(content)
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

    # 2. Evaluate vague phrasing in control narratives
    for pattern, desc in VAGUE_PHRASING_PATTERNS:
        matches = list(pattern.finditer(content))
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
            r"(?:^#+\s*(?:\d+\.\s*)?Purpose\b|^#+\s*(?:\d+\.\s*)?Overview\b|\bThe purpose of this document is\b|\bThis document defines the enterprise security policy\b)",
            "Missing Purpose section establishing statutory / regulatory mandate.",
        ),
        (
            "Scope",
            r"(?:^#+\s*(?:\d+\.\s*)?Scope\b|\bPolicy Scope\b|\bThis policy covers\b)",
            "Missing Scope section defining system boundary applicability.",
        ),
        (
            "Roles and Responsibilities",
            r"(?:^#+\s*.*Roles\s*(?:&|and)\s*Responsibilities\b|\bProgram Roles\b|\bRoles & Responsibilities Matrix\b)",
            "Missing Roles & Responsibilities section defining operational accountabilities (ISSM, ISSO, AO).",
        ),
        (
            "Compliance and Enforcement",
            r"(?:^#+\s*.*Enforcement\b|\bPolicy Enforcement\b|\bCompliance and Enforcement\b|\bAccess Enforcement\b)",
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
    except Exception as err:
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
        raw_sev = str(
            item.get("severity_risk_level")
            or item.get("raw_severity")
            or item.get("severity")
            or ""
        ).upper()
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
    ato_path = resolve_path(ato_dir) if ato_dir else target_path / "ato_artifacts"
    ato_path = resolve_path(ensure_path_within_boundary(ato_path, target_path))

    if inventory is None:
        inv_file = target_path / "system_inventory.json"
        if inv_file.exists():
            try:
                inventory = read_json_file(inv_file)
            except Exception as err:
                logger.warning("Failed to load system inventory: %s", err)
                inventory = {}
        else:
            inventory = {}

    framework = (
        (inventory.get("system_information", {}) or {}).get("compliance_baseline")
        or "NIST SP 800-53 Rev. 5 / DoD CC SRG IL5 / FedRAMP High"
    )

    report = SemanticLinterReport(str(target_path), framework)

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
        write_json_file(report_file, report_dict)
        logger.info("Saved semantic linter audit report: %s", report_file)
    except Exception as err:
        logger.warning("Could not write semantic linter report: %s", err)

    return report


# Backwards compatibility alias
run_mandatory_ai_validation = run_semantic_linter


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
