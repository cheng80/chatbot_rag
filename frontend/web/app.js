const form = document.querySelector("#chatForm");
const messageInput = document.querySelector("#message");
const apiBaseInput = document.querySelector("#apiBase");
const submitButton = document.querySelector("#submitButton");
const requestState = document.querySelector("#requestState");
const diagnostics = document.querySelector("#diagnostics");
const answerText = document.querySelector("#answerText");
const answerToggleButton = document.querySelector("#answerToggleButton");
const clarificationBanner = document.querySelector("#clarificationBanner");
const clarificationTitle = document.querySelector("#clarificationTitle");
const clarificationDescription = document.querySelector("#clarificationDescription");
const suggestions = document.querySelector("#suggestions");
const sourceList = document.querySelector("#sourceList");
const cardsGrid = document.querySelector("#cards");
const cardCount = document.querySelector("#cardCount");
const clearButton = document.querySelector("#clearButton");
const cardTemplate = document.querySelector("#cardTemplate");
const demoMoreButton = document.querySelector("#demoMoreButton");
const swaggerLink = document.querySelector("#swaggerLink");
const redocLink = document.querySelector("#redocLink");
const openapiLink = document.querySelector("#openapiLink");
const helpButton = document.querySelector("#helpButton");
const helpModal = document.querySelector("#helpModal");
const closeHelpButton = document.querySelector("#closeHelpButton");
const modeBadge = document.querySelector("#modeBadge");
const debugToggleButton = document.querySelector("#debugToggleButton");
const debugPanel = document.querySelector("#debugPanel");
const chatScroll = document.querySelector("#chatScroll");
const userEcho = document.querySelector("#userEcho");
const typingIndicator = document.querySelector("#typingIndicator");
const toast = document.querySelector("#toast");
const debugMode = isLocalDebugMode();

const accessibilityLabels = {
  wheelchair: "휠체어",
  parking: "주차",
  restroom: "화장실",
  stroller: "유아차",
  nursing_room: "수유실",
  elevator: "엘리베이터",
  route: "동선",
};

let fullAnswerText = "";
let compactAnswerText = "";
let isAnswerExpanded = false;
let sessionId = createSessionId();

const demoPreview = {
  answer:
    "시연 예시입니다. 지역을 선택하거나 질문을 보내면 실제 /tourism/chat 응답으로 교체됩니다.\n\n서울 강남구 기준으로 휠체어 접근성, 주차, 화장실 확인이 필요한 관광지를 카드 형태로 보여줍니다.",
  cards: [
    {
      title: "서울 선릉과 정릉",
      address: "서울특별시 강남구 선릉로100길 1",
      recommendation_reason:
        "도심 접근성이 좋고 산책 동선이 비교적 단순해 보호자와 함께 이동 계획을 세우기 좋습니다.",
      accessibility_tags: ["휠체어 동선 확인", "주차 확인"],
      family_tags: ["가족 산책"],
      accessibility: {
        wheelchair: "일부 구간은 현장 경사와 노면 상태 확인 필요",
        parking: "방문 전 장애인 주차 가능 여부 확인 필요",
        restroom: "현장 안내 확인 필요",
      },
      source_name: "한국관광공사 무장애 여행 정보",
    },
    {
      title: "코엑스 아쿠아리움",
      address: "서울특별시 강남구 영동대로 513",
      recommendation_reason:
        "실내 이동 중심이라 날씨 영향을 줄일 수 있고, 가족 동반 시 관람 흐름을 설명하기 쉽습니다.",
      accessibility_tags: ["실내", "엘리베이터 확인"],
      family_tags: ["아이 동반"],
      accessibility: {
        elevator: "건물 내 승강 설비 동선 확인 필요",
        restroom: "편의시설 위치 확인 필요",
        route: "혼잡 시간대 우회 동선 확인 권장",
      },
      source_name: "한국관광공사 무장애 여행 정보",
    },
  ],
};

apiBaseInput.value = defaultApiBase();
syncApiDocLinks();
syncDebugVisibility();
apiBaseInput.addEventListener("input", syncApiDocLinks);
debugToggleButton.addEventListener("click", toggleDebugPanel);
helpButton.addEventListener("click", openHelp);
closeHelpButton.addEventListener("click", closeHelp);
answerToggleButton.addEventListener("click", () => {
  setAnswerExpanded(!isAnswerExpanded);
});
helpModal.addEventListener("click", (event) => {
  if (event.target === helpModal) closeHelp();
});
renderDemoPreview();
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !helpModal.hidden) closeHelp();
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.prompt;
    messageInput.focus();
    showToast("질문 예시를 입력했습니다.", "ok");
  });
});

document.querySelectorAll("[data-region]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-region]").forEach((regionButton) => {
      regionButton.setAttribute("aria-pressed", String(regionButton === button));
    });
    const condition = inferConditionText(messageInput.value);
    messageInput.value = `${button.dataset.region}에서 ${condition} 관광지 추천해줘`;
    messageInput.focus();
    showToast(`${button.dataset.region} 기준으로 질문을 준비했습니다.`, "ok");
  });
});

clearButton.addEventListener("click", () => {
  document.querySelectorAll("[data-region]").forEach((regionButton) => {
    regionButton.setAttribute("aria-pressed", "false");
  });
  setState("대기 중");
  diagnostics.replaceChildren();
  renderClarificationBanner(null);
  suggestions.replaceChildren();
  suggestions.classList.remove("clarification-options", "condition-options", "region-options");
  sessionId = createSessionId();
  userEcho.hidden = true;
  userEcho.textContent = "";
  typingIndicator.hidden = true;
  hideToast();
  sourceList.replaceChildren(createSourceEmpty());
  setAnswerText("질문을 보내면 답변과 추천 카드가 여기에 표시됩니다.", { empty: true });
  cardsGrid.replaceChildren();
  cardCount.textContent = "0개";
  demoMoreButton.disabled = true;
  demoMoreButton.hidden = true;
  demoMoreButton.textContent = "더 보기";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();

  if (!message) {
    setState("입력 필요", "error");
    diagnostics.replaceChildren(createDiagnostic("질문을 입력해야 합니다."));
    showToast("질문을 입력해 주세요.", "error");
    messageInput.focus();
    return;
  }

  setLoading(true);
  renderUserMessage(message);
  suggestions.replaceChildren();
  renderClarificationBanner(null);
  suggestions.classList.remove("clarification-options", "condition-options", "region-options");

  try {
    const response = await fetch(`${normalizedApiBase()}/tourism/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      renderError(response.status, payload);
      return;
    }

    renderResponse(payload || {});
  } catch (error) {
    setState("연결 실패", "error");
    showToast("서버에 연결하지 못했습니다.", "error");
    setAnswerText(`서버에 연결하지 못했습니다.\n${error.message}`);
    suggestions.replaceChildren();
    renderClarificationBanner(null);
    suggestions.classList.remove("clarification-options", "condition-options", "region-options");
    sourceList.replaceChildren(createSourceEmpty("서버 연결 후 출처가 표시됩니다."));
    cardsGrid.replaceChildren();
    cardCount.textContent = "0개";
    demoMoreButton.disabled = true;
    demoMoreButton.hidden = true;
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

function isLocalDebugMode() {
  const params = new URLSearchParams(window.location.search);
  return params.get("mode") !== "release" && params.get("debug") !== "0";
}

function syncDebugVisibility() {
  document.body.classList.toggle("debug-mode", debugMode);
  document.body.classList.toggle("release-mode", !debugMode);
  modeBadge.textContent = debugMode ? "DEV" : "USER";
  modeBadge.title = debugMode ? "개발 진단 모드" : "사용자 화면";
  debugPanel.hidden = !debugMode;
  debugToggleButton.setAttribute("aria-expanded", String(debugMode));
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.classList.toggle("is-loading", isLoading);
  submitButton.textContent = isLoading ? "찾는 중" : "추천 받기";
  typingIndicator.hidden = !isLoading;
  if (isLoading) {
    demoMoreButton.disabled = true;
    scrollChatToBottom();
    if (debugMode) {
      setState("질문 분석 중");
      diagnostics.replaceChildren(createDiagnostic("지역/조건을 구조화하고, 복합 질문이면 추론 보조로 후보 순서를 조정합니다."));
    }
  }
}

function setState(text, tone = "") {
  if (!debugMode) return;
  requestState.textContent = text;
  requestState.className = `state-pill ${tone}`.trim();
}

function renderResponse(payload) {
  const cards = Array.isArray(payload.cards) ? payload.cards : [];
  const mode = payload.lookup_mode || "unknown";
  setState(modeLabel(mode, payload.degraded), modeTone(mode, payload.degraded));

  const notes = [modeDescription(mode)];
  if (payload.degraded) notes.push("일부 자료 확인이 원활하지 않아 준비된 자료로 먼저 안내했습니다.");
  if (payload.reasoning_assist_used) notes.push("복합 조건을 반영하기 위해 LLM 추론 보조로 후보 순서를 조정했습니다.");
  if (Array.isArray(payload.reasoning_assist_notes)) {
    payload.reasoning_assist_notes.forEach((note) => notes.push(`추론 보조 메모: ${note}`));
  }
  if (Array.isArray(payload.warnings)) notes.push(...payload.warnings);
  if (debugMode) {
    diagnostics.replaceChildren(...notes.map(createDiagnostic));
  }

  setAnswerText(payload.answer || "답변 문장이 비어 있습니다.", { empty: !payload.answer });
  const clarificationType = mode === "clarification" ? inferClarificationType(payload) : null;
  const suggestionType = clarificationType || inferSuggestionType(payload, cards);
  renderClarificationBanner(clarificationType);
  renderSuggestions(payload.suggested_messages || [], suggestionType);
  renderSources(payload.sources || [], cards);
  cardCount.textContent = `${cards.length}개`;
  cardsGrid.replaceChildren(...cards.map(renderCard));
  if (cards.length > 0) {
    showToast(`${cards.length}개의 추천 카드를 찾았습니다.`, "ok");
  }
  scrollChatToBottom();
}

function renderDemoPreview() {
  if (debugMode) {
    setState("시연 예시");
    diagnostics.replaceChildren(createDiagnostic("지역 선택, 추천 카드, 더 보기, 출처, 경고 문구가 보이도록 구성한 초기 예시입니다."));
    setAnswerText(demoPreview.answer);
    sourceList.replaceChildren(
      createSourceEmpty("예시 출처: 한국관광공사 무장애 여행 정보"),
      createSourceEmpty("실제 응답 후 카드별 원문 링크가 표시됩니다."),
    );
    cardCount.textContent = `${demoPreview.cards.length}개`;
    cardsGrid.replaceChildren(...demoPreview.cards.map(renderCard));
  } else {
    setAnswerText("가고 싶은 지역과 동행 조건을 알려주세요. 추천 가능한 장소를 카드로 정리해 드립니다.", { empty: true });
    sourceList.replaceChildren(createSourceEmpty());
    cardCount.textContent = "0개";
    cardsGrid.replaceChildren();
  }
  demoMoreButton.disabled = true;
  demoMoreButton.hidden = true;
}

function modeLabel(mode, degraded) {
  if (mode === "live") return "Live API 응답";
  if (mode === "live_top_up") return "Live 보강 응답";
  if (mode === "cache") return "Live 캐시 응답";
  if (mode === "indexed") return degraded ? "색인 fallback" : "색인 응답";
  if (mode === "sample") return "샘플 fallback";
  if (mode === "clarification") return "추가 확인 필요";
  if (mode === "unsupported") return "지원 범위 밖";
  return degraded ? "Fallback 응답" : "정상 응답";
}

function modeTone(mode, degraded) {
  if (mode === "clarification") return "warn";
  if (mode === "unsupported") return "warn";
  if (mode === "sample" || degraded) return "warn";
  if (mode === "cache" || mode === "live" || mode === "live_top_up" || mode === "indexed") return "ok";
  return "";
}

function modeDescription(mode) {
  if (mode === "live") return "지역이 확정되어 TourAPI 후보와 접근성 상세를 live로 조회했습니다.";
  if (mode === "live_top_up") return "저장된 후보에 live TourAPI 조회 후보를 보강했습니다.";
  if (mode === "cache") return "이전에 live 조회해 저장한 Markdown 캐시에서 같은 지역 관광 카드를 찾았습니다.";
  if (mode === "indexed") return "live 결과 대신 Chroma 색인에서 관광 카드 문서를 찾았습니다.";
  if (mode === "sample") return "API/색인 결과 대신 로컬 Markdown fallback 샘플을 사용했습니다.";
  if (mode === "clarification") return "추천 전에 지역 또는 접근성 기준 확인이 필요합니다.";
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

  setAnswerText(`${message}${code}`);
  showToast("요청 처리 중 문제가 발생했습니다.", "error");
  renderClarificationBanner(null);
  suggestions.replaceChildren();
  suggestions.classList.remove("clarification-options", "condition-options", "region-options");
  sourceList.replaceChildren(createSourceEmpty("오류가 해결되면 출처가 표시됩니다."));
  cardsGrid.replaceChildren();
  cardCount.textContent = "0개";
  demoMoreButton.disabled = true;
  demoMoreButton.hidden = true;
}

function renderClarificationBanner(type) {
  if (!type) {
    clarificationBanner.hidden = true;
    clarificationBanner.classList.remove("condition-clarification", "region-clarification");
    clarificationTitle.textContent = "추가 질문 필요";
    clarificationDescription.textContent = "아래 후보를 선택하면 원래 질문 맥락을 유지한 채 다시 조회합니다.";
    return;
  }

  const copy = {
    condition: {
      title: "조건 확인 필요",
      description: "의미가 겹치는 접근성 표현입니다. 원하는 기준을 선택하면 그 조건으로 다시 조회합니다.",
    },
    region: {
      title: "지역 선택 필요",
      description: "같은 이름의 지역이 여러 곳에 있습니다. 지역 후보를 선택하면 원래 질문 맥락을 유지해 다시 조회합니다.",
    },
    general: {
      title: "추가 질문 필요",
      description: "아래 후보를 선택하면 원래 질문 맥락을 유지한 채 다시 조회합니다.",
    },
  }[type] || {
    title: "추가 질문 필요",
    description: "아래 후보를 선택하면 원래 질문 맥락을 유지한 채 다시 조회합니다.",
  };

  clarificationBanner.hidden = false;
  clarificationBanner.classList.toggle("condition-clarification", type === "condition");
  clarificationBanner.classList.toggle("region-clarification", type === "region");
  clarificationTitle.textContent = copy.title;
  clarificationDescription.textContent = copy.description;
}

function inferClarificationType(payload) {
  const answer = String(payload?.answer || "");
  const messages = Array.isArray(payload?.suggested_messages) ? payload.suggested_messages : [];
  const joined = `${answer} ${messages.join(" ")}`;
  if (/접근성 의미|어르신 이동 부담|입구\/동선 접근로|휠체어 접근|대중교통 접근|장애인 화장실/.test(joined)) {
    return "condition";
  }
  if (/어느 지역|여러 시도|지역이 여러|서울 중구|부산 중구|인천 중구/.test(joined)) {
    return "region";
  }
  return "general";
}

function inferSuggestionType(payload, cards) {
  const messages = Array.isArray(payload?.suggested_messages) ? payload.suggested_messages : [];
  if ((payload?.lookup_mode === "unknown" || payload?.lookup_mode === "sample") && cards.length === 0 && messages.length > 0) {
    return "shortage";
  }
  if (messages.some((message) => /전체로 넓혀|범위.*넓혀/.test(message))) {
    return "expansion";
  }
  return null;
}

function renderSuggestions(messages, suggestionType = null) {
  suggestions.replaceChildren();
  suggestions.classList.toggle("clarification-options", Boolean(suggestionType) && suggestionType !== "shortage" && messages.length > 0);
  suggestions.classList.toggle("condition-options", suggestionType === "condition" && messages.length > 0);
  suggestions.classList.toggle("region-options", suggestionType === "region" && messages.length > 0);
  suggestions.classList.toggle("recovery-options", suggestionType === "shortage" && messages.length > 0);
  suggestions.classList.toggle("expansion-options", suggestionType === "expansion" && messages.length > 0);
  const moreMessage = messages.find((message) => /더 보기|전부|20곳/.test(message));
  demoMoreButton.disabled = !moreMessage;
  demoMoreButton.hidden = !moreMessage;
  demoMoreButton.textContent = moreMessage || "더 보기";
  demoMoreButton.onclick = moreMessage
    ? () => {
      messageInput.value = moreMessage;
      showToast("추가 후보를 확인합니다.", "ok");
      form.requestSubmit();
    }
    : null;
  messages.forEach((message) => {
    const button = document.createElement("button");
    button.type = "button";
    const label = suggestionButtonLabel(message, suggestionType);
    button.textContent = label;
    if (label !== message) {
      button.title = message;
      button.setAttribute("aria-label", message);
    }
    button.addEventListener("click", () => {
      messageInput.value = message;
      showToast(suggestionType === "condition" ? "선택한 조건으로 다시 조회합니다." : "후속 질문을 보냅니다.", "ok");
      form.requestSubmit();
    });
    suggestions.append(button);
  });
}

function suggestionButtonLabel(message, suggestionType) {
  if (suggestionType === "shortage") {
    if (/전체로 넓혀|범위|전체/.test(message)) return "같은 시·도까지 넓히기";
    if (/무장애 관광지/.test(message)) return "조건 완화하기";
    return "이 조건으로 다시 찾기";
  }
  if (suggestionType === "expansion" && /전체로 넓혀|범위.*넓혀/.test(message)) {
    return "같은 시·도까지 넓혀 보기";
  }
  if (suggestionType !== "condition") return message;
  const patterns = [
    ["휠체어 접근", "휠체어 접근"],
    ["입구/동선 접근로", "입구/동선 접근로"],
    ["어르신 이동 부담 적은 곳", "어르신 이동 부담 적은 곳"],
    ["장애인 화장실", "장애인 화장실"],
    ["대중교통 접근", "대중교통 접근"],
  ];
  const matched = patterns.find(([needle]) => message.includes(needle));
  return matched ? matched[1] : message;
}

function setAnswerText(text, options = {}) {
  fullAnswerText = text;
  compactAnswerText = compactAnswer(text);
  isAnswerExpanded = false;
  answerText.classList.toggle("empty", Boolean(options.empty));
  answerText.textContent = compactAnswerText;
  syncAnswerToggle();
}

function setAnswerExpanded(expanded) {
  isAnswerExpanded = expanded;
  answerText.textContent = isAnswerExpanded ? fullAnswerText : compactAnswerText;
  syncAnswerToggle();
}

function compactAnswer(text) {
  const normalized = String(text || "").replace(/\n{3,}/g, "\n\n").trim();
  if (normalized.length <= 150) return normalized;

  const paragraphs = normalized.split(/\n{2,}/).filter(Boolean);
  const firstParagraph = paragraphs[0] || normalized;
  const sentences = firstParagraph
    .split(/(?<=[.!?。！？요다니다함됨세요])\s+/)
    .filter(Boolean);
  const summary = sentences.slice(0, 2).join(" ").trim();

  if (summary.length >= 48 && summary.length <= 180) return summary;
  return `${firstParagraph.slice(0, 150).trim()}...`;
}

function syncAnswerToggle() {
  const isCompactable = fullAnswerText.trim() !== compactAnswerText.trim();
  answerToggleButton.hidden = !isCompactable;
  answerToggleButton.textContent = isAnswerExpanded ? "접기" : "전체 보기";
  answerToggleButton.setAttribute("aria-expanded", String(isAnswerExpanded));
}

function renderSources(sources, cards) {
  sourceList.replaceChildren();
  const seen = new Set();
  const sourceItems = [];

  sources.forEach((source) => {
    const title = source.title || source.source || source.name || "검색 문서";
    const url = source.url || source.source_url;
    const key = `${title}:${url || ""}`;
    if (seen.has(key)) return;
    seen.add(key);
    sourceItems.push({ title, url });
  });

  cards.forEach((card) => {
    const title = publicSourceName(card.source_name || "한국관광공사 무장애 여행 정보");
    const url = usableSourceUrl(card.source_url);
    const key = `${title}:${url || ""}`;
    if (seen.has(key)) return;
    seen.add(key);
    sourceItems.push({ title, url });
  });

  if (sourceItems.length === 0) {
    sourceList.append(createSourceEmpty("출처 정보가 비어 있습니다. 카드별 출처를 확인하세요."));
    return;
  }

  sourceItems.slice(0, 6).forEach((source) => {
    const item = document.createElement(source.url ? "a" : "span");
    item.className = "source-item";
    item.textContent = source.title;
    if (source.url) {
      item.href = source.url;
      item.target = "_blank";
      item.rel = "noreferrer";
    }
    sourceList.append(item);
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
  const evidenceHighlights = node.querySelector(".evidence-highlights");
  const tags = node.querySelector(".accessibility-tags");
  const details = node.querySelector(".details");
  const sourceChip = node.querySelector(".source-chip");

  title.textContent = card.title || "이름 없는 장소";
  address.textContent = card.address || "주소 확인 필요";
  reason.textContent = card.recommendation_reason || "추천 사유 확인 필요";
  sourceChip.textContent = card.source_name ? "출처 있음" : "출처 확인";

  if (card.image_url) {
    media.style.backgroundImage = `url("${card.image_url}")`;
  }

  const tagValues = [...(card.accessibility_tags || []), ...(card.family_tags || [])];
  const evidenceItems = cardEvidenceHighlights(card);
  evidenceHighlights.replaceChildren(...evidenceItems.map(([label, value]) => createEvidenceChip(label, value)));
  evidenceHighlights.hidden = evidenceItems.length === 0;

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

  const sourceUrl = usableSourceUrl(card.source_url);
  if (sourceUrl) {
    const source = document.createElement("a");
    source.href = sourceUrl;
    source.target = "_blank";
    source.rel = "noreferrer";
    source.textContent = "원문 보기";
    details.append(createDetail("출처", source));
  } else {
    details.append(createDetail("출처", publicSourceName(card.source_name || "한국관광공사 무장애 여행 정보")));
  }

  const rawDetailRows = rawDetailEntries(card);
  if (rawDetailRows.length > 0) {
    const detailPanel = document.createElement("div");
    detailPanel.className = "raw-detail-panel";
    detailPanel.hidden = true;

    const rawList = document.createElement("dl");
    rawList.className = "raw-details";
    rawDetailRows.forEach(([label, value]) => {
      const row = document.createElement("div");
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = label;
      dd.textContent = value;
      row.append(dt, dd);
      rawList.append(row);
    });
    detailPanel.append(rawList);

    const actions = document.createElement("div");
    actions.className = "card-actions";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.textContent = "상세 정보";
    toggle.addEventListener("click", () => {
      detailPanel.hidden = !detailPanel.hidden;
      toggle.textContent = detailPanel.hidden ? "상세 정보" : "상세 접기";
      toggle.setAttribute("aria-expanded", String(!detailPanel.hidden));
    });
    toggle.setAttribute("aria-expanded", "false");
    actions.append(toggle);

    const mapUrl = mapSearchUrl(card);
    if (mapUrl) {
      const mapLink = document.createElement("a");
      mapLink.href = mapUrl;
      mapLink.target = "_blank";
      mapLink.rel = "noreferrer";
      mapLink.textContent = "지도 검색";
      actions.append(mapLink);
    }

    node.querySelector(".card-body").append(actions, detailPanel);
  }

  return node;
}

function cardEvidenceHighlights(card) {
  const raw = normalizeObject(card.raw_fields);
  const accessibility = normalizeObject(card.accessibility);
  const candidates = [
    ["휠체어", firstValue(accessibility.wheelchair, raw["휠체어"], raw["출입통로"])],
    ["동선", firstValue(accessibility.route, raw["접근로"], raw["출입통로"], raw["대중교통"])],
    ["화장실", firstValue(accessibility.restroom, raw["화장실"])],
    ["주차", firstValue(accessibility.parking, raw["주차"])],
    ["승강", firstValue(accessibility.elevator, raw["엘리베이터"])],
    ["수어/자막", firstValue(raw["수어안내"], raw["자막/영상안내"], raw["청각장애"], raw["안내시설"])],
    ["점자/촉지", firstValue(raw["점자블록"], raw["점자홍보물"], raw["안내시스템"], raw["시각장애 기타"])],
    ["유아", firstValue(accessibility.stroller, accessibility.nursing_room, raw["유모차"], raw["수유실"], raw["유아용 의자"])],
  ];

  return candidates
    .filter(([, value]) => Boolean(value))
    .slice(0, 4)
    .map(([label, value]) => [label, shortenInline(value, 34)]);
}

function normalizeObject(value) {
  return value && typeof value === "object" ? value : {};
}

function firstValue(...values) {
  return values.find((value) => typeof value === "string" && value.trim());
}

function shortenInline(value, limit) {
  const normalized = String(value || "").replace(/<br\s*\/?>/gi, " ").replace(/\s+/g, " ").trim();
  if (normalized.length <= limit) return normalized;
  return `${normalized.slice(0, limit).trim()}...`;
}

function rawDetailEntries(card) {
  const rows = [];
  const seen = new Set();
  const labels = {
    parking: "주차",
    route: "접근로",
    publictransport: "대중교통",
    ticketoffice: "매표소",
    promotion: "홍보물",
    wheelchair: "휠체어",
    exit: "출입통로",
    elevator: "엘리베이터",
    restroom: "화장실",
    auditorium: "관람석",
    room: "객실",
    handicapetc: "장애인 기타",
    braileblock: "점자블록",
    helpdog: "보조견",
    guidehuman: "안내요원",
    audioguide: "오디오가이드",
    bigprint: "큰활자",
    brailepromotion: "점자홍보물",
    guidesystem: "안내시스템",
    blindhandicapetc: "시각장애 기타",
    signguide: "수어안내",
    videoguide: "자막/영상안내",
    hearingroom: "청각장애 객실",
    hearinghandicapetc: "청각장애 기타",
    stroller: "유모차",
    lactationroom: "수유실",
    babysparechair: "유아용 의자",
    infantsfamilyetc: "영유아 기타",
  };

  Object.entries(card.raw_fields || {}).forEach(([key, value]) => {
    if (!value) return;
    const label = labels[key] || key;
    rows.push([label, value]);
    seen.add(label);
  });

  Object.entries(card.accessibility || {}).forEach(([key, value]) => {
    const label = accessibilityLabels[key] || key;
    if (!value || seen.has(label)) return;
    rows.push([label, value]);
  });

  return rows;
}

function mapSearchUrl(card) {
  const query = [card.title, card.address].filter(Boolean).join(" ");
  if (!query) return null;
  return `https://map.naver.com/p/search/${encodeURIComponent(query)}`;
}

function usableSourceUrl(url) {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    if (parsed.hostname === "access.visitkorea.or.kr" && parsed.pathname.startsWith("/detail/")) {
      return null;
    }
    return parsed.href;
  } catch {
    return null;
  }
}

function publicSourceName(sourceName) {
  return String(sourceName || "").replace(" OpenAPI", "");
}

function createTag(text, needsCheck = false) {
  const tag = document.createElement("span");
  tag.className = needsCheck ? "tag needs-check" : "tag";
  tag.textContent = text;
  return tag;
}

function createEvidenceChip(label, value) {
  const chip = document.createElement("span");
  chip.className = "evidence-chip";

  const name = document.createElement("strong");
  name.textContent = label;

  const text = document.createElement("span");
  text.textContent = value;

  chip.append(name, text);
  return chip;
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

function createSourceEmpty(text = "응답 후 한국관광공사 자료와 카드별 출처가 표시됩니다.") {
  const empty = document.createElement("span");
  empty.className = "source-empty";
  empty.textContent = text;
  return empty;
}

function toggleDebugPanel() {
  if (!debugMode) return;
  debugPanel.hidden = !debugPanel.hidden;
  debugToggleButton.setAttribute("aria-expanded", String(!debugPanel.hidden));
}

function renderUserMessage(message) {
  userEcho.textContent = message;
  userEcho.hidden = false;
  scrollChatToBottom();
}

function showToast(message, tone = "") {
  toast.textContent = message;
  toast.className = `toast ${tone}`.trim();
  toast.hidden = false;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(hideToast, 2600);
}

function hideToast() {
  window.clearTimeout(showToast.timer);
  toast.hidden = true;
  toast.textContent = "";
  toast.className = "toast";
}

function scrollChatToBottom() {
  window.requestAnimationFrame(() => {
    chatScroll.scrollTop = chatScroll.scrollHeight;
  });
}

function createSessionId() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `web-${Date.now()}-${Math.random().toString(36).slice(2)}`;
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
