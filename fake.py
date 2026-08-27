"""The provider, faked, so the suite can run with no key and no network.

This exists for CI. A scheduled run against the real model is worth money and
worth having; a run on every push is worth neither, and a repository whose
checks only work for whoever holds the key is a repository nobody can send a
patch to. `BRIEF_FAKE_JUDGE=1` puts this in place of the SDK (see `suite.py`).

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
a fake written by reading the code would not have had.
"""

from __future__ import annotations

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


@dataclass
class _Reply:
    content: list[_Block]
    usage: _Usage = field(default_factory=_Usage)


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
        reason = f"fake judge: {wanted} wanted topics, {avoided} unwanted"

        # The prefill is `{`, and the SDK returns only what follows it: the
        # caller puts the brace back. A fake that returned the whole object
        # would hand `brief.judge()` a `{{` and fail to parse. (See
        # `AnthropicTarget._complete`.)
        answer = f'"reason": "{reason}", "score": {score}}}'
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
