# 🛰️ Antigravity Bridge

> **Cross-Project & Inter-Agent Communication Plugin for Google Antigravity 2.0**  
> Wake up chats across workspaces, delegate tasks cleanly, and manage project inboxes with the `/communicate` slash command and zero-dependency MCP server.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Compatible-orange.svg)](https://modelcontextprotocol.io/)

---

## 💡 Why Antigravity Bridge? (The Problem & Purpose)

In modern development, complex applications rarely live in a single isolated folder. You often have a **Web Frontend**, an **API Backend**, a **DevOps / Infrastructure** setup, or microservices split across different directories or workspaces.

In **Google Antigravity 2.0**, each project workspace operates in its own isolated environment. While this keeps contexts focused and clean, it introduces major friction:

### 🚨 The Problem:
* **Context Pollution & Breakage:** If an agent in your Frontend project attempts to edit files in your Backend or Server project directly, it lacks the target project's specific linters, dependencies, and `AGENTS.md` guidelines—frequently leading to hallucinations and broken foreign code.
* **Manual Workspace Switching:** You must constantly stop what you're doing, switch project workspaces in Antigravity, open a chat, re-explain the entire context from scratch, and copy results back manually.
* **No Inter-Agent Collaboration:** There was previously no native mechanism for an agent in Project A to wake up or hand off tasks to an agent in Project B.

### ✨ The Solution & Benefits:
* 🚀 **Zero Context Loss / Stay in Your Flow:** Never leave your active chat. With `/communicate`, your agent directly dispatches instructions to the responsible project agent with full context.
* 🛡️ **Strict Architectural Hygiene & Domain Isolation:** Each agent remains strictly responsible for its own codebase. The frontend agent codes frontend; the infrastructure agent manages ports and reverse proxies.
* 🔁 **Closed-Loop Feedback:** When the target agent finishes, it automatically reports an execution receipt (`reply_to_sender`) back to your originating chat.
* 📬 **Asynchronous vs. Real-Time Flexibility:**
  * Need it **now**? Wakes up the target Gateway chat immediately.
  * Need it **later**? Drops an append-only note into `.agents/INBOX.md`, where the target agent will pick it up on its next prompt.
* 🏢 **True Multi-Agent Team Dynamics:** Turns independent project chats into a cohesive, coordinated team of autonomous agents across your entire machine.

---

## 🌟 Key Features

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
