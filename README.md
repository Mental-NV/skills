# Skills

Reusable technical workflows, reference material, and small supporting tools.
Each skill is a self-contained directory with a `SKILL.md` entry point. The
instructions can be read directly, and the tools can be run independently.

## Available skills

| Skill | Purpose |
| --- | --- |
| [azure-github-oidc](skills/azure-github-oidc/SKILL.md) | Configure and troubleshoot exact GitHub Actions OIDC trust in Azure, including immutable subjects. |

## Use

```bash
git clone https://github.com/Mental-NV/skills.git
cd skills
```

Open the selected `SKILL.md` and follow its prerequisites and procedure. For
example, discover the exact Azure trust subject for a GitHub environment:

```bash
python3 skills/azure-github-oidc/scripts/discover_subject.py \
  --repository OWNER/REPO --environment Staging
```

This helper requires Python 3.12 or newer and an authenticated GitHub CLI. It
only reads repository metadata/settings; it does not change Azure or GitHub.
Azure administration examples have their own prerequisites and authorization
requirements in the skill's reference material.

## Optional local links

Link selected skill directories into any directory you choose:

```bash
python3 scripts/install.py --destination "$HOME/.local/share/skills" azure-github-oidc
```

The installer is idempotent and refuses to replace existing files, directories,
or links pointing elsewhere. Links refer to this checkout, so keep it in place.
Local edits are reflected immediately. On other machines, clone this repository
and repeat the command with the destination appropriate for that machine.

Update a checkout on `main` with `git pull --ff-only`. To use a fixed revision,
check out the desired commit instead.

## Validation

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check.py
```

Validation checks skill metadata and local documentation links, then runs the
supporting tools' tests. GitHub Actions runs these checks on pushes and pull
requests using Python 3.12 and 3.14. Tests run offline with controlled fixtures;
they do not verify a real Azure token exchange or grant permission for cloud
changes.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow.

## License

[MIT](LICENSE), Copyright (c) 2026 Ruslan Galiev.
