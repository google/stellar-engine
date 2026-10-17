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

"""Canonical Hardware/Software and PPSM record builders shared by YAML and XLSM exporters."""

import re
from typing import Any, Callable, Dict, List, Sequence, Set, Tuple

from .extract_system_data import clean_interpolated_string, is_valid_resource_name
from .file_helpers import (
    NOT_DETERMINED,
    extract_clean_subnets,
    has_terraform_infrastructure,
    is_dod_regime,
    kms_key_fips_attribute,
    kms_protection_level,
    sanitize_container_image_tag,
    sanitize_software_package_identity,
)
from .service_catalog import resolve_gcp_service

TENANT_OS_FW = "Google Cloud managed hypervisor (inherited from CSP)"
KMS_API_ENDPOINT = "cloudkms.googleapis.com"

_EMBEDDED_DB_VER_RE = re.compile(
    r"\b(PostgreSQL\s+\d+(?:\.\d+)?|MySQL\s+\d+(?:\.\d+)?|SQL\s+Server\s+\d{4})\b",
    re.IGNORECASE,
)


def tenant_ip_summary(clean_subnets: Sequence[str]) -> str:
    """Subnet CIDRs for the cloud tenant row, or the not-determined token."""
    return ", ".join(clean_subnets) if clean_subnets else NOT_DETERMINED


def gke_cluster_fields(gke: Any) -> Tuple[str, str, str, str]:
    """Returns (name, ip, model, os/firmware) for a GKE cluster record or bare name."""
    record = gke if isinstance(gke, dict) else {"name": str(gke)}
    name = clean_interpolated_string(record.get("name") or "gke-cluster", default_val="gke-cluster")
    ip = record.get("master_ipv4_cidr_block") or NOT_DETERMINED
    version = record.get("master_version") or NOT_DETERMINED
    return name, ip, f"GKE Cluster ({version})", f"Google Container-Optimized OS (COS) / K8s {version}"


def compute_vm_fields(vm: dict, vm_name: str, clean_subnets: Sequence[str], sys_abbr: str) -> Tuple[str, str, str]:
    """Returns (ip, serial/self-link, os image) for a Compute Engine instance record."""
    raw_sub = vm.get("subnetwork")
    subnet = clean_interpolated_string(raw_sub, default_val="workload-subnet") if raw_sub else "workload-subnet"
    if subnet in ("subnet_id", "subnet", ""):
        subnet = "workload-subnet"
    ip = vm.get("network_ip") or (f"Private Subnet: {subnet} ({clean_subnets[0]})" if clean_subnets else NOT_DETERMINED)
    serial = vm.get("self_link") or f"projects/{sys_abbr}/zones/{vm.get('zone') or NOT_DETERMINED}/instances/{vm_name}"
    image = clean_interpolated_string(vm.get("image") or NOT_DETERMINED, default_val=NOT_DETERMINED)
    for marker in ("/family/", "/images/"):
        if marker in image:
            image = image.split(marker)[-1].strip()
            break
    return ip, serial, image


def resolve_db_asset_and_os(raw_type: str, raw_ver: str, engine_val: str) -> Tuple[str, str]:
    """Resolves canonical database asset name and OS/engine version without inventing PostgreSQL 15."""
    t_low = str(raw_type or "").lower()
    raw_ver_clean = str(raw_ver or "").strip()
    if not raw_ver_clean or raw_ver_clean == NOT_DETERMINED:
        m = _EMBEDDED_DB_VER_RE.search(str(raw_type or ""))
        effective_ver = m.group(1) if m else NOT_DETERMINED
    else:
        effective_ver = clean_interpolated_string(raw_ver_clean, default_val=raw_ver_clean)

    if "bigquery" in t_low:
        return "BigQuery Analytics Dataset", "BigQuery Managed Analytics Engine"
    if "redis" in t_low:
        return "Memorystore Redis HA Cluster", "Redis 7.0 / Managed In-Memory Engine"
    if "spanner" in t_low:
        return "Cloud Spanner Instance", "Cloud Spanner Distributed Relational Engine"
    if "alloydb" in t_low:
        return "AlloyDB PostgreSQL Cluster", f"{effective_ver} / AlloyDB Managed Engine"

    v_low = f"{t_low} {effective_ver} {engine_val or ''}".lower()
    if "mysql" in v_low:
        engine_name, os_base = "MySQL", "Debian Linux Base"
    elif any(k in v_low for k in ("sqlserver", "sql_server", "mssql", "sql server")):
        engine_name, os_base = "SQL Server", "Windows Server Base"
    elif "postgres" in v_low or (
        effective_ver != NOT_DETERMINED and any(v in effective_ver.lower() for v in ("13", "14", "15", "16"))
    ):
        engine_name, os_base = "PostgreSQL", "Debian Linux Base"
    else:
        engine_name, os_base = "", "Managed Database Base"

    prefix = f"Cloud SQL {engine_name} Instance".replace("  ", " ") if engine_name else "Cloud SQL Database Instance"
    if effective_ver == NOT_DETERMINED:
        db_os_str = f"{engine_name} ({NOT_DETERMINED}) / {os_base}" if engine_name else NOT_DETERMINED
    elif engine_name and os_base:
        db_os_str = (
            f"{engine_name} {effective_ver} / {os_base}"
            if engine_name.lower() not in effective_ver.lower()
            else f"{effective_ver} / {os_base}"
        )
    else:
        db_os_str = str(effective_ver)
    return prefix, db_os_str


def _build_db_hardware_records(
    infra_info: Dict[str, Any],
    resolve_hw_type: Callable[[str], str],
    clean_subnets: List[str],
    csp_abbr: str,
    sys_abbr: str,
    location: str,
    start_id: int,
) -> Tuple[List[Dict[str, Any]], int]:
    """Builds canonical database hardware asset dictionaries."""
    records: List[Dict[str, Any]] = []
    hw_type_db = resolve_hw_type("database")
    seen_dbs: Set[Tuple[str, str]] = set()
    hw_id = start_id
    for db in infra_info.get("databases", []):
        raw_db_name = db.get("name", "db-instance")
        db_name = clean_interpolated_string(raw_db_name, default_val=raw_db_name)
        if not is_valid_resource_name(db_name) or db_name in ("name", "id", "db", "database"):
            continue
        raw_type = db.get("type", "Cloud Database Instance")
        raw_ver = db.get("database_version") or db.get("engine_version") or ""
        db_asset_name, db_os = resolve_db_asset_and_os(raw_type, raw_ver, db.get("engine", ""))
        dedup_key = (db_asset_name, db_name)
        if dedup_key in seen_dbs:
            continue
        seen_dbs.add(dedup_key)
        db_tier = db.get("tier") or "Managed Tier"
        p_net = db.get("private_network")
        clean_pnet = clean_interpolated_string(str(p_net), default_val="") if p_net else ""
        if p_net and "psa_private_network" in str(p_net):
            db_ip = f"Private VPC / PSC ({clean_subnets[0]})" if clean_subnets else NOT_DETERMINED
        elif clean_pnet and is_valid_resource_name(clean_pnet) and not any(
            k in clean_pnet.lower() for k in ("var.", "local.", "vpc_id", "each.", "try(")
        ):
            db_ip = f"Private VPC ({clean_pnet})"
        else:
            db_ip = "Private Service Connect / Internal Endpoint"
        records.append({
            "hw_id": hw_id,
            "component_type": hw_type_db,
            "asset_name": db_asset_name,
            "nickname": str(db_name),
            "mac_address": "Dynamic SDN MAC",
            "asset_ip_address": db_ip,
            "public_facing": "No",
            "fqdn": "N/A",
            "vlan": "N/A",
            "virtual_asset": "Yes",
            "manufacturer": "Google Cloud Platform",
            "model_number": f"{db_asset_name} ({db_tier})",
            "serial_number": f"{csp_abbr}-DB-{sys_abbr}-{hw_id:03d}",
            "os_fw_version": db_os,
            "purpose_notes": "Managed Cloud DB Allocation",
            "location": location,
            "approval_status": "Pending Assessment",
            "critical_asset": "Yes",
        })
        hw_id += 1
    return records, hw_id


def _build_kms_and_vm_hardware_records(
    infra_info: Dict[str, Any],
    resolve_hw_type: Callable[[str], str],
    clean_subnets: List[str],
    csp_abbr: str,
    sys_abbr: str,
    location: str,
    start_id: int,
) -> List[Dict[str, Any]]:
    """Builds canonical KMS/HSM and Compute VM hardware asset dictionaries."""
    records: List[Dict[str, Any]] = []
    hw_id = start_id
    hw_type_hsm = resolve_hw_type("hsm_kms")
    seen_kms: Set[str] = set()
    for k in infra_info.get("kms_keys", []):
        raw_k_name = k.get("name", "kms-key")
        k_name = clean_interpolated_string(raw_k_name, default_val=raw_k_name)
        if not is_valid_resource_name(k_name) or k_name in ("name", "key", "keys", "keyring") or k_name in seen_kms:
            continue
        seen_kms.add(k_name)
        k_prot = kms_protection_level(k) or "UNDETERMINED"
        k_loc = k.get("location") or location
        k_asset_name = "Cloud KMS Cloud HSM Key" if k_prot == "HSM" else "Cloud KMS Cryptographic Key"
        k_mfg = "Google Cloud Platform / Marvell (formerly Cavium) HSM" if k_prot == "HSM" else "Google Cloud Platform"
        records.append({
            "hw_id": hw_id,
            "component_type": hw_type_hsm,
            "asset_name": k_asset_name,
            "nickname": str(k_name),
            "mac_address": "N/A (Hardware HSM)" if k_prot == "HSM" else "N/A (Virtual Key Management)",
            "asset_ip_address": KMS_API_ENDPOINT,
            "public_facing": "No",
            "fqdn": KMS_API_ENDPOINT,
            "vlan": NOT_DETERMINED,
            "virtual_asset": "No" if k_prot == "HSM" else "Yes",
            "manufacturer": k_mfg,
            "model_number": f"Cloud KMS ({k_prot})",
            "serial_number": f"{csp_abbr}-KMS-{sys_abbr}-{hw_id:03d}",
            "os_fw_version": kms_key_fips_attribute(k),
            "purpose_notes": "Hardware Cryptographic Key Store" if k_prot == "HSM" else "Software Key Store",
            "location": k_loc,
            "approval_status": "Pending Assessment",
            "critical_asset": "Yes",
        })
        hw_id += 1

    hw_type_vm = resolve_hw_type("compute_vm")
    seen_vms: Set[str] = set()
    for vm in infra_info.get("compute_instances", []):
        raw_vm_name = vm.get("name", "vm-instance")
        vm_name = clean_interpolated_string(raw_vm_name, default_val=raw_vm_name)
        if not is_valid_resource_name(vm_name) or vm_name in ("name", "vm", "instance") or vm_name in seen_vms:
            continue
        seen_vms.add(vm_name)
        m_type = vm.get("machine_type") or NOT_DETERMINED
        ip_addr, sn, vm_os = compute_vm_fields(vm, vm_name, clean_subnets, sys_abbr)
        records.append({
            "hw_id": hw_id,
            "component_type": hw_type_vm,
            "asset_name": "Google Compute Engine VM Instance",
            "nickname": str(vm_name),
            "mac_address": "Dynamic SDN MAC",
            "asset_ip_address": ip_addr,
            "public_facing": "No",
            "fqdn": "N/A",
            "vlan": "N/A",
            "virtual_asset": "Yes",
            "manufacturer": "Google Cloud Platform",
            "model_number": str(m_type),
            "serial_number": str(sn),
            "os_fw_version": str(vm_os),
            "purpose_notes": f"Hardened Compute Engine Workload Instance ({vm_name})",
            "location": location,
            "approval_status": "Pending Assessment",
            "critical_asset": "Yes",
        })
        hw_id += 1
    return records


def _build_software_records(
    inventory: Dict[str, Any],
    sys_info: Dict[str, Any],
    infra_info: Dict[str, Any],
    app_info: Dict[str, Any],
    resolve_sw_type: Callable[[str], str],
    cloud_provider: str,
    csp_abbr: str,
) -> List[Dict[str, Any]]:
    """Builds canonical software asset dictionaries for services, Terraform, apps, containers, and packages."""
    sw_records: List[Dict[str, Any]] = []
    sw_idx = 1
    custom_svcs = inventory.get("custom_services") or {}
    cloud_provider_name = sys_info.get("cloud_provider") or inventory.get("cloud_provider") or "Google Cloud Platform"
    csp_name_abbr = sys_info.get("cloud_service_provider_abbr") or "GCP"

    for svc in infra_info.get("services_enabled", []):
        category, sw_name, purpose = resolve_gcp_service(svc, custom_svcs)
        sw_records.append({
            "sw_id": sw_idx,
            "kind": "gcp_service",
            "category": category,
            "software_type": resolve_sw_type(svc),
            "software_name": sw_name,
            "vendor": cloud_provider_name,
            "xlsm_vendor": "Google Cloud Platform",
            "version": f"{csp_name_abbr} Managed Service API",
            "xlsm_version": "GCP Managed API",
            "purpose": purpose,
            "approval_status": "Pending Assessment",
        })
        sw_idx += 1

    if has_terraform_infrastructure(inventory):
        engine_v = infra_info.get("terraform_engine_version") or inventory.get("terraform_engine_version") or "1.8.0+"
        prov_vers = infra_info.get("provider_versions") or inventory.get("provider_versions") or {}
        iac_ver_str = (
            f"{engine_v} ({', '.join(f'{p} {v}' for p, v in prov_vers.items())})"
            if prov_vers
            else f"{engine_v} / Cloud Provider v5.0+"
        )
        sw_records.append({
            "sw_id": sw_idx,
            "kind": "terraform",
            "category": "Infrastructure as Code",
            "software_type": resolve_sw_type("terraform"),
            "software_name": f"HashiCorp Terraform / {csp_abbr} Provider",
            "vendor": f"HashiCorp / {cloud_provider}",
            "xlsm_vendor": f"HashiCorp / {cloud_provider}",
            "version": iac_ver_str,
            "xlsm_version": iac_ver_str,
            "purpose": "Automated declarative IaC blueprint provisioning & drift detection",
            "approval_status": "Pending Assessment",
        })
        sw_idx += 1

    seen_apps: Set[str] = set()
    for app in app_info.get("applications", []):
        app_name = app.get("name", "Application Service")
        if app_name in seen_apps:
            continue
        seen_apps.add(app_name)
        t_low = str(app.get("type", "")).lower()
        yaml_sw_t = "Web Application" if ("web" in t_low or "frontend" in t_low) else "Custom Application"
        sw_records.append({
            "sw_id": sw_idx,
            "kind": "application",
            "category": "Application Service",
            "software_type": yaml_sw_t,
            "xlsm_software_type": resolve_sw_type(app.get("framework", "app")),
            "software_name": app_name,
            "vendor": "In-House Application Development",
            "xlsm_vendor": "Internal Development",
            "version": app.get("version", "1.0.0"),
            "xlsm_version": app.get("version", "1.0.0"),
            "purpose": f"{app.get('type', 'Custom Service')} built with {app.get('language', 'Software Application')} ({app.get('file', 'Codebase')})",
            "xlsm_purpose": f"{app.get('type', 'Custom Application')} ({app.get('language')}) in {app.get('file')}",
            "approval_status": "Pending Assessment",
        })
        sw_idx += 1

    seen_c: Set[str] = set()
    for c in app_info.get("container_images", []):
        raw_c_img = str(c.get("base_image") or c.get("image") or "container-image")
        c_img, c_ver = sanitize_container_image_tag(
            clean_interpolated_string(raw_c_img, default_val="container-image"), default_img="container-image"
        )
        if c_img in seen_c:
            continue
        seen_c.add(c_img)
        c_file = c.get("file", "Dockerfile")
        sw_records.append({
            "sw_id": sw_idx,
            "kind": "container",
            "category": "Container Base Image",
            "software_type": "Container Operating System",
            "xlsm_software_type": resolve_sw_type("container_os"),
            "software_name": c_img,
            "vendor": "Container Registry",
            "xlsm_vendor": "Container Registry",
            "version": c_ver,
            "xlsm_version": c_ver,
            "purpose": f"Containerized workload runtime ({c_file})",
            "xlsm_purpose": f"Hardened Container Base Image ({c.get('file')})",
            "approval_status": "Pending Assessment",
        })
        sw_idx += 1

    seen_pkgs: Set[str] = set()
    for pkg in app_info.get("software_packages", []):
        raw_p_name = str(pkg.get("name") or pkg.get("package_name") or "unknown-package")
        raw_p_ver = str(pkg.get("version") or "Latest")
        p_name, p_ver = sanitize_software_package_identity(
            clean_interpolated_string(raw_p_name, default_val="unknown-package"),
            clean_interpolated_string(raw_p_ver, default_val="Latest"),
            default_name="unknown-package",
        )
        if not p_name or p_name in seen_pkgs:
            continue
        seen_pkgs.add(p_name)
        p_cat = pkg.get("category", "Third-Party Library")
        p_file = pkg.get("file", "Dependencies")
        sw_t = "Application Framework" if "framework" in p_cat.lower() else "3rd Party App (SRC)"
        sw_records.append({
            "sw_id": sw_idx,
            "kind": "package",
            "category": p_cat,
            "software_type": sw_t,
            "xlsm_software_type": resolve_sw_type(p_name),
            "software_name": p_name,
            "vendor": pkg.get("ecosystem", "Open Source"),
            "xlsm_vendor": pkg.get("ecosystem", "Open Source"),
            "version": p_ver,
            "xlsm_version": p_ver,
            "purpose": f"{p_cat} dependency imported in {p_file}",
            "xlsm_purpose": f"{pkg.get('category', 'Third-Party Library')} dependency imported in {pkg.get('file')}",
            "approval_status": "Pending Assessment",
        })
        sw_idx += 1
    return sw_records


def build_hwsw_inventory_records(
    inventory: Dict[str, Any],
    resolve_hw_type: Callable[[str], str],
    resolve_sw_type: Callable[[str], str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, str]:
    """Builds canonical (hardware_records, software_records, cloud_provider, csp_abbr) for YAML and XLSM."""
    sys_info = inventory.get("system_information") or {}
    net_info = inventory.get("network_architecture") or {}
    infra_info = inventory.get("infrastructure_components") or {}
    app_info = inventory.get("application_components") or {}

    sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
    location = sys_info.get("primary_location") or "[CONFIG_REQUIRED: Primary Location]"
    clean_subnets = extract_clean_subnets(net_info.get("subnets_cidrs", []))
    clean_vpcs: List[str] = []
    for v in net_info.get("vpcs", []):
        cv = clean_interpolated_string(v)
        if is_valid_resource_name(cv) and cv not in clean_vpcs:
            clean_vpcs.append(cv)

    cloud_provider = sys_info.get("cloud_provider") or inventory.get("cloud_provider") or "Google Cloud Platform (GCP)"
    csp_abbr = sys_info.get("cloud_service_provider_abbr") or "GCP"

    hw_records: List[Dict[str, Any]] = []
    hw_id = 1
    hw_records.append({
        "hw_id": hw_id,
        "component_type": resolve_hw_type("cloud_tenant"),
        "asset_name": f"{cloud_provider} Projects & Hierarchy",
        "nickname": f"{csp_abbr} Cloud Tenant ({sys_abbr})",
        "mac_address": "N/A (Cloud Virtual Asset)",
        "asset_ip_address": tenant_ip_summary(clean_subnets),
        "public_facing": "No",
        "fqdn": "N/A (Private Cloud Boundary)",
        "vlan": "N/A",
        "virtual_asset": "Yes",
        "manufacturer": cloud_provider,
        "model_number": "Infrastructure-as-a-Service (IaaS)",
        "serial_number": f"{csp_abbr}-CSP-{sys_abbr}-001",
        "os_fw_version": TENANT_OS_FW,
        "purpose_notes": "Dynamic Cloud Allocation",
        "location": location,
        "approval_status": "Pending Assessment",
        "critical_asset": "Yes",
    })
    hw_id += 1

    if clean_vpcs or clean_subnets:
        v_str = ", ".join(clean_vpcs[:4]) if clean_vpcs else f"{csp_abbr} Software Defined VPC"
        s_str = ", ".join(clean_subnets) if clean_subnets else NOT_DETERMINED
        hw_records.append({
            "hw_id": hw_id,
            "component_type": resolve_hw_type("vpc_networking"),
            "asset_name": f"{csp_abbr} Virtual Private Cloud (VPC)",
            "nickname": v_str,
            "mac_address": "Dynamic SDN MAC",
            "asset_ip_address": s_str,
            "public_facing": "No",
            "fqdn": "N/A (Private Cloud Boundary)",
            "vlan": "N/A",
            "virtual_asset": "Yes",
            "manufacturer": cloud_provider,
            "model_number": "Software-Defined VPC Networking",
            "serial_number": f"{csp_abbr}-VPC-{sys_abbr}-001",
            "os_fw_version": f"{cloud_provider} SDN",
            "omit_yaml_os_fw": True,
            "purpose_notes": "Dynamic Cloud Allocation",
            "location": location,
            "approval_status": "Pending Assessment",
            "critical_asset": "Yes",
        })
        hw_id += 1

    hw_type_gke = resolve_hw_type("gke_cluster")
    for gke in infra_info.get("gke_clusters", []):
        gke_name, gke_ip, gke_model, k8s_os = gke_cluster_fields(gke)
        hw_records.append({
            "hw_id": hw_id,
            "component_type": hw_type_gke,
            "asset_name": "Google Kubernetes Engine (GKE) Private Cluster",
            "nickname": gke_name,
            "mac_address": "Dynamic SDN MAC",
            "asset_ip_address": gke_ip,
            "public_facing": "No",
            "fqdn": "N/A (Control Plane Private Endpoint)",
            "vlan": "N/A",
            "virtual_asset": "Yes",
            "manufacturer": "Google Cloud Platform",
            "model_number": gke_model,
            "serial_number": f"{csp_abbr}-K8S-{sys_abbr}-{hw_id:03d}",
            "os_fw_version": k8s_os,
            "purpose_notes": "Standard Node Instances",
            "location": location,
            "approval_status": "Pending Assessment",
            "critical_asset": "Yes",
        })
        hw_id += 1

    db_records, hw_id = _build_db_hardware_records(
        infra_info, resolve_hw_type, clean_subnets, csp_abbr, sys_abbr, location, hw_id
    )
    hw_records.extend(db_records)
    hw_records.extend(
        _build_kms_and_vm_hardware_records(infra_info, resolve_hw_type, clean_subnets, csp_abbr, sys_abbr, location, hw_id)
    )

    sw_records = _build_software_records(
        inventory, sys_info, infra_info, app_info, resolve_sw_type, cloud_provider, csp_abbr
    )
    return hw_records, sw_records, cloud_provider, csp_abbr


_VPN_RESOURCE_TYPES = frozenset({
    "google_compute_vpn_tunnel",
    "google_compute_ha_vpn_gateway",
    "google_compute_vpn_gateway",
    "module_net_vpn_ha",
})


def _has_vpn_resources(net_info: Dict[str, Any], infra_info: Dict[str, Any]) -> bool:
    """Returns True when the inventory contains VPN gateway or tunnel resources."""
    if net_info.get("vpn_tunnels"):
        return True
    candidates = (
        list(infra_info.get("all_resources") or [])
        + list(net_info.get("boundary_connections") or [])
        + list(infra_info.get("boundary_connections") or [])
    )
    return any(isinstance(r, dict) and str(r.get("type", "")).strip() in _VPN_RESOURCE_TYPES for r in candidates)


def build_ppsm_records(
    inventory: Dict[str, Any],
    cloud_provider_default: str = "Google Cloud Platform (GCP)",
) -> List[Dict[str, Any]]:
    """Builds canonical PPSM rows shared between YAML and XLSM exports."""
    sys_info = inventory.get("system_information") or {}
    net_info = inventory.get("network_architecture") or {}
    infra_info = inventory.get("infrastructure_components") or {}
    app_info = inventory.get("application_components") or {}
    is_dod = is_dod_regime(sys_info)

    sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
    location = sys_info.get("primary_location") or "[CONFIG_REQUIRED: Primary Location]"
    cloud_provider = sys_info.get("cloud_provider") or inventory.get("cloud_provider") or cloud_provider_default
    csp_abbr = sys_info.get("cloud_service_provider_abbr") or "GCP"
    dest_internal_domain = f"*.{csp_abbr.lower()}.internal"
    workload_fqdn = f"*.{sys_abbr.lower()}.internal" if sys_info.get("system_abbreviation") else dest_internal_domain
    clean_subnets = extract_clean_subnets(net_info.get("subnets_cidrs", []))
    subnet_ip_str = ", ".join(clean_subnets) if clean_subnets else "Dynamic Internal IP"
    custom_svcs = inventory.get("custom_services") or {}
    cap_label = (
        "Off-Premise Cloud Service (DoD Network via DISA CAP)"
        if is_dod
        else "Cloud Service Provider Boundary"
    )
    enclave_logical_point = (
        "DoD Enclave (DoD Network)"
        if is_dod
        else "Agency Network / Authorized User Boundary"
    )
    has_vpn = _has_vpn_resources(net_info, infra_info)
    vpn_encrypted = "Yes" if has_vpn else "No"
    vpn_tunnel_type = "Cloud Layer 3 VPN" if has_vpn else "N/A"

    records: List[Dict[str, Any]] = []
    p_id = 1
    seen_services: Set[str] = set()
    for svc in infra_info.get("services_enabled", []):
        svc_clean = str(svc).lower().strip()
        if not svc_clean or svc_clean in seen_services:
            continue
        seen_services.add(svc_clean)
        category, sw_name, purpose = resolve_gcp_service(svc_clean, custom_svcs)
        records.append({
            "id": p_id,
            "type": "Least Function",
            "record_name": sw_name,
            "protocol": "HTTPS",
            "data_service": category,
            "port": "443",
            "boundary": "1. Ext to DoD GW (In)",
            "source_device_name": f"{csp_abbr} Workload Nodes / Compute Instances",
            "source_location": f"{cloud_provider} ({location})",
            "source_ip": subnet_ip_str,
            "source_fqdn": workload_fqdn,
            "logical_source_point": "Off-Premise Cloud Service (non-DoD Network)",
            "destination_device_name": f"{sw_name} API Endpoint",
            "destination_location": f"{cloud_provider} ({location})",
            "destination_ip": NOT_DETERMINED,
            "destination_fqdn": svc_clean,
            "logical_destination_point": cap_label,
            "vpn_encrypted_traffic": NOT_DETERMINED,
            "vpn_tunnel_type": NOT_DETERMINED,
            "purpose": purpose,
            "ppsm_status": "Pending Assessment",
        })
        p_id += 1

    seen_firewalls: Set[Tuple[str, str, str, str]] = set()
    for fw in net_info.get("firewall_rules", []):
        fw_name = clean_interpolated_string(fw.get("name", "fw-rule"))
        protocol = str(fw.get("protocol", "TCP")).upper()
        ports = str(fw.get("ports", "443"))
        direction = str(fw.get("direction", "INGRESS")).upper()
        dedup_key = (fw_name, protocol, ports, direction)
        if dedup_key in seen_firewalls:
            continue
        seen_firewalls.add(dedup_key)
        fw_source_ip = (
            "35.235.240.0/20 (IAP IP Range)"
            if "iap" in fw_name.lower()
            else (subnet_ip_str if clean_subnets else "Configured Source CIDR")
        )
        fw_dest_ip = subnet_ip_str if clean_subnets else "Internal Subnet IP"
        records.append({
            "id": p_id,
            "type": "Least Function",
            "record_name": f"Terraform Firewall: {fw_name}",
            "protocol": protocol,
            "data_service": "VPC Ingress/Egress Traffic Filter",
            "port": str(ports),
            "boundary": "11. Enclave GW to Enclave (In)",
            "source_device_name": "VPC Network Workload",
            "source_location": f"{cloud_provider} ({location})",
            "source_ip": fw_source_ip,
            "source_fqdn": dest_internal_domain,
            "logical_source_point": enclave_logical_point,
            "destination_device_name": "Target Instance / Service",
            "destination_location": f"{cloud_provider} ({location})",
            "destination_ip": fw_dest_ip,
            "destination_fqdn": dest_internal_domain,
            "logical_destination_point": enclave_logical_point,
            "vpn_encrypted_traffic": vpn_encrypted,
            "vpn_tunnel_type": vpn_tunnel_type,
            "purpose": f"Terraform defined {direction} rule {fw_name} allowing {protocol}:{ports}",
            "ppsm_status": "Pending Assessment",
        })
        p_id += 1

    port_list = app_info.get("exposed_ports", []) or net_info.get("application_ports", [])
    seen_ports: Set[Tuple[str, str, str]] = set()
    for app_port in port_list:
        port_num = str(app_port.get("port", "8080")).strip()
        protocol = str(app_port.get("protocol", "TCP")).upper().strip()
        svc_name = app_port.get("service_name", "Application Endpoint")
        source = app_port.get("source", "Application Ingress")
        file_src = app_port.get("file", "Application Config")
        dedup_key_p = (port_num, protocol, svc_name)
        if dedup_key_p in seen_ports:
            continue
        seen_ports.add(dedup_key_p)
        dest_fqdn = f"*.{sys_abbr.lower()}.internal" if sys_info.get("system_abbreviation") else "*.workload.internal"
        records.append({
            "id": p_id,
            "type": "Least Function",
            "record_name": svc_name,
            "protocol": protocol,
            "data_service": "Application Ingress / Container Port",
            "port": str(port_num),
            "boundary": "11. Enclave GW to Enclave (In)",
            "source_device_name": "Internal VPC Workload Client",
            "source_location": f"{cloud_provider} ({location})",
            "source_ip": subnet_ip_str if clean_subnets else "Configured Subnet CIDR",
            "source_fqdn": dest_fqdn,
            "logical_source_point": enclave_logical_point,
            "destination_device_name": svc_name,
            "destination_location": f"{cloud_provider} ({location})",
            "destination_ip": subnet_ip_str if clean_subnets else "Internal Service IP",
            "destination_fqdn": dest_fqdn,
            "logical_destination_point": enclave_logical_point,
            "vpn_encrypted_traffic": vpn_encrypted,
            "vpn_tunnel_type": vpn_tunnel_type,
            "purpose": f"Application traffic on port {port_num}/{protocol} ({source} in {file_src})",
            "ppsm_status": "Pending Assessment",
        })
        p_id += 1
    return records
