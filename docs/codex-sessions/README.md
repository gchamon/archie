# Codex Session Logs

This directory documents the local Codex CLI session log format. The `.jsonl`
files are local artifacts and are ignored by Git; do not commit them. Each line
is one complete JSON object. Read them as an event stream in timestamp order,
not as one large nested document.

## File Layout

Session logs are organized by theme:

```text
docs/codex-sessions/<session-theme>/rollout-<timestamp>-<session-id>.jsonl
```

Current themes:

- `arch-distro`: sessions related to the Arch distro / ISO planning work.
- `archie-v3`: sessions related to Archie v3 deployment, migration, and release work.

## Top-Level Record Schema

Every line has the same top-level shape:

```json
{
  "timestamp": "2026-03-07T03:12:20.844Z",
  "type": "event_msg",
  "payload": {}
}
```

Fields:

```yml
- timestamp: ISO-8601 UTC timestamp for when the record was emitted.
- type:
    description: record kind
    options:
      - session_meta
      - turn_context
      - event_msg
      - response_item
- payload: record-specific data.
```

## Record Types

### `session_meta`

One per session. This is the session header.

Example shape:

```json
{
  "timestamp": "2026-03-07T03:12:20.841Z",
  "type": "session_meta",
  "payload": {
    "id": "<session-id>",
    "timestamp": "2026-03-07T03:11:46.937Z",
    "cwd": "/home/gchamon/Projects/archie",
    "originator": "codex_cli_rs",
    "cli_version": "0.106.0",
    "source": "cli",
    "model_provider": "openai",
    "base_instructions": {
      "text": "..."
    },
    "truncation_policy": {
      "mode": "tokens",
      "limit": 10000
    }
  }
}
```

Common fields:

- `id`: session identifier.
- `timestamp`: session start time.
- `cwd`: working directory.
- `originator`, `cli_version`, `source`: CLI metadata.
- `model_provider`: provider name.
- `base_instructions`: instruction bundle applied to the session.
- `truncation_policy`: context truncation configuration.

### `turn_context`

One per turn. This is the per-turn execution context snapshot.

Example shape:

```json
{
  "timestamp": "2026-03-07T03:12:20.846Z",
  "type": "turn_context",
  "payload": {
    "turn_id": "019cc648-1d61-7fc1-9562-cf7b1e48c544",
    "cwd": "/home/gchamon/Projects/archie",
    "approval_policy": "on-request",
    "sandbox_policy": {
      "type": "workspace-write",
      "network_access": false
    },
    "model": "gpt-5.3-codex",
    "personality": "pragmatic",
    "collaboration_mode": {
      "mode": "plan",
      "settings": {}
    },
    "effort": "medium",
    "summary": "...",
    "user_instructions": "...",
    "truncation_policy": {
      "mode": "tokens",
      "limit": 10000
    }
  }
}
```

Common fields:

- `turn_id`: unique identifier for the turn.
- `approval_policy`: tool approval mode.
- `sandbox_policy`: sandbox and network settings.
- `model`, `personality`, `collaboration_mode`, `effort`: model/runtime config.
- `summary`, `user_instructions`: effective instructions for that turn.

### `event_msg`

Timeline events emitted while the turn runs.

Example shape:

```json
{
  "timestamp": "2026-03-07T03:12:20.844Z",
  "type": "event_msg",
  "payload": {
    "type": "user_message"
  }
}
```

Observed `payload.type` values:

- `task_started`
- `user_message`
- `agent_reasoning`
- `agent_message`
- `item_completed`
- `token_count`
- `task_complete`

Common subtype shapes:

```json
{
  "type": "task_started",
  "turn_id": "019cc648-1d61-7fc1-9562-cf7b1e48c544",
  "model_context_window": 258400,
  "collaboration_mode_kind": "plan"
}
```

```json
{
  "type": "user_message",
  "message": "I'd like to explore ...",
  "images": [],
  "local_images": [],
  "text_elements": []
}
```

```json
{
  "type": "agent_reasoning",
  "text": "**Planning repo exploration**"
}
```

```json
{
  "type": "agent_message",
  "message": "I’m going to inspect the current structure ...",
  "phase": "commentary"
}
```

```json
{
  "type": "item_completed",
  "thread_id": "<session-id>",
  "turn_id": "019cc648-1d61-7fc1-9562-cf7b1e48c544",
  "item": {
    "type": "Plan",
    "id": "019cc648-1d61-7fc1-9562-cf7b1e48c544-plan",
    "text": "# Archie Distro Plan ..."
  }
}
```

```json
{
  "type": "token_count",
  "info": {
    "total_token_usage": {
      "input_tokens": 235516,
      "cached_input_tokens": 198400,
      "output_tokens": 7723,
      "reasoning_output_tokens": 1186,
      "total_tokens": 243239
    }
  },
  "rate_limits": {}
}
```

```json
{
  "type": "task_complete",
  "turn_id": "019cc648-1d61-7fc1-9562-cf7b1e48c544",
  "last_agent_message": "Written to ..."
}
```

### `response_item`

Structured outputs produced by the assistant during the turn.

Example shape:

```json
{
  "timestamp": "2026-03-07T03:12:27.210Z",
  "type": "response_item",
  "payload": {
    "type": "function_call"
  }
}
```

Observed `payload.type` values:

- `message`
- `reasoning`
- `function_call`
- `function_call_output`

Common subtype shapes:

```json
{
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "output_text",
      "text": "Written to ..."
    }
  ],
  "phase": "final_answer"
}
```

```json
{
  "type": "reasoning",
  "summary": [
    {
      "type": "summary_text",
      "text": "**Planning repo exploration**"
    }
  ],
  "content": null,
  "encrypted_content": "gAAAAA..."
}
```

```json
{
  "type": "function_call",
  "name": "exec_command",
  "arguments": "{\"cmd\":\"pwd\",\"workdir\":\"/home/gchamon/Projects/archie\"}",
  "call_id": "call_5dQxKD4VCZEECorHCGcuFEHE"
}
```

```json
{
  "type": "function_call_output",
  "call_id": "call_5dQxKD4VCZEECorHCGcuFEHE",
  "output": "Chunk ID: ...\nOutput:\n/home/gchamon/Projects/archie\n"
}
```

Notes:

- `call_id` links a tool call to its output.
- `arguments` is stored as a JSON string, not a nested object.
- `reasoning.summary` is readable.
- `reasoning.encrypted_content` stores the detailed reasoning payload in opaque,
  encrypted form.

## How To Read A Turn

A typical turn looks like this:

1. `turn_context`
2. `event_msg.task_started`
3. `event_msg.user_message`
4. `event_msg.agent_reasoning`
5. `response_item.reasoning`
6. `event_msg.agent_message`
7. `response_item.function_call`
8. `response_item.function_call_output`
9. more reasoning, messages, or tool calls
10. final `response_item.message` or `event_msg.item_completed`
11. `event_msg.token_count`
12. `event_msg.task_complete`

## Useful jq Queries

Replace `$LOG` with a specific file, for example:

```bash
LOG=docs/codex-sessions/<session-theme>/rollout-<timestamp>-<session-id>.jsonl
```

### List top-level record types

```bash
jq -r '.type' "$LOG" | sort | uniq -c
```

### List `payload.type` values under `event_msg` and `response_item`

```bash
jq -r 'select(.type == "event_msg" or .type == "response_item") | [.type, .payload.type] | @tsv' "$LOG" | sort | uniq -c
```

### Show only user prompts

```bash
jq -r 'select(.type == "event_msg" and .payload.type == "user_message") | .timestamp + " " + .payload.message' "$LOG"
```

### Show assistant commentary and final messages

```bash
jq -r '
  select(.type == "event_msg" and .payload.type == "agent_message")
  | .timestamp + " [" + (.payload.phase // "unknown") + "] " + .payload.message
' "$LOG"
```

### Show reasoning summaries without encrypted blobs

```bash
jq -r '
  select(.type == "response_item" and .payload.type == "reasoning")
  | .timestamp + " " + (.payload.summary[]?.text // "")
' "$LOG"
```

### Show all tool calls

```bash
jq -r '
  select(.type == "response_item" and .payload.type == "function_call")
  | .timestamp + " " + .payload.name + " " + .payload.arguments
' "$LOG"
```

### Show all tool outputs

```bash
jq -r '
  select(.type == "response_item" and .payload.type == "function_call_output")
  | .timestamp + " " + .payload.call_id + "\n" + .payload.output + "\n---"
' "$LOG"
```

### Join tool calls to tool outputs by `call_id`

```bash
jq -s '
  map(select(.type == "response_item"))
  | (map(select(.payload.type == "function_call")) | map({key: .payload.call_id, value: {name: .payload.name, arguments: .payload.arguments}}) | from_entries) as $calls
  | map(select(.payload.type == "function_call_output"))
  | map({
      timestamp,
      call_id: .payload.call_id,
      name: $calls[.payload.call_id].name,
      arguments: $calls[.payload.call_id].arguments,
      output: .payload.output
    })
' "$LOG"
```

### Show token usage snapshots

```bash
jq '
  select(.type == "event_msg" and .payload.type == "token_count")
  | {timestamp, total: .payload.info.total_token_usage, last: .payload.info.last_token_usage}
' "$LOG"
```

### Extract completed plan text

```bash
jq -r '
  select(.type == "event_msg" and .payload.type == "item_completed" and .payload.item.type == "Plan")
  | .payload.item.text
' "$LOG"
```

### Find turns that contain encrypted reasoning

```bash
jq -r '
  select(.type == "response_item" and .payload.type == "reasoning" and .payload.encrypted_content != null)
  | .timestamp
' "$LOG"
```

## Practical Notes

- These logs are append-only event streams.
- The same turn is represented across multiple lines and multiple record types.
- `event_msg.agent_reasoning` is the short readable status text.
- `response_item.reasoning.encrypted_content` is the opaque full reasoning payload.
- `response_item.message` and `event_msg.agent_message` are related but not the
  same thing: one is a structured response item, the other is a timeline event.
