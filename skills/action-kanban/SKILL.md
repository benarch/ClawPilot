---
name: "action-kanban"
description: "Scan Teams chats and Outlook inbox for action items pending on the user, then display a Kanban board grouped by customer/internal with priority, due date, and creation date. Triggers: 'action items', 'kanban', 'my tasks', 'what's pending', 'to-do board'."
---

---
name: "action-kanban"
description: "Scan Teams chats and Outlook inbox for action items pending on the user, then display a Kanban board grouped by customer/internal with priority, due date, and creation date. Triggers: 'action items', 'kanban', 'my tasks', 'what's pending', 'to-do board'."
---

## Action Item Kanban — Workflow

Scan the user's Teams chats and Outlook inbox (past 30 days), extract action items assigned to or pending on the user, classify by customer/internal, assign priority, and present as a Kanban board.

---

### Step 1 — Determine Date Range

- Calculate the start date: 30 days before today's date.
- Use this as the `startDate` for all queries in Steps 2 and 3.

---

### Step 2 — Scan Outlook Inbox (parallelize with Step 3)

**A) Flagged emails:**
- Use `m365_list_emails` with `limit: 50`, `startDate: [30 days ago]`.
- Look for emails that are flagged or have follow-up flags.
- For each flagged email, extract:
  - **Subject** as the action item title
  - **Sender name and email domain** (to classify customer vs. internal)
  - **Received date** as creation date
  - **Flag due date** if present → use as due date
  - **Preview/body snippet** for context

**B) Actionable emails (AI extraction):**
- Use `m365_search_emails` with queries targeting action language:
  - `query: "action required"`, `limit: 20`, `startDate: [30 days ago]`
  - `query: "please review"`, `limit: 20`, `startDate: [30 days ago]`
  - `query: "can you"`, `limit: 20`, `startDate: [30 days ago]`
  - `query: "need from you"`, `limit: 20`, `startDate: [30 days ago]`
  - `query: "follow up"`, `limit: 20`, `startDate: [30 days ago]`
  - `query: "waiting on you"`, `limit: 20`, `startDate: [30 days ago]`
- Deduplicate results by email ID.
- For each email, use `m365_get_email` (with `bodyContentType: "text"`) to read the body.
- Extract specific action items from the body — look for:
  - Direct requests to the user (by name or "you")
  - Bullet points or numbered lists with tasks
  - Sentences containing: "please", "can you", "need you to", "action required", "by [date]", "deadline"
- For each extracted action item, record:
  - **Title**: concise summary of the ask (max 10 words)
  - **Source**: `📧 Email` + subject line
  - **From**: sender name
  - **Customer/Internal**: check sender email domain — if `@microsoft.com` → Internal, otherwise → extract company name from domain
  - **Creation date**: email received date
  - **Due date**: extract from body if mentioned (look for date patterns), otherwise → null
  - **Context snippet**: 1-2 sentence excerpt showing the request

---

### Step 3 — Scan Teams Chats (parallelize with Step 2)

**A) Recent chats:**
- Use `m365_list_chats` with `limit: 50` to get recent chats.
- For each chat, use `m365_list_chat_messages` with `chatId` and `limit: 30`.
- Scan messages for action items directed at the user — look for:
  - @mentions of the user
  - Direct requests: "can you", "please", "need you to", "action item", "follow up"
  - Questions waiting for the user's response (unanswered questions in the last message)

**B) Targeted searches:**
- Use `m365_search_chats` with queries:
  - `query: "action item"`, `limit: 50`
  - `query: "follow up"`, `limit: 50`
  - `query: "can you"`, `limit: 50`
- For matching chats, read recent messages with `m365_list_chat_messages`.

**For each extracted action item, record:**
- **Title**: concise summary (max 10 words)
- **Source**: `💬 Teams` + chat topic or participant name
- **From**: message sender name
- **Customer/Internal**: check participant email domains — if all `@microsoft.com` → Internal, otherwise → extract company name
- **Creation date**: message timestamp
- **Due date**: extract from message if mentioned, otherwise → null
- **Context snippet**: the relevant message text (1-2 sentences)

---

### Step 4 — Classify & Deduplicate

**A) Group by Customer/Internal:**
- **Internal (Microsoft)**: all items where sender/participants are `@microsoft.com` only
- **Customer groups**: group by company name extracted from email domain. Map known domains:
  - `@checkpoint.com`, `@checkpoint.co.il` → Check Point
  - `@verint.com` → Verint
  - `@playtech.com` → Playtech
  - `@solaredge.com` → SolarEdge
  - Other external domains → use the domain name as the group label (capitalize, strip TLD)

**B) Deduplicate:**
- If the same action item appears in both email and Teams (same topic, same person) → merge into one entry, note both sources.
- Use title similarity and sender to detect duplicates.

**C) Assign Priority:**
Automatically assign priority based on these signals:

| Priority | Criteria |
|----------|----------|
| 🔴 **Urgent** | Contains words: "urgent", "ASAP", "critical", "blocker", "today", "immediately". OR due date is today or overdue. |
| 🟡 **This Week** | Due date is within the current week. OR contains: "this week", "soon", "by Friday". OR email is flagged with a near due date. |
| 🟢 **Later** | Has a due date beyond this week. OR general follow-up with no urgency signals. |
| ⚪ **No Deadline** | No due date mentioned and no urgency signals. |

**D) Sort within each priority:**
- 🔴 Urgent → sort by due date ascending (overdue first), then creation date ascending (oldest first)
- 🟡 This Week → sort by due date ascending
- 🟢 Later → sort by due date ascending
- ⚪ No Deadline → sort by creation date ascending (oldest first)

---

### Step 5 — Output Kanban Board

Present the Kanban board in chat using this format:

```markdown
## 📋 Action Item Kanban
**Scanned:** Past 30 days | **Sources:** Outlook + Teams | **Generated:** [today's date & time]
**Total items:** [count] | 🔴 [count] | 🟡 [count] | 🟢 [count] | ⚪ [count]

---

### 🏢 [Customer Name 1] ([count] items)

| # | Priority | Action Item | Source | From | Created | Due | Context |
|---|----------|-------------|--------|------|---------|-----|---------|
| 1 | 🔴 | [title] | 📧 [subject] | [name] | [date] | [date] | [snippet] |
| 2 | 🟡 | [title] | 💬 [chat] | [name] | [date] | [date] | [snippet] |
| 3 | ⚪ | [title] | 📧 [subject] | [name] | [date] | — | [snippet] |

---

### 🏢 [Customer Name 2] ([count] items)

| # | Priority | Action Item | Source | From | Created | Due | Context |
|---|----------|-------------|--------|------|---------|-----|---------|
| ... | ... | ... | ... | ... | ... | ... | ... |

---

### 🏠 Internal — Microsoft ([count] items)

| # | Priority | Action Item | Source | From | Created | Due | Context |
|---|----------|-------------|--------|------|---------|-----|---------|
| ... | ... | ... | ... | ... | ... | ... | ... |

---

### 📊 Summary
- **Most urgent:** [top 3 items that need immediate attention]
- **Overdue:** [count] items past their due date
- **Oldest open item:** [item title] from [date] — [days] days old
```

**Formatting rules:**
- Customer groups appear first, sorted by number of items (most items first)
- Internal group always appears last
- Within each group, items are sorted by priority (🔴 → 🟡 → 🟢 → ⚪), then by due date/creation date
- Dates formatted as `MMM DD` (e.g., `Apr 23`)
- Due column shows `—` if no deadline
- Overdue items get a suffix: `⚠️ OVERDUE`
- Context column is max 50 characters, truncated with `...`

---

### Step 6 — Post-Kanban Actions

After displaying the board, offer actions using `m_ask_user`:

1. **Focus on a customer** — "Show me more detail on a specific customer's items"
2. **Send digest** — "Email me this board as a daily digest"
3. **Mark items done** — "I've completed some items — update the board"
4. **Refresh** — "Re-scan with different time range"
5. **Done** — "That's all I need"

If the user selects:
- **Focus on a customer** → re-display just that customer's items with full email/message context (use `m365_get_email` to show full body)
- **Send digest** → format as HTML email and send to user's own email using `m365_send_email`
- **Mark items done** → ask which item numbers, acknowledge, and redisplay the updated board
- **Refresh** → ask for new date range, re-run from Step 1

---

## Execution Notes

- **Parallelize** Steps 2 and 3 (email scan and Teams scan are independent).
- Within Step 2, parallelize the multiple `m365_search_emails` queries.
- If any scan yields no action items, show "No action items found" for that source — don't omit the section.
- **Performance**: If Teams chat scan is slow (many chats), limit to the 30 most recent chats. Prioritize chats with external participants.
- **Deduplication is critical** — the same topic often appears in both email and Teams. Err on the side of merging similar items.
- Action item extraction requires AI judgment — look for imperative sentences, requests, and questions directed at the user. Ignore FYI-only messages, newsletters, and automated notifications.
- Skip system-generated messages (meeting invites, read receipts, auto-replies, bot messages).
- When extracting company names from email domains, handle common patterns: `company.com`, `company.co.il`, `company.co.uk` should all map to the same company name.
