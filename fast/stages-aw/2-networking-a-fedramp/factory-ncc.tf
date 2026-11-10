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
  _ncc_yaml = {
    for v in local._ncc_yaml_raw : tostring(v.name) => v
  }
  _ncc_enabled = (
    length(local._default_ncc_hubs) > 0 ||
    length(local._ncc_yaml) > 0 ||
    length(var.ncc_hubs) > 0
  )
  _all_ncc_hub_keys = toset(concat(
    keys(local._default_ncc_hubs),
    keys(local._ncc_yaml),
    keys(var.ncc_hubs)
  ))

  # Stage 2 context lookup maps for symbolic $namespace:key references.
  _ctx_locations = {
    for k, v in var.regions : k => v
  }
  _ctx_projects = merge(
    { for k, v in var.tenant_accounts : k => v.main_project },
    { for k, v in module.env-spoke-projects : k => v.project_id },
    { for k, v in module.env-spoke-projects : lower(k) => v.project_id },
    {
      for k, v in module.env-spoke-projects :
      "${lower(k)}-net-host" => v.project_id
    },
    local._hub_project_aliases
  )
  _ctx_vpcs = merge(
    local._hub_vpcs,
    { for k, v in module.env-spoke-vpc : k => v.self_link },
    { for k, v in module.env-spoke-vpc : lower(k) => v.self_link }
  )
  _ctx_vpc_projects = merge(
    { for k, _ in local._hub_vpcs : k => local._hub_project_id },
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

  _ncc_hub_raw_projects = {
    for hk in local._all_ncc_hub_keys : hk => try(
      coalesce(
        try(var.ncc_hubs[hk].project_id, null),
        try(tostring(local._ncc_yaml[hk].project_id), null),
        try(local._default_ncc_hubs[hk].project_id, null)
      ),
      null
    )
  }
  _ncc_hub_projects = {
    for hk, pid in local._ncc_hub_raw_projects : hk => (
      pid == null
      ? local._hub_project_id
      : lookup(local._ctx_projects, trimprefix(pid, "$project_ids:"), pid)
    )
  }
  _ncc_hub_policy_modes = {
    for hk in local._all_ncc_hub_keys : hk => try(
      coalesce(
        try(var.ncc_hubs[hk].policy_mode, null),
        try(tostring(local._ncc_yaml[hk].policy_mode), null),
        try(local._default_ncc_hubs[hk].policy_mode, null)
      ),
      tostring(null)
    )
  }

  ncc_hubs = {
    for hk in local._all_ncc_hub_keys : hk => {
      project_id = local._ncc_hub_projects[hk]
      description = coalesce(
        try(var.ncc_hubs[hk].description, null),
        try(tostring(local._ncc_yaml[hk].description), null),
        try(local._default_ncc_hubs[hk].description, null),
        "Terraform-managed."
      )
      export_psc = coalesce(
        try(var.ncc_hubs[hk].export_psc, null),
        try(tobool(local._ncc_yaml[hk].export_psc), null),
        try(local._default_ncc_hubs[hk].export_psc, null),
        true
      )
      policy_mode = local._ncc_hub_policy_modes[hk]
      preset_topology = (
        local._ncc_hub_policy_modes[hk] == "CUSTOM"
        ? try(
          coalesce(
            try(var.ncc_hubs[hk].preset_topology, null),
            try(tostring(local._ncc_yaml[hk].preset_topology), null)
          ),
          tostring(null)
        )
        : coalesce(
          try(var.ncc_hubs[hk].preset_topology, null),
          try(tostring(local._ncc_yaml[hk].preset_topology), null),
          try(local._default_ncc_hubs[hk].preset_topology, null),
          "MESH"
        )
      )
      labels = merge(
        try(local._default_ncc_hubs[hk].labels, {}),
        try({
          for k, v in local._ncc_yaml[hk].labels : tostring(k) => tostring(v)
        }, {}),
        try(var.ncc_hubs[hk].labels, {})
      )
    }
  }

  ncc_groups = merge([
    for hk in local._all_ncc_hub_keys : {
      for gk in toset(concat(
        keys(try(local._default_ncc_hubs[hk].groups, {})),
        keys(try(local._ncc_yaml[hk].groups, {})),
        keys(try(var.ncc_hubs[hk].groups, {}))
        )) : "${hk}/${gk}" => {
        name       = gk
        project_id = local._ncc_hub_projects[hk]
        hub_id     = lookup(local._ctx_ncc_hubs, hk, hk)
        description = coalesce(
          try(var.ncc_hubs[hk].groups[gk].description, null),
          try(tostring(local._ncc_yaml[hk].groups[gk].description), null),
          try(local._default_ncc_hubs[hk].groups[gk].description, null),
          "Terraform-managed."
        )
        labels = merge(
          try(local._default_ncc_hubs[hk].groups[gk].labels, {}),
          try({
            for k, v in local._ncc_yaml[hk].groups[gk].labels :
            tostring(k) => tostring(v)
          }, {}),
          try(var.ncc_hubs[hk].groups[gk].labels, {})
        )
        auto_accept = distinct([
          for p in concat(
            try(local._default_ncc_hubs[hk].groups[gk].auto_accept, []),
            try([
              for x in local._ncc_yaml[hk].groups[gk].auto_accept : tostring(x)
            ], []),
            try(var.ncc_hubs[hk].groups[gk].auto_accept, [])
          ) : lookup(local._ctx_projects, trimprefix(p, "$project_ids:"), p)
        ])
      }
    }
  ]...)

  # Common spoke metadata resolved once across all four spoke types.
  _ncc_spoke_types = [
    "vpcs", "tunnels", "vlan_attachments", "router_appliances"
  ]
  _ncc_spokes_common = {
    for st in local._ncc_spoke_types : st => merge([
      for hk in local._all_ncc_hub_keys : {
        for sk, sv in merge(
          try(local._default_ncc_hubs[hk].spokes[st], {}),
          try(local._ncc_yaml[hk].spokes[st], {}),
          try(var.ncc_hubs[hk].spokes[st], {})
          ) : "${hk}/${sk}" => {
          name = coalesce(
            try(tostring(sv.name), null), replace("${hk}-${sk}", "/", "-")
          )
          hub_id = lookup(local._ctx_ncc_hubs, hk, hk)
          group_id = (
            try(sv.group, null) == null
            ? tostring(null)
            : lookup(
              local._ctx_ncc_groups,
              "${hk}/${trimprefix(tostring(sv.group), "$ncc_groups:")}",
              lookup(
                local._ctx_ncc_groups,
                trimprefix(tostring(sv.group), "$ncc_groups:"),
                trimprefix(tostring(sv.group), "$ncc_groups:")
              )
            )
          )
          description = coalesce(
            try(tostring(sv.description), null), "Terraform-managed."
          )
          labels = try(
            { for k, v in sv.labels : tostring(k) => tostring(v) }, {}
          )
        }
      }
    ]...)
  }

  ncc_vpc_spokes = merge([
    for hk in local._all_ncc_hub_keys : {
      for sk, sv in merge(
        try(local._default_ncc_hubs[hk].spokes.vpcs, {}),
        try(local._ncc_yaml[hk].spokes.vpcs, {}),
        try(var.ncc_hubs[hk].spokes.vpcs, {})
        ) : "${hk}/${sk}" => merge(local._ncc_spokes_common.vpcs["${hk}/${sk}"], {
          vpc_key = trimprefix(
            trimprefix(coalesce(try(tostring(sv.vpc), null), sk), "$vpcs:"),
            "$networks:"
          )
          project_id = (
            try(sv.project_id, null) != null
            ? lookup(
              local._ctx_projects,
              trimprefix(tostring(sv.project_id), "$project_ids:"),
              tostring(sv.project_id)
            )
            : lookup(
              local._ctx_vpc_projects,
              trimprefix(
                trimprefix(coalesce(try(tostring(sv.vpc), null), sk), "$vpcs:"),
                "$networks:"
              ),
              try(
                regex(
                  "projects/([^/]+)/", coalesce(try(tostring(sv.vpc), null), sk)
                )[0],
                local._ncc_hub_projects[hk]
              )
            )
          )
          exclude_export_ranges = try(
            [for r in sv.exclude_export_ranges : tostring(r)], tolist(null)
          )
          include_export_ranges = try(
            [for r in sv.include_export_ranges : tostring(r)], tolist(null)
          )
      })
    }
  ]...)

  _ncc_uri_spokes = {
    for st in ["tunnels", "vlan_attachments"] : st => merge([
      for hk in local._all_ncc_hub_keys : {
        for sk, sv in merge(
          try(local._default_ncc_hubs[hk].spokes[st], {}),
          try(local._ncc_yaml[hk].spokes[st], {}),
          try(var.ncc_hubs[hk].spokes[st], {})
          ) : "${hk}/${sk}" => merge(local._ncc_spokes_common[st]["${hk}/${sk}"], {
            project_id = (
              try(sv.project_id, null) != null
              ? lookup(
                local._ctx_projects,
                trimprefix(tostring(sv.project_id), "$project_ids:"),
                tostring(sv.project_id)
              )
              : try(
                regex("projects/([^/]+)/", tostring(sv.uris[0]))[0],
                local._ncc_hub_projects[hk]
              )
            )
            location = (
              try(sv.location, null) != null
              ? lookup(
                local._ctx_locations,
                trimprefix(tostring(sv.location), "$locations:"),
                tostring(sv.location)
              )
              : try(
                regex("regions/([^/]+)/", tostring(sv.uris[0]))[0],
                var.regions.primary
              )
            )
            uris = [for u in sv.uris : tostring(u)]
            site_to_site_data_transfer = coalesce(
              try(tobool(sv.site_to_site_data_transfer), null), false
            )
            include_import_ranges = try(
              [for r in sv.include_import_ranges : tostring(r)],
              ["ALL_IPV4_RANGES"]
            )
        })
      }
    ]...)
  }
  ncc_vpn_spokes             = local._ncc_uri_spokes["tunnels"]
  ncc_vlan_attachment_spokes = local._ncc_uri_spokes["vlan_attachments"]

  ncc_ra_spokes = merge([
    for hk in local._all_ncc_hub_keys : {
      for sk, sv in merge(
        try(local._default_ncc_hubs[hk].spokes.router_appliances, {}),
        try(local._ncc_yaml[hk].spokes.router_appliances, {}),
        try(var.ncc_hubs[hk].spokes.router_appliances, {})
        ) : "${hk}/${sk}" => merge(
        local._ncc_spokes_common.router_appliances["${hk}/${sk}"],
        {
          project_id = (
            try(sv.project_id, null) != null
            ? lookup(
              local._ctx_projects,
              trimprefix(tostring(sv.project_id), "$project_ids:"),
              tostring(sv.project_id)
            )
            : try(
              regex(
                "projects/([^/]+)/", tostring(sv.instances[0].virtual_machine)
              )[0],
              local._ncc_hub_projects[hk]
            )
          )
          location = (
            try(sv.location, null) != null
            ? lookup(
              local._ctx_locations,
              trimprefix(tostring(sv.location), "$locations:"),
              tostring(sv.location)
            )
            : try(
              regex(
                "zones/([a-z]+-[a-z0-9]+)-[a-z]/",
                tostring(sv.instances[0].virtual_machine)
              )[0],
              var.regions.primary
            )
          )
          instances = [
            for inst in sv.instances : {
              ip_address      = tostring(inst.ip_address)
              virtual_machine = tostring(inst.virtual_machine)
            }
          ]
          site_to_site_data_transfer = coalesce(
            try(tobool(sv.site_to_site_data_transfer), null), false
          )
          include_import_ranges = try(
            [for r in sv.include_import_ranges : tostring(r)],
            ["ALL_IPV4_RANGES"]
          )
        }
      )
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

  depends_on = [module.env-spoke-projects]
}

resource "google_network_connectivity_group" "default" {
  for_each    = local.ncc_groups
  project     = each.value.project_id
  name        = each.value.name
  hub         = each.value.hub_id
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
  hub         = each.value.hub_id
  group       = each.value.group_id

  linked_vpc_network {
    uri = lookup(
      local._ctx_vpcs, each.value.vpc_key, each.value.vpc_key
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
  hub         = each.value.hub_id
  group       = each.value.group_id

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
  hub         = each.value.hub_id
  group       = each.value.group_id

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
  hub         = each.value.hub_id
  group       = each.value.group_id

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
