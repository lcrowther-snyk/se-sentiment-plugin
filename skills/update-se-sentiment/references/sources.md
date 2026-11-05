# Data sources

How to query each source. All are read-only. Run independent lookups in parallel.

## A. Snowflake (deals + current sentiment)

Tool: `execute-sql-read` (Snyk data connector). Always use fully qualified names; there is no default database.

Tables (verified Oct 2026):
- `PROD_ANALYTICS.PROD_ANALYTICS.SALESFORCE_USERS`: `USER_ID`, `USER_NAME`, `USERNAME` (= work email), `USER_ROLE`.
- `PROD_ANALYTICS.PROD_ANALYTICS.OPPORTUNITIES` (modeled): `OPPORTUNITY_ID`, `ACCOUNT_ID`, `ACCOUNT_NAME`, `SE_ID`, `SALES_ENGINEER_NAME`, `OWNER_NAME`, `FORECAST_CATEGORY`, `CLOSE_DATE`, `IS_CLOSED`, `TERRITORY_THEATRE` (`APJ`, `AMER`, `EMEA`), `TERRITORY_REGION`, `SE_SENTIMENT`, `SE_SENTIMENT_DETAILS`, `SE_SENTIMENT_STATUS_LAST_UPDATED`.
- `PROD_ANALYTICS.PROD_ANALYTICS.SALESFORCE_OPPORTUNITY` (raw Fivetran copy, ~hourly): `ID`, `NAME`, `STAGE_NAME`, `SALES_ENGINEER_C`, `LAST_SUCCESS_APP_STATUS_C`, `LAST_SUCCESS_APP_STATUS_COLOR_C`, `LAST_SUCCESS_APP_STATUS_DATE_C`, `SE_SENTIMENT_STATUS_LAST_UPDATED_C`, `SE_SENTIMENT_STATUS_LAST_UPDATED_BY_C`, `EVALUATION_START_DATE_C`, `EVALUATION_END_DATE_C`, `POC_END_DATE_C`, `POC_IS_ACTIVE_C`, `EVALUATION_TECH_DECISION_C`, `LAST_MODIFIED_DATE`, `_FIVETRAN_SYNCED`, `_FIVETRAN_DELETED`.

Use the raw table for the sentiment fields (exact Salesforce values) and the modeled table for theatre, account name and forecast category.

**A1. SE user id from email**
```sql
SELECT USER_ID, USER_NAME FROM PROD_ANALYTICS.PROD_ANALYTICS.SALESFORCE_USERS
WHERE LOWER(USERNAME) = LOWER('<se email>');
```

**A2. SE's open deals with current sentiment**
```sql
SELECT o.OPPORTUNITY_ID, s.NAME AS OPP_NAME, o.ACCOUNT_ID, o.ACCOUNT_NAME, s.STAGE_NAME,
       o.FORECAST_CATEGORY, o.CLOSE_DATE, o.OWNER_NAME, o.TERRITORY_REGION,
       s.LAST_SUCCESS_APP_STATUS_COLOR_C AS CUR_COLOR,
       s.LAST_SUCCESS_APP_STATUS_C       AS CUR_NOTE,
       s.LAST_SUCCESS_APP_STATUS_DATE_C  AS CUR_DATE,
       s.SE_SENTIMENT_STATUS_LAST_UPDATED_C AS CUR_UPDATED_AT,
       s.EVALUATION_START_DATE_C, s.EVALUATION_END_DATE_C, s.EVALUATION_TECH_DECISION_C,
       s.POC_LICENSE_ENABLED_DATE_C, s.POC_END_DATE_C, s.POC_IS_ACTIVE_C,
       s._FIVETRAN_SYNCED
FROM PROD_ANALYTICS.PROD_ANALYTICS.OPPORTUNITIES o
JOIN PROD_ANALYTICS.PROD_ANALYTICS.SALESFORCE_OPPORTUNITY s ON s.ID = o.OPPORTUNITY_ID
WHERE o.SE_ID = '<se user id>' AND o.IS_CLOSED = FALSE AND NOT s._FIVETRAN_DELETED
ORDER BY CASE o.FORECAST_CATEGORY WHEN 'Forecast' THEN 1 WHEN 'BestCase' THEN 2 WHEN 'Pipeline' THEN 3 ELSE 4 END,
         o.CLOSE_DATE;
```
Add `AND o.TERRITORY_THEATRE = 'APJ'` for APJ-only runs. Forecast category values in Snowflake: `Forecast` (= Commit), `BestCase`, `Pipeline`, `Omitted`. Never-set sentiment (blank colour/date) counts as the stalest.

**Daily-run deal filter** (add to A2):
```sql
AND o.OWNER_NAME NOT ILIKE '%IT Admin%'
AND s.CLOSE_DATE <= DATEADD(day, 90, CURRENT_DATE())
AND s.STAGE_NAME <> 'Opportunity Identification'   -- never draft for OI-stage deals
AND ( o.FORECAST_CATEGORY IN ('Forecast','BestCase')
      OR (s.POC_LICENSE_ENABLED_DATE_C IS NOT NULL AND COALESCE(s.POC_END_DATE_C, CURRENT_DATE()) >= DATEADD(day,-14,CURRENT_DATE()))
      OR (s.EVALUATION_END_DATE_C >= DATEADD(day,-14,CURRENT_DATE())) )
```
plus any other open deal (still closing within 90 days, not in Opportunity Identification) on an account where the SE had an external meeting (source J) since the last run. All current colours are included, Gray and never-set too. Mention `_FIVETRAN_SYNCED` if the user asks how fresh it is.

**A3. Account email domains** (for calendar matching) are not reliably in Snowflake; derive them from Gong attendees (Atlas) or from past calendar invites for that account.

## B. Gong via Atlas

Tool: `atlas_customer_intel`. Atlas holds Gong calls and some emails only (no Meet or Zoom, verified Oct 2026). One call can cover several accounts:

> "For these accounts: <A>, <B>, <C>: list external Gong calls since <date> with date, title, attendees, Gong URL, and a short summary of what was said about the evaluation/PoV, blockers, decision timeline, champion and competitors. Include short verbatim quotes."

Use Gong URLs as the evidence link.

## C. Google Calendar

Tool: `list_events` on the primary calendar, window = run window. Keep events where at least one attendee email is outside `@snyk.io` and the event wasn't declined. Match to an account by attendee domain or title. Note the event title and start time for matching notes in D/E. Only the running user's calendar is visible; for a manager running "for <SE>", calendar evidence is limited to meetings the manager was also on.

## D. Gemini / Google Meet notes

Tool: Gmail `search_threads`:
```
(from:gemini-notes@google.com OR from:meetings-noreply@google.com) subject:Notes newer_than:<N>d
```
Subjects look like `Notes: "<meeting title>" Oct 20, 2026`. Match to the calendar event by title and date, then `get_thread` (PLAIN_TEXT) for the summary; for more detail, open the "Open meeting notes" Doc with Drive `search_files` (`title contains '<meeting title>'`) and `read_file_content`.

## E. Zoom summaries

Gmail: `from:no-reply@zoom.us (subject:summary OR "Meeting summary") newer_than:<N>d`. Only AI Companion summaries are useful; "has joined your meeting" emails are noise. There is no Zoom connector.

## F. Slack deal channels

Tool: `search_slack_deal_channels` with a natural-language question, e.g. "What happened on the <Account> deal in the last two weeks: PoV progress, blockers, decisions?"

## G. Confluence customer pages

Tool: `search_customer_confluence_pages`: "PoV plan or success criteria for <Account>". Use it to judge progress against agreed criteria.

## H. Support tickets

Tool: `search_customer_tickets`: "Open or recent support tickets for <Account> that could block the evaluation".

## J. Salesforce activities (meetings any SE attended)

Snowflake `PROD_ANALYTICS.PROD_ANALYTICS.SALESFORCE_ACTIVITIES`. Works for every SE, not just the runner, so it is the main way to find customer meetings Gong didn't record. Events titled `[Gong] ...` are Gong-synced calls.
```sql
SELECT ACTIVITY_SCHEDULED_DATE, ACCOUNT_NAME, ACTIVITY_SUBJECT, WHAT_ID
FROM PROD_ANALYTICS.PROD_ANALYTICS.SALESFORCE_ACTIVITIES
WHERE ACTIVITY_ASSIGNED_TO = '<SE full name>'
  AND ACTIVITY_SFDC_SOURCE_TYPE = 'events'
  AND ACTIVITY_SCHEDULED_DATE BETWEEN '<window start>' AND CURRENT_DATE()
  AND ACCOUNT_NAME IS NOT NULL AND ACCOUNT_NAME <> ''
ORDER BY ACTIVITY_SCHEDULED_DATE DESC;
```
Ignore travel, holidays, conferences and internal events (no account). `WHAT_ID` is the linked Opportunity or Account.

Synced emails and call notes: `PROD_MODELED.GTM.TASKS` (`ACCOUNT_ID`, `ACTIVITY_DATE`, `SUBJECT`, `DESCRIPTION`) filtered by account and window.

## K. Deal Next Steps

`PROD_MODELED.GTM.OPPORTUNITIES.NEXT_STEPS` and `NEXT_STEPS_LAST_UPATED_DATE` (sic) joined on `OPPORTUNITY_ID`. AEs often keep this fresher than SE sentiment; use it as supporting evidence, never as the only reason to change colour.

## I. Snyk product knowledge (AlphaPatch)

Tool: `search_all_knowledge`, only when a call mentions a product gap or roadmap ask and you need to know whether it is GA, so the note doesn't overstate it.
