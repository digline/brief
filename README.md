# brief

A morning digest of the AI sources I read, and the evaluation suite that keeps
it honest.

Six RSS feeds go in. Every new item gets one `claude-haiku-4-5` call that scores
it 1–5 against a taste written down in `prompts/judge.txt`, and the ones that
clear the bar get printed. Then the digest asks which of them I actually want to
read, and writes my answer next to the model's.

That last step is the whole point. My answer is ground truth, and it costs
nothing to collect because I was going to answer anyway. `make_cases.py` turns
it into `cases/brief.json`; the suite in `suite.py` replays those cases against
the same prompt files the digest uses and asks a question a diff cannot answer:

> does the model still agree with me as often as it did yesterday?

Today it agrees on 16 of 21 cases, and 10 of the 15 items it would show me are
items I wanted. Those numbers are in `.digline/alessandro/baselines/`, committed,
and everything the suite does is compare against them.

The measurement harness is [digline](https://pypi.org/project/digline/).

## Run it

```console
$ uv sync
$ export ANTHROPIC_API_KEY=...
$ uv run brief.py            # today's digest; answer the question at the end
$ uv run brief.py read       # the queue of things marked and not yet read
$ uv run brief.py stats      # what the judge has been doing, by source
```

About $0.0001 per item judged. `MAX_JUDGED_PER_RUN = 50` caps the first run,
which is the only one that meets a whole backlog at once.

**`seen.json` is not in this repository** — it is my reading history, and it is
gitignored. A fresh clone falls back to `seen.example.json`, ten real records
that show the shape of the file. The first digest you run writes the real one.

## Run the suite

```console
$ uv run digline run     --suite suite.py            # ~$0.069: 21 cases x 5 samples
$ uv run digline compare --suite suite.py --run latest --locale en
$ uv run digline promote --suite suite.py --run latest   # only if the change is one you want
```

About **$0.069** a run, because a run is 21 cases times five samples: 105
judgements at about $0.00066 each. One judgement per case would be $0.014, and
that is the number this file carried until it was read against the run files —
each case's `cost_budget` verdict records `cost_usd`, the mean of its samples,
beside `total_cost_usd`, the five of them, and the $0.014 was the means added
up. `fixtures/recompute.py` prints what a run actually cost, from the committed
runs.

`compare` answers whether it got worse; `digline explain --suite suite.py --run
latest` reads the same run back at length — what moved, by how much, and inside
or outside which measured interval — which is the one to reach for when the
answer is yes.

What it checks, per case, five samples each:

| check | what it says |
| --- | --- |
| `JsonSchema` | the answer has an integer 1–5 score and a non-empty reason |
| `AgreesWithMark` | the model says ≥ 4 exactly when I marked the item |
| `CostBudget` | one judgement still costs under $0.0015 |

And over the run as a whole, `Precision` and `Accuracy` over `agrees_with_mark`.
Precision is the number I feel every morning — how much noise is in the list I
read. Accuracy also counts the right *no*s, which the digest never shows me, so
it is the one that would notice the judge quietly going silent.

Five samples because one sample is a coin toss: `min_agreement="3/5"` means a
case passes when the majority of its samples do, and the tolerances are set so
that two votes wobbling is noise and three is a change.

The suite calls the judge through the same two files the application does —
`prompts/judge.txt` and `prompts/item.txt`, rendered by the same
`PromptTemplate` — so the two cannot drift apart. Both files are recorded in
every run, which is why the committed baseline carries the prompt that produced
it.

## The sentence

`suite.py` measures the score. Nothing measured the sentence printed under the
title, and the sentence is what decides whether I open the article.

The model writes it from the source, the title and the summary — **it has not
read the piece.** So a sentence that names a benchmark, a comparison or a
conclusion the summary never mentions is not a florid answer; it is a decision I
took on something that does not exist. Until `reason.py` the only thing checked
about it was that it was not empty.

```console
$ uv run digline run     --suite reason.py            # ~$0.19: 21 cases x 5 samples, two models each
$ uv run digline compare --suite reason.py --run latest --locale en
```

The check is `Faithfulness`, and it needs no label I would have to invent: the
ground truth is the item, which `cases/brief.json` already holds. A claim judge
is asked to decompose the sentence and count how many of its claims the item
supports; digline does the division. The context is **both** prompt files, not
just the item — the model was given the taste in `prompts/judge.txt` too, and a
context holding only the item marks every "rilevante per ..." clause unsupported
by construction. That mistake was in the first draft and cost 0.19 of mean score.

The first run measured a mean of 0.725 over the 21 cases, median 0.733, and it
is not higher because `prompts/judge.txt` asks for a sentence that *judges*: a
characterisation is a claim neither prompt states, the judge counts it
unsupported, and it is right to. The threshold is 0.35 — under the pack, over
the floor. One case sits below it and stays there:
`controlling-reasoning-effort-in-llms`, where the item says only that LLMs learn
low-, medium- and high-effort reasoning modes and the sentence keeps promising
cost and latency optimisation for RAG and agents in production. That is the
failure this suite was written for, sitting in the reference with its name on
it.

A blank reason **errors** rather than fails, and that is correct: with no claims
there is no fraction, and 0/0 is not 0. The first exit 2 reading "the judge found
no claims in the output" is a contentless sentence from the model, and the fix is
in `prompts/judge.txt`.

`reason.py` sets `record_responses=True`. It is the first suite here that does,
which makes its runs the first that can ever be re-judged — see below.

## Re-judging, and the two measurements it unlocks

Recording is opt-in and was off, so the eighteen stored runs of `brief-judge`
hold verdicts and no answers. A run already produced cannot gain answers nobody
kept, so none of them can be replayed, and none ever will be. `brief-reason`'s
runs can:

```console
$ uv run digline rejudge --suite reason.py --run latest                  # the judge alone; no call to the target
$ uv run digline rejudge --suite reason.py --run latest --judge-samples 5
```

`rejudge` re-runs the assertions over the recorded answers and writes a run that
declares where they came from, so nothing can mistake it for a measurement — and
`promote` refuses it outright. It costs the judging and not the target, which is
what makes moving a threshold or swapping a judge affordable.

`--judge-samples M` asks each judged check M times per recorded answer and
reports the judge's own range beside the calibration result. It runs only on a
replay, because on a live target the range would mix the target's variance into
the judge's. Both of these need a check whose `KIND` is `judged`, and
`Faithfulness` is the first one in this repository: `suite.py`'s
`agrees_with_mark` is declared `deterministic`, because the model there produces
the *answer* and a threshold comparison produces the *verdict*.

The third is the calibration case, declared in `reason.py` and judged on every
run with no call to the target. It is a sentence I wrote myself about a real
item, with two claims — one the summary states, one invented — so a judge that
still has a scale puts it in the middle, and its band is 0.30–0.70. The canary
watches whether the model is still that model; this watches whether the scale is
still a scale, which repetition cannot see: a judge that has gone binary is
*more* repeatable, not less. A run whose calibration case lands outside its band
cannot be promoted.

What the three of them measured, the first time they were run:

| measurement | what it said |
| --- | --- |
| `rejudge` | the same 105 answers judged again move the per-case score by 0.073 on average, 0.200 at most — and `promote` refuses the result, because its interval is the judge's wobble with the target taken out |
| `--judge-samples 3` | on a *fixed* answer the judge's range reaches **1.000**, and 13 of 21 cases range 0.5 or more |
| the calibration case | **0.500**, five times out of five, inside its band |

Read together they say something the first two could not say alone. The judge
has not lost its scale — the calibration case is dead stable in the middle of
it. The range is `total` being the judge's own decision on sentences that are
genuinely ambiguous to decompose: "rilevante per RAG in produzione" is one claim
or two depending on the reading. The five-sample fold already suppresses that
from 0.5 to 0.073, which is why the suite works at all; the repair if a case
starts chattering is `Repeated` around the check, not a wider tolerance.

## report.html

`report.html` is committed, and it is a real one: the run of 2026-08-27 that
became the baseline that day, compared against the one before it. It is kept at
that comparison on purpose and is not re-rendered on every promotion — the gate
that matters runs `digline compare` in CI, and a report of a run that moved
nothing would document nothing.

The change it measures is `SUMMARY_MAX_CHARS`, cut from 1500 to 400 — how much
of each article's opening the judge gets to read. Nobody can eyeball whether
that hurts. The report says: one case improved, none got worse, precision
0.63 → 0.67. One case out of 21 is as much noise as it is a gain, and that is
the honest reading; what it does say is that the cut cost nothing.

## The fake judge, and CI

`.github/workflows/check.yml` runs on every push with `BRIEF_FAKE_JUDGE=1`,
which swaps both providers for `fake.py` — `FakeAnthropic` for the digest's
judge, `FakeClaimAnthropic` for the instrument `reason.py` measures it with. No key, no network, no spend, and a
fork can run the checks too.

The fake proves the wiring — the suite loads, both prompts compose, the
assertions evaluate, a run and a comparison come out. It proves nothing about
the judge, so it runs against a scratch `--root` and is compared with itself:
the committed baseline came from the real model, and putting the fake's numbers
next to it would be comparing two different judges.

The real cycle runs weekly, and on demand, with a key. That is the job that can
fail: `digline compare` exits 1 when something got worse than the baseline. A
judge does not rot because someone pushed — it rots because the model behind it
moved — so the run nobody triggered is the one worth having.

`fake.py` reads the bullet lists out of `prompts/judge.txt` and scores against
them, so editing the prompt changes its answers too. A fake that answered the
same whatever you asked would make every prompt look equally good. Its `usage`
shape was copied from a real reply through `probe.py`, including
`cache_creation_input_tokens` — a field that is *not* part of `input_tokens`,
that nothing was reading, and whose absence from an earlier hand-written fake
understated the cost by a factor of 384 with the tests green. `stop_reason` and
`model` are there for the same reason: digline reads both, so a fake without
them would make the checks see a poorer record than production writes. The fake
answers `brief-fake-judge` to "what model was that", because it is not
`claude-haiku-4-5-20251001` and must not say it was.

## What is where

```
brief.py            the digest: fetch, judge, print, ask, remember
prompts/judge.txt   the system prompt — the taste being encoded
prompts/item.txt    the user prompt, one item, rendered by app and suite alike
suite.py            the score suite: does the model still agree with me
reason.py           the sentence suite: is the reason faithful to the item
cases/brief.json    21 cases with my own marks as the expected answer
make_cases.py       seen.json -> cases/brief.json
fake.py             both providers, faked, for CI — the target and the claim judge
probe.py            one real call, printed field by field — how the fake stays honest
report.html         one comparison, rendered — the one of 2026-08-27
fixtures/           runs kept out of the ignored run store, and what they show
seen.example.json   ten records, standing in for the seen.json that is not here
.digline/           the committed baseline (runs are ephemeral and ignored)
.mcp.json           digline-mcp over this repo: six read/measure tools, no promote
```

A note on reading the data: `prompts/judge.txt` asks for the reason in Italian,
because I read it in Italian over coffee. That is why the reasons in
`seen.example.json` and in the baseline are Italian. Everything else here is not.

## License

Apache-2.0.
