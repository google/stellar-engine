# Release Strategy & Documentation

This document outlines the versioning scheme, release classification, and release automation process for the `stellar-engine` repository.

---

## 📌 Release Classification & Versioning Scheme

`stellar-engine` follows Semantic Versioning (`vMAJOR.MINOR.PATCH`). Releases are categorized based on their impact on underlying Terraform state and deployed infrastructure resources.

### 🔴 Major Releases (`vX.0.0`)
* **Definition**: Any changes that require:
  * Terraform state manipulation (e.g., manual state modification, removals).
  * Terraform state moves (`terraform state mv` or refactoring existing resource addresses).
  * Redeployment or recreation of existing infrastructure resources.
* **Process**: Executed **manually**.
* **Upgrade Guidance**: Major releases will include detailed migration notes, state refactoring scripts, or step-by-step instructions for upgrading existing environments without unexpected downtime or state drift.

### 🔵 Minor Releases (`vX.Y.0`)
* **Definition**: Feature additions, enhancements, or updates that do **not** require Terraform state manipulation, state moves, or redeployment of existing resources (e.g., backwards-compatible infrastructure additions, non-destructive parameter updates).
* **Process**: Generated **monthly automatically** from the `main` branch.

### 🟢 Patch Releases (`vX.Y.Z`)
* **Definition**: Critical bug fixes, security patches, or urgent non-breaking adjustments.
* **Process**: Executed on an **ad-hoc** basis, where the release is updated and tagged **manually**.

---

## 🔄 Release Cadence & Automation Summary

| Release Type | Trigger / Cadence | Execution | State Manipulation / Redeploy Required? |
| :--- | :--- | :--- | :--- |
| **Major** (`vX.0.0`) | As needed | Manual | **Yes** |
| **Minor** (`vX.Y.0`) | Monthly | Automated (from `main`) | **No** |
| **Patch** (`vX.Y.Z`) | Ad-hoc / As needed | Manual | **No** |

---

## 🛠️ Contributor Guidelines & Release Workflow

To ensure smooth automated and manual releases, contributors must adhere to the following workflow:

1. **Pull Request Impact Assessment**:
   * PR authors must explicitly state whether their proposed changes require state manipulation, state moves, or resource redeployment.
   * If a PR introduces breaking state changes or resource redeployments, it must be flagged for inclusion in an upcoming **Major Release**.
2. **Main Branch Readiness**:
   * All changes merged into the `main` branch should be tested and production-ready, as automated **Minor Releases** are generated directly from `main` on a monthly schedule.
3. **Patch / Hotfix Workflow**:
   * Urgent fixes requiring a **Patch Release** are tagged manually ad-hoc against the affected version target and merged back to `main`.
