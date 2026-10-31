# Changelog


## [5.2.0](https://github.com/google/stellar-engine/compare/v5.1.1...v5.2.0) (2026-10-31)


### Features

* **0-bootstrap:** add granular deploy_org_resources toggles for folder-scoped deployments ([#381](https://github.com/google/stellar-engine/issues/381)) ([3f9d8a5](https://github.com/google/stellar-engine/commit/3f9d8a5b5d1810b3e7ad2adccf3d42c233db39cd))
  * Adds `var.deploy_org_resources` to `fast/stages-aw/0-bootstrap` so brownfield and folder-scoped deployments can selectively disable organization-level audit configs, custom roles, organization policies, and logging sinks without organization-level IAM permissions.
* **0-bootstrap:** gate compute.requireOsLogin by compliance regime ([#293](https://github.com/google/stellar-engine/issues/293)) ([936a692](https://github.com/google/stellar-engine/commit/936a6925b26ef67d3dfdfb0442fde015c09db5d3))
  * Moves `compute.requireOsLogin` from static `fast/stages-aw/0-bootstrap/data/org-policies/compute_policy.yaml` into regime-aware `fast/stages-aw/0-bootstrap/data/custom-org-policies/compute_policy.yaml` so OS Login is enforced on FedRAMP Moderate, FedRAMP High, and US Region Restricted workloads while skipped on IL4 and IL5 workloads managed directly by Assured Workloads, fixing [#197](https://github.com/google/stellar-engine/issues/197).
* **0-bootstrap:** make compute.restrictVpcPeering producers configurable ([#352](https://github.com/google/stellar-engine/issues/352)) ([59095e9](https://github.com/google/stellar-engine/commit/59095e958c776496cf4c980f3d3b56e692913a91))
  * Adds `org_policies_config.constraints.allowed_vpc_peering_producers` defaulting to `["under:folders/832634261155"]` in `fast/stages-aw/0-bootstrap` so deployments can append or override Google-managed Private Services Access and GKE producer hierarchies on `constraints/compute.restrictVpcPeering`, fixing [#351](https://github.com/google/stellar-engine/issues/351).
* **1-resman:** support project organization policy overrides ([#294](https://github.com/google/stellar-engine/issues/294)) ([db8271c](https://github.com/google/stellar-engine/commit/db8271cffaaf840f87017f8caa1718d7a53b08c7))
  * Adds `org_policies = optional(string, "data/org-policies")` to `var.factories_config` in `fast/stages-aw/1-resman` and passes environment-scoped YAML factory paths to tenant automation and main projects, fixing [#14](https://github.com/google/stellar-engine/issues/14).
* **cli:** configure and render stages 0 and 1 ([#357](https://github.com/google/stellar-engine/issues/357)) ([f68b707](https://github.com/google/stellar-engine/commit/f68b70746f3df790fd342d2e399e1559cd9a0cd8))
  * Adds `stellar init` and `stellar render` commands under `cli/` to validate deployment answers into `answers.yaml` and render ready-to-run Terraform workspaces for `0-bootstrap` and `1-resman`, closing [#50](https://github.com/google/stellar-engine/issues/50).
* **security:** document security advisory policy and release workflow ([#382](https://github.com/google/stellar-engine/issues/382)) ([14f28c2](https://github.com/google/stellar-engine/commit/14f28c2876c44c8a9b24c99305a552fc23bb103e))
  * Adds `SECURITY.md` and a `Security advisories` section in `RELEASES.md` routing vulnerability reports through `https://g.co/vulnz` and reserving GitHub Security Advisories for confirmed vulnerabilities affecting tagged releases.


### Bug Fixes

* **blueprints:** apply fedramp-high/gitlab GKE control plane and node settings ([#345](https://github.com/google/stellar-engine/issues/345)) ([2be6eae](https://github.com/google/stellar-engine/commit/2be6eae2b5a1108157c1da4553f8838e9fc7cd87))
  * Authorizes the internal `10.203.0.0/16` CIDR block on the private GKE control plane endpoint via `vpc_config.master_authorized_ranges` and configures Confidential GKE Nodes on the node pool in `blueprints/fedramp-high/gitlab/main.tf`, closing [#314](https://github.com/google/stellar-engine/issues/314).
* **blueprints:** apply il5/gke-hardened CIS node settings ([#344](https://github.com/google/stellar-engine/issues/344)) ([46e268e](https://github.com/google/stellar-engine/commit/46e268e3d5601a23cf484b9b2e7eacb5fe829028))
  * Passes `block-project-ssh-keys`, `machine_type`, and `confidential_nodes` directly to `module.cluster-nodepool` in `blueprints/il5/gke-hardened` and exposes CIS node pool hardening inputs in `modules/gke-nodepool`, closing [#315](https://github.com/google/stellar-engine/issues/315).
* **docs:** fix stale Cloud Setup steps, a dead clone URL, committed conflict markers and private doc links ([#353](https://github.com/google/stellar-engine/issues/353)) ([5236231](https://github.com/google/stellar-engine/commit/5236231411d4fec25919f4b395ed1ac5b2d42c60))
  * Replaces placeholder clone URLs, committed merge conflict markers, private document links, and stale Cloud Setup group instructions across `README.md`, `docs/`, `fast/stages-aw/README.md`, and blueprint documentation.
* **security:** enforce Trivy SARIF severity filter and suppress false positives ([#342](https://github.com/google/stellar-engine/issues/342)) ([345616a](https://github.com/google/stellar-engine/commit/345616ac5c4f0c68fa4d3b1841233955649727ab))
  * Enables `limit-severities-for-sarif: true` and sample recipe `skip-dirs` on `aquasecurity/trivy-action` in `.github/workflows/ci.yml` and scopes `.trivyignore.yaml` rules to suppress false-positive Code Scanning alerts.


## [5.1.1](https://github.com/google/stellar-engine/compare/v5.1.0...v5.1.1) (2026-10-26)


### Bug Fixes

* **0-bootstrap:** let the Stage 0 folders inherit the logging settings ([#361](https://github.com/google/stellar-engine/issues/361)) ([0a140dd](https://github.com/google/stellar-engine/commit/0a140dd83e54d886b6817ad532c334f5fd789c1b))
  * Removes explicit `logging_settings` from `module.no-compliance-folder` and `module.branch-common-services-folder` in `fast/stages-aw/0-bootstrap/organization.tf` so Stage 0 child folders inherit the regional log storage location from `module.organization-logging` without triggering CMEK `kms_key_name` rejections inside Assured Workloads folders.
* **fast:** drop the size() guard from delegated grant conditions ([#358](https://github.com/google/stellar-engine/issues/358)) ([088a6ae](https://github.com/google/stellar-engine/commit/088a6aeafa5ad2cf57a6c96a02719a317465b102))
  * Removes the `api.getAttribute('iam.googleapis.com/modifiedGrantsByRole', []).size() > 0` CEL subexpression from delegated IAM role grant conditions across `fast/stages-aw/0-bootstrap` and `fast/stages-aw/1-resman` so IAM condition evaluation succeeds within the 12-operator Cloud IAM quota limit.
* **gem4gov-cli:** accept an all-digit suffix in the generate_id test ([#362](https://github.com/google/stellar-engine/issues/362)) ([d21e899](https://github.com/google/stellar-engine/commit/d21e89940d19730c5e9d39e57864be1741ca4de3))
  * Replaces `suffix.isalnum()` and `suffix.islower()` with `set(suffix) <= set(string.ascii_lowercase + string.digits)` in `tests/test_data_stores.py` and adds a deterministic unit test for all-digit random suffixes generated by `secrets.choice`.
* **modules/folder:** pass the folder number to the logging settings ([#359](https://github.com/google/stellar-engine/issues/359)) ([d74fa6e](https://github.com/google/stellar-engine/commit/d74fa6ead847cec24ed3253f6fd260c7ff434ac5))
  * Strips the `"folders/"` prefix via `local.folder_number = trimprefix(local.folder_id, "folders/")` in `modules/folder/logging.tf` so `google_logging_folder_settings.default` receives the bare numeric folder ID whether creating a new folder or referencing an existing folder.


## [5.1.0](https://github.com/google/stellar-engine/compare/v5.0.0...v5.1.0) (2026-10-26)


### Features

* **0-bootstrap:** support pre-created projects and workloads ([#355](https://github.com/google/stellar-engine/issues/355)) ([4c67f6b](https://github.com/google/stellar-engine/commit/4c67f6bbd2195c602fa2601cbf88c68477dea155))
  * Adds `var.project_deletion_policies` (`automation`, `billing`, `logging`) to `fast/stages-aw/0-bootstrap` and ignores `resource_settings` lifecycle changes on `google_assured_workloads_workload.primary` so imported pre-created Stage 0 projects and Assured Workloads workloads are not replaced during `terraform apply` or deleted during `terraform destroy`.
* **tests:** flatten test suite into tests/ and expand unit coverage ([#299](https://github.com/google/stellar-engine/issues/299)) ([5839cff](https://github.com/google/stellar-engine/commit/5839cffc815f5734dee055199c3efc6f64e8eacf))
  * Flattens `tests/gem4gov_cli/`, `tests/tools/`, and `tests/scripts/` into a single `tests/` directory, removes redundant wrapper scripts, and expands Python and shell unit test suites to 103 single-scenario Python tests and 90 shell tests.


### Bug Fixes

* **0-bootstrap:** use DENY condition on custom.kmsRotation so key destroy succeeds ([#284](https://github.com/google/stellar-engine/issues/284)) ([e107746](https://github.com/google/stellar-engine/commit/e107746e4fb6cbe4c8ce75f108984bf1279689d3))
  * Switches `custom.kmsRotation` in `fast/stages-aw/0-bootstrap/data/custom-constraint-policies/cloudkms.yaml` to an `action_type: DENY` condition (`has(resource.rotationPeriod) && resource.rotationPeriod > duration('7776000s')`) so KMS keys cannot exceed a 90-day rotation period while `terraform destroy` can clear `rotationPeriod` prior to key destruction.
* **blueprints:** apply Workbench notebook owners ([#338](https://github.com/google/stellar-engine/issues/338)) ([fc19ec4](https://github.com/google/stellar-engine/commit/fc19ec4eb3e6f4e2b9fb0b74cfd68713517b16af))
  * Wraps `var.notebooks[each.key].owner` as a single-element list `[var.notebooks[each.key].owner]` when set on `google_workbench_instance.playground` in `blueprints/fedramp-high/vertex-mlops/vertex.tf` instead of calling `tolist()` on a string, which previously failed type conversion and evaluated to `null`.
* **blueprints:** configure GitLab Cloud SQL private network ([#339](https://github.com/google/stellar-engine/issues/339)) ([7a5c594](https://github.com/google/stellar-engine/commit/7a5c5942463197b8e0bf03e6ce2a70e01ad14c99))
  * Passes `var.network_config.network_self_link` via `network_config.connectivity.psa_config.private_network` in `blueprints/third-party-solutions/gitlab/services.tf` instead of the undeclared `psa_configs` list attribute so the GitLab Cloud SQL instance attaches to the private VPC network.
* **blueprints:** return the il5/gke bastion external IP ([#343](https://github.com/google/stellar-engine/issues/343)) ([568f5a6](https://github.com/google/stellar-engine/commit/568f5a6f0b115a1139c3652b2e63b8a427168d54))
  * Reads `module.bastion-vm.external_ip` in `blueprints/il5/gke/outputs.tf` instead of the undeclared `network_interfaces` attribute so `bastion_vm_public_ip` returns the bastion external IP address when NAT is configured.
* **cli:** ignore deleted folders in the preflight folder check ([#356](https://github.com/google/stellar-engine/issues/356)) ([54943ac](https://github.com/google/stellar-engine/commit/54943ac498a8fe49ca97c030d410df1770eca8b1))
  * Filters folder searches by `state=ACTIVE` in `cli/src/stellar_engine/gcp/live.py` so `naming.folder` preflight checks ignore `DELETE_REQUESTED` folders left behind by prior Assured Workloads deletions.
* **fast:** omit log sink ingress without logging ([#340](https://github.com/google/stellar-engine/issues/340)) ([d0159cb](https://github.com/google/stellar-engine/commit/d0159cb40a3d5b29cd48ef8ce4deddb9afa5f968))
  * Gates the `"fast-org-log-sinks"` VPC Service Controls perimeter ingress policy reference on `var.logging != null` in `fast/stages-aw/3-security/vpc-sc.tf` so default perimeter configuration succeeds when `var.logging` is `null`.
* **gem4gov-cli:** handle empty data store lists and missing data store names ([#336](https://github.com/google/stellar-engine/issues/336)) ([80b7d4a](https://github.com/google/stellar-engine/commit/80b7d4a24669114345155af41e84f8ebab51a4c4))
  * Guards missing `name` fields and empty search data store lists in `blueprints/gemini-enterprise/gem4gov-cli/data_stores.py` and adds a container `HEALTHCHECK` instruction to `blueprints/gemini-enterprise/analytics/Dockerfile`.
* **gke:** enable shielded nodes by default and fix gke-hardened feature key ([#341](https://github.com/google/stellar-engine/issues/341)) ([a3c90fe](https://github.com/google/stellar-engine/commit/a3c90fed5efd9d1962f1e26da6cee248c2eaaa09))
  * Defaults `enable_features.shielded_nodes` to `true` in `modules/gke-cluster-standard` and `modules/gke-cluster-standard-se` and updates `blueprints/il5/gke-hardened/main.tf` from `enable_shielded_nodes` to `shielded_nodes` so GKE clusters enforce Shielded Nodes by default.
* **modules:** fix the datafusion-se README example and accelerators row ([#354](https://github.com/google/stellar-engine/issues/354)) ([28429c0](https://github.com/google/stellar-engine/commit/28429c0433f9eaeeadf97d5ad6d324042972eb02))
  * Updates the `modules/datafusion-se` README example to reference `datafusion-se` with `kms_key` and removes a blank line in `modules/datafusion-se/variables.tf` so `tools/tfdoc.py` renders the `accelerators` variable default accurately.


## [5.0.0](https://github.com/google/stellar-engine/compare/v4.2.0...v5.0.0) (2026-10-22)


### Breaking Changes

* **modules:** remove deprecated unreferenced cloud-run v1 module ([#298](https://github.com/google/stellar-engine/issues/298)) ([05f9084](https://github.com/google/stellar-engine/commit/05f9084c7fc46a264bd5f414a980cc5e6901e43b))
  * Removes the legacy `modules/cloud-run` v1 wrapper module and its `docs/tdd.md` and `modules/README.md` catalog references so all Cloud Run deployments standardize on `modules/cloud-run-v2` and `modules/cloud-run-v2-se`.
* **repo:** adopt snake_case resource and kebab-case module labels ([#310](https://github.com/google/stellar-engine/issues/310)) ([813e0a8](https://github.com/google/stellar-engine/commit/813e0a85715ae4813149d0f1f72aafc904a79ba7))
  * Renames Terraform resource labels to `snake_case` and module call labels to `kebab-case` across FAST stages and blueprints, adds `moved` blocks so existing Terraform states migrate without recreation, and enforces both conventions via `.tflint.hcl` and `.github/workflows/ci.yml`.


### Features

* **cli:** add the stellar command with preflight checks ([#305](https://github.com/google/stellar-engine/issues/305)) ([0fb5fcb](https://github.com/google/stellar-engine/commit/0fb5fcb3bf7970059353509b611e3cf8a7eadcca))
  * Introduces the `stellar` Python CLI under `cli/` with automated GCP organization, billing, IAM, quota, and regional compliance preflight checks and adds the `Stellar CLI Tests & Code Quality` workflow job in `.github/workflows/ci.yml`.
* **repo:** replace yapf with ruff, adopt 4-space Google Python Style Guide formatting, and run tooling in a locked uv Python 3.14 environment ([#302](https://github.com/google/stellar-engine/issues/302), [#323](https://github.com/google/stellar-engine/issues/323), [#325](https://github.com/google/stellar-engine/issues/325)) ([7595e07](https://github.com/google/stellar-engine/commit/7595e0790674569e6bc7056d5721fd410ab5e4b4), [17de1fa](https://github.com/google/stellar-engine/commit/17de1faf18b5d2b30007e3c530a5a858abfc6947), [faa743d](https://github.com/google/stellar-engine/commit/faa743dbb3b2dc94624c7f197bfbe44a8422ce63))
  * Migrates repository Python formatting and linting from `yapf` and `flake8` to `ruff==0.17.1` with 4-space indentation across 251 files, records the reformat commit in `.git-blame-ignore-revs`, and pins all test and lint dependencies in `pyproject.toml` and `uv.lock` on Python 3.14.
* **stages:** support essential_contacts maps, spoke_project_iam, and NGFW SSH key secrets ([#283](https://github.com/google/stellar-engine/issues/283)) ([d3f7d08](https://github.com/google/stellar-engine/commit/d3f7d08171ac52a718565da6b795f77ad44710ae))
  * Updates `0-bootstrap` to accept `essential_contacts` category maps, wires `spoke_project_iam` bindings into `2-networking-a-fedramp` and `2-networking-b-il5-ngfw`, and stores generated bastion and NGFW SSH private keys in Secret Manager instead of solely in Terraform state outputs.


### Bug Fixes

* **2-networking:** derive the IL5 NGFW landing gateway from the configured region ([#301](https://github.com/google/stellar-engine/issues/301)) ([5bee8f5](https://github.com/google/stellar-engine/commit/5bee8f5914c84978c0ac414dd756c380f23ff413))
  * Computes the default IL5 NGFW landing subnet gateway IP dynamically from `var.regions.primary` instead of hardcoding a `us-east4` CIDR address in `fast/stages-aw/2-networking-b-il5-ngfw/ngfw.tf`.
* **fast:** match stage-links.sh impersonation patterns to the real stage service accounts ([#300](https://github.com/google/stellar-engine/issues/300)) ([d8634b3](https://github.com/google/stellar-engine/commit/d8634b3b183c14b8c690d871ce3d2a740c128bbe))
  * Aligns the service account regex patterns in `fast/stage-links.sh` with the actual Stage 0 through Stage 3 automation service account emails so stage link generation resolves impersonation credentials reliably.
* **folder:** split CA_PROTECTED_B, IL5, HIPAA, and HITRUST in assured_workload_config validation ([#296](https://github.com/google/stellar-engine/issues/296)) ([41c89fb](https://github.com/google/stellar-engine/commit/41c89fb698316e823e5a07b62dfbb588c9a9b281))
  * Separates `CA_PROTECTED_B`, `IL5`, `HIPAA`, and `HITRUST` into distinct allowed strings in `modules/folder/variables.tf` so Assured Workloads folder configurations validate each compliance regime accurately.
* **gemini-enterprise:** harden analytics container permissions, variable validations, and token generation ([#285](https://github.com/google/stellar-engine/issues/285)) ([2b11211](https://github.com/google/stellar-engine/commit/2b112119e7563de3cd1202886e85d4efae3d8da0))
  * Runs the Gemini Enterprise analytics Streamlit container as a non-root user, validates `compliance_regime` and project inputs in `gemini-stage-0/variables.tf`, and hardens OAuth access token retrieval in `deploy.sh` and `gem4gov.py`.
* **modules:** fix health check and backend service configs in net-lb-ext, net-lb-int, and net-lb-proxy-int ([#297](https://github.com/google/stellar-engine/issues/297)) ([ad0370d](https://github.com/google/stellar-engine/commit/ad0370d6bba6ee62df83da593c46cac07ce1093a))
  * Corrects health check protocol blocks in `modules/net-lb-ext` and `modules/net-lb-int` to read `each.value` instead of undefined `var.health_check_config` attributes and removes unsupported attributes from `google_compute_region_backend_service` in `modules/net-lb-proxy-int`.
* **repo:** fix repo-wide lint failures, make tools/lint.sh fail closed, and enforce Repository Lint and Trivy misconfig scanning in CI ([#286](https://github.com/google/stellar-engine/issues/286), [#334](https://github.com/google/stellar-engine/issues/334)) ([e8c4616](https://github.com/google/stellar-engine/commit/e8c4616154fc2af4e3fa3684a6b5d45693460c57), [04d37e6](https://github.com/google/stellar-engine/commit/04d37e61634139393c7f33ec79937e7cf982610c))
  * Updates `tools/lint.sh` to track failing checks in `FAILED_CHECKS` and exit non-zero on any failure, sorts Terraform variable and output declarations and refreshes `tfdoc` tables across 83 module and blueprint files, adds or normalizes Apache 2.0 headers across 21 files, replaces `tfsec-pr-commenter-action` with `aquasecurity/trivy-action` misconfiguration scanning, and enforces `bash tools/lint.sh` via the `Repository Lint` job in `.github/workflows/ci.yml`.
* **scripts:** make deploy.sh exit on failure and honor no and skip answers ([#303](https://github.com/google/stellar-engine/issues/303)) ([39a1c6a](https://github.com/google/stellar-engine/commit/39a1c6a33bf9be08a5561f9ed692b08c3810da78))
  * Updates `scripts/common-functions.sh` and `scripts/deploy.sh` to propagate non-zero exit codes when stage commands fail and to respect `no` and `skip` confirmation responses during interactive deployment prompts.


## [4.2.0](https://github.com/google/stellar-engine/compare/v4.1.0...v4.2.0) (2026-10-17)


### Breaking Changes

* **gemini-enterprise:** relocate blueprint to blueprints/gemini-enterprise, remove us-regimes and experimental regime options, and remove var.auto_delete in bigtable ([#279](https://github.com/google/stellar-engine/issues/279)) ([22ca406](https://github.com/google/stellar-engine/commit/22ca406e867289f2e0738f0c8f6ed79372bdbd91))
  * Moves the Gemini Enterprise blueprint from `blueprints/fedramp-high/gemini-enterprise` to `blueprints/gemini-enterprise`, replaces legacy `US_REGIMES` and `EXPERIMENTAL` compliance regime options with `FEDRAMP_MODERATE`, `FEDRAMP_HIGH`, `IL4`, `IL5`, and `NONE`, and removes the unused `auto_delete` variable from `blueprints/fedramp-high/bigtable/variables.tf` so callers must update module paths and `terraform.tfvars` inputs.


### Features

* **gemini-enterprise:** add BigQuery datastore import and license retract/assign subcommands ([#280](https://github.com/google/stellar-engine/issues/280)) ([c6eafa9](https://github.com/google/stellar-engine/commit/c6eafa9f0c607a8ab60f636efa4e4854cb2508c5))
  * Implements the `bigquery` branch in `import_documents_helper` with `--dataset-id`, `--table-id`, and `--id-field` options on `gem4gov datastore import`, and adds `gem4gov license retract`, `gem4gov license assign`, and `gem4gov license unassign` subcommands so operators can ingest BigQuery tables and manage billing account and `userStores` license seats from the CLI.
* **gemini-enterprise:** harden Brownfield CMEK discovery, identity checks, and Stage 1 VPC and SSL ([#281](https://github.com/google/stellar-engine/issues/281)) ([85efc5f](https://github.com/google/stellar-engine/commit/85efc5f3a8e0433edf8cf3fd30b39a9af3b8ec3d))
  * Updates `blueprints/gemini-enterprise/deploy.sh` and `gemini-stage-1/load_balancer.tf` to discover the Stage 3 security project (`${PREFIX}-${ENVIRONMENT}-sec-core-0`) and regional KMS keyrings in brownfield mode, consolidates Cloud Identity group validation into the identity step, replaces the silent `try()` fallback on `use_shared_vpc` with explicit VPC and subnet preconditions, and adds `ssl_certificate_path` and `ssl_private_key_path` variables to upload self-managed regional SSL certificates from local PEM files.
* **gemini-enterprise:** relocate blueprint and add multi-regime compliance support ([#279](https://github.com/google/stellar-engine/issues/279)) ([22ca406](https://github.com/google/stellar-engine/commit/22ca406e867289f2e0738f0c8f6ed79372bdbd91))
  * Relocates `blueprints/fedramp-high/gemini-enterprise` to `blueprints/gemini-enterprise` and updates `gemini-stage-0`, `deploy.sh`, and `gem4gov.py` to support `FEDRAMP_MODERATE`, `FEDRAMP_HIGH`, `IL4`, `IL5`, and `NONE` with regime-aware KMS protection levels and service gating when deploying across regulated boundaries.


### Bug Fixes

* **0-bootstrap:** resolve logging circular dependency in bootstrap ([#278](https://github.com/google/stellar-engine/issues/278)) ([ae0838f](https://github.com/google/stellar-engine/commit/ae0838fccf0063120e0d13b1febf8279546a0d64))
  * Sets `local.locations.logging` directly to `var.regions.primary` in `fast/stages-aw/0-bootstrap/main.tf` instead of referencing `local.checklist.location` to break the circular dependency between `module.organization-logging`, `local.checklist`, and `module.automation-project` during Stage 0 initialization.
* **modules:** fix IAM key delimiters, log filters, and conditions in custom modules ([#275](https://github.com/google/stellar-engine/issues/275)) ([c4f60fb](https://github.com/google/stellar-engine/commit/c4f60fb7207ac03803cb1a9c19237d8cbc8250cd))
  * Exposes `var.notification_channels` and uses `each.key` for alert condition display names in `modules/cis-log-alerts`, fixes operator precedence parentheses in the `project-owner-log` filter in `modules/cis-log-metrics`, corrects the inverted `create_service_networking_connection` ternary in `modules/intrusion-detection-system`, uses `//` delimiters for `iam-bpa` keys in `modules/organization-se`, and wires dynamic IAM `condition` blocks into `modules/spanner-instance-se` so custom modules evaluate bindings and alerts accurately.
* **security:** harden IAM conditions, Terraform modules, FAST stages, and blueprints ([#274](https://github.com/google/stellar-engine/issues/274)) ([c7353a3](https://github.com/google/stellar-engine/commit/c7353a3991d1e2fedf065f2fb3588c8e10dc5779))
  * Guards delegated IAM role grant CEL conditions against vacuous `hasOnly()` evaluation in `0-bootstrap` and `3-security`, excludes Stage 0 bootstrap service accounts from cross-stage `serviceAccountAdmin` and `serviceAccountTokenCreator` bindings, converts numeric organization IDs via `tostring()` in `checklist.tf`, restricts generated credential and variable files to `0600` permissions, sets `rule_3` in `gemini-stage-0/cloudarmor.tf` to `deny(403)`, passes bearer tokens to `curl` via standard input in `gem4gov.py` and `deploy.sh`, and hardens repository tooling against path traversal, CSV injection, and SSRF.


## [4.1.0](https://github.com/google/stellar-engine/compare/v4.0.1...v4.1.0) (2026-09-28)


### Features

* **fast:** surface stage IAM impersonation context and stale env warnings ([#264](https://github.com/google/stellar-engine/issues/264)) ([7f35560](https://github.com/google/stellar-engine/commit/7f3556091ade0c045d4b55614aecf2842fc355f6))
  * Prints the active automation service account for the target stage in `stage-links.sh`, warns when `GOOGLE_IMPERSONATE_SERVICE_ACCOUNT` or `CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT` is set in the shell, and documents how to troubleshoot cross-stage `403 Forbidden` impersonation errors in `docs/ddg.md`.
* **scripts:** add Windows shell pre-flight check and WSL2 documentation ([#263](https://github.com/google/stellar-engine/issues/263)) ([5cd0bf2](https://github.com/google/stellar-engine/commit/5cd0bf26cadd93156c26d8c7bb158e7a956fd5da))
  * Detects non-WSL Windows shells (Git Bash/MSYS2, Cygwin) before running deployment scripts to prevent symlink and path translation failures, and documents WSL2, Cloud Shell, and Dev Container setup for Windows users.


### Bug Fixes

* **0-bootstrap:** fix org policy parameter encoding and provision logging CMEK settings ([#268](https://github.com/google/stellar-engine/issues/268)) ([13e2e87](https://github.com/google/stellar-engine/commit/13e2e87d2114d473841c1e8c1a3787efe4414bbe))
  * Avoids double-JSON-encoding string parameters in organization policy rules and reads `google_logging_project_settings` on the log-export project first so its Cloud Logging CMEK service agent exists before granting KMS permissions and creating CMEK log buckets.
* **0-bootstrap:** order folders and projects after organization logging settings ([#262](https://github.com/google/stellar-engine/issues/262)) ([b8da03f](https://github.com/google/stellar-engine/commit/b8da03f577cfefcf9d66218c4ac3177024d07fe1))
  * Ensures organization-level Cloud Logging CMEK settings are applied before creating Stage 0 folders and projects so newly created resources inherit the required logging configuration on first apply.
* **2-networking:** fix NVA routing, Spot default, firewall policy prefix, and peering stagger ([#269](https://github.com/google/stellar-engine/issues/269)) ([f43b0a1](https://github.com/google/stellar-engine/commit/f43b0a143c3ec005ab216c7059a81d9b3d35cfc8))
  * Generates NVA routes across all tenant subnets instead of only the first, defaults NVA instances to standard on-demand VMs (`nva_spot_vms = false`), prefixes default hierarchical firewall policy names with `${var.prefix}-net-default`, and ties VPC peering sleep delays to each spoke network instance.
* **blueprints:** enable required service APIs and enforce 30-char ID preconditions ([#271](https://github.com/google/stellar-engine/issues/271)) ([33be48b](https://github.com/google/stellar-engine/commit/33be48b942a142d48ed3e86ea30b6c537d135032))
  * Explicitly enables `appengine.googleapis.com` and `sqladmin.googleapis.com` before provisioning App Engine and Cloud SQL resources, and adds Terraform lifecycle preconditions to fail early with a clear error when generated project or service account IDs exceed GCP's 30-character limit.
* **deploy.sh:** match storage_viewer's real role ID and reject an invalid Stage 2 choice ([#243](https://github.com/google/stellar-engine/issues/243)) ([397fc2e](https://github.com/google/stellar-engine/commit/397fc2ee6b3c1a61b799fe6a627d5821a81de3dc))
  * Filters out the `storage_viewer` custom organization role using its actual snake_case ID during Stage 0 pre-flight checks and exits with an error if an invalid option is entered at the Stage 2 networking prompt.
* **fast:** pass terraform validate output via env in github-script ([#260](https://github.com/google/stellar-engine/issues/260)) ([6689e2a](https://github.com/google/stellar-engine/commit/6689e2a53f16b6254b61f3f6e8535b01a8fbeaf1))
  * Passes `terraform validate` stdout through an environment variable (`process.env.VALIDATE`) in generated GitHub Actions workflow templates to prevent special characters or backticks in validation output from breaking the PR comment script.
* **gemini-enterprise:** enforce compliance settings, validate API patches, and improve deploy script ([#270](https://github.com/google/stellar-engine/issues/270)) ([a48e0ed](https://github.com/google/stellar-engine/commit/a48e0ed36f149db6a9295e7c6dd7bd1bb26677a0))
  * Removes immutable `disableAnalytics` fields from Discovery Engine `PATCH` requests, respects `compliance_regime` and `access_time_zone` settings across Terraform and `gem4gov.py`, validates HTTP responses when patching observability and assistant configs, and updates `deploy.sh` to check the tenant IaC state bucket and reuse compatible local Terraform binaries before invoking `tfenv`.

## [4.0.1](https://github.com/google/stellar-engine/compare/v4.0.0...v4.0.1) (2026-09-17)


### Bug Fixes

* **deploy.sh:** remove kms_project_id and us_keyring_name from gemini-stage-0 tfvars ([#234](https://github.com/google/stellar-engine/issues/234)) ([d843aec](https://github.com/google/stellar-engine/commit/d843aec5243d0207c048df819084b80babe307e1)), closes [#229](https://github.com/google/stellar-engine/issues/229)
  * Resolves a Terraform plan failure where `deploy.sh` generated deprecated KMS arguments that were previously removed from `gemini-stage-0/variables.tf`.
* **kms:** use regime-aware local for kms_protection_level and propagate to downstream stages ([#233](https://github.com/google/stellar-engine/issues/233)) ([a307933](https://github.com/google/stellar-engine/commit/a307933b199d83e678cdc393eb4dbcf9ae18e56c))
  * Automatically aligns Cloud KMS protection levels with compliance regimes (e.g. FedRAMP High HSM vs. standard software keys) and passes the configuration across downstream stages 1, 2, and 3.

## [4.0.0](https://github.com/google/stellar-engine/compare/v3.0.0...v4.0.0) (2026-09-10)


### Breaking Changes

* **2-networking-a-fedramp:** follow the 2-networking-a-fedramp directory rename ([#214](https://github.com/google/stellar-engine/issues/214)) ([dca2f72](https://github.com/google/stellar-engine/commit/dca2f7259283c9e8353cfd2cbf16bc08818bfa36))
  * Updates `scripts/deploy.sh`, `scripts/destroy.sh`, `scripts/restore.sh`, and `scripts/clean.sh` to reference `fast/stages-aw/2-networking-a-fedramp` after the directory rename from `2-networking-a-fedramp-high` so Stage 2 FedRAMP automation scripts do not exit on a missing path.
* **3-security,postgresql:** remove unused variables and require common_services_folder, envs_folders, regions, and tenant_accounts in 3-security ([#207](https://github.com/google/stellar-engine/issues/207)) ([5949fa7](https://github.com/google/stellar-engine/commit/5949fa7ecd1e4cfc11910df2befdc7153b985a86))
  * Removes unreferenced `core_project_id`, `google_compute_global_address_name`, and `subnetwork_name` variables from `blueprints/il5/postgresql` and requires `common_services_folder`, `envs_folders`, `regions`, and `tenant_accounts` in `fast/stages-aw/3-security/variables.tf` so variable declarations match actual resource references.
* **gemini-enterprise:** remove kms_project_id and us_keyring_name from Stage 0 variables ([#210](https://github.com/google/stellar-engine/issues/210)) ([7a32639](https://github.com/google/stellar-engine/commit/7a3263937def0e43167d0fc351fb96954d1a057c))
  * Removes unused `kms_project_id` and `us_keyring_name` variable declarations from `blueprints/fedramp-high/gemini-enterprise/gemini-stage-0/variables.tf` after moving CMEK discovery to regional and multi-region keyrings.


### Features

* **fast:** introduce configurable force_destroy for GCS buckets and enable NGFW bucket versioning ([#226](https://github.com/google/stellar-engine/issues/226)) ([6d7d08c](https://github.com/google/stellar-engine/commit/6d7d08c0997b9aea19d9866434dfc2bc5a5ecbc5)), closes [#56](https://github.com/google/stellar-engine/issues/56)
  * Adds a configurable `force_destroy` variable defaulting to `false` across 10 Cloud Storage buckets in `fast/stages-aw/` and enables object versioning on `ngfw-bootstrap-bucket` in `2-networking-b-il5-ngfw/ngfw.tf` to protect state, logging, and bootstrap buckets from accidental deletion.


### Bug Fixes

* **0-bootstrap:** correct default log retention ([#218](https://github.com/google/stellar-engine/issues/218)) ([61fd227](https://github.com/google/stellar-engine/commit/61fd227d626ecfc96ab3d9f0b2956387d5b1725e))
  * Updates the log retention comment in `fast/stages-aw/0-bootstrap/terraform.tfvars.sample` to reflect the 365-day default of `logging_bucket_retention` instead of an outdated 30-day default.
* **0-bootstrap:** declare billing_override, fix the assured_workload output, align the prefix limit ([#213](https://github.com/google/stellar-engine/issues/213)) ([1ce9c3f](https://github.com/google/stellar-engine/commit/1ce9c3f30d6516ea6c397d35a3e369897472899e))
  * Declares `billing_override` in `fast/stages-aw/0-bootstrap/variables.tf`, removes the duplicate `folders/` prefix from the `assured_workload` output when `assured_workloads.regime` is unspecified, and aligns prefix length documentation with the 7-character validation limit.
* **0-bootstrap:** fix Assured Workloads folder resolution, CMEK logging buckets, and KMS IAM bindings ([#220](https://github.com/google/stellar-engine/issues/220)) ([f78ddd2](https://github.com/google/stellar-engine/commit/f78ddd241b961a6bf1f69d15625a2895467709d4))
  * Wraps consumer folder formatting in `try()` in `modules/folder/main.tf`, removes duplicate keyring-level logging IAM bindings in `fast/stages-aw/0-bootstrap/kms.tf`, adds `depends_on = [module.logging-kms]` to Stage 0 log export destinations, and normalizes custom organization policy constraint names in `modules/organization-se` to prevent race conditions and malformed resource IDs during initial apply.
* **0-bootstrap:** take the organization id explicitly in import.sh ([#215](https://github.com/google/stellar-engine/issues/215)) ([76443c9](https://github.com/google/stellar-engine/commit/76443c994fc33ac62d5fd2808386f73cff043743))
  * Accepts the target organization ID explicitly via CLI argument or `ORGANIZATION_ID` in `fast/stages-aw/0-bootstrap/import.sh` instead of unconditionally reading `gcloud organizations list`, preventing multi-organization output from corrupting generated `imports.tf` blocks.
* **1-resman:** update 1-resman tfvars sample to align with TDD example ([#78](https://github.com/google/stellar-engine/issues/78)) ([fb15e61](https://github.com/google/stellar-engine/commit/fb15e6155f448139ab6d9ccc61b1465148c4e9c7))
  * Updates `fast/stages-aw/0-bootstrap/terraform.tfvars.sample`, `fast/stages-aw/1-resman/terraform.tfvars.sample`, and `docs/ddg.md` to use consistent placeholder values and document the 7-character prefix limit so sample inputs pass validation out of the box.
* **2-networking-a-fedramp:** encrypt NVA boot disk with the vdss KMS key ([#211](https://github.com/google/stellar-engine/issues/211)) ([1b0aa34](https://github.com/google/stellar-engine/commit/1b0aa3425bad7182d782948973cbca752d2bbfb2)), closes [#193](https://github.com/google/stellar-engine/issues/193)
  * Passes the regional `vdss` Cloud KMS key to the NVA instance template boot disk configuration in `fast/stages-aw/2-networking-a-fedramp/nva.tf` so FedRAMP network virtual appliances use CMEK encryption.
* **2-networking-a-fedramp:** validate proxy_subnets and tenant subnets up front ([#216](https://github.com/google/stellar-engine/issues/216)) ([29715f2](https://github.com/google/stellar-engine/commit/29715f206784ab8599fcfed3378f4b25655ae549))
  * Adds plan-time `validation` blocks in `fast/stages-aw/2-networking-a-fedramp/variables.tf` verifying that `proxy_subnets` defines each environment key and that each environment defines at least one tenant subnet in `regions.primary` so missing inputs fail fast at plan time instead of raising `Invalid index` errors inside module resources.
* **3-security:** apply kms_protection_level to keys that set no version_template ([#212](https://github.com/google/stellar-engine/issues/212)) ([ec82b55](https://github.com/google/stellar-engine/commit/ec82b554261054a7a0eff6d8d10e6633ed93e4ca))
  * Applies `var.kms_protection_level` per key in `fast/stages-aw/3-security/core-prod.tf` and `core-dev.tf` so keys without an explicit `version_template` inherit the stage-wide protection level instead of defaulting to `SOFTWARE`.
* **cloudsql-instance:** always emit disabled psc_config ([#200](https://github.com/google/stellar-engine/issues/200)) ([fa14625](https://github.com/google/stellar-engine/commit/fa14625ed8d7e5cf577bcec399c5658d271f3206))
  * Emits `ip_configuration.psc_config` unconditionally on Cloud SQL primary and replica instances in `modules/cloudsql-instance/main.tf` so Terraform manages the disabled SQL Admin default without perpetual plan drift.
* **deploy.sh:** initialise ENABLE_MODEL_ARMOR_FLAG so IL4/IL5 don't abort on an empty jq argument ([#204](https://github.com/google/stellar-engine/issues/204)) ([68cf596](https://github.com/google/stellar-engine/commit/68cf5961baad865d642cbf1713a66d42f18ca6ee))
  * Initializes `ENABLE_MODEL_ARMOR_FLAG=false` before the compliance regime branch in `blueprints/fedramp-high/gemini-enterprise/deploy.sh` so IL4 and IL5 deployments do not abort on an empty `jq --argjson` argument.
* **deploy.sh:** remove false Assured Workload validation confirmation ([#221](https://github.com/google/stellar-engine/issues/221)) ([9578437](https://github.com/google/stellar-engine/commit/9578437bd83d8e9894343630861176dec31ca581)), closes [#134](https://github.com/google/stellar-engine/issues/134)
  * Replaces the premature Assured Workloads validation confirmation banner in `blueprints/fedramp-high/gemini-enterprise/deploy.sh` with a prompt reminding operators to review and apply folder updates in the Cloud Console before continuing.
* **deploy.sh:** replace instead of append gemini_apps assignment ([#223](https://github.com/google/stellar-engine/issues/223)) ([87d1efb](https://github.com/google/stellar-engine/commit/87d1efbde22ff2f05f89f5c26bf1fe991b35a830)), closes [#178](https://github.com/google/stellar-engine/issues/178)
  * Updates `blueprints/fedramp-high/gemini-enterprise/deploy.sh` to replace any existing `gemini_apps` block in `gemini-stage-0/terraform.tfvars` instead of appending duplicate attribute definitions on re-runs.
* **deploy.sh:** set COMPLIANCE_REGIME=NONE for regime option 4 instead of leaving it empty ([#203](https://github.com/google/stellar-engine/issues/203)) ([36f7651](https://github.com/google/stellar-engine/commit/36f7651193d67c779f7717bd03b68a694f5d7991))
  * Sets `COMPLIANCE_REGIME=NONE` when selecting option 4 in `blueprints/fedramp-high/gemini-enterprise/deploy.sh` so downstream Model Armor and compliance configuration prompts evaluate a non-empty regime value.
* **discovery-engine:** grant Discovery Engine service agent objectViewer on corpus bucket ([#219](https://github.com/google/stellar-engine/issues/219)) ([69b9a58](https://github.com/google/stellar-engine/commit/69b9a582ba6d2a142ce41ea3056bd863377238e7)), closes [#145](https://github.com/google/stellar-engine/issues/145)
  * Grants `roles/storage.objectViewer` on GCS corpus buckets to the Discovery Engine service agent in `gemini-stage-0/discovery-engine.tf` so `gem4gov datastore import` can read and index documents without `PERMISSION_DENIED` errors.
* **gem4gov:** name disableAnalytics in the engine updateMask so update-compliance applies it ([#201](https://github.com/google/stellar-engine/issues/201)) ([6afb24a](https://github.com/google/stellar-engine/commit/6afb24aa691a4dcfb8a9ee20c34c96617298425d))
  * Includes `disableAnalytics` in the Discovery Engine `PATCH` `updateMask` in `gem4gov-cli/gem4gov.py` so `update-compliance` applies analytics opt-out settings.
* **gem4gov:** stop update-compliance stripping the Model Armor binding from customerPolicy ([#205](https://github.com/google/stellar-engine/issues/205)) ([45fe5d3](https://github.com/google/stellar-engine/commit/45fe5d34e7202fc5a24673ba078b36ab88bbd906))
  * Removes `customerPolicy` from the assistant `PATCH` `updateMask` and payload in `gem4gov-cli/gem4gov.py` during `update-compliance` so existing `modelArmorConfig` bindings applied by `deploy.sh` are preserved.
* **gemini-enterprise:** align stage-0 tfvars sample and make stage-1 internal subnet lookup configurable ([#209](https://github.com/google/stellar-engine/issues/209)) ([1b1bb1a](https://github.com/google/stellar-engine/commit/1b1bb1ae70fec187d70dc349a1ffb0762e6e53e5))
  * Aligns `gemini-stage-0/terraform.tfvars.sample` with current `gcs_data_store_configs` and `bq_data_store_configs` schemas and adds a configurable `subnet_name` variable in `gemini-stage-1` so internal load balancer subnet lookups resolve across both Shared VPC and greenfield deployments.
* **gemini-enterprise:** clean up dead variables, redundant CLI definitions, and prompt wording ([#206](https://github.com/google/stellar-engine/issues/206)) ([d7d47e0](https://github.com/google/stellar-engine/commit/d7d47e0602d03dc1ce435ac11785af38234988fd))
  * Removes the duplicate `license` command group in `gem4gov.py`, clarifies the datastore onboarding prompt, deletes deprecated `gemini_config_id` from `gemini-stage-1/terraform.tfvars.sample`, and drops unused KMS variables from `gemini-stage-0/variables.tf` so CLI subcommands and sample variable files match current schemas.
* **gemini-enterprise:** parse hyphenated tenant ids and the FAST tenant bucket name in brownfield discovery ([#217](https://github.com/google/stellar-engine/issues/217)) ([60a8138](https://github.com/google/stellar-engine/commit/60a813873e67b0a26f42c0a4cd417f99298c77a5))
  * Updates brownfield project discovery in `blueprints/fedramp-high/gemini-enterprise/deploy.sh` to parse hyphenated FAST tenant identifiers and look up the `<prefix>-tn-<env>-<tenant>-0` state bucket created by `1-resman` instead of failing to detect existing tenant infrastructure.
* **gemini-enterprise:** resolve stage-0 teardown, internal VIP sharing, and access day bounds ([#225](https://github.com/google/stellar-engine/issues/225)) ([2bec226](https://github.com/google/stellar-engine/commit/2bec226eb6c29f49fc19ee987df3a0a4d12ec786)), closes [#174](https://github.com/google/stellar-engine/issues/174) [#185](https://github.com/google/stellar-engine/issues/185) [#186](https://github.com/google/stellar-engine/issues/186)
  * Sets `delete_contents_on_destroy = true` on the analytics BigQuery dataset in `gemini-stage-0`, configures `purpose = "SHARED_LOADBALANCER_VIP"` on the internal load balancer address in `gemini-stage-1`, and enforces `0..6` validation bounds for CEL `getDayOfWeek()` access policy variables so stage teardown, port 80 and 443 VIP sharing, and day-of-week access levels succeed without errors.
* **gemini-stage-0:** enable modelarmor.googleapis.com so terraform apply doesn't fail on a disabled API ([#202](https://github.com/google/stellar-engine/issues/202)) ([c0caf46](https://github.com/google/stellar-engine/commit/c0caf4635042650cd7e73633e11f7a9277e97889))
  * Adds `modelarmor.googleapis.com` to `restricted_services` in `gemini-stage-0/main.tf` so the Model Armor API is enabled before provisioning `google_model_armor_template` resources.
* **load_balancer:** guard keys() indexing against empty gemini_apps map ([#224](https://github.com/google/stellar-engine/issues/224)) ([2ad56c2](https://github.com/google/stellar-engine/commit/2ad56c218d21f703f1ce4738c852812823197fbe)), closes [#181](https://github.com/google/stellar-engine/issues/181)
  * Guards `keys(var.gemini_apps)` indexing with a `first_gemini_widget_id` local in `gemini-stage-1/load_balancer.tf` so Terraform plans succeed when `gemini_apps` is empty.
* **org-policies,docs:** add essential contacts policy parameters and document blueprint deployer permissions ([#210](https://github.com/google/stellar-engine/issues/210)) ([7a32639](https://github.com/google/stellar-engine/commit/7a3263937def0e43167d0fc351fb96954d1a057c))
  * Adds Essential Contacts allowed domain parameters to `fast/stages-aw/0-bootstrap/data/custom-org-policies/platform_policy.yaml` and documents required deployer IAM permissions and service account impersonation in the App Engine and PostgreSQL blueprint READMEs so verified organization contacts and blueprint deployers succeed out of the box.
* **quality:** resolve CodeQL unused local variables and add Python and shell test suites ([#222](https://github.com/google/stellar-engine/issues/222)) ([ed9adbf](https://github.com/google/stellar-engine/commit/ed9adbff347626bc0937932f6bb8f2dedf4c032d))
  * Removes 16 unused local variables across `gem4gov-cli` and `tools/*.py` to satisfy CodeQL `py/unused-local-variable` checks and adds automated Python unit tests, shell script syntax and unit test suites, and `tools/run_tests.sh` in `.github/workflows/ci.yml` so regressions are caught in CI.
* **stages,blueprints:** document 3-security KMS opt-in behavior and update postgresql PSA requirements ([#208](https://github.com/google/stellar-engine/issues/208)) ([df47667](https://github.com/google/stellar-engine/commit/df47667dd9aa11268df867b82de8cec7042c12b5))
  * Documents opt-in Cloud KMS key creation and adds `terraform.tfvars.sample` in `fast/stages-aw/3-security`, and documents Private Service Access VPC peering prerequisites in `blueprints/il5/postgresql/README.md` so operators configure Stage 3 keyrings and PSA networking before applying.


## [3.0.0](https://github.com/google/stellar-engine/compare/v2.13.0...v3.0.0) (2026-08-10)


### Breaking Changes

* **fast:** rename fast/stages-aw/2-networking-a-fedramp-high to fast/stages-aw/2-networking-a-fedramp and add FedRAMP Moderate support ([#162](https://github.com/google/stellar-engine/issues/162)) ([7033b8c](https://github.com/google/stellar-engine/commit/7033b8cc975ee929c5cd961e0a2b96d284669bca))
  * Renames `fast/stages-aw/2-networking-a-fedramp-high` to `fast/stages-aw/2-networking-a-fedramp`, adds FedRAMP Moderate support across FAST Assured Workloads stages, and parameterizes Cloud KMS key protection levels by compliance regime so callers can deploy either FedRAMP Moderate or FedRAMP High landing zones.


### Features

* **compute-mig:** expose instance_lifecycle_policy for managed instance group auto-healing repairs ([#97](https://github.com/google/stellar-engine/issues/97)) ([5cf518a](https://github.com/google/stellar-engine/commit/5cf518a4ff7918e541af8dc9b19a4367e37f0d26))
  * Exposes an optional `instance_lifecycle_policy` block with `force_update_on_repair` and `default_action_on_failure` in `modules/compute-mig` so managed instance group auto-healing repairs apply updated instance templates automatically.
* **net-lb-app-ext-regional:** add strong session affinity cookie support on regional external application load balancers ([#96](https://github.com/google/stellar-engine/issues/96)) ([ce3cb01](https://github.com/google/stellar-engine/commit/ce3cb01491b6d9ade58da8a649c6f10112e7f2a7))
  * Adds `strong_session_affinity_cookie` configuration and validation when `session_affinity` is set to `STRONG_COOKIE_AFFINITY` on regional external application load balancer backend services in `modules/net-lb-app-ext-regional`.


### Bug Fixes

* **ci:** introduce automated Terraform formatting, linting, and security scanning workflow ([#172](https://github.com/google/stellar-engine/issues/172)) ([db567c1](https://github.com/google/stellar-engine/commit/db567c1bb4bd586edc98c6c65544a2b1b7cb2613))
  * Adds `.github/workflows/ci.yml` with explicit least-privilege `GITHUB_TOKEN` permissions to run `terraform fmt`, `terraform validate`, `tflint`, `tfsec`, `trivy`, `shellcheck`, `black`, and `flake8` checks on pull requests and pushes to `main`.
* **deploy.sh:** enable Cloud Identity and Vertex AI APIs automatically during deployment ([#163](https://github.com/google/stellar-engine/issues/163)) ([c47be72](https://github.com/google/stellar-engine/commit/c47be72bfc4283d1e2b1132e4be83317d8354d93))
  * Automatically enables `cloudidentity.googleapis.com` and `aiplatform.googleapis.com` during Gemini Enterprise deployment in `blueprints/fedramp-high/gemini-enterprise/deploy.sh` so API activation prerequisites do not block initial onboarding.
* **docs:** centralize deployment prerequisites, relocate naming convention guide under docs/, and update READMEs for FedRAMP Moderate ([#173](https://github.com/google/stellar-engine/issues/173)) ([f64ce6c](https://github.com/google/stellar-engine/commit/f64ce6cd116fa6ecf5f96c8ba99fc44aafa3411e))
  * Updates root, stage, and networking READMEs for FedRAMP Moderate support, renames networking architecture diagrams, and resolves 84 broken relative documentation links across stages, modules, and blueprints so repository navigation links resolve cleanly.
* **gem4gov:** use testIamPermissions instead of getIamPolicy in check_roles to support group-inherited IAM bindings ([#166](https://github.com/google/stellar-engine/issues/166)) ([5f672e3](https://github.com/google/stellar-engine/commit/5f672e3cb02b57694c5ab5f21d87623a5a0971d4))
  * Replaces `getIamPolicy` role name matching with `testIamPermissions` in `gem4gov-cli` `check_roles()` so operators granted permissions through Google Groups, custom roles, or inherited bindings pass pre-flight validation.


## [2.13.0](https://github.com/google/stellar-engine/compare/v2.12.0...v2.13.0) (2026-07-31)


### Breaking Changes

* **gemini-enterprise:** remove var.gemini_config_id from Stage 1 and provision Gemini Enterprise applications via Terraform ([#150](https://github.com/google/stellar-engine/issues/150)) ([0068ff7](https://github.com/google/stellar-engine/commit/0068ff7c663641b6ea1f8e4ff926efff2b0e3d95))
  * Removes `var.gemini_config_id` from `gemini-stage-1` and migrates Gemini Enterprise application creation and engine feature configuration into `gemini-stage-0/discovery-engine.tf` so Stage 0 provisions Discovery Engine applications declaratively before Stage 1 runs.


### Features

* **0-bootstrap:** add optional billing account budgets for the Assured Workloads folder ([bce87f8](https://github.com/google/stellar-engine/commit/bce87f84b1fadbe033c158e7359ad10f31193738))
  * Adds `fast/stages-aw/0-bootstrap/budgets.tf` and `var.billing_budget` to provision optional Cloud Billing budgets and alert thresholds scoped to the Assured Workloads folder.
* **ci:** add automated monthly minor release workflow and release cadence documentation ([#165](https://github.com/google/stellar-engine/issues/165)) ([8f5b67a](https://github.com/google/stellar-engine/commit/8f5b67a69686f0300d9a73662e890222f88b271d))
  * Adds `.github/workflows/monthly-minor-tag-release.yml` to automate monthly minor version tagging and GitHub Release creation.
* **gemini-enterprise:** configure Model Armor for FedRAMP High deployments ([#150](https://github.com/google/stellar-engine/issues/150)) ([0068ff7](https://github.com/google/stellar-engine/commit/0068ff7c663641b6ea1f8e4ff926efff2b0e3d95))
  * Configures Model Armor templates and floor settings via Terraform in `blueprints/fedramp-high/gemini-enterprise/gemini-stage-0` so FedRAMP High deployments enforce prompt and response screening.


### Bug Fixes

* **0-bootstrap:** default organization log sinks to Cloud Logging buckets with a configurable 365-day retention period for regulatory compliance ([#127](https://github.com/google/stellar-engine/issues/127)) ([2dc67ca](https://github.com/google/stellar-engine/commit/2dc67cacdeccc20604c94ff13f8855fa280af97f))
  * Adds `var.logging_bucket_retention` defaulting to 365 days in `fast/stages-aw/0-bootstrap/variables.tf` so organization log sinks meet NIST SP 800-53 AU-11 retention requirements out of the box.
* **docs:** add ATO compliance reference artifacts, network architecture diagrams, and Stage 3 audit logging guidance in the Detailed Deployment Guide ([#130](https://github.com/google/stellar-engine/issues/130)) ([a08441e](https://github.com/google/stellar-engine/commit/a08441ed8ab26de6b018761c3e9f5f010f46140f))
  * Replaces the Stage 3 placeholder in `docs/ddg.md` with guidance on default audit log routing, 365-day log retention defaults, customization variables, and Pub/Sub SIEM export transitions so operators can configure compliant log retention and export.
* **gem4gov:** handle existing CMEK keys gracefully during Gemini Enterprise onboarding ([0c0b9eb](https://github.com/google/stellar-engine/commit/0c0b9eba7af2b7c03c95b612e59e0146d8ed4d91))
  * Handles pre-existing Cloud KMS keys gracefully during Gemini Enterprise onboarding in `blueprints/fedramp-high/gemini-enterprise/gem4gov-cli/gem4gov.py` instead of exiting on a conflict error.


## [2.12.0](https://github.com/google/stellar-engine/compare/v2.11.0...v2.12.0) (2026-06-22)


### Breaking Changes

* **fast:** replace data/cidrs.yaml networking file inputs with var.cidrs in tfvars ([#66](https://github.com/google/stellar-engine/issues/66)) ([429ab04](https://github.com/google/stellar-engine/commit/429ab04de782463ac28375d6207b76827bd100a0))
  * Replaces static `data/cidrs.yaml` file reads in Stage 2 networking with the `var.cidrs` input variable in `terraform.tfvars` so subnet and peering CIDR ranges are configured directly via Terraform variables.


### Features

* **0-bootstrap:** allow custom parameters on managed organization policy constraints ([#93](https://github.com/google/stellar-engine/issues/93)) ([606979f](https://github.com/google/stellar-engine/commit/606979f69ceb4c203045815fd5e5151b92988a4a))
  * Forwards custom `parameters` definitions on managed organization policy rules in `fast/stages-aw/0-bootstrap/organization.tf` so parameterized constraints such as Essential Contacts allowed domains are applied to GCP.
* **docs:** add incident response runbook template and align naming convention documentation with Detailed Deployment Guide ([#84](https://github.com/google/stellar-engine/issues/84)) ([5746192](https://github.com/google/stellar-engine/commit/5746192a74668375fe8d52b77cd5f5be1ec31065))
  * Adds `docs/runbooks/incident_response_runbook_template.md` and aligns resource naming examples with `docs/ddg.md` so incident response procedures and naming conventions stay consistent.
* **fast:** support dynamic tenant networking and add billing account overrides ([#66](https://github.com/google/stellar-engine/issues/66)) ([429ab04](https://github.com/google/stellar-engine/commit/429ab04de782463ac28375d6207b76827bd100a0))
  * Supports dynamic multi-tenant VPC and subnet provisioning in Stage 2, adds `billing_account_override` variables across stages, configures KMS creation timeouts, and refreshes stage README variable tables so multi-tenant environments scale without static YAML edits.


### Bug Fixes

* **0-bootstrap:** deprivilege bootstrap default service accounts and default regions variable to us-east4 when unspecified ([a13b69e](https://github.com/google/stellar-engine/commit/a13b69ec998e65715de34412f526accfaad56832))
  * Deprivileges default Compute Engine service accounts in `fast/stages-aw/0-bootstrap` projects and defaults `var.regions` to `us-east4` when unspecified in `terraform.tfvars`.
* **2-networking:** update local.cidr_ranges to read from var.cidrs instead of deprecated YAML configuration ([#77](https://github.com/google/stellar-engine/issues/77)) ([f25a895](https://github.com/google/stellar-engine/commit/f25a895b6e6e57ac9c8519055f7de83f9ed8e8af))
  * Updates `local.cidr_ranges` in `fast/stages-aw/2-networking-b-il5-ngfw/ngfw.tf` to read CIDR blocks from `var.cidrs` instead of the removed `data/cidrs.yaml` file.
* **gitlab:** verify GitLab package installation script checksums ([#74](https://github.com/google/stellar-engine/issues/74)) ([e12f2d4](https://github.com/google/stellar-engine/commit/e12f2d4f1049af879b072968f12fd0746f3af8a7))
  * Adds SHA-256 checksum verification for the downloaded GitLab repository installation script in `blueprints/fedramp-high/gitlab/main.tf` before executing the installer.


## [2.11.0](https://github.com/google/stellar-engine/compare/v2.10.0...v2.11.0) (2026-06-02)


### Breaking Changes

* **gemini-enterprise:** remove var.gcs_data_store_names, var.user_group, and six legacy datastore and CMEK outputs from Stage 0 ([bb53825](https://github.com/google/stellar-engine/commit/bb5382589b20aa6cdb2ac2756f323adae45fa17c))
  * Removes legacy single-datastore variables `var.gcs_data_store_names` and `var.user_group` along with six deprecated datastore and CMEK outputs from `gemini-stage-0` in favor of map-driven multi-application configuration so a single project can host multiple Gemini Enterprise apps.
* **net-lb-app-ext:** stop forcing a default port_name on backend services when unset ([#25](https://github.com/google/stellar-engine/issues/25)) ([aae379a](https://github.com/google/stellar-engine/commit/aae379a1829c716eb262b77b9361b6f47750cab1))
  * Stops populating a default `port_name` from the backend protocol in `modules/net-lb-app-ext/backend-service.tf` when `each.value.port_name` is `null`, preventing perpetual plan drift on backend services that omit `port_name`.


### Features

* **alloydb:** add read pool instance configuration support to AlloyDB module ([#16](https://github.com/google/stellar-engine/issues/16)) ([6606345](https://github.com/google/stellar-engine/commit/6606345746dc167ae97ee469eef1108b844757bd))
  * Adds `read_pool_instance` map configuration to `modules/alloydb` to provision and scale AlloyDB read pool instances alongside the primary instance.
* **cloudsql-instance:** allow overriding machine tier per read replica ([#28](https://github.com/google/stellar-engine/issues/28)) ([77f1953](https://github.com/google/stellar-engine/commit/77f1953b055e143df820e00897de3d2696c869cd))
  * Adds an optional `tier` attribute to each entry in `var.replicas` in `modules/cloudsql-instance` so read replicas can override the primary instance machine tier via `coalesce(each.value.tier, var.tier)`.
* **cloudsql-instance:** expose retain_backups_on_delete option on primary and replica instances ([#27](https://github.com/google/stellar-engine/issues/27)) ([d1c1e3e](https://github.com/google/stellar-engine/commit/d1c1e3e1894483d2e6a151a120915ac713f67ee8))
  * Adds an optional `retain_backups_on_delete` variable under `backup_configuration` in `modules/cloudsql-instance` to preserve automated and on-demand backups when primary or replica instances are destroyed.
* **docs:** add incident response runbooks for compromised IAM credentials, compute compromise, CMEK compromise, network intrusion, and VPC-SC violations ([d66ed6d](https://github.com/google/stellar-engine/commit/d66ed6dac85782aebce2b8e56c10c9686e3c00e3))
  * Adds NIST SP 800-53 incident response runbooks under `docs/runbooks/` covering compromised IAM credentials, Compute Engine resource compromise, Cloud KMS CMEK key compromise, network intrusion, and VPC Service Controls violations to support ATO incident handling requirements.
* **gem4gov:** add IL5 compliance regime support and enterprise license management commands ([7c7e133](https://github.com/google/stellar-engine/commit/7c7e13392af024fc1b99cf8525b14285c89011e9))
  * Extends `gem4gov-cli` with IL5 compliance regime feature gates, disabled implicit model caching, enterprise license listing and distribution subcommands, audit log enablement on application creation, and relative GCS path imports so operators can onboard and manage IL5 Gemini Enterprise deployments.
* **gemini-enterprise:** add BigQuery usage analytics dashboard and partitioned audit logging sink views within Assured Workloads boundaries ([751b7ab](https://github.com/google/stellar-engine/commit/751b7ab4156d965b232a2ef4741de92fe73aff51))
  * Adds a containerized Streamlit usage analytics dashboard under `blueprints/fedramp-high/gemini-enterprise/analytics/` backed by BigQuery log sink views and time-partitioned audit tables so operators can monitor Gemini Enterprise adoption inside the Assured Workloads boundary.
* **net-lb-app-ext-regional:** support regional Internet network endpoint groups on external application load balancers ([#26](https://github.com/google/stellar-engine/issues/26)) ([5e33c0b](https://github.com/google/stellar-engine/commit/5e33c0bdd3e1b905214e70726c3de740c0244207))
  * Adds `neg_configs.internet` support for regional `INTERNET_IP_PORT` and `INTERNET_FQDN_PORT` network endpoint groups in `modules/net-lb-app-ext-regional` and splits NEG output maps into `internet_neg_ids`, `psc_neg_ids`, and `serverless_neg_ids` so callers can route regional external load balancers to external endpoints.


### Bug Fixes

* **0-bootstrap:** deprivilege bootstrap default service accounts ([#68](https://github.com/google/stellar-engine/issues/68)) ([2a36067](https://github.com/google/stellar-engine/commit/2a36067d3cdf68d4ed701ab04b51d3e15fecd340))
  * Configures `default_service_account = "deprivilege"` on the Stage 0 automation, billing export, and log export projects in `fast/stages-aw/0-bootstrap` to prevent default Compute Engine service accounts from inheriting broad Editor permissions.
* **docs:** audit and format documentation for public release, refresh Detailed Deployment Guide to v2.9.1, and simplify gcloud service enablement commands ([#76](https://github.com/google/stellar-engine/issues/76)) ([317c358](https://github.com/google/stellar-engine/commit/317c358b7ba1cbf96d7b72ca8e118021a6ea3f07))
  * Updates `docs/ddg.md` with `FAST_PREFIX` environment variable export instructions, `billing_account_override` formatting examples, and streamlined `gcloud services enable` commands so step-by-step stage deployment commands run without manual edits.
* **gemini-enterprise:** support load-balancer-free deployment mode, Certificate Manager SSL, state hydration in deploy.sh, and principalSubject audit log capture ([bb53825](https://github.com/google/stellar-engine/commit/bb5382589b20aa6cdb2ac2756f323adae45fa17c))
  * Adds optional load-balancer-free deployment mode, Certificate Manager SSL certificate provisioning, `terraform.tfvars` hydration from remote state in `deploy.sh`, and `principalSubject` audit log capture in `blueprints/fedramp-high/gemini-enterprise` to simplify iterative stage re-runs and certificate management.
* **gitlab:** verify GitLab package installation script integrity before execution ([#74](https://github.com/google/stellar-engine/issues/74)) ([68684fd](https://github.com/google/stellar-engine/commit/68684fd631bd2483000592745080caa5fb433430))
  * Validates the SHA-256 digest of the GitLab package repository setup script in `blueprints/fedramp-high/gitlab/main.tf` via `var.script_sha256` before execution.
* **repo:** update GitHub issue and pull request templates and apply code quality fixes ([#23](https://github.com/google/stellar-engine/issues/23)) ([0a5939e](https://github.com/google/stellar-engine/commit/0a5939e2b88177faecafe1921eee696b588eee6e))
  * Adds `.github/pull_request_template.md` and issue report templates under `.github/ISSUE_TEMPLATE/` with compliance regime checklists so contributors document affected stages and security controls consistently.


## [2.10.0](https://github.com/google/stellar-engine/compare/v2.9.3...v2.10.0) (2026-03-13)


### Breaking Changes

* **0-bootstrap:** remove var.workforce_identity_providers, var.workload_identity_providers, and google_iam_workforce_pool_provider.default and delete modules/__experimental_deprecated ([#25](https://github.com/google/stellar-engine/issues/25)) ([114141a](https://github.com/google/stellar-engine/commit/114141ac8b249592fee2e64c52d17fa4fbe66bb0))
  * Removes unused `var.workforce_identity_providers`, `var.workload_identity_providers`, and `google_iam_workforce_pool_provider.default` from `fast/stages-aw/0-bootstrap` and deletes the unreferenced `modules/__experimental_deprecated` directory so Stage 0 only manages active bootstrap resources.


### Features

* **blueprints:** parameterize snapshot retention policies and compute boot images across blueprints ([63fe276](https://github.com/google/stellar-engine/commit/63fe276b3e758b90f754e176c8b45022c48e5c0f))
  * Adds configurable disk snapshot retention variables in `blueprints/fedramp-high/gitlab` and parameterizes the worker node boot image in `blueprints/il5/gke-hardened` so operators can customize backup retention and node images without editing module code.
* **scripts:** enhance deployment and destruction scripts with shared helper utilities, race-condition fixes, and safety validations ([#18](https://github.com/google/stellar-engine/issues/18)) ([1892784](https://github.com/google/stellar-engine/commit/1892784a5039c11f468ef43b5d67a8b7e2d4b307))
  * Adds `experimental/common-functions.sh` and updates `deploy.sh`, `destroy.sh`, `restore.sh`, and `clean.sh` with pre-flight IAM checks, retry loops, state backup validation, and resource teardown ordering to prevent race conditions during automated stage lifecycle operations.


### Bug Fixes

* **0-bootstrap:** skip custom organization policy import during initial bootstrap, remove invalid gcp.accessTransparency.enforcement constraint, and set structural org policy root_node ([0d3f83c](https://github.com/google/stellar-engine/commit/0d3f83cb140eac2143bb1e58c9e89a040cb640ea))
  * Enables `compute.googleapis.com` on the Stage 0 log export project, sets `root_node` on structural organization policies in `fast/stages-aw/0-bootstrap/organization.tf`, and removes the unsupported `gcp.accessTransparency.enforcement` constraint so initial Stage 0 organization policy applies succeed.
* **2-networking:** default custom firewall rule logging to INCLUDE_ALL_METADATA across stages and blueprints ([3704dfa](https://github.com/google/stellar-engine/commit/3704dfa6e90d4b3dc335440b1f598ac9e03695c1))
  * Updates `modules/net-vpc-firewall/main.tf` to default custom firewall rule `log_config` metadata to `INCLUDE_ALL_METADATA` when logging is enabled.
* **docs:** add Code of Conduct and relocate CONTRIBUTING.md under docs/ ([#16](https://github.com/google/stellar-engine/issues/16)) ([161e0a9](https://github.com/google/stellar-engine/commit/161e0a9d886b93c825daac45a5cd8ee7ed50e114))
  * Adds `docs/code-of-conduct.md` and moves `CONTRIBUTING.md` into `docs/CONTRIBUTING.md` to standardize open-source contributor documentation under `docs/`.
* **gem4gov:** update Discovery Engine datastore creation for collections API path and BigQuery schemas ([#22](https://github.com/google/stellar-engine/issues/22)) ([e6d9db7](https://github.com/google/stellar-engine/commit/e6d9db7a1c19c8eb9d6438e6833f6204ccc66c29))
  * Updates Discovery Engine datastore creation in `gem4gov-cli/data_stores.py` to use the `collections/default_collection/dataStores` API path and removes the redundant CMEK validation check on BigQuery datastores.
* **gemini-enterprise:** refine Access Context Manager device policy access levels and deployment script prompts ([#17](https://github.com/google/stellar-engine/issues/17)) ([7bc9f3b](https://github.com/google/stellar-engine/commit/7bc9f3bd9e30e18d68d7f740339a48586f418f17))
  * Refines Access Context Manager device policy access levels in `gemini-stage-0/access_policy.tf` and improves interactive prompts and documentation in `blueprints/fedramp-high/gemini-enterprise` so device trust rules match Workforce Identity Federation requirements.
* **security:** harden IAM conditions, storage encryption, compute defaults, networking controls, and logging configurations across stages and blueprints ([#25](https://github.com/google/stellar-engine/issues/25)) ([114141a](https://github.com/google/stellar-engine/commit/114141ac8b249592fee2e64c52d17fa4fbe66bb0))
  * Hardens IAM bindings, Cloud Storage CMEK encryption, Compute Engine Shielded VM and OS Login defaults, VPC firewall logging, and audit logging across FAST stages and blueprints to satisfy FedRAMP High and IL5 baseline security controls.


## [2.9.3](https://github.com/google/stellar-engine/compare/v2.9.2...v2.9.3) (2025-12-17)


### Breaking Changes

* **gemini-enterprise:** remove var.gcs_label_environment in Stage 0 and replace Stage 1 manual project and policy inputs with required var.gemini_enterprise_domain and remote state lookups ([#14](https://github.com/google/stellar-engine/issues/14)) ([ce7b94b](https://github.com/google/stellar-engine/commit/ce7b94bf722272f0858c6d6a3bf11b2960d6701f))
  * Removes `var.gcs_label_environment` from `gemini-stage-0` and replaces manual project and access policy inputs in `gemini-stage-1` with `var.gemini_enterprise_domain` and `terraform_remote_state` lookups from Stage 0 so Stage 1 consumes Stage 0 outputs automatically.


### Features

* **gem4gov:** introduce gem4gov-cli for Gemini Enterprise onboarding, identity provider configuration, and modular datastore management ([#6](https://github.com/google/stellar-engine/issues/6)) ([be7c12f](https://github.com/google/stellar-engine/commit/be7c12f3f1cb13219596aa8f602507ed8d6c09a3))
  * Adds `gem4gov-cli` under `blueprints/fedramp-high/gemini-enterprise/gem4gov-cli/` for CLI-driven Gemini Enterprise project onboarding, Workforce Identity Federation configuration, and Discovery Engine datastore lifecycle management.
* **gemini-enterprise:** implement greenfield and brownfield deployment modes with Shared VPC, multi-region US CMEK, and Workforce Identity Federation support ([#5](https://github.com/google/stellar-engine/issues/5)) ([070cc4e](https://github.com/google/stellar-engine/commit/070cc4ec1b3c62ecc61d5f148593cadc2366bea3))
  * Adds greenfield and brownfield deployment modes to `blueprints/fedramp-high/gemini-enterprise` supporting Shared VPC attachment, multi-region `us` Cloud KMS keys, and Workforce Identity Federation access policies.


### Bug Fixes

* **docs:** add CONTRIBUTING.md, Apache 2.0 license headers, and reorganized OSS VRP documentation ([#9](https://github.com/google/stellar-engine/issues/9)) ([46a9c1f](https://github.com/google/stellar-engine/commit/46a9c1f4508387a8b4db4c062fce631f40a97f52))
  * Reorganizes the Google Open Source Software Vulnerability Rewards Program section in `README.md` and adds Apache 2.0 license headers across repository files to meet open-source release compliance.
* **gemini-enterprise:** add prefix discovery, state bucket reading, and graceful Terraform failure handling in deploy.sh ([#8](https://github.com/google/stellar-engine/issues/8)) ([833317b](https://github.com/google/stellar-engine/commit/833317bed61721902402c315a0fee374846ac4d7))
  * Refactors FAST prefix discovery, remote state bucket lookups, and Terraform error handling in `blueprints/fedramp-high/gemini-enterprise/deploy.sh` so failed Terraform commands surface actionable diagnostics instead of exiting silently.


## [2.9.2](https://github.com/google/stellar-engine/compare/v2.9.1...v2.9.2) (2025-11-12)


### Breaking Changes

* **fast:** remove hardcoded us-east4 defaults, require var.regions in Stage 2 networking, and remove var.locations in 1-resman ([78e71ac](https://github.com/google/stellar-engine/commit/78e71aca46560b286bb50ae1a9e736361832454a))
  * Removes hardcoded `us-east4` region defaults in `fast/stages-aw/0-bootstrap`, makes `var.regions` required across stages, and removes the deprecated `var.locations` input from `fast/stages-aw/1-resman` so operators explicitly declare target deployment regions.
* **blueprints:** replace var.create_topic, var.new_topic_name, and var.region in cloud-scheduler-job with required var.topic_id ([2048bde](https://github.com/google/stellar-engine/commit/2048bded2fa8d1042f32c7e17623237193341eb1))
  * Replaces `var.create_topic`, `var.new_topic_name`, and `var.region` in `blueprints/fedramp-high/cloud-scheduler-job` with a required `var.topic_id` referencing an existing Pub/Sub topic so scheduled jobs bind to pre-provisioned messaging topics.


### Features

* **gemini-enterprise:** add two-stage Gemini Enterprise blueprint with Vertex AI Discovery Engine, regional internal load balancer, and Google Workspace IAM integration ([582e30e](https://github.com/google/stellar-engine/commit/582e30eb1131e0f3a7c06d2ca17ea8e0f403e368))
  * Splits `blueprints/fedramp-high/gemini-enterprise` into `gemini-stage-0` for project, CMEK, Discovery Engine, and Access Context Manager provisioning and `gemini-stage-1` for regional internal load balancing and Google Workspace IAM integration.


### Bug Fixes

* **3-security:** add Stage 3 security validation script ([5ee81eb](https://github.com/google/stellar-engine/commit/5ee81ebd95e4f385e5e44a9bb444741dd4adf73f))
  * Adds `fast/stages-aw/3-security/validation.sh` to verify Stage 3 Cloud KMS keys, keyrings, and security project resources after deployment.
* **blueprints:** align Cloud Armor WAF rules with preconfigured security best practices ([2048bde](https://github.com/google/stellar-engine/commit/2048bded2fa8d1042f32c7e17623237193341eb1))
  * Updates `blueprints/fedramp-high/cloud-armor/rules.yaml` and `main.tf` to enforce preconfigured OWASP ModSecurity CRS WAF rules and rate-based throttling policies.
* **docs:** add Apache 2.0 license headers, OSS VRP exclusion notice, CONTRIBUTING.md, and GEMINI.md contributor guidelines ([fb14045](https://github.com/google/stellar-engine/commit/fb14045f2fc26485734a6557c13dbe1038588810))
  * Adds the Google Open Source Software Vulnerability Rewards Program exclusion notice to `README.md` along with contributor and `GEMINI.md` repository guidelines.


## [2.9.1](https://github.com/google/stellar-engine/compare/v2.9.0...v2.9.1) (2025-09-19)


### Breaking Changes

* **1-resman:** remove tenant-core-folders and tenant-self-folders modules and drop var.tag_names and var.tags ([f667c1c](https://github.com/google/stellar-engine/commit/f667c1c36f645bb0032880c784de6cb074045ec6))
  * Collapses `module.tenant-core-folders` and `module.tenant-self-folders` in `fast/stages-aw/1-resman/branch-tenants.tf` so tenant resources reside directly under each tenant folder, and removes `var.tag_names` and `var.tags`.
* **blueprints:** replace gke-project, logging, and vpc-peering-project blueprints, decouple inline KMS creation across 7 IL5 blueprints, and require var.kms_key_name in bigtable ([2f91cb2](https://github.com/google/stellar-engine/commit/2f91cb2d67926b8ec5a60f4170728d647e08841f))
  * Replaces the legacy `gke-project`, `logging`, and `vpc-peering-project` directories, decouples inline Cloud KMS key creation across seven IL5 blueprints to consume existing Stage 3 KMS keys, and requires `var.kms_key_name` in `blueprints/fedramp-high/bigtable`.


### Features

* **blueprints:** add BeyondCorp Application Protection, GKE standard, GKE hardened, and GKE GitOps blueprints ([fd74626](https://github.com/google/stellar-engine/commit/fd74626e568330d0657eeb9ff36d0c4e38855ea1))
  * Adds `blueprints/il5/bcap`, `blueprints/il5/gke`, `blueprints/il5/gke-hardened`, and `blueprints/il5/gke-gitops` with Policy Controller constraints disallowing privileged pods and enforcing namespace governance for IL5 Kubernetes workloads.
* **scripts:** add automated deployment, teardown, and redeployment orchestration scripts ([6adabf9](https://github.com/google/stellar-engine/commit/6adabf9276963c02230c0924ed629da341ace4f8))
  * Adds `experimental/deploy.sh`, `experimental/destroy.sh`, `experimental/restore.sh`, and `experimental/clean.sh` to automate end-to-end FAST stage deployment, state backup, and teardown.


### Bug Fixes

* **0-bootstrap:** resolve Terraform type consistency error in organization.tf and add .managed org policy IDs for import.sh ([e1be125](https://github.com/google/stellar-engine/commit/e1be1256e9d78d10a5e6b5d8176cf6e62d0d73e3))
  * Fixes a Terraform type unification error in `fast/stages-aw/0-bootstrap/organization.tf` and adds `.managed` organization policy resource IDs in `import.sh` so existing managed constraints import cleanly into Stage 0 state.
* **2-networking:** configure Cloud DNS across FedRAMP High and IL5 networking stages ([398b514](https://github.com/google/stellar-engine/commit/398b514f324ed4fa11245d8a3bc01235769e2265))
  * Configures Cloud DNS forwarding zones, response policies, and `dns-policy-rules.yaml` in `fast/stages-aw/2-networking-a-fedramp-high` and `fast/stages-aw/2-networking-b-il5-ngfw` so spoke VPCs resolve private Google APIs and on-premises domains through the landing zone.
* **docs:** migrate repository links to GitHub and add contribution guidelines ([4c7a62c](https://github.com/google/stellar-engine/commit/4c7a62c32a683395e2e2918b07c0f9aaa49f3a41))
  * Migrates repository URLs from internal GitLab instances to `https://github.com/google/stellar-engine` across `README.md` and `blueprints/README.md`.


## [2.9.0](https://github.com/google/stellar-engine/compare/v2.8.1...v2.9.0) (2025-04-08)


### Breaking Changes

* **modules:** bump minimum Terraform required_version to >= 1.10.2 and hashicorp/google provider constraints to >= 6.21.0, < 7.0.0 ([a717964](https://github.com/google/stellar-engine/commit/a717964c522a26c391ca12c5f1a77372c52564ac))
  * Upgrades `required_version` to `>= 1.10.2` and `hashicorp/google` and `hashicorp/google-beta` provider constraints to `>= 6.21.0, < 7.0.0` across all modules, stages, and blueprints.
* **blueprints:** replace compute-persistent-disk with compute-engine and standardize input variable names across 32 FedRAMP High and IL5 blueprints ([9668230](https://github.com/google/stellar-engine/commit/96682303739dc09420da6c54ae89495c37d719e9))
  * Replaces `blueprints/il5/compute-persistent-disk` with `blueprints/il5/compute-engine` and standardizes input variable names across 32 FedRAMP High and IL5 blueprints to match `docs/naming-convention.md`.


### Features

* **1-resman:** include environment name in top-level tenant folder naming ([3d99cb0](https://github.com/google/stellar-engine/commit/3d99cb03505ac208393077809a2c357a1d322670))
  * Includes the environment key in top-level tenant folder names in `fast/stages-aw/1-resman/branch-tenants.tf` so tenant folders follow the `<prefix>-<env>-<tenant>` naming convention.
* **blueprints:** add Cloud Functions and self-managed GitLab blueprints ([9668230](https://github.com/google/stellar-engine/commit/96682303739dc09420da6c54ae89495c37d719e9))
  * Adds the FedRAMP High Cloud Functions blueprint under `blueprints/fedramp-high/cloud-functions` and the self-managed GitLab blueprint under `blueprints/fedramp-high/gitlab` so regulated tenants can deploy serverless functions and self-hosted source control.
* **docs:** add GCP resource naming standard documentation and refresh FAST stage README guides ([bc1d214](https://github.com/google/stellar-engine/commit/bc1d214e443632dd9e90862f3f9c407f9833a419))
  * Adds `documentation/naming-convention.md` defining resource, variable, and prefix naming standards across Stellar Engine stages and blueprints so module and blueprint interfaces follow a uniform schema.


### Bug Fixes

* **0-bootstrap:** update setIAM.sh to append rather than overwrite IAM policy bindings and remove obsolete DNS CIS log metric block ([8767554](https://github.com/google/stellar-engine/commit/876755487c2744d50bb5fa085ed9ce1720fca71c))
  * Updates `fast/stages-aw/0-bootstrap/setIAM.sh` to add IAM policy bindings incrementally via `gcloud organizations add-iam-policy-binding` instead of replacing the entire organization IAM policy.
* **scripts:** resolve ShellCheck warnings across repository shell scripts ([e428024](https://github.com/google/stellar-engine/commit/e4280249054faa66b6f2843b27304d080675569d))
  * Resolves ShellCheck warnings across `fast/stage-links.sh`, `fast/stages-aw/0-bootstrap/import.sh`, `fast/stages-aw/0-bootstrap/setIAM.sh`, `generate-mocks.sh`, and `tools/lint.sh` to prevent unquoted variable expansion and word-splitting defects.


## [2.8.1](https://github.com/google/stellar-engine/compare/v2.8.0...v2.8.1) (2025-03-24)


### Bug Fixes

* **0-bootstrap:** remove unsupported VPC Flow Logs organization policy constraint ([064c618](https://github.com/google/stellar-engine/commit/064c6182a159fad5498a8e19376cf47454860abd))
  * Removes the unsupported VPC Flow Logs organization policy constraint from `fast/stages-aw/0-bootstrap/data/org-policies/networking_policy.yaml` so Stage 0 organization policy applies succeed.
* **blueprints:** update GitLab blueprint deployment documentation ([f8ea573](https://github.com/google/stellar-engine/commit/f8ea5734bb4c11c27e80e34680cf8923f208dabf))
  * Updates deployment instructions and variable examples in `blueprints/third-party-solutions/gitlab/README.md` so operators configure prerequisite VPC networking and KMS keys before deploying GitLab.


## [2.8.0](https://github.com/google/stellar-engine/compare/v2.7.2...v2.8.0) (2025-03-17)


### Features

* **0-bootstrap:** lower prefix length validation limit, add tenant name validation, and map Assured Workloads compliance regimes ([c2309b9](https://github.com/google/stellar-engine/commit/c2309b9419c507020b1fa1184229e0393d6fd415))
  * Lowers the maximum `prefix` length validation limit in `fast/stages-aw/0-bootstrap` and `1-resman` to prevent generated project and service account IDs from exceeding 30 characters, adds tenant name validation, and maps Assured Workloads compliance regimes.


### Bug Fixes

* **2-networking:** increase Private Service Connect subnet sizing in IL5 NGFW networking stage ([a9222c1](https://github.com/google/stellar-engine/commit/a9222c143e11af04392fd34fb98b73955f7fdef4))
  * Increases the Private Service Connect subnet CIDR prefix size in `fast/stages-aw/2-networking-b-il5-ngfw/psc.tf` to satisfy GCP minimum subnet size requirements.
* **blueprints:** update GKE project blueprint initial deployment configuration ([db9a846](https://github.com/google/stellar-engine/commit/db9a846bbeed00a7ce3fca529e71ba0400482fbd))
  * Updates initial cluster deployment settings in `blueprints/il5/gke-project/main.tf` so first-time Terraform applies complete without node pool dependency errors.


## [2.7.2](https://github.com/google/stellar-engine/compare/v.2.7.1...v2.7.2) (2025-03-06)


### Features

* **docs:** add comprehensive root README architecture overview and export Checkov reports for SonarQube ([354d256](https://github.com/google/stellar-engine/commit/354d25671eddc1cda597ad287f53f86476eff611))
  * Expands the root `README.md` with an architecture overview of FAST stages and workload blueprints and configures Checkov XML report exports for SonarQube ingestion.


### Bug Fixes

* **0-bootstrap:** support deployments without a billing export project and fix organization policy configuration typo ([eede38c](https://github.com/google/stellar-engine/commit/eede38c8a797b272f272a06abc376494ce1d1fe1))
  * Makes the billing export project optional in `fast/stages-aw/0-bootstrap` and fixes a constraint key typo in `fast/stages-aw/0-bootstrap/organization.tf` so organizations without local billing export can complete Stage 0 bootstrap.
* **modules:** truncate generated folder and resource identifiers exceeding 30-character limits ([00b9983](https://github.com/google/stellar-engine/commit/00b998324a46178d65de9f714639e0aa81958c89))
  * Truncates generated folder, project, and service account identifiers in `modules/folder`, `modules/project`, and `modules/iam-service-account` when combined prefix strings exceed 30 characters.


## [v.2.7.1](https://github.com/google/stellar-engine/compare/v2.7.0...v.2.7.1) (2025-01-24)


### Bug Fixes

* **fast:** synchronize FAST stage links, stage variable templates, and upstream module configurations ([7972c1a](https://github.com/google/stellar-engine/commit/7972c1a0f080762b45305d0d0b029a831afc0ed5))
  * Synchronizes `fast/stage-links.sh`, stage output templates, and module references across `fast/stages-aw/0-bootstrap`, `1-resman`, `2-networking-b-il5-ngfw`, and `3-security` so generated `.auto.tfvars.json` files and provider definitions match downstream stage inputs.


## [2.7.0](https://github.com/google/stellar-engine/compare/v.2.6.0...v2.7.0) (2025-01-17)


### Breaking Changes

* **blueprints:** remove var.email and var.gke_service_account_id in gke-project and var.project in pub-sub-project ([4cca0af](https://github.com/google/stellar-engine/commit/4cca0af901567cbffd54ec97f8ed6c50e3b25246))
  * Removes unused `var.email` and `var.gke_service_account_id` from `blueprints/il5/gke-project/variables.tf` and removes `var.project` from `blueprints/il5/pub-sub-project/variables.tf` so callers only supply variables referenced by each blueprint.


### Features

* **blueprints:** add Access Context Manager, BeyondCorp Enterprise, Cloud Data Fusion, Cloud IDS, Cloud Workstations, Network Connectivity Center, and Private Service Connect blueprints ([20fcd12](https://github.com/google/stellar-engine/commit/20fcd12b1c6d74f39e4ed2cdc4d4c6444bb3582f))
  * Adds FedRAMP High blueprints for Access Context Manager, BeyondCorp Enterprise, Cloud Data Fusion, Cloud IDS, Cloud Workstations, Network Connectivity Center, and Private Service Connect under `blueprints/fedramp-high/` to expand regulated workload coverage.
* **ci:** add SonarQube analysis stage and blueprint documentation validation rules to CI pipeline ([5d28140](https://github.com/google/stellar-engine/commit/5d28140b1f5689b580edc2ade5ff8dcaf32fbd9d))
  * Adds a SonarQube static analysis stage in `.gitlab-ci.yml` and configures `sonar-project.properties` for automated repository quality scanning in CI.


### Bug Fixes

* **0-bootstrap:** conditionally include billing export project in log metric alerts and remove deprecated bootstrap project config ([fba8809](https://github.com/google/stellar-engine/commit/fba8809f9ee9125f63c0d7e8824fbe1f73b30c70))
  * Conditionally includes the billing export project in `fast/stages-aw/0-bootstrap/log-metric-alerts.tf` only when billing export is enabled.
* **1-resman:** enforce OS Login on common services projects, disable VDSS project-wide SSH keys, and enable Cloud DNS logging ([9cd07f0](https://github.com/google/stellar-engine/commit/9cd07f0b0fe05fd16482167bb52217d92ebf8331))
  * Enforces `enable-oslogin = "TRUE"` on the Stage 0 automation, billing export, and log export projects in `fast/stages-aw/0-bootstrap` and disables project-wide SSH keys in `1-resman` to satisfy CIS Compute Engine access controls.
* **blueprints:** prevent privileged pods in GKE blueprint, enforce KMS key rotation, and refine Cloud SQL log metric filters ([4cca0af](https://github.com/google/stellar-engine/commit/4cca0af901567cbffd54ec97f8ed6c50e3b25246))
  * Adds Kubernetes Policy Controller manifests in `blueprints/il5/gke-project/policies/` to block privileged pods, enforces Cloud KMS key rotation periods, and refines Cloud SQL log metric filters.


## [v.2.6.0](https://github.com/google/stellar-engine/compare/v2.5.0...v.2.6.0) (2024-12-13)


### Breaking Changes

* **blueprints:** remove var.key and var.keyring from Cloud SQL for PostgreSQL blueprint ([18e0d90](https://github.com/google/stellar-engine/commit/18e0d90988241cc7ce58c4a7f30593633b8cd99a))
  * Removes `var.key` and `var.keyring` from `blueprints/il5/postgresql/variables.tf` in favor of referencing an existing Cloud KMS key ID so the blueprint consumes Stage 3 security keys directly.


### Features

* **blueprints:** add Cloud Composer, Cloud Scheduler, Cloud Spanner, Cloud Translation, Document AI, Firestore, and Workflows blueprints for FedRAMP High ([18e0d90](https://github.com/google/stellar-engine/commit/18e0d90988241cc7ce58c4a7f30593633b8cd99a))
  * Adds FedRAMP High workload blueprints under `blueprints/fedramp-high/` for Cloud Composer, Cloud Scheduler, Cloud Spanner, Cloud Translation, Document AI, Firestore, and Workflows so operators can deploy CMEK-encrypted data and orchestration services.
* **modules:** add reusable Cloud Scheduler and Workflows Terraform modules ([74d2a88](https://github.com/google/stellar-engine/commit/74d2a885d99673215a4371b8823f75f393659b16))
  * Adds reusable `modules/cloud-scheduler` and `modules/workflows` Terraform modules for provisioning scheduled jobs and serverless orchestration workflows across blueprints.


### Bug Fixes

* **0-bootstrap:** grant Organization Policy Admin role during bootstrap and refine organization policy definitions ([dc104da](https://github.com/google/stellar-engine/commit/dc104da9cd84bf14633d3c93e94c52423f30d1fc))
  * Adds `roles/orgpolicy.policyAdmin` to `fast/stages-aw/0-bootstrap/setIAM.yaml.sample` so bootstrap deployers can manage organization policies during Stage 0 apply.
* **2-networking:** enable VPC Flow Logs, prevent 0.0.0.0/0 allow rules in firewall policies, and allow bastion SSH to NVA management instances ([257e8f3](https://github.com/google/stellar-engine/commit/257e8f306a6b62357d9428b1919ffa1d56c19847))
  * Adds bastion CIDR ranges and updates `fast/stages-aw/2-networking-b-il5-ngfw/data/firewall-rules/mgmt/rules.yaml` to permit SSH access from the management bastion to NGFW appliance interfaces.
* **3-security:** align Stage 3 security resource cleanup and CIS log alert metric configurations ([cff48b4](https://github.com/google/stellar-engine/commit/cff48b4ac761a1eddf94bf7adfc555d5ce7119ee))
  * Adds `fast/stages-aw/3-security/sa_lockdown.sh` and README instructions to deprivilege default service accounts and align CIS log alert metric configurations.


## [2.5.0](https://github.com/google/stellar-engine/compare/v2.2.0...v2.5.0) (2024-11-22)


### Breaking Changes

* **fast,blueprints:** remove fast/stages-aw/2-networking-c-nva, rename fast/stages-aw/2-security to fast/stages-aw/3-security, and replace blueprints/il5/logging ([5a2e335](https://github.com/google/stellar-engine/commit/5a2e33558408ba184225ae739dc043f58c4d1341))
  * Removes `fast/stages-aw/2-networking-c-nva`, renames `fast/stages-aw/2-security` to `fast/stages-aw/3-security`, and replaces `blueprints/il5/logging` with integrated Stage 0 audit logging and CIS log metric modules so stage numbering matches the deployment execution order.


### Features

* **2-networking:** add hierarchical firewall policy rule blocking 0.0.0.0/0 ingress across stage networks ([0e17b71](https://github.com/google/stellar-engine/commit/0e17b71b63adbb884d99fd17849a49f505c71254))
  * Adds a custom organization policy constraint in `fast/stages-aw/0-bootstrap/data/custom-constraint-policies/networking.yaml` that blocks VPC firewall rules allowing `0.0.0.0/0` ingress.
* **blueprints:** add App Engine, Cloud Run, Dataproc cluster, Datastore, and Vertex AI Workbench MLOps blueprints for FedRAMP High ([26994c1](https://github.com/google/stellar-engine/commit/26994c140eee3e81bef6b5e48cab63ae174281ec))
  * Adds FedRAMP High blueprints under `blueprints/fedramp-high/` for App Engine, Cloud Run, Dataproc, Firestore in Datastore mode, and Vertex AI Workbench MLOps alongside `modules/app-engine` to support serverless, analytics, and ML workloads.


### Bug Fixes

* **blueprints:** remove unused var.keys in Cloud SQL for PostgreSQL blueprint and verify service account bindings ([0cef625](https://github.com/google/stellar-engine/commit/0cef6251146c8442a8e278d7c5177893a122daf2))
  * Simplifies `blueprints/il5/postgresql` by removing unused `var.keys` declarations and verifying Cloud KMS service agent IAM bindings before instance creation.


## [2.2.0](https://github.com/google/stellar-engine/compare/v2.1.0...v2.2.0) (2024-11-13)


### Breaking Changes

* **modules:** upgrade hashicorp/google and hashicorp/google-beta provider constraints to >= 6.1.0, < 7.0.0 and remove modules/private-service-connect ([cb9a955](https://github.com/google/stellar-engine/commit/cb9a955a9d558160e5984593689ae5259591399e))
  * Upgrades `modules/` to the upstream Cloud Foundation Fabric module baseline with `hashicorp/google` and `hashicorp/google-beta` `>= 6.1.0, < 7.0.0` constraints and removes the standalone `modules/private-service-connect` directory so all stages and blueprints use Google provider 6.x.


### Bug Fixes

* **blueprints:** update blueprints for upgraded provider compatibility and restore backend service Cloud Armor security policy attachment ([9fd3b7f](https://github.com/google/stellar-engine/commit/9fd3b7ff252dcf8137a8be85dc820987f05f2c75))
  * Restores the `security_policy` attribute on `google_compute_region_backend_service` in `modules/net-lb-app-ext-regional/backend-service.tf` so regional external load balancers attach Cloud Armor policies.


## [2.1.0](https://github.com/google/stellar-engine/compare/v2.0.0...v2.1.0) (2024-11-12)


### Breaking Changes

* **fast,blueprints:** remove fast/stages-aw/2-networking-f-ngfw, fast/stages-aw/3-project-factory, legacy upstream stages and blueprints, and relocate cnap to blueprints/fedramp-high/cnap ([0ab08e0](https://github.com/google/stellar-engine/commit/0ab08e0c185a1c15ded742154910a6f138853c8a))
  * Removes obsolete `fast/stages-aw/2-networking-f-ngfw` and `fast/stages-aw/3-project-factory` directories along with unused upstream stages and moves the Cloud Native Access Point blueprint to `blueprints/fedramp-high/cnap` so the repository retains only supported Assured Workloads stages.


### Features

* **2-networking:** configure Private Service Connect endpoints, restrictVPCPeering organization policies, and Cloud Armor WAF throttling rules ([747d72b](https://github.com/google/stellar-engine/commit/747d72b1d2157fc620bff2f4274b11ceebb94255))
  * Configures Private Service Connect global endpoints, updates `compute.restrictVpcPeering` organization policies, and adds Cloud Armor rate-limiting rules in Stage 2 networking and blueprints to restrict private Google API egress and throttle abusive traffic.
* **2-security:** enforce KMS key rotation schedules and enable Container Scanning API for vulnerability management ([10bc0aa](https://github.com/google/stellar-engine/commit/10bc0aaadd1df69a2b499e7caa87696282f4b39c))
  * Configures automated Cloud KMS key rotation periods across stage and blueprint keyrings and enables `containerscanning.googleapis.com` for container image vulnerability scanning.
* **blueprints:** add Cloud Armor security policy blueprint with YAML-driven rule definitions ([da0a11b](https://github.com/google/stellar-engine/commit/da0a11b6ba97025e11a7c970dca2429f19e1bda8))
  * Refactors `blueprints/fedramp-high/cloud-armor` to parse WAF and rate-limiting security rules from a simplified `rules.yaml` configuration file.
* **blueprints:** add Secret Manager blueprint with CMEK encryption and secret version management helper script ([c3264d3](https://github.com/google/stellar-engine/commit/c3264d3cf3a4c25be426484540f610cde14432a1))
  * Adds `blueprints/fedramp-high/secret-manager` with Customer-Managed Encryption Key support and an `add_secret_versions.sh` helper script for populating secret versions.


### Bug Fixes

* **0-bootstrap:** restore bootstrap user variable and add IAM permission helper scripts for Stage 0 and Stage 1 ([2be4597](https://github.com/google/stellar-engine/commit/2be4597418988c40801d411c78c39aa3ff235952))
  * Adds `fast/stages-aw/0-bootstrap/setIAM.sh` and stage permission helper scripts to automate prerequisite IAM role bindings for Stage 0 and Stage 1.
* **2-networking:** enforce Confidential Compute on NGFW management bastion and disable project-wide SSH keys across compute resources ([cd1ed94](https://github.com/google/stellar-engine/commit/cd1ed941f637cb947ba5846229bb888f67c290b6))
  * Enables Confidential Compute on the `n2d-highcpu-2` management bastion in `fast/stages-aw/2-networking-b-il5-ngfw/bastion.tf` and sets `block-project-ssh-keys = true` across compute blueprints and networking stages to prevent project-wide SSH key escalation.


## [2.0.0](https://github.com/google/stellar-engine/compare/v1.0.2...v2.0.0) (2024-10-18)


### Breaking Changes

* **fast:** remove module.kms in 0-bootstrap, replace 12 tenant and branch folder modules in 1-resman with the common-services hierarchy, split Stage 2 into 2-networking-a-fedramp-high and 2-networking-b-il5-ngfw, and bump provider minimum to >= 5.43.1 ([056ba34](https://github.com/google/stellar-engine/commit/056ba344f836fa50a3ac067271ad2be609f45e04))
  * Restructures `fast/stages-aw/1-resman` to place IaC, audit log, and billing projects under a `common-services` folder hierarchy, splits Stage 2 networking into `2-networking-a-fedramp-high` and `2-networking-b-il5-ngfw`, removes `module.kms` from `0-bootstrap`, and bumps minimum provider constraints to `>= 5.43.1`.
* **blueprints:** remove var.project and var.region in gcs-project and var.billing_account and var.organization in cnap ([35ba33a](https://github.com/google/stellar-engine/commit/35ba33a09ed42c08381249c31de0435b5967615f))
  * Removes `var.project` and `var.region` from `blueprints/il5/gcs-project` and removes `var.billing_account` and `var.organization` from `blueprints/networking/cnap` to deploy into existing stage-managed projects.


### Features

* **0-bootstrap:** implement CIS Google Cloud Platform Foundation Benchmark 1.x and 2.x IAM and logging controls ([f4b8fc4](https://github.com/google/stellar-engine/commit/f4b8fc49f5e961a751a64d0d2ac786f344a2a964))
  * Implements CIS Google Cloud Platform Foundation Benchmark 1.x and 2.x IAM separation of duties, KMS rotation, and audit logging controls across `fast/stages-aw/0-bootstrap` and workload blueprints to satisfy foundational compliance audit checks.
* **2-networking:** deploy Cloud Armor security policies, Access Context Manager perimeters, and Confidential Compute bastion hosts ([c2796d5](https://github.com/google/stellar-engine/commit/c2796d54c9aec5d64e37b9be0cd270abd2faa055))
  * Deploys Cloud Armor edge security policies, Access Context Manager service perimeters, and IAP-protected Confidential Compute bastion hosts in `blueprints/networking/cnap` to secure ingress into regulated application backends.
* **blueprints:** add Cloud Bigtable blueprint for FedRAMP High workloads ([bff7319](https://github.com/google/stellar-engine/commit/bff73191a64d66a2d4ed695def3c0d95b326eddb))
  * Adds `blueprints/fedramp-high/bigtable` to provision CMEK-encrypted Cloud Bigtable instances, clusters, and tables for FedRAMP High workloads.
* **blueprints:** add Cloud IDS intrusion detection blueprint with packet mirroring ([b93bdb6](https://github.com/google/stellar-engine/commit/b93bdb63a27eb2a4382d873ed3f2eebe95d24b1e))
  * Integrates Cloud IDS threat detection endpoints and VPC packet mirroring policies into `blueprints/networking/cnap` so ingress and east-west traffic is inspected for network intrusions.


### Bug Fixes

* **1-resman:** encrypt resource management state buckets with CMEK and grant KMS admin permissions to stage service accounts ([920c502](https://github.com/google/stellar-engine/commit/920c5028650661e433a79214a4cb12784d986c07))
  * Configures Customer-Managed Encryption Keys on Stage 1 Terraform state buckets and grants Cloud KMS admin permissions to stage automation service accounts.
* **2-networking:** dynamically generate NVA routes per environment subnet and standardize subnet naming across environments ([866e882](https://github.com/google/stellar-engine/commit/866e8826771eb89b21ed6b33a6dcf71c250cc1a6))
  * Dynamically generates NVA internal routes across environment subnets in `fast/stages-aw/2-networking-a-fedramp-high/nva.tf` so spoke networks route traffic through the network virtual appliances without hardcoded subnet indices.


## [1.0.2](https://github.com/google/stellar-engine/compare/v1.0.1...v1.0.2) (2024-09-24)


### Breaking Changes

* **0-bootstrap:** reorganize Stage 0 and Stage 1 resource hierarchy under a single top-level Assured Workloads folder ([5a7b8de](https://github.com/google/stellar-engine/commit/5a7b8de8a8939f361862f5edfacc22ee04690003))
  * Consolidates Stage 0 and Stage 1 folders and automation projects under a single top-level Assured Workloads folder in `fast/stages-aw/0-bootstrap` and `fast/stages-aw/1-resman` so all landing zone resources inherit the compliance regime boundary.
* **blueprints:** rename artifact-registry and postgresql directories, remove gcp-ce-security-onion, require var.keyring in gcs-project, remove output.self_link in bq-project, and drop legacy input variables across 10 IL5 blueprints ([2cd25e5](https://github.com/google/stellar-engine/commit/2cd25e58646f7bb95f6a756dfc269b12dd989e2f))
  * Renames `artifact-registies` to `artifact-registry` and `cloud-sql-postgres` to `postgresql`, removes `gcp-ce-security-onion`, requires `var.keyring` in `gcs-project`, removes `output.self_link` in `bq-project`, and standardizes input variables across 10 IL5 blueprints.


### Features

* **1-resman:** enforce CIS Google Cloud Platform Foundation Benchmark 3.0 and 4.x networking and compute security controls ([913fe60](https://github.com/google/stellar-engine/commit/913fe60781f53f3e819072ee598e01fff4aaaebe))
  * Enforces CIS Google Cloud Platform Foundation Benchmark 3.0 and 4.x networking and Compute Engine security controls across `blueprints/il5/*` and `fast/stages-aw/3-project-factory` to harden VM metadata, SSH access, and default network rules.
* **blueprints:** add Cloud Native Access Point blueprint with load balancer, IAP, and Cloud Armor edge protection ([d6caaba](https://github.com/google/stellar-engine/commit/d6caaba7ec499aaf2790156aa04ea6373a790952))
  * Adds `blueprints/networking/cnap` provisioning an external Application Load Balancer, Identity-Aware Proxy, Cloud Run backend, Access Context Manager policy, and Cloud Armor WAF policy for zero-trust application ingress.
* **blueprints:** enforce CIS Benchmark 6.2 database auditing and logging flags in Cloud SQL for PostgreSQL blueprint ([739a748](https://github.com/google/stellar-engine/commit/739a7482f04992cc73a3901158701806557117c6))
  * Enforces CIS Benchmark 6.2 PostgreSQL database flags (`log_connections`, `log_disconnections`, `log_error_verbosity`, `log_statement`, and `log_min_error_statement`) in `blueprints/il5/postgresql` so database connection and statement events are captured in Cloud Logging.
* **ci:** integrate tflint, Checkov, terraform fmt, and documentation verification into the CI pipeline ([052ccd5](https://github.com/google/stellar-engine/commit/052ccd5a1102da4d0b23529ae67e464608623d91))
  * Adds `tflint`, `checkov`, `terraform fmt`, and documentation verification jobs to `.gitlab-ci.yml`.


## [1.0.1](https://github.com/google/stellar-engine/compare/v1.0.0...v1.0.1) (2024-07-30)


### Features

* **blueprints:** add IL5 Dataflow streaming pipeline blueprint connecting Pub/Sub to BigQuery with CMEK encryption and dedicated VPC networking ([52d0295](https://github.com/google/stellar-engine/commit/52d02957614eea6495c40acbdf1e017537ec998d))
  * Adds `blueprints/il5/dataflow` to deploy a CMEK-encrypted Dataflow streaming pipeline reading from Pub/Sub and writing to BigQuery inside a dedicated VPC.


## [1.0.0](https://github.com/google/stellar-engine/compare/v0.9.0...v1.0.0) (2024-07-19)


### Breaking Changes

* **blueprints:** remove 0.0.0.0/0 CIDR defaults, var.subnet_name_1 in gke-project, and var.shielded_config in shielded-vm-project ([66056b0](https://github.com/google/stellar-engine/commit/66056b0d6e77b54ade214ce7b2ad93ac56ede7b4))
  * Removes `0.0.0.0/0` CIDR default values, replaces `var.subnet_name_1` in `blueprints/il5/gke-project`, and removes `var.shielded_config` in `blueprints/il5/shielded-vm-project` so callers must specify explicit ingress CIDRs and subnet names.


### Features

* **0-bootstrap:** merge organization policy templates with Cloud Foundation Fabric defaults and parameterize organization-scoped constraints ([67b26b8](https://github.com/google/stellar-engine/commit/67b26b8ebf1ba42add0867b511fbad43e2a92dc0))
  * Merges custom organization policy YAML templates with Cloud Foundation Fabric defaults in `fast/stages-aw/0-bootstrap/organization.tf` and parameterizes organization-scoped constraints so customer policy overrides do not discard baseline security rules.
* **2-networking:** align network firewall rules and subnet CIDR ranges with FedRAMP High compliance requirements ([48a4b75](https://github.com/google/stellar-engine/commit/48a4b753725311104562fd9614f5aa4bf0dfc78f))
  * Updates firewall rules, bastion settings, and NGFW subnet configurations in `fast/stages-aw/2-networking-f-ngfw` and `0-bootstrap` organization policies to satisfy FedRAMP High networking controls.
* **modules:** add Private Service Connect module from Cloud Foundation Fabric ([4487583](https://github.com/google/stellar-engine/commit/44875835298a1ae9433f5ee1daec9dae10a5aa7f))
  * Adds `modules/private-service-connect` to provision Private Service Connect endpoints and private Cloud DNS forwarding zones.


### Bug Fixes

* **ci:** add GitLab CI pipeline configuration for repository validation ([c08b392](https://github.com/google/stellar-engine/commit/c08b39241902e42b617af37010b48e8c5273f1d4))
  * Updates `.gitlab-ci.yml` to run automated repository validation checks in GitLab CI.


## [0.9.0](https://github.com/google/stellar-engine/compare/daily-2024.06.12...v0.9.0) (2024-06-28)


### Features

* **0-bootstrap:** provision Assured Workloads folder and enable Access Transparency in Stage 0 bootstrap ([a6f4a89](https://github.com/google/stellar-engine/commit/a6f4a8923c359e5b2c674afdcbf5ab9ea27d0718))
  * Provisions the top-level Assured Workloads folder and enables Access Transparency organization IAM bindings during Stage 0 bootstrap in `fast/stages-aw/0-bootstrap` so downstream stages deploy into a compliant Assured Workloads hierarchy.
* **blueprints:** add Artifact Registry blueprint with CMEK encryption and consumer VM startup configuration ([5ecc0e5](https://github.com/google/stellar-engine/commit/5ecc0e51713b6d8000a814b9c4babd056e4663b7))
  * Adds `blueprints/il5/artifact-registies` with HSM-backed Cloud KMS encryption and least-privilege service account bindings for container image repositories.
* **blueprints:** add Compute Engine bastion host pattern blueprint with IAP SSH firewall rules and existing tenant VPC lookup ([8a46b37](https://github.com/google/stellar-engine/commit/8a46b3797dc0a1b4014f16ea9309ff0bf57ef3f9))
  * Adds the Compute Engine bastion host pattern blueprint with IAP TCP forwarding firewall rules and removes deprecated `sourcerepo.googleapis.com` API activations across stages so administrators can connect to private VMs without public IP addresses.
* **blueprints:** add private GKE cluster blueprint with Shielded GKE Nodes, Dataplane V2, Binary Authorization, and HSM CMEK encryption ([2078cda](https://github.com/google/stellar-engine/commit/2078cdab25c3d0f65f737727b61733441b4e0559))
  * Adds `blueprints/il5/gke-project` to provision a private GKE cluster with Shielded GKE Nodes, Dataplane V2, Binary Authorization, and HSM-backed application-layer secret encryption.
* **blueprints:** add Security Onion intrusion detection blueprint on Compute Engine with HSM-backed CMEK encryption ([7d9cd1d](https://github.com/google/stellar-engine/commit/7d9cd1d0f25accc96b950b0f6c2a33735b801310))
  * Adds `blueprints/il5/gcp-ce-security-onion` to deploy a Security Onion network monitoring instance on Compute Engine with HSM-encrypted persistent disks.
* **blueprints:** add multi-subnet VPC peering blueprint with secondary CIDR range support ([56bb583](https://github.com/google/stellar-engine/commit/56bb583347f9580f62974a2610aed3fabee54801))
  * Adds `blueprints/il5/vpc-peering-project` supporting multi-subnet VPC network peering and secondary GKE pod and service CIDR ranges so tenant projects can peer with shared landing zone networks.


### Bug Fixes

* **0-bootstrap:** interpolate project IDs directly during initial bootstrap before projects exist in state ([69805fc](https://github.com/google/stellar-engine/commit/69805fcdf406621f086b572419734a8d4ca49ae4))
  * Removes a premature `data.google_project` lookup in `fast/stages-aw/2-networking-f-ngfw/ngfw.tf` that failed during initial bootstrap before target projects existed.
* **2-networking:** add management and us-east4 DMZ subnets and extend NGFW bootstrap readiness wait duration ([235b080](https://github.com/google/stellar-engine/commit/235b0809d2be9682d1a519f7261fd843a5e44bcd))
  * Extends the NGFW bootstrap readiness wait duration in `fast/stages-aw/2-networking-f-ngfw/ngfw.tf` and replaces personal sample project YAML files in `3-project-factory` with a single `sample-dev.yaml.sample` template so firewall appliances finish bootstrapping before dependent routes apply.
* **blueprints:** standardize Cloud KMS keys across IL5 blueprints to use HSM protection level ([8f48b2d](https://github.com/google/stellar-engine/commit/8f48b2dc6f163320413de8d03de5b59202990b9f))
  * Updates default Cloud KMS key configurations across `blueprints/il5/*` to use the `HSM` protection level required for IL5 workloads.


## [daily-2024.06.12](https://github.com/google/stellar-engine/compare/daily-2024.06.08...daily-2024.06.12) (2024-06-11)


### Features

* **0-bootstrap:** enable KMS encryption support and regional location configuration for Pub/Sub log sinks ([7868da2](https://github.com/google/stellar-engine/commit/7868da2402e3bfbb523bf87dba1a845ed2c88038))
  * Configures Cloud KMS encryption keys and regional location handling for Pub/Sub log export sinks in `fast/stages-aw/0-bootstrap/log-export.tf` so organization audit logs exported to Pub/Sub are encrypted with CMEK.
* **3-project-factory:** provision per-project tenant VPCs with peering to the landing zone and dynamic CIDR allocation ([7f0313b](https://github.com/google/stellar-engine/commit/7f0313b616df74df2c026587155a9195457a33d9))
  * Refactors `fast/stages-aw/3-project-factory/dev` to read project and VPC peering parameters directly from Terraform variables instead of external files.


### Bug Fixes

* **2-networking:** add tenant return routes on the NGFW Cloud Router and allow SSH ingress to the management bastion ([1960e8c](https://github.com/google/stellar-engine/commit/1960e8cb53167f128b1166443eea150d2461be3c))
  * Adds static return routes for `10.200.0.0/16` tenant subnets on the NGFW Cloud Router and adds management bastion SSH ingress rules in `fast/stages-aw/2-networking-f-ngfw` so return traffic reaches spoke workloads and operators can administer firewall appliances over IAP.


## [daily-2024.06.08](https://github.com/google/stellar-engine/compare/daily-2024.06.07...daily-2024.06.08) (2024-06-07)


### Features

* **blueprints:** add Cloud Pub/Sub blueprint with HSM-backed CMEK encryption and dedicated publisher and subscriber service accounts ([0486fd3](https://github.com/google/stellar-engine/commit/0486fd336d2e2c5211d989d85927d1c752cfcf93))
  * Adds `blueprints/il5/pub-sub-project` to provision Pub/Sub topics and subscriptions encrypted with HSM-backed Cloud KMS keys and dedicated publisher and subscriber service accounts.


## [daily-2024.06.07](https://github.com/google/stellar-engine/compare/daily-2024.06.04...daily-2024.06.07) (2024-06-06)


### Bug Fixes

* **blueprints:** refactor Compute Engine Shielded VM blueprint variable declarations and module wiring ([469904e](https://github.com/google/stellar-engine/commit/469904e49d42d20e0586229ebbd7b977dc420665))
  * Refactors variable declarations, module inputs, and `terraform.tfvars.sample` in `blueprints/il5/shielded-vm-project` so Compute Engine instance and disk encryption settings are configured through top-level variables.


## [daily-2024.06.04](https://github.com/google/stellar-engine/compare/daily-2024.05.24...daily-2024.06.04) (2024-06-03)


### Features

* **0-bootstrap:** support CMEK encryption keys and custom log filters for organization log sink destinations ([1421565](https://github.com/google/stellar-engine/commit/14215650e48c77cc67b8a0570e7acf8173d30a28))
  * Grants Cloud KMS decrypter and encrypter IAM bindings to logging service agents and supports custom log sink filters in `fast/stages-aw/0-bootstrap`.
* **2-networking:** add Palo Alto Networks Next-Generation Firewall stage with management bastion, Cloud NAT, and regional KMS encryption ([30cbc7a](https://github.com/google/stellar-engine/commit/30cbc7aba2421455e80531c841fab4990a3897fb))
  * Adds the Palo Alto Networks Next-Generation Firewall networking stage under `fast/stages-aw/2-networking-f-ngfw` with a management bastion, Cloud NAT, and regional KMS disk encryption to inspect north-south and east-west IL5 traffic.
* **blueprints:** add Compute Engine persistent disk blueprint with CMEK encryption and dedicated service account bindings ([d0bfcde](https://github.com/google/stellar-engine/commit/d0bfcde872d23dbda0596c8be5141493e49e4a1f))
  * Adds `blueprints/il5/compute-persistent-disk` to provision Compute Engine instances with CMEK-encrypted persistent disks and dedicated service accounts.


### Bug Fixes

* **2-networking:** configure default landing zone routes, health check firewall rules, and sensitive NGFW bootstrap password outputs ([e6e0076](https://github.com/google/stellar-engine/commit/e6e0076842abbf9d8e8591e47cdb64b6ef8dd0ec))
  * Configures default landing zone routes, load balancer health check firewall rules, and sensitive NGFW bootstrap password outputs in `fast/stages-aw/2-networking-f-ngfw` so appliance health probes succeed and bootstrap credentials are redacted from CLI output.


## [daily-2024.05.24](https://github.com/google/stellar-engine/compare/daily-2024.05.18...daily-2024.05.24) (2024-05-23)


### Features

* **blueprints:** add BigQuery project blueprint with CMEK-encrypted dataset provisioning and sample configuration ([dd9fae7](https://github.com/google/stellar-engine/commit/dd9fae7816000b53fd354edf12eaa6d81c40a702))
  * Adds `blueprints/il5/bq-project` to provision a project, Cloud KMS keyring, and CMEK-encrypted BigQuery dataset with sample `terraform.tfvars.sample` inputs.


### Bug Fixes

* **blueprints:** standardize BigQuery blueprint directory layout, module variable bindings, and deployment documentation ([13b8778](https://github.com/google/stellar-engine/commit/13b8778b5eff8fda112b8a60ddb55c769861b443))
  * Removes unused variable declarations in `blueprints/il5/bq-project/variables.tf` and aligns module inputs with the blueprint README so sample configurations plan cleanly.


## [daily-2024.05.18](https://github.com/google/stellar-engine/compare/daily-2024.04.24...daily-2024.05.18) (2024-05-17)


### Features

* **1-resman:** integrate Assured Workloads folder provisioning and CMEK state buckets at the tenant folder level ([d43db29](https://github.com/google/stellar-engine/commit/d43db297b39e6acc8314321cfe155a8ee3b17a90))
  * Integrates `modules/assured-workload` into `fast/stages-aw/1-resman` to create Assured Workloads folders per tenant compliance regime and encrypts Stage 1 state buckets with a `gcs` Cloud KMS key in `iac-core-0`.
* **3-project-factory:** configure initial tenant project definitions and IAM group bindings for IL5 workloads ([bd4e5f3](https://github.com/google/stellar-engine/commit/bd4e5f37bfb46b15d458665ab2869f4dc87539c6))
  * Adds IAM group bindings and sample configuration variables in `blueprints/il5/kms-project` and `fast/stages-aw/3-project-factory` for IL5 tenant workloads.
* **blueprints:** add Cloud KMS blueprint with CMEK keyring and key provisioning for IL5 projects ([96ee83c](https://github.com/google/stellar-engine/commit/96ee83c9ab1b452bc0cce88240572994a4fd2527))
  * Adds `blueprints/il5/kms-project` to provision dedicated Cloud KMS keyrings, HSM keys, and rotation schedules for IL5 projects.
* **blueprints:** add Cloud SQL for PostgreSQL blueprint with CMEK encryption ([5d69bd9](https://github.com/google/stellar-engine/commit/5d69bd98373476084ae28ac77b4115ddfc26f541))
  * Adds `blueprints/il5/postgresql` to provision a private-IP Cloud SQL for PostgreSQL instance encrypted with a Customer-Managed Encryption Key.
* **blueprints:** add Cloud Storage blueprint with private bucket defaults, CMEK encryption, and Autoclass support ([25863ed](https://github.com/google/stellar-engine/commit/25863edf7ca7f819c8e733ffcf182a5d192859cb))
  * Adds `blueprints/il5/gcs-project` to provision Cloud Storage buckets with uniform bucket-level access, public access prevention, CMEK encryption, and Autoclass lifecycle management.
* **blueprints:** add Compute Engine Shielded VM blueprint with hardened instance defaults and sample configuration ([4f26a18](https://github.com/google/stellar-engine/commit/4f26a18aa058eec61cdecc4364d3d8fded251442))
  * Adds `blueprints/il5/shielded-vm-project` to provision Shielded Compute Engine VMs with vTPM, integrity monitoring, Secure Boot, and CMEK-encrypted boot disks.


### Bug Fixes

* **1-resman:** place top-level tenant core project inside the IL5 Assured Workloads folder ([4a602b2](https://github.com/google/stellar-engine/commit/4a602b2f6ced1e3768d9a80b3f0480d819cf70de))
  * Updates `fast/stages-aw/1-resman/branch-tenants.tf` so the top-level tenant `core` project is created inside the tenant's IL5 Assured Workloads folder.
* **blueprints:** remove hardcoded project and email defaults and enforce explicit KMS module dependencies in Cloud Storage blueprint ([897df83](https://github.com/google/stellar-engine/commit/897df833140e67d5fa65ef15cbb25cb03652f891))
  * Removes hardcoded project ID and email default values in `blueprints/il5/gcs-project/variables.tf` so callers must supply explicit environment values.
* **tests:** adapt FAST stage unit test fixtures for fast/stages-aw ([b5110ad](https://github.com/google/stellar-engine/commit/b5110add18f165adbb415fcf048a96216db68386))
  * Clones and adapts FAST Stage 0 `tftest` unit test fixtures under `tests/fast/stages-aw/s0_bootstrap` so `fast/stages-aw` changes can be validated with `terraform test`.


## [daily-2024.04.24](https://github.com/google/stellar-engine/compare/daily-2024.04.23...daily-2024.04.24) (2024-04-23)


### Bug Fixes

* **0-bootstrap:** default sample organization location and storage region to US in terraform.tfvars.sample ([0ada075](https://github.com/google/stellar-engine/commit/0ada075e607c0cf1143cf0283a903a11691b0a0a))
  * Updates `fast/stages-aw/0-bootstrap/terraform.tfvars.sample` to default organization and storage locations to `US` and `us` so sample bootstrap deployments keep resources inside US regions.
* **0-bootstrap:** include bootstrap_user variable in the initial stage apply command and remove obsolete symlink instructions ([a0926c2](https://github.com/google/stellar-engine/commit/a0926c2999e5aa9822b46e4da9ac8e9ab9cbd600))
  * Includes `-var bootstrap_user=...` in the initial `terraform apply` command and removes obsolete symlink instructions in `fast/stages-aw/0-bootstrap/README.md` so first-time operators pass required bootstrap identity inputs.
* **fast:** document gcloud config set project prerequisites across 1-resman, 2-networking, and 2-security stage READMEs ([c3c0190](https://github.com/google/stellar-engine/commit/c3c019085f755aa741c89d97bd5aad637a989b91))
  * Adds `gcloud config set project` prerequisite steps to the table of contents and deployment instructions in `fast/stages-aw/1-resman`, `2-networking-c-nva`, and `2-security` READMEs.


## [daily-2024.04.23](https://github.com/google/stellar-engine/compare/0494d36...daily-2024.04.23) (2024-04-23)


### Features

* **0-bootstrap:** document bootstrap service account IAM permission requirements ([7b9f013](https://github.com/google/stellar-engine/commit/7b9f013317827f8239f81a9bd4a45a23f78c26e7))
  * Documents required organization and folder IAM permissions for stage automation service accounts in `fast/stages-aw/1-resman`, `2-networking-c-nva`, and `2-security` READMEs so operators grant prerequisite roles before running Terraform.
* **fast:** initialize Assured Workloads stages under fast/stages-aw and default regions to US locations ([997ba85](https://github.com/google/stellar-engine/commit/997ba85f90642e1c391b5aab50e855b221ab1ceb))
  * Initializes the Assured Workloads stage hierarchy under `fast/stages-aw/` and updates default subnet and resource regions from European locations to `us-east1` and `us-east4`.


### Bug Fixes

* **fast:** prune unused networking and project factory stage variants from fast/stages-aw ([a7882c0](https://github.com/google/stellar-engine/commit/a7882c0efcc82fb1a39f814be8a844f3981a04f4))
  * Removes unused upstream `3-data-platform`, `3-gke-multitenant`, and `3-secops` stage directories from `fast/stages-aw/` so the repository contains only Assured Workloads stages.
* **fast:** replace cross-stage file symlinks with direct stage configurations and document Terraform version constraints ([e7be33a](https://github.com/google/stellar-engine/commit/e7be33abad805b17039ea4a52bdd92ad433cfe4a))
  * Replaces broken cross-stage file symlinks in `fast/stages-aw/` with direct stage configuration files and documents Terraform version constraints in stage READMEs so stages can be cloned and initialized across platforms.
