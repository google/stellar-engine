output "forwarding_zones" {
  description = "Map of forwarding zone names to their domains."
  value = {
    for k, v in module.dns-forwarding-zones : k => {
      name   = v.name
      domain = v.domain
    }
  }
}

output "peering_zones" {
  description = "Map of peering zone names for the landing VPC."
  value = {
    for k, v in module.dns-peering-landing : k => {
      name   = v.name
      domain = v.domain
    }
  }
}
