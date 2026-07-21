# Cloud Build
Cloud Build is a service that executes your builds on Google Cloud.

Cloud Build can import source code from a variety of repositories or cloud storage spaces, execute a build to your specifications, and produce artifacts such as Docker containers or Java archives.

You can also use Cloud Build to help protect your software supply chain. Cloud Build features meet the requirements of Supply chain Levels for Software Artifacts (SLSA) level 3. 

## Blueprint
This blueprint provides the base requirements to deploy pipelines in Cloud Build.  This focuses on the use case of automating the process of running a terraform pipeline to deploy infrastructure within a target environment (example: provision a cloud compute engine in a tenant's test project).

## Running Terraform Automation Pipeline
The environments folder contains the pipeline yaml files for running plans and full apply pipelines. The environments/test folder is an example utilizing cloud build to deploy a storage bucket in the FRH -> Project [tenant] Test -> XXX-test-[tenant]-main-0 project.
The environments folder can be moved out of the blueprints folder to contain any collection of blueprints or custom terraform configuration that should be included in the pipeline.

For more details on running a pipeline, see the [README](./environments/test/README.md)

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L26) | Core project ID. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L41) | Main project ID. | <code>string</code> | ✓ |  |
| [prefix](variables.tf#L46) | Prefix used for resources that need unique names. Use 7 characters or less. | <code>string</code> | ✓ |  |
| [services](variables.tf#L55) | Cloud services to enable within the project. | <code>set&#40;string&#41;</code> | ✓ |  |
| [cloud_build_core_roles](variables.tf#L17) | A list of roles for the Cloud Build SA, needed to run the build process. | <code>list&#40;string&#41;</code> |  | <code title="&#91;&#10;  &#34;roles&#47;cloudbuild.builds.builder&#34;,&#10;  &#34;roles&#47;storage.admin&#34;&#10;&#93;">&#91;&#8230;&#93;</code> |
| [locations](variables.tf#L31) | Optional locations for GCS, BigQuery, and logging buckets created here. | <code title="object&#40;&#123;&#10;  gcs &#61; optional&#40;string, &#34;US&#34;&#41;&#10;  kms &#61; optional&#40;string, &#34;US&#34;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [terraform_apply_roles](variables.tf#L60) | A list of project-level admin roles for the service account to run Terraform apply. | <code>list&#40;string&#41;</code> |  | <code title="&#91;&#10;  &#34;roles&#47;dns.admin&#34;,&#10;  &#34;roles&#47;cloudkms.admin&#34;,&#10;  &#34;roles&#47;compute.admin&#34;,&#10;  &#34;roles&#47;compute.networkAdmin&#34;,&#10;  &#34;roles&#47;container.admin&#34;,&#10;  &#34;roles&#47;gkehub.admin&#34;,&#10;  &#34;roles&#47;storage.admin&#34;&#10;&#93;">&#91;&#8230;&#93;</code> |
<!-- END TFDOC -->
