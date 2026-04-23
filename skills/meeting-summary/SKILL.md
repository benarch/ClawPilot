---
name: "meeting-summary"
description: "Summarize a completed meeting using Teams transcripts, recordings, chat messages, and related context. Extracts key discussion points, decisions, action items, and compares against meeting-prep if available. Outputs in-chat summary and saves MD file to OneDrive."
---

### Step 1 — Meeting Selection

- If the user specifies a meeting by name, time, or description → use `m365_list_events` to find it.
- If no meeting specified → list today's past meetings (already ended) as a numbered list using `m_ask_user`. Let the user pick by number.
- If no meetings ended today, expand to the past 3 calendar days.
- Once selected, use `m365_get_event` to retrieve full details (body, attendees, organizer, etc.).

### Step 2 — Classify Meeting Type

- Check all attendee email domains.
- If **ALL** attendees are `@microsoft.com` → **Internal meeting** (lighter summary: skip company context).
- If **any** attendee has a non-Microsoft domain → **Customer meeting** (full summary).
- Identify the **customer company name** from external attendee email domains.

### Step 3 — Retrieve Transcript & Recording

Attempt transcript retrieval in this priority order:

**Method A — OneDrive Recordings folder:**
- Use `m365_search_files` with the meeting subject and/or date to find transcript files (`.vtt`, `.docx`) and recordings (`.mp4`) in OneDrive.
- Search patterns: `"[meeting subject] transcript"`, `"[meeting subject] recording"`.
- If found, use `m365_download_file` to download the transcript content.

**Method B — Meeting Chat Messages:**
- Use `m365_search_chats` with the meeting subject to find the meeting chat.
- Use `m365_list_chat_messages` on the meeting chat to look for:
  - Transcript links or attachments
  - Recording links
  - Bot-generated summary messages (e.g., Copilot recap, Intelligent Recap)
  - Any shared files during the meeting

**Method C — WorkIQ:**
- Use WorkIQ: `/Users/[username]/.copilot/bin/workiq ask -q "Get the transcript or summary for the meeting '[meeting subject]' on [date]"`.

**Method D — Browser Automation (fallback):**
- If Methods A-C fail, use Playwright browser to:
  1. Navigate to the Teams meeting recap page via the meeting's online meeting URL
  2. Extract transcript content from the recap view
  3. Or navigate to `https://teams.microsoft.com` → Calendar → find the meeting → open recap/transcript tab

**If no transcript is available at all:**
- Inform the user that no transcript was found.
- Fall back to summarizing based on: meeting chat messages, email threads before/after the meeting, and the meeting-prep file if it exists.
- Clearly note in the output: "⚠️ Summary based on chat messages and email context — no transcript available."

### Step 4 — Parse Transcript

If a VTT transcript is retrieved:
- Parse speaker names and their statements.
- Group by speaker turns.
- Identify timestamps for key moments.

If transcript is in another format (DOCX, text, HTML):
- Extract the text content and speaker attributions.

### Step 5 — Retrieve Meeting Chat Messages

- Use `m365_search_chats` to find the meeting chat thread.
- Use `m365_list_chat_messages` to get all messages from the meeting chat.
- Extract:
  - Shared links and files during the meeting
  - Questions asked in chat
  - Follow-up notes posted after the meeting

### Step 6 — Cross-Reference with Meeting-Prep

- Check if a meeting-prep file exists at:
  ```
  /Users/[username]/OneDrive - Microsoft/ClawPilot/meeting-preps/[customer-company-name]/
  ```
- Search for the most recent prep file matching the meeting subject.
- If found, read it and compare:
  - Which suggested agenda items were actually covered?
  - Which were missed/skipped?
  - Were the suggested talking points addressed?
  - Were open action items from the prep discussed?
  - Any new topics that weren't in the prep?

### Step 7 — Extract Key Information from Transcript

Analyze the transcript (and chat messages) to extract:

**Discussion Points:**
- Identify the main topics discussed, with brief summaries for each.
- Note who raised each topic.

**Decisions Made:**
- Any explicit decisions or agreements reached.
- Who made or endorsed the decision.

**Action Items:**
- Extract every action item, commitment, or follow-up mentioned.
- For each: what needs to be done, who is responsible, and any deadline mentioned.
- Distinguish between items assigned to internal team vs. external (customer) attendees.

**Open Questions / Unresolved Topics:**
- Topics that were raised but not resolved.
- Questions that need follow-up.
- Parking lot items.

**Key Quotes:**
- Notable statements or commitments worth preserving verbatim (2-3 max).

### Step 8 — Generate Executive Summary

Write a 3-5 sentence executive summary capturing:
- The main purpose of the meeting
- The most important outcome(s)
- Critical next steps

### Step 9 — Generate Follow-up Recommendations

Based on all context, suggest:
- Immediate follow-up actions (within 24-48 hours)
- Emails or messages to send
- Meetings to schedule
- Documents to share or update
- Items to escalate

### Step 10 — Output

#### A) In-Chat Summary

Present the following structured summary in chat:

```markdown
## 📝 Meeting Summary: [Meeting Subject]
**Date/Time:** [date & time in Asia/Jerusalem]  |  **Duration:** [X min]  |  **Type:** [Customer/Internal]
**Organizer:** [name]  |  **Transcript:** [Available/Not Available]

---

### 📌 Executive Summary
> [3-5 sentence summary of the meeting]

---

### 👥 Attendees
| # | Name | Company | Role | Attended |
|---|------|---------|------|----------|
| 1 | ...  | ...     | ...  | ✅/❌    |

---

### 💬 Key Discussion Points
1. **[Topic]** — [summary of discussion, who raised it]
2. **[Topic]** — [summary]
...

---

### ✅ Decisions Made
1. **[Decision]** — decided by [who], endorsed by [who]
2. ...

---

### 📋 Action Items
**Internal (Microsoft):**
- [ ] [action item] — **Owner:** [name] — **Deadline:** [if mentioned]
- [ ] ...

**External ([Company]):**
- [ ] [action item] — **Owner:** [name] — **Deadline:** [if mentioned]
- [ ] ...

---

### ❓ Open Questions / Unresolved Topics
- [question or unresolved topic] — raised by [who]
- ...

---

### 💬 Key Quotes
> "[notable quote]" — [speaker name]

---

### 🔄 Meeting-Prep Comparison *(if prep file exists)*

**Agenda Coverage:**
| Suggested Agenda Item | Covered? | Notes |
|----------------------|----------|-------|
| [item from prep]     | ✅/❌    | ...   |

**Talking Points Addressed:**
- ✅ [addressed point]
- ❌ [missed point]

**Prep Action Items Status:**
- ✅ [discussed in meeting]
- ❌ [not discussed — needs follow-up]

**New Topics (not in prep):**
- [topic that emerged during the meeting]

---

### 🚀 Follow-up Recommendations
1. **[action]** — send to [who] — by [when]
2. **[action]** — schedule meeting with [who]
3. ...

---

### 📎 Shared During Meeting
- [file/link shared in meeting chat]
- ...
```

#### B) Save MD File

Save the same content as a markdown file to:

```
/Users/[username]/OneDrive - Microsoft/ClawPilot/meeting-summaries/[Customer-Company-Name]/[Customer-Company-Name]-[meeting-subject]-YYYY-MM-DD-HHMM.md
```

Rules:
- Create the customer company folder if it doesn't exist (`mkdir -p`).
- For **internal meetings**, use folder name `microsoft-internal`.
- **Sanitize** file and folder names: replace spaces with hyphens, remove special characters, use lowercase.
- Example: `stark-industries/stark-jericho-project-bi-weekly-2026-04-27-0900.md`
- Confirm the file was saved and show the full path.

#### C) Offer Distribution

After presenting the summary, ask the user:
```
Would you like me to:
1. Send this summary via email to all attendees
2. Post it in the meeting Teams chat
3. Send to specific people
4. No distribution needed
```

Use `m_ask_user` for the choice. If the user selects distribution:
- For email: use `m365_send_email` with the summary formatted in HTML.
- For Teams chat: use `m365_send_chat_message` to the meeting chat.
- Always show the user the exact content before sending and wait for confirmation.

---

## Execution Notes

- **Parallelize** independent lookups (transcript search, chat messages, prep file lookup) to minimize time.
- If the transcript is very long (>10,000 words), focus on summarizing key segments rather than processing every line.
- If no transcript is found, clearly note this and rely on chat messages + email context. Still produce a useful summary.
- For **internal meetings**: skip company-specific context. Use a simpler attendee table. Still extract action items and decisions.
- When cross-referencing with meeting-prep, look for the prep file that most closely matches the meeting subject, date, and company.
- Parse VTT format: extract speaker names from lines preceding dialogue, group consecutive statements by the same speaker.
- If the meeting had Copilot/Intelligent Recap, look for the recap in the meeting chat messages — it often contains structured notes.
