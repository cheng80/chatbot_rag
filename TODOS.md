# TODOS

## Hybrid live TourAPI fallback for no-result regions

What: Add an offline-first live TourAPI fallback path for `/tourism/chat` when indexed samples return no usable cards.

Why: The backend MVP intentionally uses indexed samples for request-time reliability. A live fallback would improve freshness and regional coverage after the stable contract is proven.

Pros: Gives users a path to fresh public data for regions missing from the local index. Keeps the current demo-stable offline path as the default.

Cons: Adds network latency, TourAPI quota/key failure modes, duplicate-card handling, and cache invalidation complexity.

Context: Start from `TourAPIService`, `TourismNormalizer`, and `TourismChatService`. Preserve the current offline-index behavior first, then call live TourAPI only when retrieval and sample fallback produce no cards.

Depends on / blocked by: Backend safe error handling, degraded-mode diagnostics, and the shared tourism card Markdown codec.

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
