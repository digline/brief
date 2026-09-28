# 0005 — The padded prompt: the describing, or the tokens?

- Named by: [0004](0004-the-constant-field.md), in the section that says what
  it could not separate, before it ran: *"the old prompt padded by about 160
  tokens of neutral text, with no field."* Nobody built it. This record builds
  it, with its own predictions
- Status: **pre-registered**, 2026-09-28. Written and committed before the
  prompt is touched, so the run can contradict it
- Is a control for: [0001](0001-about-beside-reason.md), through 0004
- Moves, on this branch only: `prompts/judge.txt`, and nothing else. It is
  restored before the branch is offered for merge, so the morning's digest
  never sees the arm
- Does not move: the cases, the marks, `samples`, `min_agreement`, the model,
  `JUDGE_MAX_TOKENS`, the schema, `parse`, `fake.py`, the thresholds, the
  baseline

## The question

0004 ruled out the shape of the reply: one key with no work in it, `"ack":
"ok"`, left the judge as stable as the old prompt (5, 3, 5, 4 against a band of
1–6). It left two readings of 0001 standing, and said it could not tell them
apart:

- **The describing.** What `about` asked for is the cost: being asked to
  describe the item changes what the model takes the job to be.
- **The tokens.** v3 added **162 input tokens** a call, measured (366.5 →
  528.5). A prompt that much longer is a different prompt, whatever the words
  say.

These are the post's two guesses, in its own words: *"Maybe asking for a
description changes what the model thinks the job is, no matter where the
answer sits. Maybe it's just a longer prompt, so a different one. I tested
neither."*

**The control:** the same token cost as v3, with nothing to describe and no
field. The old prompt plus about 160 tokens of text that asks for nothing.

## The arm

The old prompt, **byte-identical**, with one blank line and the padding after
its last line. The reply template is untouched:
`{"reason": "<one concise sentence in Italian>", "score": <int 1-5>}`.

**Where it goes, and why there.** In both prompts that carried `about`, v2
(`cdd171d6`) and v3 (`ead44034`), the describing instructions sat in one
place: after the JSON template line, separated from it by a blank line. The
template was the prompt's last line before them, so they ran to the end of the
prompt. The padding goes in exactly that place. Here "where the instructions
sat" and "at the end" are the same position. It is chosen because it is v3's
position, not because it is the end. Moving it earlier, for example between the
scale and `Respond with ONLY…`, would put back the variable this arm holds
fixed. 0004 held it fixed too: position was ruled out for the field, never for
the words.

**What the padding is.** Three short paragraphs of plain English on how a
river delta forms. It asks for nothing and describes nothing the model is
given. It says nothing about the reader, the item, the score, the reply,
Italian or quoting. It has no imperative, no list line (so `fake.py`, which
reads the prompt's bullet lists, answers as before), and no double quote. It is
English because the instructions it replaces in the comparison were English.
It is off-topic on purpose, so that nothing in it can be read as taste.

**The dose, measured before the run.** With `messages.count_tokens` on
`claude-haiku-4-5`, on the same system prompt, user turn and prefill:

| prompt | input tokens (count_tokens) | added to the old prompt |
|---|---|---|
| old (`05c20df6`) | 294 | — |
| v3 (`ead44034`, text taken from its run document) | 456 | **+162** |
| **padded** | 458 | **+164** |

The counter reproduces v3's +162 exactly, as measured in its runs, so the arm
is expected to run at **about 530.5 input tokens a call** (366.5 + 164). The
runs report it. Anything outside **525–536** means the arm is not the arm I
described, and it is reported instead of read.

**`config_hash` does not move, and that is correct.** It is built from the
assertions, thresholds, tolerances, `samples`, `min_agreement` and pricing
(`digline.core.run.config_hash`). It never sees the prompt. 0004's hash moved
because its arm changed the schema. This arm changes only the prompt, so it
runs at the old prompt's **`98fc65b1e49e930e`**. A run of this arm is therefore
**promotable over the baseline without refusal**, and nobody promotes it. The
arm's runs are told apart from the old prompt's by `judge.txt`'s sha in the run
document's artifacts and by `git_commit`, and they are counted that way. The
discipline is: every run counted here names the arm's commit and the arm's
sha, and the hash has to read `98fc65b1e49e930e`. A run with a different hash
means something besides the prompt moved.

`JUDGE_MAX_TOKENS` stays 200, as in the old prompt. The largest reply in the
four runs is reported, as 0004 did.

**Same suite, same 21 cases, five samples, four runs.** One more run of the old
prompt follows the four, on the commit that reverts the arm, as the drift
check. It is not one of the four.

## What is measured, and how it is counted

As 0004: **the number of cases whose five `agrees_with_mark` samples are not
all equal**, per run, recomputed from the run documents. The reference today,
from the same script, which reproduces 0004's tables:

| prompt | runs | cases whose samples disagree |
|---|---|---|
| old (`05c20df6`) | 24 | median **4**, range **1–6** |
| `"ack": "ok"` (`e34a074b`, 0004) | 4 | 5, 3, 5, 4 |
| `about`, first or last (`cdd171d6`, `ead44034`) | 8 | 7, 7, 8, 7, 7, 7, 8, 7 |

The old prompt has 24 runs, not 0004's 23. The 24th is 0004's drift check on
`1ab516a` (4). 0004's accidental fifth run of its arm is not counted anywhere,
as 0004 ruled.

The two cases that carry 0001's signature:

| case | old, 24 runs | with `about`, 8 runs |
|---|---|---|
| `frontier-red-teampatterns` | splits in **1** | splits in **7** |
| `don-t-classify-hallucinate` | splits in **12** | splits in **1** |

## Predictions, written before the run

One claim, one direction, one line.

**If the tokens are what costs:**

1. Every one of the four runs has **7 or more** cases whose samples disagree.
2. `frontier-red-teampatterns` splits in **3 or more** of the four.
3. `don-t-classify-hallucinate` splits in **1 or fewer** of the four.

**If the describing is what costs:**

4. Every one of the four runs has **6 or fewer** cases whose samples disagree.
5. `frontier-red-teampatterns` splits in **1 or fewer** of the four.

The thresholds are 0004's, unchanged, and for the same reason: no run of the
old prompt, 24 now, has reached 7, and no run with `about` has come in under 7.
The line between the two bands is the only line these runs can draw.

**Between, ruled now so it cannot be ruled after:**

6. **Mixed counts** (some runs at 6 or fewer, some at 7 or more): **undecided
   at four runs.** No fifth run is taken to break the tie. I will conclude only
   that 164 tokens there are neither reliably harmless nor reliably the whole
   effect. I will **not** conclude that the cost is "partly the tokens and
   partly the describing". Four runs straddling a line do not measure a split
   between two causes. Both of the post's guesses stay standing.
7. **1 holds, 2 does not** (every run at 7 or more, but `frontier` does not
   split): the padding loosens the judge, but not the way `about` did. I will
   conclude that length at this position costs. I will **not** conclude that
   length is what `about` did, because the signature is missing. That leaves
   0001 explained by "length plus something specific", undecided.
8. **4 holds, 5 does not** (every run at 6 or fewer, `frontier` splits in 2 or
   more): the count decides, and it reads as the describing. The case is
   reported. I will **not** read one case splitting as a partial token effect.
   `frontier` is one case of 21, and a borderline case moves with any edit.
9. **Every run inside the band but above the old median** (say 5, 6, 5, 6):
   this reads as 4, the describing. Twenty-four runs of the old prompt range
   from 1 to 6, so four runs cannot resolve a shift inside that band. I will
   **not** write "the tokens cost a little". 0004's 5, 3, 5, 4 was read the
   same way, and the same rule has to hold whichever way I would like it to go.

**My estimate, which is a guess:** 4 and 5, the describing. 0004's constant
field did nothing at 6 tokens, and I expect 164 tokens that ask for nothing to
do nothing either. That is the weakest kind of reason, an extrapolation across a
27-fold dose, and this series has four estimates behind it, three of them
optimistic in the same direction. It is written down so the result can be read
against it.

## What this control cannot separate, said before it can surprise anyone

**"Grows" (1–3) cannot be told from "irrelevant text distracts".** Neutral
does not mean inert. The padding is text the model has to read and set aside,
and off-topic text in a prompt is a known treatment of its own. If 1–3 hold,
the honest sentence is *"164 tokens that asked for nothing, placed where the
describing instructions were, loosened the judge as much as `about` did"*. That
removes the describing as the explanation of 0001. It does **not** show that
it is the count of tokens and not the presence of something irrelevant. An arm
that pads with on-task text that asks for nothing, such as a restatement of the
reader's interests, would come closer, but restating the taste changes the
judging. I name it here and do not plan to run it.

**"Does not grow" (4–5) cannot be told from "any instruction about the reply
costs".** The 162 tokens in v3 were instructions about what to write. The
padding is not an instruction at all. If 4 and 5 hold, the finding is *"the
cost is in what those 162 tokens said, not in how many there were"*. Put
together with 0004, that means not the shape and not the length: the content.
It is **not** *"describing, specifically"*. Instructions of the same length
that ask for more work on `reason`, and for no description, would separate
describing from instructing. That arm is not this one.

**And, as 0004 already narrowed, not "generating".** In v3 the score is
written before `about` exists. If 4 and 5 hold, the cost is in being *asked*,
not in the text the model then writes.

**One position, one model, one prompt.** The padding is where the
instructions were, by design, so the arm says nothing about padding elsewhere.
One model, `claude-haiku-4-5`, and one judging prompt, as everywhere in this
series.

## Addendum, or a piece of its own

Ruled now, like the rest. The post holds its two guesses side by side and says
it tested neither. So:

- **1–3 hold, or 4–5 hold.** One of the post's two guesses is overturned: the
  describing if the tokens cost, the length if they do not. That is a finding
  the post does not contain, so it is **a piece of its own**, which links back.
- **6, 7, 8 or 9.** For 8 and 9 the count decides, so they are 4–5 and follow
  the line above. **6 and 7 overturn nothing**, so each is **an addendum** to
  added-field, saying what was run and that it did not settle the question.

Nothing is written for the blog in this branch. This section decides the form,
not the text.

## Cost

About **$0.087 a run**: the old prompt's $0.0694, plus 164 tokens × 105 calls
at Haiku 4.5's $1 per million input tokens (+$0.017). So about **$0.35** for
four runs, and **$0.42** with the drift check. 0004 estimated $0.35 and spent
$0.45, $0.08 of it on a run taken by mistake.

## Order of work

1. This text. Committed before anything else moves.
2. The arm: `prompts/judge.txt`. Committed before the run, so every run
   document names a reachable commit and not a dirty tree.
3. Four live runs of the arm.
4. The arm reverted in its own commit, **checked with `git log -1` and a diff
   against `main` before the drift check runs**. That is the step 0004's
   accident happened at. The branch then touches only `decisions/`. The drift
   check runs on that commit: the old prompt, once.
5. The result, read against 1–9, appended below. Nothing above this line is
   edited after the run.
