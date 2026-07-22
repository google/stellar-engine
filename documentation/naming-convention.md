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

# Google Cloud Naming Convention

Google Cloud services and assets have strict naming conventions in the form of character count, capitalization or lowercase, dashes, hyphens, underscores and reserved internal words.  There are also several Google Cloud services that require globally unique naming to avoid collisions, while also forever "burning" the name so it cannot be used again ever, anywhere on Google Cloud.  

To architect to these Google Cloud naming requirements we establish a "naming standard" that will determine how we name all Google Cloud resources, assets, and services to ensure compliance with the requirements.

_Throughout this documentation we use example naming and diagrams to show examples of how the naming fits.  The example company is named ACME._

# Table of Contents
<!-- BEGIN TOC -->
- [Google Cloud Naming Convention](#google-cloud-naming-convention)
- [Table of Contents](#table-of-contents)
  - [Google Cloud Org Domain](#google-cloud-org-domain)
  - [Prefix](#prefix)
  - [Google Cloud Folders](#google-cloud-folders)
  - [Google Cloud Projects](#google-cloud-projects)
  - [Google Cloud Networks](#google-cloud-networks)
  - [Google Cloud Org Policy Custom Constraints](#google-cloud-org-policy-custom-constraints)
  - [IAM Custom Roles](#iam-custom-roles)
  - [GCS Buckets](#gcs-buckets)
  - [GCE](#gce)
<!-- END TOC -->

## Google Cloud Org Domain
`acme.dev`

## Prefix

_acme_ - `ACME` is the example prefix we will use for this codebase.

A short prefix of no more than 6 characters representing the company name and or team name that will flow down through the infrastructure for all named resources.  We use this `prefix` to ensure we comply with any globally unique naming, like `Google Cloud Projects`.

_Note: The only place we _do not_ use or need the prefix is in the `Google Cloud Folders` which are only viewable within the Google Cloud WebUI.  Brevity in the Google Cloud Folder structure is paramount for clean Resource Management._

## Google Cloud Folders

Spec:

`{compliance regime}` - `{operations role}` - `{common services}`

Example:

`fedramp-high` - `logs` - `common`

[Google Cloud Folders Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-folders#creating-folders)

Google Cloud Folders should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] dashes
- [ ] no spaces

Google Cloud Folder naming is:

- [ ] _only_ viewable within the Google Cloud Org
- [ ] _not_ globally unique
- [ ] _not_ burnable
- [ ] _does not use_ the `prefix` block

## Google Cloud Projects

Spec:

`{prefix}-{compliance regime}-{environment}-{role}-{0-9}`

`{prefix}-org-{environment}-{role}-{0-9}`

Example:

Google Cloud Project - Log Warehouse at the Google Cloud Org level

`acme-org-logs-warehouse-0`

Google Cloud Project - Log Warehouse at the IL2 level

`acme-il2-logs-warehouse-0`

Google Cloud Project - IL2 Ops Terraform Host

`acme-il2-ops-iac-0`

Google Cloud Project - IL5 Wing Directorate Sandbox Environment

`acme-il5-sbx-wingdir-0`

[Google Cloud Projects Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-projects)

Google Cloud Projects should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] dashes
- [ ] no spaces

Google Cloud Projects naming is:

- [ ] _globally_ known
- [ ] _must be_ globally unique
- [ ] _forever burnable_ - once created that name can never be created again to infinity
- [ ] _must be_ 6 to 30 characters in length
- [ ] _must_ contain _only_ lowercase letters, numbers, hyphens
- [ ] _must_ start with a letter
- [ ] _cannot_ end with a hyphen
- [ ] _cannot_ contain restricted strings, such as `google` and `ssl`

## Google Cloud Networks

VPC Network
  * spec: `{prefix}-{compliance regime}-{environment}-vpc-{region}`
  * example: `acme-il2-prod-vpc-uswest`

Subnet
  * spec: `{prefix}-{compliance regime}-{environment}-subnet-{region}-{app}`
  * example: `acme-il2-prod-subnet-uswest-gke`

Internal Firewall
  * spec: `{prefix}-{compliance regime}-{environment}-fw-{source}-{dest}-{protocal}-{port}-{action}`
  * example: `acme-il2-prod-fw-gke-lb-http-80-allow`

IP Route
  * spec: `{prefix}-{compliance regime}-{environment}-route-{source}-{nexthop}`
  * example `acme-il2-prod-route-gke-niprnet`

[Google Cloud VPCs Documentation](https://cloud.google.com/architecture/best-practices-vpc-design#naming)

Google Cloud Networks should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] dashes
- [ ] no spaces

Google Cloud Networks naming is:

- [ ] _visible_ only from the Google Cloud Org
- [ ] _not_ globally unique
- [ ] _not_ burnable
- [ ] _not_ character number limited

## Google Cloud Org Policy Custom Constraints

Spec:

`custom.{prefix}{custom constraint}{00}`

Example:

`custom.acmeDoNotAllowPublicIPsonGCEVMs00`

[Google Cloud Organization Policy Custom Constraints Documentation](https://cloud.google.com/resource-manager/docs/organization-policy/creating-managing-custom-constraints#custom_constraints)

Google Cloud Org Policy Custom Constraints should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] camelCase
- [ ] no spaces

Google Cloud Org Policy Custom Constraints naming is:

- [ ] _only_ viewable outside the Google Cloud Org
- [ ] _is_ globally unique
- [ ] _is_ burnable

## IAM Custom Roles

Spec:

`{prefix}-{compliance regime}-{environment}-{rolename}-{rw ro}`

Example:

`acme-il2-ops-terraformsa-rw`

`acme-il2-ops-terraformsa-ro`

[Google Cloud IAM Custom Roles Documentation](https://cloud.google.com/iam/docs/creating-custom-roles#creating)

IAM Custom Roles should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] dashes
- [ ] no spaces

IAM Custom Roles naming is:

- [ ] _only_ viewable inside the Google Cloud Org
- [ ] _is not_ globally unique
- [ ] _is not_ burnable

## GCS Buckets

Spec:

`{prefix}-{compliance regime}-{environment}-{role}-({public})`

Example:

`acme-il2-ops-terraform-tfstate`

`acme-il2-ops-terraformsa-ro`

[Google Cloud Storage Documentation](https://cloud.google.com/storage/docs/buckets)

GCS Buckets should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] dashes
- [ ] no spaces

GCS Bucket naming is:

- [ ] _only_ viewable inside the Google Cloud Org (unless set to Public)
- [ ] _is_ globally unique
- [ ] _is not_ burnable

## GCE

Spec:

`{prefix}-{compliance regime}-{environment}-{role}-{000-999}`

Example:

`acme-fedramphigh-ops-terraform-server-001`

[Google Cloud GCE VM Documentation](https://cloud.google.com/compute/docs/naming-resources)

GCE should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] dashes
- [ ] no spaces

GCE naming is:

- [ ] _only_ viewable inside the Google Cloud Org
- [ ] _is not_ globally unique
- [ ] _is not_ burnable
- [ ] _must be_ 1-64 characters
