from web_tracker_imot.scrapers.property_scraper_imot import scrape_property_imot

class DummyResponse:
    def __init__(self, html: bytes):
        self.content = html

    def raise_for_status(self):
        pass


def test_scrape_property_imot_basic(monkeypatch) -> None:
    html = """
    <html>
      <head><title>Test title / something</title></head>
      <body>
        <div class="cena">123 000 €</div>
        <div class="location">Sofia</div>
        <div class="adParams">
            <div>Площ <strong>80</strong></div>
        </div>
      </body>
    </html>
    """.encode("utf-8")

    def fake_get(url, headers=None, timeout=None):
        return DummyResponse(html)

    monkeypatch.setattr(
        "web_tracker_imot.scrapers.property_scraper_imot.requests.get",
        fake_get,
    )

    prop = scrape_property_imot("https://fake")

    assert prop.price == "123 000 €"
    assert prop.location == "Sofia"
    assert prop.area == "80"
    assert "Test title" in prop.title