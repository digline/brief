# 0002 — The describing call

- Status: **proposed** — the text first, checkpointed before any code, as
  [0001](0001-about-beside-reason.md) was
- Date: 2026-09-23
- Supersedes: 0001's *implementation*, not its premise. The sentence under the
  title still decides whether I open the article, and only its descriptive half
  can be checked against the item. What changes is where that half is produced
- Moves: `prompts/judge.txt` (back), a new `prompts/describe.txt`, `brief.py`'s
  call structure, `reason.py`'s target, `fake.py`, `probe.py`
- Does not move: `cases/brief.json`, the marks, and — this is the point —
  `brief-judge`'s promoted baseline

## Why this exists

One sentence, bought with eight runs and $0.8761:

> **Adding a field is not additive.** Asking one call for one more thing changes
> how it does everything else, and **moving the field does not undo it**. If the
> existing behaviour has to be preserved, the new field does not belong in that
> reply at all — it belongs in a second call.

That is not a lesson appended to 0001; it is the whole reason this record
exists. 0001 added `about` to the judge's reply and the judge got worse at
judging — per-case sample disagreement left a 2–6 band it had held over
twenty-one runs and sat at 7–8. The obvious explanation was that the score was
being conditioned on a description written above it, so the field was moved
below the score and measured again. The result was **[7, 7, 7, 8] against
[7, 7, 7, 8]** — identical, to the value. Position was not it.

What is left, after two positions and eight runs, is that **a call asked to
judge and describe is a worse judge than a call asked only to judge**, wherever
the description sits. So the description moves out of that call.

## The decision

**Two calls per item.**

1. **The judging call reverts to byte-identical with the pre-0001 prompt.**
   Not "similar to" — the same file, restoring `config_hash`
   `98fc65b1e49e930e`, which means `brief-judge`'s already-promoted baseline
   becomes the right reference again and **nothing has to be re-baselined**.
   Its stability is not recovered by argument; it is recovered by not touching
   it.
2. **A second, short call describes the item**, and nothing else. No taste, no
   score, no relevance — four lines of prompt instead of fourteen. Its output is
   `about`, and it is what `Faithfulness` checks.

### A consequence worth naming: the context gets honest again

0001's first draft passed `Faithfulness` the item alone, and that was corrected
to *both* prompt files, because the model had been given the taste and a context
without it marked every relevance clause unsupported by construction.

**Under this decision the correction reverses, and for the same reason.** The
describing call is never shown `prompts/judge.txt`. It does not know what I like.
So the context for the faithfulness check is the item and only the item —
which is what 0001 wanted in the first place and could not honestly have.

## Predictions, written before any run

1. **`brief-judge` returns to its old behaviour exactly.** Per-case disagreement
   back inside 2–6; accuracy median 16/21. **This is the falsifier**, and it is
   a hard one: the prompt will be byte-identical to a file measured over
   twenty-one runs, so if the old behaviour does not come back, the prompt was
   never the cause and this whole diagnosis — 0001's and this record's — is
   wrong. There would be no third reordering to try; the next move would be to
   find what else changed.
2. **`about` from a dedicated call is more decomposable than from the combined
   one.** Faithfulness at or above the 0.725 measured under 0001, and
   abstentions near zero, because a call that was never asked to judge has no
   judgement to smuggle into its description.
3. **Cost lands near $0.00101 an item**: $0.000666 for the judging call as
   measured over twenty-one runs, plus roughly $0.00035 for a short describing
   call at about 120 input and 45 output tokens. Against the $0.001022 the
   current single call already costs — within a whisker.
4. **`economics` becomes judgeable**, and 0001's prediction for it applies
   unchanged: 0 abstentions of 5, score 0.6 or better, with the named failure
   mode still *"senza sommario"* when the item does carry one.

### Prediction 4 of 0001 is not inherited. It is made moot

0001 asked whether `about`, written after a judgement, would describe the score
instead of the item. It was never tested, and **under this decision it stops
being askable in this form**: the describing call sees no judgement, because
there is no judgement in its context to see.

That is worth saying plainly rather than quietly dropping. The question is not
answered. It is made unaskable by removing the thing that made it a question,
and if the single-call shape ever returns, it returns unanswered.

## What this costs, honestly

**Money: within a whisker.** Roughly $0.00101 an item against $0.001022 today.

**Robustness: not within a whisker.** Two calls per item is **twice the latency
and twice the failure surface on a morning**, for a field written by a different
call. A digest that fails half as reliably is a real change to something I use
every day, and it is not paid for by the arithmetic being flat.

So the failure semantics are part of this decision and not an afterthought:

- **A failed judging call behaves exactly as it does today.** That path is
  unchanged and its existing defect — a parse failure recorded as `score=0`,
  indistinguishable from an item judged worthless — is unchanged too. It is
  written up at `JUDGE_MAX_TOKENS` and it is 0003's problem, not this one's.
- **A failed describing call must not cost me the item.** The digest still shows
  it, with the score and the reason it already has, and `about` empty — and
  `seen.json` must record *why* it is empty rather than storing an empty string
  that reads like a description of nothing. That is Handbook chapter 0's fourth
  decision applied at the point where this record creates a new way to fail.

**Latency, concretely:** `MAX_JUDGED_PER_RUN` is 50 and the calls are serial, so
a first run goes from up to 50 calls to up to 100. The describing call is the
shorter of the two, so this is less than double in wall clock and more than
nothing.

## Order of work

1. This text. **Checkpoint.**
2. Revert `prompts/judge.txt` and `suite.py`'s schema. Confirm `config_hash` is
   `98fc65b1e49e930e` again and that the existing baseline is accepted.
3. Run `brief-judge` four times. **Read prediction 1 before arguing.** If it
   fails, stop and rethink rather than adjust.
4. Write `prompts/describe.txt` and the describing call, with its failure
   semantics.
5. Point `reason.py` at it, with context = the item alone, and re-measure the
   threshold from a full run.
6. Re-test the `economics` suspension.
7. `README.md`, which describes a two-field reply that will no longer exist.

Estimated spend: four `brief-judge` runs at $0.107 is $0.43, plus two or three
`brief-reason` cycles. Call it **$0.90–$1.20**, and say so before starting
rather than after.
