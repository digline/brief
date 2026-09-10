# Notes for digline — not part of this repo, not committed

Two things that came out of building the 2026-09-03 fixture in `brief`. Both
belonged upstream in digline, not here.

**Both have since been acted on**, in digline 0.7.0 (ADR 0009, boundary
semantics). What follows is kept as it was written, with a dated note at the
head of each: the point of the file is what the fixture showed, and an
argument that was answered is worth more read than rewritten.

## 1. The edge semantics are not uniform, and are undocumented

> **Resolved in digline 0.7.0 — 2026-09-10.** ADR 0009 **unified** the bounds
> rather than documenting them: every limit in digline is now compared at
> `FLOAT_PRECISION`, and every limit is **inclusive**. So the third row below
> is no longer true — a drop of exactly the declared tolerance is `unchanged`,
> and the natural reading of "tolerance 1/21" is now the correct one.
>
> **My weak preference was overtaken, and I think rightly.** I argued for
> documenting over unifying, on the grounds that the exclusive `tolerance` is
> defensible on its own terms and that changing it would silently re-classify
> stored comparisons. The second half turned out to be the weaker worry than it
> sounded: ADR 0009 §8 keeps `SCHEMA_VERSION` at 9, re-promotes nothing, and
> checked the one recorded outcome that moves against these very fixtures. On
> the 2026-09-01 pair `accuracy` still reads `unchanged`; what changed is which
> control says so — `within_noise` went `true` → `false`, and the reason now
> names the declared tolerance instead of the measured floor. Verified here on
> 0.8.1: `digline explain` says *"inside the tolerance the suite declares"*.
>
> The last line of this section — whether the noise floor's edge was inclusive
> by intent or by an incidental `>=` — is answered by the same ADR. It is one
> rule now, stated once, and `digline.core` exports `meets`, `within`,
> `at_precision` and `STORAGE_STEP` so an assertion of my own compares the way
> the built-in ones do.

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

> **Acted on in digline 0.7.0 — 2026-09-10.** Both runs of the 2026-09-01 pair
> are now in digline's own tree at `tests/fixtures/brief/`, and the
> 0.600000-against-0.600000 case is the worked example in `docs/api.md`'s
> boundary section. ADR 0009 §8 states the red line in the same terms this
> section asked for — "a change that makes `12-29-17` read *got worse* at the
> aggregate again is a change that undoes ADR 0006" — and pins the files by
> SHA-256 so the fixtures cannot drift under the rule they anchor.
>
> `docs/api.md` links this repository's `fixtures/README.md` at `c9d86ff`, a
> pinned permalink, so edits here do not move what the docs cite.

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
