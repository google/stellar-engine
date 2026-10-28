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

# Syncs the modules under modules/ from upstream Cloud Foundation Fabric,
# plus the repository paths that tools/cff-sync.bases lists, such as the
# test fixtures and the README tooling.
#
# Each module records the Fabric release it was last synced from in the
# module_name of its versions.tf file, for example
# "google-pso-tool/cloud-foundation-fabric/modules/project:v38.0.0-tf". A copy
# such as organization-se records its upstream module, here organization.
# The script three-way merges every file of each module from that base
# release to the target release, so local changes survive and conflicts
# surface instead of being overwritten. Modules without a Fabric module_name
# exist only in Stellar Engine and are skipped. Python files outside modules/
# keep the repository ruff formatting, so the script formats both upstream
# sides the same way before it compares and merges them.
# docs/upstream-sync.md describes the procedure.
#
# Exit codes: 0 when the sync is clean, 3 when files conflict, 1 on errors.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IGNORE_FILE="${REPO_ROOT}/tools/cff-sync.ignore"
BASES_FILE="${REPO_ROOT}/tools/cff-sync.bases"
DEFAULT_UPSTREAM="https://github.com/GoogleCloudPlatform/cloud-foundation-fabric.git"
COMPARE_URL="https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/compare"
MODULE_NAME_RE='cloud-foundation-fabric/modules/([A-Za-z0-9_.-]+):(v[0-9]+\.[0-9]+\.[0-9]+)-tf'

TO="latest"
UPSTREAM="${DEFAULT_UPSTREAM}"
ONLY_MODULES=""
CONFLICT_STYLE="markers"
REPORT=""
DRY_RUN=0

usage() {
  cat <<EOF
Usage: tools/sync-from-cff.sh [options]

Options:
  --to TAG|latest          Fabric release to sync to. Default: latest.
  --upstream URL|PATH      Fabric repository. Default: ${DEFAULT_UPSTREAM}
  --modules NAME[,NAME]    Sync only these directories under modules/ or
                           paths from tools/cff-sync.bases.
  --conflict-style STYLE   markers leaves conflict markers in the files;
                           ours keeps the local file and only reports the
                           conflict. Default: markers.
  --report FILE            Write the Markdown report to FILE.
  --dry-run                Report what would change without writing files.
  -h, --help               Show this help.
EOF
}

die() {
  echo "sync-from-cff: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to) TO="${2:?--to needs a value}"; shift 2 ;;
    --upstream) UPSTREAM="${2:?--upstream needs a value}"; shift 2 ;;
    --modules) ONLY_MODULES="${2:?--modules needs a value}"; shift 2 ;;
    --conflict-style) CONFLICT_STYLE="${2:?--conflict-style needs a value}"; shift 2 ;;
    --report) REPORT="${2:?--report needs a value}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h | --help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $1" ;;
  esac
done

case "${CONFLICT_STYLE}" in
  markers | ours) ;;
  *) die "--conflict-style must be markers or ours" ;;
esac

cd "${REPO_ROOT}"

# Repository paths outside modules/ that tools/cff-sync.bases tracks: lines
# whose first field contains a slash, as "<local path> <upstream path> <tag>".
TRACKED_PATHS=()
if [[ -f "${BASES_FILE}" ]]; then
  while read -r path; do
    TRACKED_PATHS+=("${path}")
  done < <(awk '!/^#/ && $1 ~ /\// { print $1 }' "${BASES_FILE}")
fi

if [[ ${DRY_RUN} -eq 0 && -n "$(git status --porcelain -- modules tools/cff-sync.bases ${TRACKED_PATHS[@]+"${TRACKED_PATHS[@]}"})" ]]; then
  die "modules/, tools/cff-sync.bases or a tracked path has uncommitted changes; commit or discard them first"
fi

# PY_FORMAT formats Python source from stdin for the path in its last
# argument. CFF_SYNC_PY_FORMAT overrides it, for example in tests.
if [[ -n "${CFF_SYNC_PY_FORMAT:-}" ]]; then
  read -r -a PY_FORMAT <<<"${CFF_SYNC_PY_FORMAT}"
else
  PY_FORMAT=(uv run --project "${REPO_ROOT}" --locked --quiet ruff format
    --stdin-filename)
fi

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

# Resolves "latest" to the highest vX.Y.Z release tag upstream.
if [[ "${TO}" == "latest" ]]; then
  TO="$(git ls-remote --tags --refs "${UPSTREAM}" 'v*' |
    sed -n 's|.*refs/tags/\(v[0-9]*\.[0-9]*\.[0-9]*\)$|\1|p' |
    sort -V | tail -n 1)"
  [[ -n "${TO}" ]] || die "no release tags found in ${UPSTREAM}"
fi
[[ "${TO}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "invalid release tag: ${TO}"

# fetch_tag TAG downloads only the tree of TAG into refs/cff/TAG.
fetch_tag() {
  local tag="$1"
  if ! git rev-parse --verify --quiet "refs/cff/${tag}^{commit}" >/dev/null; then
    git fetch --quiet --no-tags --depth=1 "${UPSTREAM}" \
      "+refs/tags/${tag}:refs/cff/${tag}" ||
      die "cannot fetch ${tag} from ${UPSTREAM}"
  fi
}

# is_ignored PATH matches PATH, relative to the module, against the ignore
# list. A pattern ending in / matches a directory at any depth.
is_ignored() {
  local path="$1" pattern
  [[ -f "${IGNORE_FILE}" ]] || return 1
  while IFS= read -r pattern || [[ -n "${pattern}" ]]; do
    pattern="${pattern%%#*}"
    pattern="${pattern//[[:space:]]/}"
    [[ -n "${pattern}" ]] || continue
    if [[ "${pattern}" == */ ]]; then
      [[ "/${path}" == */"${pattern}"* ]] && return 0
    else
      # shellcheck disable=SC2053 # Glob matching is intended here.
      [[ "${path}" == ${pattern} || "${path##*/}" == ${pattern} ]] && return 0
    fi
  done <"${IGNORE_FILE}"
  return 1
}

# entry REF PATH prints "<kind>:<blob id>" for PATH in REF, where kind is L
# for a symbolic link, X for an executable file and F for any other file, or
# nothing if PATH is absent.
entry() {
  git ls-tree "$1" -- "$2" |
    awk '{ print ($1 == "120000" ? "L" : ($1 == "100755" ? "X" : "F")) ":" $3 }'
}

# local_entry PATH prints the same for a path in the work tree. A symbolic
# link hashes its target path, as Git stores it, instead of the file it
# points to.
local_entry() {
  if [[ -L "$1" ]]; then
    echo "L:$(printf '%s' "$(readlink "$1")" | git hash-object --stdin)"
  elif [[ -f "$1" && -x "$1" ]]; then
    echo "X:$(git hash-object "$1")"
  elif [[ -f "$1" ]]; then
    echo "F:$(git hash-object "$1")"
  fi
}

# write_entry ENTRY PATH replaces PATH with the blob of ENTRY, as a link or a
# file. Removing PATH first avoids writing through an existing link.
write_entry() {
  local kind="${1%%:*}" id="${1#*:}"
  mkdir -p "$(dirname "$2")"
  rm -f "$2"
  if [[ "${kind}" == "L" ]]; then
    ln -s "$(git cat-file blob "${id}")" "$2"
  else
    git cat-file blob "${id}" >"$2"
    [[ "${kind}" != "X" ]] || chmod +x "$2"
  fi
}

# formatted_entry ENTRY PATH prints ENTRY unchanged, or for a Python file
# outside modules/ the entry of its content after PY_FORMAT, which the
# script writes to the object database so write_entry can read it.
formatted_entry() {
  local entry="$1" path="$2" id
  if [[ -z "${entry}" || "${path}" == modules/* || "${path}" != *.py ||
    "${entry}" != [FX]:* ]]; then
    printf '%s\n' "${entry}"
    return 0
  fi
  id="$(git cat-file blob "${entry#?:}" | "${PY_FORMAT[@]}" "${path}" |
    git hash-object -w --stdin)" || die "cannot format ${path}"
  printf '%s:%s\n' "${entry%%:*}" "${id}"
}

# Records one result line: module, status, path. A "conflict" kept a line
# conflict, and a "conflict-kept" kept the local copy of a path that cannot
# merge line by line: a deletion on one side, a link or a binary file.
RESULTS="${WORK}/results.tsv"
: >"${RESULTS}"
record() {
  printf '%s\t%s\t%s\n' "$1" "$2" "$3" >>"${RESULTS}"
}

# Collects the modules and paths that track upstream: name, local root,
# upstream root, base tag and where the base comes from. A module_name in
# versions.tf takes precedence over tools/cff-sync.bases, which covers modules
# that upstream ships without one and the tracked repository paths.
MODULES="${WORK}/modules.tsv"
: >"${MODULES}"
SKIPPED="${WORK}/skipped.txt"
: >"${SKIPPED}"
for path in modules/*/; do
  dir="$(basename "${path}")"
  if [[ -n "${ONLY_MODULES}" && ",${ONLY_MODULES}," != *",${dir},"* ]]; then
    continue
  fi
  line=""
  if [[ -f "modules/${dir}/versions.tf" ]]; then
    line="$(grep -m 1 -E "${MODULE_NAME_RE}" "modules/${dir}/versions.tf" || true)"
  fi
  if [[ -n "${line}" ]]; then
    [[ "${line}" =~ ${MODULE_NAME_RE} ]]
    printf '%s\tmodules/%s\tmodules/%s\t%s\t%s\n' "${dir}" "${dir}" \
      "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" versions >>"${MODULES}"
    continue
  fi
  entry=""
  if [[ -f "${BASES_FILE}" ]]; then
    entry="$(awk -v d="${dir}" '!/^#/ && $1 == d { print "modules/" $2 "\t" $3; exit }' \
      "${BASES_FILE}")"
  fi
  if [[ -n "${entry}" ]]; then
    printf '%s\tmodules/%s\t%s\t%s\n' "${dir}" "${dir}" "${entry}" bases \
      >>"${MODULES}"
  else
    echo "${dir}" >>"${SKIPPED}"
  fi
done
if [[ -f "${BASES_FILE}" ]]; then
  awk '!/^#/ && $1 ~ /\// { print $1 "\t" $1 "\t" $2 "\t" $3 "\tpaths" }' \
    "${BASES_FILE}" | while IFS=$'\t' read -r name rest; do
    if [[ -z "${ONLY_MODULES}" || ",${ONLY_MODULES}," == *",${name},"* ]]; then
      printf '%s\t%s\n' "${name}" "${rest}" >>"${MODULES}"
    fi
  done
fi
[[ -s "${MODULES}" ]] || die "no modules with a Fabric module_name found"

fetch_tag "${TO}"
cut -f 4 "${MODULES}" | sort -u | while read -r tag; do
  fetch_tag "${tag}"
done
TARGET="refs/cff/${TO}"

# join ROOT PATH prints ROOT/PATH, or ROOT for the empty PATH of a tracked
# single file.
join() {
  if [[ -z "$2" ]]; then
    printf '%s\n' "$1"
  else
    printf '%s/%s\n' "$1" "$2"
  fi
}

# sync_file NAME ROOT UPSTREAM_ROOT BASE PATH merges one file of one module
# or tracked path.
sync_file() {
  local dir="$1" root="$2" up="$3" base="$4" path="$5"
  local local_path
  local_path="$(join "${root}" "${path}")"
  local b t o
  b="$(entry "refs/cff/${base}" "$(join "${up}" "${path}")")"
  t="$(entry "${TARGET}" "$(join "${up}" "${path}")")"
  # Upstream left the path alone, so neither side needs formatting.
  if [[ "${b}" == "${t}" ]]; then
    return 0
  fi
  b="$(formatted_entry "${b}" "${local_path}")"
  t="$(formatted_entry "${t}" "${local_path}")"
  o="$(local_entry "${local_path}")"

  if [[ "${b}" == "${t}" ]]; then
    return 0
  fi
  if [[ "${o}" == "${t}" ]]; then
    record "${dir}" "already-current" "${local_path}"
    return 0
  fi
  if [[ "${o}" == "${b}" ]]; then
    if [[ -z "${t}" ]]; then
      record "${dir}" "deleted" "${local_path}"
      [[ ${DRY_RUN} -eq 1 ]] || rm -f "${local_path}"
    else
      if [[ -z "${b}" ]]; then
        record "${dir}" "added" "${local_path}"
      else
        record "${dir}" "updated" "${local_path}"
      fi
      [[ ${DRY_RUN} -eq 1 ]] || write_entry "${t}" "${local_path}"
    fi
    return 0
  fi
  # Both sides changed the path. Only regular files can merge line by line.
  if [[ "${b}" != [FX]:* || "${t}" != [FX]:* || "${o}" != [FX]:* ]]; then
    record "${dir}" "conflict-kept" "${local_path}"
    return 0
  fi
  git cat-file blob "${b#?:}" >"${WORK}/base"
  git cat-file blob "${t#?:}" >"${WORK}/theirs"
  cp "${local_path}" "${WORK}/ours"
  local status=0
  git merge-file -q -L "stellar-engine" -L "fabric ${base}" \
    -L "fabric ${TO}" "${WORK}/ours" "${WORK}/base" "${WORK}/theirs" ||
    status=$?
  if [[ ${status} -eq 0 ]]; then
    record "${dir}" "merged" "${local_path}"
    [[ ${DRY_RUN} -eq 1 ]] || cp "${WORK}/ours" "${local_path}"
  elif [[ ${status} -gt 127 ]]; then
    # git merge-file fails this way on binary files.
    record "${dir}" "conflict-kept" "${local_path}"
  else
    record "${dir}" "conflict" "${local_path}"
    if [[ ${DRY_RUN} -eq 0 && "${CONFLICT_STYLE}" == "markers" ]]; then
      cp "${WORK}/ours" "${local_path}"
    fi
  fi
}

# relative_paths REF ROOT lists the files under ROOT in REF relative to ROOT,
# or an empty line when ROOT is a single file.
relative_paths() {
  if [[ "$(git cat-file -t "$1:$2" 2>/dev/null)" == "blob" ]]; then
    echo ""
  else
    git -c core.quotePath=false ls-tree -r --name-only "$1" -- "$2/" |
      sed "s|^$2/||"
  fi
}

while IFS=$'\t' read -r dir root up base source; do
  if [[ -z "$(git ls-tree "${TARGET}" -- "${up}")" ]]; then
    record "${dir}" "removed-upstream" "${up}"
    continue
  fi
  {
    relative_paths "refs/cff/${base}" "${up}"
    relative_paths "${TARGET}" "${up}"
    if [[ -f "${root}" ]]; then
      echo ""
    else
      git -c core.quotePath=false ls-files "${root}/" | sed "s|^${root}/||"
    fi
  } | sort -u >"${WORK}/files"
  while IFS= read -r path; do
    [[ -n "${path}" ]] && is_ignored "${path}" && continue
    sync_file "${dir}" "${root}" "${up}" "${base}" "${path}"
  done <"${WORK}/files"
  # With the ours style nobody resolves the kept conflicts before the commit,
  # so such a module keeps its base release and the next run merges the
  # conflicting files again.
  if [[ "${CONFLICT_STYLE}" == "ours" ]] &&
    awk -F '\t' -v d="${dir}" '$1 == d && $2 ~ /^conflict/ { f = 1 } END { exit !f }' \
      "${RESULTS}"; then
    record "${dir}" "base-kept" "${root}"
    # An updated versions.tf already names the target, so restore the base.
    if [[ ${DRY_RUN} -eq 0 && "${source}" == "versions" ]]; then
      sed -E -i.bak "s#(cloud-foundation-fabric/modules/[A-Za-z0-9_.-]+:)v[0-9]+\.[0-9]+\.[0-9]+-tf#\1${base}-tf#" \
        "${root}/versions.tf"
      rm -f "${root}/versions.tf.bak"
    fi
  elif [[ ${DRY_RUN} -eq 0 ]]; then
    # Record the target release as the new base, also when the module kept a
    # locally modified versions.tf.
    if [[ "${source}" == "versions" ]]; then
      sed -E -i.bak "s#(cloud-foundation-fabric/modules/[A-Za-z0-9_.-]+:)v[0-9]+\.[0-9]+\.[0-9]+-tf#\1${TO}-tf#" \
        "${root}/versions.tf"
      rm -f "${root}/versions.tf.bak"
    else
      awk -v d="${dir}" -v to="${TO}" \
        '!/^#/ && $1 == d { sub(/v[0-9]+\.[0-9]+\.[0-9]+$/, to) } { print }' \
        "${BASES_FILE}" >"${WORK}/bases" && cp "${WORK}/bases" "${BASES_FILE}"
    fi
  fi
done <"${MODULES}"

# provider_range TREE prints the Terraform and google provider constraints of
# the upstream project module, which tracks the repository baseline.
provider_range() {
  git show "$1:modules/project/versions.tf" 2>/dev/null |
    sed -n -E 's/^ *(required_version|version) *= *"([^"]*)".*/\1 \2/p' |
    sort -u | tr '\n' ';' | sed 's/;$//'
}

provider_major() {
  git show "$1:modules/project/versions.tf" 2>/dev/null |
    sed -n -E 's/^ *version *= *"[^"]*< *([0-9]+)\..*/\1/p' | head -n 1
}

# Lists relative module sources under modules/ that point to a missing
# directory, which happens when upstream starts calling a module that
# Stellar Engine does not vendor yet.
MISSING="${WORK}/missing.txt"
: >"${MISSING}"
if [[ ${DRY_RUN} -eq 0 ]]; then
  { grep -rnoE --include='*.tf' 'source[[:space:]]*=[[:space:]]*"\.\./[^"]*"' modules || true; } |
    while IFS=: read -r file _ match; do
      src="${match#*\"}"
      src="${src%\"}"
      src="${src%%//*}"
      if [[ ! -d "$(dirname "${file}")/${src}" ]]; then
        echo "\`${file}\` calls \`${src}\`"
      fi
    done | sort -u >"${MISSING}"
fi

OLDEST_BASE="$(cut -f 4 "${MODULES}" | sort -V | head -n 1)"
BASE_RANGE="$(provider_range "refs/cff/${OLDEST_BASE}")"
TARGET_RANGE="$(provider_range "${TARGET}")"
PROVIDER_MAJOR_CHANGE=false
if [[ "$(provider_major "refs/cff/${OLDEST_BASE}")" != "$(provider_major "${TARGET}")" ]]; then
  PROVIDER_MAJOR_CHANGE=true
fi

count() {
  awk -F '\t' -v s="$1" '$2 == s' "${RESULTS}" | wc -l | tr -d ' '
}
CONFLICTS=$(($(count conflict) + $(count conflict-kept)))
CHANGED=$(($(count updated) + $(count added) + $(count deleted) + $(count merged) + CONFLICTS))

write_report() {
  local up_names
  echo "## Cloud Foundation Fabric sync to ${TO}"
  echo
  echo "The sync merged each module from its recorded base release to ${TO}."
  echo
  echo "| Result | Files |"
  echo "| --- | --- |"
  local status
  for status in updated added deleted merged conflict conflict-kept \
    already-current; do
    echo "| ${status} | $(count "${status}") |"
  done
  echo
  echo "### Modules"
  echo
  echo "| Module or path | Upstream | Base | Updated | Added | Deleted | Merged | Conflicts |"
  echo "| --- | --- | --- | --- | --- | --- | --- | --- |"
  while IFS=$'\t' read -r dir _ up base _; do
    local row=()
    for status in updated added deleted merged conflict; do
      row+=("$(awk -F '\t' -v d="${dir}" -v s="${status}" \
        '$1 == d && index($2, s) == 1' "${RESULTS}" | wc -l | tr -d ' ')")
    done
    echo "| \`${dir}\` | \`${up}\` | ${base} | ${row[0]} | ${row[1]} | ${row[2]} | ${row[3]} | ${row[4]} |"
  done <"${MODULES}"
  echo
  if [[ "${CONFLICTS}" -gt 0 ]]; then
    echo "### Conflicts"
    echo
    if [[ "$(count conflict)" -gt 0 ]]; then
      if [[ "${CONFLICT_STYLE}" == "markers" && ${DRY_RUN} -eq 0 ]]; then
        echo "These files contain conflict markers to resolve."
      else
        echo "These files have line conflicts and kept the local copy."
      fi
      echo
      awk -F '\t' '$2 == "conflict" { printf "- `%s`\n", $3 }' \
        "${RESULTS}"
      echo
    fi
    if [[ "$(count conflict-kept)" -gt 0 ]]; then
      echo "These paths kept the local copy, because one side deleted them or"
      echo "they are links or binary files. Merge them by hand."
      echo
      awk -F '\t' '$2 == "conflict-kept" { printf "- `%s`\n", $3 }' \
        "${RESULTS}"
      echo
    fi
    if [[ "$(count base-kept)" -gt 0 ]]; then
      echo "These modules keep their base release, so the next run merges"
      echo "their conflicting files again."
      echo
      awk -F '\t' '$2 == "base-kept" { printf "- `%s`\n", $1 }' "${RESULTS}"
      echo
    fi
  fi
  if [[ -n "$(awk -F '\t' '$2 == "removed-upstream"' "${RESULTS}")" ]]; then
    echo "### Modules removed upstream"
    echo
    awk -F '\t' '$2 == "removed-upstream" { printf "- `%s`\n", $1 }' \
      "${RESULTS}"
    echo
  fi
  echo "### Version constraints"
  echo
  echo "- Base ${OLDEST_BASE}: \`${BASE_RANGE:-unknown}\`"
  echo "- Target ${TO}: \`${TARGET_RANGE:-unknown}\`"
  if [[ "${PROVIDER_MAJOR_CHANGE}" == "true" ]]; then
    echo "- The target needs a new google provider major version. Update"
    echo "  \`default-versions.tf\`, the Stellar Engine modules and the"
    echo "  documentation baseline in the same pull request."
  fi
  echo
  up_names="$(awk -F '\t' '$5 != "paths" { sub(/^modules\//, "", $3); print $3 }' \
    "${MODULES}" | sort -u)"
  echo "### Upstream modules not vendored"
  echo
  git ls-tree --name-only "${TARGET}" modules/ | sed 's|^modules/||' |
    while read -r name; do
      [[ -n "$(git ls-tree "${TARGET}" "modules/${name}/versions.tf")" ]] ||
        continue
      grep -qx "${name}" <<<"${up_names}" || echo "- \`${name}\`"
    done
  echo
  if [[ -s "${MISSING}" ]]; then
    echo "### Missing module dependencies"
    echo
    echo "These synced files call a module directory that does not exist. Vendor"
    echo "the upstream module or adapt the caller."
    echo
    sed "s|^|- |" "${MISSING}"
    echo
  fi
  if [[ -s "${SKIPPED}" ]]; then
    echo "### Stellar Engine modules skipped"
    echo
    echo "These modules have no Fabric module_name, so the sync leaves them alone."
    echo
    sed "s|.*|- \`&\`|" "${SKIPPED}"
    echo
  fi
  echo "### Breaking upstream changes"
  echo
  echo "These entries come from the upstream CHANGELOG.md files for the releases"
  echo "after ${OLDEST_BASE}, limited to the vendored modules and repository-wide"
  echo "changes. Upstream comparison: ${COMPARE_URL}/${OLDEST_BASE}...${TO}"
  echo
  breaking_changes | while IFS=$'\t' read -r release entry; do
    if [[ "${entry}" =~ ^-\ \`modules/([A-Za-z0-9_.-]+) ]]; then
      grep -qx "${BASH_REMATCH[1]}" <<<"${up_names}" || continue
    elif [[ "${entry}" =~ ^-\ \`(fast|blueprints)/ ]]; then
      continue
    fi
    echo "- ${release}: ${entry#- }"
  done
}

# breaking_changes prints "release<TAB>entry" for each BREAKING CHANGES entry
# and each incompatible change in the releases after the oldest base.
breaking_changes() {
  local file
  for file in CHANGELOG.md CHANGELOG.0.md; do
    git show "${TARGET}:${file}" 2>/dev/null || true
  done | awk -v base="${OLDEST_BASE}" '
    /^## \[v[0-9]/ {
      release = substr($2, 2, index($2, "]") - 2)
      if (release == base) { done = 1 }
      breaking = 0
      next
    }
    done { next }
    /^### / { breaking = ($0 ~ /^### BREAKING CHANGES/); next }
    release == "" { next }
    /^- / && (breaking || /incompatible change/) {
      sub(/ *<!--.*-->/, "")
      print release "\t" $0
    }'
}

if [[ -n "${REPORT}" ]]; then
  write_report >"${REPORT}"
fi

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "target=${TO}"
    echo "changed=${CHANGED}"
    echo "conflicts=${CONFLICTS}"
    echo "provider_major_change=${PROVIDER_MAJOR_CHANGE}"
  } >>"${GITHUB_OUTPUT}"
fi

echo "Synced $(wc -l <"${MODULES}" | tr -d ' ') modules and paths to ${TO}:" \
  "${CHANGED} files changed, ${CONFLICTS} conflicts."
if [[ "${CONFLICTS}" -gt 0 ]]; then
  awk -F '\t' '$2 ~ /^conflict/ { print "  " $2 ": " $3 }' \
    "${RESULTS}"
  exit 3
fi
