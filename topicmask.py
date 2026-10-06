"""Topic-word masking for the step-3 vocabulary test (PLAN.md change log, 2026-10-06).

Question: is industry recoverable because the text names the industry (vocabulary), or from
something less obvious? The lexicon below was written before any masked run, one list per
industry, and ALL four lists are masked in every snippet, so masking never depends on an
author's label. A word is masked when it equals a stem of 3 letters or fewer, or starts with
a longer stem. Masked words become the token "[...]" and still count toward the word total,
so the slice lengths match the unmasked sweep exactly.
"""

import re

LEXICON = {
    "Education": [
        "teach", "teacher", "school", "student", "class", "classroom", "college", "universit",
        "professor", "lectur", "homework", "exam", "grade", "grading", "campus", "curricul",
        "educat", "tutor", "principal", "kindergarten", "semester", "degree", "academ", "lesson",
        "faculty", "scholar", "pupil", "diploma", "graduat", "freshman", "sophomore", "thesis",
    ],
    "Technology": [
        "comput", "software", "code", "coding", "program", "linux", "java", "server", "internet",
        "web", "website", "network", "database", "hardware", "windows", "microsoft", "google",
        "tech", "digital", "online", "email", "e-mail", "browser", "html", "perl", "unix",
        "geek", "hack", "cpu", "pc", "bug", "debug", "download", "upload", "wireless", "laptop",
        "keyboard", "engineer", "developer", "app", "data", "system",
    ],
    "Arts": [
        "art", "artist", "artistic", "paint", "canvas", "gallery", "museum", "sculpt", "poem",
        "poet", "poetry", "music", "musician", "band", "guitar", "song", "lyric", "album",
        "concert", "drum", "piano", "theat", "actor", "actress", "stage", "dance", "film",
        "movie", "cinema", "novel", "writer", "writing", "draw", "sketch", "design", "photograph",
        "creative", "perform",
    ],
    "Communications-Media": [
        "radio", "televis", "tv", "news", "newspaper", "journal", "reporter", "editor", "magazine",
        "media", "broadcast", "publish", "press", "anchor", "channel", "station", "advertis",
        "marketing", "publicity", "public relations", "pr", "communicat", "interview", "headline",
        "article", "column", "producer", "camera", "video", "commercial", "film crew",
    ],
}

_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_STEMS = sorted({s for stems in LEXICON.values() for s in stems if " " not in s}, key=len)
_SHORT = {s for s in _STEMS if len(s) <= 3}
_LONG = tuple(s for s in _STEMS if len(s) > 3)
MASK = "[...]"


def is_topic_word(token: str) -> bool:
    w = _WORD.search(token)
    if not w:
        return False
    low = w.group(0).lower().strip("'-")
    return low in _SHORT or low.startswith(_LONG)


def mask_words(words):
    """Return (masked words, number masked). Word count is preserved."""
    out, n = [], 0
    for tok in words:
        if is_topic_word(tok):
            out.append(MASK)
            n += 1
        else:
            out.append(tok)
    return out, n
