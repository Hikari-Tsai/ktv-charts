"""Offline tests: parsing on small synthetic pages, history ranks, and failure fallback."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scraper.__main__ as main
from scraper.history import History, period_key, song_key
from scraper.sources import dam, joysound


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
