# Third-Party Provenance: eMASS Templates

This directory contains four macro-enabled Excel workbooks (`.xlsm`) used as authoritative templates for generating compliance deliverables. They are DoD eMASS export templates.

## Licensing and Origin

These templates are US Government works, which are generally not subject to domestic copyright protection under 17 USC § 105 (Public Domain in the United States). They are designed for use with the Enterprise Mission Assurance Support Service (eMASS). 

The macros embedded within these workbooks (`vbaProject.bin`) are benign form logic required by eMASS for successful ingestion. eMASS rejects workbooks with altered macros or schemas, making these exact binary payloads necessary.

The exact eMASS template version for these workbooks is unknown.

## Integrity and Modifications

The SHA-256 hashes of the files as originally committed are documented below. 

Note that `HWSWList_Template.xlsm` and `ControlInfoExport_Template.xlsm` were previously re-saved through the `openpyxl` Python library. This process destroyed any original cryptographic signatures, meaning their integrity can no longer be directly verified against a pristine DoD Cyber Exchange copy.

Additionally, `POAM_Export_Template.xlsm` and `PPSMBoundariesInformationExport_Template.xlsm` have been manually stripped of organization-identifying metadata (specifically, `docMetadata/LabelInfo.xml` and related relationship bindings) that leaked third-party Microsoft 365 tenant GUIDs.

### File Hashes

*   **POAM_Export_Template.xlsm**
    *   Original SHA-256 (as committed): `cf3551f4b2ec78b050f5fcf698f59657d2b05b2ab759c36a0ff2754f2a8a705d`
    *   Current SHA-256 (metadata stripped): `422d7b15ea35c9c2c01f29dd63f55eedf088a273ae265a3ca5c8e4b2482cb994`
*   **PPSMBoundariesInformationExport_Template.xlsm**
    *   Original SHA-256 (as committed): `58031adb607c1e85e454df753a49a4f3ee1c2ea3c8288b5dc3725dc0a582f79b`
    *   Current SHA-256 (metadata stripped): `665312ba91395e7617e478d61e1f6cdd83d7b364cfd457ef0dfbf2db8468ddf2`
*   **HWSWList_Template.xlsm**
    *   Original SHA-256 (as committed): `db05985689fbd8df9922ab198df110c44e18e23a2092ec3e170f4dd68fb3a5b1`
*   **ControlInfoExport_Template.xlsm**
    *   Original SHA-256 (as committed): `28d33d4f744b3ea4cf00882482830990c533c7e966337611d178a76c77d06a6c`

## Maintainer Instructions

Future maintainers should re-verify these templates against an authoritative download from the DoD Cyber Exchange and update the original SHA-256 hashes in this file accordingly. When downloading new versions, ensure they are checked into this repository unmodified to preserve their integrity signatures, stripping only privacy-leaking metadata if strictly necessary.

> Note regarding `pip install -e`: The `templates/` directory is not currently configured to be packaged or discovered correctly during a standard pip installation. The supported invocation method is running the scripts via the skill's own virtualenv. Restructuring the package layout to support standard pip installation is a known follow-up task.
