#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd ) 
cd "${SCRIPT_DIR}" || exit

compliance_LIST="${SCRIPT_DIR}/allowed_apis.yaml"
LZ_EXCEPTIONS="${SCRIPT_DIR}/lz_exceptions.yaml"
PLAN_FILE="tfplan"

echo "-------------------------------------------------------"
echo "Running compliance IL5 + COA2 API Cross-Check..."
echo "-------------------------------------------------------"

if [[ ! -f "$compliance_LIST" ]]; then
    echo "[ERROR] compliance list not found at $compliance_LIST"
    exit 1
fi

if [[ ! -f "$LZ_EXCEPTIONS" ]]; then
    echo "[ERROR] LZ Exceptions list not found at $LZ_EXCEPTIONS"
    exit 1
fi

ALLOWED_compliance=$(yq eval '.allowed_apis[]' "$compliance_LIST")
ALLOWED_COA2=$(yq eval '.COA2[]' "$LZ_EXCEPTIONS")

ALLOWED_APIS=$(echo -e "${ALLOWED_compliance}\n${ALLOWED_COA2}" | sort -u | sed '/^null$/d')

cd "${SCRIPT_DIR}/../fast/stages-aw/1-assured-workload" || exit 1
if [[ ! -f "$PLAN_FILE" ]]; then
    echo "Creating temporary plan for validation..."
    terraform plan -out="$PLAN_FILE" > /dev/null
fi

REQUESTED_APIS=$(terraform show -json "$PLAN_FILE" | jq -r '.resource_changes[]? | select(.type == "google_project_service") | .change.after.service' | sort -u)
MISSING_APIS=""

for api in $REQUESTED_APIS; do
    if ! echo "$ALLOWED_APIS" | grep -qx "$api"; then
        echo "[!] VIOLATION: '$api' is NOT in the compliance approved list or COA2 exceptions."
        MISSING_APIS+="$api "
    fi
done

if [[ -n "$MISSING_APIS" ]]; then
    echo -e "\n[ERROR] compliance COMPLIANCE FAILURE"
    echo "The following APIs are requested in code but missing from approved lists:"
    for missing in $MISSING_APIS; do echo "  - $missing"; done
    exit 1
else
    echo "compliance/COA2 Cross-Check Passed: All requested services are authorized."
    exit 0
fi
