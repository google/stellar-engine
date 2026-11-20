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

# Verifies that sa_lockdown.sh disabled every deployment automation service
# account. The script exits with status 0 only when it checks at least one
# account and every checked account is disabled. It exits with status 1 when an
# account is still enabled, when it finds no account to check, or when a gcloud
# or jq call fails, so a caller never reads an incomplete check as a pass.

set -euo pipefail

# Keys that the 0-bootstrap and 1-resman stages write under "service_accounts"
# in their tfvars files. Keep this list identical to VALID_NAMES in
# sa_lockdown.sh. tests/test_validation_sh.sh fails when the two lists differ.
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

# Account IDs that the 0-bootstrap and 1-resman stages give to the accounts
# behind those keys. The pattern has no anchor on the left because the stages
# put the deployment prefix in front of each ID. It matches every account that
# the previous four-name filter matched. It leaves out the "-1" and "-1r" CI/CD
# accounts, which sa_lockdown.sh does not disable.
# tests/test_validation_sh.sh fails when a stage names an account that this
# pattern misses.
SA_ID_PATTERN='(bootstrap-0r?'
SA_ID_PATTERN+='|resman-0r?'
SA_ID_PATTERN+='|security-0'
SA_ID_PATTERN+='|prod-resman-net-0r?'
SA_ID_PATTERN+='|prod-resman-sec-0r'
SA_ID_PATTERN+='|(dev|prod)-resman-(dp|gcve|gke|pf)-0r?'
SA_ID_PATTERN+='|dev-resman-sbox-0'
SA_ID_PATTERN+='|prod-resman-teams-0'
SA_ID_PATTERN+='|prod-teams-[^@]+-0)@'

IAC_PROJECT=""
PREFIX_FILTER=""

# Accounts to check and the project to pass to gcloud for each one
ACCOUNTS=()
ACCOUNT_PROJECTS=()

DISABLED_COUNT=0
ENABLED_COUNT=0
ERROR_COUNT=0

usage() {
  echo "Usage: $(basename "$0") [--project PROJECT_ID | --prefix PREFIX]"
}

# Function to add an account to the list of accounts to check, once
add_account() {
  local email="$1"
  local project="$2"
  local existing
  for existing in ${ACCOUNTS[@]+"${ACCOUNTS[@]}"}; do
    if [[ $existing == "$email" ]]; then
      return 0
    fi
  done
  ACCOUNTS+=("$email")
  ACCOUNT_PROJECTS+=("$project")
}

# Function to report a problem that prevents a complete check
report_error() {
  echo "❌ ERROR: $1" >&2
  ERROR_COUNT=$((ERROR_COUNT + 1))
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project)
      if [ $# -lt 2 ] || [ -z "$2" ] || [[ "$2" == -* ]]; then
        echo "❌ ERROR: --project requires a non-empty value." >&2
        exit 1
      fi
      IAC_PROJECT="$2"
      shift 2
      ;;
    --project=*)
      IAC_PROJECT="${1#*=}"
      if [ -z "$IAC_PROJECT" ] || [[ "$IAC_PROJECT" == -* ]]; then
        echo "❌ ERROR: --project requires a non-empty value." >&2
        exit 1
      fi
      shift
      ;;
    --prefix)
      if [ $# -lt 2 ] || [ -z "$2" ] || [[ "$2" == -* ]]; then
        echo "❌ ERROR: --prefix requires a non-empty value." >&2
        exit 1
      fi
      PREFIX_FILTER="$2"
      shift 2
      ;;
    --prefix=*)
      PREFIX_FILTER="${1#*=}"
      if [ -z "$PREFIX_FILTER" ] || [[ "$PREFIX_FILTER" == -* ]]; then
        echo "❌ ERROR: --prefix requires a non-empty value." >&2
        exit 1
      fi
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "❌ ERROR: Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ -n "$IAC_PROJECT" ] && [ -n "$PREFIX_FILTER" ]; then
  echo "❌ ERROR: --project and --prefix cannot be used together." >&2
  usage >&2
  exit 1
fi

if [ -n "$PREFIX_FILTER" ] && ! [[ "$PREFIX_FILTER" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid --prefix '$PREFIX_FILTER' (expected ^[a-z0-9-]+$)." >&2
  exit 1
fi

if [ -n "$IAC_PROJECT" ] && ! [[ "$IAC_PROJECT" =~ ^[a-z][a-z0-9-]{4,28}[a-z0-9]$ ]]; then
  echo "❌ ERROR: Invalid --project '$IAC_PROJECT' (expected valid GCP project ID)." >&2
  exit 1
fi

# With --project or --prefix the caller names one deployment, so the check
# covers the accounts of that IaC core project only
SINGLE_PROJECT=false
if [ -n "$IAC_PROJECT" ] || [ -n "$PREFIX_FILTER" ]; then
  SINGLE_PROJECT=true
fi

echo "--- Verifying Deployment Service Account Status ---"
echo ""

# Discover the Infrastructure-as-Code (IaC) core project when --project is omitted
if [ -z "$IAC_PROJECT" ]; then
  if [ -n "$PREFIX_FILTER" ]; then
    PROJECT_FILTER="projectId~'^${PREFIX_FILTER}-prod-iac-core-0$'"
    EXPECTED_SUFFIX="${PREFIX_FILTER}-prod-iac-core-0"
  else
    PROJECT_FILTER="projectId~'-prod-iac-core-0$'"
    EXPECTED_SUFFIX="-prod-iac-core-0"
  fi
  if ! IAC_PROJECT=$(gcloud projects list --filter="$PROJECT_FILTER" --format="value(projectId)"); then
    echo "❌ ERROR: Failed to list GCP projects." >&2
    exit 1
  fi
fi

# Check if a unique project was found
if [ -z "$IAC_PROJECT" ]; then
  echo "⚠️ WARNING: No IaC core project found matching '${EXPECTED_SUFFIX}'."
  exit 1
elif [ "$(printf '%s\n' "$IAC_PROJECT" | wc -l)" -ne 1 ]; then
  echo "⚠️ WARNING: Multiple possible IaC core projects found. Please re-run with --prefix or --project:"
  echo "$IAC_PROJECT"
  exit 1
fi

echo "✅ Found IaC Core Project: $IAC_PROJECT"

# Find the deployment service accounts in the IaC core project. The match runs
# here instead of in a gcloud filter so that the unit tests cover the pattern.
if ! SA_LIST=$(gcloud iam service-accounts list --project="$IAC_PROJECT" \
  --format="value(email)"); then
  echo "❌ ERROR: Failed to list service accounts in project '$IAC_PROJECT'." >&2
  exit 1
fi

while IFS= read -r sa; do
  if [[ $sa =~ $SA_ID_PATTERN ]]; then
    add_account "$sa" "$IAC_PROJECT"
  fi
done <<< "$SA_LIST"

# Add the accounts that sa_lockdown.sh reads from the tfvars files in the
# current directory. This covers accounts with custom IDs, which the pattern
# cannot find.
shopt -s nullglob
TFVARS_FILES=(./*.tfvars.json)
shopt -u nullglob

if [ ${#TFVARS_FILES[@]} -eq 0 ]; then
  echo "ℹ️ No *.tfvars.json files found in $(pwd). Checking the accounts found in $IAC_PROJECT only."
elif ! command -v jq > /dev/null; then
  report_error "jq is not installed. The accounts in ${TFVARS_FILES[*]} were not checked."
else
  for tfvars_file in "${TFVARS_FILES[@]}"; do
    # Extract the emails from every "service_accounts" block, for the same
    # keys that sa_lockdown.sh uses by default
    if ! TFVARS_ACCOUNTS=$(jq -r --arg names "${VALID_NAMES[*]}" --arg prefix "$TEAM_PREFIX" '
      ($names | split(" ")) as $valid
      | .. | .service_accounts? | objects | to_entries[]
      | select(.key as $key | any($valid[]; . == $key) or ($key | startswith($prefix)))
      | .value | strings' "$tfvars_file"); then
      report_error "jq failed to read $tfvars_file. Its accounts were not checked."
      continue
    fi

    SKIPPED_COUNT=0
    while IFS= read -r sa; do
      [ -n "$sa" ] || continue
      # Extract the project ID from the email, which has the form
      # name@project-id.iam.gserviceaccount.com
      project_id=${sa#*@}
      project_id=${project_id%.iam.gserviceaccount.com}
      if [[ $SINGLE_PROJECT == true && $project_id != "$IAC_PROJECT" ]]; then
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        continue
      fi
      add_account "$sa" "$project_id"
    done <<< "$TFVARS_ACCOUNTS"

    if [ "$SKIPPED_COUNT" -gt 0 ]; then
      echo "⚠️ WARNING: Skipped $SKIPPED_COUNT accounts in $tfvars_file that are not in project $IAC_PROJECT."
    fi
  done
fi

# Check the status of each service account
if [ ${#ACCOUNTS[@]} -eq 0 ]; then
  echo "⚠️ WARNING: No standard deployment service accounts found in $IAC_PROJECT."
else
  for ((i = 0; i < ${#ACCOUNTS[@]}; i++)); do
    sa=${ACCOUNTS[i]}
    if ! STATUS=$(gcloud iam service-accounts describe "$sa" --project="${ACCOUNT_PROJECTS[i]}" --format="value(disabled)"); then
      report_error "Failed to describe service account '$sa' in project '${ACCOUNT_PROJECTS[i]}'."
    elif [ "$STATUS" == "True" ]; then
      echo "✅ SUCCESS: $sa is disabled."
      DISABLED_COUNT=$((DISABLED_COUNT + 1))
    else
      echo "❌ FAILED: $sa is still enabled."
      ENABLED_COUNT=$((ENABLED_COUNT + 1))
    fi
  done
fi

echo ""
echo "--- Verification Complete ---"

# Pass only when every account was checked and found disabled
if [ "$ERROR_COUNT" -eq 0 ] && [ "$DISABLED_COUNT" -gt 0 ] \
  && [ "$DISABLED_COUNT" -eq "${#ACCOUNTS[@]}" ]; then
  echo "✅ All $DISABLED_COUNT deployment service accounts are disabled."
  exit 0
fi

echo "❌ Verification failed: $DISABLED_COUNT disabled, $ENABLED_COUNT still enabled, $ERROR_COUNT errors." >&2
exit 1
