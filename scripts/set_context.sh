#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: ./set-context.sh [PROJECT_ID]"
  exit 1
fi

PROJECT_ID=$1

echo "Setting context for project: $PROJECT_ID"

echo "Running: gcloud auth login..."
gcloud auth login

echo "Running: gcloud config set project $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"

echo "Running: gcloud config set billing/quota_project $PROJECT_ID..."
gcloud config set billing/quota_project "$PROJECT_ID"

echo "Running: gcloud auth application-default login..."
gcloud auth application-default login

echo "Running: gcloud auth application-default set-quota-project $PROJECT_ID..."
gcloud auth application-default set-quota-project "$PROJECT_ID"

echo "Context set successfully for project $PROJECT_ID."
