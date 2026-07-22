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

resource "google_storage_bucket_object" "tenant_outputs" {
  bucket = var.automation.outputs_bucket
  name   = "stage_3_tenant_outputs.json"
  content = jsonencode({
    edge_group_id = google_network_connectivity_group.groups["edge"].id
    hub_id        = google_network_connectivity_hub.main.id
    ilb_ips = {
      transit = module.ilb-nva-tenant-transit[var.regions.primary].forwarding_rule_addresses[""]
    }
  })
}
