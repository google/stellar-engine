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

"""Compatibility facade re-exporting shared utilities for the compliance engine.

This module exposes the shared primitives from :mod:`file_helpers` under a stable
import name for callers across the compliance pipeline. It exists purely for import
convenience and backward compatibility; :mod:`file_helpers` is the implementation.

The two import forms below support both package-relative use (``from .utils import ...``)
and direct script execution where ``scripts/`` is on ``sys.path``.
"""

_EXPORTS = (
    "FORMULA_TRIGGER_CHARS",
    "MAX_EXCEL_CELL_LENGTH",
    "MAX_PERCENT_DECODE_ROUNDS",
    "MAX_SECRET_SCAN_CHARS",
    "MAX_STRUCTURE_DEPTH",
    "MAX_TEXT_FILE_BYTES",
    "MAX_YAML_ALIASES",
    "MAX_YAML_BYTES",
    "clean_cell_value",
    "ensure_directory",
    "ensure_path_within_boundary",
    "escape_xml_text",
    "format_bullet_list",
    "format_markdown_table",
    "get_scripts_dir",
    "get_skill_root",
    "get_templates_dir",
    "is_sensitive_key",
    "parse_yaml_robust_file",
    "parse_yaml_robust_text",
    "parse_yaml_safe",
    "parse_yaml_scalar",
    "parse_yaml_simple",
    "read_json_file",
    "read_text_file",
    "read_yaml_file",
    "resolve_path",
    "safe_yaml_scalar",
    "sanitize_container_image_tag",
    "sanitize_filename",
    "sanitize_identifier",
    "sanitize_software_package_identity",
    "scrub_sensitive_data",
    "split_markdown_table_row",
    "strip_yaml_comment",
    "validate_compliance_config_schema",
    "validate_system_inventory_schema",
    "write_json_file",
    "write_text_file",
    "write_yaml_file",
)

try:
    from . import file_helpers as _file_helpers
except (ImportError, ValueError):
    import file_helpers as _file_helpers

# Re-export explicitly from the single source of truth. Deriving the bindings from
# _EXPORTS keeps the facade and __all__ from drifting apart, which is how the previous
# duplicated import blocks silently omitted newly added helpers.
for _name in _EXPORTS:
    globals()[_name] = getattr(_file_helpers, _name)
del _name

__all__ = list(_EXPORTS)
