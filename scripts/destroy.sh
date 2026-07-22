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

# Trap to kill background jobs on exit/interrupt
cleanup_background_jobs() {
  local pids
  pids=$(jobs -p)
  if [[ -n "$pids" ]]; then
    echo "Stopping background jobs..."
    kill $pids 2>/dev/null || true
    wait $pids 2>/dev/null || true
  fi
}
trap cleanup_background_jobs EXIT INT TERM

# Source common functions
if [[ -f "${SCRIPT_DIR}/common-functions.sh" ]]; then
    # shellcheck source=experimental/common-functions.sh
    source "${SCRIPT_DIR}/common-functions.sh"
else
    # Fallback logging if common functions not available
    log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
    log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
    log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }
    # Fallback for gcloud_safe - just run gcloud directly
    gcloud_safe() { gcloud "$@"; }
    safe_delete() { log_warn "safe_delete not available without common-functions.sh"; return 1; }
fi

setup_logging

# Enhanced error handler with cleanup
error_handler() {
    local line_no=$1
    local exit_code=$?
    log_error "Script failed at line $line_no with exit code $exit_code"
    log_info "You may need to run clean.sh to complete cleanup"

    # Attempt to save current state
    if [[ -n "${PREFIX:-}" ]]; then
        local state_dir="${SCRIPT_DIR}/state"
        mkdir -p "$state_dir"
        echo "LAST_FAILED_OPERATION=destroy" >> "${state_dir}/last_operation_${PREFIX}.env" 2>/dev/null || true
        echo "LAST_FAILED_LINE=$line_no" >> "${state_dir}/last_operation_${PREFIX}.env" 2>/dev/null || true
    fi

    cleanup
    exit "$exit_code"
}

# Note: error_handler is already defined above, no need for setup_error_handling
# Note: error_handler is already defined above, no need for setup_error_handling
trap 'error_handler $LINENO' ERR

# Function to mark stage as complete
mark_stage_complete() {
    local stage_id=$1
    log_info "Marking $stage_id as complete..."
    # Update current session variable
    eval "${stage_id}_DESTROYED=true"
    # Persist to file
    # Persist to file
    # Persist to file
    if [[ -n "${PREFIX:-}" ]]; then
        local state_dir="${SCRIPT_DIR}/state"
        mkdir -p "$state_dir"
        echo "${stage_id}_DESTROYED=true" >> "${state_dir}/last_operation_${PREFIX}.env"
    fi
}

# Load last operation state if available


# Helper function to wait for project deletion
# Helper function to wait for project deletion
# Helper function to wait for project deletion
wait_for_project_deletion() {
  local project_id="$1"
  local max_wait=60  # 5 minutes in 5-second intervals (increased for safety)
  local wait_count=0

  while [[ $wait_count -lt $max_wait ]]; do
    if ! gcloud projects describe "$project_id" >/dev/null 2>&1; then
      log_info "Project $project_id is now deleted (404)"
      return 0
    fi
    # Check status just in case, but we really need it to be gone for folder deletion
    local state
    state=$(gcloud projects describe "$project_id" --format="value(lifecycleState)" 2>/dev/null || echo "DELETED")
    
    if [[ "$state" == "DELETED" ]] || [[ "$state" == "DELETE_REQUESTED" ]]; then
       log_info "Project $project_id is in state $state - proceeding"
       return 0
    fi
    
    log_info "Project $project_id state: $state - waiting..."
    sleep 5
    ((wait_count++))
  done

  log_warn "Project $project_id still exists after waiting"
  return 1
}

# Recursive function to clean up folders
clean_folder_recursive() {
  local folder_id="$1"
  log_info "Cleaning up folder $folder_id..."

  # 1. Delete projects in this folder
  local projects
  projects=$(gcloud projects list --filter="parent.id=$folder_id" --format="value(projectId)" 2>/dev/null || echo "")
  
  if [[ -n "$projects" ]]; then
      log_info "Found projects in folder $folder_id: $(echo "$projects" | tr '\n' ' ')"
      local pids=()
      local log_files=()
      for project in $projects; do
        local log_file=$(mktemp)
        log_files+=("$log_file")
        (
          {
            # Remove liens
            gcloud_safe alpha resource-manager liens list --project="$project" --format="value(name)" 2>/dev/null | while read -r lien; do
              if [[ -n "$lien" ]]; then
                log_info "Removing lien $lien from project $project"
                gcloud_safe alpha resource-manager liens delete "$lien" || true
              fi
            done
            # Unlink billing
            gcloud_safe billing projects unlink "$project" 2>/dev/null || true
            # Delete project
            if ! gcloud_safe projects delete "$project" --quiet; then
              log_warn "Failed to delete project $project - checking if already deleted..."
              if gcloud projects describe "$project" >/dev/null 2>&1; then
                  log_error "Project $project still exists and could not be deleted"
              else
                  log_info "Project $project appears to be deleted already"
              fi
            else
                wait_for_project_deletion "$project"
            fi
          } > "$log_file" 2>&1
        ) &
        pids+=($!)
      done
      
      # Wait for all project deletions to complete
      log_info "Waiting for parallel project deletions in $folder_id..."
      for i in "${!pids[@]}"; do
        wait "${pids[$i]}"
        cat "${log_files[$i]}"
        rm -f "${log_files[$i]}"
      done
  else
      log_info "No projects found in folder $folder_id"
  fi

  # 2. Recurse into sub-folders (PARALLEL)
  local subfolders
  subfolders=$(gcloud resource-manager folders list --folder="$folder_id" --format="value(name)" 2>/dev/null || echo "")
  
  if [[ -n "$subfolders" ]]; then
      log_info "Found subfolders in folder $folder_id: $(echo "$subfolders" | tr '\n' ' ')"
      local folder_pids=()
      local folder_log_files=()
      for subfolder in $subfolders; do
        local subfolder_id=${subfolder##*/}
        local log_file=$(mktemp)
        folder_log_files+=("$log_file")
        ( clean_folder_recursive "$subfolder_id" > "$log_file" 2>&1 ) &
        folder_pids+=($!)
      done
      
      log_info "Waiting for subfolder cleanups in $folder_id..."
      for i in "${!folder_pids[@]}"; do
        wait "${folder_pids[$i]}"
        cat "${folder_log_files[$i]}"
        rm -f "${folder_log_files[$i]}"
      done
  else
      log_info "No subfolders found in folder $folder_id"
  fi

  # 3. Try to delete the folder itself with retries
  local max_folder_attempts=6
  local folder_attempt=1
  
  while [[ $folder_attempt -le $max_folder_attempts ]]; do
      if gcloud_safe resource-manager folders delete "$folder_id" --quiet 2>/dev/null; then
          log_info "Folder $folder_id deleted successfully"
          break
      else
          log_warn "Attempt $folder_attempt to delete folder $folder_id failed (likely waiting for projects to fully vanish). Retrying in 10s..."
          
          # If this is the last attempt, check what's blocking it
          if [[ $folder_attempt -eq $max_folder_attempts ]]; then
              log_error "Could not delete folder $folder_id after retries."
              # Verify if it's really empty
              if gcloud projects list --filter="parent.id=$folder_id" --format="value(projectId)" --limit=1 2>/dev/null | grep -q .; then
                 log_error "Folder $folder_id is still not empty (projects remain)"
              elif gcloud resource-manager folders list --folder="$folder_id" --format="value(name)" --limit=1 2>/dev/null | grep -q .; then
                 log_error "Folder $folder_id is still not empty (subfolders remain)"
              fi
          else
              sleep 10
          fi
      fi
      ((folder_attempt++))
  done
}


# Improved prompt function with better error handling
promptUser() {
    local prompt="$1"
    shift
    local commands=("$@")

    while true; do
        echo
        log_warn "DESTRUCTIVE OPERATION: $prompt"
        echo "Please choose: [y]es / [n]o / [s]kip"
        read -r choice

        case "$choice" in
            [Yy]|[Yy][Ee][Ss])
                log_info "Executing commands..."
                for cmd in "${commands[@]}"; do
                    log_info "Running: $cmd"
                    if ! bash -c "$cmd"; then
                        log_error "Command failed: $cmd"
                        echo "Continue anyway? [y/N]"
                        read -r continue_choice
                        if [[ ! "$continue_choice" =~ ^[Yy] ]]; then
                            log_error "User chose not to continue. Exiting."
                            exit 1
                        fi
                    fi
                done
                return 0
                ;;
            [Nn]|[Nn][Oo])
                log_warn "Skipping: $prompt"
                return 1
                ;;
            [Ss]|[Ss][Kk][Ii][Pp])
                log_warn "Skipping: $prompt"
                return 255
                ;;
            *)
                log_error "Invalid choice. Please enter y, n, or s."
                ;;
        esac
    done
}

########### DANGER: DESTRUCTIVE OPERATIONS ############
log_warn "=== WARNING: DESTRUCTIVE SCRIPT ==="
log_warn "This script will DELETE your ENTIRE environment!"
log_warn "This includes all projects, resources, and local .terraform directories!"
echo
log_warn "Please ensure you have:"
echo "  • Backed up any important data"
echo "  • Confirmed this is the correct environment to destroy"
echo "  • Run any necessary export/backup scripts"
echo

if ! promptUser "Do you want to proceed with DESTROYING the entire environment?"; then
    log_info "Destruction cancelled by user. Exiting safely."
    exit 0
fi

# Load configuration
# Load configuration
if [ ! -f "$SCRIPT_DIR"/config.env ]; then
    log_warn "config.env file not found."
    if promptUser "Would you like to pull config.env from a previous deployment (requires knowing the prefix)?"; then
        read -r -p "Enter the prefix of the deployment: " INPUT_PREFIX
        if [[ -n "$INPUT_PREFIX" ]]; then
            # Try to find the bucket
            if gcloud storage ls "gs://${INPUT_PREFIX}-prod-iac-core-outputs-0/config.env" &>/dev/null; then
                gcloud storage cp "gs://${INPUT_PREFIX}-prod-iac-core-outputs-0/config.env" "$SCRIPT_DIR/"
                log_info "Successfully pulled config.env"
            else
                log_error "Could not find config.env in gs://${INPUT_PREFIX}-prod-iac-core-outputs-0/"
            fi
        fi
    fi
fi

if [ ! -f "$SCRIPT_DIR"/config.env ]; then
    log_warn "No config.env found. You will need to enter details manually."
fi

# Interactive Config Setup/Update
if [ ! -f "$SCRIPT_DIR"/config.env ] || promptUser "Would you like to update/overwrite your config.env file?"; then
    # Load existing values if available
    if [ -f "$SCRIPT_DIR"/config.env ]; then
        source "$SCRIPT_DIR"/config.env
    fi

    gcloud organizations list

    # Function to prompt with default
    prompt_val() {
        local var_name=$1
        local prompt_text=$2
        local current_val=${!var_name}
        
        if [[ -n "$current_val" ]]; then
            read -r -p "$prompt_text [$current_val]: " input
            if [[ -n "$input" ]]; then
                eval "$var_name=\"$input\""
            fi
        else
            read -r -p "$prompt_text: " input
            eval "$var_name=\"$input\""
        fi
    }

    prompt_val "BILLING_ACCOUNT" "Enter your billing account"
    prompt_val "BOOTSTRAP_PROJECT_ID" "Enter your bootstrap project ID"
    prompt_val "COMPLIANCE_REGIME" "Enter the compliance regime"
    prompt_val "DIRECTORY_CUSTOMER_ID" "Enter your directory customer ID"
    prompt_val "DEPLOYER_EMAIL_ADDRESS" "Enter your deployer email address"
    prompt_val "FULLY_QUALIFIED_DOMAIN_NAME" "Enter your fully qualified domain name"
    prompt_val "LOGGING_ALERTS_EMAIL_ADDRESS" "Enter your logging alerts email address"
    prompt_val "ORGANIZATION_ID" "Enter your organization ID"
    prompt_val "PREFIX" "Enter your prefix"
    prompt_val "REGION" "Enter your region"
    prompt_val "AW_REGION" "Enter your Assured Workload region"
    prompt_val "TENANT_NAME" "Enter your tenant name"

    echo "--- Configuration Summary ---"
    echo "billing-account: $BILLING_ACCOUNT"
    echo "bootstrap-project-id: $BOOTSTRAP_PROJECT_ID"
    echo "compliance-regime: $COMPLIANCE_REGIME"
    echo "directory-customer-id: $DIRECTORY_CUSTOMER_ID"
    echo "deployer-email-address: $DEPLOYER_EMAIL_ADDRESS"
    echo "fully-qualified-domain-name: $FULLY_QUALIFIED_DOMAIN_NAME"
    echo "logging-alerts-email-address: $LOGGING_ALERTS_EMAIL_ADDRESS"
    echo "organization-id: $ORGANIZATION_ID"
    echo "prefix: $PREFIX"
    echo "region: $REGION"
    echo "aw-region: $AW_REGION"
    echo "tenant-name: $TENANT_NAME"

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
      echo "AW_REGION=$AW_REGION"
      echo "TENANT_NAME=$TENANT_NAME"
    } > "$SCRIPT_DIR"/config.env
else
    # shellcheck source=experimental/config.env.sample
    if ! source "$SCRIPT_DIR"/config.env; then
        log_error "Failed to source config.env file"
        exit 1
    fi

    log_info "Current configuration:"
    echo "------------------------------------------------------------------"
    cat config.env
    echo "------------------------------------------------------------------"

    # Validate critical variables exist
    if [[ -z "${PREFIX:-}" ]] || [[ -z "${ORGANIZATION_ID:-}" ]] || [[ -z "${BILLING_ACCOUNT:-}" ]]; then
        log_error "Missing critical variables in config.env (PREFIX, ORGANIZATION_ID, or BILLING_ACCOUNT)"
        exit 1
    fi
fi

# Load previous state if available
state_file="${SCRIPT_DIR}/state/last_operation_${PREFIX}.env"

if [[ -f "$state_file" ]]; then
    if promptUser "Found previous destroy state for prefix '${PREFIX}'. Resume from last successful stage?"; then
        log_info "Resuming from previous state..."
        source "$state_file"
    else
        log_info "Archiving previous state and starting fresh..."
        timestamp=$(date +"%Y%m%d_%H%M%S")
        # Ensure logs directory exists (it should be created by setup_logging, but just in case)
        mkdir -p "${SCRIPT_DIR}/../logs"
        mv "$state_file" "${SCRIPT_DIR}/../logs/last_operation_${PREFIX}_${timestamp}.env"
    fi
fi

# Prefix Safety Check
log_info "Performing safety checks..."
# Check for state files with mismatched prefixes
mismatched_states=$(find . -name "terraform.tfstate" -exec grep -l "prod-iac-core" {} \; | xargs -r grep -L "${PREFIX}-prod-iac-core" 2>/dev/null || echo "")
if [[ -n "$mismatched_states" ]]; then
    log_warn "WARNING: Found terraform state files that do NOT match current prefix '${PREFIX}':"
    echo "$mismatched_states"
    if ! promptUser "Are you SURE you want to proceed? (These states might belong to another deployment)"; then
        log_info "Aborting destruction."
        exit 1
    fi
else
    log_info "Prefix check passed: No mismatched state files found."
fi

if promptUser "Would you like to reauthenticate?"; then
  if [[ -n "${DEPLOYER_EMAIL_ADDRESS:-}" ]]; then
      gcloud auth revoke "${DEPLOYER_EMAIL_ADDRESS}" || log_warn "Failed to revoke auth for ${DEPLOYER_EMAIL_ADDRESS}"
  fi
  gcloud auth login
  gcloud auth application-default login
fi


########### Stage 3 - Security ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if [[ "${STAGE_3_DESTROYED:-}" == "true" ]]; then
  if promptUser "Stage 3 appears to be successfully completed. Skip?"; then
      log_info "Skipping Stage 3 (already destroyed)"
      skip_stage_3=true
  fi
fi

if [[ "${skip_stage_3:-}" != "true" ]] && promptUser "Stage 3 - Security"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/3-security || exit

  if promptUser "Would you like to set your default project to ${PREFIX}-prod-iac-core-0?"; then
    if gcloud config set project "${PREFIX}-prod-iac-core-0"; then
      log_info "Default project set to ${PREFIX}-prod-iac-core-0"

      # Set the quota project to match to avoid quota issues
      log_info "Setting Application Default Credentials quota project to match..."
      if gcloud auth application-default set-quota-project "${PREFIX}-prod-iac-core-0" 2>/dev/null; then
        log_info "Quota project updated successfully"
      else
        log_warn "Could not update quota project - you may encounter quota issues"
      fi
    else
      log_warn "Failed to set default project, but continuing with destruction"
    fi
  fi

  if promptUser "Would you like to disable org policies to allow for deletion?"; then
    # Use safe deletion for custom constraint
    safe_delete "custom-constraint" "custom.kmsRotation${PREFIX}" --organization="${ORGANIZATION_ID}" || log_warn "Custom constraint may not exist or already deleted"

    # Disable org policy with retry mechanism
    if ! gcloud_safe resource-manager org-policies disable-enforce compute.requireOsLogin --organization="${ORGANIZATION_ID}"; then
      log_warn "Failed to disable compute.requireOsLogin policy, continuing anyway"
    fi

    log_info "Waiting 60 seconds for policy changes..."; sleep 60
  fi

  # Pull config if missing
  missing_files=()
  [[ ! -f "0-globals.auto.tfvars.json" ]] && missing_files+=("0-globals.auto.tfvars.json")
  [[ ! -f "3-security-providers.tf" ]] && missing_files+=("3-security-providers.tf")

  if [[ ${#missing_files[@]} -gt 0 ]]; then
      log_warn "The following config files are missing: ${missing_files[*]}"
      if promptUser "Attempt to pull from GCS?"; then
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/providers/3-security-providers.tf" ./ 2>/dev/null || log_warn "Failed to pull providers"
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull globals"
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull bootstrap vars"
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull resman vars"
      fi
  fi

  if promptUser "Would you like to restore your bootstrap project if it was deleted?"; then
    # Check project state before attempting undelete
    PROJECT_STATE=$(gcloud projects describe "${BOOTSTRAP_PROJECT_ID}" --format="value(lifecycleState)" 2>/dev/null)
    if [[ "$PROJECT_STATE" == "DELETE_REQUESTED" ]]; then
      gcloud projects undelete "${BOOTSTRAP_PROJECT_ID}"
      sleep 60
      gcloud billing projects link "${BOOTSTRAP_PROJECT_ID}" --billing-account="${BILLING_ACCOUNT}"
    elif [[ "$PROJECT_STATE" == "ACTIVE" ]]; then
      log_info "Project ${BOOTSTRAP_PROJECT_ID} is already ACTIVE, skipping undelete."
    else
      log_warn "Project ${BOOTSTRAP_PROJECT_ID} is in state ${PROJECT_STATE}, cannot undelete."
    fi
  fi

  if promptUser "Would you like to reenable disabled Service Accounts?"; then
    if [[ -x "./sa_lockdown.sh" ]]; then
      ./sa_lockdown.sh --enable
      sleep 30
    else
      log_warn "sa_lockdown.sh not found or not executable in $(pwd)"
    fi
  fi
  
  if promptUser "Would you like to run terraform destroy?"; then
    if ! terraform destroy -auto-approve; then
      log_error "Terraform destroy failed, but continuing with cleanup"
    fi
  fi

  if promptUser "Would you like to delete your .terraform dir and related files?"; then
    # Comprehensive terraform cleanup for stage 3
    if [[ -d ".terraform" ]]; then
      rm -rf .terraform
      log_info "Deleted .terraform directory"
    else
      log_warn ".terraform directory does not exist"
    fi

    # Remove terraform lock file
    if [[ -f ".terraform.lock.hcl" ]]; then
      rm -f .terraform.lock.hcl
      log_info "Deleted .terraform.lock.hcl"
    else
      log_warn ".terraform.lock.hcl does not exist"
    fi

    # Remove any backup state files
    if [[ -f "terraform.tfstate.backup" ]]; then
      rm -f terraform.tfstate.backup
      log_info "Deleted terraform.tfstate.backup"
    fi
  fi

  if promptUser "Would you like to remove billing account admin permissions for ${PREFIX}-security-0@${PREFIX}-prod-iac-core-0.iam.gserviceaccount.com?"; then
    if ! gcloud_safe billing accounts remove-iam-policy-binding "${BILLING_ACCOUNT}" \
      --member="serviceAccount:${PREFIX}-security-0@${PREFIX}-prod-iac-core-0.iam.gserviceaccount.com" \
      --role=roles/billing.admin; then
      log_warn "Failed to remove billing permissions, but continuing"
    fi
  fi

  mark_stage_complete "STAGE_3"
fi
########## Stage 2 - Networking ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if [[ "${STAGE_2_DESTROYED:-}" == "true" ]]; then
  if promptUser "Stage 2 appears to be successfully completed. Skip?"; then
      log_info "Skipping Stage 2 (already destroyed)"
      skip_stage_2=true
  fi
fi

if [[ "${skip_stage_2:-}" != "true" ]] && promptUser "Stage 2 - Networking"; then
  # Choose networking paradigm
  echo "Please type \"1\", \"2\", or \"3\" below that corresponds to the network paradigm you want: "
  echo "1) IL2/FedRAMP Moderate"
  echo "2) FedRAMP High"
  echo "3) IL4/IL5"
  read -r choice

  ########### IL2/FedRAMP Moderate ###########
  if [ "$choice" == 1 ]; then
    echo "This stage is still under development."

  ########### FedRAMP High ###########
  elif [ "$choice" == 2 ]; then
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-a-fedramp-high || exit

    # Pull config if missing
    missing_files=()
    [[ ! -f "0-globals.auto.tfvars.json" ]] && missing_files+=("0-globals.auto.tfvars.json")
    [[ ! -f "2-networking-providers.tf" ]] && missing_files+=("2-networking-providers.tf")

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_warn "The following config files are missing: ${missing_files[*]}"
        if promptUser "Attempt to pull from GCS?"; then
            gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/providers/2-networking-providers.tf" ./ 2>/dev/null || log_warn "Failed to pull providers"
            gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull globals"
            gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull bootstrap vars"
            gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull resman vars"
        fi
    fi

    if promptUser "Would you like to run terraform destroy?"; then
      # Ensure backend is initialized before destroy
      log_info "Initializing Terraform for Stage 2..."
      terraform init -reconfigure
      destroy_success=false
      max_attempts=3
      attempt=1

      while [[ $attempt -le $max_attempts ]] && [[ "$destroy_success" == "false" ]]; do
        log_info "Terraform destroy attempt $attempt/$max_attempts"

        if terraform destroy -auto-approve; then
          destroy_success=true
          log_info "Terraform destroy completed successfully"
        else
          if [[ $attempt -lt $max_attempts ]]; then
            log_warn "Terraform destroy failed, checking for common issues..."

            # Check for peering errors (common during network destruction)
            if terraform show 2>/dev/null | grep -q "peering\|network" || [[ -f .terraform.tfstate.backup ]]; then
              log_warn "Likely network peering timing issues, waiting for resources to settle..."
              log_info "Waiting 60 seconds for network resource deletion..."; sleep 60
              ((attempt++))
            else
              log_warn "Terraform destroy failed with non-peering error"
              if promptUser "Would you like to retry destroy (attempt $((attempt+1))/$max_attempts)?"; then
                ((attempt++))
              else
                break
              fi
            fi
          else
            log_error "Terraform destroy failed after $max_attempts attempts"
            if promptUser "Would you like to try one more manual attempt?"; then
              terraform destroy -auto-approve && destroy_success=true
            fi
            break
          fi
        fi
      done

      if [[ "$destroy_success" == "false" ]]; then
        log_error "Unable to complete terraform destroy. Manual cleanup may be required."
      fi
    fi

    if promptUser "Would you like to delete your .terraform dir and related files?"; then
      # Comprehensive terraform cleanup for stage 2 - FedRAMP High
      if [[ -d ".terraform" ]]; then
        rm -rf .terraform
        log_info "Deleted .terraform directory"
      else
        log_warn ".terraform directory does not exist"
      fi

      # Remove terraform lock file
      if [[ -f ".terraform.lock.hcl" ]]; then
        rm -f .terraform.lock.hcl
        log_info "Deleted .terraform.lock.hcl"
      else
        log_warn ".terraform.lock.hcl does not exist"
      fi

      # Remove any backup state files
      if [[ -f "terraform.tfstate.backup" ]]; then
        rm -f terraform.tfstate.backup
        log_info "Deleted terraform.tfstate.backup"
      fi
    fi

  ########### IL4/IL5 ###########
  elif [ "$choice" == 3 ]; then
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-b-il5-ngfw || exit

    # Pull config if missing
    missing_files=()
    [[ ! -f "0-globals.auto.tfvars.json" ]] && missing_files+=("0-globals.auto.tfvars.json")
    [[ ! -f "2-networking-providers.tf" ]] && missing_files+=("2-networking-providers.tf")

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_warn "The following config files are missing: ${missing_files[*]}"
        if promptUser "Attempt to pull from GCS?"; then
            gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/providers/2-networking-providers.tf" ./ 2>/dev/null || log_warn "Failed to pull providers"
            gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull globals"
            gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull bootstrap vars"
            gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull resman vars"
        fi
    fi

    if promptUser "Would you like to run terraform destroy?"; then
      destroy_success=false
      max_attempts=3
      attempt=1

      while [[ $attempt -le $max_attempts ]] && [[ "$destroy_success" == "false" ]]; do
        log_info "Terraform destroy attempt $attempt/$max_attempts"

        if terraform destroy; then
          destroy_success=true
          log_info "Terraform destroy completed successfully"
        else
          if [[ $attempt -lt $max_attempts ]]; then
            log_warn "Terraform destroy failed, checking for common issues..."

            # Check for peering errors (common during network destruction)
            if terraform show 2>/dev/null | grep -q "peering\|network" || [[ -f .terraform.tfstate.backup ]]; then
              log_warn "Likely network peering timing issues, waiting for resources to settle..."
              log_info "Waiting 60 seconds for network resource deletion..."; sleep 60
              ((attempt++))
            else
              log_warn "Terraform destroy failed with non-peering error"
              if promptUser "Would you like to retry destroy (attempt $((attempt+1))/$max_attempts)?"; then
                ((attempt++))
              else
                break
              fi
            fi
          else
            log_error "Terraform destroy failed after $max_attempts attempts"
            if promptUser "Would you like to try one more manual attempt?"; then
              terraform destroy && destroy_success=true
            fi
            break
          fi
        fi
      done

      if [[ "$destroy_success" == "false" ]]; then
        log_error "Unable to complete terraform destroy. Manual cleanup may be required."
      fi
    fi

    if promptUser "Would you like to delete your .terraform dir and related files?"; then
      # Comprehensive terraform cleanup for stage 2 - IL4/IL5
      if [[ -d ".terraform" ]]; then
        rm -rf .terraform
        log_info "Deleted .terraform directory"
      else
        log_warn ".terraform directory does not exist"
      fi

      # Remove terraform lock file
      if [[ -f ".terraform.lock.hcl" ]]; then
        rm -f .terraform.lock.hcl
        log_info "Deleted .terraform.lock.hcl"
      else
        log_warn ".terraform.lock.hcl does not exist"
      fi

      # Remove any backup state files
      if [[ -f "terraform.tfstate.backup" ]]; then
        rm -f terraform.tfstate.backup
        log_info "Deleted terraform.tfstate.backup"
      fi
    fi
  fi
  
  if promptUser "Would you like to remove billing account admin permissions for the ${PREFIX}-prod-resman-net-0@${PREFIX}-prod-iac-core-0.iam.gserviceaccount.com?"; then
    if ! gcloud billing accounts remove-iam-policy-binding "${BILLING_ACCOUNT}" --member=serviceAccount:"${PREFIX}"-prod-resman-net-0@"${PREFIX}"-prod-iac-core-0.iam.gserviceaccount.com --role=roles/billing.admin; then
        log_warn "Failed to remove billing permissions (likely already removed), continuing..."
    fi
  fi
  mark_stage_complete "STAGE_2"
fi

########### Stage 1 - Resman ############
echo
echo "#######################################################"
echo "#######################################################"
echo "#######################################################"

if [[ "${STAGE_1_DESTROYED:-}" == "true" ]]; then
  if promptUser "Stage 1 appears to be successfully completed. Skip?"; then
      log_info "Skipping Stage 1 (already destroyed)"
      skip_stage_1=true
  fi
fi

if [[ "${skip_stage_1:-}" != "true" ]] && promptUser "Stage 1 - Resource Manager"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/1-resman || exit

  # Pull config if missing
  missing_files=()
  [[ ! -f "terraform.tfvars" ]] && missing_files+=("terraform.tfvars")
  [[ ! -f "0-globals.auto.tfvars.json" ]] && missing_files+=("0-globals.auto.tfvars.json")
  [[ ! -f "1-resman-providers.tf" ]] && missing_files+=("1-resman-providers.tf")

  if [[ ${#missing_files[@]} -gt 0 ]]; then
      log_warn "The following config files are missing: ${missing_files[*]}"
      if promptUser "Attempt to pull from GCS?"; then
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/providers/1-resman-providers.tf" ./ 2>/dev/null || log_warn "Failed to pull providers"
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull globals"
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull bootstrap vars"
      fi
  fi

    destroy_success=false
    if promptUser "Would you like to run terraform destroy?"; then
        if ! terraform destroy -lock=false -auto-approve; then
             log_warn "Terraform destroy failed (likely due to non-empty buckets). Proceeding to cleanup..."
        else
             destroy_success=true
        fi
    fi

    # Post-destroy bucket cleanup
    log_info "Checking for remaining storage buckets using Terraform state..."
    tenant_buckets=""
    
    # Use terraform state to find buckets (more reliable than gcloud list across projects)
    # We look for google_storage_bucket resources
    if tf_buckets=$(terraform state list 2>/dev/null | grep "google_storage_bucket"); then
        for resource in $tf_buckets; do
            # Extract bucket name from state
            # We look for 'name = "bucket-name"' pattern
            if bucket_name=$(terraform state show -no-color "$resource" 2>/dev/null | grep -E "^\s*name\s+=" | awk -F'=' '{print $2}' | tr -d ' "'); then
                if [[ -n "$bucket_name" ]]; then
                    tenant_buckets+="gs://${bucket_name} "
                fi
            fi
        done
    fi

    buckets_deleted=false
    if [[ -n "$tenant_buckets" ]]; then
        log_warn "Found remaining storage buckets (likely non-empty): $tenant_buckets"
        if promptUser "Would you like to force delete these remaining buckets?"; then
            for bucket in $tenant_buckets; do
                log_info "Removing bucket: $bucket"
                # First, remove all objects inside the bucket (force removal)
                if ! gcloud_safe storage rm -r "${bucket}/**" 2>/dev/null; then
                    log_warn "No objects found in $bucket or removal failed, continuing..."
                fi
                # Then remove the empty bucket
                bucket_name=${bucket#gs://}
                if ! gcloud_safe storage buckets delete "gs://${bucket_name}"; then
                    log_warn "Failed to remove bucket $bucket, continuing..."
                else
                    buckets_deleted=true
                fi
            done
        fi
    else
        log_info "No remaining storage buckets found."
    fi

    if [[ "$buckets_deleted" == "true" ]]; then
        log_info "Buckets were deleted manually. Re-running terraform destroy to clean up state..."
        if terraform destroy -lock=false -auto-approve; then
             destroy_success=true
        else
             log_warn "Second terraform destroy failed, but buckets are gone."
        fi
    fi

    if promptUser "If you received an error for TagValues, would you like to delete all child tags?"; then
      read -r -p "Please enter the TagValue from the above error - numbers only" TAG
      gcloud resource-manager tags values delete tagValues/"${TAG}"
      terraform destroy -auto-approve
    fi

    if promptUser "Would you like to delete your .terraform dir and related files?"; then
      # Comprehensive terraform cleanup for stage 1
      if [[ -d ".terraform" ]]; then
        rm -rf .terraform
        log_info "Deleted .terraform directory"
      else
        log_warn ".terraform directory does not exist"
      fi

      # Remove terraform lock file
      if [[ -f ".terraform.lock.hcl" ]]; then
        rm -f .terraform.lock.hcl
        log_info "Deleted .terraform.lock.hcl"
      else
        log_warn ".terraform.lock.hcl does not exist"
      fi

      # Remove any backup state files
      if [[ -f "terraform.tfstate.backup" ]]; then
        rm -f terraform.tfstate.backup
        log_info "Deleted terraform.tfstate.backup"
      fi
    fi

    # Remove resman billing permissions
    if promptUser "Would you like to remove billing account admin permissions for ${PREFIX}-prod-resman-0@${PREFIX}-prod-iac-core-0.iam.gserviceaccount.com?"; then
      if ! gcloud_safe billing accounts remove-iam-policy-binding "${BILLING_ACCOUNT}" \
        --member="serviceAccount:${PREFIX}-prod-resman-0@${PREFIX}-prod-iac-core-0.iam.gserviceaccount.com" \
        --role=roles/billing.admin; then
        log_warn "Failed to remove resman billing permissions, but continuing"
      fi
    fi

    if [[ "$destroy_success" == "true" ]]; then
        mark_stage_complete "STAGE_1"
    else
        log_warn "Stage 1 destroy did not complete successfully. Not marking as complete."
    fi
fi

########### Stage 0 - Bootstrap ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 0 - Bootstrap"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/0-bootstrap || exit

  if promptUser "Would you like to set the bootstrap project as your default project?"; then
    gcloud config set project "${BOOTSTRAP_PROJECT_ID}"
  fi

  # Pull config if missing
  missing_files=()
  [[ ! -f "terraform.tfvars" ]] && missing_files+=("terraform.tfvars")
  [[ ! -f "0-globals.auto.tfvars.json" ]] && missing_files+=("0-globals.auto.tfvars.json")
  [[ ! -f "0-bootstrap-providers.tf" ]] && missing_files+=("0-bootstrap-providers.tf")

  if [[ ${#missing_files[@]} -gt 0 ]]; then
      log_warn "The following config files are missing: ${missing_files[*]}"
      if promptUser "Attempt to pull from GCS?"; then
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/providers/0-bootstrap-providers.tf" ./ 2>/dev/null || log_warn "Failed to pull providers"
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull globals"
          # Bootstrap might not have its own auto.tfvars in outputs, usually it uses terraform.tfvars or 0-bootstrap.auto.tfvars.json
          # But let's try to pull what we can
          gcloud storage cp "gs://${PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json" ./ 2>/dev/null || log_warn "Failed to pull bootstrap vars"
      fi
  fi

  # Smart Backend Detection
  log_info "Verifying bootstrap state configuration..."
  use_remote_backend=false

  if grep -q "backend.*gcs" 0-bootstrap-providers.tf 2>/dev/null; then
    log_info "Detected remote backend configuration in providers file"
    if promptUser "Attempt to destroy using REMOTE state - GCS?"; then
       if terraform init; then
         log_info "Successfully initialized with remote backend"
         use_remote_backend=true

         # Reverse State Migration Logic
         if promptUser "Would you like to migrate state back to LOCAL before destroy? (Recommended)"; then
            log_info "Migrating state back to local..."
            
            # Backup providers file
            cp 0-bootstrap-providers.tf 0-bootstrap-providers.tf.bak
            
            # Remove backend config
            # Assuming backend block is standard format: backend "gcs" { ... }
            sed -i.bak '/backend "gcs"/,/}/d' 0-bootstrap-providers.tf
            rm -f 0-bootstrap-providers.tf.bak
            
            if terraform init -migrate-state -force-copy; then
                log_info "Successfully migrated state back to local"
                rm -f 0-bootstrap-providers.tf.bak
                use_remote_backend=false
            else
                log_error "Failed to migrate state back to local"
                log_warn "Restoring providers file..."
                mv 0-bootstrap-providers.tf.bak 0-bootstrap-providers.tf
                log_warn "Continuing with remote backend..."
            fi
         fi
       else
         log_warn "Failed to initialize with remote backend"
       fi
    fi
  fi

  if [[ "$use_remote_backend" == "false" ]]; then
      log_info "Falling back to LOCAL state check..."
      if [[ -f "./terraform.tfstate" ]]; then
        log_info "✓ Found local terraform state file"
    # Clean up temporary backup files
    log_info "Cleaning up temporary backup files..."
    rm -f terraform.tfvars.*backup* 2>/dev/null || true

    # Clean up local terraform state

        # Verify providers are configured for local backend
        if grep -q "backend.*gcs" 0-bootstrap-providers.tf 2>/dev/null; then
          log_warn "Providers incorrectly configured for remote backend but using local state - fixing..."
          if [[ -f "providers.tf.tmp" ]]; then
            cp providers.tf.tmp 0-bootstrap-providers.tf
            log_info "Reverted providers to local backend configuration"
            terraform init -reconfigure
          else
            log_error "providers.tf.tmp not found - cannot revert providers"
            log_error "You may need to manually remove backend configuration from 0-bootstrap-providers.tf"
            exit 1
          fi
        else
          log_info "✓ Providers correctly configured for local backend"
        fi
      else
        log_error "❌ Local terraform.tfstate not found in $(pwd)"
        log_error "Bootstrap stage should use local state (if not migrated), but no state file exists"
        
        # Recovery logic for interrupted migration
        if [[ -f "providers.tf.tmp" ]]; then
             log_warn "Found providers.tf.tmp - this might indicate an interrupted migration or initial deployment."
             if promptUser "Would you like to restore providers.tf from providers.tf.tmp (local backend)?"; then
                  cp providers.tf.tmp 0-bootstrap-providers.tf
                  log_info "Restored 0-bootstrap-providers.tf from template"
             fi
        fi

        if promptUser "Do you want to continue anyway and try to destroy without state (or try remote init)?"; then
             log_warn "Attempting init..."
             terraform init -reconfigure
        else
             log_info "Exiting - please locate the terraform.tfstate file or confirm bootstrap was deployed"
             exit 1
        fi
      fi
  fi

  # CRITICAL: Always restore permissions before any destroy operations (no prompt)
  log_info "Restoring IAM permissions for destroy operations..."
  if [[ -f "${SCRIPT_DIR}/../fast/stages-aw/0-bootstrap/setIAM.sh" ]]; then
    iam_output=$("${SCRIPT_DIR}/../fast/stages-aw/0-bootstrap/setIAM.sh" "${DEPLOYER_EMAIL_ADDRESS}" "${ORGANIZATION_ID}" 2>&1)
    echo "$iam_output"
    
    if echo "$iam_output" | grep -q "No new roles to add"; then
      log_info "No new roles added, skipping propagation wait."
    else
      log_info "IAM permissions updated successfully"
      log_info "Waiting 120 seconds for IAM propagation..."; sleep 120
    fi

      # Verify critical permissions are in place
      log_info "Verifying critical permissions..."
      current_user=$(gcloud config list --format 'value(core.account)')
      required_roles=(
        "roles/resourcemanager.projectDeleter"
        "roles/resourcemanager.organizationAdmin"
        "roles/owner"
        "roles/assuredworkloads.admin"
      )

      missing_roles=()
      for role in "${required_roles[@]}"; do
        if ! gcloud organizations get-iam-policy "${ORGANIZATION_ID}" \
          --flatten="bindings[].members" \
          --filter="bindings.role:$role AND bindings.members:user:$current_user" \
          --format="value(bindings.role)" 2>/dev/null | grep -q "$role"; then
          missing_roles+=("$role")
        fi
      done

      if [[ ${#missing_roles[@]} -gt 0 ]]; then
        log_error "Missing critical permissions for destroy operations:"
        printf '%s\n' "${missing_roles[@]}"
        log_error "The destroy operation will likely fail without these permissions"
        if ! promptUser "Do you want to continue anyway?"; then
          exit 1
        fi
      else
        log_info "All critical permissions verified successfully"
      fi
    else
      log_error "Failed to restore IAM permissions"
      exit 1
    fi
  else
    log_error "setIAM.sh script not found at ${SCRIPT_DIR}/../fast/stages-aw/0-bootstrap/setIAM.sh"
    log_error "Cannot proceed without proper permissions"
    exit 1
  fi

  if promptUser "Would you like to run terraform destroy?"; then
    # Check if we have sufficient permissions for project deletion
    current_account=$(gcloud config list --format 'value(core.account)')
    log_info "Attempting terraform destroy with account: $current_account"

    # CRITICAL: Strip impersonation from providers.tf since the service account is likely deleted
    if [[ -f "0-bootstrap-providers.tf" ]]; then
        log_info "Removing impersonation from 0-bootstrap-providers.tf to avoid 'Account disabled' errors..."
        sed -i.bak '/impersonate_service_account/d' 0-bootstrap-providers.tf
        rm -f 0-bootstrap-providers.tf.bak

        # NEW: Check for GCS backend and pull state to ensure destruction works even if bucket is deleted
        # NEW: Check for GCS backend and pull state to ensure destruction works even if bucket is deleted
        if grep -q 'backend "gcs"' 0-bootstrap-providers.tf; then
             log_info "Detected GCS backend. Attempting to pull state locally to ensure destruction..."
             if terraform state pull > terraform.tfstate 2>/dev/null; then
                 log_info "State pulled successfully. Switching to local backend..."
                 # Create local backend config
cat > 0-bootstrap-providers.tf <<EOF
terraform {
  backend "local" {}
}
provider "google" {
  user_project_override = true
}
EOF
                 # Re-initialize to apply the backend change
                 log_info "Re-initializing terraform with local backend..."
                 terraform init -reconfigure >/dev/null 2>&1 || log_warn "Failed to re-initialize, destroy might fail"
             else
                 log_warn "Failed to pull state (bucket might be gone). Proceeding with existing config..."
             fi
        else
             # If no GCS backend found in file, but we are here, we might still need to re-init if previous run left it in bad state
             log_info "No GCS backend detected in providers file. Ensuring local backend..."
             
             # Force write local backend to be explicit
             cat > 0-bootstrap-providers.tf <<EOF
terraform {
  backend "local" {}
}
provider "google" {
  user_project_override = true
}
EOF
             log_info "Running terraform init -reconfigure (verbose)..."
             terraform init -reconfigure || log_warn "Init failed"
        fi
    fi


    # CRITICAL: Ensure ADC has a quota project set (required for Org Policy API)
    if [[ -n "${BOOTSTRAP_PROJECT_ID:-}" ]]; then
        log_info "Setting quota project to ${BOOTSTRAP_PROJECT_ID} for ADC to avoid 'SERVICE_DISABLED' errors..."
        gcloud auth application-default set-quota-project "${BOOTSTRAP_PROJECT_ID}" >/dev/null 2>&1 || log_warn "Failed to set quota project, you may need to set it manually if errors occur"
    fi

    if ! terraform destroy -auto-approve -var bootstrap_user="$current_account"; then
         log_warn "Terraform destroy failed. Proceeding to cleanup..."
    fi

    # Post-destroy bucket cleanup for Stage 0
    log_info "Checking for remaining Stage 0 buckets..."
    # List of Stage 0 buckets
    stage0_buckets=(
        "gs://${PREFIX}-prod-iac-core-outputs-0"
        "gs://${PREFIX}-prod-iac-core-bootstrap-0"
        "gs://${PREFIX}-prod-iac-core-resman-0"
        "gs://${PREFIX}-prod-audit-logs-0-logs"
    )
    
    buckets_deleted=false
    for bucket in "${stage0_buckets[@]}"; do
        if gcloud storage buckets describe "$bucket" --project="${PREFIX}-prod-iac-core-0" >/dev/null 2>&1; then
            log_warn "Found remaining bucket: $bucket"
            if promptUser "Would you like to force delete this bucket?"; then
                log_info "Removing bucket: $bucket"
                if ! gcloud_safe storage rm -r "${bucket}/**" 2>/dev/null; then
                     log_warn "No objects found or removal failed, continuing..."
                fi
                if ! gcloud_safe storage buckets delete "$bucket"; then
                     log_warn "Failed to remove bucket $bucket"
                else
                     buckets_deleted=true
                fi
            fi
        fi
    done

    if [[ "$buckets_deleted" == "true" ]]; then
        log_info "Buckets were deleted manually. Re-running terraform destroy..."
        terraform destroy -auto-approve -var bootstrap_user="$current_account" || log_warn "Second destroy failed"
    fi



    if ! terraform destroy -auto-approve -var bootstrap_user="$current_account"; then
      log_warn "Terraform destroy failed even with restored permissions, analyzing issues..."

      # Check for specific error patterns and handle them properly
      destroy_output=$(terraform plan -destroy 2>&1 || true)

      # Handle Backend Initialization Required error
      if echo "$destroy_output" | grep -q "Backend initialization required"; then
        log_warn "Backend initialization required - attempting to reconfigure..."
        if terraform init -reconfigure; then
          log_info "Terraform init -reconfigure successful, retrying destroy..."
          if terraform destroy -auto-approve -var bootstrap_user="$current_account"; then
             log_info "Terraform destroy succeeded after reconfigure"
             return 0
          fi
        else
          log_error "Terraform init -reconfigure failed"
        fi
      fi
    fi

    # Final cleanup of backup files
    log_info "Cleaning up temporary backup files..."
    rm -f terraform.tfvars.*backup* 2>/dev/null || true

    # Manual Folder Deletion (Fallback)
    # If terraform failed or state was lost, the top-level folder might still exist.
    # We attempt to find and delete it.
    log_info "Checking for remaining top-level folder..."
    # Assuming folder display name format "StellarEngine-${PREFIX}" or similar
    # We list folders in the org and filter by display name containing PREFIX
    if [[ -n "${ORGANIZATION_ID}" && -n "${PREFIX}" ]]; then
        folder_id=$(gcloud resource-manager folders list --organization="${ORGANIZATION_ID}" --filter="displayName:StellarEngine-${PREFIX} OR displayName:${PREFIX}-bootstrap" --format="value(name)" 2>/dev/null | head -n 1)
        
        if [[ -n "$folder_id" ]]; then
            log_warn "Found remaining top-level folder: $folder_id (StellarEngine-${PREFIX})"
            if promptUser "DESTRUCTIVE: Force delete this folder and ALL its contents (projects, buckets, etc.)?"; then
                # Use the recursive cleanup function
                clean_folder_recursive "$folder_id"
            fi
        fi
    fi
      # Handle Assured Workloads permission issues
      if echo "$destroy_output" | grep -q "assuredworkloads.*permission.*denied\|assuredworkloads.*403"; then
        log_warn "Detected Assured Workloads permission issue - attempting automatic resolution"

        # Function to handle Assured Workloads deletion automatically
        handle_assured_workloads_deletion() {
          local current_account
          current_account=$(gcloud config list --format 'value(core.account)')
          log_info "Current account: $current_account"

          # Check if user already has Assured Workloads admin role
          if gcloud organizations get-iam-policy "${ORGANIZATION_ID}" --flatten="bindings[].members" --format="table(bindings.role,bindings.members)" | grep -q "roles/assuredworkloads.admin.*$current_account"; then
            log_info "User already has Assured Workloads admin role"
          else
            log_info "Granting Assured Workloads admin role to $current_account"
            if ! gcloud_safe organizations add-iam-policy-binding "${ORGANIZATION_ID}" \
              --member="user:$current_account" \
              --role="roles/assuredworkloads.admin"; then
              log_error "Failed to grant Assured Workloads admin role"
              return 1
            fi

            # Wait for IAM propagation
            log_info "Waiting for IAM propagation..."
            log_info "Waiting 90 seconds for IAM policy changes..."; sleep 90
          fi

          # List and delete Assured Workloads (with proper project cleanup)
          log_info "Listing Assured Workloads in organization ${ORGANIZATION_ID}..."
          local workloads
          workloads=$(gcloud assured workloads list \
            --organization="${ORGANIZATION_ID}" \
            --location="${AW_REGION:-us-east4}" \
            --format="value(name)" 2>/dev/null)

          if [[ -n "$workloads" ]]; then
            log_info "Found Assured Workloads to delete:"
            echo "$workloads"

            for workload in $workloads; do
              log_info "Processing Assured Workload: $workload"

              # First, get all projects in this workload
              local workload_projects
              workload_projects=$(gcloud assured workloads describe "$workload" \
                --location="${AW_REGION:-us-east4}" \
                --format="value(resources[].resourceId)" 2>/dev/null | grep "^projects/" | sed 's|projects/||' || echo "")

              if [[ -n "$workload_projects" ]]; then
                log_info "Found projects in workload that need cleanup:"
                echo "$workload_projects"

                # Delete each project in the workload
                for project in $workload_projects; do
                  log_info "Attempting to delete project $project from workload"

                  # Remove any deletion liens first
                  gcloud_safe alpha resource-manager liens list --project="$project" --format="value(name)" | while read -r lien; do
                    if [[ -n "$lien" ]]; then
                      log_info "Removing lien: $lien"
                      gcloud_safe alpha resource-manager liens delete "$lien" || log_warn "Failed to remove lien $lien"
                    fi
                  done

                  # Disable billing
                  gcloud_safe billing projects unlink "$project" 2>/dev/null || log_warn "No billing to unlink for $project"

                  # Force delete the project
                  if gcloud_safe projects delete "$project"; then
                    log_info "Successfully deleted project $project"
                  else
                    log_warn "Failed to delete project $project - continuing anyway"
                  fi
                done

                # Wait for project deletions to propagate
                log_info "Waiting for project deletions to propagate..."
                log_info "Waiting 60 seconds for project deletions..."; sleep 60
              fi

              # Now try to delete the empty workload with proper timing
              log_info "Attempting to delete Assured Workload: $workload"
              local max_attempts=5
              local attempt=1

              while [[ $attempt -le $max_attempts ]]; do
                log_info "Attempt $attempt/$max_attempts to delete workload $workload"

                if gcloud_safe assured workloads delete "$workload" --location="${AW_REGION:-us-east4}"; then
                  log_info "Successfully deleted Assured Workload: $workload"
                  break
                else
                  log_warn "Attempt $attempt failed - workload may still contain resources"
                  if [[ $attempt -lt $max_attempts ]]; then
                    # Check what resources are still in the workload
                    log_info "Checking workload contents..."
                    local remaining_resources
                    remaining_resources=$(gcloud assured workloads describe "$workload" \
                      --location="${AW_REGION:-us-east4}" \
                      --format="value(resources[].resourceId)" 2>/dev/null || echo "")

                    if [[ -n "$remaining_resources" ]]; then
                      log_info "Workload still contains: $remaining_resources"
                      log_info "Waiting for resources to be fully deleted..."

                      # Poll for resource deletion status
                      local wait_count=0
                      local max_wait=24  # 2 minutes in 5-second intervals
                      while [[ $wait_count -lt $max_wait ]]; do
                        local still_exists=false
                        for resource in $remaining_resources; do
                          if [[ "$resource" =~ ^projects/ ]]; then
                            local project_id=${resource#projects/}
                            if gcloud projects describe "$project_id" >/dev/null 2>&1; then
                              still_exists=true
                              break
                            fi
                          elif [[ "$resource" =~ ^[0-9]+$ ]]; then
                            # Folder ID
                            if gcloud resource-manager folders describe "$resource" >/dev/null 2>&1; then
                              still_exists=true
                              break
                            fi
                          fi
                        done

                        if [[ "$still_exists" == "false" ]]; then
                          log_info "All resources are now deleted"
                          break
                        fi

                        sleep 5
                        ((wait_count++))
                      done
                    fi
                  fi
                fi
                ((attempt++))
              done

              if [[ $attempt -gt $max_attempts ]]; then
                log_error "Failed to delete Assured Workload: $workload after $max_attempts attempts"
                log_error "The workload may still contain resources or have dependencies"
                return 1
              fi
            done

            # Verify workloads are actually deleted
            log_info "Verifying Assured Workloads deletion..."
            local remaining_workloads
            remaining_workloads=$(gcloud assured workloads list \
              --organization="${ORGANIZATION_ID}" \
              --location="${AW_REGION:-us-east4}" \
              --format="value(name)" 2>/dev/null || echo "")

            if [[ -n "$remaining_workloads" ]]; then
              log_warn "Some workloads may still exist: $remaining_workloads"
              log_warn "This may cause issues with terraform destroy"
            else
              log_info "All Assured Workloads successfully deleted"
            fi
          else
            log_info "No Assured Workloads found to delete"
          fi

          return 0
        }

        if handle_assured_workloads_deletion; then
          log_info "Assured Workloads deletion completed successfully"
        else
          log_warn "Automatic Assured Workloads deletion failed - falling back to manual process"
          log_info "Assured Workloads must be deleted through console: https://console.cloud.google.com/assuredworkloads"
          if promptUser "Remove Assured Workloads from terraform state (you'll need to delete manually via console)?"; then
            terraform state rm 'google_assured_workloads_workload.primary[0]' || log_warn "Failed to remove Assured Workloads from state"
          fi
        fi

      # Handle project permission issues by ensuring proper permissions exist
      if echo "$destroy_output" | grep -q "project.*403\|project.*permission.*denied"; then
        log_warn "Project deletion permission issue detected"
        if promptUser "Would you like to switch to organization admin authentication?"; then
          log_info "Please authenticate with an organization admin account when prompted"
          gcloud auth login
          current_account=$(gcloud config list --format 'value(core.account)')
          log_info "Retrying with admin account: $current_account"
        fi
      fi

      # Retry destroy after handling permission issues
      if ! terraform destroy -auto-approve -var bootstrap_user="$current_account"; then
        log_error "Terraform destroy still failing after permission fixes"
        log_error "This indicates either:"
        log_error "  1. Insufficient organization-level permissions"
        log_error "  2. Resources with deletion protection enabled"
        log_error "  3. Dependencies that need manual cleanup"

        if promptUser "Would you like to force cleanup by removing problematic resources from state?"; then
          # This is a last resort - remove from state so they can be cleaned up manually
          log_warn "Removing problematic resources from terraform state (manual cleanup required)"
          terraform state rm 'google_assured_workloads_workload.primary[0]' 2>/dev/null || true
          terraform state rm 'module.automation-project.google_project.project[0]' 2>/dev/null || true

          log_info "Attempting final terraform destroy of remaining resources..."
          terraform destroy -auto-approve -var bootstrap_user="$current_account" || log_warn "Some resources may require manual cleanup"
        fi
      else
        log_info "Terraform destroy succeeded after permission restoration"
      fi
    fi
    fi


  # CRITICAL: Final Assured Workloads cleanup AFTER terraform destroy (AUTOMATIC - NO PROMPT)
  log_info "=========================================="
  log_info "FINAL ASSURED WORKLOADS CLEANUP (AUTOMATIC)"
  log_info "=========================================="
  log_info "Checking ALL regions for Assured Workloads..."
  current_account=$(gcloud config list --format 'value(core.account)')

  # Check multiple regions (not just one)
  AW_REGIONS=("us-east4" "us-west1" "us-central1" "us-east1")
  if [[ -n "${AW_REGION:-}" ]]; then
    # Add configured region if not already in list
    if [[ ! " ${AW_REGIONS[*]} " == *" ${AW_REGION} "* ]]; then
      AW_REGIONS+=("${AW_REGION}")
    fi
  fi
  if [[ -n "${REGION:-}" ]]; then
    # Add configured primary region if not already in list
    if [[ ! " ${AW_REGIONS[*]} " == *" ${REGION} "* ]]; then
      AW_REGIONS+=("${REGION}")
    fi
  fi

  log_info "Will check regions: ${AW_REGIONS[*]}"
  echo

    # Ensure Assured Workloads admin permissions
    if ! gcloud organizations get-iam-policy "${ORGANIZATION_ID}" --flatten="bindings[].members" --format="table(bindings.role,bindings.members)" | grep -q "roles/assuredworkloads.admin.*$current_account"; then
      log_info "Granting Assured Workloads admin role to $current_account"
      if gcloud_safe organizations add-iam-policy-binding "${ORGANIZATION_ID}" \
        --member="user:$current_account" \
        --role="roles/assuredworkloads.admin"; then
        log_info "Successfully granted Assured Workloads admin role"
        sleep 30  # Wait for IAM propagation
      else
        log_warn "Failed to grant Assured Workloads admin role - may encounter issues later"
      fi
    else
      log_info "User already has Assured Workloads admin role"
    fi

  # List and handle existing workloads across ALL regions
  total_workloads_found=0
  total_workloads_deleted=0
  total_workloads_retained=0

  for region in "${AW_REGIONS[@]}"; do
    log_info "Checking region: $region..."
    workloads=$(gcloud assured workloads list \
      --organization="${ORGANIZATION_ID}" \
      --location="${region}" \
      --format="value(name)" 2>/dev/null || echo "")

    if [[ -z "$workloads" ]]; then
      log_info "  No workloads found in $region"
      continue
    fi

    workload_count=$(echo "$workloads" | wc -l)
    total_workloads_found=$((total_workloads_found + workload_count))
    log_info "  Found $workload_count workload(s) in $region"

    if [[ -n "$workloads" ]]; then

      for workload in $workloads; do
        workload_name=$(gcloud assured workloads describe "$workload" --location="${region}" --format="value(displayName)" 2>/dev/null || echo "Unknown")
        log_info "  Processing: $workload_name (region: $region)"

        # Get projects in this workload
        workload_projects=$(gcloud assured workloads describe "$workload" \
          --location="${region}" \
          --format="value(resources[].resourceId)" 2>/dev/null | grep "^projects/" | sed 's|projects/||' || echo "")

        if [[ -n "$workload_projects" ]]; then
          log_info "Found projects in workload: $workload_projects"

          # Clean up each project
          for project in $workload_projects; do
            log_info "Cleaning up project $project from workload"

            # Remove liens
            gcloud_safe resource-manager liens list --project="$project" --format="value(name)" 2>/dev/null | while read -r lien; do
              if [[ -n "$lien" ]]; then
                log_info "Removing lien: $lien"
                gcloud_safe resource-manager liens delete "$lien" || true
              fi
            done

            # Unlink billing
            gcloud_safe billing projects unlink "$project" 2>/dev/null || true

            # Delete project and wait for completion
            if gcloud_safe projects delete "$project" --quiet; then
              log_info "Project $project deletion initiated, waiting for completion..."
              wait_for_project_deletion "$project"
            else
              log_warn "Failed to delete project $project - will be handled by terraform later"
            fi
          done
        fi

        # Now delete the empty workload with proper retry logic
        log_info "    Attempting to delete workload: $workload_name"
        max_attempts=5
        attempt=1
        workload_deleted=false

        while [[ $attempt -le $max_attempts ]]; do
          log_info "    Attempt $attempt/$max_attempts"

          if gcloud_safe assured workloads delete "$workload" --location="${region}" --quiet; then
            log_info "    ✓ Successfully deleted workload: $workload_name"
            workload_deleted=true
            ((total_workloads_deleted++)) || true
            break
          else
            log_warn "    Attempt $attempt failed - workload may still contain resources"

            if [[ $attempt -lt $max_attempts ]]; then
              # Check what resources are still in the workload
              log_info "    Checking workload contents..."
              remaining_resources=$(gcloud assured workloads describe "$workload" \
                --location="${region}" \
                --format="value(resources[].resourceId)" 2>/dev/null || echo "")

              if [[ -n "$remaining_resources" ]]; then
                log_info "Workload still contains: $remaining_resources"

                # Aggressively clean up contained resources
                for resource in $remaining_resources; do
                  if [[ "$resource" =~ ^[0-9]+$ ]]; then
                     # It's a folder
                     log_info "Found folder $resource in workload - attempting recursive cleanup"
                     clean_folder_recursive "$resource"
                  fi
                done

                # Re-check contents after cleanup
                remaining_resources=$(gcloud assured workloads describe "$workload" \
                --location="${region}" \
                --format="value(resources[].resourceId)" 2>/dev/null || echo "")

                # Check if remaining resources are only undeletable Assured Workload folders
                only_aw_folders=true
                for resource in $remaining_resources; do
                  if [[ "$resource" =~ ^projects/ ]]; then
                    # It's a project, not just a folder
                    only_aw_folders=false
                    break
                  elif [[ "$resource" =~ ^[0-9]+$ ]]; then
                    # Check if it's an Assured Workload folder
                    folder_info=$(gcloud resource-manager folders describe "$resource" --format="value(displayName)" 2>/dev/null || echo "")
                    
                    # Verify if folder is actually empty
                    is_empty=true
                    if gcloud projects list --filter="parent.id=$resource" --format="value(projectId)" --limit=1 2>/dev/null | grep -q .; then
                        is_empty=false
                    elif gcloud resource-manager folders list --folder="$resource" --format="value(name)" --limit=1 2>/dev/null | grep -q .; then
                        is_empty=false
                    fi

                    if [[ "$is_empty" == "false" ]]; then
                        log_warn "Folder $resource ($folder_info) is NOT empty - recursive cleanup might have failed"
                        only_aw_folders=false
                    elif ! echo "$folder_info" | grep -qi "StellarEngine"; then
                      # It's a folder but not an Assured Workload folder
                      # If we reached here, recursive cleanup failed to delete it?
                      # Assume it might be an AW folder with different naming?
                      # Or just assume we can't delete it.
                      # Let's keep existing logic but be looser
                      # only_aw_folders=false
                      log_warn "Folder $resource ($folder_info) remains - might be retention protected"
                    fi
                  fi
                done

                if [[ "$only_aw_folders" == "true" ]]; then
                  log_warn "    Workload only contains Assured Workload folders (30-day retention)"
                  log_warn "    Cannot delete now - will auto-delete after retention period"
                  ((total_workloads_retained++)) || true
                  break  # Break out of the attempt loop
                fi

                log_info "Waiting for resources to be fully deleted..."
                # Poll for resource deletion status
                wait_count=0
                max_wait=24  # 2 minutes in 5-second intervals
                while [[ $wait_count -lt $max_wait ]]; do
                  still_exists=false
                  for resource in $remaining_resources; do
                    if [[ "$resource" =~ ^projects/ ]]; then
                      project_id=${resource#projects/}
                      project_id=${resource#projects/}
                      # Check if project is truly active
                      p_state=$(gcloud projects describe "$project_id" --format="value(lifecycleState)" 2>/dev/null || echo "DELETED")
                      if [[ "$p_state" != "DELETED" ]] && [[ "$p_state" != "DELETE_REQUESTED" ]]; then
                        still_exists=true
                        break
                      fi
                    elif [[ "$resource" =~ ^[0-9]+$ ]]; then
                      # Folder ID - check if it still exists (excluding Assured Workload folders)
                      folder_info=$(gcloud resource-manager folders describe "$resource" --format="value(displayName,lifecycleState)" 2>/dev/null || echo "")
                      if [[ -n "$folder_info" ]] && echo "$folder_info" | grep -q "ACTIVE"; then
                        if ! echo "$folder_info" | grep -qi "StellarEngine"; then
                          # Non-Assured Workload folder still exists
                          still_exists=true
                          break
                        fi
                      fi
                    fi
                  done

                  if [[ "$still_exists" == "false" ]]; then
                    log_info "All deletable resources are now deleted"
                    break
                  fi

                  sleep 5
                  wait_count=$((wait_count + 1))
                done
              fi
            fi
          fi
          ((attempt++))
        done

        if [[ "$workload_deleted" == "false" ]] && [[ $attempt -gt $max_attempts ]]; then
          log_error "    ✗ Failed to delete workload: $workload_name"
          log_error "    This workload may require manual deletion"
          ((total_workloads_retained++)) || true
        fi
        echo
      done
    fi
  done

  # Summary of Assured Workloads cleanup
  echo
  log_info "=========================================="
  log_info "ASSURED WORKLOADS CLEANUP SUMMARY"
  log_info "=========================================="
  log_info "Total workloads found: $total_workloads_found"
  log_info "Successfully deleted: $total_workloads_deleted"
  if [[ $total_workloads_retained -gt 0 ]]; then
    log_warn "Retained (30-day retention): $total_workloads_retained"
    log_warn "These will auto-delete after the retention period expires"
  fi

  # Final verification across all regions
  log_info "Verifying remaining workloads across all regions..."
  remaining_count=0
  for region in "${AW_REGIONS[@]}"; do
    remaining=$(gcloud assured workloads list --organization="${ORGANIZATION_ID}" --location="${region}" --format="value(displayName)" 2>/dev/null || echo "")
    if [[ -n "$remaining" ]]; then
      count=$(echo "$remaining" | wc -l)
      remaining_count=$((remaining_count + count))
      formatted_remaining=$(echo "$remaining" | tr '\n' ' ')
      log_warn "Region $region still has $count workload(s): $formatted_remaining"
    fi
  done

  if [[ $remaining_count -eq 0 ]]; then
    log_info "✓ All Assured Workloads successfully deleted!"
  else
    log_warn "$remaining_count workload(s) remain (likely 30-day folder retention)"
  fi
  echo

  # Custom Constraint Cleanup
  log_info "Checking for remaining custom constraints..."
  constraints=$(gcloud org-policies list-custom-constraints --organization="${ORGANIZATION_ID}" --format="value(name)" 2>/dev/null | grep "custom.*${PREFIX}" || echo "")

  if [[ -n "$constraints" ]]; then
      formatted_constraints=$(echo "$constraints" | tr '\n' ' ')
      log_warn "Found remaining custom constraints: $formatted_constraints"
      if promptUser "Would you like to delete these custom constraints?"; then
          for constraint in $constraints; do
              log_info "Deleting custom constraint: $constraint"
              gcloud org-policies delete-custom-constraint "$constraint" --organization="${ORGANIZATION_ID}" --quiet
          done
      fi
  else
      log_info "No custom constraints found with prefix ${PREFIX}"
  fi
  echo

  # Remove Assured Workloads folders from terraform state since they can't be deleted (30-day retention)
  if promptUser "Would you like to remove Assured Workloads folders from state (they have 30-day retention and can't be immediately deleted)?"; then
    log_info "Removing Assured Workloads folders from terraform state..."
    terraform state rm 'module.branch-common-services-folder.google_folder.folder[0]' 2>/dev/null || log_warn "Common Services folder not in state"
    terraform state rm 'google_assured_workloads_workload.primary[0]' 2>/dev/null || log_warn "Assured Workloads not in state"
    log_info "These folders will be cleaned up automatically after the 30-day retention period"
  fi


  # Clean up any latent storage buckets that terraform couldn't delete
  if promptUser "Would you like to delete any remaining latent storage buckets?"; then
    log_info "Checking for latent storage buckets..."
    latent_buckets=$(gcloud storage buckets list --format="value(name)" 2>/dev/null | grep -E "^${PREFIX}-prod-iac-core-(resman|outputs|bootstrap)-" | sed 's|^|gs://|' | tr '\n' ' ' || echo "")

    if [[ -n "$latent_buckets" ]]; then
      log_info "Found latent buckets: $latent_buckets"

      for bucket in $latent_buckets; do
        log_info "Removing all objects from bucket: $bucket"
        gcloud_safe storage rm -r "${bucket}/**" 2>/dev/null || log_warn "No objects found in $bucket or removal failed"

        log_info "Removing empty bucket: $bucket"
        bucket_name=${bucket#gs://}
        if ! gcloud_safe storage buckets delete "gs://${bucket_name}"; then
          log_warn "Failed to remove bucket $bucket, continuing..."
        fi
      done
      log_info "Latent bucket cleanup completed"
    else
      log_info "No latent storage buckets found"
    fi
  fi

  # CRITICAL: Delete the automation project (often requires special handling)
  automation_project="${PREFIX}-prod-iac-core-0"
  if promptUser "Would you like to delete the automation project (${automation_project})?"; then
    log_info "Checking if automation project ${automation_project} exists..."

    # Check project state first
    project_state=$(gcloud projects describe "${automation_project}" --format="value(lifecycleState)" 2>/dev/null || echo "UNKNOWN")
    
    if [[ "$project_state" == "DELETE_REQUESTED" ]]; then
      log_info "Automation project ${automation_project} is already in DELETE_REQUESTED state. Skipping deletion."
    elif [[ "$project_state" != "UNKNOWN" ]]; then
      log_info "Automation project ${automation_project} exists (State: $project_state), preparing for deletion..."

      # Remove all deletion blockers systematically
      log_info "Step 1: Removing project liens..."
      liens=$(gcloud_safe alpha resource-manager liens list --project="${automation_project}" --format="value(name)" 2>/dev/null || echo "")
      if [[ -n "$liens" ]]; then
        while IFS= read -r lien; do
          if [[ -n "$lien" ]]; then
            log_info "  Removing lien: $lien"
            gcloud_safe alpha resource-manager liens delete "$lien" || log_warn "Failed to remove lien $lien"
          fi
        done <<< "$liens"
      else
        log_info "  No liens found"
      fi

      # Unlink billing
      log_info "Step 2: Unlinking billing account..."
      if gcloud_safe billing projects unlink "${automation_project}" 2>/dev/null; then
        log_info "  Billing unlinked successfully"
      else
        log_info "  No billing to unlink or already unlinked"
      fi

      # Disable problematic APIs
      log_info "Step 3: Disabling APIs that might block deletion..."
      apis_to_disable=("cloudresourcemanager.googleapis.com" "serviceusage.googleapis.com")
      for api in "${apis_to_disable[@]}"; do
        gcloud_safe services disable "$api" --project="${automation_project}" --force 2>/dev/null || log_info "  $api not enabled or already disabled"
      done

      # Wait for changes to propagate
      log_info "Step 4: Waiting 30 seconds for changes to propagate..."
      sleep 30

      # Attempt deletion
      log_info "Step 5: Attempting to delete project ${automation_project}..."
      if gcloud_safe projects delete "${automation_project}" --quiet; then
        log_info "Successfully deleted automation project ${automation_project}"
      else
        log_error "Failed to delete automation project ${automation_project}"
        log_error "This may require manual deletion or additional permissions"
        log_error "To delete manually, run: gcloud projects delete ${automation_project}"
        log_error "You may need to grant additional roles at: https://console.cloud.google.com/iam-admin/iam?organizationId=${ORGANIZATION_ID}"
      fi
    else
      log_info "Automation project ${automation_project} does not exist or was already deleted"
    fi
  fi

  if promptUser "Did you receive any errors deleting projects or Assured Workloads resources?"; then
    "${SCRIPT_DIR}"/../fast/stages-aw/0-bootstrap/setIAM.sh "${DEPLOYER_EMAIL_ADDRESS}" "${ORGANIZATION_ID}"
    sleep 60
    terraform destroy -auto-approve
  fi



  if promptUser "Would you like to delete your .terraform dir and related files (local to Stage 0)?"; then
    # Comprehensive terraform cleanup for stage 0
    if [[ -d ".terraform" ]]; then
      rm -rf .terraform
      log_info "Deleted .terraform directory"
    else
      log_warn ".terraform directory does not exist"
    fi

    # Remove terraform lock file
    if [[ -f ".terraform.lock.hcl" ]]; then
      rm -f .terraform.lock.hcl
      log_info "Deleted .terraform.lock.hcl"
    else
      log_warn ".terraform.lock.hcl does not exist"
    fi

    # Remove any backup state files
    if [[ -f "terraform.tfstate.backup" ]]; then
      rm -f terraform.tfstate.backup
      log_info "Deleted terraform.tfstate.backup"
    fi
  fi

  if promptUser "Would you like to delete your local .tfstate file?"; then
    if [[ -f "terraform.tfstate" ]]; then
      rm -f terraform.tfstate
      log_info "Deleted terraform.tfstate"
    else
      log_warn "terraform.tfstate does not exist"
    fi
  fi
  mark_stage_complete "STAGE_0"

########### Final Cleanup - Orphaned Resources ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Would you like to check for and clean up any orphaned resources?"; then
  log_info "Scanning for orphaned projects and folders..."

  # Check for orphaned projects in known folders
  orphaned_projects=$(gcloud projects list --filter="parent.id:${AW_FOLDER_ID:-} OR parent.id:${COMMON_SERVICES_FOLDER_ID:-} OR name~'${PREFIX}-'" --format="value(projectId)" 2>/dev/null | grep "^${PREFIX}-" || echo "")

  if [[ -n "$orphaned_projects" ]]; then
    log_warn "Found orphaned projects: $orphaned_projects"
    if promptUser "Would you like to delete these orphaned projects?"; then

      for project in $orphaned_projects; do
        log_info "Deleting orphaned project: $project"

        # Systematic approach to remove all blockers before deletion
        log_info "Checking for and removing project deletion blockers..."

        # 1. Check for liens (common blocker)
        project_number=$(gcloud projects describe "$project" --format="value(projectNumber)" 2>/dev/null || echo "")
        if [[ -n "$project_number" ]]; then
          liens=$(gcloud alpha resource-manager liens list --project="$project_number" --format="value(name)" 2>/dev/null || echo "")
          if [[ -n "$liens" ]]; then
            log_warn "Found project liens blocking deletion: $liens"
            for lien in $liens; do
              log_info "Removing lien: $lien"
              gcloud_safe alpha resource-manager liens delete "$lien" || log_warn "Failed to remove lien $lien"
            done
          fi
        fi

        # 2. Unlink billing (common blocker)
        log_info "Unlinking billing account from project $project"
        gcloud_safe billing projects unlink "$project" || log_warn "Failed to unlink billing or already unlinked"

        # 3. Disable APIs that might have dependencies
        log_info "Disabling problematic APIs that might block deletion"
        apis_to_disable=("compute.googleapis.com" "container.googleapis.com" "sql.googleapis.com" "cloudfunctions.googleapis.com")
        for api in "${apis_to_disable[@]}"; do
          gcloud_safe services disable "$api" --project="$project" --force || log_warn "Failed to disable $api or not enabled"
        done

        # 4. Remove IAM policies that might have external dependencies
        log_info "Clearing project IAM policies"
        gcloud_safe projects set-iam-policy "$project" <(echo '{"bindings":[]}') || log_warn "Failed to clear IAM policies"

        # 5. Wait for changes to propagate
        log_info "Waiting for deletion blockers removal to propagate..."
        sleep 30

        # 6. Try deletion
        if ! gcloud_safe projects delete "$project" --quiet; then
          log_error "Project $project still cannot be deleted after removing blockers"

          # Advanced debugging
          log_info "Performing advanced diagnostics for project $project..."

          # Check project state
          project_state=$(gcloud projects describe "$project" --format="value(lifecycleState)" 2>/dev/null || echo "UNKNOWN")
          log_info "Project lifecycle state: $project_state"

          # Check for organization policies blocking deletion
          org_policies=$(gcloud resource-manager org-policies list --organization="${ORGANIZATION_ID}" --filter="displayName~delete" --format="value(displayName)" 2>/dev/null || echo "")
          if [[ -n "$org_policies" ]]; then
            log_warn "Organization policies that might block deletion: $org_policies"
          fi

          # Last resort: try force delete with specific flags
          log_info "Attempting force deletion with additional flags..."
          if ! gcloud_safe projects delete "$project" --quiet --verbosity=debug; then
            log_error "Force deletion failed for project $project"
            log_error "This project may require manual intervention or have Assured Workloads protection"

            # Extract project creation info for debugging
            creation_time=$(gcloud projects describe "$project" --format="value(createTime)" 2>/dev/null || echo "Unknown")
            log_info "Project creation time: $creation_time"

            # Check if part of Assured Workloads and handle automatically
            if gcloud assured workloads list --organization="${ORGANIZATION_ID}" --location="${AW_REGION:-us-east4}" 2>/dev/null | grep -q "$project"; then
              log_warn "Project $project is part of Assured Workloads - attempting automatic cleanup"

                        # Find the specific workload containing this project
                        containing_workload=$(gcloud assured workloads list \
                          --organization="${ORGANIZATION_ID}" \                --location="${AW_REGION:-us-east4}" \
                --format="table(name)" --filter="resources.resourceId:projects/$project" \
                --format="value(name)" 2>/dev/null | head -1)

              if [[ -n "$containing_workload" ]]; then
                log_info "Found workload containing project: $containing_workload"

                            # Grant Assured Workloads admin if needed
                            current_account=$(gcloud config list --format 'value(core.account)')
                            if ! gcloud organizations get-iam-policy "${ORGANIZATION_ID}" --flatten="bindings[].members" --format="table(bindings.role,bindings.members)" | grep -q "roles/assuredworkloads.admin.*$current_account"; then                  log_info "Granting Assured Workloads admin role to $current_account"
                  gcloud_safe organizations add-iam-policy-binding "${ORGANIZATION_ID}" \
                    --member="user:$current_account" \
                    --role="roles/assuredworkloads.admin"
                  sleep 30
                fi

                # Try to delete the entire workload (which should delete projects)
                log_info "Attempting to delete workload $containing_workload (which will delete project $project)"
                if gcloud_safe assured workloads delete "$containing_workload" --location="${AW_REGION:-us-east4}"; then
                  log_info "Successfully deleted workload and project via Assured Workloads"
                else
                  log_error "Failed to delete workload automatically"
                  log_error "Go to: https://console.cloud.google.com/assuredworkloads and delete the workload manually"
                fi
              else
                log_error "Could not identify specific workload containing project $project"
                log_error "Go to: https://console.cloud.google.com/assuredworkloads and delete the workload manually"
              fi
            fi
          else
            log_info "Force deletion succeeded for project $project"
          fi
        else
          log_info "Successfully deleted project $project"
        fi
      done
    fi
  else
    log_info "No orphaned projects found"
  fi

  # Check for empty folders to clean up
  if [[ -n "${COMMON_SERVICES_FOLDER_ID:-}" ]]; then
    if promptUser "Would you like to delete the Common Services folder (${COMMON_SERVICES_FOLDER_ID})?"; then
      if ! gcloud_safe resource-manager folders delete "${COMMON_SERVICES_FOLDER_ID}"; then
        log_warn "Failed to delete Common Services folder - it may still contain resources"
      fi
    fi
  fi

  if [[ -n "${AW_FOLDER_ID:-}" ]]; then
    if promptUser "Would you like to delete the main Assured Workloads folder ${AW_FOLDER_ID}?"; then
      if ! gcloud_safe resource-manager folders delete "${AW_FOLDER_ID}"; then
        log_warn "Failed to delete main folder - it may still contain resources or be managed by Assured Workloads"
      fi
    fi
  fi
fi

if promptUser "Would you like reenable compute.requireOsLogin?"; then
  gcloud resource-manager org-policies enable-enforce compute.requireOsLogin --organization="${ORGANIZATION_ID}"
fi

if promptUser "Would you like to remove your gcloud configuration?"; then
  gcloud auth revoke "${DEPLOYER_EMAIL_ADDRESS}"
fi

echo "You have deleted your environment. Please run clean.sh if you are still running into issues."

# Final Sweep Cleanup
if promptUser "Would you like to perform a final deep clean of all local Terraform state and config (Recommended for clean redeploy)?"; then
  log_info "Performing final sweep..."
  
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
      # Removing state, providers, and auto.tfvars.json for a complete reset
    fi
  done
  
  # Also clean local state in experimental dir
  rm -f "${SCRIPT_DIR}/terraform.tfstate"
  rm -f "${SCRIPT_DIR}/terraform.tfstate.backup"
  rm -rf "${SCRIPT_DIR}/.terraform"
  
  log_info "Final sweep completed. Your environment should be ready for a fresh deployment."
fi


# TODO - Remove user permissions
# Keep these
# Organization Policy Administrator
# Organization Role Administrator
# Service Account Admin
