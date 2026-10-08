---
name: communicate
description: Inter-Agent & Cross-Project Communication via antigravity-bridge MCP. Triggered by the /communicate slash command or when the user wants to dispatch tasks, coordinate, discuss, send messages to other project chats, query other projects, or append notes to an inbox.
---

# 🛰️ Inter-Project Communication Protocol (`/communicate`)

This skill coordinates cross-project and inter-agent communication between different workspaces using the **`antigravity-bridge`** MCP server.

---

## 🎯 When to Use This Skill
- The user explicitly runs the slash command **`/communicate`**.
- The user asks to coordinate, delegate, or communicate with another project:
  - *"Coordinate with ServerZentrum about..."* / *"Check with Project X..."*
  - *"Contact Caleb regarding..."* / *"Ask Gamebot about the payment webhook"*
  - *"Tell Project X that the database schema changed"*
  - *"Send the new API specs to the backend project"*
  - *"Create a task/note in Project Z's inbox"*
  - *(or multilingual user prompts, e.g. German: "Stimm dich mit ... ab", "Kontaktiere ...")*

---

## 🛠️ Available MCP Tools (`antigravity-bridge`)

| Tool | Purpose |
|---|---|
| `list_projects` | Lists all registered projects with local paths, chat metrics, and inbox status. |
| `list_project_chats` | Lists active conversations for a project from SQLite DB (highlights `[Gateway]` chats). |
| `get_chat_status` | Inspects live execution status (`RUNNING` vs `IDLE`, step count) of a conversation. |
| `send_message_to_chat` | Sends a message directly into a target conversation and wakes it up live (`agentapi send-message`). |
| `reply_to_sender` | Sends an execution receipt or status update back to the `sender_chat_id`. |
| `send_inbox_note` | Safely appends a structured task note (append-only) to `.agents/INBOX.md` in the target project. |
| `archive_inbox_note` | Moves resolved tasks from `.agents/INBOX.md` to `.agents/INBOX_ARCHIVE.md`. |

---

## 📋 Execution Protocol for `/communicate`

### Step 1: Target Discovery
- Identify the target project (e.g., `ServerZentrum`, `Nyeo`, `Gamebot-Systems`, `Anwalt`). If ambiguous or unspecified, run `list_projects` to show available target workspaces.

### Step 2: Mode Selection (Live Wakeup is DEFAULT)
- **DEFAULT: Live Chat Wakeup (`send_message_to_chat`)**
  - Always use this when the user asks to: *coordinate, contact, discuss, ask, clarify, notify, live, now, immediately* (e.g. *abstimmen, kontaktieren, besprechen, fragen, jetzt*).
  - Call `list_project_chats(project_name=...)`.
  - **Single Gateway:** If `has_multiple_gateways: false`, dispatch directly to `recommended_gateway_chat`.
  - **Multiple Gateways:** If `has_multiple_gateways: true`, present a clean numbered list and ask the user which gateway chat to target before dispatching.
  - Immediately send the full technical payload.
- **SECONDARY: Asynchronous Inbox (`send_inbox_note`)**
  - Use ONLY if the user explicitly asks to: *leave a note, add to inbox, queue as ticket, save for later* (e.g. *Notiz hinterlegen, in die Inbox schreiben*).
  - Or if no active chats exist in the target project.

### Step 3: Token-Efficient Status Check & Reactive Wait
- **Initial Verification (15s):** After dispatching the message, verify **once** after ~15 seconds with `get_chat_status(conversation_id=...)` that the target chat picked up the work (`RUNNING`).
- **End Turn & Wait for Receipt:** Once verified, inform the user and **finish your turn (stop calling tools)**.
- **No Active Loop:** DO NOT loop or poll every second! The target chat will automatically call `reply_to_sender` when done, which reactively wakes up this conversation with zero token burn while waiting.
- **5-Minute Watchdog Timeout:** If no receipt has arrived after 5 minutes, run `get_chat_status(conversation_id)`. If `IDLE`, alert the user that the target chat finished without sending a receipt. If still `RUNNING`, continue waiting.
- If monitoring is explicitly requested, poll at most **once every 30 seconds**.

---

## 🚫 Crucial Guardrails

### 1. NO "Test" Pings or Exploratory Probing
- **DO NOT** send "Test", "Ping", "Hello", or "Are you there?".
- **ALWAYS** transmit the complete technical inquiry in your first dispatch:
  1. The background context of the problem.
  2. Concrete technical details (APIs, parameters, database schemas, crediting logic, etc.).
  3. The specific questions or architectural decisions needed from the target project.
  4. Always pass `sender_chat_id` and `sender_project`.

### 2. Never Edit Foreign Code Directly
- Never touch files outside your active project workspace. Always delegate cross-project requirements via `/communicate` and `antigravity-bridge`.
