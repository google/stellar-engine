#!/bin/bash

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
if [ $# -ne 2 ]; then
  echo -e "${RED}Error: This script requires exactly 2 arguments${NC}"
  echo -e "Usage: $0 <user_email> <organization_id>"
  exit 1
fi

USER_EMAIL=$1
ORG_ID=$2

# Check if sample YAML file exists
if [ ! -f "$SAMPLE_PATH" ]; then
  echo -e "${RED}Error: Sample YAML file not found: $SAMPLE_PATH${NC}" >&2
  exit 1
fi

# Validate organization ID format (should be numeric)
if ! [[ $ORG_ID =~ ^[0-9]+$ ]]; then
  echo -e "${RED}Error: Organization ID should be numeric${NC}"
  exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
  echo -e "${RED}Error: jq is not installed. Please install it first.${NC}"
  exit 1
fi

echo -e "${BLUE}Fetching current IAM policy for organization $ORG_ID...${NC}"

# Get current IAM policy
if ! CURRENT_POLICY=$(gcloud organizations get-iam-policy "$ORG_ID" --format=json); then
  echo -e "${RED}Error: Failed to get current IAM policy${NC}"
  exit 1
fi

echo -e "${GREEN}Current IAM policy fetched successfully${NC}"

# Parse the roles to be added from sample file
echo -e "${BLUE}Parsing roles from template file...${NC}"
ROLES_TO_ADD=$(sed "s/{USER}/$USER_EMAIL/g" "$SAMPLE_PATH" | jq '.bindings')

# Display current user's roles
echo -e "${YELLOW}Current roles for $USER_EMAIL:${NC}"
CURRENT_USER_ROLES=$(echo "$CURRENT_POLICY" | jq -r --arg user "user:$USER_EMAIL" '.bindings[] | select(.members[] | contains($user)) | .role' | sort)
echo "$CURRENT_USER_ROLES"

# Extract all roles from the sample file
ALL_SAMPLE_ROLES=$(echo "$ROLES_TO_ADD" | jq -r '.[] | .role')

# Display only the roles that need to be added (not already assigned)
echo -e "${YELLOW}New roles to be added for $USER_EMAIL:${NC}"
NEW_ROLES=()
for role in $ALL_SAMPLE_ROLES; do
  # Check if the role is in the current roles using a bash array contains check
  if ! echo "$CURRENT_USER_ROLES" | grep -q "^$role$"; then
    echo "$role"
    NEW_ROLES+=("$role")
  fi
done

if [ ${#NEW_ROLES[@]} -eq 0 ]; then
  echo -e "${GREEN}No new roles to add. User already has all specified roles.${NC}"
  exit 0
fi

# Create updated policy by merging current policy with new roles
echo -e "${BLUE}Creating updated IAM policy...${NC}"

# Start with the current policy
UPDATED_POLICY="$CURRENT_POLICY"

# Add each role separately to preserve existing policy
for ROLE in "${NEW_ROLES[@]}"; do
  # Check if the role binding already exists
  if echo "$UPDATED_POLICY" | jq --arg role "$ROLE" '.bindings[] | select(.role == $role)' | grep -q .; then
    # Role exists, add the user to it if not already present
    echo -e "${BLUE}Adding user to existing role: $ROLE${NC}"
    UPDATED_POLICY=$(echo "$UPDATED_POLICY" | jq --arg role "$ROLE" --arg user "user:$USER_EMAIL" '
      .bindings = [
        .bindings[] | 
        if .role == $role and (.members | index($user) | not) then 
          .members += [$user] 
        else 
          . 
        end
      ]
    ')
  else
    # Role doesn't exist, add it with the user
    echo -e "${BLUE}Adding new role binding: $ROLE${NC}"
    UPDATED_POLICY=$(echo "$UPDATED_POLICY" | jq --arg role "$ROLE" --arg user "user:$USER_EMAIL" '
      .bindings += [{ "role": $role, "members": [$user] }]
    ')
  fi
done

if [ ${#NEW_ROLES[@]} -gt 0 ]; then
  echo -e "${BLUE}Applying updated IAM policy...${NC}"

  # Apply the updated policy by piping directly to gcloud
  if echo "$UPDATED_POLICY" | gcloud organizations set-iam-policy "$ORG_ID" /dev/stdin --format=json; then
    echo -e "${GREEN}Successfully updated IAM policy for organization $ORG_ID${NC}"
  else
    echo -e "${RED}Failed to update IAM policy${NC}"
    exit 1
  fi
else
  echo -e "${GREEN}No changes needed to be applied${NC}"
fi