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

"""Hardening tests for :mod:`extract_system_data` external command execution."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root / "scripts"))

from extract_system_data import (  # noqa: E402
    MAX_SUBPROCESS_OUTPUT_BYTES,
    _backup_existing_inventory,
    _sanitized_path_env,
    extract_system_inventory,
    safe_run_command,
)


class TestHardeningExtract(unittest.TestCase):
    """Verifies the external command boundary in extract_system_data."""

    def test_oversize_output_is_rejected_not_truncated(self) -> None:
        """Oversize stdout must raise, never return a silently clipped payload.

        This helper feeds `terraform show -json` output into the inventory. A
        truncated payload would either fail to parse or, worse, parse as a smaller
        system boundary and under-report the accreditation scope, so the only safe
        response is to refuse the result outright.
        """
        oversize = MAX_SUBPROCESS_OUTPUT_BYTES + 1024
        cmd = [sys.executable, "-c", f"print('a' * {oversize})"]
        with self.assertRaises(MemoryError):
            safe_run_command(cmd, timeout=30)

    def test_output_under_the_bound_is_returned_intact(self) -> None:
        """Output within the budget must be returned byte-for-byte."""
        payload = "b" * 1024
        cmd = [sys.executable, "-c", f"print('{payload}')"]
        result = safe_run_command(cmd, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), payload)

    def test_caller_command_list_is_not_mutated(self) -> None:
        """Resolving the binary must not rewrite the caller's list in place."""
        cmd = ["echo", "hello"]
        original = list(cmd)
        safe_run_command(cmd, timeout=10)
        self.assertEqual(
            cmd,
            original,
            "safe_run_command must not mutate the caller's command vector",
        )

    def test_path_sanitization_keeps_command_runnable(self) -> None:
        """A sanitized PATH must still resolve genuine system binaries."""
        result = safe_run_command(["echo", "hello"], timeout=10)
        self.assertIn("hello", result.stdout)

    def test_sanitized_path_excludes_cwd_and_relative_entries(self) -> None:
        """The search path must exclude the CWD and any relative entry.

        A repository under analysis is untrusted input. If its directory stayed on
        PATH, a file named `terraform` committed to that repository could be
        executed in place of the real binary (CWE-426 untrusted search path).
        """
        cwd = str(Path.cwd().resolve())
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = os.pathsep.join([cwd, "relative/bin", "", "/usr/bin"])
        try:
            entries = _sanitized_path_env()["PATH"].split(os.pathsep)
        finally:
            os.environ["PATH"] = original_path

        self.assertNotIn(cwd, entries)
        self.assertNotIn("relative/bin", entries)
        self.assertNotIn("", entries)
        self.assertIn("/usr/bin", entries)

    def test_path_prefix_is_not_confused_with_parent_directory(self) -> None:
        """'/work' is a string prefix of '/workspace' but is not its parent.

        The previous implementation filtered with str.startswith, which would drop
        unrelated sibling directories whose names merely began with the CWD string.
        """
        original_path = os.environ.get("PATH", "")
        cwd = Path.cwd().resolve()
        sibling = str(cwd) + "-sibling-not-a-child"
        os.environ["PATH"] = os.pathsep.join([sibling, "/usr/bin"])
        try:
            entries = _sanitized_path_env()["PATH"].split(os.pathsep)
        finally:
            os.environ["PATH"] = original_path

        self.assertIn(
            sibling,
            entries,
            "A sibling directory sharing a name prefix must not be filtered out",
        )

    def test_empty_command_is_rejected(self) -> None:
        """An empty argument vector must fail closed."""
        with self.assertRaises(ValueError):
            safe_run_command([], timeout=5)

    def test_unresolvable_binary_raises_file_not_found(self) -> None:
        """A binary absent from the sanitized PATH must fail fast and loudly."""
        with self.assertRaises(FileNotFoundError):
            safe_run_command(["definitely-not-a-real-binary-xyz"], timeout=5)

    def test_negative_retries_rejected(self) -> None:
        """A nonsensical retry budget must be rejected rather than silently coerced."""
        with self.assertRaises(ValueError):
            safe_run_command(["echo", "hi"], timeout=5, retries=-1)


@unittest.skipUnless(hasattr(os, "symlink"), "requires symbolic link support")
class TestInventoryBackupSymlinks(unittest.TestCase):
    """The inventory backup must never follow links planted in the target folder (CWE-59).

    A contributor-supplied blueprint could ship ``system_inventory.json.bak`` as a link to a
    file outside the folder (for example a git hook). Following it would let target-folder
    content overwrite that file when an operator runs the extractor.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.target = self.root / "blueprint"
        self.target.mkdir()
        self.outside = self.root / "outside.txt"
        self.outside.write_text("ORIGINAL", encoding="utf-8")
        self.inventory = self.target / "system_inventory.json"
        self.backup = self.target / "system_inventory.json.bak"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_symlinked_backup_path_is_replaced_not_followed(self) -> None:
        self.inventory.write_text('{"prior": true}', encoding="utf-8")
        os.chmod(self.inventory, 0o755)
        os.symlink(self.outside, self.backup)

        _backup_existing_inventory(str(self.inventory), self.target)

        self.assertEqual(self.outside.read_text(encoding="utf-8"), "ORIGINAL")
        self.assertFalse(self.backup.is_symlink())
        self.assertEqual(self.backup.read_text(encoding="utf-8"), '{"prior": true}')
        self.assertFalse(os.stat(self.backup).st_mode & 0o111, "backup must not inherit execute bits")

    def test_symlinked_inventory_is_refused(self) -> None:
        os.symlink(self.outside, self.inventory)
        with self.assertRaises(PermissionError):
            _backup_existing_inventory(str(self.inventory), self.target)
        self.assertFalse(os.path.lexists(self.backup))
        self.assertEqual(self.outside.read_text(encoding="utf-8"), "ORIGINAL")

    def test_missing_inventory_is_a_no_op(self) -> None:
        _backup_existing_inventory(str(self.inventory), self.target)
        self.assertFalse(os.path.lexists(self.backup))

    def test_extraction_does_not_write_through_planted_backup_link(self) -> None:
        (self.target / "main.tf").write_text(
            'resource "google_storage_bucket" "logs" {\n  name     = "logs"\n  location = "US"\n}\n',
            encoding="utf-8",
        )
        self.inventory.write_text("{}", encoding="utf-8")
        os.symlink(self.outside, self.backup)

        extract_system_inventory(str(self.target))

        self.assertEqual(self.outside.read_text(encoding="utf-8"), "ORIGINAL")
        self.assertFalse(self.backup.is_symlink())
        self.assertEqual(self.backup.read_text(encoding="utf-8"), "{}")


class TestAuditRemediationsExtractAndHelpers(unittest.TestCase):
    """Covers security & correctness remediations across file_helpers, safe_xml, and extract_system_data."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.target = self.root / "blueprint"
        self.target.mkdir()
        self.outside = self.root / "outside"
        self.outside.mkdir()

    @unittest.skipUnless(hasattr(os, "symlink"), "requires symbolic link support")
    def test_load_all_system_configs_skips_symlinked_config_dirs_and_files(self) -> None:
        """Symlinked config directories or files escaping target_dir must be ignored."""
        from extract_system_data import load_all_system_configs

        (self.outside / "variables.yaml").write_text(
            "system_information:\n  system_name: LEAKED_OUTSIDE_NAME\n",
            encoding="utf-8",
        )
        os.symlink(self.outside, self.target / "config")
        os.symlink(self.outside / "variables.yaml", self.target / "compliance_config.yaml")

        cfg = load_all_system_configs(str(self.target))
        self.assertNotEqual(
            cfg.get("system_information", {}).get("system_name"),
            "LEAKED_OUTSIDE_NAME",
        )

    @unittest.skipUnless(hasattr(os, "symlink"), "requires symbolic link support")
    def test_discover_plan_and_sbom_reject_symlinks_and_boundary_escapes(self) -> None:
        """discover_or_generate_terraform_json and discover_or_generate_sbom reject symlinks & outside paths."""
        from extract_system_data import (
            discover_or_generate_sbom,
            discover_or_generate_terraform_json,
        )

        outside_plan = self.outside / "plan.json"
        outside_plan.write_text('{"format_version": "1.0", "planned_values": {}}', encoding="utf-8")
        outside_sbom = self.outside / "sbom.json"
        outside_sbom.write_text('{"bomFormat": "CycloneDX", "components": [{"name": "leaked"}]}', encoding="utf-8")

        os.symlink(outside_plan, self.target / "tfplan.json")
        os.symlink(outside_sbom, self.target / "sbom.json")

        self.assertIsNone(
            discover_or_generate_terraform_json(
                self.target,
                user_config={"terraform_plan_path": str(outside_plan)},
            )
        )
        self.assertIsNone(
            discover_or_generate_sbom(
                self.target,
                user_config={"sbom_path": str(outside_sbom)},
            )
        )

    def test_terraform_json_redacts_sensitive_values_mask(self) -> None:
        """sensitive_values mask in Terraform JSON must redact matching values."""
        from extract_system_data import ingest_terraform_json

        tf_json = {
            "format_version": "1.2",
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "address": "google_sql_database_instance.main",
                            "type": "google_sql_database_instance",
                            "name": "main",
                            "values": {
                                "name": "prod-sql",
                                "database_version": "POSTGRES_15",
                                "root_password": "unmatched-custom-secret-value",
                            },
                            "sensitive_values": {
                                "root_password": True,
                            },
                        }
                    ]
                }
            },
        }
        scanned = ingest_terraform_json(tf_json, target_dir=str(self.target))
        serialized = str(scanned)
        self.assertNotIn("unmatched-custom-secret-value", serialized)

    @unittest.skipUnless(hasattr(os, "symlink"), "requires symbolic link support")
    def test_write_helpers_reject_symlinked_parent_directory_escape(self) -> None:
        """write_text_file and write_json_file must reject symlinked parent dirs escaping boundary."""
        from file_helpers import write_json_file, write_text_file

        escape_dir = self.target / "linked_out"
        os.symlink(self.outside, escape_dir)

        with self.assertRaises(PermissionError):
            write_text_file(escape_dir / "pwn.txt", "data", allowed_boundary=self.target)
        with self.assertRaises(PermissionError):
            write_json_file(escape_dir / "pwn.json", {"k": "v"}, allowed_boundary=self.target)
        self.assertFalse((self.outside / "pwn.txt").exists())
        self.assertFalse((self.outside / "pwn.json").exists())

    def test_safe_xml_rejects_doctype_and_entity_declarations(self) -> None:
        """safe_xml must reject XML containing <!DOCTYPE or <!ENTITY."""
        from compliance_engine import safe_xml

        xxe_payload = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE lolz [<!ENTITY lol "lol">]>'
            "<root>&lol;</root>"
        )
        with self.assertRaises((safe_xml.DefusedXmlException, safe_xml.ParseError)):
            safe_xml.fromstring(xxe_payload)

    def test_parse_yaml_safe_enforces_config_size_ceiling(self) -> None:
        """VULN-12b: parse_yaml_safe rejects YAML payloads exceeding MAX_YAML_BYTES."""
        import file_helpers

        with mock.patch.object(file_helpers, "MAX_YAML_BYTES", 1024):
            oversize_yaml = "key: " + ("a" * 1200)
            with self.assertRaises(ValueError):
                file_helpers.parse_yaml_safe(oversize_yaml)

    def test_deep_scan_app_files_pom_xml_does_not_clobber_walk_root(self) -> None:
        """Parsing pom.xml must not overwrite os.walk's root directory variable."""
        from extract_system_data import deep_scan_app_files

        app_dir = self.target / "java_service"
        app_dir.mkdir()
        (app_dir / "pom.xml").write_text(
            "<project><artifactId>billing-api</artifactId><version>2.1.0</version></project>",
            encoding="utf-8",
        )
        (app_dir / "requirements.txt").write_text("fastapi==0.110.0\n", encoding="utf-8")

        app_data = deep_scan_app_files(str(self.target))
        app_names = [a["name"] for a in app_data["applications"]]
        pkg_names = [p["name"] for p in app_data["software_packages"]]
        self.assertIn("billing-api", app_names)
        self.assertIn("fastapi", pkg_names)

    def test_deep_scan_tf_files_firewall_module_and_unhardcoded_vm_defaults(self) -> None:
        """net-vpc-firewall goes to firewall_rules and compute-vm does not fabricate Shielded VM."""
        from extract_system_data import deep_scan_tf_files

        (self.target / "main.tf").write_text(
            '''
            module "firewall" {
              source  = "../../modules/net-vpc-firewall"
              network = "prod-vpc"
              ingress_rules = {
                allow-ssh-iap = {
                  description   = "Allow SSH from IAP"
                  source_ranges = ["35.235.240.0/20"]
                  rules         = [{ protocol = "tcp", ports = [22] }]
                }
              }
            }

            module "simple_vm" {
              source        = "../../modules/compute-vm"
              name          = "worker-01"
              instance_type = "e2-medium"
            }
            ''',
            encoding="utf-8",
        )
        scanned = deep_scan_tf_files(str(self.target))
        self.assertNotIn("firewall", scanned["networks"])
        fw_names = [r["name"] for r in scanned["firewall_rules"]]
        self.assertIn("allow-ssh-iap", fw_names)
        self.assertEqual(len(scanned["compute_instances"]), 1)
        vm = scanned["compute_instances"][0]
        self.assertEqual(vm["name"], "worker-01")
        self.assertIsNone(vm["shielded_vm"])

    def test_clean_interpolated_string_and_auth_summary_and_symlink_regime(self) -> None:
        """HCL expression unwrapping, auth summary, and regime inference across symlinks."""
        from extract_system_data import clean_interpolated_string

        self.assertEqual(
            clean_interpolated_string('${coalesce(var.custom_name, "default-dataset")}', {}),
            "default-dataset",
        )
        self.assertEqual(
            clean_interpolated_string("${each.key}", {}, default_val="fallback-sa"),
            "fallback-sa",
        )

        # Create a blueprint with IAM bindings and invoke via a fedramp-high symlink path
        il5_dir = self.root / "blueprints" / "il5" / "sample-service"
        il5_dir.mkdir(parents=True)
        (il5_dir / "main.tf").write_text(
            '''
            resource "google_Service_account" "app" {
              account_id = "app-sa"
            }
            resource "google_project_iam_member" "binding" {
              project = "my-proj"
              role    = "roles/run.invoker"
              member  = "serviceAccount:app-sa@my-proj.iam.gserviceaccount.com"
            }
            ''',
            encoding="utf-8",
        )
        fr_parent = self.root / "blueprints" / "fedramp-high"
        fr_parent.mkdir(parents=True)
        fr_link = fr_parent / "sample-service"
        if hasattr(os, "symlink"):
            os.symlink(il5_dir, fr_link)
            inv = extract_system_inventory(str(fr_link))
            self.assertEqual(inv["system_information"]["impact_level"], "FedRAMP High")
            self.assertIn("FedRAMP High", inv["system_information"]["compliance_baseline"])
            self.assertNotEqual(inv["authentication_summary"], "Not Specified in Codebase")
            self.assertNotIn("workspace_path", inv["system_information"])

    def test_first_class_modules_and_child_module_resolution(self) -> None:
        """Test first-class module handling and safe child module HCL resolution."""
        from extract_system_data import deep_scan_tf_files
        from file_helpers import resolve_local_child_module_dir

        repo_root = self.root / "mock-repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        modules_dir = repo_root / "modules"
        modules_dir.mkdir()

        # 1. Create a mock child module with internal resources
        bq_mod = modules_dir / "bigquery-dataset"
        bq_mod.mkdir()
        (bq_mod / "main.tf").write_text(
            '''
            resource "google_bigquery_dataset" "default" {
              dataset_id = var.id
            }
            resource "google_bigquery_table" "table" {
              dataset_id = google_bigquery_dataset.default.dataset_id
              table_id   = "table_1"
            }
            ''',
            encoding="utf-8",
        )

        sa_mod = modules_dir / "iam-service-account"
        sa_mod.mkdir()
        (sa_mod / "main.tf").write_text(
            '''
            resource "google_service_account" "service_account" {
              account_id = var.name
            }
            ''',
            encoding="utf-8",
        )

        bp_dir = repo_root / "blueprints" / "il5" / "bq-test"
        bp_dir.mkdir(parents=True)
        (bp_dir / "main.tf").write_text(
            '''
            module "my_dataset" {
              source     = "../../../modules/bigquery-dataset"
              id         = "audit_logs"
              project_id = "test-project"
            }
            module "my_sa" {
              source     = "../../../modules/iam-service-account"
              name       = "custom-worker"
              project_id = "test-project"
            }
            module "my_secret" {
              source  = "modules/secret-manager"
              secrets = {
                api_token = {
                  locations = ["us-east4"]
                }
              }
            }
            module "my_topic" {
              source = "modules/pubsub"
              name   = "audit-stream"
            }
            module "my_log_bucket" {
              source = "modules/logging-bucket"
              id     = "central-audit-log"
              parent = "test-project"
            }
            ''',
            encoding="utf-8",
        )

        # Verify child module resolver resolves within repo
        resolved_bq = resolve_local_child_module_dir(
            str(bp_dir),
            "../../../modules/bigquery-dataset",
            bp_dir.resolve(),
        )
        self.assertIsNotNone(resolved_bq)
        self.assertEqual(resolved_bq, bq_mod.resolve())

        # Verify resolution rejects escaping beyond repo root
        escaped = resolve_local_child_module_dir(
            str(bp_dir),
            "../../../../../../etc",
            bp_dir.resolve(),
        )
        self.assertIsNone(escaped)

        # Run deep_scan_tf_files and assert modules and synthesized resources
        scanned = deep_scan_tf_files(str(bp_dir))
        self.assertIn("my_dataset", scanned["modules_used"])
        self.assertIn("my_sa", scanned["modules_used"])
        self.assertIn("my_secret", scanned["modules_used"])
        self.assertIn("my_topic", scanned["modules_used"])
        self.assertIn("my_log_bucket", scanned["modules_used"])

        # Check discovered components
        self.assertTrue(any(d.get("name") == "audit_logs" for d in scanned["databases"]))
        self.assertTrue(any(sa.get("name") == "custom-worker" for sa in scanned["service_accounts"]))
        self.assertIn("api_token", scanned.get("secrets", []))
        self.assertIn("audit-stream", scanned.get("pubsub_topics", []))
        self.assertTrue(any(s.get("name") == "central-audit-log" for s in scanned.get("logging_sinks", [])))

        # Check all_resources has primary and child resources
        all_res_types = [r["type"] for r in scanned["all_resources"]]
        self.assertIn("google_bigquery_dataset", all_res_types)
        self.assertIn("google_service_account", all_res_types)
        self.assertIn("google_secret_manager_secret", all_res_types)
        self.assertIn("google_pubsub_topic", all_res_types)
        self.assertIn("google_logging_project_bucket_config", all_res_types)
        # Nested child table resource
        self.assertIn("google_bigquery_table", all_res_types)


if __name__ == "__main__":
    unittest.main()
