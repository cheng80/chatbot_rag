---
name: technical-infographic
description: Create clean technical infographic documents for this project, including README visual summaries, internal RAG structure posters, architecture maps, and beginner-friendly system journey diagrams. Use when asked to make an infographic, visual README, RAG 내부 구조, or example-image-style technical poster.
metadata:
  short-description: Project technical infographic workflow
---

# Technical Infographic

Use this skill when the user asks for a visual README, clean technical infographic, internal process diagram, RAG journey poster, or “예시 이미지 같은” system explanation for this project.

For AI image-generation posters, treat any existing prompt MD as an editable artifact, not as permanent truth. Re-read the current HTML/docs and refresh the prompt from the latest source before reuse.

## Source Selection

Read only what is needed. Pick sources from the user request and artifact type instead of treating this skill as a fixed manuscript.

- README or project overview infographic: start from `README.md`, then `docs/project/progress_overview.md` if progress or scope claims are needed.
- Internal RAG/process poster: start from the named HTML/image/prompt artifact if provided; otherwise discover likely project artifacts with `rg --files docs/project`.
- Tourism feature, policy, or evaluation poster: start from the relevant `docs/tourism/` file named by the user or discovered by title/search.
- Benchmark/result visual: start from the report, eval output, or script named by the user; verify summary claims against generated result files when available.
- Architecture map: start from README/docs, then inspect code paths only for claims that need factual confirmation.
- AI image prompt refresh: treat any existing prompt MD as a previous draft. Rebuild the factual content from current HTML/docs before reusing it.

Do not invent metrics, model names, data counts, or policy claims.

## Output Types

Choose the smallest useful artifact:

- README summary infographic: high-level project structure, workflow, tech stack, progress.
- Internal process poster: question-to-answer journey for `/tourism/chat`.
- Architecture map: UI, API, services, data, models, eval.
- Benchmark/result visual: model/search/eval findings and adoption policy.

Choose the production path from the user request:

- AI poster path: if the user wants “ChatGPT 이미지”, “AI 생성형 technical infographic”, “예시 이미지 같은 포스터”, or a social-thread visual, first update the prompt MD, then use the image generation skill/tool to create a new bitmap poster. Do not merely screenshot the HTML.
- Editable docs path: if the user wants a repo-maintained README/documentation asset with exact text, build self-contained HTML/SVG and render PNG with Playwright.
- Hybrid path: use AI image generation for visual direction, then recreate/fix exact text in editable HTML/SVG if the image text is inaccurate.

For README use, save the maintained assets under:

- `docs/project/<name>.html` for editable source when using the editable docs path
- `docs/project/<name>.png` for README display
- `docs/project/<name>_image_prompt.md` or an existing prompt MD updated from current sources for AI poster regeneration

Update `README.md` with the PNG and HTML links when the artifact is meant to be visible from README.

## Beginner Copy Rules

Prefer beginner terms, with technical names as small labels when useful:

- RAG -> 저장 자료를 먼저 찾아보고 답하는 방식
- embedding -> 검색용 숫자 변환
- vector search -> 벡터 검색 / 비슷한 자료 찾기
- cache -> 저장 기록 / 재사용 저장소
- schema -> 정해진 응답 형식
- domain API names -> current source wording plus short Korean meaning
- fallback -> 예비 관광 카드 / 안전망 자료
- LLM assist modes -> current source wording plus whether it is default or optional

For user-facing infographic text, avoid unexplained percentile/performance jargon. Prefer plain wording such as “most requests finish around the documented time range” in Korean, using the actual values from the current source. Keep standard RAG implementation terms when they appear in the current source and are useful for technical readers.

Keep text short. Avoid dense paragraphs inside boxes.

## Visual Style

Default depends on output intent:

- AI/social poster: prompt -> image generation -> visual review -> optional copy into `docs/project/`.
- Exact repo documentation: self-contained HTML/CSS -> Playwright PNG -> visual review.

Use:

- Cream paper background.
- Thin black outlines.
- Muted green section labels.
- Pastel panels: green, teal, blue, yellow, red, violet.
- Red callouts only for policy warnings or important constraints.
- Arrows, branches, merge points, and right-side timing/policy summaries.
- Clean sans-serif Korean typography.

Avoid:

- Handwriting fonts unless explicitly requested.
- Decorative blobs, dark gradients, stock images.
- Overcrowded text.
- Cards inside cards except small repeated content blocks.
- Pure AI-generated bitmap as the only authoritative technical document.

AI-generated images are appropriate when the user explicitly wants a generated poster style. But generated text can be wrong. After generation, inspect the result for wrong Korean, wrong API names, wrong numbers, or invented technologies. If the result is for README or official docs and text accuracy matters, either regenerate with a stricter prompt or recreate the final as editable HTML/SVG.

When the user asks for a prompt to regenerate a poster in ChatGPT or another image tool, do not invent a fresh prompt from memory. Open the current prompt artifact if one exists, refresh it from the latest source, then point the user to that file. If no prompt artifact exists, create one next to the source infographic under `docs/project/`.

## AI Image Generation Workflow

Use this workflow for generated-image requests:

1. Read the current HTML/source docs only to extract facts.
2. Update or create a prompt MD next to the source infographic so it matches the current project facts.
3. Use the image generation skill/tool with the prompt content or a concise version of it.
4. Save/copy the generated image into `docs/project/` only if the user wants it as a project artifact.
5. Visually inspect the generated poster:
   - Korean text is readable.
   - Required technology names are correct.
   - Required numbers are correct.
   - Model/search/time/data-count values match the current source facts. Do not feed obsolete values into the image prompt because image models may copy them.
   - It does not look like a webpage screenshot.
6. If text is wrong, regenerate or switch to editable HTML/SVG for the final.

Do not replace the editable HTML source with an AI bitmap unless the user explicitly wants only a generated image.

## Internal RAG Structure Poster Workflow

Use this when asked for the chatbot internal process, RAG 내부 구조, or example-image-style journey.

This skill must not be the source of project facts. Do not hard-code step names, metrics, model names, API names, counts, or policy details from this file. Extract them from the current source files every time.

Minimum extraction checklist:

- Title and subtitle from the current infographic HTML or README section.
- User-facing example question, if present.
- Step count, step names, and step order.
- Per-step node labels and right-side explanation text.
- Timing labels and summary numbers.
- Technology labels.
- Bottom component strip and note box, if present.
- Policy callouts and “do not invent data” constraints.

Situation-based extraction:

- If the user asks to regenerate an image from a prompt, find the latest maintained HTML/docs first, then update the prompt MD as an output artifact.
- If the user asks for a new prompt only, create or refresh a prompt MD and keep facts traceable to the source files used.
- If the user asks to update README visuals, update the editable source and rendered PNG together, then link them from README.
- If the user asks for a one-off visual direction, keep generated image text minimal and do not promote it as authoritative docs unless the user asks.
- If a fact is missing from current sources, omit it or mark it as a design placeholder in the prompt instead of preserving stale text from older prompts.

Source selection:

- If the user names an HTML/image/prompt file, start there.
- If the user says “current project” or “this README”, start from `README.md` and the relevant `docs/project/` artifact.
- If there is an existing prompt MD, use it as a draft to update, not as the canonical source.
- If sources disagree, trust the maintained HTML/README for structure, then verify factual claims against project docs or code before generating image prompts.

For this repository, common artifact locations are `docs/project/`, but file names may change. Discover current files with `rg --files docs/project` instead of assuming one fixed infographic.

Prompt writing rules:

- State allowed labels and values positively; avoid putting obsolete values or forbidden text in the image prompt because image models may copy them.
- Keep exact technology labels only after verifying they still appear in current sources.
- Convert unexplained performance jargon into user-facing wording unless the user specifically wants raw metrics.
- Preserve exact numbers only when current docs still support them.
- Keep section labels short enough for generated image text.
- If generated image accuracy matters, include a small “large labels only, minimal small text” instruction.

## Editable HTML Rendering

Use this only for the editable docs path. Render with Playwright when available:

```bash
HTML_URL="$(python - <<'PY'
from pathlib import Path
print(Path('docs/project/<name>.html').resolve().as_uri())
PY
)"
npx -y playwright screenshot --full-page --viewport-size=1600,2400 "$HTML_URL" docs/project/<name>.png
```

Then visually inspect the PNG. Fix clipped text, unreadable labels, excessive whitespace, and overlap before finishing.

## Validation

Run:

```bash
git diff --check
LOCAL_PATH_PATTERN='/(Users|private/var)|~[/]Desktop'
rg -n "$LOCAL_PATH_PATTERN" README.md docs/project/<name>.html
```

Committed project docs must not contain machine-specific paths.
