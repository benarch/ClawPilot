---
name: "msx-poc-tasks"
description: "Creates 3 POC task activities (Architecture Design Session, PoC/Pilot, Technical Close/Win Plan) on every milestone for each opportunity where the user is on the deal team in MSX Dynamics 365. Invoke with /msx-poc-tasks."
---

You are automating MSX (Microsoft Sales Dynamics 365) to create POC task activities on milestones.

## IMPORTANT: Browser & Dynamics 365 Tips
- MSX is a Dynamics 365 app. Pages load slowly — always wait for elements to appear before interacting.
- After every navigation or click, wait at least 3-5 seconds for the page to load, then take a snapshot.
- If you see an "Unsaved changes" dialog, click "Discard changes".
- If you see a "Loading..." indicator, wait for it to disappear.
- The grid cells in MSX sometimes appear empty in snapshots — take screenshots when needed to see actual content.
- When double-clicking a grid row opens inline editing, press Escape and instead use the row's link or the Edit command button.

## TARGET ACCOUNTS FILTER
Only process opportunities belonging to these accounts (match by account name in the "Account" column):
1. Alpha Company
2. Umbrella Corp
3. Stark Industries
4. Wayne Enterprises
5. Willy Wonka

Use case-insensitive partial matching — e.g., "Umbrella Corp" matches "UMBRELLA CORP". Skip any opportunity whose account is NOT in this list.

## WORKFLOW

### Step 1: Navigate to MSX Opportunities
1. Navigate to: https://microsoftsales.crm.dynamics.com/
2. Wait for the page to fully load (wait for "Loading..." to disappear).
3. In the left navigation, click on "Opportunities" under the "Pipeline" section.
4. Wait for the opportunities grid to load.

### Step 2: Switch to "My Deal Team Opportunities" view
1. Click the view selector button (currently showing the active view name, e.g., "a) My Open Opportunities").
2. In the dropdown that appears, select "b) My Deal Team Opportunities".
3. Wait for the grid to reload with the deal team opportunities.
4. Take a snapshot/screenshot to see the opportunities list.

### Step 3: Collect matching opportunities and their milestones (DISCOVERY PHASE)
Scan ALL rows in the grid (scroll/page if needed). For each opportunity:

1. **Read the Account name** from the "Account" column.
2. **Check if the account matches** one of the target accounts listed above.
3. If it does NOT match, skip it.
4. If it matches, **click into the opportunity** to open it.
5. **Click the "Milestones" tab** and read the milestones in the grid.
6. Record each milestone's **Name** and the parent **Opportunity Name** and **Account**.
7. Navigate back to the opportunities list and continue scanning.

### Step 4: Present numbered milestone list for approval (APPROVAL PHASE)
After scanning all opportunities, **STOP and present a single numbered table** of ALL milestones across all matching opportunities:

| # | Opportunity Name | Account | Milestone Name |
|---|---|---|---|
| 1 | Opp A | Umbrella Corp ... | Milestone X |
| 2 | Opp A | Umbrella Corp ... | Milestone Y |
| 3 | Opp B | Wayne ... | Milestone Z |
| ... | ... | ... | ... |

Ask the user: "Here are all the milestones I found. Which ones should I create POC tasks for? Reply 'all' to proceed with all, or list the numbers (e.g., '1, 3, 5') to select specific milestones."

**DO NOT proceed to create any tasks until the user explicitly approves by number or says 'all'.**

### Step 5: Process approved milestones
For EACH approved milestone (by its number):

1. Navigate to the opportunity that contains this milestone.
2. **Click the "Milestones" tab** on the opportunity form.
3. **Click on the milestone name link** in the grid to navigate to the milestone record page.
   - IMPORTANT: Do NOT double-click (that opens inline editing). Instead, look for a link in the Name column and single-click it. If no link is visible, select the row and use the "Edit" command in the toolbar.
4. Wait for the milestone record form to load.
5. **Click the "Timeline" tab** on the milestone form.
6. Wait for the Timeline section to load.

### Step 6: Create 3 Task Activities
For each of the 3 tasks below, repeat this process:

**Task 1: Architecture Design Session**
- Click the "Create a timeline record." button (the + icon near the Timeline heading).
- A menu appears with activity types: Appointment, Email, Phone Call, Task, Chat.
- Click "Task Activity".
- The "Quick Create: Task" dialog opens with these fields:
  - **Subject**: Type "{Opportunity Name} POC" (replace {Opportunity Name} with the actual opportunity name).
  - **Task Category**: Click the dropdown and select "Architecture Design Session".
  - **Due**: Set to the last day of the current month. Calculate it: for the current month/year, find the last calendar day. Enter it in M/D/YYYY format in the date picker.
  - **Duration**: Click the dropdown and select "2 days".
- Click "Save and Close".

**Task 2: PoC/Pilot**
- Click the "Create a timeline record." button again.
- Click "Task Activity".
- In the Quick Create: Task dialog:
  - **Subject**: Type "{Opportunity Name} POC".
  - **Task Category**: Select "PoC/Pilot".
  - **Due**: Last day of current month (same as Task 1).
  - **Duration**: Select "3 days".
- Click "Save and Close".

**Task 3: Technical Close/Win Plan**
- Click the "Create a timeline record." button again.
- Click "Task Activity".
- In the Quick Create: Task dialog:
  - **Subject**: Type "{Opportunity Name} POC".
  - **Task Category**: Select "Technical Close/Win Plan".
  - **Due**: Last day of current month (same as Task 1).
  - **Duration**: Select "3 hours".
- Click "Save and Close".

### Step 7: Navigate back and continue
1. After creating all 3 tasks for a milestone, click the browser back button or "Press Enter to go back" button to return to the opportunity's Milestones tab.
2. Process the next approved milestone.
3. After all approved milestones are processed, provide a summary.

### Step 8: Summary
After processing all approved milestones, provide a summary:
- How many milestones had tasks created (and which ones by number)
- Any errors or skipped items

## KEY FIELD REFERENCES (from MSX UI exploration)
- **View selector**: Button showing current view name at top of the grid
- **Milestones tab**: Tab labeled "Milestones" in the opportunity form tablist
- **Timeline tab**: Tab labeled "Timeline" in the milestone form tablist
- **Create timeline record button**: Button labeled "Create a timeline record." in the Timeline section
- **Task Activity menu item**: Menu item labeled "Task Activity" in the activity type menu
- **Quick Create Task dialog**: Dialog titled "Quick Create: Task" with fields:
  - Subject (textbox, required)
  - Task Category (dropdown: Architecture Design Session, PoC/Pilot, Technical Close/Win Plan, etc.)
  - Due (date picker)
  - Duration (dropdown: 1 minute, 15 minutes, 30 minutes, ..., 3 hours, ..., 2 days, 3 days)
  - Save and Close (button)

## DATE CALCULATION
The due date should be the last day of the current month. To calculate:
- Get today's date
- Find the last day of the current month
- Format as M/D/YYYY (e.g., 4/30/2026 for April 2026)
