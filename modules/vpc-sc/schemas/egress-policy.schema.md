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

# VPC-SC egress policy

<!-- markdownlint-disable MD036 -->

## Properties

*additional properties: false*

- **title**: *string*
- ⁺**from**: *object*
  <br>*additional properties: false*
  - **access_levels**: *array*
    - items: *string*
  - **identity_type**: *string*
    <br>*enum: ['IDENTITY_TYPE_UNSPECIFIED', 'ANY_IDENTITY', 'ANY_USER_ACCOUNT', 'ANY_SERVICE_ACCOUNT', '']*
  - **identities**: *array*
    - items: *string*
      <br>*pattern: ^(?:serviceAccount:|user:|group:|principal:|\$identity_sets:)*
  - **resources**: *array*
    - items: *string*
- ⁺**to**: *object*
  <br>*additional properties: false*
  - **external_resources**: *array*
    - items: *string*
  - **operations**: *array*
    - items: *object*
      <br>*additional properties: false*
      - **method_selectors**: *array*
        - items: *string*
      - **permission_selectors**: *array*
        - items: *string*
      - ⁺**service_name**: *string*
  - **resources**: *array*
    - items: *string*
  - **roles**: *array*
    - items: *string*

## Definitions


