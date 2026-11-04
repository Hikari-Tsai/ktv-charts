"use strict";

/* ---------- i18n ---------- */

const LANGS = ["zh", "en", "ja"];
const DEFAULT_LANG = "zh";
const HTML_LANG = { zh: "zh-Hant", en: "en", ja: "ja" };
const LOCALE = { zh: "zh-TW", en: "en-US", ja: "ja-JP" };

const I18N = {
  zh: {
    title: "KTV 點歌排行榜",
    colon: "：",
    subtitle: "好樂迪、錢櫃、JOYSOUND、DAM 與 KKBOX 每日自動更新",
    colRank: "名次",
    colChange: "升降",
    colSong: "歌曲",
    colLink: "YouTube",
    ytSearch: "在YouTube搜尋",
    ytAria: "在 YouTube 搜尋「{q}」",
    region_tw: "台灣",
    region_jp: "日本",
    streaming: "串流",
    period: "集計期間",
    fetched: "抓取時間",
    official: "官方頁面",
    songNo: "曲號",
    newEntry: "新進",
    noPrev: "尚無上期資料",
    prevRank: "上期第 {n} 名",
    changeFromHistory: "升降依本站前次記錄計算，第一次收錄時不顯示。",
    stale: "這張榜本次更新失敗，顯示的是 {time} 的資料。",
    loading: "載入中…",
    loadError: "資料載入失敗，請稍後再試。",
    empty: "這張榜沒有資料。",
    disclaimer: "資料取自各 KTV 與 KKBOX 官方網站公開頁面，著作權屬原網站所有。本站與各業者無關。",
    sources: "資料來源",
  },
  en: {
    title: "KTV Song Rankings",
    colon: ": ",
    subtitle: "Holiday KTV, Cashbox, JOYSOUND, DAM and KKBOX, updated daily",
    colRank: "Rank",
    colChange: "Move",
    colSong: "Song",
    colLink: "YouTube",
    ytSearch: "Search on YouTube",
    ytAria: "Search YouTube for “{q}”",
    region_tw: "Taiwan",
    region_jp: "Japan",
    streaming: "Streaming",
    period: "Period",
    fetched: "Fetched",
    official: "Official page",
    songNo: "Song no.",
    newEntry: "NEW",
    noPrev: "No previous data yet",
    prevRank: "Last time: #{n}",
    changeFromHistory: "Movement is computed from this site's previous snapshot and is blank on first capture.",
    stale: "This chart failed to update; showing data from {time}.",
    loading: "Loading…",
    loadError: "Could not load data. Please try again later.",
    empty: "No data for this chart.",
    disclaimer: "Data comes from the public websites of each KTV operator and KKBOX; rights belong to the original sites. This site is not affiliated with any of them.",
    sources: "Sources",
  },
  ja: {
    title: "カラオケ人気ランキング",
    colon: "：",
    subtitle: "好樂迪・錢櫃・JOYSOUND・DAM・KKBOX を毎日自動更新",
    colRank: "順位",
    colChange: "変動",
    colSong: "曲",
    colLink: "YouTube",
    ytSearch: "YouTubeで検索",
    ytAria: "YouTube で「{q}」を検索",
    region_tw: "台湾",
    region_jp: "日本",
    streaming: "ストリーミング",
    period: "集計期間",
    fetched: "取得日時",
    official: "公式ページ",
    songNo: "曲番",
    newEntry: "NEW",
    noPrev: "前回データなし",
    prevRank: "前回 {n} 位",
    changeFromHistory: "変動は本サイトの前回記録から算出しています。初回取得時は表示されません。",
    stale: "このランキングは今回の更新に失敗しました。{time} 時点のデータを表示しています。",
    loading: "読み込み中…",
    loadError: "データを読み込めませんでした。しばらくしてから再度お試しください。",
    empty: "このランキングにはデータがありません。",
    disclaimer: "データは各カラオケ事業者と KKBOX の公式サイトの公開ページから取得しています。権利は各サイトに帰属します。本サイトは各事業者とは関係ありません。",
    sources: "データ提供元",
  },
};

function t(key, vars) {
  const dict = I18N[state.lang] || I18N[DEFAULT_LANG];
  let s = dict[key] ?? I18N[DEFAULT_LANG][key] ?? key;
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, v);
  return s;
}

/** Pick the current language from a {zh, en, ja} object, or return a plain string as-is. */
function pick(value) {
  if (value && typeof value === "object") return value[state.lang] ?? value[DEFAULT_LANG] ?? "";
  return value ?? "";
}

/* ---------- state ---------- */

const state = {
  lang: DEFAULT_LANG,
  index: null,
  source: null,
  chart: null,
  cache: new Map(),
};

function storageGet(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function storageSet(key, value) {
  try { localStorage.setItem(key, value); } catch { /* private mode etc. */ }
}

function initialLang() {
  const q = new URLSearchParams(location.search).get("lang");
  if (LANGS.includes(q)) return q;
  const saved = storageGet("ktv-lang");
  return LANGS.includes(saved) ? saved : DEFAULT_LANG;
}

function readHash() {
  const [source, chart] = decodeURIComponent(location.hash.slice(1)).split("/");
  return { source: source || null, chart: chart || null };
}

function writeHash() {
  const hash = `#${state.source}/${state.chart}`;
  if (location.hash !== hash) history.replaceState(null, "", location.pathname + location.search + hash);
}

/* ---------- dom helpers ---------- */

const $ = (sel) => document.querySelector(sel);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children) if (c != null) node.append(c);
  return node;
}

const YT_ICON =
  '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .6 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2 2.1c2 .5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8ZM9.7 15.1V8.9l5.8 3.1-5.8 3.1Z"/></svg>';

function youtubeUrl(row) {
  const q = [row.title, row.artist].filter(Boolean).join(" ");
  return "https://www.youtube.com/results?search_query=" + encodeURIComponent(q);
}

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat(LOCALE[state.lang], {
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
  }).format(d);
}

/* ---------- data ---------- */

async function getJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

async function loadSource(id) {
  if (!state.cache.has(id)) state.cache.set(id, getJson(`data/${id}.json`));
  try {
    return await state.cache.get(id);
  } catch (err) {
    state.cache.delete(id); // allow a retry on next selection
    throw err;
  }
}

/* ---------- render ---------- */

function applyStaticText() {
  document.documentElement.lang = HTML_LANG[state.lang];
  document.title = t("title");
  for (const node of document.querySelectorAll("[data-i18n]")) node.textContent = t(node.dataset.i18n);
  for (const btn of document.querySelectorAll(".lang button")) {
    btn.setAttribute("aria-pressed", String(btn.dataset.lang === state.lang));
  }
  const links = $("#source-links");
  links.replaceChildren(t("sources") + t("colon"));
  (state.index?.sources || []).forEach((s, i) => {
    if (i) links.append(" · ");
    links.append(el("a", { href: s.site_url, target: "_blank", rel: "noopener", text: pick(s.name) }));
  });
}

function renderSourceTabs() {
  const nav = $("#sources");
  nav.replaceChildren(
    ...state.index.sources.map((s) =>
      el("button", {
        type: "button",
        role: "tab",
        "aria-selected": String(s.id === state.source),
        onclick: () => selectSource(s.id),
      },
      el("span", { text: pick(s.name).replace(/\s*\(.*\)$/, "") }),
      el("span", { class: "region", text: t("region_" + s.region) + (s.kind === "streaming" ? " · " + t("streaming") : "") }))
    )
  );
}

function renderChartPills(data) {
  const nav = $("#charts");
  nav.replaceChildren(
    ...data.charts.map((c) =>
      el("button", {
        type: "button",
        "aria-pressed": String(c.id === state.chart),
        onclick: () => selectChart(c.id),
        text: pick(c.title),
      })
    )
  );
  nav.querySelector('[aria-pressed="true"]')?.scrollIntoView({ block: "nearest", inline: "nearest" });
}

function changeCell(row, chart) {
  if (row.is_new === true) return el("span", { class: "new", text: t("newEntry") });
  if (row.last_rank == null) {
    return el("span", { class: "none", title: t("noPrev"), "aria-label": t("noPrev"), text: "–" });
  }
  const diff = row.last_rank - row.rank;
  const title = t("prevRank", { n: row.last_rank });
  if (diff > 0) return el("span", { class: "up", title, text: `↑${diff}` });
  if (diff < 0) return el("span", { class: "down", title, text: `↓${-diff}` });
  return el("span", { class: "same", title, text: "→" });
}

function songCell(row) {
  const titleNode = row.song_url
    ? el("a", { href: row.song_url, target: "_blank", rel: "noopener", text: row.title })
    : row.title;
  const sub = el("div", { class: "song-sub" }, row.artist || "");
  if (row.song_no) sub.append(el("span", { class: "song-no", title: t("songNo"), text: `#${row.song_no}` }));
  return [el("div", { class: "song-title" }, titleNode), sub];
}

function linkCell(row) {
  const q = [row.title, row.artist].filter(Boolean).join(" ");
  const a = el("a", {
    class: "yt",
    href: youtubeUrl(row),
    target: "_blank",
    rel: "noopener",
    "aria-label": t("ytAria", { q }),
  });
  a.innerHTML = YT_ICON;
  a.append(el("span", { class: "yt-label", text: t("ytSearch") }));
  return a;
}

function renderChart(data) {
  const chart = data.charts.find((c) => c.id === state.chart);
  const meta = $("#meta");
  const notice = $("#notice");
  const tbody = $("#rows");
  const empty = $("#empty");

  if (!chart) {
    meta.replaceChildren();
    tbody.replaceChildren();
    notice.hidden = true;
    empty.textContent = t("empty");
    empty.hidden = false;
    return;
  }

  const parts = [];
  if (chart.period) parts.push(el("span", {}, t("period") + t("colon"), el("strong", { text: chart.period })));
  if (chart.fetched_at) parts.push(el("span", { text: t("fetched") + t("colon") + formatTime(chart.fetched_at) }));
  if (chart.source_url) {
    parts.push(el("a", { href: chart.source_url, target: "_blank", rel: "noopener", text: `${t("official")} ↗` }));
  }
  meta.replaceChildren(...parts);

  const notes = [];
  if (chart.stale) notes.push(t("stale", { time: formatTime(chart.fetched_at) }));
  if (chart.rank_change === "history" && chart.rows.every((r) => r.last_rank == null && r.is_new == null)) {
    notes.push(t("changeFromHistory"));
  }
  notice.textContent = notes.join(" ");
  notice.hidden = notes.length === 0;

  const frag = document.createDocumentFragment();
  for (const row of chart.rows) {
    frag.append(
      el("tr", {},
        el("td", { class: "col-rank", text: String(row.rank) }),
        el("td", { class: "col-change" }, changeCell(row, chart)),
        el("td", { class: "col-song" }, ...songCell(row)),
        el("td", { class: "col-link" }, linkCell(row)))
    );
  }
  tbody.replaceChildren(frag);
  empty.hidden = chart.rows.length > 0;
  if (!chart.rows.length) empty.textContent = t("empty");
}

function showMessage(text) {
  $("#meta").replaceChildren();
  $("#notice").hidden = true;
  $("#rows").replaceChildren();
  $("#empty").textContent = text;
  $("#empty").hidden = false;
}

/* ---------- actions ---------- */

let renderToken = 0;

async function render() {
  const token = ++renderToken;
  applyStaticText();
  if (!state.index) return;
  renderSourceTabs();
  let data;
  try {
    if (!state.cache.has(state.source)) showMessage(t("loading"));
    data = await loadSource(state.source);
  } catch (err) {
    console.error(err);
    if (token === renderToken) showMessage(t("loadError"));
    return;
  }
  if (token !== renderToken) return; // a newer selection won
  if (!data.charts.some((c) => c.id === state.chart)) state.chart = data.charts[0]?.id ?? null;
  writeHash();
  renderChartPills(data);
  renderChart(data);
}

function selectSource(id) {
  if (id === state.source) return;
  state.source = id;
  state.chart = null;
  render();
}

function selectChart(id) {
  state.chart = id;
  render();
}

function setLang(lang) {
  if (!LANGS.includes(lang) || lang === state.lang) return;
  state.lang = lang;
  storageSet("ktv-lang", lang);
  const url = new URL(location.href);
  if (url.searchParams.has("lang")) {
    url.searchParams.set("lang", lang);
    history.replaceState(null, "", url);
  }
  render();
}

async function init() {
  state.lang = initialLang();
  for (const btn of document.querySelectorAll(".lang button")) {
    btn.addEventListener("click", () => setLang(btn.dataset.lang));
  }
  applyStaticText();
  showMessage(t("loading"));
  try {
    state.index = await getJson("data/index.json");
  } catch (err) {
    console.error(err);
    showMessage(t("loadError"));
    return;
  }
  const ids = state.index.sources.map((s) => s.id);
  const fromHash = readHash();
  state.source = ids.includes(fromHash.source) ? fromHash.source : ids[0];
  state.chart = fromHash.chart;
  window.addEventListener("hashchange", () => {
    const h = readHash();
    if (h.source === state.source && h.chart === state.chart) return;
    if (ids.includes(h.source)) state.source = h.source;
    state.chart = h.chart;
    render();
  });
  render();
}

init();
