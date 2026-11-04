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
- **三個連結**：每首歌附「在YouTube搜尋」、「Apple Music 試聽」、「KKBOX 試聽」。
  - YouTube 以「歌名 歌手」當關鍵字開啟 `https://www.youtube.com/results?search_query=`。
  - Apple Music 連到 iTunes 比對到的曲目頁，可以試聽 30 秒。
  - KKBOX 開啟官方試聽 widget。曲目 ID 來自 KKBOX 排行榜與好樂迪資料，再依歌名歌手套用到其他來源。
  - 找不到對應曲目時，Apple Music 與 KKBOX 改成虛線框的「搜尋」連結。
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
  ├─ 有變動才 commit 回 main
  └─ 部署 site/ 到 GitHub Pages
```

- 抓取程式只用 Python 標準函式庫，不需要安裝任何套件。
- 網頁是純 HTML、CSS、JavaScript，沒有框架也沒有建置步驟。
- 每個請求間隔 1 秒，每天只執行一次。iTunes 每分鐘約限 20 次請求，所以查詢間隔 3.2 秒，只查沒看過的歌。
- 曲風查詢失敗不會影響排行榜更新，只是當天少一些標籤。
- `data/itunes.json` 與 `data/kkbox-ids.json` 是永久快取，只增不減：已找到的歌不會再查，也不會被之後的查詢結果降級；快取檔讀不出來時程式會停止查詢，不會覆寫它。所有版本也都保留在 git 歷史裡。

各家端點、參數與頁面結構的細節見 [docs/KTV-chart-api.md](docs/KTV-chart-api.md)。

## 專案結構

```
scraper/               Python 抓取程式
  sources/             每個來源一個模組：holiday、cashbox、joysound、dam、kkbox
  history.py           歷史快照與升降計算
  match.py             歌名歌手正規化與相似度
  enrich.py            曲風、Apple Music 與 KKBOX 連結
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

- 本專案與好樂迪、錢櫃、JOYSOUND（株式会社エクシング）、DAM（株式会社第一興商）、KKBOX 沒有任何關係。
- 排行榜資料取自各家官方網站的公開頁面與網站內部介面，著作權與相關權利屬原網站所有。這些介面沒有官方文件，網站改版時可能失效。
- 曲風與 Apple Music 連結來自 Apple 的 iTunes Search API，曲風是 Apple 商店的分類，不是分析音訊得來的，也可能對到不同版本。
- 如果你要自行部署或轉載資料，請先確認各網站的使用條款，並保留來源標示與連回官網的連結。

## 授權

程式碼以 [MIT License](LICENSE) 授權。MIT 授權只涵蓋本專案的程式碼與文件，不涵蓋 `site/data/` 與 `data/history/` 中取自第三方網站的排行榜資料。
