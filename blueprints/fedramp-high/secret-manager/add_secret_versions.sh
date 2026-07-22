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
set -e

# --- Script Usage and Argument Parsing ---
# Define usage function
usage() {
  echo "Usage: $0 --project-id <PROJECT_ID> [--secret-ids <ID1,ID2,...>] [--data-dir <PATH>]"
  echo "  --project-id   : Your Google Cloud Project ID (required)."
  echo "  --secret-ids   : Comma-separated list of Secret IDs to add versions to (e.g., 'secret-id-one,secret-id-two')."
  echo "                   If omitted, the script will discover all *.txt files in --data-dir."
  echo "  --data-dir     : Path to the directory containing your secret data files (default: 'secrets')."
  echo "                   Expected format: <DATA_DIR>/<SECRET_ID>.txt"
  exit 1
}

# Default values
PROJECT_ID=""
SECRET_IDS_CSV=""
DATA_DIR="secrets"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --project-id)
      PROJECT_ID="$2"
      shift # past argument
      ;;
    --secret-ids)
      SECRET_IDS_CSV="$2"
      shift # past argument
      ;;
    --data-dir)
      DATA_DIR="$2"
      shift # past argument
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown parameter: $1"
      usage
      ;;
  esac
  shift # past value
done

# Validate required arguments
if [ -z "$PROJECT_ID" ]; then
  echo "Error: --project-id is required."
  usage
fi

# --- Determine SECRET_IDS to process ---
SECRET_IDS=() # Initialize empty array

if [ -n "$SECRET_IDS_CSV" ]; then # If specific secret IDs are provided via CLI
  IFS=',' read -r -a SECRET_IDS <<< "$SECRET_IDS_CSV"
  echo "Using secret IDs provided via --secret-ids: ${SECRET_IDS[*]}"
else # If no specific IDs, discover from files in DATA_DIR
  echo "No --secret-ids provided. Discovering secrets from '$DATA_DIR' directory..."
  if [ ! -d "$DATA_DIR" ]; then
    echo "Error: Data directory '$DATA_DIR' not found. Please create it or specify a valid --data-dir."
    exit 1
  fi

  # Find all .txt files (max depth 1 to avoid subdirectories) and extract their base names
  mapfile -t FOUND_FILES < <(find "$DATA_DIR" -maxdepth 1 -type f -name "*.txt" -print0 | xargs -0 -n 1 basename)

  if [ ${#FOUND_FILES[@]} -eq 0 ]; then
    echo "Error: No .txt secret data files found in '$DATA_DIR'. Ensure your secret files are named <SECRET_ID>.txt"
    exit 1
  fi

  for FILE_BASENAME in "${FOUND_FILES[@]}"; do
    # Remove .txt extension to get the SECRET_ID
    SECRET_IDS+=( "${FILE_BASENAME%.txt}" )
  done
  echo "Discovered secret IDs from files: ${SECRET_IDS[*]}"
fi

# Final validation that we have secret IDs to process
if [ ${#SECRET_IDS[@]} -eq 0 ]; then
  echo "Error: No secret IDs determined to process. Exiting."
  exit 1
fi
# --- End SECRET_IDS determination logic ---

echo "--- Starting secret version upload ---"
echo "Project ID    : $PROJECT_ID"
echo "Secret IDs    : ${SECRET_IDS[*]}"
echo "Data Directory: $DATA_DIR"

for SECRET_ID in "${SECRET_IDS[@]}"; do
  SECRET_NAME="projects/$PROJECT_ID/secrets/$SECRET_ID"
  DATA_FILE="$DATA_DIR/$SECRET_ID.txt"

  echo "" # Newline for readability
  echo "Processing secret: '$SECRET_ID'"
  echo "  Source file: '$DATA_FILE'"

  # Check if data file exists for the current SECRET_ID (important even with auto-discovery)
  if [ ! -f "$DATA_FILE" ]; then
    echo "Error: Data file not found for secret '$SECRET_ID' at '$DATA_FILE'. Skipping this secret."
    continue # Skip to the next secret ID if its file is missing
  fi

  # Add the secret version
  # Using 'gcloud secrets versions add'
  if ! gcloud secrets versions add "$SECRET_NAME" \
    --data-file="$DATA_FILE" \
    --project="$PROJECT_ID"; then
    echo "Error adding version to secret '$SECRET_ID'. Please check permissions and secret existence in Secret Manager."
    exit 1 # Exit on first error for reliability
  fi
  echo "  Successfully added version to secret: '$SECRET_ID'"

done

echo "" # Newline for readability
echo "Secret versions upload process completed."

