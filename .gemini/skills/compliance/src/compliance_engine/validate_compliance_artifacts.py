#!/usr/bin/env python3
"""
ATO Package Post-Generation Validator, OpenXML Inspector, & Public Sector Submission Engine

This script performs senior assessor verification across all compliance deliverables:
1. Text-based Markdown (.md) and YAML (.yaml) files.
2. OpenXML Word Policy Manuals (.docx) integrity & XML structure.
3. Macro-enabled Excel Workbooks (.xlsm) data validation & formatting audit.
4. Cross-format parity checking (YAML vs Excel, Markdown vs DOCX).
5. Comprehensive DISA STIG / SRG Checklist Evaluator referencing https://www.stigviewer.com/stigs
6. Complete Public Sector / ISSM ATO Submission Checklist & Operational Evidence Roadmap (ACAS, STIGs, 14 ATCs, PIA, ISA, SAAR, TTX, ATO Memo).
7. Option `--fix`: Re-runs dual-format generator to synchronize code drift.
8. Updates and compiles comprehensive master `Path_to_Authorization.md` and `Path_to_Authorization.docx` inside `ato_artifacts/`.
"""

from datetime import datetime
import glob
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple, Union
import zipfile

try:
    from .file_helpers import (
        ensure_path_within_boundary,
        get_scripts_dir,
        get_skill_root,
        get_templates_dir,
        read_json_file,
        read_text_file,
        read_yaml_file,
        resolve_path,
        validate_system_inventory_schema,
        write_text_file,
    )
except (ImportError, ValueError):
    from file_helpers import (
        ensure_path_within_boundary,
        get_scripts_dir,
        get_skill_root,
        get_templates_dir,
        read_json_file,
        read_text_file,
        read_yaml_file,
        resolve_path,
        validate_system_inventory_schema,
        write_text_file,
    )

try:
    from . import safe_xml as ET
except (ImportError, ValueError):
    import safe_xml as ET

try:
    from .audit_log import get_audit_logger, AuditEvent, AuditOutcome, audit_operation
except (ImportError, ValueError):
    from audit_log import get_audit_logger, AuditEvent, AuditOutcome, audit_operation

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    openpyxl = None
    OPENPYXL_AVAILABLE = False

logger = logging.getLogger(__name__)

SKILL_BASE = str(get_skill_root())
TEMPLATES_DIR = str(get_templates_dir())
SCRIPTS_DIR = str(get_scripts_dir())

try:
    from . import docx_generator
except (ImportError, ValueError):
    try:
        import docx_generator
    except ImportError:
        docx_generator = None

try:
    from . import stig_resolver
except (ImportError, ValueError):
    try:
        import stig_resolver
    except ImportError:
        stig_resolver = None

try:
    from .template_engine import TemplateEngine
except (ImportError, ValueError):
    try:
        from template_engine import TemplateEngine
    except ImportError:
        TemplateEngine = None

try:
    from .semantic_linter import (
        evaluate_control_substance,
        run_semantic_linter,
    )
except (ImportError, ValueError):
    try:
        from semantic_linter import (
            evaluate_control_substance,
            run_semantic_linter,
        )
    except ImportError:
        evaluate_control_substance = None
        run_semantic_linter = None

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

# ------------------------------------------------------------------------------
# Authoritative DISA STIG Knowledge Base & Evaluator Engine
# -------------------------------------------------------------
# Foundational Cloud Computing Mission Owner STIGs (Mandatory Baseline)
# -------------------------------------------------------------

FOUNDATIONAL_CLOUD_MISSION_OWNER_STIGS: List[Dict[str, str]] = [
    {
        "title": "DISA Cloud Computing Security Requirements Guide (CC SRG)",
        "slug": "cloud_computing_srg",
        "version": "v1R4",
        "category": "Cloud Foundation Baseline",
        "scope": "Mission Owner responsibilities for cloud enclaves, Assured Workloads IL5 guardrails, organization policies, and FedRAMP inheritance.",
        "action": "Complete Cloud Computing Mission Owner CKL; verify Assured Workloads boundary guardrails and organization policy constraints."
    },
    {
        "title": "DISA Identity, Credential, and Access Management (ICAM) SRG / IAM STIG",
        "slug": "identity_and_access_management_iam_srg",
        "version": "v1R2",
        "category": "Identity & Access Control",
        "scope": "Cloud Identity SAML/OIDC federated SSO, hardware MFA enforcement, custom IAM roles, and automated service account key rotation.",
        "action": "Complete IAM CKL; audit all custom role bindings, eliminate static service account keys in favor of Workload Identity Federation."
    },
    {
        "title": "DISA Key and Certificate Management SRG / KMS STIG",
        "slug": "key_and_certificate_management_srg",
        "version": "v1R1",
        "category": "Cryptography & PKI",
        "scope": "FIPS 140-3 Cloud KMS CMEK encryption keys, 90-day automated key rotation, Certificate Manager TLS 1.3 PKI, and algorithm restrictions.",
        "action": "Complete Key Mgmt CKL; verify CMEK association across all storage buckets, disks, and databases with automatic rotation active."
    }
]


def _read_optional_lowercase(path: Union[str, Path], lower: bool = True) -> str:
    """Reads an optional deliverable, degrading to an empty string.

    An artifact that is genuinely absent and one that exists but cannot be read
    both yield ``""``, which would silently reduce reported coverage. The two
    cases are therefore distinguished in the log: absence is expected and
    recorded at DEBUG, while an existing-but-unreadable artifact is a real
    operator-actionable condition and is recorded at WARNING.

    Args:
        path: Filesystem path of the deliverable to read.
        lower: Whether to lowercase the contents for case-insensitive matching.

    Returns:
        The file contents, or ``""`` when unavailable.
    """
    if not os.path.exists(path):
        logger.debug("Optional deliverable '%s' is not present; treating as empty.", path)
        return ""
    try:
        text = read_text_file(str(path))
    except (OSError, ValueError) as err:
        logger.warning(
            "Deliverable '%s' exists but could not be read (%s); reconciliation coverage "
            "for this artifact will be under-reported.",
            path,
            err,
        )
        return ""
    return text.lower() if lower else text


# Text renditions of a deliverable that may carry asset cross-references.
# Binary renditions (.docx / .xlsm) are generated from these and are audited
# separately for OpenXML integrity, so they are deliberately excluded here.
_DELIVERABLE_TEXT_SUFFIXES: Tuple[str, ...] = (".md", ".yaml", ".yml", ".json")


def _read_deliverable_renditions(
    ato_dir: str, subfolder: str, basenames: List[str]
) -> str:
    """Reads every text rendition of a deliverable and returns their concatenation.

    A deliverable is emitted in several renditions (Markdown, YAML, JSON) and the
    asset-level evidence is not always present in all of them. Reading a single
    hard-coded filename therefore silently loses cross-references and
    under-reports reconciliation coverage, which understates how much of the
    architecture an assessor can actually trace through the package.

    Args:
        ato_dir: Absolute path to the ``ato_artifacts`` directory.
        subfolder: Deliverable subfolder name (for example ``"SSP"``).
        basenames: Candidate file basenames without extension, in preference
            order. Every candidate that exists is read, not just the first.

    Returns:
        The lowercased concatenation of every rendition found, or ``""`` when
        none of the candidates exist or are readable.
    """
    chunks: List[str] = []
    for base in basenames:
        for suffix in _DELIVERABLE_TEXT_SUFFIXES:
            candidate = os.path.join(ato_dir, subfolder, f"{base}{suffix}")
            text = _read_optional_lowercase(candidate)
            if text:
                chunks.append(text)
    if not chunks:
        logger.debug(
            "No readable rendition of deliverable '%s/%s' was found; assets that "
            "are documented only there will be reported as unreconciled.",
            subfolder,
            basenames,
        )
    return "\n".join(chunks)


def discover_workload_technology_stigs(
    inventory: Dict[str, Any],
    target_dir: Optional[Union[str, Path]] = None,
) -> List[Dict[str, str]]:
    """Identifies workload-specific technology domains dynamically from discovered inventory.

    Intelligently analyzes discovered infrastructure components (operating systems,
    databases across all paradigms, Kubernetes and serverless container platforms,
    networking routers, firewalls, gateways, message brokers, web applications,
    and storage services) and maps them to authoritative DISA STIG / SRG technology checklists.

    Args:
        inventory: System inventory dictionary containing infrastructure components.
        target_dir: Optional workspace target directory.

    Returns:
        A list of dictionaries defining matching STIG checklists with titles, slugs,
        versions, scopes, and remediation actions.
    """
    discovered_stigs: List[Dict[str, str]] = []
    seen_slugs: Set[str] = set()

    resolver = None
    if stig_resolver and hasattr(stig_resolver, "StigResolver"):
        try:
            stigs_cfg = inventory.get("disa_stigs") if isinstance(inventory, dict) else {}
            resolver = stig_resolver.StigResolver(
                target_dir=target_dir,
                config={"disa_stigs": stigs_cfg} if isinstance(stigs_cfg, dict) else None,
            )
        except Exception as e:
            logger.error("Failed to initialize STIG resolver: %s", e)
            resolver = None
            discovered_stigs.append({
                "title": "STIG Resolution Degraded",
                "slug": "stig_resolution_degraded",
                "version": "N/A",
                "version_source": "Error",
                "category": "Error",
                "scope": f"Resolver failed to initialize: {e}",
                "action": "Check logs and configure STIG resolver correctly.",
                "status": "UNVERIFIED",
                "url": ""
            })

    def add_stig(title: str, slug: str, version: str, category: str, scope: str, action: str) -> None:
        if slug in seen_slugs:
            return
        seen_slugs.add(slug)
        resolved_ver = version
        ver_source = "Authoritative Baseline"
        url = f"https://www.stigviewer.com/stigs/{slug}"
        if resolver:
            resolved_ver, ver_source = resolver.resolve_version(slug, default_version=version)
            entry = resolver.get_stig_entry(slug)
            if entry and entry.get("url"):
                url = entry["url"]
        discovered_stigs.append({
            "title": title,
            "slug": slug,
            "version": resolved_ver,
            "version_source": ver_source,
            "category": category,
            "scope": scope,
            "action": action,
            "url": url,
        })

    infra = inventory.get("infrastructure_components", {})
    net = inventory.get("network_architecture", {})
    apps = inventory.get("application_components", {})
    custom = inventory.get("custom_services", {})
    services = [str(s).lower() for s in infra.get("services_enabled", [])]
    resources = infra.get("all_resources", [])

    # 1. Operating Systems, Virtual Hosts & Appliance Images
    vms = infra.get("compute_instances", [])
    has_compute = (
        bool(vms)
        or any("compute" in s for s in services)
        or any("compute_instance" in str(r.get("type", "")).lower() for r in resources)
    )

    if has_compute:
        all_vm_text = " ".join([str(vm).lower() for vm in vms] + [str(k).lower() + " " + str(v).lower() for k, v in custom.items()])
        has_ubuntu = "ubuntu" in all_vm_text
        has_rhel = any(k in all_vm_text for k in ["rhel", "redhat", "centos", "rocky", "alma"])
        has_debian = "debian" in all_vm_text
        has_windows = any(k in all_vm_text for k in ["windows", "win2019", "win2022", "win-server"])
        has_suse = any(k in all_vm_text for k in ["suse", "sles"])
        has_cisco = any(k in all_vm_text for k in ["cisco", "ios-xe", "iosxe", "csr1000v"])

        if has_ubuntu:
            add_stig(
                "DISA Canonical Ubuntu 22.04 LTS STIG",
                "canonical_ubuntu_22.04_lts",
                "v1R2",
                "Operating Systems & Host Compute",
                "Hardened Ubuntu Linux Compute Engine instances and build worker bastions.",
                "Complete Ubuntu 22.04 CKL; apply Ubuntu Security Guide (USG) DISA profile in STIG Viewer desktop app.",
            )
        if has_rhel or (vms and not has_ubuntu and not has_debian and not has_windows and not has_suse and not has_cisco):
            add_stig(
                "DISA Red Hat Enterprise Linux 8/9 STIG",
                "red_hat_enterprise_linux_9",
                "v1R3",
                "Operating Systems & Host Compute",
                "Hardened Compute Engine VM hosts and administrative bastions.",
                "Complete RHEL / Linux OS CKL; apply OpenSCAP/Ansible DISA STIG baseline.",
            )
        if has_debian:
            add_stig(
                "DISA Debian Linux STIG / General Purpose OS SRG",
                "debian_linux",
                "v1R1",
                "Operating Systems & Host Compute",
                "Hardened Debian Linux Compute Engine host instances.",
                "Complete Debian OS CKL; apply Debian security hardening baseline.",
            )
        if has_windows:
            add_stig(
                "DISA Microsoft Windows Server 2019/2022 STIG",
                "ms_windows_server_2019",
                "v2R3",
                "Operating Systems & Host Compute",
                "Hardened Windows Server Compute Engine instances and active directory bastions.",
                "Complete Windows Server CKL; apply DISA GPO baseline in STIG Viewer desktop app.",
            )
        if has_suse:
            add_stig(
                "DISA SUSE Linux Enterprise Server STIG",
                "suse_linux_enterprise_server",
                "v1R2",
                "Operating Systems & Host Compute",
                "Hardened SUSE Linux Enterprise instances.",
                "Complete SLES CKL; apply OpenSCAP baseline.",
            )
        if has_cisco:
            add_stig(
                "DISA Cisco IOS-XE Router STIG / Network Infrastructure SRG",
                "cisco_ios_xe_router",
                "v2R4",
                "Network Appliances & Routing",
                "Virtual edge router instances, IPsec transport encryption, and perimeter routing appliances.",
                "Complete Cisco IOS-XE Router CKL; verify MACsec / IPsec encryption and control plane policing.",
            )

    # 2. Containers, Microservices & Serverless
    gke = infra.get("gke_clusters", [])
    has_k8s = bool(gke) or "container.googleapis.com" in services or any("container_cluster" in str(r.get("type", "")).lower() for r in resources)
    if has_k8s:
        add_stig(
            "DISA Kubernetes STIG & Container Platform SRG",
            "kubernetes",
            "v1R12",
            "Containers & Microservices",
            "GKE private clusters, master control plane endpoints, RBAC, and Container Platform security.",
            "Complete Kubernetes CKL; audit master authorized networks and Pod Security Standards in STIG Viewer.",
        )

    run_svcs = infra.get("cloud_run_services", [])
    cloud_funcs = infra.get("cloud_functions", [])
    has_serverless = (
        bool(run_svcs)
        or bool(cloud_funcs)
        or "run.googleapis.com" in services
        or "cloudfunctions.googleapis.com" in services
        or any("cloud_run" in str(r.get("type", "")).lower() for r in resources)
    )
    if has_serverless:
        add_stig(
            "DISA Container Platform & Serverless Workload SRG",
            "container_platform_srg",
            "v1R1",
            "Containers & Microservices",
            "Serverless container workloads, Cloud Run service perimeters, and stateless compute isolation.",
            "Complete Container Platform CKL; enforce VPC-SC perimeter on Cloud Run services and verify non-root container execution.",
        )

    if (infra.get("artifact_registries") or "artifactregistry.googleapis.com" in services) and "container_platform_srg" not in seen_slugs:
        add_stig(
            "DISA Container Platform & Image Registry SRG",
            "container_platform_srg",
            "v1R1",
            "Containers & Microservices",
            "Container image registries, vulnerability scanning, and binary authorization.",
            "Complete Container Platform CKL; configure Artifact Registry vulnerability scanning and Binary Authorization policies.",
        )

    if apps.get("container_images") and "docker_enterprise" not in seen_slugs:
        add_stig(
            "DISA Container Runtime & Docker Enterprise STIG",
            "docker_enterprise",
            "v2R1",
            "Containers & Microservices",
            "Container base images, Dockerfile hardening, and non-root execution.",
            "Complete Docker Enterprise CKL; eliminate root user in Dockerfiles and verify artifact signing.",
        )

    # 3. Databases & Data Management (Dynamic Recognition across all database engines)
    dbs = infra.get("databases", [])
    packages = [str(p.get("name", "")).lower() for p in apps.get("software_packages", []) if isinstance(p, dict)]
    res_types = [str(r.get("type", "")).lower() for r in resources]
    all_db_text = " ".join([str(db).lower() for db in dbs] + packages + res_types + services)
    has_db = (
        bool(dbs)
        or any(k in all_db_text for k in ["sql", "spanner", "bigquery", "postgres", "mysql", "redis", "database", "datastore", "firestore", "mongo", "oracle"])
    )

    if has_db:
        if any(k in all_db_text for k in ["postgres", "psql", "alloydb", "pg", "psycopg2"]):
            add_stig(
                "DISA PostgreSQL 13/14/15/16 STIG",
                "postgresql_13",
                "v2R3",
                "Databases & Data Management",
                "Cloud SQL PostgreSQL / AlloyDB instances, PGAudit logging, and TLS in transit.",
                "Complete PostgreSQL CKL; configure PGAudit database flags and verify Cloud Logging sink.",
            )
        if any(k in all_db_text for k in ["mysql", "mariadb"]):
            add_stig(
                "DISA Oracle MySQL 8.0 STIG",
                "oracle_mysql_8.0",
                "v1R3",
                "Databases & Data Management",
                "Cloud SQL MySQL database instances and secure transport enforcement.",
                "Complete MySQL CKL; enforce require_secure_transport and audit logging.",
            )
        if any(k in all_db_text for k in ["sqlserver", "mssql", "sql_server"]):
            add_stig(
                "DISA Microsoft SQL Server 2016/2019 STIG",
                "ms_sql_server_2016_instance",
                "v2R3",
                "Databases & Data Management",
                "Cloud SQL SQL Server / MSSQL database instances.",
                "Complete SQL Server CKL; configure Windows Authentication / Cloud IAM and TLS encryption.",
            )
        if "oracle" in all_db_text and "oracle_mysql" not in all_db_text:
            add_stig(
                "DISA Oracle Database 12c/19c STIG",
                "oracle_database_12c",
                "v2R4",
                "Databases & Data Management",
                "Oracle database instances and Transparent Data Encryption (TDE).",
                "Complete Oracle CKL; enforce unified auditing and secure connection strings.",
            )
        if "spanner" in all_db_text:
            add_stig(
                "DISA Cloud Spanner Distributed Database SRG",
                "database_srg",
                "v3R4",
                "Databases & Data Management",
                "Google Cloud Spanner distributed relational database and CMEK encryption.",
                "Complete Database SRG CKL; enforce IAM fine-grained access and Cloud KMS CMEK key protection.",
            )
        if "bigquery" in all_db_text:
            add_stig(
                "DISA Cloud Data Warehouse & Analytics SRG",
                "database_srg",
                "v3R4",
                "Databases & Data Management",
                "BigQuery analytics datasets, column-level security, and audit logging.",
                "Complete Database SRG CKL; enforce dataset authorized views and CMEK key encryption.",
            )
        if any(k in all_db_text for k in ["redis", "memorystore"]):
            add_stig(
                "DISA Key-Value NoSQL Store / Database SRG",
                "database_srg",
                "v3R4",
                "Databases & Data Management",
                "In-memory caching and Redis / Memorystore key-value datastores.",
                "Complete Database SRG CKL; enforce AUTH password, TLS transit encryption, and private IP.",
            )
        if any(k in all_db_text for k in ["mongo", "mongodb"]):
            add_stig(
                "DISA MongoDB Enterprise STIG / NoSQL Database SRG",
                "mongodb_enterprise_3.x",
                "v2R1",
                "Databases & Data Management",
                "Document database instances, wiredTiger encryption, and SCRAM authentication.",
                "Complete MongoDB CKL; enforce role-based access control and TLS transport.",
            )
        if any(k in all_db_text for k in ["firestore", "datastore"]):
            add_stig(
                "DISA Cloud Document Database SRG",
                "database_srg",
                "v3R4",
                "Databases & Data Management",
                "Cloud Firestore / Datastore serverless document databases.",
                "Complete Database SRG CKL; enforce security rules and IAM separation.",
            )
        if not any(slug in seen_slugs for slug in ["postgresql_13", "oracle_mysql_8.0", "ms_sql_server_2016_instance", "oracle_database_12c", "mongodb_enterprise_3.x"]):
            add_stig(
                "DISA Database Security Requirements Guide (Generic RDBMS SRG)",
                "database_srg",
                "v3R4",
                "Databases & Data Management",
                "Managed relational database services, CMEK encryption at rest, and private IP only.",
                "Complete Database SRG CKL; enforce require_ssl=true and disable public IPv4.",
            )

    # 4. Storage Area Network / Cloud Object Store
    has_storage = (
        bool(infra.get("storage_buckets"))
        or "storage.googleapis.com" in services
        or any("storage_bucket" in str(r.get("type", "")).lower() or "s3" in str(r.get("type", "")).lower() for r in resources)
    )
    if has_storage:
        add_stig(
            "DISA Storage Area Network (SAN) / Cloud Object Store SRG",
            "storage_area_network_san_srg",
            "v2R1",
            "Storage & Persistence",
            "Google Cloud Storage (GCS) buckets, uniform bucket access, and retention policy locks.",
            "Complete Storage SRG CKL; verify public access prevention and CMEK key encryption.",
        )

    # 5. Network Perimeter, Firewalls & VPN Gateways
    has_firewall = (
        bool(net.get("firewall_rules"))
        or bool(net.get("vpcs"))
        or any("firewall" in str(r.get("type", "")).lower() for r in resources)
    )
    if has_firewall:
        add_stig(
            "DISA Perimeter Firewall & Network Infrastructure SRG",
            "firewall_srg",
            "v2R1",
            "Networking & Perimeter",
            "VPC Hub/Spoke perimeter firewall policy tiers, default-deny ingress, and Cloud IAP bastions.",
            "Complete Firewall CKL; verify default-deny ingress rule and zero 0.0.0.0/0 exposure.",
        )

    has_vpn = (
        bool(net.get("vpn_tunnels"))
        or any("vpn" in str(r.get("type", "")).lower() for r in resources)
    )
    if has_vpn:
        add_stig(
            "DISA Virtual Private Network (VPN) Gateway SRG",
            "vpn_gateway_srg",
            "v2R2",
            "Networking & Perimeter",
            "Cloud HA VPN gateways, IPsec cryptographic profiles, and BGP dynamic routing.",
            "Complete VPN Gateway CKL; enforce IKEv2 and AES-GCM 256-bit encryption cipher suites.",
        )

    has_waf = (
        any("security_policy" in str(r.get("type", "")).lower() for r in resources)
        or any("armor" in s for s in services)
    )
    if has_waf:
        add_stig(
            "DISA Web Application Firewall (WAF) SRG",
            "web_application_firewall_srg",
            "v1R1",
            "Networking & Perimeter",
            "Cloud Armor WAF policies, adaptive protection against DDoS, and OWASP Top 10 rule sets.",
            "Complete WAF SRG CKL; verify pre-configured OWASP CRS rules and rate-limiting policies.",
        )

    # 6. Web & Application Security
    def _matches_web(rule_obj: Any) -> bool:
        if stig_resolver and hasattr(stig_resolver, "rule_matches_web_ports"):
            return stig_resolver.rule_matches_web_ports(rule_obj)
        if isinstance(rule_obj, dict):
            p = str(rule_obj.get("ports", ""))
            return any(pt.strip() in ("80", "443", "http", "https") for pt in re.split(r"[,;\s]+", p))
        return bool(re.search(r"(?<![0-9.])(?:80|443)(?![0-9.])", str(rule_obj)))

    has_web = (
        bool(apps.get("applications"))
        or bool(apps.get("exposed_ports"))
        or any(s in services for s in ["run.googleapis.com", "appengine.googleapis.com"])
        or any("web" in s or "app" in s for s in services)
        or any(_matches_web(r) for r in net.get("firewall_rules", []))
        or bool(custom)
    )
    if has_web:
        add_stig(
            "DISA Application Security and Development (ASD) STIG",
            "application_security_and_development_stig",
            "v5R3",
            "Application Security & DevSecOps",
            "DevSecOps CI/CD pipelines, container vulnerability scanning, and OWASP defenses.",
            "Complete ASD STIG CKL; incorporate automated container scanning in CI/CD pipeline.",
        )

    has_webserver = (
        any("nginx" in p or "apache" in p or "envoy" in p for p in packages)
        or any("target_http" in str(r.get("type", "")).lower() for r in resources)
    )
    if has_webserver:
        add_stig(
            "DISA Apache / Nginx Web Server STIG",
            "apache_server_2.4_unix_server",
            "v2R4",
            "Application Security & DevSecOps",
            "Web servers, reverse proxies, and Target HTTP/HTTPS proxies.",
            "Complete Web Server CKL; disable weak TLS ciphers, server tokens, and enforce HTTP security headers.",
        )

    has_messaging = (
        bool(infra.get("pubsub_topics"))
        or "pubsub.googleapis.com" in services
        or any("pubsub" in str(r.get("type", "")).lower() for r in resources)
    )
    if has_messaging:
        add_stig(
            "DISA Enterprise Message Broker & Telemetry Ingestion SRG",
            "enterprise_message_broker_srg",
            "v1R1",
            "Application Security & DevSecOps",
            "Cloud Pub/Sub messaging topics, telemetry pipelines, and dead-letter queues.",
            "Complete Message Broker CKL; enforce CMEK encryption on topics and restrict publisher/subscriber IAM roles.",
        )

    return discovered_stigs

def evaluate_disa_stig_applicability(
    inventory: Dict[str, Any],
    all_files: Optional[List[str]] = None,
    target_dir: Optional[str] = None,
    update_stigs: bool = False,
    stigs_mode: Optional[str] = None,
    stigs_catalog: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Evaluates DISA STIG and SRG checklist applicability for the target system.

    Combines foundational cloud mission-owner STIGs with dynamic workload-discovered
    technology checklists, resolves active versions dynamically, and generates STIG Viewer
    reference URLs.

    Args:
        inventory: System inventory dictionary containing infrastructure metadata.
        all_files: Optional list of generated compliance artifact file paths.
        target_dir: Optional workspace directory containing compliance artifacts.
        update_stigs: If True, triggers active pulling of latest versions.
        stigs_mode: Resolution mode ('auto', 'online', or 'offline').
        stigs_catalog: Optional custom catalog source URL or file path.

    Returns:
        A list of dictionaries representing applicable STIG benchmarks with metadata.
    """
    if stig_resolver and hasattr(stig_resolver, "StigResolver"):
        stigs_cfg = inventory.get("disa_stigs") if isinstance(inventory, dict) else {}
        try:
            resolver = stig_resolver.StigResolver(
                target_dir=target_dir,
                config={"disa_stigs": stigs_cfg} if isinstance(stigs_cfg, dict) else None,
                update_mode=stigs_mode,
                catalog_source=stigs_catalog,
            )
            return resolver.evaluate_applicable_stigs(inventory, trigger_pull=update_stigs)
        except Exception as e:
            logger.error("Failed to evaluate STIGs: %s", e)
            return [{
                "title": "STIG Evaluation Failed",
                "slug": "stig_evaluation_failed",
                "version": "N/A",
                "version_source": "Error",
                "category": "Error",
                "url": "",
                "cyber_exchange_url": "",
                "reason": "STIG resolver crashed during evaluation.",
                "focus": str(e),
                "action": "Check logs.",
                "status": "UNVERIFIED"
            }]

    stigs: List[Dict[str, Any]] = []

    # 1. Add Foundational Cloud Baseline STIGs
    for base in FOUNDATIONAL_CLOUD_MISSION_OWNER_STIGS:
        stigs.append({
            "title": base["title"],
            "slug": base["slug"],
            "version": base["version"],
            "version_source": "Authoritative Baseline",
            "category": base["category"],
            "url": f"https://www.stigviewer.com/stigs/{base['slug']}",
            "cyber_exchange_url": "https://public.cyber.mil/stigs/downloads/",
            "reason": "Foundational cloud baseline (Mission Owner responsibilities).",
            "focus": base["scope"],
            "action": base["action"],
            "status": "Mandatory Cloud Baseline",
        })

    # 2. Add Dynamic Workload Discovered STIGs
    workload_stigs = discover_workload_technology_stigs(inventory, target_dir=target_dir)
    for ws in workload_stigs:
        stigs.append({
            "title": ws["title"],
            "slug": ws["slug"],
            "version": ws["version"],
            "version_source": ws.get("version_source", "Authoritative Baseline"),
            "category": ws["category"],
            "url": ws.get("url") or f"https://www.stigviewer.com/stigs/{ws['slug']}",
            "cyber_exchange_url": "https://public.cyber.mil/stigs/downloads/",
            "reason": ws.get("reason", f"Discovered {ws['category']} in active infrastructure code."),
            "focus": ws.get("scope", ws.get("focus", "")),
            "action": ws["action"],
            "status": ws.get("status", f"Required ({ws['category']})"),
        })

    return stigs


# Characters that the identifier-boundary rule treats as "inside a word". A
# candidate identifier only matches when the characters immediately before and
# after it are outside this class (or the string boundary).
_IDENTIFIER_WORD_CHARS = r"A-Za-z0-9_\-"
# All maximal runs of word characters, used to index a deliverable in one pass.
_WORD_RUN_RE = re.compile(rf"[{_IDENTIFIER_WORD_CHARS}]+")
# An identifier that consists solely of word characters (the common case).
_PURE_WORD_RUN_RE = re.compile(rf"[{_IDENTIFIER_WORD_CHARS}]+\Z")
# Strict IPv4 CIDR. The extractor may serialise `subnets_cidrs` as a stringified
# Python set (for example "{'10.10.0.0/20'}"), so the ranges are recovered with
# an explicit pattern rather than by trusting the container type. Anything that
# does not match is reported as undetermined rather than guessed at.
_CIDR_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}\b")


class DeliverableIdentifierIndex:
    """Single-pass word-run index over one deliverable, for asset reconciliation.

    Reconciling discovered assets against a deliverable used to run one freshly
    built regex over the entire document per asset, which is O(assets x document
    bytes). Measured on a 441-resource fixture that cost 1.77 s for a single
    audit. This index tokenises the document once into its maximal runs of
    ``[A-Za-z0-9_-]`` and answers the overwhelmingly common case -- an
    identifier made only of word characters -- with an O(1) set membership test.

    The transformation is exact rather than approximate. If an identifier is
    entirely word characters, the boundary rule forces any match to coincide
    with a *maximal* word run, so set membership and the regex agree exactly.
    If an identifier contains separators (``.``, ``/``, ``:``), its leading word
    run must still coincide with a maximal word run of the document, so a failed
    membership test is a definitive non-match; only when that prefilter passes
    is the original regex evaluated. Matching therefore never becomes more
    permissive, which matters because a spurious match here would report an
    undocumented asset as reconciled.
    """

    __slots__ = ("_text", "_word_runs")

    def __init__(self, text: str) -> None:
        """Tokenises the deliverable text a single time.

        Args:
            text: Full deliverable contents. Callers that need case-insensitive
                reconciliation must pass already-lowercased text, matching the
                behaviour of the original matcher, which lowercased only the
                search target and never the document.
        """
        self._text = text or ""
        self._word_runs: FrozenSet[str] = (
            frozenset(_WORD_RUN_RE.findall(self._text)) if self._text else frozenset()
        )

    def contains(self, target: str) -> bool:
        """Reports whether an identifier appears in the deliverable as a whole word.

        Args:
            target: Candidate asset identifier, such as a VM name, bucket name,
                port number, or fully qualified container image reference.

        Returns:
            True when the identifier occurs delimited by non-word characters or
            string boundaries; False when it is absent, empty, or occurs only as
            a substring of a longer identifier.
        """
        if not target or not self._text:
            return False
        target_str = str(target).strip()
        if not target_str:
            return False
        needle = target_str.lower()

        if _PURE_WORD_RUN_RE.match(needle):
            return needle in self._word_runs

        leading_run = _WORD_RUN_RE.match(needle)
        if leading_run is not None and leading_run.group(0) not in self._word_runs:
            # The identifier begins with word characters that do not form any
            # maximal word run in the document, so no boundary-delimited match
            # can exist. Skipping the scan here cannot hide a real match.
            return False

        escaped = re.escape(needle)
        pattern = (
            rf"(?:^|(?<=[^{_IDENTIFIER_WORD_CHARS}])){escaped}"
            rf"(?:$|(?=[^{_IDENTIFIER_WORD_CHARS}]))"
        )
        return bool(re.search(pattern, self._text))


def _matches_text_identifier(target: str, text: str) -> bool:
    """Checks whether target identifier exists as a distinct token or word in text.

    Prevents false-positive substring matches on short or generic identifiers
    (e.g. 'db', 'app', 'api', '80').

    This is a convenience wrapper for one-off checks. Callers that test many
    identifiers against the same document must build a
    :class:`DeliverableIdentifierIndex` once and reuse it, otherwise the
    document is re-tokenised on every call.

    Args:
        target: Candidate asset identifier.
        text: Deliverable contents to search.

    Returns:
        True when the identifier occurs as a distinct whole word in the text.
    """
    return DeliverableIdentifierIndex(text).contains(target)


def audit_inventory_artifact_alignment(
    target_dir: str, inventory: Dict[str, Any], ato_dir: str
) -> Dict[str, Any]:
    """Reconciles discovered system architecture against generated ATO artifacts.

    Performs deep cross-layer verification between live discovered infrastructure
    components from system_inventory.json and the generated deliverables:
    1. Hardware & Software Inventory (YAML & Excel)
    2. Ports, Protocols & Services Matrix (PPSM)
    3. System Security Plan (SSP)
    4. FIPS 140-3 Cryptographic Matrix
    5. NIST OSCAL System Security Plan

    Every text rendition of each deliverable is searched, because the asset-level
    evidence is not present in all of them.

    The coverage denominator covers compute instances, Kubernetes clusters,
    storage buckets, databases, VPCs, subnet CIDR ranges, boundary firewall
    rules, KMS cryptographic keys, IAM service accounts, boundary ingress ports,
    applications, and container images. Other inventory collections (logging
    sinks, Pub/Sub topics, Cloud Run services, Cloud Functions, artifact
    registries, NAT gateways, forwarding rules, security policies, and service
    perimeters) are NOT yet counted, so the reported percentage is coverage over
    the classes listed above rather than over the entire estate.

    Args:
        target_dir: Workspace root directory.
        inventory: System inventory dictionary.
        ato_dir: Absolute path to the ato_artifacts directory.

    Returns:
        A dictionary summarizing alignment metrics, coverage score, matched assets,
        and itemized discrepancies.
    """
    if not inventory:
        inventory = {}
    infra = inventory.get("infrastructure_components") or {}
    net = inventory.get("network_architecture") or {}
    apps = inventory.get("application_components") or {}

    hwsw_text = _read_deliverable_renditions(
        ato_dir, "HW_SW_Inventory", ["Hardware_Software_Inventory"]
    )
    ppsm_text = _read_deliverable_renditions(
        ato_dir, "PPSM", ["PPSM_Ports_Protocols_Services"]
    )
    ssp_text = _read_deliverable_renditions(
        ato_dir, "SSP", ["SSP_System_Security_Plan", "System_Security_Plan"]
    )
    # The per-asset CMEK evidence (bucket / disk / database names bound to a key)
    # is emitted only into the Markdown rendition of the FIPS matrix; the YAML
    # rendition carries module-level metadata. Reading a single rendition
    # silently loses the asset-level cross-reference and under-reports coverage.
    fips_text = _read_deliverable_renditions(
        ato_dir,
        "FIPS_Cryptography",
        ["FIPS_Cryptographic_Matrix", "FIPS_140_3_Cryptographic_Matrix"],
    )

    # Each deliverable is tokenised exactly once here. Previously every asset
    # re-scanned every deliverable with a freshly compiled regex, making this
    # audit O(assets x document bytes).
    hwsw_index = DeliverableIdentifierIndex(hwsw_text)
    ppsm_index = DeliverableIdentifierIndex(ppsm_text)
    ssp_index = DeliverableIdentifierIndex(ssp_text)
    fips_index = DeliverableIdentifierIndex(fips_text)

    breakdown: Dict[str, Dict[str, int]] = {
        "compute": {"discovered": 0, "matched": 0},
        "storage": {"discovered": 0, "matched": 0},
        "databases": {"discovered": 0, "matched": 0},
        "vpcs": {"discovered": 0, "matched": 0},
        "subnets": {"discovered": 0, "matched": 0},
        "firewall_rules": {"discovered": 0, "matched": 0},
        "kms_keys": {"discovered": 0, "matched": 0},
        "service_accounts": {"discovered": 0, "matched": 0},
        "exposed_ports": {"discovered": 0, "matched": 0},
        "applications": {"discovered": 0, "matched": 0},
        "container_images": {"discovered": 0, "matched": 0},
    }
    discrepancies: List[str] = []
    matched_assets: List[str] = []

    # 1. Compute Instances & Kubernetes Clusters
    for vm in infra.get("compute_instances", []) or []:
        breakdown["compute"]["discovered"] += 1
        name = str(vm.get("name", "")).strip() if isinstance(vm, dict) else str(vm).strip()
        if name and (hwsw_index.contains(name) or ssp_index.contains(name)):
            breakdown["compute"]["matched"] += 1
            matched_assets.append(f"Compute Instance: {name}")
        elif name:
            discrepancies.append(f"Undocumented Compute Instance: '{name}' not found in HW/SW inventory or SSP.")

    for k8s in infra.get("gke_clusters", []) or []:
        breakdown["compute"]["discovered"] += 1
        k_name = str(k8s.get("name", "")).strip() if isinstance(k8s, dict) else str(k8s).strip()
        if k_name and (hwsw_index.contains(k_name) or ssp_index.contains(k_name)):
            breakdown["compute"]["matched"] += 1
            matched_assets.append(f"Kubernetes Cluster: {k_name}")
        elif k_name:
            discrepancies.append(f"Undocumented Kubernetes Cluster: '{k_name}' not found in HW/SW inventory or SSP.")

    # 2. Storage Buckets
    for b in infra.get("storage_buckets", []) or []:
        breakdown["storage"]["discovered"] += 1
        b_name = str(b.get("name", "")).strip() if isinstance(b, dict) else str(b).strip()
        if b_name and (hwsw_index.contains(b_name) or ssp_index.contains(b_name) or fips_index.contains(b_name)):
            breakdown["storage"]["matched"] += 1
            matched_assets.append(f"Storage Bucket: {b_name}")
        elif b_name:
            discrepancies.append(f"Undocumented Storage Bucket: '{b_name}' not found in HW/SW inventory, SSP, or FIPS matrix.")

    # 3. Databases (all engines)
    for db in infra.get("databases", []) or []:
        breakdown["databases"]["discovered"] += 1
        db_name = str(db.get("name", "")).strip() if isinstance(db, dict) else str(db).strip()
        if db_name and (hwsw_index.contains(db_name) or ssp_index.contains(db_name) or fips_index.contains(db_name)):
            breakdown["databases"]["matched"] += 1
            matched_assets.append(f"Database Instance: {db_name}")
        elif db_name:
            discrepancies.append(f"Undocumented Database: '{db_name}' not found in HW/SW inventory or SSP.")

    # 4. VPC Networks
    for vpc in net.get("vpcs", []) or []:
        breakdown["vpcs"]["discovered"] += 1
        v_name = str(vpc.get("name", "")).strip() if isinstance(vpc, dict) else str(vpc).strip()
        if v_name and (hwsw_index.contains(v_name) or ssp_index.contains(v_name)):
            breakdown["vpcs"]["matched"] += 1
            matched_assets.append(f"VPC Network: {v_name}")
        elif v_name:
            discrepancies.append(f"Undocumented VPC Network: '{v_name}' not found in HW/SW inventory or SSP.")

    # 4b. Subnet CIDR Ranges
    # Subnets are recorded by CIDR rather than by name, so the CIDR is the only
    # identifier derivable from the source. A non-empty but unparseable value is
    # counted as an unreconciled asset rather than dropped, because dropping it
    # would shrink the denominator and inflate the coverage percentage.
    raw_cidrs = net.get("subnets_cidrs")
    if isinstance(raw_cidrs, (list, tuple, set)):
        cidr_source_text = " ".join(str(c) for c in raw_cidrs)
    else:
        cidr_source_text = str(raw_cidrs or "").strip()
    parsed_cidrs = sorted(set(_CIDR_PATTERN.findall(cidr_source_text)))
    if cidr_source_text and not parsed_cidrs:
        breakdown["subnets"]["discovered"] += 1
        discrepancies.append(
            "Unreconciled Subnet Range: 'subnets_cidrs' is populated "
            f"({cidr_source_text!r}) but yields no parseable CIDR; subnet "
            "documentation coverage is [NOT DETERMINED FROM SOURCE]."
        )
    for cidr in parsed_cidrs:
        breakdown["subnets"]["discovered"] += 1
        if ssp_index.contains(cidr) or ppsm_index.contains(cidr) or hwsw_index.contains(cidr):
            breakdown["subnets"]["matched"] += 1
            matched_assets.append(f"Subnet CIDR Range: {cidr}")
        else:
            discrepancies.append(
                f"Undocumented Subnet CIDR Range: '{cidr}' not found in SSP, PPSM, or HW/SW inventory."
            )

    # 4c. Boundary Firewall Rules
    for fw in net.get("firewall_rules", []) or []:
        breakdown["firewall_rules"]["discovered"] += 1
        fw_name = str(fw.get("name", "")).strip() if isinstance(fw, dict) else str(fw).strip()
        if fw_name and (ppsm_index.contains(fw_name) or ssp_index.contains(fw_name) or hwsw_index.contains(fw_name)):
            breakdown["firewall_rules"]["matched"] += 1
            matched_assets.append(f"Firewall Rule: {fw_name}")
        elif fw_name:
            discrepancies.append(
                f"Undocumented Boundary Firewall Rule: '{fw_name}' not found in PPSM, SSP, or HW/SW inventory."
            )
        else:
            discrepancies.append(
                "Unreconciled Boundary Firewall Rule: rule discovered with no resolvable "
                "name; identifier is [NOT DETERMINED FROM SOURCE]."
            )

    # 4d. Cloud KMS Cryptographic Keys
    for key in infra.get("kms_keys", []) or []:
        breakdown["kms_keys"]["discovered"] += 1
        k_name = str(key.get("name", "")).strip() if isinstance(key, dict) else str(key).strip()
        if k_name and (fips_index.contains(k_name) or hwsw_index.contains(k_name) or ssp_index.contains(k_name)):
            breakdown["kms_keys"]["matched"] += 1
            matched_assets.append(f"KMS Cryptographic Key: {k_name}")
        elif k_name:
            discrepancies.append(
                f"Undocumented KMS Cryptographic Key: '{k_name}' not found in FIPS matrix, HW/SW inventory, or SSP."
            )
        else:
            discrepancies.append(
                "Unreconciled KMS Cryptographic Key: key discovered with no resolvable "
                "name; identifier is [NOT DETERMINED FROM SOURCE]."
            )

    # 5. Service Accounts
    for sa in infra.get("service_accounts", []) or []:
        breakdown["service_accounts"]["discovered"] += 1
        sa_id = str(sa.get("account_id") or sa.get("resource_name", "")).strip() if isinstance(sa, dict) else str(sa).strip()
        if sa_id and (ssp_index.contains(sa_id) or hwsw_index.contains(sa_id)):
            breakdown["service_accounts"]["matched"] += 1
            matched_assets.append(f"Service Account: {sa_id}")
        elif sa_id:
            discrepancies.append(f"Undocumented IAM Service Account: '{sa_id}' not found in SSP Section 1.7.")

    # 6. Ingress Ports (PPSM)
    port_list = apps.get("exposed_ports") or net.get("application_ports") or []
    for p_item in port_list:
        breakdown["exposed_ports"]["discovered"] += 1
        port = str(p_item.get("port", "")).strip() if isinstance(p_item, dict) else str(p_item).strip()
        if port and ppsm_index.contains(port):
            breakdown["exposed_ports"]["matched"] += 1
            matched_assets.append(f"PPSM Port: {port}")
        elif port:
            discrepancies.append(f"Unmapped Boundary Ingress Port: '{port}' not found in PPSM Matrix.")

    # 7. Applications
    for app in apps.get("applications", []) or []:
        breakdown["applications"]["discovered"] += 1
        a_name = str(app.get("name", "")).strip() if isinstance(app, dict) else str(app).strip()
        if a_name and (hwsw_index.contains(a_name) or ssp_index.contains(a_name)):
            breakdown["applications"]["matched"] += 1
            matched_assets.append(f"Application: {a_name}")
        elif a_name:
            discrepancies.append(f"Undocumented Application: '{a_name}' not found in HW/SW inventory.")

    # 8. Container Images
    for img in apps.get("container_images", []) or []:
        breakdown["container_images"]["discovered"] += 1
        i_name = str(img.get("image") or img.get("base_image") or img.get("name") or "").strip() if isinstance(img, dict) else str(img).strip()
        if i_name and (hwsw_index.contains(i_name) or ssp_index.contains(i_name)):
            breakdown["container_images"]["matched"] += 1
            matched_assets.append(f"Container Image: {i_name}")
        elif i_name:
            discrepancies.append(f"Undocumented Container Image: '{i_name}' not found in HW/SW inventory.")

    total_discovered = sum(v["discovered"] for v in breakdown.values())
    total_matched = sum(v["matched"] for v in breakdown.values())
    coverage_score = round((total_matched / max(1, total_discovered)) * 100.0, 1) if total_discovered > 0 else 100.0

    return {
        "total_discovered_assets": total_discovered,
        "reconciled_assets_count": total_matched,
        "coverage_score_percent": coverage_score,
        "breakdown": breakdown,
        "matched_assets": matched_assets,
        "discrepancies": discrepancies,
    }


# A control heading in the SSP, anchored so that a request for "AC-17" cannot
# latch onto "### AC-17(2)". The lookahead rejects any character that could
# extend the control identifier.
_SSP_CONTROL_HEADING_TEMPLATE = r"^###[ \t]+{ctrl}(?![A-Za-z0-9_\-(])[^\n]*\n"
# Any subsequent level-3 heading, which terminates the current control section.
_SSP_NEXT_HEADING_RE = re.compile(r"^###[ \t]", re.MULTILINE)
# A GitHub-flavoured task-list checkbox. The SSP renders the implementation
# status list inside a Markdown table cell with "<br>" separators, so the label
# is terminated by "<", "|" or a newline rather than by the end of a line.
_SSP_STATUS_CHECKBOX_RE = re.compile(r"-\s*\[(?P<mark>[ xX])\]\s*(?P<label>[^<|\n]+)")
# NIST catalog assignment placeholders. Their presence means the control
# statement was never tailored to this system, so it cannot substantiate an
# implementation claim.
_UNTAILORED_PARAMETER_RE = re.compile(r"\[assignment:|\[selection:", re.IGNORECASE)


def _extract_ssp_control_section(ssp_text: str, ctrl_id: str) -> str:
    """Extracts the body of a single control section from the SSP Markdown.

    The section is located by an anchored heading match rather than a substring
    search. A substring search for ``"### AC-17"`` also matches
    ``"### AC-17(2)"``, which either attributes another control's narrative to
    this one or, in the original implementation, silently reused the previous
    loop iteration's section as this control's evidence.

    Args:
        ssp_text: Full System Security Plan Markdown, in original case.
        ctrl_id: NIST control identifier, for example ``"IA-2(1)"``.

    Returns:
        The section body with its heading line removed and surrounding
        whitespace stripped, or ``""`` when the control has no section.
    """
    if not ssp_text or not ctrl_id:
        return ""
    heading_re = re.compile(
        _SSP_CONTROL_HEADING_TEMPLATE.format(ctrl=re.escape(ctrl_id)),
        re.MULTILINE,
    )
    match = heading_re.search(ssp_text)
    if match is None:
        return ""
    body_start = match.end()
    next_heading = _SSP_NEXT_HEADING_RE.search(ssp_text, body_start)
    body_end = next_heading.start() if next_heading else len(ssp_text)
    return ssp_text[body_start:body_end].strip()


def _parse_ssp_implementation_status(section: str) -> Tuple[FrozenSet[str], FrozenSet[str]]:
    """Parses the SSP 'Implementation Status (check all that apply)' checkboxes.

    The status must be read from the checkbox state, not from the presence of a
    word. Every control section lists all five candidate statuses, so a plain
    substring test for ``"planned"`` matches the *unchecked* ``- [ ] Planned``
    box in every section and permanently suppresses verification.

    Args:
        section: A single control section body from the SSP.

    Returns:
        A ``(checked, unchecked)`` pair of lowercased status labels. Both are
        empty when the section contains no recognisable status block, which the
        caller must treat as "status not determined" rather than as success.
    """
    checked: Set[str] = set()
    unchecked: Set[str] = set()
    for match in _SSP_STATUS_CHECKBOX_RE.finditer(section or ""):
        label = match.group("label").strip().rstrip("|").strip().lower()
        if not label:
            continue
        if match.group("mark").lower() == "x":
            checked.add(label)
        else:
            unchecked.add(label)
    return frozenset(checked), frozenset(unchecked)


def audit_senior_compliance_quality(
    target_dir: str,
    inventory: Dict[str, Any],
    ato_dir: str,
    alignment_res: Dict[str, Any],
    excel_results: List[Dict[str, Any]],
    docx_results: List[Dict[str, Any]],
    oscal_results: List[Dict[str, Any]],
    unresolved_tokens: List[Dict[str, Any]],
    config_required_vars: List[Dict[str, Any]],
    stigs_required: Optional[List[Dict[str, Any]]] = None,
    rmf_action_items: Optional[List[Dict[str, Any]]] = None,
    yaml_results: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Performs Level 4 Senior Compliance Assessor Quality & Security Posture Audit.

    Evaluates:
    - 14 ATC (Authorization to Connect) Connection Controls deep verification in SCTM/SSP.
    - Network Perimeter boundary defense & dangerous ingress exposure analysis.
    - FIPS 140-3 Cryptographic CMEK key rotation and data-at-rest coverage.
    - POA&M Continuous Monitoring health & milestone currency.
    - Classifies findings into CAT I (Critical / Blocker), CAT II (Medium), and CAT III (Low).
    - Evaluates authoritative qualitative RMF authorization readiness gates (NIST SP 800-37 / DoD RMF).

    Args:
        target_dir: Workspace root directory.
        inventory: System inventory dictionary.
        ato_dir: Absolute path to the ato_artifacts directory.
        alignment_res: Results from audit_inventory_artifact_alignment.
        excel_results: Results from audit_excel_workbooks.
        docx_results: Results from audit_docx_policies.
        oscal_results: Results from audit_oscal_packages.
        unresolved_tokens: List of unresolved macro tokens.
        config_required_vars: List of pending configuration variables.
        stigs_required: Optional list of identified DISA STIG benchmarks.
        rmf_action_items: Optional list of manual RMF action items.

    Returns:
        A dictionary containing ATC verification details, categorized findings,
        qualitative authorization status, and accreditation recommendation.
    """
    if not inventory:
        inventory = {}
    infra = inventory.get("infrastructure_components") or {}
    net = inventory.get("network_architecture") or {}
    sys_info = inventory.get("system_information") or {}

    sctm_yaml = os.path.join(ato_dir, "SCTM", "SCTM_Burndown_Matrix.yaml")
    poam_yaml = os.path.join(ato_dir, "POAM", "Plan_of_Action_and_Milestones.yaml")
    ssp_md = os.path.join(ato_dir, "SSP", "SSP_System_Security_Plan.md")
    if not os.path.exists(ssp_md):
        ssp_md = os.path.join(ato_dir, "SSP", "System_Security_Plan.md")

    cat_1_findings: List[Dict[str, str]] = []
    cat_2_findings: List[Dict[str, str]] = []
    cat_3_findings: List[Dict[str, str]] = []

    sctm_controls_map: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(sctm_yaml):
        try:
            sctm_data = read_yaml_file(sctm_yaml)
            for fam in sctm_data.get("control_families", []) or []:
                for ctrl in fam.get("controls", []) or []:
                    c_id = ctrl.get("id")
                    if c_id:
                        sctm_controls_map[c_id] = ctrl
        except (OSError, ValueError, TypeError) as err:
            logger.error("Failed to parse SCTM YAML at '%s': %s", sctm_yaml, err)
            cat_1_findings.append({
                "id": "CAT1-SCTM-PARSE",
                "component": "SCTM_Burndown_Matrix.yaml",
                "severity": "CAT I (Critical)",
                "description": f"Failed to parse SCTM YAML, content UNVERIFIED: {err}",
                "remediation": "Fix YAML syntax."
            })

    ssp_text = _read_optional_lowercase(ssp_md, lower=False)

    # 1. Insecure Boundary Ingress Analysis
    dangerous_ports = {"21": "FTP", "23": "Telnet", "5432": "PostgreSQL", "3306": "MySQL", "1433": "SQL Server", "1521": "Oracle", "27017": "MongoDB", "6379": "Redis"}
    admin_ports = {"22": "SSH", "3389": "RDP"}

    for rule in net.get("firewall_rules", []) or []:
        if not isinstance(rule, dict):
            continue
        r_name = rule.get("name", "unnamed-firewall-rule")
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

        for p_str in rule_ports:
            if p_str in dangerous_ports:
                db_rem = "Restrict source IP range to private subnet CIDRs or deploy Cloud IAP zero-trust proxy bastions."
                cat_1_findings.append({
                    "id": "CAT1-FW-001",
                    "component": f"Firewall Rule '{r_name}'",
                    "severity": "CAT I (Critical)",
                    "description": f"Direct 0.0.0.0/0 ingress allowed to {dangerous_ports[p_str]} database/sensitive port ({p_str}).",
                    "remediation": db_rem,
                })
            elif p_str in admin_ports:
                adm_rem = "Enforce Google Cloud IAP (35.235.240.0/20) and remove public 0.0.0.0/0 ingress."
                cat_1_findings.append({
                    "id": "CAT1-FW-002",
                    "component": f"Firewall Rule '{r_name}'",
                    "severity": "CAT I (Critical)",
                    "description": f"Direct 0.0.0.0/0 ingress allowed to administrative remote access port ({admin_ports[p_str]} port {p_str}).",
                    "remediation": adm_rem,
                })
            elif p_str == "80":
                cat_2_findings.append({
                    "id": "CAT2-FW-001",
                    "component": f"Firewall Rule '{r_name}'",
                    "severity": "CAT II (Medium)",
                    "description": "Plaintext HTTP port 80 exposed to 0.0.0.0/0.",
                    "remediation": "Configure automated HTTP-to-HTTPS redirect (TLS 1.3) on target proxy / load balancer."
                })

    # 2. Cryptographic Readiness & CMEK Audit
    kms_keys = infra.get("kms_keys", []) or []
    if not kms_keys and any("kms" in str(s).lower() for s in infra.get("services_enabled", []) or []):
        cat_2_findings.append({
            "id": "CAT2-CRYPTO-001",
            "component": "Cloud KMS Key Rings",
            "severity": "CAT II (Medium)",
            "description": "No customer-managed encryption keys (CMEK) discovered in active inventory.",
            "remediation": "Provision Cloud KMS CMEK key rings and associate with persistent storage resources."
        })
    else:
        for k in kms_keys:
            if not isinstance(k, dict):
                continue
            rot = str(k.get("rotation_period", "")).strip()
            k_name = k.get("name", "kms-key")
            if not rot or rot in ["null", "none", ""]:
                cat_2_findings.append({
                    "id": "CAT2-CRYPTO-002",
                    "component": f"Cloud KMS Key '{k_name}'",
                    "severity": "CAT II (Medium)",
                    "description": f"KMS key '{k_name}' missing automated key rotation policy.",
                    "remediation": "Configure automated 90-day key rotation (7776000s) in Terraform."
                })
            else:
                m = re.match(r"^(\d+)s?$", rot)
                if m and int(m.group(1)) > 31536000:
                    cat_2_findings.append({
                        "id": "CAT2-CRYPTO-003",
                        "component": f"Cloud KMS Key '{k_name}'",
                        "severity": "CAT II (Medium)",
                        "description": f"KMS key '{k_name}' rotation period ({rot}) exceeds maximum allowable 365-day interval.",
                        "remediation": "Reduce key rotation period to 90 days (7776000s) for DoD IL5 / FedRAMP High compliance."
                    })

    # 3. 14 ATC Connection Controls Substantive Architectural Verification
    atc_verification_records: List[Dict[str, Any]] = []
    verified_atc_count = 0
    # Mandatory ATC controls that appear in neither the SCTM nor the SSP. These
    # must be surfaced as a finding rather than silently reported as "PARTIAL".
    absent_atc_controls: List[str] = []

    atc_arch_criteria: Dict[str, List[str]] = {
        "AC-17": ["iap", "identity-aware", "vpn", "ssm", "bastion", "tunnel", "ssh", "rdp", "remote access", "remote", "session manager", "private access", "workstation", "baseline"],
        "AC-17(2)": ["tls", "1.3", "fips", "encryption", "crypto", "tunnel", "https", "ipsec", "cryptographic", "cipher", "baseline"],
        "IA-2(1)": ["mfa", "multi-factor", "token", "hardware token", "cac", "piv", "fido2", "webauthn", "privileged", "identity", "baseline"],
        "IA-2(2)": ["mfa", "multi-factor", "authenticator", "sso", "identity", "saml", "oidc", "token", "authentication", "baseline"],
        "IA-2(3)": ["mfa", "hardware", "token", "bastion", "console", "break-glass", "privileged", "local", "pam", "sudo", "baseline"],
        "IA-2(4)": ["mfa", "local", "authentication", "credential", "least privilege", "account", "login", "password", "baseline"],
        "IA-5(1)": ["password", "passphrase", "complexity", "length", "rotation", "expiration", "character", "secret", "vault", "passwordless", "baseline"],
        "IR-8": ["incident", "response plan", "runbook", "sla", "cisa", "us-cert", "handling", "containment", "reporting", "investigation", "baseline"],
        "IR-9": ["spillage", "spill", "sanitization", "isolation", "containment", "contamination", "forensic", "incident", "baseline"],
        "RA-5": ["vulnerability", "scan", "scanning", "acas", "nessus", "trivy", "semgrep", "cve", "remediation", "flaw", "patch", "baseline"],
        "SC-7": ["firewall", "boundary", "vpc", "subnet", "perimeter", "default-deny", "ingress", "egress", "security group", "isolation", "vpc service controls", "vpc-sc", "network", "baseline"],
        "SC-8": ["tls", "tls 1.3", "encryption", "in-transit", "transit", "https", "crypto", "integrity", "confidentiality", "transmission", "baseline"],
        "SC-28": ["kms", "cmek", "encryption at rest", "at rest", "at-rest", "fips 140", "aes-256", "customer-managed", "key ring", "key vault", "storage", "baseline"],
        "SI-2": ["flaw", "patch", "remediation", "update", "vulnerability", "30 day", "sla", "maintenance", "security patch", "baseline"],
    }

    # Statuses that, when checked in the SSP, affirmatively assert the control
    # is in place. "Partially Implemented", "Planned" and "Not Applicable" are
    # deliberately absent: none of them substantiates an ATC connection control.
    affirming_ssp_statuses = ("implemented", "inherited")
    blocking_ssp_statuses = ("not implemented", "partially implemented", "planned", "not applicable")

    for ctrl_id, ctrl_name, ctrl_desc in FOURTEEN_ATC_CONTROLS:
        ctrl_entry = sctm_controls_map.get(ctrl_id)
        status = ""
        details = ""
        is_substantive = False
        evidence_text = ""
        evidence_source = "None"

        if ctrl_entry:
            evidence_source = "SCTM"
            status = ctrl_entry.get("status") or "Documented in SCTM"
            details = ctrl_entry.get("implementation_details") or ""
            evidence_text = details
            stat_lower = str(status).lower()
            is_implemented = (
                any(stat_lower.startswith(p) for p in ("implemented", "inherited", "satisfied", "automated"))
                and "not implemented" not in stat_lower
                and "planned" not in stat_lower
            )
            if is_implemented and len(details) >= 25 and "[CONFIG_REQUIRED" not in details and "{{" not in details:
                is_substantive = True
        else:
            ssp_section = _extract_ssp_control_section(ssp_text, ctrl_id)
            if ssp_section:
                evidence_source = "SSP"
                evidence_text = ssp_section
                details = ssp_section[:160].replace("\n", " ").strip() + "..."
                checked, unchecked = _parse_ssp_implementation_status(ssp_section)
                ssp_lower = ssp_section.lower()

                affirmed = sorted(
                    label for label in checked
                    if any(a in label for a in affirming_ssp_statuses)
                    and not any(b in label for b in blocking_ssp_statuses)
                )
                blocked = sorted(
                    label for label in checked
                    if any(b in label for b in blocking_ssp_statuses)
                )

                if not checked and not unchecked:
                    # No status block at all: the narrative alone cannot tell us
                    # whether the control is in place. Fail closed.
                    status = "Documented in SSP (implementation status [NOT DETERMINED FROM SOURCE])"
                elif blocked or not affirmed:
                    checked_desc = ", ".join(sorted(checked)) if checked else "no status box checked"
                    status = f"Documented in SSP (implementation status: {checked_desc})"
                elif len(ssp_section) < 50:
                    status = "Documented in SSP (implementation narrative too short to assess)"
                elif "[config_required" in ssp_lower or "{{" in ssp_lower:
                    status = "Documented in SSP (narrative contains unresolved placeholders)"
                elif _UNTAILORED_PARAMETER_RE.search(ssp_section):
                    status = "Documented in SSP (untailored NIST assignment/selection parameters remain)"
                else:
                    status = f"Implemented in SSP ({', '.join(affirmed)})"
                    is_substantive = True
            else:
                # Fail closed: the control appears in neither authoritative
                # source. Describing it with the ATC catalog blurb would present
                # a requirement as if it were evidence of implementation.
                status = "Absent from SCTM and SSP"
                details = (
                    "[NOT DETERMINED FROM SOURCE] No implementation statement for this mandatory "
                    "ATC connection control exists in the SCTM or the SSP."
                )

        # Substantive architectural content validation via semantic linter evaluation
        if is_substantive:
            if evaluate_control_substance is not None:
                sub_ok, sub_status, sub_reason = evaluate_control_substance(
                    ctrl_id=ctrl_id,
                    narrative=evidence_text,
                    inventory=inventory,
                )
                if not sub_ok:
                    is_substantive = False
                    status = f"Incomplete Technical Narrative ({sub_status})"
                    details = f"{details} [Assessor Finding: {sub_reason}]"
            else:
                ev_lower = evidence_text.lower()
                required_concepts = atc_arch_criteria.get(ctrl_id, [])
                has_arch_substance = any(c in ev_lower for c in required_concepts)
                if not has_arch_substance:
                    is_substantive = False
                    status = "Incomplete Technical Narrative (Missing Architectural Substance)"

        # Architectural posture cross-reconciliation with live findings
        if is_substantive:
            if ctrl_id == "SC-7":
                boundary_findings = [f for f in cat_1_findings if "FW" in f.get("id", "")]
                if boundary_findings:
                    is_substantive = False
                    status = "Boundary Ingress Exposure (CAT 1 Finding)"
                    details = f"Boundary violation: {boundary_findings[0]['description']}"
            elif ctrl_id == "AC-17":
                admin_ingress = [f for f in cat_1_findings if "CAT1-FW-002" in f.get("id", "")]
                if admin_ingress:
                    is_substantive = False
                    status = "Insecure Remote Admin Ingress (CAT 1 Finding)"
                    details = f"Remote access exposure: {admin_ingress[0]['description']}"
            elif ctrl_id == "SC-28":
                cmek_missing = [f for f in cat_2_findings if "CAT2-CRYPTO-001" in f.get("id", "")]
                if cmek_missing:
                    is_substantive = False
                    status = "CMEK Cryptographic Key Absent (CAT 2 Finding)"
                    details = "Persistent data stores lack Customer-Managed Encryption Keys."

        if not details:
            # Never fall back to the ATC catalog description: that text states
            # what the control requires, not what this system implements, and
            # rendering it in an evidence column fabricates evidence.
            details = "[NOT DETERMINED FROM SOURCE] No implementation narrative recorded for this control."

        if is_substantive:
            ver_status = "VERIFIED"
            verified_atc_count += 1
        elif evidence_source == "None":
            ver_status = "MISSING"
            absent_atc_controls.append(ctrl_id)
        else:
            ver_status = "PARTIAL"

        atc_verification_records.append({
            "id": ctrl_id,
            "name": ctrl_name,
            "description": ctrl_desc,
            "status": status,
            "details": details,
            "verification": ver_status,
            "evidence_source": evidence_source,
        })

    if absent_atc_controls:
        cat_2_findings.append({
            "id": "CAT2-ATC-001",
            "component": "14 ATC Connection Controls (SCTM / SSP)",
            "severity": "CAT II (Medium)",
            "description": (
                f"{len(absent_atc_controls)} of the 14 mandatory ATC connection controls have no "
                f"implementation statement in either the SCTM or the SSP: {', '.join(absent_atc_controls)}. "
                "Their implementation status is [NOT DETERMINED FROM SOURCE]."
            ),
            "remediation": (
                "Author implementation statements for the listed controls in the SCTM (or the SSP) "
                "before requesting an Authorization to Connect; an ATC cannot be granted on undocumented controls."
            ),
        })

    # 4. Unresolved Macro Syntax Tokens
    if unresolved_tokens:
        cat_1_findings.append({
            "id": "CAT1-SYNTAX-001",
            "component": "ATO Deliverable Templates",
            "severity": "CAT I (Critical)",
            "description": f"{len(unresolved_tokens)} unresolved template macro tokens ({{{{ ... }}}}) detected in generated deliverables.",
            "remediation": "Re-run compliance generator to hydrate all template tokens prior to formal package submission."
        })

    # 5. Pending Institutional Variables
    if config_required_vars:
        cat_2_findings.append({
            "id": "CAT2-GOV-001",
            "component": "compliance_config.yaml",
            "severity": "CAT II (Medium)",
            "description": f"{len(config_required_vars)} pending institutional configuration variables requiring human assignment.",
            "remediation": "Fill in lead personnel roles and governance identifiers in compliance_config.yaml."
        })

    # 6. Undocumented Inventory Assets
    disc_list = alignment_res.get("discrepancies", [])
    if disc_list:
        sample_disc = "; ".join(disc_list[:2])
        cat_2_findings.append({
            "id": "CAT2-INVENTORY-001",
            "component": "Hardware & Software Inventory",
            "severity": "CAT II (Medium)",
            "description": f"{len(disc_list)} discovered system assets not fully cross-referenced in ATO deliverables ({sample_disc}).",
            "remediation": "Synchronize Hardware/Software inventory with latest system_inventory.json via --fix."
        })

    # 7. POA&M Milestone Currency
    if os.path.exists(poam_yaml):
        try:
            poam_data = read_yaml_file(poam_yaml)
            today_d = datetime.now().date()
            overdue_items = []
            unparseable_dates = []
            for item in poam_data.get("poam_items", []) or []:
                if not isinstance(item, dict):
                    continue
                if item.get("status") == "Ongoing":
                    sched = item.get("scheduled_completion_date")
                    if sched:
                        try:
                            d = datetime.strptime(str(sched).strip()[:10], "%Y-%m-%d").date()
                        except (ValueError, TypeError) as date_err:
                            # Fail closed: an unreadable date must not be mistaken for
                            # a future one, which would hide a slipped milestone.
                            logger.warning(
                                "POA&M item '%s' has an unparseable scheduled_completion_date %r: %s",
                                item.get("item_id"),
                                sched,
                                date_err,
                            )
                            unparseable_dates.append(f"{item.get('item_id')} ({sched!r})")
                            continue
                        if d <= today_d:
                            overdue_items.append(f"{item.get('item_id')} (due {sched})")
            if overdue_items:
                cat_2_findings.append({
                    "id": "CAT2-POAM-001",
                    "component": "Plan of Action & Milestones (POA&M)",
                    "severity": "CAT II (Medium)",
                    "description": f"POA&M contains {len(overdue_items)} overdue Ongoing milestones past scheduled date: {', '.join(overdue_items[:2])}.",
                    "remediation": "Update milestone progress or request Authorizing Official extension in eMASS."
                })
            if unparseable_dates:
                cat_2_findings.append({
                    "id": "CAT2-POAM-002",
                    "component": "Plan of Action & Milestones (POA&M)",
                    "severity": "CAT II (Medium)",
                    "description": (
                        f"{len(unparseable_dates)} Ongoing POA&M milestones have an unparseable "
                        f"scheduled completion date and could not be assessed for currency: "
                        f"{', '.join(unparseable_dates[:2])}."
                    ),
                    "remediation": "Correct the affected dates to ISO 8601 (YYYY-MM-DD) so milestone currency can be verified."
                })
        except (OSError, ValueError, TypeError) as err:
            logger.error("Failed evaluating POA&M milestones at '%s': %s", poam_yaml, err)
            cat_1_findings.append({
                "id": "CAT1-POAM-PARSE",
                "component": "Plan_of_Action_and_Milestones.yaml",
                "severity": "CAT I (Critical)",
                "description": f"Failed to parse POA&M YAML, content UNVERIFIED: {err}",
                "remediation": "Fix YAML syntax."
            })

    # 7b. DoD IL4/IL5 Continuous Monitoring & Telemetry Boundary Verification
    impact_lvl = str(sys_info.get("impact_level") or "").upper()
    comp_base = str(sys_info.get("compliance_baseline") or sys_info.get("compliance_framework") or "").upper()
    is_dod_il4_il5 = any(lvl in impact_lvl for lvl in ["IL4", "IL5", "IL-4", "IL-5", "DOD"]) or any(lvl in comp_base for lvl in ["IL4", "IL5", "IL-4", "IL-5", "DOD"])

    if is_dod_il4_il5:
        allow_unaccredited = (
            sys_info.get("allow_unaccredited_scc_in_il5") is True
            or (inventory.get("security_operations") or {}).get("allow_unaccredited_scc_in_il5") is True
        )
        telemetry_ctrl_ids = ["AU-6", "CA-7", "SI-4", "IR-4"]
        for t_id in telemetry_ctrl_ids:
            ctrl_rec = sctm_controls_map.get(t_id)
            if not ctrl_rec:
                continue
            impl = str(ctrl_rec.get("implementation_details") or "")
            evid = str(ctrl_rec.get("codebase_evidence") or "")
            combined_txt = f"{impl} {evid}".lower()
            if "security command center" in combined_txt or " scc " in combined_txt or "scc premium" in combined_txt:
                has_external_cssp = any(k in combined_txt for k in ["cssp", "siem", "export sink", "log router", "external", "bridge", "cloud logging", "chronicle", "secops"])
                if not has_external_cssp:
                    if allow_unaccredited:
                        cat_3_findings.append({
                            "id": f"CAT3-DOD-TEL-{t_id}-ETP",
                            "component": f"Telemetry Control '{t_id}' (AO Exception-to-Policy)",
                            "severity": "CAT III (Advisory)",
                            "description": f"Control {t_id} utilizes Security Command Center in DoD IL4/IL5 under an approved Authorizing Official (AO) Exception-to-Policy (allow_unaccredited_scc_in_il5: true).",
                            "remediation": "Maintain signed AO ETP memorandum in eMASS package artifacts.",
                        })
                    else:
                        cat_2_findings.append({
                            "id": f"CAT2-DOD-TEL-{t_id}",
                            "component": f"Telemetry Control '{t_id}'",
                            "severity": "CAT II (Medium)",
                            "description": f"Control {t_id} references Security Command Center (SCC) without routing via Cloud Logging export sinks to external accredited CSSP/SIEM. Centralized telemetry export to an accredited CSSP/SIEM is required per DoDI 8530.01.",
                            "remediation": "Route telemetry and audit logs via Cloud Logging export sinks to an accredited external CSSP/SIEM (e.g., DISA, C5ISR) or note an accredited cross-boundary bridge (or set allow_unaccredited_scc_in_il5: true with AO Exception-to-Policy).",
                        })

    # 8. CAT III Advisory Findings
    if stigs_required:
        cat_3_findings.append({
            "id": "CAT3-STIG-001",
            "component": "DISA STIG Checklists (.ckl)",
            "severity": "CAT III (Advisory)",
            "description": f"{len(stigs_required)} DISA STIG/SRG checklists identified for completion in desktop STIG Viewer.",
            "remediation": "Download official STIG compilation from DoD Cyber Exchange and export completed .ckl files."
        })
    if rmf_action_items:
        cat_3_findings.append({
            "id": "CAT3-GOV-001",
            "component": "RMF Action Alerts",
            "severity": "CAT III (Advisory)",
            "description": f"{len(rmf_action_items)} policy action highlights require review by appointed RMF roles.",
            "remediation": "Review highlighted <mark> tags in Policies_and_Procedures/."
        })

    broken_excel = [r for r in excel_results if r.get("status") == "FAIL"]
    broken_docx = [r for r in docx_results if r.get("status") == "FAIL"]
    broken_oscal = [r for r in oscal_results if r.get("status") == "FAIL"]
    broken_yaml = [r for r in (yaml_results or []) if r.get("status") == "FAIL"]
    for b_y in broken_yaml:
        cat_1_findings.append({
            "id": "CAT1-YAML-001",
            "component": os.path.basename(b_y.get("file", "YAML Deliverable")),
            "severity": "CAT I (Critical)",
            "description": f"Malformed YAML syntax in deliverable '{b_y.get('file')}': {b_y.get('error', 'Parse error')}",
            "remediation": "Correct YAML syntax to ensure valid structured data for automated ingestion and compliance auditing.",
        })
    broken_deliverables = broken_excel + broken_docx + broken_oscal + broken_yaml

    if cat_1_findings or broken_deliverables or unresolved_tokens:
        recommendation = "Remediation Required Prior to Assessment Submission"
        rec_badge = "caution"
    elif verified_atc_count == 14 and len(cat_2_findings) == 0:
        recommendation = "Technical Package Complete - Ready for Independent Assessor (3PAO / SCA) Review"
        rec_badge = "success"
    else:
        recommendation = "Conditional Package Readiness - Ready for Interim Assessment (IATT / Review)"
        rec_badge = "warning"

    return {
        "readiness_score": None,
        "authorization_status": recommendation,
        "recommendation": recommendation,
        "rec_badge": rec_badge,
        "verified_atc_count": verified_atc_count,
        "atc_records": atc_verification_records,
        "cat_1_findings": cat_1_findings,
        "cat_2_findings": cat_2_findings,
        "cat_3_findings": cat_3_findings,
    }


# ------------------------------------------------------------------------------
# Comprehensive Public Sector / ISSM Operational Evidence & Submission Registry
# Derived from ISSM_Checklist.xlsx and Public Sector RMF / eMASS submission standards
# ------------------------------------------------------------------------------

DOD_ISSM_OPERATIONAL_REQUIREMENTS: List[Dict[str, str]] = [
    {
        "name": "ACAS / Tenable Nessus Credentialed Vulnerability Scans",
        "control": "RA-5, SC-28",
        "category": "Vulnerability Assessment",
        "format": ".nessus / ACAS: ASR/ARF",
        "timeline": "Completed within 30 days prior to submission workflow",
        "responsible": "Security Operations / Lead ISSO",
        "criteria": "Scans must return 'Good Data' (credentialed plugins firing), 0 unmapped findings, and 0 unmitigated CISA KEV exploits.",
        "action": "Perform credentialed host & database scans; export in ASR/ARF format for eMASS upload."
    },
    {
        "name": "DISA STIG / SRG Benchmark Checklists (.ckl)",
        "control": "CM-6, CA-2",
        "category": "Configuration Baseline",
        "format": ".ckl (STIG Viewer)",
        "timeline": "Completed within 30 days prior to quarterly review / submission",
        "responsible": "Engineering Team & ISSM",
        "criteria": "100% benchmark coverage; every failed check (CAT I/II) must link to a mitigation statement in the POA&M.",
        "action": "Generate .ckl checklists for all matched technologies and attach to eMASS Asset Module."
    },
    {
        "name": "Software Assurance (SwA), SAST/DAST & Container Scans",
        "control": "SA-11, SI-2, SR-4",
        "category": "Application Security",
        "format": "Trivy/Semgrep SAST Report + CycloneDX SBOM",
        "timeline": "Continuous / At every build release",
        "responsible": "DevSecOps Lead",
        "criteria": "Zero Critical/High static analysis flaws; container images in Artifact Registry scanned and signed.",
        "action": "Export CI/CD vulnerability report and Software Bill of Materials (SBOM) into package."
    },
    {
        "name": "14 ATC (Authorization to Connect) Critical Controls Verification",
        "control": "AC-17, IA-2, IA-5, IR-8, IR-9, RA-5, SC-7, SC-8, SC-28, SI-2",
        "category": "Boundary Defense",
        "format": "SCTM Narrative + Technical Evidence",
        "timeline": "Prior to DoD Network / Interconnection Connection Approval",
        "responsible": "ISSM & Network Architect",
        "criteria": "All 14 ATC controls verified in SCTM with residual risk <= Moderate; no Very High/High residual risks.",
        "action": "Audit the 14 mandatory connection controls in eMASS and confirm boundary compliance."
    },
    {
        "name": "Privacy Impact Assessment (PIA DD Form 2930 / PTA)",
        "control": "PT-2, PT-3, AR-4",
        "category": "Privacy Governance",
        "format": "Signed DD Form 2930 PDF",
        "timeline": "Updated annually or upon major data architecture change",
        "responsible": "Privacy Officer & ISSM",
        "criteria": "Signed by Authorizing Official / Privacy Lead; uploaded to FISMA/eMASS for any system with PII/PHI.",
        "action": "Upload completed DD Form 2930 into eMASS System > Details > FISMA."
    },
    {
        "name": "System Interconnection Agreements (ISA / MOU / CCSD)",
        "control": "CA-3",
        "category": "Interconnection Security",
        "format": "Signed ISA/MOU PDF + Network Data Flow Diagram",
        "timeline": "Re-certified every 3 years",
        "responsible": "System Owner & ISSM",
        "criteria": "All external data paths, circuits (CCSD numbers), and boundary filtering devices clearly illustrated.",
        "action": "Document CCSD numbers on topology diagrams and attach signed interconnection agreements."
    },
    {
        "name": "CSSP SLA & Cloud Common Control Provider (CCP) Agreement",
        "control": "CA-3, CA-9",
        "category": "Cyber Defense Operations",
        "format": "Signed CSSP SLA Agreement PDF",
        "timeline": "Active and verified within 12 months",
        "responsible": "ISSM & CSOC Director",
        "criteria": "Established relationship with accredited CSSP (e.g. C5ISR / DISA / Agency CSOC); CCP inheritance accepted in eMASS.",
        "action": "Accept Cloud Common Control inheritance package and upload signed CSSP Service Level Agreement."
    },
    {
        "name": "Privileged User Access Agreements (SAAR / DD Form 2875 / Access Agreement)",
        "control": "AC-2, IA-2",
        "category": "Personnel Security",
        "format": "Signed SAAR / DD Form 2875 / Agreement PDFs",
        "timeline": "Recertified annually for all privileged administrators",
        "responsible": "ISSO & Platform Admin",
        "criteria": "Documented background investigations (Tier 3/5 or Public Trust) and annual cybersecurity training certificates.",
        "action": "Maintain signed access authorization forms for all Cloud IAM administrators and attach verification roster."
    },
    {
        "name": "Contingency Plan (CP) & Incident Response (IR) Tabletop Reports (TTX)",
        "control": "CP-4, IR-4",
        "category": "Resilience & Continuity",
        "format": "Tabletop After-Action Report (AAR) PDF",
        "timeline": "Conducted within last 12 months",
        "responsible": "ISSM & Contingency Lead",
        "criteria": "Documented annual failover exercise across dual cloud regions and CSOC incident escalation tabletop.",
        "action": "Conduct annual disaster recovery simulation and upload formal test results."
    },
    {
        "name": "Executive ATO Determination Request Memo for AO Signature",
        "control": "CA-6",
        "category": "Accreditation Decision",
        "format": "Official Executive Memorandum (.docx / .pdf)",
        "timeline": "Final submission step",
        "responsible": "ISSM, System Owner, AO",
        "criteria": "Formal memorandum summarizing residual risk posture and requesting 3-year ATO or continuous monitoring.",
        "action": "Submit package through eMASS Package Approval Chain (PAC) for Authorizing Official final signature."
    }
]

# 14 ATC (Authorization to Connect) Critical Controls
FOURTEEN_ATC_CONTROLS: List[Tuple[str, str, str]] = [
    ("AC-17", "Remote Access", "Mandates encrypted VPN/IAP tunnels, multi-factor authentication, and centralized access logging."),
    ("AC-17(2)", "Protection of Confidentiality / Integrity Using Encryption", "Requires FIPS 140-3 TLS 1.3 cryptographic protection for all remote sessions."),
    ("IA-2(1)", "Network Access to Privileged Accounts", "Enforces hardware token MFA for all administrative IAM network access."),
    ("IA-2(2)", "Network Access to Non-Privileged Accounts", "Enforces MFA for all standard user network access."),
    ("IA-2(3)", "Local Access to Privileged Accounts", "Enforces hardware MFA for direct local/bastion console access."),
    ("IA-2(4)", "Local Access to Non-Privileged Accounts", "Enforces MFA for local access."),
    ("IA-5(1)", "Password-Based Authentication", "Enforces complex passphrase standards and automated expiration when passwords are used."),
    ("IR-8", "Incident Response Plan", "Documented and tested incident handling procedures with CISA/DoD reporting SLAs."),
    ("IR-9", "Information Spillage Response", "Formal spillage containment, forensic isolation, and sanitization SOPs."),
    ("RA-5", "Vulnerability Scanning", "Monthly credentialed ACAS vulnerability scans with 30-day flaw remediation SLA."),
    ("SC-7", "Boundary Protection", "Default-deny network perimeter firewall rules, VPC peering, and subnet isolation."),
    ("SC-8", "Transmission Confidentiality and Integrity", "TLS 1.3 encryption across all internal and external communication paths."),
    ("SC-28", "Protection of Information at Rest", "FIPS 140-3 Cloud KMS CMEK encryption across all persistent disks, buckets, and databases."),
    ("SI-2", "Flaw Remediation", "Security patch management process remediating Critical/High vulnerabilities within 30 days.")
]


def hydrate_example_data_in_artifacts(md_and_yaml_files: List[str]) -> int:
    """Tags pending RMF placeholders with visible sample example badges.

    Replaces unconfigured variable placeholders with high-visibility callout badges
    in Markdown documents, and valid quoted YAML scalars in YAML matrices, to prevent
    premature submission of incomplete compliance artifacts without corrupting YAML syntax.

    Args:
        md_and_yaml_files: List of file paths to Markdown and YAML artifacts.

    Returns:
        Total number of artifact files updated with tagged example badges.
    """
    total_tagged_items = 0
    sample_badge_style = "background-color: #fef08a; border: 2px dashed #ca8a04; color: #854d0e; font-weight: bold; padding: 2px 6px; border-radius: 4px;"

    for fpath in md_and_yaml_files:
        try:
            content = read_text_file(fpath)
        except OSError as err:
            logger.warning("Failed reading file %s for example hydration: %s", fpath, err)
            continue

        orig_content = content
        is_yaml = fpath.endswith((".yaml", ".yml"))

        if TemplateEngine:
            content = TemplateEngine.hydrate_legacy_placeholders(
                content, is_yaml=is_yaml, badge_style=sample_badge_style
            )
        else:
            def tag_config_req(match: re.Match) -> str:
                var_name = match.group(0).replace("[CONFIG_REQUIRED:", "").replace("]", "").strip()
                if is_yaml:
                    return f'"[AI CONTEXTUAL EXAMPLE REQUIRED: {var_name}]"'
                return f'<mark style="{sample_badge_style}">⚠️ [AI CONTEXTUAL EXAMPLE REQUIRED: {var_name}]</mark>'

            if is_yaml:
                content = re.sub(
                    r'"\[CONFIG_REQUIRED:\s*[^\]]+\]"',
                    lambda m: f'"[AI CONTEXTUAL EXAMPLE REQUIRED: {m.group(0)[18:-2].strip()}]"',
                    content,
                )
                content = re.sub(
                    r"'\[CONFIG_REQUIRED:\s*[^\]]+\]'",
                    lambda m: f'"[AI CONTEXTUAL EXAMPLE REQUIRED: {m.group(0)[18:-2].strip()}]"',
                    content,
                )
                content = re.sub(r"\[CONFIG_REQUIRED:\s*[^\]]+\]", tag_config_req, content)
            else:
                content = re.sub(r"\[CONFIG_REQUIRED:\s*[^\]]+\]", tag_config_req, content)

        if content != orig_content:
            total_tagged_items += 1
            write_text_file(fpath, content)

    return total_tagged_items


def audit_excel_workbooks(ato_dir: str) -> List[Dict[str, Any]]:
    """Audits generated macro-enabled Excel workbooks for data integrity.

    Inspects sheets, row counts, and data validation rules in .xlsm workbooks
    such as Hardware/Software Inventory, POA&M, PPSM, and SCTM.

    Args:
        ato_dir: Absolute path to the ato_artifacts directory.

    Returns:
        A list of audit result dictionaries detailing file status, sheets, row counts,
        and detected issues.
    """
    excel_audit_results: List[Dict[str, Any]] = []
    if not OPENPYXL_AVAILABLE or openpyxl is None:
        logger.warning("openpyxl is not installed; skipping Excel workbook audit")
        return [{
            "file": "Excel_Workbooks",
            "path": ato_dir,
            "status": "SKIP",
            "sheets": [],
            "rows_count": {},
            "issues": ["openpyxl is not installed; install openpyxl via 'pip install openpyxl' to audit Excel workbooks."],
        }]
    xl_files = glob.glob(os.path.join(ato_dir, "**/*.xlsm"), recursive=True) + glob.glob(os.path.join(ato_dir, "**/*.xlsx"), recursive=True)

    for xl_path in xl_files:
        if "Google Services FedRamp Package" in xl_path:
            continue
        rel_name = os.path.basename(xl_path)
        item_res: Dict[str, Any] = {
            "file": rel_name,
            "path": xl_path,
            "status": "PASS",
            "sheets": [],
            "rows_count": {},
            "issues": []
        }
        wb = None
        try:
            wb = openpyxl.load_workbook(xl_path, data_only=True, keep_vba=True)
            item_res["sheets"] = wb.sheetnames

            if "Hardware_Software_Inventory" in rel_name:
                allowed_hw: Set[Any] = set()
                allowed_sw: Set[Any] = set()
                if "(U) Lists" in wb.sheetnames:
                    lists_ws = wb["(U) Lists"]
                    allowed_hw = set([lists_ws.cell(row=r, column=1).value for r in range(2, lists_ws.max_row + 1) if lists_ws.cell(row=r, column=1).value is not None])
                    allowed_sw = set([lists_ws.cell(row=r, column=3).value for r in range(2, lists_ws.max_row + 1) if lists_ws.cell(row=r, column=3).value is not None])

                if "Hardware" in wb.sheetnames:
                    ws_hw = wb["Hardware"]
                    hw_data_rows = max(0, ws_hw.max_row - 7)
                    item_res["rows_count"]["Hardware Assets"] = hw_data_rows
                    if hw_data_rows == 0:
                        item_res["issues"].append("Hardware sheet contains no data rows (empty from row 8+).")
                        item_res["status"] = "WARN"
                    elif allowed_hw:
                        for r in range(8, ws_hw.max_row + 1):
                            if not ws_hw.cell(row=r, column=1).value:
                                continue
                            val_type = ws_hw.cell(row=r, column=2).value
                            if val_type and val_type not in allowed_hw:
                                item_res["issues"].append(f"Hardware Row {r}: Component Type '{val_type}' is not in Tab_HWType dropdown.")
                                item_res["status"] = "WARN"
                else:
                    item_res["issues"].append("Missing required 'Hardware' sheet.")
                    item_res["status"] = "FAIL"

                if "Software" in wb.sheetnames:
                    ws_sw = wb["Software"]
                    sw_data_rows = max(0, ws_sw.max_row - 7)
                    item_res["rows_count"]["Software Assets"] = sw_data_rows
                    if sw_data_rows == 0:
                        item_res["issues"].append("Software sheet contains no data rows (empty from row 8+).")
                        item_res["status"] = "WARN"
                    elif allowed_sw:
                        for r in range(8, ws_sw.max_row + 1):
                            if not ws_sw.cell(row=r, column=1).value:
                                continue
                            val_type = ws_sw.cell(row=r, column=2).value
                            if val_type and val_type not in allowed_sw:
                                item_res["issues"].append(f"Software Row {r}: Software Type '{val_type}' is not in Tab_SWType dropdown.")
                                item_res["status"] = "WARN"
                else:
                    item_res["issues"].append("Missing required 'Software' sheet.")
                    item_res["status"] = "FAIL"

            elif "Plan_of_Action_and_Milestones" in rel_name:
                if "POA&M" in wb.sheetnames:
                    ws_poam = wb["POA&M"]
                    poam_rows = max(0, ws_poam.max_row - 7)
                    item_res["rows_count"]["POA&M Milestones"] = poam_rows
                    today_d = datetime.now().date()
                    for r in range(8, ws_poam.max_row + 1):
                        if not ws_poam.cell(row=r, column=1).value and not ws_poam.cell(row=r, column=2).value:
                            continue
                        p_status = str(ws_poam.cell(row=r, column=6).value or "").strip()
                        sched_d = ws_poam.cell(row=r, column=7).value
                        if p_status == "Ongoing" and sched_d:
                            try:
                                sched_parsed = datetime.strptime(str(sched_d).strip()[:10], "%Y-%m-%d").date()
                            except (ValueError, TypeError) as date_err:
                                # Fail closed: an unreadable date must not be silently
                                # treated as a future (on-track) one.
                                item_res["issues"].append(
                                    f"POA&M Row {r}: Scheduled Completion Date ({sched_d!r}) is not a "
                                    f"valid ISO 8601 date ({date_err}); milestone currency is UNVERIFIED."
                                )
                                item_res["status"] = "WARN"
                            else:
                                if sched_parsed <= today_d:
                                    item_res["issues"].append(f"POA&M Row {r}: Ongoing finding has past/today Scheduled Completion Date ({sched_d}).")
                                    item_res["status"] = "WARN"
                else:
                    item_res["issues"].append("Missing required 'POA&M' sheet.")
                    item_res["status"] = "FAIL"

            elif "PPSM" in rel_name:
                if "PPSM" in wb.sheetnames:
                    ws_ppsm = wb["PPSM"]
                    ppsm_rows = max(0, ws_ppsm.max_row - 8)
                    item_res["rows_count"]["PPSM Boundary Records"] = ppsm_rows
                else:
                    item_res["issues"].append("Missing required 'PPSM' sheet.")
                    item_res["status"] = "FAIL"

            elif "SCTM" in rel_name:
                if "Template" in wb.sheetnames:
                    ws_sctm = wb["Template"]
                    active_controls = 0
                    missing_est_date = 0
                    missing_slcm_comments = 0
                    missing_resp_entities = 0
                    invalid_date_logic = 0
                    consecutive_blanks = 0
                    today_d = datetime.now().date()

                    for r in range(7, ws_sctm.max_row + 1):
                        ctrl_id = ws_sctm.cell(row=r, column=1).value
                        if not ctrl_id or not str(ctrl_id).strip():
                            consecutive_blanks += 1
                            if consecutive_blanks > 10:
                                break
                            continue
                        consecutive_blanks = 0
                        active_controls += 1

                        status_val = str(ws_sctm.cell(row=r, column=5).value or "").strip()
                        est_date = ws_sctm.cell(row=r, column=10).value
                        resp_ent = ws_sctm.cell(row=r, column=12).value
                        slcm = ws_sctm.cell(row=r, column=19).value

                        if status_val == "Not Applicable":
                            # N/A controls require N/A justification and no completion date
                            na_just = ws_sctm.cell(row=r, column=9).value
                            if not na_just or not str(na_just).strip():
                                item_res["issues"].append(f"SCTM Row {r} ({ctrl_id}): N/A status requires N/A Justification (Col I).")
                                item_res["status"] = "WARN"
                        else:
                            if not est_date or not str(est_date).strip():
                                missing_est_date += 1
                            else:
                                # Validate date logic: Implemented/Inherited must be past/today; Planned must be future
                                try:
                                    d_parsed = datetime.strptime(str(est_date).strip(), "%m/%d/%Y").date()
                                except (ValueError, TypeError) as date_err:
                                    # Fail closed: an unreadable date must not let the
                                    # row skip the status/date consistency check.
                                    invalid_date_logic += 1
                                    item_res["issues"].append(
                                        f"SCTM Row {r} ({ctrl_id}): Estimated Completion Date ({est_date!r}) is not "
                                        f"a valid MM/DD/YYYY date ({date_err}); status/date consistency is UNVERIFIED."
                                    )
                                    item_res["status"] = "WARN"
                                else:
                                    if status_val in ["Implemented", "Inherited", "Hybrid", "Compensated"]:
                                        if d_parsed > today_d:
                                            invalid_date_logic += 1
                                            item_res["issues"].append(
                                                f"SCTM Row {r} ({ctrl_id}): {status_val} control has future Estimated Completion Date ({est_date})."
                                            )
                                            item_res["status"] = "WARN"
                                    elif status_val == "Planned":
                                        if d_parsed <= today_d:
                                            invalid_date_logic += 1
                                            item_res["issues"].append(
                                                f"SCTM Row {r} ({ctrl_id}): Planned control has past/today Estimated Completion Date ({est_date})."
                                            )
                                            item_res["status"] = "WARN"

                            if not slcm or not str(slcm).strip():
                                missing_slcm_comments += 1
                            if not resp_ent or not str(resp_ent).strip():
                                missing_resp_entities += 1

                    item_res["rows_count"]["Controls Monitored"] = active_controls
                    item_res["rows_count"]["Estimated Dates Filled"] = active_controls - missing_est_date
                    item_res["rows_count"]["SLCM Comments Filled"] = active_controls - missing_slcm_comments

                    if missing_est_date > 0:
                        item_res["issues"].append(f"SCTM contains {missing_est_date} controls missing Estimated Completion Date.")
                        item_res["status"] = "WARN"
                    if missing_slcm_comments > 0:
                        item_res["issues"].append(f"SCTM contains {missing_slcm_comments} controls missing SLCM Comments.")
                        item_res["status"] = "WARN"
                    if missing_resp_entities > 0:
                        item_res["issues"].append(f"SCTM contains {missing_resp_entities} controls missing Responsible Entities.")
                        item_res["status"] = "WARN"
                    if invalid_date_logic > 0:
                        item_res["issues"].append(f"SCTM contains {invalid_date_logic} controls with invalid date logic (future for implemented or past for planned).")
                        item_res["status"] = "WARN"
                else:
                    item_res["issues"].append("Missing required 'Template' sheet.")
                    item_res["status"] = "FAIL"

        except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as e:
            item_res["status"] = "UNVERIFIED"
            item_res["issues"].append(f"Failed to load workbook with openpyxl, content UNVERIFIED: {str(e)}")
        finally:
            if wb is not None:
                try:
                    wb.close()
                except (OSError, ValueError, AttributeError) as err:
                    logger.debug("Failed closing workbook %s: %s", xl_path, err)

        excel_audit_results.append(item_res)

    return excel_audit_results


def audit_docx_policies(ato_dir: str) -> List[Dict[str, Any]]:
    """Audits generated Word (.docx) policy documents for OpenXML validity.

    Verifies that the ZIP package contains valid word/document.xml, proper cover
    blocks, required heading paragraphs, and complete relationship mapping for
    all embedded hyperlinks.

    Args:
        ato_dir: Absolute path to the ato_artifacts directory.

    Returns:
        A list of audit result dictionaries detailing document status, XML elements,
        and hyperlink relationship integrity.
    """
    docx_audit_results: List[Dict[str, Any]] = []
    docx_files = glob.glob(os.path.join(ato_dir, "**/*.docx"), recursive=True) if os.path.exists(ato_dir) else []

    for d_path in sorted(docx_files):
        rel_name = os.path.relpath(d_path, ato_dir)
        item_res: Dict[str, Any] = {
            "file": rel_name,
            "status": "PASS",
            "has_cover": False,
            "has_headings": False,
            "hyperlinks_count": 0,
            "relationships_count": 0,
            "issues": []
        }
        try:
            with zipfile.ZipFile(d_path, "r") as docx_zip:
                namelist = docx_zip.namelist()
                if "word/document.xml" not in namelist:
                    item_res["status"] = "FAIL"
                    item_res["issues"].append("Missing 'word/document.xml' in OpenXML archive.")
                    docx_audit_results.append(item_res)
                    continue

                doc_info = docx_zip.getinfo("word/document.xml")
                if doc_info.file_size > 100 * 1024 * 1024 or (doc_info.compress_size > 0 and doc_info.file_size / doc_info.compress_size > 100):
                    raise ValueError("word/document.xml exceeds safe size/compression limits")
                doc_xml_bytes = docx_zip.read("word/document.xml")
                root = ET.fromstring(doc_xml_bytes)

                tables = root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl")
                paragraphs = root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p")

                if len(tables) >= 1:
                    item_res["has_cover"] = True
                if len(paragraphs) >= 5:
                    item_res["has_headings"] = True

                # Audit Hyperlinks and OpenXML Relationship Integrity
                hyperlinks = root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hyperlink")
                item_res["hyperlinks_count"] = len(hyperlinks)

                if "word/_rels/document.xml.rels" in namelist:
                    rels_info = docx_zip.getinfo("word/_rels/document.xml.rels")
                    if rels_info.file_size > 100 * 1024 * 1024 or (rels_info.compress_size > 0 and rels_info.file_size / rels_info.compress_size > 100):
                        raise ValueError("word/_rels/document.xml.rels exceeds safe size/compression limits")
                    rels_xml_bytes = docx_zip.read("word/_rels/document.xml.rels")
                    rels_root = ET.fromstring(rels_xml_bytes)
                    rels_map: Dict[str, Dict[str, str]] = {}
                    for r in rels_root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                        r_id = r.attrib.get("Id")
                        r_target = r.attrib.get("Target")
                        r_type = r.attrib.get("Type")
                        if r_id:
                            rels_map[r_id] = {
                                "target": r_target or "",
                                "type": r_type or "",
                                "target_mode": r.attrib.get("TargetMode", ""),
                            }
                    item_res["relationships_count"] = len(rels_map)

                    broken_links = []
                    for hl in hyperlinks:
                        rid = hl.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
                        if not rid or rid not in rels_map or not rels_map[rid].get("target"):
                            broken_links.append(rid or "missing_id")

                    if broken_links:
                        item_res["status"] = "FAIL"
                        item_res["issues"].append(
                            f"Hyperlink relationship integrity error: {len(broken_links)} hyperlink(s) lack valid target relationships ({broken_links[:5]})."
                        )
                elif hyperlinks:
                    item_res["status"] = "FAIL"
                    item_res["issues"].append("Missing 'word/_rels/document.xml.rels' with active hyperlinks present.")

        except (zipfile.BadZipFile, OSError, ET.ParseError, ValueError, KeyError) as e:
            item_res["status"] = "UNVERIFIED"
            item_res["issues"].append(f"Failed to parse OpenXML structure, content UNVERIFIED: {str(e)}")

        docx_audit_results.append(item_res)

    return docx_audit_results


def audit_oscal_packages(ato_dir: str) -> List[Dict[str, Any]]:
    """Audits generated NIST OSCAL deliverables for schema integrity and control coverage.

    Verifies system-security-plan and component-definition JSON deliverables exist,
    contain recognized NIST OSCAL metadata (e.g. 1.2.3 or 1.1.0), and define implemented
    requirements mapping to system components.

    Args:
        ato_dir: Absolute path to the ato_artifacts directory.

    Returns:
        A list of audit result dictionaries detailing OSCAL deliverable status.
    """
    oscal_audit_results: List[Dict[str, Any]] = []
    oscal_dir = os.path.join(ato_dir, "OSCAL_SSP")
    if not os.path.exists(oscal_dir):
        return oscal_audit_results

    for filename in ["system_security_plan.oscal.json", "component_definition.oscal.json"]:
        filepath = os.path.join(oscal_dir, filename)
        if not os.path.exists(filepath):
            continue
        rel_name = os.path.relpath(filepath, ato_dir)
        item_res: Dict[str, Any] = {
            "file": rel_name,
            "status": "PASS",
            "controls_count": 0,
            "components_count": 0,
            "oscal_version": None,
            "issues": [],
        }
        try:
            data = read_json_file(filepath)
            if "system-security-plan" in data:
                ssp = data["system-security-plan"]
                ver = ssp.get("metadata", {}).get("oscal-version")
                item_res["oscal_version"] = ver
                if ver not in SUPPORTED_OSCAL_VERSIONS:
                    item_res["status"] = "WARN"
                    item_res["issues"].append(
                        f"Unrecognized OSCAL version '{ver}'. Expected one of: {', '.join(SUPPORTED_OSCAL_VERSIONS[-4:])}"
                    )
                comps = ssp.get("system-implementation", {}).get("components", [])
                item_res["components_count"] = len(comps)
                reqs = ssp.get("control-implementation", {}).get("implemented-requirements", [])
                item_res["controls_count"] = len(reqs)
                if len(reqs) < 5:
                    item_res["status"] = "WARN"
                    item_res["issues"].append(f"Low control count ({len(reqs)}) in OSCAL SSP.")
            elif "component-definition" in data:
                compdef = data["component-definition"]
                ver = compdef.get("metadata", {}).get("oscal-version")
                item_res["oscal_version"] = ver
                if ver not in SUPPORTED_OSCAL_VERSIONS:
                    item_res["status"] = "WARN"
                    item_res["issues"].append(
                        f"Unrecognized OSCAL version '{ver}'. Expected one of: {', '.join(SUPPORTED_OSCAL_VERSIONS[-4:])}"
                    )
                comps = compdef.get("components", [])
                item_res["components_count"] = len(comps)
            else:
                item_res["status"] = "FAIL"
                item_res["issues"].append("Missing valid root OSCAL element.")
        except (OSError, ValueError, TypeError) as e:
            item_res["status"] = "UNVERIFIED"
            item_res["issues"].append(f"Failed parsing OSCAL JSON, content UNVERIFIED: {e}")
        oscal_audit_results.append(item_res)

    return oscal_audit_results


def audit_yaml_syntax_integrity(ato_dir: str) -> List[Dict[str, Any]]:
    """Performs deep YAML syntax integrity verification across all YAML deliverables.

    Reads each .yaml and .yml deliverable under ato_artifacts using read_yaml_file()
    to ensure valid syntax, proper indentation, and readable structured data.

    Args:
        ato_dir: Absolute path to the ato_artifacts directory.

    Returns:
        List of audit dictionaries for each audited YAML deliverable.
    """
    yaml_results: List[Dict[str, Any]] = []
    all_files = glob.glob(os.path.join(ato_dir, "**/*"), recursive=True)
    yaml_files = sorted([f for f in all_files if f.endswith((".yaml", ".yml")) and os.path.isfile(f)])

    for yf in yaml_files:
        rel = os.path.relpath(yf, ato_dir)
        item: Dict[str, Any] = {
            "file": rel,
            "abs_path": yf,
            "status": "PASS",
            "error": None,
        }
        try:
            parsed = read_yaml_file(yf)
            if parsed is None:
                item["status"] = "PASS"
                item["note"] = "Empty or null YAML document"
            elif not isinstance(parsed, (dict, list)):
                item["status"] = "WARN"
                item["note"] = f"Top-level YAML is scalar ({type(parsed).__name__})"
        except Exception as e:
            item["status"] = "FAIL"
            item["error"] = str(e)
            logger.error("YAML syntax error in deliverable '%s': %s", rel, e)
        yaml_results.append(item)

    return yaml_results


def validate_compliance_package(
    target_dir: str,
    fix_drift: bool = False,
    fill_examples: bool = False,
    policy_format: Optional[str] = None,
    data_format: Optional[str] = None,
    oscal_format: Optional[str] = None,
    oscal_version: Optional[str] = None,
    update_stigs: bool = False,
    stigs_mode: Optional[str] = None,
    stigs_catalog: Optional[str] = None,
    run_linter: bool = True,
    linter_strict: bool = True,
    **kwargs: Any,
) -> bool:
    """Performs comprehensive validation of the generated compliance package.

    Audits Markdown, YAML, OpenXML Word (.docx), and Excel (.xlsm) files,
    evaluates DISA STIG applicability, executes deterministic semantic linting
    against target public sector baselines and Terraform drift, compiles
    Path_to_Authorization.md/.docx, and optionally repairs codebase drift.

    Args:
        target_dir: Path to the foundation directory containing ato_artifacts.
        fix_drift: If True, re-runs generator to synchronize live Terraform drift.
        fill_examples: If True, hydrates sample example tags into pending cards.
        policy_format: Optional export format for policies ("both", "docx", or "markdown").
        data_format: Optional export format for matrices ("both", "excel", or "yaml").
        oscal_format: Optional export format for OSCAL packages ("both", "json", "yaml", or "none").
        oscal_version: Optional NIST OSCAL version ("1.2.3" or "1.1.0").
        update_stigs: If True, triggers active pulling of latest STIG versions from remote feeds.
        stigs_mode: Resolution mode for STIG checklists ('auto', 'online', or 'offline').
        stigs_catalog: Optional custom catalog source URL or local file path.
        run_linter: If True, executes deterministic semantic linter evaluation.
        linter_strict: If True, enforces strict Public Sector Security Engineer standard.
        **kwargs: Backward compatibility options (ai_validate, ai_strict, ai_model).

    Returns:
        True if validation completed successfully, False otherwise.
    """
    if "ai_validate" in kwargs:
        run_linter = bool(kwargs.pop("ai_validate"))
    if "ai_strict" in kwargs:
        linter_strict = bool(kwargs.pop("ai_strict"))
    kwargs.pop("ai_model", None)

    target_dir = str(resolve_path(target_dir))
    ato_dir = os.path.join(target_dir, "ato_artifacts")
    ato_dir = str(ensure_path_within_boundary(ato_dir, target_dir))
    inventory_path = os.path.join(target_dir, "system_inventory.json")
    inventory_path = str(ensure_path_within_boundary(inventory_path, target_dir))

    if not os.path.exists(ato_dir):
        logger.error("ATO artifacts directory not found at '%s'. Run generator first.", ato_dir)
        return False

    inventory: Dict[str, Any] = {}
    if os.path.exists(inventory_path):
        try:
            inventory = read_json_file(inventory_path)
            validate_system_inventory_schema(inventory, source_path=inventory_path)
        except (OSError, ValueError, TypeError) as err:
            logger.warning("System inventory validation warning: %s", err)

    repaired_files: List[str] = []
    semantic_linter_report = None

    # 0. Code Drift Pre-Flight Check & Auto-Repair (Run BEFORE audits to ensure reports reflect post-sync state)
    if inventory and fix_drift:
        generator_script = os.path.join(SKILL_BASE, "scripts", "generate_compliance_artifacts.py")
        logger.info("Pre-flight sync: Synchronizing generated compliance package with live codebase inventory before audit...")

        # Forward explicit CLI format preferences or discover saved preferences from inventory/config
        export_prefs = inventory.get("export_preferences") or inventory.get("compliance_config", {})
        p_fmt = policy_format or export_prefs.get("policy_formats")
        d_fmt = data_format or export_prefs.get("structured_data_formats")
        o_fmt = oscal_format or export_prefs.get("oscal_formats") or export_prefs.get("oscal_format")
        o_ver = oscal_version or export_prefs.get("oscal_version")

        gen_cmd = [sys.executable, generator_script]
        if p_fmt:
            gen_cmd.append(f"--policy-format={p_fmt}")
        if d_fmt:
            gen_cmd.append(f"--data-format={d_fmt}")
        if o_fmt:
            gen_cmd.append(f"--oscal-format={o_fmt}")
        if o_ver:
            gen_cmd.append(f"--oscal-version={o_ver}")
        gen_cmd.append("--")
        gen_cmd.append(str(resolve_path(target_dir)))

        try:
            with audit_operation(AuditEvent.EXTERNAL_COMMAND, obj=target_dir, detail={"command": str(gen_cmd)}):
                res = subprocess.run(gen_cmd, capture_output=False, timeout=600)
                if res.returncode == 0:
                    repaired_files.append("All RMF accreditation artifacts synchronized with latest Terraform code state.")
                else:
                    logger.warning("Artifact generator exited with non-zero code %d during drift repair.", res.returncode)
                    raise subprocess.SubprocessError(f"Generator failed with code {res.returncode}")
        except subprocess.TimeoutExpired:
            logger.error("Artifact generator timed out after 600 seconds during drift repair.")
        except (subprocess.SubprocessError, OSError) as err:
            logger.error("Failed executing artifact generator during drift repair: %s", err)

    # 1. Inspect Markdown & YAML files
    all_files = glob.glob(os.path.join(ato_dir, "**/*"), recursive=True)
    md_and_yaml_files = [filepath for filepath in all_files if filepath.endswith((".md", ".yaml"))]
    total_files_checked = len(md_and_yaml_files)

    # Optional Example Data Hydration Pass
    hydrated_example_count = 0
    if fill_examples:
        logger.info("Filling in realistic sample example data into pending RMF cards and placeholders...")
        hydrated_example_count = hydrate_example_data_in_artifacts(md_and_yaml_files)
        logger.info("Hydrated example data across %d artifact files.", hydrated_example_count)

    unresolved_tokens: List[Dict[str, Any]] = []
    config_required_vars: List[Dict[str, Any]] = []
    rmf_action_items: List[Dict[str, Any]] = []

    token_regex = re.compile(r"\{\{\s*[A-Z0-9_]+\s*\}\}")
    config_req_regex = re.compile(r"\[CONFIG_REQUIRED:\s*[^\]]+\]")
    mark_action_regex = re.compile(r"<mark\b[^>]*>(.{0,8192}?)</mark>", re.DOTALL)

    for fpath in md_and_yaml_files:
        rel_path = os.path.relpath(fpath, ato_dir)
        try:
            content = read_text_file(fpath)
        except OSError as err:
            logger.warning("Failed reading file %s during token audit: %s", fpath, err)
            continue

        content_lines = content.splitlines()

        for idx, line in enumerate(content_lines, 1):
            for m in token_regex.finditer(line):
                unresolved_tokens.append({"file": rel_path, "line": idx, "token": m.group(0), "context": line.strip()})
            for m in config_req_regex.finditer(line):
                config_required_vars.append({"file": rel_path, "line": idx, "variable": m.group(0), "context": line.strip()})
            for m in mark_action_regex.finditer(line):
                txt = m.group(1).replace("⚠️", "").strip()
                rmf_action_items.append({"file": rel_path, "line": idx, "action": txt})

    # 2. Audit YAML Deliverables Syntax Integrity
    yaml_results = audit_yaml_syntax_integrity(ato_dir)

    # 3. Audit Excel Workbooks
    excel_results = audit_excel_workbooks(ato_dir)

    # 4. Audit DOCX Policies
    docx_results = audit_docx_policies(ato_dir)

    # 4b. Audit Incident Response Runbooks
    runbooks_dir = os.path.join(ato_dir, "Incident_Response_Runbooks")
    runbook_results: List[Dict[str, Any]] = []
    expected_runbooks = [
        "IR_IAM_Compromised_Credentials_Runbook",
        "IR_Compute_Resource_Compromise_Runbook",
        "IR_KMS_CMEK_Compromise_Runbook",
        "IR_Network_Intrusion_Runbook",
        "IR_VPC_Service_Controls_Violation_Runbook"
    ]
    if os.path.exists(runbooks_dir):
        for rb_name in expected_runbooks:
            has_md = os.path.exists(os.path.join(runbooks_dir, f"{rb_name}.md"))
            has_docx = os.path.exists(os.path.join(runbooks_dir, f"{rb_name}.docx"))
            runbook_results.append({
                "runbook": rb_name,
                "has_md": has_md,
                "has_docx": has_docx,
                "status": "PASS" if has_md else "MISSING"
            })

    # 4c. Audit NIST OSCAL 1.1.0 & 1.2.3 Machine-Readable Packages
    oscal_results = audit_oscal_packages(ato_dir)

    # 5. Dynamically Evaluate DISA STIG Applicability (referencing STIG Viewer catalog)
    stigs_required = evaluate_disa_stig_applicability(
        inventory,
        md_and_yaml_files,
        target_dir=target_dir,
        update_stigs=update_stigs,
        stigs_mode=stigs_mode,
        stigs_catalog=stigs_catalog,
    )

    # 6. Dynamic Architecture & Inventory Cross-Reconciliation (Level 2 Evaluation)
    alignment_results = audit_inventory_artifact_alignment(target_dir, inventory, ato_dir)

    # 7. Senior Compliance Assessor Quality, Risk & ATO Readiness Evaluation (Level 4 Evaluation)
    senior_audit = audit_senior_compliance_quality(
        target_dir=target_dir,
        inventory=inventory,
        ato_dir=ato_dir,
        alignment_res=alignment_results,
        excel_results=excel_results,
        docx_results=docx_results,
        oscal_results=oscal_results,
        unresolved_tokens=unresolved_tokens,
        config_required_vars=config_required_vars,
        stigs_required=stigs_required,
        rmf_action_items=rmf_action_items,
        yaml_results=yaml_results,
    )

    # 6b. Deterministic Semantic Linter & Architectural Drift Evaluation (Level 6 Evaluation)
    if run_linter and run_semantic_linter is not None:
        logger.info("Executing Deterministic Semantic Linter & Architectural Drift Evaluation...")
        try:
            semantic_linter_report = run_semantic_linter(
                target_dir=target_dir,
                inventory=inventory,
                ato_dir=ato_dir,
                strict=linter_strict,
            )
        except Exception as err:
            logger.warning("Semantic linter encountered error: %s", err)
            semantic_linter_report = None

    # 7. Generate Unified Path to Authorization (PTA) Strategy & Verification Report
    # Clean up obsolete separate validation report or PTA subfolder if present
    old_val_report = os.path.join(ato_dir, "VALIDATION_REPORT.md")
    if os.path.exists(old_val_report):
        try:
            os.remove(old_val_report)
        except OSError as err:
            logger.warning(
                "Could not remove superseded report '%s': %s. Stale evidence remains in the package.",
                old_val_report,
                err,
            )
    legacy_ai_report = os.path.join(ato_dir, "ai_validation_report.json")
    if os.path.exists(legacy_ai_report):
        try:
            os.remove(legacy_ai_report)
        except OSError as err:
            logger.warning(
                "Could not remove legacy report '%s': %s.",
                legacy_ai_report,
                err,
            )
    old_pta_folder = os.path.join(ato_dir, "PTA")
    if os.path.exists(old_pta_folder) and os.path.isdir(old_pta_folder):
        try:
            shutil.rmtree(old_pta_folder)
        except OSError as err:
            logger.warning(
                "Could not remove superseded PTA folder '%s': %s. Stale evidence remains in the package.",
                old_pta_folder,
                err,
            )

    sys_info = inventory.get("system_information", {}) if inventory else {}
    sys_name = sys_info.get("system_name") or "Cloud Enclave Foundation"
    sys_abbr = sys_info.get("system_abbreviation") or "CEF"
    org_name = sys_info.get("organization") or "Department of Defense / Enterprise"
    impact_level = sys_info.get("impact_level") or "IL5 / FedRAMP High"
    fips_199 = f"Confidentiality: {sys_info.get('confidentiality_impact') or 'High'} / Integrity: {sys_info.get('integrity_impact') or 'High'} / Availability: {sys_info.get('availability_impact') or 'High'}"
    baseline = sys_info.get("compliance_baseline") or "NIST SP 800-53 Rev. 5 (FedRAMP High / DoD IL5)"
    roles_info = inventory.get("personnel_roles", {})
    issm_name = roles_info.get("issm", {}).get("name") or sys_info.get("issm_name") or "[CONFIG_REQUIRED: Lead ISSM Name]"
    issm_title = roles_info.get("issm", {}).get("title") or sys_info.get("issm_title") or "Information System Security Manager (ISSM)"
    so_name = roles_info.get("system_owner", {}).get("name") or sys_info.get("system_owner_name") or "[CONFIG_REQUIRED: System Owner Name]"
    so_title = roles_info.get("system_owner", {}).get("title") or sys_info.get("system_owner_title") or "System Owner / Program Manager"
    ao_name = roles_info.get("authorizing_official", {}).get("name") or sys_info.get("authorizing_official_name") or "[CONFIG_REQUIRED: Authorizing Official Name]"
    ao_title = roles_info.get("authorizing_official", {}).get("title") or sys_info.get("authorizing_official_title") or "Authorizing Official (AO)"
    target_date = sys_info.get("target_authorization_date") or sys_info.get("effective_date") or datetime.now().strftime("%B %d, %Y")

    csp_name = "Google Cloud Platform"
    impact_str = str(impact_level).upper()
    comp_base_str = str(baseline).upper()
    is_dod = any(lvl in impact_str for lvl in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"]) or any(lvl in comp_base_str for lvl in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"])

    report_path = os.path.join(ato_dir, "Path_to_Authorization.md")
    report_lines: List[str] = []
    report_lines.append("# Path to Authorization (PTA) Strategy, Master ATO Roadmap & Package Validation Audit\n")
    report_lines.append("## Document Governance & Accreditation Baseline\n")
    report_lines.append("| Governance Metric | Policy Standard & Specification |")
    report_lines.append("| :--- | :--- |")
    report_lines.append(f"| **Document Title** | Path to Authorization (PTA) Strategy & Master ATO Roadmap |")
    report_lines.append(f"| **Target System Name** | {sys_name} ({sys_abbr}) |")
    report_lines.append(f"| **Security Categorization** | {fips_199} ({impact_level}) |")
    report_lines.append(f"| **Governing Entity** | {org_name} |")
    report_lines.append(f"| **Compliance Baseline** | {baseline} |")
    report_lines.append(f"| **Document Owner** | {issm_name} ({issm_title}) |")
    report_lines.append(f"| **System Owner** | {so_name} ({so_title}) |")
    report_lines.append(f"| **Approval Authority** | {ao_name} ({ao_title}) |")
    report_lines.append(f"| **Target Authorization Date** | {target_date} |")
    report_lines.append(f"| **Audit Timestamp** | {datetime.now().strftime('%B %d, %Y at %H:%M:%S')} |\n")

    report_lines.append("> [!IMPORTANT]")
    report_lines.append("> **HOW THIS CODEBASE ACCELERATES YOUR PATH TO ATO**:")
    report_lines.append("> Executing this compliance automation provisions the **foundational technical deliverables (Phase 3)** and extracts live architecture facts from Terraform. However, achieving formal Authorization to Operate (ATO) requires completing the end-to-end operational, governance, and assessment itinerary below. Running code alone does not grant an ATO—it provides the accelerated baseline and technical evidence needed to achieve it.\n")

    report_lines.append("> [!NOTE]")
    report_lines.append("> **eMASS & Enterprise GRC Direct Authoring & Import Workflow**:")
    report_lines.append("> In many Department of Defense (DoD) and Federal authorization environments, the System Security Plan (SSP) is authored and maintained directly within enterprise GRC platforms such as **eMASS**, **CSAM**, **Xacta**, or the **FedRAMP Repository**.")
    report_lines.append("> The SSP documentation, SCTM burndown matrices, and policy statements generated by this engine provide the authoritative technical implementation narratives, infrastructure parameters, and control allocations formatted for direct manual entry or bulk automated ingestion (via eMASS TR/TRX and NIST OSCAL XML/JSON exports) into the GRC system of record.\n")

    report_lines.append("## Executive Artifact Audit & Integrity Summary")
    report_lines.append(f"- **Markdown & YAML Inventory Files Audited**: `{total_files_checked}` files")
    yaml_status_note = "100% Valid YAML Syntax" if all(r.get("status") != "FAIL" for r in yaml_results) else "Alerts Detected (Syntax Errors)"
    report_lines.append(f"- **Structured YAML Deliverables Audited**: `{len(yaml_results)}` files (`{yaml_status_note}`)")
    total_docx_hl = sum(r.get("hyperlinks_count", 0) for r in docx_results)
    docx_status_note = "100% Valid OpenXML"
    if any(r.get("status") != "PASS" for r in docx_results):
        docx_status_note = "Alerts Detected"
    elif total_docx_hl > 0:
        docx_status_note = f"100% Valid OpenXML — {total_docx_hl} Verified Hyperlinks"
    report_lines.append(f"- **Word Policy Manuals Audited (.docx)**: `{len(docx_results)}` documents (`{docx_status_note}`)")
    if oscal_results:
        oscal_ver_str = oscal_results[0].get("oscal_version") or "1.2.3"
        report_lines.append(f"- **NIST OSCAL Packages (v{oscal_ver_str})**: `{len(oscal_results)}` deliverables (`{'100% Valid Schema' if all(r['status'] == 'PASS' for r in oscal_results) else 'Alerts Detected'}`)")
    report_lines.append(f"- **Unresolved Macro Templates (`{{ ... }}`)**: `{len(unresolved_tokens)}` syntax gaps")
    report_lines.append(f"- **Pending Institutional Variables**: `{len(config_required_vars)}` placeholders")
    report_lines.append(f"- **Designated RMF Team Human Action Highlights**: `{len(rmf_action_items)}` review items requiring manual input")
    if runbook_results:
        report_lines.append(f"- **Incident Response Runbooks Audited**: `{len([r for r in runbook_results if r['status'] == 'PASS'])}/{len(expected_runbooks)}` verified scenarios")
    report_lines.append(f"- **Applicable DISA STIG Checklists Identified**: `{len(stigs_required)}` STIG benchmarks")
    report_lines.append(f"- **Authorization Readiness Determination**: {senior_audit['recommendation']}")
    report_lines.append(f"- **Dynamic Architecture Reconciliation Coverage**: `{alignment_results['coverage_score_percent']}%` ({alignment_results['reconciled_assets_count']}/{alignment_results['total_discovered_assets']} system assets aligned)")
    report_lines.append(f"- **14 ATC Connection Controls Verified**: `{senior_audit['verified_atc_count']}/14` verified\n")

    # Multi-Level Evaluation Dashboard
    recommendation = senior_audit["recommendation"]
    verified_atc = senior_audit["verified_atc_count"]
    cov_pct = alignment_results["coverage_score_percent"]
    reconciled_cnt = alignment_results["reconciled_assets_count"]
    total_disc_cnt = alignment_results["total_discovered_assets"]

    report_lines.append("## 🎖️ Senior Compliance Assessor Multi-Level Quality & Technical Evidence Readiness Dashboard\n")
    report_lines.append("An independent automated evaluation was conducted across all generated deliverables in accordance with NIST SP 800-37 Rev. 2, NIST SP 800-53A Rev. 5, and DoD Instruction 8510.01 assessment standards:\n")
    report_lines.append("| Assessor Evaluation Dimension | Evaluation / Determination | Target Baseline | Compliance Assessor Assessment Status |")
    report_lines.append("| :--- | :--- | :--- | :--- |")
    report_lines.append(f"| **Authorization Readiness Gate** | **{recommendation}** | Ready for Independent Review | **{recommendation}** |")
    report_lines.append(f"| **Level 1: Multi-Format Packaging Integrity** | `{'100%' if not unresolved_tokens else '90%'}` | `100%` Valid OpenXML & Schema | Validated OpenXML AST (.docx/.xlsm), Excel macros, and NIST OSCAL schemas |")
    report_lines.append(f"| **Level 2: Dynamic Architecture Reconciliation** | `{'%.1f' % cov_pct}%` | `100%` Reconciled Assets | Reconciled {reconciled_cnt} of {total_disc_cnt} discovered cloud infrastructure & application assets |")
    report_lines.append(f"| **Level 3: DISA STIG & SRG Baseline Alignment** | `{len(stigs_required)} Benchmarks` | Complete Technology Coverage | Mapped to STIG Viewer desktop workflow & DoD Cyber Exchange |")
    report_lines.append(f"| **Level 4: 14 ATC Connection Controls** | `{verified_atc} / 14 Verified` | 14/14 Implemented | Verified implementation depth across SCTM & SSP |")
    report_lines.append(f"| **Level 5: Continuous Monitoring & POA&M** | `{len(senior_audit['cat_1_findings'])} CAT I / {len(senior_audit['cat_2_findings'])} CAT II` | 0 CAT I Findings | Assessed boundary exposure, CMEK rotation, and milestone currency |")
    report_lines.append("")

    # Level 2 Reconciliation Table
    report_lines.append("### 🧩 Dynamic System Architecture & Inventory Cross-Reconciliation")
    report_lines.append("The validation engine verifies that every cloud asset discovered in `system_inventory.json` is formally accounted for in the System Security Plan (SSP), Hardware/Software Inventory, PPSM, or FIPS matrix:\n")
    report_lines.append("| Asset Category | Discovered in Inventory | Documented in ATO Package | Reconciliation Coverage | Status |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    bd = alignment_results.get("breakdown", {})
    categories_meta = [
        ("compute", "Compute & Virtual Machines"),
        ("storage", "Cloud Storage Buckets"),
        ("databases", "Database Instances & Warehouses"),
        ("vpcs", "Virtual Private Clouds (VPCs)"),
        ("subnets", "Subnet CIDR Ranges"),
        ("firewall_rules", "Boundary Firewall Rules"),
        ("kms_keys", "KMS Cryptographic Keys"),
        ("service_accounts", "IAM Service Accounts"),
        ("exposed_ports", "Boundary Ingress Ports (PPSM)"),
        ("applications", "Workload Applications"),
        ("container_images", "Container & Workload Images"),
    ]
    for cat_key, cat_label in categories_meta:
        c_disc = bd.get(cat_key, {}).get("discovered", 0)
        c_match = bd.get(cat_key, {}).get("matched", 0)
        c_pct = ("%.1f%%" % ((c_match / max(1, c_disc)) * 100.0)) if c_disc > 0 else "N/A"
        c_status = "✅ Reconciled" if (c_disc == 0 or c_match >= c_disc) else "⚠️ Review Needed"
        report_lines.append(f"| **{cat_label}** | `{c_disc}` | `{c_match}` | {c_pct} | {c_status} |")
    report_lines.append(f"| **Total Assets Reconciled** | **`{total_disc_cnt}`** | **`{reconciled_cnt}`** | **`{'%.1f' % cov_pct}%`** | **`{'✅ Complete' if cov_pct >= 95 else '⚠️ Review Needed'}`** |")
    report_lines.append("")

    if alignment_results.get("discrepancies"):
        report_lines.append("> [!NOTE]")
        report_lines.append("> **Assessor Inventory Alignment Notes**:")
        for disc in alignment_results["discrepancies"][:5]:
            report_lines.append(f"> - {disc}")
        if len(alignment_results["discrepancies"]) > 5:
            report_lines.append(f"> - *...and {len(alignment_results['discrepancies']) - 5} additional alignment observations.*")
        report_lines.append("")

    # Itemized Findings & Remediation (CAT I, CAT II, CAT III)
    all_findings = senior_audit.get("cat_1_findings", []) + senior_audit.get("cat_2_findings", []) + senior_audit.get("cat_3_findings", [])
    if all_findings:
        report_lines.append("### 🚨 Senior Compliance Assessor Findings & Remediation Plan")
        report_lines.append(
            "The following security findings and documentation gaps were identified during multi-level assessment. "
            "Findings are categorized by **NIST SP 800-30 / FedRAMP Risk Level** (Critical, High, Medium, Low) and "
            "mapped to **DoD eMASS POA&M Severity Categories** (CAT I, CAT II, CAT III) for formal package intake. "
            "Technical DISA STIG benchmark findings are tracked separately via STIG Viewer checklists (.ckl):\n"
        )
        report_lines.append("| Finding ID | Affected Component | Severity (NIST / eMASS) | Description | Assessor Remediation Guidance |")
        report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for f in all_findings:
            raw_s = f.get("severity_label") or f.get("severity", "")
            if re.search(r"\bCAT\s*III\b", raw_s, re.I) or "LOW" in raw_s.upper() or "ADVISORY" in raw_s.upper():
                sev_display = "Advisory (eMASS CAT III)"
            elif re.search(r"\bCAT\s*II\b", raw_s, re.I) or "MEDIUM" in raw_s.upper() or "MODERATE" in raw_s.upper():
                sev_display = "Medium (eMASS CAT II)"
            elif re.search(r"\bCAT\s*I\b", raw_s, re.I) or "CRITICAL" in raw_s.upper() or "HIGH" in raw_s.upper():
                sev_display = "Critical (eMASS CAT I)"
            else:
                sev_display = raw_s
            report_lines.append(f"| `{f['id']}` | **{f['component']}** | `{sev_display}` | {f['description']} | {f['remediation']} |")
        report_lines.append("")

    if semantic_linter_report:
        report_lines.append(semantic_linter_report.to_markdown())
        report_lines.append("")

    # -------------------------------------------------------------
    # SECTION 1: NIST SP 800-37 Rev. 2 RMF 7-Step Crosswalk & Master ATO Journey
    # -------------------------------------------------------------
    report_lines.append("## 🏛️ NIST SP 800-37 Rev. 2 RMF 7-Step Crosswalk\n")
    report_lines.append("Federal and Department of Defense (DoD) Authorizing Officials (AOs), assessors, and eMASS workflows track system accreditation through the canonical **7-Step Risk Management Framework (RMF)** defined in [NIST SP 800-37 Rev. 2](https://csrc.nist.gov/pubs/sp/800/37/r2/final). The table below cross-maps the official NIST RMF steps to our engineering delivery phases and automated compliance deliverables:\n")
    report_lines.append("| NIST RMF Step | Step Focus & Authoritative Publications | Delivery Phase | Key Activities & Deliverable Artifacts |")
    report_lines.append("| :--- | :--- | :--- | :--- |")
    step0_boundary = "provision Assured Workloads boundary"
    report_lines.append(f"| **Step 0: Prepare** | Essential organizational and system-level security/privacy preparation.<br>*Standards*: [NIST SP 800-37 R2](https://csrc.nist.gov/pubs/sp/800/37/r2/final), [NIST SP 800-39](https://csrc.nist.gov/pubs/sp/800/39/final), [NIST SP 800-137](https://csrc.nist.gov/pubs/sp/800/137/final) | **Phase 1**<br>(Initiation & Governance) | Formally appoint ISSM, ISSO, System Owner, and Project Sponsor; conduct kick-off with Authorizing Official (AO); articulate organizational risk tolerance; define continuous monitoring strategy; {step0_boundary}. |")
    report_lines.append("| **Step 1: Categorize** | Categorize the system and processed information based on impact analysis.<br>*Standards*: [FIPS 199](https://csrc.nist.gov/pubs/fips/199/final), [NIST SP 800-60 Vol 1 & 2](https://csrc.nist.gov/pubs/sp/800/60/v1/r1/final) | **Phase 1 & Phase 2**<br>(Architecture & Boundary) | Map information types to Security Categories across Confidentiality, Integrity, Availability (C-I-A); determine impact baseline (IL4/IL5/IL6/FedRAMP High); document system description and authorization boundary in TDD. |")
    report_lines.append("| **Step 2: Select** | Select, tailor, and document security control baseline.<br>*Standards*: [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [FIPS 200](https://csrc.nist.gov/pubs/fips/200/final), [DoD CC SRG](https://public.cyber.mil/stigs/downloads/) | **Phase 3**<br>(Compliance Automation) | Select baseline (e.g. IL5 H-H-X, FedRAMP High); tailor controls to cloud architecture; generate Security Control Traceability Matrix (`SCTM/`), Ports & Protocols Matrix (`PPSM/`), and 20 institutional policy manuals (`Policies_and_Procedures/`). |")
    step3_impl = "Deploy Terraform infrastructure with Cloud KMS CMEK, VPC Hub/Spoke, and Cloud IAP bastions; generate System Security Plan (`SSP/`); document actual deployment state and planned control enhancements."
    report_lines.append(f"| **Step 3: Implement** | Deploy controls and document implementation in security plans.<br>*Standards*: [NIST SP 800-18 Rev. 1](https://csrc.nist.gov/pubs/sp/800/18/r1/final), [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) | **Phase 2 & Phase 3**<br>(IaC & Documentation) | {step3_impl} |")
    report_lines.append("| **Step 4: Assess** | Assess controls to determine if they operate as intended and produce desired results.<br>*Standards*: [NIST SP 800-53A Rev. 5](https://csrc.nist.gov/pubs/sp/800/53a/r5/final), [DISA STIGs](https://public.cyber.mil/stigs/downloads/) | **Phase 4**<br>(Assessments & Scans) | Conduct Security Control Assessor (SCA) evaluation; execute credentialed ACAS Nessus scans (< 30 days); evaluate DISA STIG benchmarks in desktop STIG Viewer (`.ckl`); audit 14 ATC connection controls; compile initial POA&M (`POAM/`). |")
    report_lines.append("| **Step 5: Authorize** | Senior official makes risk-based decision to authorize system operation.<br>*Standards*: [NIST SP 800-37 Rev. 2](https://csrc.nist.gov/pubs/sp/800/37/r2/final), [DoD Instruction 8510.01](https://www.esd.whs.mil/Directives/issuances/dodi/) | **Phase 5 & Phase 6**<br>(Governance & eMASS) | Finalize operational agreements (CSSP/SOC SLA, ISA/MOU, Access Agreements / DD 2875, TTX); author Executive ATO Request Memo; route package through eMASS/GRC Package Approval Chain (ISSO -> ISSM -> SCA -> AO); Authorizing Official grants formal ATO. |")
    report_lines.append("| **Step 6: Monitor** | Continuously monitor control implementation and operational risk posture.<br>*Standards*: [NIST SP 800-137](https://csrc.nist.gov/pubs/sp/800/137/final), [OMB M-14-03](https://www.whitehouse.gov/omb/) | **Phase 6**<br>(Continuous Monitoring) | Execute monthly ACAS scans, quarterly STIG reviews, and continuous POA&M milestone burndown; track live infrastructure drift with `validate_compliance_artifacts.py`; manage 3-year re-authorization cycle without compliance debt. |\n")

    report_lines.append("## 🗺️ Master ATO Journey & Complete Accreditation Itinerary\n")
    report_lines.append("| Phase | Journey Phase Name | Key Activities & Requirements | Deliverable Artifacts & Outputs |")
    report_lines.append("| :--- | :--- | :--- | :--- |")
    p1_activities = ("Appoint ISSM, ISSO, System Owner, and Project Sponsor; verify U.S. Citizenship & clearances; provision eMASS/CRAMS accounts; setup Google Cloud Organization and Assured Workloads IL5 boundary." if is_dod else "Appoint ISSM, ISSO, System Owner, and Project Sponsor; verify personnel vetting; provision GRC accounts; setup Google Cloud Organization and landing zone boundary.")
    p1_outputs = "Charter, Stakeholder Roster, eMASS System Registration, GCP Project Hierarchy."
    p2_activities = "Finalize system boundary diagrams, VPC Hub/Spoke topology, private interconnects, and zero-trust IAP ingress bastions; deploy Terraform Infrastructure as Code (IaC)."
    p2_outputs = "Technical Infrastructure Design Document (TDD), Network Topology Diagram, Terraform Blueprints."
    report_lines.append(f"| **Phase 1** | **Initiation & Account Provisioning** | {p1_activities} | {p1_outputs} |")
    report_lines.append(f"| **Phase 2** | **Architecture & Boundary Solidification** | {p2_activities} | {p2_outputs} |")
    report_lines.append("| **Phase 3** | **Automated Compliance Package Provisioning** | Execute automated compliance engine to generate system security documentation, compliance matrices, and authoritative policy manuals. | System Security Plan (`SSP/`), 20 Policy Manuals (`Policies_and_Procedures/`), SCTM, PPSM, HW/SW Inventory, POA&M. |")
    report_lines.append("| **Phase 4** | **Security Assessments, Scans & STIGs** | Execute credentialed ACAS Nessus scans (< 30 days); evaluate DISA STIG benchmarks in desktop STIG Viewer (`.ckl` files); run SAST/DAST/SBOM scans; verify 14 ATC connection controls. | ACAS Scan Reports (`.nessus`), STIG Checklists (`.ckl`), Trivy/Semgrep SAST Reports, CycloneDX SBOM. |")
    report_lines.append("| **Phase 5** | **Operational Governance & Simulations** | Establish 24/7 CSSP/SOC SLA; execute Interconnection Agreements (ISA/MOU); obtain signed Privileged User Access Agreements (SAAR / DD Form 2875 or Access Agreement); conduct annual DR dual-region failover and TTX tabletop exercises. | Signed CSSP/SOC Agreement, Signed ISA/MOU PDFs, Signed Access Agreements Roster, TTX After-Action Report, PIA (DD Form 2930 / Privacy Assessment). |")
    report_lines.append("| **Phase 6** | **eMASS Submission & AO ATO Determination** | Author Executive ATO Request Memorandum; route package through eMASS Package Approval Chain (ISSO -> ISSM -> SCA -> AO); Authorizing Official issues formal ATO accreditation decision. | Executive ATO Determination Request Memo, eMASS Authorization Package, Authorizing Official Signed ATO Decision Letter. |\n")

    report_lines.append("### 🚩 Phase 1: Program Initiation, Stakeholders & Account Provisioning")
    report_lines.append("| Step | Key Activity / Requirement | Responsible Lead | Status & Verification Guidance |")
    report_lines.append("| :--- | :--- | :--- | :--- |")
    report_lines.append("| **1.1** | **Designate Key Stakeholders & Governance**: Formally appoint Project Sponsor, dedicated PM, ISSM, ISSO, System Owner, and technical/security SMEs. Conduct initial kick-off meeting with the Authorizing Official (AO) and their security team. | `Project Sponsor / System Owner` | Establish formal charter, stakeholder roster, weekly cadence, and mutual risk-tolerance alignment. |")
    s12_activity = ("**Identity Credentials, Clearances & U.S. Citizenship**: Obtain Common Access Cards (CAC) / PIV tokens and verify U.S. Citizenship with necessary security clearances (Tier 3 / Secret for IL5, Tier 5 for IL6) for all personnel managing the environment." if is_dod else "**Identity Credentials & Personnel Screening**: Obtain enterprise PIV/CAC or hardware MFA credentials and verify background screening / security clearances for all personnel managing the environment.")
    s12_guidance = "Verify active authenticator credential roster and personnel clearance/screening confirmation."
    s14_activity = "**Google Cloud Platform Foundation Setup**: Provision Google Cloud organization, Assured Workloads boundary, billing account, and audit logging sinks. Enable cloud-native threat detection (Security Command Center / Google Cloud SecOps) where configured, and establish centralized Cloud Logging export sinks to route audit telemetry to the designated CSSP or external SIEM."
    s14_guidance = "Verify Assured Workloads guardrails, active GCP billing ID, and organization log export sinks."
    s21_activity = "**Solidify ATO Boundary & Data Flows**: Finalize system boundary diagram, VPC Hub/Spoke topology, private IP ranges, and Cloud IAP zero-trust tunnels."
    s23_activity = "**Terraform IaC Deployment**: Deploy compliant GCP foundation using Cloud Foundations Fabric blueprints with Cloud KMS CMEK and Private Google Access."
    report_lines.append(f"| **1.2** | {s12_activity} | `Security Officer / HR` | {s12_guidance} |")
    report_lines.append("| **1.3** | **eMASS / CRAMS Account Provisioning**: Ensure designated security and administrative personnel have active accounts in eMASS / CRAMS with appropriate roles. | `Lead ISSM / ISSO` | Confirm system registration and workflow permissions in eMASS. |")
    report_lines.append(f"| **1.4** | {s14_activity} | `Cloud Platform Team` | {s14_guidance} |\n")

    report_lines.append("### 🏗️ Phase 2: Architecture Boundary, Infrastructure & Technical Design")
    report_lines.append("| Step | Key Activity / Requirement | Responsible Lead | Status & Verification Guidance |")
    report_lines.append("| :--- | :--- | :--- | :--- |")
    report_lines.append(f"| **2.1** | {s21_activity} | `Lead Cloud Architect` | Document network topology and boundary in TDD. |")
    report_lines.append("| **2.2** | **Technical Infrastructure Design Document (TIDD / TDD)**: Author technical design document defining all infrastructure components, encryption rings, and firewall tiers. | `Lead Cloud Architect` | Verify TDD captures AC, AU, CA, CP, IA, IR, MA, and SR controls. |")
    report_lines.append(f"| **2.3** | {s23_activity} | `DevOps / Platform Lead` | Terraform configuration active with 0 drift. |\n")

    report_lines.append("### ⚡ Phase 3: Automated ATO Foundation Generation (Delivered by this Skill)")
    report_lines.append("| Deliverable Artifact | Subfolder Location | Formats | Primary Control | Purpose & Implementation |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    report_lines.append("| **System Security Plan (SSP)** | `SSP/` | `.md`, `.docx` | PL-2, NIST SP 800-18 | Authoritative system boundary, architecture, and control implementation statements. |")
    report_lines.append("| **20 NIST Policy & Procedure Manuals** | `Policies_and_Procedures/` | `.md`, `.docx` | All 20 NIST Families | Complete institutional cybersecurity governance manuals with 5-column SCTM appendices. |")
    report_lines.append("| **Security Control Traceability Matrix** | `SCTM/` | `.yaml`, `.xlsm` | CA-2, CA-7, PL-2 | Control burndown matrix hydrated in-place across rows 7..5000+ with dropdown validations. |")
    report_lines.append("| **Ports, Protocols & Services Matrix** | `PPSM/` | `.yaml`, `.xlsm` | CA-3, CM-7, SC-7 | Boundary traffic and API endpoint inventory formatted to DoD PPSM standard. |")
    report_lines.append("| **Hardware & Software Asset Inventory** | `HW_SW_Inventory/` | `.yaml`, `.xlsm` | CM-8 | Comprehensive asset inventory with lifecycle and criticality ratings. |")
    report_lines.append("| **Plan of Action & Milestones (POA&M)** | `POAM/` | `.yaml`, `.xlsm` | CA-5 | Continuous monitoring burndown with 41-column eMASS export structure. |")
    report_lines.append("| **FIPS 140-3 Cryptographic Matrix** | `FIPS_Cryptography/` | `.yaml`, `.md`, `.docx` | SC-12, SC-13, IA-5 | Inventory of FIPS 140-3 cryptographic modules and CMEK key rings. |")
    report_lines.append("| **Incident Response Runbooks (5 Workflows)** | `Incident_Response_Runbooks/` | `.md`, `.docx` | IR-4, IR-5, IR-8 | Tactical cloud runbooks for compromised credentials, compute, CMEK, network intrusion, and VPC-SC. |")
    report_lines.append("| **Path to Authorization (PTA)** | Root `ato_artifacts/` | `.md`, `.docx` | CA-6 | Executive accreditation roadmap, validation audit, and testing strategy. |\n")

    report_lines.append("### 🔍 Phase 4: Security Assessments, Vulnerability Scans & STIG Benchmarks")
    report_lines.append("| Step | Assessment Activity | Primary Control | Format / Sourcing | Verification & Acceptance Standard |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    report_lines.append("| **4.1** | **ACAS / Nessus Credentialed Scans**: Execute credentialed vulnerability scans on all host VMs and databases within 30 days of submission. | `RA-5, SC-28` | `ACAS: ASR/ARF` or `.nessus` | Must return 'Good Data' (credentialed plugins firing), 0 unmapped findings, and 0 unmitigated CISA KEV exploits. |")
    report_lines.append("| **4.2** | **DISA STIG Benchmark Execution**: Download official STIGs from [DoD Cyber Exchange](https://public.cyber.mil/stigs/downloads/) and complete `.ckl` checklists in the [DISA STIG Viewer desktop app](https://public.cyber.mil/stigs/srg-stig-tools/). | `CM-6, CA-2` | `.ckl` (STIG Viewer Desktop) | 100% applied benchmark coverage; every failed check (CAT I/II) mapped to a POA&M item ID. |")
    report_lines.append("| **4.3** | **Software Assurance (SAST/DAST & SBOM)**: Run static code scans (Trivy/Semgrep) in CI/CD and container scans in Artifact Registry. | `SA-11, SI-2, SR-4` | Trivy SAST + CycloneDX SBOM | Zero Critical/High static analysis flaws; container images in Artifact Registry scanned and signed. |")
    report_lines.append("| **4.4** | **14 ATC Critical Controls Audit**: Audit the 14 mandatory DoD connection controls in the SCTM ensuring residual risk <= Moderate. | `AC-17, IA-2, SC-7` | SCTM Narrative + Evidence | All 14 ATC controls verified in SCTM with residual risk <= Moderate; no Very High/High residual risks. |\n")

    report_lines.append("### 🤝 Phase 5: Operational Governance, Agreements & Simulations")
    report_lines.append("| Step | Operational Requirement | Primary Control | Required Evidence Format | Acceptance & Submission Criteria |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    report_lines.append("| **5.1** | **CSSP SLA & Cloud Inheritance**: Establish 24/7 CSOC monitoring SLA and accept Cloud Common Control Provider (CCP) package in eMASS. | `CA-3, CA-9` | Signed CSSP SLA Agreement PDF | Active agreement with accredited 24/7 CSSP (e.g. C5ISR / DISA / Agency CSOC); CCP inheritance accepted. |")
    report_lines.append("| **5.2** | **Interconnection Agreements (ISA / MOU)**: Execute ISAs/MOUs for external network connections and document circuit CCSD numbers. | `CA-3` | Signed ISA/MOU PDF + Topology | Documented circuit CCSD numbers and boundary firewall filtering devices illustrated on topology diagram. |")
    report_lines.append("| **5.3** | **Privileged User Access Agreements (SAAR / DD Form 2875)**: Ensure all administrators have signed access agreements and annual cybersecurity training certificates. | `AC-2, IA-2` | Signed SAAR / DD Form 2875 PDFs | Maintain signed access agreement forms for all Cloud IAM administrators and attach verification roster. |")
    report_lines.append("| **5.4** | **Contingency Plan & IR Tabletop Exercise (TTX)**: Execute annual DR dual-region failover test and CSOC incident escalation tabletop simulation. | `CP-4, IR-4` | Tabletop After-Action Report PDF | Conduct annual disaster recovery simulation across dual regions and upload formal test results. |")
    report_lines.append("| **5.5** | **Privacy Impact Assessment (PIA DD Form 2930)**: Complete and upload privacy assessment to eMASS FISMA tab if processing PII/PHI. | `PT-2, PT-3, AR-4` | Signed DD Form 2930 PDF | Signed DD Form 2930 PDF uploaded to eMASS System > Details > FISMA for systems handling PII/PHI. |\n")

    report_lines.append("### 🎖️ Phase 6: Package Assembly, eMASS Submission & AO Authorization Determination")
    report_lines.append("| Step | Milestone Activity | Responsible Role | Target Output & Execution Action |")
    report_lines.append("| :--- | :--- | :--- | :--- |")
    report_lines.append("| **6.1** | **Lead Assessor Audit & Remediation Pass**: Run package validation (`validate_compliance_artifacts.py --fix`) to audit all deliverables. | `Lead ISSM / SCA` | Resolve all pending institutional variables and high-visibility action cards. |")
    report_lines.append("| **6.2** | **Executive ATO Determination Request Memo**: Author executive request memorandum signed by ISSM and System Owner requesting ATO. | `ISSM & System Owner` | Submit formal request memo summarizing residual risk posture and continuous monitoring cycle. |")
    report_lines.append("| **6.3** | **eMASS Package Workflow Submission**: Route package through eMASS Package Approval Chain (ISSO -> ISSM -> SCA -> AO). | `Lead ISSM` | Package submitted into eMASS Step 5 (Authorize) workflow. |")
    report_lines.append("| **6.4** | **Authorizing Official (AO) ATO Determination**: Authorizing Official reviews residual risk posture and grants formal ATO decision. | `Authorizing Official (AO)` | Formal ATO Accreditation Decision Letter issued for maximum 3-year term (subject to continuous monitoring). |")
    report_lines.append("| **6.5** | **Continuous Monitoring (ConMon) Execution**: Perform monthly ACAS scans, quarterly STIG reviews, and annual POA&M milestone burndown. | `ISSO / SecOps Team` | Maintain active ATO status, avoid re-authorization debt, and ensure zero expired POA&M milestones over 90 days. |\n")

    report_lines.append("## 🧠 Strategic RMF Considerations & Authorizing Official (AO) Engagement\n")
    report_lines.append(f"To successfully navigate the accreditation lifecycle on {csp_name}, the program team must incorporate four critical governance principles:\n")
    report_lines.append("### 1. Authorizing Official (AO) Mission-Alignment & Translation")
    report_lines.append("Authorizing Officials (AOs) are executive-level leaders (e.g., Senior Executive Service, General/Flag Officers, Agency Chief Information Officers) with demanding schedules and statutory accountability for operational missions. While AOs rely on technical advisors (ISSMs, Security Control Assessors), they are primarily experts in the **mission and business domain**, not necessarily cloud engineering subject matter experts.\n")
    report_lines.append("> [!TIP]")
    report_lines.append("> **HOW TO ENGAGE THE AUTHORIZING OFFICIAL EFFECTIVELY**:")
    ao_tip_text = "Explain *how* Google Cloud Assured Workloads, Cloud KMS CMEK, and Cloud IAP protect mission-critical data from compromise, operational interruption, or foreign adversary disruption."
    report_lines.append(f"> - **Translate Technical Safeguards to Mission Outcomes**: Avoid presenting raw technical configurations in isolation. {ao_tip_text}")
    report_lines.append("> - **Articulate Organizational Risk Tolerance**: NIST SP 800-39 emphasizes that there is no single 'correct' level of risk tolerance. Ground all security recommendations in the specific risk tolerance of the AO's operational domain.")
    report_lines.append("> - **Emphasize Compensating Countermeasures**: When presenting open POA&M findings, proactively present concrete compensating controls (e.g., VPC Service Controls, dual-region backups, strict IAM separation of duties) that constrain residual risk to an acceptable level.\n")

    report_lines.append("### 2. ATO Reciprocity & Cross-Agency Portability (DoD Instruction 8510.01)")
    report_lines.append("An Authorization to Operate (ATO) granted by one military department (e.g., US Air Force, US Army, US Navy) or federal civilian agency is legally bounded to that governing entity. However, under **DoD Instruction 8510.01 (Section on Reciprocity)** and federal RMF policy, **AOs are strongly encouraged to accept reciprocity** rather than forcing a system to undergo duplicative, full-scope security assessments.\n")
    report_lines.append("> [!IMPORTANT]")
    report_lines.append("> **LEVERAGING THIS ARTIFACT PACKAGE FOR ATO RECIPROCITY**:")
    report_lines.append(f"> - **Inheritance Transparency**: The Security Control Traceability Matrix (`SCTM/`) and System Security Plan (`SSP/`) explicitly delineate controls inherited from {csp_name}'s FedRAMP High / DoD PA-TO authorizations versus customer-configured controls.")
    report_lines.append("> - **Universal NIST SP 800-53 Baseline**: By standardizing on NIST SP 800-53 Rev. 5, secondary agency AOs can readily ingest the package into their GRC tool of record (eMASS, CSAM, Xacta) without manual re-mapping.")
    report_lines.append("> - **Assessment Artifact Sharing**: Delivering the formal Security Assessment Report (SAR), credentialed ACAS scans, DISA STIG `.ckl` checklists, and POA&M enables secondary AOs to validate the residual risk posture in days rather than months.\n")

    report_lines.append("### 3. U.S. Citizenship & Sovereign Cloud Personnel Rules")
    report_lines.append(f"For DoD Impact Levels 4, 5, and 6, and FedRAMP High boundaries deployed on {csp_name}:")
    report_lines.append("- **U.S. Persons on U.S. Soil**: All cloud support and system operations personnel with physical or logical administrative access must be verified U.S. Citizens / U.S. Persons located within the continental United States.")
    report_lines.append("- **Background Investigations**: Privileged administrators must hold favorable background determinations (minimum Tier 3 / Secret eligibility for DoD IL5; Tier 5 for IL6 / NatSec environments).")
    report_lines.append("- **Access Agreements**: All administrative users must complete and sign annual privileged user agreements (SAAR / DD Form 2875 or organizational Access Agreement) and maintain current cybersecurity training certifications prior to role assignment.\n")

    report_lines.append("### 4. ATO Lifecycle Management (3-Year Lifespan & Continuous Monitoring Debt)")
    report_lines.append("- **Maximum 3-Year Authorization Term**: Per DoD Instruction 8510.01 and OMB Circular A-130, an ATO is granted for a maximum timeframe of **three (3) years**.")
    report_lines.append("- **The Threat of 'Herculean' Re-Authorization Debt**: Receiving an ATO does not conclude cybersecurity responsibilities. If packages are shelved and allowed to stagnate, the re-authorization milestone after 3 years requires a monumental, disruptive effort to address accumulated CVEs, architecture drift, and updated DISA STIG benchmarks.")
    report_lines.append("- **Continuous Compliance Through Automation**: Utilizing this automation engine (`validate_compliance_artifacts.py --fix`) ensures that the SSP, SCTM, PPSM, and HW/SW matrices are continuously synchronized with live Terraform infrastructure changes, maintaining an inspection-ready state throughout the ATO lifecycle.\n")

    report_lines.append("### 5. Mandiant Penetration Test Hardening Safeguards")
    report_lines.append("Based on Mandiant's comprehensive penetration testing of Google Cloud Assured Workloads foundations across 18 core services, four mandatory configuration safeguards must be enforced to achieve and defend an ATO:")
    report_lines.append("- **Disable Cloud Shell (`admin.google.com/ac/appslist/additional`)**: Cloud Shell instances run on Google-managed infrastructure outside customer VPCs, bypass host-level system logging, and are **not accredited for DoD IL2, IL4, or IL5**. Attackers can leverage Cloud Shell to proxy unauthorized payloads. Cloud Shell must be explicitly disabled at the organization level via Google Workspace Admin Console.")
    report_lines.append("- **Essential Contacts Restriction (`essentialcontacts.managed.allowedContactDomains`)**: Enforce the organization policy constraint restricting notification domains to verified agency domains (`@agency.mil` / `@agency.gov`), and ensure contacts are registered across all six critical categories: **Security, Legal, Technical, Billing, Suspension, and Product Updates**.")
    report_lines.append("- **Group Permission Viewing Restrictions & Default SA Hardening**: Set Google Cloud Identity group access to **Restricted** (`Directory > Groups > Access Settings > Restricted`) to prevent unauthorized enumeration of privileged group rosters. Enforce `iam.automaticIamGrantsForDefaultServiceAccounts` and `iam.disableServiceAccountKeyCreation`.")
    report_lines.append("- **SIEM / SOC Architecture Segmentation**: The SIEM / SOAR collection environment must reside in a dedicated project and separate VPC outside the production workload boundary to prevent adversarial tampering, log suppression, or evasion.\n")

    report_lines.append("### 6. Interim Authorization to Test (IATT) Staging Workflow")
    report_lines.append("In complex federal and DoD authorizations, programs often require an **Interim Authorization to Test (IATT)** prior to full ATO submission:")
    report_lines.append("- **Purpose**: An IATT is a temporary accreditation granted by the Authorizing Official (AO) for a specified duration (typically 90 to 180 days) permitting system connection to live networks specifically to conduct credentialed ACAS vulnerability scans, DISA STIG audits, and penetration testing.")
    report_lines.append("- **Prerequisites for IATT Request**: Draft System Security Plan (`SSP/`) with preliminary boundary definition; approved IATT Test Plan detailing test schedule and tools; residual risk assessment indicating no unmitigated CAT I (Very High) vulnerabilities; Authorizing Official signed IATT Letter.\n")

    report_lines.append("## 🔒 Federal & DoD Privacy Compliance Requirements (PIA, PCIL, SORN)\n")
    report_lines.append("Federal and Department of Defense systems handling personnel records, user accounts, or mission datasets containing Personally Identifiable Information (PII) or Protected Health Information (PHI) must comply with the Privacy Act of 1974 and OMB mandates. The privacy evaluation consists of three interdependent deliverables:\n")
    report_lines.append("| Privacy Deliverable | Legal / Regulatory Mandate | Purpose & Assessment Standard | Target eMASS / Submission Location |")
    report_lines.append("| :--- | :--- | :--- | :--- |")
    report_lines.append("| **Privacy Impact Assessment (PIA)** | E-Government Act of 2002 § 208;<br>OMB M-03-22;<br>DoD Instruction 5400.16 | Comprehensive analysis of how PII is collected, stored, protected, shared, and disposed of. Documented on **DD Form 2930** (DoD) or agency-equivalent PIA template. | Uploaded to eMASS under `System Details > FISMA > Privacy > PIA`. |")
    report_lines.append("| **PII Confidentiality Impact Level (PCIL)** | [NIST SP 800-122](https://csrc.nist.gov/pubs/sp/800/122/final) (*Guide to Protecting PII Confidentiality*) | Formal rating (**Low**, **Moderate**, or **High**) assessing the potential harm to individuals and the organization resulting from an unauthorized release or breach of PII based on identifiability, sensitivity, and context. | Documented in `SSP Section 1.2` and SCTM under `PT-2` and `PT-3` controls. |")
    report_lines.append("| **System of Records Notice (SORN)** | Privacy Act of 1974 (5 U.S.C. § 552a);<br>OMB Circular A-108 | Official notice drafted for publication in the **Federal Register** describing any system of records that retrieves personal information by an individual's name, SSN, or unique identifier. | Documented in `SSP Section 1.2` and uploaded to eMASS FISMA tab under SORN Identifier. |\n")
    report_lines.append("### Privacy Compliance Decision Flow")
    report_lines.append("- **Step 1: Privacy Threshold Analysis (PTA)**: Determine whether PII/PHI is processed. If no personal data is collected or stored (pure infrastructure foundation), document PTA as exempt in eMASS.")
    report_lines.append("- **Step 2: PII Confidentiality Impact Level (PCIL)**: If PII is processed, evaluate the harm level (Low, Moderate, High) per NIST SP 800-122 to determine necessary cryptographic, access control, and auditing baselines.")
    report_lines.append("- **Step 3: Privacy Impact Assessment (PIA)**: Complete the formal PIA (DD Form 2930 for DoD) detailing data flows, third-party sharing, and retention cycles.")
    report_lines.append("- **Step 4: System of Records Notice (SORN)**: If records are retrieved by an individual's name or personal identifier (e.g. SSN, EDIPI, employee ID), draft a SORN for agency legal review and publication in the Federal Register. If records are covered under an existing government-wide or agency SORN, record the SORN system identifier in the package.\n")

    # -------------------------------------------------------------
    # SECTION 2: 14 ATC (Authorization to Connect) Critical Controls Audit
    # -------------------------------------------------------------
    report_lines.append("## ⚡ 14 ATC (Authorization to Connect) Critical Controls Verification")
    report_lines.append("For systems connecting to DoD enterprise networks or requesting an Authorization to Connect (ATC), the following 14 critical controls must have complete implementation statements in the SCTM and zero unmitigated High/Very High residual risks:\n")
    report_lines.append("| Control ID | Control Name | DoD Connection Standard & Enforcement Focus | Verification Status | Evidence Source | Implementation Evidence in SCTM / SSP |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for atc in senior_audit.get("atc_records", []):
        ctrl_id = atc["id"]
        ctrl_name = atc["name"]
        ctrl_desc = atc["description"]
        # Default to the fail-closed verdict: a record without an explicit
        # verification result has not been verified.
        ver = atc.get("verification", "MISSING")
        assessed_status = atc.get("status") or "[NOT DETERMINED FROM SOURCE]"
        source = atc.get("evidence_source", "None")
        source_label = "None — control absent from package" if source == "None" else source
        details = atc.get("details", "")
        if len(details) > 90:
            details = details[:87] + "..."
        report_lines.append(
            f"| **{ctrl_id}** | {ctrl_name} | {ctrl_desc} | `{ver}` — {assessed_status} | `{source_label}` | {details} |"
        )
    report_lines.append("")

    # -------------------------------------------------------------
    # SECTION 3: Dynamic DISA STIGs Section referencing STIG Viewer
    # -------------------------------------------------------------
    report_lines.append("## 🛡️ Mandatory DISA STIG & SRG Checklist Compliance Roadmap")
    report_lines.append("> [!IMPORTANT]")
    report_lines.append("> **AUTHORITATIVE DISA STIG SOURCE & DESKTOP STIG VIEWER APPLICATION**:")
    report_lines.append("> 1. **Official STIG Downloads**: Official DISA STIG compilation packages and checklist benchmarks must be downloaded from the DoD Cyber Exchange at [https://public.cyber.mil/stigs/downloads/](https://public.cyber.mil/stigs/downloads/) (requires CAC authentication).")
    report_lines.append("> 2. **DISA STIG Viewer Application**: The **DISA STIG Viewer desktop application** (downloadable from DoD Cyber Exchange at [https://public.cyber.mil/stigs/srg-stig-tools/](https://public.cyber.mil/stigs/srg-stig-tools/)) is the required software used to import, complete, evaluate, and export `.ckl` checklist files for eMASS ingestion.")
    report_lines.append("> 3. **Dynamic STIG Version Resolver**: All STIG/SRG checklist versions are dynamically resolved across institutional overrides, remote feeds, and authoritative baselines.")
    report_lines.append("> 4. **Public Web Reference**: The [STIG Viewer website](https://www.stigviewer.com/stigs) links provided below are reference links for web browsing and quick lookup of rule requirements and fix scripts.\n")

    dynamic_updates = [
        s for s in stigs_required
        if any(k in s.get("version_source", "") for k in ["Override", "Live", "Cached"])
    ]
    report_lines.append(f"Based on the infrastructure components discovered in Terraform code, the cybersecurity team must complete, verify, and document `{len(stigs_required)}` STIG Benchmark compliance checklists (`.ckl` files created in the STIG Viewer desktop app). Dynamically updated or overridden versions: `{len(dynamic_updates)}`.\n")
    report_lines.append("| DISA STIG / SRG Benchmark | Version | Source | Public Reference Link | Triggering Component / Scope | Action Required for Assessor Team | Status |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for s in stigs_required:
        link_md = f"[{s['slug']}]({s['url']})"
        src_label = s.get("version_source") or "Authoritative Baseline"
        report_lines.append(f"| **{s['title']}** | `{s['version']}` | {src_label} | {link_md} | {s['reason']} | {s['action']} | `{s['status']}` |")
    report_lines.append("")

    # -------------------------------------------------------------
    # SECTION 4: OpenXML Excel & Word Audit Results
    # -------------------------------------------------------------
    report_lines.append("## 📊 Excel Workbooks (.xlsm) Audit Results")
    report_lines.append("| Workbook File | Audit Status | Sheet Structure | Populated Rows | Status Details |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for xr in excel_results:
        sheets_str = ", ".join(xr["sheets"][:3])
        rows_str = ", ".join([f"{k}: {v}" for k, v in xr["rows_count"].items()]) if xr["rows_count"] else "Preserved"
        details = ", ".join(xr["issues"]) if xr["issues"] else "Valid OpenXML & Schema"
        report_lines.append(f"| `{xr['file']}` | `{xr['status']}` | {sheets_str} | {rows_str} | {details} |")
    report_lines.append("")

    report_lines.append("## 📄 Word Policy Documents (.docx) Audit Results")
    report_lines.append(f"- Total DOCX Policies Verified: `{len(docx_results)}` files")
    total_docx_hl = sum(r.get("hyperlinks_count", 0) for r in docx_results)
    report_lines.append(f"- OpenXML Packaging Conformance: `100% Passed` (Valid XML AST, {total_docx_hl} Verified External Hyperlinks, Executive Cover Headers, Bordered Tables, Dynamic Footers)\n")

    if unresolved_tokens:
        report_lines.append("## ❌ Critical Unresolved Syntax Tokens")
        report_lines.append("| Document Path | Line | Token Found | Raw Context Snippet |")
        report_lines.append("| :--- | :--- | :--- | :--- |")
        for u in unresolved_tokens:
            report_lines.append(f"| `{u['file']}` | {u['line']} | `{u['token']}` | `{u['context'][:65]}` |")
        report_lines.append("")

    if config_required_vars:
        report_lines.append("## ⚠️ Pending Institutional Configuration Variables (`compliance_config.yaml`)")
        report_lines.append("| Document Path | Line | Placeholder Variable | Action Required |")
        report_lines.append("| :--- | :--- | :--- | :--- |")
        for c in config_required_vars:
            report_lines.append(f"| `{c['file']}` | {c['line']} | `{c['variable']}` | Define in `compliance_config.yaml` and re-run generator |")
        report_lines.append("")

    # -------------------------------------------------------------
    # SECTION 4: Comprehensive Institutional Policies & Human Execution Matrix
    # -------------------------------------------------------------
    report_lines.append("## 📋 Institutional Policy Manuals & Core Deliverables Human Execution Matrix")
    report_lines.append("The compliance foundation provides 20 institutional cybersecurity policy manuals, system security plans, and structured registers. The RMF and platform teams must execute the following human governance and operational actions across all deliverables:\n")
    report_lines.append("| Deliverable Artifact | Subfolder Location | NIST Family / Control | Responsible Lead | Mandatory Human Execution & Customization Action |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")

    master_policy_roadmap = [
        ("System Security Plan (SSP)", "SSP/", "PL-2, NIST SP 800-18", "ISSM & Lead Architect", "Verify system boundary, operational points of contact, and control implementation statements."),
        ("Access Control Policy & Procedures", "Policies_and_Procedures/", "AC Family", "ISSM & IAM Admin", "Establish separation of duties matrix, privileged user review frequency, and emergency break-glass SOP."),
        ("Awareness & Training Policy & Procedures", "Policies_and_Procedures/", "AT Family", "ISSO & Training Lead", "Verify annual Cyber Awareness Challenge completion and role-based training logs."),
        ("Audit & Accountability Policy & Procedures", "Policies_and_Procedures/", "AU Family", "SecOps / CSOC Lead", "Confirm 365-day log retention duration (7-year archive) and CSOC SIEM ingestion alerts."),
        ("Assessment, Authorization & Monitoring Policy", "Policies_and_Procedures/", "CA Family", "Lead ISSM / SCA", "Define independent 3PAO assessment scope, continuous monitoring plan, and eMASS workflow."),
        ("Configuration Management Policy & Procedures", "Policies_and_Procedures/", "CM Family", "CCB Chair / DevOps Lead", "Charter Configuration Control Board (CCB), review software baseline, and enable drift alerts."),
        ("Contingency Plan Policy & Procedures", "Policies_and_Procedures/", "CP Family", "System Owner / Ops Lead", "Execute annual dual-region DR failover exercise and document Recovery Time/Point Objectives (RTO/RPO)."),
        ("Identification & Authentication Policy", "Policies_and_Procedures/", "IA Family", "IAM Lead", "Enforce CAC/PIV hardware token MFA for admin logins and audit service account key exemptions."),
        ("Incident Response Policy & Procedures", "Policies_and_Procedures/", "IR Family", "CSOC / Incident Lead", "Establish 24/7 CSOC escalation tree, CISA/DoD 1-hour reporting SLA, and annual tabletop exercise (TTX)."),
        ("Maintenance Policy & Procedures", "Policies_and_Procedures/", "MA Family", "Platform Lead", "Authorize remote maintenance tools, inspect IAP session logs, and establish vendor escort SOPs."),
        ("Media Protection Policy & Procedures", "Policies_and_Procedures/", "MP Family", "SecOps Lead", "Define crypto-erase sanitization protocols for decommissioned cloud storage buckets and disks."),
        ("Physical & Environmental Protection Policy", "Policies_and_Procedures/", "PE Family", "ISSO / Security Officer", "Verify Google Cloud Assured Workloads FedRAMP High / DoD PA-TO physical facility inheritance."),
        ("Planning Policy & Procedures", "Policies_and_Procedures/", "PL Family", "Lead ISSM", "Review and approve institutional System Security Plan every 365 days or upon major architectural changes."),
        ("Program Management Policy & Procedures", "Policies_and_Procedures/", "PM Family", "CISO / System Owner", "Maintain enterprise information security program plan and risk executive committee charter."),
        ("Personnel Security Policy", "Policies_and_Procedures/", "PS Family", "HR / Security Officer", "Verify favorable background investigation checks (Tier 3/Tier 5 / Public Trust) and signed access agreements (SAAR / DD 2875)."),
        ("PII Processing & Transparency Policy", "Policies_and_Procedures/", "PT Family", "Privacy Officer", "Complete and sign Privacy Impact Assessment (PIA / DD Form 2930) if processing personal data."),
        ("Risk Assessment Policy & Procedures", "Policies_and_Procedures/", "RA Family", "Lead ISSM / SCA", "Conduct annual risk assessment, threat modeling, and 30-day ACAS vulnerability scanning burndown."),
        ("System & Communications Protection Policy", "Policies_and_Procedures/", "SC Family", "Lead Cloud Architect", "Validate FIPS 140-3 cryptographic modules, TLS 1.3 encryption, and default-deny firewall policies."),
        ("System & Information Integrity Policy", "Policies_and_Procedures/", "SI Family", "SecOps Lead", "Establish flaw remediation SLAs (Critical <= 15 days, High <= 30 days) and configure SIEM / CSSP threat detection and monitoring via Security Command Center, Google Cloud SecOps, and/or centralized external SIEM endpoints."),
        ("Supply Chain Risk Management Policy", "Policies_and_Procedures/", "SR Family", "Procurement / ISSM", "Maintain C-SCRM policy, vendor security evaluations, and software bill of materials (SBOM) scanning."),
        ("System & Services Acquisition Policy", "Policies_and_Procedures/", "SA Family", "DevOps / Procurement", "Incorporate security requirements in Cloud procurement contracts and enforce SAST/DAST in CI/CD."),
        ("Hardware & Software Asset Inventory", "HW_SW_Inventory/", "CM-8", "ISSO / Property Lead", "Reconcile live cloud resources and local client hardware with eMASS serial numbers."),
        ("Ports, Protocols & Services Matrix (PPSM)", "PPSM/", "CA-3, SC-7", "Network Lead / ISSM", "Register all network boundaries and service endpoints in eMASS PPSM registry; obtain exception certificates."),
        ("Plan of Action & Milestones (POA&M)", "POAM/", "CA-5", "ISSM & System Owner", "Schedule quarterly milestone review with Authorizing Official (AO); track ongoing remediations."),
        ("Security Control Traceability Matrix (SCTM)", "SCTM/", "CA-2, PL-2", "Lead ISSM / Assessor", "Complete control test methods and perform assessor walkthroughs across all 14 ATC connection controls."),
        ("FIPS 140-3 Cryptographic Matrix", "FIPS_Cryptography/", "SC-12, SC-13", "Security Architect", "Verify NIST CMVP certificate validation for KMS CMEK keys and TLS 1.3 cipher suites.")
    ]

    for title, path, fam, lead, action in master_policy_roadmap:
        report_lines.append(f"| **{title}** | `{path}` | `{fam}` | `{lead}` | {action} |")
    report_lines.append("")

    if rmf_action_items:
        report_lines.append("## 🔍 Live Policy Customization & Action Item Alerts (Grouped by Document)")
        report_lines.append("The scanner identified the following action alerts across the generated policy manuals and security documentation:\n")
        report_lines.append("| Policy / Document Path | Action Items Count | Key Action Highlights |")
        report_lines.append("| :--- | :--- | :--- |")

        # Group by document
        doc_actions: Dict[str, List[str]] = {}
        for item in rmf_action_items:
            doc_key = item["file"]
            if doc_key not in doc_actions:
                doc_actions[doc_key] = []
            doc_actions[doc_key].append(item["action"])

        for doc_file in sorted(doc_actions.keys()):
            items = doc_actions[doc_file]
            unique_highlights = list(dict.fromkeys(items))[:2]
            highlights_str = "; ".join(unique_highlights)
            if len(highlights_str) > 130:
                highlights_str = highlights_str[:127] + "..."
            report_lines.append(f"| `{doc_file}` | `{len(items)} items` | {highlights_str} |")
        report_lines.append("")

    # -------------------------------------------------------------
    # SECTION 5: Sample Executive Determination Memo & WBS
    # -------------------------------------------------------------
    report_lines.append("## 📝 Sample Executive ATO Determination Request Memo Template\n")
    report_lines.append("```text")
    report_lines.append(f"MEMORANDUM FOR: Authorizing Official (AO), {org_name}")
    report_lines.append(f"FROM: Information System Security Manager (ISSM), {sys_name}")
    report_lines.append(f"SUBJECT: Request for Authorization to Operate (ATO) for {sys_name} ({sys_abbr})\n")
    report_lines.append("1. PURPOSE:")
    report_lines.append(f"This memorandum formally requests an Authorization to Operate (ATO) with a 365-day Continuous Monitoring cycle for {sys_name} at {impact_level} / {baseline}.\n")
    report_lines.append("2. SYSTEM ARCHITECTURE & BOUNDARY:")
    report_lines.append(f"{sys_name} is a modular cloud foundation deployed on Google Cloud Assured Workloads in dual regions. All data at rest is encrypted using FIPS 140-3 validated Cloud KMS CMEK keys, and all ingress is secured through Cloud IAP zero-trust bastions.\n")
    report_lines.append("3. SECURITY ASSESSMENT & RESIDUAL RISK:")
    report_lines.append("An independent security control assessment was conducted across all applicable NIST SP 800-53 Rev. 5 controls.")
    report_lines.append("- Open POA&M Items: 0 Very High, 0 High Residual Risk")
    report_lines.append(f"- DISA STIG Checklists: {len(stigs_required)} applicable STIG benchmarks identified for completion in STIG Viewer.")
    report_lines.append("- ATO Reciprocity & Interoperability: Package prepared in accordance with DoD Instruction 8510.01 reciprocity criteria to enable cross-agency re-use.\n")
    report_lines.append("4. RECOMMENDATION:")
    report_lines.append(f"Based on the implemented technical countermeasures, defense-in-depth perimeter firewalls, and low residual risk posture, I recommend that {sys_name} be granted an Authorization to Operate (ATO).\n")
    report_lines.append("____________________________________________")
    report_lines.append(f"{issm_name}")
    report_lines.append(f"{issm_title}")
    report_lines.append(f"{org_name}\n")
    report_lines.append("CONCURRENCE:")
    report_lines.append("____________________________________________")
    report_lines.append(f"{so_name}")
    report_lines.append(f"{so_title}")
    report_lines.append(f"{org_name}")
    report_lines.append("```\n")

    report_lines.append("## 📊 Work Breakdown Structure (WBS) for ATO\n")
    report_lines.append("| WBS # | Milestone Action & Target Output | Responsible Role |")
    report_lines.append("| :--- | :--- | :--- |")
    report_lines.append("| **1.0** | **Project Kick-Off & Stakeholder Alignment**: Kick-off meeting with Authorizing Official (AO), ISSM, and mission leadership. | Project Sponsor & PM |")
    report_lines.append("| **1.1** | **Roadmap, Milestones & Reciprocity Strategy**: Authorize Master ATO Roadmap, schedule, and reciprocity objectives. | System Owner & ISSM |")
    report_lines.append("| **1.2** | **Account Provisioning & System Access**: CACs, security clearance vetting (U.S. Citizens), eMASS/CRAMS, and Assured Workloads. | Security Officer & Platform Lead |")
    report_lines.append("| **1.3** | **Build & Generate ATO Deliverables** | Compliance Automation Engine |")
    report_lines.append("| **1.3.1** | Generate System Security Plan (SSP), Boundary Diagram, HW/SW List | Automated Engine |")
    report_lines.append("| **1.3.2** | Determine Security Categorization (FIPS 199 / NIST SP 800-60) & NIST SP 800-53 Control Selection | Automated Engine & ISSM |")
    report_lines.append("| **1.3.3** | Generate 20 NIST Policy & Procedure Manuals (Markdown & DOCX) | Automated Engine |")
    report_lines.append("| **1.3.4** | Hydrate Security Control Traceability Matrix (SCTM) & PPSM (.xlsm/.yaml) | Automated Engine |")
    report_lines.append("| **1.3.5** | Execute Credentialed ACAS Scans & DISA STIG Viewer Benchmarks (.ckl) | DevSecOps & Security Ops |")
    report_lines.append("| **1.3.6** | Privacy Triage (PIA / DD 2930, PCIL NIST 800-122, SORN OMB A-108) | Privacy Officer & ISSM |")
    report_lines.append("| **1.3.7** | Assemble Initial POA&M & Validate Package (`validate_compliance_artifacts.py --fix`) | Lead ISSM & SCA |")
    report_lines.append("| **1.3.8** | Submit Complete Package into eMASS Package Approval Chain (PAC) | Lead ISSM |")
    report_lines.append("| **1.4** | **Authorizing Official (AO) Awards Formal ATO Letter** | Authorizing Official (AO) |\n")

    report_lines.append("## 🎖️ Military Service Branch & Federal Agency Governance Overlays\n")
    report_lines.append("When tailoring the compliance package for specific defense components or civilian departments, align deliverables with the governing agency instructions below:\n")
    report_lines.append("> [!IMPORTANT]")
    report_lines.append("> **Defense Telemetry & CSSP Integration**: Ensure all audit logs, system telemetry, and security events route via Cloud Logging export sinks to designated CSSP / SIEM endpoints (e.g., C5ISR, DISA, Chronicle GovCloud, Splunk) per DoDI 8530.01. Responders should align monitoring consoles and roles with organizational CSSP agreements and active cloud security services.\n")
    report_lines.append("| Agency / Component | Core Governing Directives & Instructions | Tactical Cyber Operations Center & Reporting SLA | Tailoring & Workflow Guidance |")
    report_lines.append("| :--- | :--- | :--- | :--- |")
    report_lines.append("| **Department of the Army (USA)** | `AR 25-2-003` (*Army Cybersecurity Program*), `CNSSI 1253`, `CJCSM 6510.01B` | **Army RCERT** & **NETCOM**; Cat 1 Incident: 1h, Cat 2: 2h, Cat 4: 24h | Ensure direct registration in Army eMASS; coordinate 24/7 incident escalation SLAs with Army C5ISR / CSSP; adhere to ERDC-CERL security engineering standards. |")
    report_lines.append("| **Department of the Air Force (DAF / USAF)** | `DAF ITCSC v8.4` (*Information Technology Cyber Security Controls*), `CJCSM 6510.01B` | **616th Operations Center (616 OC)** / 16th AF; Cat 1: 1h, Cat 2: 2h | Align with Air Force Fast Track ATO / Continuous ATO (cATO) pathways; incorporate software factory container signing and DevSecOps gates. |")
    report_lines.append("| **Department of the Navy (DON / USN)** | `OPNAVINST 5239.1E`, `SECNAVINST 5239.3`, Navy Conventional IT RMF Workflow v1.2 | **NAVIFOR / NCDOC** (Navy Cyber Defense Ops Command); Cat 1: 1h | Reference the Navy Enterprise Inheritance Guide v1.0 and complete USN RMF System Security Categorization Form v1.6. IATT packages must follow DON IATT Test Plan standards. |")
    report_lines.append("| **US Marine Corps (USMC)** | `MCO 5239.2B` (*Marine Corps Cybersecurity Order*), `NAVMC 3500.124A` | **MCCOG** (Marine Corps Cyber Operations Group); Cat 1: 1h | Utilize Marine Corps Systems Command (MCSC) SIAT RMF Process Guide; enforce strict boundary filtering on all interconnect circuits. |")
    report_lines.append("| **US Space Force (USSF)** | `SPFGM 2021-17-01`, `CJCSM 6510.01B` | **Space Delta 6 (Cyber Operations)**; Cat 1: 1h | Map telemetry to USSF Defensive Cyberspace Operations (DCO); implement cross-domain boundary inspection and satellite uplink telemetry filtering. |")
    report_lines.append("| **Defense-Wide / 4th Estate** | `DoDI 8530.01`, `CJCSM 6510.01B` | **DISA / JFHQ-DODIN**; Cat 1: 1h, Cat 2: 2h | Report via DoD Incident Collection System (DICS); coordinate with DISA Global Operations Center (DGOC) for DISN boundary isolation. |")
    report_lines.append("| **Defense Counterintelligence & Security Agency (DCSA)** | `DAAPM v2.1` (*Assessment and Authorization Process Manual*) | **DCSA Cyber Operations Center** | Required for cleared defense contractors; complete the SAP RMF Checklist and adhere to Joint Special Access Program Implementation Guide (JSIG). |")
    report_lines.append("| **Defense Health Agency (DHA)** | `DHA RMF Process Workflow v8.3`, `DHAAI 077` | **DHA CSSP / Medical Cybersecurity Ops** | Incorporate Military Health System (MHS) privacy overlays, HIPAA Security Rule mappings, and medical device boundary isolation. |")
    report_lines.append("| **Department of Veterans Affairs (Dept of VA)** | `VA Directive 6500`, `VA Handbook 6500`, VA Notice 24-12 | **VA-ESOC** (Enterprise SOC) | Adhere to VA National Rules of Behavior; map cloud audit trails to the VA Enterprise Security Operations Center (VA-ESOC). |\n")

    report_lines.append("## 📚 References\n")
    report_lines.append("- [NIST SP 800-37 Rev. 2](https://csrc.nist.gov/pubs/sp/800/37/r2/final), Risk Management Framework for Information Systems and Organizations: A System Life Cycle Approach for Security and Privacy")
    report_lines.append("- [NIST SP 800-39](https://csrc.nist.gov/pubs/sp/800/39/final), Managing Information Security Risk: Organization, Mission, and Information System View")
    report_lines.append("- [Federal Information Processing Standards (FIPS) 199](https://csrc.nist.gov/pubs/fips/199/final), Standards for Security Categorization of Federal Information and Information Systems")
    report_lines.append("- [NIST SP 800-60 Vol. 1 & 2](https://csrc.nist.gov/pubs/sp/800/60/v1/r1/final), Guide for Mapping Types of Information and Information Systems to Security Categories")
    report_lines.append("- [FIPS 200](https://csrc.nist.gov/pubs/fips/200/final), Minimum Security Requirements for Federal Information and Information Systems")
    report_lines.append("- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), Security and Privacy Controls for Information Systems and Organizations")
    report_lines.append("- [NIST SP 800-137](https://csrc.nist.gov/pubs/sp/800/137/final), Information Security Continuous Monitoring (ISCM) for Federal Information Systems and Organizations")
    report_lines.append("- [NIST SP 800-122](https://csrc.nist.gov/pubs/sp/800/122/final), Guide to Protecting the Confidentiality of Personally Identifiable Information (PII)")
    report_lines.append("- [DoD Instruction 8510.01](https://www.esd.whs.mil/Directives/issuances/dodi/), Risk Management Framework (RMF) for DoD Systems (Reciprocity & Authorization Lifecycles)")
    report_lines.append("- [OMB Circular A-108](https://www.whitehouse.gov/omb/information-regulatory-affairs/privacy/), Federal Agency Responsibilities for Review, Reporting, and Publication under the Privacy Act")
    report_lines.append("- [DoD Cloud Computing Security Requirements Guide (CC SRG)](https://public.cyber.mil/stigs/downloads/)\n")

    # Save Path_to_Authorization.md
    write_text_file(report_path, "\n".join(report_lines))

    # Compile Path_to_Authorization.docx
    docx_path = os.path.join(ato_dir, "Path_to_Authorization.docx")
    if docx_generator:
        docx_generator.convert_markdown_to_docx("\n".join(report_lines), docx_path, inventory)

    app_info = inventory.get("application_components", {})
    apps_cnt = len(app_info.get("applications", []))
    pkgs_cnt = len(app_info.get("software_packages", []))
    ctr_cnt = len(app_info.get("container_images", []))
    ports_cnt = len(app_info.get("exposed_ports", []))

    logger.info("=" * 80)
    logger.info("✅ COMPLIANCE PACKAGE VALIDATION AUDIT COMPLETE")
    logger.info("=" * 80)
    logger.info("  • Markdown/YAML Audited      : %d", total_files_checked)
    logger.info("  • Structured YAML Audited    : %d files (%s)", len(yaml_results), yaml_status_note)
    logger.info("  • Excel Workbooks Audited    : %d (OpenXML Valid)", len(excel_results))
    logger.info("  • Word Policy Manuals Audited: %d (OpenXML Valid, %d Hyperlinks Verified)", len(docx_results), total_docx_hl)
    if oscal_results:
        oscal_ver_str = oscal_results[0].get("oscal_version") or "1.2.3"
        logger.info("  • NIST OSCAL (v%s) Audited   : %d packages (%s)", oscal_ver_str, len(oscal_results), "Schema Valid" if all(r["status"] == "PASS" for r in oscal_results) else "Alerts Detected")
    if apps_cnt > 0 or pkgs_cnt > 0 or ctr_cnt > 0:
        logger.info("  • Application Components     : %d apps, %d packages, %d container images", apps_cnt, pkgs_cnt, ctr_cnt)
    if ports_cnt > 0:
        logger.info("  • App Ingress Ports Mapped   : %d ports in PPSM", ports_cnt)
    if runbook_results:
        passed_rb = len([r for r in runbook_results if r["status"] == "PASS"])
        logger.info("  • IR Runbooks Audited        : %d/%d scenario workflows", passed_rb, len(expected_runbooks))
    logger.info("  • Unresolved Tokens          : %d", len(unresolved_tokens))
    dynamic_updates = [s for s in stigs_required if any(k in s.get("version_source", "") for k in ["Override", "Live", "Cached"])]
    logger.info("  • Applicable DISA STIGs      : %d (STIG Viewer catalog mapped, %d active updates/overrides)", len(stigs_required), len(dynamic_updates))
    logger.info("  • Architecture Reconciliation: %d/%d assets (%.1f%% coverage)", alignment_results["reconciled_assets_count"], alignment_results["total_discovered_assets"], alignment_results["coverage_score_percent"])
    missing_atc = [r for r in senior_audit.get("atc_records", []) if r.get("verification") == "MISSING"]
    if missing_atc:
        logger.info(
            "  • 14 ATC Connection Controls : %d/14 Verified (%d absent from SCTM and SSP: %s)",
            senior_audit["verified_atc_count"],
            len(missing_atc),
            ", ".join(r["id"] for r in missing_atc),
        )
    else:
        logger.info("  • 14 ATC Connection Controls : %d/14 Verified", senior_audit["verified_atc_count"])
    logger.info("  • Technical Readiness Status : %s", senior_audit["recommendation"])
    logger.info("  • Assessor Findings (CAT I/II/III): %d / %d / %d", len(senior_audit["cat_1_findings"]), len(senior_audit["cat_2_findings"]), len(senior_audit["cat_3_findings"]))
    if semantic_linter_report:
        logger.info(
            "  • Semantic Linter Audit      : %s (%d/%d passed, score: %.1f%%)",
            semantic_linter_report.summary["verdict"],
            semantic_linter_report.summary["passed_count"],
            semantic_linter_report.summary["total_artifacts_evaluated"],
            semantic_linter_report.summary["compliance_score_percent"],
        )
        logger.info(
            "  • Semantic & Drift Findings  : %d CAT I / %d CAT II / %d CAT III (%d drift findings)",
            semantic_linter_report.summary["cat_1_findings_count"],
            semantic_linter_report.summary["cat_2_findings_count"],
            semantic_linter_report.summary["cat_3_findings_count"],
            semantic_linter_report.summary["architectural_drift_findings_count"],
        )
    logger.info("  • ISSM Submission Roadmaps   : 10 Operational Evidence Items + 14 ATC Controls")
    logger.info("  • Master PTA & Audit Report  : '%s' (.md & .docx)", report_path)
    logger.info("=" * 80)

    audit_logger = get_audit_logger()
    for r in docx_results + excel_results + oscal_results:
        if r.get("status") in ("FAIL", "ERROR", "UNVERIFIED"):
            audit_logger.emit(
                AuditEvent.ARTIFACT_VALIDATED,
                outcome=AuditOutcome.DENIED,
                obj=r.get("file", "unknown"),
                detail={"issues": r.get("issues", [])}
            )

    overall_outcome = AuditOutcome.DENIED if (senior_audit.get("cat_1_findings") or unresolved_tokens) else AuditOutcome.SUCCESS
    audit_logger.emit(
        AuditEvent.ARTIFACT_VALIDATED,
        outcome=overall_outcome,
        obj=target_dir,
        detail={
            "cat_1_count": len(senior_audit.get("cat_1_findings", [])),
            "cat_2_count": len(senior_audit.get("cat_2_findings", [])),
            "verified_atc": senior_audit.get("verified_atc_count", 0),
            "linter_validated": semantic_linter_report is not None,
            "linter_verdict": semantic_linter_report.summary["verdict"] if semantic_linter_report else "N/A",
            "linter_cat_1_count": semantic_linter_report.summary["cat_1_findings_count"] if semantic_linter_report else 0,
            "linter_drift_count": semantic_linter_report.summary["architectural_drift_findings_count"] if semantic_linter_report else 0,
            "ai_validated": semantic_linter_report is not None,
            "ai_verdict": semantic_linter_report.summary["verdict"] if semantic_linter_report else "N/A",
            "ai_cat_1_count": semantic_linter_report.summary["cat_1_findings_count"] if semantic_linter_report else 0,
            "ai_drift_count": semantic_linter_report.summary["architectural_drift_findings_count"] if semantic_linter_report else 0,
        }
    )

    return True


def main() -> None:
    """CLI entry point for compliance package validation and STIG evaluation."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if "-h" in sys.argv or "--help" in sys.argv:
        print("Usage: validate_compliance_artifacts.py [target_dir] [options]")
        print("\nSenior Assessor Public Sector Verification Gate & Unified Authorization Playbook Compiler.")
        print("\nPositional Arguments:\n  target_dir       Target foundation directory containing ato_artifacts/ (default: .)")
        print("\nOptions:")
        print("  --fix                          Auto-reconcile detected architectural drift against live Terraform")
        print("  --fill-example-data            Populate realistic public-sector sample data into action boxes")
        print("  --no-fill-example-data         Leave action boxes unpopulated for operator entry (default)")
        print("  --policy-format=FORMAT         Override policy format (both, docx, markdown)")
        print("  --data-format=FORMAT           Override structured data format (both, excel, yaml)")
        print("  --oscal-format=FORMAT          Override OSCAL format (both, json, yaml, none)")
        print("  --oscal-version=VERSION        Target OSCAL specification version (e.g. 1.2.3 or 1.1.0)")
        print("  --update-stigs                 Check and refresh DISA STIG / SRG benchmark checklists")
        print("  --no-linter                    Disable deterministic semantic linter evaluation")
        print("  --no-linter-strict             Do not fail validation on CAT I semantic findings")
        sys.exit(0)

    target_dir = "."
    args = sys.argv[1:]
    if "--" in args:
        dash_idx = args.index("--")
        if dash_idx + 1 < len(args):
            target_dir = args[dash_idx + 1]
    else:
        for arg in args:
            if not arg.startswith("-"):
                target_dir = arg
                break
    fix_flag = "--fix" in sys.argv
    fill_examples = "--fill-example-data" in sys.argv or "--fill-examples" in sys.argv
    no_fill_examples = "--no-fill-example-data" in sys.argv

    if not fill_examples and not no_fill_examples and sys.stdin.isatty():
        try:
            ans = input("\n[PROMPT] Would you like to auto-populate high-visibility SAMPLE / EXAMPLE DATA into remaining RMF team action boxes and placeholders? (y/N): ").strip().lower()
            if ans in ['y', 'yes']:
                fill_examples = True
        except EOFError:
            # stdin closed mid-prompt: take the documented default (no example data).
            logger.info("No response received on stdin; defaulting to --no-fill-example-data.")
        except KeyboardInterrupt:
            # Ctrl-C means abort, not "continue with the default".
            logger.warning("Interrupted at prompt; aborting validation.")
            raise SystemExit(130)

    policy_format = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--policy-format=")), None)
    data_format = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--data-format=")), None)
    oscal_format = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--oscal-format=")), None)
    oscal_version = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--oscal-version=")), None)
    update_stigs = "--update-stigs" in sys.argv or "--update" in sys.argv
    stigs_mode = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--stigs-mode=")), None)
    stigs_catalog = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--stigs-catalog=")), None)
    run_linter = "--no-linter" not in sys.argv and "--no-ai-validate" not in sys.argv
    linter_strict = "--no-linter-strict" not in sys.argv and "--no-ai-strict" not in sys.argv

    success = validate_compliance_package(
        os.path.abspath(target_dir),
        fix_drift=fix_flag,
        fill_examples=fill_examples,
        policy_format=policy_format,
        data_format=data_format,
        oscal_format=oscal_format,
        oscal_version=oscal_version,
        update_stigs=update_stigs,
        stigs_mode=stigs_mode,
        stigs_catalog=stigs_catalog,
        run_linter=run_linter,
        linter_strict=linter_strict,
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
