# Changelog

## [4.2.0](https://github.com/google/stellar-engine/compare/v4.1.0...v4.2.0) (2026-10-17)


### Features

* **gemini-enterprise:** add BigQuery datastore import and license retract/assign subcommands ([#280](https://github.com/google/stellar-engine/issues/280)) ([c6eafa9](https://github.com/google/stellar-engine/commit/c6eafa9f0c607a8ab60f636efa4e4854cb2508c5))
* **gemini-enterprise:** harden Brownfield CMEK discovery, identity checks, and Stage 1 VPC and SSL ([#281](https://github.com/google/stellar-engine/issues/281)) ([85efc5f](https://github.com/google/stellar-engine/commit/85efc5f3a8e0433edf8cf3fd30b39a9af3b8ec3d))
* **gemini-enterprise:** relocate blueprint and add multi-regime compliance support ([#279](https://github.com/google/stellar-engine/issues/279)) ([22ca406](https://github.com/google/stellar-engine/commit/22ca406e867289f2e0738f0c8f6ed79372bdbd91))


### Bug Fixes

* logging circular dependency in bootstrap ([#278](https://github.com/google/stellar-engine/issues/278)) ([ae0838f](https://github.com/google/stellar-engine/commit/ae0838fccf0063120e0d13b1febf8279546a0d64))
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
* **stages,blueprints:** remove unused dead variables from 3-security and postgresql ([#207](https://github.com/google/stellar-engine/issues/207)) ([5949fa7](https://github.com/google/stellar-engine/commit/5949fa7ecd1e4cfc11910df2befdc7153b985a86))

## [3.0.0](https://github.com/google/stellar-engine/compare/v2.13.0...v3.0.0) (2026-08-10)


### Features

* **compute-mig:** expose instance_lifecycle_policy for repairs ([#97](https://github.com/google/stellar-engine/issues/97)) ([5cf518a](https://github.com/google/stellar-engine/commit/5cf518a4ff7918e541af8dc9b19a4367e37f0d26))
* **net-lb-app-ext-regional:** add strong session affinity cookie support ([#96](https://github.com/google/stellar-engine/issues/96)) ([ce3cb01](https://github.com/google/stellar-engine/commit/ce3cb01491b6d9ade58da8a649c6f10112e7f2a7))
* Add support for FedRAMP Moderate Assured Workloads deployments ([#162](https://github.com/google/stellar-engine/issues/162)) ([7033b8c](https://github.com/google/stellar-engine/commit/7033b8cc975ee929c5cd961e0a2b96d284669bca))


### Bug Fixes

* **gem4gov:** use testIamPermissions instead of getIamPolicy in check_roles ([#166](https://github.com/google/stellar-engine/issues/166)) ([5f672e3](https://github.com/google/stellar-engine/commit/5f672e3cb02b57694c5ab5f21d87623a5a0971d4))
* Centralize deployment prerequisites ([#88](https://github.com/google/stellar-engine/issues/88)) ([d215ad4](https://github.com/google/stellar-engine/commit/d215ad49311243ac8a802fefe97edc308d26824a))
* Delete commit_msg.txt and move naming doc ([#171](https://github.com/google/stellar-engine/issues/171)) ([1416ede](https://github.com/google/stellar-engine/commit/1416edeedafe913b875b17baf644fe8799ffc75e))
* enable cloudidentity and aiplatform APIs automatically in deploy.sh ([#163](https://github.com/google/stellar-engine/issues/163)) ([c47be72](https://github.com/google/stellar-engine/commit/c47be72bfc4283d1e2b1132e4be83317d8354d93))
* introduce comprehensive automated testing and security scans ([#172](https://github.com/google/stellar-engine/issues/172)) ([db567c1](https://github.com/google/stellar-engine/commit/db567c1bb4bd586edc98c6c65544a2b1b7cb2613))
* update readmes for FedRAMP Moderate support ([#173](https://github.com/google/stellar-engine/issues/173)) ([f64ce6c](https://github.com/google/stellar-engine/commit/f64ce6cd116fa6ecf5f96c8ba99fc44aafa3411e))

## [2.13.0](https://github.com/google/stellar-engine/compare/v2.12.0...v2.13.0) (2026-07-31)


### Features

* add last friday of each month as the minor release point ([0eafebf](https://github.com/google/stellar-engine/commit/0eafebf6452b92d250774ecf5f2a82bf88b99e6e))
* Add monthly minor release workflow ([#165](https://github.com/google/stellar-engine/issues/165)) ([8f5b67a](https://github.com/google/stellar-engine/commit/8f5b67a69686f0300d9a73662e890222f88b271d))
* Add optional billing budgets for AW folder and updated associated docs. ([bce87f8](https://github.com/google/stellar-engine/commit/bce87f84b1fadbe033c158e7359ad10f31193738))
* Initial releases.md documentation ([7a622e2](https://github.com/google/stellar-engine/commit/7a622e26bd14ec714b911965afcfef6617aa94aa))


### Bug Fixes

* Added log sinks description (routes to Cloud Logging bucket with 30-day default retention) in variables.tf ([#124](https://github.com/google/stellar-engine/issues/124)) ([d3f6e48](https://github.com/google/stellar-engine/commit/d3f6e48dec71fe2306f6c3963fab77a170df2f2b))
* Added the logging_bucket_retention variable as a commented-out customizable option. in terraform.tfvars.sample ([#129](https://github.com/google/stellar-engine/issues/129)) ([af4cd97](https://github.com/google/stellar-engine/commit/af4cd977421ddaf0de74f7d67c6bef3ab6cee1ec))
* Added the logging_bucket_retention variable defaulting to 365 (1 year) to meet regulatory requirements out-of-the-box (e.g. NIST AU-9). in variables.tf ([#127](https://github.com/google/stellar-engine/issues/127)) ([2dc67ca](https://github.com/google/stellar-engine/commit/2dc67cacdeccc20604c94ff13f8855fa280af97f))
* Clean up path to authorization markdown artifacts ([f75316a](https://github.com/google/stellar-engine/commit/f75316a6b418e8882f2b2b972c1c1c0014338f2a))
* Configure G4G w/ Model Armor for FedRAMP High ([#150](https://github.com/google/stellar-engine/issues/150)) ([0068ff7](https://github.com/google/stellar-engine/commit/0068ff7c663641b6ea1f8e4ff926efff2b0e3d95))
* Convert gem4gov GE application(s) creation to Terraform ([#148](https://github.com/google/stellar-engine/issues/148)) ([9a00e5c](https://github.com/google/stellar-engine/commit/9a00e5c371cc1386c4d8a6049dfda9844f9532f4))
* Fix case where gem4gov onboarding crashes for existing CMEK ([0c0b9eb](https://github.com/google/stellar-engine/commit/0c0b9eba7af2b7c03c95b612e59e0146d8ed4d91))
* fix link ([6cf6efc](https://github.com/google/stellar-engine/commit/6cf6efc4cf2b5d4548abbebddfcef6850aedce31))
* Misc. documentation updates ([#94](https://github.com/google/stellar-engine/issues/94)) ([05659d0](https://github.com/google/stellar-engine/commit/05659d092059f88b85f3acda10dfc75c1b0c8f0d))
* Passed the logging_bucket_retention variable to the log-export-logbucket module. in log-export.tf ([#128](https://github.com/google/stellar-engine/issues/128)) ([813eadb](https://github.com/google/stellar-engine/commit/813eadb1a086e65df503cfb602f5a0404902524e))
* README: refine wording, headers, and typos ([7e071e9](https://github.com/google/stellar-engine/commit/7e071e9be9f2cd6200be853db8dee8f3f6bfa90c))
* remove icons, bolding, amperstands and add intro sentence for each header ([ca89a85](https://github.com/google/stellar-engine/commit/ca89a8589a1e35059b3e8036f16bbbb0913a33dc))
* Replaced the TBA placeholder under Stage 3 - Security and Audit Account Configuration to document default routing, 365-day retention defaults, customization variables, and Pub/Sub transition guidelines. in ddg.md ([#130](https://github.com/google/stellar-engine/issues/130)) ([a08441e](https://github.com/google/stellar-engine/commit/a08441ed8ab26de6b018761c3e9f5f010f46140f))
* Resolved Audit Logging Discrepancy, Issue #60 in ddg.md ([7880316](https://github.com/google/stellar-engine/commit/788031645237382e16bb3ab066893059796730df))
* Switched the default routing type for all default log sinks (audit-logs, vpc-sc, workspace-audit-logs, and empty-audit-logs) from pubsub to logging. Added three lines of documentation comments above the log_sinks block explaining options and warnings. in terraform.tfvars.sample ([#125](https://github.com/google/stellar-engine/issues/125)) ([0742b18](https://github.com/google/stellar-engine/commit/0742b18eb6a7488381228eee94058631b904494a))
* Update budgets.tf with copyright and locals var. ([1b11f71](https://github.com/google/stellar-engine/commit/1b11f7105ef4d5fcb17bc3270844fa0eebd008e8))
* Update module to billing-account-budget ([3728fc9](https://github.com/google/stellar-engine/commit/3728fc9859acb3a637b8c5aa757f9db748b29459))
* Update Network READMEs ([#167](https://github.com/google/stellar-engine/issues/167)) ([f345d67](https://github.com/google/stellar-engine/commit/f345d67bbe8797d57edb4844f8f35b320d60d91c))
* Update README and releases docs (links, FAQ) ([4edaf68](https://github.com/google/stellar-engine/commit/4edaf68955cbd56d35307bc10dbfd921e3e7c780))
* Update README.md ([#149](https://github.com/google/stellar-engine/issues/149)) ([273eb62](https://github.com/google/stellar-engine/commit/273eb626927b371a37a094c8ead0fa3678dc40c7))
* Updated documentation Links and added appropriate documentation to github repository ([6d03f70](https://github.com/google/stellar-engine/commit/6d03f70036706c651dd45bdaeb76dc675dd20214))
* Updated the helper template that auto-generates the Stage 0 bootstrap configuration to set the default sink type to logging instead of pubsub. in deploy.sh ([2082407](https://github.com/google/stellar-engine/commit/208240745d825d7093af7fb04a583f0177abbdd4))

## [2.12.0](https://github.com/google/stellar-engine/compare/v2.11.0...v2.12.0) (2026-06-22)


### Features

* add FAST_PREFIX environment variables instructions for easier copy and past of command, update formatting for billing_account_override, remove instructions for fedramp moderate networking ([#76](https://github.com/google/stellar-engine/issues/76)) ([eabf54e](https://github.com/google/stellar-engine/commit/eabf54e425f2b0e113a179ac8c3ada872338256a))
* Create compromised-iam-credentials.md ([c850771](https://github.com/google/stellar-engine/commit/c850771c9f0d533a043d79f628b2a35eb0746480))
* Create compute-resource-compromise.md ([afba5e0](https://github.com/google/stellar-engine/commit/afba5e0403f2fe39aa3de89d564708358eacadfb))
* Create customer-managed-encryption-keys-compromise.md ([6870f8f](https://github.com/google/stellar-engine/commit/6870f8f3922f65ebaa1fdf921ed4c4d691e2969e))
* Create incident_response_runbook_template.md ([#84](https://github.com/google/stellar-engine/issues/84)) ([5746192](https://github.com/google/stellar-engine/commit/5746192a74668375fe8d52b77cd5f5be1ec31065))
* Create network-intrusion-detected.md ([d797fc8](https://github.com/google/stellar-engine/commit/d797fc8261e9f41054bb4e60a8d0057157043c8b))
* Create vpc-service-controls-violation.md ([af21977](https://github.com/google/stellar-engine/commit/af2197737b77b118bf3d70515e7796148f4cbdb9))


### Bug Fixes

* Added default value of us-east4 when regions is not specified in terraform.tfvars in variables.tf ([a13b69e](https://github.com/google/stellar-engine/commit/a13b69ec998e65715de34412f526accfaad56832))
* Align DDG bootstrap region example ([2c8b0bd](https://github.com/google/stellar-engine/commit/2c8b0bd871bed1d4560daf97858b3653e2235880))
* Align naming convention docs with DDG prefix ([#87](https://github.com/google/stellar-engine/issues/87)) ([e79d4b9](https://github.com/google/stellar-engine/commit/e79d4b99cc51d6ba0b43d641f51a1cb767801246))
* Allow parameters to be specified on managed custom org policies (https://github.com/google/stellar-engine/issues/92) ([#93](https://github.com/google/stellar-engine/issues/93)) ([606979f](https://github.com/google/stellar-engine/commit/606979f69ceb4c203045815fd5e5151b92988a4a))
* bugfix: update local.cidr_ranges to use var.cidrs instead of pointing to deprecated yaml file ([#77](https://github.com/google/stellar-engine/issues/77)) ([f25a895](https://github.com/google/stellar-engine/commit/f25a895b6e6e57ac9c8519055f7de83f9ed8e8af))
* deprivilege bootstrap default service accounts ([#68](https://github.com/google/stellar-engine/issues/68)) ([f1f14df](https://github.com/google/stellar-engine/commit/f1f14dfd010f9645a4dc44fd3b042abe5478fbc7))
* fixes warnings on variables for steps 1 2 3, removed yaml files from … ([#66](https://github.com/google/stellar-engine/issues/66)) ([429ab04](https://github.com/google/stellar-engine/commit/429ab04de782463ac28375d6207b76827bd100a0))
* Update LICENSE ([95b1bda](https://github.com/google/stellar-engine/commit/95b1bdac5a7ea7620278e11410b0ab07de55a9a4))
* verify gitlab package install script ([#74](https://github.com/google/stellar-engine/issues/74)) ([e12f2d4](https://github.com/google/stellar-engine/commit/e12f2d4f1049af879b072968f12fd0746f3af8a7))

## [2.11.0](https://github.com/google/stellar-engine/compare/v2.10.0...v2.11.0) (2026-06-02)


### Features

* **cloudsql-instance:** allow overriding tier per read replica ([#28](https://github.com/google/stellar-engine/issues/28)) ([77f1953](https://github.com/google/stellar-engine/commit/77f1953b055e143df820e00897de3d2696c869cd))
* **cloudsql-instance:** expose retain_backups_on_delete ([#27](https://github.com/google/stellar-engine/issues/27)) ([d1c1e3e](https://github.com/google/stellar-engine/commit/d1c1e3e1894483d2e6a151a120915ac713f67ee8))
* **gemini-analytics:** create a usage analytics dashboard for gemini enterprise in an AW boundary ([751b7ab](https://github.com/google/stellar-engine/commit/751b7ab4156d965b232a2ef4741de92fe73aff51))
* **net-lb-app-ext-regional:** support regional Internet NEGs ([#26](https://github.com/google/stellar-engine/issues/26)) ([5e33c0b](https://github.com/google/stellar-engine/commit/5e33c0bdd3e1b905214e70726c3de740c0244207))
* Add copyright header to gem4gov-cli Python files and remove unnecessary code from create_engine function ([115ab4a](https://github.com/google/stellar-engine/commit/115ab4aee797c0fcf46625df061e5c86ef864640))
* add FAST_PREFIX environment variables instructions for easier copy and past of command, update formatting for billing_account_override, remove instructions for fedramp moderate networking ([#76](https://github.com/google/stellar-engine/issues/76)) ([317c358](https://github.com/google/stellar-engine/commit/317c358b7ba1cbf96d7b72ca8e118021a6ea3f07))
* Create compromised-iam-credentials.md ([75b0108](https://github.com/google/stellar-engine/commit/75b01087fcd07b14e26b2b0c01b87f0a10c5fd83))
* Create compute-resource-compromise.md ([d66ed6d](https://github.com/google/stellar-engine/commit/d66ed6dac85782aebce2b8e56c10c9686e3c00e3))
* Create customer-managed-encryption-keys-compromise.md ([bb25b48](https://github.com/google/stellar-engine/commit/bb25b48d5126a388946f5fc2f1e433af0b4fbccc))
* Create network-intrusion-detected.md ([e3710b0](https://github.com/google/stellar-engine/commit/e3710b09d397ab1cc28f8ed009c008a7cc3f043a))
* Create vpc-service-controls-violation.md ([6ae54fc](https://github.com/google/stellar-engine/commit/6ae54fcbd556fe83153d48cdeb75a98b96bd3a91))
* feat/alloydb-read-pools ([#16](https://github.com/google/stellar-engine/issues/16)) ([6606345](https://github.com/google/stellar-engine/commit/6606345746dc167ae97ee469eef1108b844757bd))


### Bug Fixes

* **iam/cmek:** Removing default service account IAM permissions that are no longer needed and resolving CMEK registration error ([f7a7a70](https://github.com/google/stellar-engine/commit/f7a7a7025784ccd8f3097f4c52db0fedb1747034))
* **net-lb-app-ext:** stop forcing a default port_name on backend service ([#25](https://github.com/google/stellar-engine/issues/25)) ([aae379a](https://github.com/google/stellar-engine/commit/aae379a1829c716eb262b77b9361b6f47750cab1))
* Adds helper for BigQuery analytics views ([0764250](https://github.com/google/stellar-engine/commit/0764250e84f3faa1981f68f6f8806ce3db03c336))
* apply github-code-quality fixes ([8a001b6](https://github.com/google/stellar-engine/commit/8a001b65ddbed93db1acc859c43fe30fb9ea2ab8))
* audit and format documentation for public release ([#2](https://github.com/google/stellar-engine/issues/2)) ([63b2a1d](https://github.com/google/stellar-engine/commit/63b2a1d11d74ccac230944c60a920e88b538f276))
* capture principal unique identifier with principalSubject field ([bb53825](https://github.com/google/stellar-engine/commit/bb5382589b20aa6cdb2ac2756f323adae45fa17c))
* deprivilege bootstrap default service accounts ([#68](https://github.com/google/stellar-engine/issues/68)) ([2a36067](https://github.com/google/stellar-engine/commit/2a36067d3cdf68d4ed701ab04b51d3e15fecd340))
* Enables partitioned tables for logging sink ([7d32af6](https://github.com/google/stellar-engine/commit/7d32af629e1fd37dcf6e7341291cef7fc64631dc))
* Enhances Terraform infrastructure for Gemini Enterprise ([081fa90](https://github.com/google/stellar-engine/commit/081fa909f2e5b80eaf9d571b1935263480e394a3))
* Fix typo in DDG Updated Data ([#62](https://github.com/google/stellar-engine/issues/62)) ([aab431a](https://github.com/google/stellar-engine/commit/aab431a737045c03ffd803448e7aa8a7c52a39bf))
* Improves deployment script validations and user flows ([c347eac](https://github.com/google/stellar-engine/commit/c347eac21c0e01cd31466fcfa08601a70f5b21d8))
* Improves deployment script with state hydration and interactive features ([ace447d](https://github.com/google/stellar-engine/commit/ace447da9830d7e87ac788a6c21d2847857accd0))
* Refresh ddg doc to v2.9.1 ([d3872a3](https://github.com/google/stellar-engine/commit/d3872a33a131e77df649fdd92a9c377d9c0e2a48))
* Remove Gemini Enterprise CMEK config from Terraform as this is configured in deploy.sh ([94d1ba2](https://github.com/google/stellar-engine/commit/94d1ba2b728e6b551319851a620cdce91154287d))
* remove unnecessary code ([82abfaf](https://github.com/google/stellar-engine/commit/82abfaf5c16f40dcb1c5c016419bd406387de4c2))
* Removing commented code in discovery-engine.tf that is not necessary at this time ([fe970cd](https://github.com/google/stellar-engine/commit/fe970cd79ccf6c6a2b41ee4a670f82a9e790822a))
* Simplify command for enabling Google Cloud Services in DDG ([#19](https://github.com/google/stellar-engine/issues/19)) ([f081675](https://github.com/google/stellar-engine/commit/f081675dc297e78fc02e55737f507ee25e0b9165))
* Update issue templates ([#23](https://github.com/google/stellar-engine/issues/23)) ([0a5939e](https://github.com/google/stellar-engine/commit/0a5939e2b88177faecafe1921eee696b588eee6e))
* Update LICENSE ([122d9c7](https://github.com/google/stellar-engine/commit/122d9c792a87779e7137ee6fa310ef829bf5afc9))
* Updates documentation and bumps version to 1.2.0 ([0b59015](https://github.com/google/stellar-engine/commit/0b590152850c81f03ea5cb85b1844c68e18ee672))
* Updates gem4gov CLI with IL5 support and license management ([7c7e133](https://github.com/google/stellar-engine/commit/7c7e13392af024fc1b99cf8525b14285c89011e9))
* verify gitlab package install script ([#74](https://github.com/google/stellar-engine/issues/74)) ([68684fd](https://github.com/google/stellar-engine/commit/68684fd631bd2483000592745080caa5fb433430))

## [2.10.0](https://github.com/google/stellar-engine/compare/v2.9.3...v2.10.0) (2026-03-13)


### Features

* **blueprints:** parameterize snapshot retention and compute image per PR review ([63fe276](https://github.com/google/stellar-engine/commit/63fe276b3e758b90f754e176c8b45022c48e5c0f))
* Added docs/code-of-conduct.md and moved CONTRIBUTING.md into docs folder ([6552302](https://github.com/google/stellar-engine/commit/6552302464319598529032da2e780643e084390e))
* Added docs/code-of-conduct.md and moved CONTRIBUTING.md into docs folder ([#16](https://github.com/google/stellar-engine/issues/16)) ([161e0a9](https://github.com/google/stellar-engine/commit/161e0a9d886b93c825daac45a5cd8ee7ed50e114))
* Enhance deployment and destruction scripts ([f7584a6](https://github.com/google/stellar-engine/commit/f7584a6bb4a37d4a7dfc859fbf294adfe70b17a1))
* Enhance deployment and destruction scripts with robust error handling and safety checks ([#18](https://github.com/google/stellar-engine/issues/18)) ([1892784](https://github.com/google/stellar-engine/commit/1892784a5039c11f468ef43b5d67a8b7e2d4b307))


### Bug Fixes

* **bootstrap:** add compute api to log-export and set structural org policy root_node ([0d3f83c](https://github.com/google/stellar-engine/commit/0d3f83cb140eac2143bb1e58c9e89a040cb640ea))
* **security:** Address comprehensive ATP Security Review findings (Medium/Low/Informational) ([abfe572](https://github.com/google/stellar-engine/commit/abfe572a35c84edd6b24e5620e761cf8163a9be5))
* **security:** Address comprehensive ATP Security Review findings (Medium/Low/Informational) ([a8be906](https://github.com/google/stellar-engine/commit/a8be906fde142d74f732a034157654a29340f744))
* **security:** Address comprehensive ATP Security Review findings (… ([#25](https://github.com/google/stellar-engine/issues/25)) ([114141a](https://github.com/google/stellar-engine/commit/114141ac8b249592fee2e64c52d17fa4fbe66bb0))
* **security:** default all custom firewall logs to INCLUDE_ALL_METADATA ([3704dfa](https://github.com/google/stellar-engine/commit/3704dfa6e90d4b3dc335440b1f598ac9e03695c1))
* [fix][gem4gov-cli] Also update deprecated data store creation in BQ ([ce3c5fd](https://github.com/google/stellar-engine/commit/ce3c5fd5a790057cc4167040374b8dcef3bfc69f))
* [Fix][Gem4gov-cli] Update data store creation to account for new collections path and remove requirement on CMEK for data store validation ([1f4b3b2](https://github.com/google/stellar-engine/commit/1f4b3b28ecc1365329dc00e2d78529cbc336c872))
* [Fix][Gem4gov-cli] Update data store creation to account for new collections path and remove requirement on CMEK for data store validation ([#22](https://github.com/google/stellar-engine/issues/22)) ([e6d9db7](https://github.com/google/stellar-engine/commit/e6d9db7a1c19c8eb9d6438e6833f6204ccc66c29))
* Address PR comments for deployment/destruction robustness ([5fde80e](https://github.com/google/stellar-engine/commit/5fde80e48bcf00f6c587ce94f67441daf8311113))
* Deploy Script Fixes, Documentation Updates, and Access Level Refinement ([#17](https://github.com/google/stellar-engine/issues/17)) ([7bc9f3b](https://github.com/google/stellar-engine/commit/7bc9f3bd9e30e18d68d7f740339a48586f418f17))
* experimental/* updates: Fix race conditions, UX, and destroy logic ([8bedfbd](https://github.com/google/stellar-engine/commit/8bedfbd0f61841aeab9113f65d004729a8e38e26))
* minor deploy.sh fixes, updates to README, fix access levels included in device policies ([7f6f8f8](https://github.com/google/stellar-engine/commit/7f6f8f8397bc1e0cc75ccd8ca7c189312e7b05a2))
* remove invalid gcp.accessTransparency.enforcement constraint ([91f0c0a](https://github.com/google/stellar-engine/commit/91f0c0a99fa09cc603eba93c871c17bf5df971be))
* Resolve merge conflict in deploy.sh ([64844ff](https://github.com/google/stellar-engine/commit/64844ff1a82b44f03c490a1eaffc82e152e14ca1))
* skip import of custom org policies in bootstrap ([ee3d02c](https://github.com/google/stellar-engine/commit/ee3d02cc2452b083f55b14c52801164955c0119c))

## [2.9.3](https://github.com/google/stellar-engine/compare/v2.9.2...v2.9.3) (2025-12-17)


### Features

* Add `gem4gov-cli` for Gemini Enterprise onboarding, update blueprint configurations, and refactor networking stage files. ([4d07a8a](https://github.com/google/stellar-engine/commit/4d07a8ae29c73ed81fb5efe3522c521d70a64bba))
* Add prefix discovery to discover_infrastructure(), ensure state bucket is read properly ([6582fb6](https://github.com/google/stellar-engine/commit/6582fb6e6b28e2179831369a5041963f84c7cf7f))
* add stellar integration, custom brownfield integration, bug fixes, and use different key for state and resources, and updated README.md ([82c2a77](https://github.com/google/stellar-engine/commit/82c2a773746ba3306b6e7b92ec52e67844689803))
* add US keyring/key for CMEK and fix Access Policy logic ([9993517](https://github.com/google/stellar-engine/commit/9993517a88931999b312a2b58b6d867d40b8a86d))
* add US keyring/key for CMEK and fix Access Policy logic ([#5](https://github.com/google/stellar-engine/issues/5)) ([070cc4e](https://github.com/google/stellar-engine/commit/070cc4ec1b3c62ecc61d5f148593cadc2366bea3))
* added CONTRIBUTING.md file ([82cefff](https://github.com/google/stellar-engine/commit/82cefff4f61a50c744dd958d3e5ba51258e59a14))
* added CONTRIBUTING.md file ([#2](https://github.com/google/stellar-engine/issues/2)) ([92cf77f](https://github.com/google/stellar-engine/commit/92cf77fbb6e8b3fb95a6a06ce07541b2a86ebb04))
* added licence header to file ([66453f3](https://github.com/google/stellar-engine/commit/66453f35efd09b78c2f697b4b65d8180c12499e8))
* added licence header to file ([#3](https://github.com/google/stellar-engine/issues/3)) ([35c6b39](https://github.com/google/stellar-engine/commit/35c6b395939793da6466f5a6f44da0fdccf88f45))
* added us key discovery logic to deploy.sh ([0a6f794](https://github.com/google/stellar-engine/commit/0a6f794e784085fadcf926f8e330700e5a44afb8))
* create helper function sub-menu, add options for updating compliance, replacing app/routing rules, upload SSL ([f3c180c](https://github.com/google/stellar-engine/commit/f3c180c28db98ae2ffbcc985f2a942a795cf9984))
* enhance FedRAMP High blueprint with org policy checks, updated IAM roles, workforce identity federation, and refined subnet/firewall configurations. ([98af416](https://github.com/google/stellar-engine/commit/98af416a3723f8771a91e2c0782bfa96c8e26a6e))
* graceful handling of terraform failures, change messaging to end-users ([c6b81b3](https://github.com/google/stellar-engine/commit/c6b81b32203c2a6c4a02587f4df9d360be89f705))
* Implement Brownfield vs Greenfield deployment logic with Shared VPC support ([c2b528b](https://github.com/google/stellar-engine/commit/c2b528b867bc213debef447924f71642172547c8))
* modularize data store addition, terraform fmt, gem4gov app set-idp command ([db072aa](https://github.com/google/stellar-engine/commit/db072aa05bab83589ab41103971afe619f07bdee))
* Refactor deploy.sh and Stage 0 for robust discovery and CMEK management ([8d5d198](https://github.com/google/stellar-engine/commit/8d5d198ec95e63bd1c44b30af1d4d209165cb318))


### Bug Fixes

* change update-idp command to set-idp ([1df9579](https://github.com/google/stellar-engine/commit/1df957951ab3bebd77259687aeb6cfafd38000bd))
* Enhance Gemini Enterprise deployment with interactive script, tfvars reuse, and security features ([4953f9e](https://github.com/google/stellar-engine/commit/4953f9e6f541c8aa78a95a190f52220474b838cc))
* Enhanced G4G Deployment and Automation ([#4](https://github.com/google/stellar-engine/issues/4)) ([1f14061](https://github.com/google/stellar-engine/commit/1f140617bb4fc6367eaf0428f0643cd94e76cc33))
* Gemini Enterprise Blueprint: Internal Ingress Functionality + Documentation ([#1](https://github.com/google/stellar-engine/issues/1)) ([eb990f4](https://github.com/google/stellar-engine/commit/eb990f492ead4d59fc31104020bec5aae714fef3))
* Refactor CLI commands and cleanup Terraform configuration ([#6](https://github.com/google/stellar-engine/issues/6)) ([be7c12f](https://github.com/google/stellar-engine/commit/be7c12f3f1cb13219596aa8f602507ed8d6c09a3))
* Refactor Infrastructure Discovery and CMEK Logic for Robustness ([#7](https://github.com/google/stellar-engine/issues/7)) ([1420b64](https://github.com/google/stellar-engine/commit/1420b641a37601ff8d18d045c8f6320c94273d55))
* Refactor Infrastructure Discovery, Access Control, and Data Store ID Generation ([#14](https://github.com/google/stellar-engine/issues/14)) ([ce7b94b](https://github.com/google/stellar-engine/commit/ce7b94bf722272f0858c6d6a3bf11b2960d6701f))
* Refactor prefix discovery and improve state bucket handling ([#8](https://github.com/google/stellar-engine/issues/8)) ([833317b](https://github.com/google/stellar-engine/commit/833317bed61721902402c315a0fee374846ac4d7))
* refactored infrastructure discovery/prerequisites, granular access control creation, referencing terraform state to prevent re-prompting, add helper function for populating created data stores (gcs only), update random suffix on datastore replacement to prevent 409 errors ([9c808af](https://github.com/google/stellar-engine/commit/9c808af1a769360af8b10736ac6d4540117f6f6a))
* Reorganize OSS VRP section in README.md ([2474d05](https://github.com/google/stellar-engine/commit/2474d052f7d4cd12ef7a97778f725200e7b73209))
* Reorganize OSS VRP section in README.md ([#9](https://github.com/google/stellar-engine/issues/9)) ([46a9c1f](https://github.com/google/stellar-engine/commit/46a9c1f4508387a8b4db4c062fce631f40a97f52))
* time of day in readme ([400ee00](https://github.com/google/stellar-engine/commit/400ee00f5b5204055973a88fd6488f12cbd2e839))
* Update README.md ([1c0a28e](https://github.com/google/stellar-engine/commit/1c0a28ec41102154a29538ecb95dc4a54db071de))

## [2.9.2](https://github.com/google/stellar-engine/compare/v2.9.1...v2.9.2) (2025-11-12)


### Features

* **agentic-workflow:** Add draft agentic workflow for review ([2303585](https://github.com/google/stellar-engine/commit/2303585624e747b880eeed544340386266802e5c))
* add git ignore changes ([9b0c763](https://github.com/google/stellar-engine/commit/9b0c76302798e2a5aa0b74cf5462f719a946d768))
* Add initial IAM blueprint for AgentSpace ([138bd15](https://github.com/google/stellar-engine/commit/138bd15449bc286680e07f4c5c467268118faf87))
* Add OSS VRP exclusion header to README.md ([fb14045](https://github.com/google/stellar-engine/commit/fb14045f2fc26485734a6557c13dbe1038588810))
* Add updates for experimental scripts ([35721a8](https://github.com/google/stellar-engine/commit/35721a84351f0c59886d7616e7e660aa3df8cbd8))
* Add updates for experimental scripts and update doc link ([39be8ab](https://github.com/google/stellar-engine/commit/39be8abd4a0e636337f40e7947848b956dbb3f34))
* added docs/CONTRIBUTING.md ([ef0d1c2](https://github.com/google/stellar-engine/commit/ef0d1c2173cbeb1de649ab1938806b6102ac3497))
* added validation.sh to 3-security ([5ee81eb](https://github.com/google/stellar-engine/commit/5ee81ebd95e4f385e5e44a9bb444741dd4adf73f))
* Implement Secure Regional LB for Gemini Enterprise Access and Vertex AI Discovery Engine ([da971f2](https://github.com/google/stellar-engine/commit/da971f20868db1bbf8acbb5c78881d8fd5b70138))
* Implement Secure Regional LB for Gemini Enterprise Access and Vertex AI Discovery Engine ([713975d](https://github.com/google/stellar-engine/commit/713975daa6446611659a2832231b65d2514f459e))


### Bug Fixes

* # Conflicts: ([0d166f4](https://github.com/google/stellar-engine/commit/0d166f4244ef5205c90eaac7968de6d2320fdb4d))
* Add GEMINI.md for AI assistant guidelines ([f39cfa1](https://github.com/google/stellar-engine/commit/f39cfa1601f98a392de311460ee7bf9b007521e5))
* Added/Updated Apache header text where applicable ([a14ad5f](https://github.com/google/stellar-engine/commit/a14ad5f1738fbfb652ad0291e1c55f64e8c7ab49))
* adding discovery-engine blueprint with terraform apply working for data connectors, creates a sample bq dataset and gcs bucket, then creates a gemini enterprise app ([b267767](https://github.com/google/stellar-engine/commit/b2677670e9036c0a9d9cb0b1c6585746a1cdc447))
* all files in gemini-enterprise ([f89c213](https://github.com/google/stellar-engine/commit/f89c213c73a7b76ff83160f75307170e54cdcc24))
* c ([93c41a0](https://github.com/google/stellar-engine/commit/93c41a08f24b8c0a38fcd5a2867449ca85656309))
* cloud armor name syntax and gitignore .env ([390c7aa](https://github.com/google/stellar-engine/commit/390c7aa82bceea64b74374c60f40694fc77e207c))
* Cloud Scheduler Job blueprint - Consume existing Pub/Sub topic and standardize variables ([0813158](https://github.com/google/stellar-engine/commit/0813158cc576bd062868f4de96b67b6659fd4218))
* Cloud Scheduler Job blueprint - Consume existing Pub/Sub topic and standardize variables ([97b356d](https://github.com/google/stellar-engine/commit/97b356d81f54c78fbe84ecb2de0bd95d53c4fe68))
* Cloud-Armor blueprint - changed rules.yaml to align with security best practices and cloud armor preconfigured WAF rules ([db75054](https://github.com/google/stellar-engine/commit/db7505450f395f17d0a0674e1296737068d02a1e))
* Cloud-Armor blueprint - changed rules.yaml to align with security... ([2048bde](https://github.com/google/stellar-engine/commit/2048bded2fa8d1042f32c7e17623237193341eb1))
* cnap reorganization for agentspace implementation ([41ea44e](https://github.com/google/stellar-engine/commit/41ea44e79b9ae4cc7be72b93dd5c9e85f7dbd382))
* Consolidate Google Workspace group definitions\n\n- Remove redundant group definitions from iam.tf.\n- Ensure groups are defined only in groups.tf with correct provider config. ([3acf2d0](https://github.com/google/stellar-engine/commit/3acf2d0625d11bf0b259c06cb5d6878b8fee39aa))
* data connector, gemini app, bq implementation, and gcs implementation ([563a9b2](https://github.com/google/stellar-engine/commit/563a9b2920c5c59453413de719bc2b9623b078c7))
* Enforce explicit region configuration and improve bootstrap setup (Remove hardcoded us-east4 regions and make region configuration dynamic) ([78e71ac](https://github.com/google/stellar-engine/commit/78e71aca46560b286bb50ae1a9e736361832454a))
* gemini domain ([d9f5a32](https://github.com/google/stellar-engine/commit/d9f5a32996e6f14dfa6fa9b4f6c20d9d54884441))
* gemini enterprise app, data connector, data store, search engine, example gcs and bq dataset ([eae14cf](https://github.com/google/stellar-engine/commit/eae14cf4843d56c8753f3d85997567a3ba1a7047))
* gemini enterprise blueprint stage 0 and stage 1 apply success ([8e03ed0](https://github.com/google/stellar-engine/commit/8e03ed0a56f3668442c673abba62f4d4d975a7f6))
* gemini-enterprise-refactor ([76d8854](https://github.com/google/stellar-engine/commit/76d88541274762ebe7b5caf99012ce4e43bf8244))
* gemini-enterprise-refactor ([582e30e](https://github.com/google/stellar-engine/commit/582e30eb1131e0f3a7c06d2ca17ea8e0f403e368))
* Maintenance: Internal merge synchronization ([d0f3a1c](https://github.com/google/stellar-engine/commit/d0f3a1c8abc2ebc11d0d1c620b263ccafc56e758))
* Maintenance: Internal merge synchronization ([db43caa](https://github.com/google/stellar-engine/commit/db43caa1185da908f310b75105aa24b08ed0f93b))
* moved into subdir ([7d8c174](https://github.com/google/stellar-engine/commit/7d8c174799bbdb787ff7c5e3b928dcf266656620))
* name syntax ([1a4dbc1](https://github.com/google/stellar-engine/commit/1a4dbc1cf7536283b9d53a3e0bab285efec689c1))
* outputs.tf takes group.tf creation ([45b6729](https://github.com/google/stellar-engine/commit/45b67298ac3fe752dfcf16151fd34b34f8cbece2))
* picked up davion's cloud armor blueprint, got a destroy and apply working now with screenshots ([3b63c0a](https://github.com/google/stellar-engine/commit/3b63c0a140469d6cc44a06496c1c646327e4c862))
* pre-gemini enterprise changes ([2c39008](https://github.com/google/stellar-engine/commit/2c3900869c5ebc3198ff7387dd8c9801357375eb))
* Pub/Sub blueprint for enhanced consistency, CMEK, and usability ([6e8cd58](https://github.com/google/stellar-engine/commit/6e8cd58ff37bdadb7ddc5d0403c3cd4fe9370d9a))
* Pub/Sub blueprint for enhanced consistency, CMEK, and usability ([bae5f6f](https://github.com/google/stellar-engine/commit/bae5f6ffa7cedac8de637c3fd3b5cf73c84bea82))
* refactor changes ([43ea87a](https://github.com/google/stellar-engine/commit/43ea87a678b50c0cc230239c5ecb85dfe0887084))
* Remove hardcoded us-east4 regions and make region configuration dynamic ([4a1d28d](https://github.com/google/stellar-engine/commit/4a1d28dccc85812c27c0259d94230dcf02543fba))
* Remove TODO lines in files, per releasing open source projects instructions ([7fdd2c7](https://github.com/google/stellar-engine/commit/7fdd2c77e88c3d02463587df043647307f5a1142))
* Revert "feat(agentic-workflow): Add draft agentic workflow for review" ([8ac1301](https://github.com/google/stellar-engine/commit/8ac1301a10354c42d2ad7b513a584bee3e536ef8))
* Revert "feat(agentic-workflow): Add draft agentic workflow for review" ([c022033](https://github.com/google/stellar-engine/commit/c022033939cbca90afc73f85ec95b31ed0d3be17))
* stage 00 is able to deploy resources with no error ([cda17d6](https://github.com/google/stellar-engine/commit/cda17d63ae5b387269516282522c967e43b38d22))
* stage 01 apply success ([b44d4b2](https://github.com/google/stellar-engine/commit/b44d4b239445fbc2306de14f93846c4a18fa24cf))
* tfvars ([fdc4170](https://github.com/google/stellar-engine/commit/fdc4170f32eed05f37beb55966fc7b5157c9125e))
* updated .gitignore ([624fcd6](https://github.com/google/stellar-engine/commit/624fcd6bd2977450673440c8e708094f7bc01181))
* WIP: Configure Google Workspace groups and IAM for AgentSpace ([8636fb8](https://github.com/google/stellar-engine/commit/8636fb89cc435d88083acbace9040c27a810e07c))
* WIP: Saved uncommitted edits from previous session ([6313d47](https://github.com/google/stellar-engine/commit/6313d47f34c978458b48bc74da9ac4f15c7a8907))
* work 11/5/2025 on gemini enterprise stage 1 blueprint ([fb8eeaa](https://github.com/google/stellar-engine/commit/fb8eeaa297a405612229b693c518d09fba7bb102))
* work on gemini enterprise stage 01 and stage 02 structuring, pending test ([eeb2e52](https://github.com/google/stellar-engine/commit/eeb2e52183eadf761203464f9cad355a18779c4b))

## [2.9.1](https://github.com/google/stellar-engine/compare/v2.9.0...v2.9.1) (2025-09-19)


### Features

* Add failure info to check docs ([971021a](https://github.com/google/stellar-engine/commit/971021a589ef298acb2c33eecd31163794eb0987))
* Disable GitLab CI pipeline with dummy job and add useful comments. ([1f2e534](https://github.com/google/stellar-engine/commit/1f2e5343919feafeb776b85c3560fa686010133c))
* Feat/dr 611 acm refactor2 ([960d965](https://github.com/google/stellar-engine/commit/960d9653845f1de8050f2ec822805c74d2de5603))
* Feat/dr 626 datastore refactor2 ([73241ae](https://github.com/google/stellar-engine/commit/73241ae3aa18cfdefed0309e8a26f944e17beb29))
* Feat/dr 628 blueprint firestore refactor ([521cb8a](https://github.com/google/stellar-engine/commit/521cb8a3947466e272207db804243a06df3820eb))
* Feat/dr 640 pubsub refactor ([b13102d](https://github.com/google/stellar-engine/commit/b13102d202b2e40ea40d92b5bf5ee3b2f44b9189))
* Feat/enable services ([aea891e](https://github.com/google/stellar-engine/commit/aea891e275c5193d0a7b018076ebb1e72ad34ec7))
* feature/ci-fix-squash ([d13c4d0](https://github.com/google/stellar-engine/commit/d13c4d0c46934fc1e6e47bfd3ef4a343ffb1a374))


### Bug Fixes

* **gke:** Decouple cluster from VPC and KMS, add Shared VPC support ([2f91cb2](https://github.com/google/stellar-engine/commit/2f91cb2d67926b8ec5a60f4170728d647e08841f))
* **gke:** Decouple cluster from VPC and KMS, add Shared VPC support ([c674b27](https://github.com/google/stellar-engine/commit/c674b27cdabf61c9af0bcfb7f415ac30b72eedf8))
* **org:** Resolve Terraform type consistency error in organization.tf ([7186c99](https://github.com/google/stellar-engine/commit/7186c99e131c6896877ce0410171507de15c8015))
* **org:** Resolve Terraform type consistency error in organization.tf ([e1be125](https://github.com/google/stellar-engine/commit/e1be1256e9d78d10a5e6b5d8176cf6e62d0d73e3))
* 772 gke gitops ([2164b4c](https://github.com/google/stellar-engine/commit/2164b4cab510d521777de5a42279f465e9440638))
* 778 GKE Vanilla ([ea960ed](https://github.com/google/stellar-engine/commit/ea960ed6b8d91523431bd1ce990ec68f14532235))
* [DR-690] admin principal perms ([16f62f6](https://github.com/google/stellar-engine/commit/16f62f67d3d0331f110656d60eec44e5972550eb))
* [DR-773] set up dns in frh and il5 ([398b514](https://github.com/google/stellar-engine/commit/398b514f324ed4fa11245d8a3bc01235769e2265))
* Artifact Registry Blueprint Improvements ([a06754e](https://github.com/google/stellar-engine/commit/a06754eabc31b66748080a724baf4ac1d6a23cd1))
* Automation for deployment, deletion, and redeployment ([6adabf9](https://github.com/google/stellar-engine/commit/6adabf9276963c02230c0924ed629da341ace4f8))
* clear out org level tagging ([932cf3e](https://github.com/google/stellar-engine/commit/932cf3e2836e483e38dfa1a3d4f451d06f8a7eec))
* Cloud KMS Project blueprint - Shift to manage existing KMS resources ([dae45ab](https://github.com/google/stellar-engine/commit/dae45ab705c650996403c6c36fed22dfddbfac8a))
* Cloud KMS Project blueprint - Shift to manage existing KMS resources ([36d74e3](https://github.com/google/stellar-engine/commit/36d74e3014388b01474c00daf8eff4eee29cabf5))
* dr 612 app engine blueprint ([21dd6a8](https://github.com/google/stellar-engine/commit/21dd6a81f9f64a7fd4a55da8ad68bc9686ffd3ef))
* dr 614 bigtable blueprint ([f34d194](https://github.com/google/stellar-engine/commit/f34d1946e5363695ecbff99b3658b9a062ef81f0))
* dr 615 cloud armor blueprint ([98953b7](https://github.com/google/stellar-engine/commit/98953b72756bd4da03c50abbc52696b7eb934bf0))
* dr 617 cloud composer blueprint ([2de29d1](https://github.com/google/stellar-engine/commit/2de29d1a1e1cd033df3a199ce92611571d3c63a7))
* dr 617 cloud ids refactor ([ad929cd](https://github.com/google/stellar-engine/commit/ad929cd562d4ef3b4e0c8a1923b6c51a88b1bf4d))
* dr 618 cloud run ([a413731](https://github.com/google/stellar-engine/commit/a4137314bf0d4f4fa08decc27ef6eb8bf45b668c))
* dr 620 cloud spanner ([fe76d15](https://github.com/google/stellar-engine/commit/fe76d15ce50498c431679432ff73de0bc1c7a6b0))
* dr 621 cloud translation ([f3f9333](https://github.com/google/stellar-engine/commit/f3f9333f669b35245bc144bcb9e5c3ad8d19fc65))
* dr 624 datafusion ([8864715](https://github.com/google/stellar-engine/commit/886471506985477816679fecb9420d1ecb1c8412))
* dr 627 document ai ([7cffd61](https://github.com/google/stellar-engine/commit/7cffd611a60ebffc90ed443633b2cb31206bc6d0))
* DR-625 Dataproc Blueprint Refactor ([88b3c49](https://github.com/google/stellar-engine/commit/88b3c49aa411e2cef1cab6b635220fe0669c747c))
* DR-632 Artifact Registry ([1f7a4f4](https://github.com/google/stellar-engine/commit/1f7a4f4717a07a2800c95475c5d1beae5093f435))
* DR-633 Bastion Pattern ([0fb3c63](https://github.com/google/stellar-engine/commit/0fb3c636721fc8f188e8e9e33a03cecf9d8e7c84))
* DR-634 BigQuery Project ([c56bde3](https://github.com/google/stellar-engine/commit/c56bde37efd8d03af5d64506bb0efdd0b896fbb9))
* DR-636 Dataflow Blueprint Refactor ([c1a2fdf](https://github.com/google/stellar-engine/commit/c1a2fdf92763f96c34bab7541a4d3cd965882a1d))
* DR-637 GCS Project Blueprint Refactor ([8b017d5](https://github.com/google/stellar-engine/commit/8b017d5cd697aba48b0d58e3d5e74df591e7896a))
* DR-641 Shielded VM Blueprint Refactor ([6605808](https://github.com/google/stellar-engine/commit/6605808b21cd620d092dd8e29bc7c88aa337d1ba))
* dr-702-bcap-blueprint ([256daa3](https://github.com/google/stellar-engine/commit/256daa38d438c6d8a81441b80623aa8219771569))
* dr-702-bcap-symbolic-link ([734953b](https://github.com/google/stellar-engine/commit/734953b8d2e2b9b959a2bbeaee06a7f09de4c9f8))
* DR-731 Collapse tenant subfolders ([f667c1c](https://github.com/google/stellar-engine/commit/f667c1c36f645bb0032880c784de6cb074045ec6))
* dr-771-import-script-refactor ([e41939f](https://github.com/google/stellar-engine/commit/e41939fef61a52bd5d4f499b682d7eefdb6c2f45))
* dr-789-migrate-gitlab-links-to-github ([4c7a62c](https://github.com/google/stellar-engine/commit/4c7a62c32a683395e2e2918b07c0f9aaa49f3a41))
* Gke hardening ([fd74626](https://github.com/google/stellar-engine/commit/fd74626e568330d0657eeb9ff36d0c4e38855ea1))
* NCC blueprint refactor for enhanced consistency and clarity ([4d08fc9](https://github.com/google/stellar-engine/commit/4d08fc9ab103971f9d951fd4c1d930018d2e9692))
* NCC blueprint refactor for enhanced consistency and clarity ([c306e00](https://github.com/google/stellar-engine/commit/c306e00032d91ac15894eabe5e4f9e61eb4d30e5))
* org policy .managed IDs necessary for import.sh script ([ee1e255](https://github.com/google/stellar-engine/commit/ee1e255c7ed81b47002c9fb7463ab574547e8d45))
* org policy .managed IDs necessary for import.sh script ([05069ee](https://github.com/google/stellar-engine/commit/05069ee4c44d9988f3d2a4a1af5777246ed999df))
* README Contribution ([55d95f7](https://github.com/google/stellar-engine/commit/55d95f7020e94d0598688cf0f149b2b38d072a88))
* Region bug ([7a4c8a4](https://github.com/google/stellar-engine/commit/7a4c8a4705ea54bb45e4cd6a5f19af3d55606603))
* Remove Master Pipeline Rules ([ecc1c50](https://github.com/google/stellar-engine/commit/ecc1c50acf0170d548c04f77df2e0332a17ecf41))
* Secret Manager blueprint for secure CMEK, enhanced usability, and multi-project alignment ([b30e23b](https://github.com/google/stellar-engine/commit/b30e23b2d15914e99198153a473c1fa38e66aabc))
* Secret Manager blueprint for secure CMEK, enhanced usability, and multi-project alignment ([69ff9e7](https://github.com/google/stellar-engine/commit/69ff9e7ed2f96055481c15d41c29584394df8f74))
* Update .gitlab-ci.yml file ([eacfb88](https://github.com/google/stellar-engine/commit/eacfb88afed19b52fa2564e570a22901980bca7e))
* Update .gitlab-ci.yml file ([cc3ac3e](https://github.com/google/stellar-engine/commit/cc3ac3e976dbcfbc55ed920d158c754232586389))
* Update .gitlab-ci.yml file ([68753e7](https://github.com/google/stellar-engine/commit/68753e765c0e2b3435859a7bd153f1cda69f72fb))
* Update .gitlab-ci.yml file because pipeline is failing. We need to create a runner and register it with this new GL instance and prune back parts of this to meet our needs. For now, disabling it until we have a runner. ([227fe60](https://github.com/google/stellar-engine/commit/227fe605632ed0a428f2e383babc1831a8413fd9))
* VPC Peering blueprint - Relocation and functional overhaul ([ae81ce9](https://github.com/google/stellar-engine/commit/ae81ce9365a2acc7651a353dfeac7f1bddd30628))
* VPC Peering blueprint - Relocation and functional overhaul ([3dbf6ae](https://github.com/google/stellar-engine/commit/3dbf6ae8e1215d6ad60c6fc647cc6e835047449c))
* WIP: feat: Refactor Workflows blueprint (core logic and KMS decoupling) ([a5cb5ce](https://github.com/google/stellar-engine/commit/a5cb5ceb6a4562d17d2864d2cccf34667a7e9aea))
* WIP: feat: Refactor Workflows blueprint (core logic and KMS decoupling) ([da8c7ac](https://github.com/google/stellar-engine/commit/da8c7ac661505d1db4ec1b2a1caa3e6618e605b1))

## [2.9.0](https://github.com/google/stellar-engine/compare/v2.8.1...v2.9.0) (2025-04-08)


### Features

* add env name to top level tenant folder ([142adfa](https://github.com/google/stellar-engine/commit/142adfa0f5999c2f74f581b49ad29419435b3b95))


### Bug Fixes

* [DR-689] add env name to tenant top level folder ([3d99cb0](https://github.com/google/stellar-engine/commit/3d99cb03505ac208393077809a2c357a1d322670))
* Cloud functions ([c0018b4](https://github.com/google/stellar-engine/commit/c0018b4e629676b6457fbc85bd7883b88a85328a))
* docs - fast security readme ([57616a5](https://github.com/google/stellar-engine/commit/57616a5cd76ce63e8cdd16c0b78afc9fb07a772e))
* docs - gcp naming standard - DR-588 ([bc1d214](https://github.com/google/stellar-engine/commit/bc1d214e443632dd9e90862f3f9c407f9833a419))
* docs bootstrap readme - DR-603 ([8eec06e](https://github.com/google/stellar-engine/commit/8eec06e26176c7437538fdec82cc5c5c672b7b25))
* DR 564: Update setIAM script to add instead of replace permissions ([8767554](https://github.com/google/stellar-engine/commit/876755487c2744d50bb5fa085ed9ce1720fca71c))
* Dr 598 upstream module update ([4cbc47b](https://github.com/google/stellar-engine/commit/4cbc47b20219e7d355f720b658de99c4bce1c8e4))
* dr-519-deploy-il5-blueprints ([9668230](https://github.com/google/stellar-engine/commit/96682303739dc09420da6c54ae89495c37d719e9))
* dr-528-deploy-frh-blueprints ([a90f933](https://github.com/google/stellar-engine/commit/a90f9336c797f321f51d8bb9667ff3fe27d76d0d))
* DR-557 - FAST Networking Readme cleanup ([9de26b2](https://github.com/google/stellar-engine/commit/9de26b20f373b18877f28a36aa22cfe2e4c5846a))
* DR-585: Refactor Compute Engine blueprint ([a717964](https://github.com/google/stellar-engine/commit/a717964c522a26c391ca12c5f1a77372c52564ac))
* DR-730: Fix problems discovered from adding Shellcheck ([e428024](https://github.com/google/stellar-engine/commit/e4280249054faa66b6f2843b27304d080675569d))
* Edit terraform.tfvars.sample - fmt ([91466c4](https://github.com/google/stellar-engine/commit/91466c4670766466ffc0f01193d7913b59648bf1))
* Gitlab ([e3c0e74](https://github.com/google/stellar-engine/commit/e3c0e743f9abb18f7b67ba673b7768e6ce3f666b))
* removed dns block from cis logging metrics ([fa4fdf3](https://github.com/google/stellar-engine/commit/fa4fdf38879aca395c2b8be4469b390644fdfdfa))
* Resource Management Readme - DR556 ([85e4365](https://github.com/google/stellar-engine/commit/85e436552af14192bb7d901002a5075421a9a04d))
* revert change ([98516af](https://github.com/google/stellar-engine/commit/98516aff4a0a09f8af12ce8fe1709b61efa7f80e))
* SE root readme cleanup ([2172731](https://github.com/google/stellar-engine/commit/217273115f8edf03e4f9b38290b7ccbdab55316b))

## [2.8.1](https://github.com/google/stellar-engine/compare/v2.8.0...v2.8.1) (2025-03-24)


### Bug Fixes

* removed policy for requiring vpc flow logs ([064c618](https://github.com/google/stellar-engine/commit/064c6182a159fad5498a8e19376cf47454860abd))
* Updated Gitlab README ([f8ea573](https://github.com/google/stellar-engine/commit/f8ea5734bb4c11c27e80e34680cf8923f208dabf))

## [2.8.0](https://github.com/google/stellar-engine/compare/v2.7.2...v2.8.0) (2025-03-17)


### Bug Fixes

* Edit psc.tf - increase size ([a9222c1](https://github.com/google/stellar-engine/commit/a9222c143e11af04392fd34fb98b73955f7fdef4))
* gke blueprint initial deploy ([db9a846](https://github.com/google/stellar-engine/commit/db9a846bbeed00a7ce3fca529e71ba0400482fbd))
* Lower prefix validation limit, add tenant name validation, and map compliance regimes ([c2309b9](https://github.com/google/stellar-engine/commit/c2309b9419c507020b1fa1184229e0393d6fd415))

## [2.7.2](https://github.com/google/stellar-engine/compare/v.2.7.1...v2.7.2) (2025-03-06)


### Bug Fixes

* DR-504: Draft of Main Readme ([354d256](https://github.com/google/stellar-engine/commit/354d25671eddc1cda597ad287f53f86476eff611))
* Edit billing.tf tp support no villing export project ([7176dca](https://github.com/google/stellar-engine/commit/7176dcacd2cd8792fc02cbaf471c6e8467d13cee))
* Fixed typo in organization.tf ([eede38c](https://github.com/google/stellar-engine/commit/eede38c8a797b272f272a06abc376494ce1d1fe1))
* modified 0-bootstrap readme ([bb8818d](https://github.com/google/stellar-engine/commit/bb8818d229f36b902a272a76132e92b5d4cd1628))
* Output checkov reports for sonarqube ([1a22812](https://github.com/google/stellar-engine/commit/1a22812172121cd4a99663eb79c668731051b6c6))
* Removed deprecated .md files ([bd07bd9](https://github.com/google/stellar-engine/commit/bd07bd915fbcda993a7d4da4ec158605dc24e23b))
* updated to truncate folder length if greater than 30 and updates to allow for... ([00b9983](https://github.com/google/stellar-engine/commit/00b998324a46178d65de9f714639e0aa81958c89))

## [v.2.7.1](https://github.com/google/stellar-engine/compare/v2.7.0...v.2.7.1) (2025-01-24)


### Bug Fixes

* FAST Updates ([7972c1a](https://github.com/google/stellar-engine/commit/7972c1a0f080762b45305d0d0b029a831afc0ed5))

## [2.7.0](https://github.com/google/stellar-engine/compare/v.2.6.0...v2.7.0) (2025-01-17)


### Features

* Add sonarqube to the list of stages ([5d28140](https://github.com/google/stellar-engine/commit/5d28140b1f5689b580edc2ade5ff8dcaf32fbd9d))
* Added rules section to the check-docs-blueprints job ([af4e79c](https://github.com/google/stellar-engine/commit/af4e79c5d73312f0c74a943f3842e296aa700579))


### Bug Fixes

* [DR 361] workstations ([fab4203](https://github.com/google/stellar-engine/commit/fab4203ad911c89541ab3ed2291b610ec5d0bb57))
* [DR-471] psc ([2292608](https://github.com/google/stellar-engine/commit/22926084627ad2b9e662665bd60f95bb1e5d3268))
* [DR-492] key rotation ([bc3be0c](https://github.com/google/stellar-engine/commit/bc3be0cc05c04a2618b8f90798e4610b18b27aac))
* [DR-532] NCC blueprint ([20fcd12](https://github.com/google/stellar-engine/commit/20fcd12b1c6d74f39e4ed2cdc4d4c6444bb3582f))
* Datafusion ([21aa983](https://github.com/google/stellar-engine/commit/21aa983a996ccb732b6d607bb17f389b31c35760))
* Dr 449 privileged pods ([4cca0af](https://github.com/google/stellar-engine/commit/4cca0af901567cbffd54ec97f8ed6c50e3b25246))
* DR-413: BeyondCorps Module ([9507f3b](https://github.com/google/stellar-engine/commit/9507f3b9500c69c28f57a6b80a0b1bee86cb7eb5))
* DR-486:new MR for Cloud IDS ([58dbe59](https://github.com/google/stellar-engine/commit/58dbe597eb3a776ba0c2ae4125539b04b8e5125a))
* DR-488 - Enable DNS Logging ([2dffa43](https://github.com/google/stellar-engine/commit/2dffa4318896920939349ba3c3601031fbe545d7))
* DR-489 - Disable VDSS Project Wide SSH Keys ([834a423](https://github.com/google/stellar-engine/commit/834a4234aee6d44d50db89f83b3e25b20d0c9352))
* DR-490 - Enforce OS Login for Common Services (prod-audit-logs, prod-iac-core, prod-billing) ([9cd07f0](https://github.com/google/stellar-engine/commit/9cd07f0b0fe05fd16482167bb52217d92ebf8331))
* dr-493-delete-bootstrap-project ([45f776d](https://github.com/google/stellar-engine/commit/45f776d17adea81797d8c52f6c3027adf96ab833))
* DR-502: Access Context Manager (ACM) Blueprint ([30480d0](https://github.com/google/stellar-engine/commit/30480d0159908b947e8a83e08aae3ca01d9cff84))
* DR-524: Updates to readmes ([3c83e2e](https://github.com/google/stellar-engine/commit/3c83e2ed45b25fb974c2b77580b00f6b9a5419b5))
* DR-530 - Refactor CIS Comments ([73aada1](https://github.com/google/stellar-engine/commit/73aada1fa5448a1c6cfce5a2926361ac32a42950))
* FAST Updates ([7972c1a](https://github.com/google/stellar-engine/commit/7972c1a0f080762b45305d0d0b029a831afc0ed5))
* Modified sql log metrics. ([321706d](https://github.com/google/stellar-engine/commit/321706dbd178e53e85d86dfdc1a29ede7b8f83d1))
* pubsub fixes ([f5817e4](https://github.com/google/stellar-engine/commit/f5817e47d5d26f598813ad799758d4c25088a2e4))
* Update log-metric-alerts.tf to conditionally add billing-export-project. ([fba8809](https://github.com/google/stellar-engine/commit/fba8809f9ee9125f63c0d7e8824fbe1f73b30c70))
* Update variables.tf ([2f391a7](https://github.com/google/stellar-engine/commit/2f391a7a738e006a31fa6cde97b05b5adb88d18a))

## [v.2.6.0](https://github.com/google/stellar-engine/compare/v2.5.0...v.2.6.0) (2024-12-13)


### Features

* added deletion_protection var to workflows ([ff8dcbc](https://github.com/google/stellar-engine/commit/ff8dcbc43c0c194bba09508d8b636f2018b942a2))
* added orgpolicyadmin ([dc104da](https://github.com/google/stellar-engine/commit/dc104da9cd84bf14633d3c93e94c52423f30d1fc))


### Bug Fixes

* [DR-414] cloud translation ([dd9efab](https://github.com/google/stellar-engine/commit/dd9efabd0d5def151c6757b7fdfc052fd5fcc3a5))
* [Dr-416] Document AI ([5ed279c](https://github.com/google/stellar-engine/commit/5ed279c0c7572e00fd5944b878b0f6bbe2e7b6f1))
* [DR-458] cleanup stage ([cff48b4](https://github.com/google/stellar-engine/commit/cff48b4ac761a1eddf94bf7adfc555d5ce7119ee))
* allowing bastion for allow-ssh-bastion-nva-mgmt ([257e8f3](https://github.com/google/stellar-engine/commit/257e8f306a6b62357d9428b1919ffa1d56c19847))
* basic workflow defined ([cc2c84d](https://github.com/google/stellar-engine/commit/cc2c84d985b6781857c39c059eb53cc2cdd65226))
* Cloud Composer Environment ([6ed56fb](https://github.com/google/stellar-engine/commit/6ed56fbc0f0d1b844fa7e2c7ad6e058c68f14c75))
* Cloud Scheduler ([18e0d90](https://github.com/google/stellar-engine/commit/18e0d90988241cc7ce58c4a7f30593633b8cd99a))
* Cloud spanner ([74c01e7](https://github.com/google/stellar-engine/commit/74c01e77f609d347d14d265a2620c6d293677658))
* commented out deletion_protection ([19259fc](https://github.com/google/stellar-engine/commit/19259fc0c84daa15d53548a1262e690391221a50))
* Firestore ([2a99b66](https://github.com/google/stellar-engine/commit/2a99b6689e1f98f94cfbee90ff506dae84ab8476))
* fixed typo with vpc firewall change ([e85154a](https://github.com/google/stellar-engine/commit/e85154a77c6808c47856a112a99280ed2237d707))
* Flow Logs ([9742164](https://github.com/google/stellar-engine/commit/974216433831c1c0bf02f7cd0bc0c782c01df80f))
* made module + other small changes ([c4ff01e](https://github.com/google/stellar-engine/commit/c4ff01e040d4f9c0e4f928f61bc968c51abc29b8))
* moved example code to yaml file ([7bdbbbd](https://github.com/google/stellar-engine/commit/7bdbbbdfe7ebcbabb2e8b65792f36fa026bbb005))
* moved SA to blueprints from modules ([cb6c3ce](https://github.com/google/stellar-engine/commit/cb6c3cee41eacb3d19753d1cdd95a10fcb927ac1))
* removed kms and added sleep ([14aa6d4](https://github.com/google/stellar-engine/commit/14aa6d4bb3151892b4124f3aa1b6dd86095b27f5))
* replaced . with , (typo) ([b0a503a](https://github.com/google/stellar-engine/commit/b0a503a7edbb11598f1dd98df7486424bbbe58bd))
* small error fixed ([7c12ec1](https://github.com/google/stellar-engine/commit/7c12ec1fd7b0157193bed5e395a5f7ce3b1caa04))
* small typos + tf fmt ([66cb58a](https://github.com/google/stellar-engine/commit/66cb58abb32c48f8414fd2d1b3b6143a97c50dcd))
* spanner readme update ([91545ce](https://github.com/google/stellar-engine/commit/91545ce1bf5b229030e385ddc3ff8118b0588cf7))
* Spelling is fun ([755dea6](https://github.com/google/stellar-engine/commit/755dea6ba998893e9d04e6d24481a7734043b6ec))
* take workflow code in from yaml file ([78834fd](https://github.com/google/stellar-engine/commit/78834fd3313574fe610fb424b4fb2e1105f90ab7))
* tf fmt ([f7eccf9](https://github.com/google/stellar-engine/commit/f7eccf9350e0f7e4e2254ea57a1d5a2dccec2f0c))
* Update file organization.tf ([beeb09d](https://github.com/google/stellar-engine/commit/beeb09d51efc2c36c8ab64e3ebd3bb27901cf59d))
* Update the firewall policy to prevent 0.0.0.0/0 ALLOW rules ([9b3f6e4](https://github.com/google/stellar-engine/commit/9b3f6e425e3d15ca5a2c86f286d84f07ba2b92ea))
* Update translation samples ([1901236](https://github.com/google/stellar-engine/commit/1901236e6870cdb858d2efa2b6da5a686f649b1f))
* updated iam variable to use bindings ([d47a177](https://github.com/google/stellar-engine/commit/d47a177dec92c050b70cc68a165842fd80195c3e))
* updated README ([1bd70ec](https://github.com/google/stellar-engine/commit/1bd70ec7ca37b3cd790981c9f69c718a347bf4c4))
* updated readme with known error ([c1ee699](https://github.com/google/stellar-engine/commit/c1ee69961ac283ab39dca70b44be42d367e535cb))
* updated structure ([09c158f](https://github.com/google/stellar-engine/commit/09c158f6099144b1a3768dbff412846aed29ec82))
* you can now add iam roles to the service account ([c82f6be](https://github.com/google/stellar-engine/commit/c82f6be1a7cb1884886d4a54256da85e66f4aa22))

## [2.5.0](https://github.com/google/stellar-engine/compare/v2.2.0...v2.5.0) (2024-11-22)


### Features

* Add firewall policy to prevent 0.0.0.0/0+ingress on firewall rules ([0e17b71](https://github.com/google/stellar-engine/commit/0e17b71b63adbb884d99fd17849a49f505c71254))
* add readme ([eef1c07](https://github.com/google/stellar-engine/commit/eef1c077a211cb09e31b65156af6bde971234927))


### Bug Fixes

* App Engine module and blueprint ([26994c1](https://github.com/google/stellar-engine/commit/26994c140eee3e81bef6b5e48cab63ae174281ec))
* changed notebook to workbench ([50ff3fd](https://github.com/google/stellar-engine/commit/50ff3fd874bb71d3615a5b4c3cb216a9f99d164c))
* Check Docs ([326b22a](https://github.com/google/stellar-engine/commit/326b22ad0dfd94419767c19fab2513e50375f71d))
* dataproc ([1f94bab](https://github.com/google/stellar-engine/commit/1f94babd4e5eba5b81cbcd1e3f6a8a41c3368beb))
* dataproc ([793cf48](https://github.com/google/stellar-engine/commit/793cf48271a69a64286a9ea1e35e6b1f5e8d272e))
* Dataproc ([f15755c](https://github.com/google/stellar-engine/commit/f15755c2132a777b0bbd372b44b8b54a431b6ec1))
* Datastore ([2de9f35](https://github.com/google/stellar-engine/commit/2de9f35c041babc5860ada6cd32caebc686bdf03))
* delete CFF ([0a1d003](https://github.com/google/stellar-engine/commit/0a1d0031e0a7b3694a2e3384d56b3d8f9633c171))
* delete CFF ([e379954](https://github.com/google/stellar-engine/commit/e379954f3ccd33c18204d4e989763f54810b3415))
* Dr 360 cloudrun ([b50c12a](https://github.com/google/stellar-engine/commit/b50c12ac59ccf5ae673628d4561ea85861308ca8))
* DR-441 - PostgreSQL Updates ([0cef625](https://github.com/google/stellar-engine/commit/0cef6251146c8442a8e278d7c5177893a122daf2))
* fixed typos ([779db87](https://github.com/google/stellar-engine/commit/779db87064619479991f1607e309f1a33d79de63))
* fixed typos ([4895bad](https://github.com/google/stellar-engine/commit/4895badfbe21898f28b1375d749f127e9a7644e8))
* formatting ([2ff8fe4](https://github.com/google/stellar-engine/commit/2ff8fe40a14ab232b3f6baf814ab30bfa4527665))
* formatting ([c55031d](https://github.com/google/stellar-engine/commit/c55031d19ad23b6bddc5e3afe18d45528a047783))
* got rid of unnecessary iam bindings ([053ec22](https://github.com/google/stellar-engine/commit/053ec22a2a01bba2ae843e3b3c13fdc50195e247))
* made custom role ([db54bd6](https://github.com/google/stellar-engine/commit/db54bd6c2ec96aac10f6aeb4c73345c22447b2ac))
* Modularize logging ([5a2e335](https://github.com/google/stellar-engine/commit/5a2e33558408ba184225ae739dc043f58c4d1341))
* moved variables to bottom of README ([bcbb4ea](https://github.com/google/stellar-engine/commit/bcbb4eadeb273f85176124aab33e0cdf66c4e4ae))
* Must configure shared VPC + added demo ([0184c7a](https://github.com/google/stellar-engine/commit/0184c7a590fb812d66498aef5472b2e665427f9a))
* parent 9fd3b7ff252dcf8137a8be85dc820987f05f2c75 ([011cb7e](https://github.com/google/stellar-engine/commit/011cb7e85df5222d6daba60ba670e2aff3928b89))
* re-added important stuff ([3169464](https://github.com/google/stellar-engine/commit/31694649ff282602c9143557a51c7f5b7eae996e))
* readme update ([99f2eb3](https://github.com/google/stellar-engine/commit/99f2eb3e0c094edb13e35cc453bf8b509c288d28))
* readme updates ([ce452d4](https://github.com/google/stellar-engine/commit/ce452d41cce0b6b4a933934c13f901cbe8f68098))
* readme updates ([253fd0b](https://github.com/google/stellar-engine/commit/253fd0bcba95650dfb62cb8336b8c47238e1a7e8))
* Removed Cloud NAT ([d2319bc](https://github.com/google/stellar-engine/commit/d2319bc0cb9fba7fb977c4cd3de765cfe6c64e54))
* removed unused remnants from CFF ([b78326a](https://github.com/google/stellar-engine/commit/b78326a7c952e95bd67465d5b0d7edad44df9258))
* untrack files ([3b33cfe](https://github.com/google/stellar-engine/commit/3b33cfe1ec446846ddf05ae2b977a89eb8faeb73))
* untrack files ([850d295](https://github.com/google/stellar-engine/commit/850d2953d6a4a3fdedf22cfabfc099639d38e797))
* updated postgres sa ([f591019](https://github.com/google/stellar-engine/commit/f5910198d8295d6f80f51a234b6e1a0e8fd63e23))
* updated tfvars.sample ([c4e06d7](https://github.com/google/stellar-engine/commit/c4e06d73417ffedb06bf6929800e02798ec02605))
* updated tfvars.sample ([5aea214](https://github.com/google/stellar-engine/commit/5aea214388866eb1071141e8eb25413e3ba99af3))
* Vertex AI blueprint from CFF ([319a717](https://github.com/google/stellar-engine/commit/319a7174ef33322a92f4f3136f64532e9965ff57))

## [2.2.0](https://github.com/google/stellar-engine/compare/v2.1.0...v2.2.0) (2024-11-13)


### Bug Fixes

* Re-add the security_policy to the backend_service ([9fd3b7f](https://github.com/google/stellar-engine/commit/9fd3b7ff252dcf8137a8be85dc820987f05f2c75))
* Remove old modules from stellar engine ([72bba61](https://github.com/google/stellar-engine/commit/72bba61fe5730fbe9ac8177690a9a05da5204c66))
* Update all the old modules with the new CFF modules ([cb9a955](https://github.com/google/stellar-engine/commit/cb9a955a9d558160e5984593689ae5259591399e))
* Update blueprints to use the new providers ([9eccbe9](https://github.com/google/stellar-engine/commit/9eccbe946fdd87a27f7d9f5e97c75457e9fa5356))

## [2.1.0](https://github.com/google/stellar-engine/compare/v2.0.0...v2.1.0) (2024-11-12)


### Features

* Add a key policy to the throttle rule. ([260914d](https://github.com/google/stellar-engine/commit/260914df4922fe2ffc201c06cd4181f04436b728))
* Add in the policy that we are using for out GitLab as a functional example ([0e199cf](https://github.com/google/stellar-engine/commit/0e199cf61afef7ba52a46368df93fe8683d5f45b))
* Added bash script to update secret versions ([fa96b17](https://github.com/google/stellar-engine/commit/fa96b1746c11efdc18ca65c0675856e503eaf2f6))
* added comment on cis benchmark ([99ffd27](https://github.com/google/stellar-engine/commit/99ffd27b5723e4e36cb1ab5dc69e391494bdcace))
* added comment re cis benchmark ([5a6d80a](https://github.com/google/stellar-engine/commit/5a6d80aacd5395cb001c4bdd3caa3a2166383c45))
* Added comments to tfvars ([d138bf9](https://github.com/google/stellar-engine/commit/d138bf922b2d67ca56b05dc6fbe48f5b3156d17a))
* added helper scripts for permissions ([d90cc49](https://github.com/google/stellar-engine/commit/d90cc497542a9cbe1e487dd8d6c4daf2e818da3f))
* added helper scripts for permissions ([2be4597](https://github.com/google/stellar-engine/commit/2be4597418988c40801d411c78c39aa3ff235952))
* added link to folder for vpc peering ([2d4f5d0](https://github.com/google/stellar-engine/commit/2d4f5d021ba6ffea8568c1189209a2851dc383a6))
* added script for permissions and 1-resman default kms key ([fc39d9d](https://github.com/google/stellar-engine/commit/fc39d9d8cc8ffd5cfbca9255f38a1630f83d7c25))


### Bug Fixes

* adding bootstrap variable back to 0-bootstrap stage ([ffb38ae](https://github.com/google/stellar-engine/commit/ffb38aeff42b06f90923f1469ed7ea6e33629b8a))
* adding bootstrap variable back to 0-bootstrap stage ([85b7f94](https://github.com/google/stellar-engine/commit/85b7f948f7c28588209371c25abe6842fb66f44f))
* Apply 1 suggestion(s) to 1 file(s) ([e6e14cb](https://github.com/google/stellar-engine/commit/e6e14cba1a6a5cb19d5de019b012b2a8b4ed4c1f))
* cloud armor blueprints ([324930d](https://github.com/google/stellar-engine/commit/324930dc24076c290b3de61661a76743c7e1c6b0))
* Delete unused blueprints ([ab81dbd](https://github.com/google/stellar-engine/commit/ab81dbde21301b149c038944d758169a80fbf30a))
* Delete unused blueprints ([802c09e](https://github.com/google/stellar-engine/commit/802c09ee16c70a68f90f29cdbe1211a4601d1c7b))
* deleted misc unused files ([b04c87c](https://github.com/google/stellar-engine/commit/b04c87c087be03ca76f2c6d82b9dda6c85362f17))
* deleted misc unused files ([20c3735](https://github.com/google/stellar-engine/commit/20c3735d7989721e2669b96e95ac8522713d682c))
* deleted unused fast stages ([5db130f](https://github.com/google/stellar-engine/commit/5db130fef42bf81cb89d9c0872ba2a8f07f7da21))
* deleted unused fast stages ([fa95dfc](https://github.com/google/stellar-engine/commit/fa95dfc9128692627bcb10f38672278ba171857d))
* deleted unused project factory folder ([7089580](https://github.com/google/stellar-engine/commit/7089580f225c5a6f9685daeaa69f6db1ccc5867f))
* disallowed project wide ssh keys on all uses of compute ([cd1ed94](https://github.com/google/stellar-engine/commit/cd1ed941f637cb947ba5846229bb888f67c290b6))
* DR-440 KMS Key Rotation ([10bc0aa](https://github.com/google/stellar-engine/commit/10bc0aaadd1df69a2b499e7caa87696282f4b39c))
* duplicated frh changes in il5 ([f62712b](https://github.com/google/stellar-engine/commit/f62712bae14bf5d207fa5c9b9289d524a0154f03))
* Enabled vulnerability scanning api ([96af7d3](https://github.com/google/stellar-engine/commit/96af7d3d8d3968570d3d3bccbc4d4e1d2c2078e7))
* Fixed error in the README ([f60dc46](https://github.com/google/stellar-engine/commit/f60dc46700a1f9559e91d3dfe2e73c9c6ff96362))
* fixed typo ([a97993c](https://github.com/google/stellar-engine/commit/a97993ced3099fff74a912fd4c659d1a7d74f76f))
* fixed typo ([a1452d2](https://github.com/google/stellar-engine/commit/a1452d28056544846a07ccdeddc7d8c0ea5076c4))
* Formatting fix ([d41625a](https://github.com/google/stellar-engine/commit/d41625a6c93b08599a2fcca139e736cee488a4b4))
* iChanges to spacing ([036eb08](https://github.com/google/stellar-engine/commit/036eb0827efe5cd03bba421d25fd4180c4d3b54a))
* MR: [DR-369] Secret manager blueprints ([c3264d3](https://github.com/google/stellar-engine/commit/c3264d3cf3a4c25be426484540f610cde14432a1))
* MR: [DR-403] Vulnerability Scanning ([08b3f2c](https://github.com/google/stellar-engine/commit/08b3f2c78d10205a0dcb55e654931c1d0cacf2d7))
* n2d-highcpu-2 required for confidential compute ([2d2b804](https://github.com/google/stellar-engine/commit/2d2b804fc50adafb55fee748cda519c58802b8c3))
* ran tf fmt ([7c6ca45](https://github.com/google/stellar-engine/commit/7c6ca4508f9970c90721c191df890c4c49f90622))
* Refactored PostgreSQL Blueprint ([72a7b8d](https://github.com/google/stellar-engine/commit/72a7b8dab7a7d21997c79d541b7d44c6617e9ff6))
* Refactored PostgreSQL Blueprint ([0ab08e0](https://github.com/google/stellar-engine/commit/0ab08e0c185a1c15ded742154910a6f138853c8a))
* removed 2-networking-f and updated ngfw bastion to be compatible with Confidential Compute ([2aa9bc4](https://github.com/google/stellar-engine/commit/2aa9bc4ce91cb83cd0bd6db31e3bca0cffd6338c))
* removed dead code ([55a8290](https://github.com/google/stellar-engine/commit/55a829028eb91a141a66bcd83d79fa839f1f073a))
* removed psc ip ([4c5471f](https://github.com/google/stellar-engine/commit/4c5471fef248538d1876291b591c551d0f308ffb))
* Removed spaces in terraform.tfvars ([c8e5147](https://github.com/google/stellar-engine/commit/c8e51473ba5c4d65b161cc5bbcf3b824c09da424))
* reverting bastions ([6bebe33](https://github.com/google/stellar-engine/commit/6bebe337031d5c24e22bdc706606fcd15c500ac4))
* Secret manager blueprints ([97b2a43](https://github.com/google/stellar-engine/commit/97b2a43598b1e8e3ec6e83f7a23ef32d93e76810))
* Simplified yaml format ([da0a11b](https://github.com/google/stellar-engine/commit/da0a11b6ba97025e11a7c970dca2429f19e1bda8))
* symlinks and pipeline ([640a9ce](https://github.com/google/stellar-engine/commit/640a9ce735e8493e0393fe0f63521387dfdf0c43))
* symlinks and pipeline ([5b54a6c](https://github.com/google/stellar-engine/commit/5b54a6cb98ad65071d821006707cf11527554d7e))
* Take yaml file as input ([1d8023e](https://github.com/google/stellar-engine/commit/1d8023efcbf9f6a424beac96330d38a7b224f203))
* tf fmt ([fa232d3](https://github.com/google/stellar-engine/commit/fa232d3ceba5712ed5f051ff8739780f5ba50295))
* tf fmt ([c347e84](https://github.com/google/stellar-engine/commit/c347e84732630aad47bee154cbaee3ee7b70fd4c))
* tf fmt ([0f20acc](https://github.com/google/stellar-engine/commit/0f20accc77ead19c7a68b667799e7f9fac63930b))
* tf fmt ([71d99f6](https://github.com/google/stellar-engine/commit/71d99f6ef5a4d2ccbc86e830617f0a416347f608))
* turned off confdiential compute for palo alto vms ([ff3705b](https://github.com/google/stellar-engine/commit/ff3705bed57e843d6e8c41337b9379a327246143))
* Updated output file ([ebbfa7f](https://github.com/google/stellar-engine/commit/ebbfa7f2e9b2a1b5ee161f29707e710f1ae9e1c2))
* updated PSC and restrictVPCPeering policy ([eca4765](https://github.com/google/stellar-engine/commit/eca4765147da0bd9f4d3027d8e47c37addd81451))
* Updated README ([833fec0](https://github.com/google/stellar-engine/commit/833fec090f6aa6557a427c54d787423a99367095))
* Updated README ([54cbc14](https://github.com/google/stellar-engine/commit/54cbc148260a13e8a081a5d37ddb69d2186ae5b7))

## [2.0.0](https://github.com/google/stellar-engine/compare/v1.0.2...v2.0.0) (2024-10-18)


### Features

* added import script ([83632cf](https://github.com/google/stellar-engine/commit/83632cf8344bf6b3fe986f598e6352b93f3496e3))
* Added kms encryption to resman core bucket ([4e4945c](https://github.com/google/stellar-engine/commit/4e4945cbd0978bb4c4de59912f6eb93688cf455b))
* added tflint exception ([8bf01de](https://github.com/google/stellar-engine/commit/8bf01ded9de6a65127a0329ff45289076114d3f7))
* Create a common-services folder and move the iac, logs, and billing projects into it. ([130874c](https://github.com/google/stellar-engine/commit/130874c5efc26d9092184a41b360d13c12164525))
* Create a common-services folder and move the iac, logs, and billing projects into it. ([056ba34](https://github.com/google/stellar-engine/commit/056ba344f836fa50a3ac067271ad2be609f45e04))
* Create an envs:bool variable in the 0-bootstrap phase that controls whether or not we deploy with the environments. Then in the 1-resman stage, create those folders ([a0d0f90](https://github.com/google/stellar-engine/commit/a0d0f90ab6065622f8338af0a465eace3bff9c42))


### Bug Fixes

* adding tflint exception ([7e60df5](https://github.com/google/stellar-engine/commit/7e60df5e5ff1ce34cd0c08c430cf3ab7a9580e14))
* Adjust the outputs so we can run the next stages ([6136903](https://github.com/google/stellar-engine/commit/613690354e184f28c40d92befbbb215062098f56))
* allowing pipeline failure on tflint stages-aw ([71026cc](https://github.com/google/stellar-engine/commit/71026cc79cc8cd4cc211eafc65c667e150348f74))
* Attach the subnets to each project and set a default region ([a4e0185](https://github.com/google/stellar-engine/commit/a4e01855aec1cbc3cc1d973aaa3a9536491041e7))
* Begin work on il5 changes for the new networking ([ad98187](https://github.com/google/stellar-engine/commit/ad98187d893c2e0379f95e369fe7eceeb83267a0))
* Breaking ground on the new networking. Moved all the network host projects under the host folder ([c10bd8e](https://github.com/google/stellar-engine/commit/c10bd8e6794ce94dc4726cfd710142ff396a2402))
* Checkpoint commit before I try to upgrade the provider modules ([41ce22d](https://github.com/google/stellar-engine/commit/41ce22d7b8223346c7bcef91cb6abd0f0e89e310))
* CIS Benchmarks 1.X ([7955cdf](https://github.com/google/stellar-engine/commit/7955cdf3b6cc6ad8ef37d43ac81513eb5c40ef60))
* CIS Benchmarks 1.X ([f4b8fc4](https://github.com/google/stellar-engine/commit/f4b8fc49f5e961a751a64d0d2ac786f344a2a964))
* CIS Benchmarks 2.X ([c02462d](https://github.com/google/stellar-engine/commit/c02462d39f44fb6a61f8739d6265251f8fe635d8))
* CIS Benchmarks 2.X ([588584c](https://github.com/google/stellar-engine/commit/588584c5538a56353e4a4eaaaf9af8d0078aea6c))
* Connectivity tests now work for the different accounts. Unfortunately we won't be able to use the automatic IPAM until after we upgrade to the terraform provider > 6.1.0, which will come in CFF v35.0 ([31c4ee6](https://github.com/google/stellar-engine/commit/31c4ee6f1033e33bc4aa7e51519feec3fad278dc))
* Depends on the organization already being configured ([4767dbf](https://github.com/google/stellar-engine/commit/4767dbfd8dd090db44a84ebed4a8dc3475387a02))
* Deploy Cloud Armor and Access Context Manager with Terraform DR-306 and DR-302 ([e87eeb0](https://github.com/google/stellar-engine/commit/e87eeb07304711d6e618db6c50334ba3d0d60623))
* Deploy Cloud Armor and Access Context Manager with Terraform DR-306 and DR-302 ([c2796d5](https://github.com/google/stellar-engine/commit/c2796d54c9aec5d64e37b9be0cd270abd2faa055))
* Deploy proxy-subnets in the networking stage ([7c6d098](https://github.com/google/stellar-engine/commit/7c6d098302e27cc744dbde64588627aff271e4b8))
* Deploy the host-net projects in 2-networking ([14786c6](https://github.com/google/stellar-engine/commit/14786c65db94ba2136c77face0ca4c8d411c2611))
* DR-316: Write Terraform for Intrusion Detection System (IDS) ([5f2f83e](https://github.com/google/stellar-engine/commit/5f2f83ef51082c7bdb0443c6d7657bb2038415d8))
* DR-316: Write Terraform for Intrusion Detection System (IDS) ([b93bdb6](https://github.com/google/stellar-engine/commit/b93bdb63a27eb2a4382d873ed3f2eebe95d24b1e))
* DR-341: Bigtable deployment ([3f3f798](https://github.com/google/stellar-engine/commit/3f3f79812b00dc09238d49db933925217078359e))
* DR-341: Bigtable deployment ([bff7319](https://github.com/google/stellar-engine/commit/bff73191a64d66a2d4ed695def3c0d95b326eddb))
* Dynamically add the routes to the NVA based off of the environment subnets created ([4be3fdd](https://github.com/google/stellar-engine/commit/4be3fdd661f82b33fa94d59191510a723d56480c))
* Enable confidential compute on the bastion host ([78a58bb](https://github.com/google/stellar-engine/commit/78a58bbee4cae9fa8eb7f0f63084fe4ae001d865))
* Ended up doing the NVA thing anyways, but better ([2dff369](https://github.com/google/stellar-engine/commit/2dff369b29e4a3cb8a629630157e98a6e9d17489))
* Finalize the outputs from the 1-resman stage ([1d65847](https://github.com/google/stellar-engine/commit/1d65847fc77af42f5f9b82e0cf985a459124e946))
* fixed AW bug ([533b0bb](https://github.com/google/stellar-engine/commit/533b0bbb630fdf36062eb087c471c03b32c5e6f4))
* fixed cis benchmark 2.1 ([c0a626f](https://github.com/google/stellar-engine/commit/c0a626f1aeee55b90ba9550b6aa52a843abe77a5))
* fixed cis benchmark 2.1 ([2ba48a4](https://github.com/google/stellar-engine/commit/2ba48a4456ed67fa99101ccbb8fbad43db8f8caa))
* fixed if statement for import ([0fdb79f](https://github.com/google/stellar-engine/commit/0fdb79f80bcc7b4bb1a90ce74512d7a6a99aae0f))
* fixed typo in mocks ([2b585ea](https://github.com/google/stellar-engine/commit/2b585ea442403f061a2de5bc1e0e6c1f671801f8))
* fmt and readme mod ([a376e74](https://github.com/google/stellar-engine/commit/a376e749f87a541c2c084dd2dea4a7566a7f5b36))
* Formatting ([103ee01](https://github.com/google/stellar-engine/commit/103ee015d9ab128b9dd8367fdd456a4bd40b6bf0))
* Formatting ([fdc4519](https://github.com/google/stellar-engine/commit/fdc4519c46bdf3ed8de4c0ab2ea851a73d98a3d8))
* Formatting ([a3e2284](https://github.com/google/stellar-engine/commit/a3e2284c8081a52da06dba5b74d0a161ddf42799))
* full deploy w/ kms ([9a7443c](https://github.com/google/stellar-engine/commit/9a7443c39c042998ae86d6402c2b80b95bd2fe2f))
* Generate all the different combinations of folders and tenants ([a39c7ff](https://github.com/google/stellar-engine/commit/a39c7ff4a4bf631acb7fef1c458c634be1a7246a))
* hotfix routes ([a0722a0](https://github.com/google/stellar-engine/commit/a0722a0395147c628f353f6270aeb208ae99439a))
* hotfix routes ([866e882](https://github.com/google/stellar-engine/commit/866e8826771eb89b21ed6b33a6dcf71c250cc1a6))
* IL5 Changes ([920c502](https://github.com/google/stellar-engine/commit/920c5028650661e433a79214a4cb12784d986c07))
* Make sure that the resman service account has KMS permissions too ([7bcf314](https://github.com/google/stellar-engine/commit/7bcf31473eb6c95718e93cd8f4d6876e25787fb2))
* Make sure to pass along the envs folders ([362ae1c](https://github.com/google/stellar-engine/commit/362ae1c9950c70903e8a0c2bc2337c028eda2823))
* Make the envs folders easier to consume ([e11691e](https://github.com/google/stellar-engine/commit/e11691e5619e46af3bb6392f1f47f943df28a41f))
* Missed the default ingress ([fdd2f7c](https://github.com/google/stellar-engine/commit/fdd2f7cf08338876458cfc1a11eecc28d71c7d0f))
* moved providers.tf to providers.tf.tmo ([37a7ac6](https://github.com/google/stellar-engine/commit/37a7ac6a29f2a3873b694dfe35bc603b554f9e2f))
* moved providers.tf to providers.tf.tmp ([63da730](https://github.com/google/stellar-engine/commit/63da7300590868d7056c62c9bd016b3ca047fe09))
* Peer the vpcs together ([7e1363b](https://github.com/google/stellar-engine/commit/7e1363bd2c0fb2b7a608b1780b93ed68da766a2f))
* redid mocks ([7cc031b](https://github.com/google/stellar-engine/commit/7cc031b6018fbde140375f422752bb3233668d6d))
* Remove the prod and dev network folders ([b9f57b6](https://github.com/google/stellar-engine/commit/b9f57b6aa098b7c514bfdfb17ddead7ce3386ac6))
* Remove unused DNS admin service account which may not exist in most deployments ([75411b4](https://github.com/google/stellar-engine/commit/75411b4dc810860b17c55f0ae6224dcc280ebd2b))
* removed audit policy from 0-bootstrap ([bd97758](https://github.com/google/stellar-engine/commit/bd977581a4b777b900355cdf1abe3bc5e80f3785))
* removed audit policy from 0-bootstrap ([58f0f26](https://github.com/google/stellar-engine/commit/58f0f26311608e85aa52a647e0fc7929dd7db455))
* removed bootstrap_user check on imports and edited tfvars sample ([57335b4](https://github.com/google/stellar-engine/commit/57335b4e610b1a8339529e578c977a2d38fc7b54))
* removed duplicate output ([55d53e7](https://github.com/google/stellar-engine/commit/55d53e7cc754e9be3266ec7e31df634f0f815ae1))
* Rename subnets to be standardized across environments ([002da91](https://github.com/google/stellar-engine/commit/002da91eb58870fc6a4e690ee2c7871953ffbe58))
* resman service account requires admin because it's going to try to delegate permissions to the next round of service-accounts. Not sure overall if I like using the same key for all of these things, but that's what we got from CFF ([b7a6d06](https://github.com/google/stellar-engine/commit/b7a6d06e6db48d8119297307b9868dea670488b5))
* set location defaults to US ([f1fdf47](https://github.com/google/stellar-engine/commit/f1fdf47a379698a6d78934b2bec4ce8aaf7ca70c))
* Simplify CNAP deployment ([24d3768](https://github.com/google/stellar-engine/commit/24d3768dfe16851a66288ee0360855fc7f6408b8))
* Simplify CNAP deployment ([35ba33a](https://github.com/google/stellar-engine/commit/35ba33a09ed42c08381249c31de0435b5967615f))
* Skip the DMZ vpc for the fedramp-high deployment. ([7f434fe](https://github.com/google/stellar-engine/commit/7f434fecdbf4f337d27958198425313755ce3c5d))
* Standardize the names of the subnets in each env ([dab3300](https://github.com/google/stellar-engine/commit/dab33004c415e3cf06b30cb38dd228414ca2a71f))
* Update README ([7af594e](https://github.com/google/stellar-engine/commit/7af594e4463c9ffc2c2cbdd814be1dc741485381))
* Update tenant core folder iam. This should be the last of the 1-resman changes ([e6bf0a9](https://github.com/google/stellar-engine/commit/e6bf0a98a01435273359c4ec06ad5900761e30fd))
* Update the 1-resman stage to deploy a 'main' project for each tenant in their core folder, to simplify the deployment process ([ca23fab](https://github.com/google/stellar-engine/commit/ca23fabcded998ee8aa92a49bcbec8f5677d24c3))
* Update the tfvars.sample file for 1-resman ([ab8a94b](https://github.com/google/stellar-engine/commit/ab8a94b0db4e892a76f2de7d7c0d18ee02aa7dd5))
* updated sample files ([88641f7](https://github.com/google/stellar-engine/commit/88641f75e9ad01c1f66c4d11c9d754bd17055034))
* updated tfvars sample ([403ebc4](https://github.com/google/stellar-engine/commit/403ebc485a5b650dc3d1c4dfff700e522b680061))
* Upgrade the project module to v34.1 from the upstream CFF ([a16a608](https://github.com/google/stellar-engine/commit/a16a60800d2224620ca22dadbb66efbd997ec1ce))
* working on the ngfw update for il5 ([5b4ec02](https://github.com/google/stellar-engine/commit/5b4ec0234b26b06af15940fc710b95b1bfce01e5))

## [1.0.2](https://github.com/google/stellar-engine/compare/v1.0.1...v1.0.2) (2024-09-24)


### Features

* Added all other available options for the database flags, as well as updating the capitalization to reflect the CIS document. ([8127ec0](https://github.com/google/stellar-engine/commit/8127ec0644d24bbdad28fa4c52d8ea57e02cd699))
* Added all other available options for the database flags, as well as updating the capitalization to reflect the CIS document. ([25d02a9](https://github.com/google/stellar-engine/commit/25d02a95c5fd66a2eeed33bd012dfecfdf45d7f3))
* Added BigQuery table as in dataflow, ensured table in dataset use CMEK, and BigQuery dataset uses encryption key, To Verify IAM configuration, used the existing email variable for both bigquery.dataOwner and bigquery.dataViewer roles to ensure that no anonymous or public access is granted. ([53a6898](https://github.com/google/stellar-engine/commit/53a6898ccb4f833aa4b5b42d912cd2a61c68f6a3))
* added commentedo out vpc code as we may need to add ([abba792](https://github.com/google/stellar-engine/commit/abba79251ef3ee1627fa84362d876c10dc2d2133))
* added commentedo out vpc code as we may need to add ([f3e9cd5](https://github.com/google/stellar-engine/commit/f3e9cd59adfec01230bb3ae0a33185a19e708bd5))
* added dependency ([9567bac](https://github.com/google/stellar-engine/commit/9567bac6d1a5c7631dd4ff98787a9fe2d102045b))
* added dependency ([c233910](https://github.com/google/stellar-engine/commit/c2339102e91269fe7bcb1ed3aa994fb7c032df20))
* added description ([59906b8](https://github.com/google/stellar-engine/commit/59906b86440b0ae8c2e898c1105b3ccba4cd48c3))
* added descriptions ([6656d10](https://github.com/google/stellar-engine/commit/6656d10e7fcba8ff04a3236372480e5ecb10340d))
* added firewall, redid readme ([56684dc](https://github.com/google/stellar-engine/commit/56684dcd94e720cb61d55d587dd3d81eedd990a2))
* added firewall, redid readme ([307c018](https://github.com/google/stellar-engine/commit/307c018d95dd638ef5a9c55cae89be71f2d29360))
* added required ports ([8d4243b](https://github.com/google/stellar-engine/commit/8d4243b048ef55d6880f66a4bf53e3b3893dcf75))
* added required ports ([a4facbf](https://github.com/google/stellar-engine/commit/a4facbfcfc27f7441c0442ec3a0fe65496271806))
* added script and updates vars and outs ([aaab19c](https://github.com/google/stellar-engine/commit/aaab19ca54e2b0b1b6ae1c135a24199cb70b344e))
* added some . ([7ecba8d](https://github.com/google/stellar-engine/commit/7ecba8d63447ef073d8eab88c3b3adee9fd07dbb))
* Initial commit of the top-level assured workloads folder ([9f8c5e8](https://github.com/google/stellar-engine/commit/9f8c5e89a8c294cb90c26d90f4ec2a868f593bde))


### Bug Fixes

* accidently deleted lint stage ([acd7135](https://github.com/google/stellar-engine/commit/acd71356d61f30fbc12d4548d531181bbf074287))
* all good ([8feb06c](https://github.com/google/stellar-engine/commit/8feb06cd9de0efb6fb5d7ee517d6d8deff199bd2))
* all working ([3a063bd](https://github.com/google/stellar-engine/commit/3a063bd8918f4c32e02b5852fe437991deb09a2e))
* all working ([421ef19](https://github.com/google/stellar-engine/commit/421ef19ccd1da74d8227c1956b3628ebb635d706))
* Began adding flags ([a1ddb54](https://github.com/google/stellar-engine/commit/a1ddb54fb62761d934a9f8fbf041d7b79369f988))
* Began adding flags ([d4f5351](https://github.com/google/stellar-engine/commit/d4f5351af8c7311c456c7e88aeed35643d290a1a))
* Bring in folder module from CFF, this removes the Assured Workloads work that I did previously, but that work has been implemented in the upstream so we when we update our provider to the latest one, we can adopt that ([0306105](https://github.com/google/stellar-engine/commit/03061056afdea1b5ee15bef477e9ddf9ba8f6ea4))
* broke up stages and blues ([491e37d](https://github.com/google/stellar-engine/commit/491e37daedfe5cd44550ada727dc994569d93406))
* Changed the descriptions for the database flags. ([97fc49f](https://github.com/google/stellar-engine/commit/97fc49f28cc48ebab8390bd67b27905d1fc542a8))
* Changed the descriptions for the database flags. ([f074f55](https://github.com/google/stellar-engine/commit/f074f55958ba4602c1c4f2b122390bff47289de3))
* changed to default for public access, changed key name, several other minor changes ([f6789fc](https://github.com/google/stellar-engine/commit/f6789fc315ebe35eccd16ca369524382d8737744))
* Checkov ([c1ae3bc](https://github.com/google/stellar-engine/commit/c1ae3bcbc4c495a233c3d510a3848b50fe6c73f9))
* Checkov ([052ccd5](https://github.com/google/stellar-engine/commit/052ccd5a1102da4d0b23529ae67e464608623d91))
* cleaned up comments: ([b3a70c2](https://github.com/google/stellar-engine/commit/b3a70c20cd678b10512f584501a2d7a2b1696666))
* compliance ([7fcf9a0](https://github.com/google/stellar-engine/commit/7fcf9a0ee585e633a50b7f2a193bd20e4b70cfe1))
* compliance ([1f92e50](https://github.com/google/stellar-engine/commit/1f92e50c18da0b41c2e220764a9853f8519916cc))
* Compliance Benchmark 3.0 ([cf36da7](https://github.com/google/stellar-engine/commit/cf36da7d6eff6076eb100f0fb97f95b9443295c1))
* Compliance Benchmark 3.0 ([913fe60](https://github.com/google/stellar-engine/commit/913fe60781f53f3e819072ee598e01fff4aaaebe))
* Compliance Benchmark 4 - Compute / GKE ([76eeee1](https://github.com/google/stellar-engine/commit/76eeee1e230913f55b205091b0b3ac26753fba69))
* confirming it will fail ([9f7d1d1](https://github.com/google/stellar-engine/commit/9f7d1d1dc2b5ba3d025a5e200070433c735ed28d))
* Docs fixes ([12d25a3](https://github.com/google/stellar-engine/commit/12d25a325b2d88e11b45bd2d59eba46168864227))
* DR-288: Implement tflint in Gitlab Pipeline ([0ba2cf2](https://github.com/google/stellar-engine/commit/0ba2cf24427397762ee35c5cf12401cbaf8caee4))
* DR-288: Implement tflint in Gitlab Pipeline ([5e8ecb2](https://github.com/google/stellar-engine/commit/5e8ecb2c4f4a8d2f9d88f4901456f214dda55f2b))
* failing pipeline ([18e8d1f](https://github.com/google/stellar-engine/commit/18e8d1f606d0a1d4f05929ce4ec86c5ca2f30da2))
* Fix DR-285 ([f1b48d8](https://github.com/google/stellar-engine/commit/f1b48d8fd81eb24f77b5f5b3170937e1d1e54dd3))
* Fix DR-285 ([3ff2d8d](https://github.com/google/stellar-engine/commit/3ff2d8df842ac19c2eec44e49aa2fe6c955517f4))
* fixed broken pipeline ([551b790](https://github.com/google/stellar-engine/commit/551b790985ded142a2f28ad32cf419b70c64d6af))
* fixed readme for dataflow ([3b801de](https://github.com/google/stellar-engine/commit/3b801dede74150a0f1cafbf103c78980a4ce5602))
* fixed readme for dataflow ([50551f2](https://github.com/google/stellar-engine/commit/50551f2a591c977789e666937ffe17983c55bc27))
* Fixed spacing ([96b32d3](https://github.com/google/stellar-engine/commit/96b32d3ee792c829d53b649fb90346de21e9390f))
* fixed/troubleshooted broken pipeline ([d173b13](https://github.com/google/stellar-engine/commit/d173b1360460ced846be688e18873197866bf45d))
* Fmt check ([03e944c](https://github.com/google/stellar-engine/commit/03e944ca97c9f2d57eb96252ec7c636d4d6c0f9a))
* formatting ([a5f0807](https://github.com/google/stellar-engine/commit/a5f0807d9b19fbd2fd51779eafcd9efcf6edd633))
* gcs-compliance ([cea7be2](https://github.com/google/stellar-engine/commit/cea7be2e68c5ce3caa87f5a5e1ac6f7619070979))
* giving user the choice of enforced or inherited ([f16cd65](https://github.com/google/stellar-engine/commit/f16cd65b672f1977fd73b7f1981dd82ecebb56c3))
* i hate terraform ([25b22fd](https://github.com/google/stellar-engine/commit/25b22fd05c6e254bb1a3bf062598ca47cacb896a))
* i think im done ([4560936](https://github.com/google/stellar-engine/commit/45609368c0127e632f8c6ac89301d7000e773b51))
* Implemented all CIS Compliance Benchmark 4.X compatible with files in an IL5 AW Folder ([82ba0cf](https://github.com/google/stellar-engine/commit/82ba0cfb1707495a16ebfdf8f031ad0c771c91fa))
* Implemented check_documentation.py ([73ae44d](https://github.com/google/stellar-engine/commit/73ae44ddfddf04294a092c2313eec44c1ef8f9a3))
* Implemented CIS Compliance Benchmark 6.2 in postgres ([dc3c694](https://github.com/google/stellar-engine/commit/dc3c694d3ae63d51c685d2fc882cdb15abfcc9b1))
* Implemented CIS Compliance Benchmark 6.2 in postgres ([4ced35d](https://github.com/google/stellar-engine/commit/4ced35d3c6140c180795d09fc28fe82755dcc5fb))
* minor bq changes (allows table specification, cleaned up iam) ([a90614f](https://github.com/google/stellar-engine/commit/a90614f20c60a9674f246cb3c1c8b84289eddfbf))
* Minor BQ updates ([76d9e4d](https://github.com/google/stellar-engine/commit/76d9e4d5121e5c28ac1a1a6cd0032b468d40294b))
* Modified the log_min_duration_statement variable. ([9859125](https://github.com/google/stellar-engine/commit/9859125eca8a1a721ed67dcaab2da3b809cc65e6))
* Modified the log_min_duration_statement variable. ([2d02073](https://github.com/google/stellar-engine/commit/2d02073a55462ef1724ab422b51b8fc991a4e489))
* Move all of the different folders created as part of the 1-resman stage under our new assured workload folder ([ab5241a](https://github.com/google/stellar-engine/commit/ab5241af3807fe47f165e34cbd10ed86a7d0f71e))
* Move the 0-bootstrap projects into the new AW folder ([ac5af17](https://github.com/google/stellar-engine/commit/ac5af17fb11c0199a3613992c2fa87133870a128))
* pipeline ([977f376](https://github.com/google/stellar-engine/commit/977f3760e8b59be201e87571332333202712fb84))
* pipeline ([4f4d07f](https://github.com/google/stellar-engine/commit/4f4d07fefe0d3990a3ff6cd1a8958e83d4f37152))
* pipeline ([2227d26](https://github.com/google/stellar-engine/commit/2227d26e4a65474824cb9eccdbe6b58cf7a17e34))
* pipeline ([474c502](https://github.com/google/stellar-engine/commit/474c50246bbf0595f315dec1c5d236c5c18c72f5))
* pipeline works ([0c980e9](https://github.com/google/stellar-engine/commit/0c980e9ec9cb7ae0ce5830ddb27adb92d02c8f5e))
* Postgres CIS Compliance Benchmark 6.2 ([739a748](https://github.com/google/stellar-engine/commit/739a7482f04992cc73a3901158701806557117c6))
* Postgres refactor ([4141423](https://github.com/google/stellar-engine/commit/414142344afeba9635ef2d090346dbd9a3778a9b))
* Postgres refactor ([c415e34](https://github.com/google/stellar-engine/commit/c415e34a25e6964885fb7f74a1fb02362318bff2))
* ran tf fmt ([15087ef](https://github.com/google/stellar-engine/commit/15087efb5897a8315ee9af12a51b5363c910cbc9))
* readded validation ([e724c4f](https://github.com/google/stellar-engine/commit/e724c4fdde97cb0bd9e815b1e7026551adb3bd31))
* refactor ([2a9b54e](https://github.com/google/stellar-engine/commit/2a9b54e40beda104d0971af84a5d4144ced1704a))
* removed comments ([f1024a8](https://github.com/google/stellar-engine/commit/f1024a8628fb6f0653e6ac4698d634fc6d2bf83a))
* removed mock files ([5ac4430](https://github.com/google/stellar-engine/commit/5ac443012aae79db64160677b047367e1f46f671))
* removed space ([0cff16c](https://github.com/google/stellar-engine/commit/0cff16c2c502fe942f8874bd99737060789859a9))
* removed space ([79a4bd4](https://github.com/google/stellar-engine/commit/79a4bd4388530dfbdc200f3df28d697c37730c11))
* running validate in parent folders ([c3f26c6](https://github.com/google/stellar-engine/commit/c3f26c6981755bc075fbcc0347d939c5fb5d5a03))
* Single Assured Workloads folder ([5a7b8de](https://github.com/google/stellar-engine/commit/5a7b8de8a8939f361862f5edfacc22ee04690003))
* some updates to stages-aw ([6b03d31](https://github.com/google/stellar-engine/commit/6b03d31de3196464c66390cd7e1ba7a2c2f1781e))
* swapped out hardcode name for job w/ var ([001800d](https://github.com/google/stellar-engine/commit/001800dfc4d75cfccc8e58cfd114ec6b6f7f337a))
* swapped out hardcode name for job w/ var ([1eb8f84](https://github.com/google/stellar-engine/commit/1eb8f843dcd217b8ed912fb01bd6fa9573c0f608))
* Terraform the CNAP ([2a98974](https://github.com/google/stellar-engine/commit/2a989743f27a394431b00bb63dd311e1a747eea5))
* Terraform the CNAP ([d6caaba](https://github.com/google/stellar-engine/commit/d6caaba7ec499aaf2790156aa04ea6373a790952))
* test ([0601a0b](https://github.com/google/stellar-engine/commit/0601a0b193a06ffa70e80e3a5430684488ff34e3))
* test ([096c66a](https://github.com/google/stellar-engine/commit/096c66a354a77cbdea8dce5399964c86ef62a14a))
* test ([52455be](https://github.com/google/stellar-engine/commit/52455be7fbfbe92fc31670e82a8c1febd2548122))
* unbroke fmt ([16181fa](https://github.com/google/stellar-engine/commit/16181fa4c2b16b8f5eb469526b091133451a9676))
* unbroke tflint ([1d9875c](https://github.com/google/stellar-engine/commit/1d9875cf299e23142a4d44a289a2100df4162302))
* uncommented out gitlab ci ([d2370bf](https://github.com/google/stellar-engine/commit/d2370bfcbd18b59599b843412b921cb35b802e09))
* updated ci ([58a7aa7](https://github.com/google/stellar-engine/commit/58a7aa7a99ce3a9c85dce74d9ec49194d7eadc7d))
* Updated Dataflow ([2cd25e5](https://github.com/google/stellar-engine/commit/2cd25e58646f7bb95f6a756dfc269b12dd989e2f))
* updated readme ([d2b195a](https://github.com/google/stellar-engine/commit/d2b195a45975e8ec9c67fe1a39a92cffdc236ca5))
* updated readme ([ec911d4](https://github.com/google/stellar-engine/commit/ec911d4ff2635579b5aad9bc2894cf98296a5e73))
* working on all blueprints ([5f3359e](https://github.com/google/stellar-engine/commit/5f3359ed2dffa42cdb4ed22f0c4253c99a5c0bd0))

## [1.0.1](https://github.com/google/stellar-engine/compare/v1.0.0...v1.0.1) (2024-07-30)


### Features

* Added dataflow job that reads messges from pub/sub and writes them to BigQuery table, utilized google template pub/sub-BigQuery, adjusted README. ([7afca40](https://github.com/google/stellar-engine/commit/7afca40464e2c73c96dd9bd10e83d239fed449bc))
* Added dataflow job that reads messges from pub/sub and writes them to BigQuery table, utilized google template pub/sub-BigQuery, adjusted README. ([c4cf7e3](https://github.com/google/stellar-engine/commit/c4cf7e39e9be30427a8d81ef62f84ba426beff3d))
* added gcs bucket module and changedREADME. ([3d90adf](https://github.com/google/stellar-engine/commit/3d90adfaa6ac2230169204ddd4a4d401bc5d7ffe))
* added gcs bucket module and changedREADME. ([27cc3cf](https://github.com/google/stellar-engine/commit/27cc3cf27d50cc27feeaa24f5ae72b44177662fb))
* Added netowrk for the data pipeline. ([0b55f6b](https://github.com/google/stellar-engine/commit/0b55f6b41389996d61f4f1f7742d5684be7ae023))
* Added netowrk for the data pipeline. ([ac461fc](https://github.com/google/stellar-engine/commit/ac461fcef4d9719323b8c964742caf0699f850f5))
* added README ([85edfb0](https://github.com/google/stellar-engine/commit/85edfb066c8fe4c0c4c3bd6f3fe2faa3ef41e3d8))
* added README ([e0038dd](https://github.com/google/stellar-engine/commit/e0038dd6dd855e991c9fd618e5d0631505f69634))
* added some TODOs ([c61076a](https://github.com/google/stellar-engine/commit/c61076a72fee5158972dd70b774b9cbe729a90db))
* added some TODOs ([0bbc01c](https://github.com/google/stellar-engine/commit/0bbc01c106a099553e7d83106a56dbd5b0f4d164))
* Added troubleshooting instructions and disclaimer, cleaned up spacing. ([d9e016c](https://github.com/google/stellar-engine/commit/d9e016cc53c5fdf335b1e5bae253f06df54f1854))
* Added troubleshooting instructions and disclaimer, cleaned up spacing. ([ae60b17](https://github.com/google/stellar-engine/commit/ae60b172ddc201cb70d84047e13dd8ebc1e773da))


### Bug Fixes

* adding gcs module and dynamically creating service account. ([f2a436e](https://github.com/google/stellar-engine/commit/f2a436e79db3da6474f5e44a826ce8409623a701))
* adding gcs module and dynamically creating service account. ([68f928d](https://github.com/google/stellar-engine/commit/68f928db6fdb772f9788731e74ad08cee98b0fa0))
* adjusting files ([d2c46a8](https://github.com/google/stellar-engine/commit/d2c46a874901ca8d8e2d24237f7c24094a89f09a))
* adjusting files ([f12a440](https://github.com/google/stellar-engine/commit/f12a440dedab46e0c1353a04875b92d638b00623))
* adjusting files ([435c9c1](https://github.com/google/stellar-engine/commit/435c9c1fc84ac9cdb50c5daa0267af4fee4c1e9d))
* adjusting files ([9cc75bd](https://github.com/google/stellar-engine/commit/9cc75bd28135882a7c282bb08a5b9b24b00f7118))
* adjusting files ([27aeaed](https://github.com/google/stellar-engine/commit/27aeaed7d872da3d631dd2837a1978fe04b858ac))
* adjusting files ([3399421](https://github.com/google/stellar-engine/commit/339942102460f658044908cce5cc6bcc6d06c05a))
* all working ([42a337d](https://github.com/google/stellar-engine/commit/42a337dbb114e7948977b472846846859530d537))
* all working ([d344d0e](https://github.com/google/stellar-engine/commit/d344d0ecada28d2ed6bc7351a32b2d51558daffd))
* all working ([6af2409](https://github.com/google/stellar-engine/commit/6af24091afcb9bf6ca3fb55883e1097392925f4b))
* all working ([1552b71](https://github.com/google/stellar-engine/commit/1552b718d31fb83666eb5d93c19ab441252f9a0d))
* change sa perms ([5869049](https://github.com/google/stellar-engine/commit/5869049e1f0ecc2e5784c6756344dc4e7795a577))
* change sa perms ([d60826e](https://github.com/google/stellar-engine/commit/d60826eb243d35fed20841e3a4b183c454330316))
* changed file name from feature-dataflow to simply dataflow ([62ddcde](https://github.com/google/stellar-engine/commit/62ddcde4a12c01b099393079cd6521fa70193837))
* changed file name from feature-dataflow to simply dataflow ([7da9efc](https://github.com/google/stellar-engine/commit/7da9efcd55bb77b630ebadc9c0ad58c2cf51bcea))
* Changed key name and changed the spacing. ([b723ba0](https://github.com/google/stellar-engine/commit/b723ba014d8ea1ccb618fb3b227698904e3be08a))
* Changed key name and changed the spacing. ([cd91954](https://github.com/google/stellar-engine/commit/cd91954b30bd9636556e3f50a3c283e9f12f0687))
* Changed the placement of screenshot of storage bucket README.md ([639a099](https://github.com/google/stellar-engine/commit/639a099bec4c0814a432e2ccd41a69054d875495))
* Changed the placement of screenshot of storage bucket README.md ([ededbd8](https://github.com/google/stellar-engine/commit/ededbd8d7821afce012e479182ad23c9f2e33534))
* Changed the spacing. ([28efb80](https://github.com/google/stellar-engine/commit/28efb805c1f536920626104e9e65cc3b3cbb511d))
* Changed the spacing. ([5c7a283](https://github.com/google/stellar-engine/commit/5c7a283370bd21cdec07be02abeaa89c2c288270))
* Changed the spacing. ([ca6c784](https://github.com/google/stellar-engine/commit/ca6c784675271b618a36d83d1d72297b722b948d))
* Changed the spacing. ([bf7e502](https://github.com/google/stellar-engine/commit/bf7e502e2bde60255cd65406282146701d4d6298))
* cleaned up code ([3c6c70f](https://github.com/google/stellar-engine/commit/3c6c70fcb04dbde2850ad480369823e4194450c7))
* cleaned up code ([45583af](https://github.com/google/stellar-engine/commit/45583afa44061ec1f1e44ba0882610572a0b607e))
* cleaned up vars file ([36e27cc](https://github.com/google/stellar-engine/commit/36e27cce4305c852267dd81414aa62df8d54b07c))
* Dataflow ([52d0295](https://github.com/google/stellar-engine/commit/52d02957614eea6495c40acbdf1e017537ec998d))
* Dataflow to feature-dataflow ([0cabc13](https://github.com/google/stellar-engine/commit/0cabc1356843cf2e0d19a14b40fc48ef17fa4216))
* Dataflow to feature-dataflow ([80a6328](https://github.com/google/stellar-engine/commit/80a6328df792e8a419c0ad1c4eb921d092b62efb))
* Delete blueprints/il5/dataflow/google-cloud-sdk-xxx.tar.gz ([407b915](https://github.com/google/stellar-engine/commit/407b9159752bd2628bbb537c4094051289394052))
* Delete blueprints/il5/dataflow/google-cloud-sdk-xxx.tar.gz ([84b80f8](https://github.com/google/stellar-engine/commit/84b80f8f02b1e23ccb49b07b41c8812ef57c4b61))
* Delete blueprints/il5/dataflow/main.tf ([0dfe058](https://github.com/google/stellar-engine/commit/0dfe058920df6163e3c0c6c75ea86988f0d6ed6f))
* Delete blueprints/il5/dataflow/main.tf ([f79412f](https://github.com/google/stellar-engine/commit/f79412f9ac40db5c9bf0f089c8726ed926c18b6f))
* Delete blueprints/il5/dataflow/outputs.tf ([36a3508](https://github.com/google/stellar-engine/commit/36a3508a2042053ea877b5d385cddea1174e41af))
* Delete blueprints/il5/dataflow/outputs.tf ([1ee1101](https://github.com/google/stellar-engine/commit/1ee1101d4ccacd107ad3c2bdfae6a308675a4e28))
* Delete blueprints/il5/dataflow/terraform.tfvars.sample ([dc37e7d](https://github.com/google/stellar-engine/commit/dc37e7d6e91f680812227ca1875b83f8cad5cf65))
* Delete blueprints/il5/dataflow/terraform.tfvars.sample ([4b0c198](https://github.com/google/stellar-engine/commit/4b0c198c4abc4e8bfff8c46b61b314b7b43739bf))
* Delete blueprints/il5/feature-dataflow/README.md ([6c4931b](https://github.com/google/stellar-engine/commit/6c4931b39d3fe0c1640b2a2f923b97514de021aa))
* Deleting unnesseccary files ([9f5c883](https://github.com/google/stellar-engine/commit/9f5c883bdcf53ece5e054322d46d2fab40390b0c))
* Deleting unnesseccary files ([ba41ea5](https://github.com/google/stellar-engine/commit/ba41ea531378079d779ff6bb043d59e382b7799a))
* Explained in the README that customer needs existing projects with billing enabled to use data source and to create their tfvars file. ([94a688f](https://github.com/google/stellar-engine/commit/94a688f80565584d3e6239c7cc6bd64ed211d04b))
* Explained in the README that customer needs existing projects with billing enabled to use data source and to create their tfvars file. ([1d4a95e](https://github.com/google/stellar-engine/commit/1d4a95e942cb54eed0dc5be56bd040b01bc2c392))
* getting big query included ([de32cac](https://github.com/google/stellar-engine/commit/de32cac9e43e5121769712b8056df19478265f6a))
* getting big query included ([3f30073](https://github.com/google/stellar-engine/commit/3f30073b1250338af915bf7c7da70a6f5a5139d0))
* I deployed bucket, CMEK, IAM roles ([8a84637](https://github.com/google/stellar-engine/commit/8a8463715735bc2692703156a9c75ec838bc9807))
* I deployed bucket, CMEK, IAM roles ([8c75d0b](https://github.com/google/stellar-engine/commit/8c75d0b22e8e2023f02c92354ff58c0eebe518e9))
* I have changed .email property to .member in service account ([9fdeae0](https://github.com/google/stellar-engine/commit/9fdeae0fadb798e9535fbc4b64f228604de0545c))
* I have changed .email property to .member in service account ([b419aa0](https://github.com/google/stellar-engine/commit/b419aa0c480645e65d1866cf377f3788a28e16ed))
* made a service account,cmek,iam user permissions, dataflow bucket, utilized terraform dataflow module. ([a0e0bcb](https://github.com/google/stellar-engine/commit/a0e0bcb09a02006bdddcd045361225be1abfe387))
* made a service account,cmek,iam user permissions, dataflow bucket, utilized terraform dataflow module. ([95e08a5](https://github.com/google/stellar-engine/commit/95e08a5709e88ad8ef8aa3dbc5760e983220e8e3))
* made subnet, network, updated, README, updated, tfvars, updated screenshot ([150fccb](https://github.com/google/stellar-engine/commit/150fccb796c5a182ecd22f9ce9e4b279048b1978))
* made subnet, network, updated, README, updated, tfvars, updated screenshot ([aa08ca9](https://github.com/google/stellar-engine/commit/aa08ca97f68f4165a3bfb81809bbc284a41a82a0))
* making progress ([a5dd2b3](https://github.com/google/stellar-engine/commit/a5dd2b33dd54b15d27cef143cdeb02943dfb2427))
* making progress ([8aa1de7](https://github.com/google/stellar-engine/commit/8aa1de7f1afe32fd3d091e7e7cba80a884a0864a))
* Minor change in comment ([a98e851](https://github.com/google/stellar-engine/commit/a98e8513a6f255b44bd5b0690ee603fd687af930))
* Minor change in comment ([cde2ed5](https://github.com/google/stellar-engine/commit/cde2ed5fa2d4e311636f1edacc0ee9cab2a38bcf))
* minor change to network ([2b8905d](https://github.com/google/stellar-engine/commit/2b8905d05aa2386c8a7ad017d17a7fbf36ed1042))
* minor change to network ([7ddbc24](https://github.com/google/stellar-engine/commit/7ddbc24a21d44bee6c52c523db18365a2a709a7d))
* Placing dataflow job screenshot in README.md ([dc00468](https://github.com/google/stellar-engine/commit/dc004688614253b0e1bd6b9d4b17055b386ae7ab))
* rebased with master ([bd9989c](https://github.com/google/stellar-engine/commit/bd9989c62e7a857a5784d3ae14d5430b4581e391))
* refactored dataflow by manually injecting bigquery dataset and pub-sub configuration to ensure code is complicant from a customer POV. ([e196b92](https://github.com/google/stellar-engine/commit/e196b92c198e8de346dd7454bb7f68796031b970))
* refactored dataflow by manually injecting bigquery dataset and pub-sub configuration to ensure code is complicant from a customer POV. ([0a79377](https://github.com/google/stellar-engine/commit/0a79377c47b3d1d337032ebff20f980c69a061a0))
* refactored dataflow by manually injecting bigquery dataset and pub-sub configuration to ensure code is complicant from a customer POV. ([5229f39](https://github.com/google/stellar-engine/commit/5229f391bbf477fd851093f8a24ff9e89fba1093))
* refactored dataflow by manually injecting bigquery dataset and pub-sub configuration to ensure code is complicant from a customer POV. ([f37a1f2](https://github.com/google/stellar-engine/commit/f37a1f280fe5d3f1f32872175ccb3f35c0f999e8))
* stuck ([9278e26](https://github.com/google/stellar-engine/commit/9278e26016de32a43a2b0221403a427c93eb3f4f))
* stuck ([f5b6c28](https://github.com/google/stellar-engine/commit/f5b6c280b0a7a4c44c8033b0f9445c9336dbf883))
* tf format ([d958f54](https://github.com/google/stellar-engine/commit/d958f54c9130d097403f42ec2a5d14cbb8fb2cac))
* tf format ([b4af14e](https://github.com/google/stellar-engine/commit/b4af14e82f566f79b4ee4fcdeb3761fb82e659a9))
* Update README.md ([1ba7399](https://github.com/google/stellar-engine/commit/1ba73998513fc56b5d1b9332f4c7a13593b49611))
* Update README.md ([55d6a67](https://github.com/google/stellar-engine/commit/55d6a6706ceca02f5e928f9e51a4665b3c5796b2))
* Update README.md ([516f6ea](https://github.com/google/stellar-engine/commit/516f6eaf7bc56601bee001c2c0a3f1dae6c17167))
* Updated README with permissions that customer needs to enable. ([ed84d7f](https://github.com/google/stellar-engine/commit/ed84d7fa053bdc1d555d1b171509e1290b613ef9))
* Updated README with permissions that customer needs to enable. ([dbae2ba](https://github.com/google/stellar-engine/commit/dbae2bacab258a9733f4b8f9ba0e8ad9b1fa7b8f))
* Updated README with permissions that customer needs to enable. ([f86e702](https://github.com/google/stellar-engine/commit/f86e702939f2ae9482d7875b13d12dfbb48bb904))
* Uploaded storage bucket screenshot to README.md ([3a56d83](https://github.com/google/stellar-engine/commit/3a56d831c08666e5fe912b4209b184bbc64fba2d))
* Uploaded storage bucket screenshot to README.md ([0a0216a](https://github.com/google/stellar-engine/commit/0a0216a461db54ea0d97d6f1958b9abb90eb30b9))
* Whenever I change the name on local machine, new files get added to a new folder. I'm deleting this ([805da7b](https://github.com/google/stellar-engine/commit/805da7b1ec77dad959da99c83ca3b1d0b05d9398))
* Whenever I change the name on local machine, new files get added to a new folder. I'm deleting this ([3e1cc3a](https://github.com/google/stellar-engine/commit/3e1cc3aa5345797b562346b75914cade9a8cb61c))
* Whenever I change the name on local machine, new files get added to a new folder. I'm deleting this ([251c823](https://github.com/google/stellar-engine/commit/251c823f033efdd7b888936063ca8a20d54dc76c))
* Whenever I change the name on local machine, new files get added to a new folder. I'm deleting this ([bc8e9e2](https://github.com/google/stellar-engine/commit/bc8e9e26b703faea54b48e207453ee7ae13199e4))
* Whenever I change the name on local machine, new files get added to a new folder. I'm deleting this ([05f15ca](https://github.com/google/stellar-engine/commit/05f15cad8979e306372472701a2e85998294780e))
* Whenever I change the name on local machine, new files get added to a new folder. I'm deleting this ([2ae71f3](https://github.com/google/stellar-engine/commit/2ae71f397b2e103b7d39377961b9e9bebd9aad41))
* Whenever I change the name on local machine, new files get added to a new folder. I'm deleting this ([8048172](https://github.com/google/stellar-engine/commit/8048172a66d522d9970b3aaf9e2979b6cca2ebdb))
* Whenever I change the name on local machine, new files get added to a new folder. I'm deleting this ([4a8886c](https://github.com/google/stellar-engine/commit/4a8886cd9b7b3631cd1a5b22452e8303b9e6ede2))
* working ([342b6fe](https://github.com/google/stellar-engine/commit/342b6fe7c049b488a4198e716a9868ed07c5aa2a))
* working ([49888cc](https://github.com/google/stellar-engine/commit/49888cc63217efa40a1f94304293e6adc1bd8cdf))
* working ([16504aa](https://github.com/google/stellar-engine/commit/16504aa37292c4e0e4effbb32c22b33970f016fb))
* working ([a53adb8](https://github.com/google/stellar-engine/commit/a53adb89dd49c85333d1d9ae17666946173b14d5))

## [1.0.0](https://github.com/google/stellar-engine/compare/v0.9.0...v1.0.0) (2024-07-19)


### Features

* pull in private service connect module from CFT ([4487583](https://github.com/google/stellar-engine/commit/44875835298a1ae9433f5ee1daec9dae10a5aa7f))


### Bug Fixes

* Attempt 1 ([1aac113](https://github.com/google/stellar-engine/commit/1aac1133db15b47ec6e2ec200d5265ab286dd8af))
* Begin updating org-policies ([a1d3765](https://github.com/google/stellar-engine/commit/a1d376589d3b7298bad4e11e9a7a89615455cc9d))
* cidr change ([f29b1df](https://github.com/google/stellar-engine/commit/f29b1df0b7645b4356c2d0bd533c12a752657bfd))
* FedRAMP High network Compliance ([e1b4793](https://github.com/google/stellar-engine/commit/e1b4793289cad42b3f49e56e2e1b7c6d8c7181fd))
* FedRAMP High network Compliance ([48a4b75](https://github.com/google/stellar-engine/commit/48a4b753725311104562fd9614f5aa4bf0dfc78f))
* Forgot the customized policies ([89a9778](https://github.com/google/stellar-engine/commit/89a9778bcc40af54792ae09e92127652acf859ca))
* gke refactoring ([b8bc04d](https://github.com/google/stellar-engine/commit/b8bc04dc5c336eb423e4eccc6c12ca5d3d3e6554))
* Merged the org policies from stellar engine and CFF ([d4664dc](https://github.com/google/stellar-engine/commit/d4664dc5d864bdcc63d9ba40de7ae48afff1f116))
* Move the org-policies from the old Stellar Engine project to the new project ([48e8300](https://github.com/google/stellar-engine/commit/48e8300b6874b1b343e5cabd4b243c0114bca9fa))
* Refactor VPC Peer , Shielded VM ([986bcbd](https://github.com/google/stellar-engine/commit/986bcbd9751065cce3c6ffd0e77b9e2300eed2fa))
* remove 0 cidr ([60187d6](https://github.com/google/stellar-engine/commit/60187d61ad876e210312f4b044bd8087c369e971))
* Shielded VM Refactor ([c53df5f](https://github.com/google/stellar-engine/commit/c53df5fa26a044ba2a7111c59fa33550ec2383a4))
* size, fmt, variable ([66056b0](https://github.com/google/stellar-engine/commit/66056b0d6e77b54ade214ce7b2ad93ac56ede7b4))
* Templated policies are now customized to the organization ([67b26b8](https://github.com/google/stellar-engine/commit/67b26b8ebf1ba42add0867b511fbad43e2a92dc0))
* Update .gitlab-ci.yml file ([217a8a5](https://github.com/google/stellar-engine/commit/217a8a55a6d221cd46eecc1f6e325fe51b2618e9))
* Update .gitlab-ci.yml file ([7979b96](https://github.com/google/stellar-engine/commit/7979b96e966ac62eab52a9750e635dd6068514bc))
* Update .gitlab-ci.yml file ([845f3d4](https://github.com/google/stellar-engine/commit/845f3d419ad59611a1fb41bb51a3c3bbfbeee611))
* Update .gitlab-ci.yml file ([c08b392](https://github.com/google/stellar-engine/commit/c08b39241902e42b617af37010b48e8c5273f1d4))
* Whitespace changes, remove a few could-have's because they were throwing errors ([b4a612e](https://github.com/google/stellar-engine/commit/b4a612eb132fc2486832ddd4650cc6261e61b25f))

## [0.9.0](https://github.com/google/stellar-engine/compare/daily-2024.06.12...v0.9.0) (2024-06-28)


### Features

* Add assured workloads and access transparency to the 0-boostrap phase ([a6f4a89](https://github.com/google/stellar-engine/commit/a6f4a8923c359e5b2c674afdcbf5ab9ea27d0718))
* Add DMZ subnet for us-east4 ([1539722](https://github.com/google/stellar-engine/commit/15397228855fabcc1b261b9bec43a80d6eaefc35))
* Add mgmt subnets ([91f821f](https://github.com/google/stellar-engine/commit/91f821f1c1ef8d84d0af95a67280811244e2bce9))
* Add outputs file to capture the registries and repositories created by this blueprint ([f15f804](https://github.com/google/stellar-engine/commit/f15f80477bba690ad64360c5e0a63a1be8fb1c90))
* Add the consumer VM tf, and the startup-script template ([822f35c](https://github.com/google/stellar-engine/commit/822f35c138dc995d33697555d3013df78d0add98))
* added depends_on for kms and added sample to create new key to tfvars.sample ([a1b060f](https://github.com/google/stellar-engine/commit/a1b060f48fe1003bb22d702f23f66e3aabe818e3))
* Added files ([9626668](https://github.com/google/stellar-engine/commit/9626668309a4fb260585a0b64b149dedab1cdeda))
* added instructions and code for importing keystore/key ([4e5b914](https://github.com/google/stellar-engine/commit/4e5b9146a11acbd6866daaf526b5e3bb9b775847))
* added kms var ([74e263c](https://github.com/google/stellar-engine/commit/74e263c6a67d714641439eb99ad760ca5ec08923))
* Create demo vm that shows users how to use the Artifact Registry in CentOs ([f4cc563](https://github.com/google/stellar-engine/commit/f4cc563cf8a3adce53a16bcd4cda0f557f0e15c1))
* initial cluster GKE ([8249816](https://github.com/google/stellar-engine/commit/82498165af7bf7de5a94d979d06a100b2faf1693))
* Initial commit of artifact registries ([3626eb8](https://github.com/google/stellar-engine/commit/3626eb821d29ae6ce3dbffa533a0477407b074bb))


### Bug Fixes

* all good i hope ([d7e33f6](https://github.com/google/stellar-engine/commit/d7e33f6f0ef07bb7d2d3178451624f4b3d97460c))
* approach on security onion ([550716f](https://github.com/google/stellar-engine/commit/550716f37ca6ea0d4c988197189c39a3fb4cdd09))
* bq project read me and formatting ([5ff6411](https://github.com/google/stellar-engine/commit/5ff64113a3955db5152dfe6ee85e4606c1c58cec))
* Break the dependency loop ([0860537](https://github.com/google/stellar-engine/commit/0860537aa0b8bebde70f2f35405753688e3dde3a))
* Centos full deployment for security onion ([459eb46](https://github.com/google/stellar-engine/commit/459eb46fa0bf3f88e459add3e1f754d886d0db14))
* changed module vpc to mgmt vpc ([bd507b3](https://github.com/google/stellar-engine/commit/bd507b30c0605a5c977f786a93dcfb29924fa13e))
* changed service account ([01274d4](https://github.com/google/stellar-engine/commit/01274d419c465f7832df3d2d50e29dff370eb103))
* changed vpc group name ([e43f160](https://github.com/google/stellar-engine/commit/e43f160d807b75133effbbb0897e2b0fcb5719c2))
* changes ([c88f94d](https://github.com/google/stellar-engine/commit/c88f94d09f706b9658387e861b779716b4a3c79c))
* Changint the IP to Other for Security Onion ([ee14ed2](https://github.com/google/stellar-engine/commit/ee14ed296bf7ae902f91d3ad6df2b57eacdf06a5))
* Cleane up files ([07e9a22](https://github.com/google/stellar-engine/commit/07e9a22a261cec0ecc05cfb4895d8d9008ee6409))
* cleaned up branch ([92d05ab](https://github.com/google/stellar-engine/commit/92d05abaa9fdc12cf73451764e247864e2de6cf0))
* Cleaned up branch ([6d21877](https://github.com/google/stellar-engine/commit/6d21877ea1a8e06bd716e41993ff016d366aad39))
* Cleaned up branch ([ff60b08](https://github.com/google/stellar-engine/commit/ff60b0874f7e1ccf6888d354d8905fbbb1243690))
* Cleaned up branch ([619d771](https://github.com/google/stellar-engine/commit/619d771ea4778038698e249f24c181fc2b269f98))
* Cleaning up branch ([d179080](https://github.com/google/stellar-engine/commit/d179080d92cf7b30897d40ed5d72c59a000dddc8))
* comment the default values in variables ([c2dcc73](https://github.com/google/stellar-engine/commit/c2dcc7347b1bea7d658e46a5f5b97491287b042d))
* comments fixed ([870590a](https://github.com/google/stellar-engine/commit/870590a2eeeade982beffa1a3b968c2442cf24eb))
* Compute Engine, Security onion ([7d9cd1d](https://github.com/google/stellar-engine/commit/7d9cd1d0f25accc96b950b0f6c2a33735b801310))
* depends on fix ([8e2c26c](https://github.com/google/stellar-engine/commit/8e2c26c3e0c2824929ee38c696fb61d0a449f51e))
* Enable the google API for artifact registry ([78e8538](https://github.com/google/stellar-engine/commit/78e8538e0121c75bd78f58ff77e0576d4f539a4e))
* enabled the Shielded Nodes, Data plane and binary authorization ([50ffeff](https://github.com/google/stellar-engine/commit/50ffeffb471f17a39ce71f60c14602d1b1462094))
* enabled the working nodepool ([d1bd312](https://github.com/google/stellar-engine/commit/d1bd3127146aa2aba78c02eab10323f1611ab7d0))
* example of variables ([efb5e85](https://github.com/google/stellar-engine/commit/efb5e8539175850b231d6c8232734e28c826c256))
* Fix how we combine the docker registries for output ([2d7f6ad](https://github.com/google/stellar-engine/commit/2d7f6ad3822f763246f98e63cdfd7889dacdaef3))
* fixed key perms ([5ecc0e5](https://github.com/google/stellar-engine/commit/5ecc0e51713b6d8000a814b9c4babd056e4663b7))
* fixed step 3 ([df57156](https://github.com/google/stellar-engine/commit/df57156b12b2c21543ec8ed56486613440e9d1f6))
* Formatting and read me updates ([1bc4394](https://github.com/google/stellar-engine/commit/1bc4394743ab764383fa2af7baffd758d7bbb318))
* fully updated read me ([0211a0f](https://github.com/google/stellar-engine/commit/0211a0fde03dd9d2735164674be0817a9ec9fa17))
* Gave IAM permissions to group emails and using data to look up existing subnet in respect to exisiting vpc in il5 envirionment, added and changed variables file, tfvars, and test file, README accordingly, and cleaned up files to make spacing and remove extra spacing. ([4ef5e92](https://github.com/google/stellar-engine/commit/4ef5e92b6b939e3148d187cfda9073c3fa1d499a))
* Gave IAM permissions to group emails and using data to look up existing subnet in respect to exisiting vpc in il5 envirionment, added and changed variables file, tfvars, and test file, README accordingly, and cleaned up files to make spacing and remove extra spacing. ([d8bf084](https://github.com/google/stellar-engine/commit/d8bf084c9cdc36161af733add8be97e97a214795))
* gke cluster KMS service account ([ebd0f32](https://github.com/google/stellar-engine/commit/ebd0f32109001a134fb824ec500ec09fc14ba78d))
* GKE Default to change ([5c96734](https://github.com/google/stellar-engine/commit/5c96734da3bbe112d66cccf3277e900862e150f4))
* GKE Key name ([2078cda](https://github.com/google/stellar-engine/commit/2078cdab25c3d0f65f737727b61733441b4e0559))
* GKE master_authorized_ranges , enable private end point ([779faf6](https://github.com/google/stellar-engine/commit/779faf66bdea15e3b2bf6ed4b6c48562a7a3214a))
* Google Cloud SQL for PostgreSQL ([ef99140](https://github.com/google/stellar-engine/commit/ef991400e85c7842e1279798f13ec5dea074d100))
* Handle the folder or organization for the AW folder creation ([f548163](https://github.com/google/stellar-engine/commit/f548163eb6fad1c323ac222896aca66c3f5759a0))
* HSM KEY ([1b192f8](https://github.com/google/stellar-engine/commit/1b192f8fe49c4b7d532098fa8e7dcf130ae8a832))
* I changed the README so that it clearly gives the directions on how to ssh into the bastion using gcloud and what each command does. ([1381105](https://github.com/google/stellar-engine/commit/1381105785d6b96f6ed2128c450effaf90685fd0))
* I took out the mgmt vpc and refered to data to look up the existing vpc in il5 tenant environment, ensured the README is updated in regards to all files, updated tfvars and varaibles, fixed spacing, and got rid of the unnecessary spacing. ([3b2923b](https://github.com/google/stellar-engine/commit/3b2923b22b8395f4f36c0b2563cebb3cc4aea225))
* I'm using vpc as a data to llok up the existing vpc from il5 tenants repository and created firewall ruless for ssh ([20ac93e](https://github.com/google/stellar-engine/commit/20ac93e3b6d2c265c2a635bcb738431296d424b2))
* iamge update ([51d97fe](https://github.com/google/stellar-engine/commit/51d97fe4a32720d87a944046fa2226f6443f9365))
* Ignore the tenant project tfvars.json files ([659a89b](https://github.com/google/stellar-engine/commit/659a89b068ac3e350cd5fb048e4f3f5f19e2487f))
* init ([5d9980e](https://github.com/google/stellar-engine/commit/5d9980ea4d8fa9006a3bbf49e1adafbe495ce9b5))
* Interpolate the strings because the data can't look up a project on bootstrap because the project won't exist yet. ([8f330de](https://github.com/google/stellar-engine/commit/8f330deb262cb70ee4fbf237a3d9522054769def))
* keys factors ([2112d25](https://github.com/google/stellar-engine/commit/2112d2515d19f30cc385e3913e32ae1f9dd1ba12))
* main version conflict check ([374ea60](https://github.com/google/stellar-engine/commit/374ea60cecc0c29ac72a78bf411a95a159783e7c))
* minor change to README and group email removed ([1570708](https://github.com/google/stellar-engine/commit/1570708c800a7e72e864b35f3aedc6c86a67f240))
* module for KMS ([f52036c](https://github.com/google/stellar-engine/commit/f52036cbfcd7aec2986b11852f46cc06d8f89681))
* More Read ME instruction ([b31a959](https://github.com/google/stellar-engine/commit/b31a959a61d977a99885c3438bebb3372ac7799b))
* node allocation per zone ([da2c155](https://github.com/google/stellar-engine/commit/da2c155e7a61209a117b4c658d0ccceae97d8385))
* node pool standarad configuration ([db20236](https://github.com/google/stellar-engine/commit/db202368992ad8b1bc3b8ef54ad0222809a85786))
* outputs arranged ([d262200](https://github.com/google/stellar-engine/commit/d262200a7e681563c587436cfd7c41782f2a6e7b))
* READ me for multiple project with terraform variables fixed ([6932eac](https://github.com/google/stellar-engine/commit/6932eacc641d4f5919c8ebdad4d8a5dd6e4154ce))
* read me inst ([f3d7273](https://github.com/google/stellar-engine/commit/f3d72737566e2368b2fa07902738e0afd681d63a))
* read me instructions ([b173aca](https://github.com/google/stellar-engine/commit/b173aca96238b0393b6939f968b7ac089200b31a))
* read the keys from module ([5da31ec](https://github.com/google/stellar-engine/commit/5da31ec5e3ff93412d77edbb982f4eafc71e4381))
* refactor variables name ([4228b1d](https://github.com/google/stellar-engine/commit/4228b1dd5948182f92feac6fbb00a5961a7e10d8))
* refactoring the gcp compute engine fw ([25f498a](https://github.com/google/stellar-engine/commit/25f498afd8031726a1ea6a202ccf73506c7026ad))
* refactoring the variables and read me instructions ([4ca5468](https://github.com/google/stellar-engine/commit/4ca5468274984247a3eaf2f0c90707978236bff8))
* Remove a data call to a project that won't exist yet on initial bootstrap ([69805fc](https://github.com/google/stellar-engine/commit/69805fcdf406621f086b572419734a8d4ca49ae4))
* remove project name ([4bb75da](https://github.com/google/stellar-engine/commit/4bb75da8525b5e4cfed60cf08ba1ddf5564a96db))
* removed email var as it is not used and updated tfvars.sample ([cbb2aca](https://github.com/google/stellar-engine/commit/cbb2aca4effc0500c54e7ff5eb71d084165a22e7))
* removed sourcerepo.googleapis.com as it is deprecated ([8a46b37](https://github.com/google/stellar-engine/commit/8a46b3797dc0a1b4014f16ea9309ff0bf57ef3f9))
* removing the NAT ([03920c8](https://github.com/google/stellar-engine/commit/03920c80473581158832ee2d128d1689437c70d7))
* Replaced dws email with admin email and group email with gcp devops email, adjusted files accordingly to match this change ([4891079](https://github.com/google/stellar-engine/commit/48910792bdd2967667d87809f1d21c2f68cbf7f6))
* revised keys ([427af54](https://github.com/google/stellar-engine/commit/427af54e7b68572de48fa7ce6dac8b6522b98b72))
* revision in main for wait condition ([7f19efe](https://github.com/google/stellar-engine/commit/7f19efe5d653bc909e6999e4f40495294f4a2fb0))
* security onion initial commit ([5ffd8a4](https://github.com/google/stellar-engine/commit/5ffd8a465846daededb8e233f4598f6851c1c927))
* security onion startup script ([f821222](https://github.com/google/stellar-engine/commit/f8212229b137256bc48fb3d3915ccd6173027ddf))
* setup instruction ([ab002c4](https://github.com/google/stellar-engine/commit/ab002c4c9f447b06dcf5eed5c63f5bff05d628bd))
* Switch all instances of kms within the Dino Runner contributions to use HSM in order to be IL5 ready ([8f48b2d](https://github.com/google/stellar-engine/commit/8f48b2dc6f163320413de8d03de5b59202990b9f))
* terraform module with main and output ([1e2a705](https://github.com/google/stellar-engine/commit/1e2a7058c26353c80148adbe7fbb20ead5067ec1))
* terraform sample ([e4b4d2b](https://github.com/google/stellar-engine/commit/e4b4d2bcc32847bc0e7fed32f916217f9789238a))
* terraform vars ([5ad32c4](https://github.com/google/stellar-engine/commit/5ad32c401d0496c64781fb51a2120fac3fd4816e))
* tf fmt ([5e0a38a](https://github.com/google/stellar-engine/commit/5e0a38ae9bd17dd201766fe9019e2d37e5940ecd))
* tf sample ([97d2e25](https://github.com/google/stellar-engine/commit/97d2e2552db6a14a34b54043fd10f0589e17b79a))
* Update gitignore ([21f31e4](https://github.com/google/stellar-engine/commit/21f31e49817ec0e048cb42413b444fb07eb40753))
* Update KMS key for docker-hub ([125c1cf](https://github.com/google/stellar-engine/commit/125c1cf5655d74dcdaf31bb0e21d9abb152c4c8d))
* Update outputs.tf ([5b3b731](https://github.com/google/stellar-engine/commit/5b3b731d4f06670e1cc71fd708b0717057ce0ce9))
* Update README text to more clearly demonstrate how to import a keyring into the state ([cc39bb4](https://github.com/google/stellar-engine/commit/cc39bb45ebf1ccd82151972a3d8d1aa4f602b5d3))
* Update README.md ([6a81634](https://github.com/google/stellar-engine/commit/6a81634b72daf8db5968b6f98e432bc817830a6f))
* Update terraform.tfvars.sample ([6e5e148](https://github.com/google/stellar-engine/commit/6e5e148b5a6de3d24296bbfaacb81d730a9f7de5))
* update the kms module ([881a1aa](https://github.com/google/stellar-engine/commit/881a1aa4b504910c715288657efb4cc676fb1821))
* Update variables.tf ([a45e13a](https://github.com/google/stellar-engine/commit/a45e13a4eef8c5cda182fa5e1954c69deba3a45b))
* updated group name ([5eba370](https://github.com/google/stellar-engine/commit/5eba37070511d81182e68f00d28442b69d235eff))
* updated readme ([5c6e889](https://github.com/google/stellar-engine/commit/5c6e889e5ce35c4356c90dffa7c192990d00741f))
* updated the read me ([a9d05b9](https://github.com/google/stellar-engine/commit/a9d05b9847fa0ee7dc12bd385fa6e15f47cc8d69))
* upped sleep for ngfw and added just one sample project in stage 3 ([235b080](https://github.com/google/stellar-engine/commit/235b0809d2be9682d1a519f7261fd843a5e44bcd))
* variable ([14ddb5a](https://github.com/google/stellar-engine/commit/14ddb5a209cea5d06826933f9e3f17ea3b85a6c2))
* variables ([6ce4319](https://github.com/google/stellar-engine/commit/6ce43198580945c932716ccd0b0a86597e96a5bb))
* variables and module refactoring ([af9f05c](https://github.com/google/stellar-engine/commit/af9f05cc8b3cbd246483b33c42c759b025460383))
* variables configuration ([344e812](https://github.com/google/stellar-engine/commit/344e812d9897554ef767ab8bfc3d21745976e584))
* variables for the secondary cidrs ([82e5fae](https://github.com/google/stellar-engine/commit/82e5fae9664118ecd7148a7817e3f8e4dfc8267c))
* variables formatting ([7207efa](https://github.com/google/stellar-engine/commit/7207efad236b100e0d1412f78dc5e71945920197))
* variables, outputs and specification for security onion ([c6349b9](https://github.com/google/stellar-engine/commit/c6349b9beff6ac6c0541dcd741339196320a7456))
* VPC Peering with multiple subnets ([56bb583](https://github.com/google/stellar-engine/commit/56bb583347f9580f62974a2610aed3fabee54801))
* VPC regional ([dff3954](https://github.com/google/stellar-engine/commit/dff39545c0a0a994b68fef03a446293dd868d733))
* We need to add enable the API first ([40440bc](https://github.com/google/stellar-engine/commit/40440bc6e194b8b92cf53d78556e55f38d07f2cb))
* working deployment ([755b694](https://github.com/google/stellar-engine/commit/755b694dd44a3ddb426d826aa227789d765d84fc))
* Write README.md with instructions for using this blueprint ([3e866c6](https://github.com/google/stellar-engine/commit/3e866c6f8fb42cc8917658a9e2ddf0eb1a7f0eb6))

## [daily-2024.06.12](https://github.com/google/stellar-engine/compare/daily-2024.06.08...daily-2024.06.12) (2024-06-11)


### Features

* Add in subnets ([971a2e4](https://github.com/google/stellar-engine/commit/971a2e41cf979ef63253c8c3c5d84d6580204286))
* Add in the two new projects to the tenant ([b4fef86](https://github.com/google/stellar-engine/commit/b4fef864622c27db3637512f95b473af694cd7b4))
* Add tenant route back into the cloud-router ([1960e8c](https://github.com/google/stellar-engine/commit/1960e8cb53167f128b1166443eea150d2461be3c))


### Bug Fixes

* addition of readme ([f28a43f](https://github.com/google/stellar-engine/commit/f28a43f593773f577d0f929a844035c9223b2963))
* code refactoring ([99ea59f](https://github.com/google/stellar-engine/commit/99ea59f20a763ed63cce362d8b96387c12586dd5))
* default removed ([54e9f6f](https://github.com/google/stellar-engine/commit/54e9f6f2ca2ecd298e2a686282f76b1b993dc486))
* default removed proejct host ([caf180c](https://github.com/google/stellar-engine/commit/caf180c90247fc26edeb952d7abc29fdb5f29994))
* locals updated ([28975f7](https://github.com/google/stellar-engine/commit/28975f7ef16c4d4483bb52c5a0c9c83a51d99013))
* loop for the vpc creation ([38948d9](https://github.com/google/stellar-engine/commit/38948d9e089d3bba4d1d07ee20d7c32ad1bbb2e6))
* module VPC ([a68c86d](https://github.com/google/stellar-engine/commit/a68c86d93020092d5924824fac59b775a9cd4ac6))
* output vpc cidrs ([1aabbd2](https://github.com/google/stellar-engine/commit/1aabbd2122a55f04b71b10c6941b76205f9a34a8))
* Peering enabled ([c5af2f3](https://github.com/google/stellar-engine/commit/c5af2f316a57277bb5b18c0bcb1e17db000f6ae7))
* READ ME ([4c18415](https://github.com/google/stellar-engine/commit/4c18415b0c51db0d3d23d5d6c452ac17cbc8c53f))
* Reading the CIDR from Yaml ([1bf6a61](https://github.com/google/stellar-engine/commit/1bf6a61421ee847b1a5edefad551e215fc44d3f2))
* refactor to read directly from variables instead of file ([7f0313b](https://github.com/google/stellar-engine/commit/7f0313b616df74df2c026587155a9195457a33d9))
* refactor variables ([3c9c736](https://github.com/google/stellar-engine/commit/3c9c7366ac1dd67faccfeb20431d9c6d7cf9e72c))
* Terraform variables tfvars ([660dfd4](https://github.com/google/stellar-engine/commit/660dfd4525887b78045ec1396dfd649f95045088))
* Updates to allow KMS and handle location for pubsub ([7868da2](https://github.com/google/stellar-engine/commit/7868da2402e3bfbb523bf87dba1a845ed2c88038))
* variables from JSON file ([12b3757](https://github.com/google/stellar-engine/commit/12b37572eb815718188c4cadd148d041e79b6517))
* variables terraform ([4bce41e](https://github.com/google/stellar-engine/commit/4bce41ee6aedabcb2dac24ea7379f186e880793b))
* VPC per project with peering ([feb0928](https://github.com/google/stellar-engine/commit/feb09281104cea5e9576b3982d337304b0a1b1c7))

## [daily-2024.06.08](https://github.com/google/stellar-engine/compare/daily-2024.06.07...daily-2024.06.08) (2024-06-07)


### Bug Fixes

* changed main.tf roles ([1712233](https://github.com/google/stellar-engine/commit/1712233d8ede736da2ccc23744e267ecc35bc72e))
* Changed outputs ([18c397c](https://github.com/google/stellar-engine/commit/18c397cd8da438f8f97eefe7156e3c3097518c9c))
* Changed service account dynamically and added a data source pointing to current. ([f4d6f09](https://github.com/google/stellar-engine/commit/f4d6f0979203792a4f32e9b91f78ed724ff84c48))
* Co-authored-by: Will <64548206+will-darkwolf@users.noreply.github.com> in blueprints/il5/pub-sub-project/main.tf ([7a4ff15](https://github.com/google/stellar-engine/commit/7a4ff15db192fc19d33e7ba6ba39152ba443d1ae))
* Co-authored-by: Will <64548206+will-darkwolf@users.noreply.github.com> in blueprints/il5/pub-sub-project/main.tf ([91f2201](https://github.com/google/stellar-engine/commit/91f2201b93abbaf1a03a15d2069c605a6af77a1a))
* debugging and adding configurations for pub sub ([2eb69a1](https://github.com/google/stellar-engine/commit/2eb69a1bd3efba76f9a054700f06317e96705e53))
* deleted unnecessary newlines ([0486fd3](https://github.com/google/stellar-engine/commit/0486fd336d2e2c5211d989d85927d1c752cfcf93))
* injected member roles ([f1cf09c](https://github.com/google/stellar-engine/commit/f1cf09c6a92b7228e03e711e3fbfcf06e40614af))
* made chsnges to readme ([35b523f](https://github.com/google/stellar-engine/commit/35b523f7440563e545c639bd219765b07d177ab5))
* Publisher and subscriber acccounts created, outputs file modified, HSM utilized ([62ad5cc](https://github.com/google/stellar-engine/commit/62ad5ccc389aa01c5ab1d2ea641876c6e9dfd2e7))
* Utilized the pub-sub module ([c316218](https://github.com/google/stellar-engine/commit/c316218b47172350692fe05ef41703ca9d9d449c))

## [daily-2024.06.07](https://github.com/google/stellar-engine/compare/daily-2024.06.04...daily-2024.06.07) (2024-06-06)


### Bug Fixes

* Shielded VM refactoring ([469904e](https://github.com/google/stellar-engine/commit/469904e49d42d20e0586229ebbd7b977dc420665))

## [daily-2024.06.04](https://github.com/google/stellar-engine/compare/daily-2024.05.24...daily-2024.06.04) (2024-06-03)


### Features

* Add a management bastion VM, use a service account to start the Palo Alto NGFWs. Bootstrapping appears to work, but might have taken longer than expected ([58f79c7](https://github.com/google/stellar-engine/commit/58f79c74bc9e99d5f42015bd388df291734e4b01))
* add encryption IAM perms for service agents for log sink destinations ([1421565](https://github.com/google/stellar-engine/commit/14215650e48c77cc67b8a0570e7acf8173d30a28))
* add encryption key field, add filters in sample tf ([de6a644](https://github.com/google/stellar-engine/commit/de6a6446985f9156a288ba1dbba933ebee676d86))
* Add in the new subnets ([f6c5884](https://github.com/google/stellar-engine/commit/f6c5884151acc9acb1b093982235421ca0e6a972))
* Create new networking folder for ngfw ([a779751](https://github.com/google/stellar-engine/commit/a779751841acbafdb870774d950791e26ba33804))
* Create the default routes for the landing zone VPC ([54f426a](https://github.com/google/stellar-engine/commit/54f426a693132227aa0bbc024c18aaa0e2318bcd))
* Feat/dr 12 ([#24](https://github.com/google/stellar-engine/issues/24)) ([30cbc7a](https://github.com/google/stellar-engine/commit/30cbc7aba2421455e80531c841fab4990a3897fb))
* Initial commit of nfgw ([50ea039](https://github.com/google/stellar-engine/commit/50ea039549fb433c3be582bf6d877d9e928145cd))


### Bug Fixes

* Change the mgmt network from mgmt-landing-0 to be prod-mgmt-0 and begin updating README ([58b02e6](https://github.com/google/stellar-engine/commit/58b02e699de9bc576c51bb2b487c9c9e03c61ab3))
* Default service account for the compute engine role ([a67343c](https://github.com/google/stellar-engine/commit/a67343c72334a2d87fb96f84bed86ab150a2e676))
* Deploy a Cloud-NAT so the NGFW doesn't have to be made public ([aabfb0e](https://github.com/google/stellar-engine/commit/aabfb0ec66dcc1c69b35d7f29d83d3399c51fe60))
* Dynamically set the password ([75b9f8d](https://github.com/google/stellar-engine/commit/75b9f8dda81175f34cd5308a3bfb5ef60436c85e))
* fmt ([b9b3160](https://github.com/google/stellar-engine/commit/b9b3160b7a9386e8a41a35ffe89e3cb0fb19ebbf))
* fmt ([069084c](https://github.com/google/stellar-engine/commit/069084cdc998bb277cd8810a7b9fe37f59f10557))
* Healthchecks now work. ([cd8cd39](https://github.com/google/stellar-engine/commit/cd8cd39bd79768d7fb41a21cc4e9850d0e43709b))
* Instead of setting a default static route, set the second interface to never set a default route, thus only the DMZ gets a default route out. Now we don't need to know what region we're in when we deploy ([0463dcb](https://github.com/google/stellar-engine/commit/0463dcb40495499f261a042138f088c913c099c4))
* KMS Key with Service Account ([9bc1687](https://github.com/google/stellar-engine/commit/9bc1687ef5ccd56f7bbe9dbcd287124df3975151))
* Make a custom role ([39607bc](https://github.com/google/stellar-engine/commit/39607bc1c3e99db910b5e1073a71f32b54218060))
* make output marked sensitive ([9a897a2](https://github.com/google/stellar-engine/commit/9a897a2accdf4efa36383127a57a702b11210ba0))
* Make the description more accurate ([2add03d](https://github.com/google/stellar-engine/commit/2add03dde446cd233e73f7268f31847bb1cb65e8))
* Make the networking folder IL5 ([56d086d](https://github.com/google/stellar-engine/commit/56d086d39eb05cc52cb54df69a3c8a1c08a3e8c1))
* Needs cleanup, but this finally worked ([99be0af](https://github.com/google/stellar-engine/commit/99be0af68e46a128a2ccebf8d7b036974967fe03))
* oops, forgot to actually add the bastion.tf file ([bfaad56](https://github.com/google/stellar-engine/commit/bfaad563e3329eb59c47340e4c233d6c232db28b))
* Persistent Disk with Compute Engine ([39f5b8a](https://github.com/google/stellar-engine/commit/39f5b8af2381a0d37d44c5b43c11e59e70cf7521))
* Persistent Disk with Compute Engine ([#23](https://github.com/google/stellar-engine/issues/23)) ([d0bfcde](https://github.com/google/stellar-engine/commit/d0bfcde872d23dbda0596c8be5141493e49e4a1f))
* Remove references to IAP from the ingress rules ([1aae9c5](https://github.com/google/stellar-engine/commit/1aae9c5f9d051977c3211deea59166e10d67b771))
* Reset the nva folder ([913a806](https://github.com/google/stellar-engine/commit/913a8061515804d4580fe968e447d8baa8f93c9e))
* Revert changes in the blueprint folder ([497d1c7](https://github.com/google/stellar-engine/commit/497d1c784bf731c0fdbf1b6bcf7e50e58acff52b))
* Simplify the command for getting the NGFW password ([e6e0076](https://github.com/google/stellar-engine/commit/e6e0076842abbf9d8e8591e47cdb64b6ef8dd0ec))
* Split the regions out, fixed password salt ([8febda5](https://github.com/google/stellar-engine/commit/8febda58f7b66795bbce63f211f758ed004bec81))
* tfdoc ([eb933a2](https://github.com/google/stellar-engine/commit/eb933a2b2aa8960f72154122a8c06c848c8d994f))
* The encryption key doesn't seem to be taking for the NGFW instances, but the bastion is encrypted now ([fab286d](https://github.com/google/stellar-engine/commit/fab286d9f0e44f74a421af5fbd0a6118711c4505))
* This configuration finally applies ([092f542](https://github.com/google/stellar-engine/commit/092f54228f58d3ea52e9c1a2f39c0691fd0f996e))
* update readme ([7c757f1](https://github.com/google/stellar-engine/commit/7c757f1de169f4da0a11ee2c3220e71c8fc359fe))
* Update README.md ([4040953](https://github.com/google/stellar-engine/commit/40409530ee257af8cdd18076ffcfe76fb98a4f2b))
* Update README.md ([1cc3660](https://github.com/google/stellar-engine/commit/1cc36609f6b99ded7417c7b0e5483b26a4bf48f6))
* Use a dual-region bucket instead of trying to make two single region bucket, this simplifies the config a lot ([4e1c028](https://github.com/google/stellar-engine/commit/4e1c028db76219871882a338c830132d986585a1))
* Using Compute Engine Service Account ([e0cfbdf](https://github.com/google/stellar-engine/commit/e0cfbdf8cd11d13b0f855787346eda39e7404c35))
* Validates ([25b17d1](https://github.com/google/stellar-engine/commit/25b17d111173642c6584a18051b0eb6c79dbed29))
* Validates ([04d2296](https://github.com/google/stellar-engine/commit/04d22961cb940b7859fda88a12f6489a3d75005d))

## [daily-2024.05.24](https://github.com/google/stellar-engine/compare/daily-2024.05.18...daily-2024.05.24) (2024-05-23)


### Features

* added depends on ([d8662f3](https://github.com/google/stellar-engine/commit/d8662f37cae84c4835946e31468db830c67ce7f6))
* added sample file ([f3fef49](https://github.com/google/stellar-engine/commit/f3fef496706374d6d1afc2ed29af1f9ef235a44c))
* added tfvars sample file and corrected module for source. ([0fed065](https://github.com/google/stellar-engine/commit/0fed0651118881ea3a4f6f6d51bad1043ac7bedb))
* initial commit ([32dc27d](https://github.com/google/stellar-engine/commit/32dc27d35ea53cdb500ecf5bebb46f9702244c13))


### Bug Fixes

* addded bigquery module. ([e34227f](https://github.com/google/stellar-engine/commit/e34227f995eaae887addb7b8281a3e31910f1941))
* addded terraform tfvars sample file. ([7ba87de](https://github.com/google/stellar-engine/commit/7ba87dec53bc3a49bcef844723d75a2242404590))
* Big-Query-Project ([#18](https://github.com/google/stellar-engine/issues/18)) ([dd9fae7](https://github.com/google/stellar-engine/commit/dd9fae7816000b53fd354edf12eaa6d81c40a702))
* changed folder name. ([a4ac225](https://github.com/google/stellar-engine/commit/a4ac225527e5b96e155c9fa9a1fc54ac2f15cdb9))
* Changed spacing in main and variables files. ([b35e200](https://github.com/google/stellar-engine/commit/b35e200460f823d972e6e18db1d072a72638faf1))
* changed the name of folder ([6aaed5d](https://github.com/google/stellar-engine/commit/6aaed5db5f3ce54d9ae4663f6612bc257cc05d3f))
* Cleaned up files ([7809510](https://github.com/google/stellar-engine/commit/780951075b38f95e2105c9f34ecdb48e60c15e78))
* Co-authored-by: Will <64548206+will-darkwolf@users.noreply.github.com> in blueprints/il5/bq-project/main.tf ([0d6c875](https://github.com/google/stellar-engine/commit/0d6c875e859cdd1b5edea90126f3def552f57cca))
* Co-authored-by: Will <64548206+will-darkwolf@users.noreply.github.com> in blueprints/il5/bq-project/main.tf ([9c90226](https://github.com/google/stellar-engine/commit/9c902266811d9254c9011b1ff1cb357f77f3a0b7))
* Debugged organization policy error and minor changes to README. ([f077e37](https://github.com/google/stellar-engine/commit/f077e3745efe6cce30a97cd09771790e23bd5617))
* Delete blueprints/il5/bq-proj directory ([93008cf](https://github.com/google/stellar-engine/commit/93008cf079d8e1c1efbf07b57a0df0e7f8d30cdb))
* Delete blueprints/il5/bq-proj-folder/terraform.tfvars.sample ([97694ef](https://github.com/google/stellar-engine/commit/97694ef58549b072e9f85dc08827e6e7ed6ad8a9))
* Delete blueprints/il5/bq-proj/variables.tf ([a74efd8](https://github.com/google/stellar-engine/commit/a74efd85cb0939848dd5f2dee451a687edfb1f63))
* Fixed argument names as per bq  module ([2f74153](https://github.com/google/stellar-engine/commit/2f7415375e3ea03087fc5b42e98c4078c36115a8))
* Fixed terraform sample file ([52e39b8](https://github.com/google/stellar-engine/commit/52e39b8c9f92256ff2adba794e69f7f6ef49f534))
* fixing the Pull Request to std ([03f5185](https://github.com/google/stellar-engine/commit/03f5185c47dc5f558b82323a880c793d96cbe562))
* I used CFF modules to create kms, ensured no hardcode is in main file, variables are defined and used in main and ensured defaults are taken out flushed in tfvars file. ([e7dc6f4](https://github.com/google/stellar-engine/commit/e7dc6f4f8c0a26d0987c93ae64aa995d88b88b6b))
* I used CFF modules to create kms, ensured no hardcode is in main file, variables are defined and used in main and ensured defaults are taken out flushed in tfvars file. ([0085f3b](https://github.com/google/stellar-engine/commit/0085f3b5e780cba2dcf21e5d2abcd54a0b0d3021))
* made changes to variables and tfvars. ([c143bc6](https://github.com/google/stellar-engine/commit/c143bc65e2cdf3061f0e8680269fe633c9fa47e1))
* minor change in README.md ([4875103](https://github.com/google/stellar-engine/commit/48751034a1992b7decd7b1db90c56d3a526d98a9))
* minor change in README.md ([0849589](https://github.com/google/stellar-engine/commit/0849589ba60c89cb9fec8907b4d126d910839e32))
* minor change terraform.tfvars.sample ([187a628](https://github.com/google/stellar-engine/commit/187a6284e17fcbb819d55076eac4516f0f78601e))
* minor change to sample ([78c8085](https://github.com/google/stellar-engine/commit/78c80851f462c25bd4d57f18d07d9490af6c94af))
* minor changes sample ([0b1e439](https://github.com/google/stellar-engine/commit/0b1e43951eca7742df47bbdb9aa1f5c4dc1d075e))
* passing keys ([85c2a49](https://github.com/google/stellar-engine/commit/85c2a49f47c2af20cbb75a736b42b4b1da510ceb))
* README has screenshot of how deployed dataset looks on the console, varaibles injected from BigQuery, and outputs printed. ([c88bef8](https://github.com/google/stellar-engine/commit/c88bef8a4e4fbd177211655312cb016b82d80deb))
* README has screenshot of how deployed dataset looks on the console, varaibles injected from BigQuery, and outputs printed. ([a66a840](https://github.com/google/stellar-engine/commit/a66a840098139e0aaf5dde59c89877f8aad8aa31))
* Update README.md ([40c6edb](https://github.com/google/stellar-engine/commit/40c6edb0d43b6971c350b4dfc5614946f097ecd4))
* Update README.md ([7182b1b](https://github.com/google/stellar-engine/commit/7182b1b43c9ccd8a94dcf3b4a1f0734a2f98eeea))
* Update variables.tf ([13b8778](https://github.com/google/stellar-engine/commit/13b8778b5eff8fda112b8a60ddb55c769861b443))

## [daily-2024.05.18](https://github.com/google/stellar-engine/compare/daily-2024.04.24...daily-2024.05.18) (2024-05-17)


### Features

* Add instructions for the service account IAM permissions, sorry, couldn't automate this more, in a hurry ([ee975f5](https://github.com/google/stellar-engine/commit/ee975f5b4313c44e5e8b3c962d94a20717981e42))
* Add our individual projects ([d6efab2](https://github.com/google/stellar-engine/commit/d6efab2cb2ef79c0a76dfab32b9e54fdbf75a5d5))
* add the group ([bd4e5f3](https://github.com/google/stellar-engine/commit/bd4e5f37bfb46b15d458665ab2869f4dc87539c6))
* Feature: Assured Workloads Module ([#10](https://github.com/google/stellar-engine/issues/10)) ([d43db29](https://github.com/google/stellar-engine/commit/d43db297b39e6acc8314321cfe155a8ee3b17a90))
* Initial cloud sql instance ([#6](https://github.com/google/stellar-engine/issues/6)) ([5d69bd9](https://github.com/google/stellar-engine/commit/5d69bd98373476084ae28ac77b4115ddfc26f541))
* Initial commit of run through, mostly switching regions to be us-locations ([c8763ae](https://github.com/google/stellar-engine/commit/c8763ae285e796c3eebe6ee7eceef4fb2838dd9b))
* New variables and Main file ([7ceb380](https://github.com/google/stellar-engine/commit/7ceb380da514fd0817293ab64e1bbdd043990ae0))


### Bug Fixes

* Add setting default project to the ToC for 2-networking stagef in README.md ([cfcb763](https://github.com/google/stellar-engine/commit/cfcb763b85c6e2de3613cebf17d57c5fe01802c0))
* Add setting default project to ToC for 2-security README in README.md ([6e0bd4e](https://github.com/google/stellar-engine/commit/6e0bd4ef201b36bd23bb8e30a17da81c7fdccda2))
* Add setting default project to ToC on 1-resman in README.md ([005946b](https://github.com/google/stellar-engine/commit/005946b43e0a9b0f219fb24808ef414fe4a85e9a))
* Blue print GCS ([55a08d2](https://github.com/google/stellar-engine/commit/55a08d2206963bb129ae443deb825b8eda731ecd))
* Change sample defaults for 0-bootstrap to be US/us in terraform.tfvars.sample ([171ae26](https://github.com/google/stellar-engine/commit/171ae261dfe61f57bb711b2c6afd070cd47077f6))
* CMEK ([d8a3236](https://github.com/google/stellar-engine/commit/d8a3236251704d173b9c343e8090c628d6dab63e))
* CMEK Error resolving ([9288324](https://github.com/google/stellar-engine/commit/9288324b32445e38909b3864b2b17574acb5bdf6))
* Compute Engine  Shielded VM - project module build out ([d7bcde5](https://github.com/google/stellar-engine/commit/d7bcde5efbe1d449d9cfd0efb356b13af974961e))
* Compute Engine  Shielded VM - project module build out ([4f26a18](https://github.com/google/stellar-engine/commit/4f26a18aa058eec61cdecc4364d3d8fded251442))
* Copy the stages folder to begin setting up Assured Workloads ([9df559c](https://github.com/google/stellar-engine/commit/9df559cd3588c5b07d5985eb9f0b6901cf0e7181))
* correct variables ([cf4ef87](https://github.com/google/stellar-engine/commit/cf4ef87f0f00faf6d26f00fb7594144f9ce421a2))
* default is here ([9ab8d75](https://github.com/google/stellar-engine/commit/9ab8d7508a2be9cf241fc09a2280ba2ce6d86cd4))
* default requirement ([897df83](https://github.com/google/stellar-engine/commit/897df833140e67d5fa65ef15cbb25cb03652f891))
* defaults ([1623d0f](https://github.com/google/stellar-engine/commit/1623d0fed31129a4792d56aa5c46aecbd58191d3))
* depends on module kms ([af72661](https://github.com/google/stellar-engine/commit/af72661285268e8ca04da9b4d28b024d0e753e3f))
* Edits in variables, Sample, Screenshot ([91670af](https://github.com/google/stellar-engine/commit/91670afd2f389e4e3be61871fd7e334cd7beb357))
* Edits in variables, Sample, Screenshot ([e136a5e](https://github.com/google/stellar-engine/commit/e136a5e69f7dc1736275cc3210af7ed3878522d9))
* Enable Autoclass ([97199bb](https://github.com/google/stellar-engine/commit/97199bb3a6ae22a4b5679f7c26250f6068fea7d9))
* Fix capitalization in 1-resman README in README.md ([bfed94c](https://github.com/google/stellar-engine/commit/bfed94c88029412d23fdfddfc0d31af46df31e8b))
* fixup: Need to establish that the 'core' project at the top level is in IL5 ([#15](https://github.com/google/stellar-engine/issues/15)) ([4a602b2](https://github.com/google/stellar-engine/commit/4a602b2f6ced1e3768d9a80b3f0480d819cf70de))
* format ([48c5153](https://github.com/google/stellar-engine/commit/48c5153a85c2338d28f93182a8b870978aefe54a))
* GCP Cloud Key Management Service (Cloud KMS) Blueprint project ([96ee83c](https://github.com/google/stellar-engine/commit/96ee83c9ab1b452bc0cce88240572994a4fd2527))
* GCS deployment end to end ([1d8b336](https://github.com/google/stellar-engine/commit/1d8b336a1b2cdc08b1d38e96496bb09ed3f2e322))
* IL deployment worked ([25863ed](https://github.com/google/stellar-engine/commit/25863edf7ca7f819c8e733ffcf182a5d192859cb))
* Include instructions about setting project for subsequent stages in README.md ([0a49734](https://github.com/google/stellar-engine/commit/0a49734df41423f59919c1016680907cce7f1611))
* Include instructions for setting default project in 2-networking README in README.md ([fd26d3b](https://github.com/google/stellar-engine/commit/fd26d3b4240349505136cf632ff120082dcb7f96))
* Include instructions for setting default project in the dev README file in README.md ([a1f8c38](https://github.com/google/stellar-engine/commit/a1f8c3835585d58769b545c03ed8bd516a38d688))
* Include instructions for setting the default project for 2-security README in README.md ([8eca7fb](https://github.com/google/stellar-engine/commit/8eca7fb7029b21ce4f4be10996d7af8d316f4f8f))
* Include note about Terraform version in README.md ([db2c7fa](https://github.com/google/stellar-engine/commit/db2c7fa6e67dd6a0df442d0b7f6f6d67ac807f8f))
* Include the boostrap_user var in the apply command in README.md ([5c86fbc](https://github.com/google/stellar-engine/commit/5c86fbc9238203ced83ecb4efacf971b263079a1))
* Minor edit in readme ([457c5eb](https://github.com/google/stellar-engine/commit/457c5eb11197130bb5dca94ab14304284e3dc778))
* Minor edit in readme ([9d99103](https://github.com/google/stellar-engine/commit/9d9910333be25484b32c3be91d806926e0a3677b))
* module ([2d27df7](https://github.com/google/stellar-engine/commit/2d27df7fbe8646b428ec1d3a0297643e04592b9f))
* private bucket ([b9f9723](https://github.com/google/stellar-engine/commit/b9f9723628e48a045f85bca600ffa551980b7061))
* project id empty ([d8b6ed5](https://github.com/google/stellar-engine/commit/d8b6ed52ca88d1bc7c8e5c26337d3b854519886e))
* read me ([6c8c68d](https://github.com/google/stellar-engine/commit/6c8c68d565ea7a67f4fd3ac306cd11afd6f88184))
* Read me for autoclass ([92921fd](https://github.com/google/stellar-engine/commit/92921fde3ef4655f9a67e090ecdd8703feb15e50))
* read me gcs ([57a8b11](https://github.com/google/stellar-engine/commit/57a8b113ffdd473a213574032626808ca461383f))
* Remove other networking options ([347135c](https://github.com/google/stellar-engine/commit/347135cee143430c123c260c60bebb16b1f253a7))
* Remove reference to symlinking the tfvars file from the 0-bootstrap README in README.md ([83e787d](https://github.com/google/stellar-engine/commit/83e787d627329ba9ca67132efa27081ada3b7ca1))
* remove stages-aw/3-* that were extra ([6486ff6](https://github.com/google/stellar-engine/commit/6486ff6d2f4c8ff46c4e8f7a6745c3e555b85a78))
* Remove the symlink nonsense ([3256031](https://github.com/google/stellar-engine/commit/325603156ced00b50b4497bbd134a721718e7d6b))
* removing defaults ([d97b872](https://github.com/google/stellar-engine/commit/d97b8723ee9bf48ef3e1cf199c79e005c4eb57d7))
* Removing email default ([5be9ddb](https://github.com/google/stellar-engine/commit/5be9ddb5b98c09026d9ba2b0bca11608a77f9dc4))
* revert the module ([a8e6708](https://github.com/google/stellar-engine/commit/a8e670884ac4415e31a2dbcffb3da968179c78f8))
* terraform fmt ([fd27a2e](https://github.com/google/stellar-engine/commit/fd27a2e8910840120c3cc735c41ae97e52fa8d8d))
* tf variables sample ([ad6b6a7](https://github.com/google/stellar-engine/commit/ad6b6a70ab66058e13f2b041ea464458085069aa))
* try cloning the tftest folder for stages ([b5110ad](https://github.com/google/stellar-engine/commit/b5110add18f165adbb415fcf048a96216db68386))
* typo fix ([643c270](https://github.com/google/stellar-engine/commit/643c2702fde420b96f8ba6ad35b76395053d0844))
* Update 1-resman README to include instructions for setting the default project in README.md ([a3c6af9](https://github.com/google/stellar-engine/commit/a3c6af9f835f5d1668443d12e2047d32c89ee6af))
* Update README.md ([d1bd418](https://github.com/google/stellar-engine/commit/d1bd418304e1268250c93f176efa9da9f75ac154))
* Update README.md ([c5e8543](https://github.com/google/stellar-engine/commit/c5e8543bae711516cca95e3cdb8434e6f61b13be))
* Update README.md ([45478e8](https://github.com/google/stellar-engine/commit/45478e818b76b0aa6ede6e24952765b1d187aefd))
* Update README.md ([54d86c7](https://github.com/google/stellar-engine/commit/54d86c76edb8de6178ef9ee8b8d1d2775d81e9de))
* Update README.md ([81d34ee](https://github.com/google/stellar-engine/commit/81d34eeac24447363d2d265d101414372b5abfdf))
* Update README.md ([e5b4575](https://github.com/google/stellar-engine/commit/e5b4575c90b80e2efbf9c66b77f660143d2429a8))
* updated readme with infomration about duration ([c11b1ed](https://github.com/google/stellar-engine/commit/c11b1ed7165dd712389d0f6af1643722e9876f3a))
* updated the object ([47c9884](https://github.com/google/stellar-engine/commit/47c9884b9cb25f13a8a0c10b030c853c495c6404))
* updated the Read me ([4751cf7](https://github.com/google/stellar-engine/commit/4751cf70616a5c1dc07750e5849f4b51dee4b2de))
* Updated the readme instruction bootstrape ([0c3f728](https://github.com/google/stellar-engine/commit/0c3f728cc14f9562d6b7a64a0c4bd94a511e3a00))
* validate ([3de3bee](https://github.com/google/stellar-engine/commit/3de3bee052660a3563a45692627540820ef86778))
* variable update ([e3e2bf7](https://github.com/google/stellar-engine/commit/e3e2bf736e28c5da49f80b7fc752effd75e7d231))
* variables ([01c9696](https://github.com/google/stellar-engine/commit/01c969686fa3bf4e959f8f7d0527a6c7dfe6c7e6))
* Variables amd CMEK key ([706e294](https://github.com/google/stellar-engine/commit/706e29408ad2dbaccb6539fec093ef2e9e7bb7df))
* Variables and main ([e83880d](https://github.com/google/stellar-engine/commit/e83880d61adf773a09eb1bf789eabe53aeee1753))
* variables changed to specific region ([af8fa58](https://github.com/google/stellar-engine/commit/af8fa58f04a00d237ff4aa3f8801a581481f434d))
* version ([7531daa](https://github.com/google/stellar-engine/commit/7531daa5989fb249ef5abdd9dbd8d458a96a1fc9))

## [daily-2024.04.24](https://github.com/google/stellar-engine/compare/daily-2024.04.23...daily-2024.04.24) (2024-04-23)


### Bug Fixes

* Add setting default project to the ToC for 2-networking stagef in README.md ([5229753](https://github.com/google/stellar-engine/commit/52297538623358c630c8106a0bcb09dd2e8f1077))
* Add setting default project to ToC for 2-security README in README.md ([c3c0190](https://github.com/google/stellar-engine/commit/c3c019085f755aa741c89d97bd5aad637a989b91))
* Add setting default project to ToC on 1-resman in README.md ([20995e7](https://github.com/google/stellar-engine/commit/20995e738312c9cbfb3cdd1ada5c09eb210f6fca))
* Change sample defaults for 0-bootstrap to be US/us in terraform.tfvars.sample ([0ada075](https://github.com/google/stellar-engine/commit/0ada075e607c0cf1143cf0283a903a11691b0a0a))
* Fix capitalization in 1-resman README in README.md ([2ca70ac](https://github.com/google/stellar-engine/commit/2ca70acd2ea145c37c93a1d8d8cb92c2ece21789))
* Include instructions about setting project for subsequent stages in README.md ([5b25d5a](https://github.com/google/stellar-engine/commit/5b25d5af7221470eea20fe0e5cc15bd529caf434))
* Include instructions for setting default project in 2-networking README in README.md ([2b3d493](https://github.com/google/stellar-engine/commit/2b3d493ef5d96ea54ffb729d224477075a4d2d60))
* Include instructions for setting default project in the dev README file in README.md ([0cb6708](https://github.com/google/stellar-engine/commit/0cb670816a3aa346947b96cb431dc555276581e3))
* Include instructions for setting the default project for 2-security README in README.md ([2b03fca](https://github.com/google/stellar-engine/commit/2b03fcae1b85db2d200f087aee560e92b415b41d))
* Include the boostrap_user var in the apply command in README.md ([a0926c2](https://github.com/google/stellar-engine/commit/a0926c2999e5aa9822b46e4da9ac8e9ab9cbd600))
* Remove reference to symlinking the tfvars file from the 0-bootstrap README in README.md ([52052c1](https://github.com/google/stellar-engine/commit/52052c1b81912d33271372601d6add1dc3c5fc3a))
* Update 1-resman README to include instructions for setting the default project in README.md ([98f78cb](https://github.com/google/stellar-engine/commit/98f78cbf56a49be5ad5ddd92abcf2f7e90b7c924))

## [daily-2024.04.23](https://github.com/google/stellar-engine/compare/0494d36...daily-2024.04.23) (2024-04-23)


### Features

* Add instructions for the service account IAM permissions, sorry, couldn't automate this more, in a hurry ([7b9f013](https://github.com/google/stellar-engine/commit/7b9f013317827f8239f81a9bd4a45a23f78c26e7))
* Initial commit of run through, mostly switching regions to be us-locations ([997ba85](https://github.com/google/stellar-engine/commit/997ba85f90642e1c391b5aab50e855b221ab1ceb))


### Bug Fixes

* Copy the stages folder to begin setting up Assured Workloads ([5e416ea](https://github.com/google/stellar-engine/commit/5e416eadeca870a6b984f8f496c3d4cc290f85e2))
* Include note about Terraform version in README.md ([e5d0dca](https://github.com/google/stellar-engine/commit/e5d0dca468684587a427cdd77b0bb3c7a1ea8999))
* Remove other networking options ([f841048](https://github.com/google/stellar-engine/commit/f84104879dee35904b421f895865017e9b103a66))
* remove stages-aw/3-* that were extra ([a7882c0](https://github.com/google/stellar-engine/commit/a7882c0efcc82fb1a39f814be8a844f3981a04f4))
* Remove the symlink nonsense ([e7be33a](https://github.com/google/stellar-engine/commit/e7be33abad805b17039ea4a52bdd92ad433cfe4a))
