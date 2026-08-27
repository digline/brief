"""The judge of `brief.py`, measured against the judgements I made by hand.

The cases are not invented: every one of them is an item the digest showed me
and that I answered about, extracted from `seen.json` by `make_cases.py`. The
label is my own answer. So what this suite asks is not "is the output good" but
"does the model still agree with me as often as it did" — which is a question a
baseline can answer and a diff cannot.

`BRIEF_FAKE_JUDGE=1` swaps the provider for `fake.py`. That is for CI, and it
measures the wiring, not the judge — see the note there.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from digline.core import (
    STRUCTURED_ONLY,
    Accuracy,
    AssertionBase,
    CostBudget,
    EvaluatorInputs,
    JsonSchema,
    OutputKind,
    Precision,
    Verdict,
)
from digline.run import Case, Suite
from digline_anthropic import AnthropicTarget

import fake
from brief import MODEL

HERE = Path(__file__).parent
FAKE = os.environ.get("BRIEF_FAKE_JUDGE") == "1"


@dataclass(frozen=True, slots=True)
class AgreesWithMark(AssertionBase):
    """The judge says >= brief_threshold exactly when I marked the item.

    Binary per sample; with samples=5 the driver averages it (0, 0.2, ..., 1):
    threshold 0.5 means a majority, tolerance 0.41 means that up to two votes
    wobbling is noise and three is a change.
    """

    brief_threshold: int = 4
    name: str = "agrees_with_mark"
    threshold: float = 0.5
    tolerance: float = 0.41
    accepts: frozenset[OutputKind] = STRUCTURED_ONLY

    def __call__(self, inputs: EvaluatorInputs) -> Verdict:
        if (err := self._accept(inputs.output)) is not None:
            return err
        if not isinstance(inputs.expected, dict) or "marked" not in inputs.expected:
            return self._error("expected must be {'marked': bool}")
        score = inputs.output.get("score")
        if not isinstance(score, int):
            return self._error(f"output has no integer score: {score!r}")
        predicted = score >= self.brief_threshold
        marked = bool(inputs.expected["marked"])
        return self._binary(
            predicted == marked,
            f"model said {score} ({'show' if predicted else 'skip'}), I marked {marked}",
            )


SCHEMA = {
    "type": "object",
    "required": ["score", "reason"],
    "properties": {
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "reason": {"type": "string", "minLength": 1},
    },
}


class JudgeTarget(AnthropicTarget):
    """The digest's judge, called the way the digest calls it.

    Same `system` (`prompts/judge.txt`), same user prompt (`prompts/item.txt`,
    the very file `brief.judge()` renders), same prefill. Both files end up in
    the run's artifacts without the suite declaring them: the target knows what
    it is made of.

    `parse` raises on malformed JSON instead of returning `score=0` the way the
    application does. In the digest a broken answer must not bring the morning
    down; here it must become an `error` — "it did not answer in the agreed
    shape" is neither a pass nor a regression.
    """

    def parse(self, text: str) -> dict[str, object]:
        data = json.loads(text)
        return {"score": int(data["score"]), "reason": str(data["reason"])}


target = JudgeTarget(
    prompt_file=HERE / "prompts" / "item.txt",
    system_file=HERE / "prompts" / "judge.txt",
    model=MODEL,
    max_tokens=200,
    prefill="{",  # forces JSON out, as in brief.judge()
    client=fake.FakeAnthropic() if FAKE else None,
)


cases = [
    Case(
        id=c["id"],
        vars=c["vars"],
        expected=c["expected"],
        label="positive" if c["expected"]["marked"] else "negative",
        metadata=c["metadata"],
    )
    for c in json.loads((HERE / "cases" / "brief.json").read_text(encoding="utf-8"))
]

suite = Suite(
    tenant="alessandro",
    environment="dev",
    name="brief-judge",
    assertions=[
        JsonSchema(schema=SCHEMA),
        AgreesWithMark(),
        CostBudget(max_usd=0.0015, tolerance=0.15),
    ],
    # No artifacts declared here: the target names them, because the target is
    # what uses them. `prompts/judge.txt` and `prompts/item.txt` enter the run
    # on their own.
    #
    # Precision: how much noise there is in the digest I actually read
    # (measured 0.67). Accuracy: it counts the right "no"s too, which the digest
    # never shows me (measured 0.76). The thresholds sit a little below where
    # the system is, not where I would like it to get to: the gate protects
    # against getting worse, and raising them is a change you can see in
    # config_hash.
    run_assertions=[
        Precision(over="agrees_with_mark", threshold=0.60, tolerance="1/21"),
        Accuracy(over="agrees_with_mark", threshold=0.65, tolerance="1/21"),
    ],
    cases=cases,
    samples=5,
    min_agreement="3/5",
)
