# Changelog

## [4.1.0](https://github.com/google/stellar-engine/compare/v4.0.1...v4.1.0) (2026-09-25)


### Features

* **fast:** surface stage IAM impersonation context and stale env warnings ([#264](https://github.com/google/stellar-engine/issues/264)) ([7f35560](https://github.com/google/stellar-engine/commit/7f3556091ade0c045d4b55614aecf2842fc355f6))
* **scripts:** add Windows shell pre-flight check and WSL2 documentation ([#263](https://github.com/google/stellar-engine/issues/263)) ([5cd0bf2](https://github.com/google/stellar-engine/commit/5cd0bf26cadd93156c26d8c7bb158e7a956fd5da))


### Bug Fixes

* **0-bootstrap:** order folders and projects after organization logging settings ([#262](https://github.com/google/stellar-engine/issues/262)) ([b8da03f](https://github.com/google/stellar-engine/commit/b8da03f577cfefcf9d66218c4ac3177024d07fe1))
* **deploy.sh:** match storage_viewer's real role ID and reject an invalid Stage 2 choice ([#243](https://github.com/google/stellar-engine/issues/243)) ([397fc2e](https://github.com/google/stellar-engine/commit/397fc2ee6b3c1a61b799fe6a627d5821a81de3dc))
* **fast:** pass terraform validate output via env in github-script ([#260](https://github.com/google/stellar-engine/issues/260)) ([6689e2a](https://github.com/google/stellar-engine/commit/6689e2a53f16b6254b61f3f6e8535b01a8fbeaf1))

## [4.0.1](https://github.com/google/stellar-engine/compare/v4.0.0...v4.0.1) (2026-09-17)


### Bug Fixes

* **deploy.sh:** remove kms_project_id and us_keyring_name from gemini-stage-0 tfvars ([#234](https://github.com/google/stellar-engine/issues/234)) ([d843aec](https://github.com/google/stellar-engine/commit/d843aec5243d0207c048df819084b80babe307e1)), closes [#229](https://github.com/google/stellar-engine/issues/229)
  - Resolves a Terraform plan failure where `deploy.sh` generated deprecated KMS arguments that were previously removed from `gemini-stage-0/variables.tf`.
* **kms:** use regime-aware local for kms_protection_level and propagate to downstream stages ([#233](https://github.com/google/stellar-engine/issues/233)) ([a307933](https://github.com/google/stellar-engine/commit/a307933b199d83e678cdc393eb4dbcf9ae18e56c))
  - Automatically aligns Cloud KMS protection levels with compliance regimes (e.g. FedRAMP High HSM vs. standard software keys) and passes the configuration across downstream stages 1, 2, and 3.
