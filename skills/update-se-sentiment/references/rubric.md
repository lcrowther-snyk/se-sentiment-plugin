# Colour rubric

Salesforce values: `Green`, `Yellow`, `Red`, `Gray`. Pick the colour that best describes the **technical win** likelihood right now, not the commercial forecast.

| Colour | Use when | Typical evidence |
|---|---|---|
| **Green** | Technical win on track. Success criteria agreed and being met; champion engaged; next step dated. | "results look great", criteria ticked off, champion pushing internally, tech decision positive |
| **Yellow** | Progress, but at least one open blocker or unknown. | integration gap, missing stakeholder, slipping PoV dates, unanswered asks, roadmap dependency, competitor still in play |
| **Red** | Technical win at real risk. | criteria failing, competitor preferred, champion lost or silent, customer ghosting, stalled with no next step, escalation |
| **Gray** | No active technical evaluation, or too early to judge. | discovery only, renewal with no eval, post-sale hand-off, deal parked |

Rules of thumb:
- Change colour only on evidence from the window. Refreshing the note with the same colour is fine.
- Moving to or from **Red** needs a specific reason in the rationale (quote, missed date, decision).
- Two or more Yellow signals with no mitigation and a close date inside 30 days → consider Red.
- A positive call doesn't make a deal Green if a known blocker is still open; say both in the note.
- If evidence conflicts (Gong says great, Slack says escalation), go with the more recent and more specific, and mention the conflict.
- **Ghosting is a risk, not "no news".** Customer unresponsive to 2+ follow-ups for 10+ days during a PoC/eval → at least Yellow; 3+ weeks with no reply and no next step → Red.
- **Customer says pause / on hold / next quarter** → Yellow (or Gray if the eval is formally parked); never leave it Green.
- **Renewal or expansion quoted below the current contract** (`AVERAGE_ARR_NET` < 0) → not Green unless the reduction is agreed and the rest is on track; name the reduction in the note.
- **Open commercial or licensing dispute** (e.g. contributing-developer count) → at least Yellow until resolved; name it in the note.

Confidence:
- **high**: direct evidence from a call/notes in the window.
- **medium**: indirect (Slack, tickets) or older than 7 days.
- **low**: inference from a meeting title or calendar only. Prefer a **prompt** message over a low-confidence colour change.
