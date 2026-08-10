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

# Undelete Projects
gcloud projects undelete "${PREFIX}"-net-vdss-host 
gcloud projects undelete "${PREFIX}"-test-net-host 
gcloud projects undelete "${PREFIX}"-int-net-host 
gcloud projects undelete "${PREFIX}"-prod-net-host 

# Give projects time to be undeleted
sleep 60

# Reenable Billing
gcloud alpha billing projects link "${PREFIX}"-net-vdss-host --billing-account "${BILLING_ACCOUNT}"

if promptUser "Stage 2 - Networking"; then
  # Choose networking paradigm
  echo "Please type \"1\", \"2\", or \"3\" below that corresponds to the network paradigm you want: "
  echo "1) IL2"
  echo "2) FedRAMP High/Moderate"
  echo "3) IL4/IL5"
  read -r choice

  ########### IL2 ###########
  if [ "$choice" == 1 ]; then
    echo "This stage is still under development."

  ########### FedRAMP High/Moderate ###########
  elif [ "$choice" == 2 ]; then
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-a-fedramp-high || exit

  ########### IL4/IL5 ###########
  elif [ "$choice" == 3 ]; then
    cd "${SCRIPT_DIR}"/../fast/stages-aw/2-networking-b-il5-ngfw || exit
  fi
fi

# Import Projects
terraform import 'module.vdss-host-project.google_project.project[0]' "${PREFIX}-net-vdss-host"
terraform import 'module.env-spoke-projects["Test"].google_project.project[0]' "${PREFIX}-test-net-host"
terraform import 'module.env-spoke-projects["Int"].google_project.project[0]' "${PREFIX}-int-net-host"
terraform import 'module.env-spoke-projects["Prod"].google_project.project[0]' "${PREFIX}-prod-net-host"

# KMS
gcloud kms keys versions restore 1 --location="${REGION}" --keyring='vdss-keyring' --key=default --project="${PREFIX}"-net-vdss-host
gcloud kms keys versions enable 1 --location="${REGION}" --keyring=vdss-keyring --key=default --project="${PREFIX}"-net-vdss-host
terraform import 'module.kms.google_kms_key_ring.default[0]' projects/"${PREFIX}"-net-vdss-host/locations/"${REGION}"/keyRings/vdss-keyring
terraform import 'module.kms.google_kms_crypto_key.default["default"]' projects/"${PREFIX}"-net-vdss-host/locations/"${REGION}"/keyRings/vdss-keyring/cryptoKeys/default
