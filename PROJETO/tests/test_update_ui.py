import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from radar_lotes.database import Database
from radar_lotes.ui import UpdateDialog


def test_update_dialog_requires_no_credential(tmp_path):
    app = QApplication.instance() or QApplication([])
    dialog = UpdateDialog(Database(tmp_path / "radar.db"))
    texts = [widget.text() for widget in dialog.findChildren(QLabel)]
    texts += [widget.text() for widget in dialog.findChildren(QPushButton)]
    joined = " ".join(texts)
    assert "VERIFICAR ATUALIZAÇÕES" in texts
    assert "Nenhuma conta" in joined
    assert "PAT" not in joined and "SALVAR" not in joined and "token" not in joined.lower()
    dialog.close()
    assert app is not None
