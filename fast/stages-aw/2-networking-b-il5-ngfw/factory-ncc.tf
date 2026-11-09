/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

# tfdoc:file:description NCC hubs, groups, and spokes factory.

locals {
  _ncc_path = coalesce(
    var.factories_config.ncc_hubs,
    "${var.factories_config.data_dir}/ncc-hubs"
  )
  _ncc_files = try(fileset(local._ncc_path, "**/*.yaml"), [])
  _ncc_yaml_raw = [
    for f in local._ncc_files : merge(
      { name = trimsuffix(basename(f), ".yaml") },
      try(
        { for k, v in yamldecode(file("${local._ncc_path}/${f}")) : k => v },
        {}
      )
    )
  ]
  _ncc_enabled = length(local._ncc_yaml_raw) > 0 || length(var.ncc_hubs) > 0

  _ncc_yaml_configs = {
    for v in local._ncc_yaml_raw : tostring(v.name) => {
      project_id = (
        try(v.project_id, null) != null
        ? tostring(v.project_id)
        : tostring(null)
      )
      description = (
        try(v.description, null) != null
        ? tostring(v.description)
        : "Terraform-managed."
      )
      export_psc = tobool(
        try(v.export_psc, null) != null ? v.export_psc : true
      )
      policy_mode = (
        try(v.policy_mode, null) != null
        ? tostring(v.policy_mode)
        : tostring(null)
      )
      preset_topology = (
        try(v.preset_topology, null) != null
        ? tostring(v.preset_topology)
        : tostring(null)
      )
      labels = tomap(try({
        for lk, lv in v.labels : tostring(lk) => tostring(lv)
      }, {}))
      groups = tomap(try({
        for gk, gv in v.groups : tostring(gk) => {
          description = (
            try(gv.description, null) != null
            ? tostring(gv.description)
            : "Terraform-managed."
          )
          labels = tomap(try({
            for lk, lv in gv.labels : tostring(lk) => tostring(lv)
          }, {}))
          auto_accept = tolist(try([
            for p in gv.auto_accept : tostring(p)
          ], []))
        }
      }, {}))
      spokes = {
        vpcs = tomap(try({
          for sk, sv in v.spokes.vpcs : tostring(sk) => {
            vpc = (
              try(sv.vpc, null) != null ? tostring(sv.vpc) : tostring(null)
            )
            name = (
              try(sv.name, null) != null ? tostring(sv.name) : tostring(null)
            )
            project_id = (
              try(sv.project_id, null) != null
              ? tostring(sv.project_id)
              : tostring(null)
            )
            group = (
              try(sv.group, null) != null ? tostring(sv.group) : tostring(null)
            )
            description = (
              try(sv.description, null) != null
              ? tostring(sv.description)
              : "Terraform-managed."
            )
            labels = tomap(try({
              for lk, lv in sv.labels : tostring(lk) => tostring(lv)
            }, {}))
            exclude_export_ranges = (
              try(sv.exclude_export_ranges, null) != null
              ? tolist([for r in sv.exclude_export_ranges : tostring(r)])
              : tolist(null)
            )
            include_export_ranges = (
              try(sv.include_export_ranges, null) != null
              ? tolist([for r in sv.include_export_ranges : tostring(r)])
              : tolist(null)
            )
          }
        }, {}))
        tunnels = tomap(try({
          for sk, sv in v.spokes.tunnels : tostring(sk) => {
            uris = tolist([for u in sv.uris : tostring(u)])
            name = (
              try(sv.name, null) != null ? tostring(sv.name) : tostring(null)
            )
            location = (
              try(sv.location, null) != null
              ? tostring(sv.location)
              : tostring(null)
            )
            project_id = (
              try(sv.project_id, null) != null
              ? tostring(sv.project_id)
              : tostring(null)
            )
            group = (
              try(sv.group, null) != null ? tostring(sv.group) : tostring(null)
            )
            description = (
              try(sv.description, null) != null
              ? tostring(sv.description)
              : "Terraform-managed."
            )
            labels = tomap(try({
              for lk, lv in sv.labels : tostring(lk) => tostring(lv)
            }, {}))
            site_to_site_data_transfer = tobool(
              try(sv.site_to_site_data_transfer, null) != null
              ? sv.site_to_site_data_transfer
              : true
            )
            include_import_ranges = (
              try(sv.include_import_ranges, null) != null
              ? tolist([for r in sv.include_import_ranges : tostring(r)])
              : tolist(["ALL_IPV4_RANGES"])
            )
          }
        }, {}))
        vlan_attachments = tomap(try({
          for sk, sv in v.spokes.vlan_attachments : tostring(sk) => {
            uris = tolist([for u in sv.uris : tostring(u)])
            name = (
              try(sv.name, null) != null ? tostring(sv.name) : tostring(null)
            )
            location = (
              try(sv.location, null) != null
              ? tostring(sv.location)
              : tostring(null)
            )
            project_id = (
              try(sv.project_id, null) != null
              ? tostring(sv.project_id)
              : tostring(null)
            )
            group = (
              try(sv.group, null) != null ? tostring(sv.group) : tostring(null)
            )
            description = (
              try(sv.description, null) != null
              ? tostring(sv.description)
              : "Terraform-managed."
            )
            labels = tomap(try({
              for lk, lv in sv.labels : tostring(lk) => tostring(lv)
            }, {}))
            site_to_site_data_transfer = tobool(
              try(sv.site_to_site_data_transfer, null) != null
              ? sv.site_to_site_data_transfer
              : true
            )
            include_import_ranges = (
              try(sv.include_import_ranges, null) != null
              ? tolist([for r in sv.include_import_ranges : tostring(r)])
              : tolist(["ALL_IPV4_RANGES"])
            )
          }
        }, {}))
        router_appliances = tomap(try({
          for sk, sv in v.spokes.router_appliances : tostring(sk) => {
            instances = tolist([
              for inst in sv.instances : {
                ip_address      = tostring(inst.ip_address)
                virtual_machine = tostring(inst.virtual_machine)
              }
            ])
            name = (
              try(sv.name, null) != null ? tostring(sv.name) : tostring(null)
            )
            location = (
              try(sv.location, null) != null
              ? tostring(sv.location)
              : tostring(null)
            )
            project_id = (
              try(sv.project_id, null) != null
              ? tostring(sv.project_id)
              : tostring(null)
            )
            group = (
              try(sv.group, null) != null ? tostring(sv.group) : tostring(null)
            )
            description = (
              try(sv.description, null) != null
              ? tostring(sv.description)
              : "Terraform-managed."
            )
            labels = tomap(try({
              for lk, lv in sv.labels : tostring(lk) => tostring(lv)
            }, {}))
            site_to_site_data_transfer = tobool(
              try(sv.site_to_site_data_transfer, null) != null
              ? sv.site_to_site_data_transfer
              : true
            )
            include_import_ranges = (
              try(sv.include_import_ranges, null) != null
              ? tolist([for r in sv.include_import_ranges : tostring(r)])
              : tolist(["ALL_IPV4_RANGES"])
            )
          }
        }, {}))
      }
    }
  }

  _ncc_configs = merge(local._ncc_yaml_configs, var.ncc_hubs)

  # Stage 2 context lookup maps for symbolic $namespace:key references.
  _ctx_locations = {
    for k, v in var.regions : k => v
  }
  _ctx_projects = merge(
    {
      for k, v in var.tenant_accounts : k => v.main_project
    },
    {
      for k, v in module.env-spoke-projects : k => v.project_id
    },
    {
      for k, v in module.env-spoke-projects : lower(k) => v.project_id
    },
    {
      for k, v in module.env-spoke-projects :
      "${lower(k)}-net-host" => v.project_id
    },
    {
      landing       = module.vdss-host-project.project_id
      net-vdss-host = module.vdss-host-project.project_id
      vdss          = module.vdss-host-project.project_id
      vdss-host     = module.vdss-host-project.project_id
    }
  )
  _ctx_vpcs = merge(
    local._vdss_vpcs,
    { for k, v in module.env-spoke-vpc : k => v.self_link },
    { for k, v in module.env-spoke-vpc : lower(k) => v.self_link }
  )
  _ctx_vpc_projects = merge(
    {
      for k, _ in local._vdss_vpcs : k => module.vdss-host-project.project_id
    },
    { for k, v in module.env-spoke-projects : k => v.project_id },
    { for k, v in module.env-spoke-projects : lower(k) => v.project_id }
  )

  # Separate hub and group lookup maps avoid circular dependencies.
  _ctx_ncc_hubs = {
    for k, v in google_network_connectivity_hub.default : k => v.id
  }
  _ctx_ncc_groups = {
    for k, v in google_network_connectivity_group.default : k => v.id
  }

  _ncc_hub_projects = {
    for k, v in local._ncc_configs : k => lookup(
      local._ctx_projects,
      trimprefix(
        coalesce(v.project_id, "$project_ids:vdss-host"),
        "$project_ids:"
      ),
      coalesce(v.project_id, module.vdss-host-project.project_id)
    )
  }

  ncc_hubs = {
    for k, v in local._ncc_configs : k => {
      project_id  = local._ncc_hub_projects[k]
      description = v.description
      export_psc  = v.export_psc
      policy_mode = v.policy_mode
      preset_topology = (
        v.policy_mode == "CUSTOM"
        ? v.preset_topology
        : coalesce(v.preset_topology, "MESH")
      )
      labels = v.labels
    }
  }

  ncc_groups = merge([
    for hk, hv in local._ncc_configs : {
      for gk, gv in hv.groups : "${hk}/${gk}" => {
        name        = gk
        project_id  = local._ncc_hub_projects[hk]
        hub         = hk
        description = gv.description
        labels      = gv.labels
        auto_accept = distinct([
          for p in gv.auto_accept : lookup(
            local._ctx_projects,
            trimprefix(p, "$project_ids:"),
            p
          )
        ])
      }
    }
  ]...)

  ncc_vpc_spokes = merge([
    for hk, hv in local._ncc_configs : {
      for sk, sv in hv.spokes.vpcs : "${hk}/${sk}" => {
        name = coalesce(sv.name, replace("${hk}-${sk}", "/", "-"))
        hub  = hk
        vpc_key = trimprefix(
          trimprefix(coalesce(sv.vpc, sk), "$vpcs:"),
          "$networks:"
        )
        project_id = (
          sv.project_id != null
          ? lookup(
            local._ctx_projects,
            trimprefix(sv.project_id, "$project_ids:"),
            sv.project_id
          )
          : lookup(
            local._ctx_vpc_projects,
            trimprefix(
              trimprefix(coalesce(sv.vpc, sk), "$vpcs:"),
              "$networks:"
            ),
            try(
              regex("projects/([^/]+)/", coalesce(sv.vpc, sk))[0],
              local._ncc_hub_projects[hk]
            )
          )
        )
        group = (
          sv.group == null
          ? null
          : trimprefix(sv.group, "$ncc_groups:")
        )
        description           = sv.description
        labels                = sv.labels
        exclude_export_ranges = sv.exclude_export_ranges
        include_export_ranges = sv.include_export_ranges
      }
    }
  ]...)

  ncc_vpn_spokes = merge([
    for hk, hv in local._ncc_configs : {
      for sk, sv in hv.spokes.tunnels : "${hk}/${sk}" => {
        name = coalesce(sv.name, replace("${hk}-${sk}", "/", "-"))
        hub  = hk
        project_id = (
          sv.project_id != null
          ? lookup(
            local._ctx_projects,
            trimprefix(sv.project_id, "$project_ids:"),
            sv.project_id
          )
          : try(
            regex("projects/([^/]+)/", sv.uris[0])[0],
            local._ncc_hub_projects[hk]
          )
        )
        location = (
          sv.location != null
          ? lookup(
            local._ctx_locations,
            trimprefix(sv.location, "$locations:"),
            sv.location
          )
          : try(
            regex("regions/([^/]+)/", sv.uris[0])[0],
            var.regions.primary
          )
        )
        group = (
          sv.group == null
          ? null
          : trimprefix(sv.group, "$ncc_groups:")
        )
        description                = sv.description
        labels                     = sv.labels
        uris                       = sv.uris
        site_to_site_data_transfer = sv.site_to_site_data_transfer
        include_import_ranges      = sv.include_import_ranges
      }
    }
  ]...)

  ncc_vlan_attachment_spokes = merge([
    for hk, hv in local._ncc_configs : {
      for sk, sv in hv.spokes.vlan_attachments : "${hk}/${sk}" => {
        name = coalesce(sv.name, replace("${hk}-${sk}", "/", "-"))
        hub  = hk
        project_id = (
          sv.project_id != null
          ? lookup(
            local._ctx_projects,
            trimprefix(sv.project_id, "$project_ids:"),
            sv.project_id
          )
          : try(
            regex("projects/([^/]+)/", sv.uris[0])[0],
            local._ncc_hub_projects[hk]
          )
        )
        location = (
          sv.location != null
          ? lookup(
            local._ctx_locations,
            trimprefix(sv.location, "$locations:"),
            sv.location
          )
          : try(
            regex("regions/([^/]+)/", sv.uris[0])[0],
            var.regions.primary
          )
        )
        group = (
          sv.group == null
          ? null
          : trimprefix(sv.group, "$ncc_groups:")
        )
        description                = sv.description
        labels                     = sv.labels
        uris                       = sv.uris
        site_to_site_data_transfer = sv.site_to_site_data_transfer
        include_import_ranges      = sv.include_import_ranges
      }
    }
  ]...)

  ncc_ra_spokes = merge([
    for hk, hv in local._ncc_configs : {
      for sk, sv in hv.spokes.router_appliances : "${hk}/${sk}" => {
        name = coalesce(sv.name, replace("${hk}-${sk}", "/", "-"))
        hub  = hk
        project_id = (
          sv.project_id != null
          ? lookup(
            local._ctx_projects,
            trimprefix(sv.project_id, "$project_ids:"),
            sv.project_id
          )
          : try(
            regex("projects/([^/]+)/", sv.instances[0].virtual_machine)[0],
            local._ncc_hub_projects[hk]
          )
        )
        location = (
          sv.location != null
          ? lookup(
            local._ctx_locations,
            trimprefix(sv.location, "$locations:"),
            sv.location
          )
          : try(
            regex(
              "zones/([a-z]+-[a-z0-9]+)-[a-z]/",
              sv.instances[0].virtual_machine
            )[0],
            var.regions.primary
          )
        )
        group = (
          sv.group == null
          ? null
          : trimprefix(sv.group, "$ncc_groups:")
        )
        description                = sv.description
        labels                     = sv.labels
        instances                  = sv.instances
        site_to_site_data_transfer = sv.site_to_site_data_transfer
        include_import_ranges      = sv.include_import_ranges
      }
    }
  ]...)
}

resource "google_network_connectivity_hub" "default" {
  for_each        = local.ncc_hubs
  project         = each.value.project_id
  name            = each.key
  description     = each.value.description
  export_psc      = each.value.export_psc
  policy_mode     = each.value.policy_mode
  preset_topology = each.value.preset_topology
  labels          = each.value.labels

  lifecycle {
    precondition {
      condition = (
        each.value.policy_mode == null ||
        contains(["CUSTOM", "PRESET"], each.value.policy_mode)
      )
      error_message = "NCC hub policy_mode must be null, CUSTOM, or PRESET."
    }
    precondition {
      condition = (
        each.value.preset_topology == null || (
          coalesce(each.value.policy_mode, "PRESET") == "PRESET" &&
          contains(["MESH", "STAR"], each.value.preset_topology)
        )
      )
      error_message = join(" ", [
        "NCC hub preset_topology must be MESH or STAR when policy_mode is",
        "PRESET, and null when policy_mode is CUSTOM.",
      ])
    }
  }

  depends_on = [
    module.vdss-host-project,
    module.env-spoke-projects,
  ]
}

resource "google_network_connectivity_group" "default" {
  for_each    = local.ncc_groups
  project     = each.value.project_id
  name        = each.value.name
  hub         = lookup(local._ctx_ncc_hubs, each.value.hub, each.value.hub)
  labels      = each.value.labels
  description = each.value.description

  dynamic "auto_accept" {
    for_each = length(each.value.auto_accept) > 0 ? [""] : []
    content {
      auto_accept_projects = each.value.auto_accept
    }
  }

  lifecycle {
    precondition {
      condition     = contains(["default", "center", "edge"], each.value.name)
      error_message = "NCC group name must be one of default, center, or edge."
    }
  }

  depends_on = [google_network_connectivity_hub.default]
}

resource "google_network_connectivity_spoke" "vpcs" {
  for_each    = local.ncc_vpc_spokes
  project     = each.value.project_id
  name        = each.value.name
  location    = "global"
  description = each.value.description
  labels      = each.value.labels
  hub         = lookup(local._ctx_ncc_hubs, each.value.hub, each.value.hub)
  group = (
    each.value.group == null
    ? null
    : lookup(
      local._ctx_ncc_groups,
      "${each.value.hub}/${each.value.group}",
      lookup(local._ctx_ncc_groups, each.value.group, each.value.group)
    )
  )

  linked_vpc_network {
    uri = lookup(
      local._ctx_vpcs,
      each.value.vpc_key,
      each.value.vpc_key
    )
    exclude_export_ranges = each.value.exclude_export_ranges
    include_export_ranges = each.value.include_export_ranges
  }

  depends_on = [
    google_network_connectivity_hub.default,
    google_network_connectivity_group.default,
  ]
}

resource "google_network_connectivity_spoke" "tunnels" {
  for_each    = local.ncc_vpn_spokes
  project     = each.value.project_id
  name        = each.value.name
  location    = each.value.location
  description = each.value.description
  labels      = each.value.labels
  hub         = lookup(local._ctx_ncc_hubs, each.value.hub, each.value.hub)
  group = (
    each.value.group == null
    ? null
    : lookup(
      local._ctx_ncc_groups,
      "${each.value.hub}/${each.value.group}",
      lookup(local._ctx_ncc_groups, each.value.group, each.value.group)
    )
  )

  linked_vpn_tunnels {
    uris                       = each.value.uris
    site_to_site_data_transfer = each.value.site_to_site_data_transfer
    include_import_ranges      = each.value.include_import_ranges
  }

  depends_on = [
    google_network_connectivity_hub.default,
    google_network_connectivity_group.default,
  ]
}

resource "google_network_connectivity_spoke" "vlan_attachments" {
  for_each    = local.ncc_vlan_attachment_spokes
  project     = each.value.project_id
  name        = each.value.name
  location    = each.value.location
  description = each.value.description
  labels      = each.value.labels
  hub         = lookup(local._ctx_ncc_hubs, each.value.hub, each.value.hub)
  group = (
    each.value.group == null
    ? null
    : lookup(
      local._ctx_ncc_groups,
      "${each.value.hub}/${each.value.group}",
      lookup(local._ctx_ncc_groups, each.value.group, each.value.group)
    )
  )

  linked_interconnect_attachments {
    uris                       = each.value.uris
    site_to_site_data_transfer = each.value.site_to_site_data_transfer
    include_import_ranges      = each.value.include_import_ranges
  }

  depends_on = [
    google_network_connectivity_hub.default,
    google_network_connectivity_group.default,
  ]
}

# VM instances cannot be deleted while referenced by a router appliance spoke
# (HTTP 412). Triggering spoke replacement on instance URI changes destroys the
# spoke before the VMs and recreates it afterward.
resource "terraform_data" "ncc_ra_instances" {
  for_each = local.ncc_ra_spokes
  input    = [for i in each.value.instances : i.virtual_machine]
}

resource "google_network_connectivity_spoke" "router_appliances" {
  for_each    = local.ncc_ra_spokes
  project     = each.value.project_id
  name        = each.value.name
  location    = each.value.location
  description = each.value.description
  labels      = each.value.labels
  hub         = lookup(local._ctx_ncc_hubs, each.value.hub, each.value.hub)
  group = (
    each.value.group == null
    ? null
    : lookup(
      local._ctx_ncc_groups,
      "${each.value.hub}/${each.value.group}",
      lookup(local._ctx_ncc_groups, each.value.group, each.value.group)
    )
  )

  linked_router_appliance_instances {
    dynamic "instances" {
      for_each = each.value.instances
      content {
        ip_address      = instances.value.ip_address
        virtual_machine = instances.value.virtual_machine
      }
    }
    site_to_site_data_transfer = each.value.site_to_site_data_transfer
    include_import_ranges      = each.value.include_import_ranges
  }

  lifecycle {
    replace_triggered_by = [terraform_data.ncc_ra_instances[each.key]]
    precondition {
      condition     = length(each.value.instances) > 0
      error_message = "Router appliance spoke must list at least one instance."
    }
  }

  depends_on = [
    google_network_connectivity_hub.default,
    google_network_connectivity_group.default,
  ]
}
