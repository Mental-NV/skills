---
name: git-branching
description: Create and manage task branches, prepare focused commits, push changes, and open pull requests while preserving unrelated work and accurate contributor attribution.
---

# Git branching

Use clear, task-focused branches and preserve the repository's history,
conventions and existing work.

## Inspect before changing

- Check the working tree, current branch, remotes and upstream.
- Identify the intended base branch from repository settings or explicit
  instructions. Do not assume it is main or master.
- Preserve unrelated staged, unstaged and untracked changes. Do not discard or
  automatically stash them to make a branch operation succeed.
- Reuse an existing task branch when appropriate. Create a separate branch
  when requested or when starting unrelated work. Fetch the intended base
  before branching when remote access is available; report an unverified base.

## Name branches

Follow compatible repository conventions. Otherwise use:

- feature/short-description
- fix/short-description
- refactor/short-description
- docs/short-description
- test/short-description
- chore/short-description

Use lowercase words separated by hyphens. Describe the actual work. Existing
conventions must also satisfy the generic metadata requirements below.

## Keep Git metadata generic

New branch names, commit messages, authorship trailers, tags, and pull-request
titles/descriptions must not reference an LLM or its operating harness.

Do not add model/tool attribution through:

- Branch prefixes or suffixes.
- Co-Authored-By, Signed-off-by or similar trailers.
- Generated-by notices, signatures or promotional links.

Use the intended configured Git identity and preserve legitimate human
contributor attribution. Do not invent authors or co-authors. If the configured
identity conflicts with these requirements, resolve the intended identity
before committing.

Do not rewrite existing history or attribution without explicit authorization.

## Commit and publish

- Review the complete diff and stage only task-relevant changes. Preserve
  unrelated changes that were already staged.
- Run checks appropriate to the change.
- Write concise commits explaining the resulting behavior.
- Push only within the authorized scope and set the upstream when needed.
  Existing authorization remains valid; do not request it again unnecessarily.
- Do not force-push, delete branches, rewrite shared history or merge a pull
  request without explicit authorization.
- When a pull request is requested, verify its base and head branches and
  describe the final changes and validation accurately.

## Verify completion

Confirm the remote branch contains the intended commit. Report the branch,
commit, pull-request link when applicable, and actual check status.

If everything is already pushed, say so. Do not create an empty commit or
unnecessary branch merely to produce an action.
