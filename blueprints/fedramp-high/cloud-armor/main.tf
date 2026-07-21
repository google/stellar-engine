locals {
  file = yamldecode(file(var.rules_file))

  policies = {
    for policy_name, policy_data in local.file :
    policy_name => {
      description = try(policy_data.description, null)
    }
  }

  rules = flatten([
    for policy_name, data in local.file : [
      for i, rule in data.rules :
      merge(
        rule,
        {
          policy   = policy_name,
          region   = var.region,
          priority = i + 1000
        }
      )
    ]
  ])
}

resource "google_compute_region_security_policy" "policy" {
  provider = google-beta
  for_each = local.policies

  name        = each.key
  description = each.value.description
  type        = "CLOUD_ARMOR"
}

resource "google_compute_region_security_policy_rule" "policy_rule" {
  provider   = google-beta
  for_each   = { for i, rule in local.rules : i => rule }
  depends_on = [google_compute_region_security_policy.policy]

  security_policy = each.value.policy
  region          = each.value.region
  priority        = each.value.priority
  action          = try(each.value.action, "allow")

  preview     = try(each.value.preview, null)
  description = try(each.value.description, null)

  match {
    dynamic "expr" {
      for_each = try(each.value.expression, null) != null ? [1] : []
      content {
        expression = "evaluatePreconfiguredWaf('${each.value.expression}')"
      }
    }

    //only create a versioned_expr and config block if there isn't an expr block
    versioned_expr = try(each.value.expression, null) != null ? null : "SRC_IPS_V1"
    dynamic "config" {
      for_each = try(each.value.expression, null) != null ? [] : [1]
      content {
        src_ip_ranges = ["*"]
      }
    }
  }

  dynamic "rate_limit_options" {
    for_each = try(each.value.rate_limit_options, null) != null ? [1] : []
    content {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = ""
      enforce_on_key_configs {
        enforce_on_key_type = "IP"
      }
      dynamic "rate_limit_threshold" {
        for_each = try(each.value.rate_limit_options.rate_limit_threshold, null) != null ? [1] : []
        content {
          count        = try(each.value.rate_limit_options.rate_limit_threshold.count, null)
          interval_sec = try(each.value.rate_limit_options.rate_limit_threshold.interval_sec, null)
        }
      }
      dynamic "ban_threshold" {
        for_each = try(each.value.rate_limit_options.ban_threshold, null) != null ? [1] : []
        content {
          count        = try(each.value.rate_limit_options.ban_threshold.count, null)
          interval_sec = try(each.value.rate_limit_options.ban_threshold.interval_sec, null)
        }
      }
      ban_duration_sec = try(each.value.rate_limit_options.ban_duration_sec, null)
    }
  }
}