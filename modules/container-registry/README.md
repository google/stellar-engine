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

# Google Cloud Container Registry Module

This module simplifies the creation of GCS buckets used by Google Container Registry.

## Example

```hcl
module "container_registry" {
  source     = "./fabric/modules/container-registry"
  project_id = "myproject"
  location   = "EU"
  iam = {
    "roles/storage.admin" = ["group:cicd@example.com"]
  }
}
# tftest modules=1 resources=2 inventory=simple.yaml
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [location](variables.tf#L23) | Registry location. Can be US, EU, ASIA or empty. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L28) | Registry project id. | <code>string</code> | ✓ |  |
| [iam](variables.tf#L17) | IAM bindings for topic in {ROLE => [MEMBERS]} format. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L17) | Fully qualified id of the registry bucket. |  |
<!-- END TFDOC -->
