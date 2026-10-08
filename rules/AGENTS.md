# 📬 Antigravity Bridge — Universal Inter-Agent Protocol

> This rule is automatically applied to all workspaces while the `antigravity-bridge` plugin is enabled.

---

## 1. ⚡ Live Incoming Cross-Project Messages (Direct Execution — NO Asking!)
When this chat receives a message from another project (indicated by the header `🛰️ **[Antigravity-Bridge] Incoming Cross-Project Message**`):
- **EXECUTE IMMEDIATELY BY DEFAULT:** Start working on the requested analysis, tasks, questions, or verifications right away within this workspace.
- **🚫 ABSOLUTE BAN ON INTERACTIVE PAUSING:** 
  - **DO NOT** pause or ask the user how to proceed.
  - **DO NOT** ask: *"Wie möchtest du verfahren? 1. Jetzt ausführen 2. Als To-Do vormerken 3. Verwerfen"*.
  - Treat the incoming message as a high-priority prompt to be fulfilled immediately and autonomously.
- **⚠️ Mandatory Return Receipt (`reply_to_sender`):**
  Once the requested task or investigation is finished, you **MUST** call `reply_to_sender(sender_chat_id=..., status_message=...)` with your findings or status. This automatically wakes up the originating conversation.
- Present the completed findings and actions taken directly in this chat.

---

## 2. 📬 Asynchronous Project Inbox (`.agents/INBOX.md` — Offline Tickets Only)
The file `.agents/INBOX.md` is strictly an offline fallback queue for when a project had no active chat or when a user explicitly queued a task for later.
- **Separation:** Live incoming chat messages are **NOT** inbox notes and do not require reading or modifying `.agents/INBOX.md`.
- **Handling Offline Notes:** If you are explicitly instructed to check the inbox or process pending offline notes:
  1. Inspect `.agents/INBOX.md` for unhandled note blocks (`### 📩 Incoming Message`).
  2. Execute the requested task in this workspace.
  3. Archive the handled note via `archive_inbox_note(project_name=..., note_subject=..., resolution="Executed")`.
  4. If a `sender_chat_id` is present, notify the sender via `reply_to_sender(sender_chat_id, status_message)`.

---

## 3. 🛡️ Workspace Boundary Protection & Strict Plugin Immutability
- **Never touch foreign code:** If your current task requires code modifications, service restarts, or database updates in a different repository or workspace, **never** modify foreign files directly.
- **🚫 ABSOLUTE BAN ON AUTONOMOUS MODIFICATION OF PLUGINS & MCP SERVERS:**
  Agents MUST NEVER autonomously inspect, edit, modify, patch, or debug files located in `~/.gemini/` (including `~/.gemini/config/plugins/`, `~/.gemini/antigravity/mcp_servers/`, rules, or skills).
- **🚨 MCP Failure & Error Protocol:**
  If an MCP tool fails or throws an unhandled error:
  1. **Acknowledge and Report Failure Immediately:** Stop execution and inform the user that the operation failed. Provide a brief error summary and direct the user to report it:
     > *"Antigravity Bridge encountered an error. Please report this issue on GitHub: https://github.com/NyboTV/antigravity-bridge/issues"*
  2. **Provide Full Technical Details on Demand:** If the user asks for details, explain the exact technical breakdown: which tool failed, what parameters were passed, the exact error code/stderr, and probable cause.
  3. **Optional User-Authorized Self-Repair Proposal (Strictly Conditional):**
     Offer the user the option to attempt a local fix, but **ONLY** accompanied by this explicit, mandatory warning:
     > ⚠️ **CAUTION:** Allowing the agent to inspect or patch the MCP server carries a high risk of completely breaking the plugin and cross-project communication setup. Proceed only if you want experimental local debugging instead of an official GitHub report.
     The agent MUST NOT touch any plugin files unless the user explicitly commands: *"Yes, attempt local repair"*.
- **Always delegate:** Use the `/communicate` slash command or the `antigravity-bridge` MCP server.
- **Execution Receipts:** If this conversation was woken up with a `sender_chat_id`, send a completion confirmation back using the `reply_to_sender` tool once the requested work is complete.

---

## 4. ⚡ Outgoing Cross-Project Communication (Live Wakeup vs. Asynchronous Inbox)

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

### 🔔 Mandatory User Alert: First-Time MCP Permissions & Gateway Monitoring
- Whenever you dispatch a message to another project via `send_message_to_chat`, **ALWAYS alert the user**:
  - Remind them that depending on Antigravity's security settings in that workspace, the target Gateway chat may require **manual user approval** for MCP tools, bash commands, or file access (especially on first contact).
  - Explicitly ask the user to keep an eye on the target chat tab to grant any pending permissions so the remote agent is not blocked.

### 🌐 Universal Inter-Agent Protocol Language: English ONLY
- **User Conversation:** Always communicate with the USER in their preferred language (e.g. German).
- **Inter-Agent Payloads (`send_message_to_chat`, `reply_to_sender`, `send_inbox_note`):**
  - **ALL cross-project messages, technical inquiries, audit requests, and return receipts MUST ALWAYS be written in English.**
  - **Rationale:** Inter-agent communication in English ensures universal model compatibility across different LLMs (Gemini, Claude, GPT), eliminates Windows-1252 / ASCII codepage mojibake errors, and guarantees technical precision.

---

## 5. 🛑 Anti-Looping & Token-Efficient Status Protocol

### 🚫 Strict Ban on Second-by-Second Polling
- **NEVER poll in a tight loop or check status every second.** Polling burns massive tokens and clogs the session.
- Antigravity is an event-driven system: When the target chat finishes its prompt, it sends a receipt back via `reply_to_sender`, which **automatically wakes up this conversation**.

### ⏱️ The 15s Verification & Wait Cycle:
1. **Initial Verification (after ~15s):**
   - After calling `send_message_to_chat`, check the target chat's status **once** after 15 seconds using `get_chat_status(conversation_id=...)` to confirm it accepted the prompt (`execution_state: "RUNNING"` or step count progressed).
2. **Reactive Sleep (Preferred):**
   - Once verified that the target chat is running, inform the user (including the MCP approval reminder to watch the target tab) and **end your turn (stop calling tools)**.
   - You do NOT need to stay awake! When the target chat finishes and calls `reply_to_sender`, Antigravity will automatically wake you up with the results.
3. **If Periodic Monitoring is required:**
   - If monitoring is explicitly requested, check at most **once every 30 seconds** using `get_chat_status` — NEVER faster.
4. **🛡️ 5-Minute Watchdog Timeout (Fall-Back Safety Net):**
   - If no `reply_to_sender` receipt has arrived after 5 minutes, inspect `get_chat_status(conversation_id=...)`:
     - **If IDLE:** The target chat finished its execution turn but omitted calling `reply_to_sender` (e.g., interrupted by user, hit context limit, or forgot the tool call). Inform the user immediately: *"Target chat has finished (IDLE) without sending a return receipt. Please check the target conversation directly."*
     - **If RUNNING:** The target chat is actively computing a complex, long-running task. Inform the user and continue waiting.
