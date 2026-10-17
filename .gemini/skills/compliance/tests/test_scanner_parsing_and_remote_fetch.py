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
"""Scanner result parsing and remote STIG fetch security controls tests.

Covers security_scanner_bridge.py (run_checkov_scan, run_semgrep_scan,
run_trivy_scan, resolve_preinstalled_scanner_binary, parse_sarif_file) and
stig_resolver.py (_fetch_remote_catalog, _NoRedirectHandler, evaluate_applicable_stigs).
"""

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
for _p in (str(SRC_DIR), str(SCRIPT_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from compliance_engine import security_scanner_bridge as ssb  # noqa: E402
from compliance_engine import stig_resolver  # noqa: E402


def _completed(payload, returncode=0, stderr=""):
    stdout = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.CompletedProcess(["scanner"], returncode, stdout, stderr)


class TestScannerResultParsing(unittest.TestCase):
    """Realistic scanner JSON must become findings (no live binaries needed)."""

    def setUp(self):
        ssb.reset_scan_cache()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.target = self._tmp.name

    def test_checkov_failed_checks_become_findings(self):
        # Open-source checkov reports "severity": null and exits 1 when checks fail.
        payload = {"check_type": "terraform", "results": {"failed_checks": [{
            "check_id": "CKV_GCP_2",
            "check_name": "Ensure Google compute firewall ingress does not allow unrestricted ssh access",
            "resource": "google_compute_firewall.fw",
            "file_path": "/main.tf",
            "file_line_range": [5, 13],
            "guideline": "https://docs.example/ckv_gcp_2",
            "severity": None,
        }]}}
        with mock.patch.object(ssb.shutil, "which", return_value="/usr/bin/checkov"), \
                mock.patch.object(ssb, "_safe_run_subprocess", return_value=_completed(payload, 1)):
            findings = ssb.run_checkov_scan(self.target)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["check_id"], "CKV_GCP_2")
        self.assertEqual(findings[0]["resource"], "google_compute_firewall.fw")
        self.assertEqual(findings[0]["location"], "/main.tf:L5-13")
        self.assertFalse(ssb.is_scanner_failure_check_id(findings[0]["check_id"]))

    def test_trivy_vulnerabilities_become_findings_with_mapped_severity(self):
        payload = {"Results": [{"Target": "requirements.txt", "Vulnerabilities": [{
            "VulnerabilityID": "CVE-2020-14343", "PkgName": "pyyaml",
            "InstalledVersion": "5.3", "FixedVersion": "5.4",
            "Title": "arbitrary code execution", "Severity": "CRITICAL",
        }]}]}
        with mock.patch.object(ssb, "resolve_preinstalled_scanner_binary", return_value="/usr/bin/trivy"), \
                mock.patch.object(ssb, "_safe_run_subprocess", return_value=_completed(payload)):
            findings = ssb.run_trivy_scan(self.target)
        self.assertEqual([f["check_id"] for f in findings], ["CVE-2020-14343"])
        self.assertEqual(findings[0]["severity"], "High")
        self.assertEqual(findings[0]["location"], "requirements.txt:pyyaml")

    def test_semgrep_results_become_findings(self):
        payload = {"results": [{
            "check_id": "public-sector.python.os-system", "path": "app/a.py",
            "start": {"line": 3}, "end": {"line": 4},
            "extra": {"message": "os.system with user input", "severity": "ERROR",
                      "metadata": {"cwe": ["CWE-78: OS Command Injection"]}},
        }]}
        with mock.patch.object(ssb.shutil, "which", return_value="/usr/bin/semgrep"), \
                mock.patch.object(ssb, "_safe_run_subprocess", return_value=_completed(payload)):
            findings = ssb.run_semgrep_scan(self.target)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "High")
        self.assertEqual(findings[0]["location"], "app/a.py:L3-4")
        self.assertTrue(findings[0]["cwe"].startswith("CWE-78"))

    def test_semgrep_auto_config_maps_to_bundled_ruleset_for_metrics_off(self):
        """SKILL.md / semgrep rejects 'auto' with --metrics=off, so 'auto' resolves to bundled ruleset."""
        ok = _completed({"results": []})
        env = {k: v for k, v in os.environ.items() if k not in ("COMPLIANCE_OFFLINE", "SEMGREP_OFFLINE")}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(ssb.shutil, "which", return_value="/usr/bin/semgrep"), \
                mock.patch.object(ssb, "_safe_run_subprocess", return_value=ok) as run:
            findings = ssb.run_semgrep_scan(self.target, semgrep_config="auto")
        self.assertEqual(findings, [])
        self.assertEqual(run.call_count, 1)
        argv = list(run.call_args_list[0][0][0])
        self.assertIn("--metrics=off", argv)
        self.assertTrue(argv[argv.index("--config") + 1].endswith("public_sector_baseline.yaml"))

    def test_semgrep_registry_pack_falls_back_to_bundled_ruleset_on_metrics_off_error(self):
        """If a remote pack fails with 'metrics are off', run_semgrep_scan falls back to bundled ruleset."""
        refused = _completed("", 2, "[00.05][ERROR]: Cannot create auto config when metrics are off.")
        ok = _completed({"results": []})
        env = {k: v for k, v in os.environ.items() if k not in ("COMPLIANCE_OFFLINE", "SEMGREP_OFFLINE")}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(ssb.shutil, "which", return_value="/usr/bin/semgrep"), \
                mock.patch.object(ssb, "_safe_run_subprocess", side_effect=[refused, ok]) as run:
            findings = ssb.run_semgrep_scan(self.target, semgrep_config="p/ci")
        self.assertEqual(findings, [])
        self.assertEqual(run.call_count, 2)
        second_argv = list(run.call_args_list[1][0][0])
        self.assertTrue(second_argv[second_argv.index("--config") + 1].endswith("public_sector_baseline.yaml"))


class _Response:
    def __init__(self, body=b"{}", status=200, headers=None):
        self.status = status
        self.headers = headers or {}
        self._body = io.BytesIO(body)

    def read(self, size=-1):
        return self._body.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestRemoteCatalogFetchControls(unittest.TestCase):
    """Every hardening control in StigResolver._fetch_remote_catalog's docstring."""

    URL = "https://public.cyber.mil/stigs/catalog.json"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.resolver = stig_resolver.StigResolver(target_dir=self._tmp.name, update_mode="offline")
        patcher = mock.patch.object(stig_resolver.time, "sleep")  # no real backoff sleeps
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_cleartext_http_is_refused_before_any_request(self):
        opener = mock.Mock()
        result = self.resolver._fetch_remote_catalog(self.URL.replace("https:", "http:"), 5, url_opener=opener)
        self.assertIsNone(result.data)
        self.assertIn("HTTPS", result.error)
        opener.assert_not_called()

    def test_unaccredited_and_lookalike_hosts_are_refused(self):
        for url in ("https://evil.example/c.json", "https://cyber.mil.evil.example/c.json",
                    "https://notcyber.mil/c.json"):
            with self.subTest(url=url):
                opener = mock.Mock()
                result = self.resolver._fetch_remote_catalog(url, 5, url_opener=opener)
                self.assertIsNone(result.data)
                self.assertIn("Unaccredited", result.error)
                opener.assert_not_called()

    def test_redirect_is_refused_and_not_retried(self):
        redirect = urllib.error.HTTPError(self.URL, 302, "Found", {"Location": "https://evil.example/"}, None)
        opener = mock.Mock(side_effect=redirect)
        result = self.resolver._fetch_remote_catalog(self.URL, 5, url_opener=opener)
        self.assertIsNone(result.data)
        self.assertIn("redirect", result.error)
        self.assertEqual(opener.call_count, 1)

    def test_default_redirect_handler_never_follows(self):
        handler = stig_resolver._NoRedirectHandler()
        req = urllib.request.Request(self.URL)
        self.assertIsNone(handler.redirect_request(req, None, 302, "Found", {}, "https://evil.example/"))

    def test_oversize_declared_length_is_refused(self):
        too_big = str(stig_resolver.StigResolver.MAX_REMOTE_CATALOG_BYTES + 1)
        opener = mock.Mock(return_value=_Response(headers={"Content-Length": too_big}))
        result = self.resolver._fetch_remote_catalog(self.URL, 5, url_opener=opener)
        self.assertIsNone(result.data)
        self.assertIn("exceeding", result.error)

    def test_oversize_body_is_refused_not_truncated(self):
        opener = mock.Mock(return_value=_Response(body=b'{"k": "0123456789"}'))
        with mock.patch.object(stig_resolver.StigResolver, "MAX_REMOTE_CATALOG_BYTES", 8):
            result = self.resolver._fetch_remote_catalog(self.URL, 5, url_opener=opener)
        self.assertIsNone(result.data)
        self.assertIn("exceeded", result.error)

    def test_non_json_body_is_refused(self):
        opener = mock.Mock(return_value=_Response(body=b"<html>maintenance</html>"))
        result = self.resolver._fetch_remote_catalog(self.URL, 5, url_opener=opener)
        self.assertIsNone(result.data)
        self.assertIn("non-JSON", result.error)

    def test_non_200_status_is_not_parsed(self):
        opener = mock.Mock(return_value=_Response(body=b'{"stigs": []}', status=500))
        result = self.resolver._fetch_remote_catalog(self.URL, 5, url_opener=opener)
        self.assertIsNone(result.data)
        self.assertIn("HTTP status 500", result.error)


if __name__ == "__main__":
    unittest.main()
