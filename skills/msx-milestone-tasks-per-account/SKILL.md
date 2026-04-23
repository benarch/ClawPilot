---
name: "msx-milestone-tasks-per-account"
description: "Create POC task activities on MSX milestones for deal team opportunities filtered by account. Uses Dynamics 365 Web API for fast discovery, presents numbered milestones for approval, then creates 3 tasks per milestone via browser automation."
---

## MSX Milestone Tasks Per Account

### PURPOSE
Scan the user's MSX Deal Team opportunities filtered by specific accounts, discover all milestones via Dynamics 365 Web API, present a numbered approval table, then create 3 POC task activities on each approved milestone.

---

### TARGET ACCOUNTS (default list — user can override)
- CHECK POINT SOFTWARE TECHNOLOGIES LTD
- VERINT SYSTEMS LTD (COMVERSE INFOSYS)
- Playtech Software Limited
- SOLAREDGE TECHNOLOGIES

Ask the user if they want to use this default list or provide different accounts.

---

### PHASE 1: DISCOVERY (via Web API — fast, no UI scraping)

**Step 1 — Get all Deal Team opportunities:**
Navigate to any MSX page (https://microsoftsales.crm.dynamics.com/) so the browser has an authenticated session. Then run this JavaScript via `playwright-browser_evaluate`:

```javascript
async () => {
  const fetchXml = `<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="true" count="250">
    <entity name="opportunity">
      <attribute name="name" />
      <attribute name="opportunityid" />
      <attribute name="parentaccountid" />
      <attribute name="msp_opportunitynumber" />
      <filter type="and">
        <condition attribute="statecode" operator="eq" value="0" />
      </filter>
      <link-entity name="team" to="opportunityid" from="regardingobjectid" alias="aa">
        <filter type="and">
          <condition attribute="teamtype" operator="eq" value="1" />
          <condition attribute="name" operator="like" value="%cc923a9d-7651-e311-9405-00155db3ba1e" />
        </filter>
        <link-entity name="teammembership" intersect="true" visible="false" to="teamid" from="teamid">
          <link-entity name="systemuser" to="systemuserid" from="systemuserid" alias="ab">
            <filter type="and">
              <condition attribute="systemuserid" operator="eq-userid" />
            </filter>
          </link-entity>
        </link-entity>
      </link-entity>
    </entity>
  </fetch>`;
  const encoded = encodeURIComponent(fetchXml);
  const url = `/api/data/v9.2/opportunities?fetchXml=${encoded}`;
  const resp = await fetch(url, {
    headers: {
      'Accept': 'application/json',
      'OData-MaxVersion': '4.0',
      'OData-Version': '4.0',
      'Prefer': 'odata.include-annotations="OData.Community.Display.V1.FormattedValue"'
    }
  });
  const data = await resp.json();
  return data.value.map(o => ({
    id: o.opportunityid,
    name: o.name,
    accountName: o['_parentaccountid_value@OData.Community.Display.V1.FormattedValue'] || ''
  }));
}
```

Filter results client-side by target account names (case-insensitive contains match).

**Step 2 — Get all milestones for matching opportunities:**
Build an OData filter with all matching opportunity IDs and query in one call:

```javascript
async () => {
  const oppIds = [/* array of matched opportunity GUIDs */];
  const filters = oppIds.map(id => `_msp_opportunityid_value eq '${id}'`).join(' or ');
  const url = `/api/data/v9.2/msp_engagementmilestones?$select=msp_name,msp_milestonecategory,msp_engagementmilestoneid,statuscode,_msp_opportunityid_value&$filter=${filters}&$top=500`;
  const resp = await fetch(url, {
    headers: { 'Accept': 'application/json', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0' }
  });
  const data = await resp.json();
  return data.value;
}
```

**Step 3 — Store in SQL and present approval table:**
- Store opportunities and milestones in SQL tables for tracking
- Present a numbered table: `# | Opportunity | Account | Milestone`
- Also list opportunities with NO milestones as a warning
- Ask user to approve by numbers (e.g. "1, 5, 14") or "all"

---

### PHASE 2: TASK CREATION (via browser automation)

For each approved milestone, create **3 task activities**:

| Task Category | Duration | Subject |
|---|---|---|
| Architecture Design Session | 2 days | {Opportunity Name} POC |
| PoC/Pilot | 3 days | {Opportunity Name} POC |
| Technical Close/Win Plan | 3 hours | {Opportunity Name} POC |

- **Due date**: Last day of the current month
- **Subject**: The opportunity name + " POC"

**Navigation flow for each milestone:**

1. Navigate to milestone record:
   `https://microsoftsales.crm.dynamics.com/main.aspx?appid=fe0c3504-3700-e911-a849-000d3a10b7cc&pagetype=entityrecord&etn=msp_engagementmilestone&id={milestone_guid}`

2. Wait for page to load (wait for "Loading..." to disappear)

3. Click the **"Timeline"** tab on the milestone form

4. Click **"Create a timeline record."** button (or the "+" icon)

5. Select **"Task"** from the activity type menu

6. In the Quick Create: Task dialog, fill:
   - **Subject**: `{Opportunity Name} POC`
   - **Task Category**: Select the appropriate value from dropdown
   - **Due**: Set to last day of current month (e.g., 4/30/2026 for April)
   - **Duration**: Select the appropriate value from dropdown

7. Click **"Save and Close"**

8. Repeat steps 4-7 for the remaining 2 task categories

9. Move to next milestone

**IMPORTANT UI DETAILS:**
- Task Category dropdown exact values: "Architecture Design Session", "PoC/Pilot", "Technical Close/Win Plan"
- Duration dropdown exact values: "2 days", "3 days", "3 hours"
- Due date picker: Click the date field, clear it, type the date in M/D/YYYY format
- After saving each task, wait for the dialog to close before creating the next one
- If an "Unsaved changes" dialog appears, click "Discard changes"
- MSX pages load slowly — always wait for loading indicators to disappear
- The "Create a timeline record" button may appear as a "+" icon — look for it in the Timeline section

**Browser troubleshooting:**
- If Edge browser won't open due to "existing session" error, kill stale processes:
  `ps aux | grep "mcp-msedge" | grep -v grep | awk '{print $2}'` then kill each PID
- Wait 2-3 seconds after killing before retrying navigation

---

### PHASE 3: SUMMARY

After completing all tasks, present a summary:
- Total milestones processed
- Total tasks created (should be 3x milestones)
- Any failures or skipped items
- List of opportunities that had no milestones
