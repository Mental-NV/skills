# Azure target and source-of-truth examples

Read when creating/updating federation or correcting IaC. Resolve each variable from the intended workflow, manifest and independent Azure reads. Examples do not authorize mutations.

## User-assigned managed identity

Confirm context/client ID and inspect only federation metadata:

```bash
az account show --query '{subscription:id,tenant:tenantId}' -o json
az identity show --subscription "$subscription_id" --resource-group "$resource_group" \
  --name "$identity_name" --query '{id:id,clientId:clientId,principalId:principalId}' -o json
az identity federated-credential list --subscription "$subscription_id" \
  --resource-group "$resource_group" --identity-name "$identity_name" \
  --query '[].{name:name,id:id,issuer:issuer,subject:subject,audiences:audiences}' -o json
```

For an existing credential whose only mismatch is its subject:

```bash
az identity federated-credential update --subscription "$subscription_id" \
  --resource-group "$resource_group" --identity-name "$identity_name" \
  --name "$federation_name" --subject "$oidc_subject" --only-show-errors -o none
```

For a missing credential, use `az identity federated-credential create` with the same target arguments and explicit `--issuer`, `--subject`, `--audiences`. Independently call `show` and compare the three fields afterward. Do not recreate the identity or rotate its client ID for a subject mismatch. System-assigned identities are not interchangeable with this user-assigned identity model.

Example Bicep binding (identity already exists in the selected group):

```bicep
param identityName string
param federationName string
param oidcSubject string
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: identityName
}
resource federation 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: identity
  name: federationName
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: oidcSubject
    audiences: ['api://AzureADTokenExchange']
  }
}
```

This illustrates exact binding, not a required API version/new template. Prefer the project's supported version. Pass discovered subjects as non-secret parameters; do not reconstruct name-only prefixes.

## Entra application registration

Resolve the workflow client ID with `az ad app show --id "$client_id"` and confirm `appId`/application `id`. Inspect `az ad app federated-credential list --id "$application_id"`. Use this application identifier, not an unrelated enterprise application's service-principal object ID.

Build JSON containing `name`, `issuer`, `subject`, `audiences` and any existing description to preserve. `az ad app federated-credential create --id "$application_id" --parameters "$credential_json_path"` creates trust; `update` additionally takes `--federated-credential-id`. Read it back afterward. This command family uses Graph, not the managed-identity ARM API.

## Evidence and environment policy

Azure accepting a credential validates its resource shape, not whether GitHub issues its subject. Preserve a sanitized before/after comparison and verify actual Actions login separately. Serialize changes per identity and allow propagation.

Environment trust identifies jobs for that environment, not a branch by itself. Keep deployment branch/protection policies aligned with intended events. Broadening subjects/disabling protections does not repair a mismatch.

Observed failure: Azure trusted `repo:OWNER/REPO:environment:Staging`; GitHub asserted `repo:OWNER@OWNER_ID/REPO@REPO_ID:environment:Staging`. Exact-subject repair plus bootstrap discovery addressed the mismatch. Matching names alone had appeared correct in provisioning readbacks; actual token exchange remains essential.

CLI references: [managed-identity federation](https://learn.microsoft.com/en-us/cli/azure/identity/federated-credential), [application federation](https://learn.microsoft.com/en-us/cli/azure/ad/app/federated-credential).
