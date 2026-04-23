---
name: "onenote-export"
description: "Export Microsoft OneNote notebooks to Obsidian-compatible markdown files with images, folder hierarchy, and YAML frontmatter. Triggers: 'onenote', 'export onenote', 'onenote to obsidian', 'onenote to markdown', 'export notebooks', 'onenote-export'."
---

---
name: "onenote-export"
description: "Export Microsoft OneNote notebooks to Obsidian-compatible markdown with images, folder hierarchy, and YAML frontmatter"
---

## OneNote → Obsidian Export Skill

Exports OneNote notebooks via Microsoft Graph API to a local folder structure compatible with Obsidian, including images, subpage hierarchy, and YAML frontmatter.

**Helper script:** `~/.copilot/m-skills/onenote-export/onenote_export.py`

---

### Step 1 — Authenticate via Graph Explorer

The user's org (Microsoft) blocks standard MSAL auth flows. Authentication works via **Graph Explorer browser session** instead.

**Check if cached token is still valid:**
```bash
python3 ~/.copilot/m-skills/onenote-export/onenote_export.py --list 2>&1 | head -5
```

If output contains `✅ Using cached Graph Explorer token` → skip to Step 2.

If output contains `TOKEN_NEEDED` or `⚠️ Cached token expired` → get a fresh token:

1. Navigate browser to `https://developer.microsoft.com/en-us/graph/graph-explorer`
2. If not signed in, click "Sign in" and let the user sign in via SSO popup
3. Once signed in (shows "[username] Sign out" button), install a fetch interceptor:
   ```javascript
   () => {
       const origFetch = window._origFetch || window.fetch;
       window._origFetch = origFetch;
       window._capturedToken = null;
       window.fetch = function(...args) {
           const url = typeof args[0] === 'string' ? args[0] : args[0]?.url;
           const init = args[1] || {};
           const headers = init.headers;
           if (url && url.includes('graph.microsoft.com') && headers) {
               let auth = null;
               if (headers instanceof Headers) { auth = headers.get('Authorization'); }
               else if (typeof headers === 'object') { auth = headers.Authorization || headers.authorization; }
               if (auth && auth.startsWith('Bearer ')) { window._capturedToken = auth.substring(7); }
           }
           return origFetch.apply(this, args);
       };
       return 'ready';
   }
   ```
4. Click "Run query" button in Graph Explorer to trigger a Graph API call
5. Extract the token: `() => window._capturedToken`
6. Save the token to `~/.copilot/m-skills/onenote-export/.ge_token` using bash with a heredoc:
   ```bash
   cat > ~/.copilot/m-skills/onenote-export/.ge_token << 'TOKENEOF'
   <paste token here>
   TOKENEOF
   chmod 600 ~/.copilot/m-skills/onenote-export/.ge_token
   ```
7. The token is valid for ~75 minutes. For long exports, check token validity midway.

---

### Step 2 — List Notebooks

```bash
python3 ~/.copilot/m-skills/onenote-export/onenote_export.py --list
```

Parse the JSON between `NOTEBOOKS_JSON_START` and `NOTEBOOKS_JSON_END`.

Display as a numbered table:
```
📚 **Your OneNote Notebooks:**

| # | Notebook | Created | Modified |
|---|----------|---------|----------|
| 1 | ... | ... | ... |
```

---

### Step 3 — Select Notebooks

Ask the user which notebooks to export using `m_ask_user`:
- **"Export all"** — export every notebook
- **"Let me pick"** — user types notebook numbers (e.g., "1, 3, 5")

---

### Step 4 — Run Export

```bash
# Export specific notebooks:
python3 ~/.copilot/m-skills/onenote-export/onenote_export.py --notebooks "2,3" --output "/Users/[username]/OneDrive - Microsoft/[username]-dev_space/onenote-2-obsidian/onenote-export"

# Export all:
python3 ~/.copilot/m-skills/onenote-export/onenote_export.py --all --output "/Users/[username]/OneDrive - Microsoft/[username]-dev_space/onenote-2-obsidian/onenote-export"
```

Run in **sync mode with initial_wait of 10**. Export can take several minutes for large notebooks.

While waiting, inform the user:
```
⏳ **Export in progress...**
This may take a few minutes depending on notebook size and image count.
```

---

### Step 5 — Present Results

Extract results JSON between `RESULTS_JSON_START` and `RESULTS_JSON_END`.

Present summary:
```
✅ **OneNote Export Complete!**

📁 **Output:** `/Users/[username]/OneDrive - Microsoft/[username]-dev_space/onenote-2-obsidian/onenote-export`

| Notebook | Pages | Images |
|----------|-------|--------|
| ... | ... | ... |

Open this folder in Obsidian to browse your notes!
```

---

### Step 6 — Verify

```bash
find "/Users/[username]/OneDrive - Microsoft/[username]-dev_space/onenote-2-obsidian/onenote-export" -name "*.md" | wc -l
```

---

## Output Structure

```
onenote-export/
└── [Notebook Name]/
    └── [Section Name]/
        ├── assets/                     ← downloaded images
        ├── 01-Simple Page.md           ← leaf page
        ├── 02-Page With Subs/          ← folder for pages with children
        │   ├── Page With Subs.md       ← parent content
        │   ├── 02.01-Subpage A.md
        │   └── 02.02-Subpage B.md
        └── 03-Another Page.md
```

Each .md includes YAML frontmatter: title, notebook, section, created/modified dates, onenote_url.

## Execution Notes

- **Token lifetime:** ~75 minutes. For exports with many notebooks, check if token is still valid midway.
- **Rate limiting:** Auto-handled with retry on 429.
- **Section groups:** Fully supported, map to nested folders.
- **Checkboxes:** OneNote to-do tags → Obsidian `- [ ]` / `- [x]`.
- **Images:** Downloaded to `assets/` per section with Obsidian-compatible `![]()` links.
- **Re-running:** Safe to re-run — overwrites cleanly.
- **Token refresh:** If export fails mid-way with auth error, re-do Step 1 to get a fresh token, then re-run.

## Guardrails

- Create folders with `mkdir -p` before writing.
- If any step yields no results, note "No data found" rather than omitting.
- Never expose the access token in user-visible output.

