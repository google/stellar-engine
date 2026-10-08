# Changelog

## [4.2.0](https://github.com/google/stellar-engine/compare/v4.1.0...v4.2.0) (2026-10-08)


### Features

* **gemini-enterprise:** relocate blueprint and add multi-regime compliance support ([#279](https://github.com/google/stellar-engine/issues/279)) ([22ca406](https://github.com/google/stellar-engine/commit/22ca406e867289f2e0738f0c8f6ed79372bdbd91))


### Bug Fixes

* logging circular dependency in bootstrap ([#278](https://github.com/google/stellar-engine/issues/278)) ([ae0838f](https://github.com/google/stellar-engine/commit/ae0838fccf0063120e0d13b1febf8279546a0d64))
* **modules:** fix IAM key delimiters, log filters, and conditions in custom modules ([#275](https://github.com/google/stellar-engine/issues/275)) ([c4f60fb](https://github.com/google/stellar-engine/commit/c4f60fb7207ac03803cb1a9c19237d8cbc8250cd))
* **security:** harden IAM conditions, Terraform modules, FAST stages, and blueprints ([#274](https://github.com/google/stellar-engine/issues/274)) ([c7353a3](https://github.com/google/stellar-engine/commit/c7353a3991d1e2fedf065f2fb3588c8e10dc5779))

## [4.1.0](https://github.com/google/stellar-engine/compare/v4.0.1...v4.1.0) (2026-09-28)


### Features

* **fast:** surface stage IAM impersonation context and stale env warnings ([#264](https://github.com/google/stellar-engine/issues/264)) ([7f35560](https://github.com/google/stellar-engine/commit/7f3556091ade0c045d4b55614aecf2842fc355f6))
  - Prints the active automation service account for the target stage in `stage-links.sh`, warns when `GOOGLE_IMPERSONATE_SERVICE_ACCOUNT` or `CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT` is set in the shell, and documents how to troubleshoot cross-stage `403 Forbidden` impersonation errors in `docs/ddg.md`.
* **scripts:** add Windows shell pre-flight check and WSL2 documentation ([#263](https://github.com/google/stellar-engine/issues/263)) ([5cd0bf2](https://github.com/google/stellar-engine/commit/5cd0bf26cadd93156c26d8c7bb158e7a956fd5da))
  - Detects non-WSL Windows shells (Git Bash/MSYS2, Cygwin) before running deployment scripts to prevent symlink and path translation failures, and documents WSL2, Cloud Shell, and Dev Container setup for Windows users.


### Bug Fixes

* **0-bootstrap:** fix org policy parameter encoding and provision logging CMEK settings ([#268](https://github.com/google/stellar-engine/issues/268)) ([13e2e87](https://github.com/google/stellar-engine/commit/13e2e87d2114d473841c1e8c1a3787efe4414bbe))
  - Avoids double-JSON-encoding string parameters in organization policy rules and reads `google_logging_project_settings` on the log-export project first so its Cloud Logging CMEK service agent exists before granting KMS permissions and creating CMEK log buckets.
* **0-bootstrap:** order folders and projects after organization logging settings ([#262](https://github.com/google/stellar-engine/issues/262)) ([b8da03f](https://github.com/google/stellar-engine/commit/b8da03f577cfefcf9d66218c4ac3177024d07fe1))
  - Ensures organization-level Cloud Logging CMEK settings are applied before creating Stage 0 folders and projects so newly created resources inherit the required logging configuration on first apply.
* **2-networking:** fix NVA routing, Spot default, firewall policy prefix, and peering stagger ([#269](https://github.com/google/stellar-engine/issues/269)) ([f43b0a1](https://github.com/google/stellar-engine/commit/f43b0a143c3ec005ab216c7059a81d9b3d35cfc8))
  - Generates NVA routes across all tenant subnets instead of only the first, defaults NVA instances to standard on-demand VMs (`nva_spot_vms = false`), prefixes default hierarchical firewall policy names with `${var.prefix}-net-default`, and ties VPC peering sleep delays to each spoke network instance.
* **blueprints:** enable required service APIs and enforce 30-char ID preconditions ([#271](https://github.com/google/stellar-engine/issues/271)) ([33be48b](https://github.com/google/stellar-engine/commit/33be48b942a142d48ed3e86ea30b6c537d135032))
  - Explicitly enables `appengine.googleapis.com` and `sqladmin.googleapis.com` before provisioning App Engine and Cloud SQL resources, and adds Terraform lifecycle preconditions to fail early with a clear error when generated project or service account IDs exceed GCP's 30-character limit.
* **deploy.sh:** match storage_viewer's real role ID and reject an invalid Stage 2 choice ([#243](https://github.com/google/stellar-engine/issues/243)) ([397fc2e](https://github.com/google/stellar-engine/commit/397fc2ee6b3c1a61b799fe6a627d5821a81de3dc))
  - Filters out the `storage_viewer` custom organization role using its actual snake_case ID during Stage 0 pre-flight checks and exits with an error if an invalid option is entered at the Stage 2 networking prompt.
* **fast:** pass terraform validate output via env in github-script ([#260](https://github.com/google/stellar-engine/issues/260)) ([6689e2a](https://github.com/google/stellar-engine/commit/6689e2a53f16b6254b61f3f6e8535b01a8fbeaf1))
  - Passes `terraform validate` stdout through an environment variable (`process.env.VALIDATE`) in generated GitHub Actions workflow templates to prevent special characters or backticks in validation output from breaking the PR comment script.
* **gemini-enterprise:** enforce compliance settings, validate API patches, and improve deploy script ([#270](https://github.com/google/stellar-engine/issues/270)) ([a48e0ed](https://github.com/google/stellar-engine/commit/a48e0ed36f149db6a9295e7c6dd7bd1bb26677a0))
  - Removes immutable `disableAnalytics` fields from Discovery Engine `PATCH` requests, respects `compliance_regime` and `access_time_zone` settings across Terraform and `gem4gov.py`, validates HTTP responses when patching observability and assistant configs, and updates `deploy.sh` to check the tenant IaC state bucket and reuse compatible local Terraform binaries before invoking `tfenv`.

## [4.0.1](https://github.com/google/stellar-engine/compare/v4.0.0...v4.0.1) (2026-09-17)


### Bug Fixes

* **deploy.sh:** remove kms_project_id and us_keyring_name from gemini-stage-0 tfvars ([#234](https://github.com/google/stellar-engine/issues/234)) ([d843aec](https://github.com/google/stellar-engine/commit/d843aec5243d0207c048df819084b80babe307e1)), closes [#229](https://github.com/google/stellar-engine/issues/229)
  - Resolves a Terraform plan failure where `deploy.sh` generated deprecated KMS arguments that were previously removed from `gemini-stage-0/variables.tf`.
* **kms:** use regime-aware local for kms_protection_level and propagate to downstream stages ([#233](https://github.com/google/stellar-engine/issues/233)) ([a307933](https://github.com/google/stellar-engine/commit/a307933b199d83e678cdc393eb4dbcf9ae18e56c))
  - Automatically aligns Cloud KMS protection levels with compliance regimes (e.g. FedRAMP High HSM vs. standard software keys) and passes the configuration across downstream stages 1, 2, and 3.
