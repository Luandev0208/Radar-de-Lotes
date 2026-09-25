from radar_lotes.connectors import (
    default_connectors, is_probable_listing_url, listing_from_jsonld,
)
from radar_lotes.search import SearchFilters


def test_listing_url_filter_rejects_search_pages():
    assert not is_probable_listing_url("https://www.olx.com.br/imoveis/terrenos/estado-mg/belo-horizonte-e-regiao")
    assert not is_probable_listing_url("https://www.vivareal.com.br/venda/minas-gerais/contagem/lote-terreno_residencial/")
    assert is_probable_listing_url("https://www.olx.com.br/imoveis/terrenos/lote-em-contagem-123456789")
    assert is_probable_listing_url("https://www.vivareal.com.br/imovel/lote-terreno-contagem-360m2-venda-RS395000-id-12345678/")


def test_jsonld_extracts_direct_listing_geo_and_price():
    data = {
        "name": "Lote no Nacional",
        "url": "/imovel/lote-nacional-id-12345678/",
        "description": "Terreno plano, murado, 360 m², 12x30. CAB: 1,0. WhatsApp (31) 99999-9999",
        "offers": {"price": "395000.00"},
        "address": {
            "addressLocality": "Contagem",
            "addressRegion": "MG",
            "streetAddress": "Rua X, 120, Nacional",
        },
        "geo": {"latitude": -19.90, "longitude": -44.05},
        "email": "vendas@imob.com.br",
    }
    item = listing_from_jsonld(data, "https://exemplo.com/busca", "Teste", ("Nacional",))
    assert item is not None
    assert item.price == 395000
    assert item.city == "Contagem"
    assert item.neighborhood == "Nacional"
    assert item.latitude == -19.90 and item.longitude == -44.05
    assert item.dimensions == "12 x 30"
    assert item.topography == "Plano"
    assert item.walled == "Sim"
    assert item.cab == "1.0"


def test_jsonld_search_page_candidate_is_rejected():
    data = {
        "name": "Terrenos à venda em Contagem",
        "url": "/venda/minas-gerais/contagem/lote-terreno_residencial/",
        "description": "Veja lotes em Contagem",
        "address": {"addressLocality": "Contagem"},
    }
    assert listing_from_jsonld(data, "https://www.vivareal.com.br/", "Teste") is None


def test_connectors_are_region_constrained_when_city_blank():
    connectors = default_connectors(SearchFilters())
    joined = " ".join(url for connector in connectors for url in connector.urls)
    assert "belo-horizonte-e-regiao" in joined
    assert "sao-paulo" not in joined.lower()
