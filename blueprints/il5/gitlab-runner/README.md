# Hardened private GitLab Runner blueprint

<!-- BEGIN TOC -->
- [1 Runner overview](#1-runner-overview)
- [2 Security controls](#2-security-controls)
- [3 Compliance scope](#3-compliance-scope)
- [4 Prerequisites](#4-prerequisites)
- [5 Deployment steps](#5-deployment-steps)
- [6 Token rotation](#6-token-rotation)
- [7 Runner lifecycle](#7-runner-lifecycle)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Runner overview

Deploy a private, confidential Compute Engine GitLab Runner on an existing Shared VPC subnetwork without public IP addresses or runtime package downloads. The blueprint composes the repository `iam-service-account`, `compute-vm`, `secret-manager`, `net-vpc-firewall`, and `net-cloudnat` modules alongside automated project API enablement and a 60-second service-agent propagation wait so CI jobs execute inside a hardened boundary that aligns with FedRAMP High and DoD Impact Level 5 controls.

## 2 Security controls

This blueprint enforces defense-in-depth controls across compute, identity, secrets, and networking.

- The runner boots strictly from a pre-baked golden image specified in the `golden_image` variable and fails closed if `systemctl`, `gitlab-runner`, or `gcloud` are absent, or, for the `docker` executor, if `docker`, `iptables`, or `docker-credential-gcloud` are absent, eliminating runtime script downloads over the internet.
- The startup script sets `CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER` to the regional endpoint, retrieves the runner authentication token from Regional Secret Manager with the `--location` flag, injects it exclusively through the `CI_SERVER_TOKEN` environment variable during non-interactive registration, unsets the variable immediately after registration, and locks `/etc/gitlab-runner/config.toml` to mode `0600`.
- For the `docker` executor, the startup script installs a `gitlab-runner-metadata-guard.service` systemd oneshot (`After=`, `PartOf=`, and `WantedBy=docker.service`) that inserts `DROP` rules for `169.254.169.254/32`, and for `fd20:ce::254/128` when `ip6tables` is usable, at the top of Docker's `DOCKER-USER` chain, so job and service containers cannot read the runner service account token or instance metadata. The startup script verifies the rule with `iptables -C` and exits without registering or starting the runner when the rule or Docker's `FORWARD` jump to `DOCKER-USER` is missing, and a `gitlab-runner.service` drop-in requires the guard unit on every later boot.
- Docker executor runners register with `--docker-privileged=false`, `--docker-cap-drop ALL`, `--docker-security-opt no-new-privileges=true`, and `--docker-disable-entrypoint-overwrite`, plus one `--docker-allowed-images` entry per `allowed_docker_images` pattern, which defaults to `docker_image` only. CI services stay disabled (`--docker-services-limit 0`) until you set `allowed_docker_services`, which also applies the capability and privilege limits to service containers. Use `docker_cap_add` to re-add only the capabilities that specific jobs need, such as `CHOWN` or `SETUID` for package installs.
- Do not use `executor = "shell"` for untrusted repositories. Shell jobs run directly on the VM, outside the `DOCKER-USER` filter, so they can query the metadata server for the runner service account token and use it to read the runner authentication token from Secret Manager.
- The `shutdown-script` first stops `gitlab-runner.service`, which the blueprint drop-in turns into a `SIGQUIT` drain (`KillMode=mixed` with a bounded `TimeoutStopSec`), and then runs `gitlab-runner unregister --config /etc/gitlab-runner/config.toml --all-runners` on a best-effort basis to remove this VM's runner manager entry. See [7 Runner lifecycle](#7-runner-lifecycle) for the shutdown time budget and reconfiguration behavior.
- When you set the `create_runner_token_secret` variable to `true`, the blueprint provisions a CMEK-encrypted regional secret through `modules/secret-manager` and supports sensitive write-only secret versions via the `runner_token_secret_wo` variable so token bytes never enter Terraform state.
- The Compute Engine VM enables AMD SEV Confidential Compute on validated `n2d`, `c2d`, or `c3d` shapes, Shielded VM secure boot, vTPM, integrity monitoring, OS Login, project SSH key blocking, disabled serial ports, and CMEK boot disk encryption using a regional Cloud KMS key in `region`, while `instance_name` is capped at 49 characters so derived firewall (`-allow-iap-ssh`) and router (`-router`) names never exceed GCE's 63-character limit.
- Boot disk snapshots stay disabled by default through the `enable_boot_disk_snapshots` variable because stateless golden-image runners store registration tokens in `/etc/gitlab-runner/config.toml`; enabling it attaches a 14-day daily snapshot schedule pinned to `storage_locations = [var.region]`.
- `docker_image`, `allowed_docker_images`, and `allowed_docker_services` accept only Artifact Registry `<location>-docker.pkg.dev` references, compared case-insensitively, and reject any `gcr.io` host; the allowlists accept `*` wildcards only after the registry host. Production FedRAMP High and IL5 deployments should point `docker_image` to a regional private Artifact Registry mirror pinned by an immutable `@sha256:` digest (as shown in `terraform.tfvars.sample`).
- The startup script registers the `gcloud` Docker credential helper for every `*-docker.pkg.dev` host used by those image inputs in root's Docker configuration (`/root/.docker/config.json`), which `gitlab-runner` reads for image pulls. Current GitLab Runner releases do not run credential helpers named in a `DOCKER_AUTH_CONFIG` variable unless `allowed_docker_credential_helpers` lists them, so the blueprint does not rely on that variable.
- The runner executes under a dedicated service account created by `modules/iam-service-account` holding only `roles/logging.logWriter`, `roles/monitoring.metricWriter`, a secret-scoped `roles/secretmanager.secretAccessor` grant on the configured regional secret, and a repository-scoped `roles/artifactregistry.reader` grant for each entry in `artifact_registry_repositories`; set `manage_kms_iam = false` when Cloud KMS IAM bindings are managed centrally outside this blueprint.
- Administrative SSH over Identity-Aware Proxy stays disabled by default through the `enable_iap_ssh` variable; enabling it deploys `modules/net-vpc-firewall` in `network_project_id` with default convenience rules disabled and an ingress rule restricted to `35.235.240.0/20`, targeting the runner service account with `INCLUDE_ALL_METADATA` logging.
- Outbound Shared VPC NAT stays disabled by default through the `enable_cloud_nat` variable; enabling it deploys `modules/net-cloudnat` in `network_project_id` with an explicit `${instance_name}-router` Cloud Router scoped to the runner subnetwork primary range and `ALL` logging enabled.

## 3 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency, CMEK encryption, and personnel access guardrails required for federal and defense CI workloads.
- Check `versions.tf` for the supported Terraform and Google provider version constraints.

## 4 Prerequisites

1. Build and publish a hardened systemd-based golden image containing `gitlab-runner` (installed as `gitlab-runner.service`) and `gcloud`. For the `docker` executor, also include `docker` with its default `iptables` firewall integration, `iptables`, and `docker-credential-gcloud` on the default `PATH` (it ships with the Google Cloud CLI). Include `curl` when you set `graceful_shutdown_secs`.
2. Confirm that the workload project in `project_id`, the Shared VPC host project in `network_project_id`, and the regional Cloud KMS key in `kms_key_id` exist in the target Assured Workloads region. When `enable_apis = true` (default), Terraform enables `compute.googleapis.com`, `logging.googleapis.com`, `monitoring.googleapis.com`, and `secretmanager.googleapis.com` on `project_id`.
3. Enable Private Google Access on `subnetwork_name` with Cloud DNS private zones in `network_name` routing `*.googleapis.com` to `199.36.153.4/30` or `199.36.153.8/30` (or global PSC), configure a Private Service Connect (PSC) regional endpoint or backend with Cloud DNS mapping `secretmanager.<region>.rep.googleapis.com` to its internal PSC IP when `enable_cloud_nat = false`, and mirror your CI base container image into a regional private Artifact Registry repository pinned by `@sha256:` digest.
4. Mirror every default, job, and service image into Artifact Registry and list each repository in `artifact_registry_repositories` so the runner service account gets `roles/artifactregistry.reader` on it, or grant that role outside this blueprint. When `enable_cloud_nat = false`, also resolve `*.pkg.dev` to the same Private Google Access VIP so image pulls stay private.
5. Create a runner in your GitLab instance over HTTPS and store its authentication token in a CMEK-encrypted Regional Secret Manager secret, or set `create_runner_token_secret = true` to provision the regional secret container with this blueprint.
6. Ensure your deploying Terraform identity holds IAM permissions to create service accounts, Compute Engine instances, Cloud KMS key IAM members when `manage_kms_iam = true`, Secret Manager resources or IAM bindings, Artifact Registry repository IAM members when `artifact_registry_repositories` is set, and optional firewall or Cloud NAT resources in `network_project_id`, plus `roles/compute.networkUser` on `subnetwork_name` in `network_project_id` when deploying onto a Shared VPC (`network_project_id != project_id`).

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
3. Pin `runner_token_secret_version` to the new version number, or increment `wo_version` when Terraform writes the token, apply, and reboot the runner VM; the startup script detects the changed registration fingerprint, drains the runner, and registers again with the new token. With `runner_token_secret_version = "latest"` and a version added outside Terraform, the fingerprint does not change, so replace or recreate the VM instead. With modern `glrt-` runner authentication tokens, `gitlab-runner unregister` removes only this VM's runner manager entry; remove retired runner records directly in the GitLab UI or REST API when permanently decommissioning a runner.

## 7 Runner lifecycle

- Changes to registration inputs update the startup script metadata in place without replacing the VM, so they take effect on the next reboot. The startup script hashes every registration input (GitLab URL, executor, images, services, capabilities, token secret ID and version, and the startup template itself), stores the hash in `/etc/gitlab-runner/.registration-fingerprint` with mode `0600` after a successful registration, and on each boot drains the runner, unregisters it, and registers again when the stored hash is missing or different. Runner tags are not part of the hash because GitLab manages them on the server for runner authentication tokens.
- When unregister fails, for example because GitLab is unreachable, the startup script still removes the stale `[[runners]]` entries from `config.toml` before it registers again, so an outdated registration never stays active.
- Compute Engine gives the guest OS up to 120 seconds to shut down after a stop or delete. The drop-in sets `TimeoutStopSec` to `graceful_shutdown_secs` plus 90 seconds, which leaves about 30 seconds for `gitlab-runner unregister`, and systemd kills jobs that are still running at the timeout. An idle runner can take up to 60 seconds to exit on `SIGQUIT` while it waits for an open job request.
- Set `graceful_shutdown_secs` (1 to 21600) to enable Compute Engine graceful shutdown on the VM. Compute Engine runs metadata shutdown scripts only after the graceful period ends, so the startup script also installs `gitlab-runner-shutdown-watcher.service`, which polls the `shutdown-status` metadata key, drains the runner as soon as the VM enters `PENDING_STOP`, and then runs `shutdown -h now` to end the period early. Compute Engine skips graceful shutdown for host errors and for host maintenance stops of VMs that use the `TERMINATE` maintenance policy, which this Confidential VM does, so those events get only the 120-second window.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [gitlab_url](variables.tf#L186) | HTTPS base URL of the GitLab coordinator instance. | <code>string</code> | ✓ |  |
| [golden_image](variables.tf#L199) | Pre-baked GCE golden image or family with gitlab-runner. | <code>string</code> | ✓ |  |
| [kms_key_id](variables.tf#L250) | Regional Cloud KMS crypto key ID in region for CMEK. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L309) | VPC network name in network_project_id. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L321) | Project ID hosting the Shared VPC network and subnetwork. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L333) | Workload project ID hosting the GitLab Runner VM and SA. | <code>string</code> | ✓ |  |
| [region](variables.tf#L345) | GCP region for subnetwork, regional secret, and Cloud NAT. | <code>string</code> | ✓ |  |
| [runner_token_secret_id](variables.tf#L355) | Regional Secret Manager ID holding the GitLab Runner token. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L465) | Subnetwork name in network_project_id and region. | <code>string</code> | ✓ |  |
| [zone](variables.tf#L477) | GCP compute zone inside region for the GitLab Runner VM. | <code>string</code> | ✓ |  |
| [allowed_docker_images](variables.tf#L15) | Job image allowlist patterns; null allows only docker_image. | <code>list&#40;string&#41;</code> |  | <code>null</code> |
| [allowed_docker_services](variables.tf#L40) | Service image allowlist patterns; empty disables CI services. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [artifact_registry_repositories](variables.tf#L59) | Artifact Registry repositories the runner SA may read. | <code>list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#91;&#93;</code> |
| [boot_disk_size_gb](variables.tf#L80) | Size of the runner boot disk in GiB. | <code>number</code> |  | <code>50</code> |
| [boot_disk_type](variables.tf#L91) | Persistent disk type for the runner boot disk. | <code>string</code> |  | <code>&#34;pd-balanced&#34;</code> |
| [create_runner_token_secret](variables.tf#L102) | Create a CMEK regional Secret Manager secret for the runner. | <code>bool</code> |  | <code>false</code> |
| [docker_cap_add](variables.tf#L109) | Capabilities re-added to job and service containers. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [docker_image](variables.tf#L127) | Default Artifact Registry image when executor is docker. | <code>string</code> |  | <code>&#34;us-docker.pkg.dev&#47;google.com&#47;cloudsdktool&#47;google-cloud-cli:slim&#34;</code> |
| [enable_apis](variables.tf#L147) | Enable required Google Cloud APIs on var.project_id. | <code>bool</code> |  | <code>true</code> |
| [enable_boot_disk_snapshots](variables.tf#L154) | Attach an optional daily 14-day boot disk snapshot schedule. | <code>bool</code> |  | <code>false</code> |
| [enable_cloud_nat](variables.tf#L161) | Provision an optional Cloud NAT in network_project_id. | <code>bool</code> |  | <code>false</code> |
| [enable_iap_ssh](variables.tf#L168) | Create a logged SA-targeted IAP SSH firewall rule. | <code>bool</code> |  | <code>false</code> |
| [executor](variables.tf#L175) | GitLab Runner job executor type: docker or shell. | <code>string</code> |  | <code>&#34;docker&#34;</code> |
| [graceful_shutdown_secs](variables.tf#L217) | Optional Compute Engine graceful shutdown period in seconds. | <code>number</code> |  | <code>null</code> |
| [instance_name](variables.tf#L235) | Compute Engine instance name for the GitLab Runner VM. | <code>string</code> |  | <code>&#34;gitlab-runner-0&#34;</code> |
| [labels](variables.tf#L277) | Labels applied to the runner instance and boot disk. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [machine_type](variables.tf#L284) | AMD SEV-compatible GCE machine type for the runner VM. | <code>string</code> |  | <code>&#34;n2d-standard-4&#34;</code> |
| [manage_kms_iam](variables.tf#L302) | Manage Cloud KMS IAM bindings for Compute and Secret agents. | <code>bool</code> |  | <code>true</code> |
| [runner_token_secret_project_id](variables.tf#L367) | Optional project ID hosting an existing regional secret. | <code>string</code> |  | <code>null</code> |
| [runner_token_secret_version](variables.tf#L395) | Secret Manager version identifier read by startup script. | <code>string</code> |  | <code>&#34;latest&#34;</code> |
| [runner_token_secret_wo](variables.tf#L408) | Optional write-only secret version avoiding Terraform state. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [service_account_id](variables.tf#L452) | Account ID for the dedicated GitLab Runner service account. | <code>string</code> |  | <code>&#34;gitlab-runner-sa&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [instance_id](outputs.tf#L15) | Fully qualified ID of the GitLab Runner VM instance. |  |
| [instance_internal_ip](outputs.tf#L20) | Internal IP address of the GitLab Runner VM instance. |  |
| [service_account_email](outputs.tf#L25) | Email address of the dedicated GitLab Runner service account. |  |
<!-- END TFDOC -->
