# 0001 — `about` beside `reason`

- Status: **superseded in its implementation by
  [0002](0002-the-describing-call.md)**, 2026-09-23. The premise stands — the
  sentence mixes description with judgement and only the first is checkable —
  and the single-call implementation of it is refuted below, twice, by
  measurement. Read this record for how that was found; read 0002 for what
  replaces it
- Status was: **proposed** — the text first, checkpointed before any code, the
  way digline's own records are written
- Date: 2026-09-22
- Prescribed by: [Handbook chapter 0](https://digline.dev/handbook/00-before-the-prompt/),
  decision 1, *"Emit the decision, not only the prose"*
- Moves: `prompts/judge.txt`, `brief.py`, `fake.py`, and the baselines of
  **both** suites
- Does not move: `cases/brief.json`, `make_cases.py`, `seen.json`'s existing
  fields, the marks that are the ground truth

## The problem, stated once

`prompts/judge.txt` asks one sentence to do two jobs. It asks the model to say
what the item **is** and whether it **deserves the morning**, and it asks for
both in the same field:

> Respond with ONLY a JSON object: `{"reason": "<one concise sentence in
> Italian>", "score": <int 1-5>}`

What comes back is reliably of the form *"Ricerca Anthropic su misalignment
negli agenti, ma carente di profondità tecnica"*. The first half is a claim the
item supports or does not. **The second half is not a claim about the article at
all** — it is a judgement about whether the article is worth reading, and no
amount of reading the title and summary can support or refute it.

`reason.py` asks a claim judge to decompose that sentence. It can only do one of
two things with the second half, and it does both: count it as an unsupported
claim, which depresses the score for a reason unrelated to truth, or decline to
count it, which is `error`. Measured on live runs at digline 0.18, it declines
**8–10.5%** of judgements, and at least one case per run tips past
`min_agreement` and the run cannot be promoted. The suite reads and does not
gate.

That is not a bad case or a bad threshold. It is the question being unanswerable
as posed.

## The decision

**Split the field.** The judge returns three things instead of two:

```json
{"about": "<what the item is, from the title and summary alone>",
 "reason": "<why it does or does not deserve the time>",
 "score": <int 1-5>}
```

`about` describes and can be checked against the item. `reason` judges and
cannot be checked against anything the model was given. `Faithfulness` runs on
`about` **alone**.

This is chapter 0's first decision applied to a system that is one of the ones
the chapter was written from: *"a system that returns the ids it chose, in
order, beside the sentence it wrote can be asserted on mechanically, and one
that returns only the sentence cannot, whatever you bolt on later."* Here there
are no ids to return — brief scores rather than selects — but the shape is the
same one: emit the part that can be checked as its own field, rather than
leaving it embedded in prose that cannot.

**`reason` stays unchecked by faithfulness, and that is correct.** Grading a
judgement against the item is a category error. If the judgement is ever to be
checked it is against the *taste* in `prompts/judge.txt`, by a rubric, and that
is a different suite that does not exist and is not proposed here.

## What it predicts

Written down before the run, so the run can contradict it:

1. **Abstention goes to roughly zero.** A purely descriptive sentence is
   decomposable, so the judge has no reason to decline. If it still declines,
   the split did not work and the prompt is leaking judgement into `about`.
2. **The faithfulness score rises a lot.** The current 0.725 is depressed by
   evaluative clauses counted unsupported. Expect the high 0.8s or 0.9s.
3. **Therefore the threshold must be re-measured, not carried over.** `0.35`
   was set under the old distribution and would be vacuous under the new one —
   a bar nothing can trip is a bar that protects nothing. It is measured from a
   full run, not from a probe off the top of the cases file, for the reason the
   guide now gives.
4. **The suite becomes promotable**, which is the whole point.

## What it risks, and what must be measured rather than assumed

**The score may move, and the score is what the morning depends on.** `suite.py`
gates whether the model still agrees with my marks. Asking the model to state
what the item is *before* judging it is a change to how it reasons, not only to
what it returns, and it may make agreement better or worse. This is the real
cost of the change and it is why `suite.py` re-baselines: the movement has to be
read and accepted, not promoted through.

**`about` may leak judgement.** *"Interessante analisi di…"* is a description
with a verdict inside it. The prompt has to be explicit, and the first run's
abstention rate is the measurement that says whether it worked.

**The reply gets longer and `JUDGE_MAX_TOKENS` is 200.** Three fields, two of
them Italian sentences. A reply cut off at the cap is a parse failure, which the
digest turns into `score=0` and the suite turns into `error`. Measured on the
last live run there is room — **60 output tokens per reply against a cap of
200** — so a second sentence should fit twice over. That is a reason to expect
it to work, not a reason to skip the check: the cap is verified against a real
reply before anything downstream is believed.

> **Measured 2026-09-22, and the prediction was wrong in the direction that
> matters.** `probe.py` against a real item returned **137 output tokens**, not
> the ~120 "twice over" implied: the headroom was **1.46x, not 2x**. A longer
> title or a denser summary crosses 200, and what is on the other side of that
> line is `score=0` on an item the digest would otherwise have shown me. So the
> cap is raised to **400** — output tokens are billed as generated, so a cap
> that is never reached costs nothing — and it is now declared once, in
> `brief.py`, with `suite.py` and `probe.py` importing it. They each kept their
> own `200`, which is the drift `probe.py`'s own docstring warns about for the
> prompt and had quietly acquired for the cap.

**`economics` may come back**, and it gets a prediction of its own, written
here before it is re-tested. It was the headline case of digline's ADR 0024 §1
twice over — the 1.000 range on 0.15.1 and the 11-of-15 decline on 0.18 — so a
third reading of it owes the same discipline as the first two.

Its item is `{source: "Anthropic Research", title: "Economics", summary:
"Economics"}`. The prediction:

- **Judgeable: yes.** A description of a degenerate item is still a description.
  `about` for it has real claims in it — who published it, what it is called —
  and a claim judge can decompose those. Expect **0 abstentions of 5**, against
  11 of 15 on the old field.
- **Score: 0.6 or better**, and most likely 0.67 to 1.0. Source and title are
  both stated in the context verbatim, so they are supported claims; the only
  place a point can be lost is the third clause.
- **The named failure mode is that third clause.** If the model writes *"senza
  sommario"* — without a summary — that is the one thing in the sentence the
  item **contradicts**: there is a `Summary:` line and it says `Economics`. A
  faithful `about` has to say the summary is uninformative, not that it is
  absent. If the score lands at 0.5 or 0.67 this is almost certainly why, and
  the fix is in `prompts/judge.txt`, not in the band.

**What would falsify the whole decision, not just this case:** if `about` for
`economics` still draws an abstention. That would mean the judge declines
because the *item* is degenerate rather than because the *sentence* is
evaluative — and the diagnosis in this record, that the field was doing two
jobs, would be the wrong diagnosis. The suspension would stand, but on grounds
this record does not currently claim, and the text would need amending.

## Both suites re-baseline, and why

| | what moves | why |
|---|---|---|
| `brief-judge` | `config_hash` | `JsonSchema` gains a required `about`, and the schema is part of the assertion's identity — measured: `98fc65b1e49e930e` → `61333b9d823c1ed7` |
| `brief-judge` | the answers | `prompts/judge.txt` changed, so the run's artifacts differ and the scores move |
| the faithfulness suite | everything | it reads a different field, against a re-measured threshold |

Neither baseline is promoted until its movement has been read. `digline compare`
will say the suite changed and the files under test changed; that is the
comparison worth looking at, and it is the experiment.

## The name of the second suite

`reason.py` declares the suite `brief-reason`, and after this it checks `about`.
Two options, and the recommendation is the second:

- **Keep `brief-reason`.** Continuous history, and a name that says the wrong
  thing for as long as the file exists.
- **Rename to `brief-about`.** The baseline is invalid anyway — the check reads
  a different field against a different threshold — so the history it would
  preserve is history of a different measurement. A fresh name and a fresh
  baseline cost nothing that was worth keeping, and `.digline/alessandro/
  baselines/brief-reason.json` is deleted in the same commit rather than left to
  be found by someone who thinks it is current.

## Order of work

1. This text. **Checkpoint.**
2. `prompts/judge.txt`, `brief.py`, `fake.py` — the digest change. Verify the
   token cap against one real reply before going further.
3. Run `suite.py` live. Read the score movement. Promote only if it is
   acceptable; if the agreement got worse, this decision is wrong and the text
   is amended rather than the threshold.
4. Point the faithfulness suite at `about`, measure the distribution from the
   full run, set the threshold under it, re-promote.
5. Re-test the `economics` suspension and lift it if it is judgeable.
6. Update `README.md`, which currently describes the two-field reply.

Estimated spend: about **$0.30 per full cycle** of steps 3 and 4 together, and
the honest figure is two or three cycles, so **$0.60–$0.90**.

## What this does not do

**No rubric over `reason`.** It is left unchecked, deliberately, and this record
is the only place that says so out loud.

**No change to the marks.** `cases/brief.json` and the `marked` field in
`seen.json` are untouched: the ground truth is what I answered, and nothing here
re-interprets it.

**No fix for the replay bound.** `--judge-samples` still reports a floor
(digline ADR 0024 §5.6), and a cleaner `about` does not change that — it is a
property of replaying answers you already have.


## Step 3, measured (2026-09-22)

Four live runs on the split prompt, `config_hash 61333b9d823c1ed7`. Read first,
argued second.

### Agreement: flat, and the apparent gain is a denominator

| run | accuracy | precision | errored cases |
|---|---|---|---|
| baseline (old prompt) | 0.761905 = 16/21 | 0.666667 = 10/15 | — |
| 14-00-40 | 0.714286 = 15/21 | 0.666667 = 8/12 | 0 |
| 14-11-23 | 0.761905 = 16/21 | 0.727273 = 8/11 | 0 |
| 14-14-39 | 0.800000 = **16/20** | 0.727273 | 1 |
| 14-17-50 | 0.800000 = **16/20** | 0.800000 | 1 |

The median reads +0.019 accuracy and +0.061 precision, and **that reading is
wrong.** The two best runs are the two with an unjudgeable case, and their
denominator is 20 rather than 21. On the numerator, which is what can be
compared: **15, 16, 16, 16 against the baseline's 16.** Accuracy is flat.

On the two runs that are like-for-like — no errors, denominator 21 — precision
is 0.667 and 0.727 against a baseline 0.667, so precision is flat to slightly
better. That is the honest summary: **the split did not cost agreement and did
not clearly buy any.**

### The flips: one repeats, one was a coin, and the gain repeats too

| case | baseline | four runs | below 0.5 |
|---|---|---|---|
| `frontier-red-teampatterns` | 0.80 | 0.20, 0.20, 0.00, 0.20 | **4/4 — repeats** |
| `how-we-built-auto-mode` | 0.60 | 0.40, 0.60, 0.80, 0.80 | 1/4 — noise |
| `alignment…whyne` | 0.40 | 1.00, 0.80, 0.80, 1.00 | **0/4 — the gain repeats** |

So one real regression, one real improvement, one coin — which is exactly why
the house does not decide on one run.

### Where the 1.77x went, and it is not `about`

| | old | new | |
|---|---|---|---|
| `about` | — | **152.6 chars** mean | |
| `reason` | 153.0 chars mean | **212.1 chars** mean | **1.39x** |
| input/call | 366.5 tok | 558.5 tok | 1.52x |
| output/call | 59.9 tok | 123.6 tok | 2.06x |

**`about` is proportionate.** At 152.6 chars it is almost exactly the length the
single `reason` used to be (153.0) — one sentence, as asked. The suspicion that
the prompt was asking for an essay where it wanted a clause was right in shape
and wrong in field.

**`reason` is the field that grew, by 39%,** and the cause is in the text I
wrote: *"In `reason`, judge freely"*. The old prompt asked for *one concise
sentence* and nothing else; the new one repeats "concise" in the JSON line and
then hands out a licence two paragraphs later. The model took it.

**And the input grew by my own instructions, not the model's.** `prompts/judge.txt`
went 1035 → 1805 chars, +208 estimated tokens against +192 measured per call.
Every call pays that, forever, whether or not it helps.

So the cost is two text fixes and no budget change: give `reason` its brevity
back, and say the new instructions in fewer words.

### A failure mode the split introduced

**~2% of calls now return invalid JSON.** Eight of 417 calls across the four
runs raised `JSONDecodeError`, in two runs of four, concentrated on one case
each time. It did not happen once in 415 recorded replies under the old prompt.

The mechanism is asking the model to *describe* an item: a description quotes
the thing it describes, and these feeds carry a whole category of `Quoting …`
posts and titles with quotation marks in them. An unescaped `"` inside a string
value is invalid JSON, and `digline.targets.loads_lenient` does not save it —
it is lenient about the *wrapping* (fences, a sentence before the object), not
about a broken string inside.

**Where that lands is the thing already written up at `JUDGE_MAX_TOKENS`.** In
the suite it is an honest `error`. In the digest it is caught, recorded with
`score=0`, and the item silently never appears — an absence wearing a
measurement's clothes, at roughly one item in fifty. The cap comment describes
this arriving by truncation; it is arriving by a quotation mark instead, and
more often.

The fix is one clause in the prompt — do not use double quotes inside the
values — and it belongs with the other two.


## The three clauses, applied and read (2026-09-22)

The instruction block went 885 → 677 chars: `reason` lost *"judge freely"* and
got *"One concise sentence"* back, the added prose was said in fewer words, and
one clause was added — never a double quote inside a value, quote with « ».

Read against the expectation written before the run:

| | old | split v1 | **split v2** | my estimate |
|---|---|---|---|---|
| input tok/call | 366.5 | 558.5 | **508.5** | 470 |
| output tok/call | 59.9 | 123.6 | **111.6** | 105 |
| $ per judgement | 0.000666 | 0.001176 | **0.001067** | 0.0009 |
| `about` chars | — | 152.6 | **142.5** | — |
| `reason` chars | 153.0 | 212.1 | **176.6** | 153 |

**Every number moved the right way and every one fell short of the estimate.**
Cost came down 9%, not the 23% predicted; `reason` came back to 1.15x the old
length, not 1.00x. The estimate was optimistic in the same direction as the
token-cap prediction earlier the same day — twice in one session, both times
cheaper-and-shorter than reality. That is a bias worth naming: a prediction
about my own prose is a prediction about a model's, and I keep reading my own
instructions as tighter than the model treats them.

**The JSON clause: zero errors, 105 of 105 calls, and that is not proof.** At
the ~2% rate measured over the previous four runs, a clean run of 105 happens by
luck about 12% of the time. It is the right sign and nothing more; two or three
more clean runs would settle it.

**Agreement: not read from this run, on purpose.** accuracy 15/21 and precision
7/10, both on the same denominator as the baseline, `compare` says 3 checks
worse. That is one run, and the finding of the previous round is that one run
cannot tell a regression from a coin — the case that looked like a regression
after run 1 turned out to be noise in 3 of the next 4. Reading this one would be
making the mistake the round before it just documented.


## Four v2 runs: one question settled, one answered against the decision (2026-09-23)

### The JSON clause worked

| | failed calls |
|---|---|
| v1, before the clause | 8 of 417 — **1.9%** |
| v2, after | **0 of 420** |

At the measured rate a clean 420 happens by luck with probability 3.2e-4. Settled:
*"never a double quote inside the values"* closed it. The 105-of-105 after one
run was 12% by luck and was correctly not believed.

### Agreement got worse, and the noise got worse than the agreement did

The baseline is one run, and comparing a median against one run is the mistake
this decision already documented. So: the old prompt's own distribution, 21 runs
at denominator 21, against v2's four.

| | old prompt (21 runs) | v2 (4 runs) |
|---|---|---|
| accuracy numerator | median **16**, range 14–16 | median **15**, range 13–17 |
| precision | median 0.667, range 0.600–0.667 | median 0.683, range 0.600–0.750 |
| cases whose 5 samples disagree | median **4**, range **2–6** | median **7**, range **7–8** |

**The last row is the finding.** Every one of the four v2 runs is above the
worst of nineteen old ones. There is no overlap. The old prompt returned 16/21
in eighteen of twenty-one runs — very nearly deterministic — and v2 returned
13, 15, 15, 17. Neither 13 nor 17 occurred once in twenty-one runs of the old
prompt, and both occurred in four of v2.

So the split did not shift the judge so much as loosen it. Accuracy's median is
one case lower; precision's small median gain sits inside a spread that now
straddles the old value; and the per-case disagreement, which is the thing the
tolerances were set against, is up by three cases with no overlap at all.

**That is a worse digest, and by the rule this record set for itself the text is
amended and not the threshold.**

### The amendment this points at, with a prediction

The reply is generated in the order the JSON declares it, so today the model
writes `about` first and the score is conditioned on a description it has just
invented and which varies run to run. The old prompt's prefix for the score was
`reason` alone.

**Proposal: move `about` after `score`** — `{"reason": …, "score": …, "about": …}`
— restoring the exact generation prefix the score used to have, and leaving
`about` as a post-hoc description that is still a description and still
checkable.

Predictions, before the run:

1. **Cases whose samples disagree return to the old 2–6 band**, median near 4.
   This is the one that would falsify the mechanism: if the noise stays at 7–8
   with `about` generated last, then the noise is not conditioning and the
   diagnosis is wrong.
2. **Accuracy median returns toward 16/21.**
3. **Cost is roughly unchanged** — same fields, same lengths, different order.
4. `about` may become slightly worse as a description, because it is now written
   after a judgement it can echo. That is the risk the reorder buys the
   stability with, and `reason.py` is the instrument that would see it.

Not applied. It re-baselines again, and it is a change to the digest.


## The general fact, which outlives this prompt

**Where a field sits in a JSON reply is a change to everything after it.**

A model generates the reply in the order the schema declares, token by token, so
every field is written in the context of the fields above it. The old prompt's
generation prefix for `score` was `reason` alone. Putting `about` above it added
a freshly-invented sentence — different on every sample, by construction — to
that prefix, and the score moved.

It moved **by position, not by content.** Nothing in `about` is an instruction,
an opinion or a score; it is a neutral description of the item, and the clauses
around it forbid it from judging. It still changed the judgement, because a
model conditions on what it has already written and `about` varies. Measured:
per-case sample disagreement went from a 2–6 band over nineteen runs of the old
prompt to 7–8 over four of the new one, with no overlap at all.

> ### Corrected 2026-09-23 — the evidence above does not support the claim
>
> The reorder was run, four times, with `about` written **last**, and the
> disagreement count was **[7, 7, 7, 8] — identical to [7, 7, 7, 8] with `about`
> written first.** Position changed it by nothing at all.
>
> So the sentence above is wrong where it says the score moved *by position*.
> It moved because the field was **added**, and where it sits made no difference
> to the judge's stability. Model drift is ruled out: the old prompt run on the
> same day gave 6 of 21, inside its usual band.
>
> What position **did** change, measured on the same eight runs: the reply got
> shorter when `about` moved last (111.0 → 98.8 output tokens per call) and the
> accuracy median moved 15.0 → 15.5. Both small, neither the thing that was
> claimed.
>
> The claim is therefore narrowed to what the data carries, and the narrower
> version is more useful than the one it replaces:

So the thing to carry out of this decision, for anyone adding a field to a JSON
reply a model produces:

> **Adding a field is not additive.** Asking one call for one more thing
> changes how it does everything else, and *moving the field does not undo it*.
> Measured here: the judge's per-case stability left a 2–6 band and sat at 7–8
> whether the new field was written first or last. If the existing behaviour has
> to be preserved, the new field does not belong in that reply at all — it
> belongs in a second call. Re-measure everything, and budget for it rather than
> be surprised by it.

The first version of this box said the change was positional and prescribed
putting the new field last. That was written from four runs and falsified by the
next four. It is left visible above rather than tidied away, because the
prescription it gave — *move it to the end and you are safe* — is the one a
reader would most want to believe, and the one the data refuses.

This is a fact about how these models answer, not about this prompt. It is
written here because the record already existed; it belongs anywhere someone
designs a structured reply, and Handbook chapter 0's first decision — *emit the
decision as a structure* — is the place it would do the most good, since that is
the page telling people to add exactly such a field.

## What is finished, and stays finished

**The JSON clause is settled.** *"Never use a double quote inside the values.
Quote with « » or not at all."* — 0 failed calls in 420 against 8 in 417 before
it, which is probability **3.2e-4** by luck at the measured 1.9% rate. That is
the one part of this decision that is done. **Nothing about the reorder touches
it**: the clause constrains what may appear inside a value, and moving a field
changes neither the clause nor any value it governs. If a later run shows a
parse failure, it is a new fault and not this one returning.


## The reorder, run four times: prediction 1 falsified (2026-09-23)

`{"reason": …, "score": …, "about": …}`, four runs, `config_hash` unchanged at
`61333b9d823c1ed7` so the prompt file was the only variable.

| | old prompt (21 runs) | v2, `about` first | v3, `about` last |
|---|---|---|---|
| **cases whose 5 samples disagree** | median 4, range **2–6** | **7, 7, 7, 8** | **7, 7, 7, 8** |
| accuracy numerator /21 | median 16, range 14–16 | 13, 15, 15, 17 → 15.0 | 14, 15, 16, 16 → **15.5** |
| precision | median 0.667 | 0.683 | 0.655 |
| output tok/call | 59.9 | 111.0 | **98.8** |
| $/judgement | 0.000666 | 0.001063 | 0.001022 |

**Prediction 1 was the falsifier and it is falsified.** Not "moved a little" —
*identical*, to the value. 0 of 4 runs inside the old band. Whatever pushed the
judge from a 2–6 band to 7–8 has nothing to do with where the field sits.

Model drift is ruled out: the old prompt, run on 2026-09-22 alongside all of
this, gave 6 of 21 — inside its usual band. The cause is the prompt, and it is
not the order.

Prediction 2 half-held (accuracy median 15.0 → 15.5, still under the old 16).
Prediction 3 held — cost roughly unchanged, in fact slightly down. Prediction 4
is **untested**: whether `about` written after a judgement now describes the
score instead of the item is a question only `reason.py` can answer, and it has
not been run against v3.

And the JSON clause stayed closed: 420 calls, 0 errored verdicts.

### So the decision is rethought, not reordered again

The rule this record set was that a failed reorder is rethought, and the
temptation it named was to reorder again. Taking that seriously: two reorderings
of one reply are two samples of the same idea, and the idea is refuted.

What the data says is narrower and harder than "wrong field order". **Asking one
call to judge and describe makes it a worse judge, wherever the description
sits.** The old prompt returned 16/21 in eighteen of twenty-one runs — very
nearly deterministic. Nothing that keeps both jobs in one call has come close.

**The rethink: two calls.**

- The judging call becomes **byte-identical to the old prompt** — the one whose
  behaviour is measured over twenty-one runs, whose baseline is already
  promoted, and whose `config_hash` is `98fc65b1e49e930e`. Its stability is not
  recovered by argument; it is recovered by not touching it.
- A second, short call produces `about` from the same item. It is a describing
  task with no judgement in it, so it is the thing `Faithfulness` was always
  meant to check, and it can have a prompt of four lines instead of fourteen.

Estimated cost: the judging call is $0.000666 as before; a describing call at
roughly 120 input and 45 output tokens is about $0.00035. **Around $0.00101 an
item — within a whisker of the $0.001022 the single-call v3 already costs**,
and it buys back the judge that agreed with me 16 times out of 21, eighteen runs
running.

What it costs instead: two API calls per item rather than one, so twice the
latency and twice the failure surface on a morning; and `seen.json` gains a
field written by a different call, which is a bookkeeping change. Neither is
free and both are smaller than a judge that cannot hold still.

Not applied. It is a change to `brief.py`'s call structure, not to a prompt, and
it wants its own record — 0002, with its own predictions written first.
