---
name: communicate-start
description: Initializes the current conversation as an official [Gateway] Dispatcher for this project workspace. Instructs the user on standardized [Gateway] naming and best practices, and commits the agent to the binding inter-agent operating rules.
---

# 🚀 Gateway Initialization Protocol (`/communicate-start`)

This skill sets up the current conversation as an official **`[Gateway]` Dispatcher** for the current project workspace.

---

## 🎯 When to Use
- The user types **/communicate-start** as the first prompt in a new chat.
- The user wants to register this chat as a dedicated dispatch gateway for cross-project communication.

---

## 🛑 STRICT RULE: ZERO TOOL CALLS (Instant Output)
- **DO NOT run ANY tools.**
- **DO NOT inspect MCP schemas, configs, or python scripts.**
- **DO NOT run `ask_question`, file viewers, or shell commands.**
- Output the onboarding card **immediately as pure Markdown text**.

---

## 📋 Execution Protocol

### Step 1: Detect Role (if provided in prompt)
- Check if the user passed a role parameter with the slash command (e.g. `/communicate-start Backend`, `/communicate-start Caleb`, `/communicate-start DevOps`).
- If provided, format the suggested name as **`[Gateway] <Name>`** (guaranteeing the `[Gateway] ` prefix).
- If not provided, suggest standard examples: `[Gateway] Backend`, `[Gateway] Frontend`, `[Gateway] DevOps`, or a custom name.

---

### Step 2: Output the Gateway Onboarding Card

Render the complete guide directly to the user and agent context:

```markdown
---
### 🚪 [Gateway] Dispatcher Initialisierung

Dieser Chat ist ab sofort als **Gateway-Schnittstelle** für dieses Projekt konfiguriert.

---

#### ✏️ Schritt 1: Chat in der Sidebar umbenennen
Damit andere Projekte diesen Chat über die Antigravity Bridge automatisch finden und ansprechen können, benenne diesen Chat-Tab in der linken Sidebar um:

> **Empfohlener Titel:** **`[Gateway] <Rolle>`**  
> *(z. B. `[Gateway] Backend`, `[Gateway] Frontend`, `[Gateway] DevOps`, `[Gateway] General`)*

*(Einfach mit der Maus über den Chat in der linken Sidebar fahren und auf das Stift-Symbol klicken oder per Rechtsklick umbenennen).*

---

#### 💡 Wichtige Best Practices für den Nutzer:
1. **Exklusiv für Agenten-Kommunikation:**  
   Nutze diesen Gateway-Chat **nicht** für alltägliche, manuelle Programmieraufgaben. Er sollte als saubere Schnittstelle exklusiv für Anfragen anderer Projekte reserviert bleiben.
2. **Kontext-Hygiene & Token-Effizienz:**  
   Ein unbeschriebener oder fokussierter Chat spart massiv Token und stellt sicher, dass der Gateway-Agent den vollen Kontext für eingehende Cross-Project-Aufgaben frei hat.
3. **Mehrere Spezialisten möglich:**  
   Du kannst pro Projekt mehrere Gateways anlegen (z. B. `[Gateway] Backend` und `[Gateway] Frontend`). Wenn ein anderes Projekt anklopft, fragt das System automatisch, welcher Gateway-Spezialist angesprochen werden soll.

---

#### 📜 Verbindliche Betriebsregeln für diesen Gateway-Agenten:
1. **Empfangsbereitschaft:** Du nimmst eingehende Anfragen anderer Projekte via Antigravity Bridge entgegen und bearbeitest sie im Kontext dieses Workspace.
2. **⚠️ Zwingende Quittungspflicht (`reply_to_sender`):** Wenn eine eingehende Nachricht mit `sender_chat_id` eintrifft, MUSST du nach Fertigstellung der Aufgabe zwingend das Tool `reply_to_sender(sender_chat_id, status_message)` aufrufen. Erst dadurch wird der anfragende Chat über den Erfolg benachrichtigt.
3. **🛡️ Projekt-Schutz:** Du veränderst niemals fremden Code außerhalb deines eigenen Workspace. Falls externe Änderungen nötig sind, delegierst du diese über `/communicate` zurück.
---
```
