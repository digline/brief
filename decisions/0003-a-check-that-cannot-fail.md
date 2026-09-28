# 0003 — A check and a constraint that forbid the same failure

- Status: **accepted**, 2026-09-23. `brief-about` is retired
- Supersedes: nothing. [0001](0001-about-beside-reason.md) and
  [0002](0002-the-describing-call.md) stand as written — the digest keeps its
  two calls, and the reasons are unchanged
- Moves: `about.py` is deleted, its CI steps with it. `prompts/describer.txt`,
  `BriefDescriber` and the two-call morning stay exactly as they are
- Is not about: this prompt, this model, or `Faithfulness`

## The fact

**A check and a constraint that forbid the same failure make each other
redundant, and the one that runs later is the one that looks fine.**

`prompts/describer.txt` tells the describing call: *"Add no detail they do not
contain: you have not read the article."* `Faithfulness` asks a judge how much
of the output the item supports. **The constraint prevents exactly what the
check detects.**

The constraint runs first, at generation. The check runs second, over a
population the constraint has already filtered. So the check reports health the
constraint produced — and reports it as though it had measured the system.
Median 1.000 over the cases that could be scored, min 0.833. There is nothing
left in that output for a faithfulness check to find, because a sentence
constrained to state only what the item states is a near-restatement of the
item, and a near-restatement is trivially faithful.

**The instrument is not broken. It has nothing left to find.** 0002 repaired the
defect `Faithfulness` existed to catch, and did so in the prompt, where repairs
belong. The check survived the repair and kept running, and a check that keeps
running after its failure mode has been designed out is not a weak check. It is
a green light wired to nothing.

### The portable test

> **Can you state a failure the check would catch that the constraint permits?**

If not, the check is measuring the constraint. That question takes a minute and
it is the one neither 0001 nor 0002 asked, through twelve runs and $1.36.

This is not about prompts or judges. Any validation placed after something that
enforces the same property is in the same position: a schema check after a
serializer that cannot emit the wrong shape, a range assertion after a clamp, a
null check after a constructor that refuses null. The pattern is invisible
because everything is green, and green is what it is supposed to look like.

It is also the survivorship shape again, for the third time in two days — the
denominator, the probe off the head of the file, and now this. Each one is a
measurement taken over a population that something upstream had already
selected. This repository has now found it in the arithmetic, in the sampling
and in the design.

## What would have to be true for a faithfulness check to earn its place here

Three ways it could, and all three fail.

**1. The constraint would have to come out.** If `describer.txt` did not forbid
invention, the check would be measuring something real. But then the digest
ships a describer that invents, and I read inventions over coffee. That is
degrading the product to keep the instrument employed, and it is refused on
sight.

**2. The check would have to catch something the constraint cannot express.**
Measured, and it does not: median 1.000. The residual movement is the judge's
own, not the describer's — the same instrument noise ADR 0024 §1 has two
readings of.

**3. It would have to guard against drift** — prompts are files, models move,
and a check that is green today might catch tomorrow's rot. **This is the real
argument and it is the one this whole repository is built on.** It fails here on
two specific grounds:

- **A check that has never fired has unmeasured sensitivity.** I know it is
  green. I do not know it would go red, because nothing has ever made it. The
  suite that measures the score has twenty-one runs of evidence that it moves
  when the system moves; this one has none.
- **It cannot gate.** Eleven of twenty-two cases error on the run that measured
  it. A regression detector that exits 2 every morning is not a regression
  detector, and the fix for the abstentions — putting the taste back in the
  context — is the fix that makes the measurement dishonest
  (`digline` ADR 0004 §7.9b).

So the honest answer is that nothing would, and **`brief-about` is retired**
rather than kept as a suite that cannot fail.

## What replaces it, and the sting in the answer

If anything watches the describing call, it should watch **the constraint
holding**, not the outcome the constraint guarantees. The thing that would
actually rot is not *"is the description faithful"* — the prompt handles that —
but *"is the describer still describing"*: has it started judging again, which
is the exact property the two-call split was built to get.

That check is deterministic, or near enough: evaluative language is a detectable
class, and so is overlap with the judge's own `reason`. It is cheap, it runs on
every case, and it fails when the thing it watches fails.

**And it would be `KIND = "deterministic"`, which puts this repository back
where it started: no judged check at all.** That is worth saying plainly instead
of leaving it for someone to notice. The two-day search for a check where a
model produces the verdict ends with the finding that the one place brief had
for it was a place that did not need it.

**What survives is not nothing.** Exercising it produced the first empirical
demonstration of ADR 0024 §1's pairing and then a second across an instrument
change, the bound on what a replay can measure (§5.6), the context finding
(ADR 0004 §7.9b), the denominator trap and the variant trap in `guide.md` §6,
the probe-is-not-a-sample rule in §5, and the positional fact in 0001. Every one
of those outlives the suite that produced them. **`brief-about` was scaffolding,
and scaffolding comes down when the thing it was holding up can stand.**

## What is not retired

The **two-call digest stays**, and 0002's reasoning is untouched by this. The
split was justified on the judge's stability — 16, 16, 16, 16 against a
single-call 13, 15, 15, 17 — and that measurement stands whether or not anything
checks the description afterwards.

The **description stays** because I read it. Its value was always to the reader
and never to the suite; it is the suite that turned out to be the part with no
audience.

`suite.py` is untouched, at `98fc65b1e49e930e`, with its baseline promoted and
its twenty-one runs of evidence.
