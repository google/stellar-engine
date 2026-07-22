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

#### This script is an experimental state, and is designed to help restore environment where the prefix has not been changed
#### It is currently best used via copy-and-paste of commands as needed (after sourcing config.env)
#### You may still need to change the name of custom org policies in the yaml files for a successful deployment
#### Use this script at your own risk. The author assumes no responsibility for any damages or losses incurred through its use.

# Source config.env to get TENANT_ENVIRONMENTS
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
# shellcheck source=automation/config.env.sample
source "$SCRIPT_DIR"/config.env

terraform import "module.organization.google_org_policy_policy.default[\"{}\"]"

# Undelete projects for each tenant environment
IFS=',' read -r -a ENV_ARRAY <<< "$TENANT_ENVIRONMENTS"
for ENV_NAME in "${ENV_ARRAY[@]}"; do
  ENV_NAME=$(echo "$ENV_NAME" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]') # Ensure lowercase
  gcloud projects undelete "${PREFIX}"-"${ENV_NAME}"-net-host
done

# Give projects time to be undeleted
sleep 60

# Re-enable billing for each tenant environment
for ENV_NAME in "${ENV_ARRAY[@]}"; do
  ENV_NAME=$(echo "$ENV_NAME" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]') # Ensure lowercase
  gcloud alpha billing projects link "${PREFIX}"-"${ENV_NAME}"-net-host --billing-account "${BILLING_ACCOUNT}"
done

if promptUser "Stage 2 - Networking"; then
  # Choose networking paradigm
  echo "Please type \"1\", \"2\", or \"3\" below that corresponds to the network paradigm you want: "
  echo "1) IL2/FedRAMP Moderate"
  echo "2) FedRAMP High"
  echo "3) IL4/IL5"
  read -r choice

  ########### IL2/FedRAMP Moderate ###########
  if [ "$choice" == 1 ]; then
    echo "This stage is still under development."

  ########### FedRAMP High ###########
  elif [ "$choice" == 2 ]; then
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-a-fedramp-high || exit

  ########### IL4/IL5 ###########
  elif [ "$choice" == 3 ]; then
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-b-il5-ngfw || exit
  fi
fi

# Import projects for each tenant environment
for ENV_NAME in "${ENV_ARRAY[@]}"; do
  ENV_NAME=$(echo "$ENV_NAME" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]') # Ensure lowercase
  terraform import "module.env-spoke-projects[\"${ENV_NAME}\"].google_project.project[0]" "${PREFIX}"-"${ENV_NAME}"-net-host
done

# KMS
gcloud kms keys versions restore 1 --location="${REGIONS}" --keyring='security-keyring' --key=default --project="${PREFIX}"-net-security-host
gcloud kms keys versions enable 1 --location="${REGIONS}" --keyring=security-keyring --key=default --project="${PREFIX}"-net-security-host
terraform import 'module.kms.google_kms_key_ring.default[0]' projects/"${PREFIX}"-net-security-host/locations/"${REGIONS}"/keyRings/security-keyring
terraform import 'module.kms.google_kms_crypto_key.default["default"]' projects/"${PREFIX}"-net-security-host/locations/"${REGIONS}"/keyRings/security-keyring/cryptoKeys/default
