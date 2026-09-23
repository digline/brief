"""brief.py — a morning digest of the AI sources I read.

Usage: uv run brief.py [read|stats]
Needs ANTHROPIC_API_KEY in the environment.

The judge is a single Haiku call per item, scoring 1-5 against a taste
described in `prompts/judge.txt`. What I mark as interesting is written back to
`seen.json`, and that is where the ground truth in `cases/brief.json` comes
from: the suite measures this judge against the judgements I made by hand.
"""

from __future__ import annotations

import calendar
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

import feedparser
from digline.targets import Completion, JudgeBase, PromptTemplate, UnknownModelError
from digline_anthropic import ANTHROPIC_PRICING
from digline_anthropic.client import build_client, completion_of

# --- Configuration ----------------------------------------------------------

FEEDS = {
    "Simon Willison": "https://simonwillison.net/atom/everything/",
    "Ahead of AI (Raschka)": "https://magazine.sebastianraschka.com/feed",
    # The Anthropic family through Olshansk's repo (one mirror, rebuilt hourly)
    "Anthropic Engineering": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
    "Anthropic Research": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
    # Full content in the feed: the judge reads the article's real opening
    "Hamel Husain": "https://hamel.dev/index.xml",
    "Lilian Weng": "https://lilianweng.github.io/index.xml",
}

HERE = Path(__file__).parent
SEEN_PATH = HERE / "seen.json"
#: My own reading history is not in this repository. A clone starts from ten
#: records, so `stats` has something to print and the shape of the file is
#: visible before the first run writes the real one.
SEEN_EXAMPLE_PATH = HERE / "seen.example.json"

MODEL = "claude-haiku-4-5"
#: Back to 200 under decision 0002: the reply is one sentence again, and the
#: baseline this suite is measured against was produced at 200. It went to 400
#: for the two-field reply of 0001, where `probe.py` measured 137 output tokens
#: against it — headroom of 1.46x where the record had predicted 2x.
#:
#: **What is on the other side of this number is worse than an error.** A reply
#: cut off at the cap is invalid JSON, `__call__` catches the parse failure, and
#: the item is recorded with `score=0`. Zero is below `SCORE_THRESHOLD`, so the
#: item never appears in the digest — and in `seen.json` it is a row with a
#: score in it, indistinguishable by any count from an item the judge read and
#: thought worthless. An absence wearing a measurement's clothes, and the row
#: keeps saying it for as long as the file is kept.
#:
#: That is Handbook chapter 0's fourth decision — *make a failure look different
#: from an empty answer* — broken inside the repository the chapter was partly
#: written from, in the one place nobody was watching. The only thing standing
#: between it and silence is that `reason` begins with `[parse failed]`: a
#: marker in prose, in a field nothing counts. `stats()` reads `"score" in r`
#: and counts the row as judged.
#:
#: Not fixed here, and not by 0002 either: giving a failure its own state
#: changes what `seen.json` holds and what `make_cases.py` reads out of it. It
#: is 0003's, and it is named in 0002 as explicitly left alone.
JUDGE_MAX_TOKENS = 200
#: The prefill that forces JSON out. Prepended to the reply before parsing,
#: because the reply *is* the prefill plus the completion.
JUDGE_PREFILL = "{"
MAX_JUDGED_PER_RUN = 50  # ceiling on API calls (it matters mostly on the first run)
TOP_N = 5
#: How much of the summary the judge gets. It was 1500. Cutting it to 400 is
#: the kind of change you cannot eyeball, so the suite measured it: over the
#: 21 cases, one case improved, none got worse, precision 0.63 -> 0.67. That is
#: one case, which is noise as much as it is a gain — the point is that it did
#: not cost anything, and `report.html` is that comparison.
SUMMARY_MAX_CHARS = 400
SCORE_THRESHOLD = 4
MIN_SHOWN = 5

JUDGE_SYSTEM = (HERE / "prompts" / "judge.txt").read_text(encoding="utf-8")
#: The describing call of decision 0002. A separate system prompt because it is
#: a separate question: it is never shown the taste, so it cannot judge against
#: it, and that is the property `reason.py` measures. Shorter than the judge's
#: because describing is the smaller job.
DESCRIBER_SYSTEM = (HERE / "prompts" / "describer.txt").read_text(encoding="utf-8")
#: One Italian sentence. Measured at 60 output tokens for the judge's
#: single-sentence reply, so 150 is headroom without being a place to hide —
#: and what lies past a cap is written up at `JUDGE_MAX_TOKENS`.
DESCRIBER_MAX_TOKENS = 150
# The user prompt is a file, not an f-string: the suite renders it through the
# same object (`AnthropicTarget(prompt_file=...)`), so the application and its
# evaluation cannot drift apart. Change a line here and it changes there too —
# and the run records it, because it is an artifact.
JUDGE_PROMPT = PromptTemplate(HERE / "prompts" / "item.txt")


# --- Data model --------------------------------------------------------------


@dataclass
class Item:
    id: str
    source: str
    title: str
    link: str
    summary: str
    published_ts: float  # epoch; 0.0 when the feed gives no date


@dataclass
class Judgement:
    score: int
    reason: str
    cost_usd: float = 0.0


@dataclass
class Description:
    """What the describing call produced, or why it produced nothing.

    **`about` and `failed` are two different absences and never one.** A morning
    where the describing call fell over must not look like a morning where the
    model described an item as nothing: the first is our outage and the second
    would be a fact about the item. So exactly one of these is ever non-empty,
    `run_brief` writes whichever it is under its own key, and no row in
    `seen.json` carries an empty `about` that a later count would read as a
    description. That is Handbook chapter 0's fourth decision, applied at the
    one place decision 0002 creates a new way to fail.
    """

    about: str = ""
    failed: str = ""
    cost_usd: float = 0.0

    def __post_init__(self) -> None:
        if bool(self.about) == bool(self.failed):
            raise ValueError(
                "a Description carries an answer or a reason there is none, "
                f"never both and never neither: about={self.about!r} "
                f"failed={self.failed!r}"
            )


# --- State (seen.json) --------------------------------------------------------


def load_seen() -> dict[str, dict]:
    """The real history if there is one, otherwise the ten example records."""
    for path in (SEEN_PATH, SEEN_EXAMPLE_PATH):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_seen(seen: dict[str, dict]) -> None:
    # Always to seen.json: the example is a starting point, never a destination.
    SEEN_PATH.write_text(
        json.dumps(seen, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# --- Fetching and parsing -----------------------------------------------------


def to_epoch(parsed) -> float:
    """feedparser's UTC struct_time -> epoch; 0.0 when absent or nonsensical."""
    if not parsed:
        return 0.0
    try:
        return float(calendar.timegm(parsed))
    except (OverflowError, ValueError):
        return 0.0


def strip_html(text: str) -> str:
    """Crude tag removal: to give Haiku some context it is more than enough."""
    return re.sub(r"<[^>]+>", " ", text)


def fetch_new_items(seen: dict[str, dict]) -> list[Item]:
    items: list[Item] = []
    seen_this_run: set[str] = set()
    for source, url in FEEDS.items():
        feed = feedparser.parse(url, agent="Mozilla/5.0")
        if feed.bozo and not feed.entries:
            # bozo = feedparser hit an error; with no entries either, skip it
            print(f"  [warn] unreadable feed: {source} ({feed.bozo_exception})")
            continue
        for entry in feed.entries:
            item_id = entry.get("id") or entry.get("link", "")
            if not item_id or item_id in seen:
                continue
            if item_id in seen_this_run:
                print(f"  [warn] duplicate id in {source}: {entry.get('title', '?')[:60]}")
                continue
            seen_this_run.add(item_id)
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            items.append(
                Item(
                    id=item_id,
                    source=source,
                    title=entry.get("title", "(untitled)"),
                    link=entry.get("link", ""),
                    summary=strip_html(entry.get("summary", ""))[:SUMMARY_MAX_CHARS],
                    published_ts=to_epoch(published),
                )
            )
    # newest first: if the ceiling bites, it bites the stale end
    items.sort(key=lambda item: item.published_ts, reverse=True)
    return items


# --- Judging ------------------------------------------------------------------


class BriefJudge(JudgeBase):
    """The digest's judge, on digline's judging machinery.

    `JudgeBase` brings the accounting: `calls`, `spent_usd` and `latency_ms`,
    monotone for the life of the object and never reset, so "what has this
    morning cost" is a subtraction and not a tally kept by hand. The price list
    comes from the published plugin — `ANTHROPIC_PRICING`, dated in
    `digline_anthropic.pricing.PRICES_READ_ON` — instead of the two constants
    that used to sit in this file and that nobody would have remembered to
    update.

    That is not only tidiness. The old arithmetic here read `input_tokens` and
    `output_tokens` and nothing else, and `cache_creation_input_tokens` is
    billed separately and is *not* included in `input_tokens`: the plugin's
    `usage_of` — reached through `completion_of` — reads all four counts, which
    is the undercount `probe.py` documents, fixed here rather than described.

    Deliberately **not** `AnthropicJudge` from the plugin. That one is a rubric
    grader: its system prompt is a `ClassVar` on `ScoreJudge` — declared per
    subclass on purpose, never a constructor argument — and it answers a float
    in 0..1 about "the output of another system". This judge has to ask
    `prompts/judge.txt` and answer an integer 1-5, which is the scale
    `seen.json`, `cases/brief.json` and the committed baseline are all written
    in. Same machinery, same provider, same price list; different question.
    """

    provider = "anthropic"
    system = JUDGE_SYSTEM
    #: The same `JUDGE_PREFILL` that `_complete` puts back, declared where
    #: `JudgeBase` looks for it. Since digline 0.6.0 `_ask` refuses a reply the
    #: model contributed nothing to, and it has to see past the prefill to know
    #: that: `_complete` returns `"{"` for a model that said nothing, and `"{"`
    #: is not empty. Left at its `None` default, this judge would be the one
    #: the check never fired for, and a mute model would come back as a parse
    #: failure over a brace instead of as the truncation or refusal it was.
    #:
    #: What that check then *says* is decided by `_complete`'s return: see
    #: there. The two are a pair — this one makes the check fire, that one
    #: gives it something to read.
    prefill = JUDGE_PREFILL

    def __init__(self, model: str = MODEL, *, client=None) -> None:
        super().__init__(
            model, max_tokens=JUDGE_MAX_TOKENS, pricing=ANTHROPIC_PRICING
        )
        self._injected = client

    def _client(self):
        """Built on first use, so importing this module needs no key."""
        if self._injected is None:
            self._injected = build_client()
        return self._injected

    def _complete(self, system: str, prompt: str) -> Completion:
        """The one call, as the record digline 0.8.0 widened `_complete` to.

        This used to return the `(text, Usage)` pair. That pair is still
        admissible and always will be, so nothing forced this — but it is the
        *lossy* return, and what it loses is exactly what this judge wants on a
        bad morning. `Completion` carries `finish` beside the two, so `_ask`
        **reads** why a mute model said nothing instead of inferring it from a
        token count against the cap: a reply cut off at `max_tokens` and one
        that came back as a tool call are the same number and need opposite
        fixes. It also carries what the provider said actually answered, so
        `self.observed` learns the snapshot behind the `claude-haiku-4-5`
        alias rather than recording the alias twice.

        `replace` rather than a mutation because `Completion` is frozen, which
        is what keeps it a value.
        """
        reply = completion_of(
            self._client().messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": JUDGE_PREFILL},
                ],
            )
        )
        # The reply *is* the prefill plus the completion, and a parser handed
        # only the tail sees invalid JSON.
        return replace(reply, text=JUDGE_PREFILL + reply.text)

    def __call__(self, item: Item) -> Judgement:
        prompt = JUDGE_PROMPT.render(
            {"source": item.source, "title": item.title, "summary": item.summary}
        )
        # `spent_usd` is a running total for the life of the judge, so one
        # item's cost is read twice and subtracted — the idiom `JudgeBase`
        # documents. `_ask` prices the call before it parses it, so a reply
        # that fails to parse is still charged for, as it was.
        before = self.spent_usd
        try:
            data = self._ask(prompt)
            return Judgement(
                score=int(data["score"]),
                reason=str(data["reason"]),
                cost_usd=self.spent_usd - before,
            )
        except UnknownModelError:
            # A mispriced model is not a malformed answer: it would turn every
            # item into a silent zero. `preflight()` catches it before the
            # first call, and this makes sure it can never be swallowed here.
            raise
        except (ValueError, KeyError, TypeError) as exc:
            # the digest must never crash over one malformed answer
            return Judgement(
                score=0,
                reason=f"[parse failed] {exc}"[:120],
                cost_usd=self.spent_usd - before,
            )



class BriefDescriber(JudgeBase):
    """The second call of decision 0002: what the item is, and nothing else.

    A separate object rather than a second method on `BriefJudge`, because the
    whole finding behind 0002 is that one call cannot be asked two questions
    without becoming worse at the first. Two questions, two calls, two system
    prompts — and this one is never given `prompts/judge.txt`, so there is no
    taste in its context to judge against and nothing for a description to
    smuggle a verdict in from.

    It renders the same `prompts/item.txt` the judge does. That is the repo's
    standing rule and it earns its keep here: the faithfulness suite checks this
    call's output against that item, so the item the model saw and the item the
    judge is shown have to be the same bytes or the measurement is of two
    different things.
    """

    provider = "anthropic"
    system = DESCRIBER_SYSTEM
    prefill = JUDGE_PREFILL

    def __init__(self, model: str = MODEL, *, client=None) -> None:
        super().__init__(
            model, max_tokens=DESCRIBER_MAX_TOKENS, pricing=ANTHROPIC_PRICING
        )
        self._injected = client

    def _client(self):
        if self._injected is None:
            self._injected = build_client()
        return self._injected

    def _complete(self, system: str, prompt: str) -> Completion:
        reply = completion_of(
            self._client().messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": JUDGE_PREFILL},
                ],
            )
        )
        return replace(reply, text=JUDGE_PREFILL + reply.text)

    def __call__(self, item: Item) -> Description:
        prompt = JUDGE_PROMPT.render(
            {"source": item.source, "title": item.title, "summary": item.summary}
        )
        before = self.spent_usd
        try:
            about = str(self._ask(prompt)["about"]).strip()
        except UnknownModelError:
            # A mispriced model is not a malformed answer, exactly as in
            # `BriefJudge`: it would turn every description into a silent
            # failure instead of stopping the run.
            raise
        except (ValueError, KeyError, TypeError) as exc:
            return Description(
                failed=f"{type(exc).__name__}: {exc}"[:120],
                cost_usd=self.spent_usd - before,
            )
        if not about:
            # An empty string is a reply, not a description. It becomes the
            # stated absence rather than a row that reads as one.
            return Description(
                failed="the model returned an empty description",
                cost_usd=self.spent_usd - before,
            )
        return Description(about=about, cost_usd=self.spent_usd - before)

# --- Statistics ----------------------------------------------------------------


def stats() -> None:
    seen = load_seen()
    records = list(seen.values())

    judged = [r for r in records if "score" in r]
    print(f"Total: {len(records)}  |  judged: {len(judged)}  |  "
          f"skipped: {sum(1 for r in records if r.get('skipped'))}")
    print(f"marked interesting: {sum(1 for r in judged if r.get('marked'))}  |  "
          f"read: {sum(1 for r in judged if r.get('read'))}")
    shown = sum(1 for r in judged if r.get("shown"))
    print(f"shown in the digest: {shown}  |  rough precision: "
          f"{sum(1 for r in judged if r.get('marked')) / shown:.0%}" if shown else "")

    priced = [r for r in judged if "cost_usd" in r]
    if priced:
        # Only records written since the judge started keeping the figure. The
        # count is printed beside it so the total is not read as lifetime.
        print(f"judged cost: ${sum(r['cost_usd'] for r in priced):.4f} over "
              f"{len(priced)} of {len(judged)} judged")
    # The describing call is the other line of the same bill, and it is printed
    # as its own: it is made only for the items that reach the digest, so adding
    # the two would hide that they have different denominators. Two lines,
    # two counts — digline's own `Run.usage` reads the same way.
    described = [r for r in records if "about_cost_usd" in r]
    if described:
        failed = sum(1 for r in described if "about_failed" in r)
        note = f", {failed} failed" if failed else ""
        print(f"described cost: ${sum(r['about_cost_usd'] for r in described):.4f} "
              f"over {len(described)} described{note}")

    print("\nScore distribution:")
    for score, n in sorted(Counter(r["score"] for r in judged).items(), reverse=True):
        print(f"  [{score}] {'#' * n} {n}")

    print("\nBy source (judged, mean score):")
    for source in FEEDS:
        per_source = [r["score"] for r in judged if r.get("source") == source]
        if per_source:
            mean = sum(per_source) / len(per_source)
            print(f"  {source:28} {len(per_source):3}  mean {mean:.1f}")


# --- The digest ----------------------------------------------------------------


def run_brief() -> None:
    seen = load_seen()
    new_items = fetch_new_items(seen)

    if not new_items:
        print("Nothing new. See you tomorrow.")
        return

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    to_judge = new_items[:MAX_JUDGED_PER_RUN]
    for item in new_items[MAX_JUDGED_PER_RUN:]:
        # past the ceiling: recorded as seen-but-skipped, they will not be back
        seen[item.id] = {"source": item.source, "title": item.title,
                         "skipped": True, "judged_at": now}

    print(f"{len(new_items)} new items, judging {len(to_judge)}", end="", flush=True)

    judge = BriefJudge()  # the SDK reads ANTHROPIC_API_KEY from the environment
    # Is this model priced? Ask before spending, not after: an unpriced model
    # would otherwise be found out one call at a time.
    judge.preflight()
    judged: list[tuple[Item, Judgement]] = []
    for item in to_judge:
        j = judge(item)
        judged.append((item, j))
        seen[item.id] = {
            "source": item.source,
            "title": item.title,
            "link": item.link,
            "score": j.score,
            "reason": j.reason,
            "cost_usd": j.cost_usd,
            "judged_at": now,
        }
        print(".", end="", flush=True)
    print()
    print(f"{judge.calls} judged for ${judge.spent_usd:.4f} "
          f"(${judge.spent_usd / judge.calls:.6f} each, "
          f"{judge.latency_ms / judge.calls:.0f} ms each)"
          if judge.calls else "nothing judged")

    ranked = sorted(judged, key=lambda pair: pair[1].score, reverse=True)
    top = [pair for pair in ranked if pair[1].score >= SCORE_THRESHOLD]
    if len(top) < MIN_SHOWN:
        top = ranked[:MIN_SHOWN]

    # Decision 0002's second call, and it is made **only for the items I am
    # about to read**. The description exists to be read; an item that never
    # reaches the digest is never described, so this is five to ten calls on an
    # ordinary morning against up to fifty judgements. 0002 costed it per item
    # and per item was the pessimistic reading — the honest figure is smaller,
    # and so is the latency it warned about.
    describer = BriefDescriber()
    describer.preflight()
    described: dict[str, Description] = {}
    for item, _ in top:
        d = describer(item)
        described[item.id] = d
        record = seen[item.id]
        # One key or the other, never an empty `about`: see `Description`.
        if d.about:
            record["about"] = d.about
        else:
            record["about_failed"] = d.failed
        record["about_cost_usd"] = d.cost_usd
    if describer.calls:
        print(f"{describer.calls} described for ${describer.spent_usd:.4f} "
              f"(${describer.spent_usd / describer.calls:.6f} each)")
        lost = [i.id for i, _ in top if not described[i.id].about]
        if lost:
            # Said out loud, because the alternative is a digest that is quietly
            # shorter of a line and looks like a model with nothing to say.
            print(f"  {len(lost)} description(s) failed; those items are shown "
                  f"without one")

    print(f"\n=== Brief for {datetime.now():%Y-%m-%d} — {len(top)} items ===\n")
    for n, (item, j) in enumerate(top, start=1):
        filler = " (below threshold)" if j.score < SCORE_THRESHOLD else ""
        print(f"{n}. [{j.score}]{filler} {item.title}  ({item.source})")
        # The description when there is one, and nothing at all when there is
        # not: a failed second call costs me the sentence, never the item.
        if described[item.id].about:
            print(f"     {described[item.id].about}")
        print(f"     {j.reason}")
        print(f"     {item.link}\n")

    # This answer is the ground truth. Everything the suite measures starts here.
    answer = input("Which ones interest you? (comma-separated numbers, enter = none) ")
    interesting = {int(tok) for tok in answer.split(",") if tok.strip().isdigit()}
    for n, (item, j) in enumerate(top, start=1):
        seen[item.id]["summary"] = item.summary
        seen[item.id]["shown"] = True
        seen[item.id]["marked"] = n in interesting
    save_seen(seen)


# --- Reading list ---------------------------------------------------------------


def reading_list() -> None:
    seen = load_seen()
    todo = [(item_id, rec) for item_id, rec in seen.items()
            if rec.get("marked") and not rec.get("read")]
    if not todo:
        print("Nothing queued. All read.")
        return

    print(f"\n=== To read ({len(todo)}) ===\n")
    for n, (item_id, rec) in enumerate(todo, start=1):
        print(f"{n}. {rec['title']}  ({rec['source']})")
        print(f"     {rec.get('link', '')}\n")

    answer = input("Which have you read? (comma-separated numbers, enter = none) ")
    done = {int(tok) for tok in answer.split(",") if tok.strip().isdigit()}
    if not done:
        # Nothing to record, and nothing to write: an empty answer here must not
        # turn seen.example.json into a seen.json that was never earned.
        return
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for n, (item_id, rec) in enumerate(todo, start=1):
        if n in done:
            rec["read"] = True
            rec["read_at"] = now
    save_seen(seen)


# --- Main ---------------------------------------------------------------------


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "read":
        reading_list()
    elif command == "stats":
        stats()
    else:
        run_brief()


if __name__ == "__main__":
    main()
