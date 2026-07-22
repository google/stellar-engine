#!/bin/bash

#### This script is an experimental state, and is designed to help clean environments
#### Use this script at your own risk. The author assumes no responsibility for any damages or losses incurred through its use.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# shellcheck source=automation/config.env.sample
source "${SCRIPT_DIR}"/config.env

# Tags
parent_tag_name=$(gcloud resource-manager tags keys list \
  --parent=organizations/"${ORGANIZATION_ID}" \
  --format="value(name)")

child_tag_name=$(gcloud resource-manager tags values list \
  --parent="${parent_tag_name}" \
  --format="value(name)")

gcloud resource-manager tags values delete "$child_tag_name"
gcloud resource-manager tags keys delete "$parent_tag_name"

# Custom Org Roles
declare -a custom_org_roles=()
while IFS= read -r role_name; do
    custom_org_roles+=("$role_name")
done < <(gcloud iam roles list \
          --organization="${ORGANIZATION_ID}" \
          --filter='name~^organizations/' \
          --format='value(name)' | awk -F'/' '{print $NF}' 2>/dev/null)

for i in "${custom_org_roles[@]}"; do
  gcloud iam roles delete --organization="${ORGANIZATION_ID}" "$i"
done

# Log Sinks
gcloud logging sinks delete "empty-audit-logs" --organization="$ORGANIZATION_ID"
gcloud logging sinks delete "workspace-audit-logs" --organization="$ORGANIZATION_ID"
gcloud logging sinks delete "vpc-sc" --organization="$ORGANIZATION_ID"
gcloud logging sinks delete "audit-logs" --organization="$ORGANIZATION_ID"

# Org Roles
gcloud iam roles delete gcveNetworkAdmin --organization="$ORGANIZATION_ID"
gcloud iam roles delete storageViewer --organization="$ORGANIZATION_ID"
gcloud iam roles delete organizationIamAdmin --organization="$ORGANIZATION_ID"
gcloud iam roles delete tenantNetworkAdmin --organization="$ORGANIZATION_ID"
gcloud iam roles delete tagViewer --organization="$ORGANIZATION_ID"
gcloud iam roles delete serviceProjectNetworkAdmin --organization="$ORGANIZATION_ID"
gcloud iam roles delete organizationAdminViewer --organization="$ORGANIZATION_ID"

# Org Policies
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/clouddeploy.disableServiceLabelGeneration
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/cloudfunctions.requireVPCConnector
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/compute.disableAllIpv6
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/compute.disableHybridCloudIpv6
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/compute.disableInternetNetworkEndpointGroup
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/compute.disableSshInBrowser
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/compute.disableVpcExternalIpv6
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/compute.disableVpcInternalIpv6
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/compute.requireOsLogin
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/essentialcontacts.disableProjectSecurityContacts
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/firestore.requireP4SAforImportExport
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/gcp.detailedAuditLoggingMode
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/gcp.disableCloudLogging
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/iam.disableServiceAccountCreation
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/iap.requireGlobalIapWebDisabled
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/iap.requireRegionalIapWebDisabled
gcloud resource-manager org-policies delete --organization="$ORGANIZATION_ID" constraints/compute.requireOsLogin