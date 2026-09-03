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
$ uv run digline run     --suite suite.py            # ~$0.014, 21 cases x 5 samples
$ uv run digline compare --suite suite.py --run latest --locale en
$ uv run digline promote --suite suite.py --run latest   # only if the change is one you want
```

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
which swaps the provider for `fake.py`. No key, no network, no spend, and a
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
understated the cost by a factor of 384 with the tests green.

## What is where

```
brief.py            the digest: fetch, judge, print, ask, remember
prompts/judge.txt   the system prompt — the taste being encoded
prompts/item.txt    the user prompt, one item, rendered by app and suite alike
suite.py            the suite: assertions, thresholds, cases
cases/brief.json    21 cases with my own marks as the expected answer
make_cases.py       seen.json -> cases/brief.json
fake.py             the provider, faked, for CI
probe.py            one real call, printed field by field — how the fake stays honest
report.html         one comparison, rendered — the one of 2026-08-27
seen.example.json   ten records, standing in for the seen.json that is not here
.digline/           the committed baseline (runs are ephemeral and ignored)
```

A note on reading the data: `prompts/judge.txt` asks for the reason in Italian,
because I read it in Italian over coffee. That is why the reasons in
`seen.example.json` and in the baseline are Italian. Everything else here is not.

## License

Apache-2.0.
