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

"""Dynamic DISA STIG and SRG checklist version resolver and applicability evaluator."""

from __future__ import annotations

import http.client
import json
import logging
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union
import urllib.error
import urllib.parse
import urllib.request

from .audit_log import AuditEvent, AuditOutcome, get_audit_logger
from .file_helpers import (
    ensure_path_within_boundary,
    get_skill_root,
    read_json_file,
    read_yaml_file,
)

logger = logging.getLogger("stig_resolver")

CATALOG_PATH = get_skill_root() / "config" / "stig_catalog.json"

_TOKEN_SPLIT_RE = re.compile(r"[/\-_.\s:]+")
_PG_TOKEN_RE = re.compile(r"(?<![a-z0-9])(?:postgres|postgresql|psql|alloydb|psycopg2)(?![a-z0-9])", re.IGNORECASE)
_MYSQL_TOKEN_RE = re.compile(r"(?<![a-z0-9])mysql(?![a-z0-9])", re.IGNORECASE)
_MARIADB_TOKEN_RE = re.compile(r"(?<![a-z0-9])mariadb(?![a-z0-9])", re.IGNORECASE)
_MSSQL_TOKEN_RE = re.compile(r"(?<![a-z0-9])(?:sqlserver|mssql|sql_server)(?![a-z0-9])", re.IGNORECASE)
_ORACLE_TOKEN_RE = re.compile(r"(?<![a-z0-9])oracle(?![a-z0-9])", re.IGNORECASE)
_MONGO_TOKEN_RE = re.compile(r"(?<![a-z0-9])(?:mongo|mongodb)(?![a-z0-9])", re.IGNORECASE)


def _safe_is_file(path: Union[str, Path]) -> bool:
    """Safely probes whether ``path`` is a regular file without raising on OSError."""
    try:
        return Path(path).is_file()
    except OSError:
        return False


def _safe_exists(path: Union[str, Path]) -> bool:
    """Safely probes whether ``path`` exists without raising on OSError."""
    try:
        return os.path.exists(path)
    except OSError:
        return False


@dataclass(frozen=True)
class RemoteCatalogResult:
    """Outcome of a remote STIG catalog retrieval attempt."""

    data: Optional[Union[Dict[str, Any], List[Any]]]
    error: Optional[str]


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that refuses to follow any HTTP redirect."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        """Refuses the redirect by returning None, surfacing an HTTPError."""
        del fp, msg, headers
        logger.warning("Refusing redirect from '%s' to '%s' (HTTP %d)", req.full_url, newurl, code)
        return None


def normalize_stig_slug(slug: str) -> str:
    """Normalizes a STIG slug for case-insensitive, punctuation-resilient matching."""
    if not slug:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", slug).lower()


def parse_version_string(ver_str: str) -> str:
    """Normalizes diverse STIG version strings into uppercase DISA notation (e.g. 'V2R6')."""
    if not ver_str:
        return "V1R1"
    clean = str(ver_str).strip()

    m_vr = re.search(
        r"v(?:er(?:sion)?)?\s*(\d+)\s*(?:,\s*)?r(?:el(?:ease)?)?\s*(\d+)",
        clean,
        re.IGNORECASE,
    )
    if m_vr:
        return f"V{m_vr.group(1)}R{m_vr.group(2)}"

    m_dot = re.search(r"^v?(\d+)\.(\d+)$", clean, re.IGNORECASE)
    if m_dot:
        return f"V{m_dot.group(1)}R{m_dot.group(2)}"

    m_direct = re.search(r"v(\d+)r(\d+)", clean, re.IGNORECASE)
    if m_direct:
        return f"V{m_direct.group(1)}R{m_direct.group(2)}"

    return clean


def rule_matches_web_ports(rule: Any) -> bool:
    """Checks if a firewall rule explicitly exposes web ports (80 / 443 / HTTP / HTTPS)."""
    if isinstance(rule, dict):
        ports_val = rule.get("ports")
        if ports_val:
            tokens = (
                [str(p).strip() for p in ports_val]
                if isinstance(ports_val, list)
                else [p.strip() for p in re.split(r"[,;\s]+", str(ports_val))]
            )
            for token in tokens:
                if token.lower() in ("80", "443", "http", "https"):
                    return True
                if "-" in token:
                    parts = token.split("-")
                    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                        low, high = int(parts[0]), int(parts[1])
                        if low <= 80 <= high or low <= 443 <= high:
                            return True
        for blk_key in ("allow", "allowed"):
            blocks = rule.get(blk_key) or []
            if isinstance(blocks, list):
                for blk in blocks:
                    if isinstance(blk, dict) and rule_matches_web_ports(blk):
                        return True
        return False
    if isinstance(rule, str):
        return bool(re.search(r"(?<![0-9.])(?:80|443)(?![0-9.])", rule))
    return False


def _tokenize_image_field(raw_image: Any) -> List[str]:
    """Tokenizes an OS image string on path/version separators, ignoring unresolved expressions."""
    if not raw_image:
        return []
    text = str(raw_image).strip()
    if not text or "${" in text or "var." in text or "local." in text or text.startswith("["):
        return []
    return [tok for tok in _TOKEN_SPLIT_RE.split(text.lower()) if tok]


def _classify_ubuntu_or_rhel_tokens(token_set: Set[str], tokens: List[str]) -> Optional[Tuple[str, str]]:
    """Classifies Ubuntu, AlmaLinux, or RHEL image tokens."""
    if "ubuntu" in token_set:
        if "2404" in token_set or ("24" in token_set and "04" in token_set):
            return ("canonical_ubuntu_2404_lts", "Discovered Ubuntu 24.04 LTS instances in active infrastructure code.")
        if "2004" in token_set or ("20" in token_set and "04" in token_set):
            return ("canonical_ubuntu_2004_lts", "Discovered Ubuntu Linux instances in active infrastructure code.")
        return ("canonical_ubuntu_2204_lts", "Discovered Ubuntu 22.04 LTS instances in active infrastructure code.")

    if token_set & {"almalinux", "alma"}:
        return ("almalinux_os_9", "Discovered AlmaLinux OS 9 instances in active infrastructure code.")

    if token_set & {"rhel", "redhat"} or any(t.startswith("rhel") for t in tokens):
        if "10" in token_set or "rhel10" in token_set:
            return ("red_hat_enterprise_linux_10", "Discovered RHEL 10 instances in active infrastructure code.")
        if "8" in token_set or "rhel8" in token_set:
            return ("red_hat_enterprise_linux_8", "Discovered RHEL instances in active infrastructure code.")
        return ("red_hat_enterprise_linux_9", "Discovered RHEL 9 instances in active infrastructure code.")
    return None


def _classify_vm_image_tokens(tokens: List[str]) -> Optional[Tuple[str, str]]:
    """Maps tokenized VM OS image strings to (catalog_slug, reason)."""
    if not tokens:
        return None
    token_set = set(tokens)

    primary = _classify_ubuntu_or_rhel_tokens(token_set, tokens)
    if primary is not None:
        return primary

    if token_set & {"windows", "win2019", "win2022", "win2025"} or any(t.startswith("win") for t in tokens):
        if "2025" in token_set or "win2025" in token_set:
            return ("ms_windows_server_2025", "Discovered Microsoft Windows Server 2025 instances in infrastructure code.")
        if "2019" in token_set or "win2019" in token_set:
            return ("ms_windows_server_2019", "Discovered Microsoft Windows Server instances in infrastructure code.")
        return ("ms_windows_server_2022", "Discovered Microsoft Windows Server 2022 instances in infrastructure code.")

    if token_set & {"sles", "suse"} or any(t.startswith("sles") for t in tokens):
        return ("suse_linux_enterprise_server", "Discovered SUSE Linux Enterprise Server instances in infrastructure code.")

    if token_set & {"cisco", "iosxe", "csr1000v"} or ("ios" in token_set and "xe" in token_set):
        return ("cisco_ios_xe_router", "Discovered Cisco IOS XE router appliance instances in infrastructure code.")

    if token_set & {"debian", "rocky", "centos", "cos"} or ("container" in token_set and "optimized" in token_set):
        return ("debian_linux", "Discovered Linux host instances governed by DISA General Purpose OS SRG.")

    return None


def _is_unresolved_db_version(raw_ver: str, db_name: str) -> bool:
    """Reports whether a database_version string is an unresolved variable or legacy fallback."""
    if not raw_ver or "${" in raw_ver or "var." in raw_ver or "local." in raw_ver or raw_ver.startswith("["):
        return True
    low_name = db_name.lower()
    if raw_ver == "PostgreSQL 15" and any(k in low_name for k in ("mysql", "mariadb", "mssql", "sqlserver", "oracle")):
        return True
    return False


class StigResolver:
    """Resolves and manages active DISA STIG and SRG versions dynamically."""

    ACCREDITED_CATALOG_HOSTS: Tuple[str, ...] = ("cyber.mil", "disa.mil", "defense.gov", "nist.gov")
    MAX_REMOTE_CATALOG_BYTES: int = 10 * 1024 * 1024
    REMOTE_FETCH_ATTEMPTS: int = 3
    REMOTE_FETCH_BACKOFF_BASE_SECONDS: float = 0.5

    def __init__(
        self,
        target_dir: Optional[Union[str, Path]] = None,
        config: Optional[Dict[str, Any]] = None,
        catalog_path: Optional[Union[str, Path]] = None,
        update_mode: Optional[str] = None,
        catalog_source: Optional[str] = None,
    ) -> None:
        """Initializes the STIG version resolver with multi-tiered resolution channels."""
        self.target_dir = Path(target_dir).resolve() if target_dir else Path.cwd()
        self.catalog_path = Path(catalog_path).resolve() if catalog_path else CATALOG_PATH
        self.cache_file = self.target_dir / "ato_artifacts" / ".stig_cache.json"

        self.catalog = self._load_baseline_catalog()
        self.slug_index: Dict[str, str] = {}
        self._build_slug_index()

        self.config = config or self._load_project_config()
        stigs_config = self.config.get("disa_stigs", {}) if isinstance(self.config, dict) else {}

        raw_mode = (
            update_mode
            or stigs_config.get("update_mode")
            or stigs_config.get("catalog_mode")
            or "auto"
        )
        self.update_mode = str(raw_mode).lower()
        self.catalog_source = (
            catalog_source
            or stigs_config.get("catalog_source")
            or ""
        ).strip()

        self.version_overrides: Dict[str, str] = {}
        raw_overrides = stigs_config.get("version_overrides", {}) or stigs_config.get("overrides", {})
        if isinstance(raw_overrides, dict):
            for k, v in raw_overrides.items():
                norm_k = normalize_stig_slug(str(k))
                self.version_overrides[norm_k] = parse_version_string(str(v))

        self.custom_checklists: List[Dict[str, Any]] = []
        raw_custom = stigs_config.get("custom_checklists", [])
        if isinstance(raw_custom, list):
            for item in raw_custom:
                if isinstance(item, dict) and item.get("slug") and item.get("title"):
                    self.custom_checklists.append(item)

        self.cache: Dict[str, Any] = self._load_cache()
        self.pulled_in_session: bool = False

    def _load_baseline_catalog(self) -> Dict[str, Any]:
        """Loads authoritative DISA STIG catalog from local JSON storage."""
        try:
            catalog_is_file = self.catalog_path.is_file()
            probe_error = ""
        except OSError as err:
            catalog_is_file = False
            probe_error = f": {err}"
        if catalog_is_file:
            try:
                data = read_json_file(self.catalog_path)
                if isinstance(data, dict):
                    return data
            except (OSError, ValueError, KeyError) as e:
                get_audit_logger().emit(
                    event_type=AuditEvent.SECURITY_VIOLATION,
                    outcome=AuditOutcome.FAILURE,
                    subject="stig_resolver",
                    obj=str(self.catalog_path),
                    detail={"error": str(e), "message": "Failed to load STIG catalog"},
                )
                raise RuntimeError(f"CRITICAL: Failed to load STIG baseline catalog from {self.catalog_path}: {e}")
        get_audit_logger().emit(
            event_type=AuditEvent.SECURITY_VIOLATION,
            outcome=AuditOutcome.FAILURE,
            subject="stig_resolver",
            obj=str(self.catalog_path),
            detail={"message": f"STIG baseline catalog not found or not accessible{probe_error}"},
        )
        raise FileNotFoundError(
            f"CRITICAL: STIG baseline catalog not found or not accessible at {self.catalog_path}{probe_error}"
        )

    def _build_slug_index(self) -> None:
        """Indexes all primary slugs and aliases for normalized O(1) matching."""
        stigs = self.catalog.get("stigs", {})
        for canonical_slug, entry in stigs.items():
            norm_canonical = normalize_stig_slug(canonical_slug)
            self.slug_index[norm_canonical] = canonical_slug
            for alias in entry.get("aliases", []):
                norm_alias = normalize_stig_slug(alias)
                self.slug_index[norm_alias] = canonical_slug

    def _load_project_config(self) -> Dict[str, Any]:
        """Loads compliance_config.yaml or system_inventory.json from target_dir if present."""
        cfg_path = self.target_dir / "compliance_config.yaml"
        if _safe_is_file(cfg_path):
            try:
                data = read_yaml_file(cfg_path, allowed_boundary=self.target_dir)
                if isinstance(data, dict):
                    return data
            except (OSError, ValueError, KeyError) as e:
                logger.debug("Could not parse YAML from %s: %s", cfg_path, e)

        inv_path = self.target_dir / "system_inventory.json"
        if _safe_is_file(inv_path):
            try:
                inv = read_json_file(inv_path, allowed_boundary=self.target_dir)
                if isinstance(inv, dict) and "disa_stigs" in inv:
                    return {"disa_stigs": inv["disa_stigs"]}
            except (OSError, ValueError, KeyError) as e:
                logger.debug("Could not load inventory from %s: %s", inv_path, e)

        return {}

    def _load_cache(self) -> Dict[str, Any]:
        """Loads previously cached active versions from target_dir/ato_artifacts/.stig_cache.json."""
        if _safe_is_file(self.cache_file):
            try:
                data = read_json_file(self.cache_file, allowed_boundary=self.target_dir)
                if isinstance(data, dict) and "stigs" in data:
                    return data
            except (OSError, ValueError, KeyError) as e:
                logger.debug("Could not load STIG cache from %s: %s", self.cache_file, e)
        return {"cached_at": None, "stigs": {}}

    def _save_cache(self) -> None:
        """Saves current active STIG version cache to target_dir/ato_artifacts/.stig_cache.json."""
        try:
            self.cache["cached_at"] = datetime.now(timezone.utc).isoformat()
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_cache = self.cache_file.with_suffix(".tmp")
            ensure_path_within_boundary(str(self.cache_file), str(self.target_dir))

            fd = os.open(tmp_cache, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump(self.cache, f, indent=2)
            os.replace(tmp_cache, self.cache_file)
            logger.debug("Updated STIG cache saved to %s", self.cache_file)
        except (OSError, ValueError) as e:
            logger.warning("Failed saving STIG cache to %s: %s", self.cache_file, e)

    @classmethod
    def _is_accredited_host(cls, hostname: Optional[str]) -> bool:
        """Reports whether a hostname belongs to an accredited catalog domain."""
        if not hostname:
            return False
        candidate = hostname.strip().rstrip(".").lower()
        if not candidate:
            return False
        return any(
            candidate == domain or candidate.endswith("." + domain)
            for domain in cls.ACCREDITED_CATALOG_HOSTS
        )

    def _fetch_remote_catalog(self, url: str, timeout: float, url_opener: Any = None) -> RemoteCatalogResult:
        """Retrieves a STIG catalog over HTTPS from an accredited endpoint."""
        parsed_url = urllib.parse.urlparse(url)

        if parsed_url.scheme != "https":
            message = (
                f"Refusing cleartext STIG catalog source '{url}'. A security baseline must "
                "be retrieved over HTTPS so it cannot be substituted in transit (SC-8)."
            )
            logger.error(message)
            return RemoteCatalogResult(data=None, error=message)

        if not self._is_accredited_host(parsed_url.hostname):
            message = (
                f"Unaccredited remote endpoint '{url}' rejected; permitted domains are "
                f"{', '.join(self.ACCREDITED_CATALOG_HOSTS)}."
            )
            logger.error(message)
            return RemoteCatalogResult(data=None, error=message)

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "DISA-STIG-Resolver (compliance-engine)",
                "Accept": "application/json",
            },
            method="GET",
        )
        opener_func = url_opener if url_opener else urllib.request.build_opener(_NoRedirectHandler).open

        last_error = "unknown error"
        for attempt in range(1, self.REMOTE_FETCH_ATTEMPTS + 1):
            try:
                with opener_func(request, timeout=timeout) as response:
                    if response.status not in (200, 203):
                        last_error = f"HTTP status {response.status}"
                        logger.warning(
                            "Remote STIG source '%s' returned %s (attempt %d/%d)",
                            url,
                            last_error,
                            attempt,
                            self.REMOTE_FETCH_ATTEMPTS,
                        )
                        break

                    declared = response.headers.get("Content-Length")
                    if isinstance(declared, str) and declared.isdigit():
                        if int(declared) > self.MAX_REMOTE_CATALOG_BYTES:
                            message = (
                                f"Remote STIG catalog '{url}' declares {declared} bytes, "
                                f"exceeding the {self.MAX_REMOTE_CATALOG_BYTES} byte limit."
                            )
                            logger.error(message)
                            return RemoteCatalogResult(data=None, error=message)

                    body = response.read(self.MAX_REMOTE_CATALOG_BYTES + 1)

                if len(body) > self.MAX_REMOTE_CATALOG_BYTES:
                    message = (
                        f"Remote STIG catalog '{url}' exceeded the "
                        f"{self.MAX_REMOTE_CATALOG_BYTES} byte limit."
                    )
                    logger.error(message)
                    return RemoteCatalogResult(data=None, error=message)

                try:
                    return RemoteCatalogResult(data=json.loads(body.decode("utf-8")), error=None)
                except (json.JSONDecodeError, UnicodeDecodeError) as decode_err:
                    message = f"Remote source '{url}' returned non-JSON content: {decode_err}"
                    logger.error(message)
                    return RemoteCatalogResult(data=None, error=message)

            except urllib.error.HTTPError as http_err:
                if http_err.code in (301, 302, 303, 307, 308):
                    message = (
                        f"Remote STIG source '{url}' attempted a redirect to "
                        f"'{http_err.headers.get('Location', 'unknown')}'. Redirects are "
                        "refused because they would bypass the accredited-host allowlist."
                    )
                    logger.error(message)
                    return RemoteCatalogResult(data=None, error=message)
                last_error = f"HTTP error {http_err.code}"
            except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as net_err:
                last_error = str(net_err)

            if attempt < self.REMOTE_FETCH_ATTEMPTS:
                delay = self.REMOTE_FETCH_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                delay += random.uniform(0, delay / 2)
                logger.info(
                    "Remote STIG fetch attempt %d/%d failed (%s); retrying in %.2fs",
                    attempt,
                    self.REMOTE_FETCH_ATTEMPTS,
                    last_error,
                    delay,
                )
                time.sleep(delay)

        message = (
            f"Remote STIG source '{url}' unreachable after "
            f"{self.REMOTE_FETCH_ATTEMPTS} attempts ({last_error}). "
            "Falling back to the local authoritative baseline."
        )
        logger.warning(message)
        return RemoteCatalogResult(data=None, error=message)

    def pull_active_versions(
        self,
        source: Optional[str] = None,
        timeout: float = 3.0,
        url_opener: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, Any]:
        """Pulls active STIG versions and updated checklists from remote or local sources."""
        target_source = (source or self.catalog_source).strip()
        result: Dict[str, Any] = {
            "success": False,
            "updated_count": 0,
            "source": target_source or "catalog_baseline",
            "stigs": {},
            "message": "",
        }

        if self.update_mode == "offline":
            result["message"] = "Offline mode active; remote pulling skipped."
            return result

        if not target_source:
            result["success"] = True
            result["message"] = "Authoritative baseline catalog is active and up to date."
            return result

        raw_data = self._read_catalog_source(target_source, timeout, url_opener, result)
        if not isinstance(raw_data, (dict, list)):
            if not result["message"]:
                result["message"] = "Invalid catalog format: expected dictionary or list."
            return result

        updated = self._apply_pulled_catalog(raw_data)
        if updated:
            self._save_cache()
            self.pulled_in_session = True
            result["success"] = True
            result["updated_count"] = len(updated)
            result["stigs"] = updated
            logger.info("Successfully resolved %d active STIG versions from '%s'.", len(updated), target_source)

        return result

    def _read_catalog_source(
        self,
        target_source: str,
        timeout: float,
        url_opener: Optional[Callable[..., Any]],
        result: Dict[str, Any],
    ) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """Reads a local or remote catalog source into parsed JSON/YAML data."""
        if _safe_exists(target_source):
            try:
                ensure_path_within_boundary(target_source, str(self.target_dir))
                if os.path.getsize(target_source) > self.MAX_REMOTE_CATALOG_BYTES:
                    raise ValueError("Catalog file size exceeds 10MB limit")
                if target_source.endswith((".yaml", ".yml")):
                    raw_data = read_yaml_file(target_source, allowed_boundary=self.target_dir)
                else:
                    raw_data = read_json_file(target_source, allowed_boundary=self.target_dir)
                result["message"] = f"Successfully loaded STIG catalog from local file '{target_source}'."
                return raw_data
            except (OSError, ValueError, KeyError) as e:
                result["message"] = f"Failed to read local STIG catalog file '{target_source}': {e}"
                logger.warning(result["message"])
                return None

        if target_source.startswith(("http://", "https://")):
            fetch_result = self._fetch_remote_catalog(target_source, timeout, url_opener=url_opener)
            if fetch_result.error is not None:
                result["message"] = fetch_result.error
                return None
            result["message"] = f"Successfully pulled active STIG catalog from '{target_source}'."
            return fetch_result.data

        return None

    def _apply_pulled_catalog(self, raw_data: Union[Dict[str, Any], List[Any]]) -> Dict[str, str]:
        """Merges pulled STIG versions into the local cache."""
        updated: Dict[str, str] = {}
        stigs_dict: Dict[str, Any] = {}

        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict) and "slug" in item:
                    stigs_dict[item["slug"]] = item
        elif isinstance(raw_data, dict):
            stigs_dict = raw_data.get("stigs", raw_data)

        for slug, val in stigs_dict.items():
            version_val: Optional[str] = None
            if isinstance(val, dict):
                version_val = val.get("version") or val.get("release")
            elif isinstance(val, str):
                version_val = val

            if version_val:
                norm_slug = normalize_stig_slug(slug)
                norm_ver = parse_version_string(version_val)
                canonical_slug = self.slug_index.get(norm_slug, slug)
                updated[canonical_slug] = norm_ver

                if "stigs" not in self.cache:
                    self.cache["stigs"] = {}
                self.cache["stigs"][canonical_slug] = {
                    "version": norm_ver,
                    "source": "remote_feed",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
        return updated

    def resolve_version(self, slug: str, default_version: Optional[str] = None) -> Tuple[str, str]:
        """Resolves the active version for a given STIG slug via the multi-tier hierarchy."""
        if self.update_mode in ("online", "remote") and not self.pulled_in_session and self.catalog_source:
            self.pull_active_versions()

        norm_slug = normalize_stig_slug(slug)
        canonical_slug = self.slug_index.get(norm_slug, slug)

        if norm_slug in self.version_overrides:
            return self.version_overrides[norm_slug], "User Override (compliance_config.yaml)"
        norm_canonical = normalize_stig_slug(canonical_slug)
        if norm_canonical in self.version_overrides:
            return self.version_overrides[norm_canonical], "User Override (compliance_config.yaml)"

        cached_stigs = self.cache.get("stigs", {})
        if canonical_slug in cached_stigs:
            entry = cached_stigs[canonical_slug]
            cached_ver = entry.get("version") if isinstance(entry, dict) else entry
            if cached_ver:
                source_lbl = "Live Active (Remote Feed)" if self.pulled_in_session else "Cached Active (.stig_cache.json)"
                return parse_version_string(str(cached_ver)), source_lbl

        catalog_stigs = self.catalog.get("stigs", {})
        if canonical_slug in catalog_stigs:
            cat_ver = catalog_stigs[canonical_slug].get("version")
            if cat_ver:
                return parse_version_string(str(cat_ver)), "Authoritative Baseline"

        final_fallback = parse_version_string(default_version or "1.1")
        return final_fallback, "Baseline Fallback"

    def get_stig_entry(self, slug: str) -> Optional[Dict[str, Any]]:
        """Retrieves catalog metadata for a given STIG slug or alias."""
        norm_slug = normalize_stig_slug(slug)
        canonical_slug = self.slug_index.get(norm_slug, slug)
        return self.catalog.get("stigs", {}).get(canonical_slug)

    def get_all_catalog_stigs(self) -> Dict[str, Dict[str, Any]]:
        """Returns the full dictionary of cataloged STIG benchmarks."""
        return self.catalog.get("stigs", {})

    def _build_stig_item(
        self,
        slug: str,
        reason: str,
        status: str,
        *,
        is_custom: bool = False,
        custom_meta: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Builds an emitted STIG dictionary from catalog metadata, redirecting sunset entries."""
        if is_custom and custom_meta is not None:
            c_slug = str(custom_meta.get("slug", slug))
            c_ver = parse_version_string(str(custom_meta.get("version", "1.1")))
            resolved_ver, ver_source = self.resolve_version(c_slug, c_ver)
            scope = str(custom_meta.get("scope", "Custom mission enclave security requirement."))
            return {
                "title": str(custom_meta.get("title", f"Custom STIG ({c_slug})")),
                "slug": c_slug,
                "version": resolved_ver,
                "version_source": ver_source,
                "category": str(custom_meta.get("category", "Custom Mission Enclave")),
                "scope": scope,
                "action": str(custom_meta.get("action", "Complete custom CKL in STIG Viewer desktop app.")),
                "url": str(custom_meta.get("url") or f"https://www.stigviewer.com/stigs/{c_slug}"),
                "cyber_exchange_url": "https://public.cyber.mil/stigs/downloads/",
                "reason": reason,
                "focus": scope,
                "status": status,
            }

        norm_slug = normalize_stig_slug(slug)
        canonical_slug = self.slug_index.get(norm_slug, slug)
        catalog_stigs = self.catalog.get("stigs", {})
        cat_entry = catalog_stigs.get(canonical_slug)
        if not cat_entry:
            raise KeyError(f"Unknown STIG catalog slug: {slug!r}")

        if cat_entry.get("status") == "sunset":
            successor = cat_entry.get("successor_slug")
            if not successor:
                return None
            canonical_slug = self.slug_index.get(normalize_stig_slug(successor), successor)
            cat_entry = catalog_stigs.get(canonical_slug)
            if not cat_entry or cat_entry.get("status") == "sunset" or cat_entry.get("is_foundational"):
                return None

        resolved_ver, ver_source = self.resolve_version(canonical_slug)
        scope = str(cat_entry.get("scope", ""))
        action = str(cat_entry.get("action", ""))
        return {
            "title": str(cat_entry["title"]),
            "slug": canonical_slug,
            "version": resolved_ver,
            "version_source": ver_source,
            "category": str(cat_entry.get("category", "")),
            "scope": scope,
            "action": action,
            "url": str(cat_entry.get("url") or f"https://www.stigviewer.com/stigs/{canonical_slug}"),
            "cyber_exchange_url": str(
                cat_entry.get("cyber_exchange_url") or "https://public.cyber.mil/stigs/downloads/"
            ),
            "reason": reason,
            "focus": scope,
            "status": status,
        }

    def evaluate_applicable_stigs(
        self,
        inventory: Dict[str, Any],
        trigger_pull: bool = False,
        url_opener: Optional[Callable[..., Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluates DISA STIG applicability for the discovered system inventory."""
        if trigger_pull or (self.update_mode in ("online", "remote") and not self.pulled_in_session):
            self.pull_active_versions(url_opener=url_opener)

        applicable_stigs: List[Dict[str, Any]] = []
        seen_slugs: Set[str] = set()

        def emit(
            slug: str,
            reason: str,
            status: str,
            *,
            is_custom: bool = False,
            custom_meta: Optional[Dict[str, Any]] = None,
        ) -> None:
            item = self._build_stig_item(
                slug,
                reason,
                status,
                is_custom=is_custom,
                custom_meta=custom_meta,
            )
            if item is None or item["slug"] in seen_slugs:
                return
            seen_slugs.add(item["slug"])
            applicable_stigs.append(item)

        self._emit_foundational_stigs(emit)

        infra = inventory.get("infrastructure_components", {})
        net = inventory.get("network_architecture", {})
        apps = inventory.get("application_components", {})
        custom = inventory.get("custom_services", {})
        services = [str(s).lower() for s in infra.get("services_enabled", [])]
        resources = infra.get("all_resources", [])

        self._evaluate_compute_os_stigs(infra, custom, resources, services, emit)
        self._evaluate_container_stigs(infra, apps, resources, services, emit)
        self._evaluate_database_stigs(infra, apps, resources, services, emit)
        self._evaluate_network_stigs(net, resources, services, emit)
        self._evaluate_application_web_stigs(apps, net, custom, services, emit)
        self._emit_custom_checklists(emit)

        return applicable_stigs

    def _emit_foundational_stigs(self, emit: Callable[..., None]) -> None:
        """Emits mandatory foundational Mission Owner SRGs from the active catalog."""
        for slug, entry in self.catalog.get("stigs", {}).items():
            if entry.get("is_foundational") and entry.get("status") == "active":
                emit(
                    slug,
                    "Foundational cloud baseline (Mission Owner responsibilities).",
                    "Mandatory Cloud Baseline",
                )

    def _evaluate_compute_os_stigs(
        self,
        infra: Dict[str, Any],
        custom: Dict[str, Any],
        resources: List[Dict[str, Any]],
        services: List[str],
        emit: Callable[..., None],
    ) -> None:
        """Evaluates host OS STIGs strictly from VM image/OS fields rather than VM names."""
        vms = infra.get("compute_instances", [])
        has_compute = (
            bool(vms)
            or any("compute" in s for s in services)
            or any("compute_instance" in str(r.get("type", "")).lower() for r in resources)
        )
        if not has_compute:
            return

        matched_any_vm = False
        unmatched_vm = False
        for vm in vms:
            if not isinstance(vm, dict):
                continue
            img_fields = (
                vm.get("image"),
                vm.get("source_image"),
                vm.get("boot_disk_image"),
                vm.get("os"),
                vm.get("os_family"),
            )
            vm_tokens: List[str] = []
            for raw_img in img_fields:
                vm_tokens.extend(_tokenize_image_field(raw_img))
            classified = _classify_vm_image_tokens(vm_tokens)
            if classified is not None:
                slug, reason = classified
                status = (
                    "Required (Network Appliances & Routing)"
                    if slug == "cisco_ios_xe_router"
                    else "Required (Operating Systems & Host Compute)"
                )
                emit(slug, reason, status)
                matched_any_vm = True
            else:
                unmatched_vm = True

        for k, v in custom.items():
            custom_tokens = _tokenize_image_field(f"{k} {v}")
            classified = _classify_vm_image_tokens(custom_tokens)
            if classified is not None:
                slug, reason = classified
                emit(slug, reason, "Required (Operating Systems & Host Compute)")
                matched_any_vm = True

        if unmatched_vm or (vms and not matched_any_vm):
            emit(
                "debian_linux",
                "Discovered Compute Engine VM instances (OS image family not determined from IaC).",
                "Required (Operating Systems & Host Compute)",
            )

    def _evaluate_container_stigs(
        self,
        infra: Dict[str, Any],
        apps: Dict[str, Any],
        resources: List[Dict[str, Any]],
        services: List[str],
        emit: Callable[..., None],
    ) -> None:
        """Evaluates Kubernetes and Container Platform SRG applicability."""
        gke = infra.get("gke_clusters", [])
        has_k8s = (
            bool(gke)
            or "container.googleapis.com" in services
            or any("container_cluster" in str(r.get("type", "")).lower() for r in resources)
        )
        if has_k8s:
            emit(
                "kubernetes",
                "Discovered Kubernetes (GKE) clusters in active infrastructure code.",
                "Required (Containers & Microservices)",
            )

        has_serverless = (
            bool(infra.get("cloud_run_services"))
            or bool(infra.get("cloud_functions"))
            or "run.googleapis.com" in services
            or "cloudfunctions.googleapis.com" in services
            or any("cloud_run" in str(r.get("type", "")).lower() for r in resources)
        )
        if has_serverless:
            emit(
                "container_platform_srg",
                "Discovered serverless container platforms (Cloud Run / Cloud Functions) in infrastructure.",
                "Required (Containers & Microservices)",
            )

        if infra.get("artifact_registries") or "artifactregistry.googleapis.com" in services:
            emit(
                "container_platform_srg",
                "Discovered container image registries in active infrastructure code.",
                "Required (Containers & Microservices)",
            )

        if apps.get("container_images"):
            emit(
                "container_platform_srg",
                "Discovered container workload images in active application architecture.",
                "Required (Containers & Microservices)",
            )

    def _evaluate_database_stigs(
        self,
        infra: Dict[str, Any],
        apps: Dict[str, Any],
        resources: List[Dict[str, Any]],
        services: List[str],
        emit: Callable[..., None],
    ) -> None:
        """Evaluates database STIGs using structured database fields and underscore-aware tokens."""
        dbs = infra.get("databases", [])
        packages = [
            str(p.get("name", "")).lower()
            for p in apps.get("software_packages", [])
            if isinstance(p, dict)
        ]
        res_types = [str(r.get("type", "")).lower() for r in resources]

        db_versions: List[str] = []
        db_types: List[str] = list(res_types)
        for db in dbs:
            if not isinstance(db, dict):
                continue
            dtype = str(db.get("type") or "").lower()
            if dtype:
                db_types.append(dtype)
            raw_ver = str(db.get("database_version") or db.get("engine") or "").strip()
            db_name = str(db.get("name") or "")
            if not _is_unresolved_db_version(raw_ver, db_name):
                db_versions.append(raw_ver.lower())

        structured_text = " ".join(db_versions + packages + db_types + services)
        has_db = (
            bool(dbs)
            or any(
                k in structured_text
                for k in (
                    "sql", "spanner", "bigquery", "postgres", "alloydb",
                    "mysql", "mariadb", "redis", "database", "datastore",
                    "firestore", "mongo", "oracle",
                )
            )
        )
        if not has_db:
            return

        before_count = self._emit_specific_database_stigs(db_versions, db_types, structured_text, emit)
        self._emit_managed_database_srgs(structured_text, before_count, emit)

    def _emit_specific_database_stigs(
        self,
        db_versions: Iterable[str],
        db_types: Iterable[str],
        structured_text: str,
        emit: Callable[..., None],
    ) -> int:
        """Emits product-specific database STIGs and returns count of matched engines."""
        matched = 0
        ver_list = list(db_versions)
        type_set = set(db_types)

        is_pg = (
            any(v.startswith("postgres") for v in ver_list)
            or bool(type_set & {"google_alloydb_cluster", "google_alloydb_instance"})
            or bool(_PG_TOKEN_RE.search(structured_text))
        )
        if is_pg:
            emit(
                "crunchy_data_postgres_16",
                "Discovered PostgreSQL or AlloyDB database instances in infrastructure code.",
                "Required (Databases & Data Management)",
            )
            matched += 1

        if _MARIADB_TOKEN_RE.search(structured_text):
            emit(
                "mariadb_enterprise_10x",
                "Discovered MariaDB database instances in infrastructure code.",
                "Required (Databases & Data Management)",
            )
            matched += 1

        if _MYSQL_TOKEN_RE.search(structured_text):
            emit(
                "oracle_mysql_8.0",
                "Discovered MySQL database instances in infrastructure code.",
                "Required (Databases & Data Management)",
            )
            matched += 1

        if _MSSQL_TOKEN_RE.search(structured_text):
            slug = "ms_sql_server_2022_instance" if "2022" in structured_text else "ms_sql_server_2016_instance"
            emit(
                slug,
                "Discovered Microsoft SQL Server database instances in infrastructure code.",
                "Required (Databases & Data Management)",
            )
            matched += 1

        oracle_cleaned = re.sub(r"oracle_mysql", "", structured_text)
        if _ORACLE_TOKEN_RE.search(oracle_cleaned):
            emit(
                "oracle_database_19c",
                "Discovered Oracle database instances in infrastructure code.",
                "Required (Databases & Data Management)",
            )
            matched += 1

        if _MONGO_TOKEN_RE.search(structured_text):
            slug = (
                "mongodb_enterprise_advanced_8x"
                if re.search(r"mongo(?:db)?[_\-\s.]*8", structured_text)
                else "mongodb_enterprise_advanced_7x"
            )
            emit(
                slug,
                "Discovered MongoDB NoSQL document database instances.",
                "Required (Databases & Data Management)",
            )
            matched += 1

        return matched

    def _emit_managed_database_srgs(
        self,
        structured_text: str,
        specific_matches: int,
        emit: Callable[..., None],
    ) -> None:
        """Emits DISA Database SRG for managed cloud databases or unspecified engines."""
        if "spanner" in structured_text:
            emit(
                "database_srg",
                "Discovered Google Cloud Spanner distributed database services.",
                "Required (Databases & Data Management)",
            )
            return
        if "bigquery" in structured_text:
            emit(
                "database_srg",
                "Discovered BigQuery analytics warehouse datasets in infrastructure.",
                "Required (Databases & Data Management)",
            )
            return
        if any(k in structured_text for k in ("redis", "memorystore")):
            emit(
                "database_srg",
                "Discovered Redis / Memorystore in-memory caching stores.",
                "Required (Databases & Data Management)",
            )
            return
        if any(k in structured_text for k in ("firestore", "datastore")):
            emit(
                "database_srg",
                "Discovered Firestore / Datastore serverless document databases.",
                "Required (Databases & Data Management)",
            )
            return
        if specific_matches == 0:
            emit(
                "database_srg",
                "Discovered relational database services in infrastructure code.",
                "Required (Databases & Data Management)",
            )

    def _evaluate_network_stigs(
        self,
        net: Dict[str, Any],
        resources: List[Dict[str, Any]],
        services: List[str],
        emit: Callable[..., None],
    ) -> None:
        """Evaluates firewall, VPN, and WAF SRG applicability."""
        has_firewall = (
            bool(net.get("firewall_rules"))
            or bool(net.get("vpcs"))
            or any("firewall" in str(r.get("type", "")).lower() for r in resources)
        )
        if has_firewall:
            emit(
                "firewall_srg",
                "Discovered VPC perimeter and firewall policies in active network code.",
                "Required (Networking & Perimeter)",
            )

        has_vpn = (
            bool(net.get("vpn_tunnels"))
            or any("vpn" in str(r.get("type", "")).lower() for r in resources)
        )
        if has_vpn:
            emit(
                "vpn_gateway_srg",
                "Discovered Cloud HA VPN gateways or IPsec tunnels in network architecture.",
                "Required (Networking & Perimeter)",
            )

        has_waf = (
            any("security_policy" in str(r.get("type", "")).lower() for r in resources)
            or any("armor" in s for s in services)
        )
        if has_waf:
            emit(
                "web_application_firewall_srg",
                "Discovered Cloud Armor WAF security policies in active network code.",
                "Required (Networking & Perimeter)",
            )

    def _evaluate_application_web_stigs(
        self,
        apps: Dict[str, Any],
        net: Dict[str, Any],
        custom: Dict[str, Any],
        services: List[str],
        emit: Callable[..., None],
    ) -> None:
        """Evaluates ASD STIG and product-specific web server STIGs."""
        has_web = (
            bool(apps.get("applications"))
            or bool(apps.get("exposed_ports"))
            or any(s in services for s in ("run.googleapis.com", "appengine.googleapis.com"))
            or any("web" in s or "app" in s for s in services)
            or any(rule_matches_web_ports(r) for r in net.get("firewall_rules", []))
            or bool(custom)
        )
        if has_web:
            emit(
                "application_security_and_development_stig",
                "Discovered web-facing application workloads and ingress ports in architecture.",
                "Required (Application Security & DevSecOps)",
            )

        packages = [
            str(p.get("name", "")).lower()
            for p in apps.get("software_packages", [])
            if isinstance(p, dict)
        ]
        if any("nginx" in p for p in packages):
            emit(
                "f5_nginx",
                "Discovered NGINX web server or reverse proxy software in application components.",
                "Required (Application Security & DevSecOps)",
            )
        if any("apache" in p or "httpd" in p for p in packages):
            emit(
                "apache_server_2.4_unix_server",
                "Discovered Apache HTTP Server software in application components.",
                "Required (Application Security & DevSecOps)",
            )
        if any(k in p for p in packages for k in ("envoy", "caddy", "haproxy", "iis")):
            emit(
                "web_server_srg",
                "Discovered self-managed HTTP/HTTPS web server software in application components.",
                "Required (Application Security & DevSecOps)",
            )

    def _emit_custom_checklists(self, emit: Callable[..., None]) -> None:
        """Emits user-defined custom checklists from compliance_config.yaml."""
        for custom_item in self.custom_checklists:
            c_slug = str(custom_item.get("slug", "custom_stig"))
            emit(
                c_slug,
                "Specified in compliance_config.yaml custom_checklists.",
                "Custom Enclave Requirement",
                is_custom=True,
                custom_meta=custom_item,
            )


def main() -> None:
    """CLI test harness and inspector for STIG version resolver."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    target_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
    update_flag = "--update" in sys.argv or "--update-stigs" in sys.argv
    catalog_source = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--catalog-source=")), None)
    mode = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--mode=")), None)

    resolver = StigResolver(
        target_dir=target_dir,
        catalog_source=catalog_source,
        update_mode=mode or ("online" if update_flag else "auto"),
    )

    if update_flag:
        logger.info("Executing active STIG version pull...")
        res = resolver.pull_active_versions()
        logger.info("Result: %s", res.get("message"))

    inv_file = Path(target_dir) / "system_inventory.json"
    inv: Dict[str, Any] = {}
    if _safe_is_file(inv_file):
        try:
            inv = read_json_file(inv_file, allowed_boundary=target_dir)
        except (OSError, ValueError, TypeError) as err:
            logger.debug("Could not read system_inventory.json from %s: %s", inv_file, err)

    stigs = resolver.evaluate_applicable_stigs(inv)
    logger.info("\n" + "=" * 80)
    logger.info("DISA STIG / SRG Dynamic Version Resolver Results (%d Applicable STIGs)", len(stigs))
    logger.info("=" * 80)
    for s in stigs:
        logger.info("• %s", s["title"])
        logger.info("  Slug   : %s", s["slug"])
        logger.info("  Version: %s (%s)", s["version"], s["version_source"])
        logger.info("  URL    : %s", s["url"])
        logger.info("  Status : %s", s["status"])
        logger.info("-" * 80)


if __name__ == "__main__":
    main()
