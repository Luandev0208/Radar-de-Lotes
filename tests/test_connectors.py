from radar_lotes.connectors import PRIORITY_SEARCH_TERMS, default_connectors, listing_from_jsonld


def test_jsonld_price_city_neighborhood_and_contacts():
    data = {
        "name": "Lote no Nacional",
        "url": "/imovel/123",
        "description": "Terreno plano 360 m², 12x30. WhatsApp (31) 99999-9999",
        "offers": {"price": "395000.00"},
        "address": {"addressLocality": "Contagem", "streetAddress": "Rua X, Nacional"},
        "email": "vendas@imob.com.br",
    }
    item = listing_from_jsonld(data, "https://exemplo.com/busca", "Teste")
    assert item.price == 395000
    assert item.city == "Contagem"
    assert item.neighborhood == "Nacional"
    assert item.whatsapp
    assert item.email == "vendas@imob.com.br"


def test_non_listing_jsonld_is_rejected():
    menu = {"@type": "WebSite", "name": "Imóveis em Contagem", "url": "/"}
    assert listing_from_jsonld(menu, "https://exemplo.com", "Teste") is None


def test_priority_neighborhood_queries_are_present():
    joined = " ".join(PRIORITY_SEARCH_TERMS).lower()
    for name in ("nacional", "xangri-lá", "xangri la", "parque xangri", "vale das amendoeiras", "bom jesus", "arvoredo"):
        assert name in joined
    for connector in default_connectors():
        assert len(connector.urls) >= len(PRIORITY_SEARCH_TERMS)
        assert any("Nacional" in url or "nacional" in url for url in connector.urls)
