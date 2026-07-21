#!/bin/bash
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
