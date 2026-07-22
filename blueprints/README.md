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

# Terraform End-to-End Blueprints for Google Cloud

This repository contains Terraform Blueprints for Google Cloud, designed to accelerate the deployment of various Google Cloud services. The table below provides a comprehensive list of available blueprints, indicating their applicability for FedRAMP High (FRH) and/or Impact Level 5 (IL5) compliance regimes. Each blueprint name links directly to its respective folder containing detailed documentation and Terraform code.

For more information, please see the individual README files in each blueprint's repository.

## Available Blueprints

|  Blueprint                                                                  |  FRH                             |  IL5                             |
|-----------------------------------------------------------------------------|:--------------------------------:|:--------------------------------:|
|  [ACAS](./il5/acas/)                                                        |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Access Context Manager](./fedramp-high/access-context-manager/)            |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [App Engine](./fedramp-high/app-engine/)                                    |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Artifact Registry](./il5/artifact-registry/)                               |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Bastion Pattern](./il5/bastion-pattern/)                                   |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [BCAP](./il5/bcap/)                                                         |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [BeyondCorp](./fedramp-high/beyondcorp/)                                    |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Bigtable](./fedramp-high/bigtable/)                                        |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [BQ Project](./il5/bq-project/)                                             |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Cloud Armor](./fedramp-high/cloud-armor/)                                  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Cloud Composer Environment](./fedramp-high/cloud-composer-environment/)    |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Cloud Functions](./fedramp-high/cloud-functions/)                          |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Cloud IDS](./fedramp-high/cloud-ids/)                                      |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Cloud Run](./fedramp-high/cloud-run/)                                      |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Cloud Scheduler Job](./fedramp-high/cloud-scheduler-job/)                  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Cloud Spanner](./fedramp-high/cloud-spanner/)                              |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Cloud Translation](./fedramp-high/cloud-translation/)                      |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Cloud Workstations](./fedramp-high/cloud-workstations/)                    |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [CNAP](./fedramp-high/cnap/)                                                |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Compute Engine](./il5/compute-engine/)                                     |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Dataflow](./il5/dataflow/)                                                 |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Datafusion](./fedramp-high/datafusion/)                                    |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Dataproc Cluster](./fedramp-high/dataproc-cluster/)                        |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Datastore](./fedramp-high/datastore/)                                      |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Document AI](./fedramp-high/document-ai/)                                  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Firestore](./fedramp-high/firestore/)                                      |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [GCS Project](./il5/gcs-project/)                                           |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [GitLab](./fedramp-high/gitlab/)                                            |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [GKE](./il5/gke/)                                                           |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [GKE Hardened](./il5/gke-hardened/)                                         |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [KMS Project](./il5/kms-project/)                                           |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Network Connectivity Center](./fedramp-high/network-connectivity-center/)  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [PostgreSQL](./il5/postgresql/)                                             |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Private Service Connect](./il5/private-service-connect/)                   |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Pub Sub Project](./il5/pub-sub-project/)                                   |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Secret Manager](./fedramp-high/secret-manager/)                            |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [Shielded VM Project](./il5/shielded-vm-project/)                           |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Vertex MLOps](./fedramp-high/vertex-mlops/)                                |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |
|  [VPC Peering Project](./il5/vpc-peering-project/)                           |  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |
|  [Workflows](./fedramp-high/workflows/)                                      |  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |

<br>

**Legend**

|  Symbol                          |  Availability      |  Description                                                                                              |
|:--------------------------------:|:-------------------|:----------------------------------------------------------------------------------------------------------|
|  &nbsp; &nbsp; ✅ &nbsp; &nbsp;  |  Available         |  The blueprint **is** directly developed for the respective compliance regime                             |
|  &nbsp; &nbsp; ❌ &nbsp; &nbsp;  |  Not Available     |  The blueprint **is not** developed for the respective compliance regime.                                 |
|  &nbsp; &nbsp; 🔗 &nbsp; &nbsp;  |  Linked Blueprint  |  Indicates availability in the respective compliance regime via a symbolic link to its primary location.  |
