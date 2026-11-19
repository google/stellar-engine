#!/bin/bash
# Copyright 2025 Google LLC
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

set -euo pipefail

IAC_PROJECT=""
PREFIX_FILTER=""

usage() {
  echo "Usage: $(basename "$0") [--project PROJECT_ID | --prefix PREFIX]"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project)
      if [ $# -lt 2 ] || [ -z "$2" ] || [[ "$2" == -* ]]; then
        echo "❌ ERROR: --project requires a non-empty value." >&2
        exit 1
      fi
      IAC_PROJECT="$2"
      shift 2
      ;;
    --project=*)
      IAC_PROJECT="${1#*=}"
      if [ -z "$IAC_PROJECT" ] || [[ "$IAC_PROJECT" == -* ]]; then
        echo "❌ ERROR: --project requires a non-empty value." >&2
        exit 1
      fi
      shift
      ;;
    --prefix)
      if [ $# -lt 2 ] || [ -z "$2" ] || [[ "$2" == -* ]]; then
        echo "❌ ERROR: --prefix requires a non-empty value." >&2
        exit 1
      fi
      PREFIX_FILTER="$2"
      shift 2
      ;;
    --prefix=*)
      PREFIX_FILTER="${1#*=}"
      if [ -z "$PREFIX_FILTER" ] || [[ "$PREFIX_FILTER" == -* ]]; then
        echo "❌ ERROR: --prefix requires a non-empty value." >&2
        exit 1
      fi
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "❌ ERROR: Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ -n "$IAC_PROJECT" ] && [ -n "$PREFIX_FILTER" ]; then
  echo "❌ ERROR: --project and --prefix cannot be used together." >&2
  usage >&2
  exit 1
fi

if [ -n "$PREFIX_FILTER" ] && ! [[ "$PREFIX_FILTER" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid --prefix '$PREFIX_FILTER' (expected ^[a-z0-9-]+$)." >&2
  exit 1
fi

if [ -n "$IAC_PROJECT" ] && ! [[ "$IAC_PROJECT" =~ ^[a-z][a-z0-9-]{4,28}[a-z0-9]$ ]]; then
  echo "❌ ERROR: Invalid --project '$IAC_PROJECT' (expected valid GCP project ID)." >&2
  exit 1
fi

echo "--- Verifying Deployment Service Account Status ---"
echo ""

# Discover the Infrastructure-as-Code (IaC) core project when --project is omitted
if [ -z "$IAC_PROJECT" ]; then
  if [ -n "$PREFIX_FILTER" ]; then
    PROJECT_FILTER="projectId~'^${PREFIX_FILTER}-prod-iac-core-0$'"
    EXPECTED_SUFFIX="${PREFIX_FILTER}-prod-iac-core-0"
  else
    PROJECT_FILTER="projectId~'-prod-iac-core-0$'"
    EXPECTED_SUFFIX="-prod-iac-core-0"
  fi
  if ! IAC_PROJECT=$(gcloud projects list --filter="$PROJECT_FILTER" --format="value(projectId)"); then
    echo "❌ ERROR: Failed to list GCP projects." >&2
    exit 1
  fi
fi

# Check if a unique project was found
if [ -z "$IAC_PROJECT" ]; then
  echo "⚠️ WARNING: No IaC core project found matching '${EXPECTED_SUFFIX}'."
  exit 1
elif [ "$(printf '%s\n' "$IAC_PROJECT" | wc -l)" -ne 1 ]; then
  echo "⚠️ WARNING: Multiple possible IaC core projects found. Please re-run with --prefix or --project:"
  echo "$IAC_PROJECT"
  exit 1
fi

echo "✅ Found IaC Core Project: $IAC_PROJECT"

# Find and check the status of each key service account
if ! SA_LIST=$(gcloud iam service-accounts list --project="$IAC_PROJECT" \
  --filter="email ~ '(bootstrap-0|resman-0|prod-resman-net-0|security-0)@'" \
  --format="value(email)"); then
  echo "❌ ERROR: Failed to list service accounts in project '$IAC_PROJECT'." >&2
  exit 1
fi

if [ -z "$SA_LIST" ]; then
  echo "⚠️ WARNING: No standard deployment service accounts found in $IAC_PROJECT."
else
  while IFS= read -r sa; do
    [ -n "$sa" ] || continue
    if ! STATUS=$(gcloud iam service-accounts describe "$sa" --project="$IAC_PROJECT" --format="value(disabled)"); then
      echo "❌ ERROR: Failed to describe service account '$sa' in project '$IAC_PROJECT'." >&2
      exit 1
    fi
    if [ "$STATUS" == "True" ]; then
      echo "✅ SUCCESS: $sa is disabled."
    else
      echo "❌ FAILED: $sa is still enabled."
    fi
  done <<< "$SA_LIST"
fi

echo ""
echo "--- Verification Complete ---"
