from web_tracker_imot.scrapers.property_scraper_bazar import scrape_property_bazar


class DummyResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def raise_for_status(self) -> None:
        return


def test_scrape_property_bazar_estimates_price(monkeypatch) -> None:
    html = """
    <html><head>
      <meta property="og:title" content="Продава 3-стаен, София, Център">
    </head><body>
      <div>Квадратура</div>
      <div>87 кв. м.</div>
      <div>Цена на кв.м.</div>
      <div>5690 €/кв. м.</div>
    </body></html>
    """.encode("utf-8")

    def fake_get(_url, headers=None, timeout=None):
        return DummyResponse(html)

    monkeypatch.setattr("web_tracker_imot.scrapers.property_scraper_bazar.requests.get", fake_get)

    prop = scrape_property_bazar("https://bazar.bg/obiava-123")
    assert prop.area.startswith("87")
    assert "€" in prop.price  
    assert "Център" in prop.location