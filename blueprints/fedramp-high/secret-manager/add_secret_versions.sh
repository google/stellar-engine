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

PROJECT_ID="your-project-id" #Update this with your project ID

SECRET_IDS=("secret-id-one" "secret-id-two")

for SECRET_ID in "${SECRET_IDS[@]}"; do
  SECRET_NAME="projects/$PROJECT_ID/secrets/$SECRET_ID"

  DATA_FILE="secrets/$SECRET_ID.txt" #Example file path, change as needed

  #Add the secret version
  if ! gcloud secrets versions add "$SECRET_NAME" \
    --data-file="$DATA_FILE" \
    --project="$PROJECT_ID"; then
    echo "Error adding version to secret $SECRET_ID"
    exit 1
  fi

done

echo "Secret versions added successfully"