---
name: communicate
description: Inter-Agent & Cross-Project Communication via antigravity-bridge MCP. Triggered by the /communicate slash command or when the user wants to dispatch tasks, send messages to other project chats, query other projects, or append notes to an inbox.
---

# 🛰️ Inter-Project Communication Protocol (`/communicate`)

This skill coordinates cross-project and inter-agent communication between different workspaces using the **`antigravity-bridge`** MCP server.

---

## 🎯 When to Use This Skill
- The user explicitly runs the slash command **`/communicate`**.
- The user uses phrases such as:
  - *"Tell Project X that..."*
  - *"Notify Chat Y about..."*
  - *"Send the new API specs to the backend project"*
  - *"Create a task/note in Project Z's inbox"*
  - *"Reply to the originating chat with a status receipt"*

---

## 🛠️ Available MCP Tools (`antigravity-bridge`)

The `antigravity-bridge` MCP server provides the following tools:

| Tool | Purpose |
|---|---|
| `list_projects` | Lists all registered projects with local paths, chat metrics, and inbox status. |
| `list_project_chats` | Lists active conversations for a project from SQLite DB (highlights `[Gateway]` chats). |
| `send_message_to_chat` | Sends a message directly into a target conversation and wakes it up live (`agentapi send-message`). |
| `reply_to_sender` | Sends an execution receipt or status update back to the `sender_chat_id`. |
| `send_inbox_note` | Safely appends a structured task note (append-only) to `.agents/INBOX.md` in the target project. |
| `archive_inbox_note` | Moves resolved tasks from `.agents/INBOX.md` to `.agents/INBOX_ARCHIVE.md`. |

---

## 📋 Standard Workflow for `/communicate`

### Step 1: Identify Target Project
- If the user already specified the project (e.g., `/communicate Backend ...`), select it directly.
- If unspecified or ambiguous, call `list_projects` and present the available projects for selection.

### Step 2: Choose Communication Mode (Live Wakeup vs. Asynchronous Note)
1. **Live Task / Immediate Wakeup (Real-time):**
   - Call `list_project_chats(project_name=...)`.
   - If a conversation with prefix `[Gateway]` exists (e.g. `[Gateway] Backend Dispatcher`), select it by default or present a numbered list of choices to the user.
   - Send the message with `send_message_to_chat(conversation_id=..., message=..., priority=...)`.
   - Provide a clean confirmation indicating target chat and status.

2. **Asynchronous Note / Deferred Task (Inbox):**
   - If the user wants to leave a note or wants the target agent to handle it upon the next user turn:
   - Call `send_inbox_note(target_project=..., sender_project=..., message=..., priority=..., subject=...)`.
   - The note is appended safely to `.agents/INBOX.md` in the target project.

3. **Receipt / Confirmation to Origin (`reply_to_sender`):**
   - If this chat was triggered by an incoming task from another project (has a `sender_chat_id`), use `reply_to_sender` once the task is finished to notify the caller.

---

## 🛑 Golden Isolation Guardrail
- **Never edit foreign project code directly:** If you are working in one project workspace and changes are required in another repository, NEVER attempt to modify files outside your workspace directly. Always use `/communicate` or the `antigravity-bridge` MCP tools to delegate the task cleanly!
