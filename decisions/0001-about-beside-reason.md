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

**`economics` may come back.** Its item is the single word *Economics*, and it
is suspended in `reason.py` because a sentence about an empty item makes no
claims. But `about` for that item — *"un articolo intitolato Economics, senza
sommario"* — is a claim, it is decomposable, and the item supports it. The
suspension is re-tested rather than kept out of habit.

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
