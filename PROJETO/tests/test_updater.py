from datetime import datetime, timedelta

import pytest

from radar_lotes.updater import (
    CHECKSUM_NAME, INSTALLER_NAME, GitHubUpdater, UpdateError, checksum_for,
    cleanup_stale_updates, is_newer, parse_release, update_check_due, version_tuple,
)


def release_payload(tag="v1.3.0"):
    return {
        "tag_name": tag, "name": "Radar", "body": "Notas",
        "assets": [
            {"name": INSTALLER_NAME, "url": "https://api.github.test/installer"},
            {"name": CHECKSUM_NAME, "url": "https://api.github.test/checksum"},
        ],
    }


def test_semantic_version_comparison():
    assert version_tuple("v1.10.0") == (1, 10, 0)
    assert is_newer("1.3.1", "1.3.0")
    assert not is_newer("1.3.0", "1.3.0")
    assert not is_newer("1.2.9", "1.3.0")


def test_release_requires_installer_and_checksum():
    info = parse_release(release_payload())
    assert info.version == "1.3.0" and info.installer_url.endswith("installer")
    with pytest.raises(UpdateError):
        parse_release({"tag_name": "v1.3.0", "assets": []})
    normalized = release_payload()
    normalized["assets"][0]["name"] = "Instalar.Radar.de.Lotes.exe"
    assert parse_release(normalized).installer_url.endswith("installer")


def test_checksum_parsing():
    digest = "a" * 64
    assert checksum_for(INSTALLER_NAME, f"{digest}  {INSTALLER_NAME}\n") == digest
    assert checksum_for(INSTALLER_NAME, f"{digest}  outro.exe\n") is None


def test_missing_credential_is_friendly():
    with pytest.raises(UpdateError, match="não configurada"):
        GitHubUpdater(token_loader=lambda: None).latest()


def test_daily_check_interval():
    now = datetime(2026, 9, 25, 10)
    assert update_check_due(None, now)
    assert update_check_due((now - timedelta(hours=25)).isoformat(), now)
    assert not update_check_due((now - timedelta(hours=2)).isoformat(), now)


def test_cleanup_only_targets_controlled_old_installers(tmp_path, monkeypatch):
    import radar_lotes.updater as updater
    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path)
    old = tmp_path / "Instalar Radar de Lotes.exe"
    keep = tmp_path / "arquivo-do-usuario.txt"
    old.write_bytes(b"installer")
    keep.write_text("preservar", encoding="utf-8")
    old.touch()
    import os, time
    past = time.time() - 10 * 86400
    os.utime(old, (past, past))
    assert cleanup_stale_updates(7) == 1
    assert not old.exists() and keep.exists()
