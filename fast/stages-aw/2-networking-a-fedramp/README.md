# FedRAMP High / Moderate Network

This stage deploys the networking infrastructure recommended with an Assured Workload FedRAMP High, FedRAMP Moderate, or DoD Impact Level 2 (IL2) environment.

## Regime Coverage, Regional Support, and IL2 Placement

- Earlier design material referenced a separate `2-networking-c-fedramp-mod` stage using Cloud NGFW endpoints in a single VPC. That pattern was superseded by consolidating FedRAMP Moderate, FedRAMP High, and IL2 into `2-networking-a-fedramp` so all three share a consistent VDSS (Landing + DMZ) topology (SC-7, AC-4), with `kms_protection_level` (`SOFTWARE` vs. `HSM`) controlling key protection (SC-12, SC-13).
- While the Stage 0 `FEDRAMP_MODERATE` organization policy template only denies `in:asia-east2-locations` and `in:global`, this networking stage is validated and supported for US regions (`in:us-locations`, such as `us-east4`, `us-west1`, and `us-central1`).
- Replace every `<region>` placeholder in the sample `terraform.tfvars` file with the `regions.primary` value from Stage 0, because the stage validates that the first tenant subnet of each environment uses that region.
- `IL2` workloads land on `2-networking-a-fedramp`; `IL4` and `IL5` workloads use `2-networking-b-il5-ngfw`.

## Firewall Governance Coexistence

Stage 2 attaches a **hierarchical firewall policy** (`module.firewall-policy-default`) to the `Networking` folder to enforce baseline ingress governance across all environment spoke VPCs. Individual workload blueprints (such as `blueprints/fedramp-high/postgresql` and `blueprints/il5/postgresql`) may additionally provision blueprint-local **classic VPC firewall rules** (`google_compute_firewall`) directly in the Shared VPC host project (`network_project_id`).

- Google Cloud evaluates hierarchical firewall policies first, followed by global/regional network firewall policies, and finally classic VPC firewall rules (unless an earlier rule explicitly short-circuits evaluation without `goto_next`).
- When collecting CM-6 / SC-7 firewall evidence, inspect both the folder-level hierarchical policy (`gcloud compute firewall-policies rules list --firewall-policy=<policy-id> --organization=<org-id>`) and the host-project VPC firewall rules (`gcloud compute firewall-rules list --project=<network-project-id>`).

<p align="center">
  <img src="/fast/stages-aw/2-networking-a-fedramp/images/Stellar-Engine-Network-FedRAMP.png" alt="Networking diagram">
</p>

<!-- BEGIN TOC -->
- [Regime Coverage, Regional Support, and IL2 Placement](#regime-coverage-regional-support-and-il2-placement)
- [Firewall Governance Coexistence](#firewall-governance-coexistence)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

---
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [alert_email](variables.tf#L17) | Email to receive log alerts. | <code>string</code> | ✓ |  |
| [automation](variables.tf#L33) | Automation resources created by the bootstrap stage. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [billing_account](variables.tf#L41) | Billing account id. If billing account is not part of the same org set `is_org_level` to false. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [envs_folders](variables.tf#L108) | List of environments to be created for projects to go into. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [folder_ids](variables.tf#L183) | Folders to be used for the networking resources in folders/nnnnnnnnnnn format. If null, folder will be created. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [organization](variables.tf#L230) | Organization details. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [prefix](variables.tf#L246) | Prefix used for resources that need unique names. Use 9 characters or less. | <code>string</code> | ✓ |  |
| [regions](variables.tf#L296) | Region definitions. Inherited from 0-bootstrap outputs. Must be specified in bootstrap terraform.tfvars. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [tenant_accounts](variables.tf#L357) | Base Tenant accounts that are created for each folder, provided as a combination of environment and tenant. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [assured_workloads](variables.tf#L22) | Configuration for Assured Workloads. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [billing_override](variables.tf#L54) | Optional billing override configuration. If set, disables service account impersonation for project billing linkage and runs under the user account using the specified quota projects. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [cidrs](variables.tf#L63) | Named CIDR ranges to use in firewall rules. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [common_services_folder](variables.tf#L70) | Common services folder ID. | <code>string</code> |  | <code>null</code> |
| [custom_roles](variables.tf#L76) | Custom roles defined at the org level, in key => id format. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [dns](variables.tf#L84) | DNS configuration. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [dns_policy_rules](variables.tf#L94) | DNS response policy rules in name => rule format. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [essential_contacts](variables.tf#L115) | Email or map of emails to notification category lists used for essential contacts, unset if null or empty. | <code>any</code> |  | <code>&#123;&#125;</code> |
| [factories_config](variables.tf#L129) | Configuration for network resource factories. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [fast_features](variables.tf#L146) | FAST features enabled. | <code>any</code> |  | <code>null</code> |
| [firewall_rules](variables.tf#L152) | Firewall rules for each VPC / environment spoke. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [gcp_ranges](variables.tf#L192) | GCP address ranges in name => range format. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [groups](variables.tf#L203) | IAM groups mapping. | <code>any</code> |  | <code>null</code> |
| [kms_protection_level](variables.tf#L209) | KMS protection level. | <code>string</code> |  | <code>null</code> |
| [logging](variables.tf#L217) | Logging configuration. | <code>any</code> |  | <code>null</code> |
| [nva_spot_vms](variables.tf#L223) | Whether to provision NVA instances as Spot VMs. Defaults to false (standard on-demand instances with automatic restart). | <code>bool</code> |  | <code>false</code> |
| [outputs_location](variables.tf#L240) | Path where providers and tfvars files for the following stages are written. Leave empty to disable. | <code>string</code> |  | <code>null</code> |
| [proxy_subnets](variables.tf#L257) | VPC proxy-only subnet CIDRs keyed by environment. One entry per key of envs_folders is required: every environment spoke gets a proxy-only subnet in regions.primary. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [psa_ranges](variables.tf#L270) | IP ranges used for Private Service Access (e.g. CloudSQL). Ranges is in name => range format. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [regime_mapping](variables.tf#L290) | Compliance regime shorthand mapping. | <code>any</code> |  | <code>null</code> |
| [service_accounts](variables.tf#L305) | Automation service accounts in name => email format. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [spoke_project_iam](variables.tf#L319) | Additional authoritative IAM bindings for environment spoke host projects, keyed by environment name (for example dev or prod) and role. | <code>map&#40;map&#40;list&#40;string&#41;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [subnets](variables.tf#L326) | VPC subnet configurations keyed by network name. | <code>map&#40;list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [host_project_ids](outputs.tf#L62) | Network project ids. |  |
| [host_project_numbers](outputs.tf#L67) | Network project numbers. |  |
| [tfvars](outputs.tf#L72) | Terraform variables file for the following stages. | ✓ |
<!-- END TFDOC -->
