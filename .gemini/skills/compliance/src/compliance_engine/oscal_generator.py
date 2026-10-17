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

"""NIST OSCAL System Security Plan (SSP) and Component Definition generator.

Builds OSCAL SSP and component-definition models (JSON and YAML) from the system
inventory produced by ``extract_system_data.py``. The default target is OSCAL 1.2.3;
any NIST OSCAL release listed in ``SUPPORTED_OSCAL_VERSIONS`` can be requested. The
emitted structure is kept valid against the NIST JSON schemas for those releases
(required fields present, no properties the schemas do not define).
"""

import functools
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Final, List, Mapping, Optional, Set, Tuple, Union
import uuid

from .file_helpers import (
    current_utc_datetime,
    Regime,
    ensure_directory,
    kms_key_fips_attribute,
    summarize_kms_protection,
    is_dod_regime,
    require_supported_regime,
    extract_clean_subnets,
    resolve_path,
    scrub_sensitive_data,
    write_json_file,
    write_yaml_file,
)
from .baseline_registry import get_regime_baseline, get_regime_spec
from .evidence import derive_control_status
from .poam_rules import (
    active_poam_target,
    derive_poam_findings,
    extract_normalized_control_ids,
    normalize_control_id,
)
from .runbook_hydration import resolve_prepared_by
from .template_engine import is_unfilled_placeholder

logger = logging.getLogger(__name__)

# NIST OSCAL releases (https://github.com/usnistgov/OSCAL/releases). v1.2.3, published
# 2026-08-07, is the latest release. Pre-release tags (milestones, release candidates)
# are not listed.
DEFAULT_OSCAL_VERSION: str = "1.2.3"
SUPPORTED_OSCAL_VERSIONS: Tuple[str, ...] = (
    "1.0.0",
    "1.0.1",
    "1.0.2",
    "1.0.3",
    "1.0.4",
    "1.0.5",
    "1.0.6",
    "1.1.0",
    "1.1.1",
    "1.1.2",
    "1.1.3",
    "1.2.0",
    "1.2.1",
    "1.2.2",
    "1.2.3",
)


_FEDRAMP_PROFILE_BASE: Final[str] = (
    "https://raw.githubusercontent.com/OSCAL-Foundation/fedramp-resources/main/baselines/rev5/json/"
)
_NIST_PROFILE_BASE: Final[str] = (
    "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/"
)

#: FedRAMP Rev. 5 and NIST SP 800-53B baseline profile per regime. DoD IL2/IL4/IL5/IL6 and CJIS have no
#: published overlay OSCAL profile, so they import the base profile they overlay and document the overlay in remarks.
OSCAL_PROFILE_BY_REGIME: Final[Dict[Regime, Tuple[str, Optional[str]]]] = {
    Regime.FEDRAMP_HIGH: (_FEDRAMP_PROFILE_BASE + "FedRAMP_rev5_HIGH-baseline_profile.json", None),
    Regime.FEDRAMP_MODERATE: (_FEDRAMP_PROFILE_BASE + "FedRAMP_rev5_MODERATE-baseline_profile.json", None),
    Regime.FEDRAMP_LOW: (_FEDRAMP_PROFILE_BASE + "FedRAMP_rev5_LOW-baseline_profile.json", None),
    Regime.FISMA_HIGH: (_NIST_PROFILE_BASE + "NIST_SP-800-53_rev5_HIGH-baseline_profile.json", None),
    Regime.FISMA_MODERATE: (_NIST_PROFILE_BASE + "NIST_SP-800-53_rev5_MODERATE-baseline_profile.json", None),
    Regime.FISMA_LOW: (_NIST_PROFILE_BASE + "NIST_SP-800-53_rev5_LOW-baseline_profile.json", None),
    Regime.DOD_IL2: (
        _FEDRAMP_PROFILE_BASE + "FedRAMP_rev5_MODERATE-baseline_profile.json",
        "DoD IL2 provides reciprocity with the FedRAMP Moderate baseline per DISA CSP SRG V1R7 Section 3.7.5 "
        "and Table 3-1 (323 controls); no official DoD Cloud Computing SRG OSCAL overlay is published, "
        "so SRG-specific enclave requirements are documented in the SSP narrative.",
    ),
    Regime.DOD_IL4: (
        _FEDRAMP_PROFILE_BASE + "FedRAMP_rev5_MODERATE-baseline_profile.json",
        "DoD IL4 overlays the FedRAMP Moderate baseline; no official DoD Cloud Computing SRG OSCAL overlay is published, "
        "so SRG-specific parameters and controls are documented in the SSP narrative.",
    ),
    Regime.DOD_IL5: (
        _FEDRAMP_PROFILE_BASE + "FedRAMP_rev5_HIGH-baseline_profile.json",
        "DoD IL5 overlays the FedRAMP High baseline; no official DoD Cloud Computing SRG OSCAL overlay is published, "
        "so SRG-specific parameters and controls are documented in the SSP narrative.",
    ),
    Regime.DOD_IL6: (
        _FEDRAMP_PROFILE_BASE + "FedRAMP_rev5_HIGH-baseline_profile.json",
        "DoD IL6 overlays the FedRAMP High baseline per DISA CSP SRG V1R7 Table 3-1, Appendix D Table D-1 (IL6), "
        "and the CNSSI No. 1253 Classified Information Overlay (627 controls); no official DoD Cloud Computing "
        "SRG OSCAL overlay is published, so SRG-specific classified enclave requirements are documented in the "
        "SSP narrative.",
    ),
    Regime.CJIS: (
        _NIST_PROFILE_BASE + "NIST_SP-800-53_rev5_MODERATE-baseline_profile.json",
        "CJIS applies the FBI CJIS Security Policy v5.9.4 / v6.0 NIST SP 800-53 Rev. 5 Moderate harmonized "
        "baseline overlay (323 controls); no official FBI CJIS OSCAL profile is published, so CJIS Security "
        "Policy parameter overrides and State CSA obligations are documented in the SSP narrative and "
        "set-parameters.",
    ),
}


def build_oscal_import_profile(sys_info: Dict[str, Any]) -> Dict[str, str]:
    """Returns the OSCAL import-profile for a supported regime (fails closed otherwise)."""
    regime = require_supported_regime(sys_info)
    spec = get_regime_spec(regime)
    profile = {"href": spec.oscal_profile_href}
    if spec.oscal_profile_remarks:
        profile["remarks"] = spec.oscal_profile_remarks
    return profile


def resolve_oscal_version(inventory: Dict[str, Any], explicit_version: Optional[str] = None) -> str:
    """Resolves and validates the target OSCAL version from explicit parameter, inventory, or default.

    Args:
        inventory: System inventory dictionary.
        explicit_version: Optional explicit version override (e.g. '1.2.3' or '1.1.0').

    Returns:
        Validated OSCAL specification version string (defaults to DEFAULT_OSCAL_VERSION = '1.2.3').

    Raises:
        ValueError: If the requested version is not a NIST OSCAL release. Writing an
            unknown version into ``metadata.oscal-version`` would claim conformance to
            a specification that does not exist.
    """
    candidate = explicit_version
    if not candidate:
        prefs = inventory.get("export_preferences", {})
        candidate = prefs.get("oscal_version")
    if not candidate:
        sys_info = inventory.get("system_information", {})
        candidate = sys_info.get("oscal_version")
    if not candidate:
        candidate = DEFAULT_OSCAL_VERSION

    candidate = str(candidate).strip()
    if candidate not in SUPPORTED_OSCAL_VERSIONS:
        raise ValueError(
            f"OSCAL version '{candidate}' is not a NIST OSCAL release. "
            f"Supported versions: {', '.join(SUPPORTED_OSCAL_VERSIONS)}"
        )
    return candidate


@functools.lru_cache(maxsize=4096)
def _deterministic_uuid(name: str) -> str:
    """Generates a stable UUID from a seed string so regenerated packages diff cleanly.

    The UUID is derived from a SHA-256 digest of the seed (not used for security).
    The version nibble is set to 4 because the OSCAL ``UUIDDatatype`` pattern only
    accepts version 4 or 5 UUIDs.

    Args:
        name: Unique seed string (e.g. system name, component identifier, control id).

    Returns:
        String UUID format (e.g. 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx').
    """
    digest = hashlib.sha256(str(name).encode("utf-8"), usedforsecurity=False).digest()
    raw = bytearray(digest[:16])
    raw[6] = (raw[6] & 0x0f) | 0x40  # Version 4
    raw[8] = (raw[8] & 0x3f) | 0x80  # Variant 1 (RFC 4122)
    return str(uuid.UUID(bytes=bytes(raw)))


def _iso_timestamp() -> str:
    """Returns current ISO 8601 UTC timestamp formatted for OSCAL metadata."""
    return current_utc_datetime().strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_oscal_email(val: Any) -> Optional[str]:
    """Returns a schema-safe email address string, or None if missing/placeholder."""
    if val is None or is_unfilled_placeholder(val):
        return None
    s = str(val).strip()
    if not s or "@" not in s or " " in s or s.startswith("["):
        return None
    return s


def resolve_system_identity(sys_info: Mapping[str, Any]) -> Tuple[str, str]:
    """Returns canonical (system_name, system_abbreviation) with truthful config-required fallbacks."""
    name = str(sys_info.get("system_name") or "").strip() if isinstance(sys_info, Mapping) else ""
    abbr = str(sys_info.get("system_abbreviation") or "").strip() if isinstance(sys_info, Mapping) else ""
    if not name or is_unfilled_placeholder(name):
        name = "[CONFIG_REQUIRED: System Name]"
    if not abbr or is_unfilled_placeholder(abbr):
        abbr = "[CONFIG_REQUIRED: System Abbreviation]"
    return name, abbr


def build_oscal_metadata(
    inventory: Dict[str, Any],
    doc_version: str = "1.0.0",
    oscal_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Constructs OSCAL metadata block including title, roles, and responsible parties.

    Args:
        inventory: System inventory dictionary.
        doc_version: Semantic document version.
        oscal_version: Optional target OSCAL specification version (e.g. '1.2.3' or '1.1.0').

    Returns:
        Structured OSCAL metadata dictionary.
    """
    sys_info = inventory.get("system_information", {})
    if not isinstance(sys_info, dict):
        sys_info = {}
    roles_info = inventory.get("personnel_roles") or inventory.get("roles") or {}
    if not isinstance(roles_info, dict):
        roles_info = {}
    sys_name, sys_abbr = resolve_system_identity(sys_info)
    org_name = sys_info.get("organization") or "Enterprise Organization"
    if is_unfilled_placeholder(org_name):
        org_name = "Enterprise Organization"

    active_oscal_version = resolve_oscal_version(inventory, oscal_version)

    roles = [
        {"id": "authorizing-official", "title": "Authorizing Official (AO)"},
        {"id": "system-owner", "title": "Information System Owner (SO)"},
        {"id": "issm", "title": "Information System Security Manager (ISSM)"},
        {"id": "isso", "title": "Information System Security Officer (ISSO)"},
    ]

    parties: List[Dict[str, Any]] = []
    responsible_parties: List[Dict[str, Any]] = []

    for role_id, role_key in [
        ("authorizing-official", "authorizing_official"),
        ("system-owner", "system_owner"),
        ("issm", "issm"),
        ("isso", "isso"),
    ]:
        contact = roles_info.get(role_key, {})
        if not isinstance(contact, dict):
            contact = {}
        raw_name = contact.get("name")
        party_name = (
            raw_name
            if (raw_name and not is_unfilled_placeholder(raw_name))
            else f"Designated {role_id.upper()}"
        )
        party_email = _safe_oscal_email(contact.get("email"))
        party_uuid = _deterministic_uuid(f"party-{role_id}-{sys_abbr}")
        raw_phone = contact.get("phone")
        phone_val = (
            str(raw_phone).strip()
            if (raw_phone and not is_unfilled_placeholder(raw_phone))
            else "N/A"
        )

        party_obj: Dict[str, Any] = {
            "uuid": party_uuid,
            "type": "person",
            "name": party_name,
            "telephone-numbers": [
                {"type": "work", "number": phone_val}
            ],
        }
        if party_email:
            party_obj["email-addresses"] = [party_email]

        parties.append(party_obj)
        responsible_parties.append({
            "role-id": role_id,
            "party-uuids": [party_uuid],
        })

    # Add organization party
    org_party_uuid = _deterministic_uuid(f"org-{org_name}")
    parties.append({
        "uuid": org_party_uuid,
        "type": "organization",
        "name": org_name,
    })

    # The same setting that hydrates {{ PREPARED_BY }} in the Markdown and DOCX
    # deliverables. Emitted only when configured: no default team name is invented
    # for the machine-readable record.
    prepared_by = resolve_prepared_by(inventory)
    if prepared_by:
        prepared_by_uuid = _deterministic_uuid(f"party-prepared-by-{prepared_by}")
        roles.append({"id": "prepared-by", "title": "Prepared By"})
        parties.append({
            "uuid": prepared_by_uuid,
            "type": "organization",
            "name": prepared_by,
        })
        responsible_parties.append({
            "role-id": "prepared-by",
            "party-uuids": [prepared_by_uuid],
        })

    ts = _iso_timestamp()
    return {
        "title": f"System Security Plan (SSP) - {sys_name}",
        "published": ts,
        "last-modified": ts,
        "version": doc_version,
        "oscal-version": active_oscal_version,
        "roles": roles,
        "parties": parties,
        "responsible-parties": responsible_parties,
    }


def _build_oscal_information_types(
    sys_info: Dict[str, Any],
    sys_abbr: str,
    impact: str,
    fips_conf: str,
    fips_integ: str,
    fips_avail: str,
) -> List[Dict[str, Any]]:
    """Constructs the OSCAL system-information.information-types list."""
    raw_info_types = sys_info.get("information_types")
    if raw_info_types and isinstance(raw_info_types, list):
        info_types_list = []
        for idx, it in enumerate(raw_info_types):
            it_title = it.get("title") or it.get("name") or "Government & Mission Critical Cloud Workload Information"
            it_desc = it.get("description") or f"Federal / DoD mission operations data hosted in {impact} compliance boundary."
            it_ids = it.get("information_type_ids") or it.get("sp800_60_ids") or ["C.3.5.1"]
            if isinstance(it_ids, str):
                it_ids = [it_ids]
            info_types_list.append({
                "uuid": _deterministic_uuid(f"infotype-{sys_abbr}-{idx}"),
                "title": it_title,
                "description": it_desc,
                "categorizations": [{
                    "system": "https://doi.org/10.6028/NIST.SP.800-60v2r1",
                    "information-type-ids": it_ids,
                }],
                "confidentiality-impact": {"base": (it.get("confidentiality_impact") or fips_conf).lower()},
                "integrity-impact": {"base": (it.get("integrity_impact") or fips_integ).lower()},
                "availability-impact": {"base": (it.get("availability_impact") or fips_avail).lower()},
            })
        return info_types_list

    return [
        {
            "uuid": _deterministic_uuid(f"infotype-{sys_abbr}"),
            "title": sys_info.get("information_type_title") or "Government & Mission Critical Cloud Workload Information",
            "description": sys_info.get("information_type_desc") or f"Federal / DoD mission operations data hosted in {impact} compliance boundary.",
            "categorizations": [{
                "system": "https://doi.org/10.6028/NIST.SP.800-60v2r1",
                "information-type-ids": sys_info.get("sp800_60_ids") or ["C.3.5.1"],
            }],
            "confidentiality-impact": {"base": fips_conf},
            "integrity-impact": {"base": fips_integ},
            "availability-impact": {"base": fips_avail},
        }
    ]


def _build_oscal_system_ids(sys_info: Dict[str, Any], sys_abbr: str) -> List[Dict[str, str]]:
    """Constructs OSCAL system-ids (RFC 4122 UUID plus any configured eMASS/DITPR/FedRAMP IDs)."""
    system_ids = [{
        "id": _deterministic_uuid(f"system-id-{sys_abbr}"),
        "identifier-type": "https://ietf.org/rfc/rfc4122",
    }]
    for keys, id_type in (
        (("emass_system_id", "emass_package_id"), "https://emass.apps.mil"),
        (("ditpr_id",), "https://dod.mil/ditpr"),
        (("fedramp_id", "package_id"), "https://fedramp.gov"),
    ):
        val = ""
        for k in keys:
            cand = str(sys_info.get(k) or "").strip()
            if cand:
                val = cand
                break
        if val and not is_unfilled_placeholder(val):
            system_ids.append({"id": val, "identifier-type": id_type})
    return system_ids


def build_oscal_system_characteristics(inventory: Dict[str, Any]) -> Dict[str, Any]:
    """Constructs OSCAL system-characteristics defining boundary, status, and impact.

    Args:
        inventory: System inventory dictionary.

    Returns:
        Structured OSCAL system-characteristics dictionary.
    """
    sys_info = inventory.get("system_information", {})
    net_info = inventory.get("network_architecture", {})

    sys_name, sys_abbr = resolve_system_identity(sys_info)
    impact = str(sys_info.get("impact_level") or "IL5").upper()
    baseline = sys_info.get("compliance_baseline") or "NIST SP 800-53 Rev. 5 / DoD IL5"
    fips_conf = (sys_info.get("confidentiality_impact") or "High").lower()
    fips_integ = (sys_info.get("integrity_impact") or "High").lower()
    fips_avail = (sys_info.get("availability_impact") or "High").lower()

    cloud_provider = (
        sys_info.get("cloud_provider")
        or inventory.get("cloud_provider")
        or "Google Cloud"
    )

    networks = [str(n) for n in (net_info.get("vpcs") or net_info.get("networks") or []) if n]
    network_clause = f"VPC networks ({', '.join(networks)})" if networks else "VPC networks"

    boundary_desc = (
        f"The authorization boundary for {sys_name} ({sys_abbr}) encompasses "
        f"all {cloud_provider} projects/accounts, {network_clause}, interconnects, "
        f"and managed PaaS/IaaS resources governed by organizational policies under "
        f"the {baseline} security baseline."
    )

    info_types_list = _build_oscal_information_types(
        sys_info, sys_abbr, impact, fips_conf, fips_integ, fips_avail
    )
    system_ids = _build_oscal_system_ids(sys_info, sys_abbr)

    return {
        "system-ids": system_ids,
        "system-name": sys_name,
        "system-name-short": sys_abbr,
        "description": sys_info.get("system_description") or boundary_desc,
        "security-sensitivity-level": impact.lower(),
        "system-information": {
            "information-types": info_types_list
        },
        "security-impact-level": {
            "security-objective-confidentiality": fips_conf,
            "security-objective-integrity": fips_integ,
            "security-objective-availability": fips_avail,
        },
        "status": {"state": "operational"},
        "authorization-boundary": {
            "description": boundary_desc,
        },
    }


def _add_workload_and_governance_components(
    add_comp: Any,
    sys_info: Dict[str, Any],
    infra_info: Dict[str, Any],
    app_info: Dict[str, Any],
) -> None:
    """Adds GKE/Compute, database, logging/monitoring, Assured Workloads, and app OSCAL components."""
    gke_clusters = infra_info.get("gke_clusters", [])
    vms = infra_info.get("compute_instances", [])
    if gke_clusters:
        add_comp(
            "gke",
            "software",
            "Google Kubernetes Engine (GKE) Private Clusters",
            f"Hardened container orchestration ({len(gke_clusters)} clusters) with private control plane, "
            f"Shielded nodes, and Workload Identity.",
        )
    elif vms:
        add_comp(
            "compute",
            "hardware",
            "Google Compute Engine Shielded Virtual Machines",
            f"Hardened virtual instances ({len(vms)} VMs) with vTPM, Secure Boot, and integrity monitoring.",
        )

    dbs = infra_info.get("databases", [])
    if dbs:
        db_engines = sorted(set(d.get("engine", "Cloud SQL") for d in dbs))
        engine_str = ", ".join(db_engines)
        add_comp(
            "database",
            "service",
            f"Google Cloud Managed Databases ({engine_str})",
            f"Enterprise managed databases ({len(dbs)} instances) with automated point-in-time recovery, "
            f"private IP VPC connectivity, and CMEK encryption.",
        )

    if is_dod_regime(sys_info):
        log_title = "Google Cloud Logging, Cloud Monitoring & CSSP Export Sinks"
        log_desc = (
            "Centralized audit logging sinks exporting security telemetry to external accredited CSSP (C5ISR/DISA) "
            "SIEM endpoints, continuous posture monitoring, and security health analytics."
        )
    else:
        log_title = "Google Cloud Logging, Cloud Monitoring & Security Command Center"
        log_desc = (
            "Centralized audit logging sinks, continuous threat detection, CIS benchmark posture monitoring, "
            "and security health analytics across GCP infrastructure."
        )
    add_comp("logging_monitoring", "service", log_title, log_desc)

    add_comp(
        "assured_workloads",
        "service",
        "Google Cloud Assured Workloads",
        "Automated compliance enforcement ensuring US-only data residency, personnel access restrictions, "
        "and IL4/IL5 regulatory baselines.",
    )

    for app in app_info.get("applications", []):
        app_name = app.get("name") or "Workload Application"
        add_comp(
            f"app_{app_name.lower().replace('-', '_')}",
            "software",
            f"Application Workload: {app_name}",
            f"Cloud-native workload deployed within the platform boundary ({app.get('type', 'service')}).",
        )


def build_oscal_components(inventory: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Constructs OSCAL components representing infrastructure, security services, and apps.

    Args:
        inventory: System inventory dictionary.

    Returns:
        A tuple of:
        1. List of OSCAL component dictionaries.
        2. Mapping from domain key (e.g. 'iam', 'vpc', 'kms') to component UUID string.
    """
    inventory = scrub_sensitive_data(inventory)
    sys_info = inventory.get("system_information", {})
    infra_info = inventory.get("infrastructure_components", {})
    net_info = inventory.get("network_architecture", {})
    app_info = inventory.get("application_components", {})
    _, sys_abbr = resolve_system_identity(sys_info)

    components: List[Dict[str, Any]] = []
    comp_map: Dict[str, str] = {}

    def _add_comp(
        comp_key: str,
        comp_type: str,
        title: str,
        description: str,
        props: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        c_uuid = _deterministic_uuid(f"comp-{sys_abbr}-{comp_key}")
        comp_map[comp_key] = c_uuid
        comp_entry: Dict[str, Any] = {
            "uuid": c_uuid,
            "type": comp_type,
            "title": title,
            "description": description,
            "purpose": f"Provides secure {title.lower()} capabilities for {sys_abbr}.",
            "status": {"state": "operational"},
        }
        if props:
            comp_entry["props"] = props
        components.append(comp_entry)
        return c_uuid

    sa_count = len(infra_info.get("service_accounts", []))
    _add_comp(
        "iam",
        "service",
        "Google Cloud Identity & Access Management (IAM)",
        f"Enterprise Identity, fine-grained role-based access control (RBAC), Workload Identity Federation, "
        f"and principle of least privilege managing {sa_count} scoped automation identities.",
        [{"name": "service-accounts-managed", "value": str(sa_count)}],
    )

    networks = net_info.get("vpcs") or net_info.get("networks") or []
    subnets = extract_clean_subnets(net_info.get("subnets_cidrs")) or net_info.get("subnets") or []
    _add_comp(
        "vpc",
        "service",
        "Google Cloud Virtual Private Cloud (VPC)",
        f"Software-defined Virtual Private Cloud networks ({len(networks)} networks, {len(subnets)} subnets) "
        f"discovered in Terraform.",
        [{"name": "network-count", "value": str(len(networks))}],
    )

    fw_count = len(net_info.get("firewall_rules", []))
    _add_comp(
        "firewall",
        "service",
        "Google Cloud Next-Generation Firewall & Security Policies",
        f"VPC firewall rules defined in Terraform: {fw_count}.",
        [{"name": "rules-count", "value": str(fw_count)}],
    )

    kms_keys = infra_info.get("kms_keys", [])
    kms_comp_desc = (
        f"Cloud KMS customer-managed encryption keys ({len(kms_keys)} discovered in Terraform). "
        f"{summarize_kms_protection(kms_keys)}."
        if kms_keys
        else (
            "Google Cloud Key Management Service (KMS) cryptographic key management component "
            "(0 customer-managed encryption keys currently discovered in Terraform; CMEK key ring provisioning pending)."
        )
    )
    kms_props = (
        [{"name": "fips-validation", "value": v} for v in sorted({kms_key_fips_attribute(k) for k in kms_keys})]
        if kms_keys
        else [{"name": "managed-keys", "value": "0"}]
    )
    _add_comp(
        "kms",
        "service",
        "Google Cloud KMS Customer-Managed Encryption Keys (CMEK)",
        kms_comp_desc,
        kms_props,
    )

    buckets = infra_info.get("storage_buckets", [])
    storage_comp_desc = (
        f"Cloud Storage buckets defined in Terraform: {len(buckets)} "
        f"({sum(1 for b in buckets if isinstance(b, dict) and b.get('uniform_bucket_level_access'))} with uniform bucket-level access, "
        f"{sum(1 for b in buckets if isinstance(b, dict) and (b.get('cmek_encrypted') or b.get('kms_key')))} with customer-managed keys)."
    )
    _add_comp("storage", "service", "Google Cloud Storage (GCS)", storage_comp_desc)

    _add_workload_and_governance_components(_add_comp, sys_info, infra_info, app_info)
    return components, comp_map


# (control id, requirement title, component key) for the OSCAL SSP control set. Status
# and narrative come from evidence.derive_control_status; nothing here asserts state.
_OSCAL_CONTROL_SET: Tuple[Tuple[str, str, str], ...] = (
    ("ac-2", "Account management", "iam"),
    ("ac-3", "Access enforcement", "iam"),
    ("ac-4", "Information flow enforcement", "vpc"),
    ("ac-6", "Least privilege", "iam"),
    ("au-2", "Event logging", "logging_monitoring"),
    ("au-3", "Content of audit records", "logging_monitoring"),
    ("au-12", "Audit record generation", "logging_monitoring"),
    ("cm-2", "Baseline configuration", "assured_workloads"),
    ("cm-6", "Configuration settings", "assured_workloads"),
    ("cm-8", "System component inventory", "logging_monitoring"),
    ("ia-2", "Identification and authentication (organizational users)", "iam"),
    ("mp-4", "Media storage", "storage"),
    ("ra-5", "Vulnerability monitoring and scanning", "logging_monitoring"),
    ("sa-9", "External system services", "assured_workloads"),
    ("sc-7", "Boundary protection", "firewall"),
    ("sc-8", "Transmission confidentiality and integrity", "vpc"),
    ("sc-12", "Cryptographic key establishment and management", "kms"),
    ("sc-13", "Cryptographic protection", "kms"),
    ("sc-28", "Protection of information at rest", "kms"),
    ("si-4", "System monitoring", "logging_monitoring"),
)


def open_poam_control_ids(inventory: Dict[str, Any]) -> Set[str]:
    """Normalized ids of controls with an open POA&M item for the active run."""
    open_ids: Set[str] = set()
    for finding in derive_poam_findings(inventory, target_dir=active_poam_target()):
        if str(finding.get("status") or "Ongoing").strip().lower() in ("ongoing", "open", "delayed", "in progress"):
            open_ids.update(extract_normalized_control_ids(f"{finding.get('control', '')} {finding.get('aps', '')}"))
    return open_ids


def build_oscal_control_implementations(
    inventory: Dict[str, Any],
    comp_map: Dict[str, str],
) -> Dict[str, Any]:
    """Constructs NIST SP 800-53 Rev. 5 control implementations mapped to components.

    Each requirement's implementation-status and narrative come from
    :func:`evidence.derive_control_status`, so ``implemented`` is stated only when
    the inventory contains the implementing resources and no POA&M item is open.

    Args:
        inventory: System inventory dictionary.
        comp_map: Mapping from component key to component UUID string.

    Returns:
        Structured OSCAL control-implementation dictionary.
    """
    sys_info = inventory.get("system_information", {})
    _, sys_abbr = resolve_system_identity(sys_info)
    open_ids = open_poam_control_ids(inventory)

    has_regime_cfg = any(
        k in sys_info for k in ("impact_level", "compliance_baseline", "governance_regime")
    )
    regime = require_supported_regime(sys_info) if has_regime_cfg else Regime.FEDRAMP_HIGH
    active_baseline = get_regime_baseline(regime)
    allowed_ids = {normalize_control_id(c) for c in active_baseline["control_ids"]}
    params_by_ctrl = active_baseline.get("parameters_by_control", {})

    requirements: List[Dict[str, Any]] = []
    for control_id, title, comp_key in _OSCAL_CONTROL_SET:
        norm_cid = normalize_control_id(control_id)
        if norm_cid not in allowed_ids:
            continue
        result = derive_control_status(inventory, control_id, open_ids)
        comp_uuid = comp_map.get(comp_key) or _deterministic_uuid(f"comp-{sys_abbr}-{comp_key}")
        by_component: Dict[str, Any] = {
            "component-uuid": comp_uuid,
            "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-{control_id}-{comp_key}"),
            "description": result.narrative,
            "implementation-status": {"state": result.status},
        }
        if result.gaps:
            by_component["implementation-status"]["remarks"] = "; ".join(result.gaps)
        req_dict: Dict[str, Any] = {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-{control_id}"),
            "control-id": control_id,
            "remarks": title,
            "by-components": [by_component],
        }
        ctrl_params = [
            {"param-id": str(p["param_id"]), "values": [str(p["value"])]}
            for p in params_by_ctrl.get(norm_cid, [])
            if p.get("param_id") and p.get("value") and "[CONFIG_REQUIRED" not in str(p["value"])
        ]
        if ctrl_params:
            req_dict["set-parameters"] = ctrl_params
        requirements.append(req_dict)

    return {
        "description": f"Control implementation narratives for {sys_abbr} mapped against NIST SP 800-53 Rev. 5.",
        "implemented-requirements": requirements,
    }


def generate_oscal_ssp(
    inventory: Dict[str, Any],
    doc_version: str = "1.0.0",
    oscal_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates a complete, standards-compliant NIST OSCAL System Security Plan (SSP).

    Args:
        inventory: System inventory dictionary.
        doc_version: Semantic document version.
        oscal_version: Optional target OSCAL specification version (e.g. '1.2.3' or '1.1.0').

    Returns:
        A root dictionary containing the 'system-security-plan' conforming to NIST OSCAL.
    """
    inventory = scrub_sensitive_data(inventory)
    sys_info = inventory.get("system_information", {})
    _, sys_abbr = resolve_system_identity(sys_info)
    active_oscal_version = resolve_oscal_version(inventory, oscal_version)
    import_profile = build_oscal_import_profile(sys_info)

    components, comp_map = build_oscal_components(inventory)
    control_impl = build_oscal_control_implementations(inventory, comp_map)

    ssp: Dict[str, Any] = {
        "system-security-plan": {
            "uuid": _deterministic_uuid(f"ssp-uuid-{sys_abbr}"),
            "metadata": build_oscal_metadata(inventory, doc_version, oscal_version=active_oscal_version),
            "import-profile": import_profile,
            "system-characteristics": build_oscal_system_characteristics(inventory),
            "system-implementation": {
                "users": [
                    {
                        "uuid": _deterministic_uuid(f"user-admin-{sys_abbr}"),
                        "title": "Cloud Platform Administrator",
                        "role-ids": ["system-owner"],
                    },
                    {
                        "uuid": _deterministic_uuid(f"user-security-{sys_abbr}"),
                        "title": "Security & Compliance Officer",
                        "role-ids": ["issm", "isso"],
                    },
                ],
                "components": components,
            },
            "control-implementation": control_impl,
        }
    }
    return ssp


def generate_oscal_component_definition(
    inventory: Dict[str, Any],
    doc_version: str = "1.0.0",
    oscal_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates an OSCAL Component Definition for the Cloud Foundations Fabric.

    Args:
        inventory: System inventory dictionary.
        doc_version: Semantic document version.
        oscal_version: Optional target OSCAL specification version (e.g. '1.2.3' or '1.1.0').

    Returns:
        Structured OSCAL component-definition dictionary.
    """
    inventory = scrub_sensitive_data(inventory)
    sys_info = inventory.get("system_information", {})
    _, sys_abbr = resolve_system_identity(sys_info)
    active_oscal_version = resolve_oscal_version(inventory, oscal_version)
    components, _comp_map = build_oscal_components(inventory)
    # SSP system-components require "status"; component-definition
    # defined-components do not allow it.
    defined_components = [
        {key: value for key, value in component.items() if key != "status"}
        for component in components
    ]

    metadata = build_oscal_metadata(inventory, doc_version, oscal_version=active_oscal_version)
    metadata["title"] = f"Cloud Foundations Fabric Component Definitions - {sys_abbr}"

    return {
        "component-definition": {
            "uuid": _deterministic_uuid(f"compdef-uuid-{sys_abbr}"),
            "metadata": metadata,
            "components": defined_components,
        }
    }


def export_oscal_artifacts(
    target_dir: Union[str, Path],
    inventory: Dict[str, Any],
    doc_version: str = "1.0.0",
    oscal_format: str = "both",
    oscal_version: Optional[str] = None,
) -> List[Path]:
    """Serializes and exports OSCAL deliverables (SSP and Component Definition).

    Args:
        target_dir: Base target workspace directory containing ato_artifacts.
        inventory: System inventory dictionary.
        doc_version: Semantic document version.
        oscal_format: Export preference: 'both', 'json', or 'yaml'.
        oscal_version: Optional target OSCAL specification version (e.g. '1.2.3' or '1.1.0').

    Returns:
        List of generated file Path objects.
    """
    target_path = resolve_path(target_dir)
    inventory = scrub_sensitive_data(inventory)
    out_dir = ensure_directory(target_path / "ato_artifacts" / "OSCAL_SSP")
    active_oscal_version = resolve_oscal_version(inventory, oscal_version)

    ssp_data = generate_oscal_ssp(inventory, doc_version=doc_version, oscal_version=active_oscal_version)
    comp_data = generate_oscal_component_definition(inventory, doc_version=doc_version, oscal_version=active_oscal_version)

    formats = ["json", "yaml"] if oscal_format.lower() in ("both", "all") else [oscal_format.lower()]
    created_paths: List[Path] = []

    if "json" in formats:
        ssp_json_path = out_dir / "system_security_plan.oscal.json"
        comp_json_path = out_dir / "component_definition.oscal.json"
        write_json_file(ssp_json_path, ssp_data, allowed_boundary=target_path)
        write_json_file(comp_json_path, comp_data, allowed_boundary=target_path)
        created_paths.extend([ssp_json_path, comp_json_path])

    if "yaml" in formats:
        ssp_yaml_path = out_dir / "system_security_plan.oscal.yaml"
        comp_yaml_path = out_dir / "component_definition.oscal.yaml"
        write_yaml_file(ssp_yaml_path, ssp_data, allowed_boundary=target_path)
        write_yaml_file(comp_yaml_path, comp_data, allowed_boundary=target_path)
        created_paths.extend([ssp_yaml_path, comp_yaml_path])

    logger.info("Successfully exported %d NIST OSCAL %s deliverable(s) to %s", len(created_paths), active_oscal_version, out_dir)
    return created_paths
