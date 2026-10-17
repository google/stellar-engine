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

"""Template engine for the compliance artifacts.

Evaluates conditional blocks (HTML comment, Mustache, and Jinja syntax) and replaces
``{{ TOKEN }}`` placeholders with inventory values. A value that is missing renders as
a bracketed placeholder (``[EXAMPLE_DATA_REQUIRED: ...]`` or
``[CONFIG_REQUIRED: ...]``) in Markdown/DOCX output, or as a double-quoted scalar in
YAML output so the document still parses.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, FrozenSet, Optional, Tuple
import urllib.parse

logger = logging.getLogger(__name__)

# Inline CSS formerly used for HTML <mark> badges. Placeholders are now plain
# bracketed text; the value is kept so the badge_style parameters stay accepted.
DEFAULT_BADGE_STYLE: str = (
    "background-color: #FFF3CD; color: #856404; padding: 2px 6px; "
    "border-radius: 4px; border: 1px solid #FFEEBA; font-weight: bold;"
)

# Unified token matching pattern: captures optional surrounding quote, double-brace or
# single-brace expressions. Single-brace tokens must be upper case ({ SYSTEM_ABBR }) so
# that literal brace text in prose or code samples, such as a naming pattern written
# as gcp-{environment}-{role}, is not treated as a placeholder.
TOKEN_RE = re.compile(
    r"""(?P<full>(?P<q>["'])?\{\{\s*(?P<expr>[^{}]+?)\s*\}\}(?(q)(?P=q))|\{\s*(?P<single>[A-Z][A-Z0-9_]*)\s*\})"""
)

# Legacy placeholder pattern for backward-compatible file hydration
LEGACY_CONFIG_REQ_RE = re.compile(r"\[CONFIG_REQUIRED:\s*([^\]\[]+)\]")
_YAML_LEGACY_PLACEHOLDER_RE = re.compile(
    r"""(?P<q>["'])\[CONFIG_REQUIRED:\s*(?P<qvar>[^\]\[]+)\](?P=q)|\[CONFIG_REQUIRED:\s*(?P<uvar>[^\]\[]+)\]"""
)

# Bracketed sample placeholders from compliance_config.yaml.example (e.g. [YOUR_ORG_NAME],
# [YYYY-MM-DD], FR-XXXXXXXX, FR9999999999) that must be treated as unconfigured.
UNFILLED_PLACEHOLDER_RE = re.compile(
    r"^(?:\[(?:CONFIG_REQUIRED|EXAMPLE_DATA_REQUIRED|NOT DETERMINED FROM SOURCE)(?::[^\]]*)?\]"
    r"|\[(?:YOUR_[A-Z0-9_]+|YYYY-MM-DD|[A-Z][A-Z0-9_]{2,})(?::[^\]]*)?\]"
    r"|FR-?X+"
    r"|FR9{6,})$",
    re.IGNORECASE,
)


#: Any unresolved operator input or evidence gap inside free text. Sample tokens must
#: contain an underscore ([ISSM_NAME]) so prose such as "[CUI]" or the redaction
#: marker "[REDACTED_SENSITIVE]" is not mistaken for a placeholder.
PENDING_PLACEHOLDER_RE = re.compile(
    r"\[(?:CONFIG_REQUIRED|EXAMPLE_DATA_REQUIRED|NOT DETERMINED FROM SOURCE)(?::[^\]\[\n]*)?\]"
    r"|\[(?:YOUR_[A-Z0-9_]+|YYYY-MM-DD)\]"
    r"|\[(?!REDACTED_SENSITIVE\])[A-Z][A-Z0-9]*_[A-Z0-9_]+\]"
    r"|\bFR-?X{4,}\b"
    r"|\bFR9{6,}\b"
)

NOT_DETERMINED_MARKER = "[NOT DETERMINED FROM SOURCE]"


def contains_unfilled_placeholder(text: Any) -> bool:
    """True when free text still contains an unresolved placeholder or evidence gap."""
    return isinstance(text, str) and PENDING_PLACEHOLDER_RE.search(text) is not None


def is_unfilled_placeholder(val: Any) -> bool:
    """Returns True if a value is None, empty, or an unfilled template/example placeholder."""
    if val is None:
        return True
    if not isinstance(val, str):
        return False
    stripped = val.strip()
    if not stripped:
        return True
    if stripped.startswith(("[CONFIG_REQUIRED", "[EXAMPLE_DATA_REQUIRED", "[NOT DETERMINED FROM SOURCE]")):
        return True
    return bool(UNFILLED_PLACEHOLDER_RE.match(stripped))


# Matches a Markdown/HTML <mark> badge wrapper. The inner character classes are
# negated and non-overlapping, so matching is linear and cannot backtrack (no ReDoS).
HTML_BADGE_RE = re.compile(r"<mark\b[^>]*>(?P<label>[^<]*)</mark>")

# Control characters that cannot appear literally in a double-quoted YAML scalar.
_YAML_CONTROL_ESCAPES: Dict[str, str] = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
    "\x00": "\\0",
}


def _escape_yaml_double_quoted(value: str) -> str:
    """Escapes a string for safe interpolation into a double-quoted YAML scalar.

    Templates supply their own surrounding quotes, so substituted values are spliced
    directly into a quoted context. Any unescaped double quote terminates the scalar
    early and corrupts the document -- structurally the same failure mode as SQL or
    HTML injection, and observed in practice when HTML badge markup reached the SCTM
    matrix and rendered it unparseable.

    Backslash is escaped first so escapes introduced by later replacements are not
    themselves re-escaped.

    Args:
        value: Raw text destined for a double-quoted YAML scalar.

    Returns:
        The escaped text, safe to place between double quotes.
    """
    escaped: list[str] = []
    for char in value:
        replacement = _YAML_CONTROL_ESCAPES.get(char)
        if replacement is not None:
            escaped.append(replacement)
        elif ord(char) < 0x20:
            escaped.append(f"\\x{ord(char):02x}")
        else:
            escaped.append(char)
    return "".join(escaped)


def _strip_html_badges(value: str) -> str:
    """Reduces HTML ``<mark>`` badge markup to its plain-text label.

    Badges are a Markdown/DOCX presentation concern. A YAML deliverable is consumed
    by machines (eMASS, GRC intake), so the markup is both meaningless and actively
    harmful there.

    Args:
        value: Text that may contain badge markup.

    Returns:
        The text with any badge wrappers replaced by their labels.
    """
    if "<mark" not in value:
        return value
    return HTML_BADGE_RE.sub(lambda m: m.group("label").strip(), value)


def render_badge(
    label: str,
    style: Optional[str] = None,
    badge_type: str = "EXAMPLE_DATA_REQUIRED",
) -> str:
    """Renders a high-visibility badge for Markdown / DOCX deliverables.

    Args:
        label: Human-readable variable or requirement title.
        style: Optional inline CSS style string override (retained for backward compatibility).
        badge_type: Warning tag prefix inside the badge.

    Returns:
        Formatted badge string using bracketed notation.
    """
    clean_label = str(label).strip()
    return f"[{badge_type}: {clean_label}]"


def render_yaml_placeholder(
    label: str,
    badge_type: str = "EXAMPLE_DATA_REQUIRED",
    already_quoted: bool = False,
) -> str:
    """Renders a safe double-quoted scalar for YAML deliverables without breaking AST syntax.

    Args:
        label: Human-readable variable or requirement title.
        badge_type: Warning tag prefix.
        already_quoted: Unused parameter kept for API consistency.

    Returns:
        YAML-safe double-quoted scalar string.
    """
    clean_label = str(label).strip()
    return f'"[{badge_type}: {clean_label}]"'


def format_missing_placeholder(
    token_name: str,
    target_format: str = "markdown",
    already_quoted: bool = False,
    badge_style: Optional[str] = None,
    fill_examples: bool = True,
) -> str:
    """Formats a missing configuration placeholder according to the destination file format.

    Args:
        token_name: Variable identifier or label.
        target_format: Destination format identifier ('markdown', 'docx', 'yaml', etc.).
        already_quoted: If True, indicates the template token was already wrapped in quotes.
        badge_style: Optional inline CSS style override for HTML mark badges.
        fill_examples: If True, uses 'EXAMPLE_DATA_REQUIRED'; else 'CONFIG_REQUIRED'.

    Returns:
        Formatted placeholder string appropriate for the target format.
    """
    badge_type = "EXAMPLE_DATA_REQUIRED" if fill_examples else "CONFIG_REQUIRED"
    clean_name = str(token_name).strip()
    # Strip any leading [CONFIG_REQUIRED: ...] formatting if passed as raw placeholder
    if clean_name.startswith("[CONFIG_REQUIRED:"):
        clean_name = clean_name[17:].rstrip("]").strip()
    elif clean_name.startswith("[EXAMPLE_DATA_REQUIRED:"):
        clean_name = clean_name[32:].rstrip("]").strip()
    elif clean_name.startswith("[") and clean_name.endswith("]"):
        clean_name = clean_name[1:-1].strip()

    fmt = str(target_format).lower().strip()
    if fmt in ("markdown", "docx", "md", "html"):
        return render_badge(clean_name, style=badge_style, badge_type=badge_type)
    if fmt in ("yaml", "yml"):
        return render_yaml_placeholder(clean_name, badge_type=badge_type, already_quoted=already_quoted)
    return f"[{badge_type}: {clean_name}]"


def evaluate_template_conditionals(text: str, flags: Dict[str, bool]) -> str:
    """Evaluates conditional blocks across HTML comment, Mustache, and Jinja syntax.

    Supports nested conditionals in a single pass to prevent template injection tricks
    and avoid exponential ReDoS complexity.

    Args:
        text: Raw template content containing conditional blocks.
        flags: Mapping of flag names (case-insensitive) to boolean state.

    Returns:
        Content with evaluated conditional blocks rendered or excised.
    """
    norm_flags = {str(k).upper().strip(): bool(v) for k, v in flags.items()}

    TAG_RE = re.compile(
        r"(?:<!--\s*(IF|ENDIF)\s*(NOT\s+)?([A-Z0-9_]+)?\s*-->"
        r"|\{\{#(IF|IF_NOT)\s+([A-Z0-9_]+)\s*\}\}"
        r"|\{\{/(IF|IF_NOT)(?:\s+([A-Z0-9_]+))?\s*\}\}"
        r"|\{%\s*(if|endif)\s*(not\s+)?([A-Z0-9_]+)?\s*%\})",
        re.IGNORECASE
    )

    src_text = str(text)
    result: list[str] = []
    last_end = 0
    keep_stack: list[bool] = []

    for m in TAG_RE.finditer(src_text):
        tag_start = m.start()
        tag_end = m.end()

        # Strip leading horizontal whitespace and trailing newline ONLY when the tag occupies its entire line
        line_start = src_text.rfind("\n", 0, tag_start) + 1
        before_on_line = src_text[line_start:tag_start]
        if before_on_line.strip(" \t") == "":
            after_match = re.match(r"^[ \t]*(\r?\n)", src_text[tag_end:])
            if after_match:
                tag_start = line_start
                tag_end = tag_end + after_match.end()
            elif tag_end == len(src_text) and line_start < tag_start:
                tag_start = line_start

        if all(keep_stack):
            result.append(src_text[last_end:tag_start])
        last_end = tag_end

        is_open = False
        is_not = False
        var_name = ""

        if m.group(1):  # HTML
            is_open = m.group(1).upper() == "IF"
            is_not = bool(m.group(2))
            var_name = (m.group(3) or "").upper()
        elif m.group(4):  # Mustache start
            is_open = True
            is_not = m.group(4).upper() == "IF_NOT"
            var_name = (m.group(5) or "").upper()
        elif m.group(6):  # Mustache end
            is_open = False
        elif m.group(8):  # Jinja
            is_open = m.group(8).upper() == "IF"
            is_not = bool(m.group(9))
            var_name = (m.group(10) or "").upper()

        if is_open:
            val = norm_flags.get(var_name, False)
            keep = (not val) if is_not else val
            keep_stack.append(keep)
        else:
            if not keep_stack:
                raise ValueError(f"Unmatched closing conditional tag {m.group(0)!r} at offset {m.start()}")
            keep_stack.pop()

    if keep_stack:
        raise ValueError(f"Unclosed conditional block ({len(keep_stack)} open tag(s) remaining at EOF)")

    if all(keep_stack):
        result.append(src_text[last_end:])

    return "".join(result)


_BLOCK_MARKDOWN_VARS: FrozenSet[str] = frozenset({
    "SYSTEM_DESCRIPTION",
    "SUBNET_BOUNDARY_TABLE",
    "CONTAINER_WORKLOAD_TABLE",
    "FIREWALL_MATRIX",
    "SERVICE_ACCOUNTS_LIST",
    "STORAGE_BUCKETS_LIST",
    "GCP_SERVICES_ENABLED",
    "TERRAFORM_MODULES",
    "SEPARATION_OF_DUTIES_TABLE",
    "THREAT_DETECTION_IMPLEMENTATION",
    "AUDIT_AND_SIEM_IMPLEMENTATION",
    "INCIDENT_ESCALATION_IMPLEMENTATION",
    "VULNERABILITY_MANAGEMENT_IMPLEMENTATION",
    "IDENTITY_ACCESS_IMPLEMENTATION",
    "DISCOVERED_ENVIRONMENT_CONTEXT",
})

_MD_LINK_RE: re.Pattern[str] = re.compile(
    r"\[([^\]\[]+)\]\(([^()\r\n]+(?:\([^()\r\n]*\)[^()\r\n]*)*)\)"
)


def is_safe_hyperlink_url(url: str) -> bool:
    """Applies the DOCX hyperlink URL allowlist (HTTP/HTTPS, mailto, #anchor; no UNC/file/traversal)."""
    if not url:
        return False
    clean_url = re.sub(r"[\x00-\x20\x7f]", "", url)
    if not clean_url or "\\" in clean_url or ".." in clean_url or clean_url.startswith(("//", "/")):
        return False
    parsed = urllib.parse.urlparse(clean_url)
    scheme = parsed.scheme.lower()
    if scheme in ("http", "https"):
        after_scheme = clean_url[len(scheme) + 3:]
        return bool(parsed.netloc) and not after_scheme.startswith(("/", "\\"))
    if scheme == "mailto":
        return bool(parsed.path) and "/" not in parsed.path and "@" in parsed.path
    if not scheme:
        return clean_url.startswith("#") and len(clean_url) > 1 and "/" not in clean_url
    return False


def _sanitize_markdown_links(text: str) -> str:
    """Strips Markdown links whose target URL fails is_safe_hyperlink_url down to link text."""
    def _replace_link(m: re.Match[str]) -> str:
        link_text = m.group(1)
        raw_url = m.group(2).strip()
        if raw_url.startswith("<") and raw_url.endswith(">"):
            raw_url = raw_url[1:-1].strip()
        if " " in raw_url:
            raw_url = raw_url.split(None, 1)[0]
        if is_safe_hyperlink_url(raw_url):
            return m.group(0)
        return link_text

    return _MD_LINK_RE.sub(_replace_link, text)


def _sanitize_markdown_inline_value(val_str: str, on_table_line: bool, at_line_start: bool) -> str:
    """Normalizes CR/LF and escapes block/table Markdown metacharacters in inline fields."""
    cleaned = re.sub(r"[\r\n]+", " ", val_str)
    if on_table_line:
        cleaned = re.sub(r"(?<!\\)\|", r"\|", cleaned)
    if at_line_start:
        stripped = cleaned.lstrip()
        if stripped.startswith(("#", ">", "- ", "* ")):
            lead_ws = cleaned[: len(cleaned) - len(stripped)]
            cleaned = f"{lead_ws}\\{stripped}"
    return cleaned


class TemplateEngine:
    """Format-aware renderer for compliance documents and matrices.

    Supports HTML comment, Mustache, and Jinja conditionals; bracketed placeholders
    for missing values (Markdown/DOCX) or double-quoted scalars (YAML); and the
    filters ``default``, ``upper``, ``lower``, and ``title``. Values are inserted
    literally, so backslashes in a value are never interpreted as regex escapes.
    """

    def __init__(
        self,
        target_format: str = "markdown",
        fill_examples: bool = True,
        badge_style: Optional[str] = None,
    ) -> None:
        """Initializes the TemplateEngine.

        Args:
            target_format: Destination format ('markdown', 'docx', 'yaml', etc.).
            fill_examples: Whether unconfigured variables render with AI example callouts.
            badge_style: Optional inline CSS style string for HTML mark badges.
        """
        self.target_format = str(target_format).lower().strip()
        self.fill_examples = fill_examples
        self.badge_style = badge_style or DEFAULT_BADGE_STYLE

    def evaluate_conditionals(self, text: str, flags: Dict[str, bool]) -> str:
        """Evaluates conditional blocks in template text against provided boolean flags."""
        return evaluate_template_conditionals(text, flags)

    def _parse_expression(self, raw_expr: str) -> Tuple[str, list[Tuple[str, Optional[str]]]]:
        """Parses variable expression and optional filter pipelines (e.g. 'VAR | default("val")')."""
        parts = [p.strip() for p in raw_expr.split("|")]
        var_name = parts[0]
        filters: list[Tuple[str, Optional[str]]] = []
        for f_str in parts[1:]:
            f_str = f_str.strip()
            if "(" in f_str and f_str.endswith(")"):
                f_name, f_arg_str = f_str.split("(", 1)
                f_arg = f_arg_str[:-1].strip().strip("\"'")
                filters.append((f_name.strip().lower(), f_arg))
            else:
                filters.append((f_str.lower(), None))
        return var_name, filters

    def _apply_filters(self, val: Any, filters: list[Tuple[str, Optional[str]]]) -> Any:
        """Applies a sequence of filters to a resolved value."""
        curr = val
        for f_name, f_arg in filters:
            if f_name == "default":
                if is_unfilled_placeholder(curr):
                    curr = f_arg
            elif f_name == "upper" and curr is not None:
                curr = str(curr).upper()
            elif f_name == "lower" and curr is not None:
                curr = str(curr).lower()
            elif f_name == "title" and curr is not None:
                curr = str(curr).title()
        return curr

    @staticmethod
    def _is_inside_quote_on_line(text: str, match_start: int) -> bool:
        """Determines if match_start position is within an open single or double quote on the same line."""
        line_start = text.rfind("\n", 0, match_start)
        line_start = 0 if line_start == -1 else line_start + 1
        prefix = text[line_start:match_start]
        dquotes = len(re.findall(r'(?<!\\)"', prefix))
        squotes = len(re.findall(r"(?<!\\)'", prefix))
        return (dquotes % 2 == 1) or (squotes % 2 == 1)

    def render(
        self,
        template_text: str,
        context: Dict[str, Any],
        flags: Optional[Dict[str, bool]] = None,
    ) -> str:
        """Renders template text against context dictionary and optional conditional flags.

        Args:
            template_text: Raw template string with variables and conditionals.
            context: Data dictionary mapping variable keys to values.
            flags: Optional boolean flags for evaluating conditional blocks.

        Returns:
            Populated string with format-aware placeholder rendering.
        """
        curr = template_text
        if flags:
            curr = self.evaluate_conditionals(curr, flags)

        # Build normalized lookup dictionary supporting stripped, uppercase, and lowercase keys
        norm_context: Dict[str, Any] = {}
        for k, v in context.items():
            clean_k = str(k).strip("{} ").strip()
            norm_context[clean_k] = v
            norm_context[clean_k.upper()] = v
            norm_context[clean_k.lower()] = v

        is_yaml = self.target_format in ("yaml", "yml")

        result: list[str] = []
        last_end = 0

        for m in TOKEN_RE.finditer(curr):
            result.append(curr[last_end:m.start()])
            q = m.group("q")
            raw_expr = m.group("expr") or m.group("single")
            var_name, filters = self._parse_expression(raw_expr)

            # Look up value in context. Membership, not truthiness: a count of 0
            # is a real value and must not be reported as missing configuration.
            val = None
            found = False
            for key in (var_name, var_name.upper(), var_name.lower()):
                if key in norm_context:
                    val = norm_context[key]
                    found = True
                    break

            if m.group("single") and not found:
                # Single-brace syntax is only a placeholder when the name is known;
                # otherwise it is literal text (for example "${PROJECT_ID}" in a
                # shell sample) and is left unchanged.
                result.append(m.group(0))
                last_end = m.end()
                continue

            val = self._apply_filters(val, filters)

            # "[NOT DETERMINED FROM SOURCE] ..." is a deliberate, explained evidence gap
            # written by the generator; it is rendered as-is, not replaced by a badge.
            is_missing = is_unfilled_placeholder(val) and not (
                isinstance(val, str) and val.strip().startswith(NOT_DETERMINED_MARKER)
            )

            inside_quote = is_yaml and self._is_inside_quote_on_line(curr, m.start())

            if is_missing:
                # Derive label
                if (
                    isinstance(val, str)
                    and val.strip().startswith(("[CONFIG_REQUIRED:", "[EXAMPLE_DATA_REQUIRED:"))
                ):
                    label = val.split(":", 1)[1].rstrip("]").strip()
                else:
                    label = var_name.replace("_", " ").title()

                if is_yaml:
                    badge_type = "EXAMPLE_DATA_REQUIRED" if self.fill_examples else "CONFIG_REQUIRED"
                    safe_label = _escape_yaml_double_quoted(label)
                    if inside_quote:
                        result.append(f"[{badge_type}: {safe_label}]")
                    else:
                        result.append(f'"[{badge_type}: {safe_label}]"')
                else:
                    placeholder = format_missing_placeholder(
                        label,
                        target_format=self.target_format,
                        already_quoted=bool(q),
                        badge_style=self.badge_style,
                        fill_examples=self.fill_examples,
                    )
                    result.append(f"{q}{placeholder}{q}" if q else placeholder)
            else:
                # Real value present
                val_str = str(val)
                if is_yaml:
                    # Markdown badge markup must never reach a YAML deliverable: it
                    # is presentational, and its embedded double quotes terminate the
                    # scalar early.
                    val_str = _strip_html_badges(val_str)
                    if inside_quote:
                        # The template already supplies the surrounding quotes, so the
                        # value is being spliced into a double-quoted scalar. Escaping
                        # here is what keeps arbitrary extracted data (bucket
                        # descriptions, IAM role text, scanner output) from breaking
                        # the document structure.
                        result.append(_escape_yaml_double_quoted(val_str))
                    elif q:
                        result.append(f'"{_escape_yaml_double_quoted(val_str)}"')
                    else:
                        result.append(val_str)
                else:
                    val_str = _sanitize_markdown_links(val_str)
                    upper_var = var_name.upper()
                    if upper_var not in _BLOCK_MARKDOWN_VARS and not upper_var.startswith("CONTROL_PARAMETER_ROWS_"):
                        line_start = curr.rfind("\n", 0, m.start())
                        line_start = 0 if line_start == -1 else line_start + 1
                        line_end = curr.find("\n", m.end())
                        if line_end == -1:
                            line_end = len(curr)
                        line_str = curr[line_start:line_end]
                        on_table_line = "|" in line_str
                        at_line_start = (curr[line_start:m.start()].strip() == "")
                        val_str = _sanitize_markdown_inline_value(
                            val_str, on_table_line=on_table_line, at_line_start=at_line_start
                        )
                    result.append(f"{q}{val_str}{q}" if q else val_str)

            last_end = m.end()

        result.append(curr[last_end:])
        return "".join(result)

    @staticmethod
    def hydrate_legacy_placeholders(
        content: str,
        is_yaml: bool,
        badge_style: Optional[str] = None,
    ) -> str:
        """Hydrates legacy [CONFIG_REQUIRED: ...] strings in existing files safely.

        Args:
            content: Raw text content of the target file.
            is_yaml: True if destination file is a YAML deliverable.
            badge_style: Optional inline CSS style for Markdown HTML mark tags.

        Returns:
            Transformed content string.
        """
        del badge_style  # Unused: bracketed badge notation replaces inline HTML mark tags

        if is_yaml:
            def _yaml_single_pass_replacer(m: re.Match) -> str:
                raw_var = (m.group("qvar") or m.group("uvar") or "").strip()
                escaped_var = _escape_yaml_double_quoted(raw_var)
                if m.group("q"):
                    return f'"[EXAMPLE_DATA_REQUIRED: {escaped_var}]"'
                if TemplateEngine._is_inside_quote_on_line(content, m.start()):
                    return f"[EXAMPLE_DATA_REQUIRED: {escaped_var}]"
                return f'"[EXAMPLE_DATA_REQUIRED: {escaped_var}]"'

            return _YAML_LEGACY_PLACEHOLDER_RE.sub(_yaml_single_pass_replacer, content)

        def _md_replacer(m: re.Match) -> str:
            var_name = m.group(1).strip()
            return f"[EXAMPLE_DATA_REQUIRED: {var_name}]"

        return LEGACY_CONFIG_REQ_RE.sub(_md_replacer, content)
