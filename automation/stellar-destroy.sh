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

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}" || exit

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

############ Prerequisites ############
echo "Welcome to the Secure Cloud Landing Zone automated destruction!"

if ! promptUser "This script will delete your entire environment, and all local .terraform dirs. Proceed with caution."; then exit; fi

promptUser 'Would you like to authenticate with Google Cloud?' "gcloud auth login; gcloud auth application-default login"

echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Prerequisites -"; then

  # Pull Config File
  if promptUser "Would you like to use an existing config file from a Google Storage Bucket?"; then

    echo -e "\nSearching for existing config.env files in GCS buckets..."
    config_files=()
    while IFS= read -r line; do
        config_files+=("$line")
    done < <(
      for project in $(gcloud projects list --format="value(projectId)"); do
        gcloud storage ls --project="$project" "gs://*-iac-core-config*/config.env" 2>/dev/null
      done
    )

    if [ ${#config_files[@]} -eq 0 ]; then
      echo "No existing config.env files found in any accessible GCS buckets."
    else
      echo -e "\nThe following config files were found:"
      for i in "${!config_files[@]}"; do
        printf "%s) %s\n" "$((i+1))" "${config_files[$i]#"gs://"}"
      done

      echo ""
      read -r -p "Please select the config file to use: " choice

      if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#config_files[@]} ]; then
        selected_index=$((choice-1))
        GCS_SOURCE_URL="${config_files[$selected_index]}"
        display_path="${GCS_SOURCE_URL#"gs://"}"
        echo "You selected: $display_path"
        promptUser "Would you like to copy $display_path to $SCRIPT_DIR/config.env ?" "gcloud storage cp \"$GCS_SOURCE_URL\" \"$SCRIPT_DIR/config.env\""
      else
        echo "Invalid selection. Please try again."
      fi
    fi
  fi

  # Set variables
  if [ ! -f "$SCRIPT_DIR"/config.env ] || promptUser "Would you like to overwrite your config.env file?"; then
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
    } > "$SCRIPT_DIR"/config.env
  else
    # shellcheck source=automation/config.env.sample
    source "$SCRIPT_DIR"/config.env
    echo "------------------------------------------------------------------"
    echo "config.env"
    cat config.env
    echo -e "\n------------------------------------------------------------------"
    echo "If the above does not look correct your config.env may be wrong!"
  fi

  # Mapping abbreviations
  COMPLIANCE_REGIME_ABBREVIATION=$(compliance_regime_mapping "${COMPLIANCE_REGIME}")

  export PROJ="automation-project"
  RAW_PROJ_NAME=$(yq '.projects[] | select(.name == env(PROJ)) | .project_name' ../project-config.yml)
  PROJ_NAME="${RAW_PROJ_NAME//<PREFIX>/$PREFIX}"
  PROJ_NAME="${PROJ_NAME//<REGIME>/$COMPLIANCE_REGIME_ABBREVIATION}"
  promptUser "Would you like to set your default project to ${PROJ_NAME}?" "gcloud config set project ${PROJ_NAME}"

  # if promptUser "Would you to set your IAM permissions?"; then
  #   "${SCRIPT_DIR}"/../fast/stages-aw/0-organization-bootstrap/setIam.sh "${DEPLOYER_EMAIL_ADDRESS}" "${ORGANIZATION_ID}"
  # fi

  if promptUser "Would you like to disable org policies to allow for deletion?"; then
    # gcloud org-policies delete-custom-constraint custom.kmsRotation"${PREFIX}" --organization="${ORGANIZATION_ID}"
    gcloud resource-manager org-policies disable-enforce compute.requireOsLogin --folder="${TOP_LEVEL_FOLDER_ID}"
    echo "Sleeping for 60 seconds to allow disabling policies to take effect"
    sleep 60
  fi
else
  # shellcheck source=automation/config.env.sample
  source "$SCRIPT_DIR"/config.env
  echo "------------------------------------------------------------------"
  echo "${SCRIPT_DIR}/config.env"
  cat "${SCRIPT_DIR}"/config.env
  echo -e "\n------------------------------------------------------------------"
  echo "If the above does not look correct your config.env may be wrong!"

  COMPLIANCE_REGIME_ABBREVIATION=$(compliance_regime_mapping "${COMPLIANCE_REGIME}")
fi

# Convert REGIONS from a string to an array
IFS=',' read -r -a REGIONS_ARRAY <<< "$REGIONS"
REGIONS_CONFIG=$(printf '%s", "' "${REGIONS_ARRAY[@]}" | sed 's/", "$//')
REGIONS_CONFIG="[\"$REGIONS_CONFIG\"]"

########### Stage 4 - Security ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 4 - Security"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/4-security || exit

  # if promptUser "Would you like to restore your bootstrap project if it was deleted?"; then
  #   gcloud projects undelete "${BOOTSTRAP_PROJECT_ID}"
  #   sleep 60
  #   gcloud billing projects link "${BOOTSTRAP_PROJECT_ID}" --billing-account="${BILLING_ACCOUNT}"
  # fi

  if promptUser "Would you like to pull the remote tfvars files created in Stages 0 and 1?"; then
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/providers/4-security-providers.tf ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-globals.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-assured-workload.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/2-resman.auto.tfvars.json ./
  fi

  if promptUser "Would you like to re-enable disabled Service Accounts?"; then
    ./sa_lockdown.sh --enable
    sleep 30
  fi

  promptUser "Would you like to perform the terraform init?" "terraform init"
  promptUser "Would you like to run terraform destroy?" "terraform destroy"
  promptUser "Would you like to delete your .terraform dir?" "rm -r .terraform"

  export PROJ="automation-project"
  RAW_PROJ_NAME=$(yq '.projects[] | select(.name == env(PROJ)) | .project_name' "${SCRIPT_DIR}"/../project-config.yml)
  PROJ_NAME="${RAW_PROJ_NAME//<PREFIX>/$PREFIX}"
  PROJ_NAME="${PROJ_NAME//<REGIME>/$COMPLIANCE_REGIME_ABBREVIATION}"
fi

########## Stage 3 - Networking ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 3 - Networking"; then

  cd "${SCRIPT_DIR}"/../fast/stages-aw/3-networking || exit

  if promptUser "Would you like to pull the remote tfvars files created in Stages 0 and 1?"; then
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/providers/3-networking-providers.tf ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-globals.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-assured-workload.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/2-resman.auto.tfvars.json ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/3-networking.auto.tfvars.json ./ # TESTING
  fi

  promptUser "Would you like to perform the terraform init?" "terraform init"
  promptUser "Would you like to generate your hierarchical-ingress-rules.yml file?" "terraform apply -target=local_file.generated_ingress_rule"
  promptUser "Would you like to run terraform destroy?" "terraform destroy"
  promptUser "If you receive a peering error, would you like to rerun terraform destroy?" "terraform destroy"
  promptUser "Would you like to delete your .terraform dir?" "rm -r .terraform"

  export PROJ="automation-project"
  RAW_PROJ_NAME=$(yq '.projects[] | select(.name == env(PROJ)) | .project_name' "${SCRIPT_DIR}"/../project-config.yml)
  PROJ_NAME="${RAW_PROJ_NAME//<PREFIX>/$PREFIX}"
  PROJ_NAME="${PROJ_NAME//<REGIME>/$COMPLIANCE_REGIME_ABBREVIATION}"
fi


########### Stage 2 - Resman ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"

if promptUser "Stage 2 - Resource Manager"; then # Left Here
  cd "${SCRIPT_DIR}"/../fast/stages-aw/2-resman || exit

    if promptUser "Would you like to pull the remote tfvars files created in Stage 0?"; then
      gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/providers/2-resman-providers.tf ./
      gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-globals.auto.tfvars.json ./
      gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/1-assured-workload.auto.tfvars.json ./
      gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/tfvars/2-resman.auto.tfvars.json ./ ### TESTING - Find something similar for networking deletion
    fi

  promptUser "Would you like to perform the terraform init?" "terraform init"

    if promptUser "Would you like to remove all storage buckets?"; then
      terraform state rm "module.branch-security-gcs.google_storage_bucket.bucket[0]" \
                         "module.branch-network-gcs.google_storage_bucket.bucket[0]"
      sleep 2
  
      gcloud storage rm -r gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-resman-sec
      gcloud storage rm -r gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-resman-net-0
    fi
  promptUser "Would you like to run terraform destroy?" "terraform destroy -lock=false"

  # if promptUser "If you received an error for TagValues, would you like to delete all child tags?"; then
  #   read -r -p "Please enter the TagValue from the above error - numbers only" TAG
  #   gcloud resource-manager tags values delete tagValues/"${TAG}"
  #   terraform destroy
  # fi

  promptUser "Would you like to delete your .terraform dir?" "rm -r .terraform"
fi

########### Stage 1 - Assured Workload ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"


if promptUser "Stage 1 - Assured Workload"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/1-assured-workload || exit

  if promptUser "Would you like to pull the remote tfvars files created in Stage 1?"; then
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs/providers/1-assured-workload-providers.tf ./
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-inputs/stage-1/stage-1-inputs.auto.tfvars.json ./
  fi

  if promptUser "Would you like to set the bootstrap project as your default project?"; then
    gcloud config set project "${BOOTSTRAP_PROJECT_ID}"
  fi

  if promptUser "Would you like to copy the remote state to your local device, revert your providers, and migrate to the local state?"; then
    gcloud storage cp gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-bootstrap/default.tfstate ./terraform.tfstate
    cp providers.tf.tmp 1-assured-workload-providers.tf
    terraform init -migrate-state
  fi

  if promptUser "Would you to set your IAM permissions?"; then
    "${SCRIPT_DIR}"/../fast/stages-aw/0-organization-bootstrap/setIam.sh "${DEPLOYER_EMAIL_ADDRESS}" "${ORGANIZATION_ID}"
  fi

  if promptUser "Would you like to delete storage buckets?"; then
    terraform state rm 'module.automation-tf-bootstrap-gcs.google_storage_bucket.bucket[0]' \
                       'module.automation-tf-output-gcs.google_storage_bucket.bucket[0]' \
                       'module.automation-tf-resman-gcs.google_storage_bucket.bucket[0]' \
                       'module.automation-tf-inputs-gcs.google_storage_bucket.bucket[0]' \
                       'module.automation-tf-config-gcs[0].google_storage_bucket.bucket[0]' \
                       'module.automation-tf-tenant-gcs.google_storage_bucket.bucket[0]'
    sleep 2

    gcloud storage rm -r gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-outputs
    gcloud storage rm -r gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-bootstrap
    gcloud storage rm -r gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-inputs
    gcloud storage rm -r gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-config-0
    gcloud storage rm -r gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-config
    gcloud storage rm -r gs://"${PREFIX}"-"${COMPLIANCE_REGIME_ABBREVIATION}"-prod-iac-core-tenants
  fi

  if promptUser "Would you like to run terraform destroy?"; then
    terraform destroy -var bootstrap_user="$(gcloud config list --format 'value(core.account)')"
  fi

  if promptUser "Did you receive any errors deleting projects or Assured Workloads resources?"; then
    "${SCRIPT_DIR}"/../fast/stages-aw/0-organization-bootstrap/setIam.sh "${DEPLOYER_EMAIL_ADDRESS}" "${ORGANIZATION_ID}"
    sleep 60
    terraform destroy
  fi

  ### Keeping the below in for reference
  # if promptUser "Did you receive any errors deleting projects"; then
  #   "${SCRIPT_DIR}"/../fast/stages-aw/0-organization-bootstrap/setIam.sh "${DEPLOYER_EMAIL_ADDRESS}" "${ORGANIZATION_ID}"
  #   gcloud projects delete "${PREFIX}"-prod-audit-logs-0
  #   gcloud projects delete "${PREFIX}"-prod-iac-core-0
  # fi

  # if promptUser "Did you receive any errors deleting Assured Workloads?"; then
  #   "${SCRIPT_DIR}"/../fast/stages-aw/0-organization-bootstrap/setIam.sh "${DEPLOYER_EMAIL_ADDRESS}" "${ORGANIZATION_ID}"

  #   aw_folder=$(gcloud resource-manager folders list --organization="${ORGANIZATION_ID}" | grep stellar-engine-"${PREFIX}" | awk '{print $3}')
  #   common_folder=$(gcloud resource-manager folders list --folder="${aw_folder}" --format='value(ID)')
  #   aw_environment=$(gcloud assured workloads list \
  #                 --organization="${ORGANIZATION_ID}" \
  #                 --location=us-east4 \
  #                 --format='value(name)' 2>/dev/null)

  #   gcloud resource-manager folders delete "${common_folder}"
  #   gcloud resource-manager folders delete "${aw_folder}"
  #   echo 'Waiting 2 minutes to ensure child folders and projects are properly deleted, then deleting the Assured Workloads Environment'
  #   sleep 120
  #   gcloud assured workloads delete "${aw_environment}"
  # fi

  if promptUser "Would you like to delete your .terraform dir?"; then
    rm -r .terraform
  fi

  if promptUser "Would you like to delete your .tfstate?"; then
    rm terraform.tfstate*
  fi
fi

########### Stage 0 - Organization ############
echo -e "\n#######################################################"
echo "#######################################################"
echo "#######################################################"


if promptUser "Stage 0 - Organization -"; then
  cd "${SCRIPT_DIR}"/../fast/stages-aw/0-organization-bootstrap || exit

  # Check for remaining AW folders
  echo "Checking for other Assured Workloads in the folder ${TOP_LEVEL_FOLDER_ID}"
  AW_COUNT=$(gcloud resource-manager folders list --folder="${TOP_LEVEL_FOLDER_ID}" --format="value(display_name)" | grep -Ec "CRU-|FRH-|IL2-|IL4-|IL5-")

  if [[ "$AW_COUNT" -gt 0 ]]; then
    echo "There are still other Assured Workload folders deployed to this organization. Please run this script against the remaining Assured Workloads those before running this step."
    exit
  fi
  TOP_LEVEL_FOLDER_NAME_LOWER=$(echo "$TOP_LEVEL_FOLDER_NAME" | tr '[:upper:]' '[:lower:]')
  if promptUser "Would you like to pull the remote providers file created in Stage 0 and initialize the remote bucket?"; then
    gcloud storage cp gs://"${TOP_LEVEL_FOLDER_NAME_LOWER}"-org-iac-bootstrap/tfvars/stage-0-inputs.auto.tfvars.json ./
    gcloud storage cp gs://"${TOP_LEVEL_FOLDER_NAME_LOWER}"-org-iac-bootstrap/providers/0-organization-bootstrap-providers.tf ./
    terraform init
  fi

  if promptUser "Would you like to copy the remote state to your local device, revert your providers, and migrate to the local state?"; then
    gcloud storage cp gs://"${TOP_LEVEL_FOLDER_NAME_LOWER}"-org-iac/terraform/state/default.tfstate ./terraform.tfstate
    cp providers.tf.tmp 0-organization-bootstrap-providers.tf
    terraform init -migrate-state
  fi
  
  
  if promptUser "Would you like to delete storage buckets?"; then
    terraform state rm 'module.lz-logs-bootstrap-gcs.google_storage_bucket.bucket[0]' \
                       'module.lz-logs-state-gcs.google_storage_bucket.bucket[0]'
    sleep 2

    gcloud storage rm -r gs://"${TOP_LEVEL_FOLDER_NAME_LOWER}"-org-iac-bootstrap
    gcloud storage rm -r gs://"${TOP_LEVEL_FOLDER_NAME_LOWER}"-org-iac
  fi

  if promptUser "Would you like to run terraform destroy?"; then
    terraform destroy
  fi
fi

if promptUser "Would you like re-enable compute.requireOsLogin?"; then
  gcloud resource-manager org-policies enable-enforce compute.requireOsLogin --organization="${ORGANIZATION_ID}"
fi

if promptUser "Would you like to remove your gcloud configuration?"; then
  gcloud auth revoke "${DEPLOYER_EMAIL_ADDRESS}"
fi

echo -e "\nCongratulations! You have deleted your environment. Please run clean.sh if you are still running into issues."

# TODO - Remove user permissions
# Keep these
# Organization Policy Administrator
# Organization Role Administrator
# Service Account Admin
