locals {
  cr_backends = { for key, _ in try(local.cloud_runs, {}) : key =>
    {
      backends = [
        { backend = "neg-${key}" }
      ]
      id            = ""
      health_checks = []
      port_name     = ""
      iap_config = {
        oauth2_client_id     = google_iap_client.project_client.client_id
        oauth2_client_secret = google_iap_client.project_client.secret
      }
      security_policy = google_compute_region_security_policy.default.self_link
    }
  }
  vm_backends = { for key, _ in try(local.vms, {}) : key =>
    {
      backends = [{
        backend = module.cos-mig[key].group_manager.instance_group
      }]
      health_checks = [google_compute_region_health_check.http-region-health-check[key].self_link, ]
      protocol      = "HTTP"
      iap_config = {
        oauth2_client_id     = google_iap_client.project_client.client_id
        oauth2_client_secret = google_iap_client.project_client.secret
      }
      security_policy = google_compute_region_security_policy.default.self_link
    }
  }

  backends_wo_default = merge(local.cr_backends, local.vm_backends)
  default             = { (var.default_backend) = local.backends_wo_default[var.default_backend] }
  backends            = merge(local.backends_wo_default, local.default)

  host_rules = [for key, values in local.apps : {
    hosts        = ["${values.subdomain}.${var.domain}"],
    path_matcher = "path-matcher-${key}"
  }]
  lb_name       = "${var.prefix}-cloud-native-access-point"
  service_names = { for app, _ in local.apps : app => "https://www.googleapis.com/compute/v1/projects/${var.main_project_id}/regions/${var.region}/backendServices/${local.lb_name}-${app}" }

  path_matchers = merge(
    { for app, values in try(local.cloud_runs, {}) : "path-matcher-${app}" => {
      paths           = ["/*"],
      default_service = local.service_names[app]
      }
    },
    { for mig, values in try(local.vms, {}) : "path-matcher-${mig}" => {
      paths           = ["/*"],
      default_service = local.service_names[mig]
      }
    }
  )
}
resource "google_compute_shared_vpc_host_project" "host" {
  project = var.network_project_id
}

resource "tls_private_key" "default" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

data "google_compute_network" "network" {
  name    = var.network_name
  project = try(var.net_project, var.main_project_id)
}
resource "tls_self_signed_cert" "default" {
  provider        = tls
  private_key_pem = tls_private_key.default.private_key_pem
  subject {
    common_name  = var.domain
    organization = "ACME Examples, Inc"
  }
  dns_names = concat(
    [for app, values in try(local.apps, {}) : "${values.subdomain}.${var.domain}"],
    [for mig, values in try(local.vms, {}) : " ${values.subdomain}.${var.domain}"]
  )
  validity_period_hours = 720
  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}

resource "google_compute_region_ssl_certificate" "default" {
  region  = var.region
  project = var.main_project_id

  name_prefix = "${var.prefix}-cert-"
  description = "Self-signed demo cert"
  certificate = tls_self_signed_cert.default.cert_pem
  private_key = tls_private_key.default.private_key_pem

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_address" "cnap-ext-ip" {
  name         = "cnap-ip"
  region       = var.region
  address_type = "EXTERNAL"
  network_tier = "STANDARD"
}

module "cnap-0-redirect" {
  source     = "../../../modules/net-lb-app-ext-regional/"
  project_id = var.network_project_id
  name       = "${var.prefix}-cloud-native-access-point-redirect"
  vpc        = data.google_compute_network.network.self_link
  region     = var.region
  address = (
    google_compute_address.cnap-ext-ip.id
  )
  health_check_configs = {}
  urlmap_config = {
    description = "URL redirect for ${var.prefix}-cloud-native-access-point."
    default_url_redirect = {
      https         = true
      response_code = "MOVED_PERMANENTLY_DEFAULT"
    }
  }
  depends_on = [google_org_policy_policy.allow_external_lb]
}

module "cnap-0" {
  source     = "../../../modules/net-lb-app-ext-regional/"
  project_id = var.main_project_id
  name       = local.lb_name
  vpc        = data.google_compute_network.network.self_link
  region     = var.region
  address = (
    google_compute_address.cnap-ext-ip.id
  )
  backend_service_configs = local.backends
  # with a single serverless NEG the implied default health check is not needed
  health_check_configs = {}
  neg_configs = { for key, _ in local.cloud_runs : "neg-${key}" =>
    {
      project = var.main_project_id
      cloudrun = {
        region = var.region
        target_service = {
          name = google_cloud_run_v2_service.cloud_run_apps[key].name
        }
      }
  } }

  urlmap_config = {
    default_service = local.service_names[var.default_backend]
    host_rules      = local.host_rules
    path_matchers   = local.path_matchers

  }
  protocol = "HTTPS"
  ssl_certificates = {
    certificate_ids = [google_compute_region_ssl_certificate.default.id]
  }

  depends_on = [google_cloud_run_v2_service.cloud_run_apps] # google_org_policy_policy.allow_external_lb]
}
