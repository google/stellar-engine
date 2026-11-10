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


#### This script is an experemental state, and is designed to help restore environment where the prefix has not been changed
#### It is currently best used via copy-and-paste of commands as needed (after sourcing config.env)
#### You may still need to change the name of custom org policies in the yaml files for a succesful deployment
#### Use this script at your own risk. The author assumes no responsibility for any damages or losses incurred through its use.

terraform import "module.organization.google_org_policy_policy.default[\"{}\"]"

HOST_PROJECT="${PREFIX}-net-hub-host"
HOST_PROJECT_MODULE="module.hub-project"
IS_IL5=false

if promptUser "Stage 2 - Networking"; then
  # Choose networking paradigm
  echo "Please type \"1\", \"2\", or \"3\" below that corresponds to the network paradigm you want: "
  echo "1) IL2"
  echo "2) FedRAMP High/Moderate"
  echo "3) IL4/IL5"
  read -r choice

  ########### IL2 / FedRAMP High/Moderate ###########
  if [ "$choice" == 1 ] || [ "$choice" == 2 ]; then
    HOST_PROJECT="${PREFIX}-net-hub-host"
    HOST_PROJECT_MODULE="module.hub-project"
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-a-fedramp || exit

  ########### IL4/IL5 ###########
  elif [ "$choice" == 3 ]; then
    HOST_PROJECT="${PREFIX}-net-vdss-host"
    HOST_PROJECT_MODULE="module.vdss-host-project"
    IS_IL5=true
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-b-il5-ngfw || exit
  fi
fi

# Undelete Projects
gcloud projects undelete "${HOST_PROJECT}"
gcloud projects undelete "${PREFIX}"-test-net-host
gcloud projects undelete "${PREFIX}"-int-net-host
gcloud projects undelete "${PREFIX}"-prod-net-host

# Give projects time to be undeleted
sleep 60

# Reenable Billing
gcloud alpha billing projects link "${HOST_PROJECT}" --billing-account "${BILLING_ACCOUNT}"

# Import Projects
terraform import "${HOST_PROJECT_MODULE}.google_project.project[0]" "${HOST_PROJECT}"
terraform import 'module.env-spoke-projects["Test"].google_project.project[0]' "${PREFIX}-test-net-host"
terraform import 'module.env-spoke-projects["Int"].google_project.project[0]' "${PREFIX}-int-net-host"
terraform import 'module.env-spoke-projects["Prod"].google_project.project[0]' "${PREFIX}-prod-net-host"

# KMS (IL4/IL5 VDSS NGFW stage only)
if [ "$IS_IL5" = true ]; then
  gcloud kms keys versions restore 1 --location="${REGION}" --keyring='vdss-keyring' --key=default --project="${HOST_PROJECT}"
  gcloud kms keys versions enable 1 --location="${REGION}" --keyring=vdss-keyring --key=default --project="${HOST_PROJECT}"
  terraform import 'module.kms.google_kms_key_ring.default[0]' projects/"${HOST_PROJECT}"/locations/"${REGION}"/keyRings/vdss-keyring
  terraform import 'module.kms.google_kms_crypto_key.default["default"]' projects/"${HOST_PROJECT}"/locations/"${REGION}"/keyRings/vdss-keyring/cryptoKeys/default
fi
