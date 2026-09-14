import unittest
import sys
import os
import re
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import security_scanner_bridge
import stig_resolver

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
        resolver = stig_resolver.StigResolver()
        resolver.catalog_path = Path("/nonexistent/catalog.json")
        with self.assertRaises(FileNotFoundError):
            resolver._load_baseline_catalog()


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

    def test_auto_scan_is_default_when_no_config(self):
        argv = self._captured_argv()
        self.assertIn("--config", argv)
        config_value = argv[argv.index("--config") + 1]
        self.assertEqual(config_value, "auto")
        self.assertNotIn(
            "--metrics=off",
            argv,
            "--metrics=off cannot be passed when running with --config auto",
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
            with patch("security_scanner_bridge.shutil.which", return_value="/usr/bin/semgrep"):
                findings = security_scanner_bridge.run_semgrep_scan(
                    target, semgrep_config="/nonexistent/ruleset/dir"
                )
        self.assertEqual(len(findings), 1, "a missing ruleset must not scan to an empty result")
        self.assertEqual(findings[0]["check_id"], "SEMGREP_SCANNER_ERROR")
        self.assertEqual(findings[0]["cwe"], "CA-02 / RA-05")

    def test_auto_config_supported_without_metrics_off(self):
        """'auto' config is passed through and --metrics=off is omitted so auto can run."""
        argv = self._captured_argv(semgrep_config="auto")
        self.assertIn("--config", argv)
        config_value = argv[argv.index("--config") + 1]
        self.assertEqual(config_value, "auto")
        self.assertNotIn(
            "--metrics=off",
            argv,
            "--metrics=off cannot be passed when running with --config auto",
        )
        self.assertIn("--no-git-ignore", argv)

    def test_auto_sentinel_resolves_to_auto(self):
        """'auto' resolves directly to Semgrep's managed 'auto' configuration."""
        config_ref, error = security_scanner_bridge._resolve_semgrep_config("auto")
        self.assertIsNone(error)
        self.assertEqual(config_ref, "auto")

    def test_explicit_override_still_takes_precedence_over_the_bundle(self):
        """An operator pointing at an internal mirror must not be silently overridden."""
        config_ref, error = security_scanner_bridge._resolve_semgrep_config("p/ci")
        self.assertIsNone(error)
        self.assertEqual(config_ref, "p/ci")


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
                recent = security_scanner_bridge.scan_and_derive_poam_items(
                    target, eff_date="2026-09-11", config=cfg
                )
                past = security_scanner_bridge.scan_and_derive_poam_items(
                    target, eff_date="2024-01-15", config=cfg
                )

        self.assertTrue(recent and past, "both derivations must produce items")
        self.assertEqual(mock_scan.call_count, 1, "the scan itself is date-independent")
        self.assertNotEqual(
            [i["sched_date"] for i in recent],
            [i["sched_date"] for i in past],
            "caching must not leak one caller's effective date into another's",
        )
        self.assertTrue(all(i["sched_date"].startswith("2026") for i in recent))
        self.assertTrue(all(i["sched_date"].startswith("2024") for i in past))

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

        with tempfile.TemporaryDirectory(prefix="compliance-sast-fixture-") as target:
            app_dir = Path(target, "app")
            app_dir.mkdir()
            Path(app_dir, "vulnerable_sample.py").write_text(_SAST_FIXTURE, encoding="utf-8")
            findings = security_scanner_bridge.run_semgrep_scan(
                target,
                timeout_seconds=180,
                semgrep_config=str(security_scanner_bridge.SEMGREP_RULES_DIR),
            )

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
        )
        for needle in negative_controls:
            lineno = next(
                i for i, line in enumerate(fixture_lines, start=1) if needle in line
            )
            self.assertNotIn(
                lineno, flagged_lines,
                f"negative control at line {lineno} ({needle}) was incorrectly flagged",
            )

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


if __name__ == '__main__':
    unittest.main()
