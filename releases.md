# Release Strategy

Versioning, release classification, and release automation for
[stellar-engine](https://github.com/google/stellar-engine/).

## Versioning

`stellar-engine` follows Semantic Versioning (`vMAJOR.MINOR.PATCH`). The version
is derived from the Conventional Commits prefix on each squashed commit merged
to `main`.

| Bump | Trigger | Meaning |
| :--- | :--- | :--- |
| **Major** (`vX.0.0`) | `<type>!:` or a `BREAKING CHANGE:` footer | Requires Terraform state manipulation, state moves, or resource recreation. Ships with migration notes. |
| **Minor** (`vX.Y.0`) | `feat:` | Backwards-compatible additions. No state changes. |
| **Patch** (`vX.Y.Z`) | `fix:` | Bug fixes, security patches, non-breaking corrections. |

## Pull request titles

All PR titles targeting `main` must follow
[Conventional Commits](https://www.conventionalcommits.org/):
`<type>(<scope>): <description>`. A status check enforces this.

| Type | Purpose | Changelog |
| :--- | :--- | :--- |
| `feat` | A new feature | Features |
| `fix` | A bug fix | Bug Fixes |
| `docs` `style` `refactor` `test` `build` `ci` `chore` | Everything else | not shown |

Only `feat` and `fix` produce a CHANGELOG entry, and a release happens only when
that entry is non-empty — so they are also the only two types that cut a release.
Everything else is recorded in git history and ships with the next release.

Breaking changes are the exception: `!` or a `BREAKING CHANGE:` footer always
appears under **⚠ BREAKING CHANGES**, whatever the type. A refactor requiring
state moves must therefore be titled `refactor(modules/kms)!: ...`.

Dependency bumps use `build`, e.g. `build(deps): bump google provider to 6.12`.

### Scopes

Optional, but encouraged on `feat` and `fix`. The scope renders as a bold prefix
and is what tells a reader which part of the repository changed:

* `feat(modules/kms): add support for HSM protection level`
* `fix(fast/2-networking): correct subnet CIDR validation`
* `feat(blueprints/il5/bastion-pattern): add IAP tunnel support`

Start with the top-level area and narrow as far as is useful. For a PR spanning
several areas, pick the dominant one or omit the scope.

## Merging

`main` is squash-merge only, and the squashed commit title is taken from the PR
title. Check the title is clean before merging — it becomes the changelog entry.

## Releases

Release Please keeps one open PR titled `release: vX.Y.Z`, updating it as changes
land on `main`. Merging that PR tags the release and publishes it with the
compiled changelog. The `release` type is reserved for that bot PR.

## Labels

The Pull Request Labeler applies `Type - *` and `Framework - *` labels from the
paths you touch. They are informational only, and have no effect on versioning or
the CHANGELOG.
