# Hindsight-on-Comet — proof run (summary only)

Demonstrates the core claim: **stock Hindsight parses an AI browser profile fine once you point it at the right path. The blind spot is enumeration, not parsing.**

- Tool: `pyhindsight` 2026.06 (in `research/lab/.venv`)
- Input: a collected Comet profile (`…-23-comet-after-chat-live`, gitignored raw)
- Command: `hindsight.py -i <Comet User Data> -b Chrome -f jsonl`
- Result: **6,899 records** parsed —
  - 2,559 IndexedDB entries (the perplexity.ai "server-side" chat residue)
  - 3,424 cache entries · 315 cookies · 22 page visits
  - 12 extension installs · 135 extension-storage records
- Elapsed: ~2s.

The full JSONL is a parsed profile (cookie names, cache, history) and is intentionally
NOT committed — regenerate from a collected profile with the command above.
