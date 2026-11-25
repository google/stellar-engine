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

set -euo pipefail
umask 077

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure script works from any directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_PATH="${SCRIPT_DIR}/setIAM.yaml.sample"

# Validate arguments
if [[ $# -ne 2 ]]; then
  printf '%b%s%b\n' "$RED" "Error: This script requires exactly 2 arguments" "$NC" >&2
  printf 'Usage: %s <user_email> <organization_id>\n' "$0" >&2
  exit 1
fi

USER_EMAIL=$1
ORG_ID=$2

# Validate user email strictly before running any external commands
EMAIL_REGEX='^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
if [[ ! "$USER_EMAIL" =~ $EMAIL_REGEX ]]; then
  printf '%b%s%b\n' "$RED" "Error: Invalid user email address format" "$NC" >&2
  exit 1
fi

# Validate organization ID format (numeric)
ORG_ID_REGEX='^[0-9]+$'
if [[ ! "$ORG_ID" =~ $ORG_ID_REGEX ]]; then
  printf '%b%s%b\n' "$RED" "Error: Organization ID should be numeric" "$NC" >&2
  exit 1
fi

# Check if sample file exists
if [[ ! -f "$SAMPLE_PATH" ]]; then
  printf '%b%s%b\n' "$RED" "Error: Sample YAML file not found: $SAMPLE_PATH" "$NC" >&2
  exit 1
fi

# Check required CLI dependencies
if ! command -v jq > /dev/null 2>&1; then
  printf '%b%s%b\n' "$RED" "Error: jq is not installed. Please install it first." "$NC" >&2
  exit 1
fi

if ! command -v gcloud > /dev/null 2>&1; then
  printf '%b%s%b\n' "$RED" "Error: gcloud is not installed. Please install it first." "$NC" >&2
  exit 1
fi

MEMBER="user:${USER_EMAIL}"

printf '%b%s%b\n' "$BLUE" "Fetching current IAM policy for organization ${ORG_ID}" "$NC"

# Get current IAM policy
if ! CURRENT_POLICY=$(gcloud organizations get-iam-policy "$ORG_ID" --format=json); then
  printf '%b%s%b\n' "$RED" "Error: Failed to get current IAM policy" "$NC" >&2
  exit 1
fi

printf '%b%s%b\n' "$GREEN" "Current IAM policy fetched successfully" "$NC"

# Parse roles directly from the sample file without shell or sed interpolation
printf '%b%s%b\n' "$BLUE" "Parsing roles from template file" "$NC"
SAMPLE_ROLES_RAW=$(jq -r '(.bindings // [])[].role' "$SAMPLE_PATH")
ALL_SAMPLE_ROLES=()
while IFS= read -r role; do
  if [[ -n "$role" ]]; then
    ALL_SAMPLE_ROLES+=("$role")
  fi
done <<< "$SAMPLE_ROLES_RAW"

# Display current user's exact unconditional role assignments
printf '%b%s%b\n' "$YELLOW" "Current roles for ${USER_EMAIL}:" "$NC"
CURRENT_USER_ROLES_RAW=$(
  jq -r --arg user "$MEMBER" \
    '(.bindings // [])[] | select((.condition == null) and (((.members // []) | index($user)) != null)) | .role' \
    <<< "$CURRENT_POLICY" | sort -u
)
if [[ -n "$CURRENT_USER_ROLES_RAW" ]]; then
  printf '%s\n' "$CURRENT_USER_ROLES_RAW"
fi

# Identify roles that need to be added (not already assigned)
printf '%b%s%b\n' "$YELLOW" "New roles to be added for ${USER_EMAIL}:" "$NC"
NEW_ROLES=()
if [[ ${#ALL_SAMPLE_ROLES[@]} -gt 0 ]]; then
  for role in "${ALL_SAMPLE_ROLES[@]}"; do
    if ! grep -Fxq -- "$role" <<< "$CURRENT_USER_ROLES_RAW"; then
      printf '%s\n' "$role"
      NEW_ROLES+=("$role")
    fi
  done
fi

if [[ ${#NEW_ROLES[@]} -eq 0 ]]; then
  printf '%b%s%b\n' "$GREEN" "No new roles to add. User already has all specified roles." "$NC"
  exit 0
fi

# Create updated policy by merging current policy with new roles
printf '%b%s%b\n' "$BLUE" "Creating updated IAM policy" "$NC"
UPDATED_POLICY="$CURRENT_POLICY"

for ROLE in "${NEW_ROLES[@]}"; do
  if jq -e --arg role "$ROLE" \
    '(.bindings // []) | any(.role == $role and .condition == null)' \
    <<< "$UPDATED_POLICY" > /dev/null; then
    printf '%b%s%b\n' "$BLUE" "Adding user to existing role: ${ROLE}" "$NC"
    UPDATED_POLICY=$(
      jq --arg role "$ROLE" --arg user "$MEMBER" '
        .bindings = [
          (.bindings // [])[] |
          if .role == $role and .condition == null and (((.members // []) | index($user)) == null) then
            .members = ((.members // []) + [$user])
          else
            .
          end
        ]
      ' <<< "$UPDATED_POLICY"
    )
  else
    printf '%b%s%b\n' "$BLUE" "Adding new role binding: ${ROLE}" "$NC"
    UPDATED_POLICY=$(
      jq --arg role "$ROLE" --arg user "$MEMBER" '
        .bindings = ((.bindings // []) + [{ "role": $role, "members": [$user] }])
      ' <<< "$UPDATED_POLICY"
    )
  fi
done

printf '%b%s%b\n' "$BLUE" "Applying updated IAM policy" "$NC"

# Apply the updated policy by passing it via stdin to gcloud
if gcloud organizations set-iam-policy "$ORG_ID" /dev/stdin --format=json <<< "$UPDATED_POLICY"; then
  printf '%b%s%b\n' "$GREEN" "Successfully updated IAM policy for organization ${ORG_ID}" "$NC"
else
  printf '%b%s%b\n' "$RED" "Failed to update IAM policy" "$NC" >&2
  exit 1
fi
