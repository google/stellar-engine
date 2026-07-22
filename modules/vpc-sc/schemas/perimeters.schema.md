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

# perimeters

<!-- markdownlint-disable MD036 -->

## Properties

*additional properties: false*

- **description**: *string*
- **ignore_resource_changes**: *boolean*
- **spec**: *object*
  <br>*additional properties: false*
  - **access_levels**: *array*
    - items: *string*
  - **egress_policies**: *array*
    - items: *string*
  - **ingress_policies**: *array*
    - items: *string*
  - **restricted_services**: *array*
    - items: *string*
  - **resources**: *array*
    - items: *string*
  - **vpc_accessible_services**: *reference([VpcAccessibleServices](#refs-VpcAccessibleServices))*
- **status**: *object*
  <br>*additional properties: false*
  - **access_levels**: *array*
    - items: *string*
  - **egress_policies**: *array*
    - items: *string*
  - **ingress_policies**: *array*
    - items: *string*
  - **resources**: *array*
    - items: *string*
  - **restricted_services**: *array*
    - items: *string*
  - **vpc_accessible_services**: *reference([VpcAccessibleServices](#refs-VpcAccessibleServices))*
- **title**: *string*
- **use_explicit_dry_run_spec**: *boolean*

## Definitions

- **VpcAccessibleServices**<a name="refs-VpcAccessibleServices"></a>: *object*
  <br>*additional properties: false*
  - ⁺**allowed_services**: *array*
    - items: *string*
  - **enable_restriction**: *boolean*
