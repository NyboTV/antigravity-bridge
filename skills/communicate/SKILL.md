---
name: communicate
description: Live Inter-Agent & Cross-Project Communication via antigravity-bridge MCP (/communicate).
---

# 📬 Antigravity Bridge (`/communicate`)

Use `call_mcp_tool` directly with `ServerName: "antigravity-bridge"`:
- `list_projects`: `{}`
- `list_project_chats`: `{ project_name: string }`
- `send_message_to_chat`: `{ conversation_id: string, message: string, priority?: "Normal"|"Dringend", sender_project?: string, sender_chat_id?: string }`
- `reply_to_sender`: `{ sender_chat_id: string, status_message: string, sender_project?: string }`
- `get_chat_status`: `{ conversation_id: string }`
