from pathlib import Path


def test_update_is_background_and_discreet():
    source = (Path(__file__).resolve().parents[1] / "radar_lotes" / "ui.py").read_text(encoding="utf-8")
    assert "Nova versão" in source
    assert "update_notice" in source
    assert 'QPushButton("ATUALIZAÇÕES")' not in source
    assert "check_updates_silently" in source
    assert "Nenhuma conta" not in source


def test_search_button_opens_filter_dialog():
    source = (Path(__file__).resolve().parents[1] / "radar_lotes" / "ui.py").read_text(encoding="utf-8")
    assert "class SearchFilterDialog" in source
    assert "BUSCAR COM ESTES FILTROS" in source
    assert "Filtros da busca" in source
