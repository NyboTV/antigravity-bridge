# 📬 Antigravity Bridge — Universal Inter-Agent Protocol

> This rule is automatically applied to all workspaces while the `antigravity-bridge` plugin is enabled.

---

## 1. 🔍 Mandatory Inbox Check on Every Prompt
At the beginning of **EVERY** prompt or conversation turn:
1. **Check for Inbox:** Verify if an `.agents/INBOX.md` file exists in the current project workspace root.
2. **Immediate Stop on Incoming Message:** If `.agents/INBOX.md` contains an unread message block (`### 📩 Incoming Message` or `### 📩 Eingehende Nachricht`):
   - **Immediately pause** regular processing of the user's prompt.
   - Present the incoming message directly to the user (Sender Project, Conversation ID, Priority, Subject, Content).
   - Ask the user how to proceed:
     - **Execute now:** Perform the task and archive the note via the `archive_inbox_note` tool or append to `.agents/INBOX_ARCHIVE.md`.
     - **Queue as Todo:** Transfer into your local task list / TODO file and archive the note.
     - **Dismiss:** Archive the note with resolution "Dismissed / Verworfen".
   - **Important:** Notes must **never** linger in `INBOX.md` after being surfaced to the user.

---

## 2. 🛡️ Workspace Boundary Protection & Delegation
- **Never touch foreign code:** If your current task requires code modifications, service restarts, or database updates in a different repository or workspace, **never** modify foreign files directly.
- **Always delegate:** Use the `/communicate` slash command or the `antigravity-bridge` MCP server.
- **Execution Receipts:** If this conversation was woken up with a `sender_chat_id`, send a completion confirmation back using the `reply_to_sender` tool once the requested work is complete.

---

## 3. ⚡ Live Wakeup vs. Asynchronous Inbox (Strict Decision Rule)

### 🔴 Default Mode: Live Wakeup (`send_message_to_chat`)
- Whenever the user asks you to consult, coordinate, discuss, or contact another project:
  *(e.g., "abstimmen", "kontaktieren", "besprechen", "frag nach", "sag Bescheid", "jetzt", "live")*
- **DO NOT write an inbox note!**
- **Action:**
  1. Call `list_project_chats(project_name=...)` to find the target's `[Gateway]` chat (or active chat).
  2. Immediately send the message via `send_message_to_chat(conversation_id=..., message=..., priority="Normal"|"Dringend", sender_project=..., sender_chat_id=...)`.

### 🟡 Secondary Mode: Asynchronous Inbox (`send_inbox_note`)
- Use `send_inbox_note` **ONLY** if:
  1. The user explicitly asks for a note/ticket: *(e.g., "Notiz hinterlegen", "in die Inbox schreiben", "für später merken", "als Todo eintragen")*.
  2. OR if `list_project_chats` finds no active chats in the target project.

### 🚫 Strict Ban on "Test" Messages & Exploratory Pings
- **NEVER** send "Test", "Ping", "Hallo", "Bist du da?", or hesitation probing.
- **ALWAYS** include the complete, substantive technical payload directly in your first message:
  - Context & background of the issue.
  - Concrete technical details (APIs, parameters, database schemas, crediting logic, etc.).
  - The exact question or decision requested from the target project.
