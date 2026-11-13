# se-sentiment

Keeps SE Sentiment current on APJ opportunities. Every weekday morning, Claude reads the SE's own calls, Gemini notes, calendar and deal activity, drafts a colour + status note per deal, and DMs it to the SE in Slack. The SE taps **Accept**, **Edit** or **Reject**; Accept/Edit write to Salesforce as the SE through Snyk's approved Slack app. Nothing is written without that click.

## For SEs

1. Install the `se-sentiment.plugin` file your SE lead shares (not from this repo; the repo copy has no team config):
   - Upgrading? Uninstall the old version first (Settings → Plugins → se-sentiment).
   - Install via **Settings → Plugins → Upload plugin**. Dragging the file into a chat only uploads it.
   - Fully quit and restart the Claude app, otherwise the new commands aren't recognised.
   - Check you can open the ANZ / APJ customer folders and the "SE Sentiment draft log" doc.
2. In Cowork, run **/setup-se-sentiment**. It checks your connectors, schedules the daily run, and shows a sample draft.
3. Keep the Claude app open in the morning (missed runs catch up when you next open it).

Run it any time with "update my SE sentiment" or `/update-se-sentiment opp <deal>`.

## Connectors used

| Connector | Required | Why |
|---|---|---|
| Snyk data (Snowflake) | yes | deals, current sentiment, Salesforce activities, pilots |
| Slack | yes | finds your Slack ID, summary message |
| Google Calendar, Gmail, Google Drive | recommended | meetings, Gemini / Zoom notes, draft log |
| Snyk knowledge (Atlas, tickets, Confluence, deal channels) | recommended | Gong calls, blockers, PoV criteria |

## For the maintainer

- The Slack workflow `se-sentiment-daily` (Workflow Builder) is the write path; see `skills/update-se-sentiment/references/slack-workflow.md`.
- `skills/update-se-sentiment/config.json` holds the workflow webhook URL and is **git-ignored**. Start from `config.example.json`.
- Build the team plugin: `./build.sh` → `dist/se-sentiment.plugin`. Share it inside Snyk only.
- Rotating the webhook: regenerate it in Workflow Builder, update your local `config.json`, rebuild, reshare.
- Enable the secret-blocking hook once per clone: `git config core.hooksPath .githooks`.
- `evals/` holds dry-run test cases for the skill. They use placeholder names (Sam Example, Alex Example); swap in a real SE name locally before running them, and don't commit real customer or SE names.

## If you close the Edit form without saving

Slack can't reopen it. Ask Claude "resend <deal>" and you'll get a fresh DM, or use the Open in Salesforce button.
