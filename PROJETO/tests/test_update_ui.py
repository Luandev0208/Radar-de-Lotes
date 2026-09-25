from pathlib import Path


def test_update_is_background_and_discreet():
    source = (Path(__file__).resolve().parents[1] / "radar_lotes" / "ui.py").read_text(encoding="utf-8")
    assert "Nova versão" in source
    assert "update_notice" in source
    assert 'QPushButton("ATUALIZAÇÕES")' not in source


def test_search_dialog_is_region_constrained_and_price_first():
    source = (Path(__file__).resolve().parents[1] / "radar_lotes" / "ui.py").read_text(encoding="utf-8")
    assert "Belo Horizonte e Região Metropolitana" in source
    assert "Mostrar somente anúncios com preço informado" in source
    assert "BUSCAR LOTES" in source
    assert "QCheckBox" in source


def test_maps_ui_uses_coordinates_when_available():
    source = (Path(__file__).resolve().parents[1] / "radar_lotes" / "ui.py").read_text(encoding="utf-8")
    assert 'row["latitude"]' in source
    assert 'row["longitude"]' in source
