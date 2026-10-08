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
- **Always delegate:** Use the `/communicate` slash command or the `antigravity-bridge` MCP server (`send_message_to_chat` for live gateway wakeup, or `send_inbox_note` for asynchronous queued tasks).
- **Execution Receipts:** If this conversation was woken up with a `sender_chat_id`, send a completion confirmation back using the `reply_to_sender` tool once the requested work is complete.
