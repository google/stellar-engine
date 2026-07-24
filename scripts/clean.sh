#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


#### This script is an experamental state, and is designed to help clean environemnts
#### Use this script at your own risk. The author assumes no responsibility for any damages or losses incurred through its use.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# shellcheck source=experimental/common-functions.sh
if [[ -f "${SCRIPT_DIR}/common-functions.sh" ]]; then
    source "${SCRIPT_DIR}/common-functions.sh"
else
    echo "Error: common-functions.sh not found."
    exit 1
fi

# Load configuration
if [ -f "${SCRIPT_DIR}/config.env" ]; then
    source "${SCRIPT_DIR}/config.env"
else
    log_error "config.env not found."
    exit 1
fi

# Parse arguments (overrides config.env)
CLEAN_ORG_LEVEL=false
for arg in "$@"; do
  case $arg in
    --org)
      CLEAN_ORG_LEVEL=true
      shift
      ;;
    --prefix=*)
      PREFIX="${arg#*=}"
      shift
      ;;
  esac
done

########### DANGER: DESTRUCTIVE OPERATIONS ############
log_warn "=== WARNING: DESTRUCTIVE SCRIPT ==="
log_warn "This script will DELETE ORGANIZATION-LEVEL RESOURCES!"
log_warn "It deletes Tags, Custom Roles, Log Sinks, and Org Policies."
log_warn "This is NOT just a local cleanup script."
echo
if ! promptUser "Do you want to proceed with cleaning up cloud resources?"; then
    log_info "Cleanup cancelled by user. Exiting safely."
    exit 0
fi

# Tags
log_info "Scanning for tags with prefix: ${PREFIX}"
parent_tag_name=$(gcloud resource-manager tags keys list \
  --parent=organizations/"${ORGANIZATION_ID}" \
  --format="value(name)" 2>/dev/null | grep "/${PREFIX}-" || echo "")

if [[ -n "$parent_tag_name" ]]; then
  child_tag_name=$(gcloud resource-manager tags values list \
    --parent="${parent_tag_name}" \
    --format="value(name)" 2>/dev/null || echo "")

  if [[ -n "$child_tag_name" ]]; then
      log_info "Deleting tag value: $child_tag_name"
      gcloud resource-manager tags values delete "$child_tag_name" --quiet
  fi
  log_info "Deleting tag key: $parent_tag_name"
  gcloud resource-manager tags keys delete "$parent_tag_name" --quiet
else
  log_info "No tags found with prefix ${PREFIX}"
fi

# Custom Org Roles
log_info "Scanning for custom roles with prefix: ${PREFIX}"
declare -a custom_org_roles=() 
while IFS= read -r role_name; do
    custom_org_roles+=("$role_name")
done < <(gcloud iam roles list \
          --organization="${ORGANIZATION_ID}" \
          --filter="name~^organizations/${ORGANIZATION_ID}/roles/${PREFIX}" \
          --format='value(name)' | awk -F'/' '{print $NF}' 2>/dev/null)

if [[ ${#custom_org_roles[@]} -gt 0 ]]; then
    for i in "${custom_org_roles[@]}"; do
      log_info "Deleting custom role: $i"
      gcloud iam roles delete --organization="${ORGANIZATION_ID}" "$i" --quiet
    done
else
    log_info "No custom roles found with prefix ${PREFIX}"
fi

# Log Sinks
log_info "Scanning for log sinks with prefix: ${PREFIX}"
# Note: Standard sinks (empty-audit-logs, etc.) are generic and NOT prefixed.
# Only deleting sinks that explicitly match the prefix to avoid affecting other deployments.
sinks=$(gcloud logging sinks list --organization="${ORGANIZATION_ID}" --format="value(name)" 2>/dev/null | grep "^${PREFIX}" || echo "")

if [[ -n "$sinks" ]]; then
    for sink in $sinks; do
        log_info "Deleting log sink: $sink"
        gcloud logging sinks delete "$sink" --organization="$ORGANIZATION_ID" --quiet
    done
else
    log_info "No log sinks found with prefix ${PREFIX}"
fi

# Org Roles (Generic) - SKIPPED
# log_warn "Skipping generic Org Role deletion (gcveNetworkAdmin, etc.) to protect shared resources."

# Org Policies (Generic) - SKIPPED
# log_warn "Skipping generic Org Policy deletion to protect shared resources."

# Custom Constraints
log_info "Scanning for custom constraints with prefix: ${PREFIX}"
# Only deleting constraints that explicitly match the prefix to avoid affecting other deployments.
constraints=$(gcloud org-policies list-custom-constraints --organization="${ORGANIZATION_ID}" --format="value(name)" 2>/dev/null | grep "custom.*${PREFIX}" || echo "")

if [[ -n "$constraints" ]]; then
    for constraint in $constraints; do
        log_info "Deleting custom constraint: $constraint"
        gcloud org-policies delete-custom-constraint "$constraint" --organization="${ORGANIZATION_ID}" --quiet
    done
else
    log_info "No custom constraints found with prefix ${PREFIX}"
fi

# Local State Cleanup
echo
log_warn "=== LOCAL STATE CLEANUP ==="
if promptUser "Would you like to also clean up all local Terraform state and config files?"; then
    log_info "Cleaning up local files..."
    
    # Define stages to clean
    STAGES=(
      "${SCRIPT_DIR}/../fast/stages-aw/0-bootstrap"
      "${SCRIPT_DIR}/../fast/stages-aw/1-resman"
      "${SCRIPT_DIR}/../fast/stages-aw/2-networking-a-fedramp-high"
      "${SCRIPT_DIR}/../fast/stages-aw/2-networking-b-il5-ngfw"
      "${SCRIPT_DIR}/../fast/stages-aw/3-security"
    )

    for stage_dir in "${STAGES[@]}"; do
      if [[ -d "$stage_dir" ]]; then
        log_info "Cleaning $stage_dir..."
        rm -f "$stage_dir/terraform.tfstate"
        rm -f "$stage_dir/terraform.tfstate"*backup
        rm -rf "$stage_dir/.terraform"
        rm -f "$stage_dir/"*-providers.tf
        rm -f "$stage_dir/"*.auto.tfvars.json
      fi
    done
    
    # Clean experimental dir
    rm -f "${SCRIPT_DIR}/terraform.tfstate"
    rm -f "${SCRIPT_DIR}/terraform.tfstate.backup"
    rm -rf "${SCRIPT_DIR}/.terraform"
    
    log_info "Local cleanup completed."
fi

log_info "Clean.sh completed."