# 0001 — `about` beside `reason`

- Status: **proposed** — the text first, checkpointed before any code, the way
  digline's own records are written
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
