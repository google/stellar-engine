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

"""Regression tests for --allow-terraform-plan sandboxing and warnings."""

import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Dict, List
import unittest
from unittest import mock

from compliance_engine import extract_system_data


class TerraformPlanTrustTest(unittest.TestCase):
    """Verifies that Terraform execution is opt-in, warned, and env-sandboxed."""

    def test_not_run_without_flag(self) -> None:
        """safe_run_command is never called when allow_terraform_plan is False."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "main.tf").write_text('resource "google_storage_bucket" "b" {}\n', encoding="utf-8")
            (target / ".terraform.lock.hcl").write_text("", encoding="utf-8")
            (target / "tfplan").write_bytes(b"binary-plan-placeholder")
            with mock.patch.object(extract_system_data, "safe_run_command") as mock_run:
                res = extract_system_data.discover_or_generate_terraform_json(
                    target, allow_terraform_plan=False
                )
            self.assertIsNone(res)
            mock_run.assert_not_called()

    def test_sandboxed_env(self) -> None:
        """Child env has HOME/CLOUDSDK_CONFIG/TF_CLI_CONFIG_FILE under temp and empty ADC."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "main.tf").write_text('resource "google_storage_bucket" "b" {}\n', encoding="utf-8")
            (target / ".terraform.lock.hcl").write_text("", encoding="utf-8")
            captured_envs: List[Dict[str, str]] = []

            def _fake_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
                env = dict(kwargs.get("env") or {})
                captured_envs.append(env)
                return subprocess.CompletedProcess(cmd, 0, '{"values": {"root_module": {"resources": []}}}', "")

            with mock.patch.object(extract_system_data, "_find_trusted_binary", return_value="/usr/bin/terraform"), \
                    mock.patch.object(extract_system_data, "safe_run_command", side_effect=_fake_run), \
                    mock.patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/secret/adc.json"}):
                extract_system_data.discover_or_generate_terraform_json(
                    target, allow_terraform_plan=True
                )

            self.assertTrue(captured_envs, "Expected safe_run_command to be invoked when allow_terraform_plan=True")
            env = captured_envs[0]
            temp_root = os.path.realpath(tempfile.gettempdir())
            for key in ("HOME", "CLOUDSDK_CONFIG", "TF_CLI_CONFIG_FILE"):
                self.assertIn(key, env, f"Expected {key} in Terraform child environment")
                self.assertTrue(
                    os.path.realpath(env[key]).startswith(temp_root),
                    f"Expected {key}={env[key]!r} to reside under temp dir {temp_root!r}",
                )
            self.assertEqual(env.get("GOOGLE_APPLICATION_CREDENTIALS", ""), "")

            # Also verify _terraform_env() rejectstarget .terraform/providers plugin execution by default
            plugins_dir = target / ".terraform" / "providers" / "registry.terraform.io"
            plugins_dir.mkdir(parents=True)
            (plugins_dir / "terraform-provider-custom").write_text("#!/bin/sh\n", encoding="utf-8")
            captured_envs.clear()
            with mock.patch.object(extract_system_data, "_find_trusted_binary", return_value="/usr/bin/terraform"), \
                    mock.patch.object(extract_system_data, "safe_run_command", side_effect=_fake_run):
                res = extract_system_data.discover_or_generate_terraform_json(
                    target, allow_terraform_plan=True
                )
            self.assertIsNone(res)
            self.assertEqual(captured_envs, [], "Target with .terraform/providers must be refused by default")

    def test_warning_printed(self) -> None:
        """Running with allow_terraform_plan=True logs/prints an explicit untrusted-workspace risk warning."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "main.tf").write_text('resource "google_storage_bucket" "b" {}\n', encoding="utf-8")
            (target / ".terraform.lock.hcl").write_text("", encoding="utf-8")
            fake_cp = subprocess.CompletedProcess(["terraform"], 1, "", "error")
            with mock.patch.object(extract_system_data, "_find_trusted_binary", return_value="/usr/bin/terraform"), \
                    mock.patch.object(extract_system_data, "safe_run_command", return_value=fake_cp), \
                    self.assertLogs("extract_system_data", level="WARNING") as logs:
                extract_system_data.discover_or_generate_terraform_json(
                    target, allow_terraform_plan=True
                )
            joined = "\n".join(logs.output)
            self.assertRegex(joined, r"(?i)WARNING.*allow-terraform-plan|provider plugins|untrusted")


if __name__ == "__main__":
    unittest.main()
