from radar_lotes.models import Listing
from radar_lotes.search import SearchFilters


def test_blank_city_means_bh_metro_not_brazil():
    filters = SearchFilters()
    ok, _ = filters.match(Listing("Lote em Contagem", "Nacional", city="Contagem", price=395000))
    assert ok
    ok, _ = filters.match(Listing("Lote em São Paulo", "Centro", city="São Paulo", price=395000))
    assert not ok
    ok, _ = filters.match(Listing("Lote sem localização", "", city="", price=395000))
    assert not ok


def test_specific_city_and_filters():
    filters = SearchFilters.from_dict({
        "city": "Contagem",
        "neighborhoods": ["Nacional", "Arvoredo"],
        "max_price": 420000,
        "min_area": 350,
        "max_area": 380,
        "require_price": True,
    })
    ok, missing = filters.match(Listing("Lote", "Nacional", city="Contagem", price=395000, area=360))
    assert ok and missing == []
    ok, _ = filters.match(Listing("Lote", "Nacional", city="Contagem", price=500000, area=360))
    assert not ok


def test_price_is_required_by_default():
    filters = SearchFilters(city="Contagem")
    ok, reason = filters.match(Listing("Lote", "Nacional", city="Contagem", price=None))
    assert not ok and "preço" in reason
    relaxed = SearchFilters(city="Contagem", require_price=False)
    ok, _ = relaxed.match(Listing("Lote", "Nacional", city="Contagem", price=None))
    assert ok


def test_search_terms_are_constrained_to_minas_gerais():
    filters = SearchFilters(neighborhoods=("Nacional",))
    terms = " ".join(filters.search_terms())
    assert "Belo Horizonte Região Metropolitana MG" in terms
    assert "Minas Gerais" in terms
    assert "R$" in terms
