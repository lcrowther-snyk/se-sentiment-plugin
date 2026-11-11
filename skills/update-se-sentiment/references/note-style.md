# Status note style

The note lands in `Last_Success_App_Status__c`, which leaders read in forecast calls. Existing notes average ~300 characters. Write like an SE would: short, factual, specific.

Format:
```
<SE initials> - <eval/PoV state>. <key risk or win>. <next step + date>.
```

- No date prefix. The date is already in the SE Sentiment Date field and the archive. Dates inside the note are only for upcoming milestones (e.g. "Next: exec readout 28/10").
- Initials of the SE whose deal it is (e.g. `SX` for Sam Example).
- 200 to 400 characters; hard limit 1000 (the script enforces it).
- Plain text, no bullets, no emoji, no markdown.
- No customer personal data (emails, phone numbers). Job titles are fine ("CISO", "AppSec lead").
- Name products the way Snyk does (Snyk Code, Snyk Open Source, Snyk Container, Snyk IaC, Evo). If unsure whether a feature is GA, check AlphaPatch and don't overstate it.

Good examples:
- `SX - PoV week 2 of 3. SCA and SAST criteria met; IDE rollout to 40 devs done. Risk: ServiceNow integration still untested. Next: exec readout 28/10.`
- `SX - Kick-off held, criteria agreed (SCA, Container, CI in GitHub Actions). Champion is the AppSec lead; budget owner not yet engaged. Next: tech deep dive 24/10.`
- `SX - Customer comparing with Checkmarx on SAST accuracy; our FP rate questioned on Java. Asked for side-by-side on 2 repos. Next: results review 23/10.`

Bad (and why):
- `Call went well.` (no state, no next step)
- `Customer loves Snyk and will definitely buy by Friday!!` (overclaims, not evidence-based)
- `Emailed john.smith@acme.com about pricing` (personal data, commercial not technical)
