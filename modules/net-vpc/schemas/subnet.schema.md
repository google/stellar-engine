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

# Subnet

<!-- markdownlint-disable MD036 -->

## Properties

*additional properties: false*

- **active**: *boolean*
- **description**: *string*
- **enable_private_access**: *boolean*
- **allow_subnet_cidr_routes_overlap**: *boolean*
- **flow_logs_config**: *object*
  <br>*additional properties: false*
  - **aggregation_interval**: *string*
  - **filter_expression**: *string*
  - **flow_sampling**: *number*
  - **metadata**: *string*
  - **metadata_fields**: *array*
    - items: *string*
- **global**: *boolean*
- ⁺**ip_cidr_range**: *string*
- **ipv6**: *object*
  <br>*additional properties: false*
  - **access_type**: *string*
  - **ipv6_only**: *boolean*
- **ip_collection**: *string*
- **name**: *string*
- ⁺**region**: *string*
- **psc**: *boolean*
- **proxy_only**: *boolean*
- **secondary_ip_ranges**: *object*
  *additional properties: String*
- **iam**: *reference([iam](#refs-iam))*
- **iam_bindings**: *reference([iam_bindings](#refs-iam_bindings))*
- **iam_bindings_additive**: *reference([iam_bindings_additive](#refs-iam_bindings_additive))*

## Definitions

- **iam**<a name="refs-iam"></a>: *object*
  <br>*additional properties: false*
  - **`^roles/`**: *array*
    - items: *string*
      <br>*pattern: ^(?:domain:|group:|serviceAccount:|user:|principal:|principalSet:|ro|rw)*
- **iam_bindings**<a name="refs-iam_bindings"></a>: *object*
  <br>*additional properties: false*
  - **`^[a-z0-9_-]+$`**: *object*
    <br>*additional properties: false*
    - **members**: *array*
      - items: *string*
        <br>*pattern: ^(?:domain:|group:|serviceAccount:|user:|principal:|principalSet:|ro|rw)*
    - **role**: *string*
      <br>*pattern: ^roles/*
    - **condition**: *object*
      <br>*additional properties: false*
      - ⁺**expression**: *string*
      - ⁺**title**: *string*
      - **description**: *string*
- **iam_bindings_additive**<a name="refs-iam_bindings_additive"></a>: *object*
  <br>*additional properties: false*
  - **`^[a-z0-9_-]+$`**: *object*
    <br>*additional properties: false*
    - **member**: *string*
      <br>*pattern: ^(?:domain:|group:|serviceAccount:|user:|principal:|principalSet:|ro|rw)*
    - **role**: *string*
      <br>*pattern: ^roles/*
    - **condition**: *object*
      <br>*additional properties: false*
      - ⁺**expression**: *string*
      - ⁺**title**: *string*
      - **description**: *string*
