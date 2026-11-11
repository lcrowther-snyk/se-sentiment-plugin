---
name: setup-se-sentiment
description: One-time setup for the SE Sentiment automation on an SE's own machine. Checks every connector the update-se-sentiment skill needs (Snowflake, Atlas, Google Calendar, Gmail, Google Drive, Slack, Confluence, support tickets), tells the SE how to connect anything missing, confirms the shared Slack workflow is configured, creates the weekday scheduled task in the SE's local timezone, and runs a dry run. Use when someone says "set up SE sentiment", "/setup-se-sentiment", "install the sentiment automation", "check my sentiment connectors" or "reschedule my sentiment run".
---

# Set up SE Sentiment

Get one SE from "plugin installed" to "daily drafts arriving in Slack" in about five minutes. Talk in plain language; the SE doesn't need to know about webhooks, config files or SQL.

## 1. Who is this

Use the session's email as the SE. Then, in parallel:
- Snowflake (`execute-sql-read`): `SELECT USER_ID, USER_NAME FROM PROD_ANALYTICS.PROD_ANALYTICS.SALESFORCE_USERS WHERE LOWER(USERNAME) = LOWER('<email>')`. No row → tell them their Salesforce user wasn't found and stop.
- Slack (`slack_search_users` with the email) → their Slack user ID.
- Count their open deals with the A2 query in `../update-se-sentiment/references/sources.md` (with the daily-run filter) so you can tell them how many deals the daily run will cover.

## 2. Check connectors

Make one tiny read-only call per source and show a ✓ / ✗ table. Run them in parallel.

| Source | Test call | Needed for |
|---|---|---|
| Snyk data (Snowflake) | the user lookup above | deals, current sentiment, activities (**required**) |
| Slack | `slack_search_users` above | routing drafts, summary (**required**) |
| Google Calendar | `list_events`, primary, today, `pageSize` 1 | meetings Gong missed |
| Gmail | `search_threads` `from:gemini-notes@google.com newer_than:14d`, 1 result | Gemini / Zoom notes |
| Google Drive | `search_files` `title contains 'Notes by Gemini'`, `pageSize` 1 | full Gemini notes, draft log |
| Atlas (Gong) | `atlas_customer_intel` "List my accounts' most recent Gong call date" (slow; fine) | call content |
| Confluence / tickets / Slack deal channels | `search_customer_tickets` "test", one result | PoV criteria, blockers |

Also check the customer folders: list each root in `../update-se-sentiment/config.json` `drive_customer_roots` with `search_files` (`parentId = '<folder_id>'`, `pageSize` 1). If either fails, tell them to ask their SE lead for access to the ANZ / APJ customer folders (optional, but drafts are much better with it).

Also read the shared draft log (`log_doc_id` in `../update-se-sentiment/config.json`) with Drive `read_file_content`. If it fails, tell them to ask their SE lead for edit access to "SE Sentiment draft log".

For each ✗: say what it's for and how to fix it: "Open Settings → Connectors, find <name>, click Connect, then say 'check again'." Snowflake and Slack are required: if either is missing, stop after the table. The rest are optional: carry on, and say the drafts will have less evidence until they're connected.

## 3. Check the team config

Run `python3 ../update-se-sentiment/scripts/send_proposal.py --check`. If it reports no webhook, tell them: "This copy doesn't have the team config. Ask your SE lead for the current se-sentiment plugin file and install that." Then stop. Never ask the SE for a URL and never print it.

## 4. Schedule the daily run

Ask one question: what time on weekdays (default 7:30am, their local time). Then call `create_scheduled_task`:
- `taskId`: `se-sentiment-daily`
- `title`: `SE Sentiment daily (<time> weekdays)`
- `cronExpression`: `<min> <hour> * * 1-5` (local time)
- `prompt`:
  > Run the update-se-sentiment skill as a scheduled daily run for me (<SE name>, <email>). Use my own deals only, apply the daily-run filter, check the draft log so nothing is re-sent, and send the drafts to me in Slack with `send_proposal.py <file> --send`. Never write to Salesforce directly; the Slack Accept/Edit button does that. Send the one-line summary to `summary_to` if set. Finish with: sent N (deal names), no change M, prompts K (account + meeting date), notes not accessible, skipped (reason).

If a task with that id exists, use `update_scheduled_task` instead. Then say: "It runs while the Claude app is open. If your laptop is asleep or the app is closed at that time, it runs the next time you open the app." For Mac users, offer the optional wake command: `sudo pmset repeat wakeorpoweron MTWRF <time minus 5 min>:00` (they run it in Terminal themselves).

## 5. Dry run

Run the update-se-sentiment skill on-demand for their top 2 deals as a **dry run** (no `--send`), and show the draft table so they see what the daily DM will look like. Ask if they want to send one for real to try the Accept / Edit buttons. The first time they click, Slack asks them to connect Salesforce once (normal Okta login).

## 6. Done

Summarise in three lines: connectors ✓/✗, schedule time, deals covered.
