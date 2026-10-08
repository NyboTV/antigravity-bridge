#!/usr/bin/env python3
"""
Antigravity Bridge MCP Server
Multi-agent & cross-project communication, chat wakeup, and inbox dispatching
for Google Antigravity 2.0.

Author: nybotv
License: MIT
"""

import sys
import os
import json
import sqlite3
import subprocess
import datetime
import re
import shutil
import urllib.parse

# Universal Paths
GEMINI_DIR = os.path.expanduser(os.environ.get("ANTIGRAVITY_HOME", r"~/.gemini/antigravity"))
DB_PATH = os.environ.get("ANTIGRAVITY_DB_PATH", os.path.join(GEMINI_DIR, "conversation_summaries.db"))

def find_agentapi():
    """Finds the agentapi executable across operating systems."""
    env_override = os.environ.get("AGENTAPI_PATH")
    if env_override and os.path.exists(env_override):
        return env_override
    
    which_path = shutil.which("agentapi") or shutil.which("agentapi.bat")
    if which_path:
        return which_path

    # Check ~/.gemini/antigravity/bin/
    candidates = [
        os.path.join(GEMINI_DIR, "bin", "agentapi.bat"),
        os.path.join(GEMINI_DIR, "bin", "agentapi"),
        os.path.join(GEMINI_DIR, "bin", "agentapi.cmd"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

def parse_workspace_uri_to_path(uri):
    """Converts a file:// URI to a local filesystem path."""
    if not uri:
        return None
    try:
        # uri might be JSON array or single URI
        if uri.startswith("[") and uri.endswith("]"):
            uris = json.loads(uri)
            if uris:
                uri = uris[0]
            else:
                return None
        
        decoded = urllib.parse.unquote(uri)
        if decoded.startswith("file:///"):
            path = decoded[8:]
            # Windows drive letter e.g. "d:/Projekte" or "D:/Projekte"
            if len(path) > 2 and path[1] == ":":
                path = path.replace("/", "\\")
            else:
                # Unix path
                path = "/" + path.lstrip("/")
            return os.path.normpath(path)
    except Exception:
        pass
    return None

def get_db():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Antigravity SQLite database not found at: {DB_PATH}")
    return sqlite3.connect(DB_PATH)

def discover_all_projects():
    """Dynamically extracts all registered projects from conversation_summaries.db."""
    projects = {}
    try:
        conn = get_db()
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT DISTINCT project_id, workspace_uris 
            FROM conversation_summaries 
            WHERE workspace_uris != '[]' AND workspace_uris != ''
        """).fetchall()

        for pid, w_raw in rows:
            parsed_path = parse_workspace_uri_to_path(w_raw)
            if parsed_path:
                pname = os.path.basename(parsed_path.rstrip(r"\/"))
                if not pname:
                    pname = pid
                if pname not in projects:
                    projects[pname] = parsed_path
        conn.close()
    except Exception:
        pass
    return projects

def tool_list_projects():
    """Lists all detected Antigravity projects and inbox availability."""
    projects_dict = discover_all_projects()
    result = []
    
    conn = get_db()
    cursor = conn.cursor()

    for pname, ppath in projects_dict.items():
        inbox_file = os.path.join(ppath, ".agents", "INBOX.md")
        has_inbox = os.path.exists(inbox_file)
        
        # Count chats
        chat_count = 0
        try:
            row = cursor.execute(
                "SELECT COUNT(*) FROM conversation_summaries WHERE workspace_uris LIKE ?",
                (f"%{pname}%",)
            ).fetchone()
            if row:
                chat_count = row[0]
        except Exception:
            pass

        result.append({
            "project_name": pname,
            "project_path": ppath,
            "has_inbox": has_inbox,
            "inbox_path": inbox_file if has_inbox else None,
            "active_chats_count": chat_count
        })
    conn.close()
    return {"projects": sorted(result, key=lambda x: x["project_name"].lower())}

def tool_list_project_chats(project_name):
    """Lists all chats for a specific project, highlighting [Gateway] chats."""
    conn = get_db()
    cursor = conn.cursor()
    
    rows = cursor.execute("""
        SELECT conversation_id, title, project_id, workspace_uris, last_modified_time
        FROM conversation_summaries 
        WHERE workspace_uris LIKE ? OR project_id LIKE ?
        ORDER BY last_modified_time DESC
    """, (f"%{project_name}%", f"%{project_name}%")).fetchall()
    
    chats = []
    gateway_chats = []

    for cid, title, pid, w_raw, updated in rows:
        title_str = title or "Untitled Chat"
        is_gateway = "[gateway]" in title_str.lower()
        
        chat_item = {
            "conversation_id": cid,
            "title": title_str,
            "is_gateway": is_gateway,
            "last_updated": updated
        }
        chats.append(chat_item)
        if is_gateway:
            gateway_chats.append(chat_item)

    conn.close()
    return {
        "project_name": project_name,
        "total_chats": len(chats),
        "gateway_chats": gateway_chats,
        "has_multiple_gateways": len(gateway_chats) > 1,
        "recommended_gateway_chat": gateway_chats[0] if gateway_chats else (chats[0] if chats else None),
        "chats": chats[:25]
    }

def tool_get_chat_status(conversation_id):
    """Checks the live execution status of a conversation (IDLE vs RUNNING, step count)."""
    conn = get_db()
    cursor = conn.cursor()
    row = cursor.execute("""
        SELECT conversation_id, title, status, not_fully_idle, step_count, last_modified_time
        FROM conversation_summaries
        WHERE conversation_id = ?
    """, (conversation_id,)).fetchone()
    conn.close()
    if not row:
        return {"status": "not_found", "conversation_id": conversation_id}
    
    cid, title, status, not_idle, steps, last_mod = row
    is_running = (status == "CASCADE_RUN_STATUS_RUNNING" or not_idle == 1)
    return {
        "status": "success",
        "conversation_id": cid,
        "title": title,
        "is_running": is_running,
        "execution_state": "RUNNING" if is_running else "IDLE",
        "step_count": steps,
        "last_modified": last_mod
    }

def tool_send_message_to_chat(conversation_id, message, priority="Normal", sender_project="Unknown", sender_chat_id="Unknown"):
    """Sends a message directly into a target conversation via agentapi and wakes it up."""
    agentapi_cmd = find_agentapi()
    if not os.path.exists(agentapi_cmd):
        return {
            "status": "error",
            "error": f"agentapi executable not found at '{agentapi_cmd}'. Set AGENTAPI_PATH environment variable."
        }

    header = (
        f"\n\n---"
        f"\n🛰️ **[Antigravity-Bridge] Incoming Cross-Project Message**"
        f"\n- **Sender Project:** {sender_project}"
        f"\n- **Sender Conversation ID:** `{sender_chat_id}`"
        f"\n- **Priority:** {priority}"
        f"\n- **Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f"\n\n⚠️ **MANDATORY COMPLETION PROTOCOL:**"
        f"\nUpon finishing your task or analysis, you MUST invoke the tool `reply_to_sender` with:"
        f"\n- `sender_chat_id`: '{sender_chat_id}'"
        f"\n- `status_message`: Summary of actions taken, decisions, or answers."
        f"\nThis automatically wakes up and notifies the originating conversation."
        f"\n---\n\n"
    )
    full_message = header + message

    cmd = [agentapi_cmd, "send-message", full_message, "--conversation-id", conversation_id]
    
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            shell=(os.name == "nt")
        )
        if proc.returncode == 0:
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "message_dispatched": True,
                "output": proc.stdout.strip()
            }
        else:
            return {
                "status": "error",
                "returncode": proc.returncode,
                "stderr": proc.stderr.strip(),
                "stdout": proc.stdout.strip()
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def tool_reply_to_sender(sender_chat_id, status_message, sender_project="Target"):
    """Sends an execution receipt or answer back to the originating chat."""
    if not sender_chat_id or sender_chat_id in ["Unknown", ""]:
        return {"status": "error", "error": "Invalid or missing sender_chat_id."}

    agentapi_cmd = find_agentapi()
    header = (
        f"\n\n---"
        f"\n✅ **[Antigravity-Bridge] Execution Receipt / Response**"
        f"\n- **Origin Project:** {sender_project}"
        f"\n- **Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f"\n---\n\n"
    )
    full_reply = header + status_message
    
    cmd = [agentapi_cmd, "send-message", full_reply, "--conversation-id", sender_chat_id]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            shell=(os.name == "nt")
        )
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "output": proc.stdout.strip() if proc.returncode == 0 else proc.stderr.strip()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def tool_send_inbox_note(target_project, sender_project, subject, content, priority="Normal", sender_chat_id="Unknown"):
    """Appends an asynchronous task note into target project's .agents/INBOX.md."""
    projects_dict = discover_all_projects()
    target_path = projects_dict.get(target_project)
    
    if not target_path or not os.path.exists(target_path):
        return {"status": "error", "error": f"Target project path for '{target_project}' not found."}

    agents_dir = os.path.join(target_path, ".agents")
    os.makedirs(agents_dir, exist_ok=True)
    inbox_file = os.path.join(agents_dir, "INBOX.md")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"""
---
### 📩 Incoming Message
- **Timestamp:** {timestamp}
- **Sender Project:** {sender_project}
- **Sender Conversation ID:** `{sender_chat_id}`
- **Priority:** {priority}
- **Subject:** {subject}

#### Content:
{content.strip()}
---
"""
    try:
        with open(inbox_file, "a", encoding="utf-8") as f:
            f.write(entry)
        return {
            "status": "success",
            "target_project": target_project,
            "inbox_file": inbox_file,
            "timestamp": timestamp,
            "note_appended": True
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def tool_archive_inbox_note(project_name, note_subject, resolution="Resolved"):
    """Archives a handled note from .agents/INBOX.md to .agents/INBOX_ARCHIVE.md."""
    projects_dict = discover_all_projects()
    target_path = projects_dict.get(project_name)
    if not target_path:
        return {"status": "error", "error": f"Project '{project_name}' not found."}

    inbox_file = os.path.join(target_path, ".agents", "INBOX.md")
    archive_file = os.path.join(target_path, ".agents", "INBOX_ARCHIVE.md")

    if not os.path.exists(inbox_file):
        return {"status": "error", "error": f"No INBOX.md found in {project_name}."}

    try:
        with open(inbox_file, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = re.split(r'\n(?=---\n### 📩 )', content)
        remaining_blocks = []
        archived_blocks = []

        for b in blocks:
            if not b.strip():
                continue
            if note_subject.lower() in b.lower():
                archive_entry = b.strip() + f"\n- **Status:** {resolution} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                archived_blocks.append(archive_entry)
            else:
                remaining_blocks.append(b)

        if not archived_blocks:
            return {"status": "not_found", "message": f"No note matching subject '{note_subject}' found."}

        with open(inbox_file, "w", encoding="utf-8") as f:
            f.write("\n".join(remaining_blocks).strip() + "\n" if remaining_blocks else "# 📬 Inter-Agent INBOX\n\n*(No unread messages)*\n")

        with open(archive_file, "a", encoding="utf-8") as f:
            for ab in archived_blocks:
                f.write(f"\n{ab}\n---\n")

        return {
            "status": "success",
            "archived_count": len(archived_blocks),
            "archive_file": archive_file
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


TOOLS = [
    {
        "name": "list_projects",
        "description": "Lists all registered Google Antigravity projects, workspace paths, and active chat metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_project_chats",
        "description": "Lists active conversations for a specific project from Antigravity database, highlighting [Gateway] dispatcher chats.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name of the project (e.g. 'Nyeo', 'ServerZentrum', 'Gamebot-Systems', 'Anwalt')"
                }
            },
            "required": ["project_name"]
        }
    },
    {
        "name": "get_chat_status",
        "description": "Checks the live execution status of a conversation (e.g. whether it is RUNNING, IDLE, or finished, along with current step count).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation ID to inspect"
                }
            },
            "required": ["conversation_id"]
        }
    },
    {
        "name": "send_message_to_chat",
        "description": "Sends a message directly into another project's active conversation via agentapi, waking it up immediately.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversation_id": {
                    "type": "string",
                    "description": "Target conversation ID"
                },
                "message": {
                    "type": "string",
                    "description": "The message / instruction content"
                },
                "priority": {
                    "type": "string",
                    "enum": ["Normal", "Dringend"],
                    "default": "Normal"
                },
                "sender_project": {
                    "type": "string",
                    "description": "Name of the sending project"
                },
                "sender_chat_id": {
                    "type": "string",
                    "description": "Conversation ID of the sending chat for replies"
                }
            },
            "required": ["conversation_id", "message"]
        }
    },
    {
        "name": "reply_to_sender",
        "description": "Sends an execution receipt or reply back to the originating sender_chat_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sender_chat_id": {
                    "type": "string",
                    "description": "Conversation ID of the initial sender"
                },
                "status_message": {
                    "type": "string",
                    "description": "The result, status report, or confirmation"
                },
                "sender_project": {
                    "type": "string",
                    "description": "Name of the replying project"
                }
            },
            "required": ["sender_chat_id", "status_message"]
        }
    },
    {
        "name": "send_inbox_note",
        "description": "Appends an asynchronous task note into target project's .agents/INBOX.md.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_project": {
                    "type": "string",
                    "description": "Destination project name"
                },
                "sender_project": {
                    "type": "string",
                    "description": "Sending project name"
                },
                "subject": {
                    "type": "string",
                    "description": "Short subject / topic"
                },
                "content": {
                    "type": "string",
                    "description": "Detailed task instructions"
                },
                "priority": {
                    "type": "string",
                    "enum": ["Normal", "Dringend"],
                    "default": "Normal"
                },
                "sender_chat_id": {
                    "type": "string",
                    "description": "Optional conversation ID"
                }
            },
            "required": ["target_project", "sender_project", "subject", "content"]
        }
    },
    {
        "name": "archive_inbox_note",
        "description": "Archives a handled note from .agents/INBOX.md to .agents/INBOX_ARCHIVE.md.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Project where the inbox resides"
                },
                "note_subject": {
                    "type": "string",
                    "description": "Subject or part of text to match"
                },
                "resolution": {
                    "type": "string",
                    "description": "Resolution note (e.g. 'Resolved', 'Queued as Todo', 'Dismissed')"
                }
            },
            "required": ["project_name", "note_subject"]
        }
    }
]

def handle_request(req):
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "antigravity-bridge",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == "tools/call":
        params = req.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})

        try:
            if name == "list_projects":
                res = tool_list_projects()
            elif name == "list_project_chats":
                res = tool_list_project_chats(args.get("project_name"))
            elif name == "get_chat_status":
                res = tool_get_chat_status(args.get("conversation_id"))
            elif name == "send_message_to_chat":
                res = tool_send_message_to_chat(
                    conversation_id=args.get("conversation_id"),
                    message=args.get("message"),
                    priority=args.get("priority", "Normal"),
                    sender_project=args.get("sender_project", "Unknown"),
                    sender_chat_id=args.get("sender_chat_id", "Unknown")
                )
            elif name == "reply_to_sender":
                res = tool_reply_to_sender(
                    sender_chat_id=args.get("sender_chat_id"),
                    status_message=args.get("status_message"),
                    sender_project=args.get("sender_project", "Target")
                )
            elif name == "send_inbox_note":
                res = tool_send_inbox_note(
                    target_project=args.get("target_project"),
                    sender_project=args.get("sender_project"),
                    subject=args.get("subject"),
                    content=args.get("content"),
                    priority=args.get("priority", "Normal"),
                    sender_chat_id=args.get("sender_chat_id", "Unknown")
                )
            elif name == "archive_inbox_note":
                res = tool_archive_inbox_note(
                    project_name=args.get("project_name"),
                    note_subject=args.get("note_subject"),
                    resolution=args.get("resolution", "Erledigt")
                )
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{name}' not found."
                    }
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(res, indent=2, ensure_ascii=False)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"error": str(e)}, indent=2)
                        }
                    ],
                    "isError": True
                }
            }

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found."
            }
        }

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line_str = line.strip()
            if not line_str:
                continue

            req = json.loads(line_str)
            resp = handle_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
