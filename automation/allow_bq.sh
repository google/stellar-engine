#!/bin/bash

#### Use this script at your own risk. The author assumes no responsibility for any damages or losses incurred through its use.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "${SCRIPT_DIR}" || exit

# shellcheck source=automation/config.env.sample
source "${SCRIPT_DIR}"/config.env


# Mapping abbreviations
if [[ ${COMPLIANCE_REGIME} == "FEDRAMP_HIGH" ]]; then
  COMPLIANCE_REGIME="FRH"
elif [[ ${COMPLIANCE_REGIME} == "FEDRAMP_MODERATE" ]]; then
  COMPLIANCE_REGIME="FRM"
fi

aw_folder=$(gcloud resource-manager folders list --folder="${TOP_LEVEL_FOLDER_ID}" --filter="display_name:${COMPLIANCE_REGIME}-${PREFIX}" --format="value(ID)")
echo 'constraint: constraints/gcp.restrictServiceUsage' > tmp_aw_policy.yaml

gcloud resource-manager org-policies describe constraints/gcp.restrictServiceUsage --folder="${aw_folder}" --format='yaml(listPolicy.allowedValues)' >> tmp_aw_policy.yaml
{
  echo "  - bigquery.googleapis.com"
  echo "  - bigqueryconnection.googleapis.com"
  echo "  - bigquerydatapolicy.googleapis.com"
  echo "  - bigquerydatatransfer.googleapis.com"
  echo "  - bigquerymigration.googleapis.com"
  echo "  - bigqueryreservation.googleapis.com"
  echo "  - bigquerystorage.googleapis.com"

} >> tmp_aw_policy.yaml

gcloud resource-manager org-policies set-policy tmp_aw_policy.yaml --folder="${aw_folder}"