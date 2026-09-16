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
* **Trigger:** Initiated by including a `BREAKING CHANGE:` in the commit body, or by suffixing any commit type with `!` (e.g., `feat(modules/kms)!: remove old KMS key configuration`).
* **Upgrade Guidance:** Major releases will include detailed migration notes, state refactoring scripts, or step-by-step instructions for upgrading existing environments without unexpected downtime or state drift.

### Minor Releases

Minor releases (e.g., `vX.Y.0`) cover backwards-compatible feature additions, updates, and enhancements.

* **Definition:** Feature additions, enhancements, or updates that do not require Terraform state manipulation, state moves, or redeployment of existing resources (e.g., backwards-compatible infrastructure additions, non-destructive parameter updates).
* **Trigger:** Initiated by a commit prefixed with `feat:` (e.g., `feat(modules/bigquery): add support for partitioning`).

### Patch Releases

Patch releases (e.g., `vX.Y.Z`) cover critical bug fixes, security patches, and urgent non-breaking adjustments.

* **Definition:** Critical bug fixes, security patches, or urgent non-breaking adjustments.
* **Trigger:** Initiated by a commit prefixed with `fix:` (e.g., `fix(modules/gcs): resolve bucket logging variable type`).

---

## Release Cadence and Automation Summary

The repository uses Google's **Release Please** to automate release preparation. Release Please continuously compiles a draft release in an open **Release Pull Request** as changes are merged to the `main` branch. The actual release is published when a maintainer merges this Release Pull Request.

| Release Type | Trigger Prefix | Cadence | Execution | State Manipulation / Redeploy Required? |
| :--- | :--- | :--- | :--- | :--- |
| **Major (`vX.0.0`)** | any `<type>!:` or `BREAKING CHANGE:` | As needed | Automated prep, human merge | Yes |
| **Minor (`vX.Y.0`)** | `feat:` | As needed | Automated prep, human merge | No |
| **Patch (`vX.Y.Z`)** | `fix:` | As needed | Automated prep, human merge | No |

---

## Contributor Guidelines and Release Workflow

To ensure smooth automated releases, contributors and maintainers must adhere to the following workflow:

### 1. Pull Request Title Linting (Enforced)
To automate versioning accurately, all Pull Request titles must follow the **Conventional Commits** specification. The repository runs an automated **Pull Request Title Linter** on every PR targeting `main` to enforce this.

* **Format:** `<type>(<scope>): <description>`

#### Types

| Type | Purpose | Version Bump | Changelog Section |
| :--- | :--- | :--- | :--- |
| `feat` | A new feature | **Minor** | Features |
| `fix` | A bug fix | **Patch** | Bug Fixes |
| `docs` | Documentation changes | None | *not shown* |
| `style` | Whitespace, formatting | None | *not shown* |
| `refactor` | Restructuring without behavioural change | None | *not shown* |
| `test` | Adding or correcting tests | None | *not shown* |
| `build` | Build system, tooling, and dependency bumps | None | *not shown* |
| `ci` | CI/CD workflow updates | None | *not shown* |
| `chore` | Maintenance tasks | None | *not shown* |

Types marked *not shown* are valid PR titles but are deliberately left out of `changelog-sections`, so they produce no CHANGELOG entry at all.

> [!IMPORTANT]
> **A release happens if and only if the CHANGELOG entry is non-empty.** Release Please skips the Release PR entirely when nothing rendered, so the `changelog-sections` list is effectively the release gate: `feat` and `fix` are the only types that can cut a release. Everything else is recorded in git history and is invisible to the release process. If your change should ship, title it `feat` or `fix`.

Dependency bumps use `build`, the standard Conventional Commits type for external dependencies — e.g. `build(deps): bump google provider to 6.12`. These do not appear in the CHANGELOG. If a provider bump changes behaviour for consumers, raise it as a `fix` or `feat` against the affected path instead.

> [!NOTE]
> Breaking changes are the exception: a commit carrying `!` or a `BREAKING CHANGE:` footer always appears under **⚠ BREAKING CHANGES**, even when its type is *not shown*. A refactor that requires state moves must therefore be titled `refactor(modules/kms)!: ...` — that is what makes it visible and bumps the major version.

#### Scopes (optional, but encouraged on `feat` and `fix`)

A scope is **never required** — `feat: add HSM protection support` is a perfectly valid title. But the CHANGELOG groups entries by type, so a scope is what tells a reader which part of the repository changed. It renders as a bold prefix:

```markdown
### Features

* **modules/kms:** add support for HSM protection level
* **fast/2-networking:** support hub-and-spoke peering
* add support for other Google Universes
```

The third entry is valid; it just says less. Where a scope helps, start it with the top-level area you touched and narrow as far as is useful:

| Area | Example |
| :--- | :--- |
| `modules` | `feat(modules/kms): add support for HSM protection level` |
| `fast` | `fix(fast/2-networking): correct subnet CIDR validation` |
| `blueprints` | `feat(blueprints/il5/bastion-pattern): add IAP tunnel support` |
| anything else | `fix(docs/releases): correct the cadence table` |

* **Multiple areas:** pick the dominant one, or omit the scope.
* **Security fixes:** use `fix` with the affected path, e.g. `fix(modules/kms): patch CVE-2025-1234`.

> [!TIP]
> If a release cycle contains only non-bumping commits and you still need to publish, open a PR containing an empty commit that forces a version. It must go through a PR like any other change, since `main` is protected and squash-merge only:
> ```bash
> git checkout -b chore/force-release
> git commit --allow-empty -m "chore: release 4.1.0" -m "Release-As: 4.1.0"
> ```
> Keep the `Release-As:` footer in the squashed commit body when merging, otherwise it has no effect.

#### PR Labels

The **Pull Request Labeler** applies `Type - *` and `Framework - *` labels automatically from the paths you touch. These are **informational only** — they drive triage and filtering, and have no effect on versioning or on the CHANGELOG.

### 2. Squash Merging and Main Branch Cleanliness
To guarantee that the git history on `main` remains clean and compliant, the repository is configured to use **Squash and Merge**:
* When merging a pull request, the final squashed commit title is taken from the **PR Title**.
* Maintainers must verify that the PR title is clean and descriptive before clicking the merge button.

### 3. Release Merging
* As compliant PRs are merged to `main`, Release Please updates a single open PR titled `release: vX.Y.Z`. The `release` type is reserved for this bot-generated PR and should not be used by contributors.
* When ready to publish the release, a maintainer merges the Release PR. This triggers GitHub Actions to automatically create the Git tag (e.g., `v1.3.0`) and publish the GitHub Release containing the compiled changelog.
