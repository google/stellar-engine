#!/bin/bash
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