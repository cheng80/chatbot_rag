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

## Tourism model comparison run

What: Run the committed 20-question tourism evaluation set and compare `supergemma4`, `gemma3`, official `gemma4:e4b`, `qwen3:4b`, and selected Gemma 4 abliterated candidates on grounded answer quality. Native-thinking capable models must be measured in both `think=false` and `think=true` modes.

Why: The endpoint can return structured cards, but public-demo answer quality needs repeatable evidence instead of manual spot checks.

Pros: Catches prompt/model regressions and gives a defensible basis for the default local LLM choice. Keeps Gemma 4-family Korean context quality in the candidate pool while testing whether native thinking is worth the latency.

Cons: Requires running both local models, saving result summaries, and manually scoring answer quality.

Context: Use `data/eval/tourism_20_questions.jsonl`, `scripts/eval_tourism_chat.py`, `scripts/benchmark_tourism_reasoning_models.py`, the backend response contract from `/tourism/chat`, current indexed tourism samples, and the model comparison workflow described in `README.md` and `docs/tourism/tourism_model_reasoning_benchmark.md`. Current local `supergemma4` is 8B-class but exposes only `Capabilities: completion` in Ollama, so do not treat it as native `think=true` capable unless a new tag proves otherwise.

Depends on / blocked by: Rebuilt Chroma index for the tourism sample set and local Ollama models being available.

## LLM reasoning-assist eval and guardrails

What: Expand eval coverage and guardrails for `/tourism/chat` LLM reasoning-assist after deterministic parsing and card retrieval.

Why: Cache, Chroma, Markdown fallback, and TourAPI can handle clear region/condition questions, but real users will ask mixed situation questions such as `오래 걷기 힘든 부모님`, `비 오면 편한 곳`, `아이랑 쉬기 좋은 곳`, or `서울역에서 멀지 않은 곳`. These should not be solved by inventing data, but they may need LLM help for intent interpretation, candidate reranking, and counseling-style wording.

Pros: Keeps hallucination risk low while preserving the product value of an AI 상담형 챗봇. Also gives a clean presentation story: deterministic evidence first, LLM judgment second.

Cons: Requires more eval cases and guardrails so the LLM cannot add unsupported accessibility claims.

Context: `TourismChatService` now has a reasoning-assist decision point, JSON-only reranking prompt, `reasoning_assist_used` response field, and event-log fields. Start from `TourismQueryService`, `TourismChatService`, `TourismQueryEventLogger`, and `data/eval/tourism_20_questions.jsonl`. The LLM should only see the user question plus already retrieved `TourismPlaceCard` candidates and known fields.

Depends on / blocked by: Adding eval cases for complex situation questions. Native Ollama thinking is optional and should be benchmarked separately.

## Frontend tourism UI polish and QA

What: Polish and QA the web tourism check UI, then decide whether to keep it as the demo surface or port the interaction to Flutter.

Why: A minimal static web UI now renders `/tourism/chat` responses, but demo readiness still needs responsive QA, copy review, and visual checks around card density and “확인 필요” states.

Pros: Keeps the API contract visible during development and makes accessibility evidence understandable to non-technical users.

Cons: Adds UI design, responsive behavior, and browser/mobile QA scope beyond backend correctness.

Context: Start from `frontend/web/index.html`, `frontend/web/styles.css`, and `frontend/web/app.js`. The current version is intentionally build-free and focused on backend behavior visibility.

Depends on / blocked by: Stable `/tourism/chat` backend contract and a design/QA pass before demo use.

## Expand admin/legal dong alias QA and product target list

What: Expand QA around `data/processed/admin_region_aliases.json` and decide the product-level 250 실사용 지역 target list.

Why: `TourismQueryService` now reads admin/legal dong aliases, but some names still need product policy. Examples: general-gu names such as `마산합포구` and dong names that can map differently from common expectation.

Pros: Better region clarification, fewer wrong broad-region matches, and a clearer path from nationwide fallback collection to real user language.

Cons: Needs careful ambiguity handling so common names do not silently resolve to the wrong city.

Context: Start from `scripts/build_admin_region_aliases.py`, `data/processed/admin_region_aliases.json`, and `TourismQueryService`.

Depends on / blocked by: Deciding product-level target regions for the 250 실사용 지역 list.
