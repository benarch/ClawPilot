# Skill Draft: meeting-prep

**Name:** meeting-prep  
**Description:** Prepare for a specific meeting by gathering attendee intelligence, recent communications, company research, MSX opportunity data, action items, and suggested agenda. Outputs a structured in-chat summary and saves an MD file to OneDrive.

---

## Instructions

### Step 1 — Meeting Selection

- If the user provides a meeting name, time, or description → use `m365_list_events` to find the matching meeting.
- If no meeting specified → list today's remaining meetings as a numbered list using `m_ask_user`. Let the user pick by number.
- If no meetings remain today, expand to the next 3 calendar days.
- Once a meeting is selected, use `m365_get_event` to retrieve full details including the invite body/agenda.

### Step 2 — Classify Meeting Type

- Check all attendee email domains.
- If **ALL** attendees are `@microsoft.com` → **Internal meeting** (lighter prep: skip Steps 6 and 7).
- If **any** attendee has a non-Microsoft domain → **Customer meeting** (full prep).
- Identify the **customer company name** from the external attendee email domains (e.g., `@checkpoint.com` → "Check Point").
- If multiple external companies are present, use the most prominent one (most attendees) as the primary company name.

### Step 3 — Attendee Intelligence

For each attendee (parallelize lookups where possible):

- Use `m365_search_people` to retrieve: display name, job title, department, office location, email.
- Use WorkIQ (`workiq ask -q "Who is [attendee name]? What is their role and org chart position?"`) for deeper context.
- For customer meetings: note the attendee's seniority level and likely decision-making authority.
- Organize attendees into **Internal** and **External** groups.

### Step 4 — Recent Communications (30-day lookback)

All searches cover the past 30 days from today's date.

**Emails:**
- Use `m365_search_emails` with each external attendee's name and/or email address.
- Summarize key topics, decisions, and any unresolved threads.
- Note the most recent email date and subject for each thread.

**Teams Chats:**
- Use `m365_search_chats` with attendee names and the company name.
- Summarize recent exchanges, focusing on action items and decisions.

**Past Meetings:**
- Use `m365_list_events` for the past 30 days.
- Filter for meetings that share attendees with the current meeting.
- List previous meeting subjects, dates, and any patterns (e.g., recurring syncs).

### Step 5 — Related Documents

- Use `m365_search_files` with queries for:
  - The meeting subject
  - The customer company name
  - Key attendee names
- Surface the **top 3-5 most relevant** documents with their OneDrive/SharePoint links.
- Briefly describe each document's relevance.

### Step 6 — Company Research *(Customer meetings only — skip for internal)*

**News:**
- Use `web_fetch` to search for recent news about the company (past 7 days).
- Search query: `"[Company Name] news"` via a news aggregator or search engine.
- Summarize the top 3-5 most relevant news items with links.

**Social Media:**
- Use `web_fetch` to check the company's recent social media activity (LinkedIn, Twitter/X).
- Summarize notable recent posts or announcements.

**Company Website:**
- Use `web_fetch` to visit the company's main website (e.g., `https://www.[company].com`).
- Check for recent press releases, blog posts, or product announcements.
- Highlight anything updated recently that could be relevant to the meeting.

### Step 7 — MSX Opportunity Data *(Customer meetings only — skip for internal)*

- Use WorkIQ: `workiq ask -q "Open opportunities for [customer company name] where I am on the deal team"`.
- Surface:
  - Opportunity names
  - Deal stages
  - Pipeline values
  - Recent milestone activity
- Also note any opportunities where the user is **not** on the deal team but should be aware of.

### Step 8 — Action Items & Follow-ups

- From email threads (Step 4): extract any open commitments, promised deliverables, or pending responses.
- From Teams chats (Step 4): extract any action items assigned to or by the user.
- From past meetings (Step 4): identify any recurring agenda items or outstanding follow-ups.
- Present as a checklist of open items.

### Step 9 — Generate Suggested Talking Points

Based on ALL gathered context, auto-generate 5-8 suggested talking points. Consider:
- Unresolved topics from recent emails/chats
- Open action items that need status updates
- Recent company news or announcements that are conversation-worthy
- MSX opportunity movements or milestone updates
- Any gaps or risks identified in the communications

### Step 10 — Generate Suggested Meeting Agenda

Based on the context, propose a structured agenda:
1. **Opening** — brief rapport/context setter (reference recent company news if relevant)
2. **Follow-ups** — status on open action items from last interactions
3. **Recent discussions** — continue or close out recent email/chat threads
4. **New business** — topics surfaced from company research, MSX changes, or document findings
5. **Next steps** — align on action items and owners

If the meeting invite already contains an agenda (from Step 1), present it alongside the suggested agenda and note any gaps.

### Step 11 — Output

#### A) In-Chat Summary

Present the following structured summary in chat:

```markdown
## 📅 Meeting Prep: [Meeting Subject]
**Date/Time:** [date & time in Asia/Jerusalem]  |  **Duration:** [X min]  |  **Type:** [Customer/Internal]
**Location/Link:** [Teams link or room]
**Organizer:** [name]

---

### 📋 Meeting Invite Agenda
> [Include the meeting body/agenda from the invite, or "No agenda provided in the invite."]

---

### 👥 Attendees

**External:**
| # | Name | Title | Company | Relevance |
|---|------|-------|---------|-----------|
| 1 | ...  | ...   | ...     | ...       |

**Internal (Microsoft):**
| # | Name | Title | Department |
|---|------|-------|------------|
| 1 | ...  | ...   | ...        |

---

### 🏢 Company Intelligence *(customer meetings only)*

#### 📰 Recent News (past 7 days)
- [headline](link) — brief summary
- ...

#### 📱 Social Media Activity
- [platform]: [summary of recent posts]

#### 🌐 Website Updates
- [summary of recent website changes/announcements]

---

### 📧 Recent Communications (past 30 days)

#### Email Threads
- **[Subject]** (last: [date]) — [summary]
- ...

#### Teams Conversations
- **[Chat/Channel]** — [summary of recent exchanges]

#### Past Meetings with Same Attendees
| # | Date | Subject | Attendees Overlap |
|---|------|---------|-------------------|
| 1 | ...  | ...     | ...               |

---

### ✅ Open Action Items & Follow-ups
- [ ] [action item] — source: [email/chat/meeting] — owner: [name]
- [ ] ...

---

### 📄 Related Documents
| # | Document | Location | Relevance |
|---|----------|----------|-----------|
| 1 | [name](link) | OneDrive/SharePoint | [brief description] |

---

### 💼 MSX Opportunities *(customer meetings only)*
| Opportunity | Stage | Pipeline Value | On Deal Team? |
|-------------|-------|----------------|---------------|
| ...         | ...   | ...            | Yes/No        |

---

### 🎯 Suggested Talking Points
1. [talking point based on gathered context]
2. ...

---

### 📝 Suggested Meeting Agenda
1. **Opening** — [context setter]
2. **Follow-ups** — [open items to review]
3. **Recent Discussions** — [threads to continue/close]
4. **New Business** — [new topics from research]
5. **Next Steps** — [align on actions and owners]

*Existing invite agenda gaps:* [note any topics missing from the original invite agenda]
```

#### B) Save MD File

Save the same content as a markdown file to:

```
/Users/bendali/OneDrive - Microsoft/ClawPilot/meeting-preps/[Customer-Company-Name]/[Customer-Company-Name]-[meeting-subject]-YYYY-MM-DD-HHMM.md
```

Rules:
- Create the customer company folder if it doesn't exist (`mkdir -p`).
- For **internal meetings**, use folder name `Microsoft-Internal`.
- **Sanitize** file and folder names: replace spaces with hyphens, remove special characters, use lowercase.
- Example: `check-point/check-point-quarterly-business-review-2026-04-23-1500.md`
- Confirm the file was saved and show the full path.

---

## Execution Notes

- **Parallelize** independent lookups (attendee search, email search, file search) to minimize total time.
- Use `web_fetch` for company research — search Google News, LinkedIn, and the company website.
- If any step yields no results, note "No data found" in that section rather than omitting it.
- If the meeting is less than 15 minutes away, prioritize speed — skip document search and social media, focus on attendees + communications + action items.
- Always show the in-chat summary first, then save the file.
- For **internal meetings**: skip Steps 6 (Company Research) and 7 (MSX). Use a simpler attendee table. Still generate talking points and suggested agenda from communications and action items.
