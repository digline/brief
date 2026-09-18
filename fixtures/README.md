# fixtures

Runs of `brief-judge`, copied out of `.digline/alessandro/runs/`, which is
gitignored (`*/runs/`). They are here because they are worth keeping and that
directory is not: the pair and the triple two sections down are the fixtures
ADR 0006 and ADR 0009 were written from, and all six are what the numbers on
<https://digline.dev/why/> are read out of. `recompute.py` prints those numbers
from the files.

## Which number comes from which run

The numbers about this project on <https://digline.dev/why/> are read out of
these files. Each is one run: run id, the `config_hash` every one of them
shares, and the value as the file has it.

| Number | Run(s) | Value | Where it is in the file |
| --- | --- | --- | --- |
| the reader-agreement of a run | `2026-09-03T06-14-13-174316` (the baseline) | `accuracy` **0.761905 = 16/21** — 10 true positives and 6 true negatives — and `precision` **0.666667 = 10/15** | `aggregate[]`, by `assertion`; `reason` spells the fraction and `metadata` the four counts |
| one verdict out of 21 changed between two runs, nothing else changed | `2026-09-01T12-29-17-700450` → `12-44-02-518586` | `2026-08-24-evals-skills-for-coding-agents` goes `[1, 1, 0, 0, 0]` → `[1, 1, 1, 1, 1]`, 2/5 then 5/5: the majority verdict flips, and no other case does | `results[].verdicts[]` where `assertion` is `agrees_with_mark`, `metadata.scores` |
| the aggregate moves by one case out of 21 while a case moves by three votes | the same pair | `accuracy` **0.714286 (15/21) → 0.761905 (16/21)**, one case; the largest movement on a case is 3 of its 5 votes | `aggregate[]` and the same `metadata.scores` |
| how many cases out of 21 are not unanimous | all six: **2** (`06-14-13`, `06-24-50`), **4** (`12-44-02`), **5** (`12-29-17`, `06-18-43`), **6** (`06-30-18`) | between **2/21 and 6/21** on runs that are replicates of each other | count the `agrees_with_mark` verdicts whose `metadata.scores` are neither all 0 nor all 1 |
| what a run costs | any of the six | **$0.0691 – $0.0699**, about seven cents | sum `metadata.total_cost_usd` over the `cost_budget` verdicts — one per case, each already the five samples of that case |

Every one of those is recomputed from the committed files alone, with no
network and no digline:

```console
$ python3 fixtures/recompute.py
2026-09-01T12-29-17  schema  8  accuracy 0.714286 (15/21)  precision 0.642857  split 5/21  $0.0691
2026-09-01T12-44-02  schema  8  accuracy 0.761905 (16/21)  precision 0.666667  split 4/21  $0.0695
2026-09-03T06-14-13  schema  9  accuracy 0.761905 (16/21)  precision 0.666667  split 2/21  $0.0694
2026-09-03T06-18-43  schema  9  accuracy 0.666667 (14/21)  precision 0.600000  split 5/21  $0.0696
2026-09-03T06-24-50  schema  9  accuracy 0.761905 (16/21)  precision 0.666667  split 2/21  $0.0697
2026-09-03T06-30-18  schema 11  accuracy 0.761905 (16/21)  precision 0.666667  split 6/21  $0.0699
```

`split` is the count of cases whose five samples disagree. The three schemas
are why the script reads `metadata.scores` rather than the verdict's `samples`:
`scores` is in all of them, `samples` arrived with schema 9.

What these files do **not** carry: the 1–5 score the judge returns. A sample is
the outcome of an assertion — 1.0 when it held — so `[1, 1, 0, 0, 0]` says
three samples disagreed with my mark, not what they scored. Keeping the raw
output per sample became possible later, and is not on in these runs.

## 2026-09-03T06-30-18: six cases out of twenty-one

```
2026-09-03T06-30-18-474632-00-00-98fc65b1e49e930e.json
```

The fourth run of that morning, twelve minutes after the triple below, same
suite, same prompts, same `config_hash`, and the one with the most cases split:
**six of twenty-one**, in both patterns, 4–1 and 3–2. It is here as the top of
the range in the table above — the bottom, 2/21, is the baseline itself. It is
**schema 11**, the store having been migrated since the others were copied out,
which is what the version differences in the `recompute.py` output are.

## The 2026-09-03 triple

Three consecutive runs within eleven minutes, from the same suite, the same
prompt files, the same cases and the same `config_hash`
(`98fc65b1e49e930e`), five samples per case. Nothing changed between them.
`06-14-13` ran at `cc76e68` and the other two at `66484d6`; what separates
those two commits is the promoted baseline and a paragraph of README — not the
suite, the cases or the prompts. The report says the same, having checked:
*the suite is unchanged from the reference, the files under test are the same
as the reference, the system under test answered under the same configuration.*

```
2026-09-03T06-14-13-174316-00-00-98fc65b1e49e930e.json
2026-09-03T06-18-43-100637-00-00-98fc65b1e49e930e.json
2026-09-03T06-24-50-578106-00-00-98fc65b1e49e930e.json
```

`06-14-13` is the current baseline, committed under
`.digline/alessandro/baselines/brief-judge.json`.

Two cases fall out of the middle run and come back, on `agrees_with_mark`:

| case | `06-14-13` | `06-18-43` | `06-24-50` |
| --- | --- | --- | --- |
| `2026-08-24-evals-skills-for-coding-agents` | `[1, 1, 1, 1, 1]` — **5/5**, 1.0 | `[0, 0, 0, 1, 1]` — **2/5**, 0.4 | `[1, 1, 1, 1, 1]` — **5/5**, 1.0 |
| `2026-08-24-more-than-just-code-review` | `[1, 1, 1, 1, 1]` — **5/5**, 1.0 | `[0, 1, 0, 1, 0]` — **2/5**, 0.4 | `[1, 1, 1, 1, 1]` — **5/5**, 1.0 |

The check passes at 0.5, so 2/5 fails and 3/5 passes: both cases land one vote
below the line and step back over it eleven minutes later. That is the thing
five samples exist to make visible rather than to hide.

## What the comparison actually reports

`compare-2026-09-03.html` is the middle run rendered against the baseline —
`digline report`, read-only, no promotion. Its headline:

```
Did it get worse? Yes
3 checks got worse compared with the reference. 1 check moved within noise.
```

The three are the two cases above and `precision`. The fourth is `accuracy`,
and it is not counted as a regression. Both aggregates fell:

| aggregate | reference `06-14-13` | its five samples | band | middle run | reported? |
| --- | --- | --- | --- | --- | --- |
| `precision` | 0.666667 | `0.666667, 0.642857, 0.666667, 0.666667, 0.615385` | 0.615385–0.666667 | **0.600000** | **yes** — below the band |
| `accuracy` | 0.761905 | `0.761905, 0.714286, 0.761905, 0.761905, 0.666667` | 0.666667–0.761905 | **0.666667** | no — on the band's lower edge |

Under digline 0.4.0, and unchanged through 0.8.1, an aggregate is judged
against the spread of the reference's own samples, not against its declared
`tolerance`. The noise floor works in both directions on this one comparison:
it absorbs a two-case drop in `accuracy` because the reference had already
produced that number once, and it reports a one-case drop in `precision`
because the reference never had. Which is the point — the same run is noisy
enough to explain the larger movement and not the smaller one, and only the
reference's own history can tell them apart.

On the declared `tolerance` alone (0.047619, one case out of twenty-one) both
would have been reported: `accuracy` fell by 0.095238 and `precision` by
0.066667. Worth noting too that `precision` in the middle run is 0.600000
against an absolute threshold of 0.600000, and passes it.

## Reading the files

These three are **schema 9**. Each verdict carries the raw samples three ways:

```json
"samples": [0.0, 0.0, 0.0, 1.0, 1.0],
"sample_min": 0.0,
"sample_max": 1.0,
"metadata": { "scores": [0.0, 0.0, 0.0, 1.0, 1.0], "agreement": 0.6, "spread": 1.0 }
```

Entries under `aggregate` carry `samples`, `sample_min` and `sample_max` too,
and that is where the bands in the table above come from.

Nothing here needs digline to read — it is plain JSON. To hand the files back
to digline 0.8.1, copy them into the run store, which is
`.digline/<tenant>/runs/<suite>/`:

```console
$ cp fixtures/2026-09-03T*.json .digline/alessandro/runs/brief-judge/
$ uv run digline list --suite suite.py
```

## The 2026-09-01 pair, kept as the original ADR 0006 fixture

```
2026-09-01T12-29-17-700450-00-00-98fc65b1e49e930e.json
2026-09-01T12-44-02-518586-00-00-98fc65b1e49e930e.json
```

Two runs fifteen minutes apart, same `config_hash`, five samples per case, in
which `2026-08-24-evals-skills-for-coding-agents` scores `[1, 1, 0, 0, 0]` —
2/5, 0.4, failing — and then `[1, 1, 1, 1, 1]` again. This is the pair the ADR
was written from, and it is kept as it was.

Two things to know before reading it. These two are **schema 8**: the five
samples live only in `metadata.scores`, there is no `samples` on the verdict,
and digline 0.8.1 needs `digline migrate` before it will load them. And the
`compare` output quoted in the earlier version of this file was produced by
**digline 0.2.0**, before the noise floor existed, when aggregates were judged
against their declared `tolerance`. It reported `accuracy` as a regression.
Under the current rules that same movement is the one the noise floor absorbs,
as the table above shows. Do not read the 0.2.0 text with today's rules; the
2026-09-03 triple is the one that reflects how the gate behaves now.

> **Since digline 0.7.0 (ADR 0009), 2026-09-10.** The declared tolerance
> absorbs this movement, not the noise floor: `within_noise` now reads
> **false** where it read true, and the reason names the tolerance the suite
> declares instead of the measured band. The sentence above describes the
> pre-0.7.0 reading and is kept for that.
>
> **The verdict a reader acts on does not move.** `accuracy` on this pair read
> `unchanged` then and reads `unchanged` now; what changed is which of the two
> controls answered first, and `compare()` checks the declared tolerance before
> the measured floor precisely so nobody has to guess. Measured on 0.8.1
> against these files: the aggregates carry `noise_samples: 0` — schema 8 kept
> no per-sample band — so there was never a floor here to do the absorbing,
> and `digline explain` says *"inside the tolerance the suite declares"*.
>
> ADR 0009 §8 owns this explanation now, and states the red line in the same
> terms: a change that makes `12-29-17` read *got worse* at the aggregate again
> is a change that undoes ADR 0006. It still reads `unchanged`.
