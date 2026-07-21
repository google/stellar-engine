# Google Compute Shielded VM Module
module "bastion-vm" {
  source               = "../../../modules/compute-vm"
  project_id           = module.vdss-host-project.project_id
  zone                 = "${var.regions["primary"]}-c"
  name                 = "management-bastion"
  confidential_compute = true # CIS Compliance Benchmark 4.11 - Must use compliant instance and image types
  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  tags          = ["bastion"]
  instance_type = "n2d-highcpu-2"
  network_interfaces = [{
    network = module.mgmt-vpc.self_link
    subnetwork = try(
      module.mgmt-vpc.subnet_self_links["${var.regions["primary"]}/mgmt-default"], null
    )
  }]
  encryption = {
    kms_key_self_link = module.kms[var.regions.primary].keys.default.id
  }
  attached_disks = [
    {
      auto_delete = true
      size        = 10
      name        = "data-disk"
      initialize_params = {
        image = "projects/cos-cloud/global/images/family/cos-stable"
      }
      kms_key_self_link = module.kms[var.regions.primary].keys.default.id
    }
  ]

  boot_disk = {
    initialize_params = {
      image = "projects/cos-cloud/global/images/family/cos-stable"
    }
  }

  service_account = {
    email = module.ngfw-service-account.email
  }

  metadata = {
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
  }

  depends_on = [module.kms]
}