# 🛰️ Antigravity Bridge

> **Cross-Project & Inter-Agent Communication Plugin for Google Antigravity 2.0**  
> Wake up chats across workspaces, delegate tasks cleanly, and manage project inboxes with the `/communicate` slash command and zero-dependency MCP server.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Compatible-orange.svg)](https://modelcontextprotocol.io/)

---

## 🌟 Features

- ⚡ **Live Cross-Project Dispatching:** Wake up active conversations in other projects and workspaces via `agentapi` without leaving your current chat.
- 📬 **Append-Only Inbox System:** Asynchronously queue actionable task notes into `.agents/INBOX.md` of target projects without touching foreign code directly.
- 🔁 **Bidirectional Receipt Loop:** Subordinate agents send execution receipts and completion reports directly back to the requester chat (`reply_to_sender`).
- 🚪 **Gateway Chat Routing:** Automatically discovers and targets designated project dispatchers (e.g. `[Gateway] Backend Dispatcher`).
- 💬 **Integrated Slash Command:** Includes `/communicate` for instant command-driven invocation.
- 🛡️ **Zero External Dependencies:** Built entirely with Python 3 standard library (`sqlite3`, `subprocess`, `json`, `urllib`). No virtual environment or `pip install` required!

---

## 🚀 Quick Start & Installation

### Option 1: Install as Antigravity Plugin (Recommended)

Clone the repository directly into your Antigravity plugins directory:

**Windows (PowerShell):**
```powershell
git clone https://github.com/nybotv/antigravity-bridge.git "$HOME\.gemini\config\plugins\antigravity-bridge"
```

**macOS / Linux:**
```bash
git clone https://github.com/nybotv/antigravity-bridge.git ~/.gemini/config/plugins/antigravity-bridge
```

*Restart Antigravity once. Both the MCP server and the `/communicate` command are immediately active!*

---

### Option 2: Project-Level Git Submodule

If you want to bundle the bridge with a specific workspace repository:

```bash
git submodule add https://github.com/nybotv/antigravity-bridge.git .agents/plugins/antigravity-bridge
```

---

### Option 3: Manual MCP Server Integration

Add the server to your `~/.gemini/config/mcp_config.json` (or Claude Desktop configuration):

```json
{
  "mcpServers": {
    "antigravity-bridge": {
      "command": "python",
      "args": [
        "path/to/antigravity-bridge/server.py"
      ]
    }
  }
}
```

---

## 💬 Usage & `/communicate` Slash Command

Simply type `/communicate` in any Antigravity chat:

```text
/communicate Tell the Infrastructure project to restart the preview service
```

Or run it interactively:
1. Type `/communicate`
2. The agent queries all active projects and lists their gateway dispatchers.
3. Select the target chat and confirm the message.

---

## 🛠️ Exposed MCP Tools

| Tool | Description |
|---|---|
| `list_projects` | Lists all detected Antigravity projects, workspace directories, and chat metrics. |
| `list_project_chats` | Lists active conversations for a project from Antigravity SQLite DB, highlighting `[Gateway]` chats. |
| `send_message_to_chat` | Sends a message directly into an active conversation via `agentapi send-message`, waking it up immediately. |
| `reply_to_sender` | Sends an execution receipt or status update back to the `sender_chat_id`. |
| `send_inbox_note` | Safely appends an asynchronous task into target project's `.agents/INBOX.md`. |
| `archive_inbox_note` | Moves resolved tasks from `.agents/INBOX.md` to `.agents/INBOX_ARCHIVE.md`. |

---

## 🏗️ Architecture

```text
  [Active Workspace / Chat A]
            │
            ▼  (calls /communicate)
  [antigravity-bridge MCP Server]
       ├── Direct Wakeup ──────────► [agentapi send-message] ──► [Target Chat B (Gateway)]
       │                                                                  │
       │                                                      (finishes & sends receipt)
       │                                                                  ▼
       │◄─────────────────────────── [reply_to_sender] ───────────────────┘
       │
       └── Asynchronous Task ──────► [.agents/INBOX.md of Target Project]
                                                   │
                                          (checked on next prompt)
                                                   ▼
                                       [Target Agent prompts user]
```

### The Gateway Pattern
To ensure messages land in the correct project thread in Antigravity's left sidebar, create one permanent dispatcher chat in each project:
- `[Gateway] Backend Dispatcher`
- `[Gateway] Infra Dispatcher`
- `[Gateway] Frontend Dispatcher`

The bridge automatically detects `[Gateway]` in conversation titles and routes cross-project requests there by default.

---

## 📄 License

MIT License © 2026 [nybotv](https://github.com/nybotv)
