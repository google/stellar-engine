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

# ACAS Deployment

This directory contains the production deployment blueprints for the **ACAS infrastructure**. The deployments are split by functional service, as they have different scaling patterns and lifecycles.

> **Run `acas/image-factory` first** to build the Golden Images before applying any of these blueprints.

<!-- BEGIN TOC -->
- [Directories](#directories)
- [Deployment Strategy](#deployment-strategy)
<!-- END TOC -->

## Directories

| Directory | Purpose |
|---|---|
| [`scanner/`](./scanner/README.md) | Deploys one or more **ACAS Nessus Scanners**. These are typically replaced frequently as new scanner images are built, and can be scaled out across multiple regions or projects. |
| [`securitycenter/`](./securitycenter/README.md) | Deploys the **ACAS SecurityCenter (Tenable.sc)**. This is a long-lived, singleton management plane instance. |

## Deployment Strategy

By splitting the deployments:
1. You can update and replace Nessus Scanners with zero risk to the SecurityCenter state or data disks.
2. If your organization uses an external SecurityCenter (e.g., in AWS or Azure), you only need to run the `scanner/` blueprint.
3. You can deploy multiple copies of the `scanner/` blueprint into different VPCs or regions while managing a single `securitycenter/`.

<!-- BEGIN TFDOC -->
<!-- END TFDOC -->
