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