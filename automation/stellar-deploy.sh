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

GCP_ROLES=(
  "roles/resourcemanager.organizationAdmin:roles/resourcemanager.folderAdmin:roles/resourcemanager.projectCreator:roles/billing.user:roles/iam.organizationRoleAdmin:roles/orgpolicy.policyAdmin:roles/securitycenter.admin:roles/cloudsupport.admin:roles/pubsub.admin:roles/cloudkms.admin"
  "roles/billing.admin:roles/billing.creator:roles/resourcemanager.organizationViewer"
  "roles/compute.networkAdmin:roles/compute.xpnAdmin:roles/compute.securityAdmin:roles/resourcemanager.folderViewer"
  "roles/compute.networkAdmin:roles/resourcemanager.folderViewer"
  "roles/logging.admin:roles/monitoring.admin:roles/pubsub.admin"
  "roles/logging.viewer:roles/monitoring.viewer"
  "roles/orgpolicy.policyAdmin:roles/iam.securityAdmin:roles/iam.securityReviewer:roles/iam.serviceAccountCreator:roles/iam.organizationRoleViewer:roles/securitycenter.admin:roles/resourcemanager.folderIamAdmin:roles/logging.privateLogViewer:roles/logging.configWriter:roles/container.viewer:roles/compute.viewer:roles/logging.admin:roles/monitoring.admin:roles/cloudkms.admin"
  ""
  "roles/resourcemanager.folderViewer"
)

GCP_DESCRIPTIONS=(
  "Organization administrators have access to administer all resources belonging to the organization."
  "Billing administrators are responsible for setting up billing accounts and monitoring their usage."
  "Network administrators are responsible for creating VPC networks, subnets, and firewall rules."
  "Hybrid Connectivity administrators are responsible for creating network devices such as Cloud VPN instances and cloud routers."
  "Logging-monitoring administrators have access to all features of Logging and Cloud Monitoring."
  "Logging-monitoring viewers have read-only access to a defined subset of both ingested logs and monitoring data."
  "Security administrators are responsible for establishing and managing security policies for the entire organization, including access management and organization constraint policies."
  "Developers are responsible for designing, coding, and testing applications."
  "DevOps practitioners create or manage end-to-end pipelines that support continuous integration and delivery, monitoring, and system provisioning."
)

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

if [ -n "$1" ]; then
    if [ ! -f "$1" ]; then
        echo "Error: The configuration file '$1' does not exist." >&2
        exit 1
    fi
    CONFIG_FILE="$(realpath "$1")"
else
    CONFIG_FILE="$SCRIPT_DIR/config.env"
fi

echo Running deploy with configuration at path: "${CONFIG_FILE}"
echo "#######################################################"

cd "${SCRIPT_DIR}" || exit

# Allows us to decide when this array is populated if we are using environment variables
populateGroups() {
  GCP_GROUPS=(
    "${TF_VAR_gcp_organization_admins_group:-gcp-organization-admins}"
    "${TF_VAR_gcp_billing_admins_group:-gcp-billing-admins}"
    "${TF_VAR_gcp_vpc_network_admins_group:-gcp-vpc-network-admins}"
    "${TF_VAR_gcp_hybrid_connectivity_admins_group:-gcp-hybrid-connectivity-admins}"
    "${TF_VAR_gcp_logging_monitoring_admins_group:-gcp-logging-monitoring-admins}"
    "${TF_VAR_gcp_logging_monitoring_viewers_group:-gcp-logging-monitoring-viewers}"
    "${TF_VAR_gcp_security_admins_group:-gcp-security-admins}"
    "${TF_VAR_gcp_developers_group:-gcp-developers}"
    "${TF_VAR_gcp_devops_group:-gcp-devops}"
  )
}

cleanup() {
  local resourceFile=${1}
  local statusFile=${2}
  if [[ -f $resourceFile ]]; then
    rm "$resourceFile"
  fi
  if [[ -f $statusFile ]]; then
    rm "$statusFile"
  fi
}

tfRun() {
  local tf_cmd="$1"
  local resources_file="$2"
  local status_file="$3"

  if [[ ! -d $SCRIPT_DIR/tmp ]]; then
    mkdir -p "${SCRIPT_DIR}"/tmp
  fi

  local cmd="terraform $tf_cmd"

  eval "$cmd" 2>&1| tee >(sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' >> "$resources_file")
  local tf_exit_code=${PIPESTATUS[0]}
  echo "$tf_exit_code" > "$status_file"
}

errorChecking() {
  local tf_cmd="$1"
  local resource_file="$2"
  local status_file="$3"

  local upper_cmd=""
  upper_cmd=$(upper "${tf_cmd%% *}")

  while [[ $(cat "$statusFile") -ne 0 ]]; do
    echo -e "\n--- ${upper_cmd} FAILED ---"
    if grep -q "BigQuery service account: googleapi: Error 403: Request is disallowed by organization's constraints/gcp.restrictServiceUsage constraint" "$resource_file"; then
      echo -e "\n--- ${upper_cmd} FAILED WITH BQ USAGE CONSTRAINT ERROR ---"
      if promptUser "Would you like to update the Assured Workloads folder to allow BigQuery and Cloud KMS?"; then
        ("${SCRIPT_DIR}/allow_bq.sh")
        sleep 120
      fi
      return 1
    fi
    if promptUser "Would you like to see what the terraform errors are?"; then
      awk '/[Ee]rror/{p=1;print;next} p' "$resource_file"
    fi
    if promptUser "Do you want to re-run 'terraform ${tf_cmd}' now?"; then
      echo "Initiating manual 'terraform ${tf_cmd}'..."
      tfRun "$tf_cmd" "$resource_file" "$status_file"
    else
      echo "Skipping 'terraform ${tf_cmd}'."
      return 1
    fi
  done
  cleanup "$resource_file" "$status_file"
}

runTerraformCommand() {
  local tf_cmd="$1"
  local resource_file="$2"
  local status_file="$3"

  tfRun "$tf_cmd" "$resource_file" "$status_file"

  if [[ -f "$status_file" ]] && [[ $(cat "$status_file") -ne 0 ]]; then
    errorChecking "$tf_cmd" "$resource_file" "$status_file"
  else
    cleanup "$resource_file" "$status_file"
  fi
}

automateGroupsAdminAccess() {
  local TEMP_DIR="${SCRIPT_DIR}/tmp"
  if [[ ! -d $TEMP_DIR ]]; then
    mkdir -p "${TEMP_DIR}"
  fi
  POLICY_JSON="${TEMP_DIR}/policy.json"
  gcloud organizations get-iam-policy "$ORGANIZATION_ID" --format=json > "$POLICY_JSON"
  CURRENT_GROUPS_RAW=$(gcloud identity groups search --customer "$DIRECTORY_CUSTOMER_ID" --labels "cloudidentity.googleapis.com/groups.discussion_forum" --format 'value(groups.groupKey.id)')
  CURRENT_GROUPS=$(echo "$CURRENT_GROUPS_RAW" | tr ';' ' ')
  GROUP_SLEEP_FLAG=false
  for i in "${!GCP_GROUPS[@]}"; do
    group="${GCP_GROUPS[$i]}"@"$FULLY_QUALIFIED_DOMAIN_NAME"
    if ! echo "$CURRENT_GROUPS" | grep -q -w "$group"; then
      echo "Creating group ${group}"
      gcloud identity groups create "$group" --display-name="${GCP_GROUPS[$i]}" --organization "$ORGANIZATION_ID" --description "${GCP_DESCRIPTIONS[$i]}"
      GROUP_SLEEP_FLAG=true
    fi
  done
  if [[ $GROUP_SLEEP_FLAG == true ]]; then
    echo "Sleeping for 30s to allow groups to propagate in GCP"
    sleep 30
  fi
  for i in "${!GCP_GROUPS[@]}"; do
    group="${GCP_GROUPS[$i]}"@"$FULLY_QUALIFIED_DOMAIN_NAME"
    if [[ "${GCP_ROLES[$i]}" ]]; then
      IFS=':' read -ra ROLES_ARRAY <<< "${GCP_ROLES[$i]}"
      echo "Assigning roles to group: $GROUP_NAME"
      for role in "${ROLES_ARRAY[@]}"; do
        jq --arg role "$role" --arg member "group:$group" '
          .bindings |=
          (
            if any(.[]; .role == $role) then
              map(
                if .role ==$role and (.members | index($member) | not) then
                  .members += [$member]
                else
                  .
                end
              )
            else
              . + [ {"role": $role, "members": [$member]} ]
            end
          )
        ' "$POLICY_JSON" > temp.json && mv temp.json "$POLICY_JSON"
      done
      unset IFS
    fi
  done
  gcloud organizations set-iam-policy "$ORGANIZATION_ID" "$POLICY_JSON"
  rm -rf "$TEMP_DIR"
}

upper() {
  if [[ -n "$1" ]]; then
    echo "${1}" | tr '[:lower:]' '[:upper:]'
  fi
  return 0
}

compliance_regime_mapping() {
  case "${1}" in
    "COMPLIANCE_REGIME_UNSPECIFIED")
      echo "cru"
      ;;
    "IL2")
      echo "il2"
      ;;
    "IL4")
      echo "il4"
      ;;
    "IL5")
      echo "il5"
      ;;
    "FEDRAMP_HIGH")
      echo "frh"
      ;;
    "FEDRAMP_MODERATE")
      echo "frm"
      ;;
    *)
      echo "${1}" | tr '[:upper:]' '[:lower:]'
      ;;
  esac
}

promptUser() {
  echo -e "\n${1} Type 's' to skip, or 'c' to continue'."
  read -r choice
  if [[ "$choice" == "s" ]]; then
    return 255 # Won't run command
  else
    shift
    for i in "$@"; do
      eval "$i"
    done
  fi
}


############ Prerequisites ############
echo "Welcome to the Secure Cloud Landing Zone automated deployment!
This is designed for the initial deployment. For a redeployment, please make sure you change the prefix and run the delete.sh script prior to redeployment.

If you do not have a large enough quota for your billing projects, follow the below link:
https://support.google.com/code/contact/billing_quota_increase

Also, please make sure you have Super Admin privileges - if not, please contact your oganization administrator."

echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Prerequisites -"; then
  # Authentication
  promptUser 'Would you like to (re)authenticate with Google Cloud?' "gcloud auth login; gcloud auth application-default login"

  # Set variables
  if [ ! -f "$CONFIG_FILE" ] || promptUser "Would you like to overwrite your .env file?"; then
    gcloud organizations list

    read -r -p "Enter your billing account: " BILLING_ACCOUNT
    read -r -p "Enter your bootstrap project ID: " BOOTSTRAP_PROJECT_ID
    read -r -p "Enter the compliance regime: " COMPLIANCE_REGIME
    read -r -p "Enter your directory customer ID : " DIRECTORY_CUSTOMER_ID
    read -r -p "Enter your deployer email address: " DEPLOYER_EMAIL_ADDRESS
    read -r -p "Enter your fully qualified domain name: " FULLY_QUALIFIED_DOMAIN_NAME
    read -r -p "Enter your logging alerts email address: " LOGGING_ALERTS_EMAIL_ADDRESS
    read -r -p "Enter your organization ID: " ORGANIZATION_ID
    read -r -p "Enter your prefix (6 chars or less): " PREFIX
    read -r -p "Enter your regions: " REGIONS
    read -r -p "Enter your Assured Workload region: " AW_REGION
    read -r -p "Enter your tenant environment(s) (dev,prod): " TENANT_ENVIRONMENTS
    read -r -p "Enter your external Directory Customer IDs (comma-separated, or blank): " EXTERNAL_DIRECTORY_CUSTOMER_IDS
    read -r -p "Enter your external Organization IDs (comma-separated, or blank): " EXTERNAL_ORGANIZATION_IDS
    read -r -p "Enter the top level folder name: " TOP_LEVEL_FOLDER_NAME
    read -r -p "Enter the top level folder ID: " TOP_LEVEL_FOLDER_ID
    read -r -p "Enter the project path in gitlab for Workload Identity Federation (leave blank if not using): " CI_PROJECT_PATH
    read -r -p "Enter the branch name in gitlab where Workload Identity Federation will authenticate from (leave blank if not using): " CI_COMMIT_BRANCH
    read -r -p "Enter the GitLab URL if using Workload Identity Federation excluding trailing forward slash (leave blank if not using): " GITLAB_URL
    read -r -p "Enter the JWKS (JSON Web Key Set) for GitLab-to-GCP authentication. Note: This is only required if operating on an isolated enterprise network: " JWKS_KEY

    read -r -p "Enter the group name for gcp_organization_admins [default: gcp-organization-admins]: " TF_VAR_gcp_organization_admins_group
    TF_VAR_gcp_organization_admins_group=${TF_VAR_gcp_organization_admins_group:-gcp-organization-admins}
    read -r -p "Enter the group name for gcp_billing_admins [default: gcp-billing-admins]: " TF_VAR_gcp_billing_admins_group
    TF_VAR_gcp_billing_admins_group=${TF_VAR_gcp_billing_admins_group:-gcp-billing-admins}
    read -r -p "Enter the group name for gcp_vpc_network_admins [default: gcp-vpc-network-admins]: " TF_VAR_gcp_vpc_network_admins_group
    TF_VAR_gcp_vpc_network_admins_group=${TF_VAR_gcp_vpc_network_admins_group:-gcp-vpc-network-admins}
    read -r -p "Enter the group name for gcp_hybrid_connectivity_admins [default: gcp-hybrid-connectivity-admins]: " TF_VAR_gcp_hybrid_connectivity_admins_group
    TF_VAR_gcp_hybrid_connectivity_admins_group=${TF_VAR_gcp_hybrid_connectivity_admins_group:-gcp-hybrid-connectivity-admins}
    read -r -p "Enter the group name for gcp_logging_monitoring_admins [default: gcp-logging-monitoring-admins]: " TF_VAR_gcp_logging_monitoring_admins_group
    TF_VAR_gcp_logging_monitoring_admins_group=${TF_VAR_gcp_logging_monitoring_admins_group:-gcp-logging-monitoring-admins}
    read -r -p "Enter the group name for gcp_logging_monitoring_viewers [default: gcp-logging-monitoring-viewers]: " TF_VAR_gcp_logging_monitoring_viewers_group
    TF_VAR_gcp_logging_monitoring_viewers_group=${TF_VAR_gcp_logging_monitoring_viewers_group:-gcp-logging-monitoring-viewers}
    read -r -p "Enter the group name for gcp_security_admins [default: gcp-security-admins]: " TF_VAR_gcp_security_admins_group
    TF_VAR_gcp_security_admins_group=${TF_VAR_gcp_security_admins_group:-gcp-security-admins}
    read -r -p "Enter the group name for gcp_developers [default: gcp-developers]: " TF_VAR_gcp_developers_group
    TF_VAR_gcp_developers_group=${TF_VAR_gcp_developers_group:-gcp-developers}
    read -r -p "Enter the group name for gcp_devops [default: gcp-devops]: " TF_VAR_gcp_devops_group
    TF_VAR_gcp_devops_group=${TF_VAR_gcp_devops_group:-gcp-devops}

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
    echo "regions: $REGIONS"
    echo "aw-region: $AW_REGION"
    echo "tenant-environments: $TENANT_ENVIRONMENTS"
    echo "external-directory-customer-ids: $EXTERNAL_DIRECTORY_CUSTOMER_IDS"
    echo "external-organization-ids: $EXTERNAL_ORGANIZATION_IDS"
    echo "top-level-folder-name: $TOP_LEVEL_FOLDER_NAME"
    echo "top-level-folder-id: $TOP_LEVEL_FOLDER_ID"
    echo "ci-project-path: $CI_PROJECT_PATH"
    echo "ci-commit-branch: $CI_COMMIT_BRANCH"
    echo "gitlab-url: $GITLAB_URL"
    echo "jwks-key: $JWKS_KEY"
    echo "gcp-organization-admins: $TF_VAR_gcp_organization_admins_group"
    echo "gcp-billing-admins: $TF_VAR_gcp_billing_admins_group"
    echo "gcp-vpc-network-admins: $TF_VAR_gcp_vpc_network_admins_group"
    echo "gcp-hybrid-connectivity-admins: $TF_VAR_gcp_hybrid_connectivity_admins_group"
    echo "gcp-logging-monitoring-admins: $TF_VAR_gcp_logging_monitoring_admins_group"
    echo "gcp-logging-monitoring-viewers: $TF_VAR_gcp_logging_monitoring_viewers_group"
    echo "gcp-security-admins: $TF_VAR_gcp_security_admins_group"
    echo "gcp-developers: $TF_VAR_gcp_developers_group"
    echo "gcp-devops: $TF_VAR_gcp_devops_group"


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
      echo "REGIONS=$REGIONS"
      echo "AW_REGION=$AW_REGION"
      echo "TENANT_ENVIRONMENTS=$TENANT_ENVIRONMENTS"
      echo "EXTERNAL_DIRECTORY_CUSTOMER_IDS=$EXTERNAL_DIRECTORY_CUSTOMER_IDS"
      echo "EXTERNAL_ORGANIZATION_IDS=$EXTERNAL_ORGANIZATION_IDS"
      echo "TOP_LEVEL_FOLDER_NAME=$TOP_LEVEL_FOLDER_NAME"
      echo "TOP_LEVEL_FOLDER_ID=$TOP_LEVEL_FOLDER_ID"
      echo "CI_PROJECT_PATH=$CI_PROJECT_PATH"
      echo "CI_COMMIT_BRANCH=$CI_COMMIT_BRANCH"
      echo "GITLAB_URL=$GITLAB_URL"
      echo "JWKS_KEY=$JWKS_KEY"
      echo "TF_VAR_gcp_organization_admins_group=$TF_VAR_gcp_organization_admins_group"
      echo "TF_VAR_gcp_billing_admins_group=$TF_VAR_gcp_billing_admins_group"
      echo "TF_VAR_gcp_vpc_network_admins_group=$TF_VAR_gcp_vpc_network_admins_group"
      echo "TF_VAR_gcp_hybrid_connectivity_admins_group=$TF_VAR_gcp_hybrid_connectivity_admins_group"
      echo "TF_VAR_gcp_logging_monitoring_admins_group=$TF_VAR_gcp_logging_monitoring_admins_group"
      echo "TF_VAR_gcp_logging_monitoring_viewers_group=$TF_VAR_gcp_logging_monitoring_viewers_group"
      echo "TF_VAR_gcp_security_admins_group=$TF_VAR_gcp_security_admins_group"
      echo "TF_VAR_gcp_developers_group=$TF_VAR_gcp_developers_group"
      echo "TF_VAR_gcp_devops_group=$TF_VAR_gcp_devops_group"
    } >"$CONFIG_FILE"
  else
    # shellcheck source=automation/config.env.sample
    source "$CONFIG_FILE"
    echo "------------------------------------------------------------------"
    basename "$CONFIG_FILE"
    cat "$CONFIG_FILE"
    echo -e "\n------------------------------------------------------------------"
    echo "If the above does not look correct your .env file may be wrong!"
  fi

  echo -e "\n--- Compliance List Verification ---"
  if promptUser "Are the .yaml files accurately reflecting the compliance catalog?"; then
    sync_compliance_lists() {
      local target_dir=$1
      mkdir -p "${target_dir}"
      echo "[SYNC] Copying compliance lists to ${target_dir}..."
      cp "${SCRIPT_DIR}/allowed_apis.yaml" "${target_dir}/"
      cp "${SCRIPT_DIR}/lz_exceptions.yaml" "${target_dir}/"
      chmod 444 "${target_dir}/allowed_apis.yaml"
      chmod 444 "${target_dir}/lz_exceptions.yaml"
    }

    sync_compliance_lists "${SCRIPT_DIR}/../fast/stages-aw/1-assured-workload/data"
    sync_compliance_lists "${SCRIPT_DIR}/../fast/stages-aw/3-networking/data"

    echo "[SUCCESS] Compliance lists synced and locked (Read-Only)."
  fi
  # --------------------------------------------

  # Set Bootstrap Project
  echo -e "\nChecking to make sure the bootstrap project exists"
  bootstrap_state=$(gcloud projects describe "${BOOTSTRAP_PROJECT_ID}" --format 'value(lifecycleState)' 2>/dev/null)
  bootstrap_status=$?
  if [[ "$bootstrap_status" -ne 0 ]]; then
    if promptUser "Project '${BOOTSTRAP_PROJECT_ID}' does not exist. Would you like to create it and set it to the default project?"; then
      gcloud projects create "${BOOTSTRAP_PROJECT_ID}" --folder="${TOP_LEVEL_FOLDER_ID}"
      gcloud config set project "${BOOTSTRAP_PROJECT_ID}"
    fi
  elif [[ "${bootstrap_state}" == "DELETE_REQUESTED" ]]; then
    if promptUser "Project '${BOOTSTRAP_PROJECT_ID}' is pending deletion. Would you like to re-enable it and set it to the default project?"; then
      gcloud projects undelete "${BOOTSTRAP_PROJECT_ID}"
      gcloud config set project "${BOOTSTRAP_PROJECT_ID}"
    fi
  elif [[ "${bootstrap_state}" != "ACTIVE" ]]; then
    echo "Project '${BOOTSTRAP_PROJECT_ID}' exists but is in non-active state: ${bootstrap_state}. This can be caused by the project still being in a provisioning state or by the lifecycleStatus not having been set yet."
  else
    promptUser "Would you like to set the bootstrap project as the default project?" "gcloud config set project ${BOOTSTRAP_PROJECT_ID}"
  fi

  # setIAM
  promptUser "Would you like to set your IAM permissions?" "\"${SCRIPT_DIR}/../fast/stages-aw/0-organization-bootstrap/setIAM.sh\" ${DEPLOYER_EMAIL_ADDRESS} ${ORGANIZATION_ID}"

  # enable Services
  promptUser "Would you like to enable all Google Cloud Services?" "\"${SCRIPT_DIR}/../fast/stages-aw/0-organization-bootstrap/enableServices.sh\" ${DEPLOYER_EMAIL_ADDRESS} ${ORGANIZATION_ID}"

  if promptUser "Would you like to link the billing account to the bootstrap project?"; then
    gcloud billing projects link "${BOOTSTRAP_PROJECT_ID}" --billing-account="${BILLING_ACCOUNT}"
  fi

  # Groups and Admin setup
  populateGroups
  if promptUser "Would you like to create the Users and Groups and set up Administrative access?"; then
    automateGroupsAdminAccess
  fi

  echo -e "\nPlease follow the link below (if you have not yet done so) to enable access transparency for your organization"
  echo "https://console.cloud.google.com/iam-admin/settings?invt=AbuKFg&organizationId=${ORGANIZATION_ID}"
  echo "Press any key when complete to go to the next step."
  read -r -n 1 -s -p ""

  echo -e "\nCongratulations, you have finished the prerequisites!"

else

  # shellcheck source=automation/config.env.sample
  source "$CONFIG_FILE"
  populateGroups
  echo "------------------------------------------------------------------"
  basename "$CONFIG_FILE"
  cat "$CONFIG_FILE" 
  echo -e "\n------------------------------------------------------------------"
  echo -e "If the above does not look correct your configuration file may be wrong!\n"
fi

# Mapping abbreviations
COMPLIANCE_REGIME_ABBREVIATION=$(compliance_regime_mapping "${COMPLIANCE_REGIME}")

# Convert REGIONS from a string to an array
IFS=',' read -r -a REGIONS_ARRAY <<< "$REGIONS"
REGIONS_CONFIG=$(printf '%s", "' "${REGIONS_ARRAY[@]}" | sed 's/", "$//')
REGIONS_CONFIG="[\"$REGIONS_CONFIG\"]"

########### Stage 0 - Organization ###########
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 0 - Organization Bootstrap -"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/0-organization-bootstrap || exit
  resourceFile="${SCRIPT_DIR}/tmp/0-organization-bootstrap_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/0-organization-bootstrap_tf_status_$$"

  TOP_LEVEL_FOLDER_NAME_LOWER=$(echo "$TOP_LEVEL_FOLDER_NAME" | tr '[:upper:]' '[:lower:]')
  # Check for remote Terraform state for organization
  GCS_SOURCE_URL="gs://${TOP_LEVEL_FOLDER_NAME_LOWER}-prod-iac-core/terraform/state/default.tfstate"
  SKIP_STAGE=false

  # # Check if the state exists in GCS
  echo "Checking for file existence in Cloud Storage: ${GCS_SOURCE_URL}"
  if gcloud storage ls "${GCS_SOURCE_URL}" &>/dev/null; then
    echo "Skipping stage as the remote state is already present"
    SKIP_STAGE=true
  fi

  if [ "$SKIP_STAGE" = false ]; then
    # Confirm billing account privileges
    echo "Please make sure you have billing account admin privileges, and billing is enabled on the bootstrap project."
    echo "Press any key to confirm, and go to the next step."
    read -r -n 1 -s -p ""

    if promptUser "Would you to generate a new tfvars file?"; then
      # Organization Policy: Allowed Policy Member Domains
      if [ -z "$EXTERNAL_DIRECTORY_CUSTOMER_IDS" ]; then
        # No External Customer Directory IDs
        allowed_policy_member_domains_config="[]"
      else
        # Trim and Format Member Domains
        allowed_policy_member_domains_config="[\"$(echo "$EXTERNAL_DIRECTORY_CUSTOMER_IDS" | tr -d '[:space:]' | sed 's/,/\", \"/g')\"]"
      fi

      # Organization Policy: Access Boundaries
      if [ -z "$EXTERNAL_ORGANIZATION_IDS" ]; then
        # No External Organization IDs
        allowed_access_boundaries_config="[]"
      else
        # Trim and Format Access Boundaries
        allowed_access_boundaries_config="[\"$(echo "$EXTERNAL_ORGANIZATION_IDS" | tr -d '[:space:]' | sed 's/,/\", \"/g')\"]"
      fi
      GROUPS_BLOCK=""

      # Check each variable and append to our string if it exists
      [ -n "${TF_VAR_gcp_billing_admins_group}" ]      && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-billing-admins      = \"${TF_VAR_gcp_billing_admins_group}\"\n"
      [ -n "${TF_VAR_gcp_devops_group}" ]              && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-devops              = \"${TF_VAR_gcp_devops_group}\"\n"
      [ -n "${TF_VAR_gcp_vpc_network_admins_group}" ]  && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-vpc-network-admins  = \"${TF_VAR_gcp_vpc_network_admins_group}\"\n"
      [ -n "${TF_VAR_gcp_organization_admins_group}" ] && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-organization-admins = \"${TF_VAR_gcp_organization_admins_group}\"\n"
      [ -n "${TF_VAR_gcp_security_admins_group}" ]     && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-security-admins     = \"${TF_VAR_gcp_security_admins_group}\"\n"
      [ -n "${TF_VAR_gcp_devops_group}" ]              && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-support             = \"${TF_VAR_gcp_devops_group}\"\n"

      # Wrap it in the Terraform object syntax, interpreting the \n newlines safely
      # If GROUPS_BLOCK is entirely empty, this outputs a clean "groups = {}"
      if [ -n "$GROUPS_BLOCK" ]; then
        GROUPS_OUTPUT=$(printf "{\n%b}" "$GROUPS_BLOCK")
      else
        GROUPS_OUTPUT="{}"
      fi

      cat <<EOF >terraform.tfvars
assured_workloads = {
  regime   = "${COMPLIANCE_REGIME}" # "IL4, IL5, FEDRAMP_HIGH, etc... if you wish to not use assured_workloads, set this value to COMPLIANCE_REGIME_UNSPECIFIED"
  location = "${AW_REGION}"
}

billing_account = {
  id = "${BILLING_ACCOUNT}"
}

bootstrap_project = "${BOOTSTRAP_PROJECT_ID}"

groups = ${GROUPS_OUTPUT}

# locations for GCS, BigQuery, KMS, and logging buckets created here
locations = {
  bq      = "$(echo "$REGIONS_CONFIG" | jq -r '.[0]')"
  gcs     = ${REGIONS_CONFIG}
  logging = ${REGIONS_CONFIG}
  pubsub  = ${REGIONS_CONFIG}
  kms     = ${REGIONS_CONFIG}
}

# use \`gcloud organizations list\`
organization = {
  domain      = "${FULLY_QUALIFIED_DOMAIN_NAME}"
  id          = "${ORGANIZATION_ID}"
  customer_id = "${DIRECTORY_CUSTOMER_ID}"
}

org_policies_config = {
  import_defaults = false # No policies to import as of 27 SEP 2024
  constraints = {
    allowed_policy_member_domains = ${allowed_policy_member_domains_config}  # Additional externally allowed customer_ids
    allowed_access_boundaries     = ${allowed_access_boundaries_config}  # Additional externally allowed organization_ids
  }
}

top_level_folder = {
  name = "${TOP_LEVEL_FOLDER_NAME}"
  id = "${TOP_LEVEL_FOLDER_ID}"
}
EOF
    fi

    if promptUser "Would you like to ensure essential APIs are enabled for the folder context?"; then
      echo "Enabling APIs for project: ${TOP_LEVEL_FOLDER_NAME}..."

      apis=(
        "cloudbilling.googleapis.com"
        "iam.googleapis.com"
        "billingbudgets.googleapis.com"
        "kmsinventory.googleapis.com"
        "cloudkms.googleapis.com"
        "assuredworkloads.googleapis.com"
        "orgpolicy.googleapis.com"
        "cloudresourcemanager.googleapis.com"
      )

      for api in "${apis[@]}"; do
      echo "Activating $api for Folder: ${TOP_LEVEL_FOLDER_ID}..."
        gcloud beta services enable "$api" --folder="${TOP_LEVEL_FOLDER_ID}"
      done

      echo "Waiting for API propagation (120s)..."
      sleep 120
    fi

    # Create temporary providers.tf
    if [ ! -f "0-organization-bootstrap-providers.tf" ] || promptUser "Would you like to generate your initial providers.tf?"; then
      cp providers.tf.tmp 0-organization-bootstrap-providers.tf
    fi

    if promptUser "Would you like to perform the initial terraform init?"; then
      runTerraformCommand "init" "$resourceFile" "$statusFile"
    fi

    if promptUser "Would you like to perform the terraform apply?"; then
      runTerraformCommand "apply" "$resourceFile" "$statusFile"
    fi


    # Update Providers
    cmd=("gcloud storage cp gs://${TOP_LEVEL_FOLDER_NAME_LOWER}-org-iac-bootstrap/providers/0-organization-bootstrap-providers.tf ./")
    promptUser "Would you like to update your providers file?" "${cmd[@]}" # Pass the array elements

    # Migrate State
    if promptUser "Would you like to migrate to the remote state to ${TOP_LEVEL_FOLDER_NAME_LOWER}-org-iac?"; then
      runTerraformCommand "init --migrate-state" "$resourceFile" "$statusFile"
    fi

    echo "Congratulations, you have completed Stage 0!"
  fi
fi



########### Stage 1 - Assured Workload ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 1 - Assured Workload -"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/1-assured-workload || exit
  resourceFile="${SCRIPT_DIR}/tmp/1-assured-workload_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/1-assured-workload_tf_status_$$"

  # # Set file paths for tfvars file
  # GCS_SOURCE_URL="gs://${PREFIX}-prod-iac-core-inputs-0/stage-1/stage-1-inputs.auto.tfvars.json"
  # LOCAL_DEST_PATH="./stage-1-inputs.auto.tfvars.json"

  # # Check if the file exists in GCS
  # echo "Checking for file existence in Cloud Storage: ${GCS_SOURCE_URL}"
  # if gcloud storage ls "${GCS_SOURCE_URL}" &>/dev/null; then
    #   cmd=("gcloud storage cp ${GCS_SOURCE_URL} ${LOCAL_DEST_PATH}")
    #   promptUser "Would you like to download your tfvars file for stage-1 from ${PREFIX}-prod-iac-core-inputs-0/stage-1?" "${cmd[@]}"
  # fi

  # Generate TF Vars - This will NOT work indented
  if promptUser "Would you to generate a new tfvars file?"; then
    GROUPS_BLOCK=""

    # Check each variable and append to our string if it exists
    [ -n "${TF_VAR_gcp_billing_admins_group}" ]      && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-billing-admins      = \"${TF_VAR_gcp_billing_admins_group}\"\n"
    [ -n "${TF_VAR_gcp_devops_group}" ]              && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-devops              = \"${TF_VAR_gcp_devops_group}\"\n"
    [ -n "${TF_VAR_gcp_vpc_network_admins_group}" ]  && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-vpc-network-admins  = \"${TF_VAR_gcp_vpc_network_admins_group}\"\n"
    [ -n "${TF_VAR_gcp_organization_admins_group}" ] && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-organization-admins = \"${TF_VAR_gcp_organization_admins_group}\"\n"
    [ -n "${TF_VAR_gcp_security_admins_group}" ]     && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-security-admins     = \"${TF_VAR_gcp_security_admins_group}\"\n"
    [ -n "${TF_VAR_gcp_devops_group}" ]              && GROUPS_BLOCK="${GROUPS_BLOCK}  gcp-support             = \"${TF_VAR_gcp_devops_group}\"\n"

    # Wrap it in the Terraform object syntax, interpreting the \n newlines safely
    # If GROUPS_BLOCK is entirely empty, this outputs a clean "groups = {}"
    if [ -n "$GROUPS_BLOCK" ]; then
      GROUPS_OUTPUT=$(printf "{\n%b}" "$GROUPS_BLOCK")
    else
      GROUPS_OUTPUT="{}"
    fi
    cat <<EOF >terraform.tfvars
billing_account = {
  id = "${BILLING_ACCOUNT}"
}

groups = ${GROUPS_OUTPUT}

# locations for GCS, BigQuery, KMS, and logging buckets created here
locations = {
  bq      = "$(echo "$REGIONS_CONFIG" | jq -r '.[0]')"
  gcs     = ${REGIONS_CONFIG}
  logging = ${REGIONS_CONFIG}
  pubsub  = ${REGIONS_CONFIG}
  kms     = ${REGIONS_CONFIG}
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

fast_features = {
  envs = true
}

assured_workloads = {
  regime   = "${COMPLIANCE_REGIME}" # "IL4, IL5, FEDRAMP_HIGH, etc... if you wish to not use assured_workloads, set this value to COMPLIANCE_REGIME_UNSPECIFIED"
  location = "${AW_REGION}"
}

bootstrap_project = "${BOOTSTRAP_PROJECT_ID}"

alert_email = "${LOGGING_ALERTS_EMAIL_ADDRESS}"

top_level_folder = {
  name = "${TOP_LEVEL_FOLDER_NAME}"
  id = "${TOP_LEVEL_FOLDER_ID}"
}
EOF

    if [ -n "${APPLY_TIER_1_PUBSUB_SINK}" ]; then
      echo "apply_tier_1_pubsub_sink = ${APPLY_TIER_1_PUBSUB_SINK}" >> terraform.tfvars
    fi

    if [[ -n "$CI_PROJECT_PATH" && -n "$GITLAB_URL" ]]; then
      export CI_PROJECT_PATH GITLAB_URL TENANT_CI_PROJECT_PATH
      jq -n '
        .workload_identity_providers["gitlab-fed"] = {
          "issuer": "gitlab",
          "attribute_condition": "attribute.project_path == \"\(env.CI_PROJECT_PATH)\"",
          "custom_settings": {
            "issuer_uri": env.GITLAB_URL,
            "audiences": [env.GITLAB_URL],
            "jwks_json": env.JWKS_KEY
          }
        } |
        .cicd_repositories.bootstrap = {
          "name": env.CI_PROJECT_PATH,
          "type": "gitlab",
          "identity_provider": "gitlab-fed"
        } |
        .cicd_repositories.resman = {
          "name": env.CI_PROJECT_PATH,
          "type": "gitlab",
          "identity_provider": "gitlab-fed"
        } |
        
        if (env.TENANT_CI_PROJECT_PATH != null and env.TENANT_CI_PROJECT_PATH != "") then
          .workload_identity_providers["gitlab-tenants"] = {
            "issuer": "gitlab",
            "attribute_condition": "attribute.project_path == \"\(env.TENANT_CI_PROJECT_PATH)\"",
            "custom_settings": {
              "issuer_uri": env.GITLAB_URL,
              "audiences": [env.GITLAB_URL],
              "jwks_json": env.JWKS_KEY
            }
          } |
          .cicd_repositories.tenant = {
            "name": env.TENANT_CI_PROJECT_PATH,
            "type": "gitlab",
            "identity_provider": "gitlab-tenants"
          }
        else
          .cicd_repositories.tenant = {
            "name": env.CI_PROJECT_PATH,
            "type": "gitlab",
            "identity_provider": "gitlab-fed"
          }
        end
      ' > identity-providers.auto.tfvars.json
    fi
  fi

  # Create temporary providers.tf
  if [ ! -f "1-assured-workload-providers.tf" ] || promptUser "Would you like to generate your initial providers.tf?"; then
    cp providers.tf.tmp 1-assured-workload-providers.tf
  fi

  if promptUser "Would you like to perform the initial terraform init?"; then
    runTerraformCommand "init" "$resourceFile" "$statusFile"
  fi

  if promptUser "Do you want to cross reference with the compliance and LZ Exception lists to ensure compliance?"; then
    echo "Verifying project-level API allowlists against compliance and LZ Exception catalogs"
    if ! bash "${SCRIPT_DIR}/allow_compliance_apis.sh"; then
        echo "[ERROR] Exiting deployment: Unauthorized APIs detected in Terraform Plan."
        exit 1
    fi
    echo "[SUCCESS] Cross-check passed. Proceeding with Tiered Enforcement (COA 2)."
  fi

  # Terraform Apply #1
  if promptUser "Would you like to run the first terraform apply with the bootstrap user?"; then
    runTerraformCommand "apply -var bootstrap_user=${DEPLOYER_EMAIL_ADDRESS}" "$resourceFile" "$statusFile"
  fi

  # Terraform Apply #2
  if promptUser "Would you like to run the second terraform apply with the bootstrap user?"; then
    runTerraformCommand "apply -var bootstrap_user=${DEPLOYER_EMAIL_ADDRESS}" "$resourceFile" "$statusFile"
  fi

  export PROJ="automation-project"
  RAW_PROJ_NAME=$(yq '.projects[] | select(.name == env(PROJ)) | .project_name' "${SCRIPT_DIR}"/../project-config.yml)
  PROJ_NAME="${RAW_PROJ_NAME//<PREFIX>/$PREFIX}"
  PROJ_NAME="${PROJ_NAME//<REGIME>/$COMPLIANCE_REGIME_ABBREVIATION}"
  cmd=("gcloud config set project ${PROJ_NAME}")
  promptUser "Would you like to set the default project to ${PROJ_NAME}" "${cmd[@]}"

  # Update Providers
  cmd=("gcloud storage cp gs://${PREFIX}-${COMPLIANCE_REGIME_ABBREVIATION}-prod-iac-core-outputs/providers/1-assured-workload-providers.tf ./")
  promptUser "Would you like to update your providers file?" "${cmd[@]}" # Pass the array elements

  # Migrate State
  if promptUser "Would you like to migrate to the remote state to ${PROJ_NAME}?"; then
    runTerraformCommand "init --migrate-state" "$resourceFile" "$statusFile"
  fi

  # Terraform Apply #3
  if promptUser "Would you like to run the third terraform apply (without the bootstrap user)?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi
  echo "Congratulations, you have completed Stage 1!"
fi

########### Stage 2 - Resman ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 2 - Resource Manager -"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/2-resman || exit
  resourceFile="${SCRIPT_DIR}/tmp/2-resman_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/2-resman_tf_status_$$"

  export PROJ="automation-project"
  RAW_PROJ_NAME=$(yq '.projects[] | select(.name == env(PROJ)) | .project_name' "${SCRIPT_DIR}"/../project-config.yml)
  PROJ_NAME="${RAW_PROJ_NAME//<PREFIX>/$PREFIX}"
  PROJ_NAME="${PROJ_NAME//<REGIME>/$COMPLIANCE_REGIME_ABBREVIATION}"

  ## Set file paths for tfvars file
  # GCS_SOURCE_URL="gs://${PREFIX}-prod-iac-core-inputs-0/stage-2/stage-2-inputs.auto.tfvars.json"
  # LOCAL_DEST_PATH="./stage-1-inputs.auto.tfvars.json"

  # # Check if the file exists in GCS
  # echo "Checking for file existence in Cloud Storage: ${GCS_SOURCE_URL}"
  # if gcloud storage ls "${GCS_SOURCE_URL}" &>/dev/null; then
    #   cmd=("gcloud storage cp ${GCS_SOURCE_URL} ${LOCAL_DEST_PATH}")
    #   promptUser "Would you like to download your tfvars file for stage-2 from ${PREFIX}-prod-iac-core-inputs-0/stage-2?" "${cmd[@]}"
  # fi

  # Generate new tfvars - this will not work indented
  if promptUser "Would you like to generate a new 2-resman tfvars?"; then # Tenant Loop Logic
  # Tenant Environment Configuration ---"
  tenant_environments_config=""
  IFS=',' read -r -a ENV_ARRAY <<< "$TENANT_ENVIRONMENTS"
  for ENV_NAME in "${ENV_ARRAY[@]}"; do
    ENV_NAME=$(echo "$ENV_NAME" | tr -d '[:space:]')

    tenant_environments_config+="
  ${ENV_NAME} = {
  admin = \"${TF_VAR_gcp_organization_admins_group:-gcp-organization-admins}@${FULLY_QUALIFIED_DOMAIN_NAME}\"
  },"
  done
    # Remove the trailing comma
    if [[ -n "$tenant_environments_config" ]]; then
      tenant_environments_config="${tenant_environments_config%,*}"
    fi

    cat <<EOF >terraform.tfvars
fast_features = {
  envs = true
}

tenant_environments = {
${tenant_environments_config:1}
}
EOF

    if [[ -n "$CI_PROJECT_PATH" && -n "$GITLAB_URL" ]]; then
      cat <<EOF >>terraform.tfvars

cicd_repositories = {
  networking = {
    name              = "${CI_PROJECT_PATH}"
    type              = "gitlab"
    identity_provider = "gitlab-fed"
  }
  security = {
    name              = "${CI_PROJECT_PATH}"
    type              = "gitlab"
    identity_provider = "gitlab-fed"
  }
  shared_services = {
    name              = "${CI_PROJECT_PATH}"
    type              = "gitlab"
    identity_provider = "gitlab-fed"
  }
}
EOF
    fi
  fi

  # Copy remote tfvars
  cmd=(
    "gcloud storage cp gs://${PREFIX}-${COMPLIANCE_REGIME_ABBREVIATION}-prod-iac-core-outputs/providers/2-resman-providers.tf ./"
    "gcloud storage cp gs://${PREFIX}-${COMPLIANCE_REGIME_ABBREVIATION}-prod-iac-core-outputs/tfvars/1-globals.auto.tfvars.json ./"
    "gcloud storage cp gs://${PREFIX}-${COMPLIANCE_REGIME_ABBREVIATION}-prod-iac-core-outputs/tfvars/1-assured-workload.auto.tfvars.json ./"
  )
  promptUser "Would you like to pull the remote tfvars files created in Stage 1?" "${cmd[@]}"

  if promptUser "Would you like to perform the terraform init?"; then
    runTerraformCommand "init" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the terraform apply?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi

  echo "Congratulations, you have completed Stage 2!"
fi

########### Stage 3 - Networking ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 3 - Networking -"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/3-networking || exit
  # Add external billing account
  export PROJ="automation-project"
  RAW_PROJ_NAME=$(yq '.projects[] | select(.name == env(PROJ)) | .project_name' "${SCRIPT_DIR}"/../project-config.yml)
  PROJ_NAME="${RAW_PROJ_NAME//<PREFIX>/$PREFIX}"
  PROJ_NAME="${PROJ_NAME//<REGIME>/$COMPLIANCE_REGIME_ABBREVIATION}"

  resourceFile="${SCRIPT_DIR}/tmp/3-networking-ngfw_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/3-networking-ngfw_tf_status_$$"

  # cmd=("./pre-redeploy.sh")
  # promptUser "If this is a redeployment (<30 days), would you like to run the redeploy script?" "${cmd[@]}"

  if promptUser "Would you like to pull the remote tfvars files created in Stages 1 and 2?"; then
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/providers/3-networking-providers.tf ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-globals.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-assured-workload.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/2-resman.auto.tfvars.json ./
  fi

  if [ -n "${NETWORK_QUOTA_PREFERRED_VALUE}" ]; then
    echo "network_quota_preferred_value = ${NETWORK_QUOTA_PREFERRED_VALUE}" >> terraform.tfvars
  fi

  if promptUser "Would you like to perform the terraform init?"; then
    runTerraformCommand "init" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the targeted terraform apply?"; then
    runTerraformCommand "apply \
      -target=google_cloud_quotas_quota_preference.network_quota \
      -target=google_project_iam_custom_role.ngfw-custom-role \
      -target=local_file.generated_ingress_rule" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the full terraform apply?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi

  echo "Congratulations, you have completed Stage 3!"
fi

########### Stage 4 - Security ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 4 - Security -"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/4-security || exit
  resourceFile="${SCRIPT_DIR}/tmp/4-security_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/4-security_tf_status_$$"

  # Add external billing account
  export PROJ="automation-project"
  RAW_PROJ_NAME=$(yq '.projects[] | select(.name == env(PROJ)) | .project_name' "${SCRIPT_DIR}"/../project-config.yml)
  PROJ_NAME="${RAW_PROJ_NAME//<PREFIX>/$PREFIX}"
  PROJ_NAME="${PROJ_NAME//<REGIME>/$COMPLIANCE_REGIME_ABBREVIATION}"

  if promptUser "Would you like to pull the remote tfvars files created in Stages 1 and 2?"; then
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/providers/4-security-providers.tf ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-globals.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-assured-workload.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/2-resman.auto.tfvars.json ./
  fi

  if promptUser "Would you like to perform the terraform init?"; then
    runTerraformCommand "init" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the terraform apply?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi

  promptUser "Would you like to run the lockdown script?" "./sa_lockdown.sh"

  # promptUser "Would you like to delete the bootstrap project?" "./delete_gcp_project.sh --project-id=${BOOTSTRAP_PROJECT_ID}"

  echo "Congratulations, you have finished Stage 4! Please see the SBPG linked below for further hardening."
  echo 'https://docs.google.com/document/d/1bkPg-Uj6cf6_w1IHPCTZ66SC0fVWz9pUfTZy9v6hcr0/'
fi

m -rf "${SCRIPT_DIR}"/tmp