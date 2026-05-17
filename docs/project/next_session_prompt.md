# Next Session Prompt

이 문서는 다음 Codex/Agent 세션에서 바로 이어서 작업하기 위한 시작 프롬프트다. 새 세션을 시작하면 이 문서를 먼저 읽고, 아래 순서대로 현재 상태를 확인한 뒤 작업을 계속한다.

## 시작 프롬프트

```text
이 저장소는 로컬 RAG 챗봇 프로젝트다. 모든 명령은 별도 표기가 없으면 프로젝트 루트에서 실행한다.

먼저 AGENTS.md 와 docs/project/next_session_prompt.md 를 읽고, 아래 작업 순서를 기준으로 현재 상태를 확인해라. conda/Anaconda는 사용하지 않는다. Python은 프로젝트 루트의 .venv 를 사용한다.

작업을 시작하기 전에:
1. git status --short 로 변경 사항을 확인한다.
2. .venv/bin/python --version 으로 로컬 Python을 확인한다.
3. 필요한 경우 .venv/bin/python -m pytest 를 실행해 현재 테스트 상태를 본다.
4. README.md 와 docs/rag/rag_chatbot_design.md 의 실행 순서를 기준으로 RAG 챗봇 작업을 이어간다.
5. 관광 MVP 작업은 docs/project/GOAL.md, docs/tourism/accessible_tourism_mvp_plan.md, docs/tourism/tourism_data_operations.md 의 최신 API 메모를 먼저 확인한다.

로컬 VS Code 설정(.vscode/settings.json)은 git ignore 대상이다. 여기에 있는 python.defaultInterpreterPath 설정은 커밋 대상이 아니다.
```

## 프로젝트 요약

- 목표: ChatGPT/Gemini API 없이 FastAPI + ChromaDB + Ollama 기반 로컬 RAG 챗봇을 만든다.
- 답변 모델: `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M`
- 비교 모델: `gemma3:4b-it-q4_K_M`, `gemma4:e4b`, `qwen3:4b`, `huihui_ai/gemma-4-abliterated:e4b`
- 임베딩 모델: `bge-m3`
- Vector DB: ChromaDB
- API: FastAPI
- 클라이언트 후보: 웹 확인 UI 우선, Flutter는 후순위
- 평가셋: `data/eval/tourism_20_questions.jsonl`은 `/tourism/chat` 20문항 품질 평가 원본이다.
- 노트북: `notebooks/tourism_event_log_analysis.ipynb`는 `/tourism/chat` 이벤트 로그 분석용, `model_comparison_template.ipynb`는 20문항 eval/model comparison 보조용
- 모델 벤치마크: `scripts/benchmark_tourism_reasoning_models.py`는 후보 카드 재랭킹과 Ollama native thinking 여부를 비교한다.
- 문맥 해석 classifier: `app/services/tourism_context_classifier.py`는 `strict_and`, `soft_and`, `or_condition`, `add_condition`, `replace_condition`, `exclude_condition`, `family_context`, `mobility_context`, `specific_facility_required`를 shadow label로 예측한다.
- 문맥 해석 데이터/평가: `scripts/generate_tourism_context_interpretation_data.py`, `scripts/train_tourism_context_classifier.py`, `scripts/eval_tourism_context_classifier.py`
- 핵심어/동의어/오타 보강은 `docs/tourism/tourism_keyword_variant_followup.md`를 먼저 읽는다. 2026-05-18 기준 핵심어 5,000건에서 promote candidate mismatch는 1,645 -> 726 -> 159까지 줄었고, 남은 159건은 무조건 줄이는 대상이 아니다. `리프트` 단독은 차량/예약 의미와 충돌하므로 보류하지만, `휠체어 리프트`, `장애인 리프트`, `승강 리프트`, `계단 리프트`, `지하철 리프트`, `시설 리프트`, `건물 리프트`, `관광시설 리프트`처럼 접근성 설비 맥락이 분명하면 엘리베이터/승강 설비 조건으로 본다. 공공기관으로만 한정하지 않는다. paraphrase는 사전보다 문맥 학습 후보로 다룬다.
- 한국어 오타/띄어쓰기 보정은 FastAPI 내부 로컬 모델만 사용한다. 베이스는 `data/models/tourism_korean_corrector_base`, 최종 fine-tuned 모델은 `data/models/tourism_korean_corrector`다. Hugging Face/GitHub는 준비 단계의 출처일 뿐 런타임 호출 경로가 아니다. 기본 설정은 `TOURISM_KOREAN_CORRECTION_ENABLED=true`, `TOURISM_KOREAN_CORRECTION_RISKY_ONLY=true`, `TOURISM_KOREAN_CORRECTION_ALLOW_DOWNLOAD=false`다.

## 기본 작업 순서

1. 저장소 상태 확인

```bash
git status --short
```

2. Python 환경 확인

```bash
.venv/bin/python --version
.venv/bin/python -m pip --version
```

3. 의존성 확인 또는 설치

```bash
.venv/bin/python -m pip install -r requirements.txt
```

4. 테스트 실행

```bash
.venv/bin/python -m pytest
```

## 최근 미커밋 작업 메모

2026-05-18 한국어 로컬 교정 모델 작업:

- `scripts/prepare_tourism_korean_correction_finetune_data.py`로 correction fine-tuning split을 만들었다. 산출물은 `data/processed/korean_correction_finetune/train.jsonl`, `validation.jsonl`, `summary.json`이다. train 5,453 rows, validation 605 rows다.
- `scripts/materialize_korean_correction_base_model.py --local-files-only`로 `j5ng/et5-typos-corrector` 계열 베이스를 `data/models/tourism_korean_corrector_base`에 materialize했다.
- CPU/MPS 짧은 벤치에서는 CPU 29.83초, MPS 47.58초로 CPU가 빨라 CPU를 채택했다.
- 최종 학습은 `scripts/train_tourism_korean_corrector.py --epochs 5 --batch-size 8 --eval-steps 100 --save-steps 100 --early-stopping-patience 4 --device cpu --output-dir data/models/tourism_korean_corrector`로 수행했다. early stopping으로 2,900 step에서 종료했고 best validation loss는 2,500 step의 0.0631057620이다.
- 이후 `scripts/eval_tourism_korean_corrector.py`로 generation accuracy도 추가 확인했다. 기존 모델 beams=3 기준 exact accuracy 0.7107, compact accuracy 0.7488, mean similarity 0.9494다.
- 추가 fine-tuning 후보 두 개는 loss는 낮췄지만 accuracy가 떨어져 미채택했다. lr=1e-5/wd=0.01 후보는 loss 0.0627810955, exact 0.7091, compact 0.7438이고, lr=5e-6 후보는 loss 0.0616126321, exact 0.7025, compact 0.7339다.
- decoding sweep에서는 기존 모델 beams=1과 beams=4가 exact 0.7124, compact 0.7521로 더 높았다. beams=4는 느리므로 런타임 기본값은 `TOURISM_KOREAN_CORRECTION_NUM_BEAMS=1`로 둔다.
- 다음 fine-tuning에서는 validation loss만 보지 말고 exact/compact accuracy와 실제 `/tourism/chat` 카드 품질을 함께 승격 기준으로 본다.
- 런타임은 `app/services/korean_external_corrector.py`가 로컬 모델 디렉터리만 `local_files_only`로 로드한다. `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`도 설정해 기본 경로에서 네트워크를 사용하지 않는다.
- 서비스 확인 예시: `서울 강남구 근처에서 휄체어 관광지 추천해줘`는 `서울 강남구`와 `휠체어`, `부산엘베있는실내관광지`는 `부산`과 `엘리베이터`로 해석된다.
- 핵심어 변형 5,000건에서 수동/도메인 정규화와 로컬 교정 모델 병행을 비교했다. `scripts/eval_tourism_keyword_correction_coverage.py` 결과는 `data/generated/tour_api/keyword_variant_reports/keyword_correction_coverage_20260518.json`에 있다. 수동/도메인 정규화는 exact 0.8596(4,298/5,000), 로컬 교정 모델 병행은 exact 0.8598(4,299/5,000)이다. promote 후보 exact는 0.9602 -> 0.9604, 개선 1건, 회귀 0건이다. 추가 이득은 작지만 위험 회귀는 없었다. extra condition rows가 532 -> 537로 늘었으므로 원문 대체가 아니라 후보 레이어로만 유지한다.
- 검증: `.venv/bin/python -m pytest tests/test_tourism_query_service.py tests/test_tourism_quality_regression.py tests/test_korean_query_normalizer.py -q`는 200 passed다.

2026-05-18 교수 검토 문서와 조건 모델 추가 작업:

- `docs/project/professor_review_brief.md`와 `docs/project/professor_review_brief.pdf`를 갱신했다. PDF는 A4 출력용 페이지 안에 A5 폭 본문으로 렌더링한다. 10번 섹션은 삭제했고, 현재 강제 페이지 넘김은 `4. 기술 구조`, `6. 데이터와 지역 기준` 앞에만 둔다. 렌더 스크립트는 `scripts/render_professor_review_pdf.py`다.
- `quickspacer`는 후보로만 비교했다. `scripts/eval_tourism_spacing_candidates.py --limit 500` 결과 수동/도메인 정규화 exact 0.838, quickspacer 병행 exact 0.832라 런타임 적용하지 않았다. `점자`, `수어자막`, `바퀴의자`, `이동약자` 같은 보호어를 잘못 쪼개는 회귀가 있었다.
- 조건 라벨 Transformer는 `data/models/klue_roberta_small` 로컬 베이스를 사용해 `scripts/prepare_tourism_condition_transformer_data.py --augment-rows 10000`, `scripts/train_tourism_condition_transformer.py --model-name data/models/klue_roberta_small --epochs 2 --batch-size 32 --learning-rate 2e-5 --save-model --output-dir data/generated/tour_api/condition_transformer_robust_e2`로 학습했다. synthetic validation exact 0.9867/micro-F1 0.9904, synthetic test exact 0.9925/micro-F1 0.9941이지만 과적합 가능성이 있어 런타임 채택은 보류한다. fresh chat-card 평가에서 실제 카드 품질 개선이 확인될 때만 승격한다.
- 이후 기존 120건 중간 길이 평가가 모델 차이를 충분히 드러내지 못한다고 판단해 hard NLU holdout 180건을 추가했다. 결과는 rule/parser, ET5 local, quickspacer가 모두 exact 0.3889/micro-F1 0.5287이고, 기존 RoBERTa가 exact 0.6944/micro-F1 0.7390이었다. 실패 유형 기반 hard 증강 학습셋 16,200건을 만든 뒤 `scripts/train_tourism_condition_transformer.py --model-name data/models/klue_roberta_small --data-dir data/processed/tourism_condition_transformer_hard_aug --output-dir data/generated/tour_api/condition_transformer_hard_aug_e2_fast --epochs 2 --batch-size 32 --learning-rate 2e-5 --save-model --skip-rule-baselines`로 재학습했다. hard holdout 재평가에서 hard 증강 RoBERTa는 exact 0.8167/micro-F1 0.8606, precision 0.8659, recall 0.8554로 개선됐다.
- 실제 `/tourism/chat` 기준으로도 확인했다. 중간 길이 v4 120건은 기본 rule/parser와 hard 증강 RoBERTa 보조가 모두 100/120 통과로 회귀가 없었다. hard 의미 chat 40건은 기본 rule/parser 21/40 통과, hard 증강 RoBERTa 보조 36/40 통과다. 따라서 로컬 `.env`에는 `TOURISM_CONDITION_TRANSFORMER_ENABLED=true`, `TOURISM_CONDITION_TRANSFORMER_MODEL=./data/generated/tour_api/condition_transformer_hard_aug_e2_fast/model`, `TOURISM_CONDITION_TRANSFORMER_METRICS_PATH=./data/generated/tour_api/condition_transformer_hard_aug_e2_fast/metrics.json`를 적용했다. 모델 산출물은 git ignore 대상이라 새 환경에서는 학습 명령으로 다시 만들어야 한다.
- 중간 길이 실제 대화형 blind eval v3는 `scripts/generate_tourism_context_blind_chat_eval.py --variant v3`로 생성했고 direct 평가 20건 중 18건 통과했다. 실패는 대전 시각장애/안내견/점자와 강릉 보조견 후속 지역 변경 케이스다. 둘 다 모델 epoch보다 데이터/조건/지역 확장 정책 검토 대상이다.
- `강남구 근처`는 사용자가 보통 강남권을 기대하므로 상위 광역 지역 확장 신호로 쓰지 않는다. `근처`, `주변`, `가까운`, `인근`은 자동으로 서울 전체 후보를 섞지 않고, `서울 전체로 넓혀줘`, `범위 넓혀줘`처럼 명시적으로 확장한 경우에만 광역 후보를 포함한다. 안내 문구의 `expanded`도 실제 반환 카드에 질의 시군구 밖 카드가 포함됐는지로 판단한다. 관련 단위 테스트는 `tests/test_tourism_chat_service.py::test_tourism_chat_expansion_copy_requires_actual_outside_sigungu_cards`와 `tests/test_tourism_chat_service.py::test_tourism_chat_keeps_nearby_sigungu_inside_requested_region`이다.
- 중간 길이 v4 120건 평가셋은 `scripts/generate_tourism_medium_chat_eval_v4.py`로 생성했다. 결과 파일은 `data/eval/tourism_context_medium_chat_eval_v4_120.jsonl`이다. `scripts/compare_tourism_medium_chat_models.py`로 rule/parser, ET5 local, quickspacer, RoBERTa-small candidate를 같은 `/tourism/chat` 카드 품질 기준으로 비교했다. 결과는 `data/generated/tour_api/medium_chat_model_compare_20260518/summary.json`와 `docs/tourism/tourism_medium_chat_model_comparison.md`에 정리했다. 네 변형 모두 100/120 통과, 조건 라벨 micro-F1 0.8380으로 동일해 런타임 승격하지 않는다. 실패는 모델보다 청각/시각 접근성 근거 카드 부족, 일부 지역 엘리베이터/유모차 커버리지, 보조견 조건 유지 후 지역 변경 같은 데이터/정책 문제다.
- `서울 전체로 넓혀서 더 찾아줘` 같은 명시적 확장 후속질문이 이전 조건을 잃고 일반 관광지 요청으로 처리되던 문제를 수정했다. 이제 `allow_region_expansion`도 대화 맥락 유지 조건으로 인정한다. 관련 단위 테스트는 `tests/test_tourism_chat_service.py::test_tourism_chat_explicit_expand_followup_keeps_previous_condition`이다.
- 검증: `.venv/bin/python -m pytest tests/test_tourism_chat_service.py tests/test_tourism_query_service.py tests/test_korean_query_normalizer.py -q`는 89 passed다. `git diff --check`와 새 스크립트 `py_compile`도 통과했다.

2026-05-17 마지막 작업은 문맥 해석 v4 rotating blind와 실제 `/tourism/chat` 카드 적합성 v2 평가 추가다. 다음 세션에서 `git status --short`에 아래 파일들이 남아 있으면 같은 작업 묶음으로 보면 된다.

- `app/services/tourism_context_classifier.py`
- `scripts/generate_tourism_context_rotating_blind_holdout.py`
- `scripts/generate_tourism_context_blind_chat_eval.py`
- `data/eval/tourism_context_rotating_blind_holdout_20260517_v3.jsonl`
- `data/eval/tourism_context_rotating_blind_holdout_20260517_v4.jsonl`
- `data/eval/tourism_context_blind_chat_eval_v2.jsonl`
- `docs/tourism/tourism_eval_questions.md`
- `docs/tourism/ml_evaluation_governance.md`
- `docs/project/progress_overview.md`
- `docs/project/next_session_prompt.md`

작업 내용은 v3 rotating blind 80건 생성과 경계 보강 이후, 새 v4 rotating blind 80건과 실제 `/tourism/chat` 카드 적합성 v2 15건을 추가한 것이다. `scripts/generate_tourism_context_rotating_blind_holdout.py`는 `--variant v4`를 지원하고, `scripts/generate_tourism_context_blind_chat_eval.py`는 `--variant v2`를 지원한다. v3 라벨 검수 중 `촉지도나 점자 안내`는 OR, `카페 말고`, `공연장은 빼고`는 exclude로 고쳤다.

확인한 수치:

- v3 최초: hybrid LinearSVC exact 0.6625 / micro-F1 0.8560
- v3 보강 후: hybrid LinearSVC exact 0.9875 / micro-F1 0.9960
- v3 보강 후 rule-only: exact 1.0000 / micro-F1 1.0000
- independent validation: exact 0.9242 / micro-F1 0.9741
- specific-facility adversarial: exact 0.9918 / micro-F1 0.9946
- v1 after patch: exact 0.9750 / micro-F1 0.9919
- v2 after patch: exact 0.9375 / micro-F1 0.9799
- `.venv/bin/python -m pytest -q`: 274 passed
- v4 fresh rule-only: exact 0.7375 / micro-F1 0.9091
- v4 fresh hybrid LinearSVC: exact 0.7250 / micro-F1 0.9012
- v4 fresh hybrid LogisticRegression: exact 0.7125 / micro-F1 0.8968
- chat blind v2: 15/15 통과
- `.venv/bin/python -m pytest -q`: 275 passed

v1/v2/v3 보강 후 고득점은 최종 품질 점수가 아니라 해당 파일 실패를 보고 고친 tuned diagnostic이다. v4는 fresh blind라 현재 일반화 진단 신호로 보고, chat blind v2 15/15는 실제 카드 품질이 아직 깨지지 않았다는 별도 신호로 본다. 하이브리드 LogisticRegression은 계속 비교 대상이지만 v4 최고는 아니며, 현 런타임은 rule/parser + shadow ML 구조를 유지한다. 다음 문맥 작업은 모델 교체나 즉시 룰 보강이 아니라 v4 failure bucket, 특히 `mobility_context`, `exclude_condition`, `soft_and`, `strict_and`, `specific_facility_required`가 실제 `/tourism/chat` 카드 반환에 영향을 주는지 선별하는 것이다.

이후 UI/UX 앱형 보강도 이어서 반영했다. 다음 세션에서 `git status --short`에 아래 파일들이 함께 남아 있으면 같은 미커밋 작업 묶음으로 보면 된다.

- `frontend/web/index.html`
- `frontend/web/styles.css`
- `frontend/web/app.js`
- `frontend/web/README.md`

UI 변경 내용은 개발 모드와 릴리즈형 사용자 화면 분리, `DBG` 디버그 패널, release 모드 내부 진단 숨김, 사용자 질문 말풍선, bot typing indicator, 입력/오류/카드 반환 toast, 카드 등장 애니메이션, release 초기 빈 상담 상태, 모바일 1열 카드 레이아웃이다. 확인한 정적 검사는 `node --check frontend/web/app.js`, `git diff --check`, debug/release 구조 Node audit 통과다. 서버는 AGENTS 규칙 때문에 Codex 숨은 세션에서 띄우지 않았으므로, 실제 FastAPI 연결 시각 QA는 VS Code/Cursor 같은 에디터 내장 터미널의 새 터미널에서 서버를 실행한 뒤 진행해야 한다. 여기서 말하는 터미널은 외부 터미널 앱이 아니라 사용자가 로그와 종료 상태를 직접 볼 수 있는 에디터 내장 터미널이다.

UI 작업 완료 판정 전에는 Browser use와 Computer use를 모두 사용해 실제 유저처럼 대화형 QA를 수행한다. fallback-only가 아니라 live TourAPI 사용 가능 모드로 테스트해야 하며, 서버는 `TOURISM_LIVE_LOOKUP_ENABLED=true` 또는 기본 true 상태로 실행한다. 단문 20개가 아니라 한 세션 안에서 이어지는 질문을 포함해야 한다. QA 횟수는 기본 개발 모드 `/tourism-ui/` 20회 이상, 릴리즈 모드 `/tourism-ui/?mode=release` 20회 이상으로 분리한다. 필수 포함 범위는 지역 선택, 모호 지역 clarification, 조건 추가, 조건 교체, 조건 제외, 더 보기, 빈 결과 또는 부족 안내, 카드 상세 펼침, 지도 검색, Help 모달, 기본 개발 모드의 `DBG` 진단과 live/cache/fallback 경로 표시, release 모드 내부 진단 숨김이다.

2026-05-17 중간 QA 결과:

- 실제 `Browser` 플러그인 skill은 설치되어 있었지만, 이 세션에서 필요한 `node_repl/js` 실행 도구가 노출되지 않았다. `tool_search`로 `node_repl js`, `mcp__node_repl__js`, `Browser in-app browser`를 다시 검색했지만 Computer Use만 노출됐다. 원인 확인 결과 `browser@openai-bundled`와 `chrome@openai-bundled` 플러그인에는 `mcpServers`가 없고 skill + `scripts/browser-client.mjs`만 있으며, Browser skill은 별도 JavaScript 실행 MCP가 이미 노출되어 있다는 전제에서 동작한다. `codex mcp list`에도 `computer-use`, `nanobanana`, `stitch`만 있고 `node_repl`/`js_repl` 계열 서버는 없다. `codex features list`에서 `browser_use`와 `in_app_browser`는 true지만 `js_repl`은 removed 상태라 `--enable js_repl`로도 도구가 생기지 않는다. 따라서 재시작 문제가 아니라 현재 Codex/VS Code 호스트의 Browser 플러그인 패키징 또는 실행 도구 노출 불일치로 보는 것이 맞다.
- 사용자가 설치 허용을 줘서 `.venv`에 Playwright를 설치하고 Chromium으로 실제 브라우저 자동 QA를 수행했다. 설치 명령은 `.venv/bin/python -m pip install playwright`, `.venv/bin/python -m playwright install chromium`이다.
- Computer Use로 Google Chrome에서 개발 모드와 릴리즈 모드를 열어 시각 확인했다. 개발 모드는 `DEV`, `DBG`, API 입력, Swagger/ReDoc/OpenAPI 링크, 진단 패널이 보였다. 릴리즈 모드는 `DBG`/API/진단 패널 없이 빈 상담 상태로 시작했다.
- Playwright 결과 요약은 `docs/project/tourism_ui_midcheck_20260517.md`에 기록했다. 원본 JSON/스크린샷은 `data/generated/tour_api/ui_qa/` 아래에 있다. 개발 모드 18/20, 릴리즈 모드 20/20, 전체 38/40 통과. lookup mode는 cache 22, live_top_up 4, sample 5, indexed 7, clarification 1, unknown 1이며 live_top_up 관측으로 fallback-only가 아님을 확인했다.
- 실패 2건: `수어 안내나 자막 안내 있는 곳으로 다시 찾아줘`가 `unknown` 0장으로 끝났고, `오늘 환율 알려줘`가 unsupported가 아니라 관광 카드로 응답했다.
- UI는 `session_id`를 보내도록 수정했다. 브라우저 안에서 이어지는 `더 보기`, `그중`, `말고`, 지역 변경 질문이 같은 세션 맥락을 쓸 수 있다. `비우기`를 누르면 새 세션으로 초기화한다.
- 이후 실패 2건은 코드 보강했다. `수어 안내나 자막 안내 있는 곳으로 다시 찾아줘`는 지역 없는 `다시 찾아줘` 후속 조건에서 이전 조건을 누적하지 않고, 카드가 없으면 지역/조건 확장 후속 제안을 반환한다. `오늘 환율 알려줘`는 `unsupported`로 처리한다. 부정 표현인 `응급실은 말고 관광지만 계속`은 기존 관광 맥락을 유지한다. `.venv/bin/python -m pytest -q`는 275 passed였다. 실제 개발/릴리즈 각 20회 브라우저 재QA는 아직 남아 있다.
- 외부 Terminal.app의 보이는 `uvicorn` 서버로 실제 FastAPI를 띄운 뒤 Playwright Chromium 재QA를 완료했다. 개발 모드 20/20, 릴리즈 모드 20/20, 전체 40/40 통과다. 결과는 `data/generated/tour_api/ui_qa/regression_20260517_fixed/tourism_ui_regression_20260517_fixed.json`와 `.md`에 있다. 대표 스크린샷은 같은 폴더의 `debug_initial.png`, `debug_final.png`, `release_initial.png`, `release_final.png`, `mobile_cards_viewport.png`다. 이전 `live_visual_20260517` 모바일 full-page 캡처는 타이밍상 카드가 희미하게 보여 검증용으로 쓰지 않고, `live_visual_20260517_fixed` 또는 `regression_20260517_fixed`의 viewport 캡처를 사용한다.

문맥 해석 classifier를 변경했다면 다음 순서로 별도 평가를 갱신한다.

```bash
.venv/bin/python scripts/generate_tourism_context_interpretation_data.py
.venv/bin/python scripts/train_tourism_context_classifier.py
.venv/bin/python scripts/eval_tourism_context_classifier.py
.venv/bin/python scripts/prepare_tourism_context_finetune_data.py
```

2026-05-17 기준 문맥 해석 locked test 4,800건에서 `soft_and`를 참고/선택/완화 의도가 명시된 경우로 좁힌 뒤 최초 hybrid LogisticRegression micro-F1은 0.9688이었다. 이후 `아니면 제외` strict 처리, 가족/이동/soft 라벨 보정, `휠체어 위주`, `조용한 곳` 경계 보강 뒤 한때 locked test exact 0.9706/micro-F1 0.9860까지 올랐다. v2 rotating blind 보강 뒤 최신 locked test는 exact 0.9548/micro-F1 0.9803이다. independent validation 1,200건의 1.0000 또는 고득점은 실사용 품질 점수가 아니라 현재 작성된 경계 회귀셋 통과 결과로만 본다.
KoBERT/KLUE-RoBERTa 파일럿 split은 `data/processed/context_finetune/`에 있으며 train 6,886건, validation 1,200건, test 4,800건이다. validation은 `data/eval/tourism_context_independent_validation.jsonl`에서 오며, `--strict-family-split`으로 train/validation template family overlap과 text overlap을 금지한다.
독립 validation 1,200건은 한 차례 exact 0.9000/micro-F1 0.9615까지 떨어지며 오류 bucket을 드러냈고, v2 보강 뒤 최신 hybrid 기준 exact 0.9242/micro-F1 0.9741이다. `specific_facility_required`도 locked test 1.0000을 의심해 `data/eval/tourism_context_specific_facility_adversarial_holdout.jsonl` 980건을 추가했고, 최초 exact 0.7102/micro-F1 0.8809에서 최신 exact 0.9918/micro-F1 0.9946이 됐다. 고득점이 반복되므로 다음 작업은 같은 셋 반복이 아니라 새 rotating blind와 실제 `/tourism/chat` 카드 적합성 평가 추가다.
사람이 직접 쓴 holdout을 당장 확보할 수 없어 `scripts/generate_tourism_context_blind_holdout.py`로 Codex LLM blind holdout 80건을 추가했다. 기존 context generator family를 재사용하지 않는다. 최초 평가는 rule-only exact 0.4750/micro-F1 0.7304, LogisticRegression 단독 exact 0.5125/micro-F1 0.7512, hybrid LogisticRegression exact 0.4500/micro-F1 0.7296이다. 오류 bucket 보강 후 fixed blind는 hybrid LinearSVC exact 0.6250/micro-F1 0.8340까지 올랐지만, 같은 파일을 보강에 사용했으므로 최종 품질 점수로 쓰지 않는다. rotating blind `data/eval/tourism_context_rotating_blind_holdout_20260517.jsonl` 80건은 최초 hybrid LinearSVC exact 0.5750/micro-F1 0.8163이었고, 같은 파일을 보고 보강한 뒤 exact 0.9750/micro-F1 0.9919가 됐다. v2 `data/eval/tourism_context_rotating_blind_holdout_20260517_v2.jsonl` 80건은 최초 hybrid LogisticRegression exact 0.6000/micro-F1 0.8245였고, 경계 룰 보강 뒤 hybrid LinearSVC exact 0.9250/micro-F1 0.9719다. v3 `data/eval/tourism_context_rotating_blind_holdout_20260517_v3.jsonl` 80건은 최초 hybrid LinearSVC exact 0.6625/micro-F1 0.8560이었고, 라벨 검수와 경계 룰 보강 뒤 hybrid LinearSVC exact 0.9875/micro-F1 0.9960, rule-only exact/micro-F1 1.0000이 됐다. v4 `data/eval/tourism_context_rotating_blind_holdout_20260517_v4.jsonl` 80건은 fresh 기준 rule-only exact 0.7375/micro-F1 0.9091, hybrid LinearSVC exact 0.7250/micro-F1 0.9012, hybrid LogisticRegression exact 0.7125/micro-F1 0.8968이다. v1/v2/v3 보강 후 수치는 모두 tuned diagnostic이고, v4는 다음 분석 기준이다. 실제 `/tourism/chat` blind eval은 최초 10건 중 9건 통과였고, 시장 제외+조용한 곳 실패를 고친 뒤 10/10 통과했다. 확장 `data/eval/tourism_context_blind_chat_eval_v2.jsonl` 15건도 fallback-only direct 실행에서 15/15 통과했다.
PyTorch/Transformers 파일럿은 기본 의존성과 분리된 `requirements-ml.txt`를 쓴다. 실행은 `.venv/bin/python -m pip install -r requirements-ml.txt` 후 `.venv/bin/python scripts/prepare_tourism_context_finetune_data.py --validation-ratio 0 --extra-train-input data/processed/tourism_context_hard_style_extra_train.valid.jsonl --hard-validation-input data/eval/tourism_context_independent_validation.jsonl --strict-family-split`, `.venv/bin/python scripts/train_tourism_context_transformer.py --epochs 3 --batch-size 32 --learning-rate 2e-5 --model-name klue/roberta-small --baseline-metrics data/generated/tour_api/context_classifier_eval_independent_test_latest.json --output-dir data/generated/tour_api/context_transformer_independent_validation` 순서다. 독립 validation 적용 뒤 `klue/roberta-small`은 validation exact 0.8417/micro-F1 0.9241, locked test 단독 exact 0.7165/micro-F1 0.8594, rule hybrid locked test exact 0.8969/micro-F1 0.9474다. 최신 기준선 hybrid LogisticRegression locked test exact 0.9187/micro-F1 0.9688을 넘지 못하고 latency도 느려 런타임 채택은 보류한다.
ML/DL 실험은 `docs/tourism/ml_evaluation_governance.md`를 먼저 적용한다. validation 1.0000, focused holdout 1.0000, 단일 accuracy 상승은 채택 근거가 아니다. `.venv/bin/python scripts/audit_tourism_ml_experiment.py --transformer-metrics data/generated/tour_api/context_transformer_independent_validation/metrics.json --context-baseline-metrics data/generated/tour_api/context_classifier_eval_independent_test_latest.json`로 overfit/underfit/leakage/hard holdout gap/latency를 감사한다. 현재 판정은 `do_not_adopt_runtime`이다.
Codex/LLM으로 hard-style 학습셋을 만들 때는 `docs/tourism/context_llm_dataset_generation.md`를 따른다. 프롬프트 생성은 `.venv/bin/python scripts/build_tourism_context_llm_generation_prompt.py --target-rows 300 --batch-id 001`, LLM 출력 검수는 `.venv/bin/python scripts/validate_tourism_context_llm_dataset.py --input ...`, 병합은 `.venv/bin/python scripts/prepare_tourism_context_finetune_data.py --extra-train-input ...` 순서다.
핵심어/동의어/오타 후보는 `scripts/build_tourism_keyword_variant_generation_prompt.py`, `scripts/generate_tourism_keyword_variant_seed.py`, `scripts/validate_tourism_keyword_variant_dataset.py`, `scripts/build_tourism_keyword_promotion_candidates.py`로 관리한다. 리포트만 만들고 끝내지 말고, `parser_missing_conditions`와 `parser_extra_conditions`를 나눠 원인을 고친 뒤 다시 검증한다. 단독 `리프트`, 넓은 `편한 곳`류 paraphrase, 미지원 예약/차량 의미와 충돌하는 표현은 바로 런타임 사전에 넣지 않는다. 접근성 설비 맥락이 붙은 리프트 표현은 예외적으로 조건 후보로 다룬다.
SuperGemma4 문맥 보조는 `.venv/bin/python scripts/eval_supergemma_context_labels.py`로 재평가한다. 2026-05-17 이전 1,320건 holdout의 전체 오답 221건 실험에서는 exact가 0.8326에서 0.8879로 올랐지만 micro-F1이 0.9179에서 0.9105로 내려가 기본 런타임 보조 판단자로 채택하지 않았다. QA/재라벨링 보조로만 둔다. 4,800건 holdout 기준 selective 재평가는 아직 하지 않았다.

5. Ollama 모델 준비 확인

```bash
ollama list
```

필요 시:

```bash
ollama pull bge-m3
ollama pull gemma3:4b-it-q4_K_M
ollama pull gemma4:e4b
ollama pull qwen3:4b
# 선택: 사용자 제안 Gemma 4 abliterated 후보
ollama pull huihui_ai/gemma-4-abliterated:e4b
ollama run hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M
```

6. 문서 색인

```bash
.venv/bin/python scripts/ingest_all.py
```

임베딩 모델 변경 후에는 기존 벡터를 재사용하지 말고 재색인한다.

```bash
.venv/bin/python scripts/rebuild_index.py
```

7. 서버 실행

서버류 실행 원칙:

- `uvicorn`, `cloudflared`, `python3 -m http.server` 같은 장시간 실행 프로세스는 Codex 백그라운드 세션으로 조용히 띄우지 않는다.
- 에디터의 새 터미널을 열고 사용자가 로그와 종료 상태를 볼 수 있게 실행한다.
- FastAPI 서버와 Cloudflare 터널은 서로 다른 터미널에서 실행한다.

FastAPI와 Cloudflare는 같은 명령이 아니다. 외부 확인이 필요하면 터미널을 2개 연다.

터미널 1: FastAPI 서버

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

오늘처럼 TourAPI 호출을 더 쓰지 않을 때는 fallback-only로 실행한다.

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

터미널 2: Cloudflare Quick Tunnel

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

8. API 확인

```bash
curl http://localhost:8000/health
curl http://localhost:8000/documents/stats
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"환불은 언제까지 가능한가요?"}'
```

## 현재 로컬 환경 메모

- conda/Anaconda는 이 프로젝트에서 사용하지 않는다.
- `.venv`가 이미 존재하며, 확인 시점의 Python은 `3.13.7`이다.
- 관광 API는 `.env`의 `TOUR_API_BASE_URL=https://apis.data.go.kr/B551011/KorService2`를 기본 목록/검색/공통 상세 조회에 사용한다.
- `KorService2`를 코드에서 `KorWithService2`로 강제 치환하지 않는다.
- 무장애 상세 조회는 별도 `TOUR_API_ACCESSIBLE_BASE_URL=https://apis.data.go.kr/B551011/KorWithService2`를 사용한다.
- `.env`에는 `TOUR_API_SERVICE_KEY`와 `TOUR_API_ACCESSIBLE_SERVICE_KEY`가 있다. 현재는 같은 인증키지만 서비스별 분리를 위해 둘 다 유지한다.
- 2026-05-15 재테스트 결과 `areaCode2`, `searchKeyword2`, `areaBasedList2`는 200 OK였다. 단, `areaBasedList2`에 `listYN=Y`를 넣으면 `INVALID_REQUEST_PARAMETER_ERROR(listYN)`가 발생하므로 넣지 않는다.
- 공공데이터포털 화면에서 `한국관광공사_무장애 여행 정보` 개발계정 승인은 확인됐다.
- 승인 반영 후 `KorWithService2/areaCode2`, `KorWithService2/detailWithTour2`, `KorWithService2/areaBasedList2` 호출이 200 OK로 확인됐다.
- 전국 시군구 코드는 수동 하드코딩하지 않는다. `scripts/fetch_tour_area_codes.py`로 `data/processed/tour_area_codes.json` 캐시를 만들고 `TourismQueryService`가 이 캐시를 우선 사용한다. 중복되는 시군구 별칭은 캐시에 넣지 않는다.
- 지역 추천 정책은 다음과 같다. 사용자가 시군구를 명시하면 해당 시군구 결과만 먼저 제공한다. 결과가 3개 미만이어도 자동으로 다른 구/군을 섞지 않고 부족 안내를 한다. `근처`, `주변`, `가까운`, `인근`은 시군구 안의 가까운 후보 선호로 보고 상위 광역 지역 확장 신호로 쓰지 않는다. `서울 전체로 넓혀줘`, `범위 넓혀줘`처럼 명시적 확장 표현이 있을 때만 상위 광역 지역 후보를 함께 포함하고 답변에 확장 사실을 명시한다. 기본 추천은 최대 5장이다. 후보가 5장보다 많으면 `suggested_messages`에 `더 보기` 후속 질문을 넣고, 사용자가 `더 보기`, `전체`, `전부`, `20곳` 같은 의도를 말하면 확인된 후보를 가능한 만큼 반환한다. 저장된 후보가 5장 미만이고 live TourAPI를 사용할 수 있으면 자동 호출하지 않고 사용자에게는 `최신 정보 더 찾기` 후속 버튼을 제공한다. 답변 문구에는 API/fallback/cache 같은 내부 용어를 노출하지 않는다. 사용자가 이 버튼을 누른 경우에만 live TourAPI로 후보를 보강한다.
- 다음 세션에서 지역 코드가 이상하면 아래 캐시 재생성부터 실행한다.

```bash
.venv/bin/python scripts/fetch_tour_area_codes.py
```

- `/tourism/chat`은 지역이 확정되면 이전 live 조회 Markdown 캐시를 먼저 확인한다. live 캐시에 없으면 Chroma 색인과 로컬 Markdown fallback을 확인한다. 그래도 같은 지역 카드가 없고 API 키가 있으면 live TourAPI 후보 조회를 사용한다. 저장된 후보가 1-4장만 있을 때는 자동으로 live를 호출하지 않고 `최신 정보 더 찾기` 후속 버튼으로 명시 확인을 받는다. 같은 지역 반복 요청은 프로세스 메모리 캐시와 `data/generated/tour_api/live_markdown/` Markdown 캐시를 사용한다. `data/raw/tourism_accessible/`는 계획 수집한 fallback/색인 후보로 유지한다.
- TourAPI 호출은 `TourAPIService`에서 엔드포인트별 일일 1,000건 한도를 확인한 뒤 기록한다. 사용량 로그 기본 경로는 `data/generated/tour_api/usage/daily_usage.json`이다. 로그 도입 전 당일 산출물을 반영해야 하면 `.venv/bin/python scripts/bootstrap_tour_api_usage.py`로 오늘 수정된 raw/live 산출물 기준 최소 사용량을 부트스트랩한다.
- 질문 조건 인식은 `휠체어/무장애/베리어프리`, `유모차/유아차/수유/기저귀/어린이`, `고령자`, `주차`, `화장실`, `접근로`, `대중교통`, `엘리베이터` 중심이다. 카드 랭킹은 조건별 raw 편의정보 키와 태그/본문 근거를 함께 점수화하고, 답변에는 카드별 핵심 편의정보 근거를 짧게 포함한다.
- 챗봇 품질 회귀 테스트는 `tests/test_tourism_quality_regression.py`에 있다. 지역 해석 110개, 조건 인식 29개, 카드 랭킹/근거 문장 케이스를 포함한다.
- `/tourism-ui/`는 정적 HTML/CSS/JS 기반 메신저형 시연 UI다. 디자인 기준은 `docs/design/tourism_chatbot_DESIGN.md`에 있다. 카드 위 긴 답변은 기본 접힘 처리하고, 카드에는 `상세 정보` 펼침과 장소명/주소 기반 `지도 검색`을 제공한다.
- `/tourism-ui/` 기본값은 개발 모드다. `DBG` 패널에 API 주소, API 문서 링크, 응답 경로 등 내부 확인 UI가 보인다. 사용자 시연용으로 내부 상태를 숨기려면 URL에 `?mode=release` 또는 `?debug=0`을 붙인다.
- release 모드는 초기 예시 카드를 보여주지 않고 빈 상담 상태에서 시작한다. 사용자에게는 지역 선택, 질문 말풍선, 타이핑 표시, 답변, 추천 카드, 출처, 방문 전 확인 문구만 보이게 한다.
- 한국관광공사 열린관광 사이트의 상세 URL은 콘텐츠 ID만으로 안정적인 공개 상세 링크를 만들 수 없어 `access.visitkorea.or.kr/detail/...` 추정 링크 생성을 중단했다. 기존 캐시/색인에 남아 있는 해당 링크도 UI에서 숨기고 출처명만 표시한다.
- `/tourism/chat` 응답 이벤트는 `data/generated/tour_api/query_card_events.jsonl`에 JSONL로 저장한다. 기본값은 원문 질문을 저장하지 않고 `message_hash`만 저장한다. 필요할 때만 `TOURISM_QUERY_EVENT_LOG_INCLUDE_MESSAGE=true`로 원문 저장을 켠다.
- `/tourism/chat`의 LLM 추론 보조는 기본값이 꺼져 있다. 복합 상황 질문 품질 비교나 실험이 필요할 때만 `TOURISM_REASONING_ASSIST_ENABLED=true`로 켠다. 응답과 이벤트 로그의 `reasoning_assist_used`, `reasoning_assist_notes`로 사용 여부와 확인 필요 메모를 확인한다.
- 추론 보조를 끈 기본 모드에서 질문 의도 파악이 달라지는지 확인하려면 같은 eval을 ON/OFF로 실행해 `lookup_mode`, 카드 수, 카드 ID 순서, `warnings`, `suggested_messages`를 비교한다.
- 2026-05-15 로컬 모델 추론 보조 벤치마크를 실행했다. 결과 요약은 `docs/tourism/tourism_model_reasoning_benchmark.md`에 있다. 현재 결론은 MVP 기본 추론 보조는 OFF이며, 켜더라도 native `think=false`로만 실험하는 것이다. `gemma4:e4b`와 `huihui_ai/gemma-4-abliterated:e4b`는 native thinking이 동작하지만 30초 이상 지연됐고, `qwen3:4b`는 현재 프롬프트에서 JSON/한국어 계약을 지키지 못했다.
- 생성된 모델 벤치마크 원본은 `data/generated/tour_api/model_benchmarks/` 아래에 있으며 git ignore 대상이다. 필요하면 `scripts/benchmark_tourism_reasoning_models.py`로 다시 만든다.
- 개발/QA 기본 모드는 `cache/fallback-first + live-on-miss`이다. 호출량 또는 시연장 네트워크가 불안하면 `TOURISM_LIVE_LOOKUP_ENABLED=false`로 끄고 fallback-only로 운영한다. 장기 신선도는 Post-MVP 주기적 갱신 배치로 해결한다.
- offline-index 우선 방식과 cache/fallback-first + live-on-miss 방식의 차이, 장단점, 되돌림 기준은 `docs/tourism/tourism_response_strategy_decision.md`를 먼저 확인한다.
- 2026-05-15 수집은 중단했다. 추가 수집 전에는 `docs/tourism/tourism_data_operations.md`의 호출량 메모와 다음 작업 섹션을 먼저 확인한다.
- fallback 데이터는 `mvp`, `fallback-1`, `fallback-2`, `fallback-3` 배치 수집과 시군구 fallback 확장 수집, 서귀포시 보강 수집을 진행했다. `data/raw/tourism_accessible` 기준 904개 Markdown이고, Chroma 기준 905개 문서/914개 청크가 색인됐다.
- 시군구 fallback은 TourAPI 지역 코드 234개 중 228개 시군구가 3장 이상 확보됐다. 청원군, 마산시, 진해시, 남제주군, 북제주군은 부족 지역으로 표시하지 않는다. 이들은 TourAPI 지역 코드 캐시에 남아 있는 과거 지명 입력을 현재 행정구역 기준으로 안내하기 위한 예외 매핑이다. 사용자 화면에는 “현재는 청주시/창원시/서귀포시/제주시 기준으로 안내드릴게요”처럼 짧게 말하고, 내부 코드/정규화/TourAPI 표현을 쓰지 않는다. 공식 무장애 상세 3장 미만 지역은 계룡시 1장이다. 2026-05-17 재수집에서도 무장애 전용 목록은 1건만 반환했고, 일반 관광 검색 8건 중 나머지 7건은 무장애 상세가 없어 접근성 카드로 편입하지 않았다. 행안부 현행 시군구 매칭은 228개이고, 250개는 확정 행정구역 수가 아니라 행정시/일반구/생활권 표현을 포함할 수 있는 제품 목표 상한으로만 둔다.
- 2026-05-15에는 사용자의 명시 승인으로 엔드포인트별 500건 평시 안전치를 일시적으로 풀고 1,000건 기준까지 수집을 확장했으나, `detailCommon2` 429 응답 후 즉시 중단했다. 같은 quota window에서는 추가 수집하지 않는다.
- 관광 챗봇 eval은 2026-05-16에 기존 100문항/30문항/50시나리오에서 신규 274문항/97시나리오를 더해 총 551건으로 확장했다. fallback-only와 live-enabled 전체 실행 모두 자동 채점 실패 0건이었다. live-enabled 전체 실행 후 사용량은 `areaBasedList2=93`, `detailCommon2=287`, `detailWithTour2=287`였다.
- 기존 문항 반복만으로 품질을 착각하지 않도록 `data/eval/tourism_challenge_questions.jsonl`, `data/eval/tourism_conversation_challenge.jsonl`, `data/eval/tourism_expanded_questions.jsonl`, `data/eval/tourism_expanded_conversation_challenge.jsonl`을 함께 운용한다. 실내/박물관, 시장/먹거리, 공원/산책 같은 선호 조건, 식당/카페/숙박/시장 제외 같은 부정 조건, 감각 접근성, 애매 지역, 저커버리지 지역, 멀티턴 후속 질문을 자동 채점한다.
- 2026-05-16 확장 eval 과정에서 `응급실은 말고 관광지만 계속` 부정 표현, `지하철역 바로 연결` 핵심 미지원 조건, 서귀포시 저커버리지 카드를 보강했다. 서귀포시는 TourAPI 100건 수집으로 박물관/미술관/공원/가족 편의 후보를 보강했다.
- `/tourism/chat`은 같은 `session_id` 안에서 마지막 성공 응답의 지역, 조건, 선호/제외 조건을 얇게 기억한다. 후속 질문에 지역이 없으면 이전 지역을 이어받고, 명시적으로 새 지역을 말하면 덮어쓴다. `유모차 말고 휠체어`처럼 부정한 조건은 이전 조건에서 제거한다.
- `/tourism/chat`은 규칙셋만 쓰지 않고 `data/processed/tourism_intent_classifier.json`의 rule override + 문자 n-gram Naive Bayes shadow classifier를 함께 읽는다. `ml_intent`, `ml_intent_confidence`는 규칙 기반 파싱을 대체하지 않고 대화 맥락 사용 여부를 보조한다. 학습셋은 `data/processed/tourism_intent_training.jsonl`, seed 발화는 `data/eval/tourism_intent_seed_utterances.jsonl`, 생성 발화는 `data/eval/tourism_intent_generated_utterances.jsonl`, AI Hub 추출 발화는 `data/eval/tourism_intent_aihub_utterances.jsonl`이다.
- 의도 분류 모델 재생성은 `.venv/bin/python scripts/generate_tourism_intent_utterances.py`, `.venv/bin/python scripts/extract_aihub_tourism_intent_utterances.py`, `.venv/bin/python scripts/build_tourism_intent_training_set.py`, `.venv/bin/python scripts/train_tourism_intent_classifier.py` 순서다. 2026-05-16 기준 16,254 rows, 내부 holdout accuracy 0.9164, AI Hub holdout accuracy 0.9115, adversarial holdout accuracy 0.8438이다. 설계와 외부 데이터셋 기록은 `docs/tourism/tourism_intent_classifier.md`에 정리했다.
- 의도 분류 변경 후 품질 수치는 `.venv/bin/python scripts/benchmark_tourism_intent_ablation.py`로 확인한다. 2026-05-16 ablation 결과는 rule-only 0.5605, project seed/generated 0.7854, project+AI Hub 0.8745, project+AI Hub+HF external 0.8632이다. 3차 rule override 보강 후 현재 AI Hub/adversarial holdout 직접 평가는 0.9229이다. AI Hub는 기본 학습에 의미가 있었고, HF external은 재라벨링 전까지 기본 학습에 넣지 않는다.
- 답변 시간 영향은 `.venv/bin/python scripts/benchmark_tourism_latency.py`로 확인한다. 2026-05-16 결과는 classifier load 19.1482ms, predict p95 0.0055ms, direct fallback chat p50 3.4295ms, p95 95.6137ms다. 의도 분류기는 프로세스당 한 번 로드되고 예측 비용이 작아 답변 지연의 주 원인이 아니다.
- Gemini API로 AI-generated independent holdout을 만들 수 있다. 생성은 `GEMINI_API_KEY=... .venv/bin/python scripts/generate_tourism_intent_gemini_holdout.py --target 770`, 2차 라벨 검수는 `GEMINI_API_KEY=... .venv/bin/python scripts/verify_tourism_intent_gemini_holdout.py --batch-size 25 --timeout 90 --max-retries 4`로 실행한다. 키는 `.env`나 문서에 저장하지 않는다.
- 2026-05-16 Gemini raw holdout 770건 생성, 2차 검수 통과 676건 확보. 결과 파일은 `data/eval/tourism_intent_gemini_holdout_verified.jsonl`이다. 1차 rule override 보강 후 baseline은 0.5488에서 0.7308로 상승했고, change/replace 보강 후 현재 0.8536이다. 이 파일은 학습셋에 넣지 말고 개선 전/후 비교용으로만 쓴다.
- 2026-05-16 `show_more`, `live_topup`, `unsupported_request`, 애매 지역 경계 케이스 중심 deterministic hard holdout 990건을 추가했다. 생성은 `.venv/bin/python scripts/generate_tourism_intent_hard_holdout.py`, 평가는 `.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_hard_holdout.jsonl`로 실행한다. 2차 보강 전 0.8566에서 현재 0.9747로 올랐다.
- 2026-05-16 Gemini verified holdout의 `clarify_region` 35건 한계를 보완하기 위해 region clarify holdout을 추가했다. rule-boundary stress는 `.venv/bin/python scripts/generate_tourism_intent_region_clarify_stress.py`, 자연형 holdout은 `.venv/bin/python scripts/generate_tourism_intent_region_clarify_natural_holdout.py`로 재생성한다. stress 960건은 1.0000이지만 contract/regression 테스트로 분리하고, natural 600건은 전체 0.9800을 주 지표로 본다. natural의 `clarify_region` 300/300 통과도 단독 품질 지표로 쓰지 않는다. 1.0000이 반복되는 부분 셋은 실사용 판단셋이 충분하다는 뜻이 아니라 반례가 부족하다는 신호로 본다.
- 2026-05-16 `change_region`/`replace_condition` 후속 질문 경계를 확인하는 focused intent holdout을 추가했다. 생성은 `.venv/bin/python scripts/generate_tourism_intent_change_replace_natural_holdout.py`, 평가는 `.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_change_replace_natural_holdout.jsonl`로 실행한다. 현재 600건 1.0000이지만 생성형 집중 회귀셋이므로 품질 점수에서 제외한다. 이 셋은 실사용 품질 증명이 아니라 새 반례를 추가해 계속 깨뜨려야 하는 최소 경계 방어선이다.
- 2026-05-16 실제 `/tourism/chat` 응답을 채점하는 change/replace 멀티턴 판단셋을 201건으로 확장했다. 생성은 `.venv/bin/python scripts/generate_tourism_change_replace_chat_holdout.py`, 평가는 `TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_change_replace_chat_holdout.jsonl --output data/generated/tour_api/eval_runs/tourism_change_replace_chat_holdout_latest.jsonl`로 실행한다. 현재 201/201 통과다.
- 2026-05-16 adversarial chat holdout 42건을 추가했다. 생성은 `.venv/bin/python scripts/generate_tourism_adversarial_chat_holdout.py`, 평가는 `TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_adversarial_chat_holdout.jsonl --output data/generated/tour_api/eval_runs/tourism_adversarial_chat_holdout_latest.jsonl`로 실행한다. 현재 42/42 통과다. 확장 중 `말고` 뒤 새 선호 분리, 지역 교체 파싱, `replace_condition`의 이전 조건/선호 누적, 과거 지명 negation, 광역 전환 시 이전 sigungu 누수, 조사형 제외 표현 문제를 수정했다.
- 2026-05-16 `더 보기` 요청은 20장 같은 임의 상한으로 막지 않는다. 대신 광역/시군구 지역 필터를 주소 기준으로 유지해 전체 fallback 후보가 섞이지 않게 하고, 확인된 같은 지역 후보는 가능한 만큼 반환한다. 20장 이상 반환 케이스 4개, 총 186장 전수 검사에서 지역 오류 0건, 요청 조건 근거 누락 0건을 확인했다.
- 2026-05-16 복합 조건 필터를 보강했다. 사용자가 `둘 다`, `모두`, `동시에`, `반드시`처럼 명시한 경우만 strict AND로 보고, 그 외 복합 조건은 전체 충족 후보를 우선하되 없으면 부분 근거 후보를 반환한다. 단 `점자블록`, `보조견`, `수어/자막`, `장애인 주차`, `장애인 화장실`, `기저귀 교환대`처럼 사용자가 직접 말한 세부 시설은 필수 근거로 유지한다.
- 2026-05-16 유모차 조건은 `유모차/수유실/유아용 의자/영유아 가족 편의` 같은 직접 가족 편의 근거와 `턱 없음/경사로/출입통로/엘리베이터/평탄` 같은 이동 가능성 근거를 분리했다. 직접 가족 편의 근거를 우선하고, 직접 근거가 없을 때만 이동 가능성 근거를 보조로 본다. `아이랑`, `가족`, `영유아` 표현은 가족 편의 직접 근거를 요구한다.
- 2026-05-16 `수어 안내나 자막 안내`처럼 OR로 말한 감각 접근성 조건을 하나의 OR 근거 그룹으로 처리하고, `시장 말고` 같은 제외 후속 질문에서는 이전 필수 시장 근거가 세션에 남지 않도록 수정했다. fallback-only direct chat eval 7개 파일 총 794건은 모두 통과했고, TourAPI 사용량은 `areaBasedList2=144`, `detailCommon2=530`, `detailWithTour2=523`이다.
- Gemini API holdout은 현재 676건까지만 고정 평가 자산으로 둔다. API limit과 키 관리 부담 때문에 신규 AI-generated independent holdout은 Gemini API를 기본으로 쓰지 않고, 필요하면 Codex `gpt-5.4-mini` 또는 `gpt-5.3-codex-spark` 계열로 별도 파일을 만든다.
- `/tourism/chat`은 live Markdown 캐시에 지역 카드가 있어도 요청한 세부 조건의 근거가 부족하면 indexed/sample 후보까지 계속 확인한다. 새 조건 인식은 `보조견`, `시각장애`, `청각장애`를 포함하고, 선호/부정 선호는 카드 랭킹과 제외 필터에 반영한다.
- 서버 없이 현재 코드 기준 eval을 빠르게 확인할 때는 `TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct`를 사용한다.
- 전국 시군구 단위 fallback을 늘릴 경우 예상 규모와 호출량은 `docs/tourism/tourism_data_operations.md`를 참고한다. 기준 수는 TourAPI 234개이며, 행안부 alias 매칭은 228개다.
- 행정동/법정동 지역명 매칭 데이터는 `scripts/build_admin_region_aliases.py`로 생성했다. 결과는 `data/processed/admin_region_aliases.json`이고, 설계 기록은 `docs/tourism/admin_region_aliases.md`에 있다. `TourismQueryService`는 이 파일을 읽어 `부산 중구`, `해운대 좌동`, `창원 마산합포구`, `성남 분당구` 같은 예외 입력을 시군구 후보로 해석한다.
- 2026-05-18 기준 `서울 강남구에서 휠체어 관광지 추천해줘`와 `서울 강남구 근처에서 휠체어 관광지 추천해줘`는 모두 강남구 결과를 먼저 반환한다. 서울 전체 후보를 섞으려면 `서울 전체로 넓혀줘`처럼 명시적 확장 표현이 필요하다.
- VS Code 오류 `Environment manager 'ms-python.python:conda' is not registered`는 `.vscode/settings.json`의 conda 환경 관리자 설정이 원인이었다.
- 현재 `.vscode/settings.json`은 다음처럼 `.venv`를 직접 보도록 정리했다.

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python-envs.pythonProjects": []
}
```

- `.vscode/`는 `.gitignore`에 포함되어 있으므로 위 설정은 로컬 전용이며 커밋에 포함되지 않는다.

## 주요 문서

읽는 순서는 `docs/README.md`의 번호표를 따른다.

- `docs/project/next_session_prompt.md`: 새 세션 시작 문서
- `docs/project/professor_review_brief.md`: 교수님/외부 검토자에게 보여줄 단일 검토 브리프
- `docs/project/GOAL.md`: 현재 관광 MVP 목표와 API 판정 기준
- `docs/project/progress_overview.md`: 전체 진행도 요약
- `README.md`: 실행 방법과 프로젝트 개요
- `docs/rag/rag_chatbot_design.md`: RAG 구조, 폴더 역할, MVP 실행 순서
- `docs/tourism/accessible_tourism_mvp_plan.md`: 무장애·가족 친화 관광 챗봇 구현 플랜
- `docs/tourism/tourism_response_strategy_decision.md`: 응답 전략 결정 기록
- `docs/tourism/tourism_data_operations.md`: fallback 수집, 호출량, 시군구 규모, 샘플 품질 감사 방법
- `docs/tourism/admin_region_aliases.md`: 행정동/법정동 지역명 매칭 데이터
- `docs/tourism/tourism_eval_questions.md`: 551건 관광 챗봇 평가셋 설명
- `docs/tourism/tourism_intent_classifier.md`: 후속 질문 의도 분류기와 학습셋 기록
- `docs/tourism/tourism_model_reasoning_benchmark.md`: 로컬 모델 추론 보조와 native thinking 비교 결과
- `docs/project/demo_capture_scenarios.md`: 발표용 캡처와 시연 질문 시나리오
- `docs/etc/setup/remove_anaconda_mac_guide.md`: 다른 Mac에서 conda/Anaconda 정리할 때 참고
- `docs/etc/references/개방데이터_활용매뉴얼(국문)/`: 국문 관광정보 서비스_GW 매뉴얼
- `docs/etc/references/개방데이터_활용매뉴얼(무장애여행)/`: 무장애 여행 정보 매뉴얼

## 후속 문서화 메모

- 프로젝트가 어느 정도 마무리되면 AI 도구 없이도 초급 개발자가 순차적으로 따라 만들 수 있는 재현 문서셋을 Notion 또는 별도 문서로 정리한다.
- 문서셋은 개념 설명, 왜 필요한지, 만들 파일, 코드 흐름, 실행 명령, 확인 방법, 자주 나는 오류 순서를 기본 구조로 둔다.
- 범위는 FastAPI 기초, RAG, TourAPI, cache/fallback, 지역명 처리, 조건/선호 파싱, 대화 세션, intent classifier, eval, 웹 UI, 운영/디버깅까지 포함한다.

## 작업 원칙

- 기존 코드 구조를 먼저 읽고, 현재 패턴에 맞춰 작게 수정한다.
- 코드, 문서, 예제 명령, 프롬프트에는 저장소 상대경로를 사용한다. 특정 머신에 묶인 절대경로나 임시 로컬 경로는 커밋하지 않는다.
- `.env`와 로컬 설정은 커밋하지 않는다.
- `.vscode/settings.json`은 로컬 설정이므로 작업 히스토리 설명에는 포함할 수 있지만 커밋 대상처럼 다루지 않는다.
- 커밋 메시지는 항상 한글로 작성하고, 변경 내용을 명확히 요약한다. 여러 영역을 함께 커밋할 때는 제목과 본문으로 API, 데이터, 테스트, 문서 변경을 구분해 적는다.
- 사용자가 구현을 요청하면 제안에서 멈추지 말고 가능한 범위에서 구현, 테스트, 결과 요약까지 진행한다.
