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

# Exit immediately if a command exits with a non-zero status.
set -euo pipefail

# --- Configuration ---
DRY_RUN=false
GCLOUD_QUIET_FLAG="" # Will be set to "--quiet" if the corresponding flag is passed

# --- Function Definitions ---

# Function to print usage instructions
usage() {
    echo "Usage: $0 [OPTIONS] <ORGANIZATION_ID>"
    echo "Recursively deletes all folders and projects within a GCP Organization."
    echo ""
    echo "Arguments:"
    echo "  ORGANIZATION_ID   The numeric ID of the GCP Organization (e.g., 123456789012)."
    echo ""
    echo "Options:"
    echo "  --dry-run         Show what would be deleted without actually deleting anything."
    echo "  --quiet           Pass the '--quiet' flag to 'gcloud' delete commands to suppress their prompts."
    echo "  --help            Display this help and exit."
    exit 1
}

# Recursive function to delete a folder and its contents
delete_folder_recursively() {
    local folder_id="$1"
    echo ""
    echo "--- Processing Folder ID: $folder_id ---"

    # 1. Delete all projects inside the current folder
    echo "-> Searching for projects in folder $folder_id..."
    # The '|| true' prevents the script from exiting if no projects are found
    local project_ids
    project_ids=$(gcloud projects list \
        --filter="parent.id=$folder_id AND parent.type=folder" \
        --format="value(projectId)" || true)

    if [[ -n "$project_ids" ]]; then
        for project_id in $project_ids; do
            if [ "$DRY_RUN" = false ]; then
                echo "Deleting project: $project_id"
                # The $GCLOUD_QUIET_FLAG variable is used here
                gcloud projects delete "$project_id" $GCLOUD_QUIET_FLAG
            else
                echo "DRY RUN: Would delete project '$project_id'."
            fi
        done
    else
        echo "No projects found in folder $folder_id."
    fi

    # 2. Recursively delete all sub-folders
    echo "-> Searching for sub-folders in folder $folder_id..."
    # The '|| true' prevents the script from exiting if no sub-folders are found
    local sub_folder_ids
    sub_folder_ids=$(gcloud resource-manager folders list \
        --folder="$folder_id" \
        --format="value(ID)" || true)

    if [[ -n "$sub_folder_ids" ]]; then
        for sub_folder_id in $sub_folder_ids; do
            # Recursive call for each sub-folder
            delete_folder_recursively "$sub_folder_id"
        done
    else
        echo "No sub-folders found in folder $folder_id."
    fi

    # 3. Delete the (now empty) current folder
    if [ "$DRY_RUN" = false ]; then
        echo "-> Deleting folder itself: $folder_id"
        # The $GCLOUD_QUIET_FLAG variable is used here
        gcloud resource-manager folders delete "$folder_id" $GCLOUD_QUIET_FLAG
    else
        echo "-> DRY RUN: Would delete folder '$folder_id'."
    fi
    echo "--- Finished Processing Folder ID: $folder_id ---"
}


# --- Main Script Logic ---

# Check for gcloud command
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: 'gcloud' command not found. Please install and configure the Google Cloud SDK."
    exit 1
fi

# Robust argument parsing
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift # past argument
      ;;
    --quiet)
      GCLOUD_QUIET_FLAG="--quiet"
      shift # past argument
      ;;
    --help)
      usage
      ;;
    -*) # Unknown option
      echo "Error: Unknown option $1"
      usage
      ;;
    *) # Positional argument
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done
set -- "${POSITIONAL_ARGS[@]}" # Restore positional parameters

# Check for ORGANIZATION_ID
if [[ $# -ne 1 ]]; then
  echo "Error: Missing ORGANIZATION_ID."
  usage
fi
ORG_ID="$1"

# Validate ORG_ID is a number
if ! [[ "$ORG_ID" =~ ^[0-9]+$ ]]; then
    echo "Error: ORGANIZATION_ID must be a numeric value."
    usage
fi

# Main warning and confirmation prompt
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo "!!!                        W A R N I N G                      !!!"
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo "This is a destructive action, intended to clean up "
echo "A GCP ORG for DELETION"
echo "Common causes of failure are firewall associations"
echo "for shared VPC in the Networking Folders"
echo "----------------------------------------------------------------"
echo "This script will PERMANENTLY delete all folders and all projects"
echo "under the organization with ID: $ORG_ID."
echo "This action CANNOT be undone."
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "✅ DRY RUN MODE ENABLED. NO RESOURCES WILL BE DELETED."
else
    # Prompt for confirmation unless in dry-run mode
    read -r -p "To confirm this destructive action, type the organization ID ($ORG_ID) again: " confirmation
    if [[ "$confirmation" != "$ORG_ID" ]]; then
        echo "Confirmation failed. Exiting without making changes."
        exit 0
    fi
fi

echo ""
echo "Starting process for Organization ID: $ORG_ID"

# Get top-level folders in the organization
echo "Fetching top-level folders..."
top_level_folders=$(gcloud resource-manager folders list \
    --organization="$ORG_ID" \
    --format="value(ID)" || true)

if [[ -z "$top_level_folders" ]]; then
    echo "No folders found in organization $ORG_ID. Nothing to do."
    exit 0
fi

# Loop through top-level folders and start the recursive deletion
for folder_id in $top_level_folders; do
    delete_folder_recursively "$folder_id"
done

echo ""
echo "✅ Script completed."