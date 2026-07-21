
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
