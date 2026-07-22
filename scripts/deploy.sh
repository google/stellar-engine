#!/bin/bash
# Copyright 2026 Google LLC
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

#### Use this script at your own risk. The author assumes no responsibility for any damages or losses incurred through its use.

# Enable error handling
# Note: NOT using 'set -e' because it conflicts with interactive prompt functions
# that return non-zero as part of normal operation (e.g., when user says "no")
set -o pipefail

# Global variables
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}" || exit

# Source common functions
if [[ -f "${SCRIPT_DIR}/common-functions.sh" ]]; then
    # shellcheck source=experimental/common-functions.sh
    source "${SCRIPT_DIR}/common-functions.sh"
else
    # Fallback logging if common functions not available
    log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
    log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
    log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }
fi

# Enhanced error handler
error_handler() {
    local line_no=$1
    local exit_code=$?
    log_error "Script failed at line $line_no with exit code $exit_code"

    # Save deployment state for potential recovery
    if [[ -n "${PREFIX:-}" ]]; then
        local state_dir="${SCRIPT_DIR}/state"
        mkdir -p "$state_dir"
        echo "LAST_FAILED_OPERATION=deploy" >> "${state_dir}/last_operation_${PREFIX}.env" 2>/dev/null || true
        echo "LAST_FAILED_LINE=$line_no" >> "${state_dir}/last_operation_${PREFIX}.env" 2>/dev/null || true
    fi

    cleanup
    exit "$exit_code"
}

# Note: error_handler is already defined above, no need for setup_error_handling
trap 'error_handler $LINENO' ERR

# Check prerequisites before starting
if check_prerequisites; then
    log_info "Prerequisites check passed"
else
    log_error "Prerequisites check failed"
    exit 1
fi

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f tmp_*.yaml 2>/dev/null || true
}

trap cleanup EXIT

# Helper function to handle promptUser return codes properly
handle_prompt() {
    local prompt="$1"
    shift
    local commands=("$@")

    if promptUser "$prompt" "${commands[@]}"; then
        return 0  # Success - user chose "yes"
    else
        local exit_code=$?
        if [[ $exit_code -eq 255 ]]; then
            return 0  # Skip is treated as success for optional commands
        else
            return $exit_code  # Propagate other errors
        fi
    fi
}

# Handle prompts where skip should be treated as "no" (for if statements)
handle_prompt_if() {
    local prompt="$1"
    shift
    local commands=("$@")

    if promptUser "$prompt" "${commands[@]}"; then
        return 0  # Success - user chose "yes"
    else
        local exit_code=$?
        # Both "no" and "skip" return failure for if statements
        return 1
    fi
}

setup_logging

# Load configuration
load_config "${SCRIPT_DIR}" "PREFIX" "ORGANIZATION_ID" "BILLING_ACCOUNT" "BOOTSTRAP_PROJECT_ID" "DEPLOYER_EMAIL_ADDRESS" "COMPLIANCE_REGIME" "DIRECTORY_CUSTOMER_ID" "FULLY_QUALIFIED_DOMAIN_NAME" "LOGGING_ALERTS_EMAIL_ADDRESS" "REGION"

# Function to validate required environment variables
validate_env_vars() {
    local required_vars=("BILLING_ACCOUNT" "BOOTSTRAP_PROJECT_ID" "ORGANIZATION_ID" "PREFIX" "REGION")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi

    return 0
}

############ Prerequisites ############
log_info "Welcome to the Stellar Engine automated deployment!"
log_info "This is designed for the initial deployment."
log_warn "For a redeployment, please make sure you change the prefix and run the destroy.sh script prior to redeployment."
echo
log_info "Prerequisites:"
echo "• Large enough quota for your billing projects: https://support.google.com/code/contact/billing_quota_increase"
echo "• Super Admin privileges - if not, please contact your organization administrator."
 
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Continue with prerequisites setup?"; then
  # Source config.env early to get the correct PREFIX for deployment file checks
  if [[ -f "$SCRIPT_DIR"/config.env ]]; then
    # shellcheck source=experimental/config.env.sample
    source "$SCRIPT_DIR"/config.env || true
  fi

  # Check for old deployment files across ALL stages (anything that's not the current PREFIX)
  current_prefix="${PREFIX:-unknown}"
  log_info "Checking for old deployment files (not matching current prefix: '$current_prefix')..."
  old_files_found=false
  stages_with_old_files=()
  old_prefixes_found=()

  for stage_dir in "${SCRIPT_DIR}"/../fast/stages-aw/*/; do
    if [[ -d "$stage_dir" ]]; then
      stage_name=$(basename "$stage_dir")

      # Look for any terraform/json files with project references that don't match current prefix
      old_prefix_patterns=$(grep -ho '[a-z0-9]\+-prod-iac-core-[0-9]' "$stage_dir"/*.tf* "$stage_dir"/*.json 2>/dev/null | cut -d'-' -f1 | sort -u | grep -v "^${current_prefix}$" || true)
      backup_prefix_patterns=$(find "$stage_dir" -name "*.backup" -exec grep -ho '[a-z0-9]\+-prod-iac-core-[0-9]' {} \; 2>/dev/null | cut -d'-' -f1 | sort -u | grep -v "^${current_prefix}$" || true)

      # ALSO check for "prefix": "xyz" in json files (specifically for 0-globals.auto.tfvars.json)
      json_prefix_patterns=$(grep -o '"prefix"[[:space:]]*:[[:space:]]*"[^"]*"' "$stage_dir"/*.json 2>/dev/null | cut -d'"' -f4 | sort -u | grep -v "^${current_prefix}$" || true)

      if [[ -n "$old_prefix_patterns" ]] || [[ -n "$backup_prefix_patterns" ]] || [[ -n "$json_prefix_patterns" ]]; then
        old_files_found=true
        stages_with_old_files+=("$stage_name")
        # Collect unique old prefixes found
        for prefix in $old_prefix_patterns $backup_prefix_patterns $json_prefix_patterns; do
          # Use glob pattern matching instead of regex for literal string comparison
          if [[ ! " ${old_prefixes_found[*]} " == *" $prefix "* ]]; then
            old_prefixes_found+=("$prefix")
          fi
        done
      fi
    fi
  done

  if [[ "$old_files_found" == "true" ]]; then
    log_warn "Found old deployment files with prefixes: ${old_prefixes_found[*]} in stages: ${stages_with_old_files[*]}"
    log_info "These files will cause conflicts with the current '${current_prefix}' deployment"
    if handle_prompt "Would you like to clean up ALL old deployment files (keeping only '${current_prefix}') across all stages?"; then
      log_info "Cleaning up old deployment files (preserving '${current_prefix}' files)..."

      for stage_dir in "${SCRIPT_DIR}"/../fast/stages-aw/*/; do
        if [[ -d "$stage_dir" ]]; then
          stage_name=$(basename "$stage_dir")
          log_info "Cleaning stage: $stage_name"

          cd "$stage_dir" || continue

          # Smart handling of terraform files with old prefix references
          find . -name "*.tf" -exec grep -l '[a-z0-9]\+-prod-iac-core-[0-9]' {} \; 2>/dev/null | while read -r file; do
            if ! grep -q "${current_prefix}-prod-iac-core" "$file" 2>/dev/null; then
              old_prefix=$(grep -o '[a-z0-9]\+-prod-iac-core-[0-9]' "$file" | head -1 | cut -d'-' -f1)

              # Check if this is a provider file (script-generated, can be updated)
              if [[ "$file" == *"providers.tf" ]]; then
                log_info "  Updating provider file: $file ($old_prefix -> $current_prefix)"
                # Update all references to use current prefix
                sed -i.bak "s/${old_prefix}-prod-iac-core/${current_prefix}-prod-iac-core/g" "$file" 2>/dev/null || true
                sed -i.bak "s/${old_prefix}-prod-bootstrap/${current_prefix}-prod-bootstrap/g" "$file" 2>/dev/null || true
                sed -i.bak "s/${old_prefix}-prod-resman/${current_prefix}-prod-resman/g" "$file" 2>/dev/null || true
                sed -i.bak "s/${old_prefix}-security/${current_prefix}-security/g" "$file" 2>/dev/null || true
                rm -f "${file}.bak" 2>/dev/null || true
              else
                # Other .tf files - backup them as they might contain custom config
                log_info "  Backing up custom terraform file: $file (contains $old_prefix references)"
                mv "$file" "${file}.${old_prefix}.backup.$(date +%s)" 2>/dev/null || true
              fi
            fi
          done

          # Remove old tfvars files (these will be regenerated by the script)
          find . -name "*.json" -exec grep -lE '[a-z0-9]+-prod-iac-core-[0-9]|"prefix"[[:space:]]*:[[:space:]]*"[^"]*"' {} \; 2>/dev/null | while read -r file; do
            # Check for project ID mismatch
            if ! grep -q "${current_prefix}-prod-iac-core" "$file" 2>/dev/null; then
               # Check if it has a prefix key that mismatches
               file_prefix=$(grep -o '"prefix"[[:space:]]*:[[:space:]]*"[^"]*"' "$file" 2>/dev/null | head -1 | cut -d'"' -f4)
               
               # If it has a prefix key AND it doesn't match current prefix, OR if it has old project ID references
               if [[ -n "$file_prefix" && "$file_prefix" != "$current_prefix" ]] || grep -q '[a-z0-9]\+-prod-iac-core-[0-9]' "$file"; then
                  log_info "  Removing old tfvars: $file (conflicting prefix/project references)"
                  rm -f "$file" 2>/dev/null || true
               fi
            fi
          done

          # Clean old terraform state backups with old prefix references
          find . -name "*.backup" -exec grep -l '[a-z0-9]\+-prod-iac-core-[0-9]' {} \; 2>/dev/null | while read -r file; do
            if ! grep -q "${current_prefix}-prod-iac-core" "$file" 2>/dev/null; then
              old_prefix=$(grep -o '[a-z0-9]\+-prod-iac-core-[0-9]' "$file" | head -1 | cut -d'-' -f1)
              log_info "  Removing old state backup: $file (contains $old_prefix references)"
              rm -f "$file" 2>/dev/null || true
            fi
          done

          # Clean terraform cache/providers cache that might have old references
          if [[ -d ".terraform" ]]; then
            if find .terraform -type f -exec grep -l '[a-z0-9]\+-prod-iac-core-[0-9]' {} \; 2>/dev/null | grep -v "${current_prefix}-prod-iac-core" | grep -q .; then
              log_info "  Cleaning .terraform cache in $stage_name (contains old prefix references)"
              rm -rf .terraform .terraform.lock.hcl 2>/dev/null || true
            fi
          fi
        fi
      done

      cd "${SCRIPT_DIR}" || exit
      log_info "Old deployment files cleanup completed (preserved '${current_prefix}' files)"
    else
      log_warn "Skipping cleanup of old deployment files - proceeding with mixed prefixes"
      log_warn "Note: This may cause conflicts during deployment"
    fi
  else
    log_info "No conflicting deployment files found - all files match current prefix '${current_prefix}'"
  fi

  # Authentication
  handle_prompt 'Would you like to (re)authenticate with Google Cloud?' "gcloud auth login" "gcloud auth application-default login" || true

  # Set variables
  if [ ! -f "$SCRIPT_DIR"/config.env ] || handle_prompt "Would you like to overwrite your config.env file?"; then
    log_info "Available organizations:"
    if ! gcloud organizations list; then
        log_error "Failed to list organizations. Please check your authentication."
        exit 1
    fi
    echo

    # Input validation for each variable
    while [[ -z "${BILLING_ACCOUNT:-}" ]]; do
        read -r -p "Enter your billing account: " BILLING_ACCOUNT
        [[ -z "$BILLING_ACCOUNT" ]] && log_error "Billing account cannot be empty"
    done

    while [[ -z "${BOOTSTRAP_PROJECT_ID:-}" ]]; do
        read -r -p "Enter your bootstrap project ID: " BOOTSTRAP_PROJECT_ID
        [[ -z "$BOOTSTRAP_PROJECT_ID" ]] && log_error "Bootstrap project ID cannot be empty"
    done

    while [[ -z "${COMPLIANCE_REGIME:-}" ]]; do
        read -r -p "Enter the compliance regime: " COMPLIANCE_REGIME
        [[ -z "$COMPLIANCE_REGIME" ]] && log_error "Compliance regime cannot be empty"
    done

    while [[ -z "${DIRECTORY_CUSTOMER_ID:-}" ]]; do
        read -r -p "Enter your directory customer ID: " DIRECTORY_CUSTOMER_ID
        [[ -z "$DIRECTORY_CUSTOMER_ID" ]] && log_error "Directory customer ID cannot be empty"
    done

    while [[ -z "${DEPLOYER_EMAIL_ADDRESS:-}" ]] || [[ ! "$DEPLOYER_EMAIL_ADDRESS" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; do
        read -r -p "Enter your deployer email address: " DEPLOYER_EMAIL_ADDRESS
        if [[ -z "$DEPLOYER_EMAIL_ADDRESS" ]]; then
            log_error "Email address cannot be empty"
        elif [[ ! "$DEPLOYER_EMAIL_ADDRESS" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
            log_error "Please enter a valid email address"
        fi
    done

    while [[ -z "${FULLY_QUALIFIED_DOMAIN_NAME:-}" ]]; do
        read -r -p "Enter your fully qualified domain name: " FULLY_QUALIFIED_DOMAIN_NAME
        [[ -z "$FULLY_QUALIFIED_DOMAIN_NAME" ]] && log_error "Domain name cannot be empty"
    done

    while [[ -z "${LOGGING_ALERTS_EMAIL_ADDRESS:-}" ]] || [[ ! "$LOGGING_ALERTS_EMAIL_ADDRESS" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; do
        read -r -p "Enter your logging alerts email address: " LOGGING_ALERTS_EMAIL_ADDRESS
        if [[ -z "$LOGGING_ALERTS_EMAIL_ADDRESS" ]]; then
            log_error "Email address cannot be empty"
        elif [[ ! "$LOGGING_ALERTS_EMAIL_ADDRESS" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
            log_error "Please enter a valid email address"
        fi
    done

    while [[ -z "${ORGANIZATION_ID:-}" ]]; do
        read -r -p "Enter your organization ID: " ORGANIZATION_ID
        [[ -z "$ORGANIZATION_ID" ]] && log_error "Organization ID cannot be empty"
    done

    while [[ -z "${PREFIX:-}" ]] || [[ ${#PREFIX} -gt 6 ]]; do
        read -r -p "Enter your prefix (6 chars or less): " PREFIX
        if [[ -z "$PREFIX" ]]; then
            log_error "Prefix cannot be empty"
        elif [[ ${#PREFIX} -gt 6 ]]; then
            log_error "Prefix must be 6 characters or less (current: ${#PREFIX})"
        fi
    done

    while [[ -z "${REGION:-}" ]]; do
        read -r -p "Enter your region: " REGION
        [[ -z "$REGION" ]] && log_error "Region cannot be empty"
    done

    while [[ -z "${TENANT_NAME:-}" ]] || [[ ${#TENANT_NAME} -gt 6 ]]; do
        read -r -p "Enter your tenant name (6 chars or less): " TENANT_NAME
        if [[ -z "$TENANT_NAME" ]]; then
            log_error "Tenant name cannot be empty"
        elif [[ ${#TENANT_NAME} -gt 6 ]]; then
            log_error "Tenant name must be 6 characters or less (current: ${#TENANT_NAME})"
        fi
    done

    log_info "Configuration Summary:"
    echo "  • billing-account: $BILLING_ACCOUNT"
    echo "  • bootstrap-project-id: $BOOTSTRAP_PROJECT_ID"
    echo "  • compliance-regime: $COMPLIANCE_REGIME"
    echo "  • directory-customer-id: $DIRECTORY_CUSTOMER_ID"
    echo "  • deployer-email-address: $DEPLOYER_EMAIL_ADDRESS"
    echo "  • fully-qualified-domain-name: $FULLY_QUALIFIED_DOMAIN_NAME"
    echo "  • logging-alerts-email-address: $LOGGING_ALERTS_EMAIL_ADDRESS"
    echo "  • organization-id: $ORGANIZATION_ID"
    echo "  • prefix: $PREFIX"
    echo "  • region: $REGION"
    echo "  • tenant-name: $TENANT_NAME"

    {
      echo "BILLING_ACCOUNT=$BILLING_ACCOUNT"
      echo "BOOTSTRAP_PROJECT_ID=$BOOTSTRAP_PROJECT_ID"
      echo "COMPLIANCE_REGIME=$COMPLIANCE_REGIME"
      echo "DIRECTORY_CUSTOMER_ID=$DIRECTORY_CUSTOMER_ID"
      echo "DEPLOYER_EMAIL_ADDRESS=$DEPLOYER_EMAIL_ADDRESS"
      echo "FULLY_QUALIFIED_DOMAIN_NAME=$FULLY_QUALIFIED_DOMAIN_NAME"
      echo "LOGGING_ALERTS_EMAIL_ADDRESS=$LOGGING_ALERTS_EMAIL_ADDRESS"
      echo "ORGANIZATION_ID=$ORGANIZATION_ID"
      echo "PREFIX=$PREFIX"
      echo "REGION=$REGION"
      echo "TENANT_NAME=$TENANT_NAME"
    } > "$SCRIPT_DIR"/config.env
  else
    # shellcheck source=experimental/config.env.sample
    if ! source "$SCRIPT_DIR"/config.env; then
        log_error "Failed to source config.env file"
        exit 1
    fi

    log_info "Current configuration from config.env:"
    echo "------------------------------------------------------------------"
    cat config.env
    echo "------------------------------------------------------------------"

    if ! validate_env_vars; then
        log_error "Invalid configuration in config.env"
        exit 1
    fi

    log_warn "Please verify the above configuration is correct"
  fi

  # Set Bootstrap Project
  handle_prompt "Would you like to set the bootstrap project as the default project?" "gcloud config set project ${BOOTSTRAP_PROJECT_ID}" || true

  # setIAM
  if [[ -f "${SCRIPT_DIR}/../fast/stages-aw/0-bootstrap/setIAM.sh" ]]; then
      handle_prompt "Would you like to set your IAM permissions?" "${SCRIPT_DIR}/../fast/stages-aw/0-bootstrap/setIAM.sh ${DEPLOYER_EMAIL_ADDRESS} ${ORGANIZATION_ID}" || true
  else
      log_warn "setIAM.sh script not found, skipping IAM setup"
  fi

  # enable Services
  if [[ -f "${SCRIPT_DIR}/../fast/stages-aw/0-bootstrap/enableServices.sh" ]]; then
      handle_prompt "Would you like to enable all Google Cloud Services?" "${SCRIPT_DIR}/../fast/stages-aw/0-bootstrap/enableServices.sh ${DEPLOYER_EMAIL_ADDRESS} ${ORGANIZATION_ID}" || true
  else
      log_warn "enableServices.sh script not found, skipping service enablement"
  fi

  # Link billing account
  if handle_prompt_if "Would you like to link the billing account to the bootstrap project?"; then
    log_info "Linking billing account ${BILLING_ACCOUNT} to ${BOOTSTRAP_PROJECT_ID}"
    if ! gcloud billing projects link "${BOOTSTRAP_PROJECT_ID}" --billing-account="${BILLING_ACCOUNT}"; then
        log_error "Failed to link billing account"
        exit 1
    fi
    log_info "Successfully linked billing account"
  fi

  # Groups and Admin setup
  echo -e "\nPlease follow the link below (if you have not yet done so) to set up 2) Users and groups and 3) Administrative access"
  echo "https://console.cloud.google.com/cloud-setup/overview?invt=AbuI_w&organizationId=${ORGANIZATION_ID}"
  echo "Press any key when complete to go to the next step."
  read -r -n 1 -s -p ""

  echo -e "\nPlease follow the link below (if you have not yet done so) to enable access transparency for your organization"
  echo "https://console.cloud.google.com/iam-admin/settings?invt=AbuKFg&organizationId=${ORGANIZATION_ID}"
  echo "Press any key when complete to go to the next step."
  read -r -n 1 -s -p ""

  echo -e "\nCongratulations, you have finished the prerequisites!"

else
    # shellcheck source=experimental/config.env.sample
    source "$SCRIPT_DIR"/config.env
    echo "------------------------------------------------------------------"
    echo "config.env"
    cat config.env
    echo "------------------------------------------------------------------"
    echo -e "If the above does not look correct your config.env may be wrong!\n"
fi

########### Stage 0 - Bootstrap ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 0 - Bootstrap -"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/0-bootstrap || exit

  # Check for organization-level resources from previous deployments
  log_info "Checking for organization-level resources from previous deployments..."
  org_resources_found=false

  # Check for custom IAM roles
  # Filter out standard roles that we expect to be there or will be managed by Terraform
  standard_roles="gcveNetworkAdmin|organizationAdminViewer|organizationIamAdmin|serviceProjectNetworkAdmin|storageViewer|tagViewer|tenantNetworkAdmin"
  custom_roles=$(gcloud iam roles list --organization="${ORGANIZATION_ID}" --format="value(name)" 2>/dev/null | grep -vE "$standard_roles" || echo "")
  if [[ -n "$custom_roles" ]]; then
    log_warn "Found existing custom IAM roles at organization level:"
    # shellcheck disable=SC2001
    echo "$custom_roles" | sed 's/^/  - /'
    org_resources_found=true
  fi

  # Check for logging sinks
  all_logging_sinks=$(gcloud logging sinks list --organization="${ORGANIZATION_ID}" --format="value(name)" 2>/dev/null || echo "")
  custom_logging_sinks=$(echo "$all_logging_sinks" | grep -v -E "^_Default$|^_Required$" || true)

  if [[ -n "$custom_logging_sinks" ]]; then
    log_warn "Found existing CUSTOM logging sinks at organization level:"
    echo "$custom_logging_sinks" | sed 's/^/  - /'
    org_resources_found=true
  else
    if [[ -n "$all_logging_sinks" ]]; then
      log_info "Found default logging sinks (_Default, _Required) - these will not be deleted."
    fi
  fi

  if [[ "$org_resources_found" == "true" ]]; then
    log_warn "These organization-level resources may conflict with the new deployment"
    log_warn "Note: Assured Workloads folders cannot be deleted and will cause soft-delete errors"

    if handle_prompt_if "Would you like to delete the custom organization-level resources listed above?"; then
      # Delete custom IAM roles
      if [[ -n "$custom_roles" ]]; then
        log_info "Deleting custom IAM roles..."
        while IFS= read -r role; do
          role_id=$(basename "$role")
          log_info "  Deleting role: $role_id"
          if gcloud iam roles delete "$role_id" --organization="${ORGANIZATION_ID}" --quiet 2>/dev/null; then
            log_info "    Deleted successfully"
          else
            log_warn "    Failed to delete (may be in use or already deleted)"
          fi
        done <<< "$custom_roles"
      fi

      # Delete CUSTOM logging sinks
      if [[ -n "$custom_logging_sinks" ]]; then
        log_info "Deleting CUSTOM logging sinks..."
        while IFS= read -r sink; do
          log_info "  Deleting sink: $sink"
          if gcloud logging sinks delete "$sink" --organization="${ORGANIZATION_ID}" --quiet 2>/dev/null; then
            log_info "    Deleted successfully"
          else
            log_warn "    Failed to delete (may be in use or already deleted)"
          fi
        done <<< "$custom_logging_sinks"
      fi

      log_info "Organization-level resource cleanup completed"
    else
      log_warn "Skipping organization-level resource cleanup"
      log_warn "These resources may cause 'already exists' errors during deployment"
    fi
  else
    log_info "No conflicting organization-level resources found"
  fi

  # Check for previous deployment remnants with different prefix
  if [[ -f "terraform.tfstate" ]]; then
    # Extract prefix from existing state file
    existing_prefix=$(grep -o '[a-z0-9]\+-prod-iac-core-[0-9]' terraform.tfstate 2>/dev/null | head -1 | cut -d'-' -f1 || echo "")
    current_prefix="${PREFIX:-unknown}"

    if [[ -n "$existing_prefix" ]] && [[ "$existing_prefix" != "$current_prefix" ]]; then
      log_warn "Found terraform state from deployment prefix '$existing_prefix' (current: '$current_prefix')"
      log_info "This will cause conflicts with the current deployment"
      if handle_prompt_if "Would you like to clean up the old '$existing_prefix' deployment files?"; then
        log_info "Backing up old deployment files from prefix '$existing_prefix'..."
        rm -rf .terraform .terraform.lock.hcl
        mv terraform.tfstate "terraform.tfstate.${existing_prefix}.backup.$(date +%s)" 2>/dev/null || true
        # Also backup any tfvars from the old deployment
        if [[ -f "terraform.tfvars" ]]; then
          mv terraform.tfvars "terraform.tfvars.${existing_prefix}.backup.$(date +%s)" 2>/dev/null || true
        fi
        log_info "Cleaned up old '$existing_prefix' deployment files"
      else
        log_error "Cannot proceed with mixed deployment prefixes. Please clean up manually or use a different directory."
        exit 1
      fi
    elif [[ -n "$existing_prefix" ]] && [[ "$existing_prefix" == "$current_prefix" ]]; then
      log_info "Found existing terraform state for current prefix '$current_prefix' - continuing with existing deployment"
    fi
  fi

  # Confirm billing account privikleges
  echo "Please make sure you have billing account admin privileges, and billing is enabled on the bootstrap project."
  echo "Press any key to confirm, and go to the next step."
  read -r -n 1 -s -p ""

  # Generate TF Vars - This will NOT work indented
  if handle_prompt_if "Would you like to generate a new tfvars file?"; then
cat <<EOF > terraform.tfvars
billing_account = {
  id = "${BILLING_ACCOUNT}"
}

# region configuration - this will automatically populate locations for GCS, BigQuery, KMS, and logging buckets
# Default to us-east4 for IL5/FedRAMP compliance - adjust as needed
regions = {
  primary = "${REGION}"  # Change to your preferred region - this will be used for all bootstrap resources
}

# use \`gcloud organizations list\`
organization = {
  domain      = "${FULLY_QUALIFIED_DOMAIN_NAME}"
  id          = "${ORGANIZATION_ID}"
  customer_id = "${DIRECTORY_CUSTOMER_ID}"
}

outputs_location = "~/fast-config"

# use something unique and no longer than 9 characters
prefix = "${PREFIX}"
log_sinks = {
  audit-logs = {
    filter = "logName:\"/logs/cloudaudit.googleapis.com%2Factivity\" OR logName:\"/logs/cloudaudit.googleapis.com%2Fsystem_event\" OR protoPayload.metadata.@type=\"type.googleapis.com/google.cloud.audit.TransparencyLog\""
    type   = "logging"
  }
  vpc-sc = {
    filter = "protoPayload.metadata.@type=\"type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata\""
    type   = "logging"
  }
  workspace-audit-logs = {
    filter = "logName:\"/logs/cloudaudit.googleapis.com%2Fdata_access\" and protoPayload.serviceName:\"login.googleapis.com\""
    type   = "logging"
  }

  # CIS Compliance Benchmark 2.2
  empty-audit-logs = {
    filter = ""
    type   = "logging"
  }
}

org_policies_config = {
  import_defaults = false # No policies to import as of 27 SEP 2024
}

fast_features = {
  envs = true
}

assured_workloads = {
  regime   = "${COMPLIANCE_REGIME}" # "IL4, IL5, FEDRAMP_HIGH, etc... if you wish to not use assured_workloads, set this value to COMPLIANCE_REGIME_UNSPECIFIED"
  location = "${REGION}" # Uses the same region as other resources for consistency - change to match your regions.primary if different
}

bootstrap_project = "${BOOTSTRAP_PROJECT_ID}"

alert_email = "${LOGGING_ALERTS_EMAIL_ADDRESS}"
EOF
  fi

  # Clean up any terraform cache from different prefix deployments
  if [[ -d ".terraform" ]] || [[ -f ".terraform.lock.hcl" ]]; then
    # Check if cache is from a different prefix
    cache_needs_cleaning=false

    if [[ -f ".terraform/terraform.tfstate" ]]; then
      cached_prefix=$(grep -o '[a-z0-9]\+-prod-iac-core-[0-9]' .terraform/terraform.tfstate 2>/dev/null | head -1 | cut -d'-' -f1 || echo "")
      if [[ -n "$cached_prefix" ]] && [[ "$cached_prefix" != "${PREFIX}" ]]; then
        cache_needs_cleaning=true
        log_warn "Terraform cache contains references to old prefix '$cached_prefix'"
      fi
    else
      # If no cached state info, clean cache to be safe
      cache_needs_cleaning=true
      log_info "Terraform cache detected without clear prefix information"
    fi

    if [[ "$cache_needs_cleaning" == "true" ]]; then
      if handle_prompt_if "Terraform cache may have conflicts. Clean cache for fresh deployment?"; then
        log_info "Cleaning terraform cache..."
        rm -rf .terraform .terraform.lock.hcl
        log_info "Terraform cache cleaned"
      else
        log_warn "Keeping existing terraform cache - this may cause backend conflicts"
      fi
    else
      log_info "Terraform cache appears to be for current prefix '${PREFIX}' - keeping cache"
    fi
  fi

  # Create temporary providers.tf for initial deployment (local backend)
  # Check if we've already migrated to remote state
  state_migrated=false

  # Check if local state is empty or missing AND remote backend is configured
  if [[ -f "0-bootstrap-providers.tf" ]] && grep -q "backend.*gcs" 0-bootstrap-providers.tf; then
    if [[ ! -f "terraform.tfstate" ]] || [[ ! -s "terraform.tfstate" ]]; then
      # No local state file OR empty local state file = already migrated
      log_info "Detected existing remote state backend configuration"
      state_migrated=true
    elif [[ -f ".terraform/terraform.tfstate" ]] && grep -q "backend.*gcs" .terraform/terraform.tfstate 2>/dev/null; then
      # Local state exists but .terraform cache shows remote backend = already migrated, local state is stale
      log_info "Detected remote backend in use (local state is stale)"
      state_migrated=true
    fi
  fi

  if [[ "$state_migrated" == "true" ]]; then
    log_info "Using existing remote backend configuration (state already migrated)"
  elif [ ! -f "0-bootstrap-providers.tf" ] || handle_prompt "Would you like to generate your initial providers.tf?"; then
    log_info "Creating initial providers.tf for local backend deployment..."
    cp providers.tf.tmp 0-bootstrap-providers.tf
  else
    # Check if existing providers file has backend config (which would cause issues for initial deployment with local state)
    if grep -q "backend.*gcs" 0-bootstrap-providers.tf && [[ -f "terraform.tfstate" ]] && [[ -s "terraform.tfstate" ]]; then
      log_warn "Found existing providers file with remote backend configuration"
      log_info "But non-empty local state file exists - for initial deployment, we need to start with local backend"
      if handle_prompt_if "Reset providers.tf to local backend for initial deployment?"; then
        log_info "Creating initial providers.tf for local backend..."
        cp providers.tf.tmp 0-bootstrap-providers.tf
      else
        log_error "Cannot proceed with remote backend during initial bootstrap deployment with non-empty local state"
        exit 1
      fi
    fi
  fi

  # Skip init if already using remote backend (state already migrated)
  if [[ "$state_migrated" != "true" ]]; then
    if handle_prompt_if "Would you like to perform the initial terraform init?"; then
      if ! terraform init; then
        log_error "Terraform init failed"
        exit 1
      fi
    else
      log_warn "Terraform init was skipped, but it's required for the apply step"
      log_info "Running terraform init automatically..."

      if ! terraform init; then
        log_error "Terraform init failed"
        log_error "Please run 'terraform init' manually or rerun the script and answer 'yes' to the init prompt"
        exit 1
      fi
    fi
  else
    log_info "State already migrated to remote backend, ensuring terraform is initialized..."
    if ! terraform init; then
      log_error "Terraform init failed"
      exit 1
    fi
  fi

  # Skip initial applies and state migration if already using remote backend
  if [[ "$state_migrated" == "true" ]]; then
    log_info "State already migrated to remote backend - skipping initial applies and state migration"
    log_info "Proceeding to org policy import and final terraform apply"
  else
    # Attempt to import standard custom roles if they exist to avoid "already exists" errors
    log_info "Checking for existing standard custom roles to import..."
    declare -A standard_roles_map=(
        ["gcveNetworkAdmin"]="gcve_network_admin"
        ["organizationAdminViewer"]="organization_admin_viewer"
        ["organizationIamAdmin"]="organization_iam_admin"
        ["serviceProjectNetworkAdmin"]="service_project_network_admin"
        ["storage_viewer"]="storage_viewer"
        ["tagViewer"]="tag_viewer"
        ["tenantNetworkAdmin"]="tenant_network_admin"
    )

    for role_name in "${!standard_roles_map[@]}"; do
        tf_name="${standard_roles_map[$role_name]}"
        role_id="organizations/${ORGANIZATION_ID}/roles/${role_name}"
        
        # Check if role exists (active or deleted)
        if gcloud iam roles describe "$role_name" --organization="${ORGANIZATION_ID}" >/dev/null 2>&1; then
            # Check if already in state
            if ! terraform state list 2>/dev/null | grep -q "module.organization.google_organization_iam_custom_role.roles\[\"$tf_name\"\]"; then
                log_info "Importing existing role $role_name into Terraform state..."
                # Undelete if necessary (best effort)
                gcloud iam roles undelete "$role_name" --organization="${ORGANIZATION_ID}" 2>/dev/null || true
                terraform import "module.organization.google_organization_iam_custom_role.roles[\"$tf_name\"]" "$role_id" || log_warn "Failed to import $role_name - continuing"
            else
                log_info "Role $role_name already in Terraform state"
            fi
        fi
    done

    # Attempt to import logging sinks if they exist to avoid "already exists" errors
    log_info "Checking for existing logging sinks to import..."
    declare -a logging_sinks=("audit-logs" "vpc-sc" "workspace-audit-logs" "empty-audit-logs")

    for sink_name in "${logging_sinks[@]}"; do
        sink_id="organizations/${ORGANIZATION_ID}/sinks/${sink_name}"
        
        # Check if sink exists
        if gcloud logging sinks describe "$sink_name" --organization="${ORGANIZATION_ID}" >/dev/null 2>&1; then
            # Check if already in state
            if ! terraform state list 2>/dev/null | grep -q "module.organization.google_logging_organization_sink.sink\[\"$sink_name\"\]"; then
                log_info "Importing existing sink $sink_name into Terraform state..."
                terraform import "module.organization.google_logging_organization_sink.sink[\"$sink_name\"]" "$sink_id" || log_warn "Failed to import $sink_name - continuing"
            else
                log_info "Sink $sink_name already in Terraform state"
            fi
        fi
    done

    # Terraform Apply #1
    if handle_prompt_if "Would you like to run the first terraform apply with the bootstrap user?"; then
    bootstrap_user=$(gcloud config list --format 'value(core.account)')
    log_info "Running terraform apply with bootstrap user: $bootstrap_user"

    # Proactive: Create Assured Workloads folder first to apply BigQuery fix before full apply
    log_info "Creating Assured Workloads folder first to apply BigQuery allowlist..."
    
    # Target the Assured Workloads resource (or no-compliance folder)
    if terraform_safe apply -auto-approve -target="google_assured_workloads_workload.primary" -target="module.no-compliance-folder" -var bootstrap_user="$bootstrap_user"; then
      log_info "Assured Workloads folder created successfully"
      
      # Run BigQuery allowlist fix immediately
      log_info "Applying BigQuery allowlist fix..."
      if [[ -f "${SCRIPT_DIR}/allow_bq.sh" ]]; then
        if "${SCRIPT_DIR}/allow_bq.sh"; then
          log_info "BigQuery allowlist applied successfully"
          log_info "Waiting 120 seconds for BigQuery policy changes to take effect..."
          sleep 120
        else
          log_warn "BigQuery allowlist script failed - continuing, but full apply may fail"
        fi
      else
        log_warn "allow_bq.sh script not found - skipping BigQuery fix"
      fi
    else
      log_warn "Targeted apply failed - proceeding to full apply (standard error handling will catch issues)"
    fi

    # Full Terraform Apply
    log_info "Running full terraform apply..."
    if terraform_safe apply -auto-approve -var bootstrap_user="$bootstrap_user"; then
      log_info "First terraform apply completed successfully"
    else
      # Fallback to standard error handling if it still fails
      log_warn "First terraform apply failed, checking for BigQuery constraint errors..."
      
      # Run terraform plan to get the error details without making changes
      terraform_output=$(terraform plan -var bootstrap_user="$bootstrap_user" 2>&1 || true)

      # Check for BigQuery constraint error
      if [[ "$terraform_output" == *"restrictServiceUsage"* ]] && [[ "$terraform_output" == *"bigquery.googleapis.com"* ]]; then
         log_warn "Detected BigQuery constraint error (persisting after proactive fix)."
         # ... existing retry logic ...
         if handle_prompt_if "Would you like to retry the BigQuery allowlist fix and terraform apply?"; then
            # ... existing retry logic ...
             if "${SCRIPT_DIR}/allow_bq.sh"; then
               log_info "BigQuery allowlist applied successfully (retry)"
               sleep 120
               if ! terraform_safe apply -auto-approve -var bootstrap_user="$bootstrap_user"; then
                 log_error "Terraform apply still failed after BigQuery fix retry"
                 exit 1
               fi
             fi
         else
            exit 1
         fi
      else
        log_error "First terraform apply failed (not a BigQuery constraint error)"
        echo "$terraform_output"
        exit 1
      fi
    fi
  fi

  # BigQuery allowlist is now handled automatically when constraint errors are detected during terraform apply

  # Terraform Apply #2
  cmd=("terraform apply -auto-approve -var bootstrap_user=$(gcloud config list --format 'value(core.account)')")
  handle_prompt "Would you like to run the second terraform apply with the bootstrap user?" "${cmd[@]}"

  # Set Default Project
  cmd=("gcloud config set project ${PREFIX}-prod-iac-core-0")
  handle_prompt "Would you like to set the default project to ${PREFIX}-prod-iac-core-0" "${cmd[@]}"

  # Update Providers
  cmd=("gcloud storage cp gs://${PREFIX}-prod-iac-core-outputs-0/providers/0-bootstrap-providers.tf ./")
  handle_prompt "Would you like to update your providers file?" "${cmd[@]}" # Pass the array elements

  # Update Application Default Credentials quota project before state migration
  log_info "Updating Application Default Credentials quota project to ${PREFIX}-prod-iac-core-0..."
  if ! gcloud auth application-default set-quota-project "${PREFIX}-prod-iac-core-0"; then
    log_warn "Failed to set quota project automatically"
    if handle_prompt_if "Would you like to re-authenticate with Application Default Credentials?"; then
      if gcloud auth application-default login; then
        log_info "Re-authentication successful"
      else
        log_error "Failed to authenticate with Application Default Credentials"
        log_info "State migration may fail. You can manually run:"
        log_info "  gcloud auth application-default login"
        log_info "  gcloud auth application-default set-quota-project ${PREFIX}-prod-iac-core-0"
      fi
    fi
  else
    log_info "Application Default Credentials quota project updated successfully"
  fi

  # Migrate from local state to remote GCS backend
  if handle_prompt_if "Would you like to migrate from local state to remote GCS backend?"; then
    # Check if cache needs cleaning for backend switch
    if [[ -f ".terraform/terraform.tfstate" ]]; then
      cached_backend=$(grep -o '[a-z0-9]\+-prod-iac-core-bootstrap-[0-9]' .terraform/terraform.tfstate 2>/dev/null | head -1 || echo "")
      expected_backend="${PREFIX}-prod-iac-core-bootstrap-0"

      if [[ -n "$cached_backend" ]] && [[ "$cached_backend" != "$expected_backend" ]]; then
        log_info "Cleaning terraform cache for backend switch from '$cached_backend' to '$expected_backend'..."
        rm -rf .terraform .terraform.lock.hcl 2>/dev/null || true
      fi
    fi

    # Migrate state from local to remote backend
    if [[ -f "terraform.tfstate" ]]; then
      log_info "Migrating local state to remote GCS backend ${PREFIX}-prod-iac-core-bootstrap-0..."
      if ! terraform init -migrate-state -force-copy; then
        log_error "State migration failed"
        log_info "Try running: gcloud auth application-default login"
        log_info "Then: gcloud auth application-default set-quota-project ${PREFIX}-prod-iac-core-0"
        exit 1
      fi
      log_info "State migration completed successfully"
    else
      log_info "No local state found, initializing with remote backend..."
      if ! terraform init; then
        log_error "Terraform init failed"
        exit 1
      fi
    fi
  fi
  fi  # End of state_migrated check

  # Import Organization Polcies
  handle_prompt "Would you like to import recommended org policies?" "${SCRIPT_DIR}/../fast/stages-aw/0-bootstrap/import.sh" || true

  # Terraform Apply #3 (after state migration, ensuring bootstrap user access)
  cmd=("terraform apply -auto-approve -var bootstrap_user=$(gcloud config list --format 'value(core.account)')")
  if ! handle_prompt "Would you like to run the final terraform apply (ensuring user access)?" "${cmd[@]}"; then
    true
  fi
fi

########### Stage 1 - Resman ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 1 - Resource Manager -"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/1-resman || exit
  if handle_prompt_if "Would you like to provide billing account admin permissions for ${PREFIX}-prod-resman-0@${PREFIX}-prod-iac-core-0.iam.gserviceaccount.com?"; then
    gcloud billing accounts add-iam-policy-binding "${BILLING_ACCOUNT}" --member=serviceAccount:"${PREFIX}"-prod-resman-0@"${PREFIX}"-prod-iac-core-0.iam.gserviceaccount.com  --role=roles/billing.admin
  fi

  # Generate new tfvars - this will not work indented
  if handle_prompt_if "Would you like to generate a new 1-resman tfvars?"; then
cat <<EOF > terraform.tfvars
tenants = {
${TENANT_NAME} = { ## Updated with tenant-name variable
  admin_principal  = "group:gcp-devops@${FULLY_QUALIFIED_DOMAIN_NAME}"
  descriptive_name = "${TENANT_NAME}" ## Updated with tenant-name variable
  locations = {
    gcs = "${REGION}"
    kms = "${REGION}" # Must match GCS Region
   }
 }
## You can have “n” number of tenants
}

fast_features = {
 envs = true
}

envs_folders = {
 Prod = {
   admin = "gcp-organization-admins@${FULLY_QUALIFIED_DOMAIN_NAME}"
 },
 Int = {
  admin = "gcp-organization-admins@${FULLY_QUALIFIED_DOMAIN_NAME}"
 },
 Test = {
   admin = "gcp-organization-admins@${FULLY_QUALIFIED_DOMAIN_NAME}"
 }
}
EOF
  fi

  # Modify tfvars prompt
  echo -e "\nIf you have more than one tenant, please modify your tfvars."
  echo "Press any key when ready."
  read -r -n 1 -s -p ""

  # Copy remote tfvars
  cmd=(
    "gcloud storage cp gs://${PREFIX}-prod-iac-core-outputs-0/providers/1-resman-providers.tf ./"
    "gcloud storage cp gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./"
    "gcloud storage cp gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./"
  )
  handle_prompt "Would you like to pull the remote tfvars files created in Stage 0?" "${cmd[@]}" || true

  handle_prompt "Would you like to perform the terraform init?" "terraform init" || true
  handle_prompt "Would you like to perform the terraform apply?" "terraform apply -auto-approve" || true

  echo "Congratulations, you have completed Stage 1!"
fi

########### Stage 2 - Networking ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 2 - Networking -"; then
  # Add external billing account
  if handle_prompt_if "Would you like to provide billing account admin permissions for ${PREFIX}-prod-resman-net-0@${PREFIX}-prod-iac-core-0.iam.gserviceaccount.com?"; then
    gcloud billing accounts add-iam-policy-binding "${BILLING_ACCOUNT}" --member=serviceAccount:"${PREFIX}"-prod-resman-net-0@"${PREFIX}"-prod-iac-core-0.iam.gserviceaccount.com  --role=roles/billing.admin
  fi

  # Choose networking paradigm
  cd "${SCRIPT_DIR}"/../fast/stages-aw/1-resman || exit

  echo "Please type \"1\", \"2\", or \"3\" below that corresponds to the network paradigm you want: "
  echo "1) IL2/FedRAMP Moderate"
  echo "2) FedRAMP High"
  echo "3) IL4/IL5"
  read -r choice

  ########### IL2/FedRAMP Moderate ###########
  if [ "$choice" == 1 ]; then
    echo "This stage is still under development. Goodbye!"

  ########### FedRAMP High ###########
  elif [ "$choice" == 2 ]; then
    echo "You have selected FedRAMP High"
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-a-fedramp-high || exit

    if handle_prompt_if "Would you like to pull the remote tfvars files created in Stages 0 and 1?"; then
      gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/providers/2-networking-providers.tf ./
      gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./
      gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./
      gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./
    fi

    handle_prompt "Would you like to perform the terraform init?" "terraform init" || true

    # Check for existing projects to import
    if gcloud projects describe "${PREFIX}-net-vdss-host" >/dev/null 2>&1; then
      log_info "Project ${PREFIX}-net-vdss-host already exists."
      if handle_prompt_if "Would you like to import it into Terraform state?"; then
        if terraform state list | grep -q "module.vdss-host-project.google_project.project\[0\]"; then
            log_info "Removing module.vdss-host-project.google_project.project[0] from state to force re-import..."
            terraform state rm module.vdss-host-project.google_project.project[0] || true
        fi
        log_info "Importing ${PREFIX}-net-vdss-host..."
        terraform import module.vdss-host-project.google_project.project[0] "${PREFIX}-net-vdss-host" || true
      fi
    fi

    # Check for existing VPCs
    for vpc in "vdss-dmz-0" "vdss-landing-0"; do
      if gcloud compute networks describe "$vpc" --project="${PREFIX}-net-vdss-host" >/dev/null 2>&1; then
         log_info "VPC $vpc already exists."
         if handle_prompt_if "Would you like to import $vpc?"; then
            # Map VPC name to module name
            module_name="dmz-vpc"
            if [[ "$vpc" == "vdss-landing-0" ]]; then module_name="vdss-vpc"; fi
            
            if terraform state list | grep -q "module.${module_name}.google_compute_network.network\[0\]"; then
                log_info "Removing module.${module_name}.google_compute_network.network[0] from state to force re-import..."
                terraform state rm "module.${module_name}.google_compute_network.network[0]" || true
            fi
            terraform import module.${module_name}.google_compute_network.network[0] "${PREFIX}-net-vdss-host/${vpc}" || true
         fi
      fi
    done

    if handle_prompt_if "Would you like to perform the terraform apply?"; then
      apply_success=false
      max_attempts=3
      attempt=1

      while [[ $attempt -le $max_attempts ]] && [[ "$apply_success" == "false" ]]; do
        log_info "Terraform apply attempt $attempt/$max_attempts"

        if terraform apply -auto-approve; then
          apply_success=true
          log_info "Terraform apply completed successfully"
        else
          if [[ $attempt -lt $max_attempts ]]; then
            # Check if it's a peering error (common timing issue)
            if terraform show 2>/dev/null | grep -q "peering\|network" || [[ -f .terraform.tfstate.backup ]]; then
              log_warn "Terraform apply failed, likely due to network peering timing issues"
              log_info "Waiting 60 seconds for network operations to settle..."
              sleep 60
              ((attempt++))
            else
              log_warn "Terraform apply failed with non-peering error"
              # Potential Service Account/KMS bugs
              echo 'If you receive an error relating to a service account not existing, please click "Settings" in gcs within the project, and it will generate the service account for you.'
              if handle_prompt_if "Would you like to retry the apply (attempt $((attempt+1))/$max_attempts)?"; then
                ((attempt++))
              else
                break
              fi
            fi
          else
            log_error "Terraform apply failed after $max_attempts attempts"
            if handle_prompt_if "Would you like to try one more manual attempt?"; then
              terraform apply -auto-approve && apply_success=true
            fi
            break
          fi
        fi
      done

      if [[ "$apply_success" == "false" ]]; then
        log_error "Unable to complete terraform apply. You may need to investigate manually."
        exit 1
      fi
    fi

  ########### IL4/IL5 ###########
  elif [ "$choice" == 3 ]; then
    echo "You have selected IL5"
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-b-il5-ngfw || exit

    # cmd=("./pre-redeploy.sh")
    # handle_prompt "If this is a redeployment (<30 days), would you like to run the redeploy script?" "${cmd[@]}"

    if handle_prompt_if "Would you like to pull the remote tfvars files created in Stages 0 and 1?"; then
      gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/providers/2-networking-providers.tf ./
      gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./
      gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./
      gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./
    fi

    handle_prompt "Would you like to perform the terraform init?" "terraform init" || true

    cmd=("terraform apply -auto-approve -target google_project_iam_custom_role.ngfw-custom-role")
    handle_prompt "Would you like to perform the targeted terraform apply?" "${cmd[@]}" || true

    if handle_prompt_if "Would you like to perform the full terraform apply?"; then
      apply_success=false
      max_attempts=3
      attempt=1

      while [[ $attempt -le $max_attempts ]] && [[ "$apply_success" == "false" ]]; do
        log_info "Terraform apply attempt $attempt/$max_attempts"

        if terraform apply -auto-approve; then
          apply_success=true
          log_info "Terraform apply completed successfully"
        else
          if [[ $attempt -lt $max_attempts ]]; then
            # Check if it's a peering error (common timing issue)
            if terraform show 2>/dev/null | grep -q "peering\|network" || [[ -f .terraform.tfstate.backup ]]; then
              log_warn "Terraform apply failed, likely due to network peering timing issues"
              log_info "Waiting 60 seconds for network operations to settle..."
              sleep 60
              ((attempt++))
            else
              log_warn "Terraform apply failed with non-peering error"
              # Potential Service Account/KMS bugs
              echo 'If you receive an error relating to a service account not existing, please click "Settings" in gcs within the project, and it will generate the service account for you.'
              if handle_prompt_if "Would you like to retry the apply (attempt $((attempt+1))/$max_attempts)?"; then
                ((attempt++))
              else
                break
              fi
            fi
          else
            log_error "Terraform apply failed after $max_attempts attempts"
            if handle_prompt_if "Would you like to try one more manual attempt?"; then
              terraform apply -auto-approve && apply_success=true
            fi
            break
          fi
        fi
      done

      if [[ "$apply_success" == "false" ]]; then
        log_error "Unable to complete terraform apply. You may need to investigate manually."
        exit 1
      fi
    fi
  fi

  echo "Congratulations, you have completed Stage 2!"
fi

########### Stage 3 - Security ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 3 - Security -"; then
  # Ensure we are in the correct project context (Automation Project)
  gcloud config set project "${PREFIX}-prod-iac-core-0" || true

  cd "${SCRIPT_DIR}"/../fast/stages-aw/3-security || exit

  # Add external billing account
  if handle_prompt_if "Would you like to provide billing account admin permissions for ${PREFIX}-security-0@${PREFIX}-prod-iac-core-0.iam.gserviceaccount.com?"; then
    gcloud billing accounts add-iam-policy-binding "${BILLING_ACCOUNT}" --member=serviceAccount:"${PREFIX}"-security-0@"${PREFIX}"-prod-iac-core-0.iam.gserviceaccount.com  --role=roles/billing.admin
  fi

  if handle_prompt_if "Would you like to pull the remote tfvars files created in Stages 0 and 1?"; then
    gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/providers/3-security-providers.tf ./
    gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./
  fi

    handle_prompt "Would you like to perform the terraform init?" "terraform init" || true

    if handle_prompt_if "Would you like to perform the terraform apply?"; then
      if terraform apply -auto-approve; then
        log_info "Terraform apply completed successfully"
      else
        log_warn "Terraform apply failed"

        # Check for KMS service account errors
        terraform_output=$(terraform plan 2>&1 || true)
        if echo "$terraform_output" | grep -q "gcp-sa-cloudkms.iam.gserviceaccount.com does not exist"; then
          log_warn "Detected missing KMS service account(s)"

          # Extract project IDs from error
          missing_projects=$(echo "$terraform_output" | grep -o 'service-[0-9]\+@gcp-sa-cloudkms' | sed 's/service-//' | sed 's/@gcp-sa-cloudkms//' | sort -u)

          if [[ -n "$missing_projects" ]]; then
            log_info "Projects with missing KMS service accounts: $missing_projects"
            if handle_prompt_if "Would you like to recreate the KMS service accounts by toggling the API?"; then
              for project_num in $missing_projects; do
                # Find project ID from project number
                project_id=$(gcloud projects list --filter="projectNumber:$project_num" --format="value(projectId)" 2>/dev/null || echo "")

                if [[ -n "$project_id" ]]; then
                  log_info "Recreating KMS service account for $project_id (project number: $project_num)"
                  gcloud services disable cloudkms.googleapis.com --project="$project_id" --force 2>/dev/null || true
                  sleep 5
                  gcloud services enable cloudkms.googleapis.com --project="$project_id"
                  log_info "Waiting 30 seconds for service account propagation..."
                  sleep 30
                else
                  log_warn "Could not find project ID for project number: $project_num"
                fi
              done

              log_info "Retrying terraform apply after KMS service account recreation..."
              if ! terraform apply -auto-approve; then
                log_error "Terraform apply still failed after KMS service account fix"
              else
                log_info "Terraform apply completed successfully after KMS fix"
              fi
            fi
          fi
        else
          echo -e "\nIf you receive an error relating to a service account, please rerun the apply."
          if handle_prompt_if "Would you like to rerun the apply due to the above error?"; then
            terraform apply -auto-approve
          fi
        fi
      fi
    fi

    handle_prompt "Would you like to run the lockdown script?" "./sa_lockdown.sh" || true

    # handle_prompt "Would you like to delete the bootstrap project?" "./delete_gcp_project.sh --project-id=${BOOTSTRAP_PROJECT_ID}"

    echo "Congratulations, you have finished Stage 3! Please see the SBPG linked below for further hardening."
    echo 'https://docs.google.com/document/d/1uv62Fqg73r9oJNP-NPZebpzoBom8rOgLoHkiMZPutbo/edit?usp=drive_link'
fi
