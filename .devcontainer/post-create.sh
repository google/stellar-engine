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

set -e

echo "Starting post-create setup..."

# Install dependencies
echo "Installing system dependencies and Google Cloud SDK..."
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates gnupg curl jq shellcheck

# Add Google Cloud SDK
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list

# Import the Google Cloud public key
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor --yes -o /usr/share/keyrings/cloud.google.gpg

# Install the Cloud SDK
sudo apt-get update && sudo apt-get install -y google-cloud-cli

# Install python dependencies
if [ -f "tools/requirements.txt" ]; then
    echo "Installing requirements from tools/requirements.txt..."
    pip install -r tools/requirements.txt
else
    echo "Warning: tools/requirements.txt not found."
fi

# Install checkov
echo "Installing Checkov..."
pip install checkov

echo "Dev container setup complete!"
