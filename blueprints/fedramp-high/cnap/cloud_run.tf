# These Cloud Run services are meant to represent real applications deployed behind the CNAP
# This isn't mean to imply that *only* Cloud Run applications can be hosted behind the CNAP

resource "google_cloud_run_v2_service" "cloud_run_apps" {
  project  = data.google_project.project.project_id
  for_each = local.cloud_runs
  name     = "${var.prefix}-${each.key}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    containers {
      image = each.value.cloud_run_image
    }
  }
  binary_authorization {
    use_default = true
  }
  depends_on = [google_project_service.services]
}