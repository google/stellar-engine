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
Dynamic DISA STIG & SRG Checklist Version Resolver & Lifecycle Manager.

Authoritatively manages, resolves, updates, and validates DISA Security Technical
Implementation Guides (STIGs) and Security Requirements Guides (SRGs).

Key Capabilities:
1. Multi-Tiered Dynamic Version Resolution:
   - Tier 1: User / Institutional overrides from compliance_config.yaml (highest priority)
   - Tier 2: Remote / Online feeds & custom catalog endpoints (with strict air-gap timeouts)
   - Tier 3: Local target cache (.stig_cache.json)
   - Tier 4: Centralized authoritative baseline catalog (stig_catalog.json)
   - Tier 5: Resilient hardcoded fallback
2. Live pulling & caching of active STIG versions and updated checklists.
3. User-defined custom checklist injection for enclave-specific mission requirements.
4. Seamless integration with validate_compliance_artifacts.py and STIG Viewer desktop app.
"""

from __future__ import annotations

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
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import urllib.error
import urllib.parse
import urllib.request

try:
    from .audit_log import get_audit_logger, AuditOutcome, AuditEvent
except (ImportError, ValueError):
    from audit_log import get_audit_logger, AuditOutcome, AuditEvent

try:
    from .file_helpers import (
        ensure_path_within_boundary,
        get_skill_root,
        read_json_file,
        read_yaml_file,
    )
except (ImportError, ValueError):
    from file_helpers import (
        ensure_path_within_boundary,
        get_skill_root,
        read_json_file,
        read_yaml_file,
    )

logger = logging.getLogger("stig_resolver")

# Default paths
CATALOG_PATH = get_skill_root() / "config" / "stig_catalog.json"


@dataclass(frozen=True)
class RemoteCatalogResult:
    """Outcome of a remote STIG catalog retrieval attempt.

    Attributes:
        data: Parsed catalog payload, or None when retrieval failed.
        error: Operator-facing failure description, or None on success.
    """

    data: Optional[Union[Dict[str, Any], List[Any]]]
    error: Optional[str]


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that refuses to follow any redirect.

    ``urllib.request`` follows redirects transparently by default. When a destination
    host is allowlisted, transparent redirect-following means an allowlisted host can
    forward the client to an arbitrary endpoint, so the allowlist only ever constrains
    the first hop. Raising instead of following keeps the allowlist authoritative for
    the request that actually delivers content.
    """

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        """Refuses the redirect by returning None, which surfaces an HTTPError.

        Args:
            req: The originating request.
            fp: Response file object.
            code: HTTP status code of the redirect.
            msg: HTTP status message.
            headers: Response headers.
            newurl: Proposed redirect target.

        Returns:
            None, signalling to urllib that the redirect must not be followed.
        """
        logger.warning("Refusing redirect from '%s' to '%s' (HTTP %d)", req.full_url, newurl, code)
        return None


def normalize_stig_slug(slug: str) -> str:
    """Normalizes a STIG slug for robust, case-insensitive, punctuation-resilient matching.

    Examples:
        'canonical_ubuntu_22.04_lts' -> 'canonicalubuntu2204lts'
        'Canonical-Ubuntu-2204-LTS'  -> 'canonicalubuntu2204lts'
        'kubernetes'                 -> 'kubernetes'
    """
    if not slug:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", slug).lower()


def parse_version_string(ver_str: str) -> str:
    """Normalizes diverse STIG version representations into standard DoD DISA notation (e.g. 'v1R12').

    Examples:
        'Version 1, Release 12' -> 'v1R12'
        'v1r12'                 -> 'v1R12'
        '1.12'                  -> 'v1R12'
        'v2R4'                  -> 'v2R4'
        'V1R3'                  -> 'v1R3'
    """
    if not ver_str:
        return "v1R1"
    clean = str(ver_str).strip()

    # Pattern: 'Version 1, Release 12' or 'Ver 1 Rel 12' or 'V1R12'
    m_vr = re.search(r"v(?:er(?:sion)?)?\s*(\d+)\s*(?:,\s*)?r(?:el(?:ease)?)?\s*(\d+)", clean, re.IGNORECASE)
    if m_vr:
        return f"v{m_vr.group(1)}R{m_vr.group(2)}"

    # Pattern: '1.12' or '2.3'
    m_dot = re.search(r"^v?(\d+)\.(\d+)$", clean, re.IGNORECASE)
    if m_dot:
        return f"v{m_dot.group(1)}R{m_dot.group(2)}"

    # Pattern: just raw 'v1R3'
    m_direct = re.search(r"v\d+R\d+", clean, re.IGNORECASE)
    if m_direct:
        match_str = m_direct.group(0)
        return match_str[0].lower() + match_str[1:-1].lower() + match_str[-1].upper() if len(match_str) >= 4 else clean

    return clean

def rule_matches_web_ports(rule: Any) -> bool:
    """Checks if a firewall rule explicitly exposes web ports (80 / 443 / HTTP / HTTPS).

    Prevents false positives on CIDR blocks (e.g. 10.80.0.0/16), rule names
    (e.g. 'rule-80-allow-ssh'), or non-web ports (e.g. 8080).
    """
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
                        if int(parts[0]) <= 80 <= int(parts[1]) or int(parts[0]) <= 443 <= int(parts[1]):
                            return True
        for blk_key in ("allow", "allowed"):
            blocks = rule.get(blk_key) or []
            if isinstance(blocks, list):
                for blk in blocks:
                    if isinstance(blk, dict) and rule_matches_web_ports(blk):
                        return True
        return False
    elif isinstance(rule, str):
        return bool(re.search(r"(?<![0-9.])(?:80|443)(?![0-9.])", rule))
    return False


class StigResolver:
    """Resolves and manages active DISA STIG and SRG versions dynamically."""

    def __init__(
        self,
        target_dir: Optional[Union[str, Path]] = None,
        config: Optional[Dict[str, Any]] = None,
        catalog_path: Optional[Union[str, Path]] = None,
        update_mode: Optional[str] = None,
        catalog_source: Optional[str] = None,
    ) -> None:
        """Initializes the STIG version resolver with multi-tiered resolution channels.

        Args:
            target_dir: Target project workspace folder containing compliance artifacts.
            config: Optional pre-loaded compliance configuration dictionary.
            catalog_path: Optional path to the baseline STIG catalog JSON file.
            update_mode: Operational mode: 'auto', 'online', or 'offline'.
            catalog_source: Optional remote URL or local file path to pull updated checklists from.
        """
        self.target_dir = Path(target_dir).resolve() if target_dir else Path.cwd()
        self.catalog_path = Path(catalog_path).resolve() if catalog_path else CATALOG_PATH
        self.cache_file = self.target_dir / "ato_artifacts" / ".stig_cache.json"

        # 1. Load Authoritative Baseline Catalog
        self.catalog = self._load_baseline_catalog()

        # 2. Build Fast Slug & Alias Lookup Index
        self.slug_index: Dict[str, str] = {}  # normalized_slug -> canonical_slug
        self._build_slug_index()

        # 3. Load Project Configuration (compliance_config.yaml or provided config)
        self.config = config or self._load_project_config()
        stigs_config = self.config.get("disa_stigs", {}) if isinstance(self.config, dict) else {}

        # 4. Configure Resolution Parameters
        self.update_mode = (
            update_mode
            or stigs_config.get("update_mode")
            or "auto"
        ).lower()
        self.catalog_source = (
            catalog_source
            or stigs_config.get("catalog_source")
            or ""
        ).strip()

        # 5. Extract User Version Overrides and Custom Checklists
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

        # 6. Load Local Cache
        self.cache: Dict[str, Any] = self._load_cache()
        self.pulled_in_session: bool = False

    def _load_baseline_catalog(self) -> Dict[str, Any]:
        """Loads authoritative DISA STIG catalog from local JSON storage."""
        if self.catalog_path.is_file():
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
                    detail={"error": str(e), "message": "Failed to load STIG catalog"}
                )
                raise RuntimeError(f"CRITICAL: Failed to load STIG baseline catalog from {self.catalog_path}: {e}")
        else:
            get_audit_logger().emit(
                event_type=AuditEvent.SECURITY_VIOLATION,
                outcome=AuditOutcome.FAILURE,
                subject="stig_resolver",
                obj=str(self.catalog_path),
                detail={"message": "STIG baseline catalog not found"}
            )
            raise FileNotFoundError(f"CRITICAL: STIG baseline catalog not found at {self.catalog_path}")
        return {"catalog_version": "2026.1", "stigs": {}}

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
        if cfg_path.is_file():
            try:
                data = read_yaml_file(cfg_path, allowed_boundary=self.target_dir)
                if isinstance(data, dict):
                    return data
            except (OSError, ValueError, KeyError) as e:
                logger.debug("Could not parse YAML from %s: %s", cfg_path, e)

        inv_path = self.target_dir / "system_inventory.json"
        if inv_path.is_file():
            try:
                inv = read_json_file(inv_path, allowed_boundary=self.target_dir)
                if isinstance(inv, dict) and "disa_stigs" in inv:
                    return {"disa_stigs": inv["disa_stigs"]}
            except (OSError, ValueError, KeyError) as e:
                logger.debug("Could not load inventory from %s: %s", inv_path, e)

        return {}

    def _load_cache(self) -> Dict[str, Any]:
        """Loads previously cached active versions from target_dir/.stig_cache.json."""
        if self.cache_file.is_file():
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
            with os.fdopen(fd, 'w') as f:
                json.dump(self.cache, f, indent=2)
            os.replace(tmp_cache, self.cache_file)
            logger.debug("Updated STIG cache saved to %s", self.cache_file)
        except (OSError, ValueError) as e:
            logger.warning("Failed saving STIG cache to %s: %s", self.cache_file, e)

    #: Hosts from which a STIG catalog may be retrieved. Anything else is refused.
    #: Public sector deployments must not reach unaccredited endpoints (SA-9, SC-7).
    ACCREDITED_CATALOG_HOSTS: Tuple[str, ...] = ("cyber.mil", "disa.mil", "defense.gov", "nist.gov")

    #: Upper bound on a downloaded catalog. urlopen's read() is otherwise unbounded, so
    #: a compromised or hostile endpoint could stream until memory is exhausted (CWE-400).
    MAX_REMOTE_CATALOG_BYTES: int = 10 * 1024 * 1024

    #: Bounded retry policy for transient network faults.
    REMOTE_FETCH_ATTEMPTS: int = 3
    REMOTE_FETCH_BACKOFF_BASE_SECONDS: float = 0.5

    @classmethod
    def _is_accredited_host(cls, hostname: Optional[str]) -> bool:
        """Reports whether a hostname belongs to an accredited catalog domain.

        Args:
            hostname: Hostname parsed from a candidate URL, or None.

        Returns:
            True when the hostname exactly matches, or is a subdomain of, an
            accredited domain.
        """
        if not hostname:
            return False
        candidate = hostname.strip().rstrip(".").lower()
        if not candidate:
            return False
        return any(
            candidate == domain or candidate.endswith("." + domain)
            for domain in cls.ACCREDITED_CATALOG_HOSTS
        )

    def _fetch_remote_catalog(self, url: str, timeout: float, url_opener=None) -> "RemoteCatalogResult":
        """Retrieves a STIG catalog over HTTPS from an accredited endpoint.

        Hardening applied beyond a plain ``urlopen``:

        * **Transport (SC-8)** - cleartext ``http://`` is refused. A security baseline
          fetched over an unauthenticated channel can be silently substituted in transit.
        * **Allowlist integrity** - redirects are blocked entirely. ``urlopen`` follows
          redirects by default, so validating only the initial hostname lets an
          accredited host bounce the client to an arbitrary endpoint, defeating the
          allowlist and enabling SSRF-style retrieval.
        * **Bounded read (CWE-400)** - at most :attr:`MAX_REMOTE_CATALOG_BYTES` are read,
          and the body is rejected if it exceeds that, rather than being truncated into
          a partial catalog that would parse as "fewer applicable STIGs".
        * **Bounded retries** - transient faults are retried with exponential backoff
          plus jitter, so a flapping endpoint neither hangs the run nor stampedes.

        Args:
            url: Absolute catalog URL supplied by the operator.
            timeout: Per-attempt socket timeout in seconds.

        Returns:
            A :class:`RemoteCatalogResult` carrying either parsed data or an error
            message. This method does not raise on network failure; STIG resolution
            degrades to the local baseline.
        """
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
        # An opener without HTTPRedirectHandler turns any 3xx into an HTTPError instead
        # of transparently following it to a host that was never allowlisted.
        if url_opener:
            opener_func = url_opener
        else:
            opener = urllib.request.build_opener(_NoRedirectHandler)
            opener_func = opener.open

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

                    # Read one byte past the limit so an oversize body is detected
                    # rather than silently truncated into a partial catalog.
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
            except (urllib.error.URLError, TimeoutError, OSError) as net_err:
                last_error = str(net_err)

            if attempt < self.REMOTE_FETCH_ATTEMPTS:
                delay = self.REMOTE_FETCH_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                # Jitter spreads retries so concurrent runs do not synchronize.
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
        url_opener: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Pulls active STIG versions and updated checklists from remote or local sources.

        Air-gapped and network-resilient: strict timeouts and safe exception handling
        ensure execution never halts or fails if offline or firewalled.

        Args:
            source: URL or file path to pull from (defaults to configured catalog_source).
            timeout: Maximum network request timeout in seconds.

        Returns:
            Dictionary detailing update outcomes:
            {'success': bool, 'updated_count': int, 'source': str, 'stigs': dict}
        """
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
            # If no custom URL is configured, report baseline active state
            result["success"] = True
            result["message"] = "Authoritative baseline catalog is active and up to date."
            return result

        raw_data: Optional[Dict[str, Any]] = None

        # 1. Local file path source
        if os.path.exists(target_source):
            try:
                ensure_path_within_boundary(target_source, str(self.target_dir))
                if os.path.getsize(target_source) > 10 * 1024 * 1024:
                    raise ValueError("Catalog file size exceeds 10MB limit")
                if target_source.endswith((".yaml", ".yml")):
                    raw_data = read_yaml_file(target_source, allowed_boundary=self.target_dir)
                else:
                    raw_data = read_json_file(target_source, allowed_boundary=self.target_dir)
                result["message"] = f"Successfully loaded STIG catalog from local file '{target_source}'."
            except (OSError, ValueError, KeyError) as e:
                result["message"] = f"Failed to read local STIG catalog file '{target_source}': {e}"
                logger.warning(result["message"])
                return result

        # 2. Remote HTTPS URL source
        elif target_source.startswith(("http://", "https://")):
            fetch_result = self._fetch_remote_catalog(target_source, timeout, url_opener=url_opener)
            if fetch_result.error is not None:
                result["message"] = fetch_result.error
                return result
            raw_data = fetch_result.data
            result["message"] = f"Successfully pulled active STIG catalog from '{target_source}'."

        if not isinstance(raw_data, (dict, list)):
            result["message"] = "Invalid catalog format: expected dictionary or list."
            return result

        # 3. Process extracted STIG updates
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

                # Record in local cache
                if "stigs" not in self.cache:
                    self.cache["stigs"] = {}
                self.cache["stigs"][canonical_slug] = {
                    "version": norm_ver,
                    "source": "remote_feed",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }

        if updated:
            self._save_cache()
            self.pulled_in_session = True
            result["success"] = True
            result["updated_count"] = len(updated)
            result["stigs"] = updated
            logger.info("Successfully resolved %d active STIG versions from '%s'.", len(updated), target_source)

        return result

    def resolve_version(self, slug: str, default_version: Optional[str] = None) -> Tuple[str, str]:
        """Resolves the active version for a given STIG slug via the multi-tier hierarchy.

        Resolution Precedence:
        1. User Override (compliance_config.yaml)
        2. Remote Feed / Custom Catalog (if pulled in session)
        3. Local Cache (.stig_cache.json)
        4. Authoritative Baseline Catalog (stig_catalog.json)
        5. Hardcoded Fallback default_version

        Args:
            slug: Technology or baseline STIG slug identifier.
            default_version: Optional fallback version string.

        Returns:
            Tuple of (resolved_version, resolution_source_label).
        """
        norm_slug = normalize_stig_slug(slug)
        canonical_slug = self.slug_index.get(norm_slug, slug)

        # Tier 1: User / Institutional Configuration Override
        if norm_slug in self.version_overrides:
            return self.version_overrides[norm_slug], "User Override (compliance_config.yaml)"
        norm_canonical = normalize_stig_slug(canonical_slug)
        if norm_canonical in self.version_overrides:
            return self.version_overrides[norm_canonical], "User Override (compliance_config.yaml)"

        # Tier 2 & 3: Local Cache (.stig_cache.json)
        cached_stigs = self.cache.get("stigs", {})
        if canonical_slug in cached_stigs:
            entry = cached_stigs[canonical_slug]
            cached_ver = entry.get("version") if isinstance(entry, dict) else entry
            if cached_ver:
                source_lbl = "Live Active (Remote Feed)" if self.pulled_in_session else "Cached Active (.stig_cache.json)"
                return parse_version_string(str(cached_ver)), source_lbl

        # Tier 4: Authoritative Baseline Catalog (stig_catalog.json)
        catalog_stigs = self.catalog.get("stigs", {})
        if canonical_slug in catalog_stigs:
            cat_ver = catalog_stigs[canonical_slug].get("version")
            if cat_ver:
                return parse_version_string(str(cat_ver)), "Authoritative Baseline"

        # Tier 5: Fallback default
        final_fallback = parse_version_string(default_version or "v1R1")
        return final_fallback, "Baseline Fallback"

    def get_stig_entry(self, slug: str) -> Optional[Dict[str, Any]]:
        """Retrieves catalog metadata for a given STIG slug or alias."""
        norm_slug = normalize_stig_slug(slug)
        canonical_slug = self.slug_index.get(norm_slug, slug)
        return self.catalog.get("stigs", {}).get(canonical_slug)

    def get_all_catalog_stigs(self) -> Dict[str, Dict[str, Any]]:
        """Returns the full dictionary of cataloged STIG benchmarks."""
        return self.catalog.get("stigs", {})

    def evaluate_applicable_stigs(
        self,
        inventory: Dict[str, Any],
        trigger_pull: bool = False,
        url_opener: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluates complete DISA STIG applicability and dynamically resolves active versions.

        Args:
            inventory: Discovered system inventory dictionary.
            trigger_pull: If True, forces active pulling from remote catalog_source before evaluation.

        Returns:
            List of dictionaries defining matching STIG checklists with titles, slugs,
            dynamically resolved versions, resolution sources, scopes, and actions.
        """
        if trigger_pull or (self.update_mode == "online" and not self.pulled_in_session):
            self.pull_active_versions(url_opener=url_opener)

        applicable_stigs: List[Dict[str, Any]] = []
        seen_slugs: Set[str] = set()

        def add_item(
            title: str,
            slug: str,
            default_version: str,
            category: str,
            scope: str,
            action: str,
            status: str,
            reason: str,
            custom_url: Optional[str] = None,
        ) -> None:
            norm_slug = normalize_stig_slug(slug)
            canonical_slug = self.slug_index.get(norm_slug, slug)
            if canonical_slug in seen_slugs:
                return
            seen_slugs.add(canonical_slug)

            # Resolve active version & resolution channel
            resolved_ver, ver_source = self.resolve_version(canonical_slug, default_version)

            # Authoritative STIG Viewer & Cyber Exchange links
            cat_entry = self.catalog.get("stigs", {}).get(canonical_slug, {})
            url = (
                custom_url
                or cat_entry.get("url")
                or f"https://www.stigviewer.com/stigs/{canonical_slug}"
            )
            cyber_exchange_url = (
                cat_entry.get("cyber_exchange_url")
                or "https://public.cyber.mil/stigs/downloads/"
            )

            applicable_stigs.append({
                "title": cat_entry.get("title") or title,
                "slug": canonical_slug,
                "version": resolved_ver,
                "version_source": ver_source,
                "category": cat_entry.get("category") or category,
                "scope": scope or cat_entry.get("scope", ""),
                "action": action or cat_entry.get("action", ""),
                "url": url,
                "cyber_exchange_url": cyber_exchange_url,
                "reason": reason,
                "focus": scope or cat_entry.get("scope", ""),
                "status": status,
            })

        # -------------------------------------------------------------
        # 1. Foundational Cloud Mission Owner STIGs (Mandatory Baseline)
        # -------------------------------------------------------------
        foundational_defaults = [
            (
                "DISA Cloud Computing Security Requirements Guide (CC SRG)",
                "cloud_computing_srg",
                "v1R4",
                "Cloud Foundation Baseline",
                "Mission Owner responsibilities for cloud enclaves, Assured Workloads IL5 guardrails, organization policies, and FedRAMP inheritance.",
                "Complete Cloud Computing Mission Owner CKL; verify Assured Workloads boundary guardrails and organization policy constraints.",
            ),
            (
                "DISA Identity, Credential, and Access Management (ICAM) SRG / IAM STIG",
                "identity_and_access_management_iam_srg",
                "v1R2",
                "Identity & Access Control",
                "Cloud Identity SAML/OIDC federated SSO, hardware MFA enforcement, custom IAM roles, and automated service account key rotation.",
                "Complete IAM CKL; audit all custom role bindings, eliminate static service account keys in favor of Workload Identity Federation.",
            ),
            (
                "DISA Key and Certificate Management SRG / KMS STIG",
                "key_and_certificate_management_srg",
                "v1R1",
                "Cryptography & PKI",
                "FIPS 140-3 Cloud KMS CMEK encryption keys, 90-day automated key rotation, Certificate Manager TLS 1.3 PKI, and algorithm restrictions.",
                "Complete Key Mgmt CKL; verify CMEK association across all storage buckets, disks, and databases with automatic rotation active.",
            ),
        ]

        for title, slug, ver, cat, scope, action in foundational_defaults:
            add_item(
                title=title,
                slug=slug,
                default_version=ver,
                category=cat,
                scope=scope,
                action=action,
                status="Mandatory Cloud Baseline",
                reason="Foundational cloud baseline (Mission Owner responsibilities).",
            )

        # -------------------------------------------------------------
        # 2. Dynamic Workload Technology STIG Discovery
        # -------------------------------------------------------------
        infra = inventory.get("infrastructure_components", {})
        net = inventory.get("network_architecture", {})
        apps = inventory.get("application_components", {})
        custom = inventory.get("custom_services", {})
        services = [str(s).lower() for s in infra.get("services_enabled", [])]
        resources = infra.get("all_resources", [])

        # 2a. Operating Systems, Virtual Hosts & Appliance Images
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
                add_item(
                    title="DISA Canonical Ubuntu 22.04 LTS STIG",
                    slug="canonical_ubuntu_2204_lts",
                    default_version="v1R3",
                    category="Operating Systems & Host Compute",
                    scope="Hardened Ubuntu Linux Compute Engine instances and build worker bastions.",
                    action="Complete Ubuntu 22.04 CKL; apply Ubuntu Security Guide (USG) DISA profile in STIG Viewer desktop app.",
                    status="Required (Operating Systems & Host Compute)",
                    reason="Discovered Ubuntu Linux instances in active infrastructure code.",
                )
            if has_rhel or (vms and not has_ubuntu and not has_debian and not has_windows and not has_suse and not has_cisco):
                add_item(
                    title="DISA Red Hat Enterprise Linux 8/9 STIG",
                    slug="red_hat_enterprise_linux_9",
                    default_version="v1R3",
                    category="Operating Systems & Host Compute",
                    scope="Hardened Compute Engine VM hosts and administrative bastions.",
                    action="Complete RHEL / Linux OS CKL; apply OpenSCAP/Ansible DISA STIG baseline.",
                    status="Required (Operating Systems & Host Compute)",
                    reason="Discovered RHEL / Enterprise Linux instances in active infrastructure code.",
                )
            if has_debian:
                add_item(
                    title="DISA Debian Linux STIG / General Purpose OS SRG",
                    slug="debian_linux",
                    default_version="v1R1",
                    category="Operating Systems & Host Compute",
                    scope="Hardened Debian Linux Compute Engine host instances.",
                    action="Complete Debian OS CKL; apply Debian security hardening baseline.",
                    status="Required (Operating Systems & Host Compute)",
                    reason="Discovered Debian Linux instances in active infrastructure code.",
                )
            if has_windows:
                add_item(
                    title="DISA Microsoft Windows Server 2019/2022 STIG",
                    slug="ms_windows_server_2019",
                    default_version="v2R3",
                    category="Operating Systems & Host Compute",
                    scope="Hardened Windows Server Compute Engine instances and active directory bastions.",
                    action="Complete Windows Server CKL; apply DISA GPO baseline in STIG Viewer desktop app.",
                    status="Required (Operating Systems & Host Compute)",
                    reason="Discovered Microsoft Windows Server instances in active infrastructure code.",
                )
            if has_suse:
                add_item(
                    title="DISA SUSE Linux Enterprise Server STIG",
                    slug="suse_linux_enterprise_server",
                    default_version="v1R2",
                    category="Operating Systems & Host Compute",
                    scope="Hardened SUSE Linux Enterprise instances.",
                    action="Complete SLES CKL; apply OpenSCAP baseline.",
                    status="Required (Operating Systems & Host Compute)",
                    reason="Discovered SUSE Linux instances in active infrastructure code.",
                )
            if has_cisco:
                add_item(
                    title="DISA Cisco IOS-XE Router STIG / Network Infrastructure SRG",
                    slug="cisco_ios_xe_router",
                    default_version="v2R4",
                    category="Network Appliances & Routing",
                    scope="Virtual edge router instances, IPsec transport encryption, and perimeter routing appliances.",
                    action="Complete Cisco IOS-XE Router CKL; verify MACsec / IPsec encryption and control plane policing.",
                    status="Required (Network Appliances & Routing)",
                    reason="Discovered Cisco router or IOS-XE appliance instances in infrastructure code.",
                )

        # 2b. Containers, Microservices & Serverless
        gke = infra.get("gke_clusters", [])
        has_k8s = bool(gke) or "container.googleapis.com" in services or any("container_cluster" in str(r.get("type", "")).lower() for r in resources)
        if has_k8s:
            add_item(
                title="DISA Kubernetes STIG & Container Platform SRG",
                slug="kubernetes",
                default_version="v1R12",
                category="Containers & Microservices",
                scope="GKE private clusters, master control plane endpoints, RBAC, and Container Platform security.",
                action="Complete Kubernetes CKL; audit master authorized networks and Pod Security Standards in STIG Viewer.",
                status="Required (Containers & Microservices)",
                reason="Discovered Kubernetes (GKE) clusters in active infrastructure code.",
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
            add_item(
                title="DISA Container Platform & Serverless Workload SRG",
                slug="container_platform_srg",
                default_version="v1R1",
                category="Containers & Microservices",
                scope="Serverless container workloads, Cloud Run service perimeters, and stateless compute isolation.",
                action="Complete Container Platform CKL; enforce VPC-SC perimeter on Cloud Run services and verify non-root container execution.",
                status="Required (Containers & Microservices)",
                reason="Discovered serverless container platforms (Cloud Run / Cloud Functions) in infrastructure.",
            )

        if (infra.get("artifact_registries") or "artifactregistry.googleapis.com" in services) and "container_platform_srg" not in seen_slugs:
            add_item(
                title="DISA Container Platform & Image Registry SRG",
                slug="container_platform_srg",
                default_version="v1R1",
                category="Containers & Microservices",
                scope="Container image registries, vulnerability scanning, and binary authorization.",
                action="Complete Container Platform CKL; configure Artifact Registry vulnerability scanning and Binary Authorization policies.",
                status="Required (Containers & Microservices)",
                reason="Discovered container image registries in active infrastructure code.",
            )

        if apps.get("container_images") and "docker_enterprise" not in seen_slugs:
            add_item(
                title="DISA Container Runtime & Docker Enterprise STIG",
                slug="docker_enterprise",
                default_version="v2R1",
                category="Containers & Microservices",
                scope="Container base images, Dockerfile hardening, and non-root execution.",
                action="Complete Docker Enterprise CKL; eliminate root user in Dockerfiles and verify artifact signing.",
                status="Required (Containers & Microservices)",
                reason="Discovered container workload images in active application architecture.",
            )

        # 2c. Databases & Data Management
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
                add_item(
                    title="DISA PostgreSQL 13/14/15/16 STIG",
                    slug="postgresql_13",
                    default_version="v2R3",
                    category="Databases & Data Management",
                    scope="Cloud SQL PostgreSQL / AlloyDB instances, PGAudit logging, and TLS in transit.",
                    action="Complete PostgreSQL CKL; configure PGAudit database flags and verify Cloud Logging sink.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered PostgreSQL database engine instances in infrastructure code.",
                )
            if any(k in all_db_text for k in ["mysql", "mariadb"]):
                add_item(
                    title="DISA Oracle MySQL 8.0 STIG",
                    slug="oracle_mysql_8.0",
                    default_version="v1R3",
                    category="Databases & Data Management",
                    scope="Cloud SQL MySQL database instances and secure transport enforcement.",
                    action="Complete MySQL CKL; enforce require_secure_transport and audit logging.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered MySQL database engine instances in infrastructure code.",
                )
            if any(k in all_db_text for k in ["sqlserver", "mssql", "sql_server"]):
                add_item(
                    title="DISA Microsoft SQL Server 2016/2019 STIG",
                    slug="ms_sql_server_2016_instance",
                    default_version="v2R3",
                    category="Databases & Data Management",
                    scope="Cloud SQL SQL Server / MSSQL database instances.",
                    action="Complete SQL Server CKL; configure Windows Authentication / Cloud IAM and TLS encryption.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered Microsoft SQL Server database instances in infrastructure code.",
                )
            if "oracle" in all_db_text and "oracle_mysql" not in all_db_text:
                add_item(
                    title="DISA Oracle Database 12c/19c STIG",
                    slug="oracle_database_12c",
                    default_version="v2R4",
                    category="Databases & Data Management",
                    scope="Oracle database instances and Transparent Data Encryption (TDE).",
                    action="Complete Oracle CKL; enforce unified auditing and secure connection strings.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered Oracle database instances in infrastructure code.",
                )
            if "spanner" in all_db_text:
                add_item(
                    title="DISA Cloud Spanner Distributed Database SRG",
                    slug="database_srg",
                    default_version="v3R4",
                    category="Databases & Data Management",
                    scope="Google Cloud Spanner distributed relational database and CMEK encryption.",
                    action="Complete Database SRG CKL; enforce IAM fine-grained access and Cloud KMS CMEK key protection.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered Google Cloud Spanner distributed database services.",
                )
            if "bigquery" in all_db_text:
                add_item(
                    title="DISA Cloud Data Warehouse & Analytics SRG",
                    slug="database_srg",
                    default_version="v3R4",
                    category="Databases & Data Management",
                    scope="BigQuery analytics datasets, column-level security, and audit logging.",
                    action="Complete Database SRG CKL; enforce dataset authorized views and CMEK key encryption.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered BigQuery analytics warehouse datasets in infrastructure.",
                )
            if any(k in all_db_text for k in ["redis", "memorystore"]):
                add_item(
                    title="DISA Key-Value NoSQL Store / Database SRG",
                    slug="database_srg",
                    default_version="v3R4",
                    category="Databases & Data Management",
                    scope="In-memory caching and Redis / Memorystore key-value datastores.",
                    action="Complete Database SRG CKL; enforce AUTH password, TLS transit encryption, and private IP.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered Redis / Memorystore in-memory caching stores.",
                )
            if any(k in all_db_text for k in ["mongo", "mongodb"]):
                add_item(
                    title="DISA MongoDB Enterprise STIG / NoSQL Database SRG",
                    slug="mongodb_enterprise_3.x",
                    default_version="v2R1",
                    category="Databases & Data Management",
                    scope="Document database instances, wiredTiger encryption, and SCRAM authentication.",
                    action="Complete MongoDB CKL; enforce role-based access control and TLS transport.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered MongoDB NoSQL document database instances.",
                )
            if any(k in all_db_text for k in ["firestore", "datastore"]):
                add_item(
                    title="DISA Cloud Document Database SRG",
                    slug="database_srg",
                    default_version="v3R4",
                    category="Databases & Data Management",
                    scope="Cloud Firestore / Datastore serverless document databases.",
                    action="Complete Database SRG CKL; enforce security rules and IAM separation.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered Firestore / Datastore serverless document databases.",
                )
            if not any(slug in seen_slugs for slug in ["postgresql_13", "oracle_mysql_8.0", "ms_sql_server_2016_instance", "oracle_database_12c", "mongodb_enterprise_3.x", "database_srg"]):
                add_item(
                    title="DISA Database Security Requirements Guide (Generic RDBMS SRG)",
                    slug="database_srg",
                    default_version="v3R4",
                    category="Databases & Data Management",
                    scope="Managed relational database services, CMEK encryption at rest, and private IP only.",
                    action="Complete Database SRG CKL; enforce require_ssl=true and disable public IPv4.",
                    status="Required (Databases & Data Management)",
                    reason="Discovered relational database services in infrastructure code.",
                )

        # 2d. Storage Area Network / Cloud Object Store
        has_storage = (
            bool(infra.get("storage_buckets"))
            or "storage.googleapis.com" in services
            or any("storage_bucket" in str(r.get("type", "")).lower() or "s3" in str(r.get("type", "")).lower() for r in resources)
        )
        if has_storage:
            add_item(
                title="DISA Storage Area Network (SAN) / Cloud Object Store SRG",
                slug="storage_area_network_san_srg",
                default_version="v2R1",
                category="Storage & Persistence",
                scope="Google Cloud Storage (GCS) buckets, uniform bucket access, and retention policy locks.",
                action="Complete Storage SRG CKL; verify public access prevention and CMEK key encryption.",
                status="Required (Storage & Persistence)",
                reason="Discovered Cloud Object Storage (GCS/S3) resources in infrastructure code.",
            )

        # 2e. Network Perimeter, Firewalls & VPN Gateways
        has_firewall = (
            bool(net.get("firewall_rules"))
            or bool(net.get("vpcs"))
            or any("firewall" in str(r.get("type", "")).lower() for r in resources)
        )
        if has_firewall:
            add_item(
                title="DISA Perimeter Firewall & Network Infrastructure SRG",
                slug="firewall_srg",
                default_version="v2R1",
                category="Networking & Perimeter",
                scope="VPC Hub/Spoke perimeter firewall policy tiers, default-deny ingress, and Cloud IAP bastions.",
                action="Complete Firewall CKL; verify default-deny ingress rule and zero 0.0.0.0/0 exposure.",
                status="Required (Networking & Perimeter)",
                reason="Discovered VPC perimeter and firewall policies in active network code.",
            )

        has_vpn = (
            bool(net.get("vpn_tunnels"))
            or any("vpn" in str(r.get("type", "")).lower() for r in resources)
        )
        if has_vpn:
            add_item(
                title="DISA Virtual Private Network (VPN) Gateway SRG",
                slug="vpn_gateway_srg",
                default_version="v2R2",
                category="Networking & Perimeter",
                scope="Cloud HA VPN gateways, IPsec cryptographic profiles, and BGP dynamic routing.",
                action="Complete VPN Gateway CKL; enforce IKEv2 and AES-GCM 256-bit encryption cipher suites.",
                status="Required (Networking & Perimeter)",
                reason="Discovered Cloud HA VPN gateways or IPsec tunnels in network architecture.",
            )

        has_waf = (
            any("security_policy" in str(r.get("type", "")).lower() for r in resources)
            or any("armor" in s for s in services)
        )
        if has_waf:
            add_item(
                title="DISA Web Application Firewall (WAF) SRG",
                slug="web_application_firewall_srg",
                default_version="v1R1",
                category="Networking & Perimeter",
                scope="Cloud Armor WAF policies, adaptive protection against DDoS, and OWASP Top 10 rule sets.",
                action="Complete WAF SRG CKL; verify pre-configured OWASP CRS rules and rate-limiting policies.",
                status="Required (Networking & Perimeter)",
                reason="Discovered Cloud Armor WAF security policies in active network code.",
            )

        # 2f. Web & Application Security
        has_web = (
            bool(apps.get("applications"))
            or bool(apps.get("exposed_ports"))
            or any(s in services for s in ["run.googleapis.com", "appengine.googleapis.com"])
            or any("web" in s or "app" in s for s in services)
            or any(rule_matches_web_ports(r) for r in net.get("firewall_rules", []))
            or bool(custom)
        )
        if has_web:
            add_item(
                title="DISA Application Security and Development (ASD) STIG",
                slug="application_security_and_development_stig",
                default_version="v5R3",
                category="Application Security & DevSecOps",
                scope="DevSecOps CI/CD pipelines, container vulnerability scanning, and OWASP defenses.",
                action="Complete ASD STIG CKL; incorporate automated container scanning in CI/CD pipeline.",
                status="Required (Application Security & DevSecOps)",
                reason="Discovered web-facing application workloads and ingress ports in architecture.",
            )

        has_webserver = (
            any("nginx" in p or "apache" in p or "envoy" in p for p in packages)
            or any("target_http" in str(r.get("type", "")).lower() for r in resources)
        )
        if has_webserver:
            add_item(
                title="DISA Apache / Nginx Web Server STIG",
                slug="apache_server_2.4_unix_server",
                default_version="v2R4",
                category="Application Security & DevSecOps",
                scope="Web servers, reverse proxies, and Target HTTP/HTTPS proxies.",
                action="Complete Web Server CKL; disable weak TLS ciphers, server tokens, and enforce HTTP security headers.",
                status="Required (Application Security & DevSecOps)",
                reason="Discovered web server software or HTTP/HTTPS proxy targets.",
            )

        has_messaging = (
            bool(infra.get("pubsub_topics"))
            or "pubsub.googleapis.com" in services
            or any("pubsub" in str(r.get("type", "")).lower() for r in resources)
        )
        if has_messaging:
            add_item(
                title="DISA Enterprise Message Broker & Telemetry Ingestion SRG",
                slug="enterprise_message_broker_srg",
                default_version="v1R1",
                category="Application Security & DevSecOps",
                scope="Cloud Pub/Sub messaging topics, telemetry pipelines, and dead-letter queues.",
                action="Complete Message Broker CKL; enforce CMEK encryption on topics and restrict publisher/subscriber IAM roles.",
                status="Required (Application Security & DevSecOps)",
                reason="Discovered Pub/Sub message broker topics in infrastructure components.",
            )

        # -------------------------------------------------------------
        # 3. User-Defined Custom Checklists (compliance_config.yaml)
        # -------------------------------------------------------------
        for c in self.custom_checklists:
            c_slug = c.get("slug", "custom_stig")
            c_title = c.get("title", f"Custom STIG ({c_slug})")
            c_ver = c.get("version", "v1R1")
            c_cat = c.get("category", "Custom Mission Enclave")
            c_scope = c.get("scope", "Custom mission enclave security requirement.")
            c_act = c.get("action", "Complete custom CKL in STIG Viewer desktop app.")
            c_url = c.get("url")

            add_item(
                title=c_title,
                slug=c_slug,
                default_version=c_ver,
                category=c_cat,
                scope=c_scope,
                action=c_act,
                status="Custom Enclave Requirement",
                reason="Specified in compliance_config.yaml custom_checklists.",
                custom_url=c_url,
            )

        return applicable_stigs


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

    # Load inventory if available to test applicability
    inv_file = Path(target_dir) / "system_inventory.json"
    inv = {}
    if inv_file.is_file():
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
