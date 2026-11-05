# KTV 點歌排行榜

[![Update rankings](https://github.com/Hikari-Tsai/ktv-charts/actions/workflows/update.yml/badge.svg)](https://github.com/Hikari-Tsai/ktv-charts/actions/workflows/update.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**網站：<https://hikari-tsai.github.io/ktv-charts/>**

彙整台灣與日本四家 KTV 的點歌排行榜，加上 KKBOX 風雲榜的串流排行，每天由 GitHub Actions 自動抓取並發布成靜態網頁。

| 地區 | KTV | 收錄榜單 |
|---|---|---|
| 台灣 | 好樂迪 | 國、台、粵、英、日、韓、越語點播，國台語新歌 |
| 台灣 | 錢櫃 | 國、台、粵、日、英語點播，國台語新歌 |
| 日本 | JOYSOUND | 綜合日／週／月榜，動畫、VOCALOID、演歌、西洋週榜 |
| 日本 | DAM | 綜合日／週／月榜，急上昇、動畫、VOCALOID、VTuber、演歌、外國曲、對唱週榜 |
| 台灣 | KKBOX（串流） | 華語、台語、西洋、日語、韓語、粵語單曲日榜與週榜，華語新歌週榜 |

## 功能

- **五個來源 46 張榜**：好樂迪與錢櫃每榜 30 名，JOYSOUND 與 DAM 每榜 100 名，KKBOX 每榜 50 名。
- **三種語言**：中文、English、日本語，純前端即時切換，預設中文。選擇會記在瀏覽器裡，也可以用 `?lang=en` 或 `?lang=ja` 直接指定。
- **曲風標籤**：歌名後面以不同顏色標出曲風，例如華語流行、台語流行、J-Pop、演歌、動畫、搖滾。曲風取自 iTunes Search API 的 Apple Music 分類，同一曲風在三種語言下顏色一致。
- **BPM**：歌手後面標出歌曲速度，用 [Beat This!](https://github.com/CPJKU/beat_this) 模型的 ONNX 版本 [aaatmy/beat-this-onnx](https://huggingface.co/aaatmy/beat-this-onnx) 分析 iTunes 的 30 秒試聽估算。
- **Hashtag 標籤**：依風格、情緒、樂器、人聲分組標出 `#抒情 #放鬆 #鋼琴 #女聲` 這類標籤，用 Essentia 的 Discogs-EffNet 模型分析試聽得來，每組都有門檻與數量上限。
- **四個連結**：每首歌附「在YouTube搜尋」、「Apple Music 試聽」、「KKBOX 試聽」、「Spotify 試聽」。
  - YouTube 以「歌名 歌手」當關鍵字開啟 `https://www.youtube.com/results?search_query=`。
  - 點「Apple Music 試聽」或「KKBOX 試聽」會在該首歌下方展開官方嵌入播放器，同時只開一個，再點一次收起。按住 Ctrl 或 ⌘ 點擊則改為開新分頁。
  - Apple Music 播放器使用 `embed.music.apple.com`，未登入時播放 30 秒試聽。
  - KKBOX 播放器使用官方 widget。曲目 ID 來自 KKBOX 排行榜與好樂迪資料，再依歌名歌手套用到其他來源。
  - Spotify 播放器使用 `open.spotify.com/embed/track/{id}`，未登入時播放 30 秒試聽。曲目 ID 由 Spotify Web API 搜尋取得，見「Spotify 曲目」。
  - 播放器只在點擊時才載入，不會一次載入整張榜。瀏覽器可能擋下自動播放，這時要在播放器裡再按一次播放。
  - 找不到對應曲目時，Apple Music、KKBOX 與 Spotify 改成灰色虛線框的「搜尋」連結。
- **名次升降**：好樂迪、錢櫃與 KKBOX 使用官方提供的上期名次；日本兩家由本站比對前一期快照自行計算，第一次收錄時顯示「–」。
- **可直接分享**：網址 hash 記錄目前的 KTV 與榜單，例如 `#dam/anime-weekly`。
- **容錯**：某張榜抓取失敗時保留上一次的資料並在頁面標示，其他榜照常更新。
- **手機與深色模式**：版面支援窄螢幕，配色跟隨系統的深淺色設定。

## 運作方式

```
GitHub Actions（每天 03:17 UTC，台灣時間 11:17）
  ├─ 跑單元測試
  ├─ python -m scraper        抓五個來源的資料
  │    ├─ site/data/*.json    網頁讀取的最新資料
  │    └─ data/history/       每張榜每一期的快照
  ├─ python -m scraper.enrich 查詢新歌的曲風與 Apple Music 曲目，每次最多 300 首
  │    ├─ data/itunes.json    查詢結果快取，查不到的歌 30 天後重試
  │    └─ data/kkbox-ids.json 歌名歌手對應的 KKBOX 曲目 ID
  ├─ python -m scraper.spotify 用 Spotify Web API 查新歌的曲目 ID
  │    └─ data/spotify.json   Spotify 曲目 ID 永久快取
  ├─ python -m scraper.bpm    用 Beat This! 分析試聽音訊的 BPM，每次最多 300 首
  │    └─ data/bpm.json       BPM 永久快取
  ├─ python -m scraper.tags   用 Essentia 模型分析風格、情緒、樂器與人聲
  │    └─ data/essentia.json  模型分數永久快取
  ├─ 有變動才 commit 回 main
  └─ 部署 site/ 到 GitHub Pages
```

- 排行榜與曲風查詢只用 Python 標準函式庫；只有 BPM 與 hashtag 分析需要 ffmpeg、numpy 與 onnxruntime。
- 網頁是純 HTML、CSS、JavaScript，沒有框架也沒有建置步驟。
- 每個請求間隔 1 秒，每天只執行一次。iTunes 每分鐘約限 20 次請求，所以查詢間隔 3.2 秒，只查沒看過的歌。
- 曲風查詢失敗不會影響排行榜更新，只是當天少一些標籤。
- `data/itunes.json` 與 `data/kkbox-ids.json` 是永久快取，只增不減：已找到的歌不會再查，也不會被之後的查詢結果降級；快取檔讀不出來時程式會停止查詢，不會覆寫它。所有版本也都保留在 git 歷史裡。

各家端點、參數與頁面結構的細節見 [docs/KTV-chart-api.md](docs/KTV-chart-api.md)。

## 曲風標籤與試聽連結的來源

| 項目 | 來源 | 說明 |
|---|---|---|
| 曲風標籤 | iTunes Search API 回傳的 `primaryGenreName` | Apple 商店的分類，由唱片公司或發行商上架時填寫，不是分析音訊得來的。查詢時加 `lang=en_us` 取得英文名稱，網頁再翻成中文或日文 |
| Apple Music 試聽 | iTunes 比對到的 `trackId` | 嵌入 `https://embed.music.apple.com/{tw 或 jp}/song/{trackId}`，可試聽 30 秒 |
| KKBOX 試聽 | KKBOX 風雲榜的 `song_id`，以及好樂迪排行榜 `songurl` 裡的 KKBOX 曲目 ID | 嵌入 KKBOX 官方 widget。其他來源的同一首歌依歌名歌手套用 |
| Spotify 試聽 | Spotify Web API 搜尋到的曲目 ID | 嵌入 `https://open.spotify.com/embed/track/{id}`，比對規則與 iTunes 相同 |
| 在YouTube搜尋 | 歌名與歌手 | 開啟 YouTube 搜尋結果，不指定特定影片 |
| BPM | Beat This! 模型分析 iTunes 30 秒試聽 | 見下方「BPM 識別方式」 |
| Hashtag 標籤 | Essentia Discogs-EffNet 模型分析 iTunes 30 秒試聽 | 見下方「Hashtag 標籤」 |

**顏色**：每個曲風有固定的色相，三種語言下顏色一致。不在對照表裡的曲風顯示英文原名，顏色由名稱算出，每次都相同。

**灰色虛線按鈕**：代表沒有找到對應曲目，點下去是 Apple Music 或 KKBOX 的搜尋頁，不是試聽。

### 怎麼判斷有沒有找到

1. 把歌名去掉括號、副標與 feat. 段落，加上第一位歌手，向 iTunes 查詢。台灣來源先查台灣商店，日本來源先查日本商店，每次取 10 筆結果。
2. 每筆結果的歌名正規化後，相似度要至少 0.85。
3. 歌手和第一位歌手或完整歌手名稱比對，相似度要至少 0.6。
4. 排除 live、instrumental、karaoke、カラオケ、伴奏等版本，除非原本查的就是這種版本。
5. 多筆符合時，歌名和原始歌名完全相同的優先，再比歌名相似度、歌手相似度。所以「怪獣の花唄」會選原曲，不會選「怪獣の花唄 - replica -」。
6. 第一個商店沒有符合的結果，就換另一個商店再查一次。兩邊都沒有，就記為「查不到」。

KKBOX 曲目 ID 的跨來源對應：歌名歌手正規化後完全相同就套用；不同時，同一位歌手、其中一個歌名以另一個開頭、長度至少 3 個字、而且只對到一首，也會套用，例如「甲乙丙丁」對到「甲乙丙丁Strangers」。

這些都是相似度判斷，不是百分之百準確。同名同歌手的不同版本可能選錯，歌手在 iTunes 上的寫法差太多也可能查不到。前兩批在 GitHub 上查了 600 首，找到 559 首。

## Spotify 曲目

`scraper/spotify.py` 用 Spotify Web API 的搜尋查每首歌的曲目 ID，再用 `open.spotify.com/embed/track/{id}` 嵌入播放器。

- **授權方式**：client credentials，只需要 App 的 Client ID 與 Client Secret，不需要使用者登入。兩者存在 GitHub Secrets 的 `SPOTIFY_CLIENT_ID` 與 `SPOTIFY_CLIENT_SECRET`。
- **比對規則**：和 iTunes 相同（歌名相似度 ≥ 0.85、歌手 ≥ 0.6、排除 live 與伴奏等版本）。台灣來源先查 TW 市場，日本來源先查 JP，查不到再換另一邊。
- **快取**：結果存在 `data/spotify.json`，找到的永遠不再查，查不到的 30 天後重試。
- **Premium 的限制**：從 2026 年起，開發模式的 App 只在擁有者有 Spotify Premium 時才能呼叫 API。Premium 到期後查詢步驟會記錄警告並跳過，但嵌入播放器不需要 API，已查到 ID 的歌照常顯示「Spotify 試聽」，新歌則顯示灰色的「Spotify 搜尋」。重新訂閱後，下一次執行會自動補查這段期間的新歌。

設定 Secret（會提示輸入值，不會留在 shell 歷史裡）：

```bash
gh secret set SPOTIFY_CLIENT_ID --repo <你的帳號>/ktv-charts
```

```bash
gh secret set SPOTIFY_CLIENT_SECRET --repo <你的帳號>/ktv-charts
```

## BPM 識別方式

每首歌的 BPM 是用 Beat This! 節拍偵測模型分析 iTunes 的 30 秒試聽估算的。程式在 `scraper/bpm.py`，前後處理逐段移植自 [aaatmy/bpm-detector](https://huggingface.co/spaces/aaatmy/bpm-detector) Space 的 JavaScript，所以結果應與該 Space 一致。

### 模型

| 項目 | 內容 |
|---|---|
| 模型 | [aaatmy/beat-this-onnx](https://huggingface.co/aaatmy/beat-this-onnx) 的 `beat-this-final0.onnx`，約 82 MB |
| 來源 | [CPJKU/beat_this](https://github.com/CPJKU/beat_this) 的 final0 預訓練權重轉成 ONNX，不是重新訓練 |
| 版本 | 固定在 commit `e2c0d43`，下載後驗證 SHA-256 `e5e37b7d…c1b078` |
| 輸入 | log-mel 頻譜，形狀 `[1, 幀數, 128]` |
| 輸出 | `beat` 與 `downbeat`，每一幀是節拍與重拍的 logit，形狀 `[1, 幀數]` |
| 執行 | onnxruntime CPU，不需要 GPU |
| 授權 | MIT，版權屬 Institute of Computational Perception, JKU Linz |

### 流程

1. **選歌**：只分析已經對到 iTunes 曲目的歌，依各榜最佳名次由高到低處理。快取裡已有結果、而且對到的曲目沒變的歌會跳過。
2. **取得試聽**：用 iTunes lookup 一次查最多 100 個曲目 ID，取得 30 秒試聽的 `previewUrl`。請求間隔 3.2 秒，和曲風查詢共用 Apple 每分鐘約 20 次的額度。
3. **解碼**：用 ffmpeg 把 m4a 轉成 22,050 Hz 單聲道的 32 位元浮點數。整段幾乎無聲時不分析。
4. **頻譜**：
   - 用 1,024 點 FFT 計算頻譜，搭配週期性 Hann 視窗。
   - hop 是 441 個取樣點，換算成每秒 50 幀；30 秒約 1,501 幀。
   - 兩端以反射方式補值，振幅除以 √1,024。
   - 套上 `frontend.json` 的 128 個 Slaney mel 濾波器，最後取 `log1p(1000 × mel)`。
5. **推論**：
   - 每 1,500 幀切成一塊送進模型，相鄰兩塊重疊，每塊邊緣各 6 幀不採用。30 秒的試聽會切成兩塊。
   - 從最後一塊往前寫回，重疊處以較前面的一塊為準，和原始實作的 keep_first 一致。
6. **找節拍**：
   - logit 大於 0、而且是前後各 3 幀（共 7 幀）中最大值的位置，就當成一個峰值。
   - 相距不超過 1 幀的峰值合併成一個，取平均位置。
   - 幀號除以 50 得到秒數。重拍用同樣方式找，再對齊到最近的節拍。
7. **算速度**：
   - **拍號**：至少 3 個重拍，而且每兩個重拍之間的節拍數都相同，才判定拍號，例如 4 代表 4 拍一小節。
   - **constant**：至少 5 拍、拍號穩定、對節拍時間做線性迴歸後最大誤差不超過 30 毫秒，就用迴歸得到的拍長。
   - **variable**：至少 5 拍但最大誤差超過 30 毫秒，代表速度有變化，改用平均拍長。
   - **average**：不到 5 拍，或誤差在 30 毫秒內但拍號不穩定，也用平均拍長。
   - 平均拍長是「最後一拍減第一拍，再除以拍數減一」。BPM 等於 60 除以拍長（秒）。
   - 少於 2 拍時無法估算，記為「節拍太少」。
8. **存檔**：結果寫進 `data/bpm.json`，網頁顯示四捨五入後的整數 BPM。

### 快取欄位

| 欄位 | 說明 |
|---|---|
| `status` | `ok` 表示有 BPM；`none` 表示沒有，原因寫在 `reason` |
| `reason` | `no_preview` 沒有試聽，`few_beats` 節拍太少；兩種都會在 30 天後重試 |
| `bpm` | 主要 BPM，依上面的 constant、variable、average 規則算出 |
| `avg_bpm` | 整段偵測到的節拍的平均 BPM |
| `mode` | `constant`、`variable` 或 `average` |
| `signature` | 每小節的拍數，無法判定時是 `null` |
| `beats` | 偵測到的節拍數 |
| `track` | 分析用的 iTunes 曲目，格式 `地區/trackId`；曲目換了就會重算 |
| `model` | 使用的模型，目前是 `beat-this-final0` |
| `checked` | 分析日期 |

### 實測對照

| 歌曲 | 估算 BPM | 一般公開的速度 |
|---|---|---|
| APT. | 149 | 149 |
| First Love | 90 | 90 |
| My Heart Will Go On | 99 | 約 99 |
| Lemon | 91 | 87 |

### 限制

- **只看 30 秒**：試聽通常是副歌附近的片段，速度有變化的歌只代表那一段。
- **半速或倍速**：節拍偵測可能抓到實際速度的一半或兩倍，例如目前最高值 280 很可能是倍速。網頁上 BPM 的提示文字有說明這點。
- **對錯版本**：iTunes 對到 live、remix 等不同版本時，BPM 會是那個版本的速度。對到的曲目被更正後會自動重算。
- **和 Space 的差異**：Space 用瀏覽器重取樣，這裡用 ffmpeg，數值可能有極小差距。

在本機重算的方法見「本機開發」。

## Hashtag 標籤

BPM 下方的 `#抒情 #放鬆 #鋼琴 #女聲` 是用 MTG（Universitat Pompeu Fabra）的 [Essentia](https://essentia.upf.edu/models.html) Discogs-EffNet 模型分析 iTunes 30 秒試聽得來的，分成四組，各用一種顏色：

| 組別 | 來源模型 | 規則 |
|---|---|---|
| 風格 | `discogs-effnet-bsdynamic-1`（Discogs 400 種風格） | 分數至少 0.15，最多 2 個；第 2 個要有第 1 個的一半分數 |
| 情緒 | `mood_happy`、`mood_sad`、`mood_relaxed`、`mood_aggressive`、`mood_party`、`danceability` 二元分類，加上 `mtg_jamendo_moodtheme` | 二元分類至少 0.85，最多 2 個；再從 mood/theme 裡挑 1 個分數至少 0.2 的情緒類標籤 |
| 樂器 | `mtg_jamendo_instrument`（40 種） | 分數至少 0.35，最多 3 個；鼓和貝斯幾乎每首流行歌都有，要 0.6 以上才標 |
| 人聲 | `voice_instrumental`、`gender` | 有人聲機率 ≥ 0.6 且女聲 ≥ 0.9 或 ≤ 0.1 才標女聲或男聲；有人聲機率 ≤ 0.2 標純音樂 |

### 避免標籤氾濫的規則

門檻是用 300 首榜上歌曲的實際分數分佈訂的。以這些規則，平均每首約 3.6 個標籤，最多 8 個，有些歌一個都沒有。

- **不標國家或語言風格**：Discogs 的 400 類沒有華語流行，K-pop 常被套在華語和日語歌上（在 74 首排第一的歌裡只有 18 首真的是 K-Pop）。所以 K-pop、J-pop、歌謠曲、Schlager、Laïkó 這類以地區定義的風格一律不標，地區交給 iTunes 曲風標籤。
- **不重複上層分類**：已經有電吉他或木吉他時不標吉他，有鋼琴或合成器時不標鍵盤。人聲由人聲組負責，不出現在樂器組；節拍、電腦音色、取樣器、Pad 這類含糊的類別不標。
- **不標互相矛盾的情緒**：例如快樂與悲傷、放鬆與派對、放鬆與適合跳舞，只留分數較高的那個。
- **情境標籤不算情緒**：mood/theme 裡的 advertising、film、christmas、corporate 這類用途標籤不使用。
- **性別要很有把握**：門檻設在 0.9，合唱或聲線模糊的歌不標，避免把男歌手標成女聲。

### 流程與快取

1. 和 BPM 一樣，只分析有 iTunes 曲目的歌，iTunes 對到的曲目換了就重算。
2. ffmpeg 把試聽轉成 16 kHz，左右聲道平均成單聲道，用 soxr 重新取樣。這和 Essentia 官方的 MonoLoader 最接近，ffmpeg 預設的 `-ac 1` 會讓音量偏大約 3 dB、分數明顯偏掉。
3. numpy 算 96 頻帶 log-mel，參數和 Essentia 的 `TensorflowInputMusiCNN` 相同（512 點對稱 Hann 窗、hop 256、Slaney mel、`log10(1 + 10000·x)`），已和 Essentia 本身比對過。
4. 每 2 秒一段送進 EffNet，所有分類頭共用同一份 embedding，結果對各段取平均。
5. `data/essentia.json` 永久快取每首歌的分數（風格前 20、樂器前 15、mood/theme 前 15，以及 10 個二元分類），**不是**最後的 hashtag。門檻與 Top-K 寫在 `scraper/hashtags.py`，寫入網站資料時才套用，所以之後要調整，不必重新分析音訊。

模型檔從 essentia.upf.edu 下載並用 SHA-256 鎖定，存在 Actions 快取裡，每首歌分析加下載約 1 秒。也可以在 [aaatmy/essentia-music-tagger](https://huggingface.co/spaces/aaatmy/essentia-music-tagger) 用瀏覽器試同一組模型。

### 限制

- **只聽 30 秒**：試聽片段通常是副歌附近，不代表整首歌。
- **以西方音樂訓練**：二胡、古箏這類樂器沒有對應類別，華語、日語歌的風格常被歸到最接近的西方風格，例如華語抒情歌多半標成「抒情」。
- **模型判斷不是事實**：這些是機率最高的猜測，可能出錯，網頁的提示文字也標明是模型分析。

## 分批查詢機制

iTunes 每分鐘約只接受 20 次請求，第一次要查的歌有約 1,400 首，所以查詢分成多次 Action 執行完成。

| 規則 | 設定 |
|---|---|
| 每次執行的上限 | 最多 300 首或 25 分鐘，先到先停 |
| 查詢順序 | 依每首歌在所有榜單中的最佳名次，排名高的先查 |
| 存檔頻率 | 每查 10 首存一次快取；查詢步驟結束後一定會提交 |
| 剩下的歌 | 留給下一次執行，從還沒查的歌繼續 |
| 被 iTunes 限流 | 收到 403 時當次停止，已查到的結果保留 |
| 查不到的歌 | 30 天後重試；已找到的歌永遠不再查 |
| 失敗時 | 查詢步驟設成失敗也繼續，排行榜照常發布，只是少一些標籤 |
| BPM 分析 | 同樣的規則：每次最多 300 首或 20 分鐘，排名高的先做，每 10 首存一次 |
| Hashtag 分析 | 每首約 1 秒，所以每次最多 1,500 首或 20 分鐘，每 25 首存一次 |

**什麼時候會執行**：每天排程一次；推送 `site/`、`scraper/`、`tests/` 或工作流程檔的變更時；以及在 Actions 頁面按 **Run workflow** 手動執行。目前不會自己再開一次 Action 接續，所以首次補齊約需 5 次執行。之後每天新進榜的歌約 10 到 30 首，一次就能查完。想加快補齊，可以手動多執行幾次；同一時間只會跑一個，其他會排隊。

```bash
gh workflow run update.yml
```

**時間限制**：曲風查詢最多 25 分鐘，Spotify 查詢最多 15 分鐘，BPM 與 hashtag 分析各最多 20 分鐘，每個步驟另有自己的逾時上限。整個 job 上限 105 分鐘，遠低於 GitHub 單一 job 的 6 小時，所以不會因為歌曲太多而逾時。

## 專案結構

```
scraper/               Python 抓取程式
  sources/             每個來源一個模組：holiday、cashbox、joysound、dam、kkbox
  history.py           歷史快照與升降計算
  match.py             歌名歌手正規化與相似度
  enrich.py            曲風、Apple Music 與 KKBOX 連結
  spotify.py           Spotify 曲目 ID 查詢
  bpm.py               Beat This! BPM 分析，需要 ffmpeg、numpy、onnxruntime
  tags.py              Essentia 模型分析，需要 ffmpeg、numpy、onnxruntime
  hashtags.py          模型分數轉成 hashtag 的門檻與規則（只用標準函式庫）
  net.py               HTTP 請求、重試與請求間隔
  __main__.py          進入點，寫出 site/data/*.json
site/                  靜態網頁，原樣發布到 GitHub Pages
  index.html
  app.js               渲染與三語字典
  style.css
  data/                抓取結果
data/history/          歷史快照
data/itunes.json       iTunes 查詢快取
data/kkbox-ids.json    KKBOX 曲目 ID
data/spotify.json      Spotify 曲目 ID
data/bpm.json          BPM 快取
data/essentia.json     Essentia 模型分數快取
requirements-bpm.txt   BPM 與 hashtag 分析需要的套件
tests/                 離線單元測試
docs/                  API 手冊
.github/workflows/     每日排程與部署
```

## 本機開發

需要 Python 3.10 以上。

抓取全部資料：

```bash
python3 -m scraper
```

只抓某幾家，可用的 id 有 `holiday`、`cashbox`、`joysound`、`dam`、`kkbox`：

```bash
python3 -m scraper holiday dam
```

執行測試：

```bash
python3 -m unittest discover -s tests -t .
```

查詢曲風與連結；`--no-network` 只用快取重新標註：

```bash
python3 -m scraper.enrich --max 300
```

分析 BPM。需要先安裝 ffmpeg，第一次執行會從 Hugging Face 下載約 82 MB 的模型到 `.cache/beat-this/`：

```bash
python3 -m pip install -r requirements-bpm.txt
```

```bash
python3 -m scraper.bpm --max 50
```

分析 hashtag。第一次執行會從 essentia.upf.edu 下載約 31 MB 的模型到 `.cache/essentia/`：

```bash
python3 -m scraper.tags --max 50
```

只改了 `scraper/hashtags.py` 的門檻時，用快取重新標註就好：

```bash
python3 -m scraper.enrich --no-network
```

預覽網頁，然後打開 <http://localhost:8000/>：

```bash
python3 -m http.server 8000 -d site
```

## 部署到自己的帳號

1. Fork 或複製這個 repository，預設分支用 `main`。
2. 到 Settings → Pages，把 Source 設成 **GitHub Actions**。
3. 到 Actions 分頁手動執行一次 **Update rankings**。
4. 之後每天自動更新。GitHub 的排程可能延遲數十分鐘。

如果 Settings → Actions → General 的 Workflow permissions 被設成唯讀，請改成 Read and write，否則工作流程無法提交資料。

## 新增一個來源

1. 在 `scraper/sources/` 新增模組，定義 `SOURCE` 與 `JOBS`。格式見 `scraper/sources/__init__.py` 的說明。
2. 把模組加進同一檔案的 `ALL` 清單。
3. 站名與榜單名稱都用 `{"zh": ..., "en": ..., "ja": ...}` 提供三種語言。
4. 在 `tests/` 補上用小段合成 HTML 或 JSON 的解析測試。

## 免責聲明

- 本專案與好樂迪、錢櫃、JOYSOUND（株式会社エクシング）、DAM（株式会社第一興商）、KKBOX、Spotify 沒有任何關係。
- 排行榜資料取自各家官方網站的公開頁面與網站內部介面，著作權與相關權利屬原網站所有。這些介面沒有官方文件，網站改版時可能失效。
- 曲風與 Apple Music 連結來自 Apple 的 iTunes Search API，曲風是 Apple 商店的分類，不是分析音訊得來的，也可能對到不同版本。
- BPM 與 hashtag 是模型分析 30 秒試聽的估計，可能出錯。
- 如果你要自行部署或轉載資料，請先確認各網站的使用條款，並保留來源標示與連回官網的連結。

## 授權

程式碼以 [MIT License](LICENSE) 授權。BPM 使用的 Beat This! 模型權重同樣是 MIT 授權，版權屬 Institute of Computational Perception, JKU Linz。Hashtag 使用的 Essentia 模型由 Music Technology Group（Universitat Pompeu Fabra）以 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 授權，僅限非商業使用；本專案不散布模型檔，執行時才從官方網站下載（論文：Alonso-Jiménez, Serra & Bogdanov, ISMIR 2022）。按鈕上的 Apple Music 與 Spotify 圖示取自 [Simple Icons](https://simpleicons.org/)（CC0），KKBOX 圖示取自 KKBOX 官網的 App 圖示，商標皆屬各自的所有者，僅用來標示連往該服務的連結。MIT 授權只涵蓋本專案的程式碼與文件，不涵蓋 `site/data/` 與 `data/history/` 中取自第三方網站的排行榜資料。
