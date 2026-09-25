from radar_lotes.parsing import extract_contacts, find_neighborhood, maps_query, parse_price


def test_price_formats():
    expected = 395000
    for value in ("395000", "395000.00", "395000,00", "R$ 395.000", "R$ 395.000,00", "395 mil"):
        assert parse_price(value) == expected
    assert parse_price("420 mil") == 420000


def test_city_is_not_neighborhood():
    assert find_neighborhood("Terreno em Contagem") == ""
    assert find_neighborhood("Terreno no bairro Nacional, Contagem") == "Nacional"


def test_safe_contacts():
    result = extract_contacts("WhatsApp (31) 99999-9999, telefone (31) 3333-4444, contato@imob.com.br")
    assert "99999-9999" in result["whatsapp"]
    assert result["email"] == "contato@imob.com.br"
    assert result["phone"]


def test_maps_uses_only_available_location():
    url = maps_query("", "Nacional", "Contagem")
    assert "Nacional%2C+Contagem" in url
    assert "Rua" not in url

