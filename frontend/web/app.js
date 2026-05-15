const form = document.querySelector("#chatForm");
const messageInput = document.querySelector("#message");
const apiBaseInput = document.querySelector("#apiBase");
const submitButton = document.querySelector("#submitButton");
const requestState = document.querySelector("#requestState");
const diagnostics = document.querySelector("#diagnostics");
const answerText = document.querySelector("#answerText");
const clarificationBanner = document.querySelector("#clarificationBanner");
const suggestions = document.querySelector("#suggestions");
const cardsGrid = document.querySelector("#cards");
const cardCount = document.querySelector("#cardCount");
const clearButton = document.querySelector("#clearButton");
const cardTemplate = document.querySelector("#cardTemplate");
const swaggerLink = document.querySelector("#swaggerLink");
const redocLink = document.querySelector("#redocLink");
const openapiLink = document.querySelector("#openapiLink");
const helpButton = document.querySelector("#helpButton");
const helpModal = document.querySelector("#helpModal");
const closeHelpButton = document.querySelector("#closeHelpButton");

const accessibilityLabels = {
  wheelchair: "휠체어",
  parking: "주차",
  restroom: "화장실",
  stroller: "유아차",
  nursing_room: "수유실",
  elevator: "엘리베이터",
  route: "동선",
};

apiBaseInput.value = defaultApiBase();
syncApiDocLinks();
apiBaseInput.addEventListener("input", syncApiDocLinks);
helpButton.addEventListener("click", openHelp);
closeHelpButton.addEventListener("click", closeHelp);
helpModal.addEventListener("click", (event) => {
  if (event.target === helpModal) closeHelp();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !helpModal.hidden) closeHelp();
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.prompt;
    messageInput.focus();
  });
});

document.querySelectorAll("[data-region]").forEach((button) => {
  button.addEventListener("click", () => {
    const condition = inferConditionText(messageInput.value);
    messageInput.value = `${button.dataset.region}에서 ${condition} 관광지 추천해줘`;
    messageInput.focus();
  });
});

clearButton.addEventListener("click", () => {
  setState("대기 중");
  diagnostics.replaceChildren();
  clarificationBanner.hidden = true;
  suggestions.replaceChildren();
  suggestions.classList.remove("clarification-options");
  answerText.textContent = "질문을 보내면 답변과 추천 카드가 여기에 표시됩니다.";
  answerText.classList.add("empty");
  cardsGrid.replaceChildren();
  cardCount.textContent = "0개";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();

  if (!message) {
    setState("입력 필요", "error");
    diagnostics.replaceChildren(createDiagnostic("질문을 입력해야 합니다."));
    return;
  }

  setLoading(true);
  suggestions.replaceChildren();
  clarificationBanner.hidden = true;
  suggestions.classList.remove("clarification-options");

  try {
    const response = await fetch(`${normalizedApiBase()}/tourism/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      renderError(response.status, payload);
      return;
    }

    renderResponse(payload);
  } catch (error) {
    setState("연결 실패", "error");
    answerText.textContent = `API 서버에 연결하지 못했습니다.\n${error.message}`;
    answerText.classList.remove("empty");
    suggestions.replaceChildren();
    clarificationBanner.hidden = true;
    suggestions.classList.remove("clarification-options");
    cardsGrid.replaceChildren();
    cardCount.textContent = "0개";
  } finally {
    setLoading(false);
  }
});

function normalizedApiBase() {
  return apiBaseInput.value.replace(/\/+$/, "");
}

function syncApiDocLinks() {
  const base = normalizedApiBase() || defaultApiBase();
  swaggerLink.href = `${base}/docs`;
  redocLink.href = `${base}/redoc`;
  openapiLink.href = `${base}/openapi.json`;
}

function defaultApiBase() {
  const { protocol, hostname } = window.location;
  if (protocol === "file:") {
    return "http://127.0.0.1:8000";
  }
  if (["127.0.0.1", "localhost"].includes(hostname) && window.location.port === "5173") {
    return "http://127.0.0.1:8000";
  }
  return window.location.origin;
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "조회 중" : "조회";
  if (isLoading) {
    setState("질문 분석 중");
    diagnostics.replaceChildren(createDiagnostic("지역/조건을 구조화하고, 복합 질문이면 추론 보조로 후보 순서를 조정합니다."));
  }
}

function setState(text, tone = "") {
  requestState.textContent = text;
  requestState.className = `state-pill ${tone}`.trim();
}

function renderResponse(payload) {
  const cards = Array.isArray(payload.cards) ? payload.cards : [];
  const mode = payload.lookup_mode || "unknown";
  setState(modeLabel(mode, payload.degraded), modeTone(mode, payload.degraded));

  const notes = [modeDescription(mode)];
  if (payload.degraded) notes.push("live API 또는 검색 인덱스 대신 fallback 안전망을 사용했습니다.");
  if (payload.reasoning_assist_used) notes.push("복합 조건을 반영하기 위해 LLM 추론 보조로 후보 순서를 조정했습니다.");
  if (Array.isArray(payload.reasoning_assist_notes)) {
    payload.reasoning_assist_notes.forEach((note) => notes.push(`추론 보조 메모: ${note}`));
  }
  if (Array.isArray(payload.warnings)) notes.push(...payload.warnings);
  diagnostics.replaceChildren(...notes.map(createDiagnostic));

  answerText.textContent = payload.answer || "답변 문장이 비어 있습니다.";
  answerText.classList.toggle("empty", !payload.answer);
  clarificationBanner.hidden = mode !== "clarification";
  renderSuggestions(payload.suggested_messages || []);
  cardCount.textContent = `${cards.length}개`;
  cardsGrid.replaceChildren(...cards.map(renderCard));
}

function modeLabel(mode, degraded) {
  if (mode === "live") return "Live API 응답";
  if (mode === "cache") return "Live 캐시 응답";
  if (mode === "indexed") return degraded ? "색인 fallback" : "색인 응답";
  if (mode === "sample") return "샘플 fallback";
  if (mode === "clarification") return "지역 선택 필요";
  if (mode === "unsupported") return "지원 범위 밖";
  return degraded ? "Fallback 응답" : "정상 응답";
}

function modeTone(mode, degraded) {
  if (mode === "clarification") return "warn";
  if (mode === "unsupported") return "warn";
  if (mode === "sample" || degraded) return "warn";
  if (mode === "cache" || mode === "live" || mode === "indexed") return "ok";
  return "";
}

function modeDescription(mode) {
  if (mode === "live") return "지역이 확정되어 TourAPI 후보와 접근성 상세를 live로 조회했습니다.";
  if (mode === "cache") return "이전에 live 조회해 저장한 Markdown 캐시에서 같은 지역 관광 카드를 찾았습니다.";
  if (mode === "indexed") return "live 결과 대신 Chroma 색인에서 관광 카드 문서를 찾았습니다.";
  if (mode === "sample") return "API/색인 결과 대신 로컬 Markdown fallback 샘플을 사용했습니다.";
  if (mode === "clarification") return "동명이 지역이라 추천 전에 광역 지역 선택이 필요합니다.";
  if (mode === "unsupported") return "현재 MVP 범위를 벗어난 질문이라 관광지 카드를 만들지 않았습니다.";
  return "응답 생성 경로를 확인하지 못했습니다.";
}

function renderError(status, payload) {
  setState(`오류 ${status}`, "error");
  const detail = payload?.detail;
  const message =
    typeof detail === "string"
      ? detail
      : detail?.message || "요청 처리 중 문제가 발생했습니다.";
  const code = typeof detail === "object" && detail?.code ? ` (${detail.code})` : "";

  answerText.textContent = `${message}${code}`;
  answerText.classList.remove("empty");
  clarificationBanner.hidden = true;
  suggestions.replaceChildren();
  suggestions.classList.remove("clarification-options");
  cardsGrid.replaceChildren();
  cardCount.textContent = "0개";
}

function renderSuggestions(messages) {
  suggestions.replaceChildren();
  suggestions.classList.toggle("clarification-options", !clarificationBanner.hidden && messages.length > 0);
  messages.forEach((message) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = message;
    button.addEventListener("click", () => {
      messageInput.value = message;
      form.requestSubmit();
    });
    suggestions.append(button);
  });
}

function inferConditionText(message) {
  if (message.includes("유아차") || message.includes("아이") || message.includes("가족")) {
    return "유아차 가족";
  }
  if (message.includes("고령자") || message.includes("어르신") || message.includes("노인")) {
    return "휠체어 고령자";
  }
  if (message.includes("휠체어") || message.includes("장애인")) {
    return "휠체어";
  }
  return "무장애";
}

function renderCard(card) {
  const node = cardTemplate.content.firstElementChild.cloneNode(true);
  const media = node.querySelector(".card-media");
  const title = node.querySelector("h3");
  const address = node.querySelector(".address");
  const reason = node.querySelector(".reason");
  const tags = node.querySelector(".accessibility-tags");
  const details = node.querySelector(".details");

  title.textContent = card.title || "이름 없는 장소";
  address.textContent = card.address || "주소 확인 필요";
  reason.textContent = card.recommendation_reason || "추천 사유 확인 필요";

  if (card.image_url) {
    media.style.backgroundImage = `url("${card.image_url}")`;
  }

  const tagValues = [...(card.accessibility_tags || []), ...(card.family_tags || [])];
  if (tagValues.length === 0) {
    tags.append(createTag("접근성 확인 필요", true));
  } else {
    tagValues.forEach((tag) => tags.append(createTag(tag, tag.includes("확인"))));
  }

  Object.entries(card.accessibility || {}).forEach(([key, value]) => {
    if (!value) return;
    const row = document.createElement("div");
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = accessibilityLabels[key] || key;
    dd.textContent = value;
    row.append(dt, dd);
    details.append(row);
  });

  if (card.tel) {
    details.append(createDetail("전화", card.tel));
  }

  if (card.source_url) {
    const source = document.createElement("a");
    source.href = card.source_url;
    source.target = "_blank";
    source.rel = "noreferrer";
    source.textContent = "원문 보기";
    details.append(createDetail("출처", source));
  }

  return node;
}

function createTag(text, needsCheck = false) {
  const tag = document.createElement("span");
  tag.className = needsCheck ? "tag needs-check" : "tag";
  tag.textContent = text;
  return tag;
}

function createDetail(label, value) {
  const row = document.createElement("div");
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = label;
  if (value instanceof Node) {
    dd.append(value);
  } else {
    dd.textContent = value;
  }
  row.append(dt, dd);
  return row;
}

function createDiagnostic(text) {
  const note = document.createElement("span");
  note.className = "diagnostic";
  note.textContent = text;
  return note;
}

function openHelp() {
  helpModal.hidden = false;
  document.body.classList.add("modal-open");
  closeHelpButton.focus();
}

function closeHelp() {
  helpModal.hidden = true;
  document.body.classList.remove("modal-open");
  helpButton.focus();
}
