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

"""Regression tests for unresolved NIST catalog artifacts in shipped templates.

Two distinct evidence-integrity defects are guarded here.

1. **Dangling bracket citation tags.** The policy manuals are transcribed from
   the NIST SP 800-53 Rev. 5 control catalog, whose prose carries short
   bracketed source-citation tags (``[PRIVACT]``, ``[EVIDACT]``, ...). Those
   tags resolve against the catalog's references appendix, which is *not*
   shipped with these manuals. A signed policy manual containing an
   unresolvable ``[PRIVACT]`` reads to an assessor as an unfinished document.

2. **Orphaned Control Summary tables.** Each SSP control section is
   ``### <control>`` -> control statement -> ``| Control Summary Information |``
   table carrying the implementation statement. When the table drifts *after*
   the next family's ``## N.N`` heading, the control renders with no
   implementation statement at all and the table renders unlabelled under the
   wrong family. That is indistinguishable, to an Authorizing Official, from an
   unaddressed control.

The citation test is an allowlist of *known-unresolved* tags rather than a bare
assertion of zero, so that a genuinely unverifiable tag can be pinned as
explicit debt instead of being silently expanded from memory. An unconfirmed
expansion in an ATO package is worse than an unexpanded tag.

**The allowlist is currently empty.** ``[PRIVACT]``, ``[EVIDACT]`` and
``[OMB M-19-23]`` were resolved against the authoritative back-matter of the
NIST OSCAL catalog, so no unresolved tag ships today:

* Source: ``NIST_SP-800-53_rev5_catalog.json``, catalog uuid
  ``ea7c7688-79c5-463b-a91b-0650f2d98623``, version 5.2.0, OSCAL 1.2.2.
* ``PRIVACT`` -> resource ``18e71fec-c6fd-475a-925a-5d8495cf8455``,
  "Privacy Act (P.L. 93-579), December 1974."
* ``EVIDACT`` -> resource ``511da9ca-604d-43f7-be41-b862085420a9``,
  "Foundations for Evidence-Based Policymaking Act of 2018 (P.L. 115-435),
  January 2019."

Each expansion is cross-referenced to Appendix B of the Program Management
policy manual so an assessor can trace it.
"""

import json
import os
import re
import unittest
from typing import List, Set, Tuple

from compliance_engine import baseline_registry
from compliance_engine.file_helpers import Regime
from compliance_engine.poam_rules import normalize_control_id
from compliance_engine.template_engine import evaluate_template_conditionals

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "templates"))
BASELINES_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "config", "baselines"))
POLICIES_DIR = os.path.join(TEMPLATES_DIR, "policies")
SSP_DIR = os.path.join(TEMPLATES_DIR, "ssp")

#: Bracket markers the engine emits on purpose; never NIST citation tags.
INTENTIONAL_MARKERS: Tuple[str, ...] = (
    "NOT DETERMINED FROM SOURCE",
    "CONFIG_REQUIRED",
    "EXAMPLE_DATA_REQUIRED",
)

#: NIST catalog citation tags that remain unresolved because no authoritative
#: source could be reached to confirm their expansion. Shrink this, never grow
#: it. Each entry maps the tag to the template basename it appears in.
#:
#: Empty by design: every tag has been resolved against the OSCAL catalog
#: back-matter cited in the module docstring. Adding an entry here requires a
#: written justification explaining why the tag could not be verified.
KNOWN_UNRESOLVED_TAGS: Tuple[Tuple[str, str], ...] = ()

_TAG_RE = re.compile(r"\[([A-Z]{3,})\]")
_CONTROL_RE = re.compile(r"^### ([A-Z]{2}-\d+(?:\(\d+\))?)\s")
_FAMILY_RE = re.compile(r"^## \d+\.\d+\s")
_TABLE_RE = re.compile(r"^\| Control Summary Information \|")


def _read(path: str) -> List[str]:
    """Read a template as a list of lines.

    Args:
        path: Absolute path to the markdown template.

    Returns:
        The file contents split into lines with newlines stripped.

    Raises:
        OSError: If the template cannot be read, which means the shipped
            template set is incomplete and must fail loudly.
    """
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


class TestHardeningTemplateCitations(unittest.TestCase):
    """Guards shipped templates against unresolved NIST catalog residue."""

    def _policy_templates(self) -> List[str]:
        """List the policy manual templates.

        Returns:
            Sorted absolute paths of every policy markdown template.
        """
        names = sorted(
            name for name in os.listdir(POLICIES_DIR) if name.endswith(".md")
        )
        self.assertTrue(names, f"no policy templates found under {POLICIES_DIR}")
        return [os.path.join(POLICIES_DIR, name) for name in names]

    def test_policy_templates_have_no_new_dangling_citation_tags(self) -> None:
        """Every ``[UPPERCASE]`` tag is either intentional or a pinned known gap."""
        allowed = set(KNOWN_UNRESOLVED_TAGS)
        unexpected: List[str] = []
        for path in self._policy_templates():
            basename = os.path.basename(path)
            for lineno, line in enumerate(_read(path), start=1):
                if any(marker in line for marker in INTENTIONAL_MARKERS):
                    continue
                for tag in _TAG_RE.findall(line):
                    if (tag, basename) in allowed:
                        continue
                    unexpected.append(f"{basename}:{lineno}: [{tag}]")
        self.assertEqual(
            [],
            unexpected,
            "Unresolved NIST catalog citation tag(s) would ship in a signed "
            "policy manual. Resolve each against the SP 800-53 Rev. 5 "
            "references appendix, or add it to KNOWN_UNRESOLVED_TAGS with a "
            "written justification:\n  " + "\n  ".join(unexpected),
        )

    def test_known_unresolved_tags_are_still_present(self) -> None:
        """The allowlist does not rot: every pinned tag still actually exists."""
        for tag, basename in KNOWN_UNRESOLVED_TAGS:
            path = os.path.join(POLICIES_DIR, basename)
            self.assertTrue(
                any(f"[{tag}]" in line for line in _read(path)),
                f"[{tag}] is pinned in KNOWN_UNRESOLVED_TAGS but no longer "
                f"appears in {basename}; remove the stale allowlist entry.",
            )

    def test_ssp_control_summary_tables_stay_with_their_control(self) -> None:
        """No Control Summary table is separated from its control by a heading."""
        names = sorted(name for name in os.listdir(SSP_DIR) if name.endswith(".md"))
        self.assertTrue(names, f"no SSP templates found under {SSP_DIR}")
        orphans: List[str] = []
        for name in names:
            lines = _read(os.path.join(SSP_DIR, name))
            control = ""
            family_lineno = -1
            for lineno, line in enumerate(lines, start=1):
                match = _CONTROL_RE.match(line)
                if match:
                    control = match.group(1)
                    family_lineno = -1
                    continue
                if _FAMILY_RE.match(line):
                    family_lineno = lineno
                    continue
                if _TABLE_RE.match(line) and family_lineno > 0 and control:
                    orphans.append(
                        f"{name}: control {control} lost its Control Summary "
                        f"table to the family heading at line {family_lineno} "
                        f"(table at line {lineno})"
                    )
                    family_lineno = -1
        self.assertEqual(
            [],
            orphans,
            "Control(s) would render in the SSP with no implementation "
            "statement:\n  " + "\n  ".join(orphans),
        )

    def test_every_ssp_control_has_exactly_one_summary_table(self) -> None:
        """Control heading count matches Control Summary table count."""
        for name in sorted(n for n in os.listdir(SSP_DIR) if n.endswith(".md")):
            lines = _read(os.path.join(SSP_DIR, name))
            controls = sum(1 for line in lines if _CONTROL_RE.match(line))
            tables = sum(1 for line in lines if _TABLE_RE.match(line))
            self.assertEqual(
                controls,
                tables,
                f"{name}: {controls} control headings but {tables} Control "
                "Summary tables; at least one control has no implementation "
                "statement or one table is duplicated.",
            )

    def test_il5_ssp_baseline_complete(self) -> None:
        """SSP_IL5_Template.md has all 627 DoD superset controls (dod_il6.json) and filters to 624 for DoD IL5."""
        il5_path = os.path.join(SSP_DIR, "SSP_IL5_Template.md")
        lines = _read(il5_path)
        actual_ids = {
            normalize_control_id(m.group(1))
            for line in lines
            if (m := _CONTROL_RE.match(line))
        }
        with open(os.path.join(BASELINES_DIR, "dod_il6.json"), encoding="utf-8") as fh:
            expected_il6_ids = set(json.load(fh)["control_ids"])
        self.assertEqual(len(expected_il6_ids), 627)
        self.assertEqual(
            actual_ids,
            expected_il6_ids,
            f"Missing: {sorted(expected_il6_ids - actual_ids)}; Extra: {sorted(actual_ids - expected_il6_ids)}",
        )
        raw_text = "\n".join(lines)
        rendered_il5 = baseline_registry.render_ssp_for_regime(raw_text, Regime.DOD_IL5)
        il5_rendered_ids = {
            normalize_control_id(m.group(1))
            for line in rendered_il5.splitlines()
            if (m := _CONTROL_RE.match(line))
        }
        with open(os.path.join(BASELINES_DIR, "dod_il5.json"), encoding="utf-8") as fh:
            expected_il5_ids = set(json.load(fh)["control_ids"])
        self.assertEqual(len(expected_il5_ids), 624)
        self.assertEqual(il5_rendered_ids, expected_il5_ids)
        self.assertIn("unclassified National Security Systems", raw_text)
        self.assertIn("National Security Information", raw_text)

    def test_fedramp_high_ssp_baseline_complete_and_has_all_params(self) -> None:
        """SSP_FedRAMP_High_Template.md has 410 controls and all 5 required FedRAMP High ODP parameter IDs."""
        fr_path = os.path.join(SSP_DIR, "SSP_FedRAMP_High_Template.md")
        raw_text = "\n".join(_read(fr_path))
        actual_ids = {
            normalize_control_id(m.group(1))
            for line in raw_text.splitlines()
            if (m := _CONTROL_RE.match(line))
        }
        with open(os.path.join(BASELINES_DIR, "fedramp_rev5_high.json"), encoding="utf-8") as fh:
            fr_high = json.load(fh)
        expected_ids = set(fr_high["control_ids"])
        self.assertEqual(len(expected_ids), 410)
        self.assertEqual(
            actual_ids,
            expected_ids,
            f"Missing: {sorted(expected_ids - actual_ids)}; Extra: {sorted(actual_ids - expected_ids)}",
        )
        for pid in (
            "ac-06.01_odp.02",
            "ac-06.01_odp.03",
            "ac-06.01_odp.04",
            "au-02_odp.02",
            "ca-02.03_odp.01",
        ):
            self.assertIn(pid, raw_text)
            self.assertIn(pid, fr_high["parameters"])

    def test_policy_appendix_a_covers_all_eight_baselines(self) -> None:
        """Union of Policy Appendix A rows covers 100% of controls across all 8 baselines."""
        row_re = re.compile(r"^[ \t]*\|[ \t]*\**`?([A-Z]{2})-0*(\d+)(?:\s*\(0*(\d+)\))?`?\**[ \t]*\|")
        policy_ids: Set[str] = set()
        for path in self._policy_templates():
            in_app = False
            for line in _read(path):
                if line.lstrip().startswith("## "):
                    in_app = line.lstrip().startswith("## Appendix A")
                    continue
                if in_app and (m := row_re.match(line)):
                    fam, num, enh = m.groups()
                    cid = f"{fam}-{int(num)}" + (f"({int(enh)})" if enh else "")
                    policy_ids.add(cid)

        for name in sorted(os.listdir(BASELINES_DIR)):
            if not name.endswith(".json") or name == "MANIFEST.json":
                continue
            with open(os.path.join(BASELINES_DIR, name), encoding="utf-8") as fh:
                bdata = json.load(fh)
            missing = sorted(set(bdata["control_ids"]) - policy_ids)
            self.assertEqual(missing, [], f"{name} has controls missing from Policy Appendix A: {missing}")

    def test_policy_odp_matches_active_regime(self) -> None:
        """Policy ODP tokens resolve to regime-accurate values across High, Moderate, Low, and DoD."""
        for regime, expected_snippets in (
            (
                Regime.FEDRAMP_HIGH,
                {
                    "Access_Control_Policy_and_Procedures.md": [
                        "monthly for privileged accessed, every six (6) months for non-privileged access",
                        "no more than 24 hours from last use",
                        "three (3) sessions for privileged access and two (2) sessions for non-privileged access",
                    ],
                    "Assessment_Authorization_and_Monitoring_Policy.md": ["at least monthly"],
                    "Personnel_Security_Policy.md": ["one (1) hour"],
                    "System_and_Communications_Protection_Policy.md": [
                        "no longer than ten (10) minutes for privileged sessions",
                        "At least hourly",
                    ],
                },
            ),
            (
                Regime.FEDRAMP_MODERATE,
                {
                    "Access_Control_Policy_and_Procedures.md": [
                        "quarterly for privileged access, annually for non-privileged access",
                        "no more than 96 hours from last use",
                    ],
                    "Personnel_Security_Policy.md": ["four (4) hours"],
                },
            ),
            (
                Regime.DOD_IL4,
                {
                    "Access_Control_Policy_and_Procedures.md": [
                        "quarterly for privileged access, annually for non-privileged access",
                        "no more than 96 hours from last use",
                    ],
                    "Personnel_Security_Policy.md": ["four (4) hours"],
                },
            ),
        ):
            baseline = baseline_registry.get_regime_baseline(regime)
            flags = baseline_registry.build_regime_template_flags(regime, {})
            tokens = baseline_registry.build_regime_odp_tokens(regime, {})
            for fname, snippets in expected_snippets.items():
                raw = "\n".join(_read(os.path.join(POLICIES_DIR, fname)))
                filtered = baseline_registry.filter_policy_appendix_rows(raw, baseline["control_ids"])
                rendered = evaluate_template_conditionals(filtered, flags)
                for k, v in tokens.items():
                    rendered = rendered.replace(k, v)
                for snip in snippets:
                    self.assertIn(snip, rendered, f"{regime.value} {fname} missing {snip!r}")

    def test_tls_minimum_consistent(self) -> None:
        """No unconditional TLS 1.3 VPC/transit claim; minimum TLS 1.2 is consistent across templates."""
        sc_text = "\n".join(_read(os.path.join(POLICIES_DIR, "System_and_Communications_Protection_Policy.md")))
        ac_text = "\n".join(_read(os.path.join(POLICIES_DIR, "Access_Control_Policy_and_Procedures.md")))
        fips_text = "\n".join(_read(os.path.join(TEMPLATES_DIR, "fips", "FIPS_Cryptographic_Matrix_Template.md")))
        ssp_fr_text = "\n".join(_read(os.path.join(SSP_DIR, "SSP_FedRAMP_High_Template.md")))
        ssp_il5_text = "\n".join(_read(os.path.join(SSP_DIR, "SSP_IL5_Template.md")))

        self.assertNotIn("`TLS 1.3` and `AES-256-GCM` encapsulation", sc_text)
        self.assertNotIn("TLS 1.3 across all transit streams", sc_text)
        self.assertNotIn("(TLS 1.3/IPsec)", ac_text)
        self.assertIn("ALTS", sc_text)
        self.assertIn("AES-128-GCM", sc_text)

        for name, text in (
            ("SC Policy", sc_text),
            ("AC Policy", ac_text),
            ("FIPS Matrix", fips_text),
            ("FedRAMP High SSP", ssp_fr_text),
            ("DoD IL5 SSP", ssp_il5_text),
        ):
            self.assertIn("TLS 1.2", text, f"{name} must state TLS 1.2 minimum")

    def test_md5_qualified(self) -> None:
        """MD5 appears in templates only with 'not FIPS-approved', and never in IA-3(1)."""
        ia_text = "\n".join(_read(os.path.join(POLICIES_DIR, "Identification_and_Authentication_Policy.md")))
        for line in ia_text.splitlines():
            if "IA-03(01)" in line:
                self.assertNotIn("MD5", line)

        offenders: List[str] = []
        for root, _dirs, files in os.walk(TEMPLATES_DIR):
            for fname in sorted(files):
                if not fname.endswith((".md", ".yaml", ".yml")):
                    continue
                fpath = os.path.join(root, fname)
                for lineno, line in enumerate(_read(fpath), 1):
                    if re.search(r"\bMD5\b", line) and "not FIPS-approved" not in line:
                        offenders.append(f"{os.path.relpath(fpath, TEMPLATES_DIR)}:{lineno}: {line.strip()}")
        self.assertEqual(offenders, [], "Unqualified MD5 references in templates:\n" + "\n".join(offenders))

    def test_no_dodin_apl_requirement(self) -> None:
        """No template requires sunset DoDIN APL or UC APL certification."""
        dodin_re = re.compile(r"\b(?:DoDIN|UC)\s+APL\b", re.IGNORECASE)
        offenders: List[str] = []
        for root, _dirs, files in os.walk(TEMPLATES_DIR):
            for fname in sorted(files):
                if not fname.endswith((".md", ".yaml", ".yml")):
                    continue
                fpath = os.path.join(root, fname)
                for lineno, line in enumerate(_read(fpath), 1):
                    if dodin_re.search(line):
                        offenders.append(f"{os.path.relpath(fpath, TEMPLATES_DIR)}:{lineno}: {line.strip()}")
        self.assertEqual(offenders, [], "Sunset DoDIN/UC APL references in templates:\n" + "\n".join(offenders))

    def test_policy_odp_not_weaker_than_fedramp_high(self) -> None:
        """Policy ODP quantities rendered for FedRAMP High match the High baseline profile."""
        self.test_policy_odp_matches_active_regime()

    def test_ssp_has_all_fedramp_high_params(self) -> None:
        """SSP templates contain all FedRAMP High ODP parameter IDs."""
        self.test_fedramp_high_ssp_baseline_complete_and_has_all_params()

    def test_il5_scope_wording(self) -> None:
        """SSP_IL5_Template.md uses DISA CSP SRG V1R7 scope wording."""
        il5_text = "\n".join(_read(os.path.join(SSP_DIR, "SSP_IL5_Template.md")))
        self.assertIn("DISA Cloud Service Provider (CSP) Security Requirements Guide (SRG) V1R7", il5_text)
        self.assertIn("unclassified National Security Systems [NSS]", il5_text)

    def test_il5_dod_parameter_values(self) -> None:
        """DoD IL5 SSP render includes DISA CSP SRG V1R7 Table D-1 and CNSSI 1253 parameter values."""
        il5_raw = "\n".join(_read(os.path.join(SSP_DIR, "SSP_IL5_Template.md")))
        baseline = baseline_registry.get_regime_baseline(Regime.DOD_IL5)
        rendered = baseline_registry.render_ssp_for_regime(il5_raw, Regime.DOD_IL5, baseline)
        self.assertIn("all data, systems, or services", rendered)
        self.assertIn("30 minutes", rendered)
        self.assertIn("DODI 8520.02", rendered)
        self.assertIsNone(re.search(r"\b[A-Z]{3}-HQ[A-Z]{3}\b", rendered))

    def test_m2131_retention(self) -> None:
        """No template pairs OMB M-21-31 with <30 months total or <12 months active retention."""
        bad_clause_re = re.compile(
            r"\b(?:90\s+days|365\s+(?:calendar\s+)?days|1\s+year|18\s+months\s+total|6\s+months\s+active)\b",
            re.IGNORECASE,
        )
        offenders: List[str] = []
        for root, _dirs, files in os.walk(TEMPLATES_DIR):
            for fname in sorted(files):
                if not fname.endswith((".md", ".yaml", ".yml")):
                    continue
                fpath = os.path.join(root, fname)
                for lineno, line in enumerate(_read(fpath), 1):
                    if "M-21-31" not in line:
                        continue
                    for clause in re.split(r"[;()|]", line):
                        if "M-21-31" in clause and bad_clause_re.search(clause):
                            offenders.append(f"{os.path.relpath(fpath, TEMPLATES_DIR)}:{lineno}: {clause.strip()}")
        self.assertEqual(offenders, [], "OMB M-21-31 under-retention claims in templates:\n" + "\n".join(offenders))

    def test_no_retired_authorization_terms(self) -> None:
        """Templates contain no retired 'JAB ATO', 'JAB P-ATO', 'PA-TO', or 'JAB representatives' terms."""
        retired_re = re.compile(r"\b(?:JAB\s+ATO|JAB\s+P-ATO|PA-TO|JAB\s+representatives)\b")
        offenders: List[str] = []
        for root, _dirs, files in os.walk(TEMPLATES_DIR):
            for fname in sorted(files):
                if not fname.endswith((".md", ".yaml", ".yml")):
                    continue
                fpath = os.path.join(root, fname)
                for lineno, line in enumerate(_read(fpath), 1):
                    if retired_re.search(line):
                        offenders.append(f"{os.path.relpath(fpath, TEMPLATES_DIR)}:{lineno}: {line.strip()}")
        self.assertEqual(offenders, [], "Retired authorization terminology in templates:\n" + "\n".join(offenders))

    def test_pta_fedramp_no_citizenship(self) -> None:
        """FedRAMP render of Path_to_Authorization_Template.md has no U.S.-citizenship or Secret clearance requirement."""
        pta_raw = "\n".join(_read(os.path.join(TEMPLATES_DIR, "pta", "Path_to_Authorization_Template.md")))
        flags = baseline_registry.build_regime_template_flags(Regime.FEDRAMP_HIGH, {})
        rendered = evaluate_template_conditionals(pta_raw, flags)
        self.assertNotIn("U.S. Citizens", rendered)
        self.assertNotIn("U.S. Persons", rendered)
        self.assertNotIn("continental United States", rendered)
        self.assertNotIn("Secret eligibility", rendered)

        il5_ssp = "\n".join(_read(os.path.join(SSP_DIR, "SSP_IL5_Template.md")))
        self.assertNotIn("IT-I / IT-II (Tier 3 / Tier 5)", il5_ssp)
        self.assertIn("IT-I (Tier 5) / IT-II (Tier 3)", il5_ssp)

    def test_pta_scc_gated(self) -> None:
        """DoD IL5 render of Path_to_Authorization_Template.md contains no unconditional SCC monitoring claim."""
        pta_raw = "\n".join(_read(os.path.join(TEMPLATES_DIR, "pta", "Path_to_Authorization_Template.md")))
        flags = baseline_registry.build_regime_template_flags(Regime.DOD_IL5, {})
        rendered = evaluate_template_conditionals(pta_raw, flags)
        for line in rendered.splitlines():
            if "Security Command Center" in line:
                self.assertTrue(
                    "not in the Assured Workloads" in line
                    or "outside the Assured Workloads" in line
                    or "Authorizing Official exception" in line,
                    f"Unconditional SCC claim in IL5 PTA render: {line!r}",
                )

    def test_cjcsm_timelines_allowlisted(self) -> None:
        """No template cites fabricated CJCSM 6510.01B timelines (1h CAT 1, 8h CAT 2, 2h CAT 4)."""
        bad_cjcsm_re = re.compile(
            r"(?:CAT\s*1[^.\n]{0,40}1\s*h(?:our|r)?(?!\s*of\s*triage)"
            r"|1[-\s]*hr\s+CISA\s*/\s*CAT\s*1"
            r"|CAT\s*2[^.\n]{0,40}8\s*h(?:our|r)?s?\s*reporting"
            r"|Cat\s*1[^|\n]{0,40}:\s*1h"
            r"|Cat\s*4[^|\n]{0,40}:\s*2h"
            r"|CAT\s*4\s*\(Denial\s+of\s+Service,\s*2h)",
            re.IGNORECASE,
        )
        offenders: List[str] = []
        for root, _dirs, files in os.walk(TEMPLATES_DIR):
            for fname in sorted(files):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(root, fname)
                for lineno, line in enumerate(_read(fpath), 1):
                    if bad_cjcsm_re.search(line):
                        offenders.append(f"{os.path.relpath(fpath, TEMPLATES_DIR)}:{lineno}: {line.strip()}")
        self.assertEqual(offenders, [], "Fabricated CJCSM 6510.01B timelines in templates:\n" + "\n".join(offenders))

    def test_no_dics(self) -> None:
        """No template directs reporting to nonexistent DoD Incident Collection System (DICS)."""
        dics_re = re.compile(r"\b(?:DICS|Incident\s+Collection\s+System)\b")
        offenders: List[str] = []
        for root, _dirs, files in os.walk(TEMPLATES_DIR):
            for fname in sorted(files):
                if not fname.endswith((".md", ".yaml", ".yml")):
                    continue
                fpath = os.path.join(root, fname)
                for lineno, line in enumerate(_read(fpath), 1):
                    if dics_re.search(line):
                        offenders.append(f"{os.path.relpath(fpath, TEMPLATES_DIR)}:{lineno}: {line.strip()}")
        self.assertEqual(offenders, [], "Nonexistent DICS references in templates:\n" + "\n".join(offenders))

    def test_vpcsc_filter(self) -> None:
        """VPC-SC and IAM runbooks use singular VpcServiceControlAuditMetadata and unscoped policy logName."""
        runbooks_dir = os.path.join(TEMPLATES_DIR, "runbooks")
        offenders: List[str] = []
        for fname in sorted(os.listdir(runbooks_dir)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(runbooks_dir, fname)
            for lineno, line in enumerate(_read(fpath), 1):
                if "VpcServiceControlsAuditMetadata" in line:
                    offenders.append(f"runbooks/{fname}:{lineno}: plural VpcServiceControlsAuditMetadata")
                if 'logName="organizations/[ORG_ID]/logs/cloudaudit.googleapis.com%2Fpolicy"' in line:
                    offenders.append(f"runbooks/{fname}:{lineno}: org-scoped policy logName misses project violations")
        self.assertEqual(offenders, [], "VPC-SC filter violations:\n" + "\n".join(offenders))

        vpc_text = "\n".join(_read(os.path.join(runbooks_dir, "IR_VPC_Service_Controls_Violation_Runbook.md")))
        self.assertIn("VpcServiceControlAuditMetadata", vpc_text)
        self.assertIn("vpcServiceControlsUniqueId", vpc_text)
        self.assertIn("requestMetadata.callerIp", vpc_text)
        self.assertIn("authenticationInfo.principalEmail", vpc_text)

    def test_roles_exist(self) -> None:
        """Every roles/<svc>.<name> token in templates belongs to the verified predefined role set."""
        allowed_roles = {
            "roles/accesscontextmanager.policyAdmin",
            "roles/accesscontextmanager.policyReader",
            "roles/accesscontextmanager.vpcScTroubleshooterViewer",
            "roles/bigquery.dataViewer",
            "roles/cloudkms.admin",
            "roles/cloudkms.cryptoKeyEncrypterDecrypter",
            "roles/cloudkms.viewer",
            "roles/compute.networkViewer",
            "roles/compute.securityAdmin",
            "roles/compute.storageAdmin",
            "roles/compute.viewer",
            "roles/container.developer",
            "roles/container.viewer",
            "roles/editor",
            "roles/iam.securityAdmin",
            "roles/logging.admin",
            "roles/logging.bucketWriter",
            "roles/logging.configWriter",
            "roles/logging.fieldAccessor",
            "roles/logging.logWriter",
            "roles/logging.privateLogViewer",
            "roles/logging.viewAccessor",
            "roles/logging.viewer",
            "roles/owner",
            "roles/securitycenter.admin",
            "roles/securitycenter.adminViewer",
            "roles/securitycenter.findingsEditor",
            "roles/securitycenter.findingsViewer",
        }
        role_re = re.compile(r"\broles/[a-zA-Z0-9]+\.[a-zA-Z0-9]+\b|\broles/(?:owner|editor|viewer)\b")
        offenders: List[str] = []
        for root, _dirs, files in os.walk(TEMPLATES_DIR):
            for fname in sorted(files):
                if not fname.endswith((".md", ".yaml", ".yml")):
                    continue
                fpath = os.path.join(root, fname)
                for lineno, line in enumerate(_read(fpath), 1):
                    for role in role_re.findall(line):
                        if role not in allowed_roles:
                            offenders.append(f"{os.path.relpath(fpath, TEMPLATES_DIR)}:{lineno}: unknown role {role}")
        self.assertEqual(offenders, [], "Nonexistent IAM roles in templates:\n" + "\n".join(offenders))

    def test_destructive_commands_safeguarded(self) -> None:
        """Destructive gcloud commands in runbooks include --project, --keep-disks, and --all-versions."""
        runbooks_dir = os.path.join(TEMPLATES_DIR, "runbooks")
        offenders: List[str] = []
        for fname in sorted(os.listdir(runbooks_dir)):
            if not fname.endswith(".md"):
                continue
            text = "\n".join(_read(os.path.join(runbooks_dir, fname)))
            normalized = re.sub(r"\\\n\s*", " ", text)
            for lineno, line in enumerate(normalized.splitlines(), 1):
                if re.search(r"\bgcloud\s+[^\n`]*\bdelete\b", line):
                    if "--project" not in line:
                        offenders.append(f"runbooks/{fname}:{lineno}: gcloud delete missing --project: {line.strip()}")
                    if "compute instances delete" in line and "--keep-disks" not in line:
                        offenders.append(
                            f"runbooks/{fname}:{lineno}: compute instances delete missing --keep-disks: {line.strip()}"
                        )
                if "storage objects update" in line and "--encryption-key" in line:
                    if "--all-versions" not in line:
                        offenders.append(
                            f"runbooks/{fname}:{lineno}: objects update --encryption-key missing --all-versions"
                        )
        self.assertEqual(offenders, [], "Unsafeguarded destructive runbook commands:\n" + "\n".join(offenders))

        iam_rb = "\n".join(_read(os.path.join(runbooks_dir, "IR_IAM_Compromised_Credentials_Runbook.md")))
        self.assertIn("gcloud iam service-accounts keys disable", iam_rb)

    def test_access_level_not_deny(self) -> None:
        """VPC-SC runbook does not instruct operators to 'explicitly deny' an IP block in an Access Level."""
        vpc_rb = "\n".join(_read(os.path.join(TEMPLATES_DIR, "runbooks", "IR_VPC_Service_Controls_Violation_Runbook.md")))
        self.assertNotIn("explicitly deny", vpc_rb.lower())

    def test_cssp_list_and_dfars_7010(self) -> None:
        """Runbooks and PTA contain verified DoDM 8530.01 CSSP entities and DFARS 252.239-7010 reporting."""
        runbooks_dir = os.path.join(TEMPLATES_DIR, "runbooks")
        for fname in sorted(os.listdir(runbooks_dir)):
            if not fname.endswith(".md"):
                continue
            text = "\n".join(_read(os.path.join(runbooks_dir, fname)))
            self.assertNotIn("not verified for this template", text, fname)
            self.assertNotIn("Army RCERT", text, fname)
            self.assertNotIn("NAVIFOR", text, fname)
            self.assertIn("U.S. Army Cyber Command (ARCYBER) CSSP", text, fname)
            self.assertIn("252.239-7010", text, fname)
            self.assertIn("252.204-7012", text, fname)

        pta_text = "\n".join(_read(os.path.join(TEMPLATES_DIR, "pta", "Path_to_Authorization_Template.md")))
        self.assertNotIn("Army RCERT", pta_text)
        self.assertNotIn("NAVIFOR", pta_text)
        self.assertIn("U.S. Army Cyber Command (ARCYBER) CSSP", pta_text)
        self.assertIn("252.239-7010", pta_text)


if __name__ == "__main__":
    unittest.main()
