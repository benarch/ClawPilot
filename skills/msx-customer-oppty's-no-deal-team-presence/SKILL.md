---
name: "msx-customer-oppty's-no-deal-team-presence"
description: "Scans MSX opportunities for target accounts (Check Point, Verint, Playtech, SolarEdge) and lists all open opportunities where the user is NOT on the Deal Team. Returns a numbered table for action."
---

## MSX Customer Opportunities — No Deal Team Presence

### PURPOSE
Query MSX Dynamics 365 to find ALL open opportunities for target customer accounts where the current user is **NOT** listed on the Deal Team. Present a numbered table so the user can take action by referencing opportunity numbers.

---

### TARGET ACCOUNTS (default list — user can override)
- CHECK POINT SOFTWARE TECHNOLOGIES LTD
- VERINT SYSTEMS LTD (COMVERSE INFOSYS)
- Playtech Software Limited
- SOLAREDGE TECHNOLOGIES

The account filter uses partial matching (LIKE %name%) so it catches sub-entities (e.g., "Playtech Limited", "Playtech Holding Sweden AB", "SOLAREDGE E-MOBILITY SRL", "Verint Netherlands", "Check Point", etc.).

---

### PHASE 1: BROWSER SETUP

1. Navigate to `https://microsoftsales.crm.dynamics.com/` to establish an authenticated session.
2. If the browser fails to launch due to "existing session", kill stale processes:
   ```bash
   ps aux | grep "mcp-msedge" | grep -v grep | awk '{print $2}'
   ```
   Then kill each PID and retry after 3 seconds.
3. Wait for the page to load (wait for "Loading..." to disappear).

---

### PHASE 2: DISCOVERY (via Dynamics 365 Web API — fast, no UI scraping)

Run TWO FetchXML queries via `playwright-browser_evaluate` in a single JavaScript call:

**Query 1 — ALL open opportunities for target accounts:**
```javascript
async () => {
  const fetchXmlAll = `<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="true" count="500">
    <entity name="opportunity">
      <attribute name="name" />
      <attribute name="opportunityid" />
      <attribute name="parentaccountid" />
      <attribute name="msp_opportunitynumber" />
      <attribute name="estimatedvalue" />
      <attribute name="estimatedclosedate" />
      <filter type="and">
        <condition attribute="statecode" operator="eq" value="0" />
      </filter>
      <link-entity name="account" from="accountid" to="parentaccountid" alias="acct">
        <filter type="or">
          <condition attribute="name" operator="like" value="%CHECK POINT%" />
          <condition attribute="name" operator="like" value="%VERINT%" />
          <condition attribute="name" operator="like" value="%Playtech%" />
          <condition attribute="name" operator="like" value="%SOLAREDGE%" />
        </filter>
      </link-entity>
    </entity>
  </fetch>`;

  const headers = {
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0',
    'Prefer': 'odata.include-annotations="OData.Community.Display.V1.FormattedValue"'
  };

  const resp1 = await fetch(`/api/data/v9.2/opportunities?fetchXml=${encodeURIComponent(fetchXmlAll)}`, { headers });
  const allOpps = await resp1.json();

  // Query 2: My Deal Team opportunities for the same accounts
  const fetchXmlDealTeam = `<fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="true" count="500">
    <entity name="opportunity">
      <attribute name="name" />
      <attribute name="opportunityid" />
      <attribute name="parentaccountid" />
      <attribute name="msp_opportunitynumber" />
      <attribute name="estimatedvalue" />
      <attribute name="estimatedclosedate" />
      <filter type="and">
        <condition attribute="statecode" operator="eq" value="0" />
      </filter>
      <link-entity name="account" from="accountid" to="parentaccountid" alias="acct">
        <filter type="or">
          <condition attribute="name" operator="like" value="%CHECK POINT%" />
          <condition attribute="name" operator="like" value="%VERINT%" />
          <condition attribute="name" operator="like" value="%Playtech%" />
          <condition attribute="name" operator="like" value="%SOLAREDGE%" />
        </filter>
      </link-entity>
      <link-entity name="team" to="opportunityid" from="regardingobjectid" alias="tm">
        <filter type="and">
          <condition attribute="teamtype" operator="eq" value="1" />
          <condition attribute="name" operator="like" value="%cc923a9d-7651-e311-9405-00155db3ba1e" />
        </filter>
        <link-entity name="teammembership" intersect="true" visible="false" to="teamid" from="teamid">
          <link-entity name="systemuser" to="systemuserid" from="systemuserid" alias="me">
            <filter type="and">
              <condition attribute="systemuserid" operator="eq-userid" />
            </filter>
          </link-entity>
        </link-entity>
      </link-entity>
    </entity>
  </fetch>`;

  const resp2 = await fetch(`/api/data/v9.2/opportunities?fetchXml=${encodeURIComponent(fetchXmlDealTeam)}`, { headers });
  const myOpps = await resp2.json();

  const allList = allOpps.value.map(o => ({
    id: o.opportunityid,
    name: o.name,
    account: o['_parentaccountid_value@OData.Community.Display.V1.FormattedValue'] || '',
    oppNumber: o.msp_opportunitynumber || '',
    estValue: o['estimatedvalue@OData.Community.Display.V1.FormattedValue'] || '',
    estClose: o['estimatedclosedate@OData.Community.Display.V1.FormattedValue'] || ''
  }));

  const myIds = new Set(myOpps.value.map(o => o.opportunityid));
  const notOnTeam = allList.filter(o => !myIds.has(o.id));

  return {
    totalForAccounts: allList.length,
    onDealTeam: myIds.size,
    notOnDealTeam: notOnTeam.length,
    opportunities: notOnTeam
  };
}
```

---

### PHASE 3: STORE & PRESENT RESULTS

1. **Create a SQL table** for tracking:
   ```sql
   DROP TABLE IF EXISTS msx_opportunities;
   CREATE TABLE msx_opportunities (
     num INTEGER PRIMARY KEY,
     name TEXT NOT NULL,
     account TEXT NOT NULL,
     opp_number TEXT,
     est_value TEXT,
     est_close TEXT,
     opp_id TEXT NOT NULL
   );
   ```

2. **Number all results sequentially** (1, 2, 3, ...) and INSERT into the table.

3. **Present a summary**:
   - Total open opportunities for target accounts
   - How many the user IS on the deal team for
   - How many they are NOT on the deal team for

4. **Present a numbered table grouped by account** with columns:
   `| # | Opportunity Name | Est. Value | Est. Close |`

5. **Remind the user** they can reference opportunities by number to take action (e.g., "open #38", "join deal team on #80").

---

### PHASE 4: ACTIONS (on user request)

When the user references an opportunity by number:

- **"open #N"** — Navigate to: `https://microsoftsales.crm.dynamics.com/main.aspx?appid=fe0c3504-3700-e911-a849-000d3a10b7cc&pagetype=entityrecord&etn=opportunity&id={opp_id}`
- **"details #N"** — Look up the opportunity ID from SQL and fetch additional details via Web API.

---

### BROWSER TROUBLESHOOTING
- If Edge browser won't open due to "existing session" error, kill stale processes:
  `ps aux | grep "mcp-msedge" | grep -v grep | awk '{print $2}'` then kill each PID
- Wait 2-3 seconds after killing before retrying navigation
- MSX pages load slowly — always wait for loading indicators to disappear
