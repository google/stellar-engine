#!/bin/bash
set -e


# --- 1. CONFIGURATION ---
DOMAIN="keycloak.landingzone.example.com" # full domain for your keycloak deployment
EMAIL="admin@example.com" # email of user with DNS Admin permissions
DNS_PROJECT_ID="dino-runner-dns"

if [[ -z "$DOMAIN" || -z "$EMAIL" || -z "$DNS_PROJECT_ID" ]]; then
  echo "Error: One or more configuration variables are missing."
  echo "Please open this script and fill in:"
  echo "  - DOMAIN"
  echo "  - EMAIL"
  echo "  - DNS_PROJECT_ID"
  exit 1
fi

# --- 2. SETUP ENVIRONMENT ---
export GCE_PROJECT="$DNS_PROJECT_ID"

# Download the Lego tool (same tool used inside the container)
echo "Downloading Lego..."
curl -Lo lego.tar.gz https://github.com/go-acme/lego/releases/download/v4.14.0/lego_v4.14.0_linux_amd64.tar.gz
tar -xzf lego.tar.gz
chmod +x lego

# --- 3. GENERATE CERTIFICATE ---
echo "Requesting Certificate for $DOMAIN..."
# --dns gcloud: Uses your Cloud Shell credentials to create the TXT record in Cloud DNS
GCE_PROJECT="$DNS_PROJECT_ID" ./lego --email="$EMAIL" --domains="$DOMAIN" --dns="gcloud" --accept-tos run

# --- 4. UPLOAD TO BUCKET ---
# Check if lego succeeded first
if [ -f ".lego/certificates/$DOMAIN.crt" ]; then
  echo "Cert creation complete:"
else
  echo "Error: Certificate generation failed. Check the logs above."
fi