# Google Cloud Naming Convention

Google Cloud services and assets have strict naming conventions in the form of character count, capitalization or lowercase, dashes, hyphens, underscores and reserved internal words.  There are also several Google Cloud services that require globally unique naming to avoid collisions, while also forever "burning" the name so it cannot be used again ever, anywhere on Google Cloud.  

To architect to these Google Cloud naming requirements we establish a "naming standard" that will determine how we name all Google Cloud resources, assets, and services to ensure compliance with the requirements.

_Throughout this documentation we use example naming and diagrams to show examples of how the naming fits.  The example company is named example._

# Table of Contents
<!-- BEGIN TOC -->
- [Google Cloud Naming Convention](#google-cloud-naming-convention)
- [Table of Contents](#table-of-contents)
  - [Google Cloud Org Domain](#google-cloud-org-domain)
  - [Base](#base)
  - [Google Cloud Folders](#google-cloud-folders)
  - [Google Cloud Projects](#google-cloud-projects)
  - [Google Cloud Networks](#google-cloud-networks)
  - [Google Cloud Org Policy Custom Constraints](#google-cloud-org-policy-custom-constraints)
  - [IAM Custom Roles](#iam-custom-roles)
  - [GCS Buckets](#gcs-buckets)
  - [GCE](#gce)
<!-- END TOC -->

## Google Cloud Org Domain
`example.internal`

## Base

_example_ - `example` is the example we will use for this codebase.

3 or 4 letters representing the company name and or team name that will flow down through the infrastructure for all named resources.  We use this `base` to ensure we comply with any globally unique naming, like `Google Cloud Projects`.  

_Note: The only place we _do not_ use or need the base is in the `Google Cloud Folders` which are only viewable within the Google Cloud WebUI.  Brevity in the Google Cloud Folder structure is paramount for clean Resource Management._

## Google Cloud Folders

Spec:

`{prefix}` - `{compliance regime}` - `{tenant}`

Example:

`edtl` - `il5` - `tenant`

[Google Cloud Folders Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-folders#creating-folders)

Google Cloud Folders should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] dashes
- [ ] no spaces

Google Cloud Folder naming is:

- [ ] _only_ viewable within the Google Cloud Org
- [ ] _not_ globally unique
- [ ] _not_ burnable
- [ ] _does not use_ the `base` block

## Google Cloud Projects

Spec:

`{prefix}-{compliance regime}-{environment}-{role}-{sub-role}`

`{tenant}-{environment}-{appname}-{environment abbreviation}`

Example:

Google Cloud Project - Core Infrastructure:
`macom-env-iac-core`

Google Cloud Project - Application Specific:
`macom-env-appname-d`

Google Cloud Project - NetSec Services:
`edtl-il5-prod-audit-logs`

Google Cloud Projects Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-projects)

Google Cloud Projects should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] dashes
- [ ] no spaces

Google Cloud Projects naming is:

- [ ] _globally_ known
- [ ] _must be_ globally unique
- [ ] _forever burnable_ - once created that name can never be created again to infinity
- [ ] _must be_ 6 to 30 characters in length
- [ ] _app name max of_ 7 characters in length
- [ ] _environment abbreviation_ is 1 characters in length
- [ ] _must_ contain _only_ lowercase letters, numbers, hyphens
- [ ] _must_ start with a letter
- [ ] _cannot_ end with a hyphen
- [ ] _cannot_ contain restricted strings, such as `google` and `ssl`

## Google Cloud Networks

VPC Network
  * spec: `{prefix}-{compliance regime}-{environment}-{role}-host`
  * example: `edtl-il5-env-net-host`

Subnet
  * spec: `{environment}-{tenant}-{region}-subnet`
  * example: `env-macom-us-east4-subnet`

Internal Firewall
  * spec: `{prefix}-{role}-default-{compliance_regime}`
  * example: `edtl-net-default-il5`

IP Route
  * spec: `{network_name}-{routing_type}-{destination}`
  * example `env-spoke-0-private-googleapis`

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

`custom.{base}{custom constraint}{00}`

Example:

`custom.exampleDoNotAllowPublicIPsonGCEVMs00`

[Google Cloud Organization Policy Custom Constraints Documentation](https://cloud.google.com/resource-manager/docs/organization-policy/creating-managing-custom-constraints#custom_constraints)

Google Cloud Org Policy Custom Constraints should be following Google Cloud best practices by following these naming standards:

- [ ] lowercase
- [ ] camelCase
- [ ] no spaces

Google Cloud Org Policy Custom Constraints naming is:

- [ ] _only_ viewable outside the Google Cloud Org
- [ ] _is_ globally unique
- [ ] _is_ burnable

## IAM Custom & Service Roles

Spec:

`{prefix}-{compliance_regime}-{environment}-{role_name}-{rw ro}`

`{prefix}-{environment}-{function}-{index}@{project_id}.iam.gserviceaccount.com`

Example:

`edtl-il5-prod-resman-0r-ro`

`edtl-prod-bootstrap-0r@edtl-il5-prod-iac-core.iam.gserviceaccount.com`

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

`{tenant}-{environment}-{role}-({suffix})`

Example:

`macom-env-iac`

`macom-env-iac-outputs`

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

`{tenant}-{environment}-{appname}-{role}-{000-999}`

Example:

`macom-env-appname-server-001`

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
