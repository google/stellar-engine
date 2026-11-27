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

deploy_org_policies=$(
  echo 'var.deploy_org_resources.org_policies' \
    | terraform console 2>/dev/null \
    | tr -d '[:space:]'
)

if [[ "${deploy_org_policies}" == "false" ]]; then
  folder_resource=$(
    echo 'local.assured_workload_folder' \
      | terraform console 2>/dev/null \
      | tr -d '"[:space:]'
  )
  folder_id="${folder_resource#folders/}"
  if [[ -z "${folder_resource}" || "${folder_resource}" == "null" || ! "${folder_id}" =~ ^[0-9]+$ ]]; then
    echo "Error: local.assured_workload_folder is not yet created in state. Apply the bootstrap stage before running import.sh in folder mode." >&2
    exit 1
  fi

  # Import Folder Policies - get all existing policies on the AW root folder
  policies=$(gcloud org-policies list \
    --folder="${folder_id}" \
    --format='value(constraint)' 2>/dev/null)
  declared_policies=$(echo 'keys(local._root_folder_org_policies)' | terraform console 2>/dev/null)
  link_prefix="folders/${folder_id}/policies"
  target_prefix="module.root-folder-config[0].google_org_policy_policy.default"
  policy_scope="folder ${folder_id}"
else
  # Assign Organization ID: first argument, then ORGANIZATION_ID from the
  # environment, then gcloud - but only when exactly one organization is
  # visible. A deployer that can see several organizations gets a multi-line
  # list back, which would otherwise be spliced into every policy resource name
  # below.
  ORG="${1:-${ORGANIZATION_ID:-}}"
  if [[ -z "${ORG}" ]]; then
    orgs=()
    while IFS= read -r org_id; do
      if [[ -n "${org_id}" ]]; then
        orgs+=("${org_id}")
      fi
    done < <(gcloud organizations list --format='value(ID)' | sed '/^[[:space:]]*$/d')
    if [[ -n "${orgs[1]:-}" ]]; then
      echo "Error: more than one organization is visible (${orgs[*]}). Pass the organization ID as the first argument or set ORGANIZATION_ID." >&2
      exit 1
    fi
    ORG="${orgs[0]:-}"
  fi
  if [[ -z "${ORG}" ]]; then
    echo "Error: Failed to get organization ID." >&2
    exit 1
  fi

  # Import Organization Policies - get all existing policies
  policies=$(gcloud org-policies list \
    --organization="${ORG}" \
    --format='value(constraint)' 2>/dev/null)
  declared_policies=$(echo 'keys(local.org_policies)' | terraform console 2>/dev/null)
  link_prefix="organizations/${ORG}/policies"
  target_prefix="module.organization.google_org_policy_policy.default"
  policy_scope="organization ${ORG}"
fi

if [[ -z "${policies}" ]]; then
  echo "No existing ${policy_scope} policies found to import. This is normal for a fresh deployment."
  exit 0
fi

echo "Fetching current Terraform state list..."
state_list=$(terraform state list 2>/dev/null)

rm -f imports.tf
import_count=0

# Policy Iteration
while IFS= read -r constraint_path; do
  [[ -n "${constraint_path}" ]] || continue
  constraint_name=${constraint_path##*/}
  constraint_self_link="${link_prefix}/${constraint_name}"
  target_resource="${target_prefix}[\"${constraint_name}\"]"

  # Check if constraint is declared in local configuration files
  if ! echo "${declared_policies}" | grep -qF "\"${constraint_name}\""; then
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
    import_count=$((import_count + 1))
  fi
done <<< "${policies}"

if [[ ${import_count} -gt 0 ]]; then
  printf '\nStaged %d imports. Running parallel import apply...\n' "${import_count}"
  terraform apply -auto-approve
  rm -f imports.tf
  printf '\nOrganization Policy import operation is complete!\n'
else
  echo "All policies are already up to date."
fi