/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

project_id    = "tf-playground-svpc-gce"
zone          = "europe-west8-b"
name          = "test-sa"
instance_type = "e2-small"
network_interfaces = [{
  network    = "https://www.googleapis.com/compute/v1/projects/ldj-dev-net-spoke-0/global/networks/dev-spoke-0"
  subnetwork = "https://www.googleapis.com/compute/v1/projects/ldj-dev-net-spoke-0/regions/europe-west8/subnetworks/gce"
}]