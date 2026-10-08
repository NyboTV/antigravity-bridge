---
name: communicate-start
description: Initializes the current conversation as an official [Gateway] Dispatcher for this project workspace. Prompts the user with a 5-option menu (Backend, Frontend, DevOps, Tester, Custom), renames the chat via MCP rename_chat tool, and displays the Gateway operational rules.
---

# 🚀 Gateway Initialization Protocol (`/communicate-start`)

This skill initializes and configures the current active conversation as an official **`[Gateway]` Dispatcher** for the current project workspace.

---

## 🎯 When to Use
- The user types **/communicate-start** as the very first prompt in a new chat.
- The user wants to register this chat as a dedicated dispatch gateway so other projects can find and wake it up.

---

## 📋 Execution Steps

### Step 1: Identify Conversation Context
- Detect the current `Conversation ID` from your runtime context.

### Step 2: Role Selection (`/grill-me` Style)
If the user already specified the role (e.g. `/communicate-start Backend`), proceed directly to Step 3. Otherwise, present the 5 standardized options:

```text
Wie soll dieser Gateway-Chat heißen?
1. [Gateway] Backend Dispatcher (API, Datenbank, Server-Logik)
2. [Gateway] Frontend Dispatcher (Web-UI, Clients, Benutzeroberfläche)
3. [Gateway] DevOps / Infra Dispatcher (VMs, Docker, Nginx/Caddy, Ports)
4. [Gateway] QA & Tester Dispatcher (Tests, Audits, Verifikation)
5. Eigener Name (z. B. "[Gateway] General Dispatcher" oder frei wählbar)
```

*(Wait for the user's choice before renaming).*

### Step 3: Auto-Prefix & Rename Conversation
Once the user chooses an option or enters a custom name:
1. **Mandatory Prefix Verification:**
   - Inspect the provided name.
   - Check if it starts with `[Gateway]` (case-insensitive, e.g. `[gateway]`, `gateway`, `[GATEWAY]`).
   - If the `[Gateway] ` prefix is missing, **automatically prepend `[Gateway] `** (e.g. user writes `Server Coordinator` -> convert to `[Gateway] Server Coordinator`).
   - Always ensure the final string follows the standardized format: `[Gateway] <Name>`.
2. **Execute Database Rename:**
   - Call the MCP tool:
     `rename_chat(conversation_id="<current_id>", new_title="[Gateway] <Formatted Name>")`
   - Antigravity's SQLite database updates immediately, reflecting the new title in the project sidebar.


### Step 4: Output the Gateway Operating Contract
Output an affirmative confirmation and reinforce the binding rules:

```markdown
---
### 🚪 [Gateway] Dispatcher initialisiert: `<Neuer Titel>`
Dieser Chat ist nun offiziell in Antigravity als Gateway-Empfänger für dieses Projekt registriert.

#### 📜 Verbindliche Gateway-Regeln für diesen Chat:
1. **Empfangsbereitschaft:** Andere Projekte können diesen Chat ab sofort via `/communicate` und MCP automatisch finden und aufwecken.
2. **⚠️ Zwingende Quittungspflicht (`reply_to_sender`):** Wenn dieser Chat eine eingehende Nachricht mit `sender_chat_id` erhält, MUSST du nach Erledigung zwingend das Tool `reply_to_sender(sender_chat_id, status_message)` aufrufen, damit der Ursprungschat aufgeweckt wird.
3. **🛡️ Projekt-Schutz:** Bearbeite niemals fremden Code außerhalb deines Workspace. Delegiere Fremdaufgaben stets über `/communicate`.
---
```
