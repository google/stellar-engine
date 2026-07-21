module "psc" {
  source                       = "../../../modules/private-service-connect"
  project_id                   = var.main_project_id
  service_directory_region     = var.region
  private_service_connect_name = var.ip_name
  forwarding_rule_name         = var.psc_name
  network_self_link            = var.network_name
  private_service_connect_ip   = var.address
  forwarding_rule_target       = var.service
  dns_code                     = var.dns_code
  psc_global_access            = false
}