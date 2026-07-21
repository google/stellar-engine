output "gcs_iac_bucket" {
  description = "IaC buckets."
  value = {
    for key, gcs in module.tenant-self-iac-gcs-states : key => {
      id   = gcs.bucket.id
      name = gcs.bucket.name
    }
  }
}

output "projects" {
  description = "Tenant projects."
  value = {
    for key, prj in module.tenant-projects : key => {
      id   = prj.id
      name = prj.name
    }
  }
}

output "service_accounts_automation" {
  description = "Service accounts for automation."
  value = {
    for key, sa in module.tenant-self-iac-sa : key => {
      email = sa.email
      id    = sa.id
      name  = sa.name
    }
  }
}

output "service_accounts_cicd" {
  description = "Service accounts for CICD."
  value = {
    for key, sa in module.automation-tf-cicd-sa : key => {
      email = sa.email
      id    = sa.id
      name  = sa.name
    }
  }
}

output "vpc_networks" {
  description = "Tenant VPC network."
  value = {
    for key, vpc in module.tenant-vpc : key => {
      id   = vpc.id
      name = vpc.name
      subnets = {
        for skey, subnet in vpc.subnets : skey => {
          id   = subnet.id
          name = subnet.name
        }
      }
    }
  }
}

output "workload_identity_provider" {
  description = "Name of Workload Identity GitLab provider."
  value = {
    for key, prv in google_iam_workload_identity_pool_provider.default : key => {
      id   = prv.id
      name = prv.name
    }
  }
}