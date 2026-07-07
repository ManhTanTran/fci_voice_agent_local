"""Tien ich chung: an dai so PII truoc khi ghi ra file commit duoc."""
import re

_DIGITS = ["một","hai","ba","bốn","năm","sáu","bảy","tám","chín","không","mười"]
_RUN = re.compile(r"(?:%s)(?:\s+(?:%s)){3,}" % ("|".join(_DIGITS), "|".join(_DIGITS)))


def mask_digits(text: str) -> str:
    """Thay day >=4 tu chu so lien tiep bang placeholder — chong lo so DT/CCCD vao git."""
    if not text:
        return text
    return _RUN.sub("«[dãy số ẩn]»", text)
