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

# Instance Configuration via `cloud-config`

This set of modules creates specialized [cloud-config](https://cloud.google.com/container-optimized-os/docs/how-to/run-container-instance#starting_a_docker_container_via_cloud-config) configurations, which are designed for use with [Container Optimized OS](https://cloud.google.com/container-optimized-os/docs) (the onprem module is the only exception) but can also be used as a basis for other image types or cloud providers.

These modules are designed for several use cases:

- to quickly prototype specialized services (eg MySQL access or HTTP serving) for prototyping infrastructure
- to emulate production services for performance testing
- to easily add glue components for services like DNS (eg to work around inbound/outbound forwarding limitations)
- to implement cloud-native production deployments that leverage cloud-init for configuration management, without the need of a separate tool

## Available modules

- [Bindplane](./bindplane)
- [CoreDNS](./coredns)
- [MySQL](./mysql)
- [Nginx](./nginx)
- On-prem in Docker (*needs fixing*)

## Using the modules

All modules are designed to be as lightweight as possible, so that specialized modules like [compute-vm](../compute-vm) can be leveraged to manage instances or instance templates, and to allow simple forking to create custom derivatives.

To use the modules with instances or instance templates, simply set use their `cloud_config` output for the `user-data` metadata. When updating the metadata after a variable change remember to manually restart the instances that use a module's output, or the changes won't effect the running system.

## TODO

- [ ] convert all `xxx_config` variables to use file content instead of path
