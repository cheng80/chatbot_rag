# TODOS

## Persistent TourAPI response cache

What: Persist live TourAPI candidate/detail responses beyond the current process memory cache.

Why: `/tourism/chat` now uses live Markdown cache and Chroma/Markdown fallback before calling live TourAPI. The current in-process live cache is per-process only, so server restarts can repeat API calls for regions missing from persisted Markdown cache.

Pros: Reduces daily quota usage, improves repeated demo latency, and keeps live freshness without re-calling the same region repeatedly.

Cons: Requires TTL/invalidation rules and care around stale accessibility details.

Context: Start from `TourismChatService._live_cards_cache`, `TourAPIService`, and `data/generated/tour_api/`. Keep Chroma/Markdown fallback behavior intact.

Depends on / blocked by: Deciding a TTL and whether the cache should live in SQLite, JSON files, or refreshed Markdown samples.

## Move tourism event logs to SQLite when needed

What: Move `/tourism/chat` JSONL response events into SQLite when filtering, dashboards, retention, or multi-session analysis becomes awkward with flat files.

Why: MVP now writes local JSONL events to `data/generated/tour_api/query_card_events.jsonl`. That is enough for append-only inspection, but SQLite will be better once event volume grows or queries need grouping by region, card, lookup mode, and date.

Pros: Easier aggregate queries, retention policies, deduplication, and future admin/debug views.

Cons: Adds schema migrations, DB lifecycle decisions, and more care around local user question privacy.

Context: Start from `TourismQueryEventLogger`. Preserve the current JSONL event fields: timestamp, message/message_hash, region, area, sigungu, conditions, lookup_mode, degraded, live_api_called, and ranked cards.

Depends on / blocked by: Enough event volume or dashboard need to justify moving beyond JSONL.

## Tourism eval dataset and model comparison

What: Create a 20-question tourism evaluation set and compare `supergemma4` against `gemma3` on grounded answer quality.

Why: The endpoint can return structured cards, but public-demo answer quality needs repeatable evidence instead of manual spot checks.

Pros: Catches prompt/model regressions and gives a defensible basis for the default local LLM choice.

Cons: Requires maintaining eval questions, expected qualities, and model-specific run notes.

Context: Use the backend response contract from `/tourism/chat`, current indexed tourism samples, and the model comparison workflow already described in `README.md`.

Depends on / blocked by: Stable backend response schema and rebuilt Chroma index for the tourism sample set.

## Frontend tourism UI polish and QA

What: Polish and QA the web tourism check UI, then decide whether to keep it as the demo surface or port the interaction to Flutter.

Why: A minimal static web UI now renders `/tourism/chat` responses, but demo readiness still needs responsive QA, copy review, and visual checks around card density and “확인 필요” states.

Pros: Keeps the API contract visible during development and makes accessibility evidence understandable to non-technical users.

Cons: Adds UI design, responsive behavior, and browser/mobile QA scope beyond backend correctness.

Context: Start from `frontend/web/index.html`, `frontend/web/styles.css`, and `frontend/web/app.js`. The current version is intentionally build-free and focused on backend behavior visibility.

Depends on / blocked by: Stable `/tourism/chat` backend contract and a design/QA pass before demo use.
