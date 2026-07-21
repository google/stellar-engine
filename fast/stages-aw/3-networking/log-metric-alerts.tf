# CIS Compliance Benchmark 2.4
# CIS Compliance Benchmark 2.5
# CIS Compliance Benchmark 2.6
# CIS Compliance Benchmark 2.7
# CIS Compliance Benchmark 2.8
# CIS Compliance Benchmark 2.9
# CIS Compliance Benchmark 2.10
# CIS Compliance Benchmark 2.11

module "vdss_log_metrics" {
  source  = "../../../modules/cis-log-metrics"
  project = module.vdss-host-project.id
}

module "spoke_log_metrics" {
  source = "../../../modules/cis-log-metrics"

  for_each = module.env-spoke-projects
  project  = module.env-spoke-projects[each.key].id
}

# Alerts require log-metrics to be configure
resource "time_sleep" "networking_wait_10_seconds" {
  depends_on      = [module.vdss_log_metrics, module.spoke_log_metrics]
  create_duration = "10s"
}

module "vdss_log_alerts" {
  source = "../../../modules/cis-log-alerts"

  project            = module.vdss-host-project.id
  combiner           = "OR"
  duration           = "60s"
  comparison         = "COMPARISON_GT"
  alignment_period   = "60s"
  per_series_aligner = "ALIGN_RATE"
  alert_email        = var.alert_email

  depends_on = [time_sleep.networking_wait_10_seconds]
}

module "spoke_log_alerts" {
  source = "../../../modules/cis-log-alerts"

  for_each = module.env-spoke-projects
  project  = module.env-spoke-projects[each.key].id

  combiner           = "OR"
  duration           = "60s"
  comparison         = "COMPARISON_GT"
  alignment_period   = "60s"
  per_series_aligner = "ALIGN_RATE"
  alert_email        = var.alert_email

  depends_on = [time_sleep.networking_wait_10_seconds]
}
