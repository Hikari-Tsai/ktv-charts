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
- **副歌音域與男女生建議**：歌手下方顯示副歌的最低音到最高音（例如 `D3–D4`）、一條迷你音域條與「適合男生／適合女生／男女皆宜」，點一下展開鋼琴鍵盤圖、移調試算，以及男女生各自是否舒適、偏高或偏低與建議升降幾個 Key。先用 UVR MDX-Net 分離人聲，再用 openvpi 的 [GAME](https://github.com/openvpi/GAME) 模型轉成音符，並用演算法過濾鬼點，見「音域」。網頁底部附男女生音域範圍說明。
- **Hashtag 標籤**：接在歌名與曲風後面，用同樣的圓角標籤，依風格、情緒、樂器、人聲分組以不同顏色標出 `#抒情 #放鬆 #鋼琴 #女聲` 這類標籤，用 Essentia 的 Discogs-EffNet 模型分析試聽得來，每組都有門檻與數量上限。
- **出版資訊**：歌手下方顯示發行年份、發行公司、作詞與作曲，點一下展開編曲、製作人、混音、錄音、母帶後製、專輯、發行日期、ISRC、版權標示、歌詞連結與資料來源。台灣的歌查國家圖書館 ISRC 資料，其他歌查 MusicBrainz，年份與版權標示另外取自 Apple，見「出版資訊」。
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
  ├─ python -m scraper.credits 查出版資訊：Apple 專輯、國家圖書館 ISRC、MusicBrainz
  │    ├─ data/apple-albums.json 專輯、發行日期與 ℗/© 版權標示
  │    ├─ data/ncl-isrc.json  國家圖書館 ISRC 紀錄（詞曲、編曲、製作人、發行公司）
  │    └─ data/musicbrainz.json MusicBrainz 詞曲與製作人
  ├─ python -m scraper.bpm    用 Beat This! 分析試聽音訊的 BPM，每次最多 300 首
  │    └─ data/bpm.json       BPM 永久快取
  ├─ python -m scraper.tags   用 Essentia 模型分析風格、情緒、樂器與人聲
  │    └─ data/essentia.json  模型分數永久快取
  ├─ python -m scraper.vocal  分離人聲後用 GAME 轉成音符，過濾鬼點，取最低音與最高音
  │    └─ data/vocal-range.json 音域永久快取
  ├─ 有變動才 commit 回 main
  └─ 部署 site/ 到 GitHub Pages
```

- 排行榜與曲風查詢只用 Python 標準函式庫；只有 BPM、hashtag 與音域分析需要 ffmpeg、numpy 與 onnxruntime。
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
- **速度**：開發模式的配額沒有公開。一次送出約 700 個搜尋後，Spotify 回了 24 小時的 `Retry-After`，所以每次執行最多查 150 首、間隔 1.5 秒。收到長時間的限流時，截止時間會寫進 `data/spotify-pause.json`，在那之前的執行直接跳過查詢。
- **Premium 的限制**：從 2026 年起，開發模式的 App 只在擁有者有 Spotify Premium 時才能呼叫 API。Premium 到期後查詢步驟會記錄警告並跳過，但嵌入播放器不需要 API，已查到 ID 的歌照常顯示「Spotify 試聽」，新歌則顯示灰色的「Spotify 搜尋」。重新訂閱後，下一次執行會自動補查這段期間的新歌。

設定 Secret（會提示輸入值，不會留在 shell 歷史裡）：

```bash
gh secret set SPOTIFY_CLIENT_ID --repo <你的帳號>/ktv-charts
```

```bash
gh secret set SPOTIFY_CLIENT_SECRET --repo <你的帳號>/ktv-charts
```

## 出版資訊

歌手下方的一行是重要的出版資訊，例如 `2015 · 華研國際音樂 · 詞 徐世珍、吳輝福 · 曲 JerryC`。作詞與作曲是同一人時合併成「詞曲」。點這一行會展開其他資訊：編曲、製作人、混音、錄音、母帶後製、專輯、發行日期、製作公司、類別、ISRC、℗/© 版權標示、歌詞連結，以及連回原始紀錄的資料來源。

**歌詞**：歌詞受著作權保護，本站不抓取也不收錄歌詞，只連到授權的歌詞頁。有 KKBOX 曲目 ID 的歌連到 KKBOX 歌曲頁（含歌詞），沒有的連到 KKBOX 搜尋；日本來源或歌名有假名的歌，另外附歌ネット（Uta-Net）的曲名搜尋。

程式在 `scraper/credits.py`（查詢）與 `scraper/info.py`（合併），每個來源有自己的永久快取，以歌名歌手的 song key 為鍵。

| 來源 | 查哪些歌 | 取得的欄位 | 方式與速度 |
|---|---|---|---|
| Apple（iTunes Lookup API） | 所有對到 iTunes 曲目的歌 | 專輯、發行日期、℗/© 版權標示（從中取出發行公司） | 一次查 100 首，間隔 3.2 秒 |
| [國家圖書館 ISRC 查詢系統](https://isrc-web.ncl.edu.tw/C200/C200) | 台灣來源中，歌名或歌手含中日文的歌 | 表演者、作詞、作曲、編曲、製作人、錄音員、發行公司、製作公司、發行日期、ISRC、出版類別 | 以「曲名 AND 表演者」查詢，查不到再只用曲名查，請求間隔 1.5 秒 |
| [MusicBrainz](https://musicbrainz.org/) | 國家圖書館沒有詞曲資料的歌 | 作詞、作曲、編曲、製作人、混音、錄音、母帶後製、首次發行日期、ISRC | 搜尋錄音再查作品關聯，每秒 1 次 |

**國家圖書館 ISRC**：國家圖書館是台灣的 ISRC 管理中心，在台灣發行的唱片公司申請 ISRC 時會登記每首錄音的表演者與詞曲等資料，所以這是台灣歌最完整的來源。同一批紀錄也以 [政府資料開放平臺 36940 號資料集](https://data.gov.tw/dataset/36940) 公開（政府資料開放授權條款第 1 版），但只有最近幾個半年度的 CSV；查詢系統則涵蓋 2003 年以後的紀錄，所以改用查詢系統。

**怎麼選出正確的紀錄**：

- 曲名相似度 ≥ 0.85、表演者相似度 ≥ 0.6，規則和 iTunes 相同。
- 排除伴奏、kala、導唱、純音樂、演奏版、demo 等錄音，除非榜單歌名本身就是這種版本。
- 同一首歌有多筆紀錄（單曲、專輯、精選輯）時，取發行日期最早的一筆當原始發行。詞曲取同一個 ISRC 中資料最完整的一筆。
- MusicBrainz 的第一個符合錄音常常還沒連到作品，所以最多試 3 個符合的錄音，直到找到詞曲為止。

**合併規則**（`scraper/info.py`）：

- 詞曲、編曲、製作人、混音、錄音、母帶後製：每個角色都是國家圖書館優先，沒有的才用 MusicBrainz。國家圖書館沒有混音欄位，所以混音只會來自 MusicBrainz。MusicBrainz 的 writer 同時當作作詞與作曲。
- 發行年份：取三個來源中最早的日期，因為數位重新發行與精選輯的日期比原始發行晚。
- 發行公司：國家圖書館登記的發行公司優先，否則取 Apple ℗/© 標示中的公司名稱（去掉年份與 under license to 之後的文字）。

**解析規則改版**：`NCL_VERSION` 或 `MB_VERSION` 加一時，舊版本的紀錄（包括已找到的）會重查一次；重查沒找到時保留原本的結果。

**分批與重試**：每次執行國家圖書館最多 200 首、MusicBrainz 最多 300 首，整步最多 20 分鐘，排名高的先查。查不到的歌 60 天後重試，已找到的永遠不再查。連續 5 次連線失敗就停止當次查詢，排行榜照常發布。

**限制**：

- 國家圖書館只有在台灣申請 ISRC 的錄音。中國、香港與國外唱片公司發行的歌通常查不到，有些紀錄是簡體字。
- MusicBrainz 是社群編輯的資料庫，日本與歐美歌曲的詞曲比較齊全，華語歌很少。
- Apple 的發行日期可能是數位上架或重新發行的日期，所以只在其他來源沒有更早日期時採用。
- 都是依歌名與歌手自動比對，翻唱或同名歌曲可能對到別的錄音。例如翻唱歌曲會顯示原曲的詞曲作者，這通常是正確的，但發行公司可能是原唱的版本。

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

## 音域

歌手下方的「副歌音域 D3–D4 · 適合男生」是分析 iTunes 30 秒試聽的歌聲得來的。iTunes 試聽多半截自副歌附近，所以網頁標成「副歌音域」，不是整首歌的音域。最低音與最高音和建議放在外面，點一下展開鍵盤圖、跨度與男女生各自的建議。

**視覺化**（`site/app.js` 的 `rangeBar`、`rangeKeys`）：

- **迷你音域條**：音名旁邊的小橫條，所有歌共用 G2–A5 同一把尺，往下捲就能比出哪首比較高。淡藍是男生舒適區，淡粉是女生舒適區，黑色短條是這首副歌。
- **鋼琴鍵盤圖**：展開後是 E2–E6 的鋼琴鍵盤，黑鍵較短、較窄，副歌用到的音會亮起。上方兩條是男生與女生的舒適區，接著的褐色段是「偏高」。
- **移調試算**：拖動滑桿可以升降 ±7 Key，亮起的鍵、音域與男女生判斷會即時更新；超出時會提示「低八度唱就舒適」或「高八度唱就舒適」。預設停在原調，旁邊的「男生建議」「女生建議」按鈕直接跳到建議的 Key。判斷規則與 `scraper/singrange.py` 相同，前端的 `VOICE_ZONES` 由測試確認和 Python 端一致。
- 鍵盤只在第一次展開時才產生，一頁上百首歌也不會多出大量元素。程式在 `scraper/vocal.py`（模型與音訊）和 `scraper/singrange.py`（過濾與建議，只用標準函式庫）。

### 模型

| 用途 | 模型 | 來源 | 授權 |
|---|---|---|---|
| 人聲分離 | UVR MDX-Net `Kim_Vocal_2.onnx` | [aaatmy/uvr-mdx-net-onnx](https://huggingface.co/aaatmy/uvr-mdx-net-onnx)（UVR 官方檔案的原樣鏡像） | 作者 KimberleyJensen 公開同意任意使用，詳見鏡像的 NOTICE |
| 歌聲轉音符 | GAME Small v1.0.3（openvpi，Generative Adaptive MIDI Extractor） | [aaatmy/game-small-onnx](https://huggingface.co/aaatmy/game-small-onnx)（官方 ONNX 的原樣鏡像） | CC BY-NC-SA 4.0，僅限非商業使用 |

兩個模型都鎖定 Hugging Face 的 commit，下載後用 SHA-256 檢查，存在 Actions 快取 `.cache/vocal/`，約 118 MB。

### 流程

1. **選歌**：和 BPM 一樣，只分析有 iTunes 曲目的歌，排名高的先做；iTunes 對到的曲目換了就重算。
2. **解碼**：ffmpeg 把試聽轉成 44,100 Hz 雙聲道。
3. **分離人聲**：MDX-Net 以 n_fft 7680、hop 1024 做 STFT，取前 3,072 個頻率、每段 256 格，預測人聲頻譜再轉回波形。前奏的貝斯、鋼琴與吉他因此不會被當成音符。實測直接把混音交給 GAME 時，越南歌與演歌的前奏被轉成 C2–B2 之類不合理的音域；先分離後，這些歌因為唱的音不夠而不給結果。
4. **轉成音符**：GAME 每 8 秒一段、前後各多看 1 秒，依官方流程跑 encoder、segmenter（8 步 D3PM，t = i/8）、estimator，語言設為通用，邊界與有聲門檻 0.2。輸出每個音的起點、長度與浮點 MIDI 音高。
5. **過濾鬼點**（`filter_notes()`），依序：

   | 規則 | 設定 | 處理的問題 |
   |---|---|---|
   | 太短的音 | 短於 0.1 秒 | 子音、換氣、切段雜訊 |
   | 不可能的音 | C2（MIDI 36）以下或 C7（96）以上 | 明顯的錯誤 |
   | 尖峰 | 短於 0.3 秒，且和前後相鄰（1 秒內）的音都差 7 個半音以上 | 八度誤判、瞬間的樂器殘留 |
   | 脫離主體 | 從時長加權的中位音高往上下延伸，遇到相差 5 個半音以上、中間沒有音的空隙就停，空隙外的音全部丟掉 | 殘留的前奏低音、和聲或效果音 |
   | 極值要有支撐 | 最低音與最高音必須合計唱滿 0.25 秒，或出現 2 次以上，不然往內退一個 | 只閃過一下的音 |
   | 唱得太少 | 過濾後不到 12 個音或不到 4 秒 | 純音樂、前奏很長的試聽，不給結果 |

6. **存檔**：最低音、最高音（MIDI 整數）、音名、保留的音數、丟掉的音數與總長寫進 `data/vocal-range.json`。

### 男女生建議

建議在寫入網站資料時才由 `advise()` 計算，所以調整門檻不必重新分析音訊。舒適範圍以沒受過訓練的一般人在 KTV 用真聲唱為準：

| | 舒適 | 偏高 | 很高 |
|---|---|---|---|
| 男生 | A2–F#4（MIDI 45–66） | 最高音 G4–A4 | 最高音 A#4 以上 |
| 女生 | F3–C5（MIDI 53–72） | 最高音 C#5–E5 | 最高音 F5 以上 |

- 最低音低於舒適範圍是「偏低」，高低都超出是「音域很寬」。
- 原調剛好在某一方的舒適範圍內，就標「適合男生」或「適合女生」，兩邊都在範圍內標「男女皆宜」。只適合一方時，後面附上另一方的判斷，例如「適合女生 · 男生偏高」；兩邊都不舒適時，直接列出兩邊的判斷，例如「男生很高 · 女生偏低」。男生上限參考日本卡拉 OK 常用的男性平均音域（約到 mid2G，也就是 G4）。
- 不舒適的一方會給建議：在 ±7 個 Key 之內，找能讓整段音域落在舒適範圍的最小升降，也考慮男生低八度、女生高八度唱。例如〈晴天〉D3–D4 對女生偏低，建議「高八度唱，降 2 Key」。找不到時顯示「升降 Key 也不容易唱得舒服」。
- 網頁底部的「關於音域與男女生建議」列出上面的範圍、男低音到女高音的參考音域，以及音名的讀法（C4 是中央 C，1 Key 是 1 個半音）。

### 快取欄位

| 欄位 | 說明 |
|---|---|
| `status` | `ok` 表示有音域；`none` 表示沒有，原因寫在 `reason`（`no_preview` 或 `few_notes`） |
| `low`、`high` | 過濾後的最低音與最高音，MIDI 整數（60 = C4） |
| `low_name`、`high_name` | 音名，例如 `D3` |
| `notes`、`dropped` | 保留與丟掉的音數 |
| `voiced` | 保留的音合計秒數 |
| `track`、`model`、`v`、`checked` | 分析的 iTunes 曲目、模型、流程版本與日期；`v` 比程式的 `VERSION` 舊就重算 |

### 限制

- **只聽 30 秒**：試聽通常在副歌附近，主歌更低或結尾更高的音可能沒聽到，網頁的提示文字也有說明。
- **和聲與合唱**：分離出來的人聲包含和聲與合唱，男女對唱會把兩個人的音域算在一起。
- **饒舌、假音、重效果器**：GAME 以一般歌聲訓練，這些情況比較容易出錯。
- **隨機性**：GAME 的 D3PM 取樣理論上有隨機成分。實測〈晴天〉、〈Lemon〉、〈アイドル〉各重跑 4 次，過濾後的音域完全相同，但其他歌仍可能差一個半音。
- **舒適範圍因人而異**：上面的範圍是一般參考，不是每個人都適用。

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
| 音域分析 | 人聲分離加 GAME 每首約 20 到 40 秒，所以每次最多 80 首或 25 分鐘，排名高的先做，每 10 首存一次 |
| 出版資訊 | 國家圖書館每首 2 到 6 秒、MusicBrainz 每首 2 到 7 秒，每次最多 20 分鐘，每 25 首存一次 |

**什麼時候會執行**：每天排程一次；推送 `site/`、`scraper/`、`tests/` 或工作流程檔的變更時；以及在 Actions 頁面按 **Run workflow** 手動執行。目前不會自己再開一次 Action 接續，所以首次補齊約需 5 次執行。之後每天新進榜的歌約 10 到 30 首，一次就能查完。想加快補齊，可以手動多執行幾次；同一時間只會跑一個，其他會排隊。

```bash
gh workflow run update.yml
```

**時間限制**：曲風查詢最多 25 分鐘，Spotify 查詢最多 10 分鐘，出版資訊最多 20 分鐘，BPM 與 hashtag 分析各最多 20 分鐘，音域分析最多 25 分鐘，每個步驟另有自己的逾時上限。整個 job 上限 165 分鐘，遠低於 GitHub 單一 job 的 6 小時，所以不會因為歌曲太多而逾時。

## 專案結構

```
scraper/               Python 抓取程式
  sources/             每個來源一個模組：holiday、cashbox、joysound、dam、kkbox
  history.py           歷史快照與升降計算
  match.py             歌名歌手正規化與相似度
  enrich.py            曲風、Apple Music 與 KKBOX 連結
  spotify.py           Spotify 曲目 ID 查詢
  credits.py           出版資訊查詢：Apple 專輯、國家圖書館 ISRC、MusicBrainz
  info.py              合併三個來源成網頁的 info 欄位（只用標準函式庫）
  bpm.py               Beat This! BPM 分析，需要 ffmpeg、numpy、onnxruntime
  tags.py              Essentia 模型分析，需要 ffmpeg、numpy、onnxruntime
  hashtags.py          模型分數轉成 hashtag 的門檻與規則（只用標準函式庫）
  vocal.py             人聲分離與 GAME 音域分析，需要 ffmpeg、numpy、onnxruntime
  singrange.py         鬼點過濾與男女生建議（只用標準函式庫）
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
data/apple-albums.json Apple 專輯、發行日期與版權標示
data/ncl-isrc.json     國家圖書館 ISRC 紀錄
data/musicbrainz.json  MusicBrainz 詞曲資料
data/bpm.json          BPM 快取
data/essentia.json     Essentia 模型分數快取
data/vocal-range.json  音域快取
requirements-bpm.txt   BPM、hashtag 與音域分析需要的套件
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

分析音域。第一次執行會從 Hugging Face 下載約 118 MB 的模型到 `.cache/vocal/`：

```bash
python3 -m scraper.vocal --max 20
```

只改了 `scraper/hashtags.py` 或 `scraper/singrange.py` 裡建議的門檻時，用快取重新標註就好：

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
- BPM、hashtag 與音域是模型分析 30 秒試聽的估計，可能出錯；男女生建議只是一般參考。
- 出版資訊依歌名與歌手自動比對國家圖書館 ISRC、MusicBrainz 與 Apple 的資料，可能對到翻唱或同名的錄音。
- 網頁底部也有免責聲明：曲風、BPM、音域與男女生建議、# 標籤與出版資訊由人工智慧模型與自動比對產生，人工智慧有其極限，可能有錯誤或遺漏，僅供參考。
- 如果你要自行部署或轉載資料，請先確認各網站的使用條款，並保留來源標示與連回官網的連結。

## 授權

程式碼以 [MIT License](LICENSE) 授權。BPM 使用的 Beat This! 模型權重同樣是 MIT 授權，版權屬 Institute of Computational Perception, JKU Linz。Hashtag 使用的 Essentia 模型由 Music Technology Group（Universitat Pompeu Fabra）以 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 授權，僅限非商業使用；本專案不散布模型檔，執行時才從官方網站下載（論文：Alonso-Jiménez, Serra & Bogdanov, ISMIR 2022）。音域使用的 GAME 模型由 [openvpi](https://github.com/openvpi/GAME) 以 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 授權，僅限非商業使用；人聲分離使用 [Ultimate Vocal Remover](https://github.com/Anjok07/ultimatevocalremovergui) 收錄、KimberleyJensen 訓練的 MDX-Net Kim_Vocal_2 模型，架構來自 kuielab 的 MDX-Net。兩者都從 [aaatmy](https://huggingface.co/aaatmy) 的原樣鏡像下載，本專案不散布模型檔。按鈕上的 Apple Music 與 Spotify 圖示取自 [Simple Icons](https://simpleicons.org/)（CC0），KKBOX 圖示取自 KKBOX 官網的 App 圖示，商標皆屬各自的所有者，僅用來標示連往該服務的連結。出版資訊來自國家圖書館 ISRC 資料（[政府資料開放授權條款第 1 版](https://data.gov.tw/license)）、MusicBrainz（核心資料為 [CC0](https://creativecommons.org/publicdomain/zero/1.0/)）與 Apple 的 iTunes API。MIT 授權只涵蓋本專案的程式碼與文件，不涵蓋 `site/data/` 與 `data/history/` 中取自第三方網站的排行榜資料。
