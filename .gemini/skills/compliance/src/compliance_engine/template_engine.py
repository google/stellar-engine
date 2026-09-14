#!/usr/bin/env python3
"""Unified Pure-Python Template Engine for Compliance & Authorization Artifacts.

Provides format-aware template rendering for public-sector and regulated ATO artifacts,
evaluating conditionals (HTML, Mustache, Jinja) and resolving configuration placeholders.
Missing configurations directly render high-visibility HTML <mark> badges in Markdown/DOCX
or safe double-quoted scalars in YAML deliverables without post-hoc regex file patching.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# High-visibility default styling for unresolved human-action review badges in Markdown
DEFAULT_BADGE_STYLE: str = (
    "background-color: #FFF3CD; color: #856404; padding: 2px 6px; "
    "border-radius: 4px; border: 1px solid #FFEEBA; font-weight: bold;"
)

# Regular expressions for template conditionals
HTML_CONDITIONAL_RE = re.compile(
    r"[ \t]*<!--\s*IF\s+(NOT\s+)?([A-Z0-9_]+)\s*-->\r?\n?(.*?)[ \t]*<!--\s*ENDIF(?:\s+\1?\2)?\s*-->\r?\n?",
    re.DOTALL | re.IGNORECASE,
)
MUSTACHE_CONDITIONAL_RE = re.compile(
    r"[ \t]*\{\{#(IF|IF_NOT)\s+([A-Z0-9_]+)\s*\}\}\r?\n?(.*?)[ \t]*\{\{/(?:IF|IF_NOT)(?:\s+\2)?\s*\}\}\r?\n?",
    re.DOTALL | re.IGNORECASE,
)
JINJA_CONDITIONAL_RE = re.compile(
    r"[ \t]*\{%\s*if\s+(not\s+)?([A-Z0-9_]+)\s*%\}\r?\n?(.*?)[ \t]*\{%\s*endif(?:\s+\1?\2)?\s*%\}\r?\n?",
    re.DOTALL | re.IGNORECASE,
)

# Unified token matching pattern: captures optional surrounding quote, double-brace or single-brace expressions
TOKEN_RE = re.compile(
    r"""(?P<full>(?P<q>["'])?\{\{\s*(?P<expr>[^{}]+?)\s*\}\}(?(q)(?P=q))|\{\s*(?P<single>[A-Za-z0-9_]+)\s*\})"""
)

# Legacy placeholder pattern for backward-compatible file hydration
LEGACY_CONFIG_REQ_RE = re.compile(r"\[CONFIG_REQUIRED:\s*([^\]]+)\]")
LEGACY_QUOTED_CONFIG_REQ_RE = re.compile(r"""(?P<q>["'])\[CONFIG_REQUIRED:\s*([^\]]+)\](?P=q)""")

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
    badge_type: str = "AI CONTEXTUAL EXAMPLE REQUIRED",
) -> str:
    """Renders a high-visibility HTML <mark> badge for Markdown / DOCX deliverables.

    Args:
        label: Human-readable variable or requirement title.
        style: Optional inline CSS style string override.
        badge_type: Warning tag prefix inside the badge.

    Returns:
        Formatted HTML <mark> string.
    """
    applied_style = style or DEFAULT_BADGE_STYLE
    clean_label = str(label).strip()
    return f'<mark style="{applied_style}">⚠️ [{badge_type}: {clean_label}]</mark>'


def render_yaml_placeholder(
    label: str,
    badge_type: str = "AI CONTEXTUAL EXAMPLE REQUIRED",
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
        fill_examples: If True, uses 'AI CONTEXTUAL EXAMPLE REQUIRED'; else 'CONFIG_REQUIRED'.

    Returns:
        Formatted placeholder string appropriate for the target format.
    """
    badge_type = "AI CONTEXTUAL EXAMPLE REQUIRED" if fill_examples else "CONFIG_REQUIRED"
    clean_name = str(token_name).strip()
    # Strip any leading [CONFIG_REQUIRED: ...] formatting if passed as raw placeholder
    if clean_name.startswith("[CONFIG_REQUIRED:"):
        clean_name = clean_name[17:].rstrip("]").strip()
    elif clean_name.startswith("[AI CONTEXTUAL EXAMPLE REQUIRED:"):
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
        r"[ \t]*<!--\s*(IF|ENDIF)\s*(NOT\s+)?([A-Z0-9_]+)?\s*-->[ \t]*(?:\r?\n)?"
        r"|[ \t]*\{\{#(IF|IF_NOT)\s+([A-Z0-9_]+)\s*\}\}[ \t]*(?:\r?\n)?"
        r"|[ \t]*\{\{/(IF|IF_NOT)(?:\s+([A-Z0-9_]+))?\s*\}\}[ \t]*(?:\r?\n)?"
        r"|[ \t]*\{%\s*(if|endif)\s*(not\s+)?([A-Z0-9_]+)?\s*%\}[ \t]*(?:\r?\n)?",
        re.IGNORECASE
    )

    result: list[str] = []
    last_end = 0
    keep_stack: list[bool] = []

    for m in TAG_RE.finditer(str(text)):
        if all(keep_stack):
            result.append(text[last_end:m.start()])
        last_end = m.end()

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
            if keep_stack:
                keep_stack.pop()

    if all(keep_stack):
        result.append(text[last_end:])

    return "".join(result)


class TemplateEngine:
    """Pure-Python format-aware templating engine for compliance documents and matrices.

    Features:
      - Native multi-syntax conditionals (HTML comments, Mustache, Jinja).
      - Direct rendering of high-visibility <mark> badges (Markdown/DOCX).
      - Direct rendering of safe double-quoted scalars (YAML).
      - Filter pipeline support (| default, | upper, | lower, | title).
      - Zero regex backslash corruption on values containing escape characters.
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
        filters = []
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
                if curr is None or curr == "" or (isinstance(curr, str) and curr.startswith("[CONFIG_REQUIRED")):
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

            # Look up value in context
            val = (
                norm_context.get(var_name)
                or norm_context.get(var_name.upper())
                or norm_context.get(var_name.lower())
            )

            val = self._apply_filters(val, filters)

            is_missing = (
                val is None
                or val == ""
                or (isinstance(val, str) and (val.startswith("[CONFIG_REQUIRED") or val.startswith("[AI CONTEXTUAL EXAMPLE REQUIRED")))
            )

            inside_quote = is_yaml and self._is_inside_quote_on_line(curr, m.start())

            if is_missing:
                # Derive label
                if isinstance(val, str) and ":" in val:
                    label = val.split(":", 1)[1].rstrip("]").strip()
                else:
                    label = var_name.replace("_", " ").title()

                if is_yaml:
                    badge_type = "AI CONTEXTUAL EXAMPLE REQUIRED" if self.fill_examples else "CONFIG_REQUIRED"
                    if inside_quote:
                        result.append(f"[{badge_type}: {label}]")
                    else:
                        result.append(f'"[{badge_type}: {label}]"')
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
        style = badge_style or DEFAULT_BADGE_STYLE

        if is_yaml:
            def _yaml_replacer(m: re.Match) -> str:
                var_name = m.group(1).strip()
                return f'"[AI CONTEXTUAL EXAMPLE REQUIRED: {var_name}]"'

            def _yaml_quoted_replacer(m: re.Match) -> str:
                var_name = m.group(2).strip()
                return f'"[AI CONTEXTUAL EXAMPLE REQUIRED: {var_name}]"'

            # First handle already-quoted placeholders to avoid double quoting
            res = LEGACY_QUOTED_CONFIG_REQ_RE.sub(_yaml_quoted_replacer, content)
            return LEGACY_CONFIG_REQ_RE.sub(_yaml_replacer, res)

        def _md_replacer(m: re.Match) -> str:
            var_name = m.group(1).strip()
            return f'<mark style="{style}">⚠️ [AI CONTEXTUAL EXAMPLE REQUIRED: {var_name}]</mark>'

        return LEGACY_CONFIG_REQ_RE.sub(_md_replacer, content)


def render_template(
    template_text: str,
    context: Dict[str, Any],
    flags: Optional[Dict[str, bool]] = None,
    target_format: str = "markdown",
    fill_examples: bool = True,
) -> str:
    """Convenience helper to render template text with standard TemplateEngine configuration.

    Args:
        template_text: Raw template content string.
        context: Context mapping of variables.
        flags: Optional boolean flags for conditional evaluation.
        target_format: Target format ('markdown' or 'yaml').
        fill_examples: Whether unassigned variables render with AI example callouts.

    Returns:
        Rendered string deliverable.
    """
    engine = TemplateEngine(target_format=target_format, fill_examples=fill_examples)
    return engine.render(template_text, context, flags=flags)
