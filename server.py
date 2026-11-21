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
import time
import ssl
import errno
import argparse
import sqlite3
import subprocess
import datetime
import re
import shutil
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVER_VERSION = "1.2.0"

# Universal Paths
GEMINI_DIR = os.path.expanduser(os.environ.get("ANTIGRAVITY_HOME", r"~/.gemini/antigravity"))
DB_PATH = os.environ.get("ANTIGRAVITY_DB_PATH", os.path.join(GEMINI_DIR, "conversation_summaries.db"))

_CACHED_LS_SESSION = None


def find_agentapi():
    """Finds the agentapi executable across operating systems."""
    for key in ("ANTIGRAVITY_AGENTAPI_EXE", "AGENTAPI_PATH"):
        env_override = os.environ.get(key)
        if env_override and os.path.exists(env_override):
            return env_override

    which_path = shutil.which("agentapi") or shutil.which("agentapi.bat")
    if which_path:
        return which_path

    candidates = [
        os.path.join(GEMINI_DIR, "bin", "agentapi.bat"),
        os.path.join(GEMINI_DIR, "bin", "agentapi"),
        os.path.join(GEMINI_DIR, "bin", "agentapi.cmd"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


def _probe_connect_rpc_port(scheme, port, token, timeout=1.2):
    """Verifies that (scheme, port, token) is a real Antigravity Language Server ConnectRPC endpoint (HTTP 200),
    filtering out Sidecar HTTP/1.1 ports (401) and wrong-protocol listeners (400)."""
    url = f"{scheme}://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
    headers = {
        "Content-Type": "application/json",
        "Connect-Protocol-Version": "1",
    }
    if token:
        headers["x-codeium-csrf-token"] = token
    req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
    ctx = ssl._create_unverified_context() if scheme == "https" else None
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status == 200
    except Exception:
        return False


def discover_verified_ls_session(force_refresh=False):
    """Discovers and verifies the active Language Server ConnectRPC/h2c port & CSRF token.
    Primary path (Antigravity v2.34+): Official Sidecar / Agent environment variables
    (ANTIGRAVITY_LS_ADDRESS + ANTIGRAVITY_CSRF_TOKEN).
    Fallback path: Locale-safe TCP listener discovery (0.0.0.0:0 instead of locale-specific LISTENING)."""
    global _CACHED_LS_SESSION
    now = time.time()
    if (
        not force_refresh
        and _CACHED_LS_SESSION is not None
        and (now - _CACHED_LS_SESSION["ts"]) < 60.0
    ):
        return _CACHED_LS_SESSION

    # 1. Official Antigravity Sidecar / Agent Environment (0ms fast path!)
    env_addr = os.environ.get("ANTIGRAVITY_LS_ADDRESS", "").strip()
    env_tok = os.environ.get("ANTIGRAVITY_CSRF_TOKEN", "").strip()
    if env_addr and ":" in env_addr:
        try:
            env_port = int(env_addr.rsplit(":", 1)[1])
            preferred_scheme = "https" if env_addr.lower().startswith("https://") else "http"
            alt_scheme = "http" if preferred_scheme == "https" else "https"
            for sch in (preferred_scheme, alt_scheme):
                if _probe_connect_rpc_port(sch, env_port, env_tok):
                    _CACHED_LS_SESSION = {
                        "scheme": sch,
                        "port": env_port,
                        "http_port": env_port if sch == "http" else None,
                        "token": env_tok,
                        "ts": now,
                    }
                    return _CACHED_LS_SESSION
        except ValueError:
            pass

    # 2. Legacy Fallback (for Antigravity < 2.34 where --csrf_token was on CommandLine; locale-independent 0.0.0.0:0)
    candidates = []
    try:
        if os.name == "nt":
            ps_out = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name='language_server.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
                ],
                text=True,
                timeout=4,
            ).strip()
            net_out = subprocess.check_output(
                ["netstat.exe", "-ano", "-p", "tcp"],
                text=True,
                timeout=3,
            )
            ports_by_pid = {}
            for line in net_out.splitlines():
                # Locale-independent: match 0.0.0.0:0 instead of 'LISTENING' ('ABHOEREN' on German Windows)
                m = re.match(r"^\s*TCP\s+127\.0\.0\.1:(\d+)\s+0\.0\.0\.0:0\s+\S+\s+(\d+)\s*$", line, re.IGNORECASE)
                if m:
                    ports_by_pid.setdefault(int(m.group(2)), []).append(int(m.group(1)))

            if ps_out:
                parsed = json.loads(ps_out)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                for srv in parsed:
                    cmd_str = str(srv.get("CommandLine") or "")
                    tm = re.search(r"--csrf_token\s+(\S+)", cmd_str)
                    tok = tm.group(1) if tm else env_tok
                    pid = int(srv.get("ProcessId") or 0)
                    for p in sorted(set(ports_by_pid.get(pid, []))):
                        if tok and (p, tok) not in candidates:
                            candidates.append((p, tok))
    except Exception:
        pass

    for sch in ("http", "https"):
        for port, tok in candidates:
            if _probe_connect_rpc_port(sch, port, tok):
                _CACHED_LS_SESSION = {
                    "scheme": sch,
                    "port": port,
                    "http_port": port if sch == "http" else None,
                    "token": tok,
                    "ts": now,
                }
                return _CACHED_LS_SESSION

    return None


def call_connect_rpc(rpc_path, payload_obj, timeout=8.0):
    """Calls Antigravity Language Server directly via ConnectRPC JSON (HTTP/HTTPS) with automatic port re-discovery."""
    session = discover_verified_ls_session(force_refresh=False)
    if not session:
        session = discover_verified_ls_session(force_refresh=True)
    if not session:
        raise RuntimeError("Could not locate an active Antigravity Language Server RPC port.")

    body = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")

    for attempt in range(2):
        scheme = session["scheme"]
        port = session["port"]
        token = session["token"]
        url = f"{scheme}://127.0.0.1:{port}{rpc_path}"
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Connect-Protocol-Version": "1",
                "x-codeium-csrf-token": token,
            },
            method="POST",
        )
        ctx = ssl._create_unverified_context() if scheme == "https" else None
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw_resp = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw_resp) if raw_resp.strip() else {}
        except Exception as err:
            if attempt == 0:
                session = discover_verified_ls_session(force_refresh=True)
                if not session:
                    raise err
            else:
                raise err


def get_agentapi_env(force_refresh=False):
    """Ensures ANTIGRAVITY_LS_ADDRESS points to the verified HTTP/h2c port (never a Sidecar or HTTPS-only port)."""
    env = os.environ.copy()
    session = discover_verified_ls_session(force_refresh=force_refresh)
    if session and session.get("http_port") and session.get("token"):
        env["ANTIGRAVITY_LS_ADDRESS"] = f"localhost:{session['http_port']}"
        env["ANTIGRAVITY_CSRF_TOKEN"] = session["token"]
    return env


def run_agentapi_command(args, timeout=15):
    """Executes an agentapi subcommand cleanly against the verified HTTP/h2c port."""
    env = get_agentapi_env(force_refresh=True)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTHONLEGACYWINDOWSSTDIO"] = "0"

    ls_exe = os.environ.get("ANTIGRAVITY_AGENTAPI_EXE")
    if not ls_exe:
        default_ls = os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\resources\bin\language_server.exe")
        if os.path.exists(default_ls):
            ls_exe = default_ls
        else:
            try:
                proc_path = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", "(Get-Process language_server -ErrorAction SilentlyContinue | Select-Object -First 1).Path"],
                    text=True,
                    timeout=3
                ).strip()
                if proc_path and os.path.exists(proc_path):
                    ls_exe = proc_path
            except Exception:
                pass

    if ls_exe and os.path.exists(ls_exe):
        cmd = [ls_exe, "agentapi"] + args
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
            env=env
        )
    else:
        agentapi_cmd = find_agentapi()
        cmd = [agentapi_cmd] + args
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=(os.name == "nt"),
            env=env
        )


def dispatch_agent_message(recipient_id, content, display_title, sender_id=None):
    """Primary dispatch via verified ConnectRPC SendAgentMessage (<15ms, full UTF-8), with verified agentapi fallback."""
    effective_sender = sender_id if (sender_id and sender_id not in ("Unknown", "")) else recipient_id
    try:
        call_connect_rpc(
            "/exa.language_server_pb.LanguageServerService/SendAgentMessage",
            {
                "recipient": recipient_id,
                "senderId": effective_sender,
                "content": content,
                "displayTitle": display_title,
            },
            timeout=8.0,
        )
        return {"ok": True, "transport": "connect_rpc"}
    except Exception as rpc_err:
        # Fallback to CLI agentapi against verified HTTP/h2c port
        proc = run_agentapi_command(["send-message", f"--title={display_title}", recipient_id, content])
        if proc.returncode == 0:
            return {"ok": True, "transport": "agentapi"}
        return {
            "ok": False,
            "rpc_error": str(rpc_err),
            "returncode": proc.returncode,
            "stderr": proc.stderr.strip()[:500],
            "stdout": proc.stdout.strip()[:500],
        }

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
        "chats": chats[:8]
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
    """Sends a message directly into a target conversation via verified ConnectRPC / agentapi and wakes it up."""
    header = (
        f"\n\n---"
        f"\n🛰️ **[Antigravity-Bridge] Incoming Cross-Project Message**"
        f"\n- **Sender Project:** {sender_project}"
        f"\n- **Sender Conversation ID:** `{sender_chat_id}`"
        f"\n- **Priority:** {priority}"
        f"\n- **Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f"\n\n⚡ **DIRECT AUTONOMOUS EXECUTION REQUIRED:**"
        f"\nExecute the requested analysis, tasks, or queries immediately within this workspace. DO NOT pause or ask the user how to proceed."
        f"\n\n⚠️ **MANDATORY COMPLETION PROTOCOL:**"
        f"\nUpon finishing your task or analysis, you MUST invoke the tool `reply_to_sender` with:"
        f"\n- `sender_chat_id`: '{sender_chat_id}'"
        f"\n- `status_message`: Summary of actions taken, decisions, or answers (written in English)."
        f"\nThis automatically wakes up and notifies the originating conversation."
        f"\n---\n\n"
    )
    full_message = header + message
    try:
        res = dispatch_agent_message(
            recipient_id=conversation_id,
            content=full_message,
            display_title=f"Antigravity-Bridge ({sender_project})",
            sender_id=sender_chat_id,
        )
        if res.get("ok"):
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "message_dispatched": True,
                "transport": res.get("transport"),
                "user_reminder": "Remind the user to watch the target tab for tool approvals if needed."
            }
        else:
            return {
                "status": "error",
                "rpc_error": res.get("rpc_error"),
                "returncode": res.get("returncode"),
                "stderr": res.get("stderr"),
                "stdout": res.get("stdout")
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def tool_reply_to_sender(sender_chat_id, status_message, sender_project="Target"):
    """Sends an execution receipt or answer back to the originating chat."""
    if not sender_chat_id or sender_chat_id in ["Unknown", ""]:
        return {"status": "error", "error": "Invalid or missing sender_chat_id."}

    header = (
        f"\n\n---"
        f"\n✅ **[Antigravity-Bridge] Execution Receipt / Response**"
        f"\n- **Origin Project:** {sender_project}"
        f"\n- **Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f"\n---\n\n"
    )
    full_reply = header + status_message
    try:
        res = dispatch_agent_message(
            recipient_id=sender_chat_id,
            content=full_reply,
            display_title=f"Bridge Receipt ({sender_project})",
            sender_id=sender_chat_id,
        )
        if res.get("ok"):
            return {
                "status": "success",
                "sender_chat_id": sender_chat_id,
                "receipt_dispatched": True,
                "transport": res.get("transport")
            }
        return {
            "status": "error",
            "sender_chat_id": sender_chat_id,
            "receipt_dispatched": False,
            "error": res.get("stderr") or res.get("rpc_error")
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
    }
]

def handle_request(req):
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        params = req.get("params") or {}
        client_proto = params.get("protocolVersion", "2025-03-26")
        negotiated_proto = client_proto if client_proto in ("2025-03-26", "2024-11-05") else "2025-03-26"
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": negotiated_proto,
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "antigravity-bridge",
                    "version": SERVER_VERSION
                }
            }
        }

    elif method and method.startswith("notifications/"):
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

class McpStreamableHttpHandler(BaseHTTPRequestHandler):
    """MCP 2025-03-26 Streamable HTTP transport handler (localhost-only)."""

    def log_message(self, format_str, *args):
        return  # Silence noisy access logs

    def _check_origin(self):
        origin = (self.headers.get("Origin") or "").strip()
        if origin and not re.match(r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$", origin, re.IGNORECASE):
            self.send_response(403)
            self.end_headers()
            return False
        return True

    def do_OPTIONS(self):
        if not self._check_origin():
            return
        self.send_response(204)
        self.send_header("Allow", "POST, DELETE, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if not self._check_origin():
            return
        if self.path.startswith("/health"):
            body = json.dumps({
                "status": "ok",
                "name": "antigravity-bridge",
                "version": SERVER_VERSION,
                "lsEnvConfigured": bool(os.environ.get("ANTIGRAVITY_LS_ADDRESS") and os.environ.get("ANTIGRAVITY_CSRF_TOKEN")),
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Per MCP 2025-03-26 Streamable HTTP spec: return 405 when server does not expose GET SSE stream
        self.send_response(405)
        self.send_header("Allow", "POST, DELETE, OPTIONS")
        self.end_headers()

    def do_DELETE(self):
        if not self._check_origin():
            return
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        if not self._check_origin():
            return
        if not (self.path == "/" or self.path.startswith("/mcp")):
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length") or "0")
        raw_bytes = self.rfile.read(length) if length > 0 else b""
        session_hdr = self.headers.get("Mcp-Session-Id")

        try:
            parsed = json.loads(raw_bytes.decode("utf-8", errors="replace"))
        except Exception as err:
            err_body = json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {err}"}
            }).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)
            return

        if isinstance(parsed, list):
            responses = []
            for item in parsed:
                if isinstance(item, dict):
                    r = handle_request(item)
                    if r is not None and "id" in item:
                        responses.append(r)
            if not responses:
                self.send_response(202)
                if session_hdr:
                    self.send_header("Mcp-Session-Id", session_hdr)
                self.end_headers()
                return
            out_bytes = json.dumps(responses, ensure_ascii=False).encode("utf-8")
        elif isinstance(parsed, dict):
            # Notifications / responses without 'id' MUST receive 202 Accepted per MCP 2025-03-26 spec
            if "id" not in parsed:
                handle_request(parsed)
                self.send_response(202)
                if session_hdr:
                    self.send_header("Mcp-Session-Id", session_hdr)
                self.end_headers()
                return
            resp_obj = handle_request(parsed)
            if resp_obj is None:
                self.send_response(202)
                self.end_headers()
                return
            out_bytes = json.dumps(resp_obj, ensure_ascii=False).encode("utf-8")
        else:
            self.send_response(400)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if session_hdr:
            self.send_header("Mcp-Session-Id", session_hdr)
        self.send_header("Content-Length", str(len(out_bytes)))
        self.end_headers()
        self.wfile.write(out_bytes)


def run_http_server(port):
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), McpStreamableHttpHandler)
    except OSError as e:
        win_in_use = getattr(errno, "WSAEADDRINUSE", 10048)
        if e.errno in (errno.EADDRINUSE, win_in_use):
            sys.exit(0)
        raise
    httpd.serve_forever()


def _forward_to_local_sidecar(req, port=3841):
    """When invoked via stdio without ANTIGRAVITY_LS_ADDRESS, transparently delegates tool calls to the managed local Sidecar."""
    url = f"http://127.0.0.1:{port}/mcp"
    data = json.dumps(req, ensure_ascii=False).encode("utf-8")
    http_req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(http_req, timeout=15.0) as resp:
        if resp.status == 202:
            return None
        raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw.strip() else None


def run_stdio_server():
    has_direct_ls_env = bool(os.environ.get("ANTIGRAVITY_LS_ADDRESS"))
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line_str = line.strip()
            if not line_str:
                continue

            req = json.loads(line_str)
            resp = None
            if not has_direct_ls_env and isinstance(req, dict) and req.get("method") == "tools/call":
                try:
                    resp = _forward_to_local_sidecar(req, 3841)
                except Exception:
                    resp = handle_request(req)
            else:
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


def main():
    parser = argparse.ArgumentParser(description="Antigravity Bridge MCP Server")
    parser.add_argument(
        "--http-port",
        type=int,
        default=int(os.environ.get("ANTIGRAVITY_BRIDGE_HTTP_PORT") or "0"),
        help="Run as Streamable HTTP MCP server on 127.0.0.1:<port>/mcp (for Antigravity v2.34+ Sidecars).",
    )
    args, _ = parser.parse_known_args()
    if args.http_port > 0:
        run_http_server(args.http_port)
    else:
        run_stdio_server()


if __name__ == "__main__":
    main()
