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

"""
Excel Template Hydration Engine for RMF / FedRAMP Compliance Package

This module provides non-destructive, schema-validated hydration of authoritative
DoD / FedRAMP Excel templates (.xlsm) for:
1. Hardware & Software Asset Inventory (HWSWList_Template.xlsm)
2. Plan of Action & Milestones (POAM_Export_Template.xlsm)
3. Ports, Protocols, & Services Matrix (PPSMBoundariesInformationExport_Template.xlsm)
4. Security Control Traceability Matrix (ControlInfoExport_Template.xlsm)

Key Architectural Features:
- Preserves all VBA macros (keep_vba=True), formula calculations, fonts, and cell styles.
- Strict data validation checking against embedded lookup sheets ((U) Lists, Data Validation, Glossary).
- In-place row matching for SCTM (updating Columns E..AC while preserving Column A..C descriptions).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import copy
from datetime import date, datetime, timedelta
import functools
import json
import logging
import os
from pathlib import Path
import re
import zipfile
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from . import audit_log
from .baseline_registry import get_regime_baseline
from .evidence import derive_control_status, has_evidence_rule
from .file_helpers import (
    current_utc_datetime,
    zip_entry_date_time,
    classify_regime,
    clean_cell_value,
    is_dod_regime,
    is_supported_regime,
    resolve_default_csp_pato_package_id,
    ensure_directory,
    ensure_path_within_boundary,
    get_skill_root,
    get_templates_dir,
    read_json_file,
    read_yaml_file,
    resolve_path,
    scrub_sensitive_data,
    validate_system_inventory_schema,
)
from .hardware_records import (
    build_hwsw_inventory_records,
    build_ppsm_records,
    resolve_db_asset_and_os,
)
from .poam_rules import (
    active_poam_target,
    derive_poam_findings,
    extract_normalized_control_ids,
    normalize_control_id,
)

yaml: Any
try:
    import yaml
except ImportError:
    yaml = None

try:
    import openpyxl
    from openpyxl.cell.cell import Cell
    from openpyxl.worksheet.worksheet import Worksheet
    OPENPYXL_AVAILABLE = True
except ImportError:
    openpyxl = None
    Cell = None
    Worksheet = None
    OPENPYXL_AVAILABLE = False

logger = logging.getLogger(__name__)


def safe_set_cell_value(ws: Worksheet, coord: str, val: Any) -> None:
    """Safely sets a worksheet cell value handling merged cell constraints.

    Args:
        ws: The openpyxl Worksheet object.
        coord: The cell coordinate string (e.g., 'C2', 'H4').
        val: The value to clean and assign to the target cell.
    """
    try:
        cell = ws[coord]
        if type(cell).__name__ != "MergedCell":
            cell.value = clean_cell_value(val)
    except (KeyError, IndexError, ValueError, TypeError) as err:
        logger.debug("safe_set_cell_value failed for coordinate %s: %s", coord, err)


class RowStyleTemplate:
    """Per-column formatting snapshot taken once from a worksheet template row.

    Data rows inherit their formatting from a fixed template row, so the source
    cell for a given column never changes while a table is being populated.
    Copying that cell's font, border, fill, number format, protection, and
    alignment once per *cell* therefore repeats identical work for every row.
    Measured on a 441-resource fixture, that accounted for 46,550 calls and
    18.4 s of workbook hydration.

    This class performs the copies once per column and reuses the resulting
    objects. Output is unchanged: openpyxl stores styles in a workbook-level
    indexed table that deduplicates by value, so assigning one shared object to
    many cells and assigning many equal copies resolve to the same style index
    and serialise to identical bytes. The shared objects are never mutated.
    """

    __slots__ = ("_worksheet", "_row", "_cache")

    def __init__(self, worksheet: Any, row: int) -> None:
        """Binds the template to a worksheet row without reading any cells yet.

        Args:
            worksheet: Worksheet containing the template row.
            row: 1-based index of the row whose formatting should be inherited.
        """
        self._worksheet = worksheet
        self._row = row
        self._cache: Dict[int, Tuple[Any, Any, Any, Any, Any, Any]] = {}

    def _snapshot(self, column: int) -> Tuple[Any, Any, Any, Any, Any, Any]:
        """Returns the cached style objects for one column, copying on first use.

        Args:
            column: 1-based column index.

        Returns:
            A tuple of (font, border, fill, number_format, protection,
            alignment); any element is None when the template cell did not
            define that property, mirroring the guards in ``copy_cell_style``.
        """
        cached = self._cache.get(column)
        if cached is None:
            src = self._worksheet.cell(row=self._row, column=column)
            cached = (
                copy.copy(src.font) if src.font else None,
                copy.copy(src.border) if src.border else None,
                copy.copy(src.fill) if src.fill else None,
                copy.copy(src.number_format) if src.number_format else None,
                copy.copy(src.protection) if src.protection else None,
                copy.copy(src.alignment) if src.alignment else None,
            )
            self._cache[column] = cached
        return cached

    def apply(self, target_cell: Cell, column: int) -> None:
        """Applies the template row's formatting for one column to a cell.

        Args:
            target_cell: Destination cell to receive the formatting.
            column: 1-based column index whose template formatting to apply.
        """
        font, border, fill, number_format, protection, alignment = self._snapshot(column)
        if font is not None:
            target_cell.font = font
        if border is not None:
            target_cell.border = border
        if fill is not None:
            target_cell.fill = fill
        if number_format is not None:
            target_cell.number_format = number_format
        if protection is not None:
            target_cell.protection = protection
        if alignment is not None:
            target_cell.alignment = alignment


def parse_date_val(d: Any) -> Any:
    """Parses a date string or object into a date instance for Excel templates.

    Args:
        d: Raw date value (str, date, or datetime).

    Returns:
        A date object if parseable, or original string/value.
    """
    if isinstance(d, (date, datetime)):
        return d if isinstance(d, date) and not isinstance(d, datetime) else d.date()
    if isinstance(d, str):
        d_str = d.strip()
        if not d_str or d_str.upper() in ("N/A", "NONE", "PERPETUAL"):
            return d_str
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y"):
            try:
                return datetime.strptime(d_str, fmt).date()
            except ValueError:
                continue
        return d_str
    return d


def _load_reference_mappings(
    config_override_path: Optional[Union[str, Path]] = None,
    allowed_boundary: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Loads externalized reference data (military ranks, honorifics, software type maps).

    Precedence:
    1. Direct override from user compliance_config.yaml (if provided).
    2. Dedicated reference JSON: .gemini/skills/compliance/config/reference_mappings.json.
    3. Safe built-in fallback mappings.
    """
    ref_path = get_skill_root() / "config" / "reference_mappings.json"
    data: Dict[str, Any] = {}
    if ref_path.is_file():
        try:
            with open(ref_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except (OSError, ValueError) as err:
            logger.error("Failed loading reference_mappings.json from %s: %s", ref_path, err)

    if config_override_path and Path(config_override_path).is_file():
        try:
            c_data = read_yaml_file(config_override_path, allowed_boundary=allowed_boundary)
            if isinstance(c_data, dict) and isinstance(c_data.get("reference_mappings"), dict):
                for k, v in c_data["reference_mappings"].items():
                    if k == "software_type_exact_map" and isinstance(v, dict):
                        base_sw = dict(data.get("software_type_exact_map") or {})
                        for mk, mv in v.items():
                            base_sw[str(mk).lower().strip()] = str(mv)
                        data["software_type_exact_map"] = base_sw
                    elif isinstance(v, dict) and isinstance(data.get(k), dict):
                        merged_d = dict(data[k])
                        merged_d.update(v)
                        data[k] = merged_d
                    else:
                        data[k] = v
        except (OSError, ValueError) as c_err:
            logger.error("Failed loading custom reference_mappings from %s: %s", config_override_path, c_err)

    return data


def _load_target_reference_mappings(target_dir: Optional[Union[str, Path]]) -> Dict[str, Any]:
    """Loads reference_mappings from target_dir/compliance_config.yaml bounded to target_dir."""
    if not target_dir:
        return _load_reference_mappings()
    target_path = resolve_path(target_dir)
    for cfg_name in ("compliance_config.yaml", "compliance_config.yml"):
        cand = target_path / cfg_name
        if cand.is_file() and not cand.is_symlink():
            return _load_reference_mappings(cand, allowed_boundary=target_path)
    return _load_reference_mappings()


_REF_DATA = _load_reference_mappings()
MILITARY_RANKS: Set[str] = set(_REF_DATA.get("military_ranks", []))
CIVILIAN_HONORIFICS: Set[str] = set(_REF_DATA.get("civilian_honorifics", []))
KNOWN_SUFFIXES: Set[str] = set(_REF_DATA.get("known_suffixes", []))
SW_TYPE_EXACT_MAP: Dict[str, str] = dict(_REF_DATA.get("software_type_exact_map", {}))


def format_poc_name_with_comma(name: str) -> str:
    """Ensures a POC name conforms to standard DoD/eMASS 'Last, First' format.

    Military Rank vs. Name Distinction:
        In military contexts (e.g. US Army, Navy, Air Force, Marine Corps, Space Force,
        Coast Guard), titles such as 'Major', 'Colonel', 'Captain', 'General', or 'Sergeant'
        are military ranks/grades (e.g. Major is an O-4 officer rank), NOT given/first names.
        This function distinguishes military ranks and civilian honorifics from given names
        and surnames, ensuring the surname correctly precedes the comma while preserving
        the rank alongside the given name (or formatting as 'Last, Rank First'). This satisfies
        eMASS and DISA Excel spreadsheet data validation rules and automated import parsers.

    Args:
        name: Name string (e.g. 'Jane Doe', 'Major Jane Doe', 'Jane Doe, Major', or 'Doe, Jane').

    Returns:
        Formatted name string conforming to 'Last, First' or 'Last, Rank First'
        (e.g. 'Doe, Jane' or 'Doe, Major Jane').
    """
    if not name or name.startswith("[CONFIG"):
        return name
    clean = name.strip()
    if not clean:
        return name

    # If comma is present, check if rank was placed after the comma (e.g. "Jane Doe, Major")
    if "," in clean:
        parts = [p.strip() for p in clean.split(",")]
        if len(parts) == 2 and parts[1].lower() in MILITARY_RANKS:
            rank = parts[1]
            left_words = parts[0].split()
            if len(left_words) >= 2:
                last = left_words[-1]
                first = " ".join(left_words[:-1])
                return f"{last}, {rank} {first}"
            elif len(left_words) == 1:
                return f"{left_words[0]}, {rank}"
        return clean

    tokens = clean.split()
    if len(tokens) == 1:
        return clean

    # Suffix check (e.g. Jr., III)
    suffix = ""
    if len(tokens) >= 3 and tokens[-1].lower() in KNOWN_SUFFIXES:
        suffix = tokens[-1]
        tokens = tokens[:-1]

    # Check for multi-word or single-word military ranks or honorifics at start
    rank = ""
    name_tokens = tokens
    for k in range(min(4, len(tokens) - 1), 0, -1):
        prefix_candidate = " ".join(tokens[:k]).lower()
        if prefix_candidate in MILITARY_RANKS or prefix_candidate in CIVILIAN_HONORIFICS:
            rank = " ".join(tokens[:k])
            name_tokens = tokens[k:]
            break

    if len(name_tokens) >= 2:
        last = name_tokens[-1]
        first = " ".join(name_tokens[:-1])
        last_str = f"{last} {suffix}".strip()
        if rank:
            return f"{last_str}, {rank} {first}"
        return f"{last_str}, {first}"
    elif len(name_tokens) == 1:
        last_str = f"{name_tokens[0]} {suffix}".strip()
        if rank:
            return f"{last_str}, {rank}"
        return last_str

    return clean


def expand_validation_ranges(ws: Worksheet, last_row: int) -> None:
    """Expands worksheet data validation ranges ending in template table bounds up to last_row.

    Expands table validation ranges such as A8:A30 or K9:K33 up to last_row,
    while strictly preserving metadata validation ranges in rows 1 to 7 (e.g. F4:G4).

    Args:
        ws: The openpyxl Worksheet object.
        last_row: The highest populated row index.
    """
    if last_row <= 30:
        return
    for dv in ws.data_validations.dataValidation:
        if not dv.sqref:
            continue
        parts = str(dv.sqref).split()
        new_parts = []
        for part in parts:
            m = re.match(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$", part)
            if m and int(m.group(2)) >= 8 and int(m.group(4)) in (30, 33) and int(m.group(4)) < last_row:
                new_parts.append(f"{m.group(1)}{m.group(2)}:{m.group(3)}{last_row}")
            else:
                new_parts.append(part)
        dv.sqref = " ".join(new_parts)


_SW_TYPE_SIMPLE_KEYWORD_RULES: Tuple[Tuple[Tuple[str, ...], str], ...] = (
    (("postgres",), "PostgreSQL"),
    (("sql", "database", "spanner", "bigtable", "datastore", "firestore"), "Application - Database"),
    (("container", "k8s", "gke", "docker"), "Container Orchestration"),
    (("registry",), "Container Image Storage"),
    (("kms", "crypt", "secret", "vault", "key"), "KMS"),
    (("audit",), "Audit Logging"),
    (("log", "syslog"), "Centralized Event Logging"),
    (("monitor", "metric", "alert", "trace"), "Alert and Monitoring"),
    (("iam", "auth", "identity", "rbac"), "IAM"),
    (("storage", "bucket", "gcs"), "Blob Storage"),
    (("terraform",), "Terraform"),
    (("ubuntu",), "Ubuntu 22.04"),
    (("cos", "linux", "alpine", "debian", "rhel", "container_os"), "Container Operating System"),
)

_SW_TYPE_FALLBACK_KEYWORD_RULES: Tuple[Tuple[Tuple[str, ...], str, str], ...] = (
    (("react", "next", "vue", "angular", "frontend", "web"), "Web Application", "3rd Party App (SRC)"),
    (
        ("app", "custom", "service", "api", "backend", "express", "fastapi", "flask", "django", "spring"),
        "Custom Application",
        "3rd Party App (SRC)",
    ),
    (("package", "library", "framework", "npm", "pip", "pypi", "go_mod", "maven"), "3rd Party App (SRC)", "Other (Type in box)"),
)


def resolve_exact_sw_type(
    service_api: str,
    custom_services: Optional[Dict[str, Any]] = None,
    allowed_sw_types: Optional[Set[str]] = None,
    sw_type_exact_map: Optional[Dict[str, str]] = None,
) -> str:
    """Resolves any GCP service or custom tool to an exact match in Tab_SWType.

    Matches against predefined static mapping, custom service overrides, and
    keyword heuristics to ensure compliance with the sheet's data validation list.

    Args:
        service_api: The service API identifier or tool name.
        custom_services: Optional custom service catalog definitions.
        allowed_sw_types: Optional set of allowed software types from lookup tab.
        sw_type_exact_map: Optional override map loaded from target compliance_config.yaml.

    Returns:
        The matched software type string compatible with the template dropdown.
    """
    s = str(service_api).lower().strip()
    active_map = sw_type_exact_map if sw_type_exact_map is not None else SW_TYPE_EXACT_MAP
    if s in active_map:
        res = active_map[s]
        if not allowed_sw_types or res in allowed_sw_types:
            return res

    if custom_services and isinstance(custom_services, dict) and s in custom_services:
        entry = custom_services[s]
        if isinstance(entry, dict) and entry.get("sw_type"):
            cand = entry["sw_type"]
            if not allowed_sw_types or cand in allowed_sw_types:
                return cand

    for keywords, target_type in _SW_TYPE_SIMPLE_KEYWORD_RULES:
        if any(k in s for k in keywords):
            return target_type

    for keywords, preferred, fallback in _SW_TYPE_FALLBACK_KEYWORD_RULES:
        if any(k in s for k in keywords):
            return preferred if (not allowed_sw_types or preferred in allowed_sw_types) else fallback

    default_choice = "API Service"
    if allowed_sw_types and default_choice not in allowed_sw_types:
        return "3rd Party App (SRC)" if "3rd Party App (SRC)" in allowed_sw_types else "Other (Type in box)"
    return default_choice


def resolve_exact_hw_type(
    category_key: str,
    allowed_hw_types: Optional[Set[str]] = None,
) -> str:
    """Resolves hardware component category to an exact match in Tab_HWType.

    Args:
        category_key: Key representing the hardware classification.
        allowed_hw_types: Optional set of allowed hardware types from lookup tab.

    Returns:
        The matched hardware type string compatible with the template dropdown.
    """
    hw_map = {
        "cloud_tenant": "Server",
        "vpc_networking": "Switch",
        "gke_cluster": "Server - Application",
        "database": "Server - Database",
        "hsm_kms": "Virtual HSM Server",
        "compute_vm": "Virtual Machine",
        "firewall": "Firewall",
        "router": "Router",
        "switch": "Switch",
        "storage_san": "SAN",
        "load_balancer": "Server - Web",
    }
    res = hw_map.get(category_key, "Other (Type in box)")
    if allowed_hw_types and res not in allowed_hw_types:
        return "Other (Type in box)"
    return res


def _normalize_zip_timestamps(archive_path: str) -> None:
    """Rewrites ZIP member timestamps and core.xml modified date to SOURCE_DATE_EPOCH."""
    zdt = zip_entry_date_time()
    iso_ts = current_utc_datetime().strftime("%Y-%m-%dT%H:%M:%SZ")
    tmp_zip = f"{archive_path}.det.tmp"
    with zipfile.ZipFile(archive_path, "r") as zin, zipfile.ZipFile(tmp_zip, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "docProps/core.xml":
                xml_str = data.decode("utf-8", errors="replace")
                xml_str = re.sub(
                    r"(<dcterms:modified\b[^>]*>)[^<]*(</dcterms:modified>)",
                    rf"\g<1>{iso_ts}\g<2>",
                    xml_str,
                )
                data = xml_str.encode("utf-8")
            new_info = zipfile.ZipInfo(filename=item.filename, date_time=zdt)
            new_info.compress_type = item.compress_type
            new_info.external_attr = item.external_attr
            new_info.create_system = item.create_system
            zout.writestr(new_info, data)
    os.replace(tmp_zip, archive_path)


class BaseExcelHydrator(ABC):
    """Abstract base class for Excel workbook hydration pipelines."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Wraps subclass hydrate implementations with automatic descriptor cleanup."""
        super().__init_subclass__(**kwargs)
        if "hydrate" in cls.__dict__:
            orig_hydrate = cls.__dict__["hydrate"]

            @functools.wraps(orig_hydrate)
            def wrapped_hydrate(self: Any, inventory: Dict[str, Any], output_path: str, **kwargs: Any) -> str:
                try:
                    return orig_hydrate(self, inventory, output_path, **kwargs)
                finally:
                    self.close_workbook()

            setattr(cls, "hydrate", wrapped_hydrate)

    def __init__(
        self,
        template_path: str,
        target_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initializes the hydrator with a template workbook path and optional target config dir.

        Args:
            template_path: File system path to the Excel template (.xlsm).
            target_dir: Optional target workspace directory containing compliance_config.yaml.
        """
        self.template_path = template_path
        self.target_dir: Optional[Path] = resolve_path(target_dir) if target_dir else None
        self._ref_data: Dict[str, Any] = _load_target_reference_mappings(self.target_dir)
        self._sw_type_exact_map: Dict[str, str] = dict(
            self._ref_data.get("software_type_exact_map", SW_TYPE_EXACT_MAP)
        )
        self._current_wb: Optional[openpyxl.Workbook] = None

    def load_workbook(self) -> openpyxl.Workbook:
        """Validates existence and securely loads the template workbook.

        Preserves VBA macros (keep_vba=True) and formulas (data_only=False).

        Returns:
            Loaded openpyxl Workbook instance.

        Raises:
            FileNotFoundError: If the template file does not exist.
            ValueError: If the template exceeds size limits or is out of bounds.
        """
        self.template_path = str(ensure_path_within_boundary(self.template_path, os.path.dirname(os.path.abspath(self.template_path))))

        if not os.path.exists(self.template_path):
            raise FileNotFoundError(
                f"Workbook template not found at {self.template_path}"
            )

        template_size = os.path.getsize(self.template_path)
        if template_size > 50 * 1024 * 1024:
            audit_logger = audit_log.get_audit_logger()
            audit_logger.emit(
                audit_log.AuditEvent.SECURITY_VIOLATION,
                audit_log.AuditOutcome.DENIED,
                subject="excel_hydrator",
                obj=self.template_path,
                detail={"reason": f"Template workbook exceeds 50MB limit ({template_size} bytes)", "cwe": "CWE-400"}
            )
            raise ValueError(f"Template workbook exceeds size limit of 50MB: {template_size} bytes")

        logger.debug("Loading template workbook: %s", self.template_path)
        wb = openpyxl.load_workbook(
            self.template_path, data_only=False, keep_vba=True
        )
        self._current_wb = wb
        return wb

    def close_workbook(self, wb: Optional[openpyxl.Workbook] = None) -> None:
        """Safely closes workbook file descriptors and VBA ZipFile archive if open.

        Args:
            wb: Optional workbook instance to close; defaults to self._current_wb.
        """
        target = wb or self._current_wb
        if target is not None:
            vba_archive = getattr(target, "vba_archive", None)
            if vba_archive is not None:
                try:
                    vba_archive.close()
                except (OSError, ValueError) as err:
                    logger.debug("Error closing workbook vba_archive: %s", err)
                target.vba_archive = None
            try:
                target.close()
            except OSError as err:
                logger.warning("Error closing workbook descriptor: %s", err)
        if target is self._current_wb:
            self._current_wb = None

    def save_workbook(self, wb: openpyxl.Workbook, output_path: str, allowed_boundary: Optional[str] = None) -> str:
        """Ensures parent directory existence, saves workbook, and releases descriptors.

        Args:
            wb: The populated openpyxl Workbook.
            output_path: Target output path for the saved workbook.
            allowed_boundary: Optional boundary directory to restrict output path.

        Returns:
            The normalized output path to the saved workbook.
        """
        if allowed_boundary:
            abs_out = str(ensure_path_within_boundary(output_path, allowed_boundary, allow_symlinks=False))
        else:
            abs_out = os.path.abspath(output_path)

        os.makedirs(os.path.dirname(abs_out), exist_ok=True)
        try:
            now_naive = current_utc_datetime().replace(tzinfo=None)
            if getattr(wb, 'properties', None) is not None:
                wb.properties.created = now_naive
                wb.properties.modified = now_naive
            wb.save(abs_out)
            if os.environ.get('SOURCE_DATE_EPOCH', '').strip():
                _normalize_zip_timestamps(abs_out)
            logger.info("Saved hydrated workbook: %s", abs_out)
            audit_logger = audit_log.get_audit_logger()
            audit_logger.emit(
                audit_log.AuditEvent.ARTIFACT_GENERATED,
                audit_log.AuditOutcome.SUCCESS,
                subject="excel_hydrator",
                obj=output_path,
                detail={"format": "excel"}
            )
            return output_path
        finally:
            self.close_workbook(wb)

    @abstractmethod
    def hydrate(self, inventory: Dict[str, Any], output_path: str, allowed_boundary: Optional[str] = None) -> str:
        """Abstract hydration method to be overridden by specialized hydrators."""
        raise NotImplementedError


_resolve_db_asset_and_os = resolve_db_asset_and_os


def _read_hwsw_allowed_dropdown_sets(wb: openpyxl.Workbook) -> Tuple[Set[Any], Set[Any]]:
    """Reads allowed hardware and software dropdown sets from the '(U) Lists' tab."""
    if "(U) Lists" not in wb.sheetnames:
        return set(), set()
    lists_ws = wb["(U) Lists"]
    allowed_hw = {
        lists_ws.cell(row=r, column=1).value
        for r in range(2, lists_ws.max_row + 1)
        if lists_ws.cell(row=r, column=1).value is not None
    }
    allowed_sw = {
        lists_ws.cell(row=r, column=3).value
        for r in range(2, lists_ws.max_row + 1)
        if lists_ws.cell(row=r, column=3).value is not None
    }
    return allowed_hw, allowed_sw


def _populate_hwsw_sheet_headers(
    wb: openpyxl.Workbook,
    sys_info: Dict[str, Any],
    sys_name: str,
    org: str,
    so_name: str,
    isso_name: str,
    isso_email: str,
    isso_phone: str,
    eff_date: str,
) -> None:
    """Populates metadata headers on Hardware and Software worksheets."""
    eff_dt_val = parse_date_val(eff_date)
    ditpr_id = (
        sys_info.get("ditpr_id")
        or sys_info.get("ditpr_don_id")
        or sys_info.get("ditpr_emass_id")
        or "[CONFIG_REQUIRED: DITPR ID]"
    )
    for sname in ("Hardware", "Software"):
        if sname not in wb.sheetnames:
            continue
        ws = wb[sname]
        safe_set_cell_value(ws, "C2", eff_dt_val)
        safe_set_cell_value(ws, "C3", "Compliance Automation Engine")
        safe_set_cell_value(ws, "H3", org)
        safe_set_cell_value(ws, "C4", so_name)
        safe_set_cell_value(ws, "H4", format_poc_name_with_comma(isso_name))
        safe_set_cell_value(ws, "K4", eff_dt_val)
        safe_set_cell_value(ws, "C5", sys_name)
        safe_set_cell_value(ws, "H5", isso_phone)
        safe_set_cell_value(ws, "K5", isso_name)
        safe_set_cell_value(ws, "C6", ditpr_id)
        safe_set_cell_value(ws, "H6", isso_email)


def _resolve_hwsw_contract_dates(inventory: Dict[str, Any], eff_date: str) -> Tuple[Any, str, str, Any, Any]:
    """Resolves (in_service_dt_val, contract_num, contract_year, contract_exp_val, renewal_date_val)."""
    today_dt = current_utc_datetime().replace(tzinfo=None)
    try:
        eff_dt = datetime.strptime(eff_date, "%Y-%m-%d")
        in_service_dt = eff_dt if eff_dt <= today_dt else today_dt
    except (ValueError, TypeError):
        in_service_dt = today_dt

    in_service_dt_val = in_service_dt.date() if isinstance(in_service_dt, datetime) else in_service_dt
    in_service_date = in_service_dt.strftime("%Y-%m-%d")
    one_year_future = (in_service_dt + timedelta(days=365)).strftime("%Y-%m-%d")
    renewal_future = (in_service_dt + timedelta(days=335)).strftime("%Y-%m-%d")

    contracts_info = inventory.get("contracts", {})
    contract_num = contracts_info.get("contract_number") or "[CONFIG_REQUIRED: Contract Number]"
    contract_year = str(contracts_info.get("contract_year") or (in_service_date[:4] if len(in_service_date) >= 4 else "2026"))

    raw_exp = contracts_info.get("expiration_date")
    contract_exp = one_year_future
    renewal_date = renewal_future
    if raw_exp and not str(raw_exp).startswith("[CONFIG_REQUIRED"):
        try:
            exp_dt = datetime.strptime(str(raw_exp).strip(), "%Y-%m-%d")
            if exp_dt > today_dt:
                contract_exp = str(raw_exp).strip()
                renewal_date = (exp_dt - timedelta(days=30)).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    return in_service_dt_val, contract_num, contract_year, parse_date_val(contract_exp), parse_date_val(renewal_date)


def _format_hwsw_excel_rows(
    inventory: Dict[str, Any],
    allowed_hw_types: Set[Any],
    allowed_sw_types: Set[Any],
    active_sw_map: Dict[str, str],
    sys_name: str,
    so_name: str,
    eff_date: str,
) -> Tuple[List[List[Any]], List[List[Any]]]:
    """Formats canonical hardware and software records into 21-col and 34-col Excel rows."""
    custom_svcs = inventory.get("custom_services") or {}
    hw_records, sw_records, _cp, _ca = build_hwsw_inventory_records(
        inventory,
        resolve_hw_type=lambda k: resolve_exact_hw_type(k, allowed_hw_types),
        resolve_sw_type=lambda k: resolve_exact_sw_type(k, custom_svcs, allowed_sw_types, active_sw_map),
    )

    hw_rows = [
        [
            rec["hw_id"], rec["component_type"], rec["asset_name"], rec["nickname"],
            rec["mac_address"], rec["asset_ip_address"], rec["public_facing"], rec["fqdn"],
            rec["vlan"], "N/A", rec["virtual_asset"], rec["manufacturer"], rec["model_number"],
            rec["serial_number"], "N/A", "N/A", rec["os_fw_version"],
            rec["purpose_notes"], rec["location"], rec["approval_status"], rec["critical_asset"],
        ]
        for rec in hw_records
    ]

    in_service_dt_val, contract_num, contract_year, contract_exp_val, renewal_date_val = _resolve_hwsw_contract_dates(
        inventory, eff_date
    )
    contracts_info = inventory.get("contracts") or {}
    contract_agreement = contracts_info.get("agreement_name") or "[CONFIG_REQUIRED: Contract / Agreement Name]"

    sw_rows: List[List[Any]] = []
    for srec in sw_records:
        kind = srec["kind"]
        sw_id = srec["sw_id"]
        sw_type = srec.get("xlsm_software_type") or srec["software_type"]
        vendor = srec.get("xlsm_vendor") or srec["vendor"]
        ver = srec.get("xlsm_version") or srec["version"]
        purpose = srec.get("xlsm_purpose") or srec["purpose"]
        if kind == "gcp_service":
            sw_rows.append([
                sw_id, sw_type, vendor, srec["software_name"], ver,
                sys_name, "GCP Cloud Infrastructure Tenant", "VPC Network Workload Subnet",
                "Google Cloud Assured Workloads", "Resource Manager API", "N/A (Managed Cloud SaaS)",
                in_service_dt_val, contract_num, contract_year, contract_exp_val, contract_agreement,
                "Annual / Multi-Year", 0.0, 1, 0.0, 1,
                so_name, renewal_date_val, contract_exp_val, "Pending Assessment", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                "N/A", "N/A", "N/A", "Yes", "GCP Cloud Control Plane", purpose,
            ])
        elif kind == "terraform":
            sw_rows.append([
                sw_id, sw_type, vendor, srec["software_name"], ver,
                sys_name, "CI/CD Deployment Automation", "Build Worker Subnet",
                "Cloud Build / Private Worker Pool", "Git Repository", "N/A (Open Source Engine)",
                in_service_dt_val, "[CONFIG_REQUIRED: Contract Number]", contract_year, contract_exp_val, "MPL 2.0 / Commercial License",
                "Perpetual / Cloud", 0.0, 1, 0.0, 1,
                so_name, "N/A", "N/A", "Pending Assessment", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                "N/A", "N/A", "N/A", "Yes", "CI/CD Service Account", purpose,
            ])
        elif kind == "application":
            sw_rows.append([
                sw_id, sw_type, vendor, srec["software_name"], ver,
                sys_name, "Application Workload Tier", "Workload Subnet / GKE Pod",
                "Application Service", "Codebase Source", "N/A (In-House Software)",
                in_service_dt_val, "[CONFIG_REQUIRED: Contract Number]", contract_year, contract_exp_val, "Internal Proprietary",
                "Perpetual", 0.0, 1, 0.0, 1,
                so_name, "N/A", "N/A", "Pending Assessment", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                "N/A", "N/A", "N/A", "Yes", "Application Service Account", purpose,
            ])
        elif kind == "container":
            sw_rows.append([
                sw_id, sw_type, vendor, srec["software_name"], ver,
                sys_name, "Container Execution Environment", "GKE Node Pool / Cloud Run",
                "Artifact Registry", "OCI Image Manifest", "N/A (Container Image)",
                in_service_dt_val, "[CONFIG_REQUIRED: Contract Number]", contract_year, contract_exp_val, "Open Source / OCI",
                "Perpetual", 0.0, 1, 0.0, 1,
                so_name, "N/A", "N/A", "Pending Assessment", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                "N/A", "N/A", "N/A", "Yes", "Container Workload Identity", purpose,
            ])
        else:
            sw_rows.append([
                sw_id, sw_type, vendor, srec["software_name"], ver,
                sys_name, "Software Dependency", "Application Runtime Tier",
                "Package Manager Repository", "Manifest Dependency", "N/A (Open Source)",
                in_service_dt_val, "[CONFIG_REQUIRED: Contract Number]", contract_year, contract_exp_val, "Open Source Software",
                "Perpetual", 0.0, 1, 0.0, 1,
                so_name, "N/A", "N/A", "Pending Assessment", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                "N/A", "N/A", "N/A", "Yes", "Application Runtime", purpose,
            ])
    return hw_rows, sw_rows


def _write_styled_hwsw_table_rows(
    ws: Worksheet,
    rows: List[List[Any]],
    clear_to_row: int,
    clear_cols: int,
    table_name: str,
    col_end: str,
    clear_heights_up_to: int = 0,
) -> None:
    """Writes styled Hardware or Software rows starting at row 8 and updates table/validation ranges."""
    last_row = 7 + len(rows) if rows else 8
    r8_height = ws.row_dimensions[8].height
    if clear_heights_up_to:
        for r in range(8, max(clear_heights_up_to, last_row + 1)):
            ws.row_dimensions[r].height = None
    style = RowStyleTemplate(ws, 8)
    for r_offset, row_data in enumerate(rows):
        target_r = 8 + r_offset
        if not clear_heights_up_to and target_r > 8 and r8_height:
            ws.row_dimensions[target_r].height = r8_height
        for c_offset, val in enumerate(row_data):
            target_c = 1 + c_offset
            cell = ws.cell(row=target_r, column=target_c)
            cell.value = clean_cell_value(val)
            if target_r > 8:
                style.apply(cell, target_c)
    if last_row < clear_to_row:
        for r in range(last_row + 1, clear_to_row + 1):
            for c in range(1, clear_cols + 1):
                ws.cell(row=r, column=c).value = None
    tbl = ws.tables.get(table_name)
    if tbl:
        tbl.ref = f"A7:{col_end}{max(8, last_row)}"
    expand_validation_ranges(ws, last_row)


class HWSWHydrator(BaseExcelHydrator):
    """Hydrates Hardware and Software Inventory (HWSWList_Template.xlsm)."""

    def __init__(self, template_path: str, target_dir: Optional[Union[str, Path]] = None) -> None:
        """Initializes the HWSWHydrator with a template workbook path.

        Args:
            template_path: File system path to the HWSWList_Template.xlsm template.
            target_dir: Optional target directory containing compliance_config.yaml.
        """
        super().__init__(template_path, target_dir=target_dir)

    def hydrate(self, inventory: Dict[str, Any], output_path: str, allowed_boundary: Optional[str] = None) -> str:
        """Hydrates the hardware and software workbook with system inventory data."""
        wb = self.load_workbook()
        allowed_hw_types, allowed_sw_types = _read_hwsw_allowed_dropdown_sets(wb)

        sys_info = inventory.get("system_information", {})
        roles_info = inventory.get("personnel_roles", {})

        so_info = roles_info.get("system_owner", {})
        isso_info = roles_info.get("isso", {})

        sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
        org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
        eff_date = sys_info.get("effective_date") or current_utc_datetime().replace(tzinfo=None).strftime("%Y-%m-%d")

        so_name = so_info.get("name") or "[CONFIG_REQUIRED: System Owner Name]"
        isso_name = isso_info.get("name") or "[CONFIG_REQUIRED: ISSO Name]"
        isso_email = isso_info.get("email") or "[CONFIG_REQUIRED: ISSO Email]"
        isso_phone = isso_info.get("phone") or "[CONFIG_REQUIRED: ISSO Phone]"

        _populate_hwsw_sheet_headers(
            wb, sys_info, sys_name, org, so_name, isso_name, isso_email, isso_phone, eff_date
        )

        hw_rows, sw_rows = _format_hwsw_excel_rows(
            inventory, allowed_hw_types, allowed_sw_types, self._sw_type_exact_map,
            sys_name, so_name, eff_date,
        )
        if "Hardware" in wb.sheetnames:
            _write_styled_hwsw_table_rows(wb["Hardware"], hw_rows, 15, 21, "HardwareList", "U")

        if "Software" in wb.sheetnames:
            _write_styled_hwsw_table_rows(
                wb["Software"], sw_rows, 42, 34, "SoftwareList", "AH", clear_heights_up_to=45
            )

        return self.save_workbook(wb, output_path, allowed_boundary=allowed_boundary)


# POA&M rule evaluation and finding derivation is decoupled into poam_rules.py
# derive_poam_findings is imported above for backward compatibility.


class POAMHydrator(BaseExcelHydrator):
    """Hydrates Plan of Action & Milestones (POAM_Export_Template.xlsm)."""

    def __init__(self, template_path: str, target_dir: Optional[Union[str, Path]] = None) -> None:
        """Initializes the POAMHydrator with a template workbook path.

        Args:
            template_path: File system path to the POAM_Export_Template.xlsm template.
            target_dir: Optional target directory containing compliance_config.yaml.
        """
        super().__init__(template_path, target_dir=target_dir)

    def hydrate(self, inventory: Dict[str, Any], output_path: str, allowed_boundary: Optional[str] = None) -> str:
        """Hydrates the Plan of Action & Milestones workbook with findings.

        Populates system metadata and evaluates open vulnerabilities, unencrypted
        assets, or missing audit controls into schema-validated POA&M items.

        Args:
            inventory: Dictionary containing system inventory and security findings.
            output_path: Target path for the hydrated .xlsm workbook.

        Returns:
            The output path to the generated workbook.

        Raises:
            FileNotFoundError: If the template file does not exist.
        """
        wb = self.load_workbook()

        sys_info = inventory.get("system_information", {})
        roles_info = inventory.get("personnel_roles", {})
        isso_info = roles_info.get("isso", {})

        sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
        org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
        eff_date = sys_info.get("effective_date") or current_utc_datetime().replace(tzinfo=None).strftime("%Y-%m-%d")

        isso_name = isso_info.get("name") or "[CONFIG_REQUIRED: ISSO Name]"
        isso_email = isso_info.get("email") or "[CONFIG_REQUIRED: ISSO Email]"
        isso_phone = isso_info.get("phone") or "[CONFIG_REQUIRED: ISSO Phone]"

        issm_info = roles_info.get("issm", {})
        issm_name = issm_info.get("name")
        issm_phone = issm_info.get("phone")
        issm_email = issm_info.get("email")
        if issm_name and issm_email:
            office_org = f"{org}, {issm_name}, {issm_phone or 'N/A'}, {issm_email}"
        else:
            office_org = org

        if "POA&M" in wb.sheetnames:
            ws = wb["POA&M"]

            safe_set_cell_value(ws, "D2", eff_date)
            safe_set_cell_value(ws, "M2", "Major Application / Cloud Environment")
            safe_set_cell_value(ws, "P2", sys_info.get("omb_unique_investment_id") or "[CONFIG_REQUIRED: OMB Unique Investment Identifier]")
            safe_set_cell_value(ws, "D3", "Compliance Automation Engine")
            safe_set_cell_value(ws, "D4", org)
            safe_set_cell_value(ws, "M4", isso_name)
            safe_set_cell_value(ws, "D5", sys_name)
            safe_set_cell_value(ws, "M5", isso_phone)
            safe_set_cell_value(ws, "P5", sys_info.get("funding_source") or "[CONFIG_REQUIRED: Funding Source]")
            ditpr_id = (
                sys_info.get("ditpr_id")
                or sys_info.get("ditpr_don_id")
                or sys_info.get("ditpr_emass_id")
                or "[CONFIG_REQUIRED: DITPR ID]"
            )
            safe_set_cell_value(ws, "D6", ditpr_id)
            safe_set_cell_value(ws, "M6", isso_email)

            # derive_poam_findings consumes inventory["poam_items"] as *raw* user
            # input and returns normalized findings. Skipping the call when that key
            # is present would push unnormalized config straight into the workbook.
            poam_items = derive_poam_findings(inventory, eff_date, target_dir=active_poam_target())
            # When zero findings exist, maintain strict parity between YAML and Excel:
            # do not inject synthetic baseline rows into the findings table.
            poam_style = RowStyleTemplate(ws, 8)
            for r_offset, item in enumerate(poam_items):
                target_r = 8 + r_offset
                row_vals = [
                    item["control"], item["item_id"], item["desc"], item["aps"], item["checks"],
                    item["status"], item["sched_date"], "", item.get("completion_date", ""), item["milestone_id"],
                    item["milestone_desc"], item["milestone_status"], "Automated tracking active",
                    item["sched_date"], item.get("milestone_completion_date", ""), item["source"], "Cloud Posture Scanner",
                    office_org, "Cloud Security Team", "Assessor finding tracking", item["severity"],
                    "All Cloud Infrastructure Workloads", "Continuous automated guardrails in place",
                    item["severity"], item["threat"], item["likelihood"], item["impact"],
                    "Minimal mission impact under active compensating controls", item["residual"],
                    "Maintain continuous monitoring and automated IAM drift alerts", "No",
                    "[CONFIG_REQUIRED: Funding Status]", "[CONFIG_REQUIRED: Estimated Hours]", "", "", "", "", "[CONFIG_REQUIRED: Estimated Cost]", "", "", ""
                ]

                for c_offset, val in enumerate(row_vals):
                    target_c = 1 + c_offset
                    cell = ws.cell(row=target_r, column=target_c)
                    cell.value = clean_cell_value(val)
                    if target_r > 8:
                        poam_style.apply(cell, target_c)

        return self.save_workbook(wb, output_path, allowed_boundary=allowed_boundary)


def _populate_ppsm_sheet_headers(
    ws: Worksheet,
    sys_info: Dict[str, Any],
    sys_name: str,
    org: str,
    so_name: str,
    isso_name: str,
    isso_email: str,
    isso_phone: str,
    eff_date: str,
) -> None:
    """Populates metadata cells on the PPSM worksheet."""
    eff_dt_val = parse_date_val(eff_date)
    safe_set_cell_value(ws, "C2", eff_dt_val)
    safe_set_cell_value(ws, "C3", "Compliance Automation Engine")
    safe_set_cell_value(ws, "F3", org)
    safe_set_cell_value(ws, "C4", so_name)
    safe_set_cell_value(ws, "F4", format_poc_name_with_comma(isso_name))
    safe_set_cell_value(ws, "I4", eff_dt_val)
    safe_set_cell_value(ws, "C5", sys_name)
    safe_set_cell_value(ws, "F5", isso_phone)
    safe_set_cell_value(ws, "I5", isso_name)
    emass_id = sys_info.get("emass_system_id") or sys_info.get("emass_id") or "[CONFIG_REQUIRED: eMASS System ID]"
    safe_set_cell_value(ws, "C6", emass_id)
    safe_set_cell_value(ws, "F6", isso_email)
    ditpr_id = (
        sys_info.get("ditpr_id")
        or sys_info.get("ditpr_don_id")
        or sys_info.get("ditpr_emass_id")
        or "[CONFIG_REQUIRED: DITPR ID]"
    )
    safe_set_cell_value(ws, "C7", ditpr_id)
    safe_set_cell_value(ws, "F7", sys_info.get("version") or "1.0.0")


def _build_ppsm_sheet_rows(inventory: Dict[str, Any]) -> List[List[Any]]:
    """Builds PPSM table rows from canonical build_ppsm_records."""
    return [
        [
            rec["id"], rec["type"], rec["record_name"], rec["protocol"],
            rec["data_service"], rec["port"], rec["boundary"],
            rec["source_device_name"], rec["source_location"], rec["source_ip"],
            rec["source_fqdn"], rec["logical_source_point"],
            rec["destination_device_name"], rec["destination_location"],
            rec["destination_ip"], rec["destination_fqdn"],
            rec["logical_destination_point"], rec["vpn_encrypted_traffic"],
            rec["vpn_tunnel_type"], rec["purpose"],
        ]
        for rec in build_ppsm_records(inventory, cloud_provider_default="Google Cloud Platform")
    ]


class PPSMHydrator(BaseExcelHydrator):
    """Hydrates Ports, Protocols, and Services Matrix (PPSMBoundariesInformationExport_Template.xlsm)."""

    def __init__(self, template_path: str, target_dir: Optional[Union[str, Path]] = None) -> None:
        """Initializes the PPSMHydrator with a template workbook path.

        Args:
            template_path: File system path to the PPSMBoundariesInformationExport_Template.xlsm template.
            target_dir: Optional target directory containing compliance_config.yaml.
        """
        super().__init__(template_path, target_dir=target_dir)

    def hydrate(self, inventory: Dict[str, Any], output_path: str, allowed_boundary: Optional[str] = None) -> str:
        """Hydrates the Ports, Protocols, and Services Matrix workbook."""
        wb = self.load_workbook()

        sys_info = inventory.get("system_information", {})
        roles_info = inventory.get("personnel_roles", {})

        so_info = roles_info.get("system_owner", {})
        isso_info = roles_info.get("isso", {})

        sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
        org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
        eff_date = sys_info.get("effective_date") or current_utc_datetime().replace(tzinfo=None).strftime("%Y-%m-%d")

        so_name = so_info.get("name") or "[CONFIG_REQUIRED: System Owner Name]"
        isso_name = isso_info.get("name") or "[CONFIG_REQUIRED: ISSO Name]"
        isso_email = isso_info.get("email") or "[CONFIG_REQUIRED: ISSO Email]"
        isso_phone = isso_info.get("phone") or "[CONFIG_REQUIRED: ISSO Phone]"

        if "PPSM" in wb.sheetnames:
            ws = wb["PPSM"]
            _populate_ppsm_sheet_headers(
                ws, sys_info, sys_name, org, so_name, isso_name, isso_email, isso_phone, eff_date
            )
            ppsm_rows = _build_ppsm_sheet_rows(inventory)
            last_ppsm_row = 8 + len(ppsm_rows) if ppsm_rows else 9
            ppsm_r9_height = ws.row_dimensions[9].height or 45.0
            ppsm_style = RowStyleTemplate(ws, 9)

            for r_offset, row_data in enumerate(ppsm_rows):
                target_r = 9 + r_offset
                ws.row_dimensions[target_r].height = ppsm_r9_height
                for c_offset, val in enumerate(row_data):
                    target_c = 1 + c_offset
                    cell = ws.cell(row=target_r, column=target_c)
                    cell.value = clean_cell_value(val)
                    ppsm_style.apply(cell, target_c)

            if last_ppsm_row < 21:
                for r in range(last_ppsm_row + 1, 22):
                    for c in range(1, 21):
                        ws.cell(row=r, column=c).value = None

            tbl_ppsm = ws.tables.get("PPSMList")
            if tbl_ppsm:
                tbl_ppsm.ref = f"A8:T{max(9, last_ppsm_row)}"
                if tbl_ppsm.autoFilter:
                    tbl_ppsm.autoFilter.ref = tbl_ppsm.ref

            expand_validation_ranges(ws, last_ppsm_row)

        return self.save_workbook(wb, output_path, allowed_boundary=allowed_boundary)


def _prepare_sctm_hydration_context(inventory: Dict[str, Any]) -> Dict[str, Any]:
    """Resolves SCTM dates, POA&M index, YAML control guidance, and active baseline IDs."""
    sys_info = inventory.get("system_information", {})
    sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
    pato_id = resolve_default_csp_pato_package_id(sys_info)
    org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
    is_dod = is_dod_regime(sys_info)

    allow_scc = bool(
        sys_info.get("allow_unaccredited_scc_in_il5")
        or (inventory.get("security_operations") or {}).get("allow_unaccredited_scc_in_il5")
    )
    sctm_recommendation = (
        "Maintain continuous monitoring through Cloud Logging export to the CSSP SIEM and ACAS scanning."
        if (is_dod and not allow_scc)
        else "Maintain continuous monitoring through Cloud Logging and the organization's vulnerability scanning program."
    )
    today_dt = current_utc_datetime().replace(tzinfo=None)
    eff_date_str = sys_info.get("effective_date")
    past_dt = today_dt
    if eff_date_str:
        try:
            eff_dt = datetime.strptime(str(eff_date_str).strip(), "%Y-%m-%d")
            past_dt = eff_dt if eff_dt <= today_dt else today_dt
        except (ValueError, TypeError) as err:
            logger.warning(
                "Configured effective_date %r is not a valid ISO 8601 date (%s); "
                "using today's date for Implemented/Inherited controls.",
                eff_date_str,
                err,
            )
    past_date_str = past_dt.strftime("%m/%d/%Y")

    target_auth_str = sys_info.get("target_authorization_date")
    future_target_dt = None
    if target_auth_str:
        try:
            t_dt = datetime.strptime(str(target_auth_str).strip(), "%Y-%m-%d")
            if t_dt > today_dt:
                future_target_dt = t_dt
        except (ValueError, TypeError) as err:
            logger.warning(
                "Configured target_authorization_date %r is not a valid ISO 8601 date (%s); "
                "falling back to staggered default milestone dates.",
                target_auth_str,
                err,
            )

    poam_by_control: Dict[str, Dict[str, Any]] = {}
    try:
        live_poam_items = derive_poam_findings(inventory, past_date_str, target_dir=active_poam_target())
        for p_item in live_poam_items:
            c_field = f"{p_item.get('control', '')} {p_item.get('aps', '')}"
            for norm_k in extract_normalized_control_ids(c_field):
                poam_by_control.setdefault(norm_k, p_item)
    except (TypeError, ValueError, AttributeError) as err:
        logger.error("Failed to derive POA&M items for SCTM risk mapping: %s", err)

    sctm_yaml_path = get_templates_dir() / "sctm" / "SCTM_Template.yaml"
    yaml_controls: Dict[str, Dict[str, Any]] = {}
    if sctm_yaml_path.exists():
        try:
            yaml_data = read_yaml_file(sctm_yaml_path)
            for fam_item in yaml_data.get("control_families", []):
                for c_item in fam_item.get("controls", []):
                    cid = str(c_item.get("id", "")).upper().strip()
                    yaml_controls[cid] = c_item
                    yaml_controls[normalize_control_id(cid)] = c_item
        except (OSError, ValueError) as err:
            logger.warning("Optional SCTM_Template.yaml loading skipped: %s", err)

    active_regime = classify_regime(sys_info)
    active_baseline_ids: Optional[Set[str]] = (
        {normalize_control_id(c) for c in get_regime_baseline(active_regime)["control_ids"]}
        if is_supported_regime(active_regime)
        else None
    )
    return {
        "sys_name": sys_name,
        "org": org,
        "pato_id": pato_id,
        "is_dod": is_dod,
        "sctm_recommendation": sctm_recommendation,
        "past_date_str": past_date_str,
        "future_target_dt": future_target_dt,
        "future_90d": (today_dt + timedelta(days=90)).strftime("%m/%d/%Y"),
        "future_180d": (today_dt + timedelta(days=180)).strftime("%m/%d/%Y"),
        "poam_by_control": poam_by_control,
        "yaml_controls": yaml_controls,
        "active_regime": active_regime,
        "active_baseline_ids": active_baseline_ids,
    }


def _write_sctm_out_of_baseline_row(
    ws: Worksheet,
    r: int,
    norm_cid: str,
    regime_label: str,
    baseline_count: int,
) -> None:
    """Marks a control row outside the active regime baseline as Not Applicable."""
    ws.cell(row=r, column=5).value = clean_cell_value("Not Applicable")
    ws.cell(row=r, column=6).value = clean_cell_value("")
    ws.cell(row=r, column=7).value = clean_cell_value("System-Specific")
    ws.cell(row=r, column=8).value = clean_cell_value("Examine")
    ws.cell(row=r, column=9).value = clean_cell_value(
        f"Control {norm_cid} is not selected in the {regime_label} baseline."
    )
    ws.cell(row=r, column=10).value = clean_cell_value("")
    ws.cell(row=r, column=11).value = clean_cell_value(
        f"Not applicable: control {norm_cid} is outside the {regime_label} baseline "
        f"({baseline_count} controls)."
    )
    ws.cell(row=r, column=12).value = clean_cell_value("Not Applicable (Outside Baseline)")
    ws.cell(row=r, column=14).value = clean_cell_value("Low")
    ws.cell(row=r, column=15).value = clean_cell_value("Annually")
    ws.cell(row=r, column=16).value = clean_cell_value("Manual")
    ws.cell(row=r, column=17).value = clean_cell_value("Not Applicable (Outside Baseline)")
    ws.cell(row=r, column=18).value = clean_cell_value("Not Applicable (Outside Baseline)")
    ws.cell(row=r, column=19).value = clean_cell_value("Control is outside the active baseline.")
    for col_idx in range(21, 26):
        ws.cell(row=r, column=col_idx).value = clean_cell_value("Low")
    ws.cell(row=r, column=26).value = clean_cell_value("Control is outside the active baseline.")
    ws.cell(row=r, column=27).value = clean_cell_value("Not Applicable (Outside Baseline)")
    ws.cell(row=r, column=28).value = clean_cell_value("Not Applicable (Outside Baseline)")
    ws.cell(row=r, column=29).value = clean_cell_value("None required (outside baseline).")


def _write_sctm_risk_columns(
    ws: Worksheet,
    r: int,
    matched_poam: Optional[Dict[str, Any]],
    ctrl_evidence: Any,
    sctm_recommendation: str,
) -> None:
    """Writes Risk Assessment columns U..AC for an in-baseline SCTM row."""
    if matched_poam:
        poam_desc = (
            matched_poam.get("weakness_description")
            or matched_poam.get("desc")
            or matched_poam.get("title")
            or f"Open architectural finding {matched_poam.get('item_id', '')} tracked in POA&M."
        )
        poam_mit = matched_poam.get("milestone_desc") or "Automated compensating controls and Terraform policy enforcement."
        poam_imp_desc = (
            matched_poam.get("impact_description")
            or f"Potential mission impact associated with {matched_poam.get('item_id', 'finding')}; compensating guardrails active."
        )
        poam_rec = matched_poam.get("recommendations") or (
            f"Remediate via milestone {matched_poam.get('milestone_id')}: {matched_poam.get('milestone_desc')}"
            if matched_poam.get("milestone_id")
            else "Maintain continuous monitoring and remediation schedule."
        )
        values = [
            matched_poam.get("severity") or "Moderate",
            matched_poam.get("threat") or "Moderate",
            matched_poam.get("likelihood") or "Moderate",
            matched_poam.get("impact") or "Moderate",
            matched_poam.get("residual") or "Low",
            poam_desc,
            poam_mit,
            poam_imp_desc,
            poam_rec,
        ]
    else:
        values = [
            "Low",
            "Low",
            "Low",
            "Low",
            "Low",
            "No open POA&M item is recorded for this control.",
            "; ".join(ctrl_evidence.evidence) or "[CONFIG_REQUIRED: Mitigations]",
            "[CONFIG_REQUIRED: Impact Description]",
            sctm_recommendation,
        ]
    for offset, val in enumerate(values):
        ws.cell(row=r, column=21 + offset).value = clean_cell_value(val)


def _write_sctm_in_baseline_row(
    ws: Worksheet,
    r: int,
    norm_cid: str,
    clean_cid: str,
    family: str,
    inventory: Dict[str, Any],
    ctx: Dict[str, Any],
    populate_macros: Any,
) -> None:
    """Hydrates a single in-baseline SCTM row using evidence status and POA&M findings."""
    poam_by_control = ctx["poam_by_control"]
    yaml_ctrl = ctx["yaml_controls"].get(norm_cid) or ctx["yaml_controls"].get(clean_cid)
    matched_poam = (
        poam_by_control.get(norm_cid)
        or poam_by_control.get(clean_cid)
        or (poam_by_control.get(norm_cid.split("(")[0]) if "(" in norm_cid else None)
    )
    open_ids = [norm_cid.split("(")[0]] if matched_poam else []
    ctrl_evidence = derive_control_status(inventory, norm_cid, open_ids)

    common_provider = ""
    if family == "PE":
        status = "Inherited"
        designation = "Common"
        common_provider = "DoD" if ctx["is_dod"] else "Component"
        test_method = "Examine"
        narrative = (
            f"Physical and environmental protection is inherited from the cloud service provider's "
            f"authorization ({ctx['pato_id']}). [CONFIG_REQUIRED: confirm the inherited authorization and its scope]"
        )
    elif has_evidence_rule(norm_cid) and ctrl_evidence.status == "implemented":
        status = "Implemented"
        designation = "System-Specific"
        test_method = "Test, Examine"
        narrative = ctrl_evidence.narrative
    elif has_evidence_rule(norm_cid):
        status = "Planned"
        designation = "System-Specific"
        test_method = "Test, Examine"
        narrative = ctrl_evidence.narrative
    else:
        status = "Planned"
        designation = "System-Specific"
        test_method = "Test, Examine"
        narrative = f"[CONFIG_REQUIRED: implementation statement for {norm_cid}]"
        yaml_details = str((yaml_ctrl or {}).get("implementation_details") or "")
        if yaml_details and populate_macros is not None:
            narrative += " Template guidance: " + populate_macros(yaml_details, inventory, fill_examples=False)

    if status == "Planned":
        na_justification = ""
        if ctx["future_target_dt"]:
            ctrl_est_date = ctx["future_target_dt"].strftime("%m/%d/%Y")
        elif family in ("PL", "PM", "PS", "SA"):
            ctrl_est_date = ctx["future_90d"]
        else:
            ctrl_est_date = ctx["future_180d"]
    else:
        na_justification = ""
        ctrl_est_date = ctx["past_date_str"]

    slcm_comments = (
        "Inheritance reviewed against the provider's continuous monitoring deliverables."
        if status == "Inherited"
        else f"[CONFIG_REQUIRED: continuous monitoring approach for {norm_cid}]"
    )
    for col, val in (
        (5, status),
        (6, common_provider),
        (7, designation),
        (8, test_method),
        (9, na_justification),
        (10, ctrl_est_date),
        (11, narrative),
        (12, "[CONFIG_REQUIRED: Responsible Entities]"),
        (14, "High" if family in ("AC", "AU", "IA", "SC", "SI") else "Moderate"),
        (15, "Annually" if status == "Inherited" else "Monthly"),
        (16, "Manual"),
        (17, "[CONFIG_REQUIRED: continuous monitoring reporting channel]"),
        (18, "eMASS Continuous Monitoring"),
        (19, slcm_comments),
    ):
        ws.cell(row=r, column=col).value = clean_cell_value(val)

    _write_sctm_risk_columns(ws, r, matched_poam, ctrl_evidence, ctx["sctm_recommendation"])


class SCTMHydrator(BaseExcelHydrator):
    """Hydrates Security Control Traceability Matrix (ControlInfoExport_Template.xlsm) in-place."""

    def __init__(self, template_path: str, target_dir: Optional[Union[str, Path]] = None) -> None:
        """Initializes the SCTMHydrator with a template workbook path.

        Args:
            template_path: File system path to the ControlInfoExport_Template.xlsm template.
            target_dir: Optional target directory containing compliance_config.yaml.
        """
        super().__init__(template_path, target_dir=target_dir)

    def hydrate(self, inventory: Dict[str, Any], output_path: str, allowed_boundary: Optional[str] = None) -> str:
        """Hydrates the Security Control Traceability Matrix workbook in-place."""
        wb = self.load_workbook()
        inventory = scrub_sensitive_data(inventory)
        ctx = _prepare_sctm_hydration_context(inventory)
        from .generate_compliance_artifacts import populate_placeholders as _populate_sctm_macros

        if "Template" in wb.sheetnames:
            ws = wb["Template"]
            safe_set_cell_value(ws, "A2", f"Control Import Template: {ctx['sys_name']} ({ctx['org']})")
            active_baseline_ids = ctx["active_baseline_ids"]
            regime_label = ctx["active_regime"].value

            consecutive_blanks = 0
            for r in range(7, ws.max_row + 1):
                ctrl_acronym = ws.cell(row=r, column=1).value
                if not ctrl_acronym:
                    consecutive_blanks += 1
                    if consecutive_blanks > 30:
                        break
                    continue
                consecutive_blanks = 0

                ctrl_str = str(ctrl_acronym).strip().upper()
                norm_cid = normalize_control_id(ctrl_str)
                clean_cid = re.sub(r"^\[R5\]\s*", "", ctrl_str).strip()
                family = norm_cid.split("-", 1)[0] if "-" in norm_cid else "AC"

                if active_baseline_ids is not None and norm_cid not in active_baseline_ids:
                    _write_sctm_out_of_baseline_row(
                        ws, r, norm_cid, regime_label, len(active_baseline_ids)
                    )
                    continue

                _write_sctm_in_baseline_row(
                    ws, r, norm_cid, clean_cid, family, inventory, ctx, _populate_sctm_macros
                )

        return self.save_workbook(wb, output_path, allowed_boundary=allowed_boundary)


def hydrate_all_excel_templates(
    target_dir: Union[str, Path],
    inventory: Dict[str, Any],
) -> Dict[str, str]:
    """Hydrates all available Excel templates using extracted system inventory data.

    Coordinates hydration across four core DoD/FedRAMP workbooks:
    1. Hardware & Software Asset Inventory (HWSWList_Template.xlsm)
    2. Plan of Action & Milestones (POAM_Export_Template.xlsm)
    3. Ports, Protocols, & Services Matrix (PPSMBoundariesInformationExport_Template.xlsm)
    4. Security Control Traceability Matrix (ControlInfoExport_Template.xlsm)

    Args:
        target_dir: The target workspace folder where ato_artifacts should be created.
        inventory: Dictionary of system inventory, architecture, and roles.

    Returns:
        Dictionary mapping workbook keys ('hwsw', 'poam', 'ppsm', 'sctm') to output paths.
    """
    target_path = resolve_path(target_dir)
    templates_dir = get_templates_dir()
    out_dir = ensure_directory(target_path / "ato_artifacts")
    validate_system_inventory_schema(inventory, source_path=target_path / "system_inventory.json")
    inventory = scrub_sensitive_data(inventory)
    if not OPENPYXL_AVAILABLE or openpyxl is None:
        logger.warning("openpyxl is not installed; skipping Excel template hydration. Install openpyxl via 'pip install openpyxl'.")
        return {}
    logger.info("Starting Excel template hydration for target dir: %s", target_path)

    results: Dict[str, str] = {}

    # 1. HWSW
    hwsw_tpl = templates_dir / "hwsw" / "HWSWList_Template.xlsm"
    if hwsw_tpl.exists():
        hwsw_folder = ensure_directory(out_dir / "HW_SW_Inventory")
        hwsw_out = ensure_path_within_boundary(hwsw_folder / "Hardware_Software_Inventory.xlsm", out_dir)
        hydrator: BaseExcelHydrator = HWSWHydrator(str(hwsw_tpl), target_dir=target_path)
        results["hwsw"] = hydrator.hydrate(inventory, str(hwsw_out))
    else:
        logger.warning("HWSW template not found at %s", hwsw_tpl)

    # 2. POAM
    poam_tpl = templates_dir / "poam" / "POAM_Export_Template.xlsm"
    if poam_tpl.exists():
        poam_folder = ensure_directory(out_dir / "POAM")
        poam_out = ensure_path_within_boundary(poam_folder / "Plan_of_Action_and_Milestones.xlsm", out_dir)
        hydrator = POAMHydrator(str(poam_tpl), target_dir=target_path)
        results["poam"] = hydrator.hydrate(inventory, str(poam_out))
    else:
        logger.warning("POAM template not found at %s", poam_tpl)

    # 3. PPSM
    ppsm_tpl = templates_dir / "ppsm" / "PPSMBoundariesInformationExport_Template.xlsm"
    if ppsm_tpl.exists():
        ppsm_folder = ensure_directory(out_dir / "PPSM")
        ppsm_out = ensure_path_within_boundary(ppsm_folder / "PPSM_Ports_Protocols_Services.xlsm", out_dir)
        hydrator = PPSMHydrator(str(ppsm_tpl), target_dir=target_path)
        results["ppsm"] = hydrator.hydrate(inventory, str(ppsm_out))
    else:
        logger.warning("PPSM template not found at %s", ppsm_tpl)

    # 4. SCTM
    sctm_tpl = templates_dir / "sctm" / "ControlInfoExport_Template.xlsm"
    if sctm_tpl.exists():
        sctm_folder = ensure_directory(out_dir / "SCTM")
        sctm_out = ensure_path_within_boundary(sctm_folder / "SCTM_Burndown_Matrix.xlsm", out_dir)
        hydrator = SCTMHydrator(str(sctm_tpl), target_dir=target_path)
        results["sctm"] = hydrator.hydrate(inventory, str(sctm_out))
    else:
        logger.warning("SCTM template not found at %s", sctm_tpl)

    logger.info("Successfully hydrated %d Excel workbooks: %s", len(results), list(results.keys()))
    return results


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    target_path = sys.argv[1] if len(sys.argv) > 1 else "."
    inv_path = os.path.join(target_path, "system_inventory.json")
    if not os.path.exists(inv_path):
        logger.error(
            "System inventory not found at '%s'. Please run extract_system_data.py first.",
            inv_path,
        )
        sys.exit(1)

    inv_data = read_json_file(inv_path)
    validate_system_inventory_schema(inv_data, source_path=inv_path)

    generated = hydrate_all_excel_templates(os.path.abspath(target_path), inv_data)
    logger.info("Excel hydration completed: %s", list(generated.keys()))
