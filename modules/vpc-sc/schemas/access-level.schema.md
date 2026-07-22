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

# VPC-SC access level

<!-- markdownlint-disable MD036 -->

## Properties

*additional properties: false*

- **combining_function**: *string*
- **conditions**: *array*
  - items: *object*
    <br>*additional properties: false*
    - **device_policy**: *object*
      <br>*additional properties: false*
      - **allowed_device_management_levels**: *array*
        - items: *string*
      - **allowed_encryption_statuses**: *array*
        - items: *string*
      - ⁺**require_admin_approval**: *boolean*
      - ⁺**require_corp_owned**: *boolean*
      - **require_screen_lock**: *boolean*
      - **os_constraints**: *array*
        - items: *object*
          <br>*additional properties: false*
          - **os_type**: *string*
          - **minimum_version**: *string*
          - **require_verified_chrome_os**: *boolean*
    - **ip_subnetworks**: *array*
      - items: *string*
    - **members**: *array*
      - items: *string*
    - **negate**: *boolean*
    - **regions**: *array*
      - items: *string*
    - **required_access_levels**: *array*
      - items: *string*
    - **vpc_subnets**: *object*
      <br>*additional properties: false*
      - **`^//compute.googleapis.com/projects/[^/]+/global/networks/[^/]+$`**: *array*
        - items: *string*

## Definitions


