#!/usr/bin/env python3
"""Modular Export Strategies for Compliance Documents and Structured Data.

This module implements the Strategy pattern for the dual-format output generation
pipeline. It decouples document and matrix rendering from the master orchestrator,
allowing new output formats (e.g. HTML, PDF, JSON) to be introduced by implementing
a strategy interface without modifying core generation workflows.
"""

from abc import ABC, abstractmethod
import functools
import logging
try:
    from . import audit_log
except (ImportError, ValueError):
    import audit_log
from pathlib import Path
import types
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from .file_helpers import (
        clean_cell_value,
        ensure_directory,
        ensure_path_within_boundary,
        get_templates_dir,
        read_text_file,
        resolve_path,
        write_text_file,
    )
except (ImportError, ValueError):
    from file_helpers import (
        clean_cell_value,
        ensure_directory,
        ensure_path_within_boundary,
        get_templates_dir,
        read_text_file,
        resolve_path,
        write_text_file,
    )

logger = logging.getLogger(__name__)


def sanitize_tabular_cell(val: Any) -> Any:
    """Sanitizes tabular and spreadsheet cell values against formula injection (CWE-1236).

    Prepends a single quote to strings starting with formula execution triggers
    (=, +, -, @, |, %, \t, \r, etc.) unless representing a valid numeric literal.

    Args:
        val: Raw cell value.

    Returns:
        Sanitized value safe against formula injection.
    """
    return clean_cell_value(val)


class BasePolicyExporter(ABC):
    """Abstract strategy for exporting policy and narrative documents."""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Format identifier string for this policy exporter.

        Returns:
            String format identifier (e.g. 'markdown', 'docx').
        """
        pass

    @abstractmethod
    def export_document(
        self,
        markdown_content: str,
        output_base_path: Union[str, Path],
        inventory: Dict[str, Any],
        allowed_boundary: Optional[Union[str, Path]] = None,
    ) -> Path:
        """Exports a document from Markdown content to the target format.

        Args:
            markdown_content: The hydrated Markdown content of the document.
            output_base_path: Target path without extension or with source extension.
            inventory: System inventory dictionary with metadata and roles.
            allowed_boundary: Optional root directory boundary to confine file writes.

        Returns:
            Path to the generated deliverable.
        """
        pass


class MarkdownPolicyExporter(BasePolicyExporter):
    """Exports policy and narrative documents as standard Markdown (.md) files."""

    @property
    def format_name(self) -> str:
        """Format identifier string for markdown exporter.

        Returns:
            String format identifier 'markdown'.
        """
        return "markdown"

    def export_document(
        self,
        markdown_content: str,
        output_base_path: Union[str, Path],
        inventory: Dict[str, Any],
        allowed_boundary: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> Path:
        """Writes hydrated Markdown content directly to a .md file.

        Args:
            markdown_content: The hydrated Markdown content.
            output_base_path: Target path without extension or with .md extension.
            inventory: System inventory dictionary (unused in markdown export).
            allowed_boundary: Optional root directory boundary to confine file writes.
            **kwargs: Additional keyword arguments.

        Returns:
            Path to the saved Markdown file.
        """
        target = resolve_path(output_base_path)
        if target.suffix != ".md":
            target = target.with_suffix(".md")
        return write_text_file(target, markdown_content, allowed_boundary=allowed_boundary)


class DocxPolicyExporter(BasePolicyExporter):
    """Exports policy documents as styled OpenXML Microsoft Word (.docx) documents."""

    def __init__(self) -> None:
        """Initializes the DOCX exporter and ensures docx_generator is available."""
        self._docx_generator = None
        self._ensure_generator()

    def _ensure_generator(self) -> Any:
        """Dynamically imports or re-imports docx_generator if not yet loaded.

        Returns:
            The loaded docx_generator module, or None if unavailable.
        """
        if self._docx_generator is None:
            try:
                from . import docx_generator
                self._docx_generator = docx_generator
            except (ImportError, ValueError):
                try:
                    import docx_generator
                    self._docx_generator = docx_generator
                except ImportError:
                    self._docx_generator = None
        return self._docx_generator

    @property
    def format_name(self) -> str:
        """Format identifier string for docx exporter.

        Returns:
            String format identifier 'docx'.
        """
        return "docx"

    def export_document(
        self,
        markdown_content: str,
        output_base_path: Union[str, Path],
        inventory: Dict[str, Any],
        allowed_boundary: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> Path:
        """Converts Markdown content into a styled .docx document.

        Args:
            markdown_content: The hydrated Markdown content.
            output_base_path: Target path without extension or with .docx extension.
            inventory: System inventory dictionary providing metadata for cover page.
            allowed_boundary: Optional root directory boundary to confine file writes.
            **kwargs: Additional keyword arguments.

        Returns:
            Path to the generated .docx file.

        Raises:
            RuntimeError: If docx_generator is unavailable.
        """
        target = resolve_path(output_base_path)
        if target.suffix != ".docx":
            target = target.with_suffix(".docx")

        if allowed_boundary is not None:
            ensure_path_within_boundary(target, allowed_boundary)

        generator = self._ensure_generator()
        if not generator:
            raise RuntimeError("docx_generator module is not available for DOCX export")

        target.parent.mkdir(parents=True, exist_ok=True)
        generator.convert_markdown_to_docx(markdown_content, str(target), inventory)
        return target


class BaseDataExporter(ABC):
    """Abstract strategy for exporting structured compliance matrices."""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Format identifier string for this data exporter.

        Returns:
            String format identifier (e.g. 'yaml', 'excel').
        """
        pass

    @abstractmethod
    def export_all_matrices(
        self,
        target_dir: Union[str, Path],
        inventory: Dict[str, Any],
        doc_versions: Dict[str, Any],
        generators: Dict[str, Callable[..., Any]],
    ) -> List[Path]:
        """Exports all structured compliance matrices for the package.

        Args:
            target_dir: Root foundation directory containing ato_artifacts.
            inventory: System inventory dictionary.
            doc_versions: Version dictionary for individual documents.
            generators: Callback dictionary for generating domain-specific matrices.

        Returns:
            List of Path objects for all generated matrix deliverables.
        """
        pass


class YamlDataExporter(BaseDataExporter):
    """Exports structured compliance matrices as YAML deliverables."""

    @property
    def format_name(self) -> str:
        """Format identifier string for yaml data exporter.

        Returns:
            String format identifier 'yaml'.
        """
        return "yaml"

    def _export_template_matrix(
        self,
        template_file: Path,
        output_folder: Path,
        output_filename: str,
        version_key: str,
        out_dir: Path,
        inventory: Dict[str, Any],
        doc_versions: Dict[str, Any],
        pop_fn: Optional[Callable[..., Any]],
    ) -> Optional[Path]:
        """Helper to hydrate and write a YAML matrix from a template file (DRY).

        Args:
            template_file: Path to authoritative YAML template.
            output_folder: Target directory to contain deliverable.
            output_filename: Deliverable filename.
            version_key: Document version lookup key.
            out_dir: Master ato_artifacts root directory.
            inventory: System inventory dictionary.
            doc_versions: Version dictionary.
            pop_fn: Placeholder population function.

        Returns:
            Path of written deliverable if template exists, else None.
        """
        if not template_file.exists() or not pop_fn:
            return None
        folder = ensure_directory(output_folder)
        raw_text = read_text_file(template_file)
        version = doc_versions.get(version_key, "1.0.0")
        # `target_format="yaml"` is required, not optional: in Markdown mode the
        # template engine renders unresolved values as HTML <mark> badges, whose
        # embedded double quotes terminate the surrounding YAML scalar and leave the
        # deliverable unparseable. This was previously called with a non-existent
        # `target_detail` kwarg whose TypeError was caught and retried without any
        # format at all, silently selecting the Markdown default.
        populated = pop_fn(raw_text, inventory, version, target_format="yaml")
        out_path = ensure_path_within_boundary(folder / output_filename, out_dir)
        result_path = write_text_file(out_path, populated, allowed_boundary=out_dir)
        if result_path:
            audit_logger = audit_log.get_audit_logger()
            audit_logger.emit(
                audit_log.AuditEvent.ARTIFACT_GENERATED,
                audit_log.AuditOutcome.SUCCESS,
                subject="export_strategies.yaml",
                obj=str(result_path),
                detail={"format": "yaml"}
            )
        return result_path

    def export_all_matrices(
        self,
        target_dir: Union[str, Path],
        inventory: Dict[str, Any],
        doc_versions: Dict[str, Any],
        generators: Dict[str, Callable[..., Any]],
    ) -> List[Path]:
        """Exports HW/SW, PPSM, SCTM, POA&M, and FIPS matrices as structured YAML files.

        Args:
            target_dir: Target foundation directory.
            inventory: System inventory dictionary.
            doc_versions: Document versions mapping.
            generators: Mapping of matrix generation callback functions.

        Returns:
            List of generated YAML file paths.
        """
        out_dir = resolve_path(target_dir) / "ato_artifacts"
        templates_dir = get_templates_dir()
        generated_paths: List[Path] = []
        pop_fn = generators.get("populate_placeholders")

        # 1. HW/SW Inventory YAML
        hwsw_folder = ensure_directory(out_dir / "HW_SW_Inventory")
        hwsw_version = doc_versions.get("hwsw_inventory", "1.0.0")
        hwsw_gen = generators.get("hwsw")
        if hwsw_gen:
            hwsw_content = hwsw_gen(inventory, hwsw_version)
            hwsw_out = ensure_path_within_boundary(hwsw_folder / "Hardware_Software_Inventory.yaml", out_dir)
            generated_paths.append(write_text_file(hwsw_out, hwsw_content, allowed_boundary=out_dir))

        # 2. PPSM Ports & Protocols YAML
        ppsm_folder = ensure_directory(out_dir / "PPSM")
        ppsm_version = doc_versions.get("ppsm", "1.0.0")
        ppsm_gen = generators.get("ppsm")
        if ppsm_gen:
            ppsm_content = ppsm_gen(inventory, ppsm_version)
            ppsm_out = ensure_path_within_boundary(ppsm_folder / "PPSM_Ports_Protocols_Services.yaml", out_dir)
            generated_paths.append(write_text_file(ppsm_out, ppsm_content, allowed_boundary=out_dir))

        # 3. SCTM Burndown Matrix YAML
        sctm_res = self._export_template_matrix(
            template_file=templates_dir / "sctm" / "SCTM_Template.yaml",
            output_folder=out_dir / "SCTM",
            output_filename="SCTM_Burndown_Matrix.yaml",
            version_key="sctm",
            out_dir=out_dir,
            inventory=inventory,
            doc_versions=doc_versions,
            pop_fn=pop_fn,
        )
        if sctm_res:
            generated_paths.append(sctm_res)

        # 4. POA&M Weakness Matrix YAML
        poam_folder = ensure_directory(out_dir / "POAM")
        poam_version = doc_versions.get("poam", "1.0.0")
        poam_gen = generators.get("poam")
        if poam_gen:
            poam_content = poam_gen(inventory, poam_version)
            poam_out = ensure_path_within_boundary(poam_folder / "Plan_of_Action_and_Milestones.yaml", out_dir)
            generated_paths.append(write_text_file(poam_out, poam_content, allowed_boundary=out_dir))

        # 5. FIPS Cryptographic Matrix YAML
        fips_res = self._export_template_matrix(
            template_file=templates_dir / "fips" / "FIPS_Cryptographic_Matrix_Template.yaml",
            output_folder=out_dir / "FIPS_Cryptography",
            output_filename="FIPS_Cryptographic_Matrix.yaml",
            version_key="fips_matrix",
            out_dir=out_dir,
            inventory=inventory,
            doc_versions=doc_versions,
            pop_fn=pop_fn,
        )
        if fips_res:
            generated_paths.append(fips_res)

        return generated_paths


class ExcelDataExporter(BaseDataExporter):
    """Exports structured compliance matrices into macro-enabled Excel (.xlsm) workbooks."""

    def __init__(self) -> None:
        """Initializes the Excel hydrator strategy."""
        self._excel_hydrator = None
        self._ensure_hydrator()

    def _ensure_hydrator(self) -> Any:
        """Dynamically imports or re-imports excel_hydrator if not yet loaded.

        Returns:
            The loaded excel_hydrator module, or None if unavailable.
        """
        if self._excel_hydrator is None:
            try:
                from . import excel_hydrator
                self._excel_hydrator = excel_hydrator
            except (ImportError, ValueError):
                try:
                    import excel_hydrator
                    self._excel_hydrator = excel_hydrator
                except ImportError:
                    self._excel_hydrator = None
        return self._excel_hydrator

    @property
    def format_name(self) -> str:
        """Format identifier string for excel data exporter.

        Returns:
            String format identifier 'excel'.
        """
        return "excel"

    def export_all_matrices(
        self,
        target_dir: Union[str, Path],
        inventory: Dict[str, Any],
        doc_versions: Dict[str, Any],
        generators: Dict[str, Callable[..., Any]],
    ) -> List[Path]:
        """Hydrates HWSW, POAM, PPSM, and SCTM Excel workbooks from authoritative templates.

        Args:
            target_dir: Foundation target directory.
            inventory: System inventory dictionary.
            doc_versions: Document version mapping (unused in Excel).
            generators: Callback dictionary (unused in Excel).

        Returns:
            List of generated .xlsm file paths.
        """
        hydrator = self._ensure_hydrator()
        if not hydrator:
            logger.warning("excel_hydrator is not available; skipping Excel export")
            return []

        logger.info("Hydrating Excel Workbooks (.xlsm) from authoritative templates...")
        xl_results = hydrator.hydrate_all_excel_templates(str(target_dir), inventory)
        generated: List[Path] = []
        for _, path_str in xl_results.items():
            p = resolve_path(path_str)
            generated.append(p)
            logger.info("  ✓ Hydrated Excel: %s", p.name)

        return generated


class OscalDataExporter(BaseDataExporter):
    """Exports machine-readable NIST OSCAL deliverables (SSP and Component Definitions)."""

    def __init__(self, oscal_format: str = "both", oscal_version: Optional[str] = None) -> None:
        """Initializes OSCAL exporter with format and version preference."""
        self._oscal_format = oscal_format
        self._oscal_version = oscal_version
        self._oscal_generator = None
        self._ensure_generator()

    def _ensure_generator(self) -> Any:
        """Dynamically imports oscal_generator if not yet loaded."""
        if self._oscal_generator is None:
            try:
                from . import oscal_generator
                self._oscal_generator = oscal_generator
            except (ImportError, ValueError):
                try:
                    import oscal_generator
                    self._oscal_generator = oscal_generator
                except ImportError:
                    self._oscal_generator = None
        return self._oscal_generator

    @property
    def format_name(self) -> str:
        """Format identifier string for oscal data exporter."""
        return "oscal"

    def export_all_matrices(
        self,
        target_dir: Union[str, Path],
        inventory: Dict[str, Any],
        doc_versions: Dict[str, Any],
        generators: Dict[str, Callable[..., Any]],
    ) -> List[Path]:
        """Exports NIST OSCAL SSP and Component Definition deliverables.

        Args:
            target_dir: Base target workspace directory.
            inventory: System inventory dictionary.
            doc_versions: Document versions mapping.
            generators: Callback dictionary (unused in OSCAL).

        Returns:
            List of generated OSCAL file Path objects.
        """
        gen = self._ensure_generator()
        if not gen:
            logger.warning("oscal_generator is not available; skipping OSCAL export")
            return []

        ssp_version = doc_versions.get("ssp", "1.0.0")
        target_oscal_ver = (
            self._oscal_version
            or inventory.get("export_preferences", {}).get("oscal_version")
            or getattr(gen, "DEFAULT_OSCAL_VERSION", "1.2.3")
        )
        logger.info("Exporting NIST OSCAL %s deliverables (%s)...", target_oscal_ver, self._oscal_format)
        return gen.export_oscal_artifacts(
            target_dir,
            inventory,
            doc_version=ssp_version,
            oscal_format=self._oscal_format,
            oscal_version=target_oscal_ver,
        )


class dualmethod:
    """Standard decorator enabling methods to be invoked on either an instance or class.

    When invoked on an instance, executes with instance scope (dependency injection).
    When invoked on a class, delegates to the process-wide default registry instance.
    Uses standard types.MethodType and functools.update_wrapper for robust Python semantics.
    """

    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func
        functools.update_wrapper(self, func)

    def __get__(self, instance: Any, owner: Any) -> Any:
        target = instance if instance is not None else owner._get_default_instance()
        return types.MethodType(self.func, target)


# Backward-compatible alias for existing references
class_or_instance_method = dualmethod


class ExporterRegistry:
    """Registry maintaining active export strategies for policies and structured data.

    Supports instance-based dependency injection to ensure thread-safety, isolation
    in parallel execution, and clean test fixtures without global state pollution.
    """

    _default_registry_instance: Optional["ExporterRegistry"] = None

    def __init__(
        self,
        policy_exporters: Optional[Dict[str, BasePolicyExporter]] = None,
        data_exporters: Optional[Dict[str, BaseDataExporter]] = None,
        load_defaults: bool = True,
    ) -> None:
        """Initializes an instance-based exporter registry.

        Args:
            policy_exporters: Optional initial mapping of format names to BasePolicyExporter.
            data_exporters: Optional initial mapping of format names to BaseDataExporter.
            load_defaults: Whether to populate default standard exporters.
        """
        self._policy_exporters: Dict[str, BasePolicyExporter] = {}
        self._data_exporters: Dict[str, BaseDataExporter] = {}
        if load_defaults:
            self.reset_defaults()
        if policy_exporters:
            for name, exporter in policy_exporters.items():
                self.register_policy_exporter(name, exporter)
        if data_exporters:
            for name, exporter in data_exporters.items():
                self.register_data_exporter(name, exporter)

    @classmethod
    def _get_default_instance(cls) -> "ExporterRegistry":
        """Returns or creates the process-wide default ExporterRegistry instance.

        Returns:
            The singleton ExporterRegistry default instance.
        """
        if cls._default_registry_instance is None:
            cls._default_registry_instance = cls()
        return cls._default_registry_instance

    @class_or_instance_method
    def register_policy_exporter(self, name: str, exporter: BasePolicyExporter) -> None:
        """Registers a policy document exporter strategy.

        Args:
            name: Case-insensitive format name (e.g. 'markdown', 'docx', 'html').
            exporter: Instance of BasePolicyExporter.
        """
        self._policy_exporters[name.lower()] = exporter

    @class_or_instance_method
    def register_data_exporter(self, name: str, exporter: BaseDataExporter) -> None:
        """Registers a structured data exporter strategy.

        Args:
            name: Case-insensitive format name (e.g. 'yaml', 'excel', 'json').
            exporter: Instance of BaseDataExporter.
        """
        self._data_exporters[name.lower()] = exporter

    @class_or_instance_method
    def get_registered_policy_exporters(self) -> Dict[str, BasePolicyExporter]:
        """Returns a defensive copy of all registered policy exporters.

        Returns:
            Dictionary mapping format names to BasePolicyExporter instances.
        """
        return dict(self._policy_exporters)

    @class_or_instance_method
    def get_registered_data_exporters(self) -> Dict[str, BaseDataExporter]:
        """Returns a defensive copy of all registered data exporters.

        Returns:
            Dictionary mapping format names to BaseDataExporter instances.
        """
        return dict(self._data_exporters)

    @class_or_instance_method
    def clear(self) -> None:
        """Clears all registered policy and data exporters."""
        self._policy_exporters.clear()
        self._data_exporters.clear()

    @class_or_instance_method
    def reset_defaults(self) -> None:
        """Resets registry to the default standard exporters."""
        self.clear()
        self.register_policy_exporter("markdown", MarkdownPolicyExporter())
        self.register_policy_exporter("docx", DocxPolicyExporter())
        self.register_data_exporter("yaml", YamlDataExporter())
        self.register_data_exporter("excel", ExcelDataExporter())
        self.register_data_exporter("oscal", OscalDataExporter())

    @class_or_instance_method
    def get_policy_exporters(self, format_pref: str) -> List[BasePolicyExporter]:
        """Resolves active policy exporter strategies based on format preference.

        Supports 'both', single format names, and comma-separated format lists.

        Args:
            format_pref: Format preference string ('both', 'markdown', 'docx', etc.).

        Returns:
            List of active BasePolicyExporter strategy instances.
        """
        pref = format_pref.strip().lower()
        if pref in ("both", "all"):
            exporters: List[BasePolicyExporter] = []
            if "markdown" in self._policy_exporters:
                exporters.append(self._policy_exporters["markdown"])
            if "docx" in self._policy_exporters:
                exporters.append(self._policy_exporters["docx"])
            return exporters

        if "," in pref:
            formats = [f.strip() for f in pref.split(",") if f.strip()]
            matched: List[BasePolicyExporter] = []
            for fmt in formats:
                if fmt in self._policy_exporters and self._policy_exporters[fmt] not in matched:
                    matched.append(self._policy_exporters[fmt])
            if matched:
                return matched

        if pref in self._policy_exporters:
            return [self._policy_exporters[pref]]

        logger.warning("Unrecognized policy format '%s', falling back to markdown", format_pref)
        return [self._policy_exporters.get("markdown", MarkdownPolicyExporter())]

    @class_or_instance_method
    def get_data_exporters(self, format_pref: str) -> List[BaseDataExporter]:
        """Resolves active structured data exporter strategies based on format preference.

        Supports 'both', 'all', single format names ('yaml', 'excel', 'oscal'), and comma lists.

        Args:
            format_pref: Format preference string ('both', 'yaml', 'excel', 'oscal', etc.).

        Returns:
            List of active BaseDataExporter strategy instances.
        """
        pref = format_pref.strip().lower()
        if pref in ("all", "full"):
            exporters: List[BaseDataExporter] = []
            for k in ("yaml", "excel", "oscal"):
                if k in self._data_exporters:
                    exporters.append(self._data_exporters[k])
            return exporters

        if pref == "both":
            exporters = []
            if "yaml" in self._data_exporters:
                exporters.append(self._data_exporters["yaml"])
            if "excel" in self._data_exporters:
                exporters.append(self._data_exporters["excel"])
            return exporters

        if "," in pref:
            formats = [f.strip() for f in pref.split(",") if f.strip()]
            matched: List[BaseDataExporter] = []
            for fmt in formats:
                if fmt in self._data_exporters and self._data_exporters[fmt] not in matched:
                    matched.append(self._data_exporters[fmt])
            if matched:
                return matched

        if pref in self._data_exporters:
            return [self._data_exporters[pref]]

        logger.warning("Unrecognized structured data format '%s', falling back to yaml", format_pref)
        return [self._data_exporters.get("yaml", YamlDataExporter())]
