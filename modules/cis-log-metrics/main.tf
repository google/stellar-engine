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

locals {
  log_filter = {
    project-owner-log = <<EOH
    (protoPayload.serviceName="cloudresourcemanager.googleapis.com") 
    AND (ProjectOwnership OR projectOwnerInvitee) 
    OR (protoPayload.serviceData.policyDelta.bindingDeltas.action="REMOVE" 
    AND protoPayload.serviceData.policyDelta.bindingDeltas.role="roles/owner") 
    OR (protoPayload.serviceData.policyDelta.bindingDeltas.action="ADD" 
    AND protoPayload.serviceData.policyDelta.bindingDeltas.role="roles/owner")
    EOH

    audit-config-change = <<EOH
    protoPayload.methodName="SetIamPolicy" 
    AND protoPayload.serviceData.policyDelta.auditConfigDeltas:*
    EOH

    custom-role-change = <<EOH
    resource.type="iam_role" 
    AND (protoPayload.methodName="google.iam.admin.v1.CreateRole" 
    OR protoPayload.methodName="google.iam.admin.v1.DeleteRole" 
    OR protoPayload.methodName="google.iam.admin.v1.UpdateRole")
    EOH

    vpc-firewall-change = <<EOH
    resource.type="gce_firewall_rule" 
    AND (protoPayload.methodName:"compute.firewalls.patch" 
    OR protoPayload.methodName:"compute.firewalls.insert" 
    OR protoPayload.methodName:"compute.firewalls.delete")
    EOH

    vpc-route-change = <<EOH
    resource.type="gce_route" 
    AND (protoPayload.methodName:"compute.routes.delete" 
    OR protoPayload.methodName:"compute.routes.insert")
    EOH

    vpc-network-change = <<EOH
    resource.type="gce_network" 
    AND (protoPayload.methodName:"compute.networks.insert" 
    OR protoPayload.methodName:"compute.networks.patch" 
    OR protoPayload.methodName:"compute.networks.delete" 
    OR protoPayload.methodName:"compute.networks.removePeering"
    OR protoPayload.methodName:"compute.networks.addPeering")
    EOH

    storage-iam-change = <<EOH
    resource.type="gcs_bucket" 
    AND protoPayload.methodName="storage.setIamPermissions"
    EOH

    sql-config-change = <<EOH
    protoPayload.methodName:"cloudsql.instances.update"
    OR protoPayload.methodName:"cloudsql.instances.create"
    OR protoPayload.methodName:"cloudsql.instances.delete"
    EOH
  }
}

resource "google_logging_metric" "logging_metric" {
  for_each = local.log_filter
  project  = var.project

  name   = each.key
  filter = each.value
}
