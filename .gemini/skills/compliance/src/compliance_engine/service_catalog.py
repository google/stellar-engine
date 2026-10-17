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

"""GCP service catalog loader.

Maps GCP service API domains (*.googleapis.com) to a category, display name, and
purpose string used in the SSP and the hardware/software inventory.

Resolution order (see :func:`resolve_gcp_service`):
1. ``custom_services`` passed by the caller (``compliance_config.yaml`` values carried
   in ``system_inventory.json``).
2. The declarative catalog in ``config/gcp_service_catalog.yaml``.
3. Token-anchored keyword heuristics for services in neither, and a neutral label
   when no keyword matches.
"""

import logging
import os
from typing import Any, Dict, Final, Optional, Tuple

from .file_helpers import get_skill_root, read_yaml_file

logger = logging.getLogger(__name__)

DEFAULT_CATALOG_PATH = str(get_skill_root() / "config" / "gcp_service_catalog.yaml")

_CACHED_CATALOG: Optional[Dict[str, Dict[str, str]]] = None

#: Qualifiers that carry no classification signal and are stripped from a token
#: before matching, so that e.g. ``cloudkms`` is matched on ``kms``.
_TOKEN_QUALIFIER_PREFIXES: Final[Tuple[str, ...]] = ("cloud", "google")

#: Ordered heuristic classification table for GCP service APIs that are absent
#: from both the declarative catalog and any user-supplied overrides.
#:
#: Each entry is ``(keywords, category, display-name suffix, purpose)``. Order is
#: significant: the first matching entry wins, so narrower domains precede broader
#: ones. Keywords are matched against *tokens*, never as free substrings -- an
#: unanchored ``"ai"`` previously classified ``retail`` as AI/ML, and ``"log"``
#: classified ``dialogflow`` and ``datacatalog`` as Observability.
_HEURISTIC_CATEGORIES: Final[Tuple[Tuple[Tuple[str, ...], str, str, str], ...]] = (
    (
        ("ai", "ml", "genai", "vertex", "gemini", "translate", "speech", "vision"),
        "AI & Machine Learning",
        " (AI/ML)",
        "Machine Learning & Artificial Intelligence Platform API",
    ),
    (
        ("db", "sql", "spanner", "datastore", "firestore", "bigtable", "alloydb"),
        "Database Management",
        " Database",
        "Managed Cloud Database & Persistence Service",
    ),
    (
        ("net", "dns", "vpc", "interconnect", "router", "nat", "firewall"),
        "Network & Connectivity",
        "",
        "Software-Defined Network Connectivity & Routing",
    ),
    (
        ("sec", "iam", "kms", "auth", "guard", "shield", "cert"),
        "Security & Access Control",
        "",
        "Security Posture, Cryptography & Access Control",
    ),
    (
        ("log", "mon", "trace", "telemetry", "audit", "metric"),
        "Observability & Audit",
        "",
        "Centralized Monitoring, Logging & Observability",
    ),
    (
        ("storage", "bucket", "file", "drive"),
        "Storage & Persistence",
        "",
        "Cloud Object & File Storage Persistence",
    ),
    (
        ("compute", "container", "k8s", "run", "function", "batch"),
        "Compute & Workload Execution",
        "",
        "Cloud Compute & Workload Scheduling Runtime",
    ),
)


def _match_tokens(tokens: Tuple[str, ...], keywords: Tuple[str, ...]) -> bool:
    """Reports whether any token is, or begins with, one of ``keywords``.

    Matching is anchored to the start of a token rather than performed anywhere
    in the service name. Free substring matching produces confidently wrong
    classifications that then propagate into the SSP and HW/SW inventory as if
    they were derived facts.

    Args:
        tokens: Normalized service-name tokens.
        keywords: Candidate keywords for one classification.

    Returns:
        True when at least one token matches at a token boundary.
    """
    return any(token.startswith(keyword) for token in tokens for keyword in keywords)


def _infer_category(prefix: str) -> Optional[Tuple[str, str, str]]:
    """Classifies an unmapped service name against the heuristic table.

    Args:
        prefix: Service name with the ``.googleapis.com`` suffix removed and
            separators normalized to spaces.

    Returns:
        A ``(category, display-name suffix, purpose)`` triple, or None when no
        entry matches -- in which case the caller must emit a neutral,
        non-committal classification rather than guess.
    """
    raw_tokens = [t for t in prefix.lower().split() if t]
    tokens = list(raw_tokens)
    for token in raw_tokens:
        for qualifier in _TOKEN_QUALIFIER_PREFIXES:
            if token.startswith(qualifier) and len(token) > len(qualifier):
                tokens.append(token[len(qualifier):])
    frozen = tuple(tokens)
    for keywords, category, name_suffix, purpose in _HEURISTIC_CATEGORIES:
        if _match_tokens(frozen, keywords):
            return (category, name_suffix, purpose)
    return None


def parse_simple_yaml_services(filepath: str) -> Dict[str, Dict[str, str]]:
    """Loads the service catalog YAML into a domain -> attributes mapping.

    The file is parsed only through :func:`file_helpers.read_yaml_file`, which applies
    the size and alias budgets. A file that fails to load is reported at WARNING
    level and yields an empty catalog, so every service then goes through the
    heuristic classification instead of a partially parsed catalog.

    Args:
        filepath: Path to the service catalog YAML configuration file.

    Returns:
        A dictionary mapping service API domains to their metadata attributes, or an
        empty dictionary when the file is missing or cannot be parsed.
    """
    services: Dict[str, Dict[str, str]] = {}
    if not os.path.exists(filepath):
        logger.warning("Service catalog %s not found; using heuristic classification only", filepath)
        return services

    try:
        data = read_yaml_file(filepath)
    except (OSError, ValueError) as err:
        logger.warning("Service catalog %s could not be loaded (%s); using heuristic classification only", filepath, err)
        return services

    raw_services = data.get("services", data)
    if isinstance(raw_services, dict):
        for svc_domain, svc_attrs in raw_services.items():
            if isinstance(svc_attrs, dict):
                services[str(svc_domain)] = {str(k): str(v) for k, v in svc_attrs.items()}
    return services


def get_service_catalog() -> Dict[str, Dict[str, str]]:
    """Retrieves the loaded and cached GCP service catalog dictionary.

    Returns:
        A cached dictionary mapping service domain names to classification metadata.
    """
    global _CACHED_CATALOG
    if _CACHED_CATALOG is None:
        _CACHED_CATALOG = parse_simple_yaml_services(DEFAULT_CATALOG_PATH)
    return _CACHED_CATALOG


def _text_or_default(value: Any, default: str) -> str:
    """Returns ``value`` as a stripped string, or ``default`` when it is empty or None.

    Args:
        value: Raw value from a user-supplied mapping.
        default: Text used when ``value`` carries nothing.

    Returns:
        A non-empty string.
    """
    text = "" if value is None else str(value).strip()
    return text or default


def resolve_gcp_service(
    service_api: Optional[str],
    custom_services: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str, str]:
    """Resolves a service domain to category, display name, and compliance statement.

    Priority Order:
    1. User-provided custom_services (from compliance_config.yaml); keys are matched
       case-insensitively.
    2. Declarative catalog (gcp_service_catalog.yaml)
    3. Heuristic keyword inference

    Args:
        service_api: GCP service API identifier (e.g., 'cloudkms.googleapis.com').
        custom_services: Optional dictionary containing user-defined overrides.

    Returns:
        A 3-tuple containing (Category, Display Name, Compliance Statement).
    """
    if not service_api:
        return ("Cloud Service", "Generic GCP API", "Managed Google Cloud Platform Service")

    svc_clean = str(service_api).lower().strip()

    # 1. Check user custom services
    if custom_services and isinstance(custom_services, dict):
        normalized = {str(key).lower().strip(): value for key, value in custom_services.items()}
        if svc_clean in normalized:
            entry = normalized[svc_clean]
            if isinstance(entry, (list, tuple)) and len(entry) >= 3:
                return (str(entry[0]), str(entry[1]), str(entry[2]))
            if isinstance(entry, dict):
                return (
                    _text_or_default(entry.get("category"), "Custom Service"),
                    _text_or_default(entry.get("display_name", entry.get("name")), svc_clean),
                    _text_or_default(entry.get("purpose"), f"Configured custom service ({svc_clean})"),
                )

    # 2. Check declarative catalog
    catalog = get_service_catalog()
    if svc_clean in catalog:
        entry = catalog[svc_clean]
        cat = entry.get("category", "Cloud Infrastructure")
        name = entry.get("display_name", svc_clean)
        purp = entry.get("purpose", f"Managed {name} ({svc_clean})")
        return (cat, name, purp)

    # 3. Dynamic Heuristic Inference for new / unmapped APIs
    prefix = svc_clean.replace(".googleapis.com", "").replace("-", " ").replace("_", " ")
    title = prefix.title()
    inferred = _infer_category(prefix)
    if inferred is not None:
        category, name_suffix, purpose_template = inferred
        sw_name = f"Google {title}{name_suffix}"
        purpose = f"{purpose_template} ({svc_clean})"
    else:
        category = f"{title} Cloud Service"
        sw_name = f"Google {title} API ({svc_clean})"
        purpose = f"Managed Google Cloud Platform API Service ({svc_clean})"

    return (category, sw_name, purpose)
