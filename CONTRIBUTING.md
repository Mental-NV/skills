# Contributing

Keep each skill focused on one practical workflow and usable independently.

1. Create a branch for the change.
2. Add or update `skills/SKILL-NAME/SKILL.md` with `name` and `description` in YAML
   frontmatter. Match the directory name to the skill name.
3. Put detailed reference material in `references/` and reusable tools in
   `scripts/` only when they help the workflow. Use relative local links.
4. State prerequisites, inputs, intended effects, verification and limitations.
   Keep instructions independent of any particular execution environment.
5. Test meaningful behavior for executable tools, including relevant failure
   cases. Keep routine tests offline; distinguish fixture results from actual
   service verification. Existing authorization remains limited to its intended
   resources and actions.
6. Run `python3 scripts/check.py` using the development environment described in
   the README, then submit a pull request to `main`.

Use generic examples. Keep credentials, access tokens, machine-specific paths,
generated output and private operational records out of the repository.

Contributions are provided under the repository's MIT license.
