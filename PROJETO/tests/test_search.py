from radar_lotes.models import Listing
from radar_lotes.search import SearchFilters


def test_filters_are_dynamic_and_allow_empty_values():
    filters = SearchFilters.from_dict({
        "city": "Contagem",
        "neighborhoods": ["Nacional", "Arvoredo"],
        "max_price": 420000,
        "min_area": 350,
        "max_area": 380,
    })
    ok, missing = filters.match(Listing("Lote", "Nacional", city="Contagem", price=395000, area=360))
    assert ok and missing == []
    ok, _ = filters.match(Listing("Lote", "Nacional", city="Contagem", price=500000, area=360))
    assert not ok


def test_unknown_data_is_kept_for_confirmation_instead_of_invented():
    filters = SearchFilters.from_dict({"city": "Contagem", "max_price": 420000, "min_area": 350})
    ok, missing = filters.match(Listing("Lote", "", city="Contagem"))
    assert ok
    assert "preço" in missing and "área" in missing


def test_search_terms_follow_user_neighborhoods():
    filters = SearchFilters(city="Contagem", neighborhoods=("Jardim Riacho", "Nacional"))
    terms = " ".join(filters.search_terms())
    assert "Jardim Riacho" in terms and "Nacional" in terms
