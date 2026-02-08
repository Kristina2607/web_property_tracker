import pytest

from web_tracker_imot.models.tracked_imot import TrackedItem, CriterionType
from web_tracker_imot.services import extractor


def _item(
    *,
    site: str = "imot.bg",
    crit_type: CriterionType = CriterionType.CSS,
    crit_value: str = ".cena",
) -> TrackedItem:
    return TrackedItem(
        id="1",
        site=site,
        url="https://example.com/x",
        criterion_type=crit_type,
        criterion_value=crit_value,
        check_interval_sec=60,
        email_notify=False,
    )


def test_css_extracts_text(monkeypatch) -> None:
    html = "<html><body><div class='cena'>123 000 €</div></body></html>".encode("utf-8")
    extractor.SITE_FETCHERS["imot.bg"] = lambda _url: html

    out = extractor.extract_value(_item(crit_type=CriterionType.CSS, crit_value=".cena"))
    assert "123" in out


def test_css_empty_selector_raises() -> None:
    extractor.SITE_FETCHERS["imot.bg"] = lambda _url: b"<html></html>"
    with pytest.raises(extractor.ExtractError):
        extractor.extract_value(_item(crit_type=CriterionType.CSS, crit_value="   "))


def test_css_title_is_short() -> None:
    html = """
    <html>
      <head><title>Long title / something :: imot.bg Обява 123</title></head>
      <body></body>
    </html>
    """.encode("utf-8")
    extractor.SITE_FETCHERS["imot.bg"] = lambda _url: html

    out = extractor.extract_value(_item(crit_type=CriterionType.CSS, crit_value="title"))
    assert "Long title" in out
    assert "::" not in out
    assert "/" not in out


def test_keyword_found_returns_snippet() -> None:
    html = "<html><body>Hello Sofia center</body></html>".encode("utf-8")
    extractor.SITE_FETCHERS["imot.bg"] = lambda _url: html

    out = extractor.extract_value(_item(crit_type=CriterionType.KEYWORD, crit_value="Sofia"))
    assert "Sofia" in out


def test_keyword_not_found() -> None:
    html = "<html><body>Hello world</body></html>".encode("utf-8")
    extractor.SITE_FETCHERS["imot.bg"] = lambda _url: html

    out = extractor.extract_value(_item(crit_type=CriterionType.KEYWORD, crit_value="Sofia"))
    assert out == "NOT FOUND"


def test_keyword_empty_raises() -> None:
    extractor.SITE_FETCHERS["imot.bg"] = lambda _url: b"<html></html>"
    with pytest.raises(extractor.ExtractError):
        extractor.extract_value(_item(crit_type=CriterionType.KEYWORD, crit_value=""))


def test_preset_price_uses_scraper(monkeypatch) -> None:
    class P:
        title = "T"
        price = "100 €"
        location = "Sofia"
        area = "50"

    monkeypatch.setattr("web_tracker_imot.services.extractor.scrape_property_imot", lambda _url: P())

    out = extractor.extract_value(_item(site="imot.bg", crit_type=CriterionType.CSS, crit_value="preset:price"))
    assert out == "100 €"


def test_preset_psm_bazar_uses_label(monkeypatch) -> None:
    html = """
    <html><body>
      <div>Цена на кв.м.</div>
      <div>5690 €/кв. м.</div>
    </body></html>
    """.encode("utf-8")
    extractor.SITE_FETCHERS["bazar.bg"] = lambda _url: html

    class P:
        title = "T"
        price = "P"
        location = "L"
        area = "A"

    monkeypatch.setattr("web_tracker_imot.services.extractor.scrape_property_bazar", lambda _url: P())

    out = extractor.extract_value(_item(site="bazar.bg", crit_type=CriterionType.CSS, crit_value="preset:psm"))
    assert "5690" in out


def test_unsupported_site_raises() -> None:
    item = _item(site="unknown.site", crit_type=CriterionType.CSS, crit_value=".x")
    with pytest.raises(extractor.ExtractError):
        extractor.extract_value(item)