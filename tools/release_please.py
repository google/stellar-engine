#!/usr/bin/env python3
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
"""Prepares Release Please templates, sub-bullets, and curated PR labels."""

import argparse
import base64
import json
import os
import pathlib
import re
import sys
import urllib.request

DEFAULT_REPO = "google/stellar-engine"
RELEASE_BRANCH = "release-please-branches-main"
RELEASE_PR_LABELS = (
    "Documentation",
    "Priority - Low",
    "Level of Effort - Low",
)
SUB_BULLETS_PATH = pathlib.Path("/tmp/release_sub_bullets.json")

_COMMIT_BULLET_RE = re.compile(
    r"^\* .*?\(\[([0-9a-f]{7,40})\]\([^)\n]+/commit/[0-9a-f]+\)\)"
    r"(?:, closes [^\n]+)?\s*$"
)
_CONVENTIONAL_HEADER_RE = re.compile(r"(?i)^([a-z]+)(?:\([^)]*\))?(!)?:")
_ISSUE_BOILERPLATE_RE = re.compile(
    r"(?i)^(?:Fixes|Closes|Resolves|Part of|"
    r"No (?:separate )?(?:GitHub )?issue)\b"
)
_SENTENCE_SPLIT_RE = re.compile(
    r"(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)(?<!\b[A-Z]\.[A-Z])"
    r"(?<=[A-Za-z0-9`)\]])\.\s+(?=[A-Z`\[])"
)
_TRAILER_RE = re.compile(
    r"(?i)^(?:Co-authored-by|Signed-off-by|Reviewed-by|BREAKING[ -]CHANGE):"
)
_VISIBLE_TYPES = frozenset({"feat", "feature", "fix"})


def gh_get(path, repo=DEFAULT_REPO, token=""):
    """Fetches JSON from the GitHub REST API, returning None on error."""
    if not token:
        return None
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def normalize_gh_refs(text, repo=DEFAULT_REPO):
    """Formats issue and PR references as [#NNNN](url) and strips @mentions."""
    if not text:
        return text

    def fmt_link(owner_repo, kind, num):
        label = (
            f"#{num}"
            if owner_repo.lower() == repo.lower()
            else f"{owner_repo}#{num}"
        )
        return f"[{label}](https://github.com/{owner_repo}/{kind}/{num})"

    parts = re.split(r"(`[^`]+`|\[[^\]]+\]\([^)]+\))", text)
    out = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            m_link = re.match(
                r"^\[[^\]]+\]\(https://github\.com/"
                r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/"
                r"(issues|pull)/(\d+)(?:#[^)]*)?\)$",
                part,
            )
            out.append(fmt_link(*m_link.groups()) if m_link else part)
            continue
        s = re.sub(
            r"https://github\.com/"
            r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/"
            r"(issues|pull)/(\d+)(?:#[^\s.,;)]*)?",
            lambda m: fmt_link(*m.groups()),
            part,
        )
        s = re.sub(
            r"(?<![/\w.-])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)\b",
            lambda m: fmt_link(m.group(1), "issues", m.group(2)),
            s,
        )
        s = re.sub(
            r"(?<![&\w/\[])#([1-9]\d*)\b",
            lambda m: (
                f"[#{m.group(1)}](https://github.com/{repo}/issues/{m.group(1)})"
            ),
            s,
        )
        out.append(
            re.sub(
                r"(?<![\w/.@])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)"
                r"(?![/\w-]|\.[A-Za-z0-9_])",
                r"\1",
                s,
            )
        )
    return "".join(out)


def extract_existing(markdown_text, repo=DEFAULT_REPO):
    """Extracts section-scoped sub-bullets keyed by '<prefix><sha7>'."""
    found, prefix = {}, ""
    lines = (markdown_text or "").splitlines()
    for i, line in enumerate(lines[:-1]):
        if line.startswith(("## ", "### ")):
            prefix = "breaking:" if "breaking changes" in line.lower() else ""
            continue
        match = _COMMIT_BULLET_RE.search(line)
        if match and lines[i + 1].startswith("  * "):
            sub = normalize_gh_refs(lines[i + 1][4:].strip(), repo=repo)
            if sub:
                found.setdefault(f"{prefix}{match.group(1)[:7]}", sub)
    return found


def _first_sentence(text):
    cleaned = " ".join(text.split()).strip()
    if not cleaned:
        return ""
    sentence = _SENTENCE_SPLIT_RE.split(cleaned, maxsplit=1)[0]
    return sentence.rstrip(" .")


def fallback_sub_bullet(pr_body, message, breaking=False):
    """Extracts a deterministic one-line release summary from PR or commit."""
    note_patterns = [
        r"(?im)(?:<!--\s*release-note:\s*(.*?)\s*-->|^Release-Note:\s*(.+)$)"
    ]
    if breaking:
        note_patterns.insert(0, r"(?is)<!--\s*breaking-note:\s*(.*?)\s*-->")
    for pattern in note_patterns:
        for source in (pr_body or "", message or ""):
            match = re.search(pattern, source)
            if match:
                note = " ".join(
                    next((g for g in match.groups() if g), "").split()
                ).rstrip(" .")
                if note:
                    return note

    desc = (pr_body or "").split("## Description", 1)[-1].split("\n## ", 1)[0]
    desc = re.sub(r"<!--[\s\S]*?-->", "", desc)
    blocks, paragraph = [], []
    for raw in desc.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            if paragraph:
                blocks.append(" ".join(paragraph))
                paragraph = []
            continue
        if stripped.startswith(("- ", "* ")):
            if paragraph:
                blocks.append(" ".join(paragraph))
                paragraph = []
            bullet = re.sub(r"^\*\*[^*]+\*\*\s*:\s*", "", stripped[2:].strip())
            blocks.append(bullet)
        else:
            paragraph.append(stripped)
    if paragraph:
        blocks.append(" ".join(paragraph))

    for block in blocks:
        if (
            block.endswith(":")
            or _ISSUE_BOILERPLATE_RE.match(block)
            or _TRAILER_RE.match(block)
        ):
            continue
        summary = _first_sentence(block)
        if summary:
            return summary

    for raw in (message or "").splitlines()[1:]:
        stripped = re.sub(r"^[-*]\s*", "", raw.strip())
        if not stripped or _ISSUE_BOILERPLATE_RE.match(stripped):
            continue
        if _TRAILER_RE.match(stripped):
            break
        summary = _first_sentence(stripped)
        if summary:
            return summary
    return ""


def gemini_sub_bullet(
    title, pr_body, files, repo=DEFAULT_REPO, gemini_key="", breaking=False
):
    """Generates a single-line summary via Gemini when GEMINI_API_KEY is set."""
    if not gemini_key:
        return ""
    kind = "breaking-change migration" if breaking else "release note"
    prompt = (
        f"Write a single-line plain-English {kind} sub-bullet sentence in "
        "active present tense starting with a verb (for example: 'Wires...', "
        "'Removes...', 'Adds...', 'Updates...') that explains what changed "
        "and how it affects deployments. Format any GitHub issue or pull "
        f"request reference strictly as [#NNNN](https://github.com/{repo}/"
        "issues/NNNN) so only the hyperlinked number renders, never bare "
        "#NNNN, raw URLs, or issue/PR titles. Do not include leading bullet "
        "markers, em-dashes, ampersands, or line breaks.\n\n"
        f"Commit Title: {title}\n"
        f"Files: {', '.join(files[:15])}\n"
        f"PR Description:\n{(pr_body or '')[:3000]}"
    )
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.8-flash:generateContent?key={gemini_key}"
    )
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(
        "utf-8"
    )
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = " ".join(
            data["candidates"][0]["content"]["parts"][0]["text"].split()
        )
        text = re.sub(r"^[-*•]\s*", "", text).strip()
        if text and not text.endswith("."):
            text += "."
        return normalize_gh_refs(text, repo=repo)
    except Exception:
        return ""


def collect_sub_bullets(
    repo=DEFAULT_REPO, token="", gemini_key="", fetcher=None
):
    """Preserves curated sub-bullets and synthesizes missing summaries."""
    fetch = fetcher or (lambda path: gh_get(path, repo=repo, token=token))
    sub_bullets = {}
    owner = repo.split("/", 1)[0]

    branch_cl = fetch(f"contents/CHANGELOG.md?ref={RELEASE_BRANCH}")
    if isinstance(branch_cl, dict) and branch_cl.get("content"):
        raw_cl = base64.b64decode(branch_cl["content"]).decode(
            "utf-8", errors="replace"
        )
        sub_bullets.update(extract_existing(raw_cl, repo=repo))

    open_prs = fetch(f"pulls?head={owner}:{RELEASE_BRANCH}&state=open")
    if isinstance(open_prs, list):
        for pr in open_prs:
            sub_bullets.update(extract_existing(pr.get("body", ""), repo=repo))

    if not token:
        return sub_bullets

    manifest = fetch("contents/.github/.release-please-manifest.json?ref=main")
    last_ver = None
    if isinstance(manifest, dict) and manifest.get("content"):
        raw_manifest = base64.b64decode(manifest["content"]).decode("utf-8")
        last_ver = json.loads(raw_manifest).get(".")
    if not last_ver:
        return sub_bullets

    comparison = fetch(f"compare/v{last_ver}...main") or {}
    for commit in comparison.get("commits", []):
        sha = commit.get("sha", "")
        sha7 = sha[:7]
        message = commit.get("commit", {}).get("message") or ""
        title = message.partition("\n")[0]
        header = _CONVENTIONAL_HEADER_RE.match(title)
        visible = bool(header and header.group(1).lower() in _VISIBLE_TYPES)
        breaking = bool(
            (header and header.group(2))
            or re.search(r"(?m)^BREAKING[ -]CHANGE:", message)
        )
        missing = [
            pfx
            for pfx, needed in (("", visible), ("breaking:", breaking))
            if needed and f"{pfx}{sha7}" not in sub_bullets
        ]
        if not sha7 or not missing:
            continue

        pr_match = re.search(r"\(#(\d+)\)\s*$", title)
        pr = (fetch(f"pulls/{pr_match.group(1)}") if pr_match else None) or {}
        if "body" not in pr:
            prs = fetch(f"commits/{sha}/pulls") or []
            pr = prs[0] if prs else {}
        pr_body = pr.get("body") or ""
        files = (
            [
                f.get("filename", "")
                for f in (fetch(f"commits/{sha}") or {}).get("files", [])
            ]
            if gemini_key
            else []
        )

        for pfx in missing:
            is_breaking = pfx == "breaking:"
            summary = gemini_sub_bullet(
                title,
                pr_body,
                files,
                repo=repo,
                gemini_key=gemini_key,
                breaking=is_breaking,
            ) or fallback_sub_bullet(pr_body, message, breaking=is_breaking)
            if summary:
                normalized = normalize_gh_refs(summary.strip(), repo=repo)
                sub_bullets[f"{pfx}{sha7}"] = (
                    normalized if normalized.endswith(".") else f"{normalized}."
                )
    return sub_bullets


def _replace_exact(text, label, old, new):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected 1 occurrence of {label}, found {count}.")
    return text.replace(old, new, 1)


def patch_dist(dist_dir, sub_bullets_path=SUB_BULLETS_PATH):
    """Patches Release Please templates and bundle atomically in dist_dir."""
    dist_path = pathlib.Path(dist_dir)
    template_path = dist_path / "template1.hbs"
    index_path = dist_path / "index.js"
    hbs = template_path.read_text(encoding="utf-8")
    src = index_path.read_text(encoding="utf-8")

    hbs = _replace_exact(
        hbs,
        "Breaking Changes heading icon",
        "### \u26a0 {{title}}",
        "### {{title}}",
    )
    hbs = _replace_exact(
        hbs,
        "Breaking Changes bullet template",
        "* {{#if commit.scope}}**{{commit.scope}}:** {{/if}}{{text}}",
        "* {{#if commit.scope}}**{{commit.scope}}:** {{/if}}{{text}}"
        "{{#if commit.hash}} ([{{commit.shortHash}}]"
        "({{@root.host}}/{{@root.owner}}/{{@root.repository}}/"
        "commit/{{commit.hash}})){{/if}}",
    )

    src = _replace_exact(
        src,
        "Breaking Changes title case",
        "note.title = 'BREAKING CHANGES'",
        "note.title = 'Breaking Changes'",
    )
    src = _replace_exact(
        src,
        "PR notes delimiter",
        "const NOTES_DELIMITER = '---'",
        "const NOTES_DELIMITER = '<!-- release-please-notes -->'",
    )
    src = _replace_exact(
        src,
        "release comment suppression",
        "await this.github.commentOnIssue(comment, pullRequest.number);",
        "void 0;",
    )
    sub_path_js = json.dumps(str(sub_bullets_path))
    src = _replace_exact(
        src,
        "DefaultChangelogNotes.buildNotes parseArray",
        ".parseArray(changelogCommits, context, preset.writerOpts)\n"
        "            .trim();",
        ".parseArray(changelogCommits, context, preset.writerOpts)\n"
        "            .trim()\n"
        "            .replace(\n"
        r"              /^### .+|^[*]\s.*?\(\[([0-9a-f]{7,40})\]"
        r"\([^)\n]+\/commit\/[0-9a-f]+\)\)(?:, closes .*)?$/gm,"
        "\n"
        "              ((saved, pfx) => {\n"
        "                const p =\n"
        "                  process.env.RELEASE_SUB_BULLETS_PATH ||\n"
        f"                  {sub_path_js};\n"
        "                try {\n"
        "                  saved = JSON.parse(\n"
        "                    require('fs').readFileSync(p, 'utf8')\n"
        "                  );\n"
        "                } catch (_) {}\n"
        "                return (line, sha) => {\n"
        "                  if (!sha) {\n"
        "                    pfx = line.includes('Breaking Changes')\n"
        "                      ? 'breaking:'\n"
        "                      : '';\n"
        "                    return line;\n"
        "                  }\n"
        "                  const sb = saved[pfx + sha.slice(0, 7)];\n"
        "                  return sb ? `${line}\\n  * ${sb}` : line;\n"
        "                };\n"
        "              })({}, '')\n"
        "            );",
    )
    src = _replace_exact(
        src,
        "BranchName.ofTargetBranch",
        "return new DefaultBranchName("
        "`${RELEASE_PLEASE}--branches--${targetBranch}`);",
        "return new DefaultBranchName("
        "`${RELEASE_PLEASE}-branches-${targetBranch}`);",
    )
    src = _replace_exact(
        src,
        "AutoreleaseBranchName.matches",
        "if (branchName.startsWith(RELEASE_PLEASE_BRANCH_PREFIX)) {",
        "if (branchName.startsWith(RELEASE_PLEASE_BRANCH_PREFIX) || "
        "branchName.startsWith('release-please-branches-')) {",
    )
    src = _replace_exact(
        src,
        "DefaultBranchName DEFAULT_PATTERN",
        "const DEFAULT_PATTERN = "
        "`^${RELEASE_PLEASE}--branches--(?<branch>.+)$`;",
        "const DEFAULT_PATTERN = `^${RELEASE_PLEASE}-branches-(?<branch>.+)$`;",
    )
    src = _replace_exact(
        src,
        "DefaultBranchName.toString",
        "return `${RELEASE_PLEASE}--branches--${this.targetBranch}`;",
        "return `${RELEASE_PLEASE}-branches-${this.targetBranch}`;",
    )
    template_path.write_text(hbs, encoding="utf-8")
    index_path.write_text(src, encoding="utf-8")


def label_release_pr(release_pr_json, repo=DEFAULT_REPO, token=""):
    """Applies curated repository labels to the generated Release PR."""
    pr = json.loads(release_pr_json)
    pr_number = pr.get("number")
    if not pr_number or not token:
        return
    payload = json.dumps({"labels": list(RELEASE_PR_LABELS)}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()


def _cmd_prepare():
    repo = os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO)
    token = os.environ.get("GH_TOKEN", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    out_path = pathlib.Path(
        os.environ.get("RELEASE_SUB_BULLETS_PATH", str(SUB_BULLETS_PATH))
    )
    try:
        sub_bullets = collect_sub_bullets(
            repo=repo, token=token, gemini_key=gemini_key
        )
    except Exception as exc:
        print(f"Warning: sub-bullet collection failed: {exc}", file=sys.stderr)
        sub_bullets = {}
    out_path.write_text(json.dumps(sub_bullets), encoding="utf-8")

    runner_temp = os.environ.get("RUNNER_TEMP", "")
    if not runner_temp:
        raise RuntimeError("RUNNER_TEMP is not set.")
    actions_root = (
        pathlib.Path(runner_temp).parent
        / "_actions/googleapis/release-please-action"
    )
    dist_dirs = sorted(actions_root.glob("*/dist"))
    if not dist_dirs:
        raise RuntimeError(f"No release-please dist found under {actions_root}")
    for dist_dir in dist_dirs:
        patch_dist(dist_dir, sub_bullets_path=out_path)


def _cmd_label_pr():
    label_release_pr(
        os.environ["RELEASE_PR"],
        repo=os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO),
        token=os.environ.get("GH_TOKEN", ""),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    subparsers.add_parser("label-pr")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        _cmd_prepare()
    elif args.command == "label-pr":
        _cmd_label_pr()


if __name__ == "__main__":
    main()
