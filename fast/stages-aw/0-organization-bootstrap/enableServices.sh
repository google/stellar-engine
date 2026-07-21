#!/bin/bash
list_of_services="iam cloudkms pubsub serviceusage cloudresourcemanager bigquery assuredworkloads cloudbilling logging iamcredentials orgpolicy"

for service in ${list_of_services}; do
  echo "Enabling ${service}.googleapis.com..."
  gcloud services enable "${service}.googleapis.com"
done

# printf "%s\n" iam cloudkms pubsub serviceusage cloudresourcemanager bigquery assuredworkloads cloudbilling logging iamcredentials orgpolicy | xargs -I {} gcloud services enable "{}.googleapis.com"
