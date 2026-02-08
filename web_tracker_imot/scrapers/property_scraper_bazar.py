
import re
import requests
from bs4 import BeautifulSoup
from web_tracker_imot.utils import extract_value_by_label
from web_tracker_imot.models.property import Property

HEADERS: dict[str,str] = {"User-Agent": "Mozilla/5.0", "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.8"}
TIMEOUT_SECONDS: float = 15.0

def _first_number(text: str) -> float | None:
    m = re.search(r"(\d+(?:[\s.,]\d+)*)", text)
    if not m:
        return None
    num = m.group(1).replace(" ", "").replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return None
    

def scrape_property_bazar(url:str) -> Property:
    response=requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    soup=BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")

    title_meta = soup.find("meta", property="og:title")
    title = title_meta["content"].strip() if title_meta and title_meta.get("content") else "No title"

    location="Unknown location"
    if "," in title:
        location=title.split(",", maxsplit=1)[1].strip()

    area=extract_value_by_label(soup, "Квадратура") or "Unknown area"
    psm = extract_value_by_label(soup, "Цена на кв.м.") or ""

    price="No price"

    price_meta = soup.find("meta", property="og:price")
    if price_meta and price_meta.get("content"):
        price = price_meta["content"].strip()
    else:
        area_num = _first_number(area)
        psm_num = _first_number(psm)
        if area_num and psm_num:
            total = area_num * psm_num
            price = f"{total:,.0f} € (est.)".replace(",", " ")


    return Property(
        title=title, 
        price=price, 
        location=location, 
        area=area,
        url=url)
