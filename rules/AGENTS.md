# 📬 Antigravity Bridge — Universal Inter-Agent Protocol

> This rule is automatically applied to all workspaces while the `antigravity-bridge` plugin is enabled.

---

## 1. 🔍 Mandatory Inbox Check on Every Prompt
At the beginning of **EVERY** prompt or conversation turn:
*(Exception: For initialization commands like `/communicate-start`, skip the inbox check in favor of displaying the gateway setup card immediately).*
1. **Check for Inbox:** Verify if an `.agents/INBOX.md` file exists in the current project workspace root.
2. **Immediate Stop on Incoming Message:** If `.agents/INBOX.md` contains an unread message block (`### 📩 Incoming Message` or legacy `### 📩 Eingehende Nachricht`):
   - **Immediately pause** regular processing of the user's prompt.
   - Present the incoming message directly to the user (Sender Project, Conversation ID, Priority, Subject, Content).
   - Ask the user how to proceed:
     - **Execute now:** Perform the task and archive the note via the `archive_inbox_note` tool or append to `.agents/INBOX_ARCHIVE.md`.
     - **Queue as Todo:** Transfer into your local task list / TODO file and archive the note.
     - **Dismiss:** Archive the note with resolution "Dismissed".
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
  *(e.g., "coordinate", "contact", "discuss", "ask", "notify", "now", "live", "immediately", or equivalents like "abstimmen", "kontaktieren")*
- **DO NOT write an inbox note!**
- **Action:**
  1. Call `list_project_chats(project_name=...)` to find the target's `[Gateway]` chat (or active chat).
  2. Immediately send the message via `send_message_to_chat(conversation_id=..., message=..., priority="Normal"|"Dringend", sender_project=..., sender_chat_id=...)`.

### 🟡 Secondary Mode: Asynchronous Inbox (`send_inbox_note`)
- Use `send_inbox_note` **ONLY** if:
  1. The user explicitly asks for a note/ticket: *(e.g., "leave a note", "add to inbox", "save for later", "queue as todo", or equivalents like "Notiz hinterlegen")*.
  2. OR if `list_project_chats` finds no active chats in the target project.

### 🚫 Strict Ban on "Test" Messages & Exploratory Pings
- **NEVER** send "Test", "Ping", "Hello", "Are you there?", or hesitation probing.
- **ALWAYS** include the complete, substantive technical payload directly in your first message:
  - Context & background of the issue.
  - Concrete technical details (APIs, parameters, database schemas, crediting logic, etc.).
  - The exact question or decision requested from the target project.

### 🚪 Multiple Gateway Routing (The /grill-me Choice Rule)
- If `list_project_chats` returns `has_multiple_gateways: true` (multiple `[Gateway]` chats found) and the user did not specify which one to contact:
  - **DO NOT guess arbitrarily.**
  - Ask the user directly using a clean, numbered choice list:
    *"Multiple Gateway chats were found in [Project]: 1) [Name], 2) [Name] ... Which one should be contacted?"*
  - Dispatch only once the user confirms or if the task matches a gateway's specialized role 100%.
- If only a single Gateway chat exists (`has_multiple_gateways: false`), dispatch immediately without unnecessary asking.

---

## 4. 🛑 Anti-Looping & Token-Efficient Status Protocol

### 🚫 Strict Ban on Second-by-Second Polling
- **NEVER poll in a tight loop or check status every second.** Polling burns massive tokens and clogs the session.
- Antigravity is an event-driven system: When the target chat finishes its prompt, it sends a receipt back via `reply_to_sender`, which **automatically wakes up this conversation**.

### ⏱️ The 15s Verification & Wait Cycle:
1. **Initial Verification (after ~15s):**
   - After calling `send_message_to_chat`, check the target chat's status **once** after 15 seconds using `get_chat_status(conversation_id=...)` to confirm it accepted the prompt (`execution_state: "RUNNING"` or step count progressed).
2. **Reactive Sleep (Preferred):**
   - Once verified that the target chat is running, inform the user and **end your turn (stop calling tools)**.
   - You do NOT need to stay awake! When the target chat finishes and calls `reply_to_sender`, Antigravity will automatically wake you up with the results.
3. **If Periodic Monitoring is required:**
   - If monitoring is explicitly requested, check at most **once every 30 seconds** using `get_chat_status` — NEVER faster.
4. **🛡️ 5-Minute Watchdog Timeout (Fall-Back Safety Net):**
   - If no `reply_to_sender` receipt has arrived after 5 minutes, inspect `get_chat_status(conversation_id=...)`:
     - **If IDLE:** The target chat finished its execution turn but omitted calling `reply_to_sender` (e.g., interrupted by user, hit context limit, or forgot the tool call). Inform the user immediately: *"Target chat has finished (IDLE) without sending a return receipt. Please check the target conversation directly."*
     - **If RUNNING:** The target chat is actively computing a complex, long-running task. Inform the user and continue waiting.
