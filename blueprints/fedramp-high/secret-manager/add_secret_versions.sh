#!/bin/bash

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