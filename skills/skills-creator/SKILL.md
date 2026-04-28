---
name: "skill-creator"
description: "Create new Clawpilot skills through a hybrid intake process. User describes what they want, AI fills gaps with 2-3 targeted follow-ups, then generates a complete, production-quality skill with numbered steps, tool-specific instructions, and guardrails. Supports iteration and refinement after generation."
---

## Skill Creator — Hybrid Intake Workflow

You are creating a new Clawpilot skill. Follow this process exactly.

---

### Step 1 — Intake

The user has provided a description of the skill they want. Extract the following from their description (do NOT ask if already clear):

| Field | What to extract |
|-------|----------------|
| **Goal** | What does this skill accomplish? |
| **Trigger** | When/how will the user invoke it? |
| **Inputs** | What data does the skill need from the user? |
| **Outputs** | What does the skill produce? (in-chat summary, file, email, browser action, etc.) |
| **Data sources** | Where does the skill get its data? (M365 APIs, browser/web, local files, external APIs) |
| **Skill type** | Auto-detect: `api` (m365_*/WorkIQ calls), `browser` (Playwright automation), `hybrid` (API discovery + browser actions), `document` (generates files), `research` (web_fetch + analysis) |

---

### Step 2 — Targeted Follow-ups (max 2-3 questions)

Only ask questions about **gaps you cannot reasonably fill with defaults**. Use `m_ask_user` with structured answer choices when possible.

**Common gaps to check:**
- If outputs include saving files → ask for destination folder (suggest: `/Users/bendali/OneDrive - Microsoft/ClawPilot/[skill-name]/`)
- If the skill involves a specific website → ask for the exact URL and key navigation paths
- If the skill involves specific accounts/filters → ask for the default list (mention user's known accounts: Stark Industries, Wonka, Umbrella Corp if relevant)
- If the skill has conditional branches → confirm which branches matter

**Do NOT ask about:**
- Error handling (add sensible defaults automatically)
- Tool selection (auto-select based on skill type)
- Output formatting (match existing skill patterns)
- Parallelization strategy (add automatically where applicable)

---

### Step 3 — Generate Skill Instructions

Write the SKILL.md content following these **mandatory patterns** (learned from user's existing skills):

#### A) Frontmatter
```yaml
---
name: "[skill-name]"
description: "[one-line description — precise, includes key verbs and nouns for trigger matching]"
---
```

#### B) Step Structure
- Use `### Step N — [Descriptive Title]` for each step
- Number steps sequentially
- Each step has bullet points with specific tool calls and parameters
- Use conditional logic with arrows: `If X → do Y. Otherwise → do Z.`
- Reference exact tool names: `m365_list_events`, `m365_search_emails`, `m365_search_files`, `m365_download_file`, `web_fetch`, `m365_search_people`, `m365_send_email`, `m365_send_chat_message`, `m_ask_user`, `playwright-browser_navigate`, `playwright-browser_snapshot`, `playwright-browser_click`, `playwright-browser_evaluate`, WorkIQ (`/Users/bendali/.copilot/bin/workiq ask -q "..."`)
- For browser automation steps: always include wait times, snapshot checks, and "Unsaved changes" dialog handling
- For API steps: include the exact query patterns (search terms, date ranges, filters)

#### C) Tool Selection by Skill Type

| Skill Type | Primary Tools |
|-----------|---------------|
| `api` | `m365_*` tools, WorkIQ, `m_ask_user` |
| `browser` | `playwright-browser_*`, `playwright-browser_evaluate` for JS execution |
| `hybrid` | API for discovery/data, browser for UI actions |
| `document` | `bash` (mkdir -p, file writes), `m365_upload_file`, template literals |
| `research` | `web_fetch`, `m365_search_*`, WorkIQ |

#### D) Output Section
Every skill MUST have an output step that defines:
1. **In-chat format** — use a markdown template with emoji section headers, tables, and checklists (match the style of existing skills like meeting-prep)
2. **File output** (if applicable) — exact path pattern, folder creation with `mkdir -p`, filename sanitization rules (lowercase, hyphens, no special chars)
3. **Distribution** (if applicable) — offer to send via email or Teams using `m_ask_user`

#### E) Execution Notes
End with a `## Execution Notes` section containing:
- Parallelization hints (which steps can run simultaneously)
- Fallback strategies (what to do if a data source is empty)
- Performance tips (skip X if time is short, batch queries, etc.)
- Any platform-specific quirks (MSX load times, browser session issues, etc.)

#### F) Guardrails to Auto-Include

**For browser automation skills:**
```
- MSX/Dynamics 365 pages load slowly — always wait for elements to appear before interacting.
- After every navigation or click, wait at least 3-5 seconds, then take a snapshot.
- If "Unsaved changes" dialog appears → click "Discard changes".
- If Edge browser won't open → kill stale processes: `ps aux | grep "mcp-msedge" | grep -v grep | awk '{print $2}'` then kill each PID.
```

**For API skills:**
```
- If any step yields no results, note "No data found" in that section rather than omitting it.
- Parallelize independent lookups to minimize total time.
```

**For file-saving skills:**
```
- Create destination folders with `mkdir -p` before writing.
- Sanitize filenames: lowercase, replace spaces with hyphens, remove special characters.
- Confirm the file was saved and show the full path.
```

---

### Step 4 — Create the Skill

Use `m_create_skill` with:
- **name**: kebab-case, concise (e.g., `deal-scanner`, `weekly-report`)
- **description**: the one-liner from the frontmatter (must be rich enough for trigger matching — include key action verbs and nouns)
- **instructions**: the full SKILL.md content generated in Step 3

After creation, confirm:
- ✅ Skill name and invocation command (`/skill-name`)
- 📁 Skill location (`~/.copilot/m-skills/[skill-name]/`)
- 📝 Brief summary of what it does (3-4 bullet points)

---

### Step 5 — Refine Loop

After presenting the created skill, ask:

```
Want to refine anything?
- "Make step X more detailed"
- "Add error handling for Y"
- "Change the output format"
- "Add a new step for Z"
- Or say "looks good" to finish
```

Use `m_ask_user` with choices:
1. **Refine a step** — "I want to adjust specific steps"
2. **Add something** — "Add a new capability or step"
3. **Looks good** — "Ship it as-is"

If the user wants changes:
- Use `m_get_skill` to read current instructions
- Use `m_update_skill` to apply changes
- Show what changed
- Return to this step

---

## Quality Checklist (internal — verify before creating)

Before calling `m_create_skill`, verify the generated instructions against this checklist:

- [ ] Every step has a clear, numbered heading
- [ ] Every tool call uses the exact tool name (not generic descriptions)
- [ ] Conditional logic uses → arrows for clarity
- [ ] Output section includes a markdown template
- [ ] File paths use the user's actual OneDrive path: `/Users/bendali/OneDrive - Microsoft/ClawPilot/`
- [ ] Execution notes cover parallelization and fallbacks
- [ ] Browser steps include wait times and snapshot checks
- [ ] The description is specific enough to trigger on relevant user requests
- [ ] No unnecessary complexity — each step earns its place
