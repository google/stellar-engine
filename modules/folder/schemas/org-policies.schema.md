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

# Organization Policies

<!-- markdownlint-disable MD036 -->

## Properties

*additional properties: false*

- **`^[a-z-]+[a-zA-Z0-9\.]+$`**: *object*
  <br>*additional properties: false*
  - **inherit_from_parent**: *boolean*
  - **reset**: *boolean*
  - **rules**: *array*
    - items: *object*
      <br>*additional properties: false*
      - **allow**: *reference([allow-deny](#refs-allow-deny))*
      - **deny**: *reference([allow-deny](#refs-allow-deny))*
      - **enforce**: *boolean*
      - **condition**: *object*
        <br>*additional properties: false*
        - **description**: *string*
        - **expression**: *string*
        - **location**: *string*
        - **title**: *string*
      - **parameters**: *string*

## Definitions

- **allow-deny**<a name="refs-allow-deny"></a>: *object*
  <br>*additional properties: false*
  - **all**: *boolean*
  - **values**: *array*
    - items: *string*
