#!/usr/bin/env python3
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

import os
import re
import unittest
from typing import List, Tuple

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "templates"))
POLICIES_DIR = os.path.join(TEMPLATES_DIR, "policies")
SSP_DIR = os.path.join(TEMPLATES_DIR, "ssp")

#: Bracket markers the engine emits on purpose; never NIST citation tags.
INTENTIONAL_MARKERS: Tuple[str, ...] = (
    "NOT DETERMINED FROM SOURCE",
    "CONFIG_REQUIRED",
    "AI CONTEXTUAL EXAMPLE REQUIRED",
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


if __name__ == "__main__":
    unittest.main()
