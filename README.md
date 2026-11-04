# KTV 點歌排行榜

好樂迪、錢櫃、JOYSOUND、DAM 四家 KTV 的點歌排行榜，每天由 GitHub Actions 自動抓取，發布成 GitHub Pages 靜態網頁。網頁支援中文、英文、日文即時切換，預設中文；每首歌都附「在YouTube搜尋」連結。

## 結構

```
scraper/            Python 抓取程式，只用標準函式庫
  sources/          四家各一個模組
  history.py        歷史快照，用來替日本兩家計算升降
  net.py            HTTP 請求、重試與請求間隔
site/               靜態網頁，直接發布到 GitHub Pages
  data/             抓取結果，每家一個 JSON，外加 index.json
data/history/       每張榜每一期的快照
tests/              離線單元測試
docs/               各家排行榜介面的 API 手冊
.github/workflows/  每日排程
```

## 本機執行

需要 Python 3.10 以上，不需要安裝任何套件。

```bash
python3 -m scraper
```

只抓某幾家：

```bash
python3 -m scraper holiday dam
```

跑測試：

```bash
python3 -m unittest discover -s tests -t .
```

預覽網頁：

```bash
python3 -m http.server 8000 -d site
```

然後打開 http://localhost:8000/ 。

## 部署到 GitHub Pages

1. 在 GitHub 建立新的 repository，把這個資料夾推上去，預設分支用 `main`。
2. 到 repository 的 Settings → Pages，把 Source 設成 **GitHub Actions**。
3. 到 Actions 分頁，手動執行一次 **Update rankings**，確認四家都抓得到。
4. 之後每天台灣時間 11:17 左右自動更新。GitHub 的排程常延遲數十分鐘。

如果 Settings → Actions → General 的 Workflow permissions 被組織設成唯讀，要改成 Read and write，否則工作流程無法提交資料。

## 資料與行為

| KTV | 榜單 | 升降來源 |
|---|---|---|
| 好樂迪 | 國、台、粵、英、日、韓、越語點播，國台語新歌；每榜 30 名 | 官方提供上週名次 |
| 錢櫃 | 國、台、粵、日、英語點播，國台語新歌；每榜 30 名 | 官方提供上週名次 |
| JOYSOUND | 綜合日／週／月榜，動畫、VOCALOID、演歌、西洋週榜；每榜 100 名 | 本站比對前一期快照 |
| DAM | 綜合日／週／月榜，急上昇、動畫、VOCALOID、VTuber、演歌、外國曲、對唱週榜；每榜 100 名 | 本站比對前一期快照 |

- 日本兩家第一次收錄時沒有前期資料，升降欄顯示「–」，第二期開始才有數字。
- 某一家或某一張榜抓取失敗時，保留上一次的資料並在網頁上標示，其他榜照常更新。全部失敗時工作流程才會變紅。
- DAM 頁面只標更新日，集計期間依官方 FAQ 的規則推算。
- YouTube 連結是 `https://www.youtube.com/results?search_query=` 加上「歌名 歌手」。

## 注意

- 各家端點、參數與頁面結構的細節見 [docs/KTV-chart-api.md](docs/KTV-chart-api.md)。

- 這些資料來自各家官網的內部介面與公開頁面，沒有官方 API 文件，網站改版就可能失效。
- 公開發布前請確認各網站的使用條款。網頁上已標明來源並連回官網。
- 抓取程式每個請求間隔 1 秒，每天只跑一次，請勿調高頻率。
