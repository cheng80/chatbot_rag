# RAG Tutorial Book Planning Discovery

## User Goal

초급 개발자가 Codex, ChatGPT 같은 외부 LLM 없이 이 프로젝트를 처음부터 세팅하고, FastAPI 기반 RAG 시스템과 웹 채팅 기능까지 순차적으로 완성할 수 있는 튜토리얼북 계획을 만든다.

최종 산출물은 다음을 포함해야 한다.

- 초급자용 재현 문서셋
- 단계별 Markdown 1차 정리
- 실제 실행 검증되는 Jupyter Notebook 산출물
- 별도 산출물 폴더
- Notion 플러그인을 사용한 최종 정리

## User Clarification

기존 문서와 경로를 재사용하면 안 된다. 기존 구현과 문서는 참고만 하고, 튜토리얼북은 아무것도 없는 환경에서 새 프로젝트를 제작할 수 있는 토대가 되어야 한다.

Implication:

- The plan must not assume the learner starts from this repository's existing `app/`, `docs/`, `notebooks/`, `scripts/`, or `frontend/` paths.
- The tutorial must define a fresh project skeleton from zero.
- Existing repository files are evidence for architecture and sequencing only.
- Tutorial artifact paths should be isolated and clearly marked as generated educational outputs, not reused production paths.
- Each chapter must include the new files a learner creates from scratch.

Additional user question: if needed, build the tutorial in a separate environment from this project, including a separate Python environment.

Recommendation:

- Yes. The tutorial should use a fully separate project root and Python virtual environment.
- Learner-facing example root: `rag_fastapi_tutorial/`.
- Learner-facing venv: `rag_fastapi_tutorial/.venv/`.
- Verification/artifact root inside this repo for our planning/execution outputs: `tutorial_outputs/rag_fastapi_tutorial/`.
- The production repo's `.venv`, `requirements.txt`, Chroma DB, SQLite DB, generated data, and notebooks must not be treated as learner prerequisites.
- The plan should include a clean-room smoke test that creates the tutorial venv, installs only tutorial dependencies, runs notebook checks, starts FastAPI in a visible terminal/tmux QA scenario only when execution begins, and tears it down.

## Skills Survey

- `omo:ulw-plan`: 반드시 사용. 사용자가 명시적으로 계획 수립을 요청했고, 범위가 5단계 이상이며 여러 모듈과 문서/노트북/Notion 산출물을 포함한다.
- `notion:notion-research-documentation`: 보조 사용. 기존 Notion 페이지 검색과 최종 Notion 문서 생성/정리 단계에 필요하다.
- `document-generate`: 참고 사용. 실제 문서 생성 단계에서 Diataxis 구조를 적용할 때 유용하지만, 현재 턴은 계획 전 탐색과 승인 게이트라 직접 실행하지 않는다.
- `documents`: 제외. DOCX/Word/Google Docs 산출물이 요구되지 않았다.

Sub-agent note: current exposed multi-agent tool says spawn is allowed only when the user explicitly asks for sub-agents/delegation/parallel agent work. The user invoked planning but did not explicitly request sub-agents, so discovery was performed locally.

## Repository Facts

- Worktree status: clean at discovery time.
- Startup instructions require reading `docs/project/next_session_prompt.md`.
- Existing follow-up memo exists at `docs/project/next_session_prompt.md`: "AI 도구 없이도 초급 개발자가 순차적으로 따라 만들 수 있는 재현 문서셋을 Notion 또는 별도 문서로 정리한다."
- Existing docs are indexed in `docs/README.md`.
- General RAG baseline is in `docs/rag/rag_chatbot_design.md`.
- Tourism MVP architecture and implementation history are in `docs/tourism/accessible_tourism_mvp_plan.md`.
- Current progress summary is in `docs/project/progress_overview.md`.
- Web UI operation and QA checklist are in `frontend/web/README.md`.

These repository facts are source evidence only. They must not become learner-facing prerequisite paths.

## Existing Notebook Assets

- `notebooks/api_test.ipynb`: basic API health/stats/chat request checks.
- `notebooks/model_comparison_template.ipynb`: model comparison helper and result export.
- `notebooks/tourism_event_log_analysis.ipynb`: JSONL event log analysis and visualization.

These are useful references, but not sufficient as beginner tutorial notebooks. The plan should create a separate tutorial-notebook output folder with executed notebooks and captured outputs.

## Notion Findings

Notion search did not find a dedicated RAG/FastAPI tutorialbook page.

Closest destination:

- `Codex 정리함`
- child page `프로젝트 기획·워크플로우`

Recommendation: write Markdown and notebooks locally first, verify them, then create a final Notion page under `프로젝트 기획·워크플로우` or `Codex 정리함`.

## Recommended Plan Shape

Use a three-layer tutorial structure:

1. Greenfield foundation: create a brand-new project folder, virtual environment, FastAPI app, config, health route, and first test.
2. General RAG from scratch: create document loading, chunking, embeddings, Chroma, retrieval, prompt building, local Ollama LLM client, `/chat`, and notebook checks.
3. Tourism product extension from scratch: create TourAPI client, cache/fallback data format, region aliases, condition/preference parsing, session memory, intent classifier, eval runner, web UI, and operations/debugging guide.

Each chapter should include:

- concept explanation
- why it exists
- files to create or inspect
- code flow
- commands to run
- notebook verification
- expected result
- common errors and fixes

## Genuine Remaining Decisions

1. Scope depth:
   - Recommended: tutorial builds a clean greenfield educational project from zero, then adds an appendix mapping concepts back to this production repository.
   - Alternative: tutorial attempts to reproduce the full production project directly in a new folder.

2. Notebook folder:
   - Recommended: `tutorial_outputs/rag_fastapi_tutorial/notebooks/` for executed tutorial notebooks and `tutorial_outputs/rag_fastapi_tutorial/md/` for Markdown drafts.
   - Alternative: `docs/tutorial_book/` for Markdown plus `tutorial_outputs/notebooks/` for executed notebooks.

3. Notion destination:
   - Recommended: create a new page under `프로젝트 기획·워크플로우`.
   - Alternative: create under top-level `Codex 정리함`.

4. Notebook execution policy:
   - Recommended: notebooks should be runnable in fallback/offline mode where possible, and live TourAPI cells should be clearly marked as optional when API keys are missing.
   - Alternative: require TourAPI keys and live local Ollama for every notebook.

5. Learner-facing project path:
   - Recommended: tutorial consistently uses a fresh example root named `rag_fastapi_tutorial/`.
   - Alternative: use a generic placeholder such as `my_rag_chatbot/`.

6. Python environment isolation:
   - Recommended: every tutorial command uses the tutorial project's own `.venv` and dependency file, never this repository's `.venv`.
   - Alternative: document environment creation but run verification in this repository's existing `.venv`.

## Proposed Approval Brief

Ask the user to approve the recommended direction before writing `.omo/plans/rag-tutorial-book.md`.
