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



echo "--- Verifying Deployment Service Account Status ---"
echo ""

# Discover the Infrastructure-as-Code (IaC) core project
IAC_PROJECT=$(gcloud projects list --filter="projectId~'-prod-iac-core-0$'" --format="value(projectId)")

# Check if a unique project was found
if [ -z "$IAC_PROJECT" ]; then
  echo "⚠️ WARNING: No IaC core project found ending in '-prod-iac-core-0'."
  exit 1
elif [ $(echo "$IAC_PROJECT" | wc -l) -ne 1 ]; then
  echo "⚠️ WARNING: Multiple possible IaC core projects found. Please verify manually:"
  echo "$IAC_PROJECT"
  exit 1
fi

echo "✅ Found IaC Core Project: $IAC_PROJECT"

# Find and check the status of each key service account
SA_LIST=$(gcloud iam service-accounts list --project="$IAC_PROJECT" \
  --filter="email ~ '(bootstrap-0|resman-0|prod-resman-net-0|security-0)@'" \
  --format="value(email)")

if [ -z "$SA_LIST" ]; then
    echo "⚠️ WARNING: No standard deployment service accounts found in $IAC_PROJECT."
else
    for sa in $SA_LIST; do
      STATUS=$(gcloud iam service-accounts describe "$sa" --project="$IAC_PROJECT" --format="value(disabled)")
      if [ "$STATUS" == "True" ]; then
        echo "✅ SUCCESS: $sa is disabled."
      else
        echo "❌ FAILED: $sa is still enabled."
      fi
    done
fi

echo ""
echo "--- Verification Complete ---"
