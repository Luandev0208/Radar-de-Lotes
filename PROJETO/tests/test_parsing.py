from radar_lotes.parsing import (
    extract_cab_cam, extract_contacts, extract_dimensions, extract_topography,
    extract_walled, find_neighborhood, location_is_approximate, maps_query, parse_price,
)


def test_price_formats():
    expected = 395000
    for value in ("395000", "395000.00", "395000,00", "R$ 395.000", "R$ 395.000,00", "395 mil"):
        assert parse_price(value) == expected
    assert parse_price("420 mil") == 420000


def test_dynamic_neighborhood_candidates():
    assert find_neighborhood("Terreno em Contagem") == ""
    assert find_neighborhood("Terreno no bairro Nacional, Contagem") == "Nacional"
    assert find_neighborhood("Lote no Jardim Riacho", candidates=["Jardim Riacho"]) == "Jardim Riacho"


def test_safe_contacts_and_property_details():
    text = "Terreno plano e murado, 12x30. CAB: 1,0. CAM: 2,0. WhatsApp (31) 99999-9999 contato@imob.com.br"
    result = extract_contacts(text)
    assert "99999-9999" in result["whatsapp"]
    assert result["email"] == "contato@imob.com.br"
    assert extract_dimensions(text) == "12 x 30"
    assert extract_topography(text) == "Plano"
    assert extract_walled(text) == "Sim"
    assert extract_cab_cam(text) == ("1.0", "2.0")


def test_maps_complete_address_is_specific_and_not_duplicated():
    url = maps_query("Rua das Flores, 120, Nacional, Contagem", "Nacional", "Contagem", "MG")
    assert "Rua+das+Flores" in url
    assert "120" in url
    assert url.count("Nacional") == 1
    assert url.count("Contagem") == 1
    assert not location_is_approximate("Rua das Flores, 120")


def test_maps_incomplete_address_is_marked_approximate():
    url = maps_query("Rua das Flores", "Nacional", "Contagem", "MG")
    assert "Rua+das+Flores" in url
    assert "Nacional" in url
    assert location_is_approximate("Rua das Flores")
