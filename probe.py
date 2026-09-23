"""A probe: what the judge really answers, and in what shape.

Not a test — this is the instrument you look at a real reply with, and
therefore the instrument you build a fake from. A fake written by reading the
code only confirms the code: that happened here with
`cache_creation_input_tokens`, a field nobody was reading and the fake did not
have, with the tests green and the cost understated by a factor of 384.

It happened a second time, in the smaller way this file exists to catch early.
digline 0.8.0 began reading `stop_reason` and `model` off the reply, and this
probe was printing neither — so the fake did not have them either, and a fake
run recorded a poorer document than a real one without anything going red.
Both are printed below now, beside what `completion_of` makes of them: the
rule is that whatever this script does not show is what the fake will not have,
and so what the checks will never see.

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
from digline_anthropic.client import completion_of

from brief import JUDGE_MAX_TOKENS, JUDGE_PROMPT, JUDGE_SYSTEM, MODEL, SUMMARY_MAX_CHARS

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
    max_tokens=JUDGE_MAX_TOKENS,
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

print("--- how the turn ended, and what answered ---")
print("   digline 0.8.0 reads both of these. `model` is the snapshot behind the")
print("   alias that was sent, and `stop_reason` is the cause a mute reply used")
print("   to have inferred for it from a token count.")
print(f"   {'stop_reason':32} = {getattr(response, 'stop_reason', '<absent>')!r}")
print(f"   {'model':32} = {getattr(response, 'model', '<absent>')!r}")
print()

print("--- what the plugin makes of it ---")
print("   `completion_of` is the one door both `BriefJudge` and the suite's")
print("   target read a reply through, so this is the record, not a reading of")
print("   it. Whatever is absent here is what the fake must not invent.")
completion = completion_of(response)
print(f"   {'finish':32} = {completion.finish!r}")
print(f"   {'finish_raw':32} = {completion.finish_raw!r}")
print(f"   {'tools':32} = {completion.tools!r}")
print(f"   {'model':32} = {completion.model!r}")
print(f"   {'fingerprint':32} = {completion.fingerprint!r}")
print()

print("--- usage, field by field ---")
print("   this is what a fake gets rebuilt from: whatever is not printed here")
print("   is what the fake will not have, and so what the tests will not see.")
for field in sorted(type(response.usage).model_fields):
    print(f"   {field:32} = {getattr(response.usage, field, '<absent>')!r}")
print()

raw = "{" + response.content[0].text
data = json.loads(raw)
print("--- the reply, field by field ---")
print("   the rule this whole file rests on: whatever the probe does not show")
print("   is what the fake will not have, and so what the checks never see.")
print("   `about` was here under decision 0001 and left with 0002, which moved")
print("   the description into a call of its own.")
for key in ("reason", "score"):
    print(f"   {key:8} = {data.get(key, '<ABSENT>')!r}")
print()
print("--- did it fit? ---")
print("   the reply against JUDGE_MAX_TOKENS.")
print("   a reply cut off at the cap is a parse failure the digest turns into")
print("   score=0, so the cap is verified here rather than assumed.")
print(f"   output_tokens {response.usage.output_tokens} of the "
      f"{JUDGE_MAX_TOKENS} sent as max_tokens")
print(f"   stop_reason   {response.stop_reason!r}  (must be 'end_turn', never 'max_tokens')")
