# CalmConnect — escalation ladder design

## The problem this solves

Phase 1 produces two outputs per interaction: a category prediction
(Anxiety/Depression/etc.) and a binary escalation flag (Suicidal vs. not,
tuned for high recall). On their own these are just numbers. This
document defines what the *product* actually does with them — the
difference between "we have a classifier" and "we have a triage system,"
which is the gap that made the original version of this project feel
thin.

## Grounding: stepped care

This ladder is explicitly modelled on the **stepped care** framework used
in real mental health service design (originating in the UK, now used
internationally — including in a UNSW-affiliated stepped-care trial in
Jordan). The core principles, and how this project operationalizes each
one:

1. **Least intensive effective intervention first.** Stepped care
   delivers the most effective yet least resource-intensive treatment
   first, escalating only as needed (Centre for Innovation in Campus
   Mental Health). CalmConnect's five self-help modules ARE that bottom
   step — explicitly framed as Tier 0 self-directed support, not as a
   replacement for anything above it.
2. **Ongoing assessment, not a one-off triage.** A foundational principle
   of stepped care is that people who don't respond at their current
   level get stepped up — based on monitored outcomes, not a single
   intake decision. This is precisely why Phase 2 (trajectory modeling)
   matters: a single message's sentiment is a one-off triage; a trend
   across repeated check-ins is the "ongoing assessment" stepped care
   actually requires. Phase 1 alone is necessarily a simplification of
   this — stated honestly below, not hidden.
3. **Escalation is need-based, not diagnosis-based.** Modern stepped-care
   framings (e.g. "Stepped Care 2.0") explicitly move away from triaging
   purely on diagnostic category toward triaging on distress/need level.
   This is why Task 2 (the escalation trigger) is deliberately NOT just
   "is Suicidal the top category" — it is a separate, need-focused signal
   tuned on its own recall floor, independent of the category label.

## The ladder, as implemented in v1

| Step | Trigger | Product behaviour | Stepped-care analogue |
|---|---|---|---|
| 0 — Self-directed | Default state | Five therapy modules available, ranked by category + AU-season signal | Pure self-help, no professional involved |
| 1 — Gentle check-in | Repeated negative-leaning sessions (Phase 2 — not yet implemented, see below) | Surface a non-alarming prompt: "You've mentioned feeling low a few times this week — would a longer read on this help?" | Guided self-help / low-intensity monitoring |
| 2 — Encouraged professional contact | Category = Depression/Anxiety/Bipolar/Personality disorder AND high model confidence AND (once Phase 2 exists) a sustained negative trend | Persistent, non-blocking banner suggesting a GP or Lifeline's non-crisis line, alongside the therapy recommendation — not instead of it | Stepping up to primary-care-level mental health support |
| 3 — Crisis resources | Escalation trigger fires (Task 2, recall-floor tuned) | Crisis banner shown immediately and persistently (Lifeline, Beyond Blue, 000), in addition to — never instead of — the therapy recommendation | Stepping up to crisis/specialist care |

**What's actually implemented in the current codebase**: Step 0 and Step 3.
Step 1 and Step 2 require Phase 2's trajectory signal to be meaningful —
implementing them now, on single-message data, would just be re-badging
the category classifier's output as if it were a trend, which is exactly
the kind of overclaim this whole rebuild is trying to avoid. They are
specified here, with their trigger conditions, so the system design is
complete and reviewable even though the code isn't — and so that
Phase 2's actual purpose (making Steps 1-2 honestly implementable) is
clear.

## Why Step 3 never blocks or replaces Step 0

A deliberate, stated design choice: crisis resources are always shown
*alongside* a therapy recommendation, never as a replacement screen that
blocks access to the rest of the product. Two reasons:
1. A wellbeing tool that responds to distress by taking away the thing the
   person came for (functionally punishing disclosure) creates a
   perverse incentive to under-report how they're feeling next time.
2. CalmConnect is explicitly not a crisis service and should not behave
   like a gatekeeper pretending to be one. Its job at Step 3 is to make
   real crisis support visible and easy to reach, not to manage the
   crisis itself.

## What this is not

This is not a clinical triage tool and should never be presented as
having clinical validation, regulatory approval, or equivalence to an
actual stepped-care service run by trained professionals. The value of
grounding this in stepped-care literature is structural and intellectual
honesty — showing the reasoning is informed by how real systems are
designed — not a claim that this system has been validated the way a real
clinical stepped-care program would be.

## References

- Centre for Innovation in Campus Mental Health — Stepped Care Approach
  overview: least-intensive-first, outcome-monitored stepping up.
- "Improving Access to Mental Health Care through a Stepped Care
  Approach" (PMC, University of Coimbra study) — stepped care as an
  organizing framework proportioning care intensity to need, per NICE
  guidelines.
- Starling Minds — "Stepped Care 2.0," on triaging by need/context rather
  than diagnosis/symptom severity alone.
- "Stepping Up: Predictors of 'Stepping' within an iCBT Stepped-Care
  Intervention for Depression" (PMC) — on ongoing assessment as a
  foundation of stepped care, distinct from one-off intake triage.
- UNSW/Institute for Family Health Jordan stepped-care pilot RCT
  (medRxiv) — example of stepped care implemented and tested in a
  resource-constrained setting, methodologically relevant to "tools for
  people who can't access or afford therapy."
