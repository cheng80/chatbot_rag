---
name: tourism-eval-checkpoint
description: >
  Project-specific regression checkpoint for the accessible tourism chatbot.
  Use when asked to recheck remaining tourism work, rerun tourism chat evals,
  verify noisy/v4/context regressions, update progress docs, or decide whether
  a tourism code change is safe without manual visual review.
---

# Tourism Eval Checkpoint

Use this skill for repeatable `/tourism/chat` regression passes in this repo. It is narrower than generic QA: it knows the project eval assets, the fallback/live policy, and the docs that must stay synced.

## Start

1. Read `AGENTS.md` and `docs/project/next_session_prompt.md`.
2. Check state:

```bash
git status --short
.venv/bin/python --version
```

3. Do not start hidden long-running servers. Direct evals do not need a server.

## Core Checks

Run the smallest set that matches the change. Prefer fallback-only direct eval for deterministic backend checks:

```bash
.venv/bin/python -m pytest tests/test_tourism_query_service.py tests/test_tourism_chat_service.py tests/test_eval_tourism_chat_script.py -q
git diff --check
```

For frontend JS changes:

```bash
node --check frontend/web/app.js
```

For noisy realistic regression:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_noisy_realistic_chat_eval_v1_200.jsonl --output data/generated/tour_api/eval_runs/noisy_realistic_v1_200_latest.jsonl
```

For v4 context impact regression:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_context_v4_chat_impact_eval.jsonl --output data/generated/tour_api/eval_runs/tourism_context_v4_chat_impact_latest.jsonl
```

For challenge/residual hard regression:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_challenge_questions.jsonl --output data/generated/tour_api/eval_runs/tourism_challenge_questions_latest.jsonl
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_residual_hard_chat_20260518.jsonl --output data/generated/tour_api/eval_runs/residual_hard_chat_latest.jsonl
```

## Interpret Results

- Treat `unsupported` copy regressions as code/policy bugs.
- Treat repeated `card_count_low` or `card_missing_required_terms` for 수어/자막, 점자/촉지도, 보조견, strict combo as data coverage candidates unless a clear parser bug exists.
- Do not use tuned diagnostic files as final quality proof. Fresh blind or actual chat eval matters more.
- Keep `TOURISM_LIVE_LOOKUP_ENABLED=false` for stable regression unless the task is specifically live TourAPI behavior.

## Update Docs

When results change the project status, update only relevant sections:

- `docs/project/progress_overview.md`
- `docs/project/next_session_prompt.md`
- `docs/tourism/tourism_eval_questions.md`
- task-specific docs such as `docs/tourism/noisy_realistic_residuals.md`

Record:

- exact command
- input file
- output file
- pass/fail count
- decision: code fix, data gap, skip, or follow-up

## Stop Condition

Finish when the requested eval scope has command output, a clear pass/fail interpretation, and any required doc sync is done. If failures are data coverage rather than code, do not overfit code to the eval.
