"""The other half of the judge's answer: the sentence, measured against the item.

`suite.py` measures the score — does the model still agree with me about what
deserves my morning. Nothing measures the sentence beside it, and the sentence
is the lever. It is what I read under the title, and it is what decides whether
I open the article.

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

The suite is separate from `suite.py` rather than a fourth assertion in it
because one target cannot return two shapes. `suite.py` needs the parsed object
— `JsonSchema` and `AgreesWithMark` read `output["score"]` — and `Faithfulness`
accepts text only. Same call, same two prompt files, same model, same price:
what differs is which half of the answer is kept.

`BRIEF_FAKE_JUDGE=1` swaps both providers for `fake.py`, as in `suite.py`. It
measures the wiring and not the judge — see the note there.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from digline.core import Faithfulness
from digline.run import Case, Suite
from digline.targets import PromptTemplate
from digline_anthropic import AnthropicClaimJudge, AnthropicTarget

import fake
from brief import JUDGE_MAX_TOKENS, JUDGE_PREFILL, JUDGE_SYSTEM, MODEL

HERE = Path(__file__).parent
FAKE = os.environ.get("BRIEF_FAKE_JUDGE") == "1"

#: The same template the digest and `suite.py` render, read here a third time
#: for the one thing neither of them needs: the item as text, to hand the judge
#: as the context the sentence has to be faithful to.
ITEM = PromptTemplate(HERE / "prompts" / "item.txt")


class ReasonTarget(AnthropicTarget):
    """`suite.py`'s call, keeping the other field.

    Byte for byte the same request as `JudgeTarget`: same `prompts/judge.txt`,
    same `prompts/item.txt`, same model, same cap, same prefill. `parse` keeps
    `reason` where that one keeps the whole object, because `Faithfulness`
    accepts text and only text — in a structured output, deciding which field
    holds the claims to be checked is a real decision, and digline refuses to
    take it in silence.

    It raises on malformed JSON for `JudgeTarget`'s reason: in the digest a
    broken answer must not bring the morning down, here it must become an
    `error`. A missing `reason` key raises too rather than yielding `""` — the
    empty sentence this suite gates on is one the model actually wrote, not one
    a parser invented out of a `KeyError`.
    """

    def parse(self, text: str) -> str:
        return str(json.loads(text)["reason"])


target = ReasonTarget(
    prompt_file=HERE / "prompts" / "item.txt",
    system_file=HERE / "prompts" / "judge.txt",
    model=MODEL,
    max_tokens=JUDGE_MAX_TOKENS,
    prefill=JUDGE_PREFILL,
    client=fake.FakeAnthropic() if FAKE else None,
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


cases = [
    Case(
        id=c["id"],
        vars=c["vars"],
        # **Both prompts.** The context is what the model was given, and it was
        # given two things: the taste in `prompts/judge.txt` and the item in
        # `prompts/item.txt`. The first draft of this file passed the item
        # alone, and six live cases said why that was wrong — every sentence
        # here has the shape "<what the article is about>, rilevante per <why
        # it matters to him>", and with the taste outside the context that
        # second half is unsupported *by construction*. The judge was marking
        # the model down for knowing what I asked it to know. Scores went from
        # a mean of 0.28 to 0.47 on the same six cases when the taste went in,
        # and that difference is my context being wrong, not the model being
        # better.
        #
        # What it does not weaken is the thing this suite is for: the taste
        # says nothing about any particular article, so a sentence that invents
        # an article's content is still unsupported by both files together.
        context=[JUDGE_SYSTEM, ITEM.render(c["vars"], case_id=c["id"])],
        metadata=c["metadata"],
        # No `expected`: `Faithfulness` compares the sentence with the item, not
        # with an answer of mine. And no `label`, because there is no run
        # assertion here to count a confusion matrix — I have never sat down and
        # marked 21 sentences faithful or not, and a label I invented this
        # afternoon would be ground truth with no ground under it.
    )
    for c in json.loads((HERE / "cases" / "brief.json").read_text(encoding="utf-8"))
]

suite = Suite(
    tenant="alessandro",
    environment="dev",
    name="brief-reason",
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
        # twice and never disagreeing usefully. What that leaves ungated is the
        # judge's own spend — `CostBudget` reads `Response.cost_usd`, which is
        # the target's — and nothing digline ships can gate it. It is announced
        # by `planned_calls` before the run and recorded by `judge.spent_usd`
        # after it; it is not a check, and this comment is the only place that
        # says so.
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
            # It is 2σ for a *typical* case and the honest caveat is that two or
            # three cases are not typical. Where the judge finds one claim in
            # the sentence — `economics` is 0.8 supported of 1.0 — each sample
            # is 0 or 1 and nothing between, the standard error reaches 0.200,
            # and 2σ there is 0.40. Those are the cases that will chatter first,
            # and `compare` already says so in its own words: five checks are
            # on the line, their measured bands covering the threshold. Widening
            # the tolerance until they stopped would be buying quiet with the
            # only cases that can still move.
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
