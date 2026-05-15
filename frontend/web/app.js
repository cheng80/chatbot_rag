const form = document.querySelector("#chatForm");
const messageInput = document.querySelector("#message");
const apiBaseInput = document.querySelector("#apiBase");
const submitButton = document.querySelector("#submitButton");
const requestState = document.querySelector("#requestState");
const diagnostics = document.querySelector("#diagnostics");
const answerText = document.querySelector("#answerText");
const answerToggleButton = document.querySelector("#answerToggleButton");
const clarificationBanner = document.querySelector("#clarificationBanner");
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
      source_name: "한국관광공사 무장애 여행 정보 OpenAPI",
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
      source_name: "한국관광공사 무장애 여행 정보 OpenAPI",
    },
  ],
};

apiBaseInput.value = defaultApiBase();
syncApiDocLinks();
apiBaseInput.addEventListener("input", syncApiDocLinks);
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
  });
});

clearButton.addEventListener("click", () => {
  document.querySelectorAll("[data-region]").forEach((regionButton) => {
    regionButton.setAttribute("aria-pressed", "false");
  });
  setState("대기 중");
  diagnostics.replaceChildren();
  clarificationBanner.hidden = true;
  suggestions.replaceChildren();
  suggestions.classList.remove("clarification-options");
  sourceList.replaceChildren(createSourceEmpty());
  setAnswerText("질문을 보내면 답변과 추천 카드가 여기에 표시됩니다.", { empty: true });
  cardsGrid.replaceChildren();
  cardCount.textContent = "0개";
  demoMoreButton.disabled = true;
  demoMoreButton.textContent = "더 보기";
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
    setAnswerText(`API 서버에 연결하지 못했습니다.\n${error.message}`);
    suggestions.replaceChildren();
    clarificationBanner.hidden = true;
    suggestions.classList.remove("clarification-options");
    sourceList.replaceChildren(createSourceEmpty("API 연결 후 출처가 표시됩니다."));
    cardsGrid.replaceChildren();
    cardCount.textContent = "0개";
    demoMoreButton.disabled = true;
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
  submitButton.textContent = isLoading ? "조회 중" : "추천 받기";
  if (isLoading) {
    demoMoreButton.disabled = true;
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

  setAnswerText(payload.answer || "답변 문장이 비어 있습니다.", { empty: !payload.answer });
  clarificationBanner.hidden = mode !== "clarification";
  renderSuggestions(payload.suggested_messages || []);
  renderSources(payload.sources || [], cards);
  cardCount.textContent = `${cards.length}개`;
  cardsGrid.replaceChildren(...cards.map(renderCard));
}

function renderDemoPreview() {
  setState("시연 예시");
  diagnostics.replaceChildren(createDiagnostic("지역 선택, 추천 카드, 더 보기, 출처, 경고 문구가 보이도록 구성한 초기 예시입니다."));
  setAnswerText(demoPreview.answer);
  sourceList.replaceChildren(
    createSourceEmpty("예시 출처: 한국관광공사 무장애 여행 정보 OpenAPI"),
    createSourceEmpty("실제 응답 후 카드별 원문 링크가 표시됩니다."),
  );
  cardCount.textContent = `${demoPreview.cards.length}개`;
  cardsGrid.replaceChildren(...demoPreview.cards.map(renderCard));
  demoMoreButton.disabled = true;
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

  setAnswerText(`${message}${code}`);
  clarificationBanner.hidden = true;
  suggestions.replaceChildren();
  suggestions.classList.remove("clarification-options");
  sourceList.replaceChildren(createSourceEmpty("오류가 해결되면 출처가 표시됩니다."));
  cardsGrid.replaceChildren();
  cardCount.textContent = "0개";
  demoMoreButton.disabled = true;
}

function renderSuggestions(messages) {
  suggestions.replaceChildren();
  suggestions.classList.toggle("clarification-options", !clarificationBanner.hidden && messages.length > 0);
  const moreMessage = messages.find((message) => /더 보기|전체|전부|20곳/.test(message));
  demoMoreButton.disabled = !moreMessage;
  demoMoreButton.textContent = moreMessage || "더 보기";
  demoMoreButton.onclick = moreMessage
    ? () => {
        messageInput.value = moreMessage;
        form.requestSubmit();
      }
    : null;
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
    const title = card.source_name || "한국관광공사 무장애 여행 정보 OpenAPI";
    const url = usableSourceUrl(card.source_url);
    const key = `${title}:${url || ""}`;
    if (seen.has(key)) return;
    seen.add(key);
    sourceItems.push({ title, url });
  });

  if (sourceItems.length === 0) {
    sourceList.append(createSourceEmpty("출처 정보가 비어 있습니다. 응답 경로와 카드별 출처를 확인하세요."));
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
    details.append(createDetail("출처", card.source_name || "한국관광공사 무장애 여행 정보 OpenAPI"));
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
    });
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

function createSourceEmpty(text = "응답 후 한국관광공사 OpenAPI, live 캐시, 색인 문서 출처가 표시됩니다.") {
  const empty = document.createElement("span");
  empty.className = "source-empty";
  empty.textContent = text;
  return empty;
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
