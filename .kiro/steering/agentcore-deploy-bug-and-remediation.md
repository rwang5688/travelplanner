---
inclusion: auto
---

# AgentCore Deploy: Credential State Loss Bug & Remediation

## Bug Summary

`agentcore deploy` silently drops the `credentials` section from `agentcore/.cli/deployed-state.json` after every successful deploy. This affects all versions through at least v0.8.0.

### Root Cause

OAuth credentials are created via API in a pre-deploy step and written to `deployed-state.json`. After CDK deploy completes, the CLI overwrites the file with only CDK-managed resources (runtimes, memories, gateways, policy engines, policies). Credentials are NOT CDK-managed, so they get silently dropped.

### Impact

- Every deploy after the first silently loses credential state
- Subsequent deploys fail at CDK synth: `Credential "FlightsMcp-oauth" not found in deployed state`
- `agentcore status` shows credentials as `local-only` even though they exist in AWS
- No AWS CLI command exists to list credential providers for recovery

### Diagnosis

1. Run `agentcore status` — credentials show as `local-only`
2. Check `agentcore/.cli/deployed-state.json` — no `credentials` section present
3. CloudFormation stack outputs don't include credential ARNs (managed outside CDK)

## CRITICAL: Restore credentials after every `agentcore deploy`

After every `agentcore deploy`, the `credentials` section will be missing from `deployed-state.json`. You MUST restore it before running another deploy.

### Preferred: Restore from git

```bash
git checkout HEAD -- agentcore/.cli/deployed-state.json
```

This works as long as the last committed version of `deployed-state.json` contains the credentials.

### Manual: Re-insert the credentials section

If git restore isn't possible (e.g., credentials were never committed), manually add the `credentials` block back into `deployed-state.json` under `targets.default.resources`.

Key details for manual restoration:
- The `credentials` key must be placed between `mcp` and `policyEngines` to match the canonical key order: `runtimes → memories → mcp → credentials → policyEngines → policies → stackName`
- Each credential entry has THREE fields: `credentialProviderArn`, `clientSecretArn`, AND `callbackUrl` — do not omit `callbackUrl`
- Credential ARNs can only be recovered from git history or from a previous backup — there is no AWS CLI command to list credential providers

### Verification

After restoring, confirm the credentials section is present:
```bash
python -c "import json; d=json.load(open('agentcore/.cli/deployed-state.json')); creds=d['targets']['default']['resources'].get('credentials',{}); print(f'{len(creds)} credentials found:', list(creds.keys()))"
```

Expected: `3 credentials found: ['FlightsMcp-oauth', 'HotelsMcp-oauth', 'travel-planner-gateway-oauth']`

## Nuclear Option: Clean Redeploy

When deployed state is too far out of sync to recover from git, do a clean redeploy:

```bash
agentcore remove all
agentcore deploy -y
```

This clears local state and recreates all resources from `agentcore.json` in one shot.

### Post-Redeploy Checklist

After a clean redeploy, runtime ARNs and endpoints change. Update:
1. Gateway URL in `agent.py` (`GATEWAY_MCP_URL`)
2. Cognito client ID/secret in `agent.py` (if new user pools were created)
3. Gateway target endpoints in `agentcore.json` (new runtime ARNs)
4. Run `agentcore status` to verify all resources show as `deployed`

## Related Cedar Policy Bugs

### Bug: Cedar "Resource stabilization failed" — Missing `has` Check

Cedar requires a `has` check before accessing optional attributes on `context.input`. Without it, deploy fails with "Resource stabilization failed".

**Wrong:**
```cedar
) when {
  context.input.max_price <= 1000
};
```

**Correct:**
```cedar
) when {
  context.input has max_price && context.input.max_price <= 1000
};
```

### Bug: CLI auto-adds `validationMode: FAIL_ON_ANY_FINDINGS`

`agentcore add policy` auto-adds `"validationMode": "FAIL_ON_ANY_FINDINGS"` to the policy entry in `agentcore.json`. Combined with the missing `has` check, this causes immediate deploy failure. Change to `IGNORE_ALL_FINDINGS` or remove the field if needed.
