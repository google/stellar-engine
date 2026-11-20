# Cloud KMS project blueprint

This blueprint manages IAM bindings on existing Cloud KMS key rings and CryptoKeys provisioned by a foundational landing zone stage in a multi-project Google Cloud environment.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L15) | The Google Cloud Project ID where the existing KMS KeyRing and CryptoKeys are actually provisioned (this could be the same as `main_project_id`). | <code>string</code> | ✓ |  |
| [existing_kms_keyring_name](variables.tf#L26) | The name of the existing Cloud KMS KeyRing to manage or apply policies to. | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L40) | The Google Cloud region where the existing KMS KeyRing is located. This will also be used as the default region for the provider. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L51) | The Google Cloud Project ID where KMS-related IAM policies will be managed (i.e., the project where the existing KMS keys reside). | <code>string</code> | ✓ |  |
| [email](variables.tf#L20) | Email address of a user to grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` on every key in `existing_kms_keys`. Set to null to skip the grant. | <code>string</code> |  | <code>&#34;null &#35; Made optional, as it might not always be used&#34;</code> |
| [existing_kms_keys](variables.tf#L31) | A map where keys are the names of existing CryptoKeys within the specified KeyRing, and values are objects defining additional properties (e.g., IAM members to add). The `iam_members` attribute maps a role to the members to grant it to on the key, and its member strings must be known at plan time. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [group_email](variables.tf#L45) | Email address of a Google group to grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` on every key in `existing_kms_keys`. Set to null to skip the grant. | <code>string</code> |  | <code>&#34;null &#35; Made optional, as it might not always be used&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [managed_key_ids](outputs.tf#L17) | A map of names to fully qualified IDs for the existing CryptoKeys being managed by this blueprint. |  |
| [managed_key_self_links](outputs.tf#L25) | A map of names to self-links for the existing CryptoKeys being managed by this blueprint. |  |
| [managed_keyring_id](outputs.tf#L33) | The fully qualified ID of the existing KMS KeyRing being managed by this blueprint. |  |
| [managed_keyring_name](outputs.tf#L38) | The name of the existing KMS KeyRing being managed by this blueprint. |  |
<!-- END TFDOC -->

## 1 Cloud KMS overview

Google Cloud Key Management Service creates and manages cryptographic keys across Google Cloud services and custom workloads. This blueprint applies granular IAM bindings to Cloud KMS key rings and CryptoKeys already provisioned by your foundational landing zone:

- Grants key-level IAM roles such as `roles/cloudkms.cryptoKeyEncrypterDecrypter` to users, groups, and service accounts.
- Centralizes access governance across workload and security projects without duplicating key creation.

## 2 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and FIPS cryptographic guardrails required for federal and defense workloads.

## 3 Prerequisites

Verify that your projects, KMS resources, and IAM permissions exist before running Terraform:

- Identify `main_project_id` and `core_project_id`, where `core_project_id` hosts the existing Cloud KMS key ring and CryptoKeys.
- Provision the target Cloud KMS key ring (`existing_kms_keyring_name`) and CryptoKeys (`existing_kms_keys`) ahead of time; this blueprint references existing KMS keys rather than creating new ones.
- Grant the deploying identity `roles/cloudkms.admin`, `roles/serviceusage.serviceUsageAdmin`, and `roles/resourcemanager.projectIamAdmin` on `main_project_id` and `core_project_id` so Terraform can enable `cloudkms.googleapis.com` and manage key-level IAM policies.

## 4 Deployment steps

1. Copy the sample variables file and update `terraform.tfvars` with your project IDs, `existing_kms_keyring_name`, `existing_kms_keys`, and optional `email` or `group_email` principals such as `user@example.com`:

```bash
cp terraform.tfvars.sample terraform.tfvars
```

2. Initialize the Terraform working directory:

```bash
terraform init
```

3. Review the execution plan to verify proposed Cloud KMS IAM bindings:

```bash
terraform plan
```

4. Apply the configuration:

```bash
terraform apply
```

5. If you need to remove the IAM bindings managed by this blueprint without deleting the underlying key ring or CryptoKeys, run `terraform destroy`:

```bash
terraform destroy
```

## 5 Deployment verification

Verify the managed key ring, CryptoKeys, and IAM bindings in the Google Cloud console or with the `gcloud` CLI:

- In the Google Cloud console, open Key Management in `core_project_id`, select `existing_kms_keyring_name` and each key in `existing_kms_keys`, and confirm on the Permissions tab that `roles/cloudkms.cryptoKeyEncrypterDecrypter` and any custom roles bind to the expected principals.
- Inspect the key ring, CryptoKey metadata, and IAM policy from the command line:

```bash
gcloud kms key-rings describe <KEYRING_NAME> --location=<REGION> --project=<CORE_PROJECT_ID>
gcloud kms keys describe <KEY_NAME> --keyring=<KEYRING_NAME> --location=<REGION> --project=<CORE_PROJECT_ID>
gcloud kms keys get-iam-policy <KEY_NAME> --keyring=<KEYRING_NAME> --location=<REGION> --project=<CORE_PROJECT_ID>
```

## 6 Operational notes

- This blueprint manages IAM bindings on existing Cloud KMS key rings and CryptoKeys rather than creating new cryptographic keys.
- Match `gcp_region` to the regional or multi-regional location of `existing_kms_keyring_name`.
- Granting `roles/cloudkms.cryptoKeyEncrypterDecrypter` at the individual CryptoKey level enforces least-privilege access for service agents and operators.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L1) | The Google Cloud Project ID where KMS-related IAM policies will be managed (i.e., the project where the existing KMS keys reside). | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L6) | The Google Cloud region where the existing KMS KeyRing is located. This will also be used as the default region for the provider. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L11) | The Google Cloud Project ID where the existing KMS KeyRing and CryptoKeys are actually provisioned (this could be the same as `main_project_id`). | <code>string</code> | ✓ |  |
| [existing_kms_keyring_name](variables.tf#L16) | The name of the existing Cloud KMS KeyRing to manage or apply policies to. | <code>string</code> | ✓ |  |
| [existing_kms_keys](variables.tf#L20) | A map where keys are the names of existing CryptoKeys within the specified KeyRing, and values are objects defining additional properties (e.g., IAM members to add). | <code title="map&#40;object&#40;&#123;&#10;  iam_members &#61; optional&#40;map&#40;list&#40;string&#41;, &#123;&#125;&#41;&#10;  rotation_period_s &#61; optional&#40;number&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [email](variables.tf#L29) | Email address of a user to grant permissions on KMS keys (if used in `existing_kms_keys.iam_members`). | <code>string</code> |  | <code>null</code> |
| [group_email](variables.tf#L35) | An email address that represents a Google group to grant permissions on KMS keys (if used in `existing_kms_keys.iam_members`). | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [managed_keyring_id](outputs.tf#L16) | The fully qualified ID of the existing KMS KeyRing being managed by this blueprint. |  |
| [managed_keyring_name](outputs.tf#L21) | The name of the existing KMS KeyRing being managed by this blueprint. |  |
| [managed_key_self_links](outputs.tf#L26) | A map of names to self-links for the existing CryptoKeys being managed by this blueprint. |  |
| [managed_key_ids](outputs.tf#L33) | A map of names to fully qualified IDs for the existing CryptoKeys being managed by this blueprint. |  |
<!-- END TFDOC -->
