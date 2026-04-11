---
inclusion: manual
---

# AgentCore Memory Setup — TravelPlannerMemory

## Step 1: Add Memory

```bash
agentcore add memory --name TravelPlannerMemory --strategies "SEMANTIC,SUMMARIZATION,USER_PREFERENCE" --expiry 30
```

Note: strategies must be quoted as a single string.

## Step 2: Check Memory Status

```bash
agentcore status --type memory
```

Before deploy, this shows "Local only". After deploy, it shows the memory ID.

## Step 3: Deploy Memory

```bash
agentcore deploy -y
```

Memory provisioning takes 30-180 seconds. The deploy waits for ACTIVE status.

## Step 4: Verify Memory is Deployed

```bash
agentcore status --type memory
```

Should now show status "Deployed" with a memory ID. Save this ID — it becomes the
`MEMORY_TRAVELPLANNERMEMORY_ID` env var that the agent uses at runtime.

Note: The workshop content is missing the deploy step between add and status.
Without deploying, status only shows "Local only" with no memory ID.

## Step 5: Set Memory ID for Local Development

After deploy, retrieve the memory ID:

```bash
agentcore status --type memory
```

Copy the memory ID from the output and add it to `agentcore/.env.local`:

```
MEMORY_TRAVELPLANNERMEMORY_ID=<memory-id-from-status>
```

This env var is needed for `agentcore dev` (local testing). The deployed runtime
gets it injected automatically — you only need `.env.local` for local dev.

## How Memory Works

- `agentcore dev`: Uses memory only if `MEMORY_TRAVELPLANNERMEMORY_ID` is set in
  `.env.local`. Without it, `get_memory_session_manager()` returns `None` and the
  agent runs without memory.
- `agentcore invoke` / deployed runtime: Memory ID is injected as an env var
  automatically. Memory is stored in the AgentCore Memory service in AWS.
- Both local dev and deployed agent hit the same cloud memory store if using the
  same memory ID.
