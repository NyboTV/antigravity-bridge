---
name: communicate-start
description: Initializes the current conversation as an official [Gateway] Dispatcher for this project workspace. Prompts the user with a 5-option menu (Backend, Frontend, DevOps, Tester, Custom), formats the standardized [Gateway] title, and displays the Gateway operational rules.
---

# 🚀 Gateway Initialization Protocol (`/communicate-start`)

This skill initializes and configures the current active conversation as an official **`[Gateway]` Dispatcher** for the current project workspace.

---

## 🎯 When to Use
- The user types **/communicate-start** as the first prompt in a chat.
- The user wants to register this chat as a dedicated dispatch gateway so other projects can find and wake it up.

---

## 🛑 STRICT RULE: ZERO PRE-FLIGHT EXPLORATION (Ask IMMEDIATELY)
- **DO NOT run ANY tools before asking the question.**
- **DO NOT read or inspect MCP files, schemas, configs, or python scripts (e.g., `server.py`).**
- **DO NOT check tool availability or explore directories.**
- **IMMEDIATE ACTION:** If the user has not already specified a role in their prompt, your **VERY FIRST ACTION MUST BE TO ASK THE QUESTION IMMEDIATELY** using `ask_question` (or direct text output). Zero delay, zero pre-flight steps.

---

## 📋 Execution Protocol

### Step 1: Immediate Role Selection (First Turn)
If the user already specified a role (e.g. `/communicate-start Backend`), proceed directly to Step 2.

Otherwise, **immediately call `ask_question`** (or display the options):
- Question: `Wie soll dieser Gateway-Chat für dieses Projekt heißen?`
- Options:
  1. `[Gateway] Backend Dispatcher (API, Datenbank, Server-Logik)`
  2. `[Gateway] Frontend Dispatcher (Web-UI, Clients, Benutzeroberfläche)`
  3. `[Gateway] DevOps / Infra Dispatcher (VMs, Docker, Nginx/Caddy, Ports)`
  4. `[Gateway] QA & Tester Dispatcher (Tests, Audits, Verifikation)`
  *(Option 5 "Other / Eigener Name" is automatically provided by the UI).*

**STOP HERE AND WAIT FOR USER SELECTION. Do NOT run any tools.**

---

### Step 2: Auto-Prefix & Confirmation (Second Turn)
Only **after** the user chooses an option or enters a custom name:
1. **Mandatory Prefix Verification:**
   - Inspect the provided name.
   - Check if it starts with `[Gateway]` (case-insensitive, e.g. `[gateway]`, `gateway`, `[GATEWAY]`).
   - If the `[Gateway] ` prefix is missing, **automatically prepend `[Gateway] `** (e.g. user writes `Caleb` -> convert to `[Gateway] Caleb`).
   - Always ensure the final string follows the standardized format: `[Gateway] <Name>`.

2. **Output Confirmation & UI Rename Guidance:**
   Since Antigravity manages active conversation tab titles in its IDE session, output the clear formatted name and prompt the user to rename the tab:

```markdown
---
### 🚪 [Gateway] Dispatcher bereit: `<Formatierter Titel>`
Dieser Chat ist nun bereit als Gateway-Empfänger für dieses Projekt.

> ✏️ **Wichtig für die UI-Erkennung:**
> Bitte benenne diesen Chat-Tab in der linken Antigravity-Sidebar kurz um zu:
> **`<Formatierter Titel>`** *(Klick auf den Titel oder das Stift-Symbol)*

#### 📜 Verbindliche Gateway-Regeln für diesen Chat:
1. **Empfangsbereitschaft:** Andere Projekte können diesen Chat ab sofort via `/communicate` und MCP automatisch finden und aufwecken.
2. **⚠️ Zwingende Quittungspflicht (`reply_to_sender`):** Wenn dieser Chat eine eingehende Nachricht mit `sender_chat_id` erhält, MUSST du nach Erledigung zwingend das Tool `reply_to_sender(sender_chat_id, status_message)` aufrufen, damit der Ursprungschat aufgeweckt wird.
3. **🛡️ Projekt-Schutz:** Bearbeite niemals fremden Code außerhalb deines Workspace. Delegiere Fremdaufgaben stets über `/communicate`.
---
```
