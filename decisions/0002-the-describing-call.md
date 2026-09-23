# 0002 — The describing call

- Status: **proposed** — the text first, checkpointed before any code, as
  [0001](0001-about-beside-reason.md) was
- Date: 2026-09-23
- Supersedes: 0001's *implementation*, not its premise. The sentence under the
  title still decides whether I open the article, and only its descriptive half
  can be checked against the item. What changes is where that half is produced
- Moves: `prompts/judge.txt` (back), a new `prompts/describe.txt`, `brief.py`'s
  call structure, `reason.py`'s target, `fake.py`, `probe.py`
- Does not move: `cases/brief.json`, the marks, and — this is the point —
  `brief-judge`'s promoted baseline

## Why this exists

One sentence, bought with eight runs and $0.8761:

> **Adding a field is not additive.** Asking one call for one more thing changes
> how it does everything else, and **moving the field does not undo it**. If the
> existing behaviour has to be preserved, the new field does not belong in that
> reply at all — it belongs in a second call.

That is not a lesson appended to 0001; it is the whole reason this record
exists. 0001 added `about` to the judge's reply and the judge got worse at
judging — per-case sample disagreement left a 2–6 band it had held over
twenty-one runs and sat at 7–8. The obvious explanation was that the score was
being conditioned on a description written above it, so the field was moved
below the score and measured again. The result was **[7, 7, 7, 8] against
[7, 7, 7, 8]** — identical, to the value. Position was not it.

What is left, after two positions and eight runs, is that **a call asked to
judge and describe is a worse judge than a call asked only to judge**, wherever
the description sits. So the description moves out of that call.

## The decision

**Two calls per item.**

1. **The judging call reverts to byte-identical with the pre-0001 prompt.**
   Not "similar to" — the same file, restoring `config_hash`
   `98fc65b1e49e930e`, which means `brief-judge`'s already-promoted baseline
   becomes the right reference again and **nothing has to be re-baselined**.
   Its stability is not recovered by argument; it is recovered by not touching
   it.
2. **A second, short call describes the item**, and nothing else. No taste, no
   score, no relevance — four lines of prompt instead of fourteen. Its output is
   `about`, and it is what `Faithfulness` checks.

### A consequence worth naming: the context gets honest again

0001's first draft passed `Faithfulness` the item alone, and that was corrected
to *both* prompt files, because the model had been given the taste and a context
without it marked every relevance clause unsupported by construction.

**Under this decision the correction reverses, and for the same reason.** The
describing call is never shown `prompts/judge.txt`. It does not know what I like.
So the context for the faithfulness check is the item and only the item —
which is what 0001 wanted in the first place and could not honestly have.

## Predictions, written before any run

> ### How to write a prediction here
>
> **A falsifier that does not name the direction is half a falsifier.**
>
> Prediction 1 of 0002 was *"back inside the old 2–6 band"*. It was refuted by a
> run that scored **1** — quieter than any of the nineteen runs the band was
> drawn from — and the check printed **`0 of 4 inside the band`** while meaning
> the exact opposite of what it said. The falsifier existed to catch the
> disagreement *staying high*. It could not tell high from low, because a band
> has two sides and the prediction named neither.
>
> So: say which way. *"Below 6, and I do not care how far below"* is a
> prediction. *"Inside 2–6"* is a band, and a band will one day be broken from
> the good side by something you were hoping for. The next prediction written in
> this repository will be a band unless this paragraph stops it.


1. **`brief-judge` returns to its old behaviour exactly.** Per-case disagreement
   back inside 2–6; accuracy median 16/21. **This is the falsifier**, and it is
   a hard one: the prompt will be byte-identical to a file measured over
   twenty-one runs, so if the old behaviour does not come back, the prompt was
   never the cause and this whole diagnosis — 0001's and this record's — is
   wrong. There would be no third reordering to try; the next move would be to
   find what else changed.
2. **`about` from a dedicated call is more decomposable than from the combined
   one.** Faithfulness at or above the 0.725 measured under 0001, and
   abstentions near zero, because a call that was never asked to judge has no
   judgement to smuggle into its description.
3. **Cost lands near $0.00101 an item**: $0.000666 for the judging call as
   measured over twenty-one runs, plus roughly $0.00035 for a short describing
   call at about 120 input and 45 output tokens. Against the $0.001022 the
   current single call already costs — within a whisker.
4. **`economics` becomes judgeable**, and 0001's prediction for it applies
   unchanged: 0 abstentions of 5, score 0.6 or better, with the named failure
   mode still *"senza sommario"* when the item does carry one.

### Prediction 4 of 0001 is not inherited. It is made moot

0001 asked whether `about`, written after a judgement, would describe the score
instead of the item. It was never tested, and **under this decision it stops
being askable in this form**: the describing call sees no judgement, because
there is no judgement in its context to see.

That is worth saying plainly rather than quietly dropping. The question is not
answered. It is made unaskable by removing the thing that made it a question,
and if the single-call shape ever returns, it returns unanswered.

## What this costs, honestly

**Money: within a whisker.** Roughly $0.00101 an item against $0.001022 today.

**Robustness: not within a whisker.** Two calls per item is **twice the latency
and twice the failure surface on a morning**, for a field written by a different
call. A digest that fails half as reliably is a real change to something I use
every day, and it is not paid for by the arithmetic being flat.

So the failure semantics are part of this decision and not an afterthought:

- **A failed judging call behaves exactly as it does today.** That path is
  unchanged and its existing defect — a parse failure recorded as `score=0`,
  indistinguishable from an item judged worthless — is unchanged too. It is
  written up at `JUDGE_MAX_TOKENS` and it is 0003's problem, not this one's.
- **A failed describing call must not cost me the item.** The digest still shows
  it, with the score and the reason it already has, and `about` empty — and
  `seen.json` must record *why* it is empty rather than storing an empty string
  that reads like a description of nothing. That is Handbook chapter 0's fourth
  decision applied at the point where this record creates a new way to fail.

**Latency, concretely:** `MAX_JUDGED_PER_RUN` is 50 and the calls are serial, so
a first run goes from up to 50 calls to up to 100. The describing call is the
shorter of the two, so this is less than double in wall clock and more than
nothing.

## Order of work

1. This text. **Checkpoint.**
2. Revert `prompts/judge.txt` and `suite.py`'s schema. Confirm `config_hash` is
   `98fc65b1e49e930e` again and that the existing baseline is accepted.
3. Run `brief-judge` four times. **Read prediction 1 before arguing.** If it
   fails, stop and rethink rather than adjust.
4. Write `prompts/describe.txt` and the describing call, with its failure
   semantics.
5. Point `reason.py` at it, with context = the item alone, and re-measure the
   threshold from a full run.
6. Re-test the `economics` suspension.
7. `README.md`, which describes a two-field reply that will no longer exist.

Estimated spend: four `brief-judge` runs at $0.107 is $0.43, plus two or three
`brief-reason` cycles. Call it **$0.90–$1.20**, and say so before starting
rather than after.


## Step 3, measured (2026-09-23)

`prompts/judge.txt` byte-identical to pre-0001, `max_tokens` back to 200,
`config_hash` back to `98fc65b1e49e930e`. Four runs. No re-promotion.

### The hash, proven rather than asserted

```
brief-judge  config_hash 98fc65b1e49e930e   suite, now
baseline     config_hash 98fc65b1e49e930e   promoted 2026-09-22T12:41
git diff a82e9ee -- prompts/judge.txt       0 lines
```

and `compare` against that untouched baseline:

> Nothing got worse compared with the reference. … Every case could be judged.
> **The suite is unchanged from the reference. The files under test are the same
> as the reference. The system under test answered under the same configuration
> as the reference.**

Three sentences that could not have been produced by anything but a genuine
restoration. **Nothing was re-promoted.** The reference has been sitting in
`.digline/` since yesterday morning and became correct again by the
configuration returning to it.

### Prediction 1 — read first, and read honestly

| | cases of 21 whose five samples disagree |
|---|---|
| old prompt, 19 runs before 0001 | median 4, band **2–6** |
| 0001 v2, `about` first | **7, 7, 7, 8** |
| 0001 v3, `about` last | **7, 7, 7, 8** |
| **0002, prompt restored** | **1, 2, 2, 4** — median **2** |

**The literal test I wrote — "back inside 2–6" — fails, on one run of four.** It
fails because that run scored **1**, quieter than any of the nineteen old runs.
The check counted "outside the band" without caring which side, and the side is
the whole point: the falsifier existed to catch the disagreement *staying* at
7–8, and it did not stay. It collapsed.

So: **the direction is confirmed emphatically and the band test is a bad test.**
Written down that way rather than quietly rescored, because the sentence "0 of 4
inside the band" appeared on screen and a reader of this record deserves to know
it did, and why it means the opposite of what it says.

Whether the restored runs are genuinely *quieter* than the old ones — median 2
against 4 — is not something four runs can say. Noted, not theorised.

### Predictions 2 and 3

| | accuracy /21 | precision | $/judgement |
|---|---|---|---|
| old prompt, 19 runs | median 16, range 14–16 | 0.667 | 0.000668 |
| 0001 v2 | 13, 15, 15, 17 → 15.0 | 0.683 | 0.001063 |
| 0001 v3 | 14, 15, 16, 16 → 15.5 | 0.655 | 0.001022 |
| **0002 restored** | **16, 16, 16, 16** | **0.667** | **0.000663** |

Prediction 2 confirmed, and more exactly than it was written: not a median near
16 but **16 in every one of four runs**, which the old prompt itself managed in
eighteen of nineteen. Prediction 3 confirmed: $0.000663 against $0.000668, a
difference of 0.7%. Zero errored verdicts.

### The correction this forces, and it is mine

I told you `frontier-red-teampatterns` was a real disagreement with the mark
that *survived the wording*, below the line in 7 of 8 runs, and should be left
alone as a separate question. **It is not separate and it does not survive.**

| case | baseline | 0001 (8 runs) | 0002 restored |
|---|---|---|---|
| `frontier-red-teampatterns` | 0.80 | below the line 7 of 8 | **1.00, 1.00, 1.00, 1.00** |
| `how-we-built-auto-mode` | 0.60 | below 3 of 8 | 1.00, 0.80, 1.00, 0.80 |
| `alignment…whyne` | 0.40 | **above** in 8 of 8 | **0.20, 0.00, 0.00, 0.00** |

All three "findings" about individual cases were artefacts of the split prompt.
The regression that repeated seven times out of eight is gone the moment the
field leaves the reply; the improvement that repeated eight times out of eight
is gone with it. What looked like the judge changing its mind about three
articles was the judge being asked a different question.

*"It survives the wording"* was true and useless: it survived every wording I
tried **inside** the split, which is not the same as surviving the split, and I
should not have offered it as a separate question before the split had been
undone.

> ### The general trap
>
> **A finding that repeats under every variant of a change is not independent of
> the change.** It is evidence that the finding is stable, and stability is what
> repetition is for — but every variant shared the change, so every repetition
> was drawn from inside it. Eight runs said `frontier-red-teampatterns` had
> regressed, 7 of 8, across two orderings. Four runs with the change removed say
> 1.00, 1.00, 1.00, 1.00.
>
> The dangerous part is that this is the *same evidence* that correctly
> separated a real regression from a coin one round earlier — repetition across
> runs. It works across runs. It does not work across variants, and the two look
> identical on the page: *"7 of 8"*.
>
> The test is not how many times it repeated but **what every repetition had in
> common.** If the answer is *the thing under test*, the count says nothing
> about independence. The only run that could speak was the one with the change
> taken out, and there was no reason to expect it would disagree — which is
> exactly why it had to be run.

### What it cost, and why it was not waste

**$0.8761** — two prompt versions, eight runs — to establish that a second field
cannot live in that reply. **$1.3608** in total under the split prompt.

A round that ends by restoring a file byte-for-byte reads like a wasted round.
It was not, and the reason is narrow: **the only way to know the field was the
cause was to put it there and take it out.** Nothing in the first four runs
could separate *the field is the problem* from *the field is in the wrong
place* — the two hypotheses predict the same numbers. That took the second four,
and the answer was identical numbers. And nothing in either set could separate
*the prompt is the cause* from *something else moved* — that took this third
set, and the answer is 16, 16, 16, 16.

Three sets of four runs, three questions, each one unanswerable without the one
before it:

| runs | the question only they could answer | the answer |
|---|---|---|
| 0001 v2, `about` first | is the two-field reply worse than the one-field one? | yes — disagreement 2–6 → 7–8 |
| 0001 v3, `about` last | is it worse *because of where the field sits*? | no — 7, 7, 7, 8 again, identical |
| 0002, field removed | is it the prompt at all, or did something else move? | the prompt — 16, 16, 16, 16 |

Neither of the first two can distinguish *the field is the problem* from *the
field is in the wrong place*: both hypotheses predict the same numbers. Neither
of the first two, together, can distinguish *the prompt is the cause* from
*something else moved under us*. Only the third set can, and only because the
first two had narrowed it to that.

---

**If you are reading this as a diff six months from now, you are looking at a
revert.** `prompts/judge.txt` ends this decision byte-identical to how it
started it, and the natural reading of that is that a week was spent and nothing
happened.

What happened is the table above. The file is identical because **identical was
the finding** — that a second field cannot live in that reply, which is not a
fact anyone could have read off the code, and which cost $1.3608 and twelve runs
to establish. The description did not get dropped; it moved to a call of its
own, which is what the rest of this record is about. The revert is the
experiment's control arriving last, not the experiment being abandoned.


## Step 4, built (2026-09-23)

`prompts/describer.txt`, `BriefDescriber`, `Description`, a third fake, and a
probe that shows both calls. No suite is re-baselined; `brief-judge` still reads
`98fc65b1e49e930e` and `compare` still says the suite, the files and the
configuration are unchanged from the reference.

### The failure semantics, which are in the code and not only in this record

`Description` carries **`about` or `failed`, never both and never neither**, and
refuses at construction otherwise. `run_brief` writes whichever it is under its
own key, so `seen.json` never holds an empty `about` that a later count would
read as a description of nothing. A failed describing call costs me the
sentence; it never costs me the item, and the digest says how many were lost
rather than printing a line short and looking like a model with nothing to say.

Both paths are exercised: a broken reply comes back as
`failed="ValueError: the judge replied with no JSON object: …"` with `about`
empty, and the item still prints.

### Two corrections to this record's own numbers

**The describing call is made only for the items that reach the digest.** This
record costed it per judged item, which was the pessimistic reading. The
description exists to be read, and an item that is never shown is never
described — five to ten calls on an ordinary morning against up to fifty
judgements. The latency warning above is correspondingly smaller: the morning
does not double, it gains a handful of short calls at the end.

**And the per-call estimate was low again.** Predicted about 120 input and 45
output tokens, roughly $0.00035. Measured live: **342 in, 58 out, $0.000632** —
**1.8x** the estimate. The system prompt is 200 tokens, not the 60 I had in
mind.

That is the **third** optimistic estimate of this work, all in the same
direction: the token cap (1.46x headroom where 2x was claimed), the three
clauses (9% cost saving where 23% was claimed), and now this. The bias is
recorded in 0001 and it has not improved by being recorded, which is worth
knowing too — naming a bias is not correcting it, and the only thing that has
actually caught any of these is measuring afterwards.

**The morning's bill, with both corrections applied.** Fifty judged and eight
shown: 50 x $0.000663 + 8 x $0.000632 = **$0.0382**, against $0.0334 for the
old single-call digest. **Up 15%**, not the 52% a per-item reading of this
record would have predicted.
