# fixtures

Two runs of `brief-judge`, copied out of `.digline/alessandro/runs/`, which is
gitignored (`*/runs/`). They are here because they are worth keeping and that
directory is not: the real-world case for **ADR 0006**, repeated samples and a
within-noise drop.

Both were produced fifteen minutes apart on 2026-09-01, from the same suite,
the same prompt files and the same `config_hash` (`98fc65b1e49e930e`). Nothing
changed between them. What changed is the model.

| run | `agrees_with_mark` on `evals-skills-for-coding-agents` | precision | accuracy |
| --- | --- | --- | --- |
| `12-29-17-700450` | **0.4** — samples `[1, 1, 0, 0, 0]`, agreement 0.6 | 0.642857 | 0.714286 |
| `12-44-02-518586` | **1.0** — samples `[1, 1, 1, 1, 1]`, agreement 1.0 | 0.666667 | 0.761905 |

The first one made `compare` exit 1 against a baseline measuring 0.761905:

```
2 checks got worse compared with the reference.
2026-08-24-evals-skills-for-coding-agents · agrees_with_mark · Went from passing to failing (1.000000 → 0.400000).
whole run · accuracy · Score fell from 0.761905 to 0.714286.
```

Accuracy fell by exactly 1/21 — one case out of twenty-one — which is the
`tolerance` those run assertions are declared with, so the bound is exclusive
and the drop was reported. The second run came back to the baseline's numbers
to six decimal places. One borderline item, five samples, three votes moving:
that is the thing `samples=5` and `min_agreement="3/5"` exist to make visible
rather than to hide, and the first run sits right on the `3/5` line.

Neither run is a regression. Both aggregates clear their absolute thresholds in
both runs (precision > 0.60, accuracy > 0.65). `12-44-02-518586` is the
promoted baseline; `12-29-17-700450` is kept because a gate that fires on noise
is only arguable with the noise in hand.

Also the first two runs written under schema 8: `target_config` is recorded on
both. `judge_config` is `{}` in both and correctly so — this suite has no LLM
judge, only `AnthropicTarget` and assertions that are ordinary code.
