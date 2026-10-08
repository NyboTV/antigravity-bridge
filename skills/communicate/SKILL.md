---
name: communicate
description: Inter-Agent & Cross-Project Communication via antigravity-bridge MCP. Triggered by the /communicate slash command or when the user wants to dispatch tasks, coordinate, discuss, send messages to other project chats, query other projects, or append notes to an inbox.
---

# 🛰️ Inter-Project Communication Protocol (`/communicate`)

This skill coordinates cross-project and inter-agent communication between different workspaces using the **`antigravity-bridge`** MCP server.

---

## 🎯 When to Use This Skill
- The user explicitly runs the slash command **`/communicate`**.
- The user asks to coordinate or talk with another project:
  - *"Stimm dich mit ServerZentrum ab..."* / *"Sprich mit Projekt X ab..."*
  - *"Kontaktiere Caleb..."* / *"Frag Gamebot nach..."*
  - *"Tell Project X that..."* / *"Notify Chat Y about..."*
  - *"Send the new API specs to the backend project"*
  - *"Create a task/note in Project Z's inbox"*

---

## 🛠️ Available MCP Tools (`antigravity-bridge`)

| Tool | Purpose |
|---|---|
| `list_projects` | Lists all registered projects with local paths, chat metrics, and inbox status. |
| `list_project_chats` | Lists active conversations for a project from SQLite DB (highlights `[Gateway]` chats). |
| `send_message_to_chat` | Sends a message directly into a target conversation and wakes it up live (`agentapi send-message`). |
| `reply_to_sender` | Sends an execution receipt or status update back to the `sender_chat_id`. |
| `send_inbox_note` | Safely appends a structured task note (append-only) to `.agents/INBOX.md` in the target project. |
| `archive_inbox_note` | Moves resolved tasks from `.agents/INBOX.md` to `.agents/INBOX_ARCHIVE.md`. |

---

## 📋 Execution Protocol for `/communicate`

### Step 1: Target Discovery
- Identify the target project (e.g., `ServerZentrum`, `Nyeo`, `Gamebot-Systems`, `Anwalt`). If ambiguous, run `list_projects`.

### Step 2: Mode Selection (Live Wakeup is DEFAULT)
- **DEFAULT: Live Chat Wakeup (`send_message_to_chat`)**
  - Always use this when the user says: *abstimmen, kontaktieren, besprechen, fragen, klären, jetzt, live, sofort*.
  - Call `list_project_chats(project_name=...)`.
  - Automatically pick the `recommended_gateway_chat` (or first active chat).
  - Immediately send the full technical payload.
- **SECONDARY: Asynchronous Inbox (`send_inbox_note`)**
  - Use ONLY if the user explicitly says: *Notiz hinterlegen, in die Inbox schreiben, für später, als Todo eintragen*.
  - Or if no active chats exist in the target project.

---

## 🚫 Crucial Guardrails

### 1. NO "Test" Pings or Exploratory Probing
- **DO NOT** send "Test", "Hallo", "Ping", or "Bist du da?".
- **ALWAYS** transmit the complete technical inquiry in your first dispatch:
  1. The background context of the problem.
  2. Concrete technical details (APIs, parameters, database schemas, crediting logic, etc.).
  3. The specific questions or architectural decisions needed from the target project.
  4. Always pass `sender_chat_id` and `sender_project`.

### 2. Never Edit Foreign Code Directly
- Never touch files outside your active project workspace. Always delegate cross-project requirements via `/communicate` and `antigravity-bridge`.
