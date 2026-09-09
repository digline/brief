# Notes for digline — not part of this repo, not committed

Two things that came out of building the 2026-09-03 fixture in `brief`. Both
belong upstream in digline, not here. Nothing in the digline repo has been
touched.

## 1. The edge semantics are not uniform, and are undocumented

Three bounds decide whether a number is reported, and they do not agree on
what "on the line" means:

| bound | behaviour at the exact edge | seen in |
| --- | --- | --- |
| noise floor (aggregate vs the reference's sample band) | **inclusive** — on the edge is *within* noise, not reported | `accuracy` 0.666667 against a band of 0.666667–0.761905 |
| absolute `threshold` | **inclusive** — on the threshold passes | `precision` 0.600000 against `threshold` 0.600000 |
| declared `tolerance` | **exclusive** — a drop of exactly the tolerance *is* reported | `accuracy` falling 0.047619 against `tolerance` 0.047619, in the 2026-09-01 pair under 0.2.0 |

So two of the three are inclusive and one is exclusive, and nothing in the
docs or the report says so. Either unify them or write the rule down per
bound. My weak preference is to document rather than unify: the exclusive
`tolerance` is defensible on its own terms (a movement equal to the declared
noise is not below it), and changing it would silently re-classify stored
comparisons. But it has to be stated, because the natural reading of
"tolerance 1/21" is that a 1/21 drop is tolerated, and it is not.

Worth checking at the same time whether the noise floor's edge is inclusive by
intent or by an incidental `>=`.

## 2. A test case that sits on two lines at once

In run `2026-09-03T06-18-43-100637` (kept in `brief` at
`fixtures/2026-09-03T06-18-43-100637-00-00-98fc65b1e49e930e.json`), `precision`
scores **0.600000** with:

- an absolute `threshold` of **0.600000** — exactly on it, and passes;
- a reference noise band of **0.615385–0.666667** — below it, and is reported
  as a regression.

The same number simultaneously clears an absolute bound and violates a
relative one, in the same run, on the same check. That is the case worth
having in digline's own suite: it pins both edge behaviours at once and would
catch a change to either. The companion is `accuracy` in the same run at
0.666667, which sits exactly on the *other* kind of edge — the band's lower
bound, inclusive — and is not reported.

A regression fixture built from these two aggregates covers all three bounds
with one stored run.
