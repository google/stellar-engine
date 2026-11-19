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


# Default list of service account names. These are the static keys that the
# 0-bootstrap and 1-resman stages write under "service_accounts" in their
# tfvars files. The "-r" keys are the read-only plan accounts.
VALID_NAMES=(
  "bootstrap" "resman" "networking" "security"
  "bootstrap-r" "resman-r" "networking-r" "security-r"
  "data-platform-dev" "data-platform-dev-r"
  "data-platform-prod" "data-platform-prod-r"
  "gcve-dev" "gcve-dev-r" "gcve-prod" "gcve-prod-r"
  "gke-dev" "gke-dev-r" "gke-prod" "gke-prod-r"
  "project-factory-dev" "project-factory-dev-r"
  "project-factory-prod" "project-factory-prod-r"
  "sandbox" "teams"
)

# 1-resman also writes one "team-<name>" key for each entry in team_folders
TEAM_PREFIX="team-"

# Initialize variables
ACTION="disable"  # Default action is to disable
SERVICE_ACCOUNTS=()  # empty list

# Function to display help
usage() {
  echo "Usage: $0 [--enable] [--sa <comma-separated list of names>]"
  echo "  --enable           Enable the service accounts (default is disable)"
  echo "  --sa               Comma-separated list of service account names to look for (default is all valid names and every '${TEAM_PREFIX}<name>' account)"
  echo "Valid names are: ${VALID_NAMES[*]} ${TEAM_PREFIX}<name>"
  exit 1
}

# Function to validate the names
validate_names() {
  local invalid_names=()
  for name in "${SERVICE_ACCOUNTS[@]}"; do
    valid=false
    if [[ ${name} == "${TEAM_PREFIX}"?* ]]; then
      valid=true
    fi
    for valid_name in "${VALID_NAMES[@]}"; do
      if [[ ${name} == "${valid_name}" ]]; then
        valid=true
        break
      fi
    done
    
    # If the name is not valid, add it to the invalid_names array
    if [[ $valid == false ]]; then
      invalid_names+=("$name")
    fi
  done

  if [ ${#invalid_names[@]} -gt 0 ]; then
    echo "Invalid names provided: ${invalid_names[*]}"
    echo "Valid names are: ${VALID_NAMES[*]} ${TEAM_PREFIX}<name>"
    exit 1
  fi
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --enable)
      ACTION="enable"
      shift
      ;;
    --sa)
      IFS=',' read -r -a SERVICE_ACCOUNTS <<< "$2"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

# If no names are provided, use the default names
USE_DEFAULT_NAMES=false
if [ ${#SERVICE_ACCOUNTS[@]} -eq 0 ]; then
  SERVICE_ACCOUNTS=("${VALID_NAMES[@]}")
  USE_DEFAULT_NAMES=true
fi

# Validate that all provided names are valid
validate_names

# Find all auto.tfvars.json files in the current directory
for tfvars_file in *.tfvars.json; do
  # echo "Processing $tfvars_file..."

  # The default run also covers the per-team keys that this file defines
  names=("${SERVICE_ACCOUNTS[@]}")
  if [[ $USE_DEFAULT_NAMES == true ]]; then
    while IFS= read -r team_name; do
      names+=("$team_name")
    done < <(jq -r --arg prefix "$TEAM_PREFIX" '.. | .service_accounts? | objects | keys[] | select(startswith($prefix))' "$tfvars_file")
  fi

  # Use jq to extract service account emails from the "service_accounts" block
  for name in "${names[@]}"; do
    # Extract the email from the "service_accounts" block, keyed by the name
    service_account=$(jq -r --arg name "$name" '.. | .service_accounts?[$name] // empty' "$tfvars_file")
    
    # If service account is found, disable/enable it
    if [ "$service_account" != "null" ] && [ -n "$service_account" ]; then
      # Extract project ID from service account email (format: name@project-id.iam.gserviceaccount.com)
      project_id=$(echo "$service_account" | sed -E 's/.*@(.*)\.iam\.gserviceaccount\.com/\1/')
      
      # echo "$ACTION service account: $service_account in project: $project_id"
      if [ "$ACTION" == "disable" ]; then
        gcloud iam service-accounts disable "$service_account" --project="$project_id" --quiet
      elif [ "$ACTION" == "enable" ]; then
        gcloud iam service-accounts enable "$service_account" --project="$project_id" --quiet
      else
        echo "Unknown action: $ACTION"
        exit 1
      fi
    fi
  done
done