"""Offline tests: parsing on small synthetic pages, history ranks, and failure fallback."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import datetime as dt

import scraper.__main__ as main
from scraper import bpm, credits, enrich, hashtags, info, match, singrange, spotify
from scraper.history import History, period_key, song_key
from scraper.sources import dam, joysound, kkbox


class PeriodKeyTest(unittest.TestCase):
    def test_range(self):
        self.assertEqual(period_key("2026/10/26 ~ 2026/11/01", "x"), "2026-10-26_2026-11-01")

    def test_single_and_month(self):
        self.assertEqual(period_key("2026/11/2", "x"), "2026-11-02")
        self.assertEqual(period_key("2026/10", "x"), "2026-10")

    def test_fallback(self):
        self.assertEqual(period_key(None, "2026-11-04"), "2026-11-04")


class HistoryTest(unittest.TestCase):
    def test_previous_ranks(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = History(Path(tmp))
            old = {"id": "w", "period": "a", "period_key": "2026-10-19_2026-10-25",
                   "rows": [{"rank": 1, "title": "A", "artist": "x"},
                            {"rank": 2, "title": "B", "artist": "y"}]}
            h.save("src", old)
            cur = {"id": "w", "period": "b", "period_key": "2026-10-26_2026-11-01",
                   "rows": [{"rank": 1, "title": "B", "artist": "y"},
                            {"rank": 2, "title": "Ａ", "artist": "X"},   # full-width / case differ
                            {"rank": 3, "title": "C", "artist": "z"}]}
            h.fill_previous_ranks("src", cur)
            got = [(r["last_rank"], r["is_new"]) for r in cur["rows"]]
            self.assertEqual(got, [(2, False), (1, False), (None, True)])

    def test_no_history_leaves_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            cur = {"id": "w", "period_key": "2026-11-01", "rows": [{"rank": 1, "title": "A", "artist": "x"}]}
            History(Path(tmp)).fill_previous_ranks("src", cur)
            self.assertIsNone(cur["rows"][0]["last_rank"])
            self.assertIsNone(cur["rows"][0]["is_new"])

    def test_song_key_prefers_number(self):
        self.assertEqual(song_key({"song_no": "1234-56", "title": "A"}), "no:1234-56")


class JoysoundParseTest(unittest.TestCase):
    PAGE = """
    <div>集計期間:<span>2026/10/26 - 2026/11/01</span></div>
    <script type="application/ld+json">{"@graph":[{"@type":"WebPage","mainEntity":{"@type":"ItemList",
      "itemListElement":[
        {"position":2,"item":{"name":"Song &amp; B","byArtist":{"name":"Artist B"},"url":"https://www.joysound.com/web/search/song/2"}},
        {"position":1,"item":{"name":"Song A","byArtist":{"name":"Artist A"},"url":"https://www.joysound.com/web/search/song/1"}}
      ]}}]}</script>"""

    def test_parse(self):
        period, rows = joysound.parse_page(self.PAGE)
        self.assertEqual(period, "2026/10/26 ~ 2026/11/01")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], "Song & B")
        self.assertEqual(rows[1]["song_url"], "https://www.joysound.com/web/search/song/1")


class DamParseTest(unittest.TestCase):
    ROW = ('<li><a class="p-song" href="/karaokesearch/songleaf.html?requestNo={no}">'
           '<div class="p-ranking__num">{rank}</div><div class="p-song__inner">'
           '<h4 class="p-song__title">{title}</h4> <div class="p-song__artist">{artist}</div></div></a></li>')

    def page(self):
        rows = self.ROW.format(no="1111-11", rank=1, title="曲&amp;A", artist="歌手A")
        rows += rows  # PC + mobile duplicate
        rows += self.ROW.format(no="2222-22", rank=2, title="曲B", artist="歌手B")
        return ('<div class="c-section" id="ranking-weekly"><span class="p-section-header__date">2026/11/01 更新</span>'
                + rows + '</div><div class="c-section" id="other"></div>')

    def test_parse_and_dedupe(self):
        sec = dam.parse_sections(self.page())["ranking-weekly"]
        self.assertEqual(sec["updated"], "2026/11/01")
        self.assertEqual([r["song_no"] for r in sec["rows"]], ["1111-11", "2222-22"])
        self.assertEqual(sec["rows"][0]["title"], "曲&A")

    def test_derive_period(self):
        self.assertEqual(dam.derive_period("2026/11/01", "weekly"), "2026/10/25 ~ 2026/10/31")
        self.assertEqual(dam.derive_period("2026/11/04", "daily"), "2026/11/03")
        self.assertEqual(dam.derive_period("2026/11/01", "monthly"), "2026/10/01 ~ 2026/10/31")


class KkboxParseTest(unittest.TestCase):
    PAYLOAD = {"code": 0, "data": {"date": "2026-10-29", "charts": {"song": [
        {"rankings": {"this_period": 2, "last_period": None}, "song_name": "New", "artist_name": "B",
         "song_url": "https://www.kkbox.com/tw/tc/song/b"},
        {"rankings": {"this_period": 1, "last_period": 3}, "song_name": "Up", "artist_name": "A",
         "song_url": "https://www.kkbox.com/tw/tc/song/a"},
    ]}}}

    def test_parse(self):
        date, rows = kkbox.parse(self.PAYLOAD, "song")
        self.assertEqual(date, "2026-10-29")
        self.assertEqual([(r["rank"], r["last_rank"], r["is_new"]) for r in rows], [(1, 3, False), (2, None, True)])

    def test_string_success_code(self):
        payload = dict(self.PAYLOAD, code="0")
        self.assertEqual(len(kkbox.parse(payload, "song")[1]), 2)

    def test_error_code(self):
        with self.assertRaises(RuntimeError):
            kkbox.parse({"code": 104, "data": []}, "song")

    def test_weekly_period_is_friday_to_thursday(self):
        self.assertEqual(kkbox.derive_period("weekly", "2026-10-29"), "2026/10/23 ~ 2026/10/29")
        self.assertEqual(kkbox.derive_period("daily", "2026-11-03"), "2026/11/03")

    def test_titles(self):
        self.assertEqual(kkbox.chart_title("weekly", "song", 297)["zh"], "華語單曲週榜")
        self.assertEqual(kkbox.chart_title("daily", "song", 390)["en"], "Western · Daily")


class MatchTest(unittest.TestCase):
    def test_same_song_across_sources(self):
        self.assertEqual(match.song_key("APT.", "ROSÉ、Bruno Mars"), match.song_key("APT.", "ROSÉ & Bruno Mars"))
        self.assertEqual(match.song_key("對等關係", "李榮浩、張惠妹(aMEI)"), match.song_key("對等關係", "李榮浩、張惠妹"))
        self.assertEqual(match.song_key("沒有人像我一樣 - 影集主題曲", "宇宙人 (Cosmos People)"),
                         match.song_key("沒有人像我一樣", "宇宙人"))

    def test_first_artist(self):
        self.assertEqual(match.first_artist("ROSÉ、Bruno Mars"), "ROSÉ")
        self.assertEqual(match.first_artist("Max Liu"), "Max Liu")

    def test_bad_version(self):
        self.assertTrue(match.is_bad_version("Lemon (Live)"))
        self.assertTrue(match.is_bad_version("怪獣の花唄 (カラオケ)"))
        self.assertFalse(match.is_bad_version("怪獣の花唄 - replica -"))


class ItunesPickTest(unittest.TestCase):
    def r(self, name, artist, genre="Rock", tid=1, coll=""):
        return {"kind": "song", "trackName": name, "artistName": artist, "primaryGenreName": genre,
                "trackId": tid, "collectionName": coll}

    def test_prefers_exact_title_over_alternate_version(self):
        res = [self.r("怪獣の花唄 - replica -", "Vaundy", tid=1), self.r("怪獣の花唄", "Vaundy", tid=2)]
        self.assertEqual(enrich.pick_best(res, "怪獣の花唄", "Vaundy")["trackId"], 2)

    def test_rejects_live_and_wrong_artist(self):
        res = [self.r("Lemon (Live)", "米津玄師", tid=1), self.r("Lemon", "Someone Else", tid=2)]
        self.assertIsNone(enrich.pick_best(res, "Lemon", "米津玄師"))

    def test_matches_artist_with_alias(self):
        res = [self.r("甲乙丙丁Strangers", "李佳薇", genre="Mandopop", tid=9)]
        self.assertEqual(enrich.pick_best(res, "甲乙丙丁Strangers - 你我怎麼兩清", "李佳薇 (Jess Lee)")["trackId"], 9)


class EnrichTest(unittest.TestCase):
    def sites(self):
        return {
            "kkbox": {"charts": [{"id": "a", "rows": [
                {"rank": 1, "title": "甲乙丙丁Strangers - 你我怎麼兩清", "artist": "李佳薇 (Jess Lee)", "kkbox": "KID1"}]}]},
            "holiday": {"charts": [{"id": "b", "rows": [
                {"rank": 3, "title": "甲乙丙丁", "artist": "李佳薇"},
                {"rank": 1, "title": "擱淺", "artist": "周杰倫"}]}]},
        }

    def test_candidates_order_and_retry(self):
        sites = self.sites()
        today = dt.date(2026, 11, 4)
        cache = {match.song_key("擱淺", "周杰倫"): {"status": "none", "checked": "2026-11-01"}}
        keys = [c["key"] for c in enrich.candidates(sites, cache, today)]
        self.assertNotIn(match.song_key("擱淺", "周杰倫"), keys)  # not found 3 days ago: wait
        cache[match.song_key("擱淺", "周杰倫")]["checked"] = "2026-09-01"
        keys = [c["key"] for c in enrich.candidates(sites, cache, today)]
        self.assertEqual(len(keys), 3)
        self.assertEqual(keys[-1], match.song_key("甲乙丙丁", "李佳薇"))  # best rank is 3, so it goes last

    def test_annotate_genre_apple_and_kkbox(self):
        sites = self.sites()
        known = {}
        enrich.collect_kkbox_ids(sites, known)
        cache = {match.song_key("擱淺", "周杰倫"): {"status": "ok", "genre": "Mandopop", "id": 42, "cc": "tw"}}
        counts = enrich.annotate(sites, cache, known)
        holiday = sites["holiday"]["charts"][0]["rows"]
        self.assertEqual(holiday[0]["kkbox"], "KID1")          # prefix match to KKBOX's longer title
        self.assertEqual(holiday[1]["genre"], "Mandopop")
        self.assertEqual(holiday[1]["apple"], "tw/42")
        self.assertNotIn("kkbox", holiday[1])
        self.assertEqual(counts["kkbox"], 2)

    def test_fuzzy_needs_unique_match(self):
        index = {"artist": [("abcde", "X"), ("abcdf", "Y")]}
        self.assertIsNone(enrich.fuzzy_kkbox("abc|artist", index))
        self.assertEqual(enrich.fuzzy_kkbox("abcdeplus|artist", {"artist": [("abcde", "X")]}), "X")


class CacheTest(unittest.TestCase):
    def test_save_never_drops_existing_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            enrich.save_cache(path, {"a": {"status": "ok"}, "b": {"status": "none"}})
            enrich.save_cache(path, {"b": {"status": "ok"}, "c": {"status": "ok"}})  # "a" missing here
            data = enrich.load_cache(path)
            self.assertEqual(set(data), {"a", "b", "c"})
            self.assertEqual(data["b"]["status"], "ok")

    def test_corrupt_cache_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                enrich.save_cache(path, {"a": {"status": "ok"}})
            self.assertEqual(path.read_text(encoding="utf-8"), "{not json")

    def test_missing_cache_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(enrich.load_cache(Path(tmp) / "none.json"), {})


class BpmTest(unittest.TestCase):
    def test_chunk_starts_match_space(self):
        self.assertEqual(bpm.chunk_starts(1000), [-6])
        self.assertEqual(bpm.chunk_starts(1501), [-6, 7])           # 30 s preview: two chunks
        self.assertEqual(bpm.chunk_starts(3000), [-6, 1482, 1506])

    def test_peaks_and_dedupe(self):
        logits = [-1.0] * 100
        for f in (10, 35, 60, 85):
            logits[f] = 2.0
        logits[61] = 2.0  # plateau of two frames -> one beat at their mean
        self.assertEqual(bpm.peaks(logits), [0.2, 0.7, 60.5 / 50, 1.7])

    def test_constant_tempo(self):
        beats = [i * 0.5 for i in range(16)]        # 120 BPM, a downbeat every 4 beats
        down = beats[::4]
        r = bpm.estimate_tempo(beats, down)
        self.assertEqual((r["bpm"], r["mode"], r["signature"]), (120.0, "constant", 4))

    def test_too_few_beats(self):
        self.assertIsNone(bpm.estimate_tempo([1.0], []))

    def test_new_itunes_match_triggers_reanalysis(self):
        sites = {"holiday": {"charts": [{"id": "a", "rows": [{"rank": 1, "title": "Baby", "artist": "Justin Bieber"}]}]}}
        key = match.song_key("Baby", "Justin Bieber")
        itunes = {key: {"status": "ok", "id": 2, "cc": "tw"}}
        done = {key: {"status": "ok", "track": "tw/2", "bpm": 65}}
        self.assertEqual(bpm.candidates(sites, itunes, done, dt.date(2026, 11, 4)), [])
        stale = {key: {"status": "ok", "track": "tw/1", "bpm": 130}}
        self.assertEqual(len(bpm.candidates(sites, itunes, stale, dt.date(2026, 11, 4))), 1)


class RecheckTest(unittest.TestCase):
    def test_suspect_version_is_rechecked_once(self):
        sites = {"holiday": {"charts": [{"id": "a", "rows": [{"rank": 1, "title": "Creep", "artist": "Radiohead"}]}]}}
        key = match.song_key("Creep", "Radiohead")
        cache = {key: {"status": "ok", "name": "Creep (Acoustic)", "checked": "2026-11-01"}}
        self.assertEqual(len(enrich.candidates(sites, cache, dt.date(2026, 11, 4))), 1)
        cache[key]["rechecked"] = "2026-11-03"
        self.assertEqual(enrich.candidates(sites, cache, dt.date(2026, 11, 4)), [])


class FallbackTest(unittest.TestCase):
    def test_failed_job_keeps_previous_chart(self):
        def boom():
            raise RuntimeError("site down")

        fake = mock.Mock()
        fake.SOURCE = {"id": "fake", "name": {"zh": "假"}, "region": "tw", "site_url": "https://example.com/"}
        fake.JOBS = [{"name": "a", "charts": ["a"], "fetch": boom}]
        with tempfile.TemporaryDirectory() as tmp:
            site, hist = Path(tmp) / "site", Path(tmp) / "hist"
            site.mkdir()
            (site / "fake.json").write_text(json.dumps(
                {"charts": [{"id": "a", "title": {"zh": "A"}, "rows": [{"rank": 1, "title": "x"}], "stale": False}]}
            ), encoding="utf-8")
            with mock.patch.object(main, "SITE_DATA", site), mock.patch("sys.stderr"):
                data, ok, total = main.run_source(fake, History(hist))
            self.assertEqual((ok, total), (0, 1))
            self.assertTrue(data["charts"][0]["stale"])
            self.assertEqual(data["charts"][0]["rows"][0]["title"], "x")
            self.assertIn("site down", data["errors"][0])


class HashtagTest(unittest.TestCase):
    def entry(self, **over):
        e = {
            "status": "ok",
            "style": {"Pop---K-pop": 0.6, "Pop---Ballad": 0.4, "Rock---Pop Rock": 0.18, "Pop---Vocal": 0.1},
            "instrument": {"piano": 0.6, "keyboard": 0.5, "drums": 0.5, "strings": 0.4, "voice": 0.9, "flute": 0.36},
            "moodtheme": {"advertising": 0.5, "love": 0.3, "happy": 0.25},
            "binary": {"voice_instrumental": 0.98, "gender": 0.95, "danceability": 0.9, "mood_happy": 0.2,
                       "mood_sad": 0.95, "mood_relaxed": 0.9, "mood_party": 0.1, "mood_aggressive": 0.0},
        }
        e.update(over)
        return e

    def test_rules(self):
        tags = hashtags.select_tags(self.entry())
        # K-pop is regional; Pop Rock is under half of Ballad's score; Top-2 at most.
        self.assertEqual(tags["genre"], ["Ballad"])
        # drums needs 0.6, keyboard is a parent of piano, voice is skipped, Top-3 cap.
        self.assertEqual(tags["instrument"], ["piano", "strings", "flute"])
        # sad then relaxed (danceable conflicts with both); one mood-like theme, not "advertising".
        self.assertEqual(tags["mood"], ["sad", "relaxed", "love"])
        self.assertEqual(tags["vocal"], ["female"])

    def test_sparse_or_unsure_gives_nothing(self):
        e = self.entry(style={"Pop---Ballad": 0.1}, instrument={"piano": 0.2}, moodtheme={},
                       binary={"voice_instrumental": 0.9, "gender": 0.6})
        self.assertEqual(hashtags.select_tags(e), {})
        self.assertEqual(hashtags.select_tags({"status": "none"}), {})
        e = self.entry(binary={"voice_instrumental": 0.1, "gender": 0.95})
        self.assertEqual(hashtags.select_tags(e)["vocal"], ["instrumental"])
        self.assertEqual(hashtags.select_tags(self.entry(style={"Pop---Vocal": 0.3}))["genre"], ["Vocal Pop"])

    def test_annotate_writes_and_clears_tags(self):
        key = match.song_key("擱淺", "周杰倫")
        sites = {"holiday": {"charts": [{"id": "b", "rows": [{"rank": 1, "title": "擱淺", "artist": "周杰倫",
                                                               "tags": {"genre": ["old"]}}]}]}}
        counts = enrich.annotate(sites, {}, {}, tags={key: self.entry()})
        row = sites["holiday"]["charts"][0]["rows"][0]
        self.assertEqual(row["tags"]["genre"], ["Ballad"])
        self.assertEqual(counts["tags"], 1)
        enrich.annotate(sites, {}, {}, tags={})
        self.assertNotIn("tags", row)


class SpotifyTest(unittest.TestCase):
    def test_pick_best_uses_itunes_rules(self):
        items = [
            {"id": "LIVE", "name": "擱淺 (Live)", "artists": [{"name": "周杰倫"}], "album": {"name": "2004 演唱會"}},
            {"id": "OK", "name": "擱淺", "artists": [{"name": "周杰倫"}], "album": {"name": "七里香"}},
            {"id": "OTHER", "name": "擱淺", "artists": [{"name": "別人"}], "album": {"name": "x"}},
            None,
        ]
        self.assertEqual(spotify.pick_best(items, "擱淺", "周杰倫 (Jay Chou)")["_id"], "OK")
        self.assertIsNone(spotify.pick_best(items[2:], "擱淺", "周杰倫"))

    def test_candidates_and_annotate(self):
        key = match.song_key("擱淺", "周杰倫")
        sites = {"holiday": {"charts": [{"id": "b", "rows": [{"rank": 1, "title": "擱淺", "artist": "周杰倫"}]}]}}
        today = dt.date(2026, 11, 5)
        self.assertEqual([c["key"] for c in spotify.candidates(sites, {}, today)], [key])
        fresh_miss = {"status": "none", "checked": "2026-11-01", "v": spotify.MATCH_VERSION}
        self.assertEqual(spotify.candidates(sites, {key: fresh_miss}, today), [])
        old_matcher = {"status": "none", "checked": "2026-11-05"}  # no "v": found by an older matcher
        self.assertEqual(len(spotify.candidates(sites, {key: old_matcher}, today)), 1)
        self.assertEqual(len(spotify.candidates(sites, {key: {"status": "none", "checked": "2026-09-01"}}, today)), 1)
        self.assertEqual(spotify.candidates(sites, {key: {"status": "ok", "id": "X"}}, today), [])
        counts = enrich.annotate(sites, {}, {}, spotify={key: {"status": "ok", "id": "X"}})
        self.assertEqual(sites["holiday"]["charts"][0]["rows"][0]["spotify"], "X")
        self.assertEqual(counts["spotify"], 1)

    def test_pause_file(self):
        now = dt.datetime(2026, 11, 5, 7, 10, tzinfo=dt.timezone.utc)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(spotify, "PAUSE_FILE", Path(tmp) / "p.json"):
            self.assertIsNone(spotify.paused_until(now))
            spotify.pause(now, 85600)
            self.assertGreater(spotify.paused_until(now), now + dt.timedelta(hours=23))
            self.assertIsNone(spotify.paused_until(now + dt.timedelta(days=1)))
            with mock.patch.dict("os.environ", {"SPOTIFY_CLIENT_ID": "id", "SPOTIFY_CLIENT_SECRET": "s"}), \
                    mock.patch.object(spotify, "paused_until", return_value=now), \
                    mock.patch.object(spotify, "get_token") as token, \
                    mock.patch.object(enrich, "apply_files", return_value={}):
                spotify.main([])
            token.assert_not_called()

    def test_main_without_secrets_skips_network(self):
        with mock.patch.dict("os.environ", {"SPOTIFY_CLIENT_ID": "", "SPOTIFY_CLIENT_SECRET": ""}), \
                mock.patch.object(spotify, "get_token") as token, \
                mock.patch.object(enrich, "apply_files", return_value={}) as apply:
            self.assertEqual(spotify.main([]), 0)
        token.assert_not_called()
        apply.assert_called_once()


try:
    import numpy  # noqa: F401
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False


@unittest.skipUnless(HAVE_NUMPY, "numpy not installed")
class EssentiaFrontEndTest(unittest.TestCase):
    def test_mel_filters_have_unit_area(self):
        from scraper import tags
        filters = tags._mel_filters()
        self.assertEqual(filters.shape, (96, 257))
        area = filters.sum(axis=1) * (tags.SR / tags.FRAME)  # weights * bin width (Hz)
        self.assertAlmostEqual(float(area[0]), 1.0, places=3)  # wide-enough bands sum to 1
        self.assertTrue(((area > 0.9) & (area < 1.1)).all())   # narrow ones only roughly

    def test_mdx_stft_round_trip(self):
        import numpy as np
        from scraper import vocal
        x = np.random.default_rng(0).standard_normal((2, vocal.MDX_CHUNK))
        window = vocal._window()
        spec = vocal._stft(x, window)
        self.assertEqual(spec.shape, (2, vocal.N_FFT // 2 + 1, vocal.DIM_T))
        self.assertTrue(np.allclose(vocal._istft(spec, vocal.MDX_CHUNK, window), x, atol=1e-6))

    def test_patching(self):
        import numpy as np
        from scraper import tags
        mel = tags.log_mel(np.zeros(tags.SR * 30, dtype=np.float32))
        self.assertEqual(mel.shape, (1 + (tags.SR * 30 - 512) // 256, 96))
        self.assertTrue(np.allclose(mel, 0))
        self.assertEqual(tags.patches(mel).shape, (29, 128, 96))
        self.assertEqual(tags.patches(mel[:10]).shape, (1, 128, 96))  # short input is padded


class CreditsTest(unittest.TestCase):
    NCL = [
        {"ITEM": 1, "TOPIC": "TWD951562101", "NAME": "曲目名稱:小幸運<br />",
         "ACTION": "表演者:田馥甄<br />作詞者:徐世珍, 吳輝福<br />作曲者:JerryC<br />編曲者:JerryC<br />製作人:呂禎晃, 郭文宗<br />",
         "PRODUCER": "D95華研國際音樂", "aNAME": "我的少女時代", "aSENT_COM": "D95華研國際音樂",
         "aSENT_TIME": "2015-10-21T00:00:00", "apubtype": "電影原聲帶"},
        {"ITEM": 2, "TOPIC": "TWD951562101", "NAME": "曲目名稱:小幸運<br />", "ACTION": "表演者:田馥甄<br />",
         "PRODUCER": "D95華研國際音樂", "aNAME": "小幸运 (单曲)", "aSENT_COM": "D95華研國際音樂",
         "aSENT_TIME": "2015-07-10T00:00:00"},
        {"ITEM": 3, "TOPIC": "TWD951562103", "NAME": "曲目名稱:小幸運(kala)<br />", "ACTION": "表演者:田馥甄<br />",
         "aSENT_TIME": "2015-01-01T00:00:00"},
        {"ITEM": 4, "TOPIC": "TWX831611118", "NAME": "曲目名稱:小幸運<br />", "ACTION": "表演者:玩聲樂團<br />",
         "aSENT_TIME": "2016-09-30T00:00:00"},
    ]

    def test_ncl_parsing(self):
        roles = credits.ncl_roles("表演者:告五人<BR />作詞者:潘雲安/潘燕山<BR />作曲者:潘雲安+潘燕山等<BR />樂團名稱:告五人")
        self.assertEqual(roles, {"performer": ["告五人"], "lyricist": ["潘雲安", "潘燕山"], "composer": ["潘雲安", "潘燕山"]})
        self.assertEqual(credits.ncl_company("K23       相信音樂國際股份有限公司"), "相信音樂國際股份有限公司")
        self.assertEqual(credits.ncl_company("AE3街聲"), "街聲")
        self.assertEqual(credits.ncl_company("EMI百代唱片"), "EMI百代唱片")  # no digit: not a registrant code
        self.assertEqual(credits.ncl_company("禾廣娛樂府份有限公司\t\t"), "禾廣娛樂府份有限公司")
        self.assertEqual(credits.artist_keyword("芒果醬 Mango Jump"), "芒果醬")
        self.assertEqual(credits.artist_keyword("A-Lin"), "A-Lin")

    def test_ncl_pick_takes_original_and_richest_credits(self):
        matches = credits.ncl_pick(self.NCL, "小幸運", "田馥甄 (Hebe)")
        self.assertEqual([m["ITEM"] for m in matches], [2, 1])  # no karaoke, no other performer
        entry = credits.ncl_entry(matches, "2026-11-05")
        self.assertEqual(entry["released"], "2015-07-10")
        self.assertEqual(entry["label"], "華研國際音樂")
        self.assertEqual(entry["credits"]["lyricist"], ["徐世珍", "吳輝福"])
        self.assertEqual(entry["credits"]["producer"], ["呂禎晃", "郭文宗"])
        self.assertEqual(credits.ncl_pick(self.NCL, "小幸運", "別人"), [])

    def test_mb_credits_and_shape(self):
        detail = {"relations": [
            {"type": "producer", "artist": {"name": "n-buna"}},
            {"type": "vocal", "artist": {"name": "suis"}},
            {"type": "performance", "work": {"relations": [
                {"type": "composer", "artist": {"name": "n-buna"}},
                {"type": "lyricist", "artist": {"name": "n-buna"}}]}}]}
        self.assertEqual(credits.mb_credits(detail),
                         {"producer": ["n-buna"], "composer": ["n-buna"], "lyricist": ["n-buna"]})
        rec = {"id": "x", "title": "花に亡霊", "artist-credit": [{"name": "ヨルシカ"}], "releases": [{"title": "盗作"}]}
        self.assertEqual(enrich.pick_best(credits.mb_shape([rec]), "花に亡霊", "ヨルシカ")["_rec"]["id"], "x")

    def test_engineer_roles_and_redo(self):
        roles = credits.ncl_roles("表演者:A<br />錄音員:錄音甲<br />混音師:混音乙<br />")
        self.assertEqual((roles["recording"], roles["mix"]), (["錄音甲"], ["混音乙"]))
        detail = {"relations": [{"type": "mix", "artist": {"name": "福井昌彦"}},
                                {"type": "recording", "artist": {"name": "斎藤孝之"}}]}
        self.assertEqual(credits.mb_credits(detail), {"mix": ["福井昌彦"], "recording": ["斎藤孝之"]})
        today = dt.date(2026, 11, 5)
        self.assertTrue(credits._due({"status": "ok", "v": 1}, today, 2))  # older parser: redo
        self.assertFalse(credits._due({"status": "ok", "v": 2}, today, 2))
        self.assertFalse(credits._due({"status": "none", "v": 2, "checked": "2026-11-01"}, today, 2))
        got = info.build_info(None, {"status": "ok", "credits": {"mix": ["福井昌彦"]}}, None)
        self.assertEqual((got["mix"], got["src"]), (["福井昌彦"], ["mb"]))

    def test_build_info_priority(self):
        ncl = {"status": "ok", "isrc": "TW1", "item": 9, "released": "2015-07-10", "label": "華研國際音樂",
               "credits": {"lyricist": ["徐世珍"], "composer": ["JerryC"]}}
        mb = {"status": "ok", "id": "m", "released": "2015", "credits": {"writer": ["X"], "producer": ["P"]}}
        apple = {"status": "ok", "album": "我的少女時代", "released": "2015-10-21",
                 "copyright": "℗ 2015 HIM International Music Inc."}
        got = info.build_info(ncl, mb, apple)
        self.assertEqual((got["year"], got["released"], got["label"]), ("2015", "2015-07-10", "華研國際音樂"))
        self.assertEqual((got["lyricist"], got["producer"]), (["徐世珍"], ["P"]))
        self.assertEqual(got["src"], ["ncl", "mb", "apple"])
        only_apple = info.build_info(None, {"status": "none"}, apple)
        self.assertEqual((only_apple["label"], only_apple["year"]), ("HIM International Music Inc", "2015"))
        self.assertEqual(only_apple["src"], ["apple"])
        self.assertEqual(info.build_info(None, None, None), {})
        self.assertEqual(info.copyright_holder("℗ 2011 Simco Limited under exclusive licence to Sony Music"),
                         ("2011", "Simco Limited"))

    def test_annotate_adds_info(self):
        key = match.song_key("小幸運", "田馥甄")
        sites = {"holiday": {"charts": [{"id": "b", "rows": [{"rank": 1, "title": "小幸運", "artist": "田馥甄"}]}]}}
        apple = {key: {"status": "ok", "released": "2015-10-21", "copyright": "℗ 2015 HIM"}}
        counts = enrich.annotate(sites, {}, {}, credits=({}, {}, apple))
        self.assertEqual(sites["holiday"]["charts"][0]["rows"][0]["info"]["year"], "2015")
        self.assertEqual(counts["info"], 1)
        self.assertEqual([s["key"] for s in credits.songs(sites, "jp")], [])


class VocalRangeTest(unittest.TestCase):
    @staticmethod
    def phrase(pitches, start=0.0, dur=0.4):
        return [(start + i * dur, dur, float(p)) for i, p in enumerate(pitches)]

    def test_site_zones_match(self):
        """The keyboard view in site/app.js judges key changes with the same zones as the Python advice."""
        import re
        js = (Path(__file__).resolve().parents[1] / "site" / "app.js").read_text(encoding="utf-8")
        found = re.search(r"const VOICE_ZONES = \{ m: \[(.+?)\], f: \[(.+?)\] \};", js)
        self.assertIsNotNone(found)
        parse = lambda text: tuple(int(x) for x in text.split(","))
        self.assertEqual({"m": parse(found[1]), "f": parse(found[2])}, singrange.ZONES)

    def test_note_names(self):
        self.assertEqual(singrange.note_name(60), "C4")
        self.assertEqual(singrange.note_name(69), "A4")
        self.assertEqual(singrange.note_name(45), "A2")

    def test_clean_melody_keeps_its_extremes(self):
        notes = self.phrase([55, 57, 59, 60, 62, 64, 62, 60, 59, 57, 55, 57, 59, 60, 64, 62])
        r = singrange.filter_notes(notes)
        self.assertEqual((r["low"], r["high"], r["dropped"]), (55, 64, 0))

    def test_octave_spike_inside_a_phrase_is_dropped(self):
        notes = self.phrase([60, 62, 62, 74, 62, 60, 59, 60, 62, 60, 59, 57, 59, 60, 62, 60])
        notes[3] = (notes[3][0], 0.2, 74.0)  # short octave error between two D4s
        self.assertEqual(singrange.filter_notes(notes)["high"], 62)

    def test_intro_bass_cut_off_from_the_melody_is_dropped(self):
        intro = self.phrase([38, 43, 37, 38], dur=0.45)  # D2 G2 C#2 D2: bass in the intro
        melody = self.phrase([50, 55, 57, 59, 59, 57, 55, 54, 55, 59, 62, 62, 60, 59, 55, 57], start=2.0)
        r = singrange.filter_notes(intro + melody)
        self.assertEqual((r["low"], r["high"]), (50, 62))
        self.assertEqual(r["dropped"], 4)

    def test_brief_extreme_needs_support(self):
        melody = self.phrase([55, 57, 59, 60, 59, 57, 55, 57, 59, 60, 59, 57, 55, 57])
        melody.append((melody[-1][0] + 0.4, 0.15, 63.0))  # one 0.15 s E-flat at the end
        self.assertEqual(singrange.filter_notes(melody)["high"], 60)
        melody.append((melody[-1][0] + 0.4, 0.15, 63.0))  # sung twice: it counts
        self.assertEqual(singrange.filter_notes(melody)["high"], 63)

    def test_too_little_singing_gives_nothing(self):
        self.assertIsNone(singrange.filter_notes(self.phrase([60, 62, 64, 65, 67])))
        self.assertIsNone(singrange.filter_notes([(i * 0.1, 0.05, 60.0) for i in range(100)]))  # all blips

    def test_advice(self):
        a = singrange.advise(50, 62)  # D3-D4
        self.assertEqual((a["fit"], a["m"]["v"], a["f"]["v"]), ("m", "ok", "low"))
        self.assertEqual((a["f"]["key"], a["f"]["oct"]), (-2, 12))  # an octave up, two keys down
        a = singrange.advise(58, 77)  # A#3-F5
        self.assertEqual((a["fit"], a["f"]["v"], a["m"]["v"]), ("f", "vhigh", "vhigh"))
        self.assertEqual((a["f"]["key"], a["f"]["oct"]), (-5, 0))
        self.assertEqual(singrange.advise(55, 64)["fit"], "both")
        self.assertEqual(singrange.advise(40, 80)["m"], {"v": "wide"})  # too wide for any key

    def test_annotate_adds_range(self):
        key = match.song_key("晴天", "周杰倫")
        sites = {"holiday": {"charts": [{"id": "b", "rows": [{"rank": 1, "title": "晴天", "artist": "周杰倫"}]}]}}
        counts = enrich.annotate(sites, {}, {}, ranges={key: {"status": "ok", "low": 50, "high": 62}})
        row = sites["holiday"]["charts"][0]["rows"][0]
        self.assertEqual((row["range"]["low"], row["range"]["high"], row["range"]["fit"]), (50, 62, "m"))
        self.assertEqual(counts["range"], 1)
        enrich.annotate(sites, {}, {}, ranges={key: {"status": "none"}})
        self.assertNotIn("range", row)


if __name__ == "__main__":
    unittest.main()
