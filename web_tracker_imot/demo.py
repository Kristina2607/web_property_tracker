from web_tracker_imot.property_search import search_properties
from web_tracker_imot.scrapers.property_scraper_imot import scrape_property_imot
from web_tracker_imot.scrapers.property_scraper_bazar import scrape_property_bazar
from web_tracker_imot.models.property import Property
from web_tracker_imot.gui.main_window import MainWindow

SITES: list[dict[str,str]] = [
    {
        "site": "imot.bg",
        "base_url": "https://www.imot.bg",
        "url": "https://www.imot.bg/obiavi/prodazhbi",
        "link_selector": "a[href*='obiava-']"
    },
    {
        "site": "bazar.bg",
        "base_url": "https://bazar.bg",
        "url": "https://bazar.bg/obiavi/imoti", 
        "link_selector": "a[href*='obiava-']"
    },
]

SCRAPERS: dict[str, callable[[str], Property]]={
    "imot.bg":scrape_property_imot,
    "bazar.bg":scrape_property_bazar
}

def main():
    for site in SITES:
        site_name=site["site"]
        print(f"\n=== {site_name} ===")

        urls = search_properties(
        search_url=site["url"],
        base_url=site["base_url"],
        link_selector=site["link_selector"],
        limit=5)

        scraper=SCRAPERS.get(site_name)
        if scraper is None:
            print(f"No scraper configured for: {site_name}")
            continue

        print("Scraping properties:")
        for url in urls:
            try:
                prop=scraper(url)
                print(prop)
            except Exception as exc:
                print(f"Error {url} -> {exc}")

