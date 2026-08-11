# Role-Based Prompting Exercise — Technical Documentation Assistant

Turns informal engineering notes into structured internal documentation using
role-based prompting in Amazon Bedrock Playground.

**Model:** Amazon Nova Pro (`amazon.nova-pro-v1:0`)
**Parameters:** Temperature 1, Top-P 1, Max output tokens 2560, no guardrails, no prompt caching

---

## Final Prompt

**System Prompt:**
```
You are a senior technical writer embedded in a software engineering team.
You write internal documentation for other engineers who will read it weeks
or months later, without the context the original author had.

AUDIENCE: Software engineers with general technical background, but no
prior knowledge of this specific change.

OUTPUT FORMAT — use exactly these headings, in this order. Omit a heading
only if the notes contain no relevant content for it:

## Summary
One to two sentences on what changed, including when it was deployed if
the notes state a date.

## Motivation
Why the change was made, based only on what the notes state.

## Implementation
Bullet points describing current behavior.

## Behavior & Edge Cases
Bullet points for specific scenarios and how the system handles each one.

## Known Tradeoffs / Limitations
Bullet points for anything explicitly called out as an accepted tradeoff.

## Open Items
Bullet points for unfinished work or follow-ups, taken directly from the
"still to do" / open items in the notes. Do not mark anything as complete
if the notes describe it as pending.

CONSTRAINTS:
- Every fact from the notes must appear in the output exactly once, under
  its single most relevant heading. Do not repeat the same fact under
  multiple headings, even in different wording.
- Do not omit any item from the notes, including dates, deployment
  timing, or "still to do" items — every distinct fact in the source
  notes must map to exactly one place in the output.
- Do not invent, infer, or add any detail, metric, or behavior not
  explicitly stated in the notes.
- Do not use marketing or hype language ("robust," "seamless,"
  "significantly improved," etc.).
- Keep total output under 200 words.
- Plain, direct, technical language only. No filler sentences.
```

**User message:**
```
<engineering_notes>
[raw notes pasted here]
</engineering_notes>
```

---

## Methodology

Four iterations were run against the same sample notes (a Redis caching
change) to isolate what actually improves output quality, rather than
assuming role-based prompting helps by default.

| Task | Change tested | Fabrication | Completeness | Duplication | Length |
|---|---|---|---|---|---|
| 1 — No role | baseline | ❌ invents success claims | ✅ | — | over limit (no cap set) |
| 2 — Role added, no format spec | role framing only | ⚠️ softened, not fixed | ✅ | ❌ new redundancy | longer than Task 1 |
| 3 — Explicit format + constraints | structured output, anti-fabrication rule | ✅ | ❌ dropped deploy date | ❌ | ✅ under 200 words |
| 3 (retest) — added anti-duplication + anti-drop rules | stronger constraints | ✅ | ✅ | ❌ still persists | ✅ |
| 4 — System prompt vs. bundled user message | prompt placement (same wording as Task 3 retest) | ✅ | ✅ | ❌ still persists | ✅ |

---

## Key Findings

- **Role framing alone is weak.** Adding a persona softened fabricated
  claims but didn't eliminate them, and added structural redundancy without
  improving completeness or length.
- **Explicit format + anti-fabrication constraints fixed fabrication and
  length**, but this first version introduced a new failure — it silently
  dropped an item (the deploy date) despite its own "don't drop items" rule.
- **Constraint specificity matters.** Making the "don't drop items" rule
  explicit about dates/timing fixed the drop. A generic "don't repeat
  yourself" instruction did not fix duplication.
- **Duplication is the most persistent failure mode.** The same fact
  (sold-out items showing as available) was repeated across two headings in
  every version from Task 2 onward — including after adding an explicit
  anti-duplication constraint, and including after moving the entire prompt
  from a bundled user message into the dedicated System Prompt field.
  Prompt placement had no measurable effect. This points to the model
  treating "behavior" and "tradeoff" as independently valid reasons to
  restate the same fact, not a fixable prompt-assembly artifact — likely
  requires explicit heading precedence to resolve.
- **All comparisons were run at Temperature 1**, not Temperature 0. This
  was not a controlled ablation of randomness — the persistent duplication
  could be partly influenced by sampling temperature, which was not tested.

## Known Limitations of This Prompt

- Duplication across "Behavior & Edge Cases" and "Known Tradeoffs /
  Limitations" is unresolved as of the final version tested.
- Not tested at Temperature 0 — unclear whether duplication is
  temperature-sensitive or a consistent model behavior.
- Audience-swap experiment (technical vs. non-technical PM) was scoped but
  not completed in this run.

## Files in This Repo

- `README.md` — this summary
- `technical-documentation-assistant-exercise.md` — full task-by-task log with
  every prompt, output, and observation for Tasks 1–4
- `Exercise-Technical_Documentation_Assistant.md` — initial exercise 