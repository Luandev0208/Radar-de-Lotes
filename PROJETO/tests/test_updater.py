from datetime import datetime, timedelta
import hashlib
import os
import time
import requests

import pytest

from radar_lotes.updater import (
    CHECKSUM_NAME, INSTALLER_NAME, GitHubUpdater, UpdateError, checksum_for,
    cleanup_stale_updates, is_newer, parse_release, update_check_due,
    verify_installer, version_tuple,
)


def release_payload(tag="v1.4.2"):
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
    assert is_newer("1.4.2", "1.4.1")


def test_release_requires_installer_and_checksum():
    info = parse_release(release_payload())
    assert info.version == "1.4.2" and info.installer_url.endswith("installer")
    with pytest.raises(UpdateError):
        parse_release({"tag_name": "v1.3.0", "assets": []})
    normalized = release_payload()
    normalized["assets"][0]["name"] = "Instalar.Radar.de.Lotes.exe"
    assert parse_release(normalized).installer_url.endswith("installer")


def test_checksum_parsing():
    digest = "a" * 64
    assert checksum_for(INSTALLER_NAME, f"{digest}  {INSTALLER_NAME}\n") == digest
    assert checksum_for(INSTALLER_NAME, f"{digest}  outro.exe\n") is None


def test_installer_sha_accepts_correct_and_rejects_incorrect(tmp_path):
    installer = tmp_path / INSTALLER_NAME
    installer.write_bytes(b"instalador-v1.4.2")
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    assert verify_installer(installer, f"{digest}  {INSTALLER_NAME}\n")
    assert not verify_installer(installer, f"{'0' * 64}  {INSTALLER_NAME}\n")
    assert not verify_installer(installer, f"{digest}  outro.exe\n")


class FakeResponse:
    def __init__(self, payload=None, chunks=()):
        self.payload = payload
        self.chunks = chunks
    def raise_for_status(self): pass
    def json(self): return self.payload
    def iter_content(self, _size): return iter(self.chunks)
    def __enter__(self): return self
    def __exit__(self, *_args): return False


class RecordingSession:
    def __init__(self, response):
        self.response = response
        self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_public_release_needs_no_authorization_or_credential():
    session = RecordingSession(FakeResponse(release_payload()))
    info = GitHubUpdater(session=session).latest()
    assert info.version == "1.4.2"
    assert "Authorization" not in session.calls[0][1]["headers"]


def test_public_binary_download_has_no_authorization(tmp_path):
    session = RecordingSession(FakeResponse(chunks=[b"abc", b"123"]))
    target = tmp_path / "download.exe"
    GitHubUpdater(session=session)._download("https://api.github.test/asset", target)
    assert target.read_bytes() == b"abc123"
    assert "Authorization" not in session.calls[0][1]["headers"]


def test_interrupted_download_removes_partial_file(tmp_path):
    class InterruptedSession:
        def get(self, *_args, **_kwargs):
            raise requests.ConnectionError("interrompido")

    target = tmp_path / "parcial.exe"
    target.write_bytes(b"parcial")
    with pytest.raises(UpdateError, match="Falha ao baixar"):
        GitHubUpdater(session=InterruptedSession())._download("https://api.github.test/asset", target)
    assert not target.exists()


def test_daily_check_interval():
    now = datetime(2026, 9, 25, 10)
    assert update_check_due(None, now)
    assert update_check_due((now - timedelta(hours=25)).isoformat(), now)
    assert not update_check_due((now - timedelta(hours=2)).isoformat(), now)


def test_cleanup_only_targets_controlled_old_installers(tmp_path, monkeypatch):
    import radar_lotes.updater as updater
    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path)
    old = tmp_path / "Instalar Radar de Lotes.exe"
    old_checksum = tmp_path / CHECKSUM_NAME
    old_helper = tmp_path / "instalar_e_limpar.cmd"
    fresh = tmp_path / "Instalar Radar de Lotes teste.exe"
    keep = tmp_path / "arquivo-do-usuario.txt"
    old.write_bytes(b"installer")
    old_checksum.write_text("hash", encoding="utf-8")
    old_helper.write_text("helper", encoding="utf-8")
    fresh.write_bytes(b"novo")
    keep.write_text("preservar", encoding="utf-8")
    past = time.time() - 10 * 86400
    for path in (old, old_checksum, old_helper, keep):
        os.utime(path, (past, past))
    assert cleanup_stale_updates(7) == 3
    assert not old.exists() and not old_checksum.exists() and not old_helper.exists()
    assert fresh.exists() and keep.exists()


def test_windows_helper_only_accepts_controlled_installer(tmp_path, monkeypatch):
    import radar_lotes.updater as updater

    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path)
    monkeypatch.setattr(updater.sys, "platform", "win32")
    calls = []
    monkeypatch.setattr(updater.subprocess, "Popen", lambda *args, **kwargs: calls.append((args, kwargs)))
    installer = tmp_path / INSTALLER_NAME
    installer.write_bytes(b"ok")
    GitHubUpdater.launch_installer(installer)
    helper = (tmp_path / "instalar_e_limpar.cmd").read_text(encoding="utf-8")
    assert "/wait" in helper and INSTALLER_NAME in helper and CHECKSUM_NAME in helper
    assert calls
    outside = tmp_path.parent / INSTALLER_NAME
    with pytest.raises(UpdateError, match="pasta temporária controlada"):
        GitHubUpdater.launch_installer(outside)
