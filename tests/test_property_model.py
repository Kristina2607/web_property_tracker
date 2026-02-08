from web_tracker_imot.models.property import Property

def test_property_str_contains_fields() -> None:
    p = Property(title="T", price="100", location="Sofia", area="50", url="u")
    s = str(p)
    assert "T" in s
    assert "100" in s