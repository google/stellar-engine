# FAST stages

Each subdirectory in `fast/stages-aw/` is a standalone Terraform root module representing a landing zone stage. You can deploy a single stage in isolation, such as provisioning a hub-and-spoke VPC in an existing environment, or combine all stages sequentially to configure a Google Cloud organization from the top down.

Each stage consumes outputs from earlier stages and exports configuration contracts for downstream stages:

- You can replace any stage implementation as long as it provides the expected outputs and accepts the upstream stage inputs.
- Automated output files pass provider and `.auto.tfvars.json` definitions forward between stages as described in the [Stage 0 documentation](./0-bootstrap/README.md), eliminating manual variable transcription.
- Data flows strictly forward through the stage sequence so earlier stages never depend on downstream outputs.
- Stages use Google Cloud [delegated role grants](https://medium.com/google-cloud/managing-gcp-service-usage-through-delegated-role-grants-a843610f2226) to scope organization-level IAM administration to specific roles per stage.

Refer to each stage `README.md` file for architectural details and deployment steps, and follow the cleanup instructions to tear down an existing deployment.

## 1 Stage architecture diagram

![Stellar Engine Fast Stages](../stages.png)

## 2 Organization stages

- [0-bootstrap](0-bootstrap/README.md) provisions the top-level Assured Workloads folder, stage automation service accounts and state buckets, organization policies, and organization-level audit log sinks, and exports automation variables and custom roles.
- [1-resman](1-resman/README.md) creates the environment, networking, security, and tenant folder hierarchy, configures resource management tags for scoped IAM bindings, and provisions tenant projects. Update `terraform.tfvars` in this stage and re-apply Terraform to add, modify, or remove tenant definitions.

## 3 Networking stages

- [2-networking-a-fedramp](/fast/stages-aw/2-networking-a-fedramp/README.md) deploys a Network Connectivity Center hub-and-spoke architecture for FedRAMP High, FedRAMP Moderate, and IL2 environments.
- [2-networking-b-il5-ngfw](2-networking-b-il5-ngfw/README.md) deploys a Palo Alto VM-Series Next-Generation Firewall hub-and-spoke architecture for IL4 and IL5 environments.

Stage 2 centralizes Shared VPC host projects, subnets, Cloud DNS zones, and firewall policies for the networking team. Design hybrid connectivity separately according to your on-premises transit requirements.

## 4 Security stage

- [3-security](3-security/README.md) provisions security projects, centralized Cloud KMS keys, CIS log metric alerts, and VPC Service Controls perimeters across the landing zone. See the [Security Best Practices Guide](../../docs/security-best-practices.md) for additional hardening guidance.

