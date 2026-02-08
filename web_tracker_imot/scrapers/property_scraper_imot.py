import requests
from bs4 import BeautifulSoup
from web_tracker_imot.models.property import Property

HEADERS: dict[str,str] = {"User-Agent": "Mozilla/5.0"}
TIMEOUT_SECONDS:float=15.0

def scrape_property_imot(url:str) -> Property:
    response=requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    soup=BeautifulSoup(response.content, "html.parser", from_encoding='utf-8')

    price_el=soup.select_one(".cena")
    price = price_el.text.strip() if price_el else "No price"

    location_el=soup.select_one(".location")
    location=location_el.text.strip() if location_el else "No location"

    area="Unknown area"
    for div in soup.select(".adParams div"):
        if "Площ" in div.text:
            strong=div.find("strong")
            if strong:
                area=strong.text.strip()
            break

    raw_title = soup.title.get_text(strip=True) if soup.title else "No title"
    title = raw_title.split("/")[0].strip() if "/" in raw_title else raw_title
    
    return Property(
        title=title, 
        price=price, 
        location=location, 
        area=area,
        url=url)

