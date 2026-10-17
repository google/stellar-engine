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

"""Evidence-gated control status: the single source of truth for implementation claims.

Every artifact (OSCAL, SCTM, SSP narratives) asks :func:`derive_control_status` whether a
control is implemented. A control is ``implemented`` only when the inventory contains the
resources that implement it; otherwise it is ``partial`` (some evidence, named gaps) or
``planned`` (no evidence). An open POA&M item for the control always caps it at
``partial``. Narratives cite the inventory facts and never assert products, protocol
versions or personnel attributes the inventory does not show.
"""

import dataclasses
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .file_helpers import (
    NOT_DETERMINED,
    kms_protection_level,
    summarize_kms_protection,
)
from .poam_rules import base_control_id, firewall_rule_exposes_ports, is_public_ingress_allow_rule

IMPLEMENTED = "implemented"
PARTIAL = "partial"
PLANNED = "planned"

_PRIMITIVE_ROLES = ("roles/owner", "roles/editor")


@dataclasses.dataclass(frozen=True)
class ControlEvidence:
    """Derived status of one control with the facts behind it."""

    control_id: str
    status: str
    narrative: str
    evidence: Tuple[str, ...] = ()
    gaps: Tuple[str, ...] = ()


def _infra(inv: Mapping[str, Any]) -> Mapping[str, Any]:
    value = inv.get("infrastructure_components")
    return value if isinstance(value, Mapping) else {}


def _items(inv: Mapping[str, Any], key: str) -> List[Mapping[str, Any]]:
    return [x for x in (_infra(inv).get(key) or []) if isinstance(x, Mapping)]


def _resource_types(inv: Mapping[str, Any]) -> List[str]:
    return [str(r.get("type") or "") for r in _items(inv, "all_resources")]


def _firewall_rules(inv: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    net = inv.get("network_architecture")
    rules = net.get("firewall_rules") if isinstance(net, Mapping) else None
    return [r for r in (rules or []) if isinstance(r, Mapping)]


def _plural(count: int, noun: str) -> str:
    if count == 1:
        return f"{count} {noun}"
    return f"{count} {noun[:-1]}ies" if noun.endswith("y") else f"{count} {noun}s"


def _result(cid: str, evidence: Sequence[str], gaps: Sequence[str], *, complete: bool, what: str) -> ControlEvidence:
    """Builds the status: implemented when complete with evidence, partial with some, else planned."""
    if evidence and complete and not gaps:
        status = IMPLEMENTED
    elif evidence:
        status = PARTIAL
    else:
        status = PLANNED
    if evidence:
        narrative = f"{what}: " + "; ".join(evidence) + "."
    else:
        narrative = f"{NOT_DETERMINED} No Terraform evidence of {what.lower()} was found."
    if gaps:
        narrative += " Gaps: " + "; ".join(gaps) + "."
    return ControlEvidence(cid, status, narrative, tuple(evidence), tuple(gaps))


def _ac2(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    sas, bindings = _items(inv, "service_accounts"), _items(inv, "iam_bindings")
    evidence = []
    if sas:
        evidence.append(f"{_plural(len(sas), 'service account')} defined in Terraform")
    if bindings:
        evidence.append(f"{_plural(len(bindings), 'IAM binding')} defined in Terraform")
    gaps = ["[CONFIG_REQUIRED: account lifecycle, review and disablement procedures]"]
    return _result(cid, evidence, gaps, complete=False, what="Account management")


def _ac3(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    bindings = _items(inv, "iam_bindings")
    evidence = [f"{_plural(len(bindings), 'IAM role binding')} enforced by Cloud IAM"] if bindings else []
    return _result(cid, evidence, [], complete=True, what="Access enforcement")


def _ac6(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    bindings = _items(inv, "iam_bindings")
    broad = sorted({str(b.get("role")) for b in bindings if str(b.get("role") or "") in _PRIMITIVE_ROLES})
    evidence = [f"{_plural(len(bindings), 'IAM binding')} reviewed for primitive roles"] if bindings else []
    gaps = [f"primitive role(s) granted: {', '.join(broad)}"] if broad else []
    return _result(cid, evidence, gaps, complete=True, what="Least privilege")


def _ac4(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    vpcs = (inv.get("network_architecture") or {}).get("vpcs") or []
    perimeters = _items(inv, "service_perimeters")
    evidence = []
    if vpcs:
        evidence.append(f"{_plural(len(vpcs), 'VPC network')} defined")
    if perimeters:
        evidence.append(f"{_plural(len(perimeters), 'VPC Service Controls perimeter')} defined")
    gaps = [] if perimeters else ["no VPC Service Controls perimeter found in Terraform"]
    return _result(cid, evidence, gaps, complete=True, what="Information flow enforcement")


def _sc7(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    rules = _firewall_rules(inv)
    deny = [r for r in rules if str(r.get("action") or "").upper() == "DENY" and str(r.get("direction") or "INGRESS").upper() == "INGRESS"]
    public = [str(r.get("name")) for r in rules if is_public_ingress_allow_rule(r)]
    exposed_admin = [str(r.get("name")) for r in rules if firewall_rule_exposes_ports(r, {22, 3389})]
    policies = _items(inv, "security_policies")
    evidence = []
    if rules:
        evidence.append(f"{_plural(len(rules), 'VPC firewall rule')} defined")
    if deny:
        evidence.append(f"{_plural(len(deny), 'explicit ingress deny rule')}")
    if policies:
        evidence.append(f"{_plural(len(policies), 'Cloud Armor security policy')} defined")
    gaps = []
    if rules and not deny:
        gaps.append("no explicit default-deny ingress rule in Terraform (relies on the implied VPC deny)")
    if exposed_admin:
        gaps.append(f"SSH/RDP open to the internet in {', '.join(sorted(exposed_admin))}")
    elif public:
        gaps.append(f"public ingress allowed by {', '.join(sorted(public))}")
    return _result(cid, evidence, gaps, complete=True, what="Boundary protection")


def _logging(inv: Mapping[str, Any], cid: str, what: str) -> ControlEvidence:
    sinks = _items(inv, "logging_sinks")
    evidence = [f"{_plural(len(sinks), 'Cloud Logging sink')} defined"] if sinks else []
    gaps = []
    if base_control_id(cid) == "AU-2":
        gaps.append("[CONFIG_REQUIRED: list of audited event types and review cadence]")
    return _result(cid, evidence, gaps, complete=True, what=what)


def _cm2(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    count = len(_items(inv, "all_resources"))
    evidence = [f"{_plural(count, 'resource')} codified in version-controlled Terraform"] if count else []
    return _result(cid, evidence, [], complete=True, what="Baseline configuration")


def _cm6(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    aw = _items(inv, "assured_workloads")
    evidence = [f"{_plural(len(aw), 'Assured Workloads folder')} enforcing configuration constraints"] if aw else []
    gaps = ["[CONFIG_REQUIRED: configuration settings baseline and deviation process]"]
    return _result(cid, evidence, gaps, complete=False, what="Configuration settings")


def _cm8(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    count = len(_items(inv, "all_resources"))
    evidence = [f"{_plural(count, 'resource')} inventoried from Terraform"] if count else []
    gaps = ["runtime inventory (Cloud Asset Inventory export) not evidenced in Terraform"]
    return _result(cid, evidence, gaps, complete=False, what="Component inventory")


def _ia2(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    ext = inv.get("external_systems") if isinstance(inv.get("external_systems"), Mapping) else {}
    mfa = str((ext or {}).get("mfa_mechanism") or "")
    evidence = [f"configured MFA mechanism: {mfa}"] if mfa and not mfa.startswith("[") else []
    gaps = ["MFA enforcement is configured in the identity provider and is not visible in Terraform"]
    return _result(cid, evidence, gaps, complete=False, what="Identification and authentication")


def _encryption_targets(inv: Mapping[str, Any]) -> Tuple[int, int]:
    buckets, dbs = _items(inv, "storage_buckets"), _items(inv, "databases")
    total = len(buckets) + len(dbs)
    cmek = sum(1 for b in buckets if b.get("cmek_encrypted") or b.get("kms_key")) + sum(1 for d in dbs if d.get("cmek_key") or d.get("kms_key"))
    return total, cmek


def _sc28(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    total, cmek = _encryption_targets(inv)
    evidence = []
    if total:
        evidence.append(f"{cmek} of {_plural(total, 'data store')} use customer-managed keys; the rest use Google default encryption")
    gaps = [] if total and cmek == total else (["data stores without customer-managed keys"] if total else [])
    return _result(cid, evidence, gaps, complete=True, what="Protection of information at rest")


def _mp4(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    buckets = _items(inv, "storage_buckets")
    ubla = sum(1 for b in buckets if b.get("uniform_bucket_level_access"))
    evidence = [f"{ubla} of {_plural(len(buckets), 'storage bucket')} enforce uniform bucket-level access"] if buckets else []
    gaps = ["buckets without uniform bucket-level access"] if buckets and ubla < len(buckets) else []
    return _result(cid, evidence, gaps, complete=True, what="Media storage")


def _sc12(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    keys = _items(inv, "kms_keys")
    rotated = [k for k in keys if k.get("rotation_period")]
    evidence = [f"{_plural(len(keys), 'Cloud KMS key')}, {len(rotated)} with a rotation period"] if keys else []
    gaps = ["keys without rotation_period"] if keys and len(rotated) < len(keys) else []
    return _result(cid, evidence, gaps, complete=True, what="Cryptographic key management")


def _sc13(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    keys = _items(inv, "kms_keys")
    evidence = [summarize_kms_protection(keys)] if keys else []
    undetermined = [str(k.get("name")) for k in keys if kms_protection_level(k) not in ("HSM", "SOFTWARE")]
    gaps = [f"protection level not determined for {', '.join(undetermined)}"] if undetermined else []
    return _result(cid, evidence, gaps, complete=True, what="Cryptographic protection")


def _sc8(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    types = _resource_types(inv)
    ssl_policies = [t for t in types if t == "google_compute_ssl_policy"]
    dbs_ssl = [d for d in _items(inv, "databases") if d.get("require_ssl")]
    evidence = []
    if ssl_policies:
        evidence.append(f"{_plural(len(ssl_policies), 'SSL policy')} defined for load balancers")
    if dbs_ssl:
        evidence.append(f"{_plural(len(dbs_ssl), 'database')} requiring TLS client connections")
    gaps = ["TLS versions for all external and internal endpoints are not determined from source"]
    return _result(cid, evidence, gaps, complete=False, what="Transmission confidentiality and integrity")


def _ra5(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    services = [str(s) for s in (_infra(inv).get("services_enabled") or [])]
    scanning = [s for s in services if s in ("containerscanning.googleapis.com", "containeranalysis.googleapis.com", "ondemandscanning.googleapis.com")]
    evidence = [f"vulnerability scanning API(s) enabled: {', '.join(sorted(scanning))}"] if scanning else []
    gaps = ["[CONFIG_REQUIRED: vulnerability scanner, scan cadence and remediation SLAs]"]
    return _result(cid, evidence, gaps, complete=False, what="Vulnerability monitoring")


def _si4(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    types = _resource_types(inv)
    ids = [t for t in types if t == "google_cloud_ids_endpoint"]
    sinks = _items(inv, "logging_sinks")
    evidence = []
    if ids:
        evidence.append(f"{_plural(len(ids), 'Cloud IDS endpoint')} defined")
    if sinks:
        evidence.append(f"{_plural(len(sinks), 'Cloud Logging sink')} exporting telemetry")
    gaps = [] if ids else ["no intrusion detection resource found in Terraform"]
    return _result(cid, evidence, gaps, complete=True, what="System monitoring")


def _sa9(inv: Mapping[str, Any], cid: str) -> ControlEvidence:
    gaps = ["[CONFIG_REQUIRED: external service agreements and the CSP authorization being inherited]"]
    return _result(cid, [], gaps, complete=False, what="External system services")


_RULES: Dict[str, Callable[[Mapping[str, Any], str], ControlEvidence]] = {
    "AC-2": _ac2,
    "AC-3": _ac3,
    "AC-4": _ac4,
    "AC-6": _ac6,
    "AU-2": lambda inv, cid: _logging(inv, cid, "Event logging"),
    "AU-3": lambda inv, cid: _logging(inv, cid, "Audit record content"),
    "AU-12": lambda inv, cid: _logging(inv, cid, "Audit record generation"),
    "CM-2": _cm2,
    "CM-6": _cm6,
    "CM-8": _cm8,
    "IA-2": _ia2,
    "MP-4": _mp4,
    "RA-5": _ra5,
    "SA-9": _sa9,
    "SC-7": _sc7,
    "SC-8": _sc8,
    "SC-12": _sc12,
    "SC-13": _sc13,
    "SC-28": _sc28,
    "SI-4": _si4,
}


def has_evidence_rule(control_id: str) -> bool:
    """True when the inventory can evidence ``control_id`` (base control)."""
    return base_control_id(control_id) in _RULES


def derive_control_status(
    inventory: Mapping[str, Any],
    control_id: str,
    open_poam_controls: Optional[Iterable[str]] = None,
) -> ControlEvidence:
    """Derives the implementation status of ``control_id`` from inventory facts.

    Args:
        inventory: System inventory.
        control_id: Any NIST control id spelling (AC-02, ac-2(1), ...); enhancements use
            the base control's rule.
        open_poam_controls: Normalized control ids with open POA&M items; such controls
            are never reported as implemented.

    Returns:
        ControlEvidence; controls without a rule are ``planned`` with a configuration token.
    """
    cid = base_control_id(control_id)
    rule = _RULES.get(cid)
    if rule is None:
        result = ControlEvidence(
            cid, PLANNED, f"[CONFIG_REQUIRED: implementation statement for {cid}]", (), ("no inventory evidence rule",)
        )
    else:
        result = rule(inventory, cid)
    open_ids = {base_control_id(c) for c in (open_poam_controls or [])}
    if cid in open_ids and result.status == IMPLEMENTED:
        result = dataclasses.replace(
            result,
            status=PARTIAL,
            narrative=result.narrative + " An open POA&M item tracks a remaining weakness for this control.",
            gaps=result.gaps + ("open POA&M item",),
        )
    return result
