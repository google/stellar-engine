# Changelog

## [4.0.2](https://github.com/google/stellar-engine/compare/v4.0.1...v4.0.2) (2026-09-18)


### Bug Fixes

* **deploy.sh:** match storage_viewer's real role ID and reject an invalid Stage 2 choice ([#243](https://github.com/google/stellar-engine/issues/243)) ([397fc2e](https://github.com/google/stellar-engine/commit/397fc2ee6b3c1a61b799fe6a627d5821a81de3dc))

## [4.0.1](https://github.com/google/stellar-engine/compare/v4.0.0...v4.0.1) (2026-09-17)


### Bug Fixes

* **deploy.sh:** remove kms_project_id and us_keyring_name from gemini-stage-0 tfvars ([#234](https://github.com/google/stellar-engine/issues/234)) ([d843aec](https://github.com/google/stellar-engine/commit/d843aec5243d0207c048df819084b80babe307e1)), closes [#229](https://github.com/google/stellar-engine/issues/229)
  - Resolves a Terraform plan failure where `deploy.sh` generated deprecated KMS arguments that were previously removed from `gemini-stage-0/variables.tf`.
* **kms:** use regime-aware local for kms_protection_level and propagate to downstream stages ([#233](https://github.com/google/stellar-engine/issues/233)) ([a307933](https://github.com/google/stellar-engine/commit/a307933b199d83e678cdc393eb4dbcf9ae18e56c))
  - Automatically aligns Cloud KMS protection levels with compliance regimes (e.g. FedRAMP High HSM vs. standard software keys) and passes the configuration across downstream stages 1, 2, and 3.
