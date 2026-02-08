from bs4 import BeautifulSoup, Tag

def extract_value_by_label(soup: BeautifulSoup, label_text:str) -> str|None :
    label = label_text.strip().lower()
    lines = [ln.strip() for ln in soup.get_text("\n", strip=True).splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if ln.lower() == label:
            return lines[i + 1] if i + 1 < len(lines) else None
    return None