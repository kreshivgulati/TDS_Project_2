import base64
import json
from typing import Optional


def safe_json_loads(data: str) -> Optional[dict]:
    """
    Safely load JSON. Returns None instead of raising exceptions.
    """
    try:
        return json.loads(data)
    except Exception:
        return None


def extract_base64_json(encoded: str) -> Optional[dict]:
    """
    Detect base64-encoded JSON payloads.
    Returns decoded dict or None.
    """
    try:
        # Fix missing padding if needed
        missing_padding = len(encoded) % 4
        if missing_padding:
            encoded += "=" * (4 - missing_padding)

        decoded_bytes = base64.b64decode(encoded)
        decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
        return safe_json_loads(decoded_str)
    except Exception:
        return None


def is_base64(s: str) -> bool:
    """
    Quick heuristic to check if a string is likely base64.
    """
    try:
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False


def extract_table_from_html(html: str):
    """
    Lightweight HTML table extractor using BeautifulSoup.
    Returns list of rows, each row is list of cell strings.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return None

    rows = []
    for tr in table.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
        if cells:
            rows.append(cells)

    return rows


def url_join(base: str, relative: str) -> str:
    """
    Combine base URL and relative URL safely.
    """
    from urllib.parse import urljoin
    return urljoin(base, relative)
