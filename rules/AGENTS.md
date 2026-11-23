# 📬 Antigravity Bridge — Live Inter-Agent Protocol

> **⚡ ZERO-TURN MCP RULE:** NEVER read `SKILL.md` or `.json` schema files before calling `antigravity-bridge` tools. Call `call_mcp_tool(ServerName="antigravity-bridge", ToolName=..., Arguments=...)` directly in Turn 1 using these exact signatures:
- `list_projects`: `{}`
- `list_project_chats`: `{ project_name: string }`
- `spawn_project_chat`: `{ project_name: string, title: string, prompt: string, model?: string }`
- `get_mcp_health`: `{}`
- `send_message_to_chat`: `{ conversation_id: string, message: string, priority?: "Normal"|"Dringend", sender_project?: string, sender_chat_id?: string }`
- `reply_to_sender`: `{ sender_chat_id: string, status_message: string, sender_project?: string }`
- `get_chat_status`: `{ conversation_id: string }`

---

## 1. ⚡ Incoming Cross-Project Messages (`🛰️ [Antigravity-Bridge]`)
- **Execute Immediately:** Never pause or ask the user how to proceed. Fulfill the request autonomously within this workspace (respecting read-only if it is a pure question).
- **Mandatory Receipt:** When finished, you **MUST** call `reply_to_sender(sender_chat_id=..., status_message=...)` in English to wake up the sender chat.

## 2. 🚀 Outgoing Cross-Project Communication (Live Wakeup Only)
- **Workflow:** Call `list_project_chats(project_name=...)` -> dispatch full technical payload via `send_message_to_chat` (pure 7-bit ASCII/English, no emojis/em-dashes in payload to avoid Windows gRPC encoding errors, no "test/ping" messages).
- **Multiple Gateways:** If `has_multiple_gateways: true` and target is ambiguous, ask the user which Gateway chat to contact.
- **Wait Cycle:** Check `get_chat_status` **once** after ~15s to verify `RUNNING`, remind the user to watch the target tab for tool approvals, and **end your turn** (reactive wakeup handles the reply).

## 3. 🛡️ Immutability & Error Protocol
- Never modify foreign workspaces directly or autonomously edit `~/.gemini/` plugin files. If an MCP tool fails, stop and report: *"Antigravity Bridge encountered an error: https://github.com/NyboTV/antigravity-bridge/issues"*.
