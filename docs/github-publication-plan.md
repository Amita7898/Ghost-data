# Proposed publication: amita7898/ghost-data

**Historical preparation plan.** This document was written before publication
authorization. The owner subsequently explicitly approved MIT and public publication;
see publication-status.md. The gates/commands below record the reviewed process.

## Final proposed metadata

| Field | Value |
|---|---|
| Owner | amita7898 |
| Repository | ghost-data |
| Proposed URL | https://github.com/amita7898/ghost-data |
| Description | An AI-powered data deletion auditing platform with local LLM agents, evidence verification, and an interactive investigation workspace. |
| Topics | agentic-ai, llm, python, react, fastapi, ollama, privacy, full-stack |
| Initial version | v0.4.0 (matches Python/frontend metadata; tag not created) |
| Release notes | docs/releases/v0.4.0.md (draft) |
| License | MIT recommended; explicit approval and copyright holder pending |

The URL is proposed, not a verified published project. No authenticated account or
repository-availability check was made. GitHub CLI was not found on this machine
during review. Installation/authentication are prerequisites for later commands.

## Exact current publication candidates and history

The snapshot `docs/prepublication/files.txt` enumerates every reviewed candidate
path. `docs/prepublication/files.json` records hashes (excluding its own recursive
hash), file sizes and the exact two existing commit IDs. It is a current snapshot,
not an approved final commit. A chosen LICENSE is not present and will be an
explicit approved addition. Any subsequent dependency/license/file change requires
an updated snapshot/audit and another staged-file review before publication.

Current history to retain on main:

1. 98c25551ccc7b59224ed4a047e0e6e96ed326d5f — Milestone 3 standalone checkpoint.
2. 1c780bcfcf0bc3589f29169c118e37c9bcd1a55d — Milestone 4 standalone checkpoint.
3. One future release-preparation commit containing approved M5/review files and
   approved licensing. Its hash does not exist yet and cannot be specified now.

Only `main` and, if approved, the `v0.4.0` tag should be pushed. Do not use --mirror,
--all, force-push or copy Git objects from the original competition checkout.
No restricted asset/credential pattern was found in current candidates or reachable
standalone history; no clean-history replacement is indicated by observed findings.

## Approval gates

Confirm source/contribution rights and participation terms; approve a license and
copyright holder; accept or require remediation of the moderate development-only
advisory; approve the exact staged files/history, public repository creation and
push. Approve public Git commit identity (use a verified GitHub no-reply email).
No private email or legal name is inferred from the GitHub username.

## Commands — only after explicit publication approval

Commands assume the standalone checkout, main branch, no existing origin, an
approved LICENSE already added locally, and a current reviewed file snapshot.
Stop if the target repository already exists or any assumption differs. Do not
change an existing repository's visibility or overwrite unrelated history.

First install the official [GitHub CLI](https://cli.github.com/), authenticate, and
verify the selected account. Authentication is interactive; do not paste a token
into source code, logs or shell command arguments.

```sh
# Run from the standalone ghost-data repository root.
gh --version
gh auth login --hostname github.com
gh auth status
test "$(gh api user --jq .login)" = "amita7898"
test "$(git branch --show-current)" = "main"
.venv/bin/python scripts/release_audit.py
git remote -v
```

The publication snapshot lists the current reviewed files. Add the specifically
approved LICENSE as well, then inspect everything staged. If licensing introduces
NOTICE or other files, review/include them explicitly and refresh the snapshot.

```sh
git add --pathspec-from-file=docs/prepublication/files.txt
git add -- LICENSE
git diff --cached --name-status
git diff --cached --check
git diff --cached
```

After staged-file approval, use a public commit identity. In the next command,
enter the exact verified no-reply email from your GitHub email settings; it is not
known from the username and is deliberately not invented here.

```sh
read -r release_public_email
case "$release_public_email" in
  *@users.noreply.github.com) ;;
  *) echo "Use your verified GitHub no-reply email."; exit 1 ;;
esac
git -c user.name=amita7898 -c user.email="$release_public_email" commit -m "Prepare Ghost Data v0.4.0 portfolio release"
git status --short
git log --oneline main
git log -1 --format=fuller
```

Only the following block creates a **public** repository and pushes code. It must
not be run before explicit approval of these exact external actions. Repository
creation is separated from pushing so the target can be verified before upload.

```sh
gh repo create amita7898/ghost-data --public --source=. --remote=origin --description "An AI-powered data deletion auditing platform with local LLM agents, evidence verification, and an interactive investigation workspace."
git remote get-url origin
git push --set-upstream origin main
gh repo edit amita7898/ghost-data --add-topic agentic-ai --add-topic llm --add-topic python --add-topic react --add-topic fastapi --add-topic ollama --add-topic privacy --add-topic full-stack
```

Check the real GitHub Actions run before claiming remote CI success:

```sh
gh run list --repo amita7898/ghost-data --branch main --limit 5
```

Inspect/watch the selected actual run ID and require its successful conclusion.
After successful CI, and only if the version/release is approved:

```sh
test -n "$release_public_email"
git -c user.name=amita7898 -c user.email="$release_public_email" tag -a v0.4.0 -m "Ghost Data v0.4.0"
git push origin refs/tags/v0.4.0
gh release create v0.4.0 --repo amita7898/ghost-data --verify-tag --title "Ghost Data v0.4.0" --notes-file docs/releases/v0.4.0.md
```

No binary, dataset, archive, local database or model asset is attached. Enable
private vulnerability reporting and inspect the public README/media after release.
A source release is not approval to expose the localhost application as a service.

CLI references: [create](https://cli.github.com/manual/gh_repo_create),
[metadata](https://cli.github.com/manual/gh_repo_edit),
[release](https://cli.github.com/manual/gh_release_create).
