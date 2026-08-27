"""Extracts the ground-truth cases from seen.json into cases/brief.json.

A case is an item I was actually shown and actually answered about: the vars
are what the judge saw, `expected.marked` is what I said. Nothing here is
written by hand, which is the point — the test set is a by-product of using
the thing.
"""

import json
import re
import sys
from pathlib import Path

from brief import SEEN_PATH, SUMMARY_MAX_CHARS


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


# `seen.example.json` is deliberately not a fallback here: the ten example
# records are not anybody's reading history, and regenerating the ground truth
# from them would quietly replace 21 real cases with a copy of the example.
if not SEEN_PATH.exists():
    sys.exit(f"{SEEN_PATH.name} does not exist yet — run the digest first.")

seen = json.loads(SEEN_PATH.read_text(encoding="utf-8"))
records = [r for r in seen.values()
           if r.get("shown") and "summary" in r and "marked" in r]
records.sort(key=lambda r: (r["judged_at"], r["title"]))

cases = [
    {
        "id": f"{r['judged_at'][:10]}-{slug(r['title'])}",
        # Truncated here as well as at fetch time: a record written when the
        # cap was 1500 must not come back through this door and quietly undo
        # the cap the judge is running with today.
        "vars": {
            "source": r["source"],
            "title": r["title"],
            "summary": r["summary"][:SUMMARY_MAX_CHARS],
        },
        "expected": {"marked": r["marked"]},
        "metadata": {"link": r["link"], "original_score": r["score"]},
    }
    for r in records
]
out = Path(__file__).parent / "cases"
out.mkdir(exist_ok=True)
(out / "brief.json").write_text(
    json.dumps(cases, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{len(cases)} cases, {sum(c['expected']['marked'] for c in cases)} marked")
