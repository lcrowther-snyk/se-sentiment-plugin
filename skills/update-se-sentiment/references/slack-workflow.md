# Slack approval workflow

The write path. One shared Slack workflow, owned by the SE lead; each SE approves their own drafts.

## How it works

```
send_proposal.py  ->  POST webhook {se_user, opp_id, opp_name, colour, status_note, status_date, current, rationale, evidence_url}
   -> Slack DM to se_user: draft + [Approve and update Salesforce]
   -> SE taps Approve -> Salesforce "Update a record" runs AS THE SE -> confirmation message
```

The first time an SE taps Approve, Slack asks them to connect Salesforce (normal Okta login, once).

## Workflow setup (Workflow Builder)

**Trigger: From a webhook.** Variables (exact names, all Text unless noted):

| Variable | Type |
|---|---|
| `se_user` | Slack user ID |
| `opp_id` | Text |
| `opp_name` | Text |
| `colour` | Text |
| `status_note` | Text |
| `status_date` | Text |
| `current` | Text |
| `rationale` | Text |
| `evidence_url` | Text |
| `set_eval_dates` | Text (`no` / `start` / `end` / `both`) |
| `tech_decision` | Text (`Win` / `Loss` / `Undecided`, blank unless the end date is set) |

**Tech decision (live since 5 Nov 2026):** Salesforce requires `Evaluation_Tech_Decision__c` whenever `Evaluation_End_Date__c` is set. Accept branches AA (`both`) and AC (`end`) set Evaluation Tech Decision = `{tech_decision}` in the same Update step. The Edit form has an optional Evaluation Tech Decision dropdown (default = current Salesforce value, hint "Needed if you set an Evaluation End Date. Pick Undecided if unsure."). The DM shows the decision via the rationale line.

**Live workflow `se-sentiment-daily` (published 28 Oct 2026):**

**Step 1: Send a message to `{se_user}`**
```
SE Sentiment draft for {opp_name}
Now: {current} -> Proposed: {colour}
Note: {status_note}
Why: {rationale}
Evidence: {evidence_url}
Pick one: Accept saves it as is, Edit lets you change it first, Reject skips it. To change it later, use the Open in Salesforce button.
[Accept] [Reject] [Edit] [Open in Salesforce]
```
Accept / Reject / Edit are **mutually exclusive**: once one is clicked, all three disappear, so a rejected draft can't be accepted later and each draft is edited at most once. **Open in Salesforce** is a link button (`https://snyksec.lightning.force.com/lightning/r/Opportunity/{opp_id}/view`) that never disappears, for any later changes.

**Branch A, Accept: Salesforce Update a record** on Opportunity `{opp_id}`, run as the person who clicked:
- SE Sentiment Status (`Last_Success_App_Status__c`) = `{status_note}`
- SE Sentiment Status Color (`Last_Success_App_Status_Color__c`) = `{colour}`
- SE Sentiment Status Date (`Last_Success_App_Status_Date__c`) = time the button was clicked

then DM: "✓ Saved to Salesforce for {opp_name}: {colour} - {status_note}".

Slack can't rewrite the original draft message, so the ✓ reply is how the SE sees what was actually saved.

Then (still on Accept) **Read a record** on the Opportunity, and a branch on `set_eval_dates` (values read from Salesforce, so they arrive as real dates):
- `both` → Update Evaluation Start = POC License Enabled Date and Evaluation End = Pilot End Date
- `start` → Update Evaluation Start only
- `end` → Update Evaluation End only
- `no` (or anything else) → nothing

**Branch B, Reject:** DM to `{se_user}`: "Skipped: nothing changed in Salesforce for {opp_name}".

**Branch C, Edit: Update a record with a form** ("Edit SE Sentiment"), run as the clicker. Form fields are pre-filled: Colour = `{colour}`, Status note = `{status_note}`, Date = time clicked, Evaluation Start / End Date = current Salesforce values (hints say "usually the pilot switch-on / end date"). Whatever the SE submits is written (Submit = save; the form is titled "Edit, Submit to save" because Slack doesn't allow renaming the Submit button), then DM: "✓ Saved your edit to Salesforce for {opp_name}: {edited colour} - {edited note}".

Notes:
- The Date field only accepts a Slack time variable, so `status_date` from the webhook is shown nowhere and the date written is the approval date. Fine for forecast purposes; the note itself starts with the evidence date.
- If a Salesforce step ever shows "Connect your external account", the step holds a stale connection: delete it and re-add it (Slack > Preferences > Connected accounts shows whether Salesforce is connected).

## Verified behaviour (21 Oct 2026)

- Webhook POST returns `{"ok":true}` (HTTP 200) when accepted; that only means the DM was queued.
- A test write via this workflow set `Last_Success_App_Status__c` on 006000000000001AAA, recorded as the clicking SE, and the archive/last-updated automation fired. Snowflake picked it up ~70 minutes later.
- Webhook variables not defined in the workflow are ignored silently, so keep this table in sync with the live workflow.

## Security

- The webhook URL lives in `config.json`; anyone with it can trigger DMs (not Salesforce writes; those still need the recipient's tap). Don't paste it in chat or logs. Regenerate it if it leaks.
- The script only sends the allow-listed variables above.
