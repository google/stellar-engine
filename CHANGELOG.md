# Changelog


## [4.2.0](https://github.com/google/stellar-engine/compare/v4.1.0...v4.2.0) (2026-10-17)


### Breaking Changes

* **gemini-enterprise:** relocate blueprint to blueprints/gemini-enterprise, remove us-regimes and experimental regime options, and remove var.auto_delete in bigtable ([#279](https://github.com/google/stellar-engine/issues/279)) ([22ca406](https://github.com/google/stellar-engine/commit/22ca406e867289f2e0738f0c8f6ed79372bdbd91))


### Features

* **gemini-enterprise:** add BigQuery datastore import and license retract/assign subcommands ([#280](https://github.com/google/stellar-engine/issues/280)) ([c6eafa9](https://github.com/google/stellar-engine/commit/c6eafa9f0c607a8ab60f636efa4e4854cb2508c5))
* **gemini-enterprise:** harden Brownfield CMEK discovery, identity checks, and Stage 1 VPC and SSL ([#281](https://github.com/google/stellar-engine/issues/281)) ([85efc5f](https://github.com/google/stellar-engine/commit/85efc5f3a8e0433edf8cf3fd30b39a9af3b8ec3d))
* **gemini-enterprise:** relocate blueprint and add multi-regime compliance support ([#279](https://github.com/google/stellar-engine/issues/279)) ([22ca406](https://github.com/google/stellar-engine/commit/22ca406e867289f2e0738f0c8f6ed79372bdbd91))


### Bug Fixes

* **0-bootstrap:** resolve logging circular dependency in bootstrap ([#278](https://github.com/google/stellar-engine/issues/278)) ([ae0838f](https://github.com/google/stellar-engine/commit/ae0838fccf0063120e0d13b1febf8279546a0d64))
* **modules:** fix IAM key delimiters, log filters, and conditions in custom modules ([#275](https://github.com/google/stellar-engine/issues/275)) ([c4f60fb](https://github.com/google/stellar-engine/commit/c4f60fb7207ac03803cb1a9c19237d8cbc8250cd))
* **security:** harden IAM conditions, Terraform modules, FAST stages, and blueprints ([#274](https://github.com/google/stellar-engine/issues/274)) ([c7353a3](https://github.com/google/stellar-engine/commit/c7353a3991d1e2fedf065f2fb3588c8e10dc5779))


## [4.1.0](https://github.com/google/stellar-engine/compare/v4.0.1...v4.1.0) (2026-09-28)


### Features

* **fast:** surface stage IAM impersonation context and stale env warnings ([#264](https://github.com/google/stellar-engine/issues/264)) ([7f35560](https://github.com/google/stellar-engine/commit/7f3556091ade0c045d4b55614aecf2842fc355f6))
* **scripts:** add Windows shell pre-flight check and WSL2 documentation ([#263](https://github.com/google/stellar-engine/issues/263)) ([5cd0bf2](https://github.com/google/stellar-engine/commit/5cd0bf26cadd93156c26d8c7bb158e7a956fd5da))


### Bug Fixes

* **0-bootstrap:** fix org policy parameter encoding and provision logging CMEK settings ([#268](https://github.com/google/stellar-engine/issues/268)) ([13e2e87](https://github.com/google/stellar-engine/commit/13e2e87d2114d473841c1e8c1a3787efe4414bbe))
* **0-bootstrap:** order folders and projects after organization logging settings ([#262](https://github.com/google/stellar-engine/issues/262)) ([b8da03f](https://github.com/google/stellar-engine/commit/b8da03f577cfefcf9d66218c4ac3177024d07fe1))
* **2-networking:** fix NVA routing, Spot default, firewall policy prefix, and peering stagger ([#269](https://github.com/google/stellar-engine/issues/269)) ([f43b0a1](https://github.com/google/stellar-engine/commit/f43b0a143c3ec005ab216c7059a81d9b3d35cfc8))
* **blueprints:** enable required service APIs and enforce 30-char ID preconditions ([#271](https://github.com/google/stellar-engine/issues/271)) ([33be48b](https://github.com/google/stellar-engine/commit/33be48b942a142d48ed3e86ea30b6c537d135032))
* **deploy.sh:** match storage_viewer's real role ID and reject an invalid Stage 2 choice ([#243](https://github.com/google/stellar-engine/issues/243)) ([397fc2e](https://github.com/google/stellar-engine/commit/397fc2ee6b3c1a61b799fe6a627d5821a81de3dc))
* **fast:** pass terraform validate output via env in github-script ([#260](https://github.com/google/stellar-engine/issues/260)) ([6689e2a](https://github.com/google/stellar-engine/commit/6689e2a53f16b6254b61f3f6e8535b01a8fbeaf1))
* **gemini-enterprise:** enforce compliance settings, validate API patches, and improve deploy script ([#270](https://github.com/google/stellar-engine/issues/270)) ([a48e0ed](https://github.com/google/stellar-engine/commit/a48e0ed36f149db6a9295e7c6dd7bd1bb26677a0))


## [4.0.1](https://github.com/google/stellar-engine/compare/v4.0.0...v4.0.1) (2026-09-18)


### Bug Fixes

* **deploy.sh:** remove kms_project_id and us_keyring_name from gemini-stage-0 tfvars ([#234](https://github.com/google/stellar-engine/issues/234)) ([d843aec](https://github.com/google/stellar-engine/commit/d843aec5243d0207c048df819084b80babe307e1)), closes [#229](https://github.com/google/stellar-engine/issues/229)
* **kms:** use regime-aware local for kms_protection_level and propagate to downstream stages ([#233](https://github.com/google/stellar-engine/issues/233)) ([a307933](https://github.com/google/stellar-engine/commit/a307933b199d83e678cdc393eb4dbcf9ae18e56c))


## [4.0.0](https://github.com/google/stellar-engine/compare/v3.0.0...v4.0.0) (2026-09-10)


### Breaking Changes

* **2-networking-a-fedramp:** follow the 2-networking-a-fedramp directory rename ([#214](https://github.com/google/stellar-engine/issues/214)) ([dca2f72](https://github.com/google/stellar-engine/commit/dca2f7259283c9e8353cfd2cbf16bc08818bfa36))
* **3-security,postgresql:** remove unused variables and require common_services_folder, envs_folders, regions, and tenant_accounts in 3-security ([#207](https://github.com/google/stellar-engine/issues/207)) ([5949fa7](https://github.com/google/stellar-engine/commit/5949fa7ecd1e4cfc11910df2befdc7153b985a86))
* **gemini-enterprise:** remove kms_project_id and us_keyring_name from Stage 0 variables ([#210](https://github.com/google/stellar-engine/issues/210)) ([7a32639](https://github.com/google/stellar-engine/commit/7a3263937def0e43167d0fc351fb96954d1a057c))


### Features

* **fast:** introduce configurable force_destroy for GCS buckets and enable NGFW bucket versioning ([#226](https://github.com/google/stellar-engine/issues/226)) ([6d7d08c](https://github.com/google/stellar-engine/commit/6d7d08c0997b9aea19d9866434dfc2bc5a5ecbc5)), closes [#56](https://github.com/google/stellar-engine/issues/56)


### Bug Fixes

* **0-bootstrap:** correct default log retention ([#218](https://github.com/google/stellar-engine/issues/218)) ([61fd227](https://github.com/google/stellar-engine/commit/61fd227d626ecfc96ab3d9f0b2956387d5b1725e))
* **0-bootstrap:** declare billing_override, fix the assured_workload output, align the prefix limit ([#213](https://github.com/google/stellar-engine/issues/213)) ([1ce9c3f](https://github.com/google/stellar-engine/commit/1ce9c3f30d6516ea6c397d35a3e369897472899e))
* **0-bootstrap:** fix Assured Workloads folder resolution, CMEK logging buckets, and KMS IAM bindings ([#220](https://github.com/google/stellar-engine/issues/220)) ([f78ddd2](https://github.com/google/stellar-engine/commit/f78ddd241b961a6bf1f69d15625a2895467709d4))
* **0-bootstrap:** take the organization id explicitly in import.sh ([#215](https://github.com/google/stellar-engine/issues/215)) ([76443c9](https://github.com/google/stellar-engine/commit/76443c994fc33ac62d5fd2808386f73cff043743))
* **1-resman:** update 1-resman tfvars sample to align with TDD example ([#78](https://github.com/google/stellar-engine/issues/78)) ([fb15e61](https://github.com/google/stellar-engine/commit/fb15e6155f448139ab6d9ccc61b1465148c4e9c7))
* **2-networking-a-fedramp:** encrypt NVA boot disk with the vdss KMS key ([#211](https://github.com/google/stellar-engine/issues/211)) ([1b0aa34](https://github.com/google/stellar-engine/commit/1b0aa3425bad7182d782948973cbca752d2bbfb2)), closes [#193](https://github.com/google/stellar-engine/issues/193)
* **2-networking-a-fedramp:** validate proxy_subnets and tenant subnets up front ([#216](https://github.com/google/stellar-engine/issues/216)) ([29715f2](https://github.com/google/stellar-engine/commit/29715f206784ab8599fcfed3378f4b25655ae549))
* **3-security:** apply kms_protection_level to keys that set no version_template ([#212](https://github.com/google/stellar-engine/issues/212)) ([ec82b55](https://github.com/google/stellar-engine/commit/ec82b554261054a7a0eff6d8d10e6633ed93e4ca))
* **cloudsql-instance:** always emit disabled psc_config ([#200](https://github.com/google/stellar-engine/issues/200)) ([fa14625](https://github.com/google/stellar-engine/commit/fa14625ed8d7e5cf577bcec399c5658d271f3206))
* **deploy.sh:** initialise ENABLE_MODEL_ARMOR_FLAG so IL4/IL5 don't abort on an empty jq argument ([#204](https://github.com/google/stellar-engine/issues/204)) ([68cf596](https://github.com/google/stellar-engine/commit/68cf5961baad865d642cbf1713a66d42f18ca6ee))
* **deploy.sh:** remove false Assured Workload validation confirmation ([#221](https://github.com/google/stellar-engine/issues/221)) ([9578437](https://github.com/google/stellar-engine/commit/9578437bd83d8e9894343630861176dec31ca581)), closes [#134](https://github.com/google/stellar-engine/issues/134)
* **deploy.sh:** replace instead of append gemini_apps assignment ([#223](https://github.com/google/stellar-engine/issues/223)) ([87d1efb](https://github.com/google/stellar-engine/commit/87d1efbde22ff2f05f89f5c26bf1fe991b35a830)), closes [#178](https://github.com/google/stellar-engine/issues/178)
* **deploy.sh:** set COMPLIANCE_REGIME=NONE for regime option 4 instead of leaving it empty ([#203](https://github.com/google/stellar-engine/issues/203)) ([36f7651](https://github.com/google/stellar-engine/commit/36f7651193d67c779f7717bd03b68a694f5d7991))
* **discovery-engine:** grant Discovery Engine service agent objectViewer on corpus bucket ([#219](https://github.com/google/stellar-engine/issues/219)) ([69b9a58](https://github.com/google/stellar-engine/commit/69b9a582ba6d2a142ce41ea3056bd863377238e7)), closes [#145](https://github.com/google/stellar-engine/issues/145)
* **gem4gov:** name disableAnalytics in the engine updateMask so update-compliance applies it ([#201](https://github.com/google/stellar-engine/issues/201)) ([6afb24a](https://github.com/google/stellar-engine/commit/6afb24aa691a4dcfb8a9ee20c34c96617298425d))
* **gem4gov:** stop update-compliance stripping the Model Armor binding from customerPolicy ([#205](https://github.com/google/stellar-engine/issues/205)) ([45fe5d3](https://github.com/google/stellar-engine/commit/45fe5d34e7202fc5a24673ba078b36ab88bbd906))
* **gemini-enterprise:** align stage-0 tfvars sample and make stage-1 internal subnet lookup configurable ([#209](https://github.com/google/stellar-engine/issues/209)) ([1b1bb1a](https://github.com/google/stellar-engine/commit/1b1bb1ae70fec187d70dc349a1ffb0762e6e53e5))
* **gemini-enterprise:** clean up dead variables, redundant CLI definitions, and prompt wording ([#206](https://github.com/google/stellar-engine/issues/206)) ([d7d47e0](https://github.com/google/stellar-engine/commit/d7d47e0602d03dc1ce435ac11785af38234988fd))
* **gemini-enterprise:** parse hyphenated tenant ids and the FAST tenant bucket name in brownfield discovery ([#217](https://github.com/google/stellar-engine/issues/217)) ([60a8138](https://github.com/google/stellar-engine/commit/60a813873e67b0a26f42c0a4cd417f99298c77a5))
* **gemini-enterprise:** resolve stage-0 teardown, internal VIP sharing, and access day bounds ([#225](https://github.com/google/stellar-engine/issues/225)) ([2bec226](https://github.com/google/stellar-engine/commit/2bec226eb6c29f49fc19ee987df3a0a4d12ec786)), closes [#174](https://github.com/google/stellar-engine/issues/174) [#185](https://github.com/google/stellar-engine/issues/185) [#186](https://github.com/google/stellar-engine/issues/186)
* **gemini-stage-0:** enable modelarmor.googleapis.com so terraform apply doesn't fail on a disabled API ([#202](https://github.com/google/stellar-engine/issues/202)) ([c0caf46](https://github.com/google/stellar-engine/commit/c0caf4635042650cd7e73633e11f7a9277e97889))
* **load_balancer:** guard keys() indexing against empty gemini_apps map ([#224](https://github.com/google/stellar-engine/issues/224)) ([2ad56c2](https://github.com/google/stellar-engine/commit/2ad56c218d21f703f1ce4738c852812823197fbe)), closes [#181](https://github.com/google/stellar-engine/issues/181)
* **org-policies,docs:** add essential contacts policy parameters and document blueprint deployer permissions ([#210](https://github.com/google/stellar-engine/issues/210)) ([7a32639](https://github.com/google/stellar-engine/commit/7a3263937def0e43167d0fc351fb96954d1a057c))
* **quality:** resolve CodeQL unused local variables and add Python and shell test suites ([#222](https://github.com/google/stellar-engine/issues/222)) ([ed9adbf](https://github.com/google/stellar-engine/commit/ed9adbff347626bc0937932f6bb8f2dedf4c032d))
* **stages,blueprints:** document 3-security KMS opt-in behavior and update postgresql PSA requirements ([#208](https://github.com/google/stellar-engine/issues/208)) ([df47667](https://github.com/google/stellar-engine/commit/df47667dd9aa11268df867b82de8cec7042c12b5))


## [3.0.0](https://github.com/google/stellar-engine/compare/v2.13.0...v3.0.0) (2026-08-10)


### Breaking Changes

* **fast:** rename fast/stages-aw/2-networking-a-fedramp-high to fast/stages-aw/2-networking-a-fedramp and add FedRAMP Moderate support ([#162](https://github.com/google/stellar-engine/issues/162)) ([7033b8c](https://github.com/google/stellar-engine/commit/7033b8cc975ee929c5cd961e0a2b96d284669bca))


### Features

* **compute-mig:** expose instance_lifecycle_policy for managed instance group auto-healing repairs ([#97](https://github.com/google/stellar-engine/issues/97)) ([5cf518a](https://github.com/google/stellar-engine/commit/5cf518a4ff7918e541af8dc9b19a4367e37f0d26))
* **net-lb-app-ext-regional:** add strong session affinity cookie support on regional external application load balancers ([#96](https://github.com/google/stellar-engine/issues/96)) ([ce3cb01](https://github.com/google/stellar-engine/commit/ce3cb01491b6d9ade58da8a649c6f10112e7f2a7))


### Bug Fixes

* **ci:** introduce automated Terraform formatting, linting, and security scanning workflow ([#172](https://github.com/google/stellar-engine/issues/172)) ([db567c1](https://github.com/google/stellar-engine/commit/db567c1bb4bd586edc98c6c65544a2b1b7cb2613))
* **deploy.sh:** enable Cloud Identity and Vertex AI APIs automatically during deployment ([#163](https://github.com/google/stellar-engine/issues/163)) ([c47be72](https://github.com/google/stellar-engine/commit/c47be72bfc4283d1e2b1132e4be83317d8354d93))
* **docs:** centralize deployment prerequisites, relocate naming convention guide under docs/, and update READMEs for FedRAMP Moderate ([#173](https://github.com/google/stellar-engine/issues/173)) ([f64ce6c](https://github.com/google/stellar-engine/commit/f64ce6cd116fa6ecf5f96c8ba99fc44aafa3411e))
* **gem4gov:** use testIamPermissions instead of getIamPolicy in check_roles to support group-inherited IAM bindings ([#166](https://github.com/google/stellar-engine/issues/166)) ([5f672e3](https://github.com/google/stellar-engine/commit/5f672e3cb02b57694c5ab5f21d87623a5a0971d4))


## [2.13.0](https://github.com/google/stellar-engine/compare/v2.12.0...v2.13.0) (2026-07-31)


### Breaking Changes

* **gemini-enterprise:** remove var.gemini_config_id from Stage 1 and provision Gemini Enterprise applications via Terraform ([#150](https://github.com/google/stellar-engine/issues/150)) ([0068ff7](https://github.com/google/stellar-engine/commit/0068ff7c663641b6ea1f8e4ff926efff2b0e3d95))


### Features

* **0-bootstrap:** add optional billing account budgets for the Assured Workloads folder ([bce87f8](https://github.com/google/stellar-engine/commit/bce87f84b1fadbe033c158e7359ad10f31193738))
* **ci:** add automated monthly minor release workflow and release cadence documentation ([#165](https://github.com/google/stellar-engine/issues/165)) ([8f5b67a](https://github.com/google/stellar-engine/commit/8f5b67a69686f0300d9a73662e890222f88b271d))
* **gemini-enterprise:** configure Model Armor for FedRAMP High deployments ([#150](https://github.com/google/stellar-engine/issues/150)) ([0068ff7](https://github.com/google/stellar-engine/commit/0068ff7c663641b6ea1f8e4ff926efff2b0e3d95))


### Bug Fixes

* **0-bootstrap:** default organization log sinks to Cloud Logging buckets with a configurable 365-day retention period for regulatory compliance ([#127](https://github.com/google/stellar-engine/issues/127)) ([2dc67ca](https://github.com/google/stellar-engine/commit/2dc67cacdeccc20604c94ff13f8855fa280af97f))
* **docs:** add ATO compliance reference artifacts, network architecture diagrams, and Stage 3 audit logging guidance in the Detailed Deployment Guide ([#130](https://github.com/google/stellar-engine/issues/130)) ([a08441e](https://github.com/google/stellar-engine/commit/a08441ed8ab26de6b018761c3e9f5f010f46140f))
* **gem4gov:** handle existing CMEK keys gracefully during Gemini Enterprise onboarding ([0c0b9eb](https://github.com/google/stellar-engine/commit/0c0b9eba7af2b7c03c95b612e59e0146d8ed4d91))


## [2.12.0](https://github.com/google/stellar-engine/compare/v2.11.0...v2.12.0) (2026-06-22)


### Breaking Changes

* **fast:** replace data/cidrs.yaml networking file inputs with var.cidrs in tfvars ([#66](https://github.com/google/stellar-engine/issues/66)) ([429ab04](https://github.com/google/stellar-engine/commit/429ab04de782463ac28375d6207b76827bd100a0))


### Features

* **0-bootstrap:** allow custom parameters on managed organization policy constraints ([#93](https://github.com/google/stellar-engine/issues/93)) ([606979f](https://github.com/google/stellar-engine/commit/606979f69ceb4c203045815fd5e5151b92988a4a))
* **docs:** add incident response runbook template and align naming convention documentation with Detailed Deployment Guide ([#84](https://github.com/google/stellar-engine/issues/84)) ([5746192](https://github.com/google/stellar-engine/commit/5746192a74668375fe8d52b77cd5f5be1ec31065))
* **fast:** support dynamic tenant networking and add billing account overrides ([#66](https://github.com/google/stellar-engine/issues/66)) ([429ab04](https://github.com/google/stellar-engine/commit/429ab04de782463ac28375d6207b76827bd100a0))


### Bug Fixes

* **0-bootstrap:** deprivilege bootstrap default service accounts and default regions variable to us-east4 when unspecified ([a13b69e](https://github.com/google/stellar-engine/commit/a13b69ec998e65715de34412f526accfaad56832))
* **2-networking:** update local.cidr_ranges to read from var.cidrs instead of deprecated YAML configuration ([#77](https://github.com/google/stellar-engine/issues/77)) ([f25a895](https://github.com/google/stellar-engine/commit/f25a895b6e6e57ac9c8519055f7de83f9ed8e8af))
* **gitlab:** verify GitLab package installation script checksums ([#74](https://github.com/google/stellar-engine/issues/74)) ([e12f2d4](https://github.com/google/stellar-engine/commit/e12f2d4f1049af879b072968f12fd0746f3af8a7))


## [2.11.0](https://github.com/google/stellar-engine/compare/v2.10.0...v2.11.0) (2026-06-02)


### Breaking Changes

* **gemini-enterprise:** remove var.gcs_data_store_names, var.user_group, and six legacy datastore and CMEK outputs from Stage 0 ([bb53825](https://github.com/google/stellar-engine/commit/bb5382589b20aa6cdb2ac2756f323adae45fa17c))
* **net-lb-app-ext:** stop forcing a default port_name on backend services when unset ([#25](https://github.com/google/stellar-engine/issues/25)) ([aae379a](https://github.com/google/stellar-engine/commit/aae379a1829c716eb262b77b9361b6f47750cab1))


### Features

* **alloydb:** add read pool instance configuration support to AlloyDB module ([#16](https://github.com/google/stellar-engine/issues/16)) ([6606345](https://github.com/google/stellar-engine/commit/6606345746dc167ae97ee469eef1108b844757bd))
* **cloudsql-instance:** allow overriding machine tier per read replica ([#28](https://github.com/google/stellar-engine/issues/28)) ([77f1953](https://github.com/google/stellar-engine/commit/77f1953b055e143df820e00897de3d2696c869cd))
* **cloudsql-instance:** expose retain_backups_on_delete option on primary and replica instances ([#27](https://github.com/google/stellar-engine/issues/27)) ([d1c1e3e](https://github.com/google/stellar-engine/commit/d1c1e3e1894483d2e6a151a120915ac713f67ee8))
* **docs:** add incident response runbooks for compromised IAM credentials, compute compromise, CMEK compromise, network intrusion, and VPC-SC violations ([d66ed6d](https://github.com/google/stellar-engine/commit/d66ed6dac85782aebce2b8e56c10c9686e3c00e3))
* **gem4gov:** add IL5 compliance regime support and enterprise license management commands ([7c7e133](https://github.com/google/stellar-engine/commit/7c7e13392af024fc1b99cf8525b14285c89011e9))
* **gemini-enterprise:** add BigQuery usage analytics dashboard and partitioned audit logging sink views within Assured Workloads boundaries ([751b7ab](https://github.com/google/stellar-engine/commit/751b7ab4156d965b232a2ef4741de92fe73aff51))
* **net-lb-app-ext-regional:** support regional Internet network endpoint groups on external application load balancers ([#26](https://github.com/google/stellar-engine/issues/26)) ([5e33c0b](https://github.com/google/stellar-engine/commit/5e33c0bdd3e1b905214e70726c3de740c0244207))


### Bug Fixes

* **0-bootstrap:** deprivilege bootstrap default service accounts ([#68](https://github.com/google/stellar-engine/issues/68)) ([2a36067](https://github.com/google/stellar-engine/commit/2a36067d3cdf68d4ed701ab04b51d3e15fecd340))
* **docs:** audit and format documentation for public release, refresh Detailed Deployment Guide to v2.9.1, and simplify gcloud service enablement commands ([#76](https://github.com/google/stellar-engine/issues/76)) ([317c358](https://github.com/google/stellar-engine/commit/317c358b7ba1cbf96d7b72ca8e118021a6ea3f07))
* **gemini-enterprise:** support load-balancer-free deployment mode, Certificate Manager SSL, state hydration in deploy.sh, and principalSubject audit log capture ([bb53825](https://github.com/google/stellar-engine/commit/bb5382589b20aa6cdb2ac2756f323adae45fa17c))
* **gitlab:** verify GitLab package installation script integrity before execution ([#74](https://github.com/google/stellar-engine/issues/74)) ([68684fd](https://github.com/google/stellar-engine/commit/68684fd631bd2483000592745080caa5fb433430))
* **repo:** update GitHub issue and pull request templates and apply code quality fixes ([#23](https://github.com/google/stellar-engine/issues/23)) ([0a5939e](https://github.com/google/stellar-engine/commit/0a5939e2b88177faecafe1921eee696b588eee6e))


## [2.10.0](https://github.com/google/stellar-engine/compare/v2.9.3...v2.10.0) (2026-03-13)


### Breaking Changes

* **0-bootstrap:** remove var.workforce_identity_providers, var.workload_identity_providers, and google_iam_workforce_pool_provider.default and delete modules/__experimental_deprecated ([#25](https://github.com/google/stellar-engine/issues/25)) ([114141a](https://github.com/google/stellar-engine/commit/114141ac8b249592fee2e64c52d17fa4fbe66bb0))


### Features

* **blueprints:** parameterize snapshot retention policies and compute boot images across blueprints ([63fe276](https://github.com/google/stellar-engine/commit/63fe276b3e758b90f754e176c8b45022c48e5c0f))
* **scripts:** enhance deployment and destruction scripts with shared helper utilities, race-condition fixes, and safety validations ([#18](https://github.com/google/stellar-engine/issues/18)) ([1892784](https://github.com/google/stellar-engine/commit/1892784a5039c11f468ef43b5d67a8b7e2d4b307))


### Bug Fixes

* **0-bootstrap:** skip custom organization policy import during initial bootstrap, remove invalid gcp.accessTransparency.enforcement constraint, and set structural org policy root_node ([0d3f83c](https://github.com/google/stellar-engine/commit/0d3f83cb140eac2143bb1e58c9e89a040cb640ea))
* **2-networking:** default custom firewall rule logging to INCLUDE_ALL_METADATA across stages and blueprints ([3704dfa](https://github.com/google/stellar-engine/commit/3704dfa6e90d4b3dc335440b1f598ac9e03695c1))
* **docs:** add Code of Conduct and relocate CONTRIBUTING.md under docs/ ([#16](https://github.com/google/stellar-engine/issues/16)) ([161e0a9](https://github.com/google/stellar-engine/commit/161e0a9d886b93c825daac45a5cd8ee7ed50e114))
* **gem4gov:** update Discovery Engine datastore creation for collections API path and BigQuery schemas ([#22](https://github.com/google/stellar-engine/issues/22)) ([e6d9db7](https://github.com/google/stellar-engine/commit/e6d9db7a1c19c8eb9d6438e6833f6204ccc66c29))
* **gemini-enterprise:** refine Access Context Manager device policy access levels and deployment script prompts ([#17](https://github.com/google/stellar-engine/issues/17)) ([7bc9f3b](https://github.com/google/stellar-engine/commit/7bc9f3bd9e30e18d68d7f740339a48586f418f17))
* **security:** harden IAM conditions, storage encryption, compute defaults, networking controls, and logging configurations across stages and blueprints ([#25](https://github.com/google/stellar-engine/issues/25)) ([114141a](https://github.com/google/stellar-engine/commit/114141ac8b249592fee2e64c52d17fa4fbe66bb0))


## [2.9.3](https://github.com/google/stellar-engine/compare/v2.9.2...v2.9.3) (2025-12-17)


### Breaking Changes

* **gemini-enterprise:** remove var.gcs_label_environment in Stage 0 and replace Stage 1 manual project and policy inputs with required var.gemini_enterprise_domain and remote state lookups ([#14](https://github.com/google/stellar-engine/issues/14)) ([ce7b94b](https://github.com/google/stellar-engine/commit/ce7b94bf722272f0858c6d6a3bf11b2960d6701f))


### Features

* **gem4gov:** introduce gem4gov-cli for Gemini Enterprise onboarding, identity provider configuration, and modular datastore management ([#6](https://github.com/google/stellar-engine/issues/6)) ([be7c12f](https://github.com/google/stellar-engine/commit/be7c12f3f1cb13219596aa8f602507ed8d6c09a3))
* **gemini-enterprise:** implement greenfield and brownfield deployment modes with Shared VPC, multi-region US CMEK, and Workforce Identity Federation support ([#5](https://github.com/google/stellar-engine/issues/5)) ([070cc4e](https://github.com/google/stellar-engine/commit/070cc4ec1b3c62ecc61d5f148593cadc2366bea3))


### Bug Fixes

* **docs:** add CONTRIBUTING.md, Apache 2.0 license headers, and reorganized OSS VRP documentation ([#9](https://github.com/google/stellar-engine/issues/9)) ([46a9c1f](https://github.com/google/stellar-engine/commit/46a9c1f4508387a8b4db4c062fce631f40a97f52))
* **gemini-enterprise:** add prefix discovery, state bucket reading, and graceful Terraform failure handling in deploy.sh ([#8](https://github.com/google/stellar-engine/issues/8)) ([833317b](https://github.com/google/stellar-engine/commit/833317bed61721902402c315a0fee374846ac4d7))


## [2.9.2](https://github.com/google/stellar-engine/compare/v2.9.1...v2.9.2) (2025-11-12)


### Breaking Changes

* **fast:** remove hardcoded us-east4 defaults, require var.regions in Stage 2 networking, and remove var.locations in 1-resman ([78e71ac](https://github.com/google/stellar-engine/commit/78e71aca46560b286bb50ae1a9e736361832454a))
* **blueprints:** replace var.create_topic, var.new_topic_name, and var.region in cloud-scheduler-job with required var.topic_id ([2048bde](https://github.com/google/stellar-engine/commit/2048bded2fa8d1042f32c7e17623237193341eb1))


### Features

* **gemini-enterprise:** add two-stage Gemini Enterprise blueprint with Vertex AI Discovery Engine, regional internal load balancer, and Google Workspace IAM integration ([582e30e](https://github.com/google/stellar-engine/commit/582e30eb1131e0f3a7c06d2ca17ea8e0f403e368))


### Bug Fixes

* **3-security:** add Stage 3 security validation script ([5ee81eb](https://github.com/google/stellar-engine/commit/5ee81ebd95e4f385e5e44a9bb444741dd4adf73f))
* **blueprints:** align Cloud Armor WAF rules with preconfigured security best practices ([2048bde](https://github.com/google/stellar-engine/commit/2048bded2fa8d1042f32c7e17623237193341eb1))
* **docs:** add Apache 2.0 license headers, OSS VRP exclusion notice, CONTRIBUTING.md, and GEMINI.md contributor guidelines ([fb14045](https://github.com/google/stellar-engine/commit/fb14045f2fc26485734a6557c13dbe1038588810))


## [2.9.1](https://github.com/google/stellar-engine/compare/v2.9.0...v2.9.1) (2025-09-19)


### Breaking Changes

* **1-resman:** remove tenant-core-folders and tenant-self-folders modules and drop var.tag_names and var.tags ([f667c1c](https://github.com/google/stellar-engine/commit/f667c1c36f645bb0032880c784de6cb074045ec6))
* **blueprints:** replace gke-project, logging, and vpc-peering-project blueprints, decouple inline KMS creation across 7 IL5 blueprints, and require var.kms_key_name in bigtable ([2f91cb2](https://github.com/google/stellar-engine/commit/2f91cb2d67926b8ec5a60f4170728d647e08841f))


### Features

* **blueprints:** add BeyondCorp Application Protection, GKE standard, GKE hardened, and GKE GitOps blueprints ([fd74626](https://github.com/google/stellar-engine/commit/fd74626e568330d0657eeb9ff36d0c4e38855ea1))
* **scripts:** add automated deployment, teardown, and redeployment orchestration scripts ([6adabf9](https://github.com/google/stellar-engine/commit/6adabf9276963c02230c0924ed629da341ace4f8))


### Bug Fixes

* **0-bootstrap:** resolve Terraform type consistency error in organization.tf and add .managed org policy IDs for import.sh ([e1be125](https://github.com/google/stellar-engine/commit/e1be1256e9d78d10a5e6b5d8176cf6e62d0d73e3))
* **2-networking:** configure Cloud DNS across FedRAMP High and IL5 networking stages ([398b514](https://github.com/google/stellar-engine/commit/398b514f324ed4fa11245d8a3bc01235769e2265))
* **docs:** migrate repository links to GitHub and add contribution guidelines ([4c7a62c](https://github.com/google/stellar-engine/commit/4c7a62c32a683395e2e2918b07c0f9aaa49f3a41))


## [2.9.0](https://github.com/google/stellar-engine/compare/v2.8.1...v2.9.0) (2025-04-08)


### Breaking Changes

* **modules:** bump minimum Terraform required_version to >= 1.10.2 and hashicorp/google provider constraints to >= 6.21.0, < 7.0.0 ([a717964](https://github.com/google/stellar-engine/commit/a717964c522a26c391ca12c5f1a77372c52564ac))
* **blueprints:** replace compute-persistent-disk with compute-engine and standardize input variable names across 32 FedRAMP High and IL5 blueprints ([9668230](https://github.com/google/stellar-engine/commit/96682303739dc09420da6c54ae89495c37d719e9))


### Features

* **1-resman:** include environment name in top-level tenant folder naming ([3d99cb0](https://github.com/google/stellar-engine/commit/3d99cb03505ac208393077809a2c357a1d322670))
* **blueprints:** add Cloud Functions and self-managed GitLab blueprints ([9668230](https://github.com/google/stellar-engine/commit/96682303739dc09420da6c54ae89495c37d719e9))
* **docs:** add GCP resource naming standard documentation and refresh FAST stage README guides ([bc1d214](https://github.com/google/stellar-engine/commit/bc1d214e443632dd9e90862f3f9c407f9833a419))


### Bug Fixes

* **0-bootstrap:** update setIAM.sh to append rather than overwrite IAM policy bindings and remove obsolete DNS CIS log metric block ([8767554](https://github.com/google/stellar-engine/commit/876755487c2744d50bb5fa085ed9ce1720fca71c))
* **scripts:** resolve ShellCheck warnings across repository shell scripts ([e428024](https://github.com/google/stellar-engine/commit/e4280249054faa66b6f2843b27304d080675569d))


## [2.8.1](https://github.com/google/stellar-engine/compare/v2.8.0...v2.8.1) (2025-03-24)


### Bug Fixes

* **0-bootstrap:** remove unsupported VPC Flow Logs organization policy constraint ([064c618](https://github.com/google/stellar-engine/commit/064c6182a159fad5498a8e19376cf47454860abd))
* **blueprints:** update GitLab blueprint deployment documentation ([f8ea573](https://github.com/google/stellar-engine/commit/f8ea5734bb4c11c27e80e34680cf8923f208dabf))


## [2.8.0](https://github.com/google/stellar-engine/compare/v2.7.2...v2.8.0) (2025-03-17)


### Features

* **0-bootstrap:** lower prefix length validation limit, add tenant name validation, and map Assured Workloads compliance regimes ([c2309b9](https://github.com/google/stellar-engine/commit/c2309b9419c507020b1fa1184229e0393d6fd415))


### Bug Fixes

* **2-networking:** increase Private Service Connect subnet sizing in IL5 NGFW networking stage ([a9222c1](https://github.com/google/stellar-engine/commit/a9222c143e11af04392fd34fb98b73955f7fdef4))
* **blueprints:** update GKE project blueprint initial deployment configuration ([db9a846](https://github.com/google/stellar-engine/commit/db9a846bbeed00a7ce3fca529e71ba0400482fbd))


## [2.7.2](https://github.com/google/stellar-engine/compare/v.2.7.1...v2.7.2) (2025-03-06)


### Features

* **docs:** add comprehensive root README architecture overview and export Checkov reports for SonarQube ([354d256](https://github.com/google/stellar-engine/commit/354d25671eddc1cda597ad287f53f86476eff611))


### Bug Fixes

* **0-bootstrap:** support deployments without a billing export project and fix organization policy configuration typo ([eede38c](https://github.com/google/stellar-engine/commit/eede38c8a797b272f272a06abc376494ce1d1fe1))
* **modules:** truncate generated folder and resource identifiers exceeding 30-character limits ([00b9983](https://github.com/google/stellar-engine/commit/00b998324a46178d65de9f714639e0aa81958c89))


## [v.2.7.1](https://github.com/google/stellar-engine/compare/v2.7.0...v.2.7.1) (2025-01-24)


### Bug Fixes

* **fast:** synchronize FAST stage links, stage variable templates, and upstream module configurations ([7972c1a](https://github.com/google/stellar-engine/commit/7972c1a0f080762b45305d0d0b029a831afc0ed5))


## [2.7.0](https://github.com/google/stellar-engine/compare/v.2.6.0...v2.7.0) (2025-01-17)


### Breaking Changes

* **blueprints:** remove var.email and var.gke_service_account_id in gke-project and var.project in pub-sub-project ([4cca0af](https://github.com/google/stellar-engine/commit/4cca0af901567cbffd54ec97f8ed6c50e3b25246))


### Features

* **blueprints:** add Access Context Manager, BeyondCorp Enterprise, Cloud Data Fusion, Cloud IDS, Cloud Workstations, Network Connectivity Center, and Private Service Connect blueprints ([20fcd12](https://github.com/google/stellar-engine/commit/20fcd12b1c6d74f39e4ed2cdc4d4c6444bb3582f))
* **ci:** add SonarQube analysis stage and blueprint documentation validation rules to CI pipeline ([5d28140](https://github.com/google/stellar-engine/commit/5d28140b1f5689b580edc2ade5ff8dcaf32fbd9d))


### Bug Fixes

* **0-bootstrap:** conditionally include billing export project in log metric alerts and remove deprecated bootstrap project config ([fba8809](https://github.com/google/stellar-engine/commit/fba8809f9ee9125f63c0d7e8824fbe1f73b30c70))
* **1-resman:** enforce OS Login on common services projects, disable VDSS project-wide SSH keys, and enable Cloud DNS logging ([9cd07f0](https://github.com/google/stellar-engine/commit/9cd07f0b0fe05fd16482167bb52217d92ebf8331))
* **blueprints:** prevent privileged pods in GKE blueprint, enforce KMS key rotation, and refine Cloud SQL log metric filters ([4cca0af](https://github.com/google/stellar-engine/commit/4cca0af901567cbffd54ec97f8ed6c50e3b25246))


## [v.2.6.0](https://github.com/google/stellar-engine/compare/v2.5.0...v.2.6.0) (2024-12-13)


### Breaking Changes

* **blueprints:** remove var.key and var.keyring from Cloud SQL for PostgreSQL blueprint ([18e0d90](https://github.com/google/stellar-engine/commit/18e0d90988241cc7ce58c4a7f30593633b8cd99a))


### Features

* **blueprints:** add Cloud Composer, Cloud Scheduler, Cloud Spanner, Cloud Translation, Document AI, Firestore, and Workflows blueprints for FedRAMP High ([18e0d90](https://github.com/google/stellar-engine/commit/18e0d90988241cc7ce58c4a7f30593633b8cd99a))
* **modules:** add reusable Cloud Scheduler and Workflows Terraform modules ([74d2a88](https://github.com/google/stellar-engine/commit/74d2a885d99673215a4371b8823f75f393659b16))


### Bug Fixes

* **0-bootstrap:** grant Organization Policy Admin role during bootstrap and refine organization policy definitions ([dc104da](https://github.com/google/stellar-engine/commit/dc104da9cd84bf14633d3c93e94c52423f30d1fc))
* **2-networking:** enable VPC Flow Logs, prevent 0.0.0.0/0 allow rules in firewall policies, and allow bastion SSH to NVA management instances ([257e8f3](https://github.com/google/stellar-engine/commit/257e8f306a6b62357d9428b1919ffa1d56c19847))
* **3-security:** align Stage 3 security resource cleanup and CIS log alert metric configurations ([cff48b4](https://github.com/google/stellar-engine/commit/cff48b4ac761a1eddf94bf7adfc555d5ce7119ee))


## [2.5.0](https://github.com/google/stellar-engine/compare/v2.2.0...v2.5.0) (2024-11-22)


### Breaking Changes

* **fast,blueprints:** remove fast/stages-aw/2-networking-c-nva, rename fast/stages-aw/2-security to fast/stages-aw/3-security, and replace blueprints/il5/logging ([5a2e335](https://github.com/google/stellar-engine/commit/5a2e33558408ba184225ae739dc043f58c4d1341))


### Features

* **2-networking:** add hierarchical firewall policy rule blocking 0.0.0.0/0 ingress across stage networks ([0e17b71](https://github.com/google/stellar-engine/commit/0e17b71b63adbb884d99fd17849a49f505c71254))
* **blueprints:** add App Engine, Cloud Run, Dataproc cluster, Datastore, and Vertex AI Workbench MLOps blueprints for FedRAMP High ([26994c1](https://github.com/google/stellar-engine/commit/26994c140eee3e81bef6b5e48cab63ae174281ec))


### Bug Fixes

* **blueprints:** remove unused var.keys in Cloud SQL for PostgreSQL blueprint and verify service account bindings ([0cef625](https://github.com/google/stellar-engine/commit/0cef6251146c8442a8e278d7c5177893a122daf2))


## [2.2.0](https://github.com/google/stellar-engine/compare/v2.1.0...v2.2.0) (2024-11-13)


### Breaking Changes

* **modules:** upgrade hashicorp/google and hashicorp/google-beta provider constraints to >= 6.1.0, < 7.0.0 and remove modules/private-service-connect ([cb9a955](https://github.com/google/stellar-engine/commit/cb9a955a9d558160e5984593689ae5259591399e))


### Bug Fixes

* **blueprints:** update blueprints for upgraded provider compatibility and restore backend service Cloud Armor security policy attachment ([9fd3b7f](https://github.com/google/stellar-engine/commit/9fd3b7ff252dcf8137a8be85dc820987f05f2c75))


## [2.1.0](https://github.com/google/stellar-engine/compare/v2.0.0...v2.1.0) (2024-11-12)


### Breaking Changes

* **fast,blueprints:** remove fast/stages-aw/2-networking-f-ngfw, fast/stages-aw/3-project-factory, legacy upstream stages and blueprints, and relocate cnap to blueprints/fedramp-high/cnap ([0ab08e0](https://github.com/google/stellar-engine/commit/0ab08e0c185a1c15ded742154910a6f138853c8a))


### Features

* **2-networking:** configure Private Service Connect endpoints, restrictVPCPeering organization policies, and Cloud Armor WAF throttling rules ([747d72b](https://github.com/google/stellar-engine/commit/747d72b1d2157fc620bff2f4274b11ceebb94255))
* **2-security:** enforce KMS key rotation schedules and enable Container Scanning API for vulnerability management ([10bc0aa](https://github.com/google/stellar-engine/commit/10bc0aaadd1df69a2b499e7caa87696282f4b39c))
* **blueprints:** add Cloud Armor security policy blueprint with YAML-driven rule definitions ([da0a11b](https://github.com/google/stellar-engine/commit/da0a11b6ba97025e11a7c970dca2429f19e1bda8))
* **blueprints:** add Secret Manager blueprint with CMEK encryption and secret version management helper script ([c3264d3](https://github.com/google/stellar-engine/commit/c3264d3cf3a4c25be426484540f610cde14432a1))


### Bug Fixes

* **0-bootstrap:** restore bootstrap user variable and add IAM permission helper scripts for Stage 0 and Stage 1 ([2be4597](https://github.com/google/stellar-engine/commit/2be4597418988c40801d411c78c39aa3ff235952))
* **2-networking:** enforce Confidential Compute on NGFW management bastion and disable project-wide SSH keys across compute resources ([cd1ed94](https://github.com/google/stellar-engine/commit/cd1ed941f637cb947ba5846229bb888f67c290b6))


## [2.0.0](https://github.com/google/stellar-engine/compare/v1.0.2...v2.0.0) (2024-10-18)


### Breaking Changes

* **fast:** remove module.kms in 0-bootstrap, replace 12 tenant and branch folder modules in 1-resman with the common-services hierarchy, split Stage 2 into 2-networking-a-fedramp-high and 2-networking-b-il5-ngfw, and bump provider minimum to >= 5.43.1 ([056ba34](https://github.com/google/stellar-engine/commit/056ba344f836fa50a3ac067271ad2be609f45e04))
* **blueprints:** remove var.project and var.region in gcs-project and var.billing_account and var.organization in cnap ([35ba33a](https://github.com/google/stellar-engine/commit/35ba33a09ed42c08381249c31de0435b5967615f))


### Features

* **0-bootstrap:** implement CIS Google Cloud Platform Foundation Benchmark 1.x and 2.x IAM and logging controls ([f4b8fc4](https://github.com/google/stellar-engine/commit/f4b8fc49f5e961a751a64d0d2ac786f344a2a964))
* **2-networking:** deploy Cloud Armor security policies, Access Context Manager perimeters, and Confidential Compute bastion hosts ([c2796d5](https://github.com/google/stellar-engine/commit/c2796d54c9aec5d64e37b9be0cd270abd2faa055))
* **blueprints:** add Cloud Bigtable blueprint for FedRAMP High workloads ([bff7319](https://github.com/google/stellar-engine/commit/bff73191a64d66a2d4ed695def3c0d95b326eddb))
* **blueprints:** add Cloud IDS intrusion detection blueprint with packet mirroring ([b93bdb6](https://github.com/google/stellar-engine/commit/b93bdb63a27eb2a4382d873ed3f2eebe95d24b1e))


### Bug Fixes

* **1-resman:** encrypt resource management state buckets with CMEK and grant KMS admin permissions to stage service accounts ([920c502](https://github.com/google/stellar-engine/commit/920c5028650661e433a79214a4cb12784d986c07))
* **2-networking:** dynamically generate NVA routes per environment subnet and standardize subnet naming across environments ([866e882](https://github.com/google/stellar-engine/commit/866e8826771eb89b21ed6b33a6dcf71c250cc1a6))


## [1.0.2](https://github.com/google/stellar-engine/compare/v1.0.1...v1.0.2) (2024-09-24)


### Breaking Changes

* **0-bootstrap:** reorganize Stage 0 and Stage 1 resource hierarchy under a single top-level Assured Workloads folder ([5a7b8de](https://github.com/google/stellar-engine/commit/5a7b8de8a8939f361862f5edfacc22ee04690003))
* **blueprints:** rename artifact-registry and postgresql directories, remove gcp-ce-security-onion, require var.keyring in gcs-project, remove output.self_link in bq-project, and drop legacy input variables across 10 IL5 blueprints ([2cd25e5](https://github.com/google/stellar-engine/commit/2cd25e58646f7bb95f6a756dfc269b12dd989e2f))


### Features

* **1-resman:** enforce CIS Google Cloud Platform Foundation Benchmark 3.0 and 4.x networking and compute security controls ([913fe60](https://github.com/google/stellar-engine/commit/913fe60781f53f3e819072ee598e01fff4aaaebe))
* **blueprints:** add Cloud Native Access Point blueprint with load balancer, IAP, and Cloud Armor edge protection ([d6caaba](https://github.com/google/stellar-engine/commit/d6caaba7ec499aaf2790156aa04ea6373a790952))
* **blueprints:** enforce CIS Benchmark 6.2 database auditing and logging flags in Cloud SQL for PostgreSQL blueprint ([739a748](https://github.com/google/stellar-engine/commit/739a7482f04992cc73a3901158701806557117c6))
* **ci:** integrate tflint, Checkov, terraform fmt, and documentation verification into the CI pipeline ([052ccd5](https://github.com/google/stellar-engine/commit/052ccd5a1102da4d0b23529ae67e464608623d91))


## [1.0.1](https://github.com/google/stellar-engine/compare/v1.0.0...v1.0.1) (2024-07-30)


### Features

* **blueprints:** add IL5 Dataflow streaming pipeline blueprint connecting Pub/Sub to BigQuery with CMEK encryption and dedicated VPC networking ([52d0295](https://github.com/google/stellar-engine/commit/52d02957614eea6495c40acbdf1e017537ec998d))


## [1.0.0](https://github.com/google/stellar-engine/compare/v0.9.0...v1.0.0) (2024-07-19)


### Breaking Changes

* **blueprints:** remove 0.0.0.0/0 CIDR defaults, var.subnet_name_1 in gke-project, and var.shielded_config in shielded-vm-project ([66056b0](https://github.com/google/stellar-engine/commit/66056b0d6e77b54ade214ce7b2ad93ac56ede7b4))


### Features

* **0-bootstrap:** merge organization policy templates with Cloud Foundation Fabric defaults and parameterize organization-scoped constraints ([67b26b8](https://github.com/google/stellar-engine/commit/67b26b8ebf1ba42add0867b511fbad43e2a92dc0))
* **2-networking:** align network firewall rules and subnet CIDR ranges with FedRAMP High compliance requirements ([48a4b75](https://github.com/google/stellar-engine/commit/48a4b753725311104562fd9614f5aa4bf0dfc78f))
* **modules:** add Private Service Connect module from Cloud Foundation Fabric ([4487583](https://github.com/google/stellar-engine/commit/44875835298a1ae9433f5ee1daec9dae10a5aa7f))


### Bug Fixes

* **ci:** add GitLab CI pipeline configuration for repository validation ([c08b392](https://github.com/google/stellar-engine/commit/c08b39241902e42b617af37010b48e8c5273f1d4))


## [0.9.0](https://github.com/google/stellar-engine/compare/daily-2024.06.12...v0.9.0) (2024-06-28)


### Features

* **0-bootstrap:** provision Assured Workloads folder and enable Access Transparency in Stage 0 bootstrap ([a6f4a89](https://github.com/google/stellar-engine/commit/a6f4a8923c359e5b2c674afdcbf5ab9ea27d0718))
* **blueprints:** add Artifact Registry blueprint with CMEK encryption and consumer VM startup configuration ([5ecc0e5](https://github.com/google/stellar-engine/commit/5ecc0e51713b6d8000a814b9c4babd056e4663b7))
* **blueprints:** add Compute Engine bastion host pattern blueprint with IAP SSH firewall rules and existing tenant VPC lookup ([8a46b37](https://github.com/google/stellar-engine/commit/8a46b3797dc0a1b4014f16ea9309ff0bf57ef3f9))
* **blueprints:** add private GKE cluster blueprint with Shielded GKE Nodes, Dataplane V2, Binary Authorization, and HSM CMEK encryption ([2078cda](https://github.com/google/stellar-engine/commit/2078cdab25c3d0f65f737727b61733441b4e0559))
* **blueprints:** add Security Onion intrusion detection blueprint on Compute Engine with HSM-backed CMEK encryption ([7d9cd1d](https://github.com/google/stellar-engine/commit/7d9cd1d0f25accc96b950b0f6c2a33735b801310))
* **blueprints:** add multi-subnet VPC peering blueprint with secondary CIDR range support ([56bb583](https://github.com/google/stellar-engine/commit/56bb583347f9580f62974a2610aed3fabee54801))


### Bug Fixes

* **0-bootstrap:** interpolate project IDs directly during initial bootstrap before projects exist in state ([69805fc](https://github.com/google/stellar-engine/commit/69805fcdf406621f086b572419734a8d4ca49ae4))
* **2-networking:** add management and us-east4 DMZ subnets and extend NGFW bootstrap readiness wait duration ([235b080](https://github.com/google/stellar-engine/commit/235b0809d2be9682d1a519f7261fd843a5e44bcd))
* **blueprints:** standardize Cloud KMS keys across IL5 blueprints to use HSM protection level ([8f48b2d](https://github.com/google/stellar-engine/commit/8f48b2dc6f163320413de8d03de5b59202990b9f))


## [daily-2024.06.12](https://github.com/google/stellar-engine/compare/daily-2024.06.08...daily-2024.06.12) (2024-06-11)


### Features

* **0-bootstrap:** enable KMS encryption support and regional location configuration for Pub/Sub log sinks ([7868da2](https://github.com/google/stellar-engine/commit/7868da2402e3bfbb523bf87dba1a845ed2c88038))
* **3-project-factory:** provision per-project tenant VPCs with peering to the landing zone and dynamic CIDR allocation ([7f0313b](https://github.com/google/stellar-engine/commit/7f0313b616df74df2c026587155a9195457a33d9))


### Bug Fixes

* **2-networking:** add tenant return routes on the NGFW Cloud Router and allow SSH ingress to the management bastion ([1960e8c](https://github.com/google/stellar-engine/commit/1960e8cb53167f128b1166443eea150d2461be3c))


## [daily-2024.06.08](https://github.com/google/stellar-engine/compare/daily-2024.06.07...daily-2024.06.08) (2024-06-07)


### Features

* **blueprints:** add Cloud Pub/Sub blueprint with HSM-backed CMEK encryption and dedicated publisher and subscriber service accounts ([0486fd3](https://github.com/google/stellar-engine/commit/0486fd336d2e2c5211d989d85927d1c752cfcf93))


## [daily-2024.06.07](https://github.com/google/stellar-engine/compare/daily-2024.06.04...daily-2024.06.07) (2024-06-06)


### Bug Fixes

* **blueprints:** refactor Compute Engine Shielded VM blueprint variable declarations and module wiring ([469904e](https://github.com/google/stellar-engine/commit/469904e49d42d20e0586229ebbd7b977dc420665))


## [daily-2024.06.04](https://github.com/google/stellar-engine/compare/daily-2024.05.24...daily-2024.06.04) (2024-06-03)


### Features

* **0-bootstrap:** support CMEK encryption keys and custom log filters for organization log sink destinations ([1421565](https://github.com/google/stellar-engine/commit/14215650e48c77cc67b8a0570e7acf8173d30a28))
* **2-networking:** add Palo Alto Networks Next-Generation Firewall stage with management bastion, Cloud NAT, and regional KMS encryption ([30cbc7a](https://github.com/google/stellar-engine/commit/30cbc7aba2421455e80531c841fab4990a3897fb))
* **blueprints:** add Compute Engine persistent disk blueprint with CMEK encryption and dedicated service account bindings ([d0bfcde](https://github.com/google/stellar-engine/commit/d0bfcde872d23dbda0596c8be5141493e49e4a1f))


### Bug Fixes

* **2-networking:** configure default landing zone routes, health check firewall rules, and sensitive NGFW bootstrap password outputs ([e6e0076](https://github.com/google/stellar-engine/commit/e6e0076842abbf9d8e8591e47cdb64b6ef8dd0ec))


## [daily-2024.05.24](https://github.com/google/stellar-engine/compare/daily-2024.05.18...daily-2024.05.24) (2024-05-23)


### Features

* **blueprints:** add BigQuery project blueprint with CMEK-encrypted dataset provisioning and sample configuration ([dd9fae7](https://github.com/google/stellar-engine/commit/dd9fae7816000b53fd354edf12eaa6d81c40a702))


### Bug Fixes

* **blueprints:** standardize BigQuery blueprint directory layout, module variable bindings, and deployment documentation ([13b8778](https://github.com/google/stellar-engine/commit/13b8778b5eff8fda112b8a60ddb55c769861b443))


## [daily-2024.05.18](https://github.com/google/stellar-engine/compare/daily-2024.04.24...daily-2024.05.18) (2024-05-17)


### Features

* **1-resman:** integrate Assured Workloads folder provisioning and CMEK state buckets at the tenant folder level ([d43db29](https://github.com/google/stellar-engine/commit/d43db297b39e6acc8314321cfe155a8ee3b17a90))
* **3-project-factory:** configure initial tenant project definitions and IAM group bindings for IL5 workloads ([bd4e5f3](https://github.com/google/stellar-engine/commit/bd4e5f37bfb46b15d458665ab2869f4dc87539c6))
* **blueprints:** add Cloud KMS blueprint with CMEK keyring and key provisioning for IL5 projects ([96ee83c](https://github.com/google/stellar-engine/commit/96ee83c9ab1b452bc0cce88240572994a4fd2527))
* **blueprints:** add Cloud SQL for PostgreSQL blueprint with CMEK encryption ([5d69bd9](https://github.com/google/stellar-engine/commit/5d69bd98373476084ae28ac77b4115ddfc26f541))
* **blueprints:** add Cloud Storage blueprint with private bucket defaults, CMEK encryption, and Autoclass support ([25863ed](https://github.com/google/stellar-engine/commit/25863edf7ca7f819c8e733ffcf182a5d192859cb))
* **blueprints:** add Compute Engine Shielded VM blueprint with hardened instance defaults and sample configuration ([4f26a18](https://github.com/google/stellar-engine/commit/4f26a18aa058eec61cdecc4364d3d8fded251442))


### Bug Fixes

* **1-resman:** place top-level tenant core project inside the IL5 Assured Workloads folder ([4a602b2](https://github.com/google/stellar-engine/commit/4a602b2f6ced1e3768d9a80b3f0480d819cf70de))
* **blueprints:** remove hardcoded project and email defaults and enforce explicit KMS module dependencies in Cloud Storage blueprint ([897df83](https://github.com/google/stellar-engine/commit/897df833140e67d5fa65ef15cbb25cb03652f891))
* **tests:** adapt FAST stage unit test fixtures for fast/stages-aw ([b5110ad](https://github.com/google/stellar-engine/commit/b5110add18f165adbb415fcf048a96216db68386))


## [daily-2024.04.24](https://github.com/google/stellar-engine/compare/daily-2024.04.23...daily-2024.04.24) (2024-04-23)


### Bug Fixes

* **0-bootstrap:** default sample organization location and storage region to US in terraform.tfvars.sample ([0ada075](https://github.com/google/stellar-engine/commit/0ada075e607c0cf1143cf0283a903a11691b0a0a))
* **0-bootstrap:** include bootstrap_user variable in the initial stage apply command and remove obsolete symlink instructions ([a0926c2](https://github.com/google/stellar-engine/commit/a0926c2999e5aa9822b46e4da9ac8e9ab9cbd600))
* **fast:** document gcloud config set project prerequisites across 1-resman, 2-networking, and 2-security stage READMEs ([c3c0190](https://github.com/google/stellar-engine/commit/c3c019085f755aa741c89d97bd5aad637a989b91))


## [daily-2024.04.23](https://github.com/google/stellar-engine/compare/0494d36...daily-2024.04.23) (2024-04-23)


### Features

* **0-bootstrap:** document bootstrap service account IAM permission requirements ([7b9f013](https://github.com/google/stellar-engine/commit/7b9f013317827f8239f81a9bd4a45a23f78c26e7))
* **fast:** initialize Assured Workloads stages under fast/stages-aw and default regions to US locations ([997ba85](https://github.com/google/stellar-engine/commit/997ba85f90642e1c391b5aab50e855b221ab1ceb))


### Bug Fixes

* **fast:** prune unused networking and project factory stage variants from fast/stages-aw ([a7882c0](https://github.com/google/stellar-engine/commit/a7882c0efcc82fb1a39f814be8a844f3981a04f4))
* **fast:** replace cross-stage file symlinks with direct stage configurations and document Terraform version constraints ([e7be33a](https://github.com/google/stellar-engine/commit/e7be33abad805b17039ea4a52bdd92ad433cfe4a))
