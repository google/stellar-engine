# Hardened private GitLab Runner blueprint

<!-- BEGIN TOC -->
- [1 Runner overview](#1-runner-overview)
- [2 Security controls](#2-security-controls)
- [3 Compliance scope](#3-compliance-scope)
- [4 Prerequisites](#4-prerequisites)
- [5 Deployment steps](#5-deployment-steps)
- [6 Token rotation](#6-token-rotation)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Runner overview

Deploy a private, confidential Compute Engine GitLab Runner on an existing Shared VPC subnetwork without public IP addresses or runtime package downloads. The blueprint composes the repository `iam-service-account`, `compute-vm`, `secret-manager`, `net-vpc-firewall`, and `net-cloudnat` modules alongside automated project API enablement and a 60-second service-agent propagation wait so CI jobs execute inside a hardened boundary that aligns with FedRAMP High and DoD Impact Level 5 controls.

## 2 Security controls

This blueprint enforces defense-in-depth controls across compute, identity, secrets, and networking.

- The runner boots strictly from a pre-baked golden image specified in the `golden_image` variable and fails closed if the `gitlab-runner`, `gcloud`, or `docker` binaries are absent, eliminating runtime script downloads over the internet.
- The startup script sets `CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER` to the regional endpoint, retrieves the runner authentication token from Regional Secret Manager with the `--location` flag, injects it exclusively through the `CI_SERVER_TOKEN` environment variable during non-interactive registration, unsets the variable immediately after registration, and locks `/etc/gitlab-runner/config.toml` to mode `0600`.
- A best-effort `shutdown-script` runs `gitlab-runner unregister --config /etc/gitlab-runner/config.toml --all-runners || true` on VM stop or replacement to clean up local runner manager entries.
- When you set the `create_runner_token_secret` variable to `true`, the blueprint provisions a CMEK-encrypted regional secret through `modules/secret-manager` and supports sensitive write-only secret versions via the `runner_token_secret_wo` variable so token bytes never enter Terraform state.
- The Compute Engine VM enables AMD SEV Confidential Compute on validated `n2d`, `c2d`, or `c3d` shapes, Shielded VM secure boot, vTPM, integrity monitoring, OS Login, project SSH key blocking, disabled serial ports, and CMEK boot disk encryption using a regional Cloud KMS key in `region`, while `instance_name` is capped at 49 characters so derived firewall (`-allow-iap-ssh`) and router (`-router`) names never exceed GCE's 63-character limit.
- Boot disk snapshots stay disabled by default through the `enable_boot_disk_snapshots` variable because stateless golden-image runners store registration tokens in `/etc/gitlab-runner/config.toml`; enabling it attaches a 14-day daily snapshot schedule pinned to `storage_locations = [var.region]`.
- The `docker_image` variable rejects legacy `gcr.io` paths and defaults to Artifact Registry; production FedRAMP High and IL5 deployments should point `docker_image` to a regional private Artifact Registry mirror pinned by an immutable `@sha256:` digest (as shown in `terraform.tfvars.sample`).
- The runner executes under a dedicated service account created by `modules/iam-service-account` holding only `roles/logging.logWriter`, `roles/monitoring.metricWriter`, and a secret-scoped `roles/secretmanager.secretAccessor` grant on the configured regional secret; set `manage_kms_iam = false` when Cloud KMS IAM bindings are managed centrally outside this blueprint.
- Administrative SSH over Identity-Aware Proxy stays disabled by default through the `enable_iap_ssh` variable; enabling it deploys `modules/net-vpc-firewall` in `network_project_id` with default convenience rules disabled and an ingress rule restricted to `35.235.240.0/20`, targeting the runner service account with `INCLUDE_ALL_METADATA` logging.
- Outbound Shared VPC NAT stays disabled by default through the `enable_cloud_nat` variable; enabling it deploys `modules/net-cloudnat` in `network_project_id` with an explicit `${instance_name}-router` Cloud Router scoped to the runner subnetwork primary range and `ALL` logging enabled.

## 3 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency, CMEK encryption, and personnel access guardrails required for federal and defense CI workloads.
- Check `versions.tf` for the supported Terraform and Google provider version constraints.

## 4 Prerequisites

1. Build and publish a hardened golden image containing `gitlab-runner`, `gcloud`, and `docker` when using the `docker` executor.
2. Confirm that the workload project in `project_id`, the Shared VPC host project in `network_project_id`, and the regional Cloud KMS key in `kms_key_id` exist in the target Assured Workloads region. When `enable_apis = true` (default), Terraform enables `compute.googleapis.com`, `logging.googleapis.com`, `monitoring.googleapis.com`, and `secretmanager.googleapis.com` on `project_id`.
3. Enable Private Google Access on `subnetwork_name` and configure Cloud DNS private zones in `network_name` routing `*.googleapis.com` and regional `*.rep.googleapis.com` (including `secretmanager.<region>.rep.googleapis.com`) to `199.36.153.4/30` or `199.36.153.8/30`, and mirror your CI base container image into a regional private Artifact Registry repository pinned by `@sha256:` digest when `enable_cloud_nat = false`.
4. Create a runner in your GitLab instance over HTTPS and store its authentication token in a CMEK-encrypted Regional Secret Manager secret, or set `create_runner_token_secret = true` to provision the regional secret container with this blueprint.
5. Ensure your deploying Terraform identity holds IAM permissions to create service accounts, Compute Engine instances, Cloud KMS key IAM members when `manage_kms_iam = true`, Secret Manager resources or IAM bindings, and optional firewall or Cloud NAT resources in `network_project_id`, plus `roles/compute.networkUser` on `subnetwork_name` in `network_project_id` when deploying onto a Shared VPC (`network_project_id != project_id`).

## 5 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and set your project IDs, Shared VPC network and subnetwork names, regional Cloud KMS key ID, golden image path, private Artifact Registry `docker_image` digest, GitLab HTTPS URL, and regional secret ID.
2. Initialize, inspect, and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

Applying the configuration outputs the runner instance ID, internal IP address, and dedicated service account email without exposing any secret token values.

## 6 Token rotation

Rotate the GitLab Runner authentication token without placing plaintext secrets in Terraform files or state.

1. Generate a replacement authentication token in GitLab and add a new regional secret version using the regional Secret Manager endpoint:

```bash
printf '%s' "${NEW_TOKEN}" | \
  CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER="https://secretmanager.us-east4.rep.googleapis.com/" \
  gcloud secrets versions add my-runner-token \
    --data-file=- \
    --project=my-runner-project-0 \
    --location=us-east4
```

2. If you manage versions with the `runner_token_secret_wo` variable, supply the replacement token through a mode `0600` local file path rather than a committed literal in `terraform.tfvars`, increment `wo_version`, and run `terraform apply`.
3. Replace or recreate the runner VM from the latest golden image so startup registration picks up the new version cleanly. Note that when using modern `glrt-` runner authentication tokens, the VM's `shutdown-script` (`gitlab-runner unregister --all-runners`) unregisters only the local runner manager entry; remove retired top-level runner records directly in the GitLab UI or REST API when permanently decommissioning a runner.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [gitlab_url](variables.tf#L98) | HTTPS base URL of the GitLab coordinator instance. | <code>string</code> | ✓ |  |
| [golden_image](variables.tf#L111) | Pre-baked GCE golden image or family with gitlab-runner. | <code>string</code> | ✓ |  |
| [kms_key_id](variables.tf#L144) | Regional Cloud KMS crypto key ID in region for CMEK. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L203) | VPC network name in network_project_id. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L215) | Project ID hosting the Shared VPC network and subnetwork. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L227) | Workload project ID hosting the GitLab Runner VM and SA. | <code>string</code> | ✓ |  |
| [region](variables.tf#L239) | GCP region for subnetwork, regional secret, and Cloud NAT. | <code>string</code> | ✓ |  |
| [runner_token_secret_id](variables.tf#L249) | Regional Secret Manager ID holding the GitLab Runner token. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L359) | Subnetwork name in network_project_id and region. | <code>string</code> | ✓ |  |
| [zone](variables.tf#L371) | GCP compute zone inside region for the GitLab Runner VM. | <code>string</code> | ✓ |  |
| [boot_disk_size_gb](variables.tf#L15) | Size of the runner boot disk in GiB. | <code>number</code> |  | <code>50</code> |
| [boot_disk_type](variables.tf#L26) | Persistent disk type for the runner boot disk. | <code>string</code> |  | <code>&#34;pd-balanced&#34;</code> |
| [create_runner_token_secret](variables.tf#L37) | Create a CMEK regional Secret Manager secret for the runner. | <code>bool</code> |  | <code>false</code> |
| [docker_image](variables.tf#L44) | Default Artifact Registry image when executor is docker. | <code>string</code> |  | <code>&#34;us-docker.pkg.dev&#47;google.com&#47;cloudsdktool&#47;google-cloud-cli:slim&#34;</code> |
| [enable_apis](variables.tf#L59) | Enable required Google Cloud APIs on var.project_id. | <code>bool</code> |  | <code>true</code> |
| [enable_boot_disk_snapshots](variables.tf#L66) | Attach an optional daily 14-day boot disk snapshot schedule. | <code>bool</code> |  | <code>false</code> |
| [enable_cloud_nat](variables.tf#L73) | Provision an optional Cloud NAT in network_project_id. | <code>bool</code> |  | <code>false</code> |
| [enable_iap_ssh](variables.tf#L80) | Create a logged SA-targeted IAP SSH firewall rule. | <code>bool</code> |  | <code>false</code> |
| [executor](variables.tf#L87) | GitLab Runner job executor type: docker or shell. | <code>string</code> |  | <code>&#34;docker&#34;</code> |
| [instance_name](variables.tf#L129) | Compute Engine instance name for the GitLab Runner VM. | <code>string</code> |  | <code>&#34;gitlab-runner-0&#34;</code> |
| [labels](variables.tf#L171) | Labels applied to the runner instance and boot disk. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [machine_type](variables.tf#L178) | AMD SEV-compatible GCE machine type for the runner VM. | <code>string</code> |  | <code>&#34;n2d-standard-4&#34;</code> |
| [manage_kms_iam](variables.tf#L196) | Manage Cloud KMS IAM bindings for Compute and Secret agents. | <code>bool</code> |  | <code>true</code> |
| [runner_token_secret_project_id](variables.tf#L261) | Optional project ID hosting an existing regional secret. | <code>string</code> |  | <code>null</code> |
| [runner_token_secret_version](variables.tf#L289) | Secret Manager version identifier read by startup script. | <code>string</code> |  | <code>&#34;latest&#34;</code> |
| [runner_token_secret_wo](variables.tf#L302) | Optional write-only secret version avoiding Terraform state. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [service_account_id](variables.tf#L346) | Account ID for the dedicated GitLab Runner service account. | <code>string</code> |  | <code>&#34;gitlab-runner-sa&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [instance_id](outputs.tf#L15) | Fully qualified ID of the GitLab Runner VM instance. |  |
| [instance_internal_ip](outputs.tf#L20) | Internal IP address of the GitLab Runner VM instance. |  |
| [service_account_email](outputs.tf#L25) | Email address of the dedicated GitLab Runner service account. |  |
<!-- END TFDOC -->
