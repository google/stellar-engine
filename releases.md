# Release Strategy and Documentation

This document outlines the versioning scheme, release classification, and release automation process for the [stellar-engine](https://github.com/google/stellar-engine/) repository.

## Release Classification and Versioning Scheme

`stellar-engine` follows Semantic Versioning (`vMAJOR.MINOR.PATCH`). To maintain complete transparency and predictability for our users, releases are automated and categorized based on the syntax of merged commit messages.

### Major Releases

Major releases (e.g., `vX.0.0`) cover breaking changes or updates that require state manipulation or resource redeployment.

* **Definition:** Any changes that require:
  * Terraform state manipulation (e.g., manual state modification, removals).
  * Terraform state moves (`terraform state mv` or refactoring existing resource addresses).
  * Redeployment or recreation of existing infrastructure resources.
* **Trigger:** Initiated by including a `BREAKING CHANGE:` in the commit body, or by suffixing the commit type with `!` (e.g., `feat(kms)!: remove old KMS key configuration`).
* **Upgrade Guidance:** Major releases will include detailed migration notes, state refactoring scripts, or step-by-step instructions for upgrading existing environments without unexpected downtime or state drift.

### Minor Releases

Minor releases (e.g., `vX.Y.0`) cover backwards-compatible feature additions, updates, and enhancements.

* **Definition:** Feature additions, enhancements, or updates that do not require Terraform state manipulation, state moves, or redeployment of existing resources (e.g., backwards-compatible infrastructure additions, non-destructive parameter updates).
* **Trigger:** Initiated by a commit prefixed with `feat:` (e.g., `feat(bigquery): add support for partitioning`).

### Patch Releases

Patch releases (e.g., `vX.Y.Z`) cover critical bug fixes, security patches, and urgent non-breaking adjustments.

* **Definition:** Critical bug fixes, security patches, or urgent non-breaking adjustments.
* **Trigger:** Initiated by a commit prefixed with `fix:` (e.g., `fix(gcs): resolve bucket logging variable type`).

---

## Release Cadence and Automation Summary

The repository uses Google's **Release Please** to automate release preparation. Release Please continuously compiles a draft release in an open **Release Pull Request** as changes are merged to the `main` branch. The actual release is published when a maintainer merges this Release Pull Request.

| Release Type | Trigger Prefix | Cadence | Execution | State Manipulation / Redeploy Required? |
| :--- | :--- | :--- | :--- | :--- |
| **Major (`vX.0.0`)** | `feat!:` or `BREAKING CHANGE:` | As needed | Automated prep, human merge | Yes |
| **Minor (`vX.Y.0`)** | `feat:` | As needed / Batch merged weekly | Automated prep, human merge | No |
| **Patch (`vX.Y.Z`)** | `fix:` | As needed | Automated prep, human merge | No |

---

## Contributor Guidelines and Release Workflow

To ensure smooth automated releases, contributors and maintainers must adhere to the following workflow:

### 1. Pull Request Title Linting (Enforced)
To automate versioning accurately, all Pull Request titles must follow the **Conventional Commits** specification. The repository runs an automated **Pull Request Title Linter** on every PR to enforce this.

* **Format:** `<type>(<scope>): <description>` or `<type>: <description>`
* **Allowed Types:**
  * `feat`: A new feature (bumps Minor version)
  * `fix`: A bug fix (bumps Patch version)
  * `chore`: Maintenance tasks (no release)
  * `docs`: Documentation changes (no release)
  * `ci`: CI/CD workflow updates (no release)
  * `test`: Adding or correcting tests (no release)
  * `refactor`: Code refactoring without behavioral changes (no release)
  * `style`: Code style changes, whitespace, formatting (no release)
* **Example:** `feat(kms): add support for HSM protection level`

### 2. Squash Merging and Main Branch Cleanliness
To guarantee that the git history on `main` remains clean and compliant, the repository is configured to use **Squash and Merge**:
* When merging a pull request, the final squashed commit title is taken from the **PR Title**.
* Maintainers must verify that the PR title is clean and descriptive before clicking the merge button.

### 3. Release Merging
* As compliant PRs are merged to `main`, Release Please updates a single open PR titled `chore: release vX.Y.Z`.
* When ready to publish the release, a maintainer merges the Release PR. This triggers GitHub Actions to automatically create the Git tag (e.g., `v1.3.0`) and publish the GitHub Release containing the compiled changelog.
