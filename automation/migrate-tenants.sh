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

# This is a temporary script to migrate tenants from a single tenants.yml to the tenants directory.
# This script will only need to be ran once.

# Exit immediately if a command exits with a non-zero status
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

compliance_regime_mapping() {
  case "${1}" in
    "COMPLIANCE_REGIME_UNSPECIFIED") echo "cru" ;;
    "IL2") echo "il2" ;;
    "IL4") echo "il4" ;;
    "IL5") echo "il5" ;;
    "FEDRAMP_HIGH") echo "frh" ;;
    "FEDRAMP_MODERATE") echo "frm" ;;
    *) echo "${1}" | tr '[:upper:]' '[:lower:]' ;;
  esac
}

# ==========================================
# CONFIGURATION & INITIALIZATION
# ==========================================

# shellcheck source=automation/config.env.sample
if [ -f "$SCRIPT_DIR/config.env" ]; then
    source "$SCRIPT_DIR"/config.env
else
    echo "Error: config.env not found at $SCRIPT_DIR/config.env"
    exit 1
fi

COMPLIANCE_REGIME_ABBREVIATION=$(compliance_regime_mapping "${COMPLIANCE_REGIME}")
TENANTS_BUCKET="gs://${PREFIX}-${COMPLIANCE_REGIME_ABBREVIATION}-prod-iac-core-tenants/tenant-config"

OLD_TENANTS_FILE="${SCRIPT_DIR}/../tenants.yml"
TENANTS_DIR="${SCRIPT_DIR}/../tenants"

# Ensure the local output directory exists
mkdir -p "$TENANTS_DIR"

# ==========================================
# STEP 1: Pull the legacy tenants.yml
# ==========================================
echo "Downloading legacy tenants.yml from GCS..."
if ! gcloud storage cp "$TENANTS_BUCKET/tenants.yml" "$OLD_TENANTS_FILE" 2>/dev/null; then
    echo "Error: Could not find or download tenants.yml from $TENANTS_BUCKET/tenants.yml"
    exit 1
fi

if [ ! -s "$OLD_TENANTS_FILE" ]; then
    echo "Error: The downloaded tenants.yml file is empty."
    exit 1
fi

# ==========================================
# STEP 2: Parse and Split Tenants
# ==========================================
# Count how many tenants exist in the array
TOTAL_TENANTS=$(yq '.tenants | length' "$OLD_TENANTS_FILE")

if [ "$TOTAL_TENANTS" -eq 0 ] || [ "$TOTAL_TENANTS" == "null" ]; then
    echo "No tenants found in the legacy file to migrate."
    exit 0
fi

echo "Found $TOTAL_TENANTS tenants to migrate. Processing..."
echo "------------------------------------------------"

for (( idx=0; idx<TOTAL_TENANTS; idx++ )); do
    # Fetch the tenant name to use as the filename
    TEN_NAME=$(yq ".tenants[$idx].name" "$OLD_TENANTS_FILE")
    
    if [[ -z "$TEN_NAME" || "$TEN_NAME" == "null" ]]; then
        echo "[-] Warning: Skipping index $idx due to missing or invalid tenant name."
        continue
    fi

    TEN_FILE="${TENANTS_DIR}/${TEN_NAME}.yml"
    echo "[*] Migrating tenant: $TEN_NAME"

    # Extract the array element. yq will automatically flatten it 
    # out into a root-level object when written out to a separate file.
    yq ".tenants[$idx]" "$OLD_TENANTS_FILE" > "$TEN_FILE"
    chmod 444 "$TEN_FILE"

    # ==========================================
    # STEP 3: Push individual file to GCS
    # ==========================================
    echo "    -> Uploading ${TEN_NAME}.yml to GCS..."
    gcloud storage cp "$TEN_FILE" "$TENANTS_BUCKET/${TEN_NAME}.yml"
done

echo "------------------------------------------------"
echo "Success! Cleaned up and split $TOTAL_TENANTS tenants into individual files."

# ==========================================
# STEP 4: Remove Legacy artifacts
# ==========================================
echo "------------------------------------------------"
echo "[!] Migration processing is complete."
read -r -p "Would you like to permanently delete the legacy tenants.yml file from GCS and local storage? (y/N): " CONFIRM

if [[ "$CONFIRM" =~ ^[Yy](es)?$ ]]; then
    echo "Cleaning up legacy artifacts..."
    
    echo "    -> Removing legacy tenants.yml from GCS..."
    gcloud storage rm "$TENANTS_BUCKET/tenants.yml"

    echo "    -> Removing legacy tenants.yml locally..."
    rm -f "$OLD_TENANTS_FILE"
    
    echo "------------------------------------------------"
    echo "Success! Split $TOTAL_TENANTS tenants into individual files and uploaded them."
    echo "The legacy tenants.yml file has been completely deleted from both GCS and your local drive."
else
    echo "------------------------------------------------"
    echo "Success! Split $TOTAL_TENANTS tenants into individual files and uploaded them."
    echo "[*] Cleanup skipped. The legacy tenants.yml files have been left intact on GCS and locally."
fi