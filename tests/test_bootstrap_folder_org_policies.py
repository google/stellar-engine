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

"""Checks Stage 0 folder org policy attachment."""

import pathlib
import re
import unittest

import yaml

_BOOTSTRAP_DIR = (
    pathlib.Path(__file__).resolve().parents[1] / "fast/stages-aw/0-bootstrap"
)
_ORG_TF = _BOOTSTRAP_DIR / "organization.tf"
_PLACEHOLDER_RE = re.compile(r"\$\{[^}]+\}")


def _block(text, header):
    pattern = re.compile(
        r"^" + re.escape(header) + r"\s*\{.*?^\}", re.MULTILINE | re.DOTALL
    )
    match = pattern.search(text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _render_custom_policy_template(text):
    """Simulates templatefile() rendering for custom org policy YAML."""
    rendered = re.sub(
        r"%\{\s*for\s+domain\s+in\s+allowed_domains\s*~?\s*\}\n"
        r"([\s\S]*?)"
        r"%\{\s*endfor\s*~?\s*\}\n?",
        lambda m: m.group(1).replace("${domain}", "C01234567"),
        text,
    )
    rendered = re.sub(
        r"%\{\s*for\s+producer\s+in\s+allowed_vpc_peering_producers\s*~?\s*\}\n"
        r"([\s\S]*?)"
        r"%\{\s*endfor\s*~?\s*\}\n?",
        lambda m: m.group(1).replace(
            "${producer}", "under:folders/832634261155"
        ),
        rendered,
    )
    lines = []
    in_else = False
    for line in rendered.splitlines():
        stripped = line.strip()
        if stripped.startswith("%{ if "):
            in_else = False
            continue
        if stripped.startswith("%{ else"):
            in_else = True
            continue
        if stripped.startswith("%{ endif"):
            in_else = False
            continue
        if not in_else:
            lines.append(line)
    rendered = "\n".join(lines) + "\n"
    replacements = {
        "${organization_id}": "123456789012",
        "${domain_name}": "example.com",
        "${customer_id}": "C01234567",
        "${drs_tag_name}": "123456789012/org-policies",
        "${regime}": "IL5",
    }
    for key, val in replacements.items():
        rendered = rendered.replace(key, val)
    return rendered


class TestBootstrapFolderOrgPolicies(unittest.TestCase):
    def setUp(self):
        self.text = _ORG_TF.read_text(encoding="utf-8")
        self.root_folder = _block(self.text, 'module "root-folder-config"')

    def test_deploy_root_folder_config_includes_org_policies(self):
        self.assertRegex(
            self.text,
            r"deploy_root_folder_config\s*=\s*\([\s\S]*?"
            r"!var\.deploy_org_resources\.org_policies[\s\S]*?\)",
        )

    def test_root_folder_config_filters_org_policies_without_factory(self):
        self.assertRegex(
            self.root_folder,
            r"org_policies\s*=\s*\(\s*"
            r"var\.deploy_org_resources\.org_policies\s*\|\|\s*"
            r"var\.bootstrap_user\s*!=\s*null\s*\?\s*null\s*:\s*\{\s*"
            r"for\s+k,\s*v\s+in\s+local\.org_policies\s*:\s*k\s*=>\s*v\s+"
            r'if\s*!startswith\(trimprefix\(k,\s*"dry_run:"\),\s*"custom\."\)\s*&&\s*'
            r'!contains\(local\.org_only_policies,\s*trimprefix\(k,\s*"dry_run:"\)\)\s*'
            r"\}\s*\)",
        )
        self.assertNotIn("factories_config", self.root_folder)

    def test_root_folder_config_omits_scalar_context_condition_vars(self):
        self.assertNotIn("condition_vars", self.root_folder)

    def test_folder_policies_have_no_custom_or_unresolved_placeholders(self):
        merged = {}
        policy_dir = _BOOTSTRAP_DIR / "data/org-policies"
        for path in sorted(policy_dir.glob("*_policy.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged.update(data)
        custom_dir = _BOOTSTRAP_DIR / "data/custom-org-policies"
        for path in sorted(custom_dir.glob("*_policy.yaml")):
            rendered = _render_custom_policy_template(
                path.read_text(encoding="utf-8")
            )
            data = yaml.safe_load(rendered)
            if isinstance(data, dict):
                merged.update(data)

        org_only_policies = {"resourcemanager.accessBoundaries"}
        folder_policies = {
            k: v
            for k, v in merged.items()
            if not k.removeprefix("dry_run:").startswith("custom.")
            and k.removeprefix("dry_run:") not in org_only_policies
        }
        self.assertTrue(folder_policies)
        for key in folder_policies:
            self.assertFalse(key.removeprefix("dry_run:").startswith("custom."))
            self.assertNotIn(key.removeprefix("dry_run:"), org_only_policies)

        dumped = yaml.safe_dump(folder_policies)
        self.assertEqual(
            _PLACEHOLDER_RE.findall(dumped),
            [],
            f"Unresolved placeholders in folder policies: {dumped}",
        )


if __name__ == "__main__":
    unittest.main()
