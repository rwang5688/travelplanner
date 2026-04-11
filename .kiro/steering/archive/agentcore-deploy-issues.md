---
inclusion: manual
---

# AgentCore Deploy Issues & Workarounds

> **NOTE (2026-04-07):** This document was written using the older AgentCore CLI
> (`agentcore configure` / `.bedrock_agentcore.yaml` / manual Dockerfile workflow).
> The current project uses the newer CDK-based AgentCore CLI (`agentcore.json` +
> `agentcore add runtime` + `agentcore deploy`). Most issues below (Dockerfile CMD,
> stale YAML, configure prompts, container image caching) do NOT apply to the new CLI.
> Kept for historical reference and in case participants encounter the old CLI.

Documented during the Travel Planner workshop on 2026-03-22 and 2026-03-23. These issues should be addressed in workshop content or AgentCore CLI updates.

---

## 🚨 WORKSHOP BLOCKERS — Must Fix Before Workshop

These two issues will block every participant. They are not edge cases — they are guaranteed to hit on every deploy.

### [IMPORTANT] Defect: Replace WSParticipantRole IAM Permission `AWSCodeBuildDeveloperAccess` with `AWSCodeBuildAdminAccess`

`AWSCodeBuildDeveloperAccess` lacks `codebuild:DeleteProject` and `codebuild:CreateProject`. When participants run `agentcore destroy`, the CodeBuild project deletion fails with `AccessDeniedException`, which cascades and also blocks runtime deletion. This makes the destroy → configure → deploy cycle impossible, completely blocking iterative development. Replace with `AWSCodeBuildAdminAccess` in the WSParticipantRole.

See: Issue 2, Issue 5 below for full details.

### [IMPORTANT] Defect: `agentcore configure` Generated Dockerfile Uses Broken CMD — Must Change `python -m __main__` to `python __main__.py`

`agentcore configure` auto-generates a Dockerfile with `CMD ["opentelemetry-instrument", "python", "-m", "__main__"]`. The `opentelemetry-instrument` wrapper crashes with `__main__.__spec__ is None` before any user code executes. The MCP server never starts, tools don't register, and the runtime returns 0 tools or 401. The fix is to change the last line of `<server>/.bedrock_agentcore/<server>/Dockerfile` to `CMD ["opentelemetry-instrument", "python", "__main__.py"]`. This must be done after every `agentcore configure` since configure regenerates the Dockerfile each time, overwriting the fix. Ideally the CLI should be patched to generate the correct CMD.

See: Issue 11 below for full details.

### [IMPORTANT] Defect: Workshop Step 6 Does Not Specify Working Directory for `agentcore identity create-credential-provider`

Workshop Step 6 instructs participants to run `agentcore identity create-credential-provider` but does not specify which directory to run it from. The command must be run from the corresponding server directory (e.g., `flights_mcp/` for flights, `hotels_mcp/` for hotels) so the credential provider config is saved into that server's `.bedrock_agentcore.yaml`. Running from the project root produces a warning (`⚠️ .bedrock_agentcore.yaml not found. Provider created but not saved to config.`) and fails to persist the credential provider reference locally. While the credential provider is still created in AgentCore's token vault, the missing YAML entry will confuse participants and may cause issues if downstream tooling expects it. The workshop instructions should explicitly include `cd flights_mcp` and `cd hotels_mcp` before each respective command.

### [QUESTION] For Reviewers: Is Step 6 Redundant Given Step 7?

Step 6 creates credential providers via `agentcore identity create-credential-provider` (names: `flights-mcp-identity`, `hotels-mcp-identity`). Step 7's `add-target` helper also creates its own credential providers via the `bedrock-agentcore-control` API (names: `flights-mcp-oauth`, `hotels-mcp-oauth`). Running both steps results in duplicate credential providers per server. The `add-target` helper only uses the ones it creates (`*-oauth`), not the ones from Step 6 (`*-identity`). Clarify: is Step 6 needed at all, or should it be removed in favor of letting Step 7 handle credential provider creation automatically?

### [QUESTION] For Reviewers: Observability `AccessDeniedException` During Gateway Creation

During `create-gateway`, the observability/log delivery setup fails with `AccessDeniedException: Access Denied for this DeliveryDestination`. The gateway itself is created and works, but CloudWatch log delivery is not enabled. The WSParticipantRole may need additional permissions for vended log delivery. Is this expected, or does the role need updating?

---

## Issue 1: Absolute Windows Path as Entrypoint

**Problem:** `agentcore configure` resolves the entrypoint to an absolute Windows path (e.g. `D:/Users/.../flights_mcp/__main__.py`), even when run from the server directory. The container runs on Linux and this path doesn't exist there.

**Symptom:** Runtime shows READY but logs show:
```
/usr/local/bin/python: Error while finding module specification for '__main__' (ValueError: __main__.__spec__ is None)
```

**Root cause:** Two issues compound here:
1. `agentcore configure` always resolves to an absolute OS path regardless of input
2. `__main__.py` requires Python package context (`python -m package_name`) to resolve imports like `from flights_mcp.server import mcp`. When the container runs `python __main__.py` directly, there's no parent package.

**Root cause confirmed:** The auto-generated Dockerfile uses `CMD ["opentelemetry-instrument", "python", "-m", "__main__"]`. This runs `__main__.py` as a top-level module with no parent package, so `from flights_mcp.server import mcp` fails. The `app.py` workaround does NOT work because the Dockerfile CMD is hardcoded and ignores whatever entrypoint you configure — it always runs `__main__`.

**Workaround:** Make `__main__.py` dual-mode — detect whether it's running with package context or standalone, and handle both:
```python
import os, sys

if __package__ is None or __package__ == "":
    # AgentCore container: no parent package context
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from server import mcp
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000, stateless_http=True)
else:
    # Local development: python -m flights_mcp
    from flights_mcp.server import mcp
    mcp.run()
```

**Recommendation for workshop content:** This is the only approach that works. The Dockerfile CMD is auto-generated and cannot be overridden by the entrypoint config. Participants MUST use this dual-mode `__main__.py` pattern. The `app.py` approach is dead — the container ignores it.

## Issue 2: `agentcore destroy` Can't Clean Up All Resources

**Problem:** In the workshop environment, `agentcore destroy` fails to delete the CodeBuild project due to IAM restrictions on the `WSParticipantRole`:
```
AccessDeniedException: User is not authorized to perform codebuild:DeleteProject
```

**Symptom:** Subsequent `agentcore configure` may fail with "Launch failed" because it tries to create resources (ECR repo, IAM roles) that already exist from the previous deploy.

**Workaround:** When re-running `agentcore configure`, reuse existing resources instead of auto-creating:
- Accept the existing execution role when prompted
- Accept the existing ECR repository when prompted

**Recommendation for workshop content:** The WSParticipantRole MUST have `codebuild:DeleteProject` and `codebuild:CreateProject` permissions. Without these, participants cannot destroy and reconfigure runtimes, making iterative development impossible. This is a blocker for the workshop. The current `AWSCodeBuildDeveloperAccess` policy does NOT include these actions — the role needs `AWSCodeBuildAdminAccess` instead.

## Issue 3: OAuth Configure Prompts Are Confusing

**Problem:** `agentcore configure` asks for several OAuth fields that aren't clearly explained:
- "OAuth audience" vs "OAuth scope" — easy to confuse
- "Allowed OAuth custom claims as JSON string" — not needed, just skip
- "Configure request header allowlist" — not needed, just skip
- "Memory configuration" — not needed for stateless MCP servers

**Correct values for this workshop:**
- Audience: LEAVE BLANK (press Enter to skip) — Cognito `client_credentials` tokens do NOT include an `aud` claim. Setting any value here causes a 401 with `Claim 'aud' value mismatch with configuration.`
- Scope: `flights-mcp/access` (the full scope including the scope name)
- Custom claims: press Enter to skip
- Header allowlist: press Enter (default: no)
- Memory: type `s` to skip

**Recommendation for workshop content:** Add a clear table of exactly what to enter for each prompt. The audience field is a trap — Cognito client_credentials tokens have no `aud` claim, so any value causes a mismatch. Leave it blank.

## Issue 4: 401 Unauthorized After Deploy

**Problem:** `verify-runtime` returns HTTP 401 even when the runtime shows READY.

**Possible causes:**
1. Server crashed on startup (see Issue 1) — AgentCore returns 401 when the runtime can't handle requests
2. OAuth audience/scope mismatch between Cognito and the runtime config
3. Token expired (Cognito tokens have a 1-hour TTL)

**Debugging steps:**
1. Check CloudWatch logs: `aws logs tail /aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT --log-stream-name-prefix "$(date +%Y/%m/%d)/[runtime-logs]" --since 30m --region us-west-2`
2. Verify the server actually started (look for startup errors vs just OTel noise)
3. Re-run `verify-runtime` — it fetches a fresh token each time

## Issue 5: `agentcore destroy` Fails Entirely When CodeBuild Delete Fails

**Problem:** `agentcore destroy` fails with `AccessDeniedException` on `DeleteAgentRuntime` — but this is NOT an SCP issue. The root cause is that `AWSCodeBuildDeveloperAccess` lacks `codebuild:DeleteProject`. When the CodeBuild deletion fails, the entire destroy chain cascades and subsequent steps (including runtime deletion) also fail.

**Symptom:**
```
AccessDeniedException: User is not authorized to perform: bedrock-agentcore:DeleteAgentRuntime
```

**Root cause:** Missing `AWSCodeBuildAdminAccess`. Once this policy is added (replacing `AWSCodeBuildDeveloperAccess`), `agentcore destroy` works cleanly — including runtime deletion with ParticipantRole. No OpsRole or SCP changes needed.

**Recommendation for workshop content:** This is the single most important IAM fix. Replace `AWSCodeBuildDeveloperAccess` with `AWSCodeBuildAdminAccess` in the WSParticipantRole. Without it, participants cannot destroy or iterate on deployments at all.

## Issue 6: `agentcore destroy` Leaves Stale agent_id in YAML

**Problem:** When `agentcore destroy` deletes a runtime (or fails to), it does NOT null out `agent_id` and `agent_arn` in `.bedrock_agentcore.yaml`. On the next `agentcore deploy`, the CLI sees the old ID and tries to update a runtime that no longer exists.

**Symptom:**
```
ResourceNotFoundException: Agent 'flights_mcp-MUwI5Q56AV' was not found.
```

**Workaround:** Delete `.bedrock_agentcore.yaml` entirely and re-run `agentcore configure` from scratch. Simpler than trying to fix individual fields.

**Recommendation for workshop content:** This is a bug in `agentcore destroy` — it should clean up the YAML on destroy. Document the manual fix for participants until it's patched.

```
__main__.py  →  Dual-mode: detects context automatically
                - Local (python -m flights_mcp): stdio transport, package imports
                - AgentCore container (python -m __main__): streamable-HTTP, standalone imports
app.py       →  DEAD CODE — container ignores it, Dockerfile CMD is hardcoded to __main__
```

The Kiro MCP config (`.kiro/settings/mcp.json`) uses `python -m flights_mcp` which hits `__main__.py` with `__package__="flights_mcp"` → stdio mode. The AgentCore container runs `python -m __main__` which hits `__main__.py` with `__package__=""` → streamable-HTTP mode.

## Issue 7: `agentcore deploy` Does Not Rebuild Container Image

**Problem:** After updating source files (e.g. `__main__.py`), running `agentcore deploy` does NOT rebuild the container image. The runtime continues running the old image with the old code. There is no `--force` flag to force a rebuild.

**Symptom:** CloudWatch logs still show the old error even after fixing the code and redeploying. The runtime keeps crash-looping on the stale image.

**Workaround:** Delete `.bedrock_agentcore.yaml` entirely, re-run `agentcore configure` from scratch, then `agentcore deploy`. This forces a full rebuild because flagentcore treats it as a brand new agent.

**Recommendation for workshop content:** This is a critical gap. Iterative development is impossible if code changes aren't picked up on deploy. Participants will waste enormous time debugging "why didn't my fix work" when the answer is "the container is still running your old code." Document the nuclear option (delete YAML, reconfigure, redeploy) as the standard workflow for code changes.

## Issue 8: `agentcore deploy` Fails on Name Conflict Without Helpful Default

**Problem:** After deleting `.bedrock_agentcore.yaml` and reconfiguring, `agentcore deploy` fails with:
```
ConflictException: Agent 'flights_mcp' already exists. To update the existing agent, use the --auto-update-on-conflict flag with the launch command.
```

The CLI knows the fix (`--auto-update-on-conflict`) but doesn't offer it as a default or prompt — it just fails and tells you to retry with the flag.

**Workaround:** Run `agentcore deploy --auto-update-on-conflict` instead of `agentcore deploy`.

**Recommendation for workshop content:** Always use `agentcore deploy --auto-update-on-conflict`. This should be the default behavior, not an opt-in flag. Document this as the standard deploy command for participants. The full redeploy cycle is:
1. Delete `.bedrock_agentcore.yaml`
2. `agentcore configure` (re-enter all values)
3. `agentcore deploy --auto-update-on-conflict`

## Issue 9: `.bedrock_agentcore.yaml` Is the Root of All Evil

**Problem:** `.bedrock_agentcore.yaml` is the single point of failure for the entire AgentCore workflow. It accumulates stale state, stores absolute OS-specific paths, and cannot be incrementally updated. Every problem eventually leads back to "delete the YAML and start over."

**Specific problems:**
1. Stores absolute Windows paths as entrypoint (useless in Linux container)
2. Retains stale `agent_id`/`agent_arn` after failed destroys
3. Cannot be partially updated — it's all or nothing
4. `agentcore deploy` uses it to decide whether to rebuild, but gets it wrong
5. No `--force` flag to override its cached state
6. The entrypoint field is completely ignored by the auto-generated Dockerfile

**Impact:** Every code change requires the full nuclear cycle: delete YAML → reconfigure (re-enter ALL values manually) → deploy with `--auto-update-on-conflict`. This is the standard workflow, not the exception.

**Recommendation for workshop content:** Tell participants upfront that `.bedrock_agentcore.yaml` is disposable. They will delete it multiple times during the workshop. Have them keep their configure values (execution role ARN, ECR repo, OAuth settings) in a separate doc so they can re-enter them quickly.

## Issue 10: Runtime Never Pulls Updated Container Images

**Problem:** After a successful `agentcore deploy` that rebuilds and pushes a new container image to ECR, the runtime continues running the old cached image. Multiple deploys with `--auto-update-on-conflict` confirmed: CodeBuild runs, image is pushed to ECR with a new tag, but the runtime keeps crash-looping on the stale image.

**Symptom:** CloudWatch logs show the same old error indefinitely, even though the ECR image was updated minutes ago. The runtime's "Last Updated" timestamp changes but the actual container doesn't.

**Workaround:** Full destroy + fresh deploy. With `AWSCodeBuildAdminAccess`, `agentcore destroy` works cleanly with ParticipantRole. Then reconfigure and deploy from scratch.

**Recommendation for workshop content:** This is a showstopper for iterative development. If participants need to fix code after the first deploy, they must do a full destroy/reconfigure/deploy cycle. Document this upfront.

## Issue 11: `opentelemetry-instrument` Wrapper Breaks `python -m __main__`

**Problem:** The auto-generated Dockerfile uses:
```dockerfile
CMD ["opentelemetry-instrument", "python", "-m", "__main__"]
```

The `opentelemetry-instrument` wrapper crashes when trying to resolve the module spec for `__main__` BEFORE any user code executes. The error `__main__.__spec__ is None` happens at the Python/OTel interpreter level — the dual-mode `__main__.py` code never gets a chance to run.

**Symptom:** Even with a correctly written dual-mode `__main__.py`, the container crash-loops with:
```
/usr/local/bin/python: Error while finding module specification for '__main__' (ValueError: __main__.__spec__ is None)
```

This was confirmed on a completely fresh deploy (clean destroy, fresh configure, fresh image build). The dual-mode `__main__.py` is irrelevant — the OTel wrapper kills the process before our code runs.

**Root cause:** `python -m __main__` combined with `opentelemetry-instrument` is broken. The OTel wrapper can't handle running `__main__` as a module without a parent package.

**Fix:** Edit the Dockerfile AFTER `agentcore configure` but BEFORE `agentcore deploy`. Change the last line from:
```dockerfile
CMD ["opentelemetry-instrument", "python", "-m", "__main__"]
```
to:
```dockerfile
CMD ["opentelemetry-instrument", "python", "__main__.py"]
```

This runs the file directly instead of as a module. No module spec resolution, no `__spec__` check. The dual-mode `__main__.py` detects `__package__` is None and takes the container (streamable-HTTP) path.

**The Dockerfile is at:** `<server_name>/.bedrock_agentcore/<server_name>/Dockerfile`

**CRITICAL:** `agentcore configure` regenerates this Dockerfile every time. The fix must be applied AFTER configure but BEFORE deploy. If participants run configure again, the fix is overwritten.

**Recommendation for workshop content:** This is the real root cause of all the 401 errors. The Dockerfile CMD is wrong. Either:
1. Fix the agentcore CLI to generate `python __main__.py` instead of `python -m __main__`
2. Document the manual Dockerfile edit as a required post-configure step
3. Both — fix the CLI and document the workaround until it's patched

## Issue 12: OAuth Audience Must Be Left Blank — Cognito `client_credentials` Has No `aud` Claim

**Problem:** When configuring the AgentCore runtime with `agentcore configure`, the "OAuth audience" prompt accepts a value. If you enter anything (e.g. `flights-mcp`), the runtime rejects all tokens with HTTP 401 and the message:
```
Claim 'aud' value mismatch with configuration.
```

**Root cause:** Cognito `client_credentials` grant tokens do NOT include an `aud` (audience) claim at all. The AgentCore runtime's JWT validator checks the `aud` claim against the configured `allowedAudience`. Since the token has no `aud`, any non-empty audience value causes a mismatch → 401.

**Symptom:** Runtime shows READY, CloudWatch logs confirm the FastMCP server started successfully (you can see `FastMCP 3.0.0 starting with streamable-http transport`), but every request returns HTTP 401 with `Claim 'aud' value mismatch with configuration.`

**This is especially deceptive** because:
1. The runtime is genuinely healthy — the server code is running fine
2. The token is valid — Cognito issued it correctly
3. The 401 looks identical to the 401 you get when the server crashes (Issue 1/11)
4. You can waste hours debugging server code when the problem is a single config field

**THE TWO 401s:** AgentCore returns HTTP 401 for two completely different root causes that are indistinguishable from the caller's side:
- **401 #1 (Issues 1/11):** Server crashed on startup (Dockerfile CMD `python -m __main__` + OTel = `__spec__ is None`). The container is dead, so AgentCore returns 401 for every request. Fix: edit Dockerfile CMD to `python __main__.py`.
- **401 #2 (This issue):** Server is running perfectly, but the JWT validator rejects the token because `allowedAudience` is set to a value and Cognito `client_credentials` tokens have no `aud` claim. Fix: leave audience blank during configure.

Both return the same 401 status code. The ONLY way to tell them apart is CloudWatch logs — if you see the server startup message, it's 401 #2. If you see a crash, it's 401 #1. This cost us 12+ deploy attempts and a 3 AM debugging session.

**Fix:** During `agentcore configure`, when prompted for "OAuth audience", press Enter to leave it blank. Do NOT enter the resource server identifier, the client ID, or any other value.

**If already deployed with wrong audience:** Full destroy/reconfigure/deploy cycle:
```bash
agentcore destroy
rm <server>/.bedrock_agentcore.yaml
agentcore configure --protocol MCP   # LEAVE AUDIENCE BLANK this time
# Fix Dockerfile (Issue 11)
agentcore deploy
```

**Recommendation for workshop content:** This is a trap that will catch every participant who follows OAuth conventions. Most OAuth setups use audience — Cognito `client_credentials` is the exception. Add a bold warning in the workshop instructions: "LEAVE AUDIENCE BLANK — Cognito client_credentials tokens have no aud claim."

---

# Tomorrow's Plan (2026-03-23)

## Current State
- All runtimes destroyed cleanly (flights_mcp and flights_mcp_v2)
- `.bedrock_agentcore.yaml` exists but is stale — DELETE IT before starting
- Cognito OAuth resources still exist in us-west-2 (pool `us-west-2_fmQIOJRyX`, client `58f4pedffurf155fmo979tku2f`)
- `__main__.py` is dual-mode (handles both stdio and streamable-HTTP) — this is correct
- The Dockerfile at `flights_mcp/.bedrock_agentcore/flights_mcp/Dockerfile` has been manually fixed to `python __main__.py`
- BUT `agentcore configure` will regenerate the Dockerfile and overwrite the fix

## Steps

### 1. Delete stale YAML
```bash
rm flights_mcp/.bedrock_agentcore.yaml
```

### 2. Configure (from `flights_mcp/` directory)
```bash
agentcore configure --protocol MCP
```

Values to enter:

| Prompt | Value |
|--------|-------|
| Agent name | `flights_mcp` |
| Entrypoint | `__main__.py` (type explicitly, never leave blank) |
| Execution role | let it auto-create |
| ECR repo | let it auto-create |
| Network | PUBLIC |
| OAuth discovery URL | `https://cognito-idp.us-west-2.amazonaws.com/us-west-2_fmQIOJRyX/.well-known/openid-configuration` |
| Allowed clients | `58f4pedffurf155fmo979tku2f` |
| OAuth audience | LEAVE BLANK (press Enter to skip) |
| OAuth scope | `flights-mcp/access` |
| Custom claims | Enter to skip |
| Header allowlist | Enter (no) |
| Memory | `s` to skip |

### 3. Fix the Dockerfile (AFTER configure, BEFORE deploy)

Edit `flights_mcp/.bedrock_agentcore/flights_mcp/Dockerfile` — change the last line from:
```dockerfile
CMD ["opentelemetry-instrument", "python", "-m", "__main__"]
```
to:
```dockerfile
CMD ["opentelemetry-instrument", "python", "__main__.py"]
```

### 4. Deploy
```bash
agentcore deploy
```

### 5. Verify
Wait 1-2 minutes, then:
```bash
python workshop_helper.py verify-runtime flights_mcp
```

Expected: `✅ Runtime is live! Found 3 tool(s)`

### If It Fails
Check CloudWatch logs:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT --log-stream-name-prefix "$(date +%Y/%m/%d)/[runtime-logs]" --since 10m --region us-west-2
```

- If `__main__.__spec__ is None` → Dockerfile fix was overwritten by configure. Re-edit it.
- If different error → new problem, debug from logs.

### If You Need to Redeploy After Code Changes
```bash
agentcore destroy
rm flights_mcp/.bedrock_agentcore.yaml
agentcore configure --protocol MCP
# Fix Dockerfile again (step 3)
agentcore deploy
```

---

# First-Time Success Guide: Deploying an MCP Server to AgentCore

This is the sequence that actually works. Follow it exactly to avoid the issues above.

## Step 0: Write `__main__.py` as Dual-Mode BEFORE First Deploy

Your `__main__.py` MUST handle both local (stdio) and container (streamable-HTTP) contexts:

```python
"""Entry point for the MCP Server.

Works in two contexts:
- Local development: `python -m flights_mcp` (stdio transport)
- AgentCore container: `python __main__.py` (streamable-HTTP transport)
"""

import os
import sys

if __package__ is None or __package__ == "":
    # AgentCore container: no parent package context
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from server import mcp
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000, stateless_http=True)
else:
    # Local development: python -m flights_mcp
    from flights_mcp.server import mcp
    mcp.run()
```

## Step 1: Setup OAuth (one-time)

```bash
python workshop_helper.py setup-auth flights_mcp
```

Save the output values.

## Step 2: Configure

```bash
agentcore configure --protocol MCP
```

See table above for values. Always type `__main__.py` explicitly as entrypoint.

## Step 3: Fix the Dockerfile (REQUIRED)

Edit `<server>/.bedrock_agentcore/<server>/Dockerfile`, change last line to:
```dockerfile
CMD ["opentelemetry-instrument", "python", "__main__.py"]
```

## Step 4: Deploy

```bash
agentcore deploy
```

## Step 5: Verify

```bash
python workshop_helper.py verify-runtime flights_mcp
```

## Workshop IAM Requirements

The WSParticipantRole needs these policies (not the defaults):
- `AWSCodeBuildAdminAccess` (NOT `AWSCodeBuildDeveloperAccess` — need `CreateProject` and `DeleteProject`)
- `BedrockAgentCoreFullAccess`
- `AmazonCognitoPowerUser`
- `AmazonEC2ContainerRegistryFullAccess`
- `AmazonS3FullAccess`
- `IAMFullAccess`
- `CloudWatchLogsFullAccess`
- `AmazonBedrockFullAccess`
