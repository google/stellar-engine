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

# tfdoc:file:description Decoupled multi-project tenant factory stage.

locals {
  _allowed_shared_vpc_agent_roles = toset([
    "roles/composer.sharedVpcAgent",
    "roles/compute.networkUser",
    "roles/container.hostServiceAgentUser",
    "roles/vpcaccess.user",
  ])
  _cmek_companion_apis = {
    "composer.googleapis.com" = [
      "storage.googleapis.com",
    ]
    "container.googleapis.com" = [
      "compute.googleapis.com",
    ]
    "dataflow.googleapis.com" = [
      "compute.googleapis.com",
    ]
    "datafusion.googleapis.com" = [
      "compute.googleapis.com",
      "dataproc.googleapis.com",
      "pubsub.googleapis.com",
      "spanner.googleapis.com",
      "storage.googleapis.com",
    ]
  }
  _default_lien_reason = (
    "Managed by 4-tenant-factory. Set lifecycle_state to archived first."
  )
  _forbidden_roles = toset([
    "roles/compute.xpnAdmin",
    "roles/editor",
    "roles/iam.organizationRoleAdmin",
    "roles/iam.securityAdmin",
    "roles/iam.serviceAccountKeyAdmin",
    "roles/orgpolicy.policyAdmin",
    "roles/owner",
    "roles/resourcemanager.folderAdmin",
    "roles/resourcemanager.folderIamAdmin",
    "roles/resourcemanager.lienModifier",
    "roles/resourcemanager.organizationAdmin",
    "roles/resourcemanager.projectIamAdmin",
  ])
  _gcp_id_regex = "^[a-z][a-z0-9-]{4,28}[a-z0-9]$"
  _gcs_resman_outputs = (
    length(data.google_storage_bucket_object_content.resman_outputs) > 0
    ? try(
      jsondecode(
        data.google_storage_bucket_object_content.resman_outputs[0].content
      ),
      {}
    )
    : {}
  )
  _gcs_environment_folders = {
    for k, v in try(local._gcs_resman_outputs.folder_ids.envs, {}) :
    lower(k) => v if v != null
  }
  _var_environment_folders = {
    for k, v in coalesce(try(var.folder_ids.envs, null), {}) :
    lower(k) => v if v != null
  }
  _service_agents_raw = yamldecode(file(
    "${path.module}/../../../modules/project/service-agents.yaml"
  ))
  _service_agent_alias_apis = merge([
    for entry in local._service_agents_raw : {
      for alias in concat([entry.name], try(entry.aliases, [])) :
      alias => coalesce(try(entry.api, null), "compute.googleapis.com")
    }
  ]...)
  _svpc_grants_raw = yamldecode(file(
    "${path.module}/../../../modules/project/sharedvpc-agent-iam.yaml"
  ))
  _svpc_grant_companion_apis = {
    for entry in local._svpc_grants_raw : entry.service => distinct(compact(
      concat(
        [entry.service],
        [
          for agent_alias in keys(try(entry.agents, {})) :
          lookup(local._service_agent_alias_apis, agent_alias, null)
        ]
      )
    ))
  }
  _project_templates_path = (
    var.factories_config.project_templates_path == null
    ? null
    : (
      startswith(var.factories_config.project_templates_path, "/") ||
      startswith(var.factories_config.project_templates_path, "~")
      ? pathexpand(var.factories_config.project_templates_path)
      : "${path.module}/${var.factories_config.project_templates_path}"
    )
  )
  _project_templates = {
    for f in try(fileset(local._project_templates_path, "**/*.yaml"), []) :
    trimsuffix(f, ".yaml") => try(
      {
        for k, v in yamldecode(
          file("${local._project_templates_path}/${f}")
        ) : k => v
      },
      {}
    )
  }
  _tenants_data_path = (
    var.factories_config.tenants_data_path == null
    ? null
    : (
      startswith(var.factories_config.tenants_data_path, "/") ||
      startswith(var.factories_config.tenants_data_path, "~")
      ? pathexpand(var.factories_config.tenants_data_path)
      : "${path.module}/${var.factories_config.tenants_data_path}"
    )
  )
  _yaml_tenant_files = {
    for f in try(fileset(local._tenants_data_path, "**/*.yaml"), []) :
    replace(trimsuffix(f, ".yaml"), "/", "-") => try(
      {
        for k, v in yamldecode(
          file("${local._tenants_data_path}/${f}")
        ) : k => v
      },
      {}
    )
  }
  _yaml_tenants = {
    for f, data in local._yaml_tenant_files :
    format(
      "%s/%s",
      try(data.environment, ""),
      coalesce(try(data.tenant_id, null), f)
      ) => {
      data        = data
      tenant_slug = coalesce(try(data.tenant_id, null), f)
    }
    if length(data) > 0
  }
  _hcl_tenants = {
    for tk, tv in var.tenants :
    format(
      "%s/%s",
      tv.environment,
      coalesce(tv.tenant_id, trimprefix(tk, "${tv.environment}/"))
      ) => {
      data = tv
      tenant_slug = coalesce(
        tv.tenant_id,
        trimprefix(tk, "${tv.environment}/")
      )
    }
  }
  _tenants_raw = merge(local._yaml_tenants, local._hcl_tenants)
  _tenants_have_org_policies = anytrue(flatten([
    for tk, entry in local._tenants_raw : concat(
      [try(entry.data.org_policies, null) != null],
      [
        for pk, pv in try(entry.data.projects, {}) :
        try(pv.org_policies, null) != null
      ]
    )
  ]))
  _all_assigned_roles = flatten([
    for tk, tv in local.tenants : concat(
      keys(tv.iam),
      flatten([
        for pk, pv in tv.projects : concat(
          keys(pv.iam),
          keys(pv.shared_vpc_service_agent_iam),
          flatten(values(pv.iam_by_principals)),
          [for bk, bv in pv.iam_bindings_additive : bv.role],
          flatten([
            for sk, sv in pv.service_accounts : sv.iam_self_roles
          ])
        )
      ])
    )
  ])
  _all_shared_vpc_agent_roles = flatten([
    for pk, pv in local.tenant_projects :
    keys(pv.shared_vpc_service_agent_iam)
  ])
  _all_shared_vpc_agent_members = flatten([
    for pk, pv in local.tenant_projects :
    flatten(values(pv.shared_vpc_service_agent_iam))
  ])
  _all_shared_vpc_grants = flatten([
    for pk, pv in local.tenant_projects : pv.shared_vpc_service_grants
  ])
  _all_shared_vpc_subnets = flatten([
    for pk, pv in local.tenant_projects : pv.shared_vpc_subnets
  ])
  _all_computed_project_ids = [
    for pk, pv in local.tenant_projects : "${var.prefix}-${pv.name}"
  ]
  _all_automation_sa_ids = flatten([
    for tk, tv in local.tenants :
    tv.automation == null ? [] : [
      for sk in keys(tv.automation.service_accounts) :
      "${replace(tv.folder_key, "/", "-")}-${sk}"
    ]
  ])
  environment_folders = merge(
    local._var_environment_folders,
    local._gcs_environment_folders,
    var.environment_folders
  )
  tenants = {
    for tk, entry in local._tenants_raw : tk => {
      automation = (
        try(entry.data.automation, null) == null
        ? null
        : {
          bucket_kms_key = try(
            coalesce(
              try(entry.data.automation.bucket_kms_key, null),
              try(var.automation.kms_keys.gcs, null)
            ),
            null
          )
          bucket_location = try(entry.data.automation.bucket_location, null)
          create_bucket = coalesce(
            try(entry.data.automation.create_bucket, null),
            true
          )
          project_id = try(coalesce(
            try(entry.data.automation.project_id, null),
            try(var.automation.project_id, null)
          ), null)
          service_accounts = {
            for sk, sv in try(entry.data.automation.service_accounts, {}) :
            sk => {
              description  = try(sv.description, null)
              display_name = try(sv.display_name, null)
            }
          }
        }
      )
      contacts = try(entry.data.contacts, {})
      descriptive_name = coalesce(
        try(entry.data.descriptive_name, null),
        entry.tenant_slug
      )
      environment = try(entry.data.environment, "")
      folder_key = format(
        "%s/%s",
        try(entry.data.environment, ""),
        entry.tenant_slug
      )
      iam    = try(entry.data.iam, {})
      labels = try(entry.data.labels, {})
      lifecycle_state = coalesce(
        try(entry.data.lifecycle_state, null),
        "active"
      )
      projects = {
        for pk, pv in try(entry.data.projects, {}) : pk => {
          contacts         = try(pv.contacts, {})
          descriptive_name = try(pv.descriptive_name, null)
          iam              = try(pv.iam, {})
          iam_bindings_additive = {
            for bk, bv in try(pv.iam_bindings_additive, {}) : bk => {
              member    = bv.member
              role      = bv.role
              condition = try(bv.condition, null)
            }
          }
          iam_by_principals = try(pv.iam_by_principals, {})
          kms_services      = try(pv.kms_services, {})
          labels            = try(pv.labels, {})
          lien_reason       = try(pv.lien_reason, null)
          metric_scopes     = try(pv.metric_scopes, [])
          name              = try(pv.name, null)
          project_template  = try(pv.project_template, null)
          service_accounts = {
            for sk, sv in try(pv.service_accounts, {}) : sk => {
              description    = try(sv.description, null)
              display_name   = try(sv.display_name, null)
              iam_self_roles = try(sv.iam_self_roles, [])
            }
          }
          services                 = try(pv.services, [])
          shared_vpc_host_project  = try(pv.shared_vpc_host_project, null)
          shared_vpc_network_users = try(pv.shared_vpc_network_users, [])
          shared_vpc_service_agent_iam = try(
            pv.shared_vpc_service_agent_iam, {}
          )
          shared_vpc_service_grants = try(pv.shared_vpc_service_grants, [])
          shared_vpc_subnets        = try(pv.shared_vpc_subnets, [])
          tag_bindings              = try(pv.tag_bindings, {})
          vpc_sc_perimeter          = try(pv.vpc_sc_perimeter, null)
        }
      }
      tag_bindings = try(entry.data.tag_bindings, {})
      tenant_slug  = entry.tenant_slug
    }
  }
  pf_folders = {
    for tk, tv in local.tenants : tv.folder_key => merge(
      {
        contacts            = tv.contacts
        deletion_protection = tv.lifecycle_state == "active"
        iam                 = tv.iam
        name                = tv.descriptive_name
        parent = lookup(
          local.environment_folders, tv.environment, null
        )
        tag_bindings = tv.tag_bindings
      },
      (
        tv.automation == null || try(tv.automation.project_id, null) == null
        ? {}
        : {
          automation = merge(
            {
              prefix  = var.prefix
              project = tv.automation.project_id
              service_accounts = {
                for sk, sv in tv.automation.service_accounts : sk => {
                  description = coalesce(
                    sv.description,
                    "Tenant ${tv.tenant_slug} ${sk} automation SA."
                  )
                  display_name = coalesce(
                    sv.display_name,
                    "Tenant ${tv.tenant_slug} ${sk} automation."
                  )
                  iam_project_roles = {
                    (tv.automation.project_id) = [
                      "roles/serviceusage.serviceUsageConsumer"
                    ]
                  }
                }
              }
            },
            !tv.automation.create_bucket ? {} : {
              bucket = {
                encryption_key = (
                  tv.automation.bucket_kms_key == null
                  ? null
                  : lookup(
                    var.kms_keys,
                    tv.automation.bucket_kms_key,
                    tv.automation.bucket_kms_key
                  )
                )
                force_destroy = var.force_destroy
                iam = merge(
                  contains(keys(tv.automation.service_accounts), "rw") ? {
                    "roles/storage.objectAdmin" = [
                      format(
                        "$iam_principals:service_accounts/%s/automation/rw",
                        tv.folder_key
                      )
                    ]
                  } : {},
                  contains(keys(tv.automation.service_accounts), "ro") ? {
                    "roles/storage.objectViewer" = [
                      format(
                        "$iam_principals:service_accounts/%s/automation/ro",
                        tv.folder_key
                      )
                    ]
                  } : {}
                )
                location = coalesce(
                  tv.automation.bucket_location, var.storage_location
                )
                name                        = "tf-state"
                public_access_prevention    = "enforced"
                uniform_bucket_level_access = true
                versioning                  = true
              }
            }
          )
        }
      )
    )
  }
  _tenant_projects_flat = flatten([
    for tk, tv in local.tenants : [
      for pk, pv in tv.projects : {
        key             = "${tv.environment}/${tv.tenant_slug}/${pk}"
        tenant_slug     = tv.tenant_slug
        project_key     = pk
        environment     = tv.environment
        folder_key      = tv.folder_key
        lifecycle_state = tv.lifecycle_state
        template = (
          pv.project_template == null
          ? {}
          : lookup(local._project_templates, pv.project_template, {})
        )
        tenant  = tv
        project = pv
      }
    ]
  ])
  tenant_projects = {
    for item in local._tenant_projects_flat : item.key => {
      bigquery_kms_keys = distinct([
        for ref in lookup(
          merge(
            try(item.template.kms_services, {}),
            item.project.kms_services
          ),
          "bigquery.googleapis.com",
          []
        ) : lookup(var.kms_keys, ref, ref)
      ])
      billing_account = (
        var.billing_linkage_mode == "managed"
        ? try(var.billing_account.id, null)
        : null
      )
      contacts = merge(
        try(item.template.contacts, {}),
        item.tenant.contacts,
        item.project.contacts
      )
      deletion_policy = (
        item.lifecycle_state == "active"
        ? "PREVENT"
        : (var.force_destroy ? "DELETE" : "ABANDON")
      )
      descriptive_name = coalesce(
        item.project.descriptive_name,
        "${item.tenant.descriptive_name} ${item.project_key}"
      )
      environment           = item.environment
      folder_key            = item.folder_key
      iam                   = item.project.iam
      iam_bindings_additive = item.project.iam_bindings_additive
      iam_by_principals     = item.project.iam_by_principals
      labels = merge(
        try(item.template.labels, {}),
        item.tenant.labels,
        item.project.labels,
        {
          environment     = item.environment
          lifecycle_state = item.lifecycle_state
          tenant          = item.tenant_slug
        }
      )
      lien_reason = (
        item.lifecycle_state == "active"
        ? coalesce(item.project.lien_reason, local._default_lien_reason)
        : null
      )
      metric_scopes = distinct(concat(
        try(item.template.metric_scopes, []),
        item.project.metric_scopes
      ))
      name = coalesce(
        item.project.name,
        "${item.environment}-${item.tenant_slug}-${item.project_key}"
      )
      needs_shared_vpc = (
        item.project.shared_vpc_host_project != null ||
        length(item.project.shared_vpc_subnets) > 0 ||
        length(item.project.shared_vpc_network_users) > 0 ||
        length(item.project.shared_vpc_service_agent_iam) > 0 ||
        length(item.project.shared_vpc_service_grants) > 0
      )
      project_template = item.project.project_template
      resolved_host_project = try(coalesce(
        item.project.shared_vpc_host_project,
        lookup(var.shared_vpc_host_projects, item.environment, null)
      ), null)
      service_accounts = item.project.service_accounts
      service_encryption_key_ids = {
        for svc, key_refs in merge(
          try(item.template.kms_services, {}),
          item.project.kms_services
          ) : svc => [
          for ref in key_refs : lookup(var.kms_keys, ref, ref)
        ]
        if svc != "bigquery.googleapis.com"
      }
      services = distinct(concat(
        try(item.template.services, []),
        item.project.services,
        [
          for svc in keys(merge(
            try(item.template.kms_services, {}),
            item.project.kms_services
          )) : svc if endswith(svc, ".googleapis.com")
        ],
        flatten([
          for svc in keys(merge(
            try(item.template.kms_services, {}),
            item.project.kms_services
          )) : lookup(local._cmek_companion_apis, svc, [])
        ]),
        flatten([
          for grant in distinct(concat(
            try(item.template.shared_vpc_service_grants, []),
            item.project.shared_vpc_service_grants
            )) : lookup(
            local._svpc_grant_companion_apis,
            trimprefix(grant, "$service_agents:"),
            [trimprefix(grant, "$service_agents:")]
          )
          if endswith(
            trimprefix(grant, "$service_agents:"),
            ".googleapis.com"
          )
        ]),
        compact([
          for member in flatten(
            values(item.project.shared_vpc_service_agent_iam)
            ) : lookup(
            local._service_agent_alias_apis,
            trimprefix(member, "$service_agents:"),
            null
          )
        ])
      ))
      shared_vpc_network_users     = item.project.shared_vpc_network_users
      shared_vpc_service_agent_iam = item.project.shared_vpc_service_agent_iam
      shared_vpc_service_grants = distinct(concat(
        try(item.template.shared_vpc_service_grants, []),
        item.project.shared_vpc_service_grants
      ))
      shared_vpc_subnets = item.project.shared_vpc_subnets
      tag_bindings       = item.project.tag_bindings
      vpc_sc = (
        item.project.vpc_sc_perimeter == null
        ? null
        : {
          is_dry_run = coalesce(
            try(item.project.vpc_sc_perimeter.is_dry_run, null),
            false
          )
          perimeter_name = item.project.vpc_sc_perimeter.perimeter_name
        }
      )
    }
  }
  tenant_project_shared_vpc = {
    for k, v in local.tenant_projects : k => (
      !v.needs_shared_vpc || v.resolved_host_project == null
      ? {
        host_project             = null
        network_subnet_users     = {}
        network_users            = []
        service_agent_iam        = {}
        service_agent_subnet_iam = {}
        service_iam_grants       = []
      }
      : {
        host_project = v.resolved_host_project
        network_subnet_users = (
          length(v.shared_vpc_subnets) == 0 ||
          length(v.shared_vpc_network_users) == 0
          ? {}
          : {
            for subnet in v.shared_vpc_subnets :
            subnet => v.shared_vpc_network_users
          }
        )
        network_users = (
          length(v.shared_vpc_subnets) > 0 ? [] : v.shared_vpc_network_users
        )
        service_agent_iam = v.shared_vpc_service_agent_iam
        service_agent_subnet_iam = {
          for subnet in v.shared_vpc_subnets : subnet => distinct(compact([
            contains(v.services, "compute.googleapis.com")
            ? "cloudservices"
            : null,
            contains(v.services, "container.googleapis.com")
            ? "container-engine"
            : null,
          ]))
          if(
            contains(v.services, "compute.googleapis.com") ||
            contains(v.services, "container.googleapis.com")
          )
        }
        service_iam_grants = v.shared_vpc_service_grants
      }
    )
  }
  tenant_bigquery_projects = {
    for pk, pv in local.tenant_projects : pk => pv
    if length(pv.bigquery_kms_keys) > 0
  }
  tenant_bigquery_cmek = merge([
    for pk, pv in local.tenant_bigquery_projects : {
      for idx, key_id in pv.bigquery_kms_keys : "${pk}/${idx}" => {
        crypto_key_id = key_id
        project_key   = pk
      }
    }
  ]...)
  tenant_workload_sas = merge([
    for pk, pv in local.tenant_projects : {
      for sk, sv in pv.service_accounts : "${pk}/${sk}" => {
        description    = sv.description
        display_name   = sv.display_name
        iam_self_roles = sv.iam_self_roles
        name           = sk
        project_key    = pk
      }
    }
  ]...)
  project_context = {
    folder_ids = module.project-factory.folder_ids
    kms_keys   = var.kms_keys
  }
}

data "google_storage_bucket_object_content" "resman_outputs" {
  count = (
    var.read_stage_outputs_from_gcs &&
    try(var.automation.outputs_bucket, null) != null
  ) ? 1 : 0
  bucket = var.automation.outputs_bucket
  name   = "tfvars/1-resman.auto.tfvars.json"
}

resource "terraform_data" "tenant_validation" {
  lifecycle {
    precondition {
      condition = alltrue([
        for tk, tv in local.tenants :
        contains(keys(local.environment_folders), tv.environment)
      ])
      error_message = "Tenant environment must exist in environment_folders."
    }
    precondition {
      condition = alltrue([
        for tk, tv in local.tenants :
        can(regex("^[a-z]([a-z0-9-]{0,18}[a-z0-9])?$", tv.tenant_slug))
      ])
      error_message = "Tenant slug must be 1 to 20 lowercase slug characters."
    }
    precondition {
      condition = alltrue([
        for tk, tv in local.tenants :
        contains(["active", "archived"], tv.lifecycle_state)
      ])
      error_message = "Tenant lifecycle_state must be active or archived."
    }
    precondition {
      condition = alltrue([
        for role in local._all_assigned_roles :
        !contains(local._forbidden_roles, role)
      ])
      error_message = "Tenant IAM cannot grant forbidden high-privilege roles."
    }
    precondition {
      condition = alltrue([
        for role in local._all_shared_vpc_agent_roles :
        contains(local._allowed_shared_vpc_agent_roles, role)
      ])
      error_message = "shared_vpc_service_agent_iam role is not allowlisted."
    }
    precondition {
      condition = alltrue([
        for member in local._all_shared_vpc_agent_members :
        can(regex("^\\$service_agents:[a-z0-9-]+$", member))
      ])
      error_message = "shared_vpc_service_agent_iam requires $service_agents."
    }
    precondition {
      condition = alltrue(flatten([
        for pk, pv in local.tenant_projects : [
          for member in flatten(values(pv.shared_vpc_service_agent_iam)) : (
            contains(
              keys(local._service_agent_alias_apis),
              trimprefix(member, "$service_agents:")
            ) &&
            contains(
              pv.services,
              lookup(
                local._service_agent_alias_apis,
                trimprefix(member, "$service_agents:"),
                ""
              )
            )
          )
        ]
      ]))
      error_message = "Unknown $service_agents alias or missing backing API."
    }
    precondition {
      condition = alltrue([
        for grant in local._all_shared_vpc_grants :
        can(regex("^\\$service_agents:[a-z0-9-]+\\.googleapis\\.com$", grant))
      ])
      error_message = "shared_vpc_service_grants must match service agent API."
    }
    precondition {
      condition = alltrue([
        for subnet in local._all_shared_vpc_subnets :
        can(regex("^[a-z]+-[a-z]+[0-9]+/[a-z][a-z0-9-]*$", subnet))
      ])
      error_message = "shared_vpc_subnets entries must use <region>/<subnet>."
    }
    precondition {
      condition = alltrue([
        for pk, pv in local.tenant_projects :
        pv.vpc_sc == null ||
        can(regex(
          "^accessPolicies/[0-9]+/servicePerimeters/[A-Za-z0-9_]+$",
          pv.vpc_sc.perimeter_name
        ))
      ])
      error_message = "vpc_sc_perimeter.perimeter_name is invalid."
    }
    precondition {
      condition     = !local._tenants_have_org_policies
      error_message = "Per-tenant org_policies overrides are forbidden."
    }
    precondition {
      condition = alltrue([
        for tk, tv in local.tenants : length(tv.projects) > 0
      ])
      error_message = "Every tenant manifest must define at least one project."
    }
    precondition {
      condition = alltrue([
        for pk, pv in local.tenant_projects :
        !pv.needs_shared_vpc || pv.resolved_host_project != null
      ])
      error_message = "Shared VPC projects require a resolved host project."
    }
    precondition {
      condition = alltrue([
        for pk, pv in local.tenant_projects :
        pv.project_template == null ||
        contains(keys(local._project_templates), pv.project_template)
      ])
      error_message = "Referenced project_template was not found."
    }
    precondition {
      condition = alltrue([
        for tk, tv in local.tenants :
        tv.automation == null || tv.automation.project_id != null
      ])
      error_message = "Tenant automation requires automation.project_id."
    }
    precondition {
      condition = alltrue([
        for tk, tv in local.tenants :
        tv.automation == null || alltrue([
          for sk in keys(tv.automation.service_accounts) :
          contains(["ro", "rw"], sk)
        ])
      ])
      error_message = "automation.service_accounts allows only rw and ro keys."
    }
    precondition {
      condition = alltrue([
        for pid in local._all_computed_project_ids :
        can(regex(local._gcp_id_regex, pid))
      ])
      error_message = "Computed project IDs must be 6-30 valid GCP ID chars."
    }
    precondition {
      condition = (
        length(distinct(local._all_computed_project_ids)) ==
        length(local.tenant_projects)
      )
      error_message = "Computed tenant project IDs must be unique."
    }
    precondition {
      condition = alltrue(concat(
        [
          for k, v in local.tenant_workload_sas :
          can(regex(local._gcp_id_regex, v.name))
        ],
        [
          for sa_id in local._all_automation_sa_ids :
          can(regex(local._gcp_id_regex, sa_id))
        ]
      ))
      error_message = "Service account IDs must be 6-30 valid GCP ID chars."
    }
  }
}

module "project-factory" {
  source = "../../../modules/project-factory"
  context = {
    folder_ids = local.environment_folders
    kms_keys   = var.kms_keys
  }
  data_defaults = {
    bucket = {
      force_destroy = var.force_destroy
    }
    locations = {
      storage = var.storage_location
    }
  }
  factories_config = {
    basepath = "${path.module}/.project-factory-empty"
  }
  folders    = local.pf_folders
  depends_on = [terraform_data.tenant_validation]
}

module "tenant-projects" {
  source                  = "../../../modules/project"
  for_each                = local.tenant_projects
  billing_account         = each.value.billing_account
  contacts                = each.value.contacts
  context                 = local.project_context
  default_service_account = "deprivilege"
  deletion_policy         = each.value.deletion_policy
  descriptive_name        = each.value.descriptive_name
  iam                     = each.value.iam
  iam_bindings_additive   = each.value.iam_bindings_additive
  iam_by_principals       = each.value.iam_by_principals
  labels                  = each.value.labels
  lien_reason             = each.value.lien_reason
  metric_scopes           = each.value.metric_scopes
  name                    = each.value.name
  parent                  = "$folder_ids:${each.value.folder_key}"
  prefix                  = var.prefix
  service_agents_config = {
    grant_service_agent_editor = false
  }
  service_encryption_key_ids = each.value.service_encryption_key_ids
  services                   = each.value.services
  shared_vpc_service_config  = local.tenant_project_shared_vpc[each.key]
  tag_bindings               = each.value.tag_bindings
  vpc_sc                     = each.value.vpc_sc
  depends_on                 = [terraform_data.tenant_validation]
}

data "google_bigquery_default_service_account" "tenant_bq" {
  for_each   = local.tenant_bigquery_projects
  project    = module.tenant-projects[each.key].project_id
  depends_on = [module.tenant-projects]
}

resource "time_sleep" "tenant_bq_sa_propagation" {
  for_each        = local.tenant_bigquery_projects
  create_duration = "60s"
  depends_on      = [data.google_bigquery_default_service_account.tenant_bq]
}

resource "google_kms_crypto_key_iam_member" "tenant_bigquery_cmek" {
  for_each      = local.tenant_bigquery_cmek
  crypto_key_id = each.value.crypto_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member = (
    data.google_bigquery_default_service_account.tenant_bq[
      each.value.project_key
    ].member
  )
  depends_on = [time_sleep.tenant_bq_sa_propagation]
}

module "tenant-service-accounts" {
  source      = "../../../modules/iam-service-account"
  for_each    = local.tenant_workload_sas
  project_id  = module.tenant-projects[each.value.project_key].project_id
  name        = each.value.name
  description = each.value.description
  display_name = coalesce(
    each.value.display_name,
    "Workload service account ${each.value.name}."
  )
  iam_project_roles = (
    length(each.value.iam_self_roles) == 0
    ? {}
    : {
      (module.tenant-projects[each.value.project_key].project_id) = (
        each.value.iam_self_roles
      )
    }
  )
}
