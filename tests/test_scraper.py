"""Offline tests: parsing on small synthetic pages, history ranks, and failure fallback."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import datetime as dt

import scraper.__main__ as main
from scraper import enrich, match
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


if __name__ == "__main__":
    unittest.main()
