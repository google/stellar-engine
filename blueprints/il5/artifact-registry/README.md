# Artifact Registry blueprint

<!-- BEGIN TOC -->
- [1 Artifact Registry overview](#1-artifact-registry-overview)
- [2 Blueprint scope](#2-blueprint-scope)
- [3 Compliance scope](#3-compliance-scope)
- [4 Organization policy prerequisites](#4-organization-policy-prerequisites)
- [5 Deployment steps](#5-deployment-steps)
- [6 Deployment verification](#6-deployment-verification)
  - [Yum repositories](#yum-repositories)
  - [Docker registries](#docker-registries)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Artifact Registry overview

Google Artifact Registry stores internal CI/CD build artifacts and caches upstream public package and container registries inside your Google Cloud project across supported formats:

- Docker repositories store container images and OCI-packaged Helm charts.
- Maven repositories store Java packages built with Maven or Gradle.
- npm repositories store Node.js packages.
- Python repositories store Python distributions and wheels.
- Apt repositories store Debian packages.
- Yum repositories store RPM packages managed with Yum and DNF.
- Kubeflow repositories store Vertex AI Kubeflow pipeline templates.
- Go repositories store Go modules.

## 2 Blueprint scope

This blueprint reduces software supply chain exposure by provisioning pull-through Artifact Registry remote repositories so VMs pull RPM packages and container images from VPC-reachable caches while firewall policies block direct outbound access to external registries.

The configuration uses YAML factories to create remote Yum repositories for CentOS 9 Stream alongside remote Docker repositories for Docker Hub, Quay.io, and `registry.k8s.io`, and deploys a CentOS 9 Stream consumer VM whose startup script disables public repositories and configures `/etc/yum.repos.d/` to pull exclusively from Artifact Registry.

## 3 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and encryption guardrails required for federal and defense workloads.

## 4 Organization policy prerequisites

Before deploying into an IL5 environment, confirm that the [Restrict Resource Service Usage](https://console.cloud.google.com/iam-admin/orgpolicies/gcp-restrictServiceUsage) organization policy allows `artifactregistry.googleapis.com` on `main_project_id`:

1. Select your Google Cloud organization in the console and open [Assured Workloads](https://console.cloud.google.com/compliance/assuredworkloads).
2. Open your Stellar Engine Assured Workloads folder.
3. Under Available Updates, select `Review available updates` if updates are pending.
4. Select Allowed Services, verify `artifactregistry.googleapis.com` appears in the list, and apply the update to allow the service on downstream projects.
5. Re-check [Restrict Resource Service Usage](https://console.cloud.google.com/iam-admin/orgpolicies/gcp-restrictServiceUsage) to confirm `artifactregistry.googleapis.com` is permitted.

## 5 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and set your project IDs, VPC subnet, region, Cloud KMS key, and `developer_registries` map.
2. Initialize and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

Run `terraform destroy` if you need to tear down the deployed repositories and consumer VM.

## 6 Deployment verification

1. Open [Artifact Registry](https://console.cloud.google.com/artifacts) in the Google Cloud console and confirm the remote and standard repositories exist.
2. Open `centos9-stream-appstream` and confirm no RPM packages are cached before first pull.
3. Connect to the `rpm-consumer` VM over OS Login SSH and run `sudo dnf update -y`.
4. Refresh `centos9-stream-appstream` in Artifact Registry to verify RPM packages are now cached.
5. Pull container images through the `docker-hub` remote repository using its full Artifact Registry path, such as `docker pull us-east4-docker.pkg.dev/my-main-project/docker-hub/hello-world`.

### Yum repositories

The `yum-repos.yaml` factory provisions pull-through Yum remote repositories such as [CentOS Stream 9 BaseOS](https://mirror.stream.centos.org/9-stream/BaseOS/x86_64/os):

```yaml
yum:
  centos9-stream-baseos:
    remote:
      base: CENTOS_STREAM
      path: 9-stream/BaseOS/x86_64/os
```

Add additional entries under `yum:` to proxy more RPM upstream repositories.

### Docker registries

The `docker-registries.yaml` factory provisions pull-through Docker remote repositories:

```yaml
docker:
  registry-k8s-io:
      remote:
        uri: https://registry.k8s.io
```

Add additional entries under `docker:` to proxy more upstream container registries.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L15) | Core project ID. | <code>string</code> | ✓ |  |
| [developer_registries](variables.tf#L20) | A map of developer registries and readers/writers for those developer registries. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [kms_key_name](variables.tf#L28) | Short name of the existing KMS crypto key (for example `my-key`) used for disk encryption, not the full resource path. It is looked up in the key ring named by `kms_keyring_name`. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L33) | Keyring attributes. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L38) | GCP Project to deploy Google Artifact Registries into. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L43) | Project that the Consumer Compute Engine VPC is located. | <code>string</code> | ✓ |  |
| [region](variables.tf#L48) | GCP Region to deploy Consumer VM into. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L53) | VPC Subnet to deploy Consumer VM into. | <code>string</code> | ✓ |  |
| [vpc_network_name](variables.tf#L58) | Name of the VPC where the subnet is deployed. | <code>string</code> |  | <code>&#34;&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [docker_registries](outputs.tf#L15) | Docker registries created from the docker-registries.yaml file, with Docker Hub appended. |  |
| [yum_repositories](outputs.tf#L20) | Yum repositories created from the yum-repos.yaml file. |  |
<!-- END TFDOC -->
