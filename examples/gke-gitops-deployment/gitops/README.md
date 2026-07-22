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

## GitOps Deployment
This folder represents an example repository holding Kubernetes manifests to 
deploy a containerized FastAPI application with required supporting infrastructure
for GKE to build the loadbalancer and set up a secure connection with a certificate.

This code should be deployed in a Git repository and pointed to from the gke.tf file 
```
module "gke-deployment" {
  ...
  source_branch = var.source_branch
  source_dir    = var.source_dir
  source_repo   = var.source_repo
}
```

# Flash Sample Deployment

To create the CRDs for the Gateway and HTTPRoute, run
```
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

To update the cluster after the gateway is applied through gitops, run
```
gcloud container clusters update CLUSTER_NAME --gateway-api=standard --zone=CLUSTER_ZONE --project=PROJECT_ID
```