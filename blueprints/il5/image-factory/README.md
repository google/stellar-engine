# Golden image factory blueprint

This blueprint provisions a private Cloud Build golden image factory for hardened RHEL 9 Compute Engine images in regulated Google Cloud environments. Every build executes inside a VPC-peered private worker pool with no external IP addresses, uses a dedicated least-privilege service account, pulls digest-pinned builder containers from a private CMEK-encrypted Artifact Registry mirror, and produces Confidential Computing compatible images.

<!-- BEGIN TOC -->
- [1 Architecture](#1-architecture)
- [2 Security controls](#2-security-controls)
- [3 Prerequisites](#3-prerequisites)
- [4 Deployment steps](#4-deployment-steps)
- [5 Running builds](#5-running-builds)
- [6 Compliance scope](#6-compliance-scope)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Architecture

This blueprint composes reusable repository modules and native Cloud Build resources inside `project_id`:

- Project API enablement (`enable_apis = true` by default), service identity provisioning for Artifact Registry, Cloud Build, and Cloud Storage, and a 60-second IAM propagation wait before Cloud KMS and token-creator grants execute on fresh projects.
- A dedicated least-privilege Cloud Build service account created with `modules/iam-service-account` and granted project-scoped `roles/compute.instanceAdmin.v1`, `roles/compute.osAdminLogin`, `roles/compute.storageAdmin`, and `roles/logging.logWriter`.
- A regional CMEK-encrypted Cloud Storage staging bucket created with `modules/gcs` enforcing uniform bucket-level access, object versioning, and `public_access_prevention = "enforced"`, storing the rendered Cloud Build pipeline YAML object with read-only `roles/storage.objectViewer` access for the builder service account.
- A regional CMEK-encrypted Docker Artifact Registry repository created with `modules/artifact-registry` using immutable tags and vulnerability scanning to host mirrored builder container images.
- A private `google_cloudbuild_worker_pool` resource peered to `peered_network` (automatically normalized to the host project number to prevent `ForceNew` drift) with `no_external_ip = true` so workers reach ephemeral builder VMs strictly over private RFC1918 routes, plus an optional `modules/net-vpc-firewall` rule (`enable_ssh_firewall_rule`) allowing TCP `22` from `peered_network_ip_range` to `image-builder` targets in the VPC network that owns `builder_subnetwork`, which a `google_compute_subnetwork` data source resolves at plan time.
- An optional `google_cloudbuild_trigger` resource supporting either Cloud Build 2nd generation repository events or Pub/Sub-driven rebuild schedules without using `local-exec` provisioners.

## 2 Security controls

This blueprint enforces defense-in-depth defaults required for FedRAMP High and DoD IL5 landing zones:

- Private workers have no public IP addresses and connect to ephemeral Shielded VMs over `--internal-ip` with `--ssh-key-expire-after=1h` so OS Login profiles do not exhaust their key limit, removing any need for Identity-Aware Proxy SSH firewall rules or `199.36.153.8/30` VPC Service Controls bypass routes. The SSH readiness probe passes `-oConnectTimeout=10` and `-oBatchMode=yes`, so 30 attempts against an unreachable builder fail in roughly 10 to 15 minutes, well inside the default `3600s` `build_timeout`.
- Ephemeral builder VMs boot with `--confidential-compute-type=SEV` by default (`builder_confidential_compute_type`, configurable to `SEV`, `SEV_SNP`, `TDX`, or `null` for non-Confidential shapes), `--maintenance-policy=TERMINATE`, `--min-cpu-platform="AMD Milan"` when `SEV_SNP` is selected, `--no-address`, `--no-service-account`, `--no-scopes`, CMEK boot disk encryption, Secure Boot, vTPM, integrity monitoring, and `block-project-ssh-keys=TRUE`. A guarded cleanup trap on `EXIT`, `INT`, and `TERM` deletes each VM exactly once and preserves the step exit status, so failed, interrupted, or terminated build steps do not orphan VMs or CMEK disks.
- The rendered `harden-rhel9.sh` script provides a guest-agent hardening scaffold that creates `/opt/google-startup-scripts` with mode `0750`, enables `firewalld`, updates `[MetadataScripts]` `run_dir = /opt/google-startup-scripts` in `/etc/default/instance_configs.cfg`, and writes only that minimal override stanza to `/etc/default/instance_configs.cfg.template` so RHEL 9 STIG `/tmp` `noexec` hardening does not break Google Guest Agent startup scripts on downstream VMs; extend this scaffold with your organization's DISA STIG OpenSCAP or Ansible remediation tasks before production use.
- Plan-time variable validation rejects legacy `gcr.io` image references, unpinned container tags lacking a 64-character `@sha256:` digest, `guest_os_features` lists that miss the capability matching `builder_confidential_compute_type` (`SEV_CAPABLE` for `SEV`, `SEV_SNP_CAPABLE` for `SEV_SNP`, `TDX_CAPABLE` for `TDX`, and none for `null`), incompatible Confidential Computing machine shapes, global or cross-region Cloud KMS keys, cross-region zones or subnetworks, invalid CIDR ranges, service account IDs exceeding 30 characters, and `image_name_prefix` values exceeding 26 characters.
- A plan-time precondition on the worker pool requires the VPC network that owns `builder_subnetwork` to match `peered_network` (same host project number and network name), because private pools attach through VPC Network Peering, which is non-transitive. Set `allow_builder_network_mismatch = true` only when HA VPN with custom route advertisements or Network Connectivity Center routes `peered_network_ip_range` to the builder network.
- Captured golden images receive the configured `guest_os_features` (`SEV_CAPABLE`, `UEFI_COMPATIBLE`, and `GVNIC` by default) alongside CMEK encryption and regional `--storage-location` pinning so downstream Confidential Computing VMs boot reliably.
- Subnetwork IAM grants `roles/compute.networkUser` solely on `builder_subnetwork` when the builder subnet resides in a Shared VPC host project.

## 3 Prerequisites

1. Verify that Terraform and Google provider versions match `versions.tf`. When `enable_apis = true` (default), Terraform enables `artifactregistry.googleapis.com`, `cloudbuild.googleapis.com`, `compute.googleapis.com`, `containerscanning.googleapis.com`, `oslogin.googleapis.com`, and `storage.googleapis.com` on `project_id`; ensure `cloudkms.googleapis.com` is enabled on the Cloud KMS host project.
2. Provision a regional Cloud KMS key matching `region` and configure Private Services Access (`servicenetworking.googleapis.com`) on `peered_network` with an allocated `google_compute_global_address` (`purpose = "VPC_PEERING"`) and `google_service_networking_connection`.
3. Place `builder_subnetwork` in the same VPC network and host project as `peered_network`. Private pools reach builders through VPC Network Peering, which is non-transitive, so a builder subnet in a spoke VPC that only peers with `peered_network` is unreachable and the plan fails. Set `allow_builder_network_mismatch = true` only after HA VPN with custom route advertisements or Network Connectivity Center routes `peered_network_ip_range` to the builder network; `enable_ssh_firewall_rule` then creates the TCP `22` rule in the builder network. Plans read the subnetwork and its host project, so the deployer needs `compute.subnetworks.get` on `builder_subnetwork` and `resourcemanager.projects.get` on its host project.
4. Look up an immutable RHEL 9 or CIS RHEL 9 source image path for `base_image`, for example using `gcloud compute images describe-from-family rhel-9 --project=rhel-cloud --format='value(selfLink)'`.
5. Mirror the Google Cloud SDK builder container image into the private Artifact Registry repository and record its immutable `@sha256:` digest for `builder_image_digest`.
6. Reserve a deterministic IPv4 CIDR slice (such as `10.250.0.0/24`) in `peered_network_ip_range` and either set `enable_ssh_firewall_rule = true` to provision a logged `modules/net-vpc-firewall` rule or ensure your Shared VPC firewall policy permits TCP port `22` ingress solely from `peered_network_ip_range` to ephemeral VMs tagged `image-builder` inside `builder_subnetwork`.
7. Grant operators or automation principals `roles/iam.serviceAccountUser` on the builder service account before submitting builds.

## 4 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and configure your project ID, region, builder zone, immutable base image path, regional Cloud KMS key ID, peered VPC network, builder subnetwork, and digest-pinned builder image reference.
2. Initialize, validate, and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

3. Because object versioning is enabled on the CMEK staging bucket (`versioning = true`), `staging_bucket_force_destroy` defaults to `false` to protect production artifacts. For non-production or sandbox environments where `terraform destroy` should remove versioned Cloud Build objects automatically, set `staging_bucket_force_destroy = true` (or apply `-var="staging_bucket_force_destroy=true"` prior to `terraform destroy`).

## 5 Running builds

You can trigger builds automatically through `trigger_config` or submit the rendered pipeline configuration stored in the CMEK staging bucket:

1. Download the rendered YAML configuration from the `cloudbuild_config_object` output:

```bash
gcloud storage cp "$(terraform output -raw cloudbuild_config_object)" ./cloudbuild-rhel9-stig.yaml
```

2. Submit a private worker pool build using the dedicated builder service account:

```bash
gcloud builds submit --no-source \
  --project="<your-project-id>" \
  --region="<your-region>" \
  --config="./cloudbuild-rhel9-stig.yaml"
```

When using `trigger_config.repository_event`, omit the top-level `serviceAccount:` field from your committed `cloudbuild-rhel9-stig.yaml` file. Cloud Build runs triggered builds with `google_cloudbuild_trigger.default.service_account` (the dedicated builder service account) and does not use a `serviceAccount:` value from the build config. Keep `options.logging: CLOUD_LOGGING_ONLY` and `options.pool.name` from the rendered file, because builds that run as a user-specified service account require `CLOUD_LOGGING_ONLY` logging or a user-owned logs bucket.

## 6 Compliance scope

- Deploy this blueprint inside a FedRAMP High or DoD IL5 Assured Workloads folder within your Google Cloud organization.
- Ensure `region`, `builder_zone`, `kms_key_id`, and `builder_subnetwork` stay within the approved Assured Workloads regional boundary.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [base_image](variables.tf#L37) | Immutable Compute Engine source image path for RHEL 9 builds. | <code>string</code> | ✓ |  |
| [builder_image_digest](variables.tf#L108) | Artifact Registry builder image pinned by @sha256: digest. | <code>string</code> | ✓ |  |
| [builder_subnetwork](variables.tf#L177) | Full resource path of the private builder VPC subnetwork. | <code>string</code> | ✓ |  |
| [builder_zone](variables.tf#L203) | Compute Engine zone in var.region for ephemeral builder VMs. | <code>string</code> | ✓ |  |
| [kms_key_id](variables.tf#L345) | Regional Cloud KMS CryptoKey ID in var.region for CMEK. | <code>string</code> | ✓ |  |
| [peered_network](variables.tf#L379) | Peered VPC network path for the private worker pool. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L428) | Google Cloud project ID hosting the golden image factory. | <code>string</code> | ✓ |  |
| [region](variables.tf#L442) | Google Cloud region hosting image factory resources. | <code>string</code> | ✓ |  |
| [allow_builder_network_mismatch](variables.tf#L15) | Allow builder_subnetwork in a VPC other than peered_network. | <code>bool</code> |  | <code>false</code> |
| [artifact_registry_name](variables.tf#L22) | Name of the private CMEK Artifact Registry Docker repository. | <code>string</code> |  | <code>&#34;image-factory-builders&#34;</code> |
| [build_timeout](variables.tf#L55) | Maximum Cloud Build pipeline duration in seconds. | <code>string</code> |  | <code>&#34;3600s&#34;</code> |
| [builder_confidential_compute_type](variables.tf#L66) | Confidential VM type for ephemeral builders, or null. | <code>string</code> |  | <code>&#34;SEV&#34;</code> |
| [builder_machine_type](variables.tf#L129) | Compute Engine machine type for ephemeral RHEL 9 builder VMs. | <code>string</code> |  | <code>&#34;n2d-standard-2&#34;</code> |
| [builder_sa_name](variables.tf#L145) | Short account name for the Cloud Build service account. | <code>string</code> |  | <code>&#34;image-builder&#34;</code> |
| [cloudbuild_config_object_name](variables.tf#L217) | Object path in the staging bucket for the Cloud Build YAML. | <code>string</code> |  | <code>&#34;cloudbuild&#47;cloudbuild-rhel9-stig.yaml&#34;</code> |
| [enable_apis](variables.tf#L233) | Enable required Google Cloud APIs on project_id. | <code>bool</code> |  | <code>true</code> |
| [enable_ssh_firewall_rule](variables.tf#L240) | Create an ingress TCP 22 rule from peered_network_ip_range. | <code>bool</code> |  | <code>false</code> |
| [grant_service_agent_kms_iam](variables.tf#L259) | Grant Cloud KMS encrypter/decrypter IAM to service agents. | <code>bool</code> |  | <code>true</code> |
| [guest_os_features](variables.tf#L266) | Guest OS features stamped on golden images. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;SEV_CAPABLE&#34;, &#34;UEFI_COMPATIBLE&#34;, &#34;GVNIC&#34;&#93;</code> |
| [image_family](variables.tf#L315) | Compute Engine image family assigned to golden images. | <code>string</code> |  | <code>&#34;rhel-9-stig-golden&#34;</code> |
| [image_name_prefix](variables.tf#L330) | Prefix prepended to golden image names (max 26 characters). | <code>string</code> |  | <code>&#34;rhel9-stig&#34;</code> |
| [labels](variables.tf#L372) | Labels applied to the staging bucket and Artifact Registry. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [peered_network_ip_range](variables.tf#L397) | Optional CIDR block or prefix length for Cloud Build workers. | <code>string</code> |  | <code>null</code> |
| [prefix](variables.tf#L413) | Optional prefix prepended to bucket, SA, and pool names. | <code>string</code> |  | <code>null</code> |
| [staging_bucket_force_destroy](variables.tf#L452) | Allow Terraform destroy to delete objects in staging bucket. | <code>bool</code> |  | <code>false</code> |
| [staging_bucket_name](variables.tf#L459) | Name suffix of the CMEK Cloud Storage staging bucket. | <code>string</code> |  | <code>&#34;image-factory-staging&#34;</code> |
| [trigger_config](variables.tf#L472) | Optional Cloud Build trigger for repo or Pub/Sub events. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [worker_pool_disk_size_gb](variables.tf#L538) | Boot disk size in GB for private Cloud Build workers. | <code>number</code> |  | <code>100</code> |
| [worker_pool_machine_type](variables.tf#L552) | Compute Engine machine type for private Cloud Build workers. | <code>string</code> |  | <code>&#34;e2-standard-4&#34;</code> |
| [worker_pool_name](variables.tf#L571) | Name suffix of the private Cloud Build worker pool. | <code>string</code> |  | <code>&#34;image-factory-pool&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [artifact_registry_repository_id](outputs.tf#L15) | Resource ID of the CMEK Artifact Registry mirror. |  |
| [builder_service_account_email](outputs.tf#L20) | Email of the dedicated Cloud Build service account. |  |
| [cloudbuild_config_object](outputs.tf#L25) | Cloud Storage URI of the rendered Cloud Build YAML. |  |
| [staging_bucket_name](outputs.tf#L35) | Name of the CMEK Cloud Storage staging bucket. |  |
| [trigger_id](outputs.tf#L40) | ID of the optional Cloud Build trigger, or null. |  |
| [worker_pool_id](outputs.tf#L45) | Resource ID of the private Cloud Build worker pool. |  |
<!-- END TFDOC -->
