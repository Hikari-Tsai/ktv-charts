"""Each source module exposes SOURCE (metadata) and JOBS (list of fetch jobs).

A job is {"name": str, "charts": [chart ids it produces], "fetch": callable -> list[chart]}.
A chart is {"id", "title", "period", "source_url", "prev_from": "site"|"history", "rows": [...]}.
A row is {"rank", "title", "artist", "song_no"?, "song_url"?, "last_rank"?, "is_new"?}.
"""

from . import cashbox, dam, holiday, joysound

ALL = [holiday, cashbox, joysound, dam]
