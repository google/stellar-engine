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

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
STELLAR_HOME="${STELLAR_HOME:-/tmp/stellar-home}"
PREPARE_HELPER="${SCRIPT_DIR}/prepare_stages.py"
TF_VERSION="1.13.3"

LOCKS_BUCKET="gs://${CI_PROJECT_ID}-locks"
CONFIGS_BUCKET="gs://${CI_PROJECT_ID}-configs"
ACTIVE_LOCKS=()

export TF_IN_AUTOMATION=1

bootstrap_tools() {
  local need_apt=false
  if [[ ! -f /etc/ssl/certs/ca-certificates.crt ]]; then
    need_apt=true
  fi
  for cmd in jq openssl; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
      need_apt=true
    fi
  done
  if ! command -v uv >/dev/null 2>&1 && ! python3 -c "import ensurepip" >/dev/null 2>&1; then
    need_apt=true
  fi

  if [[ "${need_apt}" == "true" ]]; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
      ca-certificates \
      jq \
      openssl \
      python3-venv
  fi

  mkdir -p /tmp/ci-bin
  export PATH="/tmp/ci-bin:${PATH}"

  if ! command -v terraform >/dev/null 2>&1; then
    TF_VERSION="${TF_VERSION}" python3 - << 'EOF'
import hashlib
import os
import pathlib
import urllib.request
import zipfile

version = os.environ["TF_VERSION"]
base = f"https://releases.hashicorp.com/terraform/{version}"
zip_name = f"terraform_{version}_linux_amd64.zip"
sums_name = f"terraform_{version}_SHA256SUMS"
tmp_dir = pathlib.Path("/tmp/tf-download")
tmp_dir.mkdir(parents=True, exist_ok=True)
zip_path = tmp_dir / zip_name
sums_path = tmp_dir / sums_name

urllib.request.urlretrieve(f"{base}/{zip_name}", zip_path)
urllib.request.urlretrieve(f"{base}/{sums_name}", sums_path)

expected = None
for line in sums_path.read_text(encoding="utf-8").splitlines():
    parts = line.split()
    if len(parts) == 2 and parts[1] == zip_name:
        expected = parts[0]
        break
if not expected:
    raise RuntimeError(f"Checksum for {zip_name} not found in {sums_name}")

actual = hashlib.sha256(zip_path.read_bytes()).hexdigest()
if actual != expected:
    raise RuntimeError(
        f"Checksum mismatch for {zip_name}: expected {expected}, got {actual}"
    )

with zipfile.ZipFile(zip_path) as archive:
    archive.extract("terraform", "/tmp/ci-bin")
pathlib.Path("/tmp/ci-bin/terraform").chmod(0o755)
EOF
  fi

  if ! command -v uv >/dev/null 2>&1; then
    python3 -m venv /tmp/uv-venv
    /tmp/uv-venv/bin/pip install -q uv
    ln -sf /tmp/uv-venv/bin/uv /tmp/ci-bin/uv
  fi
}

regime_to_dir() {
  case "$1" in
    FEDRAMP_MODERATE) echo "fedramp-moderate" ;;
    FEDRAMP_HIGH)     echo "fedramp-high" ;;
    IL5)              echo "il5" ;;
    *) echo "Unknown regime: $1" >&2; exit 1 ;;
  esac
}

regime_to_net_stage() {
  case "$1" in
    FEDRAMP_MODERATE|FEDRAMP_HIGH) echo "2-networking-a-fedramp" ;;
    IL5)                           echo "2-networking-b-il5-ngfw" ;;
    *) echo "Unknown regime: $1" >&2; exit 1 ;;
  esac
}

acquire_lock() {
  local regime_dir="$1"
  local lock_uri="${LOCKS_BUCKET}/locks/${regime_dir}.lock"
  local payload
  payload=$(printf '{"trigger":"%s","sha":"%s","timestamp":%d}' \
    "${TRIGGER:-workflow_dispatch}" "${SHORT_SHA}" "$(date +%s)")

  while true; do
    if echo "${payload}" | gcloud storage cp - "${lock_uri}" --if-generation-match=0 2>/dev/null; then
      ACTIVE_LOCKS+=("${lock_uri}")
      echo "[LOCK] Acquired ${lock_uri}"
      return 0
    fi
    echo "[LOCK] Waiting 30s for ${lock_uri}..."
    sleep 30
  done
}

release_locks() {
  local exit_code=$?
  for lock_uri in "${ACTIVE_LOCKS[@]}"; do
    gcloud storage rm "${lock_uri}" 2>/dev/null || true
    echo "[LOCK] Released ${lock_uri}"
  done
  exit "${exit_code}"
}
trap release_locks EXIT

baseline_is_initialized() {
  local regime_dir="$1"
  gcloud storage ls \
    "${LOCKS_BUCKET}/baselines/${regime_dir}/fast-config/tfvars/0-bootstrap.auto.tfvars.json" \
    >/dev/null 2>&1
}

sync_handoff_from_gcs() {
  local regime_dir="$1"
  local prefix="$2"
  local fast_config_dir="${STELLAR_HOME}/envs/${prefix}/fast-config"

  mkdir -p "${fast_config_dir}"
  gcloud storage rsync \
    "${LOCKS_BUCKET}/baselines/${regime_dir}/fast-config" \
    "${fast_config_dir}" \
    --recursive >/dev/null 2>&1 || true
}

sync_handoff_to_gcs() {
  local regime_dir="$1"
  local prefix="$2"
  local fast_config_dir="${STELLAR_HOME}/envs/${prefix}/fast-config"

  gcloud storage rsync \
    "${fast_config_dir}" \
    "${LOCKS_BUCKET}/baselines/${regime_dir}/fast-config" \
    --recursive >/dev/null
}

run_stage0() {
  local repo_dir="$1"
  local prefix="$2"
  local stage_dir="${STELLAR_HOME}/envs/${prefix}/fast/stages-aw/0-bootstrap"
  local state_bucket="gs://${prefix}-prod-iac-core-bootstrap-0"
  local remote_state="false"

  if gcloud storage ls "${state_bucket}" >/dev/null 2>&1; then
    remote_state="true"
  fi

  uv run --project "${repo_dir}/cli" --frozen python "${PREPARE_HELPER}" \
    bootstrap-providers \
    --home "${STELLAR_HOME}" \
    --repo "${repo_dir}" \
    --prefix "${prefix}" \
    --remote-state "${remote_state}"

  echo "=== [${prefix}] Running terraform apply on 0-bootstrap (remote_state=${remote_state}) ==="
  if [[ "${remote_state}" == "true" ]]; then
    terraform -chdir="${stage_dir}" init -reconfigure -input=false
  else
    terraform -chdir="${stage_dir}" init -input=false
  fi
  terraform -chdir="${stage_dir}" apply -auto-approve -input=false

  if [[ "${remote_state}" == "false" ]]; then
    echo "=== [${prefix}] Migrating initial 0-bootstrap state to ${state_bucket} ==="
    uv run --project "${repo_dir}/cli" --frozen python "${PREPARE_HELPER}" \
      bootstrap-providers \
      --home "${STELLAR_HOME}" \
      --repo "${repo_dir}" \
      --prefix "${prefix}" \
      --remote-state true
    terraform -chdir="${stage_dir}" init -force-copy -input=false
    rm -f "${stage_dir}"/terraform.tfstate*
  fi
}

run_stage() {
  local prefix="$1"
  local stage="$2"
  local stage_dir="${STELLAR_HOME}/envs/${prefix}/fast/stages-aw/${stage}"

  echo "=== [${prefix}] Running terraform apply on ${stage} ==="
  terraform -chdir="${stage_dir}" init -reconfigure -input=false
  terraform -chdir="${stage_dir}" apply -auto-approve -input=false
}

apply_regime() {
  local regime="$1"
  local repo_dir="$2"
  local regime_dir net_stage tmp_tfvars prefix

  regime_dir="$(regime_to_dir "${regime}")"
  net_stage="$(regime_to_net_stage "${regime}")"
  tmp_tfvars="$(mktemp)"

  gcloud storage cp "${CONFIGS_BUCKET}/${regime_dir}/tfvars.yaml" "${tmp_tfvars}" >/dev/null
  prefix="$(
    uv run --project "${repo_dir}/cli" --frozen python "${PREPARE_HELPER}" \
      prepare-answers \
      --file "${tmp_tfvars}" \
      --repo "${repo_dir}" \
      --home "${STELLAR_HOME}"
  )"
  rm -f "${tmp_tfvars}"

  sync_handoff_from_gcs "${regime_dir}" "${prefix}"

  # Render Stages 0 and 1 against target repo_dir
  uv run --project "${repo_dir}/cli" --frozen stellar render \
    --home "${STELLAR_HOME}" \
    --repo "${repo_dir}" \
    --prefix "${prefix}" \
    --force \
    --non-interactive

  # Stage 0: Bootstrap
  run_stage0 "${repo_dir}" "${prefix}"
  sync_handoff_to_gcs "${regime_dir}" "${prefix}"

  # Verify Stage 0 auto-tfvars keep all deploy_org_resources flags false
  uv run --project "${repo_dir}/cli" --frozen python "${PREPARE_HELPER}" \
    verify-stage0-outputs \
    --home "${STELLAR_HOME}" \
    --repo "${repo_dir}" \
    --prefix "${prefix}"

  # Re-render so 1-resman links newly created Stage 0 outputs on cold bootstrap
  uv run --project "${repo_dir}/cli" --frozen stellar render \
    --home "${STELLAR_HOME}" \
    --repo "${repo_dir}" \
    --prefix "${prefix}" \
    --force \
    --non-interactive

  # Stage 1: Resource Management
  run_stage "${prefix}" "1-resman"
  sync_handoff_to_gcs "${regime_dir}" "${prefix}"

  # Prepare and render Stages 2 and 3 against Stage 0 + Stage 1 outputs
  uv run --project "${repo_dir}/cli" --frozen python "${PREPARE_HELPER}" \
    later-stages \
    --home "${STELLAR_HOME}" \
    --repo "${repo_dir}" \
    --prefix "${prefix}" \
    --net-stage "${net_stage}"

  # Stage 2: Networking
  run_stage "${prefix}" "${net_stage}"
  sync_handoff_to_gcs "${regime_dir}" "${prefix}"

  # Stage 3: Security
  run_stage "${prefix}" "3-security"
  sync_handoff_to_gcs "${regime_dir}" "${prefix}"
}

IFS=":" read -r -a TARGET_REGIMES <<< "${REGIMES:-}"
if [[ ${#TARGET_REGIMES[@]} -eq 0 || -z "${TARGET_REGIMES[0]}" ]]; then
  echo "Error: REGIMES is empty." >&2
  exit 1
fi

RUNNABLE_REGIMES=()
for reg in "${TARGET_REGIMES[@]}"; do
  regime_dir="$(regime_to_dir "${reg}")"
  if [[ "${TRIGGER:-workflow_dispatch}" == "push" ]] && ! baseline_is_initialized "${regime_dir}"; then
    echo "[SKIP] Baseline ${reg} is not initialized yet; run workflow_dispatch to bootstrap it first."
    continue
  fi
  RUNNABLE_REGIMES+=("${reg}")
done

if [[ ${#RUNNABLE_REGIMES[@]} -eq 0 ]]; then
  echo "No initialized baselines matched trigger=${TRIGGER:-workflow_dispatch}; exiting cleanly."
  exit 0
fi

bootstrap_tools

for reg in "${RUNNABLE_REGIMES[@]}"; do
  acquire_lock "$(regime_to_dir "${reg}")"
  apply_regime "${reg}" "${REPO_ROOT}"
done
