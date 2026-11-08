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
    spotifyListen: "Spotify 試聽",
    spotifySearch: "Spotify 搜尋",
    playerTitle: "{service} 播放器：{q}",
    closePlayer: "再點一次收起播放器",
    searchHint: "沒有找到對應曲目，改為搜尋「{q}」",
    genreHint: "曲風：{g}（Apple Music 分類）",
    genreCredit: "曲風與 Apple Music 連結來自 iTunes Search API，Spotify 曲目來自 Spotify Web API；BPM 由 Beat This! 模型、# 標籤由 Essentia（MTG Discogs-EffNet）模型分析 30 秒試聽估算。",
    tagHint: "{group}：{tag}（Essentia 模型分析 30 秒試聽）",
    tagGroup_genre: "風格",
    tagGroup_mood: "情緒",
    tagGroup_instrument: "樂器",
    tagGroup_vocal: "人聲",
    aboutTagsTitle: "關於 # 標籤",
    aboutTagsIntro: "歌曲下方的彩色 # 標籤，是用西班牙龐培法布拉大學音樂科技研究組（MTG）的 Essentia Discogs-EffNet 模型分析 iTunes 30 秒試聽得來的。模型先把音訊轉成特徵向量，再由多個小型分類器判斷風格、情緒、樂器與人聲。",
    aboutTagsGenre: "Discogs 的 400 種音樂風格，最多 2 個。",
    aboutTagsMood: "快樂、悲傷、放鬆、派對、愛情等情緒，最多 3 個。",
    aboutTagsInstrument: "40 種樂器，最多 3 個。",
    aboutTagsVocal: "女聲、男聲或純音樂，只在模型很有把握時才標。",
    aboutTagsRules: "為了避免標籤太多，每組都有分數門檻與數量上限，平均每首約 3 到 4 個，有些歌一個都沒有。K-pop、J-pop 這類依國家或語言定義的風格不標，地區請看歌名旁的曲風標籤；互相矛盾的情緒（例如快樂與悲傷）只留分數較高的一個。",
    aboutTagsLimits: "這些是模型根據 30 秒試聽做的推測，可能出錯。模型以西方音樂訓練，二胡、古箏等樂器沒有對應類別，華語抒情歌多半會標成「抒情」。",
    aboutTagsLicense: "模型以 CC BY-NC-SA 4.0 授權，僅限非商業使用。",
    aboutTagsDemo: "在瀏覽器試用同一組模型",
    aboutTagsMore: "完整規則",
    infoLyricist: "詞",
    infoComposer: "曲",
    infoWriter: "詞曲",
    infoArranger: "編曲",
    infoProducer: "製作人",
    infoMix: "混音",
    infoRecording: "錄音",
    infoMastering: "母帶後製",
    infoLyrics: "歌詞",
    lyricsKkbox: "KKBOX 歌詞頁",
    lyricsKkboxSearch: "在 KKBOX 搜尋",
    lyricsUtaNet: "在歌ネット搜尋",
    infoAlbum: "專輯",
    infoReleased: "發行日期",
    infoYear: "發行年份",
    infoLabel: "發行公司",
    infoMaker: "製作公司",
    infoIsrc: "ISRC",
    infoType: "類別",
    infoCopyright: "版權標示",
    infoSources: "資料來源",
    infoMore: "點一下展開完整出版資訊",
    infoSrc_ncl: "國家圖書館 ISRC",
    infoSrc_mb: "MusicBrainz",
    infoSrc_apple: "Apple Music",
    infoCredit: "出版資訊（詞曲、編曲、製作人、混音、錄音、發行公司、年份、ISRC）來自國家圖書館 ISRC 資料（政府資料開放授權條款第 1 版）、MusicBrainz（CC0）與 iTunes，自動比對歌名與歌手，可能有誤。歌詞受著作權保護，本站不收錄，只連到 KKBOX 等授權歌詞頁。",
    nameSep: "、",
    aiDisclaimer: "免責聲明：本站的曲風、BPM、音域與男女生建議、# 標籤與出版資訊，是由人工智慧模型與自動比對程式產生的。人工智慧有其極限，結果可能有錯誤或遺漏，僅供參考，請以唱片公司、KTV 業者與各官方來源公布的資料為準。",
    rangeLabel: "副歌音域",
    rangeHint: "GAME 模型分析 30 秒試聽（多半是副歌）的人聲，過濾鬼點後的最低音與最高音。整首歌的音域可能更寬。點一下看男女生建議",
    rangeSemis: "{n} 個半音",
    rangeSpan: "跨度",
    rangeAdvice: "建議",
    fit_both: "男女皆宜",
    fit_m: "適合男生",
    fit_f: "適合女生",
    voice_m: "男生",
    voice_f: "女生",
    voiceVerdict: "{g}{v}",
    v_ok: "舒適",
    v_high: "偏高",
    v_vhigh: "很高",
    v_low: "偏低",
    v_wide: "音域很寬",
    keyUp: "升 {n} Key",
    keyDown: "降 {n} Key",
    octUp: "高八度唱",
    octDown: "低八度唱",
    keyNone: "升降 Key 也不容易唱得舒服",
    keyJoin: "，",
    rangeNote: "這是副歌音域：依 30 秒試聽（多半是副歌附近）估算，主歌等其他段落可能更高或更低。",
    aboutRangeTitle: "關於副歌音域與男女生建議",
    aboutRangeIntro: "歌手下方的「副歌音域」是先用 UVR MDX-Net（Kim_Vocal_2）把 30 秒試聽裡的人聲分離出來，再用 openvpi 的 GAME 模型把歌聲轉成音符，取最低音與最高音。iTunes 試聽多半截自副歌附近，所以標成副歌音域。",
    aboutRangeFilter: "模型轉出來的音符可能有鬼點，所以會先過濾：太短的音（0.1 秒以下）、超出人聲範圍（C2 到 C7 以外）的音、前後都差 7 個半音以上的短音（常見的八度誤判）、和主要旋律相差 5 個半音以上、中間沒有其他音的孤立音，最低音與最高音也要唱滿 0.25 秒或出現 2 次以上才算數。唱的音太少（不到 4 秒）的歌不顯示。",
    aboutRangeMale: "一般男生舒適音域約 A2–F#4，G4–A4 偏高，A#4 以上很高。參考：男低音約 E2–E4、男中音約 A2–A4、男高音約 C3–C5。",
    aboutRangeFemale: "一般女生舒適音域約 F3–C5，C#5–E5 偏高，F5 以上很高。參考：女低音約 F3–F5、女中音約 A3–A5、女高音約 C4–C6。",
    aboutRangeNotes: "音名用國際標準：C4 是鋼琴正中間的 Do（中央 C），A4 = 440 Hz，數字加 1 就高一個八度。KTV 的 1 Key 等於 1 個半音。男生唱女生的歌常低八度唱，女生唱男生的歌常高八度唱，建議裡的「高八度／低八度」就是這個意思。",
    aboutRangeLimits: "這是模型的推測，只看 30 秒試聽：合唱、和聲、饒舌、假音與很重的效果器都可能讓結果偏差。舒適音域因人而異，請當作參考。",
    aboutRangeLicense: "GAME 模型以 CC BY-NC-SA 4.0 授權，僅限非商業使用；UVR MDX-Net 模型依 UVR 與作者的授權使用。",
    aboutRangeMore: "完整規則",
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
    starCta: "在 GitHub 給我星星",
    starAria: "到 GitHub 為這個專案按星星，目前 {n} 顆",
    authorLabel: "作者",
    sourceCode: "GitHub 原始碼",
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
    spotifyListen: "Listen on Spotify",
    spotifySearch: "Search Spotify",
    playerTitle: "{service} player: {q}",
    closePlayer: "Click again to close the player",
    searchHint: "No matching track found; searches for “{q}”",
    genreHint: "Genre: {g} (Apple Music category)",
    genreCredit: "Genres and Apple Music links come from the iTunes Search API and Spotify tracks from the Spotify Web API; BPM (Beat This! model) and # tags (Essentia's MTG Discogs-EffNet models) are estimated from 30-second previews.",
    tagHint: "{group}: {tag} (Essentia models on a 30-second preview)",
    tagGroup_genre: "Style",
    tagGroup_mood: "Mood",
    tagGroup_instrument: "Instrument",
    tagGroup_vocal: "Vocals",
    aboutTagsTitle: "About the # tags",
    aboutTagsIntro: "The coloured # tags under each song come from the Essentia Discogs-EffNet models by the Music Technology Group (MTG) at Universitat Pompeu Fabra, run on the 30-second iTunes preview. The model turns the audio into an embedding, and small classifiers on top of it judge style, mood, instruments and vocals.",
    aboutTagsGenre: "one or two of Discogs' 400 music styles.",
    aboutTagsMood: "up to three moods such as happy, sad, relaxed, party or love.",
    aboutTagsInstrument: "up to three of 40 instruments.",
    aboutTagsVocal: "female vocals, male vocals or instrumental, only when the model is very sure.",
    aboutTagsRules: "To keep tags sparse, every group has a minimum score and a cap, so a song gets about 3 to 4 tags on average and some get none. Country- or language-based styles such as K-pop and J-pop are left out (the genre label next to the title covers that), and of two contradicting moods, such as happy and sad, only the stronger one is kept.",
    aboutTagsLimits: "These are the model's guesses from a 30-second preview and can be wrong. It was trained mostly on Western music, so instruments such as erhu or guzheng have no class.",
    aboutTagsLicense: "The models are licensed CC BY-NC-SA 4.0, for non-commercial use only.",
    aboutTagsDemo: "Try the same models in your browser",
    aboutTagsMore: "Full rules",
    infoLyricist: "Lyrics",
    infoComposer: "Music",
    infoWriter: "Words & music",
    infoArranger: "Arranger",
    infoProducer: "Producer",
    infoMix: "Mixing",
    infoRecording: "Recording",
    infoMastering: "Mastering",
    infoLyrics: "Lyrics",
    lyricsKkbox: "KKBOX lyrics page",
    lyricsKkboxSearch: "Search on KKBOX",
    lyricsUtaNet: "Search on Uta-Net",
    infoAlbum: "Album",
    infoReleased: "Released",
    infoYear: "Release year",
    infoLabel: "Label",
    infoMaker: "Production company",
    infoIsrc: "ISRC",
    infoType: "Category",
    infoCopyright: "Copyright",
    infoSources: "Sources",
    infoMore: "Click for full publishing details",
    infoSrc_ncl: "National Central Library ISRC",
    infoSrc_mb: "MusicBrainz",
    infoSrc_apple: "Apple Music",
    infoCredit: "Publishing details (songwriters, arranger, producer, mixing, recording, label, year, ISRC) come from Taiwan's National Central Library ISRC records (Open Government Data License v1), MusicBrainz (CC0) and iTunes, matched automatically by title and artist, so some may be wrong. Lyrics are copyrighted, so the site does not copy them and only links to licensed lyrics pages such as KKBOX.",
    nameSep: ", ",
    aiDisclaimer: "Disclaimer: genres, BPM, vocal ranges and voice advice, # tags and publishing details on this site are produced by AI models and automatic matching. AI has limits, so results may contain errors or omissions. Treat them as a reference only and rely on information published by labels, KTV operators and other official sources.",
    rangeLabel: "Chorus range",
    rangeHint: "Lowest and highest sung note in the 30-second preview (usually the chorus), from the GAME model after filtering ghost notes. The full song may span more. Click for advice for male and female voices",
    rangeSemis: "{n} semitones",
    rangeSpan: "Span",
    rangeAdvice: "Advice",
    fit_both: "Fits any voice",
    fit_m: "Male voice",
    fit_f: "Female voice",
    voice_m: "Male",
    voice_f: "Female",
    voiceVerdict: "{g} {v}",
    v_ok: "comfortable",
    v_high: "high",
    v_vhigh: "very high",
    v_low: "low",
    v_wide: "very wide",
    keyUp: "key +{n}",
    keyDown: "key −{n}",
    octUp: "sing an octave up",
    octDown: "sing an octave down",
    keyNone: "hard to fit even with a key change",
    keyJoin: ", ",
    rangeNote: "This is the chorus range, estimated from a 30-second preview that is usually around the chorus; verses and other parts may go higher or lower.",
    aboutRangeTitle: "About chorus range and voice advice",
    aboutRangeIntro: "The chorus range under each artist comes from separating the vocals in the 30-second preview with UVR MDX-Net (Kim_Vocal_2), transcribing them into notes with openvpi's GAME model, and taking the lowest and highest note. iTunes previews are usually cut from around the chorus, hence “chorus range”.",
    aboutRangeFilter: "The transcription can contain ghost notes, so they are filtered first: notes under 0.1 s, notes outside the human range (C2 to C7), short notes 7 or more semitones away from both neighbours (typical octave errors), and isolated notes 5 or more semitones away from the main melody with nothing in between. The lowest and highest note must also last 0.25 s in total or occur at least twice. Songs with under 4 seconds of singing show no range.",
    aboutRangeMale: "A typical male voice is comfortable around A2–F#4; G4–A4 is high and A#4 and above is very high. For reference: bass about E2–E4, baritone A2–A4, tenor C3–C5.",
    aboutRangeFemale: "A typical female voice is comfortable around F3–C5; C#5–E5 is high and F5 and above is very high. For reference: alto about F3–F5, mezzo-soprano A3–A5, soprano C4–C6.",
    aboutRangeNotes: "Note names use scientific pitch: C4 is middle C, A4 = 440 Hz, and each number up is one octave higher. One karaoke key step is one semitone. Men often sing women's songs an octave down and women sing men's songs an octave up; that is what “octave up/down” in the advice means.",
    aboutRangeLimits: "These are model estimates from a 30-second preview only. Duets, harmonies, rap, falsetto and heavy effects can skew them, and comfortable ranges differ from person to person.",
    aboutRangeLicense: "The GAME model is licensed CC BY-NC-SA 4.0 (non-commercial use only); the UVR MDX-Net model is used under the terms given by UVR and its author.",
    aboutRangeMore: "Full rules",
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
    starCta: "Star on GitHub",
    starAria: "Star this project on GitHub ({n} stars so far)",
    authorLabel: "Author",
    sourceCode: "Source on GitHub",
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
    spotifyListen: "Spotify で試聴",
    spotifySearch: "Spotify で検索",
    playerTitle: "{service} プレーヤー：{q}",
    closePlayer: "もう一度押すとプレーヤーを閉じます",
    searchHint: "該当曲が見つからないため「{q}」を検索します",
    genreHint: "ジャンル：{g}（Apple Music の分類）",
    genreCredit: "ジャンルと Apple Music のリンクは iTunes Search API、Spotify の曲は Spotify Web API から取得。BPM（Beat This! モデル）と # タグ（Essentia の MTG Discogs-EffNet モデル）は 30 秒の試聴音源から推定しています。",
    tagHint: "{group}：{tag}（Essentia モデルで 30 秒の試聴音源から推定）",
    tagGroup_genre: "スタイル",
    tagGroup_mood: "ムード",
    tagGroup_instrument: "楽器",
    tagGroup_vocal: "ボーカル",
    aboutTagsTitle: "# タグについて",
    aboutTagsIntro: "曲の下に表示される色付きの # タグは、ポンペウ・ファブラ大学 Music Technology Group（MTG）の Essentia Discogs-EffNet モデルで iTunes の 30 秒試聴音源を分析したものです。音声を特徴ベクトルに変換し、その上の小さな分類器がスタイル、ムード、楽器、ボーカルを判定します。",
    aboutTagsGenre: "Discogs の 400 種類の音楽スタイルから最大 2 個。",
    aboutTagsMood: "ハッピー、切ない、リラックス、パーティー、ラブなどのムードを最大 3 個。",
    aboutTagsInstrument: "40 種類の楽器から最大 3 個。",
    aboutTagsVocal: "女性ボーカル、男性ボーカル、インスト。モデルの確信度が高いときだけ表示します。",
    aboutTagsRules: "タグが増えすぎないよう、グループごとにスコアの下限と個数の上限を設けています。平均は 1 曲 3〜4 個で、タグがない曲もあります。K-pop や J-pop など国や言語で決まるスタイルは付けず（地域は曲名横のジャンルタグを参照）、ハッピーと切ないのように矛盾するムードはスコアの高い方だけを残します。",
    aboutTagsLimits: "30 秒の試聴音源にもとづくモデルの推定なので、間違うこともあります。主に欧米の音楽で学習しているため、二胡や古箏などの楽器には対応するクラスがありません。",
    aboutTagsLicense: "モデルは CC BY-NC-SA 4.0 ライセンスで、非商用利用に限られます。",
    aboutTagsDemo: "同じモデルをブラウザで試す",
    aboutTagsMore: "詳しいルール",
    infoLyricist: "作詞",
    infoComposer: "作曲",
    infoWriter: "作詞・作曲",
    infoArranger: "編曲",
    infoProducer: "プロデューサー",
    infoMix: "ミックス",
    infoRecording: "レコーディング",
    infoMastering: "マスタリング",
    infoLyrics: "歌詞",
    lyricsKkbox: "KKBOX の歌詞ページ",
    lyricsKkboxSearch: "KKBOX で検索",
    lyricsUtaNet: "歌ネットで検索",
    infoAlbum: "アルバム",
    infoReleased: "発売日",
    infoYear: "発売年",
    infoLabel: "レーベル",
    infoMaker: "制作会社",
    infoIsrc: "ISRC",
    infoType: "区分",
    infoCopyright: "著作権表示",
    infoSources: "出典",
    infoMore: "クリックで出版情報をすべて表示",
    infoSrc_ncl: "台湾国家図書館 ISRC",
    infoSrc_mb: "MusicBrainz",
    infoSrc_apple: "Apple Music",
    infoCredit: "出版情報（作詞・作曲・編曲・プロデューサー・ミックス・レコーディング・レーベル・発売年・ISRC）は台湾国家図書館の ISRC データ（政府資料開放授権条款 第1版）、MusicBrainz（CC0）、iTunes から曲名と歌手名で自動照合しているため、誤りがある場合があります。歌詞は著作権で保護されているため掲載せず、KKBOX などの正規の歌詞ページへリンクしています。",
    nameSep: "、",
    aiDisclaimer: "免責事項：本サイトのジャンル、BPM、音域と男女別アドバイス、# タグ、出版情報は AI モデルと自動照合によって生成されています。AI には限界があり、誤りや抜けが含まれる場合があります。参考情報としてご利用いただき、正確な情報はレコード会社・カラオケ事業者などの公式発表をご確認ください。",
    rangeLabel: "サビ音域",
    rangeHint: "GAME モデルで 30 秒の試聴音源（主にサビ）の歌声を分析し、ゴーストノートを除いた最低音と最高音。曲全体ではもっと広い場合があります。クリックで男女別のアドバイス",
    rangeSemis: "{n} 半音",
    rangeSpan: "幅",
    rangeAdvice: "アドバイス",
    fit_both: "男女どちらも",
    fit_m: "男性向け",
    fit_f: "女性向け",
    voice_m: "男性",
    voice_f: "女性",
    voiceVerdict: "{g}{v}",
    v_ok: "歌いやすい",
    v_high: "やや高い",
    v_vhigh: "かなり高い",
    v_low: "やや低い",
    v_wide: "音域が広い",
    keyUp: "キー +{n}",
    keyDown: "キー −{n}",
    octUp: "1 オクターブ上で",
    octDown: "1 オクターブ下で",
    keyNone: "キーを変えても歌いにくい",
    keyJoin: "、",
    rangeNote: "サビの音域です。30 秒の試聴音源（主にサビ付近）から推定しているため、A メロなど他の部分はもっと高い・低い場合があります。",
    aboutRangeTitle: "サビ音域と男女別アドバイスについて",
    aboutRangeIntro: "歌手名の下の「サビ音域」は、30 秒の試聴音源から UVR MDX-Net（Kim_Vocal_2）で歌声を分離し、openvpi の GAME モデルで音符に変換して、最低音と最高音を求めたものです。iTunes の試聴音源は主にサビ付近なので「サビ音域」としています。",
    aboutRangeFilter: "変換結果にはゴーストノートが混じるため、先に除外します：0.1 秒未満の音、人の声の範囲（C2〜C7）外の音、前後どちらとも 7 半音以上離れた短い音（よくあるオクターブ誤認）、主旋律から 5 半音以上離れ、間に音がない孤立した音。最低音と最高音は合計 0.25 秒以上か 2 回以上出てくる必要があります。歌声が 4 秒未満の曲は表示しません。",
    aboutRangeMale: "一般的な男性が歌いやすいのは A2〜F#4（lowA〜mid2F#）くらいで、G4〜A4 はやや高く、A#4 以上はかなり高めです。参考：バス E2〜E4、バリトン A2〜A4、テノール C3〜C5。",
    aboutRangeFemale: "一般的な女性が歌いやすいのは F3〜C5（mid1F〜hiC）くらいで、C#5〜E5 はやや高く、F5 以上はかなり高めです。参考：アルト F3〜F5、メゾソプラノ A3〜A5、ソプラノ C4〜C6。",
    aboutRangeNotes: "音名は国際式で、C4 がピアノ中央のド（mid2C）、A4 = 440 Hz、数字が 1 増えると 1 オクターブ上です。カラオケのキー 1 つは半音 1 つ分。男性が女性曲を 1 オクターブ下で、女性が男性曲を 1 オクターブ上で歌うことが多く、アドバイスの「オクターブ上／下」はその意味です。",
    aboutRangeLimits: "30 秒の試聴音源だけを使ったモデルの推定です。デュエット、ハモリ、ラップ、裏声、強いエフェクトで結果がずれることがあり、歌いやすい音域も人によって違います。",
    aboutRangeLicense: "GAME モデルは CC BY-NC-SA 4.0（非商用のみ）、UVR MDX-Net モデルは UVR と作者が示す条件で利用しています。",
    aboutRangeMore: "詳しいルール",
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
    starCta: "GitHub でスターをください",
    starAria: "GitHub でこのプロジェクトにスターを付ける（現在 {n}）",
    authorLabel: "作者",
    sourceCode: "GitHub のソースコード",
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

/* Hashtags from the Essentia models (scraper/hashtags.py). Keys are the models' English
   class names; [zh, ja] translations, English is the key itself (styles keep their
   Discogs names unless listed). */
const TAG_GROUPS = ["genre", "mood", "instrument", "vocal"];
const TAG_NAMES = {
  genre: {
    "Ballad": ["抒情", "バラード"], "Pop Rock": ["流行搖滾", "ポップロック"], "Dance-pop": ["舞曲流行", "ダンスポップ"],
    "Synth-pop": ["合成器流行", "シンセポップ"], "Alternative Rock": ["另類搖滾", "オルタナティブロック"],
    "Indie Rock": ["獨立搖滾", "インディーロック"], "Indie Pop": ["獨立流行", "インディーポップ"],
    "Hard Rock": ["硬式搖滾", "ハードロック"], "Soft Rock": ["軟式搖滾", "ソフトロック"], "Folk Rock": ["民謠搖滾", "フォークロック"],
    "Punk": ["龐克", "パンク"], "Pop Punk": ["流行龐克", "ポップパンク"], "Folk": ["民謠", "フォーク"],
    "Vocal Pop": ["人聲流行", "ボーカルポップ"], "City Pop": ["City Pop", "シティポップ"], "Bubblegum": ["泡泡糖流行", "バブルガムポップ"],
    "House": ["浩室", "ハウス"], "Electro": ["電子", "エレクトロ"], "Trance": ["迷幻舞曲", "トランス"], "Trap": ["陷阱", "トラップ"],
    "Cloud Rap": ["雲端饒舌", "クラウドラップ"], "Pop Rap": ["流行饒舌", "ポップラップ"], "Contemporary R&B": ["當代 R&B", "コンテンポラリー R&B"],
    "RnB/Swing": ["R&B 搖擺", "R&B スウィング"], "Soul": ["靈魂樂", "ソウル"], "Funk": ["放克", "ファンク"], "Disco": ["迪斯可", "ディスコ"],
    "Downtempo": ["慢拍", "ダウンテンポ"], "Ambient": ["氛圍", "アンビエント"], "Acoustic": ["原聲", "アコースティック"],
    "Soundtrack": ["原聲帶", "サウンドトラック"], "Score": ["配樂", "スコア"], "Musical": ["音樂劇", "ミュージカル"],
    "Emo": ["Emo", "エモ"], "Metalcore": ["金屬核", "メタルコア"], "Reggaeton": ["雷鬼動", "レゲトン"],
  },
  mood: {
    happy: ["快樂", "ハッピー"], sad: ["悲傷", "切ない"], relaxed: ["放鬆", "リラックス"], aggressive: ["激烈", "アグレッシブ"],
    party: ["派對", "パーティー"], danceable: ["適合跳舞", "踊れる"], calm: ["平靜", "穏やか"], dark: ["黑暗", "ダーク"],
    dramatic: ["戲劇性", "ドラマチック"], dream: ["夢幻", "ドリーミー"], emotional: ["感性", "エモーショナル"],
    energetic: ["活力", "エネルギッシュ"], epic: ["壯闊", "壮大"], groovy: ["律動", "グルーヴィー"], heavy: ["沉重", "ヘヴィ"],
    hopeful: ["希望", "希望"], love: ["愛情", "ラブ"], melancholic: ["憂鬱", "メランコリック"], powerful: ["強烈", "パワフル"],
    romantic: ["浪漫", "ロマンチック"], sexy: ["性感", "セクシー"], soft: ["柔和", "やさしい"], uplifting: ["振奮", "高揚感"],
  },
  instrument: {
    accordion: ["手風琴", "アコーディオン"], acousticbassguitar: ["原聲貝斯", "アコースティックベース"],
    acousticguitar: ["木吉他", "アコースティックギター"], bass: ["貝斯", "ベース"], bell: ["鐘聲", "ベル"], bongo: ["邦哥鼓", "ボンゴ"],
    brass: ["銅管", "ブラス"], cello: ["大提琴", "チェロ"], clarinet: ["單簧管", "クラリネット"], classicalguitar: ["古典吉他", "クラシックギター"],
    doublebass: ["低音提琴", "コントラバス"], drummachine: ["鼓機", "ドラムマシン"], drums: ["鼓", "ドラム"], electricguitar: ["電吉他", "エレキギター"],
    electricpiano: ["電鋼琴", "エレクトリックピアノ"], flute: ["長笛", "フルート"], guitar: ["吉他", "ギター"], harmonica: ["口琴", "ハーモニカ"],
    harp: ["豎琴", "ハープ"], horn: ["號", "ホルン"], keyboard: ["鍵盤", "キーボード"], oboe: ["雙簧管", "オーボエ"],
    orchestra: ["管弦樂", "オーケストラ"], organ: ["風琴", "オルガン"], percussion: ["打擊樂", "パーカッション"], piano: ["鋼琴", "ピアノ"],
    pipeorgan: ["管風琴", "パイプオルガン"], rhodes: ["Rhodes 電鋼琴", "ローズ"], saxophone: ["薩克斯風", "サックス"], strings: ["弦樂", "ストリングス"],
    synthesizer: ["合成器", "シンセサイザー"], trombone: ["長號", "トロンボーン"], trumpet: ["小號", "トランペット"], viola: ["中提琴", "ヴィオラ"],
    violin: ["小提琴", "バイオリン"],
  },
  vocal: { female: ["女聲", "女性ボーカル"], male: ["男聲", "男性ボーカル"], instrumental: ["純音樂", "インスト"] },
};
const TAG_EN = {
  acousticbassguitar: "acoustic bass", acousticguitar: "acoustic guitar", classicalguitar: "classical guitar",
  doublebass: "double bass", drummachine: "drum machine", electricguitar: "electric guitar", electricpiano: "electric piano",
  pipeorgan: "pipe organ", female: "female vocals", male: "male vocals",
};

function tagLabel(group, key) {
  const names = TAG_NAMES[group]?.[key];
  if (state.lang === "zh" && names) return names[0];
  if (state.lang === "ja" && names) return names[1];
  return TAG_EN[key] || key;
}

function hashtagLine(row) {
  if (!row.tags) return null;
  const line = el("div", { class: "hashtags" });
  for (const group of TAG_GROUPS) {
    for (const key of row.tags[group] || []) {
      const label = tagLabel(group, key);
      line.append(el("span", {
        class: `hashtag ${group}`,
        title: t("tagHint", { group: t(`tagGroup_${group}`), tag: label }),
        text: `#${label}`,
      }));
    }
  }
  return line.childElementCount ? line : null;
}

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

function spotifyLink(row) {
  if (row.spotify) {
    const id = encodeURIComponent(row.spotify);
    return {
      href: `https://open.spotify.com/track/${id}`,
      embed: `https://open.spotify.com/embed/track/${id}?utm_source=generator`,
      label: t("spotifyListen"),
      direct: true,
    };
  }
  return {
    href: "https://open.spotify.com/search/" + encodeURIComponent(songQuery(row)),
    label: t("spotifySearch"),
    direct: false,
  };
}

const YT_ICON =
  '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .6 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2 2.1c2 .5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8ZM9.7 15.1V8.9l5.8 3.1-5.8 3.1Z"/></svg>';

// Brand marks: Apple Music and Spotify glyphs from Simple Icons (CC0 path data); KKBOX app icon from kkbox.com.
// Trademarks belong to their owners and are used only to label links to their services.
const APPLE_ICON =
  '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M23.994 6.124a9.23 9.23 0 00-.24-2.19c-.317-1.31-1.062-2.31-2.18-3.043a5.022 5.022 0 00-1.877-.726 10.496 10.496 0 00-1.564-.15c-.04-.003-.083-.01-.124-.013H5.986c-.152.01-.303.017-.455.026-.747.043-1.49.123-2.193.4-1.336.53-2.3 1.452-2.865 2.78-.192.448-.292.925-.363 1.408-.056.392-.088.785-.1 1.18 0 .032-.007.062-.01.093v12.223c.01.14.017.283.027.424.05.815.154 1.624.497 2.373.65 1.42 1.738 2.353 3.234 2.801.42.127.856.187 1.293.228.555.053 1.11.06 1.667.06h11.03a12.5 12.5 0 001.57-.1c.822-.106 1.596-.35 2.295-.81a5.046 5.046 0 001.88-2.207c.186-.42.293-.87.37-1.324.113-.675.138-1.358.137-2.04-.002-3.8 0-7.595-.003-11.393zm-6.423 3.99v5.712c0 .417-.058.827-.244 1.206-.29.59-.76.962-1.388 1.14-.35.1-.706.157-1.07.173-.95.045-1.773-.6-1.943-1.536a1.88 1.88 0 011.038-2.022c.323-.16.67-.25 1.018-.324.378-.082.758-.153 1.134-.24.274-.063.457-.23.51-.516a.904.904 0 00.02-.193c0-1.815 0-3.63-.002-5.443a.725.725 0 00-.026-.185c-.04-.15-.15-.243-.304-.234-.16.01-.318.035-.475.066-.76.15-1.52.303-2.28.456l-2.325.47-1.374.278c-.016.003-.032.01-.048.013-.277.077-.377.203-.39.49-.002.042 0 .086 0 .13-.002 2.602 0 5.204-.003 7.805 0 .42-.047.836-.215 1.227-.278.64-.77 1.04-1.434 1.233-.35.1-.71.16-1.075.172-.96.036-1.755-.6-1.92-1.544-.14-.812.23-1.685 1.154-2.075.357-.15.73-.232 1.108-.31.287-.06.575-.116.86-.177.383-.083.583-.323.6-.714v-.15c0-2.96 0-5.922.002-8.882 0-.123.013-.25.042-.37.07-.285.273-.448.546-.518.255-.066.515-.112.774-.165.733-.15 1.466-.296 2.2-.444l2.27-.46c.67-.134 1.34-.27 2.01-.403.22-.043.442-.088.663-.106.31-.025.523.17.554.482.008.073.012.148.012.223.002 1.91.002 3.822 0 5.732z"/></svg>';
const SPOTIFY_ICON =
  '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>';
const KKBOX_ICON_SRC = "assets/kkbox.png";

function brandIcon(kind) {
  if (kind === "apple" || kind === "spotify") {
    const span = el("span", { class: "icon" });
    span.innerHTML = kind === "apple" ? APPLE_ICON : SPOTIFY_ICON;
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
  $("#info-credit").textContent = t("infoCredit");
  renderStars();
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
  spotify: {
    service: "Spotify",
    height: 152,
    allow: "autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture",
    sandbox: null,
  },
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

const INFO_ROLES = ["lyricist", "composer", "arranger", "producer"];
const INFO_SRC_URL = {
  ncl: (info) => info.ncl ? `https://isrc-web.ncl.edu.tw/C100/C102/${info.ncl}` : "https://isrc-web.ncl.edu.tw/C200/C200",
  mb: (info) => info.mb ? `https://musicbrainz.org/recording/${info.mb}` : null,
  apple: () => null,
};

function names(list, max = 99) {
  const shown = list.slice(0, max).join(t("nameSep"));
  return list.length > max ? shown + " …" : shown;
}

// Links to licensed lyrics pages only: lyrics are copyrighted, so the site never copies them.
function lyricsLinks(row) {
  const out = el("span", {});
  const link = (href, key) => el("a", { href, target: "_blank", rel: "noopener", text: `${t(key)} ↗` });
  if (row.kkbox) out.append(link(`https://www.kkbox.com/tw/tc/song/${encodeURIComponent(row.kkbox)}`, "lyricsKkbox"));
  else out.append(link("https://www.kkbox.com/tw/tc/search?q=" + encodeURIComponent(songQuery(row)), "lyricsKkboxSearch"));
  if (sourceRegion() === "jp" || /[\u3040-\u30ff]/.test(row.title || "")) {
    out.append(" · ", link("https://www.uta-net.com/search/?Aselect=2&Bselect=3&Keyword=" + encodeURIComponent(row.title || ""), "lyricsUtaNet"));
  }
  return out;
}

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const noteName = (midi) => `${NOTE_NAMES[midi % 12]}${Math.floor(midi / 12) - 1}`;

function keyAdvice(item) {
  if (item.v === "ok") return "";
  if (item.key === undefined) return t("keyNone");
  const parts = [];
  if (item.oct > 0) parts.push(t("octUp"));
  if (item.oct < 0) parts.push(t("octDown"));
  if (item.key > 0) parts.push(t("keyUp", { n: item.key }));
  if (item.key < 0) parts.push(t("keyDown", { n: -item.key }));
  return parts.join(t("keyJoin"));
}

// "Fits any voice", or "Female voice · male high", or both verdicts when neither fits.
function fitText(r) {
  const verdict = (g) => t("voiceVerdict", { g: t(`voice_${g}`), v: t(`v_${r[g].v}`) });
  if (r.fit === "both") return t("fit_both");
  if (r[r.fit]?.v === "ok") return `${t(`fit_${r.fit}`)} · ${verdict(r.fit === "m" ? "f" : "m")}`;
  return ["m", "f"].map(verdict).join(" · ");
}

// Lowest-highest note and who it suits stay in view; per-voice key advice opens from them.
function rangeBlock(row) {
  const r = row.range;
  if (!r) return null;
  const fit = r.fit === "both" || r[r.fit]?.v === "ok" ? r.fit : "none";
  const line = el("span", { class: "info-brief" },
    el("b", { text: t("rangeLabel") }), " ",
    el("span", { class: "range-notes", text: `${noteName(r.low)}–${noteName(r.high)}` }),
    el("span", { class: "sep", "aria-hidden": "true", text: "·" }),
    el("span", { class: `range-fit fit-${fit}`, text: fitText(r) }));
  const more = [];
  const add = (label, value) => more.push(el("dt", { text: label }), el("dd", {}, value));
  add(t("rangeSpan"), t("rangeSemis", { n: r.high - r.low }));
  for (const g of ["m", "f"]) {
    const advice = keyAdvice(r[g]);
    add(t(`voice_${g}`), `${t(`v_${r[g].v}`)}${advice ? t("keyJoin") + advice : ""}`);
  }
  more.push(el("dd", { class: "range-note", text: t("rangeNote") }));
  return el("details", { class: "song-info song-range" },
    el("summary", { title: t("rangeHint") }, line),
    el("dl", { class: "info-more" }, ...more));
}

// Year, label, lyricist and composer stay in view; everything else opens from them.
function infoBlock(row) {
  const info = row.info;
  if (!info) return null;
  const same = info.lyricist && info.composer && info.lyricist.join() === info.composer.join();
  const brief = [];
  if (info.year) brief.push(el("span", { class: "info-year", title: t("infoYear"), text: info.year }));
  if (info.label) brief.push(el("span", { class: "info-label", title: t("infoLabel"), text: info.label }));
  if (same) {
    brief.push(el("span", {}, el("b", { text: t("infoWriter") }), " ", names(info.lyricist, 3)));
  } else {
    if (info.lyricist) brief.push(el("span", {}, el("b", { text: t("infoLyricist") }), " ", names(info.lyricist, 3)));
    if (info.composer) brief.push(el("span", {}, el("b", { text: t("infoComposer") }), " ", names(info.composer, 3)));
  }

  const more = [];
  const add = (key, value) => { if (value) more.push(el("dt", { text: t(key) }), el("dd", {}, value)); };
  if (same) {
    if (info.lyricist.length > 3) add("infoWriter", names(info.lyricist));
  } else {
    if (info.lyricist?.length > 3) add("infoLyricist", names(info.lyricist));
    if (info.composer?.length > 3) add("infoComposer", names(info.composer));
  }
  if (info.arranger) add("infoArranger", names(info.arranger));
  if (info.producer) add("infoProducer", names(info.producer));
  if (info.mix) add("infoMix", names(info.mix));
  if (info.recording) add("infoRecording", names(info.recording));
  if (info.mastering) add("infoMastering", names(info.mastering));
  add("infoAlbum", info.album);
  add("infoReleased", info.released && info.released.length > 4 ? info.released : null);
  add("infoMaker", info.maker);
  add("infoType", info.type);
  add("infoIsrc", info.isrc);
  add("infoCopyright", info.copyright);
  add("infoLyrics", lyricsLinks(row));
  if (info.src?.length) {
    const dd = el("span", {});
    info.src.forEach((s, i) => {
      if (i) dd.append(" · ");
      const url = INFO_SRC_URL[s]?.(info);
      dd.append(url ? el("a", { href: url, target: "_blank", rel: "noopener", text: `${t(`infoSrc_${s}`)} ↗` })
                    : t(`infoSrc_${s}`));
    });
    add("infoSources", dd);
  }
  if (!brief.length && !more.length) return null;

  const line = el("span", { class: "info-brief" });
  brief.forEach((node, i) => { if (i) line.append(el("span", { class: "sep", "aria-hidden": "true", text: "·" })); line.append(node); });
  if (!more.length) return el("div", { class: "song-info" }, line);
  return el("details", { class: "song-info" },
    el("summary", { title: t("infoMore") }, line),
    el("dl", { class: "info-more" }, ...more));
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
  return [head, sub, rangeBlock(row), infoBlock(row), hashtagLine(row)];
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
  for (const [kind, info] of [["apple", appleLink(row)], ["kkbox", kkboxLink(row)], ["spotify", spotifyLink(row)]]) {
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

// Live star count from the GitHub API (60 requests/hour per visitor IP; failures are ignored).
let starCount = null;

async function loadStars() {
  try {
    const res = await fetch("https://api.github.com/repos/Hikari-Tsai/ktv-charts", {
      headers: { Accept: "application/vnd.github+json" },
    });
    if (!res.ok) return;
    const n = (await res.json()).stargazers_count;
    if (Number.isInteger(n)) {
      starCount = n;
      renderStars();
    }
  } catch { /* offline or rate limited: keep the plain button */ }
}

function renderStars() {
  const badge = $("#star-count");
  const button = $("#star-btn");
  if (starCount == null || !badge || !button) return;
  badge.textContent = new Intl.NumberFormat(LOCALE[state.lang]).format(starCount);
  badge.hidden = starCount === 0;
  button.setAttribute("aria-label", t("starAria", { n: starCount }));
}

async function init() {
  state.lang = initialLang();
  for (const btn of document.querySelectorAll(".lang button")) {
    btn.addEventListener("click", () => setLang(btn.dataset.lang));
  }
  applyStaticText();
  loadStars();
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
