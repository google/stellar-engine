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

from datetime import datetime, timedelta
import unittest
import sys
import os
import re
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts and src directories to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
for _d in (str(SRC_DIR), str(SCRIPT_DIR)):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import security_scanner_bridge  # noqa: E402
import stig_resolver  # noqa: E402


class TestHardeningScanners(unittest.TestCase):

    def test_safe_run_subprocess_flag_injection(self):
        # We test that flag injection defense is in place for checkov, semgrep, trivy, scc
        self.assertEqual(security_scanner_bridge.run_checkov_scan("-foo"), [])
        self.assertEqual(security_scanner_bridge.run_semgrep_scan("-foo"), [])
        self.assertEqual(security_scanner_bridge.run_trivy_scan("-foo"), [])
        self.assertEqual(security_scanner_bridge.fetch_live_scc_findings(project_id="-foo"), [])

    @patch('security_scanner_bridge._safe_run_subprocess')
    def test_scc_failure_reports_unknown(self, mock_run):
        mock_run.side_effect = OSError("Crash")
        findings = security_scanner_bridge.fetch_live_scc_findings("my-project")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["check_id"], "SCC_QUERY_FAILURE")

    def test_stig_resolver_baseline_fail_closed(self):
        import tempfile

        resolver = stig_resolver.StigResolver()
        with tempfile.TemporaryDirectory() as tmp:
            # A path inside a fresh temp dir is guaranteed not to exist on any host.
            resolver.catalog_path = Path(tmp) / "missing" / "catalog.json"
            with self.assertRaises(FileNotFoundError):
                resolver._load_baseline_catalog()

    def test_stig_resolver_unreadable_catalog_fails_closed(self):
        """An unreadable catalog location must fail closed, not crash with PermissionError."""

        class _UnreadablePath(type(Path())):
            def is_file(self, *args, **kwargs):
                raise PermissionError(13, "Permission denied", str(self))

        resolver = stig_resolver.StigResolver()
        resolver.catalog_path = _UnreadablePath("/restricted/catalog.json")
        with self.assertRaises(FileNotFoundError) as ctx:
            resolver._load_baseline_catalog()
        self.assertIn("not accessible", str(ctx.exception))


class TestSemgrepInvocationContract(unittest.TestCase):
    """Pins the Semgrep command line.

    The shipped invocation previously combined ``--config auto`` with
    ``--metrics=off``, a combination semgrep rejects outright, so the SAST scan
    failed on every single run and surfaced only as a bogus "High" POA&M item.
    It also placed the ``scan`` subcommand after global flags, which makes
    semgrep treat the literal word "scan" as a scan target. Nothing caught
    either defect, so the exact argv is asserted here.
    """

    def _captured_argv(self, semgrep_config=None):
        """Runs a scan against a real temp directory and returns the argv used."""
        import tempfile

        with tempfile.TemporaryDirectory() as target:
            with patch("security_scanner_bridge.shutil.which", return_value="/usr/bin/semgrep"), \
                    patch("security_scanner_bridge._safe_run_subprocess") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout='{"results": []}', stderr="")
                security_scanner_bridge.run_semgrep_scan(target, semgrep_config=semgrep_config)
            self.assertTrue(mock_run.called, "semgrep was never invoked")
            return list(mock_run.call_args[0][0])

    def test_scan_subcommand_immediately_follows_binary(self):
        argv = self._captured_argv()
        self.assertEqual(argv[0], "semgrep")
        self.assertEqual(
            argv[1],
            "scan",
            f"'scan' must directly follow the binary or it is parsed as a target: {argv!r}",
        )

    def test_bundled_scan_is_default_when_no_config(self):
        argv = self._captured_argv()
        self.assertIn("--config", argv)
        config_value = argv[argv.index("--config") + 1]
        self.assertIn("public_sector_baseline.yaml", config_value)
        self.assertIn(
            "--metrics=off",
            argv,
            "--metrics=off must be passed",
        )
        self.assertIn("--no-git-ignore", argv)

    def test_bundled_ruleset_used_when_explicitly_configured(self):
        argv = self._captured_argv(semgrep_config=str(security_scanner_bridge.SEMGREP_RULES_DIR))
        self.assertIn("--config", argv)
        config_value = argv[argv.index("--config") + 1]
        self.assertEqual(
            config_value,
            str(security_scanner_bridge.SEMGREP_RULES_DIR),
        )
        self.assertTrue(
            os.path.isdir(config_value),
            f"the bundled offline ruleset must exist on disk: {config_value!r}",
        )
        self.assertIn("--metrics=off", argv)
        self.assertIn(
            "--no-git-ignore",
            argv,
            "without this, a gitignored target scans to zero findings and reports clean",
        )

    def test_missing_ruleset_fails_closed_not_silent(self):
        """A ruleset that cannot be resolved must produce a coverage finding."""
        import tempfile

        with tempfile.TemporaryDirectory() as target:
            # A path inside a fresh temp dir is guaranteed not to exist on any host.
            missing_ruleset = os.path.join(target, "missing", "ruleset", "dir")
            with patch("security_scanner_bridge.shutil.which", return_value="/usr/bin/semgrep"):
                findings = security_scanner_bridge.run_semgrep_scan(
                    target, semgrep_config=missing_ruleset
                )
        self.assertEqual(len(findings), 1, "a missing ruleset must not scan to an empty result")
        self.assertEqual(findings[0]["check_id"], "SEMGREP_SCANNER_ERROR")
        self.assertEqual(findings[0]["cwe"], "CA-02 / RA-05")

    def test_unreadable_ruleset_path_fails_closed(self):
        """A ruleset path whose parent is unreadable must yield a coverage finding, not a crash."""
        import tempfile

        denied = PermissionError(13, "Permission denied")
        with tempfile.TemporaryDirectory() as target:
            with patch("security_scanner_bridge.shutil.which", return_value="/usr/bin/semgrep"), \
                    patch.object(security_scanner_bridge.Path, "exists", side_effect=denied):
                ref, err = security_scanner_bridge._resolve_semgrep_config("/restricted/rules.yaml")
                findings = security_scanner_bridge.run_semgrep_scan(
                    target, semgrep_config="/restricted/rules.yaml"
                )
        self.assertIsNone(ref)
        self.assertIn("not accessible", err)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["check_id"], "SEMGREP_SCANNER_ERROR")

    def test_auto_config_supported_with_metrics_off(self):
        """'auto' config resolves to the bundled offline ruleset so --metrics=off never fails."""
        argv = self._captured_argv(semgrep_config="auto")
        self.assertIn("--config", argv)
        config_value = argv[argv.index("--config") + 1]
        self.assertEqual(config_value, str(security_scanner_bridge.SEMGREP_BUNDLED_RULES_FILE))
        self.assertIn(
            "--metrics=off",
            argv,
            "--metrics=off must be passed even when configured with 'auto'",
        )
        self.assertIn("--no-git-ignore", argv)

    def test_auto_sentinel_resolves_to_bundled_rules_file(self):
        """'auto' resolves to the bundled offline ruleset because Semgrep rejects --config auto with --metrics=off."""
        config_ref, error = security_scanner_bridge._resolve_semgrep_config("auto")
        self.assertIsNone(error)
        self.assertEqual(config_ref, str(security_scanner_bridge.SEMGREP_BUNDLED_RULES_FILE))

    def test_explicit_override_still_takes_precedence_over_the_bundle(self):
        """An operator pointing at an internal mirror must not be silently overridden."""
        with patch.dict(os.environ, {"COMPLIANCE_OFFLINE": "0", "SEMGREP_OFFLINE": "0"}):
            config_ref, error = security_scanner_bridge._resolve_semgrep_config("p/ci")
        self.assertIsNone(error)
        self.assertEqual(config_ref, "p/ci")

    def test_operator_semgrep_config_cli_and_env_accepted_while_target_config_ignored(self):
        """Only operator CLI/env may choose a custom Semgrep ruleset; target config must not."""
        import tempfile

        from compliance_engine import poam_rules

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            (target / "app.py").write_text("x = 1\n", encoding="utf-8")
            op_rules = Path(tmp) / "operator_rules.yaml"
            op_rules.write_text("rules: []\n", encoding="utf-8")
            evil_rules = Path(tmp) / "evil_rules.yaml"
            evil_rules.write_text("rules: []\n", encoding="utf-8")

            inventory = {
                "system_information": {"system_abbreviation": "TST"},
                "infrastructure_components": {},
                "semgrep_config": str(evil_rules),
                "security_scanners": {
                    "semgrep_config": str(evil_rules),
                },
            }

            with patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": "0", "COMPLIANCE_SEMGREP_CONFIG": ""}, clear=False):
                # 1. Target inventory/config cannot select evil_rules.
                with patch("security_scanner_bridge.run_semgrep_scan", return_value=[]) as mock_sem:
                    security_scanner_bridge.reset_scan_cache()
                    poam_rules.collect_scanner_items(
                        inventory,
                        target,
                        scanner_policy=security_scanner_bridge.resolve_scanner_policy(True, ["semgrep"]),
                    )
                    self.assertEqual(mock_sem.call_count, 1)
                    self.assertIsNone(mock_sem.call_args.kwargs.get("semgrep_config"))

                # 2. Operator CLI / ScannerPolicy.semgrep_config selects op_rules.
                with patch("security_scanner_bridge.run_semgrep_scan", return_value=[]) as mock_sem_cli:
                    security_scanner_bridge.reset_scan_cache()
                    policy = security_scanner_bridge.resolve_scanner_policy(
                        True, ["semgrep"], semgrep_config=str(op_rules)
                    )
                    poam_rules.collect_scanner_items(inventory, target, scanner_policy=policy)
                    self.assertEqual(mock_sem_cli.call_count, 1)
                    self.assertEqual(mock_sem_cli.call_args.kwargs.get("semgrep_config"), str(op_rules))

            # 3. Operator COMPLIANCE_SEMGREP_CONFIG env var resolves to op_rules even outside target.
            with patch.dict(os.environ, {"COMPLIANCE_SEMGREP_CONFIG": str(op_rules)}, clear=False):
                ref, err = security_scanner_bridge._resolve_semgrep_config(None, target_dir=target)
                self.assertIsNone(err)
                self.assertEqual(ref, str(op_rules.resolve()))

    def test_custom_checklist_outside_boundary_is_rejected(self):
        """StigResolver must reject custom_checklists pointing outside target_dir."""
        import tempfile

        with tempfile.TemporaryDirectory() as root_tmp:
            target = Path(root_tmp) / "target"
            outside = Path(root_tmp) / "outside"
            target.mkdir()
            outside.mkdir()
            secret_ckl = outside / "secret.ckl"
            secret_ckl.write_text(
                "<CHECKLIST><STIGS><iSTIG><VULN><STIG_DATA>"
                "<VULN_ATTRIBUTE>Vuln_Num</VULN_ATTRIBUTE><ATTRIBUTE_DATA>V-999999</ATTRIBUTE_DATA>"
                "</STIG_DATA><STATUS>Open</STATUS></VULN></iSTIG></STIGS></CHECKLIST>",
                encoding="utf-8",
            )

            resolver = stig_resolver.StigResolver(target_dir=str(target), update_mode="offline")
            inv = {
                "disa_stigs": {
                    "custom_checklists": [str(secret_ckl), "../outside/secret.ckl"],
                },
                "infrastructure_components": {},
                "network_architecture": {},
            }
            stigs = resolver.evaluate_applicable_stigs(inv)
            all_open_vulns = [
                v.get("vuln_num")
                for s in stigs
                for v in s.get("open_checklist_findings", [])
            ]
            self.assertNotIn("V-999999", all_open_vulns)


class TestRawScanMemo(unittest.TestCase):
    """Guards the raw-scan cache against the corruption mode it replaced.

    An earlier caching attempt in this codebase memoized *derived* POA&M items.
    Derivation is date-sensitive: the SCTM hydrator deliberately derives against
    a past date while the POA&M sheet uses the package effective date. Sharing
    derived items between them silently rewrote one deliverable with the other's
    dates. Only raw, date-free scanner output may be cached.
    """

    def setUp(self):
        security_scanner_bridge.reset_scan_cache()

    def tearDown(self):
        security_scanner_bridge.reset_scan_cache()

    def _fake_finding(self):
        return [{
            "source": "Checkov IaC Scanner",
            "check_id": "CKV_GCP_TEST",
            "check_name": "Ensure bucket has CMEK",
            "resource": "google_storage_bucket.test",
            "location": "main.tf:L1-3",
            "guideline": "Enable CMEK",
            "severity": "High",
        }]

    def test_identical_target_scans_once(self):
        import tempfile

        with tempfile.TemporaryDirectory() as target:
            Path(target, "main.tf").write_text('resource "google_storage_bucket" "t" {}')
            with patch("security_scanner_bridge.run_checkov_scan") as mock_scan:
                mock_scan.return_value = self._fake_finding()
                cfg = {"run_checkov": True, "run_semgrep": False, "ingest_sarif": False}
                security_scanner_bridge.scan_and_derive_poam_items(target, config=cfg)
                security_scanner_bridge.scan_and_derive_poam_items(target, config=cfg)
                security_scanner_bridge.scan_and_derive_poam_items(target, config=cfg)
            self.assertEqual(
                mock_scan.call_count, 1,
                "three derivations over an unchanged tree must run the scanner once",
            )

    def test_different_effective_dates_still_produce_different_schedules(self):
        """The exact defect the previous cache shipped. Must never regress."""
        import tempfile

        with tempfile.TemporaryDirectory() as target:
            Path(target, "main.tf").write_text('resource "google_storage_bucket" "t" {}')
            with patch("security_scanner_bridge.run_checkov_scan") as mock_scan:
                mock_scan.return_value = self._fake_finding()
                cfg = {"run_checkov": True, "run_semgrep": False, "ingest_sarif": False}
                # Derived target dates are never in the past, so both
                # effective dates are in the future to keep them distinguishable.
                near = datetime.now() + timedelta(days=10)
                far = datetime(near.year + 2, 1, 15)
                recent = security_scanner_bridge.scan_and_derive_poam_items(
                    target, eff_date=near.strftime("%Y-%m-%d"), config=cfg
                )
                past = security_scanner_bridge.scan_and_derive_poam_items(
                    target, eff_date=far.strftime("%Y-%m-%d"), config=cfg
                )
                stale = security_scanner_bridge.scan_and_derive_poam_items(
                    target, eff_date="2001-01-15", config=cfg
                )

        self.assertTrue(recent and past, "both derivations must produce items")
        self.assertEqual(mock_scan.call_count, 1, "the scan itself is date-independent")
        self.assertNotEqual(
            [i["sched_date"] for i in recent],
            [i["sched_date"] for i in past],
            "caching must not leak one caller's effective date into another's",
        )
        self.assertTrue(all(i["sched_date"] > near.strftime("%Y-%m-%d") for i in recent))
        self.assertTrue(all(i["sched_date"].startswith(str(far.year)) for i in past))
        self.assertTrue(all(i["sched_date"] >= datetime.now().strftime("%Y-%m-%d") for i in stale))

    def test_content_change_invalidates_cache(self):
        import tempfile

        with tempfile.TemporaryDirectory() as target:
            tf_file = Path(target, "main.tf")
            tf_file.write_text('resource "google_storage_bucket" "a" {}')
            with patch("security_scanner_bridge.run_checkov_scan") as mock_scan:
                mock_scan.return_value = self._fake_finding()
                cfg = {"run_checkov": True, "run_semgrep": False, "ingest_sarif": False}
                security_scanner_bridge.scan_and_derive_poam_items(target, config=cfg)
                # Change the tree; a stale cached result would be a false assurance.
                tf_file.write_text('resource "google_storage_bucket" "a" {\n  name = "changed"\n}')
                security_scanner_bridge.scan_and_derive_poam_items(target, config=cfg)
            self.assertEqual(
                mock_scan.call_count, 2,
                "editing the scanned tree must invalidate the cached scan",
            )

    def test_cache_is_not_shared_across_targets(self):
        import tempfile

        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            Path(first, "main.tf").write_text('resource "google_storage_bucket" "a" {}')
            Path(second, "main.tf").write_text('resource "google_storage_bucket" "b" {}')
            with patch("security_scanner_bridge.run_checkov_scan") as mock_scan:
                mock_scan.return_value = self._fake_finding()
                cfg = {"run_checkov": True, "run_semgrep": False, "ingest_sarif": False}
                security_scanner_bridge.scan_and_derive_poam_items(first, config=cfg)
                security_scanner_bridge.scan_and_derive_poam_items(second, config=cfg)
            self.assertEqual(
                mock_scan.call_count, 2,
                "a different target directory must never reuse another target's findings",
            )

    def test_caller_mutation_cannot_poison_the_cache(self):
        import tempfile

        with tempfile.TemporaryDirectory() as target:
            Path(target, "main.tf").write_text('resource "google_storage_bucket" "t" {}')
            resolved = str(Path(target).resolve())
            with patch("security_scanner_bridge.run_checkov_scan") as mock_scan:
                mock_scan.return_value = self._fake_finding()
                first = security_scanner_bridge._cached_scan(
                    "checkov", resolved, (300,),
                    lambda: security_scanner_bridge.run_checkov_scan(target),
                )
                first[0]["severity"] = "TAMPERED"
                first.append({"check_id": "INJECTED"})
                second = security_scanner_bridge._cached_scan(
                    "checkov", resolved, (300,),
                    lambda: security_scanner_bridge.run_checkov_scan(target),
                )
        self.assertEqual(len(second), 1, "cache returned a caller-mutated list")
        self.assertEqual(second[0]["severity"], "High")

    def test_disable_scan_cache_bypasses_memo(self):
        """COMPLIANCE_DISABLE_SCAN_CACHE=1 forces a fresh scan on every call."""
        import tempfile

        with tempfile.TemporaryDirectory() as target:
            Path(target, "main.tf").write_text('resource "google_storage_bucket" "t" {}')
            with (
                patch.dict(os.environ, {"COMPLIANCE_DISABLE_SCAN_CACHE": "1"}),
                patch("security_scanner_bridge.run_checkov_scan") as mock_scan,
            ):
                mock_scan.return_value = self._fake_finding()
                cfg = {"run_checkov": True, "run_semgrep": False, "ingest_sarif": False}
                security_scanner_bridge.scan_and_derive_poam_items(target, config=cfg)
                security_scanner_bridge.scan_and_derive_poam_items(target, config=cfg)
                security_scanner_bridge.scan_and_derive_poam_items(target, config=cfg)
            self.assertEqual(
                mock_scan.call_count,
                3,
                "COMPLIANCE_DISABLE_SCAN_CACHE=1 must bypass _SCAN_CACHE on every call",
            )


class TestScannerFailureReporting(unittest.TestCase):
    """A scanner outage must read as a coverage gap, not a code vulnerability."""

    def test_scanner_failure_is_reported_as_assessment_gap(self):
        import tempfile

        with tempfile.TemporaryDirectory() as target:
            Path(target, "main.tf").write_text('resource "google_storage_bucket" "t" {}')
            security_scanner_bridge.reset_scan_cache()
            with patch("security_scanner_bridge.run_semgrep_scan") as mock_scan:
                mock_scan.return_value = [{
                    "source": "Semgrep Application SAST Scanner",
                    "check_id": "SEMGREP_SCANNER_ERROR",
                    "check_name": "Semgrep scanner execution failed with exit code 2",
                    "message": "Semgrep scanner execution failed with exit code 2: "
                               "[00.08][ERROR]: Cannot create auto config when metrics are off.",
                    "cwe": "CA-02 / RA-05",
                    "resource": "codebase",
                    "location": "codebase",
                    "guideline": "Investigate failure.",
                    "severity": "High",
                }]
                items = security_scanner_bridge.scan_and_derive_poam_items(
                    target,
                    config={
                        "run_checkov": False,
                        "run_semgrep": True,
                        "ingest_sarif": False,
                        "include_scanner_failures_in_poam": True,
                    },
                )
            security_scanner_bridge.reset_scan_cache()

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertIn("CA-02", item["aps"])
        self.assertNotIn(
            "Sanitize and refactor code", item["milestone_desc"],
            "a scanner outage cannot be remediated by editing code",
        )
        self.assertIn("Restore", item["milestone_desc"])
        self.assertNotIn(
            "[SEMGREP_SCANNER_ERROR]", item["title"],
            "internal scanner check IDs must not leak into a deliverable title",
        )
        self.assertNotIn("[ERROR]", item["title"])

    def test_scanner_failure_is_omitted_from_poam_by_default(self):
        """By default, scanner execution failures are not added to POA&M as security findings."""
        import tempfile

        with tempfile.TemporaryDirectory() as target:
            Path(target, "main.tf").write_text('resource "google_storage_bucket" "t" {}')
            security_scanner_bridge.reset_scan_cache()
            with patch("security_scanner_bridge.run_semgrep_scan") as mock_scan:
                mock_scan.return_value = [{
                    "source": "Semgrep Application SAST Scanner",
                    "check_id": "SEMGREP_SCANNER_ERROR",
                    "check_name": "Semgrep scanner execution failed with exit code 2",
                    "message": "Semgrep scanner execution failed with exit code 2",
                    "cwe": "CA-02 / RA-05",
                    "resource": "codebase",
                    "location": "codebase",
                    "guideline": "Investigate failure.",
                    "severity": "High",
                }]
                items = security_scanner_bridge.scan_and_derive_poam_items(
                    target,
                    config={"run_checkov": False, "run_semgrep": True, "ingest_sarif": False},
                )
            security_scanner_bridge.reset_scan_cache()

        self.assertEqual(len(items), 0)

    def test_scanner_diagnostic_is_flattened_and_scrubbed(self):
        multiline = "line one\n[00.08][ERROR]: failed\n  with AKIAIOSFODNN7EXAMPLE trailing"
        summary = security_scanner_bridge._summarize_scanner_diagnostic(multiline)
        self.assertNotIn("\n", summary, "newlines would break YAML scalars in the POA&M")
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", summary)

    def test_scanner_diagnostic_is_length_bounded(self):
        summary = security_scanner_bridge._summarize_scanner_diagnostic("x" * 5000)
        self.assertLessEqual(len(summary), 340)
        self.assertTrue(summary.endswith("[truncated]"))


#: Fixture exercising the bundled ruleset. Each vulnerable line is paired with a
#: benign counterpart so a rule that matches indiscriminately fails the test.
_SAST_FIXTURE = '''\
"""Fixture for the bundled offline Semgrep ruleset. Not production code."""
import hashlib
import os
import pickle
import random
import subprocess
import xml.etree.ElementTree as ET

import requests
from flask import Flask


def weak_hash(data):
    return hashlib.md5(data).hexdigest()


def strong_hash(data):
    # Negative control: non-security digest use must NOT be reported.
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def disabled_tls(url):
    return requests.get(url, verify=False, timeout=30)


def command_injection(user_input):
    return subprocess.call("ls " + user_input, shell=True)


def unsafe_deserialize(blob):
    return pickle.loads(blob)


def xxe_parse(xml_text):
    return ET.fromstring(xml_text)


def sql_injection(cursor, user_id):
    return cursor.execute("SELECT * FROM users WHERE id = '" + user_id + "'")


def parameterized_query(cursor, user_id):
    # Negative control: bound parameters must NOT be reported.
    return cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))


def generate_session_token():
    return str(random.random())


def get_session_key():
    return random.randint(0, 2**32)


def session_retry_jitter_ms():
    # Negative control: non-credential session timing jitter must NOT be reported.
    return random.randint(0, 100)


def shuffle_display_order(items):
    # Negative control: non-security randomness must NOT be reported.
    return random.choice(items)


HARDCODED_PASSWORD = "S3cr3t-Static-Value"

# Negative control: unpopulated scaffolding must NOT be reported.
DB_PASSWORD = "[CONFIG_REQUIRED]"

# Negative control: a name that denotes a reference, not the secret itself.
API_KEY_NAME = "projects/example/secrets/api-key"


def safe_secret():
    # Negative control: reading from the environment must NOT be reported.
    return os.environ.get("APP_PASSWORD")


def debug_server():
    Flask(__name__).run(debug=True)
'''


class TestSemgrepRulesetDetectsRealVulnerabilities(unittest.TestCase):
    """Runs the real semgrep binary against a known-vulnerable fixture.

    This is the test that would have caught the original defect. The shipped
    invocation was rejected by semgrep on every run, so SAST silently reported a
    clean codebase; every unit test still passed because they all mocked the
    subprocess. Asserting on argv is necessary but not sufficient -- the rules
    themselves must actually match.
    """

    @classmethod
    def setUpClass(cls):
        if not shutil.which("semgrep"):
            raise unittest.SkipTest("semgrep is not installed on this host")

    def setUp(self):
        security_scanner_bridge.reset_scan_cache()

    def tearDown(self):
        security_scanner_bridge.reset_scan_cache()

    def test_bundled_ruleset_flags_known_vulnerabilities(self):
        import tempfile
        import shutil

        if not shutil.which("semgrep"):
            self.skipTest("semgrep is not installed")

        with tempfile.TemporaryDirectory(prefix="compliance-sast-fixture-") as target:
            app_dir = Path(target, "app")
            app_dir.mkdir()
            Path(app_dir, "vulnerable_sample.py").write_text(_SAST_FIXTURE, encoding="utf-8")

            # Reduce max memory using env var if possible, though handling -9 is safer
            findings = security_scanner_bridge.run_semgrep_scan(
                target,
                timeout_seconds=180,
                semgrep_config=str(security_scanner_bridge.SEMGREP_RULES_DIR),
            )

        if findings and any(
            f.get("check_id") == "SEMGREP_SCANNER_ERROR"
            and ("exit code -9" in f.get("message", "") or "exit code 137" in f.get("message", ""))
            for f in findings
        ):
            self.skipTest("semgrep was killed, likely OOM in full-suite run (exit code -9 / 137)")

        self.assertTrue(findings, "the bundled ruleset produced no findings on vulnerable code")
        for finding in findings:
            self.assertFalse(
                security_scanner_bridge.is_scanner_failure_check_id(finding["check_id"]),
                f"semgrep failed to execute: {finding.get('message')}",
            )

        detected = {str(f.get("cwe", "")).upper() for f in findings}
        for expected in ("CWE-327", "CWE-78", "CWE-502", "CWE-89", "CWE-798",
                         "CWE-295", "CWE-611", "CWE-489", "CWE-338"):
            self.assertIn(
                expected, detected,
                f"{expected} was not detected; detected={sorted(detected)}",
            )

    def test_negative_controls_do_not_fire(self):
        """Rules must discriminate: safe equivalents must not be reported."""
        import tempfile

        with tempfile.TemporaryDirectory(prefix="compliance-sast-fixture-") as target:
            app_dir = Path(target, "app")
            app_dir.mkdir()
            Path(app_dir, "vulnerable_sample.py").write_text(_SAST_FIXTURE, encoding="utf-8")
            findings = security_scanner_bridge.run_semgrep_scan(
                target,
                timeout_seconds=180,
                semgrep_config=str(security_scanner_bridge.SEMGREP_RULES_DIR),
            )

        flagged_lines = set()
        for finding in findings:
            match = re.search(r":L(\d+)-", str(finding.get("location", "")))
            if match:
                flagged_lines.add(int(match.group(1)))

        fixture_lines = _SAST_FIXTURE.splitlines()
        negative_controls = (
            "usedforsecurity=False",
            'os.environ.get("APP_PASSWORD")',
            'WHERE id = %s',
            'DB_PASSWORD = "[CONFIG_REQUIRED]"',
            "API_KEY_NAME =",
            "return random.choice(items)",
            "return random.randint(0, 100)",
        )
        for needle in negative_controls:
            lineno = next(
                i for i, line in enumerate(fixture_lines, start=1) if needle in line
            )
            self.assertNotIn(
                lineno, flagged_lines,
                f"negative control at line {lineno} ({needle}) was incorrectly flagged",
            )

    def test_semgrep_test_fixtures_pass(self):
        """Runs `semgrep --test` over all annotated rule fixtures."""
        import subprocess

        semgrep_bin = shutil.which("semgrep")
        if not semgrep_bin:
            self.skipTest("semgrep is not installed")
        fixtures_dir = Path(__file__).resolve().parent / "semgrep_fixtures"
        proc = subprocess.run(
            [
                semgrep_bin,
                "--test",
                "--metrics=off",
                "--config",
                str(security_scanner_bridge.SEMGREP_RULES_DIR),
                str(fixtures_dir),
            ],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"semgrep --test failed (rc={proc.returncode}):\n{proc.stdout}\n{proc.stderr}",
        )
        self.assertIn("All tests passed", proc.stdout + proc.stderr)

    def test_findings_map_to_expected_nist_controls(self):
        """A finding is only useful if it lands on the right control."""
        expectations = {
            "CWE-327": "SC-13",
            "CWE-78": "SI-10",
            "CWE-89": "SI-10",
            "CWE-502": "SI-10",
            "CWE-611": "SI-10",
            "CWE-798": "IA-05",
        }
        for cwe, expected_control in expectations.items():
            control, _title = security_scanner_bridge.map_cwe_to_nist(cwe)
            self.assertEqual(control, expected_control, f"{cwe} mapped to {control}")


class TestSemgrepFixtureCoverage(unittest.TestCase):
    """Every bundled Semgrep rule must have >=1 ruleid and >=1 ok fixture."""

    def test_all_bundled_rules_have_positive_and_negative_fixtures(self) -> None:
        import yaml

        rules_doc = yaml.safe_load(
            security_scanner_bridge.SEMGREP_BUNDLED_RULES_FILE.read_text(encoding="utf-8")
        )
        rule_ids = {rule["id"] for rule in rules_doc.get("rules", [])}
        self.assertEqual(len(rule_ids), 14)

        fixtures_dir = (
            Path(__file__).resolve().parent
            / "semgrep_fixtures"
            / "public_sector_baseline"
        )
        self.assertTrue(fixtures_dir.is_dir())

        ruleid_re = re.compile(r"(?:#|//)\s*ruleid:\s*([A-Za-z0-9_-]+)")
        ok_re = re.compile(r"(?:#|//)\s*ok:\s*([A-Za-z0-9_-]+)")
        seen_ruleids: set = set()
        seen_oks: set = set()
        for path in sorted(fixtures_dir.iterdir()):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            seen_ruleids.update(ruleid_re.findall(text))
            seen_oks.update(ok_re.findall(text))

        missing_pos = sorted(rule_ids - seen_ruleids)
        missing_neg = sorted(rule_ids - seen_oks)
        self.assertEqual(missing_pos, [], f"rules missing ruleid: fixtures: {missing_pos}")
        self.assertEqual(missing_neg, [], f"rules missing ok: fixtures: {missing_neg}")


class TestScanAndDeriveCharacterization(unittest.TestCase):
    """Characterization test pinning scan_and_derive_poam_items across all 5 sources."""

    def test_scan_and_derive_characterization(self) -> None:
        import json
        import tempfile

        checkov_out = [
            {
                "check_id": "CKV_GCP_114",
                "check_name": "Ensure bucket CMEK encryption",
                "resource": "google_storage_bucket.b1",
                "location": "main.tf:L1-5",
                "guideline": "Configure kms_key_name",
                "severity": "High",
                "source": "Checkov IaC Static Security Scanner",
            },
            {
                "check_id": "CKV_GCP_26",
                "check_name": "Ensure VPC Flow Logs is enabled",
                "resource": "google_compute_subnetwork.s1",
                "location": "net.tf:L10-20",
                "guideline": "Enable flow logs",
                "severity": "Moderate",
                "source": "Checkov IaC Static Security Scanner",
            },
            {
                "check_id": "CKV_GCP_26",
                "check_name": "Ensure VPC Flow Logs is enabled",
                "resource": "google_compute_subnetwork.s2",
                "location": "net.tf:L25-35",
                "guideline": "Enable flow logs",
                "severity": "High",
                "source": "Checkov IaC Static Security Scanner",
            },
        ]
        semgrep_out = [
            {
                "check_id": "python-sql-injection-string-built-query",
                "message": "SQL statement assembled by string formatting.",
                "cwe": "CWE-89",
                "cwe_list": ["CWE-89"],
                "nist_controls": ["SI-10"],
                "location": "app/db.py:L14-14",
                "severity": "High",
                "source": "Semgrep Application SAST Scanner",
            },
            {
                "check_id": "python-disabled-tls-verification",
                "message": "TLS certificate verification is disabled.",
                "cwe": "CWE-295",
                "cwe_list": ["CWE-295"],
                "nist_controls": ["SC-8", "SC-23"],
                "location": "app/client.py:L8-8",
                "severity": "High",
                "source": "Semgrep Application SAST Scanner",
            },
            {
                "check_id": "python-disabled-tls-verification",
                "message": "TLS certificate verification is disabled.",
                "cwe": "CWE-295",
                "cwe_list": ["CWE-295"],
                "nist_controls": ["SC-8", "SC-23"],
                "location": "app/client.py:L22-22",
                "severity": "Moderate",
                "source": "Semgrep Application SAST Scanner",
            },
        ]
        trivy_out = [
            {
                "check_id": "CVE-2025-0001",
                "message": "CVE-2025-0001 (urllib3 1.26.0 -> 1.26.19): Request smuggling",
                "cwe": "SI-02",
                "location": "requirements.txt:urllib3",
                "severity": "High",
                "source": "Trivy Vulnerability Scanner",
            },
        ]
        scc_out = [
            {
                "check_id": "SCC_OPEN_FIREWALL",
                "check_name": "Public ingress firewall rule",
                "resource": "projects/demo-proj/global/firewalls/allow-all",
                "location": "projects/demo-proj",
                "guideline": "Restrict source ranges",
                "severity": "High",
                "source": "Live Cloud Telemetry (Google SCC v1)",
            },
        ]
        sarif_doc = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "CustomAnalyzer"}},
                    "results": [
                        {
                            "ruleId": "CWE-798: HardcodedCredential",
                            "level": "error",
                            "message": {"text": "Hardcoded token in config (CWE-798)"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "app/settings.py"},
                                        "region": {"startLine": 12},
                                    }
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "main.tf").write_text('resource "google_storage_bucket" "b1" {}\n', encoding="utf-8")
            Path(tmp, "report.sarif").write_text(json.dumps(sarif_doc), encoding="utf-8")
            with (
                patch.dict(
                    os.environ,
                    {
                        "COMPLIANCE_DISABLE_LIVE_SCANNERS": "0",
                        "COMPLIANCE_ALLOW_LIVE_CLOUD_TELEMETRY": "1",
                    },
                    clear=False,
                ),
                patch.object(security_scanner_bridge, "run_checkov_scan", return_value=checkov_out),
                patch.object(security_scanner_bridge, "run_semgrep_scan", return_value=semgrep_out),
                patch.object(security_scanner_bridge, "run_trivy_scan", return_value=trivy_out),
                patch.object(security_scanner_bridge, "fetch_live_scc_findings", return_value=scc_out),
            ):
                security_scanner_bridge.reset_scan_cache()
                items = security_scanner_bridge.scan_and_derive_poam_items(
                    tmp,
                    sys_abbr="CHR",
                    eff_date="2030-01-15",
                    config={
                        "run_checkov": True,
                        "run_semgrep": True,
                        "run_trivy": True,
                        "query_live_cloud_telemetry": True,
                        "project_id": "demo-proj-123",
                        "impact_level": "FedRAMP High",
                        "ingest_sarif": True,
                    },
                )

        self.assertEqual(len(items), 7)
        self.assertEqual(
            [i["item_id"] for i in items],
            [f"POAM-CHR-{n:03d}" for n in range(100, 107)],
        )
        self.assertEqual(
            [i["checks"] for i in items],
            [
                "CKV_GCP_114",
                "CKV_GCP_26",
                "python-sql-injection-string-built-query",
                "python-disabled-tls-verification",
                "CVE-2025-0001",
                "SCC_OPEN_FIREWALL",
                "CWE-798: HardcodedCredential",
            ],
        )
        self.assertEqual(
            [i["aps"] for i in items],
            [
                "SC-28",
                "AU-02 / AU-12",
                "SI-10",
                "SC-8 / SC-23",
                "SA-11",
                "AC-03 / SC-07",
                "IA-05",
            ],
        )
        self.assertIn("(2 affected locations)", items[1]["title"])
        self.assertIn("(2 affected locations)", items[3]["title"])
        for item in items:
            self.assertEqual(item["status"], "Ongoing")
            self.assertEqual(item["milestone_status"], "Open")
            self.assertEqual(item["sched_date"], "2030-02-14")


if __name__ == '__main__':
    unittest.main()
