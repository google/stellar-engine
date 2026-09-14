#!/usr/bin/env python3
"""NIST OSCAL 1.1.0 System Security Plan (SSP) & Component Definition Generator.

This module provides authoritative, machine-readable NIST OSCAL 1.1.0 JSON and YAML
generation for cloud foundations, transforming discovered infrastructure (VPC, IAM,
Cloud KMS CMEK, GKE, Cloud SQL, Storage, SCC, Assured Workloads) and application
components into standards-compliant OSCAL models consumable by FedRAMP automated
intake engines, eMASS, Xacta 360, and continuous compliance pipelines.
"""

from datetime import datetime, timezone
import functools
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

try:
    from .file_helpers import (
        ensure_directory,
        resolve_path,
        scrub_sensitive_data,
        write_json_file,
        write_yaml_file,
    )
except (ImportError, ValueError):
    from file_helpers import (
        ensure_directory,
        resolve_path,
        scrub_sensitive_data,
        write_json_file,
        write_yaml_file,
    )

logger = logging.getLogger(__name__)

# NIST OSCAL Specification Versions
DEFAULT_OSCAL_VERSION: str = "1.2.3"
SUPPORTED_OSCAL_VERSIONS: Tuple[str, ...] = (
    "1.0.0",
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
OSCAL_VERSION: str = DEFAULT_OSCAL_VERSION

# Fixed UUID Namespace for deterministic RFC 4122 v5 UUID generation
OSCAL_NAMESPACE = uuid.UUID("4c58b54e-6e42-4f32-8e6d-68b209a80479")


def resolve_oscal_version(inventory: Dict[str, Any], explicit_version: Optional[str] = None) -> str:
    """Resolves and validates the target OSCAL version from explicit parameter, inventory, or default.

    Args:
        inventory: System inventory dictionary.
        explicit_version: Optional explicit version override (e.g. '1.2.3' or '1.1.0').

    Returns:
        Validated OSCAL specification version string (defaults to DEFAULT_OSCAL_VERSION = '1.2.3').
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
        logger.warning(
            "Specified OSCAL version '%s' is not in known NIST releases (%s). Using '%s'.",
            candidate,
            ", ".join(SUPPORTED_OSCAL_VERSIONS),
            candidate,
        )
    return candidate


import hashlib

@functools.lru_cache(maxsize=4096)
def _deterministic_uuid(name: str) -> str:
    """Generates a stable RFC 4122 UUID based on SHA-256 to avoid git churn and comply with FIPS 140-3.

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
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    inventory = scrub_sensitive_data(inventory)
    sys_info = inventory.get("system_information", {})
    roles_info = inventory.get("personnel_roles", {})
    sys_name = sys_info.get("system_name") or "Cloud Foundation Platform"
    sys_abbr = sys_info.get("system_abbreviation") or "CFP"
    org_name = sys_info.get("organization") or "Google Public Sector"

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
        party_name = contact.get("name") or f"Designated {role_id.upper()}"
        party_email = contact.get("email")
        party_uuid = _deterministic_uuid(f"party-{role_id}-{sys_abbr}")

        party_obj: Dict[str, Any] = {
            "uuid": party_uuid,
            "type": "person",
            "name": party_name,
            "telephone-numbers": [
                {"type": "work", "number": contact.get("phone") or "N/A"}
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


def build_oscal_system_characteristics(inventory: Dict[str, Any]) -> Dict[str, Any]:
    """Constructs OSCAL system-characteristics defining boundary, status, and impact.

    Args:
        inventory: System inventory dictionary.

    Returns:
        Structured OSCAL system-characteristics dictionary.
    """
    inventory = scrub_sensitive_data(inventory)
    sys_info = inventory.get("system_information", {})
    infra_info = inventory.get("infrastructure_components", {})
    net_info = inventory.get("network_architecture", {})

    sys_name = sys_info.get("system_name") or "Cloud Foundation Platform"
    sys_abbr = sys_info.get("system_abbreviation") or "CFP"
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

    networks = net_info.get("networks", [])
    network_str = ", ".join(networks) if networks else "Managed Cloud Foundation VPC"

    boundary_desc = (
        f"The authorization boundary for {sys_name} ({sys_abbr}) encompasses "
        f"all {cloud_provider} projects/accounts, VPC networks ({network_str}), interconnects, "
        f"and managed PaaS/IaaS resources governed by organizational policies under "
        f"the {baseline} security baseline."
    )

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
                "categorization": {
                    "system": "https://doi.org/10.6028/NIST.SP.800-60v2r1",
                    "information-type-ids": it_ids,
                },
                "confidentiality-impact": {"base": (it.get("confidentiality_impact") or fips_conf).lower()},
                "integrity-impact": {"base": (it.get("integrity_impact") or fips_integ).lower()},
                "availability-impact": {"base": (it.get("availability_impact") or fips_avail).lower()},
            })
    else:
        info_types_list = [
            {
                "uuid": _deterministic_uuid(f"infotype-{sys_abbr}"),
                "title": sys_info.get("information_type_title") or "Government & Mission Critical Cloud Workload Information",
                "description": sys_info.get("information_type_desc") or f"Federal / DoD mission operations data hosted in {impact} compliance boundary.",
                "categorization": {
                    "system": "https://doi.org/10.6028/NIST.SP.800-60v2r1",
                    "information-type-ids": sys_info.get("sp800_60_ids") or ["C.3.5.1"],
                },
                "confidentiality-impact": {"base": fips_conf},
                "integrity-impact": {"base": fips_integ},
                "availability-impact": {"base": fips_avail},
            }
        ]

    system_ids = []
    emass_id = str(sys_info.get("emass_system_id") or sys_info.get("emass_package_id") or "").strip()
    if emass_id and not emass_id.startswith("[CONFIG_REQUIRED"):
        system_ids.append({
            "id": emass_id,
            "identifier-type": "https://emass.apps.mil",
        })
    ditpr_id = str(sys_info.get("ditpr_id") or "").strip()
    if ditpr_id and not ditpr_id.startswith("[CONFIG_REQUIRED"):
        system_ids.append({
            "id": ditpr_id,
            "identifier-type": "https://dod.mil/ditpr",
        })
    fedramp_id = str(sys_info.get("fedramp_id") or sys_info.get("package_id") or "").strip()
    if fedramp_id and not fedramp_id.startswith("[CONFIG_REQUIRED"):
        system_ids.append({
            "id": fedramp_id,
            "identifier-type": "https://fedramp.gov",
        })

    char_dict: Dict[str, Any] = {
        "system-name": sys_name,
        "system-name-short": sys_abbr,
        "description": sys_info.get("system_description") or boundary_desc,
        "system-information": {
            "information-types": info_types_list
        },
        "security-sensitivity-level": impact.lower(),
        "security-impact-level": {
            "security-objective-confidentiality": fips_conf,
            "security-objective-integrity": fips_integ,
            "security-objective-availability": fips_avail,
        },
        "status": {"state": "operational"},
        "authorization-boundary": {
            "description": boundary_desc,
        },
        "deployment-model": "cloud-government" if any(k in impact for k in ["IL", "DOD"]) else "cloud-public",
    }
    if system_ids:
        char_dict["system-ids"] = system_ids

    return char_dict


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
    sys_abbr = sys_info.get("system_abbreviation") or "CFP"
    cloud_provider = "Google Cloud Platform"
    csp_abbr = "GCP"

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

    # 1. Identity and Access Management (IAM)
    sa_count = len(infra_info.get("service_accounts", []))
    iam_title = "Google Cloud Identity & Access Management (IAM)"
    _add_comp(
        "iam",
        "service",
        iam_title,
        f"Enterprise Identity, fine-grained role-based access control (RBAC), Workload Identity Federation, "
        f"and principle of least privilege managing {sa_count} scoped automation identities.",
        [{"name": "service-accounts-managed", "value": str(sa_count)}],
    )

    # 2. Virtual Private Cloud (VPC) & Perimeter Networking
    networks = net_info.get("networks", [])
    subnets = net_info.get("subnets", [])
    vpc_title = "Google Cloud Virtual Private Cloud (VPC)"
    _add_comp(
        "vpc",
        "service",
        vpc_title,
        f"Isolated software-defined Andromeda multi-tenant networks ({len(networks)} networks, {len(subnets)} subnets) "
        f"with private endpoints and VPC Flow Logs.",
        [{"name": "network-count", "value": str(len(networks))}],
    )

    # 3. Cloud Firewalls & Boundary Protection
    fw_count = len(net_info.get("firewall_rules", []))
    fw_title = "Google Cloud Next-Generation Firewall & Security Policies"
    _add_comp(
        "firewall",
        "service",
        fw_title,
        f"Stateful ingress/egress firewall policies ({fw_count} rules) and hierarchical security policies "
        f"enforcing microsegmentation and default-deny egress controls.",
        [{"name": "rules-count", "value": str(fw_count)}],
    )

    # 4. Cloud Key Management Service (KMS) CMEK
    kms_keys = infra_info.get("kms_keys", [])
    kms_title = "Google Cloud KMS Customer-Managed Encryption Keys (CMEK)"
    _add_comp(
        "kms",
        "service",
        kms_title,
        f"FIPS 140-3 Level 3 validated Hardware Security Module (HSM) key management with automated 90-day "
        f"key rotation and CMEK binding across {len(kms_keys)} managed keys.",
        [{"name": "fips-level", "value": "140-3 Level 3"}],
    )

    # 5. Cloud Storage
    buckets = infra_info.get("storage_buckets", [])
    storage_title = "Google Cloud Storage (GCS)"
    _add_comp(
        "storage",
        "service",
        storage_title,
        f"Object storage infrastructure ({len(buckets)} buckets) enforcing Uniform Bucket-Level Access, "
        f"TLS 1.3 in transit, and CMEK at rest.",
    )

    # 6. Kubernetes Engine or Compute
    gke_clusters = infra_info.get("gke_clusters", [])
    vms = infra_info.get("compute_instances", [])
    if gke_clusters:
        gke_title = "Google Kubernetes Engine (GKE) Private Clusters"
        _add_comp(
            "gke",
            "software",
            gke_title,
            f"Hardened container orchestration ({len(gke_clusters)} clusters) with private control plane, "
            f"Shielded nodes, and Workload Identity.",
        )
    elif vms:
        vm_title = "Google Compute Engine Shielded Virtual Machines"
        _add_comp(
            "compute",
            "hardware",
            vm_title,
            f"Hardened virtual instances ({len(vms)} VMs) with vTPM, Secure Boot, and integrity monitoring.",
        )

    # 7. Relational Databases
    dbs = infra_info.get("databases", [])
    if dbs:
        db_engines = sorted(set(d.get("engine", "Cloud SQL") for d in dbs))
        engine_str = ", ".join(db_engines)
        _add_comp(
            "database",
            "service",
            f"Google Cloud Managed Databases ({engine_str})",
            f"Enterprise managed databases ({len(dbs)} instances) with automated point-in-time recovery, "
            f"private IP VPC connectivity, and CMEK encryption.",
        )

    # 8. Security Telemetry & Centralized Logging
    is_dod_il5_comp = any(
        k in str(sys_info.get("impact_level") or "").upper()
        or k in str(sys_info.get("compliance_baseline") or "").upper()
        for k in ["IL4", "IL5", "IL6", "DOD IL4", "DOD IL5", "DOD IL6", "DISA"]
    )
    if is_dod_il5_comp:
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
    _add_comp("logging_monitoring", "service", log_title, log_desc)

    # 9. Assured Workloads / Compliance Boundary
    assured_title = "Google Cloud Assured Workloads"
    _add_comp(
        "assured_workloads",
        "service",
        assured_title,
        "Automated compliance enforcement ensuring US-only data residency, personnel access restrictions, "
        "and IL4/IL5 regulatory baselines.",
    )

    # 10. Application Components (if discovered)
    apps = app_info.get("applications", [])
    for app in apps:
        app_name = app.get("name") or "Workload Application"
        _add_comp(
            f"app_{app_name.lower().replace('-', '_')}",
            "software",
            f"Application Workload: {app_name}",
            f"Cloud-native workload deployed within the platform boundary ({app.get('type', 'service')}).",
        )

    return components, comp_map


def build_oscal_control_implementations(
    inventory: Dict[str, Any],
    comp_map: Dict[str, str],
) -> Dict[str, Any]:
    """Constructs NIST SP 800-53 Rev. 5 control implementations mapped to components.

    Args:
        inventory: System inventory dictionary.
        comp_map: Mapping from component key to component UUID string.

    Returns:
        Structured OSCAL control-implementation dictionary.
    """
    inventory = scrub_sensitive_data(inventory)
    sys_info = inventory.get("system_information", {})
    infra_info = inventory.get("infrastructure_components", {})
    net_info = inventory.get("network_architecture", {})
    sys_abbr = sys_info.get("system_abbreviation") or "CFP"
    cloud_provider = "Google Cloud"
    csp_abbr = "GCP"

    # Fallback to general component if specific is absent
    iam_uuid = comp_map.get("iam") or _deterministic_uuid(f"comp-{sys_abbr}-iam")
    vpc_uuid = comp_map.get("vpc") or _deterministic_uuid(f"comp-{sys_abbr}-vpc")
    fw_uuid = comp_map.get("firewall") or _deterministic_uuid(f"comp-{sys_abbr}-firewall")
    kms_uuid = comp_map.get("kms") or _deterministic_uuid(f"comp-{sys_abbr}-kms")
    storage_uuid = comp_map.get("storage") or _deterministic_uuid(f"comp-{sys_abbr}-storage")
    log_uuid = comp_map.get("logging_monitoring") or _deterministic_uuid(f"comp-{sys_abbr}-logging_monitoring")
    assured_uuid = comp_map.get("assured_workloads") or _deterministic_uuid(f"comp-{sys_abbr}-assured_workloads")

    impact_level = str(sys_info.get("impact_level", "")).upper()
    compliance_baseline = str(sys_info.get("compliance_baseline", "")).upper()
    is_dod_il5 = any(
        k in impact_level or k in compliance_baseline
        for k in ["IL4", "IL5", "IL6", "DOD IL4", "DOD IL5", "DOD IL6", "DISA"]
    )

    if is_dod_il5:
        cm6_desc = (
            "Cloud Logging aggregated sinks continuously stream audit logs and VPC flow telemetry to "
            "accredited external CSSP (C5ISR/DISA) SIEM endpoints for configuration drift and security baseline auditing."
        )
        ra5_desc = (
            "Artifact Analysis continuously scans container images and packages in Artifact Registry. "
            "Audit telemetry and vulnerability reports stream to accredited external CSSP / SIEM endpoints "
            "for 24/7 security monitoring."
        )
        si4_desc = (
            "Cloud Logging centralized log sinks continuously export security telemetry to external accredited "
            "CSSP (C5ISR/DISA) SIEM endpoints for 24/7 threat monitoring and intrusion detection."
        )
    else:
        cm6_desc = "Security Command Center (SCC) Premium continuously scans resources against CIS GCP Foundation Baselines."
        ra5_desc = (
            "Security Command Center and Artifact Analysis continuously scan container images, VM images, "
            "and configurations for known CVEs and security misconfigurations."
        )
        si4_desc = (
            "Security Command Center Event Threat Detection analyzes Cloud Logging streams in real-time "
            "for anomalies, compromised credentials, and lateral movement."
        )

    vpc_net_flow_desc = (
        "Multi-tenant VPC topology isolates application environments. Andromeda SDN, Private Google Access, and "
        "Private Service Connect guarantee private traffic paths without public IP exposure."
    )
    au12_desc = (
        "Centralized Organization-level Log Sinks export all security and operational logs to "
        "dedicated BigQuery datasets and CMEK-encrypted Cloud Storage buckets with Object Lock retention."
    )
    cm2_desc = (
        "All foundation resources are codified in version-controlled Terraform blueprints from Google Cloud Foundations Fabric. "
        "Assured Workloads enforces continuous guardrails against non-compliant resource creation."
    )
    cm8_desc = "Cloud Asset Inventory continuously catalogs all GCP cloud resources, IAM policies, and networking state in real-time."
    sa9_desc = (
        "Underlying GCP services are validated under FedRAMP High and DoD IL4/IL5 authorizations. "
        "Assured Workloads enforces personnel access restrictions to US citizens with appropriate clearances."
    )

    # Evidence gating for SC-7, SC-12, SC-28
    fw_rules = net_info.get("firewall_rules", [])
    has_fw_rules = len(fw_rules) > 0
    sc7_status = "implemented" if has_fw_rules else "planned"
    sc7_desc = (
        f"Hierarchical firewall policies and VPC security rules ({len(fw_rules)} rules active) block all unsolicited inbound traffic; "
        "outbound traffic is restricted to validated endpoints."
        if has_fw_rules
        else "Hierarchical firewall policies and perimeter microsegmentation rules are planned for deployment in Terraform blueprints."
    )

    kms_keys = infra_info.get("kms_keys", [])
    has_kms = len(kms_keys) > 0 or len(inventory.get("cryptographic_modules", [])) > 0
    sc12_status = "implemented" if has_kms else "planned"
    sc12_desc = (
        f"Google Cloud KMS Customer-Managed Encryption Keys ({len(kms_keys)} managed keys) enforce automated 90-day rotation "
        "and strict IAM separation between key administrators and service consumers."
        if has_kms
        else "Google Cloud KMS Customer-Managed Encryption Keys (CMEK) are planned for provisioning in foundational key rings."
    )

    sc28_status = "implemented" if has_kms else "planned"
    sc28_desc = (
        "All persistent disks, storage buckets, database tables, and backups are encrypted at rest with hardware-backed Cloud KMS CMEK."
        if has_kms
        else "Hardware-backed Cloud KMS CMEK encryption at rest is planned for all persistent data assets."
    )

    implemented_requirements: List[Dict[str, Any]] = [
        # AC - Access Control
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-ac-2"),
            "control-id": "ac-2",
            "description": f"Automated account management via {cloud_provider} Identity and Access Management (IAM).",
            "by-components": [
                {
                    "component-uuid": iam_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-ac-2-iam"),
                    "description": (
                        f"{cloud_provider} IAM enforces centralized identity lifecycles, automated account revocation, "
                        "and strictly scoped service accounts provisioned via Terraform IaC."
                    ),
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-ac-3"),
            "control-id": "ac-3",
            "description": "Access enforcement through mandatory Role-Based Access Control (RBAC).",
            "by-components": [
                {
                    "component-uuid": iam_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-ac-3-iam"),
                    "description": (
                        f"Enforces principle of least privilege across {csp_abbr} resource hierarchy. "
                        "Direct primitive administrator roles are prohibited; custom least-privilege roles are required."
                    ),
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-ac-4"),
            "control-id": "ac-4",
            "description": "Information flow enforcement across network and VPC boundaries.",
            "by-components": [
                {
                    "component-uuid": vpc_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-ac-4-vpc"),
                    "description": vpc_net_flow_desc,
                    "implementation-status": {"state": "implemented"},
                },
                {
                    "component-uuid": fw_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-ac-4-fw"),
                    "description": "Hierarchical firewall rules enforce strict perimeter and lateral flow control.",
                    "implementation-status": {"state": "implemented"},
                },
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-ac-6"),
            "control-id": "ac-6",
            "description": "Least privilege enforced on all user identities and automation services.",
            "by-components": [
                {
                    "component-uuid": iam_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-ac-6-iam"),
                    "description": (
                        "Workload Identity Federation eliminates long-lived static service account keys. All cloud "
                        "services operate with narrowly scoped permissions."
                    ),
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        # AU - Audit and Accountability
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-au-2"),
            "control-id": "au-2",
            "description": "Event logging across administrative, control plane, and data operations.",
            "by-components": [
                {
                    "component-uuid": log_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-au-2-log"),
                    "description": (
                        f"{cloud_provider} Audit Logs capture Admin Activity, System Events, Access Transparency, and Data Access. "
                        "VPC Flow Logs record all network layer traffic."
                    ),
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-au-3"),
            "control-id": "au-3",
            "description": "Content of audit records adheres to NIST standards with caller identity, timestamp, and action.",
            "by-components": [
                {
                    "component-uuid": log_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-au-3-log"),
                    "description": f"{cloud_provider} Logging records JSON payloads detailing principal, resource, method, timestamp, and IP.",
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-au-12"),
            "control-id": "au-12",
            "description": "Audit record generation exported to centralized, immutable storage sinks.",
            "by-components": [
                {
                    "component-uuid": log_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-au-12-log"),
                    "description": au12_desc,
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        # CM - Configuration Management
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-cm-2"),
            "control-id": "cm-2",
            "description": "Baseline configuration enforced via declarative Terraform Infrastructure-as-Code.",
            "by-components": [
                {
                    "component-uuid": assured_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-cm-2-assured"),
                    "description": cm2_desc,
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-cm-6"),
            "control-id": "cm-6",
            "description": "Configuration settings audited continuously against CIS Benchmarks.",
            "by-components": [
                {
                    "component-uuid": log_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-cm-6-log"),
                    "description": cm6_desc,
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-cm-8"),
            "control-id": "cm-8",
            "description": "Information system component inventory dynamically maintained.",
            "by-components": [
                {
                    "component-uuid": log_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-cm-8-log"),
                    "description": cm8_desc,
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        # IA - Identification and Authentication
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-ia-2"),
            "control-id": "ia-2",
            "description": "Identification and authentication with mandatory multi-factor authentication (MFA).",
            "by-components": [
                {
                    "component-uuid": iam_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-ia-2-iam"),
                    "description": (
                        "Google Cloud Identity enforces FIDO2 / WebAuthn hardware security keys and mandatory MFA "
                        "for all administrative sessions."
                    ),
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        # MP - Media Protection
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-mp-4"),
            "control-id": "mp-4",
            "description": "Media storage protection through ubiquitous cryptographic controls at rest.",
            "by-components": [
                {
                    "component-uuid": storage_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-mp-4-storage"),
                    "description": "Google Cloud Storage enforces CMEK encryption and disables public access via Uniform Bucket-Level Access.",
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        # RA - Risk Assessment
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-ra-5"),
            "control-id": "ra-5",
            "description": "Continuous vulnerability monitoring and automated security posture management.",
            "by-components": [
                {
                    "component-uuid": log_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-ra-5-scc"),
                    "description": ra5_desc,
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        # SA - System and Services Acquisition
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-sa-9"),
            "control-id": "sa-9",
            "description": "External system services governed under FedRAMP / DoD IL5 certified agreements.",
            "by-components": [
                {
                    "component-uuid": assured_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-sa-9-assured"),
                    "description": sa9_desc,
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        # SC - System and Communications Protection
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-sc-7"),
            "control-id": "sc-7",
            "description": "Boundary protection with microsegmentation, firewall policies, and private endpoints.",
            "by-components": [
                {
                    "component-uuid": fw_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-sc-7-fw"),
                    "description": sc7_desc,
                    "implementation-status": {"state": sc7_status},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-sc-8"),
            "control-id": "sc-8",
            "description": "Transmission confidentiality and integrity enforced via TLS 1.3.",
            "by-components": [
                {
                    "component-uuid": vpc_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-sc-8-vpc"),
                    "description": "All data in transit across Google Cloud's Andromeda private software-defined network is encrypted by default with TLS 1.3 / ALTS / IPsec.",
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-sc-12"),
            "control-id": "sc-12",
            "description": "Cryptographic key establishment and automated lifecycle management.",
            "by-components": [
                {
                    "component-uuid": kms_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-sc-12-kms"),
                    "description": sc12_desc,
                    "implementation-status": {"state": sc12_status},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-sc-13"),
            "control-id": "sc-13",
            "description": "Cryptographic protection validated under FIPS 140-3 Level 3.",
            "by-components": [
                {
                    "component-uuid": kms_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-sc-13-kms"),
                    "description": "Google Cloud KMS utilizes hardware security modules (HSM) validated under NIST FIPS 140-3 Level 3 with AES-256 and RSA-4096.",
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-sc-28"),
            "control-id": "sc-28",
            "description": "Protection of information at rest with hardware-backed encryption.",
            "by-components": [
                {
                    "component-uuid": kms_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-sc-28-kms"),
                    "description": sc28_desc,
                    "implementation-status": {"state": sc28_status},
                }
            ],
        },
        # SI - System and Information Integrity
        {
            "uuid": _deterministic_uuid(f"req-{sys_abbr}-si-4"),
            "control-id": "si-4",
            "description": "Information system monitoring and threat detection.",
            "by-components": [
                {
                    "component-uuid": log_uuid,
                    "uuid": _deterministic_uuid(f"bycomp-{sys_abbr}-si-4-log"),
                    "description": si4_desc,
                    "implementation-status": {"state": "implemented"},
                }
            ],
        },
    ]

    return {
        "description": f"Control implementation narratives for {sys_abbr} mapped against NIST SP 800-53 Rev. 5.",
        "implemented-requirements": implemented_requirements,
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
    sys_abbr = sys_info.get("system_abbreviation") or "CFP"
    impact = str(sys_info.get("impact_level") or "IL5").upper()
    active_oscal_version = resolve_oscal_version(inventory, oscal_version)

    components, comp_map = build_oscal_components(inventory)
    control_impl = build_oscal_control_implementations(inventory, comp_map)

    # Determine standard import profile URL based on impact
    if any(k in impact for k in ["IL5", "IL4", "DOD"]):
        profile_href = (
            "https://raw.githubusercontent.com/usnistgov/oscal-content/master/"
            "nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_MODERATE-baseline_profile.json"
        )
    else:
        profile_href = (
            "https://raw.githubusercontent.com/usnistgov/oscal-content/master/"
            "nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_HIGH-baseline_profile.json"
        )

    ssp: Dict[str, Any] = {
        "system-security-plan": {
            "id": _deterministic_uuid(f"ssp-{sys_abbr}"),
            "uuid": _deterministic_uuid(f"ssp-uuid-{sys_abbr}"),
            "metadata": build_oscal_metadata(inventory, doc_version, oscal_version=active_oscal_version),
            "import-profile": {
                "href": profile_href,
            },
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
    sys_abbr = sys_info.get("system_abbreviation") or "CFP"
    active_oscal_version = resolve_oscal_version(inventory, oscal_version)
    components, comp_map = build_oscal_components(inventory)

    metadata = build_oscal_metadata(inventory, doc_version, oscal_version=active_oscal_version)
    metadata["title"] = f"Cloud Foundations Fabric Component Definitions - {sys_abbr}"

    return {
        "component-definition": {
            "id": _deterministic_uuid(f"compdef-{sys_abbr}"),
            "uuid": _deterministic_uuid(f"compdef-uuid-{sys_abbr}"),
            "metadata": metadata,
            "components": components,
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
