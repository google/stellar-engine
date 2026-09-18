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

"""Guards the shipped configuration example against silent key drift.

The engine reads configuration by key name. Two failure modes follow from that,
and both are silent -- the run succeeds, the deliverables generate, and the
operator's declared value simply never appears:

1. **A renamed key.** ``system_information`` is deep-merged verbatim, so a key
   spelled ``primary_gcp_location`` when the reader asks for ``primary_location``
   is accepted, stored, and ignored. Every deliverable then renders
   ``[CONFIG_REQUIRED: Primary Location]`` while the operator sees their region
   sitting in the config file.

2. **A key nothing consumes.** ``continuous_monitoring`` was parsed, merged, and
   written into ``system_inventory.json``, but no template referenced it. An ISSM
   declaring "Independent Third-Party Assessment (3PAO / SCA-R)" got a package
   that never said so.

Neither is caught by schema validation, by the generator, or by the validator,
because in both cases the configuration is structurally valid. This module
asserts the weaker but checkable property that every key the example advertises
is at least named somewhere in the engine source.
"""

import os
import re
import sys
import unittest
from typing import Any, Dict, List, Tuple

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.abspath(os.path.join(TESTS_DIR, ".."))
SRC_DIR = os.path.join(SKILL_ROOT, "src")
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
TEMPLATES_DIR = os.path.join(SKILL_ROOT, "templates")
EXAMPLE_CONFIG = os.path.join(SKILL_ROOT, "config", "compliance_config.yaml.example")

for _p in (SRC_DIR, SCRIPTS_DIR, TESTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from compliance_engine import file_helpers  # noqa: E402,F401
except ImportError:
    import file_helpers  # noqa: E402,F401

import yaml  # noqa: E402

#: Subtrees whose leaf keys are looked up dynamically at runtime rather than
#: named in source. ``document_versions.policies`` is indexed by policy manual
#: title, so its 20 leaves will never appear as string literals.
DYNAMIC_SUBTREES: Tuple[str, ...] = (
    "document_versions.policies",
)

#: Keys that must reach a rendered deliverable, not merely be parsed. Each maps
#: to the ``{{ TOKEN }}`` that carries it into the templates. Regressions here
#: are the "parsed but never consumed" failure mode described in the docstring.
CONSUMED_VIA_TOKEN: Dict[str, str] = {
    "primary_location": "{{ PRIMARY_LOCATION }}",
    "csp_pato_package_id": "{{ CSP_PATO_PACKAGE_ID }}",
    "review_frequency": "{{ CONMON_REVIEW_FREQUENCY }}",
    "assessment_type": "{{ CONMON_ASSESSMENT_TYPE }}",
    "grc_tool_reference": "{{ GRC_TOOL_REFERENCE }}",
}


def _read_source(directory: str, suffixes: Tuple[str, ...]) -> str:
    """Concatenate every matching file under a directory.

    Args:
        directory: Absolute path to walk.
        suffixes: Filename suffixes to include.

    Returns:
        The concatenated contents of every matching file.

    Raises:
        OSError: If the directory cannot be walked, which means the shipped
            skill is incomplete and must fail loudly rather than vacuously pass.
    """
    chunks: List[str] = []
    for root, _dirs, files in os.walk(directory):
        for name in sorted(files):
            if name.endswith(suffixes):
                path = os.path.join(root, name)
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    chunks.append(handle.read())
    return "\n".join(chunks)


def _walk_keys(node: Any, path: Tuple[str, ...] = ()) -> List[Tuple[str, ...]]:
    """Enumerate every mapping key path in a parsed YAML document.

    Args:
        node: The parsed YAML node.
        path: Accumulated key path to the current node.

    Returns:
        A list of key paths, each a tuple of key names from the document root.
    """
    found: List[Tuple[str, ...]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if not isinstance(key, str):
                continue
            found.append(path + (key,))
            found.extend(_walk_keys(value, path + (key,)))
    elif isinstance(node, list):
        for item in node:
            found.extend(_walk_keys(item, path))
    return found


class TestConfigExampleAlignment(unittest.TestCase):
    """Every advertised configuration key is wired to the engine."""

    @classmethod
    def setUpClass(cls) -> None:
        with open(EXAMPLE_CONFIG, "r", encoding="utf-8") as handle:
            cls.config = yaml.safe_load(handle)
        cls.source = _read_source(SRC_DIR, (".py",)) + "\n" + _read_source(SCRIPTS_DIR, (".py",))
        cls.templates = _read_source(TEMPLATES_DIR, (".md", ".yaml"))

    def test_example_config_parses(self) -> None:
        """The shipped example must be valid YAML with a mapping at the root."""
        self.assertIsInstance(
            self.config, dict,
            "compliance_config.yaml.example does not parse to a mapping; every "
            "operator copies this file as their starting point.",
        )

    def test_every_advertised_key_is_read_by_the_engine(self) -> None:
        """No key is advertised in the example that no code path looks up."""
        orphans: List[str] = []
        for path in _walk_keys(self.config):
            dotted = ".".join(path)
            if any(dotted.startswith(prefix) for prefix in DYNAMIC_SUBTREES):
                continue
            leaf = path[-1]
            if re.search(r"[\"']" + re.escape(leaf) + r"[\"']", self.source):
                continue
            orphans.append(dotted)
        self.assertEqual(
            [], orphans,
            "compliance_config.yaml.example advertises key(s) that no engine "
            "code path reads. An operator setting these gets no error and no "
            "effect. Either wire the key up or remove it from the example:\n  "
            + "\n  ".join(orphans),
        )

    def test_load_bearing_keys_reach_a_template(self) -> None:
        """Being parsed is not enough: the value must render in a deliverable."""
        unrendered: List[str] = []
        for key, token in CONSUMED_VIA_TOKEN.items():
            if token not in self.templates:
                unrendered.append(f"{key} -> {token}")
        self.assertEqual(
            [], unrendered,
            "Configuration value(s) are parsed and carried into "
            "system_inventory.json but their token appears in no template, so "
            "they never reach a deliverable:\n  " + "\n  ".join(unrendered),
        )

    def test_load_bearing_tokens_are_registered_in_the_generator(self) -> None:
        """A token used by a template must have a replacement entry."""
        generator = os.path.join(SRC_DIR, "compliance_engine", "generate_compliance_artifacts.py")
        if not os.path.isfile(generator):
            generator = os.path.join(SCRIPTS_DIR, "generate_compliance_artifacts.py")
        with open(generator, "r", encoding="utf-8") as handle:
            body = handle.read()
        missing = [
            token for token in CONSUMED_VIA_TOKEN.values()
            if f'"{token}"' not in body
        ]
        self.assertEqual(
            [], missing,
            "Template token(s) have no entry in the generator's replacement "
            "map, so they would render literally into the deliverable:\n  "
            + "\n  ".join(missing),
        )

    def test_primary_location_key_name_is_exact(self) -> None:
        """Regression: the extractor reads `primary_location`, nothing else.

        `system_information` is deep-merged verbatim, so a near-miss spelling is
        accepted in silence.
        """
        sys_info = self.config.get("system_information") or {}
        self.assertIn(
            "primary_location", sys_info,
            "system_information.primary_location is missing. The extractor "
            "deep-merges this block and reads exactly this key; any other "
            "spelling is stored and ignored.",
        )
        for near_miss in ("primary_gcp_location", "primary_region", "gcp_location"):
            self.assertNotIn(
                near_miss, sys_info,
                f"system_information.{near_miss} is not read by any code path; "
                "it will be silently ignored. Use primary_location.",
            )


class TestLegacyConfigKeyAliases(unittest.TestCase):
    """A key renamed after release must keep working for configurations in the field."""

    def setUp(self) -> None:
        import extract_system_data

        self.esd = extract_system_data

    def test_deprecated_key_is_honored_at_the_top_level(self) -> None:
        """Configurations in the field set the legacy name; dropping it loses the value."""
        cfg = {"primary_gcp_location": "us-east4 / us-central1"}
        self.esd.apply_legacy_config_aliases(cfg)
        self.assertEqual(cfg.get("primary_location"), "us-east4 / us-central1")
        self.assertNotIn("primary_gcp_location", cfg)

    def test_deprecated_key_is_honored_inside_system_information(self) -> None:
        """``system_information`` is deep-merged verbatim, so it needs the same shim."""
        cfg = {"system_information": {"primary_gcp_location": "us-central1"}}
        self.esd.apply_legacy_config_aliases(cfg)
        sys_info = cfg["system_information"]
        self.assertEqual(sys_info.get("primary_location"), "us-central1")
        self.assertNotIn("primary_gcp_location", sys_info)

    def test_current_key_wins_over_deprecated_key(self) -> None:
        """A half-migrated file must resolve to the value the operator migrated to."""
        cfg = {
            "system_information": {
                "primary_gcp_location": "us-west1",
                "primary_location": "us-east4",
            }
        }
        self.esd.apply_legacy_config_aliases(cfg)
        self.assertEqual(cfg["system_information"]["primary_location"], "us-east4")
        self.assertNotIn("primary_gcp_location", cfg["system_information"])

    def test_empty_deprecated_key_does_not_manufacture_a_value(self) -> None:
        """A blank legacy value must not become a blank asserted region."""
        for blank in ("", "   ", None):
            with self.subTest(blank=blank):
                cfg = {"system_information": {"primary_gcp_location": blank}}
                self.esd.apply_legacy_config_aliases(cfg)
                self.assertNotIn("primary_location", cfg["system_information"])

    def test_deprecation_is_announced_with_the_offending_file(self) -> None:
        """A silent rewrite would leave the operator's file permanently stale."""
        cfg = {"system_information": {"primary_gcp_location": "us-central1"}}
        with self.assertLogs("extract_system_data", level="WARNING") as captured:
            self.esd.apply_legacy_config_aliases(cfg, source_path="/tmp/example.yaml")
        joined = "\n".join(captured.output)
        self.assertIn("primary_gcp_location", joined)
        self.assertIn("primary_location", joined)
        self.assertIn("/tmp/example.yaml", joined)

    def test_normalizer_tolerates_non_mapping_input(self) -> None:
        """It runs on every loaded file, including malformed ones."""
        for payload in (None, [], "text", 7):
            with self.subTest(payload=payload):
                self.assertEqual(self.esd.apply_legacy_config_aliases(payload), payload)

    def test_every_alias_target_is_a_key_the_engine_reads(self) -> None:
        """An alias pointing at an unread key would relocate the value into oblivion."""
        source = _read_source(SRC_DIR, (".py",)) + "\n" + _read_source(SCRIPTS_DIR, (".py",))
        for legacy, current in self.esd.LEGACY_CONFIG_KEY_ALIASES.items():
            with self.subTest(alias=legacy):
                self.assertRegex(
                    source,
                    r"[\"']" + re.escape(current) + r"[\"']",
                    f"Alias '{legacy}' maps to '{current}', which no code path reads.",
                )


class TestRepoRootConfigExample(unittest.TestCase):
    """The example operators actually copy must not drift from the skill's example.

    Two example configurations ship in this repository. The provisioning workflow
    copies the repo-root one, but only the skill-local one was previously guarded --
    which is exactly how the root copy came to retain a deprecated key name that the
    extractor had stopped reading.
    """

    REPO_ROOT = os.path.abspath(os.path.join(SKILL_ROOT, "..", "..", ".."))
    ROOT_EXAMPLE = os.path.join(REPO_ROOT, "compliance_config.yaml.example")

    def setUp(self) -> None:
        if not os.path.isfile(self.ROOT_EXAMPLE):
            self.skipTest(f"No repo-root example config at {self.ROOT_EXAMPLE}")
        with open(self.ROOT_EXAMPLE, "r", encoding="utf-8") as handle:
            self.config = yaml.safe_load(handle)

    def test_root_example_uses_the_supported_location_key(self) -> None:
        """The deprecated spelling still works, but must not be what we hand out."""
        sys_info = self.config.get("system_information") or {}
        self.assertIn(
            "primary_location",
            sys_info,
            "The repo-root example config omits system_information.primary_location, "
            "so every operator who copies it starts with no declared region.",
        )
        self.assertNotIn(
            "primary_gcp_location",
            sys_info,
            "The repo-root example config still ships the deprecated "
            "'primary_gcp_location' spelling.",
        )

    def test_root_example_advertises_no_key_the_engine_ignores(self) -> None:
        """Same orphan-key guard as the skill-local example."""
        source = _read_source(SRC_DIR, (".py",)) + "\n" + _read_source(SCRIPTS_DIR, (".py",))
        orphans: List[str] = []
        for path in _walk_keys(self.config):
            dotted = ".".join(path)
            if any(dotted.startswith(prefix) for prefix in DYNAMIC_SUBTREES):
                continue
            if re.search(r"[\"']" + re.escape(path[-1]) + r"[\"']", source):
                continue
            orphans.append(dotted)
        self.assertEqual(
            [],
            orphans,
            "The repo-root example config advertises key(s) no engine code path "
            "reads:\n  " + "\n  ".join(orphans),
        )


if __name__ == "__main__":
    unittest.main()

