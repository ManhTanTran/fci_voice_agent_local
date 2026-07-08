from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", str(text)).lower()
    text = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in text)
    return re.sub(r"\s+", " ", text).strip()
