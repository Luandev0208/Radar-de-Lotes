from datetime import datetime, timedelta
import hashlib
import os
import time
import zipfile

import pytest
import requests

from radar_lotes.updater import (
    CHECKSUM_NAME, COMPAT_PACKAGE_NAME, INSTALLER_NAME, GitHubUpdater, UpdateError,
    checksum_for, cleanup_stale_updates, is_newer, parse_release, update_check_due,
    verify_installer, version_tuple,
)


def release_payload(tag="v1.5.0", compatible=False):
    asset_name = COMPAT_PACKAGE_NAME if compatible else INSTALLER_NAME
    return {
        "tag_name": tag,
        "name": "Radar",
        "body": "Notas",
        "assets": [
            {"name": asset_name, "url": "https://api.github.test/installer"},
            {"name": CHECKSUM_NAME, "url": "https://api.github.test/checksum"},
        ],
    }


def test_semantic_version_comparison():
    assert version_tuple("v1.10.0") == (1, 10, 0)
    assert is_newer("1.5.0", "1.4.3")
    assert not is_newer("1.4.3", "1.4.3")


def test_release_prefers_compatible_package_when_available():
    payload = release_payload(compatible=False)
    payload["assets"].insert(0, {"name": COMPAT_PACKAGE_NAME, "url": "https://api.github.test/compat"})
    info = parse_release(payload)
    assert info.installer_name == COMPAT_PACKAGE_NAME
    assert info.installer_url.endswith("compat")


def test_release_falls_back_to_legacy_exe_for_old_releases():
    info = parse_release(release_payload())
    assert info.installer_name == INSTALLER_NAME
    assert info.installer_url.endswith("installer")
    with pytest.raises(UpdateError):
        parse_release({"tag_name": "v1.5.0", "assets": []})


def test_checksum_parsing_and_verification(tmp_path):
    payload = tmp_path / COMPAT_PACKAGE_NAME
    payload.write_bytes(b"pacote")
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    text = f"{digest}  {COMPAT_PACKAGE_NAME}\n"
    assert checksum_for(COMPAT_PACKAGE_NAME, text) == digest
    assert verify_installer(payload, text, COMPAT_PACKAGE_NAME)
    assert not verify_installer(payload, f"{'0' * 64}  {COMPAT_PACKAGE_NAME}\n", COMPAT_PACKAGE_NAME)


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


def test_public_release_needs_no_authorization():
    session = RecordingSession(FakeResponse(release_payload()))
    info = GitHubUpdater(session=session).latest()
    assert info.version == "1.5.0"
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


def test_check_interval_is_six_hours_by_default():
    now = datetime(2026, 9, 25, 10)
    assert update_check_due(None, now)
    assert update_check_due((now - timedelta(hours=7)).isoformat(), now)
    assert not update_check_due((now - timedelta(hours=2)).isoformat(), now)


def test_compatible_zip_requires_setup_and_bin(tmp_path):
    package = tmp_path / "package.zip"
    with zipfile.ZipFile(package, "w") as z:
        z.writestr("Setup.exe", b"exe")
        z.writestr("Setup-0.bin", b"bin")
    setup = GitHubUpdater._safe_extract(package, tmp_path / "out")
    assert setup.name == "Setup.exe"
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("Setup.exe", b"exe")
    with pytest.raises(UpdateError, match="incompleto"):
        GitHubUpdater._safe_extract(bad, tmp_path / "out2")


def test_windows_helper_waits_old_process_and_disables_restart(tmp_path, monkeypatch):
    import radar_lotes.updater as updater

    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path)
    monkeypatch.setattr(updater.sys, "platform", "win32")
    calls = []
    monkeypatch.setattr(updater.subprocess, "Popen", lambda *args, **kwargs: calls.append((args, kwargs)))
    installer = tmp_path / INSTALLER_NAME
    installer.write_bytes(b"ok")
    GitHubUpdater.launch_installer(installer)
    helper = (tmp_path / "instalar_e_limpar.cmd").read_text(encoding="utf-8")
    assert "RADAR_PID" in helper
    assert "/NORESTARTAPPLICATIONS" in helper
    assert "/wait" in helper
    assert calls


def test_cleanup_targets_only_controlled_update_files(tmp_path, monkeypatch):
    import radar_lotes.updater as updater
    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path)
    old = tmp_path / INSTALLER_NAME
    checksum = tmp_path / CHECKSUM_NAME
    keep = tmp_path / "usuario.txt"
    for path in (old, checksum, keep):
        path.write_text("x", encoding="utf-8")
    past = time.time() - 10 * 86400
    for path in (old, checksum, keep):
        os.utime(path, (past, past))
    assert cleanup_stale_updates(7) == 2
    assert keep.exists()
