# 0004 — The constant field: the field, or the describing?

- Credit: **the control is u/aofu_dev's**, proposed on the r/LLMDevs thread
  for *"Adding a field to a JSON reply changed the rest of the answer, and
  moving it didn't help"* (2026-09-23). They proposed exactly the arm run here:
  a dummy field that always returns "ok", to see whether the disagreement still
  goes up on the same cases without asking for a description. The design below
  is theirs. What this record adds is the predictions, the counting and the
  limits. We had tested where the field sits, and never whether it matters
  what the field contains
- Status: **pre-registered**, 2026-09-23. Written and committed before the
  prompt is touched, so the run can contradict it
- Is a control for: [0001](0001-about-beside-reason.md), whose eight runs say
  outright that they measured an effect and not a mechanism
- Moves, on this branch only: `prompts/judge.txt` (one line), `suite.py`'s
  schema and `parse`, `fake.py`'s reply. All three are restored before the
  branch is offered for merge, so the morning's digest never sees the arm
- Does not move: the cases, the marks, `samples`, `min_agreement`, the model,
  the thresholds, the baseline

## The question

0001 added a field, `about`, to the judge's reply and the judge went loose: the
number of cases whose five samples disagree went from the old prompt's band to
**7–8 in eight runs of eight**, with `about` written first and with it written
last. Position is ruled out. What is left is two readings, and 0001 could not
tell them apart:

- **The field.** Asking for any extra key changes the reply's shape, and the
  shape is what costs.
- **The describing.** Asking the model to describe the item is extra work, and
  the work is what costs. This is what everybody assumes, the published post
  included, and nobody has checked it.

**The control:** the same reply shape with no work in it. A field that is
always the string `"ok"`.

## The arm

The old prompt, **byte-identical except for one line**:

```
{"reason": "<one concise sentence in Italian>", "score": <int 1-5>}
```
becomes
```
{"reason": "<one concise sentence in Italian>", "score": <int 1-5>, "ack": "ok"}
```

No sentence explains `ack`. The template shows a literal value, which is the
least instruction that can ask for a field.

- **Compared against the old prompt, not against v3.** The old prompt is the
  arm that did not have the field. This arm differs from it by one key and
  nothing else. v3 differs from it by the key, 162 tokens of instructions, the
  double-quote clause and `about` itself. Those are what the old-prompt
  comparison removes.
- **Last, like v3.** The score is written before `ack`, the way it was written
  before `about` in v3. The field cannot condition the score through what it
  generates, in either arm. Position was measured to make no difference, so
  the choice does not decide anything. It only keeps this arm one step away
  from the nearest arm already measured.
- **`name`**: `ack`, chosen because it asks for nothing. `status` or `check`
  would read as a judgement to make.
- `suite.py` requires `ack` with `"const": "ok"`, so a reply that does not
  return the constant is a `json_schema` failure. The control is only a control
  if the field really is constant, and this is where that shows. `config_hash`
  moves, as it did for 0001. The measure is `agrees_with_mark`, and its
  identity does not.
- `JUDGE_MAX_TOKENS` stays 200, as in the old prompt. v3 ran at 400. That can
  only matter if a reply reaches the cap. The old prompt's replies average 60
  output tokens, and the largest reply in the four runs is reported with the
  result.

**Same suite, same 21 cases, five samples, four runs.** One more run of the old
prompt follows the four, as the drift check 0001 ran for the same reason. It is
not one of the four.

## What is measured, and how it is counted

**The number of cases whose five `agrees_with_mark` samples are not all
equal**, per run. It is the same count 0001 reported. It is recomputed here
from the run documents, and it reproduces 0001's numbers exactly:

| prompt | runs | cases whose samples disagree |
|---|---|---|
| old (`judge.txt` `05c20df6`) | 23 | median **4**, range **1–6** |
| v2, `about` first (`cdd171d6`) | 4 | 7, 7, 8, 7 |
| v3, `about` last (`ead44034`) | 4 | 7, 7, 8, 7 |

The old prompt has 23 runs and not the 19 of 0001's table. The four extra are
0002's restored runs of this morning (1, 2, 2, 4). They are the same prompt and
they sit inside the band. **No run of the old prompt has reached 7. No run with
`about` has come in under 7.** That is the line this control is read against.

**The same cases.** One case carries 0001's signature more than any other:

| case | old, 23 runs | with `about`, 8 runs |
|---|---|---|
| `frontier-red-teampatterns` | splits in **1** | splits in **7** |
| `don-t-classify-hallucinate` | splits in **12** | splits in **1** |

The first is the case `about` made unstable. The second is the one it made
stable. A result that says "the same way" has to reproduce both.

## Predictions, written before the run

One claim, one direction, one line, as 0001 asks of itself.

**If the field is what costs:**

1. Every one of the four runs has **7 or more** cases whose samples disagree.
2. `frontier-red-teampatterns` splits in **3 or more** of the four.
3. `don-t-classify-hallucinate` splits in **1 or fewer** of the four.

**If the describing is what costs:**

4. Every one of the four runs has **6 or fewer** cases whose samples disagree.
5. `frontier-red-teampatterns` splits in **1 or fewer** of the four.

**Neither, and it is ruled now so it cannot be ruled after:**

6. **Mixed counts** (some runs at 6 or fewer, some at 7 or more): **undecided at
   four runs.** No fifth run is taken to break the tie. A control that needs one
   more run after it has been seen is being steered.
7. **1 holds and 2 does not.** The count grows, but on other cases. The field
   loosened the judge, but not the way `about` did. One reading, and the limits below: an edit
   this small moves where the borderline cases sit, and which cases those are
   depends on the edit. That is a third reading. This control can report it
   but cannot confirm it.

**My estimate, which is a guess:** 4 and 5, the describing. It is weak, and this
series has made three optimistic estimates in one direction already. It is
written down so the result can be read against it, not because it should be
believed.

## What this control cannot separate, said before it can surprise anyone

A constant field still adds an instruction to the prompt. 0001 measured that
instructions cost on their own: +192 input tokens a call for v1, +162 for v3.
So each reading has a length question, and the two answers are not the same.

**"Grows the same" (1–3) can be separated from "the prompt got longer".** This
arm adds about **7 input tokens** to the old prompt, measured from the run and
reported. v3 added 162. If about 4% of the added prompt produces the full
effect, the effect does not scale with length, and length is not the
explanation.

**What it cannot be separated from is "the prompt changed at all".** You cannot
ask for a field without editing the prompt, so in this control the field and
the edit are one treatment. If 1–3 hold, the honest sentence is *"one extra key,
and seven tokens, were enough"*. It is not *"the shape of the reply is the
cause, and any other seven-token edit would have been harmless"*. That second
claim needs an arm that edits the prompt by a few tokens without adding a field.
This control does not have one.

**"Does not grow" (4–5) cannot be separated from length, and this is the limit
that matters.** `about` came with 162 tokens of instructions and this field
comes with about 7. The describing reading and the length reading predict the
same result. If 4 and 5 hold, the finding is *"the cost is in the describing or
in the words that asked for it"*. It is not *"the cost is the describing"*.
Separating them takes an arm this control does not include: the old prompt
padded by about 160 tokens of neutral text, with no field. It is named here so
nobody reads a "no" as the answer the published post assumed.

**And "the describing" does not mean generating it.** In v3 the score is
written before `about` exists, so the description's tokens cannot have
influenced the score. If 4 and 5 hold, the cost is in being *asked* to describe:
the job as the prompt states it, not the text the model then writes. The post
says "generating the description". The data from v3 alone already narrows that
word.

## Cost

About **$0.07 a run** at the old prompt's measured $0.000666 a judgement, so
**about $0.35** for four runs and the drift check. I expect this estimate to be
low as well.

## Order of work

1. This text. Committed before anything else moves.
2. The arm: `prompts/judge.txt`, `suite.py`, `fake.py`. Committed before the
   run, so every run document names a reachable commit and not a dirty tree.
3. Four live runs of the arm.
4. The arm reverted in its own commit. The branch then touches only
   `decisions/`. The drift check runs on that commit: the old prompt, once.
5. The result, read against 1–7, appended below. Nothing above this line is
   edited after the run, except the credit line.


## Result, 2026-09-23: the field does not cost. Predictions 4 and 5 hold

Four runs of the arm at `7d5d269`, `config_hash 6b36822dfb5114f3`, `judge.txt`
`e34a074b`. The same count and the same script as the table above.

| | old prompt (23 runs) | `about`, first or last (8) | **`"ack": "ok"` (4)** |
|---|---|---|---|
| **cases whose samples disagree** | median 4, range 1–6 | 7, 7, 8, 7, 7, 7, 8, 7 | **5, 3, 5, 4** |
| `frontier-red-teampatterns` splits | 1 of 23 | 7 of 8 | **1 of 4** |
| `don-t-classify-hallucinate` splits | 12 of 23 | 1 of 8 | **3 of 4** |
| accuracy numerator /21 | median 16 | median 15 | **16, 16, 15, 16** |
| input tokens a call | 366.5 | 508.5 / 528.5 | **372.5** |

Against the predictions, one line each:

1. **Falsified.** No run reached 7. The largest count was 5.
2. **Falsified.** `frontier-red-teampatterns` split in 1 of 4.
3. **Falsified.** `don-t-classify-hallucinate` split in 3 of 4, back to what it
   does under the old prompt.
4. **Holds.** All four runs are at 6 or fewer, inside the old prompt's band.
5. **Holds.** 1 of 4.
6. Does not arise. The counts are not mixed.
7. Does not arise. The count did not grow.

The estimate held as well: 4 and 5. It is the first estimate in this series
that did not come back optimistic. With four runs that is one data point, not a
recalibration.

**The control was a control.** All 420 replies returned `"ack": "ok"`. Zero
`json_schema` failures, zero errored samples. The largest reply was 91 output
tokens against the cap of 200, so the cap that differs from v3 never came into
play. The arm added **6 input tokens a call**, measured (366.5 → 372.5), against
the 7 estimated. It also added about 11 output tokens: 70 a call against 59 for
the old prompt on the same day. The constant costs tokens to write, and it is
the only thing the arm costs: $0.00072 a judgement against $0.00066.

**No drift.** The old prompt, run once on `1ab516a` after the arm was reverted:
**4** cases, accuracy 16/21. That is its median, on the same afternoon.

### What this says, within the limits written above

**The shape of the reply is ruled out, at this dose.** One more key in the JSON,
with no work in it, left the judge exactly as stable as it was. So 0001's
finding narrows: what loosened the judge was not *asking for a field*, it was
asking for **that** field.

**What is left is the half this control said it could not settle.** Reading 4
and 5 as the section above requires: *the cost is in the describing, or in the
162 tokens of instructions that asked for it.* This control cannot tell those
two apart, and it said so before it ran. It is still a sharper result than
it looks, because those two are **exactly the post's two guesses**: "asking for
a description changes what the model thinks the job is", and "maybe it's just a
longer prompt". The reader's control removed the third explanation, the shape,
which the post did not even list. It leaves the post's own two standing, and it
names the arm that separates them: the old prompt plus about 160 tokens of
neutral text, with no field.

**What changes for the post's advice.** *"The new field doesn't belong in that
reply at all, first or last"* was written about a field with content. A field
with no content was harmless here. The advice stands for a field the model has
to work to fill. It does not stand as *any key costs you*, and nobody should
read it that way now that it has been measured.

**Not a third piece on its own.** The dummy did not move the verdicts, so the
condition for a third piece in the series did not fire. It is a correction to
the second piece, and it is the most useful kind: it narrows a finding in public,
on a reader's design.

### An accident, recorded rather than tidied away

A fifth run of the arm was taken by mistake. A failed `git revert` left the arm
in place, and the run meant as the drift check ran the arm instead. Its
document names `680a4ce`, an amended copy of `7d5d269` with the same tree
(`81d1325`), no longer on any branch. It gave **4**. It is **not part of the
reading**: the four were fixed in advance, and prediction 6 forbids a fifth run
from deciding anything. It is reported because it was taken, and because
dropping a run that agrees is no more honest than dropping one that does not.
The real drift check is the run on `1ab516a` above.

Spent: **$0.45**. $0.30 on the four runs, $0.07 on the drift check, and
$0.08 on the accidental fifth.
