# Security policy

This policy defines how to report security vulnerabilities in Stellar Engine
and when maintainers publish a GitHub Security Advisory versus a standard
release note.

## 1 Reporting vulnerabilities

Report suspected security vulnerabilities through
[Google Vulnerability Reporting][vulnz] rather than opening a public GitHub
issue or pull request. Maintainers use `https://g.co/vulnz` for intake and
triage, and respond within five working days based on report severity. Stellar
Engine is an open-source solution accelerator and is ineligible for monetary
rewards under the [Google Open Source Software VRP][oss-vrp].

## 2 Advisory scope

Maintainers publish a [GitHub Security Advisory][advisories] only when a
confirmed vulnerability affects an already-tagged `vMAJOR.MINOR.PATCH` release
and requires action on existing deployments:

* Configurations in a shipped release that break a documented security boundary
  or compliance control in `fast/stages-aw/`, `blueprints/`, or `modules/`,
  such as unintended external IAM grants or public network exposure.
* Plaintext exposure of credentials, private keys, or sensitive tokens into
  Terraform state or logs.
* Command injection, credential leakage, or privilege escalation defects in
  `cli/` or `scripts/`.

Routine security work ships through `CHANGELOG.md` and standard
[GitHub Releases](RELEASES.md) via `fix` or breaking `feat!` pull requests with
the `Security` label rather than generating a `GHSA` advisory, preventing
false-positive noise in downstream `osv.dev`, Dependabot, and Trivy scans:

* Defense-in-depth posture improvements and CIS, FedRAMP, IL4, or IL5 control
  additions.
* Static-analysis findings, linter rules, and CI workflow or development
  dependency updates.
* Defects introduced on `main` that never shipped in a tagged release.

## 3 Disclosure workflow

Maintainers coordinate confirmed release vulnerabilities privately and publish
advisories together with the patched release tag rather than on merge to `main`:

1. Confirm whether the vulnerability affects at least one tagged
   `vMAJOR.MINOR.PATCH` release.
2. Develop and validate the fix inside a draft GitHub Security Advisory private
   fork before opening a public pull request, running `bash tools/run_tests.sh`
   locally because GitHub Actions workflows do not execute on advisory private
   forks.
3. Coordinate CVE assignment through Google as a CVE Numbering Authority when
   eligible rather than requesting a CVE identifier from GitHub.
4. Merge the `fix` commit into `main` and merge the Release Please pull request
   to cut the patched `vMAJOR.MINOR.PATCH` tag before publishing the advisory.
5. Publish the GitHub Security Advisory alongside the tagged release with the
   affected version range, patched version tag, and `terraform apply` upgrade
   instructions for existing deployments.

[advisories]: https://github.com/google/stellar-engine/security/advisories
[oss-vrp]: https://bughunters.google.com/open-source-security
[vulnz]: https://g.co/vulnz
