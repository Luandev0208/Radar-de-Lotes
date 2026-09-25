from datetime import datetime, timedelta
from pathlib import Path

from radar_lotes.scheduling import search_is_overdue


def test_overdue_search():
    now = datetime(2026, 9, 25, 10, 0)
    assert search_is_overdue(None, now)
    assert search_is_overdue((now - timedelta(hours=7)).isoformat(), now)
    assert not search_is_overdue((now - timedelta(hours=1)).isoformat(), now)


def test_windows_tasks_have_recovery_and_removal():
    root = Path(__file__).parents[1]
    install = (root / "install_tasks.ps1").read_text(encoding="utf-8")
    uninstall = (root / "uninstall_tasks.ps1").read_text(encoding="utf-8")
    installer = (root / "installer.iss").read_text(encoding="utf-8")
    assert "-StartWhenAvailable" in install
    assert "MultipleInstances IgnoreNew" in install
    assert 'Argument "--scheduled"' in install
    assert "py " not in install.lower() and "python" not in install.lower()
    assert "Unregister-ScheduledTask" in uninstall
    assert "[UninstallRun]" in installer
