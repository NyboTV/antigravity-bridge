---
name: communicate
description: Inter-Agent & Cross-Project Communication via antigravity-bridge MCP. Triggered by the /communicate slash command or when the user wants to dispatch tasks, send messages to other project chats, query other projects, or append notes to an inbox.
---

# 🛰️ Inter-Project Communication Protocol (`/communicate`)

Dieses Skill steuert die agenten- und projektübergreifende Kommunikation zwischen verschiedenen Arbeitsbereichen über den **`antigravity-bridge`** MCP-Server.

---

## 🎯 Wann dieses Skill verwendet wird
- Der Nutzer ruft explizit den Slash-Command **`/communicate`** auf.
- Der Nutzer sagt Formulierungen wie:
  - *„Sag Projekt X Bescheid, dass...“*
  - *„Informiere Chat Y über...“*
  - *„Gib dem Backend-Projekt die neue API durch“*
  - *„Erstelle ein Ticket / eine Notiz in der Inbox von Projekt Z“*
  - *„Antworte dem Absender-Chat mit einer Quittung“*

---

## 🛠️ Verfügbare MCP-Tools (`antigravity-bridge`)

Der MCP-Server `antigravity-bridge` stellt folgende Werkzeuge bereit:

| Tool | Zweck |
|---|---|
| `list_projects` | Listet alle registrierten Projekte samt Pfaden, Chat-Statistiken und Inbox-Status auf. |
| `list_project_chats` | Listet alle aktiven Chats eines Projekts aus der SQLite-DB auf (inkl. `[Gateway]` Kennzeichnung). |
| `send_message_to_chat` | Sendet eine Nachricht direkt in einen Ziel-Chat und weckt diesen live auf (`agentapi send-message`). |
| `reply_to_sender` | Sendet eine Quittung / Statusbericht an die `sender_chat_id` eines Auftraggebers zurück. |
| `send_inbox_note` | Hängt eine strukturierte Aufgabe append-only in `.agents/INBOX.md` des Zielprojekts an. |
| `archive_inbox_note` | Verschiebt einen bearbeiteten Inbox-Eintrag nach `.agents/INBOX_ARCHIVE.md`. |

---

## 📋 Standard-Ablauf bei `/communicate`

### Schritt 1: Zielprojekt bestimmen
- Hat der Nutzer das Zielprojekt bereits genannt (z. B. `/communicate ServerZentrum ...`), übernimm dieses direkt.
- Ist das Zielprojekt unklar, rufe `list_projects` auf und zeige dem Nutzer die verfügbaren Projekte zur Auswahl.

### Schritt 2: Kommunikationsmodus wählen (Live-Wakeup vs. Asynchrone Notiz)
1. **Live-Aufgabe / Sofort-Wakeup (Echtzeit):**
   - Rufe `list_project_chats(project_name=...)` auf.
   - Falls ein Chat mit Präfix `[Gateway]` existiert (z. B. `[Gateway] Dispatcher`), wähle bevorzugt diesen oder präsentiere dem Nutzer die Chats als durchnummerierte Auswahlliste.
   - Sende die Nachricht mit `send_message_to_chat(conversation_id=..., message=..., priority=...)`.
   - Gib dem Nutzer eine Bestätigung mit Ziel-Chat und Status aus.

2. **Asynchrone Notiz / Aufgabe für später (Inbox):**
   - Wenn der Nutzer eine Notiz hinterlegen möchte oder der Ziel-Chat erst beim nächsten Prompt des Nutzers reagieren soll:
   - Rufe `send_inbox_note(target_project=..., sender_project=..., message=..., priority=..., subject=...)` auf.
   - Der Eintrag wird append-only in `.agents/INBOX.md` des Zielprojekts geschrieben.

3. **Rückmeldung an Absender (`reply_to_sender`):**
   - Wurde dieser Chat zuvor von einem anderen Agenten beauftragt (enthält eine `sender_chat_id`), nutze `reply_to_sender`, um das Ergebnis zurückzumelden.

---

## 🛑 Eiserne Sicherheitsregel
- **Niemals fremden Code selbst editieren:** Wenn du in einem Projekt arbeitest und Änderungen in einem anderen Projekt erforderlich sind, ändere diese NIEMALS direkt im fremden Workspace ab. Verwende IMMER `/communicate` bzw. die `antigravity-bridge` MCP-Tools zur Delegation!
