from bs4 import BeautifulSoup
from web_tracker_imot.utils import extract_value_by_label


def test_extract_value_by_label_finds_next_line() -> None:
    html = """
    <html><body>
      <div>Квадратура</div>
      <div>87 кв. м.</div>
      <div>Цена на кв.м.</div>
      <div>5690 €/кв. м.</div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    assert extract_value_by_label(soup, "Квадратура") == "87 кв. м."
    assert extract_value_by_label(soup, "Цена на кв.м.") == "5690 €/кв. м."


def test_extract_value_by_label_returns_none_when_missing() -> None:
    html = "<html><body><div>Нещо друго</div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    assert extract_value_by_label(soup, "Квадратура") is None