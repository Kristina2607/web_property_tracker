from web_tracker_imot.property_search import search_properties


class DummyResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def raise_for_status(self) -> None:
        return


def test_search_properties_collects_links_and_applies_limit(monkeypatch) -> None:
    html = """
    <html><body>
      <a href="/obiava-111">A</a>
      <a href="/obiava-222">B</a>
      <a href="/obiava-333">C</a>
      <a href="/obiava-444">D</a>
    </body></html>
    """.encode("utf-8")

    def fake_get(_url, headers=None, timeout=None):
        return DummyResponse(html)

    monkeypatch.setattr("web_tracker_imot.property_search.requests.get", fake_get)

    urls = search_properties(
        search_url="https://example.com/search",
        base_url="https://example.com",
        link_selector="a[href*='obiava-']",
        limit=2,
    )

    assert len(urls) >= 2
    assert "obiava-111" in urls[0]
    assert "obiava-222" in urls[1]
    assert urls[0].startswith("https://example.com")
    assert "obiava-111" in urls[0]