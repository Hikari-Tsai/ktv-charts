# 台灣與日本 KTV 點歌排行榜、KKBOX 風雲榜與 iTunes 曲風 API 手冊

整理日期：2026-11-03
涵蓋：台灣 好樂迪（holiday.com.tw）、錢櫃（cashboxparty.com）、星聚點（newcbparty.com，附錄）；日本 JOYSOUND（joysound.com）、DAM（clubdam.com）；串流 KKBOX 風雲榜（kma.kkbox.com）

> **注意**
> 這些端點是各家官網前端 JavaScript 使用的內部 AJAX 介面，官方並未公開文件，也沒有承諾相容性。
> 本文內容全部由實際抓取與測試得來（統計週 2026/10/27～2026/11/02），欄位與行為隨時可能改變。
> 請遵守各站使用條款，控制請求頻率（榜單每週才更新一次，沒有必要頻繁抓取），並在產品中標明資料來源。

---

## 0. 快速對照

### 台灣

| 項目 | 好樂迪 | 錢櫃 |
|---|---|---|
| 端點 | `POST https://www.holiday.com.tw/Ashx/SongInfo.ashx` | `POST https://www.cashboxparty.com/ashx/ah_Song.ashx` |
| 請求格式 | body 是 **JSON 陣列**，只有一個物件 | 同左 |
| `Content-Type` | `application/x-www-form-urlencoded; charset=utf-8`（照抄前端，實際內容是 JSON） | 同左 |
| 必要標頭 | 無（`User-Agent` 建議帶） | **必須帶 `Referer: https://www.cashboxparty.com/...`**，否則回 `Result: "998"` |
| GET 是否可用 | 否，302 轉到錯誤頁 | 否，200 但空 body |
| 回應 | JSON 陣列，`[0]` 是唯一物件，`DataList` 是歌曲清單 | JSON 陣列，**每一列就是一首歌**，狀態欄位重複出現在每列 |
| 字串編碼 | 回傳值經 `encodeURIComponent`，**需 URL-decode** | 一般 UTF-8，不需解碼 |
| 分頁 | 有，每頁 20 筆 | 榜單一次回全部（每語言 30 筆）；搜尋有分頁 |
| 統計期間 | 榜單回應有 `sdate` / `edate` | 每列有 `StartDate` / `EndDate` |
| 成功判斷 | `Ok == "1"` | `Result == "0"` |
| 榜單長度 | 30 名（2 頁） | 30 名 |
| 語言 | 國、台、粵、英、日、韓、越 | 國、台、粵、日、英 |


### 日本

| 項目 | JOYSOUND | DAM |
|---|---|---|
| 取得方式 | `GET` 榜單頁面，解析內嵌的 JSON-LD | `GET` 榜單頁面，解析靜態 HTML |
| 網址規則 | `/web/karaoke/ranking/{genre}/{period}` | `/ranking/`、`/ranking/{kind}/`、`/genre/{genre}/` |
| 必要標頭 | 無 | 無 |
| 一頁幾首 | 100（急上昇 30、PV 榜約 30） | 每區塊 100，一頁同時含日／週／月 |
| 期間 | 日（預設）、週、月 | 日、週、月，另附上半期／下半期／年間前 3 名 |
| 分類 | 總合、動畫、VOCALOID、演歌、外國曲、歌手；另有急上昇、PV、新曲トレンド | 總合、急上昇、雙人對唱、歌手；動畫、VOCALOID、VTuber、演歌、外國曲 |
| 曲號 | 歌曲 ID（數字，`/web/search/song/{id}`） | 曲番 `XXXX-XX`（`requestNo`） |
| 上週名次 | 頁面沒有 | 頁面沒有（急上昇榜另算） |
| 更新時間 | 日榜每日；週榜週一到週日 | 每天 11:00；週榜週日到週六，週日更新；月榜每月 1 日 |

---

## 1. 好樂迪（Holiday KTV）

### 1.1 端點

```
POST https://www.holiday.com.tw/Ashx/SongInfo.ashx
Content-Type: application/x-www-form-urlencoded; charset=utf-8
User-Agent: <任意瀏覽器 UA>

[{"m": "<method>", ...}]
```

- body 一定是「只含一個物件的 JSON 陣列」。送單一物件（沒有 `[]`）會被導到 `/pageerror.aspx`。
- 不需要 Cookie、Referer 或登入。
- 回應是 JSON 陣列，取 `[0]`。

### 1.2 方法一覽

| `m` | 用途 | 其他參數 |
|---|---|---|
| `top` | 點播排行 / 新歌排行 | `ltype`, `page` |
| `new` | 新進歌曲（依入庫順序） | `ltype`, `page` |
| `search` | 搜尋歌手 / 歌名 | `stype`, `keyw`, `len`, `page` |
| `addsobook` | 加入「我的歌本」 | `sno`；需登入，本文不涵蓋 |

### 1.3 `m = "top"`：排行榜

**請求**

```json
[{"m": "top", "ltype": "tc", "page": 1}]
```

| 參數 | 型別 | 說明 |
|---|---|---|
| `ltype` | string | 榜單代碼，見下表 |
| `page` | int | 1 起算，每頁 20 筆；超過 `MaxPage` 會回最後一頁 |

`ltype` 代碼（對應官網網址 `/SongInfo/SongList.aspx?st=top&lt=<ltype>`）：

| `ltype` | 榜單 |
|---|---|
| `tc` | 國語點播排行 |
| `tt` | 台語點播排行 |
| `ct` | 粵語點播排行 |
| `et` | 英語點播排行 |
| `jt` | 日語點播排行 |
| `kt` | 韓語點播排行 |
| `vt` | 越南語點播排行 |
| `nc` | 國語新歌排行 |
| `nt` | 台語新歌排行 |

**回應**

```json
[{
  "Ok": "1",
  "Msg": "",
  "sdate": "2026%2F10%2F27",
  "edate": "2026%2F11%2F02",
  "Page": [{"MaxPage": 2, "ThisPage": 1, "PreviousPage": 1, "NextPage": 2}],
  "DataList": [
    {
      "thisweek": "1",
      "lastweek": "1",
      "weeks": "%E2%86%92",
      "id": "02657",
      "songname": "%E7%94%B2%E4%B9%99%E4%B8%99%E4%B8%81",
      "singer": "%E6%9D%8E%E4%BD%B3%E8%96%87",
      "iconurl": "https%3A%2F%2Fi.kfs.io%2Falbum%2Fglobal%2F295320632%2C0v2%2Ffit%2F160x160.jpg",
      "songurl": "https%3A%2F%2Fwidget.kkbox.com%2Fv1%2F%3Fid%3DGptIJ2y--IKc1ewMvC%26type%3Dsong%26terr%3Dtw%26lang%3Dtc%26autoplay%3Dtrue"
    }
  ]
}]
```

| 欄位 | 說明 |
|---|---|
| `Ok` | `"1"` 成功；`"-91"` 榜單代碼錯誤（`Msg: 歌曲類別不正確`） |
| `sdate` / `edate` | 統計起訖日，URL-encoded，格式 `yyyy/MM/dd` |
| `Page[0]` | 分頁資訊 |
| `DataList[].thisweek` | 本週名次 |
| `DataList[].lastweek` | 上週名次 |
| `DataList[].weeks` | 升降符號，解碼後是 `↑` `↓` `→`（新進榜另有文字） |
| `DataList[].id` | 好樂迪曲號（5 碼，點歌機用） |
| `DataList[].songname` / `singer` | 歌名 / 歌手，URL-encoded |
| `DataList[].iconurl` | KKBOX 專輯封面 160×160，可能為空字串 |
| `DataList[].songurl` | KKBOX 試聽 widget 連結，可能為空字串 |

**所有字串欄位都要 `decodeURIComponent` / `urllib.parse.unquote`。**

### 1.4 `m = "new"`：新進歌曲

```json
[{"m": "new", "ltype": "c", "page": 1}]
```

| `ltype` | 語言 |
|---|---|
| `c` | 國語 |
| `t` | 台語 |
| `g` | 粵語 |
| `w` | 英語 |
| `j` | 日語 |
| `k` | 韓語 |
| `v` | 越南語 |

回應與 `top` 相同，但沒有 `sdate`/`edate`/`thisweek`/`lastweek`/`weeks`，多一個 `lanype`（`"1"` 國語、`"2"` 台語…）。實測國語有 5 頁、每頁 20 筆。

### 1.5 `m = "search"`：搜尋

```json
[{"m": "search", "stype": "0", "keyw": "周杰倫", "len": "", "page": 1}]
```

| 參數 | 說明 |
|---|---|
| `stype` | `"0"` 依歌手，`"1"` 依歌名（模糊比對，子字串） |
| `keyw` | 關鍵字，直接放 UTF-8 即可（前端會先 encodeURIComponent，兩種都收） |
| `len` | 歌名字數，`""` 不限，`"1"`～`"11"`（11 = 十一字以上）；只對 `stype=1` 有意義 |
| `page` | 1 起算，每頁 20 筆 |

回應欄位同 `new`（`id`, `songname`, `singer`, `iconurl`, `songurl`），無統計期間。

### 1.6 範例

curl：

```bash
curl -s -A "Mozilla/5.0" \
  -H "Content-Type: application/x-www-form-urlencoded; charset=utf-8" \
  --data-raw '[{"m":"top","ltype":"tc","page":1}]' \
  https://www.holiday.com.tw/Ashx/SongInfo.ashx
```

Python：

```python
import json, urllib.parse, urllib.request

def holiday(method, **params):
    body = json.dumps([{"m": method, **params}]).encode()
    req = urllib.request.Request(
        "https://www.holiday.com.tw/Ashx/SongInfo.ashx",
        data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                 "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r)[0]
    if d.get("Ok") != "1":
        raise RuntimeError(d.get("Msg"))
    dec = lambda v: urllib.parse.unquote(v) if isinstance(v, str) else v
    d["sdate"], d["edate"] = dec(d.get("sdate")), dec(d.get("edate"))
    d["DataList"] = [{k: dec(v) for k, v in row.items()} for row in d.get("DataList", [])]
    return d

def holiday_chart(ltype="tc"):
    first = holiday("top", ltype=ltype, page=1)
    rows = first["DataList"]
    for p in range(2, first["Page"][0]["MaxPage"] + 1):
        rows += holiday("top", ltype=ltype, page=p)["DataList"]
    return first["sdate"], first["edate"], rows

sdate, edate, rows = holiday_chart("tc")
print(sdate, "~", edate)
for r in rows[:10]:
    print(r["thisweek"], r["songname"], "-", r["singer"], f"(上週 {r['lastweek']})")
```

---

## 2. 錢櫃（Cashbox PartyWorld）

### 2.1 端點

```
POST https://www.cashboxparty.com/ashx/ah_Song.ashx
Content-Type: application/x-www-form-urlencoded; charset=utf-8
Referer: https://www.cashboxparty.com/Music/KTVMusic.aspx
User-Agent: <任意瀏覽器 UA>

[{"m": "<method>", ...}]
```

- **沒有 `Referer` 會被拒絕**：回 `[{"Result":"998","Msg":"路徑不合法，無權使用該服務！"}]`。Referer 只要是 cashboxparty.com 的頁面即可。
- body 同樣是「只含一個物件的 JSON 陣列」。
- 回應是 JSON 陣列，**每個元素是一首歌**，`Result`/`Msg` 在每一列重複。沒有資料時回單一列 `{"Result":"0","Msg":"","SongNo":""}`，請用 `SongNo == ""` 判斷空結果。
- 未知的 `m` 會回空 body（非 JSON）。

### 2.2 方法一覽

| `m` | 用途 | 其他參數 |
|---|---|---|
| `bl` | 排行榜（新歌排行 / 點播總排行 / 外語排行） | `t`, `lang` |
| `sn5` | 最近 5 個新歌入庫日期 | 無 |
| `sn` | 指定日期的新歌快報 | `lang`, `date` |
| `ss` | 搜尋 | `lang`, `sir`, `son`, `wl`, `type`, `page` |
| `sf` | 我的點歌本 | `uid`；需登入，本文不涵蓋 |

同站另有 `ah_Adv.ashx`（廣告）、`ah_Member.ashx`（會員）、`ah_Security.ashx`（試聽 token 解密），與榜單無關。

### 2.3 `m = "bl"`：排行榜

```json
[{"m": "bl", "t": "2", "lang": "01,02"}]
```

| 參數 | 說明 |
|---|---|
| `t` | `"1"` 新歌排行榜，`"2"` 點播總排行（外語榜也是 `"2"`）。其他值回空 |
| `lang` | 語言代碼，可用逗號一次要多個 |

`lang` 代碼：

| `lang` | 語言 | 哪個榜有 |
|---|---|---|
| `01` | 國語 | t=1, t=2 |
| `02` | 台語 | t=1, t=2 |
| `03` | 粵語 | 只有 t=2 |
| `04` | 日語 | 只有 t=2 |
| `05` | 英語 | 只有 t=2 |

官網的三個分頁對應：新歌排行榜 = `t=1, lang=01,02`；點播總排行 = `t=2, lang=01,02`；外語排行榜 = `t=2, lang=03,04,05`。

**回應**（每列一首歌，每語言 30 筆，依 `LangCode` 再依 `ThisWeekend` 排序）

```json
[{
  "Result": "0",
  "Msg": "",
  "Type": "2",
  "LangCode": "01",
  "LangName": "國語",
  "SongNo": "02574",
  "ESongNo": "8F197E17E58F4F85BF330FDC3DB96C1C",
  "SongName": "甲乙丙丁",
  "Singer": "李佳薇",
  "ThisWeekend": "1",
  "LastWeekend": "1",
  "StartDate": "2026/10/27",
  "EndDate": "2026/11/02",
  "Greatest": "1",
  "Champion": "6",
  "KKSongID": "6882E5...（加密字串）",
  "IconUrl": "https://i.kfs.io/album/global/295320632,0v2/fit/160x160.jpg"
}]
```

| 欄位 | 說明 |
|---|---|
| `Result` / `Msg` | `"0"` 成功；`"998"` Referer 不合法 |
| `Type` | 回傳你送的 `t` |
| `LangCode` / `LangName` | 語言代碼 / 中文名 |
| `SongNo` | 錢櫃曲號（5 碼，點歌機用） |
| `ESongNo` | 曲號的雜湊，前端用來當 DOM id 與加歌本 |
| `SongName` / `Singer` | 歌名 / 歌手（含多人用「、」分隔） |
| `ThisWeekend` | 本週名次 |
| `LastWeekend` | 上週名次；`"0"` 表示新進榜（前端顯示「新進」「--」） |
| `StartDate` / `EndDate` | 統計起訖日 |
| `Greatest` | 歷史最高名次 |
| `Champion` | 累計冠軍週數 |
| `KKSongID` | KKBOX 曲目 id 的加密值，需經 `ah_Security.ashx` 解密才能試聽，對外無用 |
| `IconUrl` | KKBOX 專輯封面 160×160，可能為空 |

外語榜（03/04/05）一樣有 `LastWeekend`，但官網前端刻意不顯示升降。

### 2.4 `m = "sn5"`、`m = "sn"`：新歌快報

```json
[{"m": "sn5"}]
```
回 5 列 `{"Result":"0","Msg":"","InDate":"2026/10/29"}`，是最近 5 個新歌入庫批次日期。

```json
[{"m": "sn", "lang": "01,02", "date": "2026/10/29"}]
```
`date` 填 `sn5` 給的日期；`""` 代表最新一批。回應每列一首歌：`LangCode`, `SongNo`, `ESongNo`, `SongName`, `Indate`（注意小寫 d）, `Singer`, `LangName`, `KKSongID`, `IconUrl`。

### 2.5 `m = "ss"`：搜尋

```json
[{"m": "ss", "lang": "01", "sir": "", "son": "%E6%93%B1%E6%B7%BA", "wl": "", "type": "02", "page": 1}]
```

| 參數 | 說明 |
|---|---|
| `lang` | `"01"` 國語、`"02"` 台語、`"03"` 外語、`""` 不限 |
| `type` | `"01"` 依歌手名稱（用 `sir`），`"02"` 依曲名（用 `son`） |
| `sir` | 歌手關鍵字，前端會 `encodeURIComponent`；實測直接送 UTF-8 也可 |
| `son` | 曲名關鍵字，同上 |
| `wl` | 前端固定送 `""`（推測為字數 word length，未實作） |
| `page` | 1 起算，每頁 20 筆 |

回應每列一首歌，另含 `ThisPage`, `TotalPage`, `TotalCount`, `PageShowCount`。

### 2.6 範例

curl：

```bash
curl -s -A "Mozilla/5.0" \
  -H "Referer: https://www.cashboxparty.com/Music/KTVMusic.aspx" \
  -H "Content-Type: application/x-www-form-urlencoded; charset=utf-8" \
  --data-raw '[{"m":"bl","t":"2","lang":"01,02"}]' \
  https://www.cashboxparty.com/ashx/ah_Song.ashx
```

Python：

```python
import json, urllib.request

def cashbox(method, **params):
    body = json.dumps([{"m": method, **params}]).encode()
    req = urllib.request.Request(
        "https://www.cashboxparty.com/ashx/ah_Song.ashx",
        data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                 "Referer": "https://www.cashboxparty.com/Music/KTVMusic.aspx",
                 "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        rows = json.load(r)
    if not rows or rows[0].get("Result") != "0":
        raise RuntimeError(rows[0].get("Msg") if rows else "empty response")
    return [r for r in rows if r.get("SongNo")]

rows = cashbox("bl", t="2", lang="01,02")
for lang in ("01", "02"):
    sub = [r for r in rows if r["LangCode"] == lang]
    print(sub[0]["LangName"], sub[0]["StartDate"], "~", sub[0]["EndDate"])
    for r in sub[:10]:
        print(r["ThisWeekend"], r["SongName"], "-", r["Singer"], f"(上週 {r['LastWeekend']})")
```

---

## 3. 兩家資料合併的注意事項

- **曲號不能當主鍵**：好樂迪 `id` 與錢櫃 `SongNo` 都是 5 碼點歌機曲號。老歌兩邊常常相同（《擱淺》67060、《天后》45744、《我懷念的》42589），但近年新歌各自編號（《甲乙丙丁》好樂迪 02657、錢櫃 02574；《看著我的眼睛說》21900 對 58828）。要對齊請用「歌名 + 歌手」正規化後比對，曲號相同只當加分條件，另可用兩邊都有的 KKBOX 封面 URL 當輔助鍵。
- **統計週一致**：兩家都是週一到週日（實測 10/27～11/02），通常週一或週二更新。排程抓取建議每週一次。
- **升降欄位語意不同**：好樂迪給符號 `weeks`，錢櫃只給 `LastWeekend` 數字，`"0"` 代表新進榜。
- **歌手分隔符**：好樂迪用「、」或「．」，錢櫃用「、」；合併前統一。
- **編碼**：只有好樂迪需要 URL-decode。

---

---

## 4. JOYSOUND（エクシング）

### 4.1 取得方式

沒有 AJAX API。榜單頁面由 Next.js 在伺服器端輸出，完整 TOP100 直接在 HTML 裡，而且頁面內嵌一段 schema.org 的 **JSON-LD `ItemList`**，解析它就能拿到名次、歌名、歌手、歌曲 ID 與歌手 ID，不需要碰 DOM。

```
GET https://www.joysound.com/web/karaoke/ranking/{genre}/{period}
User-Agent: <任意瀏覽器 UA>
```

- 不需要 Cookie、Referer 或登入。
- 用 `RSC: 1` 標頭要 React Server Components payload 會被 307 轉走，不要走這條。

### 4.2 網址規則

| `genre` | 榜單 |
|---|---|
| `all` | 総合カラオケランキング |
| `anime` | アニメ |
| `vocaloid` | ボカロ |
| `enka` | 演歌 |
| `foreign` | 洋楽 |
| `artist` | アーティスト（以歌手為單位） |

| `period` | 說明 |
|---|---|
| （省略） | デイリー。`/all/daily` 這種寫法不存在，會 404 |
| `weekly` | 週間，週一到週日 |
| `monthly` | 月間 |

特殊頁面（沒有 `period`）：

| 路徑 | 榜單 | 筆數 |
|---|---|---|
| `/web/karaoke/ranking/hot` | 急上昇 | 30 |
| `/web/karaoke/ranking/pv` | アクセスランキング（網頁瀏覽數，非歌唱次數） | 約 30 |
| `/web/karaoke/ranking/trends/all` | 新曲トレンド（新配信曲的頁面存取數） | 依當週新曲數 |
| `/web/s/karaoke/feature/ranking/2026-half` | 上半期 | 專題頁 |
| `/web/s/karaoke/contents/annual_ranking/2025` | 年間 | 專題頁 |

### 4.3 頁面裡的資料

**集計期間**：HTML 中有「集計期間:」字樣，後面接 `2026/10/26 - 2026/11/01`（日榜只有一個日期）。急上昇頁沒有期間，只有「2026/11/03 00:00更新」。

**JSON-LD**（`<script type="application/ld+json">`）：

```json
{
  "@context": "https://schema.org",
  "@graph": [{
    "@type": "WebPage",
    "name": "カラオケランキング-週間 | JOYSOUND",
    "mainEntity": {
      "@type": "ItemList",
      "name": "カラオケランキング-週間",
      "numberOfItems": 100,
      "itemListElement": [{
        "@type": "ListItem",
        "position": 1,
        "item": {
          "@type": "MusicRecording",
          "name": "伯方の塩",
          "byArtist": {"@type": "MusicGroup", "name": "塩谷信廣",
                       "url": "https://www.joysound.com/web/search/artist/432512"},
          "url": "https://www.joysound.com/web/search/song/1143056"
        }
      }]
    }
  }]
}
```

| 欄位 | 說明 |
|---|---|
| `position` | 名次 |
| `item.name` | 歌名 |
| `item.byArtist.name` | 歌手 |
| `item.url` 最後一段 | JOYSOUND 歌曲 ID |
| `item.byArtist.url` 最後一段 | JOYSOUND 歌手 ID |

頁面**沒有**上週名次或升降資訊。統計依據是 JOYSOUND 與 UGA 機台的歌唱次數（官方年間榜新聞稿說明）。

### 4.4 範例

```python
import json, re, urllib.request

def joysound_chart(genre="all", period="weekly"):
    """genre: all|anime|vocaloid|enka|foreign|artist, period: ''(daily)|weekly|monthly
       special pages: genre='hot'/'pv'/'trends/all' with period=''"""
    path = f"/web/karaoke/ranking/{genre}" + (f"/{period}" if period else "")
    req = urllib.request.Request("https://www.joysound.com" + path,
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8")
    m = re.search(r"集計期間[:：]\s*(?:<[^>]+>\s*)*([0-9/]+(?:\s*-\s*[0-9/]+)?)", page)
    period_text = m.group(1).strip() if m else None
    rows = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        data = json.loads(block)
        for g in data.get("@graph", [data]):
            lst = g.get("mainEntity") if isinstance(g, dict) else None
            if lst and lst.get("@type") == "ItemList":
                for it in lst["itemListElement"]:
                    song = it["item"]
                    rows.append({
                        "rank": it["position"],
                        "title": song["name"],
                        "artist": song.get("byArtist", {}).get("name"),
                        "song_id": song["url"].rsplit("/", 1)[-1],
                        "artist_id": song.get("byArtist", {}).get("url", "").rsplit("/", 1)[-1],
                    })
    return period_text, rows

period, rows = joysound_chart("all", "weekly")
print("集計期間", period, "件數", len(rows))
for r in rows[:10]:
    print(r["rank"], r["title"], "-", r["artist"], "(id", r["song_id"] + ")")
```

---

## 5. DAM（第一興商）

### 5.1 取得方式

沒有 AJAX API。榜單是靜態 HTML，每首歌一個 `<li>`，頁面上「11位以下を見る」只是前端收合，第 11～100 名已經在原始碼裡。頁面沒有 JSON-LD，要用正規表示式或 HTML parser 解析。

```
GET https://www.clubdam.com/ranking/
User-Agent: <任意瀏覽器 UA>
```

不需要 Cookie、Referer 或登入。站內另有 `/dkwebsys/search-api/AutoCompleteApi` 與 `/karaokesearch/trendwords.xml`，是搜尋框用的，與榜單無關。

### 5.2 網址規則

| 路徑 | 榜單 | 含哪些區塊 |
|---|---|---|
| `/ranking/` | 総合 | daily, weekly, monthly, firsthalf, secondhalf, year |
| `/ranking/burst/` | 急上昇 | daily, weekly, monthly |
| `/ranking/duet/` | デュエット | weekly, monthly, firsthalf, secondhalf, year |
| `/ranking/artist/` | アーティスト | weekly, monthly…（以歌手為單位，不是歌曲，本文的 regex 抓不到） |
| `/genre/anison/` | アニメ | weekly, monthly |
| `/genre/vocaloid/` | ボーカロイド | weekly, monthly |
| `/genre/vtuber/` | VTuber | weekly, monthly |
| `/genre/enka/` | 演歌・歌謡 | weekly, monthly |
| `/genre/foreign/` | 外国曲 | weekly, monthly |
| `/genre/{g}/ranking_year.html` 等 | 各分類年間／上下半期 | 專題頁 |

寫 `/ranking/index.html` 或 `/ranking/` 都可以；`/ranking/burst/index.html` 會 301 到 `/ranking/burst/`。

### 5.3 頁面結構

每個榜單是一個 `<div class="c-section" id="ranking-weekly">` 區塊：

```html
<div class="c-section" id="ranking-weekly">
  <h2 class="p-section-header__title">週間ランキング</h2>
  <span class="p-section-header__date">2026/11/01 更新</span>
  <ul class="p-song-list p-ranking-list" data-default="10">
    <li class="p-song-list__item p-ranking-list__item">
      <a class="p-song p-song--song p-ranking" href="/karaokesearch/songleaf.html?requestNo=5277-09">
        <div class="p-ranking__num p-ranking__num--first">1</div>
        <h4 class="p-song__title">怪獣の花唄</h4>
        <div class="p-song__artist">Vaundy</div>
```

| 區塊 id | 榜單 |
|---|---|
| `ranking-daily`（總合頁另有 `daily-ranking` 容器） | デイリー |
| `ranking-weekly` | 週間 |
| `ranking-monthly` | 月間 |
| `ranking_firsthalf` / `ranking_secondhalf` / `ranking_year` | 上半期／下半期／年間，主頁只放前 3 名 |

| 欄位 | 說明 |
|---|---|
| `requestNo` | DAM 曲番，格式 `XXXX-XX`，點歌機輸入用 |
| `p-ranking__num` | 名次 |
| `p-song__title` / `p-song__artist` | 歌名 / 歌手（HTML entity 要 unescape） |
| `p-section-header__date` | 更新日 |

注意：同一區塊的 `<li>` 會為 PC 與手機版各輸出一次，依 `requestNo` 去重後才是 100 筆。頁面沒有上週名次。

### 5.4 官方集計規則（來自 DAM FAQ）

| 期間 | 範圍 | 更新 |
|---|---|---|
| デイリー | 前一天 | 每天 11:00 |
| 週間 | 前一週，週日～週六 | 每週日 11:00 |
| 月間 | 前一個月 1 日～月底 | 每月 1 日 11:00 |
| 上半期 | 1/1～6/30 | 7/1 |
| 下半期 | 7/1～12/31 | 隔年 1/1 |
| 年間 | 1/1～12/31 | 隔年 1/1 |

急上昇榜：比較前一期與前前一期的名次差，差距大的歌排前面；日／週／月的更新時間同上。

### 5.5 範例

```python
import html, re, urllib.request

ROW = re.compile(
    r'requestNo=([\d-]+)"[^>]*>\s*<div class="p-ranking__num[^"]*">(\d+)</div>'
    r'.*?p-song__title">(.*?)</h4>\s*<div class="p-song__artist">(.*?)</div>', re.S)

def dam_chart(path="/ranking/"):
    """path: /ranking/ (總合) | /ranking/burst/ | /ranking/duet/ | /ranking/artist/
             /genre/anison/ | /genre/vocaloid/ | /genre/vtuber/ | /genre/enka/ | /genre/foreign/
       returns {section_id: {"title", "updated", "rows": [...]}}"""
    req = urllib.request.Request("https://www.clubdam.com" + path,
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8")
    out = {}
    for m in re.finditer(r'<div class="c-section" id="([^"]*ranking[^"]*)">(.*?)(?=<div class="c-section" id="|\Z)',
                         page, re.S):
        sid, body = m.group(1), m.group(2)
        title = re.search(r'p-section-header__title">(.*?)</h2>', body)
        updated = re.search(r'p-section-header__date">(.*?)</span>', body)
        rows, seen = [], set()
        for req_no, rank, song, artist in ROW.findall(body):
            if req_no in seen:          # PC 與手機版各輸出一次，去重
                continue
            seen.add(req_no)
            rows.append({"rank": int(rank), "title": html.unescape(song),
                         "artist": html.unescape(artist), "request_no": req_no})
        out[sid] = {"title": html.unescape(title.group(1)) if title else sid,
                    "updated": updated.group(1) if updated else None, "rows": rows}
    return out

charts = dam_chart("/ranking/")
for sid in ("ranking-daily", "ranking-weekly", "ranking-monthly"):
    c = charts[sid]
    print(c["title"], c["updated"], "件數", len(c["rows"]))
    for r in c["rows"][:5]:
        print(" ", r["rank"], r["title"], "-", r["artist"], "(曲番", r["request_no"] + ")")
```

---

## 6. 日本資料的注意事項

- **週的定義不同**：JOYSOUND 週榜是週一～週日，DAM 是週日～週六，兩家「本週」差一天，對照時要看各自的期間。
- **曲號不互通**：JOYSOUND 歌曲 ID 是純數字，DAM 曲番是 `XXXX-XX`，與台灣的 5 碼曲號也無關。跨系統同樣用「歌名 + 歌手」正規化比對。
- **歌名寫法有差**：同一首歌 JOYSOUND 寫「好きすぎて滅!」（半形驚嘆號）、DAM 寫「好きすぎて滅！」（全形）。比對前先做 NFKC 正規化。
- **沒有升降欄位**：兩家頁面都只有本期名次。要算升降要自己保存上一期的結果。
- **抓取頻率**：日榜每天一次、週榜每週一次就夠；JOYSOUND 頁面約 400～600 KB，DAM 約 360 KB，不要輪詢。

---

## 7. KKBOX 風雲榜（串流）

### 7.1 端點

KKBOX 風雲榜網頁 kma.kkbox.com/charts 的前端用一組不需登入的 JSON 介面載入榜單。它和 KKBOX Open API 是兩回事，後者要申請 client 憑證並走 OAuth。

```
GET https://kma.kkbox.com/charts/api/v1/{period}?terr=tw&lang=tc&type={type}&category={category}&limit=50
User-Agent: <任意瀏覽器 UA>
```

不需要 Cookie、Referer 或登入。

| `period` | 說明 |
|---|---|
| `daily` | 日榜 |
| `weekly` | 週榜，週五到週四 |
| `yearly` | 年度累積榜（本站未收錄） |
| `hourly` | 即時榜（本站未收錄） |

| 參數 | 說明 |
|---|---|
| `terr` | 地區：`tw`、`hk`、`sg`、`jp` |
| `lang` | 名稱語言，`tc` 為繁體中文 |
| `type` | `song` 單曲，`newrelease` 新歌 |
| `category` | 曲風 id，見 7.2 |
| `date` | 選填，`YYYY-MM-DD`；省略時回最新一期。週榜填該週的週四 |
| `limit` | 筆數，**不帶時只回 5 筆**，上限 50 |

### 7.2 曲風清單

```
GET https://kma.kkbox.com/charts/api/v1/{daily|weekly}/categories?terr=tw&lang=tc&type=song
```

回傳每個曲風的 `category_id`、`category_name`、`start_date`、`end_date`。日榜有 6 種，週榜另有原聲帶、電子、嘻哈等共 17 種。

| `category` | 曲風 |
|---|---|
| 297 | 華語 |
| 304 | 台語 |
| 390 | 西洋 |
| 308 | 日語 |
| 314 | 韓語 |
| 320 | 粵語 |

### 7.3 回應

```json
{
  "code": 0,
  "message": "",
  "data": {
    "date": "2026-10-29",
    "charts": {
      "song": [{
        "rankings": {"this_period": 1, "last_period": 1},
        "song_id": "GptIJ2y--IKc1ewMvC",
        "song_name": "甲乙丙丁Strangers - 你我怎麼兩清",
        "artist_name": "李佳薇 (Jess Lee)",
        "album_name": "甲乙丙丁Strangers",
        "song_url": "https://www.kkbox.com/tw/tc/song/GptIJ2y--IKc1ewMvC",
        "cover_image": {"small": "https://i.kfs.io/...160x160.jpg", "normal": "https://i.kfs.io/...500x500.jpg"},
        "release_date": 1783440000
      }]
    },
    "playlist_id": {"song": "..."}
  }
}
```

| 欄位 | 說明 |
|---|---|
| `code` | `0` 成功，**有時是數字、有時是字串**，比對前先轉字串；`104` 曲風 id 錯誤等，`data` 會是空陣列 |
| `data.date` | 這一期的日期。週榜是週四，統計區間是往前 6 天的週五到這天 |
| `data.charts.{type}` | 歌曲陣列，key 與請求的 `type` 相同 |
| `rankings.this_period` | 本期名次 |
| `rankings.last_period` | 上期名次；新進榜是 `null` |
| `song_name` / `artist_name` | 歌名與歌手，常帶副標或英文名，例如「李佳薇 (Jess Lee)」 |
| `song_url` | KKBOX 歌曲頁 |

週期的換算來自前端程式：2016-01-01 起週榜以週五開頭、週四結尾，更早的資料是週日到週六。

### 7.4 範例

```python
import json, urllib.request

def kkbox_chart(period="weekly", category=297, type_="song"):
    url = (f"https://kma.kkbox.com/charts/api/v1/{period}"
           f"?terr=tw&lang=tc&type={type_}&category={category}&limit=50")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if str(payload.get("code")) != "0":   # sometimes 0, sometimes "0"
        raise RuntimeError(f"code={payload.get('code')} {payload.get('message')}")
    data = payload["data"]
    return data["date"], data["charts"][type_]

date, rows = kkbox_chart("weekly", 297)
print("週榜截至", date)
for r in rows[:10]:
    rk = r["rankings"]
    print(rk["this_period"], r["song_name"], "-", r["artist_name"], f"(上期 {rk['last_period'] or 'NEW'})")
```

---

## 8. iTunes Search API（曲風與 Apple Music 連結）

這是 Apple 官方公開、不需要金鑰的搜尋介面。本站用它取得曲風與 Apple Music 曲目 ID。

```
GET https://itunes.apple.com/search?term={歌名 歌手}&country={tw|jp}&media=music&entity=song&limit=10&lang=en_us
```

| 參數 | 說明 |
|---|---|
| `term` | 關鍵字。本站用去掉括號與副標的歌名，加第一位歌手 |
| `country` | 商店地區。台灣來源先查 `tw`，日本來源先查 `jp`，查不到再換另一區 |
| `lang` | 加 `en_us` 讓 `primaryGenreName` 固定是英文，例如 `Mandopop`、`Tai-Pop`、`Enka`、`Anime`；不加會回傳該地區的語言 |
| `limit` | 回傳筆數，本站取 10 筆再自己挑 |

回應的 `results[]` 中，本站使用：

| 欄位 | 用途 |
|---|---|
| `trackName` / `artistName` | 比對是否為同一首歌 |
| `primaryGenreName` | 曲風標籤 |
| `trackId` | 組成 `https://music.apple.com/{country}/song/{trackId}` 試聽連結 |
| `collectionName` | 排除 live、伴奏、卡拉 OK 等版本 |

比對規則：歌名相似度至少 0.85，歌手相似度至少 0.6；排除 live、instrumental、karaoke、カラオケ、伴奏等版本；歌名與查詢完全相同的結果優先，例如會選「怪獣の花唄」而不是「怪獣の花唄 - replica -」。

限制與注意：

- 頻率約每分鐘 20 次，超過會回 403。本站每次請求間隔 3.2 秒，被擋時當次停止並保留已查到的結果。
- 曲風是商店分類，粒度粗，台語歌也可能標成 Mandopop。
- 同一首歌在不同版本可能有不同曲風。

### KKBOX 試聽 widget

```
https://widget.kkbox.com/v1/?id={KKBOX song id}&type=song&terr=tw&lang=tc&autoplay=true
```

KKBOX 曲目 ID 的來源：KKBOX 風雲榜回應的 `song_id`，以及好樂迪排行榜 `songurl` 欄位裡的 `id` 參數。

## 附錄 A：星聚點（newcbparty.com）

沒有 AJAX API，榜單是伺服器端輸出的靜態 HTML，**而且資料停在 2024/10/04～10/08，之後未更新**，不建議當資料源。

```
GET https://www.newcbparty.com/billboard.php?p=<n>
```

| `p` | 榜單 |
|---|---|
| 7 | 新進歌曲 |
| 5 | 國語新歌排行 |
| 6 | 台語新歌排行 |
| 12 | 華語新歌排行 |
| 0 | 國語點播排行 |
| 1 | 台語點播排行 |
| 3 | 英語點播排行 |
| 4 | 日語點播排行 |
| 2 | 粵語點播排行 |
| 11 | 華語點播排行 |

頁面是一張 `<table>`，欄位依序：本週排名、上週排名、升降、曲號、歌曲名稱、歌手；頁首有「統計期間 yyyy/MM/dd~ yyyy/MM/dd」。

## 附錄 B：錯誤碼速查

| 站 | 回傳 | 意義 |
|---|---|---|
| 好樂迪 | `Ok: "1"` | 成功 |
| 好樂迪 | `Ok: "-91"`, `Msg: 歌曲類別不正確` | `ltype` 錯誤 |
| 好樂迪 | HTTP 302 → `/pageerror.aspx` | 用 GET、或 body 不是 JSON 陣列 |
| 錢櫃 | `Result: "0"` | 成功（`SongNo == ""` 表示無資料） |
| 錢櫃 | `Result: "998"`, `Msg: 路徑不合法，無權使用該服務！` | 缺少或錯誤的 `Referer` |
| 錢櫃 | HTTP 200 空 body | 用 GET、或未知的 `m` |
| JOYSOUND | HTTP 404 | 不存在的 genre/period 組合（例如 `/all/daily`） |
| JOYSOUND | HTTP 307 | 帶 `RSC: 1` 標頭請求 |
| DAM | HTTP 301 | `/index.html` 會轉到目錄路徑，跟著轉即可 |
| KKBOX | `code: 104`, `data: []` | 曲風 id 不存在 |
| KKBOX | 只回 5 筆 | 沒帶 `limit` |
| iTunes | HTTP 403 | 超過每分鐘約 20 次的頻率限制 |
