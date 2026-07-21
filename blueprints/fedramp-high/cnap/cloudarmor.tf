locals {
  waf = yamldecode(file("data/cloudarmor.yaml"))
}

resource "google_compute_region_security_policy" "default" {
  provider = google-beta
  project  = data.google_project.project.number

  region      = var.region
  name        = "cloud-armor-policy"
  description = "Preconfigured WAF Rules"
  type        = "CLOUD_ARMOR"
}

resource "google_compute_region_security_policy_rule" "policy_rules" {
  for_each        = local.waf.basic_rules
  security_policy = google_compute_region_security_policy.default.name
  provider        = google-beta
  region          = var.region
  project         = data.google_project.project.number
  preview         = false
  action          = "deny(403)"
  priority        = index(keys(local.waf.basic_rules), each.key) + 1000
  description     = "Block ${each.key} attack"
  match {
    expr {
      # Assuming 'rule.value' contains something like 'sqli-v33-stable', we construct the expression using evaluatePreconfiguredWaf(value).
      expression = "evaluatePreconfiguredWaf('${each.value.expression}')"
    }
  }
}