# fixtures

Runs of `brief-judge`, copied out of `.digline/alessandro/runs/`, which is
gitignored (`*/runs/`). They are here because they are worth keeping and that
directory is not.

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

Under digline 0.4.0 an aggregate is judged against the spread of the
reference's own samples, not against its declared `tolerance`. The noise floor
works in both directions on this one comparison: it absorbs a two-case drop in
`accuracy` because the reference had already produced that number once, and it
reports a one-case drop in `precision` because the reference never had. Which
is the point — the same run is noisy enough to explain the larger movement and
not the smaller one, and only the reference's own history can tell them apart.

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
to digline 0.4.0, copy them into the run store, which is
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
and digline 0.4.0 needs `digline migrate` before it will load them. And the
`compare` output quoted in the earlier version of this file was produced by
**digline 0.2.0**, before the noise floor existed, when aggregates were judged
against their declared `tolerance`. It reported `accuracy` as a regression.
Under the current rules that same movement is the one the noise floor absorbs,
as the table above shows. Do not read the 0.2.0 text with the 0.4.0 rules; the
2026-09-03 triple is the one that reflects how the gate behaves now.
