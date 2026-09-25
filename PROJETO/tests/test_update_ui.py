from pathlib import Path


def test_update_dialog_requires_no_credential():
    ui_path = Path(__file__).resolve().parents[1] / "radar_lotes" / "ui.py"
    source = ui_path.read_text(encoding="utf-8")
    update_dialog = source.split("class UpdateDialog", 1)[1].split("class AddDialog", 1)[0]

    assert "VERIFICAR ATUALIZAÇÕES" in update_dialog
    assert "Nenhuma conta" in update_dialog
    assert "save_token" not in update_dialog
    assert "token_input" not in update_dialog
    assert "PAT" not in update_dialog
