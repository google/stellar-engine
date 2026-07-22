#!/usr/bin/env bash
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

# TODO - replace with terraform

# Assign Organization ID
ORG="$1"
if [[ -z "${ORG}" ]]; then
  echo "Error: Failed to get organization ID." >&2
  exit 1
fi

# Import Organization Policies Filtered by "SET" Constraints
policies=$(gcloud resource-manager org-policies list \
  --organization="${ORG}" \
  --filter='booleanPolicy.enforced=true OR listPolicy:*' \
  --format='value(constraint)')

if [[ -z "${policies}" ]]; then
  echo "No organization policies found matching the filter."
else
  echo -e "Importing policies...\n"

  failed_imports=()

  # Policy Iteration
  while IFS= read -r constraint_path; do
    constraint_name=${constraint_path##*/}
    constraint_self_link="organizations/${ORG}/policies/${constraint_name}"

    # Check Policy State
    if terraform state show "module.organization.google_org_policy_policy.default[\"${constraint_name}\"]" > /dev/null 2>&1; then
      # Skip Import
      echo "${constraint_name} already managed, skipping import."
    else

      # Attempt Import
      if ! terraform import \
        "module.organization.google_org_policy_policy.default[\"${constraint_name}\"]" \
        "${constraint_self_link}"; then
        echo "Error: terraform import failed for constraint: ${constraint_name}" >&2
        failed_imports+=("${constraint_name}")
      fi
    fi
  done <<< "$policies"

  if [[ ${#failed_imports[@]} -gt 0 ]]; then
    echo -e "\nError: The following organizational policies failed to import:" >&2
    for failed_policy in "${failed_imports[@]}"; do
      echo "- ${failed_policy}" >&2
    done
    exit 1
  else
    echo -e "\nOrganization Policy import operation is complete!"
  fi
fi
