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
try:
    import yaml
except ImportError:
    yaml = None
try:
    from . import audit_log
except (ImportError, ValueError):
    import audit_log
from typing import Any, Dict, Optional, Set, Tuple, Union
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

try:
    from .extract_system_data import (
        clean_interpolated_string,
        is_valid_cidr,
        is_valid_resource_name,
    )
    from .file_helpers import (
        clean_cell_value,
        DEFAULT_CSP_PATO_PACKAGE_ID,
        ensure_directory,
        ensure_path_within_boundary,
        extract_clean_subnets,
        get_skill_root,
        get_templates_dir,
        has_terraform_infrastructure,
        read_json_file,
        read_yaml_file,
        resolve_path,
        sanitize_container_image_tag,
        sanitize_software_package_identity,
        scrub_sensitive_data,
        validate_system_inventory_schema,
    )
    from .service_catalog import resolve_gcp_service
    from .poam_rules import derive_poam_findings
except (ImportError, ValueError):
    from extract_system_data import (
        clean_interpolated_string,
        is_valid_cidr,
        is_valid_resource_name,
    )
    from file_helpers import (
        clean_cell_value,
        DEFAULT_CSP_PATO_PACKAGE_ID,
        ensure_directory,
        ensure_path_within_boundary,
        extract_clean_subnets,
        get_skill_root,
        get_templates_dir,
        has_terraform_infrastructure,
        read_json_file,
        read_yaml_file,
        resolve_path,
        sanitize_container_image_tag,
        sanitize_software_package_identity,
        scrub_sensitive_data,
        validate_system_inventory_schema,
    )
    from service_catalog import resolve_gcp_service
    from poam_rules import derive_poam_findings

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


def copy_cell_style(src_cell: Cell, target_cell: Cell) -> None:
    """Safely copies formatting properties from a source cell to a target cell.

    Suitable for one-off copies. When styling a whole table from a single
    template row, use :class:`RowStyleTemplate` instead: this function
    re-derives the same six style copies for every target cell, which dominates
    workbook hydration cost on large inventories.

    Args:
        src_cell: The reference Cell object containing styles.
        target_cell: The destination Cell object to receive styling.
    """
    if src_cell.font:
        target_cell.font = copy.copy(src_cell.font)
    if src_cell.border:
        target_cell.border = copy.copy(src_cell.border)
    if src_cell.fill:
        target_cell.fill = copy.copy(src_cell.fill)
    if src_cell.number_format:
        target_cell.number_format = copy.copy(src_cell.number_format)
    if src_cell.protection:
        target_cell.protection = copy.copy(src_cell.protection)
    if src_cell.alignment:
        target_cell.alignment = copy.copy(src_cell.alignment)


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


def _load_reference_mappings(config_override_path: Optional[str] = None) -> Dict[str, Any]:
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
            c_data = read_yaml_file(config_override_path)
            if isinstance(c_data, dict) and "reference_mappings" in c_data:
                for k, v in c_data["reference_mappings"].items():
                    if isinstance(v, dict) and isinstance(data.get(k), dict):
                        data[k].update(v)
                    else:
                        data[k] = v
        except (OSError, ValueError) as c_err:
            logger.error("Failed loading custom reference_mappings from %s: %s", config_override_path, c_err)

    return data


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





def resolve_exact_sw_type(
    service_api: str,
    custom_services: Optional[Dict[str, Any]] = None,
    allowed_sw_types: Optional[Set[str]] = None,
) -> str:
    """Resolves any GCP service or custom tool to an exact match in Tab_SWType.

    Matches against predefined static mapping, custom service overrides, and
    keyword heuristics to ensure compliance with the sheet's data validation list.

    Args:
        service_api: The service API identifier or tool name.
        custom_services: Optional custom service catalog definitions.
        allowed_sw_types: Optional set of allowed software types from lookup tab.

    Returns:
        The matched software type string compatible with the template dropdown.
    """
    s = str(service_api).lower().strip()
    if s in SW_TYPE_EXACT_MAP:
        res = SW_TYPE_EXACT_MAP[s]
        if not allowed_sw_types or res in allowed_sw_types:
            return res

    if custom_services and isinstance(custom_services, dict) and s in custom_services:
        entry = custom_services[s]
        if isinstance(entry, dict) and "sw_type" in entry and entry["sw_type"]:
            cand = entry["sw_type"]
            if not allowed_sw_types or cand in allowed_sw_types:
                return cand

    # Keyword heuristics guaranteed to match Tab_SWType
    if "postgres" in s:
        return "PostgreSQL"
    if any(k in s for k in ["sql", "database", "spanner", "bigtable", "datastore", "firestore"]):
        return "Application - Database"
    if any(k in s for k in ["container", "k8s", "gke", "docker"]):
        return "Container Orchestration"
    if "registry" in s:
        return "Container Image Storage"
    if any(k in s for k in ["kms", "crypt", "secret", "vault", "key"]):
        return "KMS"
    if "audit" in s:
        return "Audit Logging"
    if any(k in s for k in ["log", "syslog"]):
        return "Centralized Event Logging"
    if any(k in s for k in ["monitor", "metric", "alert", "trace"]):
        return "Alert and Monitoring"
    if any(k in s for k in ["iam", "auth", "identity", "rbac"]):
        return "IAM"
    if any(k in s for k in ["storage", "bucket", "gcs"]):
        return "Blob Storage"
    if "terraform" in s:
        return "Terraform"
    if "ubuntu" in s:
        return "Ubuntu 22.04"
    if any(k in s for k in ["cos", "linux", "alpine", "debian", "rhel", "container_os"]):
        return "Container Operating System"
    if any(k in s for k in ["react", "next", "vue", "angular", "frontend", "web"]):
        if not allowed_sw_types or "Web Application" in allowed_sw_types:
            return "Web Application"
        return "3rd Party App (SRC)"
    if any(k in s for k in ["app", "custom", "service", "api", "backend", "express", "fastapi", "flask", "django", "spring"]):
        if not allowed_sw_types or "Custom Application" in allowed_sw_types:
            return "Custom Application"
        return "3rd Party App (SRC)"
    if any(k in s for k in ["package", "library", "framework", "npm", "pip", "pypi", "go_mod", "maven"]):
        return "3rd Party App (SRC)" if (not allowed_sw_types or "3rd Party App (SRC)" in allowed_sw_types) else "Other (Type in box)"

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

            cls.hydrate = wrapped_hydrate

    def __init__(self, template_path: str) -> None:
        """Initializes the hydrator with a template workbook path.

        Args:
            template_path: File system path to the Excel template (.xlsm).
        """
        self.template_path = template_path
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
        try:
            from .file_helpers import ensure_path_within_boundary, get_templates_dir
        except (ImportError, ValueError):
            from file_helpers import ensure_path_within_boundary, get_templates_dir
            
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
        """Safely closes workbook file descriptors if open.

        Args:
            wb: Optional workbook instance to close; defaults to self._current_wb.
        """
        target = wb or self._current_wb
        if target is not None:
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
            wb.save(abs_out)
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


def resolve_db_asset_and_os(raw_type: str, raw_ver: str, engine_val: str) -> Tuple[str, str]:
    """Resolves canonical database asset name and operating system string.

    Ensures consistent hardware/software inventory representation across
    both macro-enabled Excel workbooks (.xlsm) and structured YAML files.

    Args:
        raw_type: Database resource type (e.g. google_sql_database_instance, google_spanner_instance).
        raw_ver: Configured or default database version string.
        engine_val: Specific database engine identifier.

    Returns:
        Tuple of (asset_name, os_name_ver).
    """
    t_low = str(raw_type).lower()
    v_low = (str(raw_ver) + " " + str(engine_val)).lower()

    if "bigquery" in t_low:
        return "BigQuery Analytics Dataset", "BigQuery Managed Analytics Engine"
    if "redis" in t_low:
        return "Memorystore Redis HA Cluster", "Redis 7.0 / Managed In-Memory Engine"
    if "spanner" in t_low:
        return "Cloud Spanner Instance", "Cloud Spanner Distributed Relational Engine"
    if "alloydb" in t_low:
        return "AlloyDB PostgreSQL Cluster", "PostgreSQL 15 / AlloyDB Managed Engine"

    if "mysql" in v_low:
        engine_name = "MySQL"
        os_base = "Debian Linux Base"
    elif "sqlserver" in v_low or "sql_server" in v_low or "mssql" in v_low:
        engine_name = "SQL Server"
        os_base = "Windows Server Base"
    elif "postgres" in v_low or any(v in v_low for v in ("13", "14", "15", "16")):
        engine_name = "PostgreSQL"
        os_base = "Debian Linux Base"
    else:
        engine_name = "PostgreSQL"
        os_base = "Debian Linux Base"

    prefix = f"Cloud SQL {engine_name} Instance".replace("  ", " ") if engine_name else "Cloud SQL Database Instance"

    clean_v = clean_interpolated_string(str(raw_ver), default_val=str(raw_ver))
    if engine_name and os_base:
        db_os_str = f"{engine_name} {clean_v} / {os_base}" if engine_name.lower() not in clean_v.lower() else f"{clean_v} / {os_base}"
    else:
        db_os_str = str(clean_v)

    return prefix, db_os_str


_resolve_db_asset_and_os = resolve_db_asset_and_os


class HWSWHydrator(BaseExcelHydrator):
    """Hydrates Hardware and Software Inventory (HWSWList_Template.xlsm)."""

    def __init__(self, template_path: str) -> None:
        """Initializes the HWSWHydrator with a template workbook path.

        Args:
            template_path: File system path to the HWSWList_Template.xlsm template.
        """
        super().__init__(template_path)

    def hydrate(self, inventory: Dict[str, Any], output_path: str, allowed_boundary: Optional[str] = None) -> str:
        """Hydrates the hardware and software workbook with system inventory data.

        Populates system metadata, hardware components (VMs, GKE, databases, VPCs, KMS),
        and software components (GCP APIs, Terraform, applications, container images, packages).

        Args:
            inventory: Dictionary containing extracted system inventory information.
            output_path: Target path for the hydrated .xlsm workbook.

        Returns:
            The output path to the generated workbook.

        Raises:
            FileNotFoundError: If the template file does not exist.
        """
        wb = self.load_workbook()

        # Read allowed dropdown sets from (U) Lists if present
        allowed_hw_types = set()
        allowed_sw_types = set()
        allowed_approvals = set()
        if "(U) Lists" in wb.sheetnames:
            lists_ws = wb["(U) Lists"]
            allowed_hw_types = set([lists_ws.cell(row=r, column=1).value for r in range(2, lists_ws.max_row+1) if lists_ws.cell(row=r, column=1).value is not None])
            allowed_sw_types = set([lists_ws.cell(row=r, column=3).value for r in range(2, lists_ws.max_row+1) if lists_ws.cell(row=r, column=3).value is not None])
            allowed_approvals = set([lists_ws.cell(row=r, column=5).value for r in range(2, lists_ws.max_row+1) if lists_ws.cell(row=r, column=5).value is not None])

        sys_info = inventory.get("system_information", {})
        net_info = inventory.get("network_architecture", {})
        infra_info = inventory.get("infrastructure_components", {})
        roles_info = inventory.get("personnel_roles", {})

        so_info = roles_info.get("system_owner", {})
        isso_info = roles_info.get("isso", {})

        sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
        sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
        org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
        location = sys_info.get("primary_location") or "[CONFIG_REQUIRED: Primary Location]"
        eff_date = sys_info.get("effective_date") or datetime.now().strftime("%Y-%m-%d")

        so_name = so_info.get("name") or "[CONFIG_REQUIRED: System Owner Name]"
        isso_name = isso_info.get("name") or "[CONFIG_REQUIRED: ISSO Name]"
        isso_email = isso_info.get("email") or "[CONFIG_REQUIRED: ISSO Email]"
        isso_phone = isso_info.get("phone") or "[CONFIG_REQUIRED: ISSO Phone]"

        # -------------------------------------------------------------
        # 1. Populate Metadata on Hardware and Software Sheets
        # -------------------------------------------------------------
        eff_dt_val = parse_date_val(eff_date)
        for sname in ["Hardware", "Software"]:
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
            ditpr_id = sys_info.get("ditpr_id") or sys_info.get("ditpr_don_id") or sys_info.get("ditpr_emass_id") or (f"DITPR-{sys_abbr}-001" if sys_info.get("system_abbreviation") else "[CONFIG_REQUIRED: DITPR ID]")
            safe_set_cell_value(ws, "C6", ditpr_id)
            safe_set_cell_value(ws, "H6", isso_email)

        # -------------------------------------------------------------
        # 2. Populate Hardware Sheet Data (Row 8+)
        # -------------------------------------------------------------
        if "Hardware" in wb.sheetnames:
            ws_hw = wb["Hardware"]
            hw_rows = []
            hw_id = 1

            # Baseline CSP Tenant (Server)
            hw_type_tenant = resolve_exact_hw_type("cloud_tenant", allowed_hw_types)
            raw_subnets = net_info.get("subnets_cidrs", [])
            clean_subnets = extract_clean_subnets(raw_subnets)
            tenant_ip = ", ".join(clean_subnets) if clean_subnets else "Dynamic Cloud IP Allocation"
            cloud_provider = (
                sys_info.get("cloud_provider")
                or inventory.get("cloud_provider")
                or "Google Cloud Platform (GCP)"
            )
            csp_abbr = "GCP"
            hypervisor_sdn = "Google Cloud Hypervisor / Andromeda SDN"

            hw_rows.append([
                hw_id, hw_type_tenant, f"{cloud_provider} Projects & Hierarchy", f"{csp_abbr} Cloud Tenant ({sys_abbr})",
                "N/A (Cloud Virtual Asset)", tenant_ip, "No", "N/A (Private Cloud Boundary)",
                "N/A", "N/A", "Yes", cloud_provider, "Infrastructure-as-a-Service (IaaS)",
                f"{csp_abbr}-CSP-{sys_abbr}-001", "N/A", "N/A", hypervisor_sdn,
                "Dynamic Cloud Allocation", location, "Approved", "Yes"
            ])
            hw_id += 1

            # VPCs & Subnets (Switch)
            raw_vpcs = net_info.get("vpcs", [])
            clean_vpcs = []
            for v in raw_vpcs:
                cv = clean_interpolated_string(v)
                if is_valid_resource_name(cv) and cv not in clean_vpcs:
                    clean_vpcs.append(cv)
            if clean_vpcs or clean_subnets:
                v_str = ", ".join(clean_vpcs[:4]) if clean_vpcs else f"{csp_abbr} Software Defined VPC"
                s_str = ", ".join(clean_subnets) if clean_subnets else "10.0.0.0/16"
                hw_type_switch = resolve_exact_hw_type("vpc_networking", allowed_hw_types)
                hw_rows.append([
                    hw_id, hw_type_switch, f"{csp_abbr} Virtual Private Cloud (VPC)", v_str,
                    "Dynamic SDN MAC", s_str, "No", "N/A (Private Cloud Boundary)",
                    "N/A", "N/A", "Yes", cloud_provider, "Software-Defined VPC Networking",
                    f"{csp_abbr}-VPC-{sys_abbr}-001", "N/A", "N/A", f"{cloud_provider} SDN",
                    "Dynamic Cloud Allocation", location, "Approved", "Yes"
                ])
                hw_id += 1

            # GKE Clusters (Server - Application)
            hw_type_gke = resolve_exact_hw_type("gke_cluster", allowed_hw_types)
            for gke in infra_info.get("gke_clusters", []):
                raw_gke_name = gke.get("name", "gke-cluster")
                gke_name = clean_interpolated_string(raw_gke_name, default_val="gke-cluster")
                gke_ip = gke.get("master_ipv4_cidr_block") or "Private Control Plane & Node CIDR"
                gke_ver = gke.get("master_version", "1.28+")
                gke_mfg = "Google Cloud Platform"
                k8s_title = "Google Kubernetes Engine (GKE) Private Cluster"
                k8s_os = f"Google Container-Optimized OS (COS) / K8s {gke_ver}"
                hw_rows.append([
                    hw_id, hw_type_gke, k8s_title, gke_name,
                    "Dynamic SDN MAC", gke_ip, "No", "N/A (Control Plane Private Endpoint)",
                    "N/A", "N/A", "Yes", gke_mfg, f"Managed Control Plane & Node Pool ({gke_ver})",
                    f"{csp_abbr}-K8S-{sys_abbr}-{hw_id:03d}", "N/A", "N/A", k8s_os,
                    "Standard Node Instances", location, "Approved", "Yes"
                ])
                hw_id += 1

            _resolve_db_asset_and_os = resolve_db_asset_and_os

            hw_type_db = resolve_exact_hw_type("database", allowed_hw_types)
            seen_dbs = set()
            for db in infra_info.get("databases", []):
                raw_db_name = db.get("name", "db-instance")
                db_name = clean_interpolated_string(raw_db_name, default_val=raw_db_name)
                if not is_valid_resource_name(db_name) or db_name in ("name", "id", "db", "database"):
                    continue
                raw_type = db.get("type", "Cloud Database Instance")
                raw_ver = db.get("database_version") or db.get("engine_version") or "PostgreSQL 15"
                engine_val = db.get("engine", "")

                db_asset_name, db_os = _resolve_db_asset_and_os(raw_type, raw_ver, engine_val)
                dedup_key = (db_asset_name, db_name)
                if dedup_key in seen_dbs:
                    continue
                seen_dbs.add(dedup_key)

                db_tier = db.get("tier", "Managed Tier")
                p_net = db.get("private_network")
                clean_pnet = clean_interpolated_string(str(p_net), default_val="") if p_net else ""
                if p_net and "psa_private_network" in str(p_net):
                    db_ip = f"Private VPC / PSC ({clean_subnets[0] if clean_subnets else '100.127.4.0/24'})"
                elif clean_pnet and is_valid_resource_name(clean_pnet) and not any(k in clean_pnet.lower() for k in ("var.", "local.", "vpc_id", "each.", "try(")):
                    db_ip = f"Private VPC ({clean_pnet})"
                else:
                    db_ip = "Private Service Connect / Internal Endpoint"

                db_mfg = "Google Cloud Platform"
                hw_rows.append([
                    hw_id, hw_type_db, db_asset_name, str(db_name),
                    "Dynamic SDN MAC", db_ip, "No", "N/A",
                    "N/A", "N/A", "Yes", db_mfg, f"{db_asset_name} ({db_tier})",
                    f"{csp_abbr}-DB-{sys_abbr}-{hw_id:03d}", "N/A", "N/A", db_os,
                    "Managed Cloud DB Allocation", location, "Approved", "Yes"
                ])
                hw_id += 1

            # KMS Key Rings / HSM (Virtual HSM Server)
            hw_type_hsm = resolve_exact_hw_type("hsm_kms", allowed_hw_types)
            seen_kms = set()
            for k in infra_info.get("kms_keys", []):
                raw_k_name = k.get("name", "kms-key")
                k_name = clean_interpolated_string(raw_k_name, default_val=raw_k_name)
                if not is_valid_resource_name(k_name) or k_name in ("name", "key", "keys", "keyring"):
                    continue
                if k_name in seen_kms:
                    continue
                seen_kms.add(k_name)

                k_prot = k.get("protection_level", "SOFTWARE")
                k_loc = k.get("location") or location or "us-east4"
                k_asset_name = "Cloud KMS FIPS 140-3 Level 3 HSM Key Ring" if k_prot == "HSM" else "Cloud KMS Cryptographic Key"
                k_model = f"Cloud KMS ({k_prot})"
                k_vendor = (
                    "Google Cloud Platform / Marvell LiquidSecurity HSM"
                    if k_prot == "HSM"
                    else "Google Cloud Platform"
                )
                kms_conn = "Private Service Connect Endpoint"
                kms_endpoint = "cloudkms.googleapis.com"
                kms_vip = "N/A (Restricted VIP 199.36.153.4/30)"

                hw_rows.append([
                    hw_id, hw_type_hsm, k_asset_name, str(k_name),
                    "N/A (Hardware HSM)" if k_prot == "HSM" else "N/A (Virtual Key Management)",
                    kms_conn, "No", kms_endpoint,
                    kms_vip, "N/A", "No" if k_prot == "HSM" else "Yes",
                    k_vendor, k_model,
                    f"{csp_abbr}-KMS-{sys_abbr}-{hw_id:03d}", "N/A", "N/A", "FIPS 140-3 Level 3 Verified Firmware",
                    "Hardware Cryptographic Key Store" if k_prot == "HSM" else "Software Key Store",
                    k_loc, "Approved", "Yes"
                ])
                hw_id += 1

            # Compute VMs (Virtual Machine)
            hw_type_vm = resolve_exact_hw_type("compute_vm", allowed_hw_types)
            seen_vms = set()
            for vm in infra_info.get("compute_instances", []):
                raw_vm_name = vm.get("name", "vm-instance")
                vm_name = clean_interpolated_string(raw_vm_name, default_val=raw_vm_name)
                if not is_valid_resource_name(vm_name) or vm_name in ("name", "vm", "instance"):
                    continue
                if vm_name in seen_vms:
                    continue
                seen_vms.add(vm_name)

                m_type = vm.get("machine_type", "n2-standard-4")
                raw_sub = vm.get("subnetwork")
                clean_sub = clean_interpolated_string(raw_sub, default_val="workload-subnet") if raw_sub else "workload-subnet"
                if clean_sub in ("subnet_id", "subnet", ""):
                    clean_sub = "workload-subnet"
                ip_addr = vm.get("network_ip") or f"Private Subnet: {clean_sub} ({clean_subnets[0] if clean_subnets else '100.127.4.0/24'})"

                default_zone = (
                    f"{location.split()[0]}-a"
                    if location and not location.startswith("[CONFIG")
                    else "us-east4-a"
                )
                sn = (
                    vm.get("self_link")
                    or f"projects/{sys_abbr}/zones/{vm.get('zone', default_zone)}/instances/{vm_name}"
                )
                raw_img = vm.get("image", "Linux / Shielded VM")
                vm_os = clean_interpolated_string(raw_img, default_val="Linux / Shielded VM")
                if "/family/" in vm_os:
                    vm_os = vm_os.split("/family/")[-1].strip()
                elif "/images/" in vm_os:
                    vm_os = vm_os.split("/images/")[-1].strip()

                vm_asset_name = "Google Compute Engine VM Instance"
                vm_mfg = "Google Cloud Platform"
                vm_desc = f"Hardened Compute Engine Workload Instance ({vm_name})"
                hw_rows.append([
                    hw_id, hw_type_vm, vm_asset_name, str(vm_name),
                    "Dynamic SDN MAC", ip_addr, "No", "N/A",
                    "N/A", "N/A", "Yes", vm_mfg, str(m_type),
                    str(sn), "N/A", "N/A", str(vm_os),
                    vm_desc, location, "Approved", "Yes"
                ])
                hw_id += 1

            # Populate Data Rows (Row 8+) on Hardware
            # Inherit template formatting (font, border, fill, number_format, alignment) from row 8
            last_hw_row = 7 + len(hw_rows) if hw_rows else 8
            hw_r8_height = ws_hw.row_dimensions[8].height
            hw_style = RowStyleTemplate(ws_hw, 8)
            for r_offset, row_data in enumerate(hw_rows):
                target_r = 8 + r_offset
                if target_r > 8 and hw_r8_height:
                    ws_hw.row_dimensions[target_r].height = hw_r8_height
                for c_offset, val in enumerate(row_data):
                    target_c = 1 + c_offset
                    cell = ws_hw.cell(row=target_r, column=target_c)
                    cell.value = clean_cell_value(val)
                    if target_r > 8:
                        hw_style.apply(cell, target_c)

            # Clear unused rows within the original template table range (A7:U15)
            if last_hw_row < 15:
                for r in range(last_hw_row + 1, 16):
                    for c in range(1, 22):
                        ws_hw.cell(row=r, column=c).value = None

            # Update Excel Table definition range
            tbl_hw = ws_hw.tables.get("HardwareList")
            if tbl_hw:
                tbl_hw.ref = f"A7:U{max(8, last_hw_row)}"

            # Expand data validations if last_hw_row > 30
            expand_validation_ranges(ws_hw, last_hw_row)

        # -------------------------------------------------------------
        # 3. Populate Software Sheet Data (Row 8+)
        # -------------------------------------------------------------
        if "Software" in wb.sheetnames:
            ws_sw = wb["Software"]
            sw_rows = []
            sw_id = 1

            today_dt = datetime.now()
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
            contract_agreement = contracts_info.get("agreement_name") or "Google Cloud Enterprise Master Agreement"
            contract_num = contracts_info.get("contract_number") or "UII-GCP-001"
            contract_year = str(contracts_info.get("contract_year") or (in_service_date[:4] if len(in_service_date) >= 4 else "2026"))

            raw_exp = contracts_info.get("expiration_date")
            if raw_exp and not str(raw_exp).startswith("[CONFIG_REQUIRED"):
                try:
                    exp_dt = datetime.strptime(str(raw_exp).strip(), "%Y-%m-%d")
                    if exp_dt > today_dt:
                        contract_exp = str(raw_exp).strip()
                        renewal_date = (exp_dt - timedelta(days=30)).strftime("%Y-%m-%d")
                    else:
                        contract_exp = one_year_future
                        renewal_date = renewal_future
                except (ValueError, TypeError):
                    contract_exp = one_year_future
                    renewal_date = renewal_future
            else:
                contract_exp = one_year_future
                renewal_date = renewal_future

            contract_exp_val = parse_date_val(contract_exp)
            renewal_date_val = parse_date_val(renewal_date)

            custom_svcs = inventory.get("custom_services", {})
            for svc in infra_info.get("services_enabled", []):
                category, sw_name, purpose = resolve_gcp_service(svc, custom_svcs)
                exact_sw_type = resolve_exact_sw_type(svc, custom_svcs, allowed_sw_types)

                sw_rows.append([
                    sw_id, exact_sw_type, "Google Cloud Platform", sw_name, "GCP Managed API",
                    sys_name, "GCP Cloud Infrastructure Tenant", "VPC Network Workload Subnet",
                    "Google Cloud Assured Workloads", "Resource Manager API", "N/A (Managed Cloud SaaS)",
                    in_service_dt_val, contract_num, contract_year, contract_exp_val, contract_agreement,
                    "Annual / Multi-Year", 0.0, 1, 0.0, 1,
                    so_name, renewal_date_val, contract_exp_val, "Approved", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                    "N/A", "N/A", "N/A", "Yes", "GCP Cloud Control Plane", purpose
                ])
                sw_id += 1

            # HashiCorp Terraform Engine (Only if Terraform IaC is present in the boundary)
            if has_terraform_infrastructure(inventory):
                engine_v = (
                    infra_info.get("terraform_engine_version")
                    or inventory.get("terraform_engine_version")
                    or "1.8.0+"
                )
                prov_vers = (
                    infra_info.get("provider_versions")
                    or inventory.get("provider_versions")
                    or {}
                )
                if prov_vers:
                    prov_desc = ", ".join(f"{p} {v}" for p, v in prov_vers.items())
                    iac_ver_str = f"{engine_v} ({prov_desc})"
                else:
                    iac_ver_str = f"{engine_v} / Cloud Provider v5.0+"

                exact_tf_type = resolve_exact_sw_type(
                    "terraform", custom_svcs, allowed_sw_types
                )
                sw_rows.append([
                    sw_id, exact_tf_type, f"HashiCorp / {cloud_provider}",
                    f"HashiCorp Terraform / {csp_abbr} Provider",
                    iac_ver_str, sys_name, "CI/CD Deployment Automation", "Build Worker Subnet",
                    "Cloud Build / Private Worker Pool", "Git Repository", "N/A (Open Source Engine)",
                    in_service_dt_val, "UII-IAC-001", contract_year, contract_exp_val, "MPL 2.0 / Commercial License",
                    "Perpetual / Cloud", 0.0, 1, 0.0, 1,
                    so_name, "N/A", "N/A", "Approved", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                    "N/A", "N/A", "N/A", "Yes", "CI/CD Service Account",
                    "Automated declarative IaC blueprint provisioning & drift detection"
                ])
                sw_id += 1

            # Discovered Applications & Services
            app_info = inventory.get("application_components", {})
            seen_apps = set()
            for app in app_info.get("applications", []):
                app_name = app.get("name", "Application Service")
                if app_name in seen_apps:
                    continue
                seen_apps.add(app_name)
                app_type_exact = resolve_exact_sw_type(app.get("framework", "app"), custom_svcs, allowed_sw_types)
                app_ver = app.get("version", "1.0.0")
                app_desc = f"{app.get('type', 'Custom Application')} ({app.get('language')}) in {app.get('file')}"
                sw_rows.append([
                    sw_id, app_type_exact, "Internal Development", app_name, app_ver,
                    sys_name, "Application Workload Tier", "Workload Subnet / GKE Pod",
                    "Application Service", "Codebase Source", "N/A (In-House Software)",
                    in_service_dt_val, f"UII-APP-{sw_id:03d}", contract_year, contract_exp_val, "Internal Proprietary",
                    "Perpetual", 0.0, 1, 0.0, 1,
                    so_name, "N/A", "N/A", "Approved", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                    "N/A", "N/A", "N/A", "Yes", "Application Service Account", app_desc
                ])
                sw_id += 1

            # Discovered Container Images
            seen_c = set()
            for c in app_info.get("container_images", []):
                raw_c_img = str(c.get("base_image") or c.get("image") or "container-image")
                c_img, c_ver = sanitize_container_image_tag(
                    clean_interpolated_string(raw_c_img, default_val="container-image"),
                    default_img="container-image"
                )
                if c_img in seen_c:
                    continue
                seen_c.add(c_img)
                c_type_exact = resolve_exact_sw_type("container_os", custom_svcs, allowed_sw_types)
                c_desc = f"Hardened Container Base Image ({c.get('file')})"
                sw_rows.append([
                    sw_id, c_type_exact, "Container Registry", c_img, c_ver,
                    sys_name, "Container Execution Environment", "GKE Node Pool / Cloud Run",
                    "Artifact Registry", "OCI Image Manifest", "N/A (Container Image)",
                    in_service_dt_val, f"UII-CTR-{sw_id:03d}", contract_year, contract_exp_val, "Open Source / OCI",
                    "Perpetual", 0.0, 1, 0.0, 1,
                    so_name, "N/A", "N/A", "Approved", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                    "N/A", "N/A", "N/A", "Yes", "Container Workload Identity", c_desc
                ])
                sw_id += 1

            # Discovered Software Packages & Frameworks
            seen_p = set()
            for pkg in app_info.get("software_packages", []):
                raw_p_name = str(pkg.get("name") or pkg.get("package_name") or "unknown-package")
                raw_p_ver = str(pkg.get("version") or "Latest")
                p_name, p_ver = sanitize_software_package_identity(
                    clean_interpolated_string(raw_p_name, default_val="unknown-package"),
                    clean_interpolated_string(raw_p_ver, default_val="Latest"),
                    default_name="unknown-package"
                )
                if not p_name or p_name in seen_p:
                    continue
                seen_p.add(p_name)
                p_eco = pkg.get("ecosystem", "Open Source")
                p_cat = pkg.get("category", "Third-Party Library")
                p_type_exact = resolve_exact_sw_type(p_name, custom_svcs, allowed_sw_types)
                p_desc = f"{p_cat} dependency imported in {pkg.get('file')}"
                sw_rows.append([
                    sw_id, p_type_exact, p_eco, p_name, p_ver,
                    sys_name, "Software Dependency", "Application Runtime Tier",
                    "Package Manager Repository", "Manifest Dependency", "N/A (Open Source)",
                    in_service_dt_val, f"UII-LIB-{sw_id:03d}", contract_year, contract_exp_val, "Open Source Software",
                    "Perpetual", 0.0, 1, 0.0, 1,
                    so_name, "N/A", "N/A", "Approved", in_service_dt_val, in_service_dt_val, in_service_dt_val,
                    "N/A", "N/A", "N/A", "Yes", "Application Runtime", p_desc
                ])
                sw_id += 1

            # Populate Data Rows (Row 8+) on Software
            # Inherit template formatting (font, border, fill, number_format, alignment) from row 8
            last_sw_row = 7 + len(sw_rows) if sw_rows else 8
            # Clear pre-allocated fixed row heights from template rows 8..45 to allow auto-fitting
            for r in range(8, max(45, last_sw_row + 1)):
                ws_sw.row_dimensions[r].height = None

            sw_style = RowStyleTemplate(ws_sw, 8)
            for r_offset, row_data in enumerate(sw_rows):
                target_r = 8 + r_offset
                for c_offset, val in enumerate(row_data):
                    target_c = 1 + c_offset
                    cell = ws_sw.cell(row=target_r, column=target_c)
                    cell.value = clean_cell_value(val)
                    if target_r > 8:
                        sw_style.apply(cell, target_c)

            # Clear unused rows within the original template table range (A7:AH42)
            if last_sw_row < 42:
                for r in range(last_sw_row + 1, 43):
                    for c in range(1, 35):
                        ws_sw.cell(row=r, column=c).value = None

            # Update Excel Table definition range
            tbl_sw = ws_sw.tables.get("SoftwareList")
            if tbl_sw:
                tbl_sw.ref = f"A7:AH{max(8, last_sw_row)}"

            # Expand data validations if last_sw_row > 30
            expand_validation_ranges(ws_sw, last_sw_row)

        return self.save_workbook(wb, output_path, allowed_boundary=allowed_boundary)


# POA&M rule evaluation and finding derivation is decoupled into poam_rules.py
# derive_poam_findings is imported above for backward compatibility.


class POAMHydrator(BaseExcelHydrator):
    """Hydrates Plan of Action & Milestones (POAM_Export_Template.xlsm)."""

    def __init__(self, template_path: str) -> None:
        """Initializes the POAMHydrator with a template workbook path.

        Args:
            template_path: File system path to the POAM_Export_Template.xlsm template.
        """
        super().__init__(template_path)

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
        so_info = roles_info.get("system_owner", {})
        isso_info = roles_info.get("isso", {})

        sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
        sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
        org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
        eff_date = sys_info.get("effective_date") or datetime.now().strftime("%Y-%m-%d")

        try:
            base_dt = datetime.strptime(eff_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            base_dt = datetime.now()
        omb_year = str(base_dt.year)

        so_name = so_info.get("name") or "[CONFIG_REQUIRED: System Owner Name]"
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
            safe_set_cell_value(ws, "P2", f"OMB-{sys_abbr}-{omb_year}" if sys_info.get("system_abbreviation") else "[CONFIG_REQUIRED: OMB Number]")
            safe_set_cell_value(ws, "D3", "Compliance Automation Engine")
            safe_set_cell_value(ws, "D4", org)
            safe_set_cell_value(ws, "M4", isso_name)
            safe_set_cell_value(ws, "D5", sys_name)
            safe_set_cell_value(ws, "M5", isso_phone)
            safe_set_cell_value(ws, "P5", sys_info.get("funding_source") or "[CONFIG_REQUIRED: Funding Source]")
            ditpr_id = sys_info.get("ditpr_id") or sys_info.get("ditpr_don_id") or sys_info.get("ditpr_emass_id") or (f"DITPR-{sys_abbr}-001" if sys_info.get("system_abbreviation") else "[CONFIG_REQUIRED: DITPR ID]")
            safe_set_cell_value(ws, "D6", ditpr_id)
            safe_set_cell_value(ws, "M6", isso_email)

            # derive_poam_findings consumes inventory["poam_items"] as *raw* user
            # input and returns normalized findings. Skipping the call when that key
            # is present would push unnormalized config straight into the workbook.
            poam_items = derive_poam_findings(inventory, eff_date)
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
                    "Funded", "40", "0", "None", "N/A", "Cost-Base", "$0.00", "$0.00", "None", "N/A"
                ]

                for c_offset, val in enumerate(row_vals):
                    target_c = 1 + c_offset
                    cell = ws.cell(row=target_r, column=target_c)
                    cell.value = clean_cell_value(val)
                    if target_r > 8:
                        poam_style.apply(cell, target_c)

        return self.save_workbook(wb, output_path, allowed_boundary=allowed_boundary)


class PPSMHydrator(BaseExcelHydrator):
    """Hydrates Ports, Protocols, and Services Matrix (PPSMBoundariesInformationExport_Template.xlsm)."""

    def __init__(self, template_path: str) -> None:
        """Initializes the PPSMHydrator with a template workbook path.

        Args:
            template_path: File system path to the PPSMBoundariesInformationExport_Template.xlsm template.
        """
        super().__init__(template_path)

    def hydrate(self, inventory: Dict[str, Any], output_path: str, allowed_boundary: Optional[str] = None) -> str:
        """Hydrates the Ports, Protocols, and Services Matrix workbook.

        Populates system metadata and generates inbound/outbound communication
        rules based on enabled GCP APIs, Terraform firewalls, and application ports.

        Args:
            inventory: Dictionary containing network architecture and application ports.
            output_path: Target path for the hydrated .xlsm workbook.

        Returns:
            The output path to the generated workbook.

        Raises:
            FileNotFoundError: If the template file does not exist.
        """
        wb = self.load_workbook()

        sys_info = inventory.get("system_information", {})
        net_info = inventory.get("network_architecture", {})
        infra_info = inventory.get("infrastructure_components", {})
        app_info = inventory.get("application_components", {})
        roles_info = inventory.get("personnel_roles", {})

        so_info = roles_info.get("system_owner", {})
        isso_info = roles_info.get("isso", {})

        sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
        sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
        org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
        location = sys_info.get("primary_location") or "[CONFIG_REQUIRED: Primary Location]"
        eff_date = sys_info.get("effective_date") or datetime.now().strftime("%Y-%m-%d")

        so_name = so_info.get("name") or "[CONFIG_REQUIRED: System Owner Name]"
        isso_name = isso_info.get("name") or "[CONFIG_REQUIRED: ISSO Name]"
        isso_email = isso_info.get("email") or "[CONFIG_REQUIRED: ISSO Email]"
        isso_phone = isso_info.get("phone") or "[CONFIG_REQUIRED: ISSO Phone]"

        if "PPSM" in wb.sheetnames:
            ws = wb["PPSM"]

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
            emass_id = sys_info.get("emass_system_id") or (f"EMASS-{sys_abbr}-001" if sys_info.get("system_abbreviation") else "[CONFIG_REQUIRED: eMASS System ID]")
            safe_set_cell_value(ws, "C6", emass_id)
            safe_set_cell_value(ws, "F6", isso_email)
            ditpr_id = sys_info.get("ditpr_id") or sys_info.get("ditpr_don_id") or sys_info.get("ditpr_emass_id") or (f"DITPR-{sys_abbr}-001" if sys_info.get("system_abbreviation") else "[CONFIG_REQUIRED: DITPR ID]")
            safe_set_cell_value(ws, "C7", ditpr_id)
            safe_set_cell_value(ws, "F7", sys_info.get("version") or "1.0.0")

            cloud_provider = (
                sys_info.get("cloud_provider")
                or inventory.get("cloud_provider")
                or "Google Cloud Platform"
            )
            csp_abbr = (
                sys_info.get("cloud_service_provider_abbr")
                or "GCP"
            )
            dest_internal_domain = f"*.{csp_abbr.lower()}.internal"
            workload_fqdn = f"*.{sys_abbr.lower()}.internal" if sys_info.get("system_abbreviation") else dest_internal_domain

            raw_subnets = net_info.get("subnets_cidrs", [])
            clean_subnets = extract_clean_subnets(raw_subnets)
            subnet_ip_str = ", ".join(clean_subnets) if clean_subnets else "Dynamic Internal IP"

            ppsm_rows = []
            p_id = 1

            # 1. Cloud API Endpoints
            custom_svcs = inventory.get("custom_services", {})
            seen_services = set()
            for svc in infra_info.get("services_enabled", []):
                svc_clean = str(svc).lower().strip()
                if not svc_clean or svc_clean in seen_services:
                    continue
                seen_services.add(svc_clean)
                category, sw_name, purpose = resolve_gcp_service(svc, custom_svcs)

                ppsm_rows.append([
                    p_id, "Least Function", sw_name, "HTTPS", category, "443",
                    "1. Ext to DoD GW (In)", f"{csp_abbr} Workload Nodes / Compute Instances",
                    f"{cloud_provider} ({location})", subnet_ip_str, workload_fqdn,
                    "Off-Premise Cloud Service (non-DoD Network)", f"{sw_name} API Endpoint",
                    f"{cloud_provider} ({location})", "Private Service Connect VIP 199.36.153.4/30",
                    svc_clean, "Off-Premise Cloud Service (DoD Network via DISA CAP)",
                    "Yes", "Cloud Layer 3 VPN", purpose
                ])
                p_id += 1

            # 2. Terraform Firewall Rules
            seen_firewalls = set()
            for fw in net_info.get("firewall_rules", []):
                fw_name = clean_interpolated_string(fw.get("name", "fw-rule"))
                protocol = str(fw.get("protocol", "TCP")).upper()
                ports = str(fw.get("ports", "443"))
                direction = str(fw.get("direction", "INGRESS")).upper()
                dedup_key = (fw_name, protocol, ports, direction)
                if dedup_key in seen_firewalls:
                    continue
                seen_firewalls.add(dedup_key)

                fw_source_ip = (
                    "35.235.240.0/20 (IAP IP Range)"
                    if "iap" in fw_name.lower()
                    else (subnet_ip_str if clean_subnets else "Configured Source CIDR")
                )
                fw_dest_ip = subnet_ip_str if clean_subnets else "Internal Subnet IP"

                ppsm_rows.append([
                    p_id, "Least Function", f"Terraform Firewall: {fw_name}", protocol,
                    "VPC Ingress/Egress Traffic Filter", str(ports), "11. Enclave GW to Enclave (In)",
                    "VPC Network Workload", f"{cloud_provider} ({location})", fw_source_ip,
                    dest_internal_domain, "DoD Enclave (DoD Network)", "Target Instance / Service",
                    f"{cloud_provider} ({location})", fw_dest_ip, dest_internal_domain,
                    "DoD Enclave (DoD Network)", "Yes", "Cloud Layer 3 VPN",
                    f"Terraform defined {direction} rule {fw_name} allowing {protocol}:{ports}"
                ])
                p_id += 1

            # 3. Discovered Application and Container Ingress Ports
            port_list = app_info.get("exposed_ports", []) or net_info.get("application_ports", [])
            seen_ports = set()
            for app_port in port_list:
                port_num = str(app_port.get("port", "8080")).strip()
                protocol = str(app_port.get("protocol", "TCP")).upper().strip()
                svc_name = app_port.get("service_name", "Application Ingress")
                source = app_port.get("source", "Application Ingress")
                file_src = app_port.get("file", "Application Config")
                dedup_key = (port_num, protocol, svc_name)
                if dedup_key in seen_ports:
                    continue
                seen_ports.add(dedup_key)

                dest_fqdn = (
                    f"*.{sys_abbr.lower()}.internal"
                    if sys_info.get("system_abbreviation")
                    else "*.workload.internal"
                )
                ppsm_rows.append([
                    p_id, "Least Function", f"App Port: {svc_name}", protocol,
                    "Application Workload Traffic", str(port_num), "11. Enclave GW to Enclave (In)",
                    "Internal VPC Workload Client", f"{cloud_provider} ({location})",
                    subnet_ip_str if clean_subnets else "Configured Subnet CIDR",
                    dest_fqdn, "DoD Enclave (DoD Network)", "Container / Application Endpoint",
                    f"{cloud_provider} ({location})",
                    subnet_ip_str if clean_subnets else "Internal Service IP", dest_fqdn,
                    "DoD Enclave (DoD Network)", "Yes", "Cloud Layer 3 VPN",
                    f"Application ingress traffic on port {port_num}/{protocol} ({source} in {file_src})"
                ])
                p_id += 1

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

            # Clear unused rows within the original template table range (A8:T21)
            if last_ppsm_row < 21:
                for r in range(last_ppsm_row + 1, 22):
                    for c in range(1, 21):
                        ws.cell(row=r, column=c).value = None

            # Update Excel Table definition range and autoFilter
            tbl_ppsm = ws.tables.get("PPSMList")
            if tbl_ppsm:
                tbl_ppsm.ref = f"A8:T{max(9, last_ppsm_row)}"
                if tbl_ppsm.autoFilter:
                    tbl_ppsm.autoFilter.ref = tbl_ppsm.ref

            # Expand data validations if last_ppsm_row > 33
            expand_validation_ranges(ws, last_ppsm_row)

        return self.save_workbook(wb, output_path, allowed_boundary=allowed_boundary)


class SCTMHydrator(BaseExcelHydrator):
    """Hydrates Security Control Traceability Matrix (ControlInfoExport_Template.xlsm) in-place."""

    def __init__(self, template_path: str) -> None:
        """Initializes the SCTMHydrator with a template workbook path.

        Args:
            template_path: File system path to the ControlInfoExport_Template.xlsm template.
        """
        super().__init__(template_path)

    def hydrate(self, inventory: Dict[str, Any], output_path: str, allowed_boundary: Optional[str] = None) -> str:
        """Hydrates the Security Control Traceability Matrix workbook in-place.

        Preserves existing control catalog rows and populates implementation status,
        control designation, common provider, test methods, estimated completion dates,
        SLCM attributes/comments, and risk assessment parameters.

        Args:
            inventory: Dictionary containing system metadata and impact level.
            output_path: Target path for the hydrated .xlsm workbook.

        Returns:
            The output path to the generated workbook.

        Raises:
            FileNotFoundError: If the template file does not exist.
        """
        wb = self.load_workbook()
        inventory = scrub_sensitive_data(inventory)

        sys_info = inventory.get("system_information", {})
        sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
        # Inherited CSP authorization identifier. Hardcoding it here meant the
        # SCTM asserted a Google Cloud package for every tenancy, including
        # non-Google ones. See DEFAULT_CSP_PATO_PACKAGE_ID.
        pato_id = sys_info.get("csp_pato_package_id") or DEFAULT_CSP_PATO_PACKAGE_ID
        org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
        impact_level = str(sys_info.get("impact_level", "")).upper()
        baseline = str(sys_info.get("compliance_baseline", "")).upper()
        is_dod = any(k in impact_level or k in baseline for k in ["IL4", "IL5", "IL6", "DOD"])

        today_dt = datetime.now()

        # Date for Implemented / Inherited controls: MUST be in the past or today
        eff_date_str = sys_info.get("effective_date")
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
                past_dt = today_dt
        else:
            past_dt = today_dt
        past_date_str = past_dt.strftime("%m/%d/%Y")

        # Future date for Planned controls: MUST be strictly in the future (> today)
        target_auth_str = sys_info.get("target_authorization_date")
        future_target_dt = None
        if target_auth_str:
            try:
                t_dt = datetime.strptime(str(target_auth_str).strip(), "%Y-%m-%d")
            except (ValueError, TypeError) as err:
                logger.warning(
                    "Configured target_authorization_date %r is not a valid ISO 8601 date (%s); "
                    "falling back to staggered default milestone dates.",
                    target_auth_str,
                    err,
                )
            else:
                if t_dt > today_dt:
                    future_target_dt = t_dt

        # Staggered future milestone dates:
        # Governance/Policy (PL, PM, PS, policy milestones): 90 days out
        future_90d = (today_dt + timedelta(days=90)).strftime("%m/%d/%Y")
        # Technical Engineering controls (AC, IA, SC, etc.): 180 days out
        future_180d = (today_dt + timedelta(days=180)).strftime("%m/%d/%Y")

        # Derive live POA&M findings and index by normalized control identifier
        poam_by_control: Dict[str, Dict[str, Any]] = {}
        try:
            # Derived independently of the POA&M sheet: this hydrator uses a
            # different effective date, so a shared cache would attribute findings
            # to the wrong reporting period.
            live_poam_items = derive_poam_findings(inventory, past_date_str)
            for p_item in live_poam_items:
                c_field = str(p_item.get("control", "")).upper()
                c_matches = re.findall(r'([A-Z]{2})-0*(\d+)(?:\(0*(\d+)\))?', c_field)
                for prefix, num, enh in c_matches:
                    norm_k = f"{prefix}-{num}"
                    if enh:
                        norm_k += f"({enh})"
                    if norm_k not in poam_by_control:
                        poam_by_control[norm_k] = p_item
                    base_k = f"{prefix}-{num}"
                    if base_k not in poam_by_control:
                        poam_by_control[base_k] = p_item
        except (TypeError, ValueError, AttributeError) as err:
            logger.error("Failed to derive POA&M items for SCTM risk mapping: %s", err)

        # Load authoritative SCTM YAML catalog for control-level implementation details if available
        sctm_yaml_path = get_templates_dir() / "sctm" / "SCTM_Template.yaml"
        yaml_controls: Dict[str, Dict[str, Any]] = {}
        if sctm_yaml_path.exists():
            try:
                yaml_data = read_yaml_file(sctm_yaml_path)
                for fam_item in yaml_data.get("control_families", []):
                    for c_item in fam_item.get("controls", []):
                        cid = str(c_item.get("id", "")).upper().strip()
                        yaml_controls[cid] = c_item
            except (OSError, ValueError) as err:
                logger.warning("Optional SCTM_Template.yaml loading skipped: %s", err)

        if "Template" in wb.sheetnames:
            ws = wb["Template"]
            safe_set_cell_value(ws, "A2", f"Control Import Template: {sys_name} ({org})")

            monitoring_dashboard = (
                "CSSP SIEM / Cloud Logging Dashboard"
                if is_dod
                else "Security Command Center Dashboard"
            )

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
                family_match = re.search(r'([A-Z]{2})-\d+', ctrl_str)
                family = family_match.group(1) if family_match else "AC"

                # Normalize control identifier (e.g. '[r5] AC-02(01)' -> 'AC-2(1)')
                clean_cid = re.sub(r'\[[^\]]{0,256}\]\s*', '', ctrl_str).strip()
                norm_cid = re.sub(r'([A-Z]{2})-0*(\d+)', r'\1-\2', clean_cid)
                norm_cid = re.sub(r'\(0*(\d+)\)', r'(\1)', norm_cid)
                yaml_ctrl = yaml_controls.get(norm_cid) or yaml_controls.get(clean_cid)

                matched_poam = (
                    poam_by_control.get(norm_cid)
                    or poam_by_control.get(clean_cid)
                    or (poam_by_control.get(norm_cid.split("(")[0]) if "(" in norm_cid else None)
                )

                status = "Implemented"
                designation = "Hybrid"
                common_provider = "Component"
                test_method = "Test, Examine"
                narrative = (
                    f"Implemented across {sys_name} infrastructure using automated Terraform blueprints, "
                    f"enforcing least-privilege IAM roles, CMEK encryption, and Google Cloud Assured Workloads guardrails."
                )

                if yaml_ctrl and yaml_ctrl.get("status"):
                    y_stat = str(yaml_ctrl["status"]).lower()
                    if "inherit" in y_stat:
                        status = "Inherited"
                        designation = "Common"
                        common_provider = "DoD"
                        test_method = "Examine"
                    elif "planned" in y_stat or "manual" in y_stat:
                        status = "Planned"
                        designation = "System-Specific"
                        common_provider = ""
                        test_method = "Test, Examine"
                    else:
                        status = "Implemented"
                        designation = "Hybrid" if family in ["AU", "SI", "CA", "PL"] else "System-Specific"
                        common_provider = "Component" if designation == "Hybrid" else ""
                        test_method = "Test"
                    if yaml_ctrl.get("implementation_details"):
                        narrative = str(yaml_ctrl["implementation_details"])
                elif family in ["PE", "PS"]:
                    status = "Inherited"
                    designation = "Common"
                    common_provider = "DoD"
                    test_method = "Examine"
                    narrative = f"Inherited from Google Cloud Physical Infrastructure & Facility Security P-ATO ({pato_id})."
                elif family in ["PL", "PM"]:
                    status = "Planned"
                    designation = "System-Specific"
                    common_provider = ""
                    test_method = "Test, Examine"
                    narrative = f"Institutional cybersecurity program management and security planning procedures documented in eMASS for {sys_name}."
                elif family in ["AC", "IA", "SC"]:
                    status = "Implemented"
                    designation = "System-Specific"
                    common_provider = ""
                    test_method = "Test"
                    narrative = (
                        f"Technical controls enforced via Terraform IAM role bindings, VPC firewall policies, "
                        f"and Google Cloud KMS FIPS 140-3 CMEK cryptography."
                    )
                elif family in ["AU", "SI"]:
                    status = "Implemented"
                    designation = "Hybrid"
                    common_provider = "Component"
                    test_method = "Test, Examine"
                    if is_dod:
                        narrative = (
                            f"Audit logging ingested into Cloud Logging buckets with retention locks and exported "
                            f"via Pub/Sub to external CSSP SIEM for continuous 24/7 analysis."
                        )
                    else:
                        narrative = (
                            f"Audit logging ingested into Cloud Logging buckets with retention locks and monitored "
                            f"continuously via Security Command Center threat event detection."
                        )

                # SLCM monitoring parameters and comments
                if status == "Inherited":
                    resp_entities = "Google Cloud CSP, ISSM"
                    criticality = "Moderate"
                    frequency = "Annually"
                    method = "Examine"
                    reporting = "FedRAMP / DoD PA Continuous Monitoring Package"
                    slcm_comments = (
                        f"Inherited from Google Cloud FedRAMP High / DoD IL5 Provisional Authorization ({pato_id}). "
                        f"CSP continuous monitoring artifacts, annual 3PAO assessments, and monthly vulnerability reports reviewed and tracked in eMASS."
                    )
                elif status == "Planned":
                    resp_entities = "Cloud Platform Engineering Team, ISSM"
                    criticality = "High"
                    frequency = "Monthly"
                    method = "Test, Examine"
                    reporting = "eMASS Milestones / ISSM Oversight"
                    slcm_comments = (
                        f"Scheduled for continuous monitoring integration upon final deployment. Operational evidence and assessment artifacts "
                        f"will be tracked through monthly eMASS POA&M milestone reviews."
                    )
                elif family in ["AC", "IA"]:
                    resp_entities = "Cloud Platform Engineering Team, ISSM"
                    criticality = "High"
                    frequency = "Monthly"
                    method = "Automated"
                    reporting = monitoring_dashboard
                    slcm_comments = (
                        f"User identities, Workload Identity Federation (WIF), and service account permissions monitored continuously via Google Cloud IAM Recommender "
                        f"and Cloud Audit Logs. Inactive accounts disabled automatically; privileged access reviewed monthly in eMASS."
                    )
                elif family in ["AU", "SI"]:
                    resp_entities = "Cloud Platform Engineering Team, ISSM"
                    criticality = "High"
                    frequency = "Monthly"
                    method = "Automated"
                    reporting = monitoring_dashboard
                    slcm_comments = (
                        f"Audit log streams ingested with Bucket Lock retention into Cloud Logging and streamed via Pub/Sub to external CSSP SIEM for continuous 24/7 analysis. "
                        f"Automated threat detection alerts and monthly ACAS vulnerability scans tracked continuously in eMASS."
                    )
                elif family in ["SC"]:
                    resp_entities = "Cloud Platform Engineering Team, ISSM"
                    criticality = "High"
                    frequency = "Monthly"
                    method = "Automated"
                    reporting = monitoring_dashboard
                    slcm_comments = (
                        f"Hub-and-Spoke VPC boundaries, VPC Service Controls perimeters, and Cloud KMS CMEK key rotations monitored continuously via VPC Flow Logs "
                        f"and Cloud Audit Logs. Firewall changes audited against approved baseline with alerts sent to NetOps/CSSP."
                    )
                elif family in ["CM"]:
                    resp_entities = "Cloud Platform Engineering Team, ISSM"
                    criticality = "High"
                    frequency = "Monthly"
                    method = "Automated"
                    reporting = monitoring_dashboard
                    slcm_comments = (
                        f"Infrastructure as Code configurations version-controlled in Git repositories with automated CI/CD security scanning. "
                        f"Configuration drift monitored continuously via Google Cloud Asset Inventory feeds and tracked in eMASS."
                    )
                elif family in ["CP"]:
                    resp_entities = "Cloud Platform Engineering Team, ISSM"
                    criticality = "High"
                    frequency = "Semi-annually"
                    method = "Test, Examine"
                    reporting = "Disaster Recovery Testing Reports / eMASS"
                    slcm_comments = (
                        f"Multi-region dual-tier architecture with Cloud Storage multi-region replication and automated Cloud SQL backups. "
                        f"Disaster recovery failover and contingency plan simulations executed and validated annually per RTO/RPO targets."
                    )
                elif family in ["IR"]:
                    resp_entities = "Incident Response Team, ISSM, CSSP"
                    criticality = "High"
                    frequency = "Monthly"
                    method = "Semi-Automated"
                    reporting = monitoring_dashboard
                    slcm_comments = (
                        f"Tactical cloud incident response runbooks maintained for IAM, compute, KMS, network, and VPC-SC events. "
                        f"Integrated with 24/7 CSSP SOC, automated SCC alerting, and annual TTX tabletop simulation exercises."
                    )
                else:
                    resp_entities = "Cloud Platform Engineering Team, ISSM"
                    criticality = "High"
                    frequency = "Monthly"
                    method = "Automated"
                    reporting = monitoring_dashboard
                    posture_monitoring = (
                        "external CSSP continuous monitoring"
                        if is_dod
                        else "Security Command Center posture checks"
                    )
                    slcm_comments = (
                        f"System-level continuous monitoring enforced through automated {sys_name} Terraform guardrails, "
                        f"monthly credentialed ACAS scans, {posture_monitoring}, and continuous eMASS milestone tracking."
                    )

                # Determine Estimated Completion Date per eMASS instructions:
                # - Implemented / Inherited: MUST be today or in the past (when implemented)
                # - Planned: MUST be strictly in the future (> today)
                # - Not Applicable: empty / blank (N/A Justification is required instead)
                if status == "Not Applicable":
                    ctrl_est_date = ""
                    na_justification = "Control is not applicable to the cloud-native system boundary and hosted workloads."
                elif status == "Planned":
                    na_justification = ""
                    if future_target_dt:
                        ctrl_est_date = future_target_dt.strftime("%m/%d/%Y")
                    elif family in ["PL", "PM", "PS", "SA"]:
                        ctrl_est_date = future_90d
                    else:
                        ctrl_est_date = future_180d
                else:
                    na_justification = ""
                    ctrl_est_date = past_date_str

                # Implementation Plan (IM) Columns E..L
                ws.cell(row=r, column=5).value = clean_cell_value(status)          # Implementation Status (Col E)
                ws.cell(row=r, column=6).value = clean_cell_value(common_provider) # Common Control Provider (Col F)
                ws.cell(row=r, column=7).value = clean_cell_value(designation)     # Security Control Designation (Col G)
                ws.cell(row=r, column=8).value = clean_cell_value(test_method)     # Test Method (Col H)
                ws.cell(row=r, column=9).value = clean_cell_value(na_justification)# N/A Justification (Col I)
                ws.cell(row=r, column=10).value = clean_cell_value(ctrl_est_date)  # Estimated Completion Date (Col J - REQUIRED)
                ws.cell(row=r, column=11).value = clean_cell_value(narrative)      # Implementation Narrative (Col K)
                ws.cell(row=r, column=12).value = clean_cell_value(resp_entities)  # Responsible Entities (Col L - REQUIRED)

                # System-Level Continuous Monitoring (SLCM) Columns N..S
                ws.cell(row=r, column=14).value = clean_cell_value(criticality)    # Criticality (Col N - REQUIRED)
                ws.cell(row=r, column=15).value = clean_cell_value(frequency)      # Frequency (Col O - REQUIRED)
                ws.cell(row=r, column=16).value = clean_cell_value(method)         # Method (Col P - REQUIRED)
                ws.cell(row=r, column=17).value = clean_cell_value(reporting)      # Reporting (Col Q - REQUIRED)
                ws.cell(row=r, column=18).value = clean_cell_value("eMASS Continuous Monitoring")    # Tracking (Col R - REQUIRED)
                ws.cell(row=r, column=19).value = clean_cell_value(slcm_comments)  # SLCM Comments (Col S - REQUIRED)

                # Risk Assessment (RA) Columns U..AC synchronized with live POA&M findings
                if matched_poam:
                    poam_sev = matched_poam.get("severity") or "Moderate"
                    poam_threat = matched_poam.get("threat") or "Moderate"
                    poam_like = matched_poam.get("likelihood") or "Moderate"
                    poam_imp = matched_poam.get("impact") or "Moderate"
                    poam_res = matched_poam.get("residual") or "Low"
                    poam_desc = (
                        matched_poam.get("weakness_description")
                        or matched_poam.get("desc")
                        or matched_poam.get("title")
                        or f"Open architectural finding {matched_poam.get('item_id', '')} tracked in POA&M."
                    )
                    poam_mit = (
                        matched_poam.get("milestone_desc")
                        or "Automated compensating controls and Terraform policy enforcement."
                    )
                    poam_imp_desc = (
                        matched_poam.get("impact_description")
                        or f"Potential mission impact associated with {matched_poam.get('item_id', 'finding')}; compensating guardrails active."
                    )
                    poam_rec = (
                        matched_poam.get("recommendations")
                        or (f"Remediate via milestone {matched_poam.get('milestone_id')}: {matched_poam.get('milestone_desc')}" if matched_poam.get("milestone_id") else "Maintain continuous monitoring and remediation schedule.")
                    )

                    ws.cell(row=r, column=21).value = clean_cell_value(poam_sev)
                    ws.cell(row=r, column=22).value = clean_cell_value(poam_threat)
                    ws.cell(row=r, column=23).value = clean_cell_value(poam_like)
                    ws.cell(row=r, column=24).value = clean_cell_value(poam_imp)
                    ws.cell(row=r, column=25).value = clean_cell_value(poam_res)
                    ws.cell(row=r, column=26).value = clean_cell_value(poam_desc)
                    ws.cell(row=r, column=27).value = clean_cell_value(poam_mit)
                    ws.cell(row=r, column=28).value = clean_cell_value(poam_imp_desc)
                    ws.cell(row=r, column=29).value = clean_cell_value(poam_rec)
                else:
                    ws.cell(row=r, column=21).value = clean_cell_value("Low")                            # Severity (Col U)
                    ws.cell(row=r, column=22).value = clean_cell_value("Low")                            # Relevance of Threat (Col V)
                    ws.cell(row=r, column=23).value = clean_cell_value("Low")                            # Likelihood (Col W)
                    ws.cell(row=r, column=24).value = clean_cell_value("Low")                            # Impact (Col X)
                    ws.cell(row=r, column=25).value = clean_cell_value("Low")                            # Residual Risk Level (Col Y)
                    ws.cell(row=r, column=26).value = clean_cell_value(                               # Vulnerability Summary (Col Z)
                        "No open high or critical vulnerabilities identified in baseline IaC architecture."
                    )
                    ws.cell(row=r, column=27).value = clean_cell_value(                               # Mitigations (Col AA)
                        "Automated Terraform guardrails, VPC Service Controls, and least-privilege IAM roles."
                    )
                    ws.cell(row=r, column=28).value = clean_cell_value(                               # Impact Description (Col AB)
                        "Minimal operational impact under baseline zero-trust configuration."
                    )
                    ws.cell(row=r, column=29).value = clean_cell_value(                               # Recommendations (Col AC)
                        "Maintain continuous automated monitoring via SCC and monthly ACAS scans."
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
        hydrator = HWSWHydrator(str(hwsw_tpl))
        results["hwsw"] = hydrator.hydrate(inventory, str(hwsw_out))
    else:
        logger.warning("HWSW template not found at %s", hwsw_tpl)

    # 2. POAM
    poam_tpl = templates_dir / "poam" / "POAM_Export_Template.xlsm"
    if poam_tpl.exists():
        poam_folder = ensure_directory(out_dir / "POAM")
        poam_out = ensure_path_within_boundary(poam_folder / "Plan_of_Action_and_Milestones.xlsm", out_dir)
        hydrator = POAMHydrator(str(poam_tpl))
        results["poam"] = hydrator.hydrate(inventory, str(poam_out))
    else:
        logger.warning("POAM template not found at %s", poam_tpl)

    # 3. PPSM
    ppsm_tpl = templates_dir / "ppsm" / "PPSMBoundariesInformationExport_Template.xlsm"
    if ppsm_tpl.exists():
        ppsm_folder = ensure_directory(out_dir / "PPSM")
        ppsm_out = ensure_path_within_boundary(ppsm_folder / "PPSM_Ports_Protocols_Services.xlsm", out_dir)
        hydrator = PPSMHydrator(str(ppsm_tpl))
        results["ppsm"] = hydrator.hydrate(inventory, str(ppsm_out))
    else:
        logger.warning("PPSM template not found at %s", ppsm_tpl)

    # 4. SCTM
    sctm_tpl = templates_dir / "sctm" / "ControlInfoExport_Template.xlsm"
    if sctm_tpl.exists():
        sctm_folder = ensure_directory(out_dir / "SCTM")
        sctm_out = ensure_path_within_boundary(sctm_folder / "SCTM_Burndown_Matrix.xlsm", out_dir)
        hydrator = SCTMHydrator(str(sctm_tpl))
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
