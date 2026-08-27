"""A probe: what the judge really answers, and in what shape.

Not a test — this is the instrument you look at a real reply with, and
therefore the instrument you build a fake from. A fake written by reading the
code only confirms the code: that happened here with
`cache_creation_input_tokens`, a field nobody was reading and the fake did not
have, with the tests green and the cost understated by a factor of 384.

The prompt and the system come from `brief.py`, which takes them from the same
files the suite uses. This script is the fourth caller of that template: it
used to keep its own copy of the prompt, already divergent in two places (other
wording for levels 3 and 4, and no `Source:` line), which is exactly how a
probe stops probing what actually runs.

Usage: uv run probe.py
"""

import json

import anthropic
import feedparser

from brief import JUDGE_PROMPT, JUDGE_SYSTEM, MODEL, SUMMARY_MAX_CHARS

SOURCE = "Simon Willison"
FEED = "https://simonwillison.net/atom/everything/"

entry = feedparser.parse(FEED).entries[0]
prompt = JUDGE_PROMPT.render(
    {
        "source": SOURCE,
        "title": entry.title,
        "summary": entry.get("summary", "")[:SUMMARY_MAX_CHARS],
    }
)

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
response = client.messages.create(
    model=MODEL,
    max_tokens=200,
    system=JUDGE_SYSTEM,
    messages=[
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": "{"},  # prefill, as in brief.judge()
    ],
)

print("--- prompt sent ---")
print(prompt[:300], "...\n")

print("--- content blocks ---")
print(repr(response.content), "\n")

print("--- usage, field by field ---")
print("   this is what a fake gets rebuilt from: whatever is not printed here")
print("   is what the fake will not have, and so what the tests will not see.")
for field in sorted(type(response.usage).model_fields):
    print(f"   {field:32} = {getattr(response.usage, field, '<absent>')!r}")
print()

raw = "{" + response.content[0].text
data = json.loads(raw)
print("score:", data["score"], "| reason:", data["reason"])
