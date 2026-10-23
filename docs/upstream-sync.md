# Upstream sync

Stellar Engine vendors the reusable modules under `modules/`, the README tooling and its test fixtures from upstream [Cloud Foundation Fabric](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric), and a weekly pull request keeps them close to the latest Fabric release. Small, regular syncs keep upstream fixes flowing in and keep each merge reviewable.

<!-- BEGIN TOC -->
- [1. Base release tracking](#1-base-release-tracking)
- [2. Sync procedure](#2-sync-procedure)
- [3. Review checklist](#3-review-checklist)
- [4. Local changes](#4-local-changes)
- [5. Weekly workflow](#5-weekly-workflow)
- [6. Sync cadence](#6-sync-cadence)
<!-- END TOC -->

## 1. Base release tracking

Every synced module records the Fabric release it last merged, so the sync knows the common ancestor of the local and the upstream copy.

- The `module_name` in a module's `versions.tf` file records the release, such as `google-pso-tool/cloud-foundation-fabric/modules/project:<tag>-tf`.
- A Stellar Engine copy such as `modules/organization-se/` records the upstream module that it tracks, here `organization`.
- The `tools/cff-sync.bases` file records the release for modules that upstream ships without a `module_name`, such as `modules/cloud-config-container/`.
- Modules with neither record exist only in Stellar Engine, such as `modules/cis-log-metrics/`, and the sync leaves them alone.
- The `tools/cff-sync.bases` file also records the release of each tracked repository path outside `modules/`. Such an entry names a directory or a single file, and its local path contains a slash, which sets it apart from a module entry.
- The tracked paths are the `tools/tfdoc.py` and `tools/check_documentation.py` README tools, the `tests/examples/utils.py` directive parser that `tools/tfdoc.py` imports, and the `tests/fixtures/` files that module README examples name.
- Python files outside `modules/` keep the repository `ruff format` style. The script formats the base and the target copy the same way before it compares and merges them, so the indentation difference from upstream never conflicts.
- The `tools/cff-sync.ignore` file lists paths that the sync never writes, such as the OpenTofu `versions.tofu` files that `.gemini/styleguide.md` forbids.

The stages under `fast/stages-aw/` derive from the FAST stage generation that Fabric replaced in v44.0.0 and removed in v47.0.0. The sync never touches them, so maintainers port stage changes from upstream by hand.

## 2. Sync procedure

The `tools/sync-from-cff.sh` script three-way merges each file of each tracked module from its base release to the target release.

1. Start from a clean `modules/` directory and clean tracked paths on a new branch.
2. Preview the result with `tools/sync-from-cff.sh --to <tag> --dry-run --report /tmp/cff-sync.md`.
3. Run the sync with `tools/sync-from-cff.sh --to <tag>`. The `--to latest` option picks the newest release tag.
4. Resolve the conflict markers that the script leaves in files that both sides changed, and merge by hand the paths that the report lists as kept, such as a file that one side deleted.
5. Commit the merged files, `tools/cff-sync.bases` and the updated `module_name` lines together.

The script fetches only the trees of the base and target releases into `refs/cff/<tag>`. Remove those refs with `git for-each-ref --format='%(refname)' refs/cff | xargs -n1 git update-ref -d` when you no longer need them.

The `--conflict-style ours` option keeps the local copy of every conflicting file and only reports it. A module with such conflicts keeps its base release, so a later run with conflict markers merges the same files again.

The script exits with status 0 for a clean merge, 3 when files conflict, and 1 on errors. Its report lists the per-module results, the Terraform and provider constraint changes, the upstream modules that Stellar Engine does not vendor, and the upstream breaking changes since the base release.

## 3. Review checklist

A sync pull request merges only after these checks pass.

- No conflict markers remain, and each resolution keeps the local changes in section 4 unless upstream now provides them.
- Every root under `fast/stages-aw/` and `blueprints/` passes `terraform init -backend=false` and `terraform validate`, and callers follow every module interface change that the report lists.
- The repository baseline in `default-versions.tf`, `.gemini/styleguide.md` and the documentation matches the provider and Terraform versions that the synced modules require.
- The README of every module with a local interface change has tables regenerated with the `tools/tfdoc.py` script, which the sync keeps at the target Fabric release.
- `bash tools/lint.sh` and `bash tools/run_tests.sh` pass.
- A fresh deployment of stages 0 to 3 and a plan against an existing deployment of the previous release both succeed in a test organization.
- The pull request has a Breaking Changes section with an `upgrade-note` whenever callers, tfvars files or state need changes.

## 4. Local changes

Stellar Engine keeps these changes on top of the upstream modules and tracked paths. Each sync preserves them until upstream ships an equivalent, and then removes the entry here.

| Module or path | Local change |
| --- | --- |
| `project` | A precondition fails when the prefixed project ID or name exceeds 30 characters. |
| `project` | Terraform ignores `auto_create_network` and a `gcloud` step deletes the default network. |
| `project` | The Cloud KMS service agent gets no automatic IAM grant, and the module does not look up the BigQuery default service account. |
| `iam-service-account` | A precondition fails when the service account ID exceeds 30 characters. |
| `folder` | The module picks the `CONSUMER_FOLDER` resource from the Assured Workloads workload and caps the display name at 30 characters. |
| `organization-se` | The copy of `organization` drops tags, prefixes custom constraint and policy names, joins additive IAM keys with `//`, and accepts flat `condition_vars`. |
| `spanner-instance`, `spanner-instance-se` | Databases default to deletion protection, and the copy defaults to the `ENTERPRISE` edition. |
| `cloudsql-instance` | The `psc_config` block is always present, and backups survive instance deletion by default. |
| `net-lb-app-ext-regional` | Backend services support a strong session affinity cookie. |
| `net-lb-app-ext` | The module passes `port_name` through without a protocol-derived default. |
| `net-vpc-firewall` | Firewall rules log with all metadata unless a rule opts out. |
| `datafusion`, `datafusion-se` | The instance logs with all metadata, and the copy carries a Stellar Engine implementation. |
| `gke-cluster-standard`, `gke-cluster-autopilot` | The control plane public endpoint stays disabled unless a caller enables it. |
| `gke-cluster-standard-se` | Every cluster registers with a fleet, by default in its own project. |
| `gke-cluster-standard`, `gke-cluster-standard-se` | Shielded GKE Nodes default to on. |
| `pubsub` | The module keeps the `name` output. |
| `net-vpc-peering` | Variable descriptions are more detailed. |
| `tools/tfdoc.py` | The script follows the repository Python style, creates missing parser contexts, matches the README markers non-greedily, and escapes pipes in output descriptions. |
| `tools/check_documentation.py` | The labels name each failure, the description, order, period and type checks run only on READMEs with tables, and output description failures report their own state. |
| `tests/examples/utils.py` | The parser follows the repository Python style and drops unused imports. |

The `cloud-run-v2-se` copy matches the upstream `cloud-run-v2` module since the v59.2.0 sync, so a later change can point its callers to `modules/cloud-run-v2/` and remove the copy.

## 5. Weekly workflow

The `.github/workflows/cff-sync.yml` workflow runs the sync every Monday against the latest Fabric release and keeps one pull request open on the `chore/cff-sync` branch.

- The workflow runs the script with `--conflict-style ours`, so the branch never holds conflict markers, and the pull request body lists each conflict for a maintainer to resolve.
- A maintainer resolves the conflicts on the `chore/cff-sync` branch by running the script with conflict markers there and pushing the result.
- The workflow never overwrites a branch that holds commits from anyone but the bot, and comments on the pull request once per new release instead.
- The workflow opens the pull request as a draft when files conflict or when the release needs a new provider major version.
- A maintainer can start a run for a specific release from the Actions tab with the `to` input.
- The workflow sets up uv before the sync, because the script formats tracked Python files with the `ruff` version that the root `uv.lock` file pins.

The workflow needs repository configuration that only maintainers can set.

- Pull requests that the default `GITHUB_TOKEN` opens do not trigger other workflows, so CI does not run on them. Create a GitHub App with the `contents: write` and `pull-requests: write` permissions, install it on the repository, and store its client ID in the `CFF_SYNC_APP_CLIENT_ID` variable and its private key in the `CFF_SYNC_APP_PRIVATE_KEY` secret.
- Without the app, the workflow falls back to `GITHUB_TOKEN`. That fallback needs the "Allow GitHub Actions to create and approve pull requests" repository setting, and a maintainer then closes and reopens the pull request to start CI.
- Commits from the workflow carry a bot identity, so maintainers decide how those commits satisfy the Google CLA check.

## 6. Sync cadence

Fabric ships about one major and two minor releases a month, so the weekly pull request usually carries one or two releases.

- Maintainers review and merge the open sync pull request at least once a month, so a merge never spans more than a few releases.
- A release that needs a new provider major version stays a draft until a pull request migrates the stages, blueprints and Stellar Engine modules to that provider.
- Fixes that Stellar Engine needs before the next sync go upstream first when possible, so the next sync brings them back without a local change.
