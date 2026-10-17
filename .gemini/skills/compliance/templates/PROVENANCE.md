<!-- skip boilerplate check -->
# Template Provenance and Boilerplate Policy

This directory contains templates used to generate compliance deliverables compatible with the Enterprise Mission Assurance Support Service (eMASS) and federal Risk Management Framework (RMF) packages.

## Macro-Enabled Excel Workbooks (`.xlsm`)

The four macro-enabled Excel workbooks (`.xlsm`) under `hwsw/`, `poam/`, `ppsm/`, and `sctm/` provide the worksheet structure, column layouts, named ranges, data validation dropdowns, and embedded VBA macros (`xl/vbaProject.bin`) expected by eMASS import and export workflows.

### Sanitization and Structural Modifications

All four `.xlsm` workbooks are sanitized copies rather than raw upstream binaries. Each workbook has been sanitized for distribution while preserving its eMASS column structure, named ranges, data validations, and original VBA macro modules:

1. **Metadata, Archive Structure, and VBA Stream Sanitization**:
   - `docProps/core.xml` and `docProps/app.xml` are normalized to neutral application metadata with empty creator, modified-by, and company elements.
   - Custom document properties (`docProps/custom.xml`), sensitivity label parts (`docMetadata/LabelInfo.xml`), and custom XML parts are removed.
   - Worksheet `<headerFooter>` elements are cleared across all sheets so no organization-specific headers, footers, or markings remain.
   - `xl/vbaProject.bin` streams (`PROJECT`, `VBA/_VBA_PROJECT`, and compressed `VBA/dir`) retain the original VBA macro source modules while removing workstation-specific `HelpFile` and temporary cache paths.
2. **Worksheet Content and Reference Tab Sanitization**:
   - `hwsw/HWSWList_Template.xlsm`: Uses generic header labels (`Registration ID:`) on the `Hardware` and `Software` tabs and a curated set of canonical hardware types, software types, and approval statuses in `(U) Lists` (`Tab_HWType`, `Tab_SWType`, `Tab_Approval`).
   - `ppsm/PPSMBoundariesInformationExport_Template.xlsm`: Uses a generic `Registration ID` header label.
   - `sctm/ControlInfoExport_Template.xlsm`: Uses generic baseline tier labels (`Enterprise`, `DoW Enterprise`, `[r5] Privacy (DoW - Risk Level: Low)`) and standard DoD/NIST publication citations in the `Assignment Values` reference tab, with neutral example metadata on the `Example` tab.
   - `poam/POAM_Export_Template.xlsm`: Uses neutral placeholder organization and contact text (`Example Organization, Sample Contact`) on the `Example` reference sheet.
3. **Standard OpenXML Data Validation Compatibility**:
   - `poam/POAM_Export_Template.xlsm`: List dropdowns on the `POA&M` and `Example` worksheets use standard OpenXML `<dataValidation type="list">` entries so `openpyxl.load_workbook(..., keep_vba=True)` preserves all dropdown validations without emitting extension warnings.

### Verified SHA-256 Checksums

The automated test suite (`tests/test_xlsm_hygiene.py`) verifies these exact SHA-256 digests and byte sizes and structurally audits all `.xlsm` archives:

| Template Path | Size (Bytes) | Sanitized SHA-256 Digest |
| :--- | :---: | :--- |
| `hwsw/HWSWList_Template.xlsm` | `40306` | `d3a6e839ed5bbef158822f2ba24450d8dfe9f0723eb22d24891c48b104e7a84c` |
| `poam/POAM_Export_Template.xlsm` | `130228` | `0cfc5c96fdb1432b8adc3f5896f7b6c14506bb3bfbe31cce313c6aef032d4b0f` |
| `ppsm/PPSMBoundariesInformationExport_Template.xlsm` | `27967` | `ead172b71a784c7fd0980eafc10ace24668a7a211d2b009b402a08559cd5194d` |
| `sctm/ControlInfoExport_Template.xlsm` | `977742` | `d977d7bbe8fa4b2c0a4eb736d5cfcf709efbec45c13282b500379d7d7e5e34cf` |

## YAML and Markdown Template Boilerplate Policy (`skip boilerplate check`)

The YAML and Markdown templates under `templates/` (`fips/*.yaml`, `fips/*.md`, `hwsw/*.yaml`, `poam/*.yaml`, `ppsm/*.yaml`, `sctm/*.yaml`, `ssp/*.md`, `pta/*.md`, `policies/*.md`, and `runbooks/*.md`) are hydrated directly into customer authorization deliverables. Because repository copyright headers must not be stamped onto a customer's generated authorization artifacts, these template files begin with `# skip boilerplate check` (for YAML) or `<!-- skip boilerplate check -->` (for Markdown) as recognized by `tools/check_boilerplate.py`.
