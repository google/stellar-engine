# Gemini Enterprise Stage 1 frontend

<!-- BEGIN TOC -->
- [1 Stage scope](#1-stage-scope)
- [2 Deployment steps](#2-deployment-steps)
- [Variables](#variables)
<!-- END TOC -->

This stage deploys the HTTPS regional Application Load Balancer, URL routing map, and Identity-Aware Proxy access bindings for Gemini Enterprise on top of remote outputs from `gemini-stage-0`. See the parent [Gemini Enterprise guide](../README.md) for full architecture and `deploy.sh` details.

## 1 Stage scope

This configuration provisions:

- Regional HTTPS target proxy, forwarding rule, and backend service targeting the `gemini-stage-0` network endpoint group.
- Path-based URL routing from each configured application path to its Discovery Engine widget ID.
- Identity-Aware Proxy IAM bindings for Gemini Enterprise admin groups, user groups, or Workforce Identity principals.

## 2 Deployment steps

1. Deploy `gemini-stage-0` first so its outputs exist in `stage_0_state_bucket`.
2. Configure `terraform.tfvars` from `terraform.tfvars.sample`.
3. Initialize, plan, and apply this stage:

```bash
terraform init -backend-config="bucket=my-state-bucket"
terraform plan
terraform apply
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [gemini_enterprise_domain](variables.tf#L25) | Your domain that you associated the reserved IP from stage 0 to. | <code>string</code> | ✓ |  |
| [stage_0_state_bucket](variables.tf#L61) | The name of the GCS bucket used for Stage 0 Terraform state. | <code>string</code> | ✓ |  |
| [cert_management_choice](variables.tf#L15) | Certificate management choice for external deployments: 'google_managed' or 'self_managed'. | <code>string</code> |  | <code>&#34;self_managed&#34;</code> |
| [host_project_id](variables.tf#L30) | The ID of the host project where the VPC network resides. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [network_name](variables.tf#L36) | The name of the VPC network. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [ssl_certificate_name](variables.tf#L43) | The name of the regional SSL certificate in Google Cloud (either pre-uploaded or created by Terraform when ssl_certificate_path and ssl_private_key_path are set). | <code>string</code> |  | <code>&#34;&#34;</code> |
| [ssl_certificate_path](variables.tf#L49) | Optional local filesystem path to a PEM-encoded SSL certificate file. When set together with ssl_private_key_path, Terraform provisions the regional self-managed SSL certificate directly. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [ssl_private_key_path](variables.tf#L55) | Optional local filesystem path to a PEM-encoded SSL private key file. When set together with ssl_certificate_path, Terraform provisions the regional self-managed SSL certificate directly. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [subnet_name](variables.tf#L66) | The name of the subnetwork for internal load balancer deployments. If empty, falls back to stage 0 outputs or default. | <code>string</code> |  | <code>&#34;&#34;</code> |
<!-- END TFDOC -->
