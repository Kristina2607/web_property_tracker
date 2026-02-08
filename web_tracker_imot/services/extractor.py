import requests
from bs4 import BeautifulSoup
from typing import Callable

from web_tracker_imot.models.tracked_imot import CriterionType, TrackedItem
from web_tracker_imot.scrapers.property_scraper_bazar import scrape_property_bazar
from web_tracker_imot.scrapers.property_scraper_imot import scrape_property_imot
from web_tracker_imot.utils import extract_value_by_label

HEADERS: dict[str,str] = {"User-Agent": "Mozilla/5.0"}
TIMEOUT_SECONDS: float = 15.0

Fetcher=Callable[[str], bytes]

class ExtractError(Exception):
    pass

def _fetch_generic(url:str) -> bytes:
    resp=requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.content

SITE_FETCHERS: dict[str, Fetcher]={
    "imot.bg": _fetch_generic,
    "bazar.bg": _fetch_generic
}

def _soup_from_html(html: bytes) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser", from_encoding="utf-8")

def _short_title(text: str) -> str:
    text = text.split("::", maxsplit=1)[0].strip()
    text = text.split("/", maxsplit=1)[0].strip()
    return text

def extract_value(item: TrackedItem) -> str:
    fetcher=SITE_FETCHERS.get(item.site)
    if fetcher is None:
        raise ExtractError(f"Unsupported site: {item.site}")
    
    try:
        html = fetcher(item.url)
    except Exception:
        return "ERROR"
    soup=_soup_from_html(html)

    crit_raw = item.criterion_value.strip()
    crit=crit_raw.lower()

    if crit.startswith("preset:"):
        preset_name = crit.split(":", maxsplit=1)[1].strip()

        try:
            if item.site == "imot.bg":
                prop = scrape_property_imot(item.url)
            elif item.site == "bazar.bg":
                prop = scrape_property_bazar(item.url)
            else:
                return "NOT FOUND"
        except Exception:
            return "ERROR"
        
        if preset_name == "price":
            return prop.price
        if preset_name == "title":
            return prop.title
        if preset_name == "location":
            return prop.location
        if preset_name == "area":
            return prop.area
        if preset_name == "psm":
            if item.site == "bazar.bg":
                return extract_value_by_label(soup, "Цена на кв.м.") or "NOT FOUND"
            return "N/A"
        return "NOT FOUND"

    if item.criterion_type==CriterionType.CSS:
        selector=crit_raw
        if not selector:
            raise ExtractError("Empty CSS selector.")
        
        el=soup.select_one(selector)
        if el is None:
            return "NOT FOUND"
        
        text=el.get_text(" ", strip=True)
        if not text:
            return "EMPTY"
        
        if selector == "title":
            text = _short_title(text)

        return text

    if item.criterion_type == CriterionType.KEYWORD:
        keyword=item.criterion_value.strip()
        if not keyword:
            raise ExtractError("Empty keyword")
        
        page_text = soup.get_text("\n", strip=True)
        idx = page_text.lower().find(keyword.lower())
        if idx == -1:
            return "NOT FOUND"

        start = max(0, idx - 40)
        end = min(len(page_text), idx + 80)
        snippet = page_text[start:end].replace("\n", " ")
        return f"...{snippet}..."
    
    raise ExtractError(f"Unsupported criterion type: {item.criterion_type}")