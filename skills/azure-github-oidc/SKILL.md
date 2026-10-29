---
name: azure-github-oidc
description: Create, repair, or review GitHub Actions OIDC federation with Azure managed identities or Entra applications, including AADSTS700213 subject mismatches and immutable repository/owner IDs. Use for Azure login trust and its bootstrap/IaC; ordinary application deployment without identity changes does not require this skill.
---

# Azure federation for GitHub Actions

Make Azure trust the exact claims GitHub emits for the intended job. Successfully creating a federated credential does not prove that token exchange will succeed.

## Discover before creating trust

Read the workflow, identity configuration and failing login's sanitized claim details. Establish the repository, actual job environment/event, Azure tenant/subscription, identity client ID and identity resource type. Use existing task authorization; this skill does not authorize extra environments, RBAC changes or deployment retries.

Inspect metadata and OIDC settings instead of guessing from repository names or creation dates:

```bash
gh api repos/OWNER/REPO
gh api repos/OWNER/REPO/actions/oidc/customization/sub
```

For default public GitHub subjects, run the bundled read-only helper from this skill's directory:

```bash
python3 scripts/discover_subject.py --repository OWNER/REPO --environment Staging
```

It checks immutable IDs, subject mode and reported prefix, and emits non-secret trust JSON. Alternatives: `--branch main`, `--tag v1`, or `--pull-request` for jobs without an environment. Add `--observed-subject 'repo:...'` to compare with a sanitized assertion subject from the failing job. Override `--audience` only to match the action's explicitly configured audience.

Essential distinctions:

- Immutable mode uses `repo:OWNER@OWNER_ID/REPO@REPO_ID`; legacy mode uses `repo:OWNER/REPO`. Preserve exact case, IDs and context. Never remove IDs to fit an old template.
- Jobs referencing an environment use `:environment:NAME`, even on PRs or `main` pushes. Without an environment, PR jobs use `:pull_request`; otherwise use the branch/tag ref. Colons inside context values become `%3A`.
- Checking out the PR head does not change the job's OIDC context. Do not derive its subject from the checkout branch, merge ref or `job_workflow_ref` unless a custom template explicitly uses those claims.
- The helper supports the default public GitHub template. Missing/inaccessible, inherited/custom or inconsistent settings stop automatic construction. Inspect the effective template and actual non-secret claim values from an authorized job. Do not reset GitHub's template or assume legacy mode to make discovery pass. GitHub Enterprise Server and sovereign clouds require their actual issuer, subject format and audience.
- Azure public cloud usually uses issuer exactly `https://token.actions.githubusercontent.com` and audience `api://AzureADTokenExchange`. Match the job's actual settings, including case and trailing slashes. Never log/save/paste JWTs, access tokens, provider keys or complete credential dumps. An observed subject is useful evidence, not a verified JWT.

## Reconcile the intended identity

Before mutation, resolve the configured client ID to the actual identity and confirm tenant/subscription/scope. Read existing federation metadata. Distinguish a user-assigned managed identity (ARM) from an Entra application registration (Graph); client IDs, application object IDs and service-principal object IDs differ.

Read [references/azure-trust.md](references/azure-trust.md) for CLI and IaC examples when creating/updating trust. Prefer the project's supported tools and IaC conventions.

Create a missing credential or update the intended existing credential to the exact verified issuer/subject/audience. For a subject-only mismatch, preserve its resource/name and other matching fields. Keep the user's environment separation, resource names and role scope. A trust mismatch does not justify broad roles, wildcard subjects, another environment's trust, client secrets or publish profiles. If identity creation/RBAC is requested, use the selected identity model and permissions required for that target.

Fix the source of truth alongside an authorized live correction. Bootstrap must discover the actual format before creating identities or requesting unrelated secrets. Pass the verified full subject (or validated prefix plus exact context) into IaC. Avoid a wizard/hardcoded name-only template that recreates the failure. Support custom templates when the project needs them; do not universally require default templates.

Check deployment-job `id-token: write`, Azure/login client/tenant/subscription IDs, the actual job environment and its deployment branch policy. Preserve existing fork/Dependabot restrictions and avoid executing untrusted PR code with credentials.

## Verify the actual boundary

1. Independently read back issuer, subject and audience; compare exactly and verify identity/client ID/scope remain intended. Check each authorized environment separately.
2. Compile affected IaC. Test immutable/legacy modes, environment/PR/ref contexts and inconsistent settings. Helper regression command: `python3 -m unittest discover -s scripts -p 'test_*.py'`.
3. When authorized, run a bounded login-only Actions check in the same context, or retry the intended failed job if its deployment side effects are authorized. Local `az login` or readback cannot prove GitHub token exchange. An old commit's deployment may be rejected by freshness checks.
4. Allow propagation with bounded retries when readback matches. If fresh claims still fail, stop repeated mutations/retries and investigate the discrepancy. Login success followed by `AuthorizationFailed` is a separate permission problem; inspect the denied action instead of weakening federation.
5. Report configured subjects, affected identities/environments, source fix and verification level. State when Actions exchange/deployment remains pending. Skill/local test success does not establish cloud deployment success.

## Primary references

Verify current documentation when APIs or formats differ:

- [GitHub OIDC and immutable subjects](https://docs.github.com/en/actions/reference/security/oidc)
- [Repository OIDC settings API](https://docs.github.com/en/rest/actions/oidc)
- [Azure exact-match trust requirements](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust-user-assigned-managed-identity)
- [Azure/login OIDC](https://github.com/Azure/login#login-with-openid-connect-oidc-recommended)
