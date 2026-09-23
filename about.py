"""The describing call, measured against the item it was given.

`suite.py` measures the score — does the model still agree with me about what
deserves my morning. This measures the sentence I read under the title, which is
what decides whether I open the article.

**It was a field of the judge's reply and it is now a call of its own.** That is
decision 0002, and it was not tidiness: a call asked to judge *and* describe was
measurably a worse judge, wherever the description sat in the reply, and twelve
runs were spent establishing it. `decisions/0002-the-describing-call.md` is the
account.

The model writes it from the source, the title and the summary. **It has not
read the piece.** So a sentence that names a benchmark, a comparison or a
conclusion the summary never mentions is not a florid answer — it is a decision
I took on something that does not exist. Until this file, the only thing
checked about that sentence was that it was not empty (`JsonSchema`'s
`minLength: 1` in `suite.py`).

The check is `Faithfulness` and not `LlmRubric` on purpose: it needs no label I
would have to invent. The ground truth is the item itself, which is already in
`cases/brief.json` because the digest recorded it. The judge is asked to
decompose the sentence into claims and count how many of them the item
supports; the core does the division.

The suite is separate from `suite.py` because it measures a different call. It
used to be separate because one target could not return two shapes, which was
true and turned out to be the smaller reason.

`BRIEF_FAKE_JUDGE=1` swaps both providers for `fake.py`, as in `suite.py`. It
measures the wiring and not the judge — see the note there.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from digline.core import Faithfulness
from digline.run import Calibration, Case, Suite
from digline.targets import PromptTemplate
from digline_anthropic import AnthropicClaimJudge, AnthropicTarget

import fake
from brief import DESCRIBER_MAX_TOKENS, DESCRIBER_SYSTEM, JUDGE_PREFILL, MODEL

HERE = Path(__file__).parent
FAKE = os.environ.get("BRIEF_FAKE_JUDGE") == "1"

#: The same template the digest and `suite.py` render, read here a third time
#: for the one thing neither of them needs: the item as text, to hand the judge
#: as the context the sentence has to be faithful to.
ITEM = PromptTemplate(HERE / "prompts" / "item.txt")


class DescribeTarget(AnthropicTarget):
    """`brief.BriefDescriber`'s call, as the suite makes it.

    Same `prompts/describer.txt`, same `prompts/item.txt`, same model, same cap,
    same prefill — the application's second call, reproduced here so the two
    cannot drift.

    It raises on malformed JSON where the application returns a stated failure:
    in the digest a broken description must cost the sentence and not the item,
    here it must become an `error`. A missing `about` key raises too rather than
    yielding `""` — the empty description this suite gates on is one the model
    actually wrote, not one a parser invented out of a `KeyError`.
    """

    def parse(self, text: str) -> str:
        return str(json.loads(text)["about"])


target = DescribeTarget(
    prompt_file=HERE / "prompts" / "item.txt",
    system_file=HERE / "prompts" / "describer.txt",
    model=MODEL,
    max_tokens=DESCRIBER_MAX_TOKENS,
    prefill=JUDGE_PREFILL,
    client=fake.FakeDescriberAnthropic() if FAKE else None,
)

#: The instrument. `AnthropicClaimJudge` and not `AnthropicJudge`: the second
#: is the rubric grader that answers a float, and `Faithfulness` needs the
#: `ClaimJudge` protocol — two counts, so that arithmetic can contradict them.
#:
#: Haiku judging Haiku, deliberately. A small model is the one you can afford
#: to call five times per case, and the question asked here is not the question
#: under test: the target is asked to rate an article, the judge is asked which
#: words in a sentence the item beneath it supports. The second is the easier
#: job, and it is not the one the target was tuned for.
judge = AnthropicClaimJudge(
    model=MODEL,
    client=fake.FakeClaimAnthropic() if FAKE else None,
)


#: `economics` was suspended here under 0001, when the sentence being checked
#: was a *judgement* of an item with no content and the judge declined to count
#: claims in it 11 times of 15. 0002 changes the sentence: it is now a
#: *description* of that item, written by a call that was never asked to judge,
#: and a description of a one-word item still makes claims — who published it,
#: what it is called, that the summary says nothing.
#:
#: So the suspension is lifted and the prediction is in
#: `decisions/0002-the-describing-call.md`, written before this run: 0
#: abstentions of 5 and a score at or above 0.6. If it abstains again, the
#: suspension comes back and 0001's diagnosis has failed at the last case that
#: can test it.
UNJUDGEABLE: dict[str, str] = {}

cases = [
    Case(
        id=c["id"],
        vars=c["vars"],
        suspended=UNJUDGEABLE.get(c["id"]),
        # **The item alone, and this is the second time this line has moved.**
        # 0001 passed the item, found every "rilevante per ..." clause
        # unsupported by construction, and corrected the context to *both*
        # prompt files, because the model had been given the taste and a context
        # without it was marking it down for knowing what I asked it to know.
        #
        # 0002 reverses that correction, for the reason that made it: the
        # describing call is never shown `prompts/judge.txt`. It does not know
        # what I like, so there is no taste to be faithful to, and the item is
        # the honest whole of what it was given. The context is what the model
        # saw — that rule never changed; what it points at did.
        context=[ITEM.render(c["vars"], case_id=c["id"])],
        metadata=c["metadata"],
        # No `expected`: `Faithfulness` compares the sentence with the item, not
        # with an answer of mine. And no `label`, because there is no run
        # assertion here to count a confusion matrix — I have never sat down and
        # marked 21 sentences faithful or not, and a label I invented this
        # afternoon would be ground truth with no ground under it.
    )
    for c in json.loads((HERE / "cases" / "brief.json").read_text(encoding="utf-8"))
]

# --- The calibration case ------------------------------------------------------
#
# The canary watches whether the model is still that model; this watches whether
# the scale is still a scale. A judge that has gone binary is *more* repeatable,
# not less, so no amount of repetition sees the collapse — and `--judge-samples`
# says so itself, in the sentence it prints when a suite declares none.
#
# The item is declared here rather than borrowed from `cases/brief.json`, and
# the point is that `make_cases.py` rewrites that file from `seen.json` whenever
# I answer the digest. A control instrument that could be rebuilt out from under
# itself by an ordinary morning is not a control instrument.
CALIBRATION_VARS = {
    "source": "Anthropic Engineering",
    "title": "Quantifying infrastructure noise in agentic coding evals",
    "summary": (
        "Infrastructure configuration can swing agentic coding benchmarks by "
        "several percentage points—sometimes more than the leaderboard gap "
        "between top models."
    ),
}
CALIBRATION_ITEM = ITEM.render(CALIBRATION_VARS)

#: Two claims, and I know which is which. The first is the summary's own
#: sentence back in Italian; the second — a containerised execution protocol
#: that zeroes the measured variance — is not in the item, not in the taste, and
#: not anywhere. A judge that still has a scale puts this in the middle.
#:
#: Measured five times before it was declared: 0.500 every time, 1 claim of 2,
#: and five reasons that all named the containerised protocol as the unsupported
#: one. That stability is worth saying out loud next to the noise in the real
#: cases — the judge is not flaky, the *real sentences* are ambiguous to
#: decompose. "Rilevante per RAG in produzione" is one claim or two depending on
#: the reading, and that is where the wobble comes from. Here there is nothing
#: to be ambiguous about, and the judge does not wobble.
CALIBRATION_ANSWER = (
    "Misura di quanto la configurazione dell'infrastruttura sposti i benchmark "
    "di coding agentico, e propone un protocollo di esecuzione containerizzato "
    "che azzera la varianza misurata."
)

cases.append(
    Case(
        id="calibration-half-supported",
        vars=CALIBRATION_VARS,
        # The item alone here too, for the reason above.
        context=[CALIBRATION_ITEM],
        calibration=Calibration(
            output=CALIBRATION_ANSWER,
            check="faithfulness",
            # Measured 0.500 and dead stable, so the band is not built around
            # noise that is not there — it is built around the noise the *real*
            # cases show. One judgement of five landing at an extreme folds to
            # 0.4 or 0.6 and is inside; two fold to 0.3 or 0.7 and are still
            # inside, inclusive; three are outside. `suite.py`'s reading of its
            # own five samples — two wobbling is noise, three is a change —
            # applied to the instrument instead of to the system.
            #
            # Both ends strictly inside (0, 1) because digline refuses anything
            # else, and it is right to: a band containing an extreme counts a
            # judge that has collapsed onto that extreme as in band, so it could
            # not detect the one thing it exists for.
            low=0.30,
            high=0.70,
            # Mandatory, and digline refuses the case without it: `Faithfulness`
            # puts the question in front of the judge beside the answer on every
            # real case, and the target that would render it is never called for
            # a calibration case. Graded blind, this would measure a different
            # question than the cases it is the control for.
            input=CALIBRATION_ITEM,
        ),
    )
)


suite = Suite(
    tenant="alessandro",
    environment="dev",
    name="brief-about",
    assertions=[
        # An empty reason **errors** here, and that is correct, not a gap to be
        # closed later. `Faithfulness` asks the judge for two counts and divides
        # `supported` by `total`; with no claims there is no fraction, and 0/0
        # is not 0. Scoring a blank sentence 0.0 would be arithmetic nobody
        # performed, and scoring it 1.0 would reward saying nothing.
        #
        # So: the first exit 2 on this suite with the reason "the judge found no
        # claims in the output" is a blank or contentless sentence from the
        # model. It is recognised, not debugged. `digline explain` will name the
        # case. The fix is in `prompts/judge.txt`, never here.
        #
        # No `CostBudget`. The call this suite makes is `suite.py`'s call, and
        # its price is already gated there at $0.0015; a second budget over the
        # same number would be two gates on one fact, failing twice or passing
        # twice and never disagreeing usefully.
        #
        # What that leaves ungated is the judge's own spend, and since digline
        # 0.16.0 the run at least *states* it: `Run.usage` carries two lines,
        # `target` and `judge`, and the command prints both when it finishes.
        # Measured on this suite, one run is **$0.070135 of target and
        # $0.134599 of judge** — the judge is 1.92x the target and 66% of the
        # bill. `CostBudget` reads `Response.cost_usd`, which is the target's,
        # so the gated third is the smaller one. Nothing digline ships gates the
        # larger, deliberately (ADR 0025 §6); it is a fact on the document, not
        # a check, and this comment is the only place in this repository that
        # says which part of the bill the green `cost_budget` in `suite.py`
        # actually covers.
        Faithfulness(
            judge=judge,
            # Measured, not wished for — the house rule from `suite.py`: the
            # bar sits a little below where the system is, because the gate
            # protects against getting worse and raising it is a change you can
            # see in `config_hash`.
            #
            # The first run measured: mean 0.725 across the 21 cases, median
            # 0.733, best 0.933, worst 0.300. The bar goes under the pack and
            # over the floor.
            #
            # It is not 0.9, and that is structural rather than a failing of the
            # model. `prompts/judge.txt` asks for a sentence that *judges*, so
            # part of every reason is characterisation — "approfondimento
            # tecnico", "manca sostanza" — and a characterisation is a claim
            # neither prompt states. The judge counts it unsupported and is
            # right to. A suite that demanded 0.9 here would be demanding the
            # model stop answering the question it was asked.
            #
            # One case is under the bar and stays under it: the baseline records
            # `controlling-reasoning-effort-in-llms` at 0.300, where the item
            # says only that LLMs learn low-, medium- and high-effort reasoning
            # modes and the sentence keeps promising cost and latency
            # optimisation for RAG and agents in production. That is the failure
            # this file was written for, sitting in the reference with its name
            # on it — not a bar tuned until it disappeared.
            threshold=0.35,
            # Measured off the same run rather than chosen: the standard error
            # of the five-sample mean is 0.098 for a typical case, so 0.20 is
            # two sigma — a case that moves further than this moved for a reason
            # other than the judge counting claims differently today.
            #
            # Then measured a second way, which is the number to worry about.
            # `rejudge` put the same 105 recorded answers past the judge again:
            # the per-case score moved by 0.073 on average and by 0.200 at the
            # most — `economics`, exactly on this line. Nothing crossed it, in
            # that replay or in the live run after it, but one case sitting on
            # the boundary is where the first false regression will come from.
            #
            # The tolerance is left where it is anyway, because widening it is
            # the wrong repair. `--judge-samples` says why: on a *fixed* answer
            # three judgements of `economics` ranged over the whole scale, 0.0
            # to 1.0, and thirteen of the 21 cases ranged 0.5 or more. That is
            # not a flaky judge — the calibration case proves the scale is
            # intact — it is `total` being the judge's own decision on sentences
            # that are genuinely ambiguous to decompose: "rilevante per RAG in
            # produzione" is one claim or two depending on the reading. The
            # answer to noise at the source is `Repeated` around this check,
            # which is what `Faithfulness`'s own docstring prescribes and what
            # `Suite.samples` explicitly is not. It triples the judging, so it
            # is a decision to take when a case actually chatters, not before.
            tolerance=0.20,
        ),
    ],
    cases=cases,
    samples=5,
    min_agreement="3/5",
    # Ruling: on, and the run it produces is the first of this repository that
    # can ever be re-judged. The eighteen stored runs of `brief-judge` cannot —
    # recording is opt-in and was off, so they hold verdicts and no answers, and
    # a run already produced cannot gain answers nobody kept. What this unlocks
    # is `digline rejudge`: the judge, the threshold and the rubric can be
    # changed and re-measured over answers that do not move, for the price of
    # the judging alone and no call to the target.
    record_responses=True,
)
