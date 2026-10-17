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

"""Multi-regime baseline catalog and registry verification tests ."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import yaml

from compliance_engine import baseline_registry
from compliance_engine import excel_hydrator
from compliance_engine import oscal_generator
from compliance_engine.file_helpers import Regime
from compliance_engine.poam_rules import normalize_control_id
from compliance_engine.template_engine import evaluate_template_conditionals

_SKILL_ROOT = Path(__file__).resolve().parents[1]
_BASELINES_DIR = _SKILL_ROOT / "config" / "baselines"
_TEMPLATES_DIR = _SKILL_ROOT / "templates"

_EXPECTED_COUNTS = {
    "fedramp_rev5_low.json": (Regime.FEDRAMP_LOW, 156, 135, 21, 80),
    "fedramp_rev5_moderate.json": (Regime.FEDRAMP_MODERATE, 323, 181, 142, 137),
    "fedramp_rev5_high.json": (Regime.FEDRAMP_HIGH, 410, 191, 219, 170),
    "nist_800_53b_low.json": (Regime.FISMA_LOW, 149, 131, 18, 108),
    "nist_800_53b_moderate.json": (Regime.FISMA_MODERATE, 287, 177, 110, 198),
    "nist_800_53b_high.json": (Regime.FISMA_HIGH, 370, 188, 182, 254),
    "dod_il2.json": (Regime.DOD_IL2, 323, 181, 142, 137),
    "dod_il4.json": (Regime.DOD_IL4, 334, 182, 152, 149),
    "dod_il5.json": (Regime.DOD_IL5, 624, 238, 386, 216),
    "dod_il6.json": (Regime.DOD_IL6, 627, 238, 389, 216),
    "cjis.json": (Regime.CJIS, 323, 181, 142, 140),
}


class RegimeBaselinesFoundationTest(unittest.TestCase):
    """Verifies vendored baseline JSON catalogs, MANIFEST.json digests, and baseline_registry API."""

    def test_vendored_baselines_match_manifest_and_profiles(self) -> None:
        manifest_path = _BASELINES_DIR / "MANIFEST.json"
        self.assertTrue(manifest_path.is_file(), f"Missing {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files_map = manifest.get("files", {})
        self.assertEqual(set(files_map.keys()), set(_EXPECTED_COUNTS.keys()))
        self.assertFalse((_BASELINES_DIR / "nist_800_53b_privacy.json").exists())

        for filename, (regime, ctrl_cnt, base_cnt, enh_cnt, param_ctrl_cnt) in _EXPECTED_COUNTS.items():
            with self.subTest(filename=filename):
                fpath = _BASELINES_DIR / filename
                self.assertTrue(fpath.is_file(), f"Missing {fpath}")
                actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
                self.assertEqual(actual_sha, files_map[filename]["sha256"])

                data = json.loads(fpath.read_text(encoding="utf-8"))
                self.assertEqual(data["display_name"], regime.value)
                self.assertEqual(data["control_count"], ctrl_cnt)
                self.assertEqual(len(data["control_ids"]), ctrl_cnt)
                self.assertEqual(data["base_control_count"], base_cnt)
                self.assertEqual(data["enhancement_count"], enh_cnt)
                self.assertEqual(len(data["formatted_parameter_rows"]), param_ctrl_cnt)

                # Verify uniform schema keys and zero unresolved {{ ... }} or literal backslashes/newlines
                for key in (
                    "control_ids",
                    "parameters",
                    "parameters_by_control",
                    "guidance_by_control",
                    "formatted_parameter_rows",
                ):
                    self.assertIn(key, data)
                for cid, row in data["formatted_parameter_rows"].items():
                    self.assertNotIn("{{", row, f"{filename} {cid}")
                    self.assertNotIn("}}", row, f"{filename} {cid}")
                    self.assertNotIn("\n", row, f"{filename} {cid}")
                    self.assertNotIn("\\", row, f"{filename} {cid}")
                    self.assertNotIn("Organization-defined organization-defined", row, f"{filename} {cid}")
                if "au-06.05_odp.01" in data["parameters"]:
                    self.assertNotIn(
                        "(au-06.05_odp.02)",
                        data["parameters"]["au-06.05_odp.01"]["value"],
                        filename,
                    )
                for pid in data["parameters"]:
                    self.assertNotIn("_prm", pid, f"Legacy Rev4 _prm parameter leaked in {filename}: {pid}")

        # Verify DoD IL4 11 Table D-1 additions and exclusions
        il4 = baseline_registry.get_regime_baseline(Regime.DOD_IL4)
        mod = baseline_registry.get_regime_baseline(Regime.FEDRAMP_MODERATE)
        expected_il4_additions = {
            "AU-5(1)", "MA-5(5)", "PS-3(4)", "SA-4(5)", "SA-9(3)",
            "SA-9(6)", "SA-9(7)", "SA-9(8)", "SC-12(6)", "SC-18(2)", "SC-24",
        }
        self.assertEqual(set(il4["control_ids"]) - set(mod["control_ids"]), expected_il4_additions)
        for excluded in ("SC-18(3)", "SC-18(4)", "MA-5(2)", "MA-5(3)", "MA-5(4)", "SC-46"):
            self.assertNotIn(excluded, il4["control_ids"])

        # Verify SC-18(3) in DoD IL5 includes the Section 5.11 sentence
        il5 = baseline_registry.get_regime_baseline(Regime.DOD_IL5)
        self.assertIn("Refer to Section 5.11, Mobile Code, for more information.", il5["formatted_parameter_rows"]["SC-18(3)"])

        # Verify DoD IL2 equals FedRAMP Moderate 323 controls
        il2 = baseline_registry.get_regime_baseline(Regime.DOD_IL2)
        self.assertEqual(set(il2["control_ids"]), set(mod["control_ids"]))

        # Verify DoD IL6 adds MA-5(2..4) on top of DoD IL5 (624 + 3 = 627)
        il6 = baseline_registry.get_regime_baseline(Regime.DOD_IL6)
        self.assertEqual(set(il6["control_ids"]) - set(il5["control_ids"]), {"MA-5(2)", "MA-5(3)", "MA-5(4)"})

        # Verify CJIS includes FBI CJIS Security Policy v5.9.4/v6.0 parameter overrides
        cjis = baseline_registry.get_regime_baseline(Regime.CJIS)
        self.assertEqual(set(cjis["control_ids"]), set(mod["control_ids"]))
        for cjis_cid in ("AC-7", "AC-11", "AU-11", "IA-2", "IA-5", "IR-6", "PS-3", "SC-8", "SC-13", "SC-28"):
            self.assertIn("CJIS Security Policy", cjis["formatted_parameter_rows"][cjis_cid], cjis_cid)

    def test_ssp_control_set_equals_profile_per_regime(self) -> None:
        """Rendered SSP control heading set equals baseline['control_ids'] for all 8 supported regimes."""
        heading_re = re.compile(r"(?m)^###\s+([A-Z]{2}-\d+(?:\(\d+\))?)(?=\s|$)")
        for _filename, (regime, ctrl_cnt, _b, _e, _p) in _EXPECTED_COUNTS.items():
            with self.subTest(regime=regime.value):
                spec = baseline_registry.get_regime_spec(regime)
                baseline = baseline_registry.get_regime_baseline(regime)
                raw_ssp = (_TEMPLATES_DIR / "ssp" / spec.ssp_template_filename).read_text(encoding="utf-8")
                rendered = baseline_registry.render_ssp_for_regime(raw_ssp, regime, baseline)
                rendered = evaluate_template_conditionals(
                    rendered, baseline_registry.build_regime_template_flags(regime, {})
                )
                actual_ids = {normalize_control_id(m.group(1)) for m in heading_re.finditer(rendered)}
                expected_ids = set(baseline["control_ids"])
                self.assertEqual(len(actual_ids), ctrl_cnt)
                self.assertEqual(actual_ids, expected_ids)

    def test_ssp_parameters_equal_profile_values_per_regime(self) -> None:
        """Rendered SSP parameter value rows equal baseline['formatted_parameter_rows'] for all 8 regimes."""
        ctrl_re = re.compile(r"(?m)^###\s+([A-Z]{2}-\d+(?:\(\d+\))?)(?=\s|$)")
        for _filename, (regime, _c, _b, _e, _p) in _EXPECTED_COUNTS.items():
            with self.subTest(regime=regime.value):
                spec = baseline_registry.get_regime_spec(regime)
                baseline = baseline_registry.get_regime_baseline(regime)
                raw_ssp = (_TEMPLATES_DIR / "ssp" / spec.ssp_template_filename).read_text(encoding="utf-8")
                rendered = baseline_registry.render_ssp_for_regime(raw_ssp, regime, baseline)

                if regime != Regime.FEDRAMP_HIGH:
                    self.assertNotIn(" — FedRAMP High:", rendered)
                if spec.is_fisma or regime == Regime.CJIS:
                    self.assertNotIn("**FedRAMP Additional Guidance**:", rendered)
                if spec.is_dod:
                    self.assertNotIn("**FedRAMP High Parameter Values**:", rendered)
                    self.assertNotIn("**FedRAMP Moderate Parameter Values**:", rendered)

                prefix = f"| **{regime.value} Parameter Values**: "
                found_params = {}
                current_cid = None
                for line in rendered.splitlines():
                    m = ctrl_re.match(line)
                    if m:
                        current_cid = normalize_control_id(m.group(1))
                        continue
                    if current_cid and line.startswith(prefix):
                        body = line[len(prefix) :]
                        if body.endswith(" |"):
                            body = body[:-2]
                        body = body.split("<br>**FedRAMP Additional Guidance**:")[0]
                        found_params[current_cid] = body
                self.assertEqual(found_params, baseline["formatted_parameter_rows"])

    def test_dod_il4_overlay_exact(self) -> None:
        """DoD IL4 rendered artifacts contain the 11 SRG Table D-1 additions and zero IL5 strings."""
        regime = Regime.DOD_IL4
        baseline = baseline_registry.get_regime_baseline(regime)
        flags = baseline_registry.build_regime_template_flags(regime, {})
        tokens = baseline_registry.build_regime_odp_tokens(regime, {})
        il5_re = re.compile(r"\b(?:IL[ _-]?5|Impact Level 5)\b")

        raw_ssp = (_TEMPLATES_DIR / "ssp" / "SSP_IL5_Template.md").read_text(encoding="utf-8")
        rendered_ssp = baseline_registry.render_ssp_for_regime(raw_ssp, regime, baseline)
        rendered_ssp = evaluate_template_conditionals(rendered_ssp, flags)
        for k, v in tokens.items():
            rendered_ssp = rendered_ssp.replace(k, v)
        self.assertIsNone(il5_re.search(rendered_ssp), "IL5 string leaked into DoD IL4 SSP")

        for sub in ("policies", "runbooks", "pta"):
            for path in sorted((_TEMPLATES_DIR / sub).glob("*.md")):
                raw = path.read_text(encoding="utf-8")
                if sub == "policies":
                    raw = baseline_registry.filter_policy_appendix_rows(raw, baseline["control_ids"])
                rendered = evaluate_template_conditionals(raw, flags)
                for k, v in tokens.items():
                    rendered = rendered.replace(k, v)
                m = il5_re.search(rendered)
                self.assertIsNone(m, f"IL5 string leaked into DoD IL4 {sub}/{path.name}: {m.group(0) if m else ''}")

    def test_no_dod_only_text_in_fedramp_and_fisma_packages(self) -> None:
        """Civilian FedRAMP and FISMA packages contain zero DoD-only strings across SSP, policies, runbooks, and PTA."""
        forbidden = (
            "DoD password complexity",
            "15+ chars",
            "50% change",
            "CJCSM 6510.01B",
            "USCYBERCOM",
            "JFHQ-DODIN",
            "DIBNet",
            "DFARS 252.",
            "REQUIRED eMASS STANDARD",
            "DoD IL5 PA",
            "DoD IL4 PA",
        )
        civilian_regimes = (
            Regime.FEDRAMP_LOW,
            Regime.FEDRAMP_MODERATE,
            Regime.FEDRAMP_HIGH,
            Regime.FISMA_LOW,
            Regime.FISMA_MODERATE,
            Regime.FISMA_HIGH,
            Regime.CJIS,
        )
        for regime in civilian_regimes:
            with self.subTest(regime=regime.value):
                baseline = baseline_registry.get_regime_baseline(regime)
                flags = baseline_registry.build_regime_template_flags(regime, {})
                tokens = baseline_registry.build_regime_odp_tokens(regime, {})

                raw_ssp = (_TEMPLATES_DIR / "ssp" / "SSP_FedRAMP_High_Template.md").read_text(encoding="utf-8")
                rendered_ssp = baseline_registry.render_ssp_for_regime(raw_ssp, regime, baseline)
                rendered_ssp = evaluate_template_conditionals(rendered_ssp, flags)
                for k, v in tokens.items():
                    rendered_ssp = rendered_ssp.replace(k, v)
                for f_str in forbidden:
                    self.assertNotIn(f_str, rendered_ssp, f"{regime.value} SSP leaked {f_str!r}")

                for sub in ("policies", "runbooks", "pta"):
                    for path in sorted((_TEMPLATES_DIR / sub).glob("*.md")):
                        raw = path.read_text(encoding="utf-8")
                        if sub == "policies":
                            raw = baseline_registry.filter_policy_appendix_rows(raw, baseline["control_ids"])
                        rendered = evaluate_template_conditionals(raw, flags)
                        for k, v in tokens.items():
                            rendered = rendered.replace(k, v)
                        for f_str in forbidden:
                            self.assertNotIn(f_str, rendered, f"{regime.value} {sub}/{path.name} leaked {f_str!r}")

    def test_policy_appendix_a_and_sctm_filtered_to_baseline(self) -> None:
        """Policy Appendix A union and SCTM (.yaml + .xlsm) filter strictly to each baseline."""
        import openpyxl  # pylint: disable=import-outside-toplevel

        row_re = re.compile(r"^[ \t]*\|[ \t]*\**`?([A-Z]{2})-0*(\d+)(?:\s*\(0*(\d+)\))?`?\**[ \t]*\|")
        sctm_yaml_raw = (_TEMPLATES_DIR / "sctm" / "SCTM_Template.yaml").read_text(encoding="utf-8")
        xlsm_tpl = _TEMPLATES_DIR / "sctm" / "ControlInfoExport_Template.xlsm"

        for _filename, (regime, ctrl_cnt, _b, _e, _p) in _EXPECTED_COUNTS.items():
            with self.subTest(regime=regime.value):
                baseline = baseline_registry.get_regime_baseline(regime)
                expected_ids = set(baseline["control_ids"])

                # 1. Policy Appendix A union equals expected_ids
                policy_ids = set()
                for path in sorted((_TEMPLATES_DIR / "policies").glob("*.md")):
                    filtered = baseline_registry.filter_policy_appendix_rows(
                        path.read_text(encoding="utf-8"), expected_ids
                    )
                    in_app = False
                    for line in filtered.splitlines():
                        if line.lstrip().startswith("## "):
                            in_app = line.lstrip().startswith("## Appendix A")
                            continue
                        if in_app and (m := row_re.match(line)):
                            fam, num, enh = m.groups()
                            cid = f"{fam}-{int(num)}" + (f"({int(enh)})" if enh else "")
                            policy_ids.add(cid)
                self.assertEqual(policy_ids, expected_ids)

                # 2. SCTM YAML filtered to baseline
                filtered_yaml_str = baseline_registry.filter_sctm_yaml_for_regime(sctm_yaml_raw, regime, baseline)
                parsed_yaml = yaml.safe_load(filtered_yaml_str)
                self.assertEqual(parsed_yaml["system_metadata"]["compliance_baseline"], regime.value)
                self.assertEqual(
                    parsed_yaml["overall_traceability_summary"]["total_baseline_controls"], ctrl_cnt
                )
                yaml_cids = {
                    normalize_control_id(c["id"])
                    for fam in parsed_yaml["control_families"]
                    for c in fam["controls"]
                }
                self.assertTrue(yaml_cids.issubset(expected_ids))

                # 3. SCTM XLSM marks out-of-baseline rows as Not Applicable with Col F='', Col G='System-Specific'
                with tempfile.TemporaryDirectory() as td:
                    out_xlsm = Path(td) / "SCTM.xlsm"
                    inv = {
                        "system_information": {
                            "system_name": "TestSys",
                            "organization": "TestOrg",
                            "impact_level": regime.value,
                            "compliance_baseline": regime.value,
                        },
                        "infrastructure_components": {},
                        "network_architecture": {},
                    }
                    excel_hydrator.SCTMHydrator(str(xlsm_tpl)).hydrate(inv, str(out_xlsm))
                    wb = openpyxl.load_workbook(out_xlsm, keep_vba=True)
                    ws = wb["Template"]
                    for r in range(7, ws.max_row + 1):
                        raw_cid = ws.cell(row=r, column=1).value
                        if not raw_cid or not str(raw_cid).strip():
                            continue
                        norm_cid = normalize_control_id(str(raw_cid))
                        status = ws.cell(row=r, column=5).value
                        col_f = ws.cell(row=r, column=6).value or ""
                        col_g = ws.cell(row=r, column=7).value
                        col_i = ws.cell(row=r, column=9).value or ""
                        col_j = ws.cell(row=r, column=10).value or ""
                        if norm_cid in expected_ids:
                            self.assertIn(status, ("Implemented", "Inherited", "Planned"))
                        else:
                            self.assertEqual(status, "Not Applicable", f"{regime.value} {norm_cid}")
                            self.assertEqual(col_f, "", f"{regime.value} {norm_cid} Col F")
                            self.assertEqual(col_g, "System-Specific", f"{regime.value} {norm_cid} Col G")
                            self.assertTrue(bool(str(col_i).strip()), f"{regime.value} {norm_cid} Col I")
                            self.assertEqual(col_j, "", f"{regime.value} {norm_cid} Col J")
                            for col_idx in range(5, 30):
                                cell_val = str(ws.cell(row=r, column=col_idx).value or "")
                                self.assertNotIn("[CONFIG_REQUIRED", cell_val, f"{regime.value} {norm_cid} Col {col_idx}")
                    wb.close()

    def test_oscal_import_profile_and_requirements_by_regime(self) -> None:
        """OSCAL SSP import-profile, implemented-requirements, and set-parameters match each regime."""
        for _filename, (regime, _c, _b, _e, _p) in _EXPECTED_COUNTS.items():
            with self.subTest(regime=regime.value):
                spec = baseline_registry.get_regime_spec(regime)
                baseline = baseline_registry.get_regime_baseline(regime)
                expected_ids = set(baseline["control_ids"])
                inv = {
                    "system_information": {
                        "system_name": "TestSys",
                        "system_abbreviation": "TST",
                        "impact_level": regime.value,
                        "compliance_baseline": regime.value,
                    },
                    "infrastructure_components": {},
                    "network_architecture": {},
                }
                ssp = oscal_generator.generate_oscal_ssp(inv)["system-security-plan"]
                self.assertEqual(ssp["import-profile"]["href"], spec.oscal_profile_href)
                if spec.is_dod:
                    self.assertIn("SRG", ssp["import-profile"].get("remarks", ""))
                elif regime == Regime.CJIS:
                    self.assertIn("CJIS Security Policy", ssp["import-profile"].get("remarks", ""))
                else:
                    self.assertNotIn("remarks", ssp["import-profile"])

                reqs = ssp["control-implementation"]["implemented-requirements"]
                self.assertTrue(reqs)
                for req in reqs:
                    norm_cid = normalize_control_id(req["control-id"])
                    self.assertIn(norm_cid, expected_ids, f"{regime.value} emitted out-of-baseline {norm_cid}")
                    if "set-parameters" in req:
                        for sp in req["set-parameters"]:
                            self.assertIn("param-id", sp)
                            self.assertNotIn("param_id", sp)
                            self.assertTrue(isinstance(sp["values"], list) and sp["values"])
                            for val in sp["values"]:
                                self.assertNotIn("[CONFIG_REQUIRED", val)

    def test_dod_il2_and_dod_il6_and_cjis_honesty_invariants(self) -> None:
        """Verify DoD IL6 honesty markers (never unclassified GCP PA), DoD IL2 PA, and CJIS Assured Workloads headers."""
        # 1. DoD IL6 must never claim unclassified Google Services FedRAMP High P-ATO, DoD IL5 PA, or FR1805751477
        il6_spec = baseline_registry.get_regime_spec(Regime.DOD_IL6)
        self.assertEqual(
            il6_spec.csp_inheritance_header,
            "[CONFIG_REQUIRED: Classified Cloud / GDC Secret Enclave Inheritance Boundary — DoD IL6 PA "
            "(Verify SIPRNet / NSA Type 1 Crypto / Cross-Domain Solution Inheritance)]",
        )
        self.assertEqual(
            il6_spec.default_csp_pato_package_id,
            "[CONFIG_REQUIRED: DoD IL6 Secret Enclave PA Package ID]",
        )
        raw_il5_ssp = (_TEMPLATES_DIR / "ssp" / "SSP_IL5_Template.md").read_text(encoding="utf-8")
        il6_ssp = baseline_registry.render_ssp_for_regime(raw_il5_ssp, Regime.DOD_IL6)
        il6_ssp = evaluate_template_conditionals(il6_ssp, baseline_registry.build_regime_template_flags(Regime.DOD_IL6, {}))
        self.assertIn(il6_spec.csp_inheritance_header, il6_ssp)
        self.assertNotIn("DoD IL5 PA", il6_ssp)
        self.assertNotIn("Google Services FedRAMP High P-ATO", il6_ssp)

        # 2. DoD IL2 cites DoD IL2 PA and contains zero IL5 strings
        il2_ssp = baseline_registry.render_ssp_for_regime(raw_il5_ssp, Regime.DOD_IL2)
        il2_ssp = evaluate_template_conditionals(il2_ssp, baseline_registry.build_regime_template_flags(Regime.DOD_IL2, {}))
        self.assertIn("DoD IL2 PA", il2_ssp)
        self.assertNotIn("DoD IL5", il2_ssp)

        # 3. CJIS cites Google Cloud Assured Workloads for CJIS
        cjis_spec = baseline_registry.get_regime_spec(Regime.CJIS)
        self.assertEqual(
            cjis_spec.csp_inheritance_header,
            "Inherited from Google Cloud Assured Workloads for CJIS "
            "(FBI CJIS Security Policy v5.9.4 / v6.0 Data Boundary — {{ CSP_PATO_PACKAGE_ID }}).",
        )
        self.assertEqual(
            cjis_spec.default_csp_pato_package_id,
            "[CONFIG_REQUIRED: State CJIS Systems Agency (CSA) Information Exchange Agreement / Package ID]",
        )
        raw_fr_ssp = (_TEMPLATES_DIR / "ssp" / "SSP_FedRAMP_High_Template.md").read_text(encoding="utf-8")
        cjis_ssp = baseline_registry.render_ssp_for_regime(raw_fr_ssp, Regime.CJIS)
        self.assertIn(cjis_spec.csp_inheritance_header, cjis_ssp)

    def test_unsupported_regimes_fail_closed_before_writing(self) -> None:
        """All 3 CLI entrypoints fail closed (exit 1, zero output files) on unsupported regimes."""
        scripts_dir = _SKILL_ROOT / "scripts"
        unsupported_cases = (
            ("GovRAMP Moderate", "GovRAMP"),
            ("StateRAMP High", "GovRAMP"),
            ("FedRAMP Tailored LI-SaaS", "Unsupported regime"),
            ("DoD", "Unsupported regime"),
            ("FISMA", "Unsupported regime"),
            ("FedRAMP", "Unsupported regime"),
            ("", "Unsupported regime"),
        )
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", COMPLIANCE_DISABLE_LIVE_SCANNERS="1")
        for raw_regime, expected_err in unsupported_cases:
            with self.subTest(raw_regime=raw_regime):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root / ".git").mkdir()
                    target = root / "bp"
                    target.mkdir()
                    (target / "main.tf").write_text('resource "google_storage_bucket" "b" {\n  name = "b"\n  location = "US"\n}\n', encoding="utf-8")
                    (target / "compliance_config.yaml").write_text(
                        yaml.safe_dump(
                            {
                                "system_information": {
                                    "system_name": "Demo",
                                    "impact_level": raw_regime,
                                    "compliance_baseline": raw_regime,
                                }
                            }
                        ),
                        encoding="utf-8",
                    )
                    # 1. extract_system_data.py fails closed before writing system_inventory.json
                    proc_ext = subprocess.run(
                        [sys.executable, str(scripts_dir / "extract_system_data.py"), str(target)],
                        env=env,
                        cwd=tmp,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        check=False,
                    )
                    self.assertEqual(proc_ext.returncode, 1, proc_ext.stdout + proc_ext.stderr)
                    self.assertIn(expected_err, proc_ext.stderr)
                    self.assertFalse((target / "system_inventory.json").exists())

    def test_e2e_multi_regime_blueprints_and_configs(self) -> None:
        """E2E generation on blueprints across FedRAMP, DoD IL2/IL4/IL5/IL6, and CJIS."""
        import shutil
        from compliance_engine import extract_system_data, generate_compliance_artifacts, validate_compliance_artifacts

        repo_root = _SKILL_ROOT.parents[2]
        unresolved_macro_re = re.compile(r"\{\{[^{}]+\}\}")
        heading_re = re.compile(r"(?m)^###\s+([A-Z]{2}-\d+(?:\(\d+\))?)(?=\s|$)")

        cases = (
            ("blueprints/fedramp-high/cloud-run", None, Regime.FEDRAMP_HIGH, 410),
            ("blueprints/il5/bigquery", None, Regime.DOD_IL5, 624),
            ("blueprints/fedramp-high/cloud-run", "FedRAMP Moderate", Regime.FEDRAMP_MODERATE, 323),
            ("blueprints/il5/bigquery", "DoD IL2", Regime.DOD_IL2, 323),
            ("blueprints/il5/bigquery", "DoD IL4", Regime.DOD_IL4, 334),
            ("blueprints/il5/bigquery", "DoD IL6", Regime.DOD_IL6, 627),
            ("blueprints/fedramp-high/cloud-run", "CJIS", Regime.CJIS, 323),
        )
        env = {"COMPLIANCE_DISABLE_LIVE_SCANNERS": "1", "COMPLIANCE_OFFLINE": "1"}
        from unittest import mock

        with mock.patch.dict(os.environ, env):
            for rel_bp, override_regime, expected_regime, expected_count in cases:
                with self.subTest(blueprint=rel_bp, regime=expected_regime.value):
                    with tempfile.TemporaryDirectory() as tmp:
                        root = Path(tmp)
                        (root / ".git").mkdir()
                        shutil.copytree(repo_root / "modules", root / "modules")
                        target = root / rel_bp
                        shutil.copytree(repo_root / rel_bp, target, symlinks=False)
                        if override_regime:
                            (target / "compliance_config.yaml").write_text(
                                yaml.safe_dump(
                                    {
                                        "system_information": {
                                            "system_name": f"Demo {override_regime}",
                                            "impact_level": override_regime,
                                            "compliance_baseline": override_regime,
                                        }
                                    }
                                ),
                                encoding="utf-8",
                            )
                        inv = extract_system_data.extract_system_inventory(str(target))
                        (target / "system_inventory.json").write_text(json.dumps(inv), encoding="utf-8")
                        generate_compliance_artifacts.generate_ato_artifacts(
                            str(target),
                            policy_format="markdown",
                            data_format="yaml",
                            oscal_format="json",
                        )
                        ato_dir = target / "ato_artifacts"
                        ssp_md = (ato_dir / "SSP" / "SSP_System_Security_Plan.md").read_text(encoding="utf-8")
                        self.assertIsNone(unresolved_macro_re.search(ssp_md), f"Unresolved macro in {expected_regime.value} SSP")
                        ssp_ids = {normalize_control_id(m.group(1)) for m in heading_re.finditer(ssp_md)}
                        self.assertEqual(len(ssp_ids), expected_count)
                        if expected_regime == Regime.DOD_IL6:
                            self.assertIn(
                                "[CONFIG_REQUIRED: Classified Cloud / GDC Secret Enclave Inheritance Boundary — DoD IL6 PA",
                                ssp_md,
                            )
                            self.assertIn("[CONFIG_REQUIRED: DoD IL6 Secret Enclave PA Package ID]", ssp_md)
                            self.assertNotIn("DoD IL5 PA", ssp_md)
                            self.assertNotIn("FR1805751477", ssp_md)
                        elif expected_regime == Regime.CJIS:
                            self.assertIn(
                                "Inherited from Google Cloud Assured Workloads for CJIS (FBI CJIS Security Policy v5.9.4 / v6.0 Data Boundary",
                                ssp_md,
                            )
                            self.assertIn(
                                "[CONFIG_REQUIRED: State CJIS Systems Agency (CSA) Information Exchange Agreement / Package ID]",
                                ssp_md,
                            )
                        parity_findings = validate_compliance_artifacts.audit_baseline_control_parity(str(ato_dir), inv)
                        self.assertEqual(parity_findings, [])


if __name__ == "__main__":
    unittest.main()
