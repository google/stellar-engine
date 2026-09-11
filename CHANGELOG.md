# Changelog

## [4.1.0](https://github.com/google/stellar-engine/compare/v4.0.0...v4.1.0) (2026-09-11)


### Features

* automate release management with Release Please and enforce conventional commit PR titles ([db65b3d](https://github.com/google/stellar-engine/commit/db65b3d7dec4979632f47dd3c52c7c958f925d94))
* **kms:** add test-conventional-commits-formatting ([0b3d03e](https://github.com/google/stellar-engine/commit/0b3d03e35a75e38495d504a10ab10bb079b0062d))
* **labeler:** automate pr labeling by modules, fast stages, and blueprints ([b36e20a](https://github.com/google/stellar-engine/commit/b36e20af718bf0daca70a7ac37583c1932c5358b))
* **release:** configure custom emoji-free release format with config and manifest json ([b3f2922](https://github.com/google/stellar-engine/commit/b3f29221d16b3e731747bf041e075d5cd26f3f3f))


### Bug Fixes

* **deploy.sh:** remove kms_project_id and us_keyring_name from gemini-stage-0 tfvars ([#234](https://github.com/google/stellar-engine/issues/234)) ([d843aec](https://github.com/google/stellar-engine/commit/d843aec5243d0207c048df819084b80babe307e1)), closes [#229](https://github.com/google/stellar-engine/issues/229)
* **labeler:** use verified actions/labeler v5 commit hash and make triggers explicit ([ac6e34c](https://github.com/google/stellar-engine/commit/ac6e34c236fbac333e9768f0fc8e595864ebe0b8))


### Security Updates

* **release:** fix zizmor template injection vulnerabilities by using env mappings ([89c761f](https://github.com/google/stellar-engine/commit/89c761fc72df161e2b439f60c70b9ffa348bc86d))


### Refactors

* **labeler:** simplify rules to high-level groupings for modules and blueprints ([b32c349](https://github.com/google/stellar-engine/commit/b32c349b309e5961919adcee4ca9431e41b454f7))
