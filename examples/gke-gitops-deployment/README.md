<!--
Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

## Example Tenant Deployment - GKE With GitOps

This environment is an example utilizing cloud build to deploy a FastApi service on GKE in the
FRH -> Project [tenant] Test -> XXX-test-[tenant]-main-0 project after running the Deployment stage

This example follows the use of the Cloud Build Automation for Terraform blueprint. 
Details can be found there on deployment. [README](../../blueprints/il5/cloudbuild-tf-automation/README.md)

These are key parts to this example:
1. Cloud Build blueprint deployed
1. Configured folder to deploy GKE in the environment (example in the [environments/int](./environments/int) folder)
1. Container built and available in Artifact Registry
1. External Git repository with GKE manifests for deployment (example in the [gitops](./gitops/) folder)
   The Terraform code will point to this repo when configuring GKE
1. The certificate created will need to be configured with a CNAME record in you domain's zone DNS
1. An A record will be needed to point to the static IP created in Terraform


Additional Note:
There are some organizational policies that may require exemption base on how the load balancers are configured
with a certificate.
 - compute.restrictLoadBalancerCreationForTypes
 - compute.disableGlobalLoadBalancing