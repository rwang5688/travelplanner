---
inclusion: manual
---

# Bug Report: AgentCore CLI silently drops credentials from deployed-state.json after every deploy

## Summary
`agentcore deploy` overwrites `deployed-state.json` after CDK deploy completes, dropping the `credentials` section that was written during the pre-deploy "Creating OAuth credentials" step. This causes subsequent deploys to fail at CDK synth with `Credential "X" not found in deployed state`.

## Environment
- AgentCore CLI: v0.7.1 (`@aws/agentcore`), CDK-backed
- OS: Windows 11
- Region: us-east-1

## Steps to Reproduce
1. Have a working project with credentials, gateway, runtimes, and memory deployed
2. Add a new resource (e.g., policy engine) to `agentcore.json`
3. Run `agentcore deploy -y`
4. Deploy succeeds
5. Check `agentcore/.cli/deployed-state.json` — `credentials` section is gone
6. Run `agentcore deploy -y` again
7. CDK synth fails: `Credential "FlightsMcp-oauth" not found in deployed state`

## Expected Behavior
The CLI should merge credential state into `deployed-state.json` after CDK deploy, preserving credential ARNs alongside runtimes, memories, gateways, and policy engines.

## Actual Behavior
The CLI overwrites `deployed-state.json` with only CDK-managed resources (runtimes, memories, gateways, policy engines). Credentials are created via API in a pre-deploy step and are NOT CDK-managed, so they get silently dropped every deploy.

## Evidence
- Commit `620c02e`: First gateway deploy — `deployed-state.json` contains credentials with real ARNs ✅
- Commit `6541d52`: Memory deploy — `deployed-state.json` overwritten, credentials section gone ❌
- Every subsequent deploy: credentials missing, but deploys still worked because nothing needed them
- Adding policy engine: CDK synth now reads credential ARNs from deployed state → fails

## Impact
- Every deploy after the first silently loses credential state
- Any new CDK construct that references credentials will fail on synth
- `agentcore status` shows credentials as "local-only" even though they exist in AWS
- `agentcore remove all` / reset schemas deletes the file entirely with no way to recover credential ARNs (except git history)
- No AWS CLI command exists to list credential providers (`aws bedrock-agentcore` doesn't support it)

## Workaround
After every deploy, manually restore credentials to `deployed-state.json`:
```bash
git checkout HEAD -- agentcore/.cli/deployed-state.json
```
Or keep a backup of the credentials section and re-inject it after each deploy.

## Suggested Fix
In the CLI's post-deploy state writer, read the existing `deployed-state.json` first and merge the new CDK outputs with the existing credential entries, rather than overwriting the entire file.

## Bug 2: Cedar Policy "Resource stabilization failed" — Missing `has` Check

### Symptom
`agentcore deploy` fails with `Resource stabilization failed` when deploying a Cedar policy that accesses `context.input.max_price` directly.

### Root Cause
Cedar requires a `has` check before accessing optional attributes on `context.input`. Without it, the policy fails validation with: "unable to guarantee safety of access to optional attribute `input.max_price`".

### Incorrect (fails)
```cedar
) when {
  context.input.max_price <= 1000
};
```

### Correct (works)
```cedar
) when {
  context.input has max_price && context.input.max_price <= 1000
};
```

### Impact
- The workshop instructions show the incorrect syntax without the `has` check
- The CLI `agentcore add policy --statement` also doesn't warn about this
- Every deploy attempt with the incorrect syntax causes a CloudFormation rollback
- The error message from CloudFormation is generic ("Resource stabilization failed") and doesn't mention the Cedar validation issue — you only see the real error when creating the policy via the console UI

## Bug 3: CLI auto-adds `validationMode: FAIL_ON_ANY_FINDINGS`

### Symptom
`agentcore add policy` auto-adds `"validationMode": "FAIL_ON_ANY_FINDINGS"` to the policy entry in `agentcore.json`, even though the workshop instructions don't mention this field.

### Impact
Combined with Bug 2, this causes immediate deploy failure since the validation mode rejects the policy.
