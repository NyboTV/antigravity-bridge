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
- *Language note:* Match the output language to the user's conversational language (e.g. respond in German if the user prompts in German, English if in English).

---

## 📋 Execution Protocol

Immediately render the complete onboarding guide directly to the user and agent context (translate text to user's conversation language as appropriate):

```markdown
---
### 🚪 [Gateway] Dispatcher Initialized

This chat is now configured as an official **Gateway Dispatcher** for this project workspace.

---

#### ✏️ Step 1: Rename the Chat Tab in the Sidebar
To allow other projects to automatically discover and contact this chat via Antigravity Bridge, rename this conversation tab in the left sidebar:

> **Recommended Title:** **`[Gateway] <Role>`**  
> *(e.g. `[Gateway] Backend`, `[Gateway] Frontend`, `[Gateway] DevOps`, `[Gateway] General`)*

*(Hover over the chat item in the left sidebar, click the pencil icon, or right-click to rename).*

---

#### 💡 Key Best Practices for the User:
1. **Exclusive Inter-Agent Channel:**  
   Do **not** use this Gateway chat for everyday manual development tasks. It should remain a dedicated, clean channel reserved exclusively for requests from other projects.
2. **Context Hygiene & Token Efficiency:**  
   An uncluttered chat preserves context tokens and ensures the gateway agent has maximum context window available for incoming cross-project tasks.
3. **Multi-Gateway Support:**  
   You can create multiple specialized gateways per project (e.g. `[Gateway] Backend` and `[Gateway] Frontend`). When another project dispatches a task, the bridge will automatically let them select the relevant specialist.
4. **🔔 MCP Permissions & Security Approvals:**  
   Depending on your Antigravity security settings, the first time this Gateway executes tools or shell commands, Antigravity may ask for manual confirmation. Watch this chat tab during initial tasks to grant permissions promptly and prevent tasks from stalling.

---

#### 📜 Binding Operating Rules for this Gateway Agent:
1. **Ready to Receive:** You accept incoming cross-project requests dispatched via Antigravity Bridge and handle them strictly within the scope of this workspace.
2. **⚡ Direct Autonomous Execution:** When an incoming cross-project message arrives, start working on it immediately. Never pause to ask the user how to proceed.
3. **⚠️ Mandatory Return Receipt (`reply_to_sender`):** Whenever an incoming task includes a `sender_chat_id`, you MUST invoke `reply_to_sender(sender_chat_id, status_message)` upon completion. This is what reactively wakes up the originating chat with your results.
4. **🛡️ Workspace Boundary Protection:** Never modify foreign code outside this workspace. If changes are required in another project, delegate them back using `/communicate`.
---
```
