"""The provider, faked, so the suite can run with no key and no network.

This exists for CI. A scheduled run against the real model is worth money and
worth having; a run on every push is worth neither, and a repository whose
checks only work for whoever holds the key is a repository nobody can send a
patch to. `BRIEF_FAKE_JUDGE=1` puts this in place of the SDK (see `suite.py`).

Two providers are faked, because there are two models in play. `FakeAnthropic`
stands in for the one being measured — the digest's own judge, scoring an item
1-5. `FakeClaimAnthropic` stands in for the *instrument* `reason.py` measures it
with: the claim judge that counts how much of the sentence the item supports.
Different questions, different shapes, so they are two classes and not one.

What it proves is the wiring, not the judge: that the suite loads, that the
target composes both prompt files, that the assertions evaluate, that a run and
a report come out the other end. It says nothing about whether the real judge
agrees with me — only a live run says that, and the committed baseline is the
one it is measured against.

It is still made to read the prompt rather than ignore it. The bullet lists in
`prompts/judge.txt` are what it scores against, so deleting a line from the
prompt changes these answers too. A fake that answered the same whatever you
asked it would make every prompt look equally good.

The shape of `usage` comes from `probe.py`, from a real reply — including
`cache_creation_input_tokens`, which is *not* part of `input_tokens` and which
a fake written by reading the code would not have had. `stop_reason` and
`model` are here for the same reason and arrived the same way: digline 0.8.0
reads both, so a fake without them would quietly make the checks see a poorer
record than production writes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

#: Words too common to carry a topic. Everything else in a bullet is a signal.
STOPWORDS = frozenset(
    "a an and are as at be by for from in into is it its of on or the to with "
    "real not without he wants does want items about production systems".split()
)


def _keywords(bullet: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", bullet.lower())
    return {w for w in words if w not in STOPWORDS}


def _field(prompt: str, label: str) -> str:
    """One labelled line of a rendered `prompts/item.txt`, or the empty string.

    Read out of the prompt rather than passed in, because that is the only
    thing this fake is ever given — and reading it is what lets the sentences it
    writes be about the item, the way the real ones are.
    """
    for line in prompt.splitlines():
        if line.startswith(f"{label}:"):
            return line[len(label) + 1 :].strip()
    return ""


def _title(prompt: str) -> str:
    return _field(prompt, "Title")


def _bullets(system: str, heading: str) -> list[set[str]]:
    """The `- ` lines under one heading of the judge prompt, as keyword sets."""
    after = system.split(heading, 1)[-1]
    out = []
    for line in after.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(_keywords(line[2:]))
        elif out and line:
            break  # the list has ended
    return out


@dataclass
class _Block:
    text: str
    type: str = "text"


@dataclass
class _Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


#: What this fake says answered, when asked the way a real reply is asked.
#: Deliberately **not** `claude-haiku-4-5-20251001` and deliberately not the
#: model id off the request: the first would put a real snapshot's name in a
#: record no real model produced, and the second is the echo `completion_of`
#: refuses on Bedrock because it "would manufacture the one fact it exists to
#: obtain". The fake is a judge; this is its name. A fake run that ever landed
#: beside a real baseline would say so in one line of the comparison.
FAKE_MODEL = "brief-fake-judge"


@dataclass
class _Reply:
    content: list[_Block]
    usage: _Usage = field(default_factory=_Usage)
    #: Both fields come from a real reply through `probe.py`, like `usage`
    #: before them. Since digline 0.8.0 the plugin reads `stop_reason` into
    #: `Completion.finish` and `model` into what the run records as
    #: `resolved_model` — so a fake without them is a fake that makes the
    #: harness record *less* than it does in production, which is the shape of
    #: the `cache_creation_input_tokens` mistake this file already carries a
    #: paragraph about. `end_turn` is the truthful word here: this judge always
    #: finishes what it is saying.
    stop_reason: str = "end_turn"
    model: str = FAKE_MODEL


class _Messages:
    def create(self, **request: Any) -> _Reply:
        system: str = request.get("system", "")
        prompt: str = request["messages"][0]["content"]
        text = prompt.lower()

        wanted = sum(bool(kw & _keywords(text)) for kw in _bullets(system, "He WANTS"))
        avoided = sum(
            bool(kw & _keywords(text)) for kw in _bullets(system, "He does NOT want")
        )
        score = max(1, min(5, 3 + wanted - avoided))
        # Two fields since decision 0001, and they are faked to the same split
        # the real prompt asks for: `about` says only what the item states and
        # nothing else, `reason` carries the bookkeeping that is this fake's
        # judgement. A fake that put its own words in `about` would make the
        # faithfulness suite score the fake instead of the shape.
        about = (
            f"Articolo di {_field(prompt, 'Source')} intitolato "
            f"{_title(prompt)}."
        )
        # The sentence names the item, because the real one does. A fake whose
        # words were the same whatever it had been shown would score identically
        # on all 21 cases — the "every prompt looks equally good" failure this
        # file exists to avoid, moved one field along.
        reason = (
            f"fake judge: {_title(prompt)}; "
            f"{wanted} wanted topics, {avoided} unwanted"
        )

        # The prefill is `{`, and the SDK returns only what follows it: the
        # caller puts the brace back. A fake that returned the whole object
        # would hand `brief.judge()` a `{{` and fail to parse. (See
        # `AnthropicTarget._complete`.)
        #
        # Built by `json.dumps` and beheaded, not by an f-string: a title
        # carrying a quote — `Quoting ...` posts are a whole category in these
        # feeds — would otherwise produce a reply that is not JSON, and the
        # fake would fail for a reason the real provider never has.
        # Same key order as `prompts/judge.txt` asks for, and that is not
        # cosmetic: a field's position is part of what the real model is being
        # asked, so a fake that ordered them differently would be faking a
        # different question. (decision 0001, "the general fact")
        answer = json.dumps(
            {"reason": reason, "score": score, "about": about}, ensure_ascii=False
        )[1:]
        return _Reply(
            content=[_Block(answer)],
            usage=_Usage(
                input_tokens=len(system + prompt) // 4,
                output_tokens=len(answer) // 4,
            ),
        )


class FakeAnthropic:
    """Whatever `AnthropicTarget` calls, and nothing else."""

    def __init__(self) -> None:
        self.messages = _Messages()


# --- The claim judge, faked ---------------------------------------------------

#: The line every judge prompt puts the graded text behind. Declared in
#: `digline.core.assertions` as `JUDGE_OUTPUT_LABEL` and repeated here rather
#: than imported, because a fake that broke when digline renamed a private
#: constant would be a fake nobody could read. It is interface — `docs/api.md`
#: spells the shape out under `Judge` — and a rename would be a release note.
CLAIM_OUTPUT_LABEL = "Output to judge:"

#: The claim judge's own name, for `FAKE_MODEL`'s reason. It is a second
#: instrument and must not answer to the first one's name: a run in which the
#: target was faked and the judge was real, or the reverse, is a run whose
#: `judge_config` and `target_config` have to disagree.
FAKE_CLAIM_MODEL = "brief-fake-claim-judge"

#: What a claim is, to this fake. Splitting an Italian sentence into claims is
#: the real judge's whole job and is not reproducible here; splitting it on the
#: marks that separate clauses is the honest approximation — it moves when the
#: sentence moves, which is the only property the wiring test needs.
_CLAUSE = re.compile(r"[.,;:!?]|\s+—\s+|\s+-\s+")


def _clauses(text: str) -> list[str]:
    return [part.strip() for part in _CLAUSE.split(text) if part.strip()]


class _ClaimMessages:
    def create(self, **request: Any) -> _Reply:
        prompt: str = request["messages"][0]["content"]
        # Everything before the label is what the output was allowed to use —
        # the Context section and, in this suite, the Input that repeats it.
        # Everything after is the sentence being checked. Reading them this way
        # round is what makes the fake follow `judge_prompt`'s shape rather than
        # a shape of its own.
        given, _, output = prompt.partition(CLAIM_OUTPUT_LABEL)
        given_words = _keywords(given.split("Context:", 1)[-1])

        clauses = _clauses(output)
        total = len(clauses)
        supported = sum(1 for clause in clauses if _keywords(clause) & given_words)
        # `total == 0` is returned rather than nudged to 1. An output with no
        # clauses is an empty sentence, and `Faithfulness` turns that into an
        # `error` on purpose — 0/0 is not 0. A fake that quietly reported one
        # claim would hide the one outcome `reason.py` says it is watching for.
        reason = (
            f"fake claim judge: {supported} of {total} clauses share a word "
            f"with the context"
        )
        answer = json.dumps(
            {"supported": supported, "total": total, "reason": reason},
            ensure_ascii=False,
        )[1:]
        return _Reply(
            content=[_Block(answer)],
            usage=_Usage(
                input_tokens=len(prompt) // 4,
                output_tokens=len(answer) // 4,
            ),
            model=FAKE_CLAIM_MODEL,
        )


class FakeClaimAnthropic:
    """Whatever `AnthropicClaimJudge` calls, and nothing else."""

    def __init__(self) -> None:
        self.messages = _ClaimMessages()
