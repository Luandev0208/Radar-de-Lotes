from radar_lotes.parsing import (
    extract_cab_cam, extract_contacts, extract_dimensions, extract_topography,
    extract_walled, find_city, find_neighborhood, location_is_approximate,
    maps_query, parse_price,
)


def test_price_formats():
    expected = 395000
    for value in ("395000", "395000.00", "395000,00", "R$ 395.000", "R$ 395.000,00", "395 mil"):
        assert parse_price(value) == expected
    assert parse_price("420 mil") == 420000


def test_dynamic_neighborhood_and_metro_city():
    assert find_neighborhood("Terreno em Contagem") == ""
    assert find_neighborhood("Terreno no bairro Nacional, Contagem") == "Nacional"
    assert find_neighborhood("Lote no Jardim Riacho", candidates=["Jardim Riacho"]) == "Jardim Riacho"
    assert find_city("Lote em Ribeirão das Neves - MG") == "Ribeirão das Neves"
    assert find_city("Terreno em São Paulo") == ""


def test_safe_contacts_and_property_details():
    text = "Terreno plano e murado, 12x30. CAB: 1,0. CAM: 2,0. WhatsApp (31) 99999-9999 contato@imob.com.br"
    result = extract_contacts(text)
    assert "99999-9999" in result["whatsapp"]
    assert result["email"] == "contato@imob.com.br"
    assert extract_dimensions(text) == "12 x 30"
    assert extract_topography(text) == "Plano"
    assert extract_walled(text) == "Sim"
    assert extract_cab_cam(text) == ("1.0", "2.0")


def test_maps_prefers_coordinates_when_available():
    url = maps_query("Rua errada, 10", "Nacional", "Contagem", "MG", -19.9001234, -44.0505678)
    assert "-19.9001234%2C-44.0505678" in url
    assert "Rua+errada" not in url
    assert not location_is_approximate("", -19.9, -44.05)


def test_maps_address_is_constrained_to_mg_brazil():
    url = maps_query("Rua das Flores, 120", "Nacional", "Contagem", "MG")
    assert "Rua+das+Flores" in url
    assert "Nacional" in url
    assert "Contagem" in url
    assert "MG" in url
    assert "Brasil" in url
    assert not location_is_approximate("Rua das Flores, 120")


def test_maps_refuses_ambiguous_location_without_city():
    assert maps_query("", "Centro", "", "MG") == ""
