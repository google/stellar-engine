#!/usr/bin/env bash
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

# Assign Organization ID
ORG=$(gcloud organizations list --format='value(ID)')
if [[ -z "${ORG}" ]]; then
  echo "Error: Failed to get organization ID." >&2
  exit 1
fi

# Import Organization Policies - get all existing policies
policies=$(gcloud org-policies list \
  --organization="${ORG}" \
  --format='value(constraint)' 2>/dev/null)

if [[ -z "${policies}" ]]; then
  echo "No existing organization policies found to import. This is normal for a fresh deployment."
  exit 0
fi

echo "Fetching current Terraform state list..."
state_list=$(terraform state list 2>/dev/null)

rm -f imports.tf
import_count=0

# Policy Iteration
while IFS= read -r constraint_path; do
  constraint_name=${constraint_path##*/}
  constraint_self_link="organizations/${ORG}/policies/${constraint_name}"
  target_resource="module.organization.google_org_policy_policy.default[\"${constraint_name}\"]"

  # Check if constraint is declared in local configuration files
  if ! grep -rq "^${constraint_name}:" ./data/org-policies/ ./data/custom-org-policies/ 2>/dev/null; then
    continue
  fi

  # Check if already in state
  if echo "${state_list}" | grep -qF "${target_resource}"; then
    echo "${constraint_name} already managed, skipping."
  elif [[ "${constraint_name}" == custom.* ]]; then
     echo "${constraint_name} is a custom policy, skipping."
  else
    echo "Staging import for ${constraint_name}..."
    cat <<EOF >> imports.tf
import {
  to = ${target_resource}
  id = "${constraint_self_link}"
}
EOF
    ((import_count++))
  fi
done <<< "$policies"

if [[ $import_count -gt 0 ]]; then
  echo -e "\nStaged $import_count imports. Running parallel import apply..."
  terraform apply -auto-approve
  rm -f imports.tf
  echo -e "\nOrganization Policy import operation is complete!"
else
  echo "All policies are already up to date."
fi