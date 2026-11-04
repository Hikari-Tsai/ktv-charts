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
    appleListen: "Apple Music 試聽",
    appleSearch: "Apple Music 搜尋",
    kkboxListen: "KKBOX 試聽",
    kkboxSearch: "KKBOX 搜尋",
    playerTitle: "{service} 播放器：{q}",
    closePlayer: "再點一次收起播放器",
    searchHint: "沒有找到對應曲目，改為搜尋「{q}」",
    genreHint: "曲風：{g}（Apple Music 分類）",
    genreCredit: "曲風與 Apple Music 連結來自 iTunes Search API；BPM 由 Beat This! 模型分析 30 秒試聽估算。",
    bpmHint: "由 Beat This! 模型分析 30 秒試聽估算，可能是實際速度的一半或兩倍",
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
    appleListen: "Listen on Apple Music",
    appleSearch: "Search Apple Music",
    kkboxListen: "Listen on KKBOX",
    kkboxSearch: "Search KKBOX",
    playerTitle: "{service} player: {q}",
    closePlayer: "Click again to close the player",
    searchHint: "No matching track found; searches for “{q}”",
    genreHint: "Genre: {g} (Apple Music category)",
    genreCredit: "Genres and Apple Music links come from the iTunes Search API; BPM is estimated from 30-second previews with the Beat This! model.",
    bpmHint: "Estimated from a 30-second preview with the Beat This! model; may be half or double the real tempo",
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
    appleListen: "Apple Music で試聴",
    appleSearch: "Apple Music で検索",
    kkboxListen: "KKBOX で試聴",
    kkboxSearch: "KKBOX で検索",
    playerTitle: "{service} プレーヤー：{q}",
    closePlayer: "もう一度押すとプレーヤーを閉じます",
    searchHint: "該当曲が見つからないため「{q}」を検索します",
    genreHint: "ジャンル：{g}（Apple Music の分類）",
    genreCredit: "ジャンルと Apple Music のリンクは iTunes Search API から取得し、BPM は Beat This! モデルで 30 秒の試聴音源から推定しています。",
    bpmHint: "Beat This! モデルで 30 秒の試聴音源から推定。実際のテンポの半分または倍の場合があります",
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

/* Genre names come from iTunes in English; hue picks the tag colour. Unknown genres
   keep the English name and get a stable colour from a hash of the name. */
const GENRES = {
  "Pop": { zh: "流行", ja: "ポップ", h: 330 },
  "Mandopop": { zh: "華語流行", ja: "華語ポップ", h: 350 },
  "Cantopop": { zh: "粵語流行", ja: "広東語ポップ", h: 15 },
  "Tai-Pop": { zh: "台語流行", ja: "台湾語ポップ", h: 28 },
  "J-Pop": { zh: "J-Pop", ja: "J-Pop", h: 300 },
  "K-Pop": { zh: "K-Pop", ja: "K-Pop", h: 275 },
  "Kayokyoku": { zh: "歌謠曲", ja: "歌謡曲", h: 40 },
  "Enka": { zh: "演歌", ja: "演歌", h: 45 },
  "Anime": { zh: "動畫", ja: "アニメ", h: 190 },
  "Rock": { zh: "搖滾", ja: "ロック", h: 5 },
  "Hard Rock": { zh: "硬式搖滾", ja: "ハードロック", h: 0 },
  "Metal": { zh: "金屬", ja: "メタル", h: 0 },
  "Punk": { zh: "龐克", ja: "パンク", h: 10 },
  "Alternative": { zh: "另類", ja: "オルタナティブ", h: 20 },
  "Indie Pop": { zh: "獨立流行", ja: "インディーポップ", h: 320 },
  "Hip-Hop/Rap": { zh: "嘻哈／饒舌", ja: "ヒップホップ／ラップ", h: 255 },
  "Hip-Hop": { zh: "嘻哈", ja: "ヒップホップ", h: 255 },
  "Rap": { zh: "饒舌", ja: "ラップ", h: 250 },
  "R&B/Soul": { zh: "R&B／靈魂", ja: "R&B／ソウル", h: 230 },
  "Soul": { zh: "靈魂樂", ja: "ソウル", h: 230 },
  "Electronic": { zh: "電子", ja: "エレクトロニック", h: 180 },
  "Dance": { zh: "舞曲", ja: "ダンス", h: 170 },
  "House": { zh: "浩室", ja: "ハウス", h: 175 },
  "Soundtrack": { zh: "原聲帶", ja: "サウンドトラック", h: 140 },
  "Original Score": { zh: "配樂", ja: "スコア", h: 145 },
  "Musicals": { zh: "音樂劇", ja: "ミュージカル", h: 150 },
  "Singer/Songwriter": { zh: "創作歌手", ja: "シンガーソングライター", h: 95 },
  "Folk": { zh: "民謠", ja: "フォーク", h: 85 },
  "Country": { zh: "鄉村", ja: "カントリー", h: 70 },
  "Jazz": { zh: "爵士", ja: "ジャズ", h: 50 },
  "Blues": { zh: "藍調", ja: "ブルース", h: 215 },
  "Classical": { zh: "古典", ja: "クラシック", h: 205 },
  "Vocal": { zh: "人聲", ja: "ヴォーカル", h: 60 },
  "Easy Listening": { zh: "輕音樂", ja: "イージーリスニング", h: 120 },
  "New Age": { zh: "新世紀", ja: "ニューエイジ", h: 160 },
  "Reggae": { zh: "雷鬼", ja: "レゲエ", h: 110 },
  "Latin": { zh: "拉丁", ja: "ラテン", h: 35 },
  "World": { zh: "世界音樂", ja: "ワールド", h: 100 },
  "Children's Music": { zh: "兒童音樂", ja: "キッズ", h: 55 },
  "Holiday": { zh: "節慶", ja: "ホリデー", h: 125 },
  "Christmas": { zh: "聖誕", ja: "クリスマス", h: 125 },
};

function genreInfo(name) {
  const g = GENRES[name];
  if (g) return { label: state.lang === "en" ? name : g[state.lang], hue: g.h };
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.codePointAt(0)) % 360;
  return { label: name, hue: hash };
}

function sourceRegion() {
  return state.index?.sources.find((s) => s.id === state.source)?.region || "tw";
}

function songQuery(row) {
  return [row.title, row.artist].filter(Boolean).join(" ");
}

function appleLink(row) {
  if (row.apple) {
    const [cc, id] = row.apple.split("/");
    return {
      href: `https://music.apple.com/${cc}/song/${id}`,
      embed: `https://embed.music.apple.com/${cc}/song/${id}`,
      label: t("appleListen"),
      direct: true,
    };
  }
  return {
    href: `https://music.apple.com/${sourceRegion()}/search?term=` + encodeURIComponent(songQuery(row)),
    label: t("appleSearch"),
    direct: false,
  };
}

function kkboxLink(row) {
  if (row.kkbox) {
    const widget = "https://widget.kkbox.com/v1/?id=" + encodeURIComponent(row.kkbox) + "&type=song&terr=tw&lang=tc";
    return { href: widget + "&autoplay=true", embed: widget + "&autoplay=true", label: t("kkboxListen"), direct: true };
  }
  return {
    href: "https://www.kkbox.com/tw/tc/search?q=" + encodeURIComponent(songQuery(row)),
    label: t("kkboxSearch"),
    direct: false,
  };
}

const YT_ICON =
  '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .6 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2 2.1c2 .5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8ZM9.7 15.1V8.9l5.8 3.1-5.8 3.1Z"/></svg>';

// Brand marks: Apple Music glyph from Simple Icons (CC0 path data); KKBOX app icon from kkbox.com.
// Trademarks belong to their owners and are used only to label links to their services.
const APPLE_ICON =
  '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M23.994 6.124a9.23 9.23 0 00-.24-2.19c-.317-1.31-1.062-2.31-2.18-3.043a5.022 5.022 0 00-1.877-.726 10.496 10.496 0 00-1.564-.15c-.04-.003-.083-.01-.124-.013H5.986c-.152.01-.303.017-.455.026-.747.043-1.49.123-2.193.4-1.336.53-2.3 1.452-2.865 2.78-.192.448-.292.925-.363 1.408-.056.392-.088.785-.1 1.18 0 .032-.007.062-.01.093v12.223c.01.14.017.283.027.424.05.815.154 1.624.497 2.373.65 1.42 1.738 2.353 3.234 2.801.42.127.856.187 1.293.228.555.053 1.11.06 1.667.06h11.03a12.5 12.5 0 001.57-.1c.822-.106 1.596-.35 2.295-.81a5.046 5.046 0 001.88-2.207c.186-.42.293-.87.37-1.324.113-.675.138-1.358.137-2.04-.002-3.8 0-7.595-.003-11.393zm-6.423 3.99v5.712c0 .417-.058.827-.244 1.206-.29.59-.76.962-1.388 1.14-.35.1-.706.157-1.07.173-.95.045-1.773-.6-1.943-1.536a1.88 1.88 0 011.038-2.022c.323-.16.67-.25 1.018-.324.378-.082.758-.153 1.134-.24.274-.063.457-.23.51-.516a.904.904 0 00.02-.193c0-1.815 0-3.63-.002-5.443a.725.725 0 00-.026-.185c-.04-.15-.15-.243-.304-.234-.16.01-.318.035-.475.066-.76.15-1.52.303-2.28.456l-2.325.47-1.374.278c-.016.003-.032.01-.048.013-.277.077-.377.203-.39.49-.002.042 0 .086 0 .13-.002 2.602 0 5.204-.003 7.805 0 .42-.047.836-.215 1.227-.278.64-.77 1.04-1.434 1.233-.35.1-.71.16-1.075.172-.96.036-1.755-.6-1.92-1.544-.14-.812.23-1.685 1.154-2.075.357-.15.73-.232 1.108-.31.287-.06.575-.116.86-.177.383-.083.583-.323.6-.714v-.15c0-2.96 0-5.922.002-8.882 0-.123.013-.25.042-.37.07-.285.273-.448.546-.518.255-.066.515-.112.774-.165.733-.15 1.466-.296 2.2-.444l2.27-.46c.67-.134 1.34-.27 2.01-.403.22-.043.442-.088.663-.106.31-.025.523.17.554.482.008.073.012.148.012.223.002 1.91.002 3.822 0 5.732z"/></svg>';
const KKBOX_ICON_SRC = "assets/kkbox.png";

function brandIcon(kind) {
  if (kind === "apple") {
    const span = el("span", { class: "icon" });
    span.innerHTML = APPLE_ICON;
    return span;
  }
  return el("img", { class: "icon", src: KKBOX_ICON_SRC, alt: "", width: "14", height: "14", decoding: "async" });
}

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
  $("#genre-credit").textContent = t("genreCredit");
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

/* ---------- embedded players ---------- */

const PLAYER = {
  apple: {
    service: "Apple Music",
    height: 175,
    allow: "autoplay *; encrypted-media *; clipboard-write",
    sandbox: "allow-forms allow-popups allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation",
  },
  kkbox: { service: "KKBOX", height: 112, allow: "autoplay; encrypted-media", sandbox: null },
};

let openPlayer = null; // { row: <tr>, button }

function closePlayer() {
  if (!openPlayer) return;
  openPlayer.row.remove();
  openPlayer.button.setAttribute("aria-expanded", "false");
  openPlayer = null;
}

function togglePlayer(songRow, button, kind, src, query) {
  const reopen = !(openPlayer && openPlayer.button === button);
  closePlayer();
  if (!reopen) return;
  const cfg = PLAYER[kind];
  const iframe = el("iframe", {
    class: `player player-${kind}`,
    src,
    title: t("playerTitle", { service: cfg.service, q: query }),
    allow: cfg.allow,
    sandbox: cfg.sandbox,
    loading: "eager",
    referrerpolicy: "strict-origin-when-cross-origin",
  });
  iframe.style.height = cfg.height + "px";
  const row = el("tr", { class: "player-row" }, el("td", { colspan: "3", class: "player-cell" }, iframe));
  songRow.after(row);
  button.setAttribute("aria-expanded", "true");
  openPlayer = { row, button };
}

function genreTag(row) {
  if (!row.genre) return null;
  const g = genreInfo(row.genre);
  const tag = el("span", { class: "tag", title: t("genreHint", { g: g.label }), text: g.label });
  tag.style.setProperty("--h", String(g.hue));
  return tag;
}

function songCell(row) {
  const titleNode = row.song_url
    ? el("a", { href: row.song_url, target: "_blank", rel: "noopener", text: row.title })
    : row.title;
  const sub = el("div", { class: "song-sub" }, row.artist || "");
  if (row.song_no) sub.append(el("span", { class: "song-no", title: t("songNo"), text: `#${row.song_no}` }));
  if (row.bpm) sub.append(el("span", { class: "bpm", title: t("bpmHint"), text: `${row.bpm} BPM` }));
  const head = el("div", { class: "song-title" }, titleNode);
  const tag = genreTag(row);
  if (tag) head.append(" ", tag);
  return [head, sub];
}

function linkRow(row, songRow) {
  const q = songQuery(row);
  const yt = el("a", {
    class: "btn yt",
    href: youtubeUrl(row),
    target: "_blank",
    rel: "noopener",
    "aria-label": t("ytAria", { q }),
  });
  yt.innerHTML = YT_ICON;
  yt.append(el("span", { text: t("ytSearch") }));

  const links = [yt];
  for (const [kind, info] of [["apple", appleLink(row)], ["kkbox", kkboxLink(row)]]) {
    if (info.direct) {
      // Opens the official player under this song; ctrl/cmd-click still opens the page.
      const link = el("a", {
        class: `btn ${kind}`,
        href: info.href,
        target: "_blank",
        rel: "noopener",
        role: "button",
        "aria-expanded": "false",
        title: t("closePlayer"),
      }, brandIcon(kind), el("span", { text: info.label }));
      link.addEventListener("click", (ev) => {
        if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button !== 0) return;
        ev.preventDefault();
        togglePlayer(songRow, link, kind, info.embed, q);
      });
      links.push(link);
    } else {
      links.push(el("a", {
        class: `btn ${kind} search`,
        href: info.href,
        target: "_blank",
        rel: "noopener",
        title: t("searchHint", { q }),
      }, brandIcon(kind), el("span", { text: info.label })));
    }
  }
  return el("div", { class: "song-links" }, ...links);
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

  openPlayer = null; // the old player row goes away with the old rows
  const frag = document.createDocumentFragment();
  for (const row of chart.rows) {
    const songCellNode = el("td", { class: "col-song" }, ...songCell(row));
    const tr = el("tr", { class: row.rank <= 3 ? "podium" : null },
      el("td", { class: "col-rank", text: String(row.rank) }),
      el("td", { class: "col-change" }, changeCell(row, chart)),
      songCellNode);
    songCellNode.append(linkRow(row, tr));
    frag.append(tr);
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
