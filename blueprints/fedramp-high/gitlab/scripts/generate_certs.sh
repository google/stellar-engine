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

# --- 1. CONFIGURATION ---
DOMAIN=""              # full domain for your keycloak deployment
EMAIL=""               # email of user with DNS Admin permissions
DNS_PROJECT_ID=""      # dns project

# --- 2. SETUP ENVIRONMENT ---
# Set the variable explicitly for Lego
export GCE_PROJECT="$DNS_PROJECT_ID"

# Download the Lego tool (same tool used inside the container)
echo "Downloading Lego..."
curl -Lo lego.tar.gz https://github.com/go-acme/lego/releases/download/v4.14.0/lego_v4.14.0_linux_amd64.tar.gz
tar -xzf lego.tar.gz
chmod +x lego

# --- 3. GENERATE CERTIFICATE ---
echo "Requesting Certificate for $DOMAIN..."
# --dns gcloud: Uses your Cloud Shell credentials to create the TXT record in Cloud DNS
./lego --email="$EMAIL" --domains="$DOMAIN" --dns="gcloud" --accept-tos run

# --- 4. Validate ---
# Check if lego succeeded first
if [ -f ".lego/certificates/$DOMAIN.crt" ]; then
  echo "Success"
else
  echo "Error: Certificate generation failed. Check the logs above."
fi