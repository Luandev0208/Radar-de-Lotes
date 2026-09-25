from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import requests

from .version import __version__


REPOSITORY = "Luandev0208/Radar-de-Lotes"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"
INSTALLER_NAME = "Instalar Radar de Lotes.exe"
INSTALLER_ASSET_NAMES = (INSTALLER_NAME, "Instalar.Radar.de.Lotes.exe")
COMPAT_PACKAGE_NAME = "Radar-de-Lotes-Instalador-Compatibilidade.zip"
CHECKSUM_NAME = "SHA256SUMS.txt"
UPDATE_DIR = Path(tempfile.gettempdir()) / "RadarDeLotesUpdate"


class UpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    name: str
    notes: str
    installer_url: str
    checksum_url: str
    installer_name: str = INSTALLER_NAME


def version_tuple(value: str) -> tuple[int, ...]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", value.strip())
    if not match:
        raise UpdateError(f"Versão inválida recebida: {value!r}")
    return tuple(int(part) for part in match.groups())


def is_newer(candidate: str, installed: str = __version__) -> bool:
    return version_tuple(candidate) > version_tuple(installed)


def update_check_due(last_check: str | None, now: datetime | None = None, hours: int = 6) -> bool:
    if not last_check:
        return True
    try:
        previous = datetime.fromisoformat(last_check)
    except (TypeError, ValueError):
        return True
    return (now or datetime.now()) - previous >= timedelta(hours=hours)


def parse_release(payload: dict) -> ReleaseInfo:
    tag = str(payload.get("tag_name", ""))
    assets = {
        asset.get("name"): asset.get("url")
        for asset in payload.get("assets", [])
        if asset.get("name") and asset.get("url")
    }

    selected = None
    if COMPAT_PACKAGE_NAME in assets:
        selected = COMPAT_PACKAGE_NAME
    else:
        selected = next((name for name in INSTALLER_ASSET_NAMES if name in assets), None)

    if not selected or CHECKSUM_NAME not in assets:
        raise UpdateError(
            "A Release não contém o pacote de instalação e o arquivo SHA256SUMS.txt esperados."
        )
    return ReleaseInfo(
        tag.removeprefix("v"),
        payload.get("name") or tag,
        payload.get("body") or "",
        assets[selected],
        assets[CHECKSUM_NAME],
        selected,
    )


class GitHubUpdater:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()

    def _headers(self, binary=False) -> dict[str, str]:
        return {
            "Accept": "application/octet-stream" if binary else "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Radar-de-Lotes-Updater",
        }

    def latest(self) -> ReleaseInfo:
        try:
            response = self.session.get(
                f"{API_ROOT}/releases/latest",
                headers=self._headers(),
                timeout=20,
            )
            response.raise_for_status()
            return parse_release(response.json())
        except requests.RequestException as exc:
            raise UpdateError(
                "Não foi possível consultar atualizações. Verifique sua conexão com a internet."
            ) from exc

    def _download(self, url: str, target: Path) -> None:
        try:
            with self.session.get(
                url, headers=self._headers(binary=True), timeout=90, stream=True
            ) as response:
                response.raise_for_status()
                with target.open("wb") as output:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            output.write(chunk)
        except requests.RequestException as exc:
            target.unlink(missing_ok=True)
            raise UpdateError("Falha ao baixar a atualização.") from exc

    @staticmethod
    def _safe_extract(package: Path, target: Path) -> Path:
        shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)
        root = target.resolve()
        try:
            with zipfile.ZipFile(package) as archive:
                for member in archive.infolist():
                    destination = (target / member.filename).resolve()
                    if root != destination and root not in destination.parents:
                        raise UpdateError("O pacote de atualização contém um caminho inválido.")
                archive.extractall(target)
        except (zipfile.BadZipFile, OSError) as exc:
            raise UpdateError("O pacote de atualização não pôde ser extraído.") from exc

        setup = target / "Setup.exe"
        bins = list(target.glob("Setup-*.bin"))
        if not setup.is_file() or not bins:
            raise UpdateError("O pacote compatível está incompleto.")
        return setup

    def download_verified(self, release: ReleaseInfo) -> Path:
        UPDATE_DIR.mkdir(parents=True, exist_ok=True)
        checksum_path = UPDATE_DIR / CHECKSUM_NAME
        payload_name = (
            COMPAT_PACKAGE_NAME
            if release.installer_name == COMPAT_PACKAGE_NAME
            else INSTALLER_NAME
        )
        payload_path = UPDATE_DIR / payload_name
        try:
            self._download(release.checksum_url, checksum_path)
            self._download(release.installer_url, payload_path)
        except UpdateError:
            checksum_path.unlink(missing_ok=True)
            payload_path.unlink(missing_ok=True)
            raise

        checksum_text = checksum_path.read_text(encoding="utf-8")
        checksum_filename = (
            COMPAT_PACKAGE_NAME
            if release.installer_name == COMPAT_PACKAGE_NAME
            else INSTALLER_NAME
        )
        if not verify_installer(payload_path, checksum_text, checksum_filename):
            payload_path.unlink(missing_ok=True)
            checksum_path.unlink(missing_ok=True)
            raise UpdateError(
                "A verificação de integridade falhou. A atualização não será instalada."
            )

        if release.installer_name == COMPAT_PACKAGE_NAME:
            return self._safe_extract(payload_path, UPDATE_DIR / "compat")
        return payload_path

    @staticmethod
    def launch_installer(path: Path) -> None:
        if sys.platform != "win32":
            subprocess.Popen(
                [str(path), "/SILENT", "/CLOSEAPPLICATIONS", "/NORESTARTAPPLICATIONS"],
                close_fds=True,
            )
            return

        resolved = path.resolve()
        controlled = UPDATE_DIR.resolve()
        if controlled != resolved.parent and controlled not in resolved.parents:
            raise UpdateError(
                "O instalador não pertence à pasta temporária controlada pelo Radar."
            )
        if resolved.name not in (INSTALLER_NAME, "Setup.exe"):
            raise UpdateError("Arquivo de instalação inesperado.")

        cleanup = UPDATE_DIR / "instalar_e_limpar.cmd"
        current_pid = os.getpid()
        cleanup.write_text(
            "@echo off\r\n"
            "setlocal\r\n"
            f'set "RADAR_PID={current_pid}"\r\n'
            ":aguardar_radar\r\n"
            'tasklist /FI "PID eq %RADAR_PID%" /NH 2>nul | findstr /R /C:"[ ]%RADAR_PID%[ ]" >nul\r\n'
            "if not errorlevel 1 (\r\n"
            "  timeout /t 1 /nobreak >nul\r\n"
            "  goto aguardar_radar\r\n"
            ")\r\n"
            f'start "" /wait "{resolved}" /SILENT /CLOSEAPPLICATIONS /NORESTARTAPPLICATIONS\r\n'
            "set "SETUP_RC=%ERRORLEVEL%"\r\n"
            "if not "%SETUP_RC%"=="0" (\r\n"
            "  echo A instalacao falhou ou foi bloqueada pela politica de seguranca do Windows.>"%TEMP%\\RadarDeLotesUpdateErro.txt"\r\n"
            "  exit /b %SETUP_RC%\r\n"
            ")\r\n"
            f'del /q "{UPDATE_DIR / INSTALLER_NAME}" 2>nul\r\n'
            f'del /q "{UPDATE_DIR / COMPAT_PACKAGE_NAME}" 2>nul\r\n'
            f'del /q "{UPDATE_DIR / CHECKSUM_NAME}" 2>nul\r\n'
            f'rmdir /s /q "{UPDATE_DIR / "compat"}" 2>nul\r\n'
            'del /q "%~f0"\r\n',
            encoding="utf-8",
        )
        subprocess.Popen(
            ["cmd.exe", "/d", "/c", str(cleanup)],
            close_fds=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )


def cleanup_stale_updates(max_age_days: int = 7) -> int:
    if not UPDATE_DIR.exists():
        return 0
    cutoff = datetime.now().timestamp() - max_age_days * 86400
    removed = 0
    candidates = list(UPDATE_DIR.glob("Instalar*Radar*Lotes*.exe"))
    candidates += [
        UPDATE_DIR / COMPAT_PACKAGE_NAME,
        UPDATE_DIR / CHECKSUM_NAME,
        UPDATE_DIR / "instalar_e_limpar.cmd",
    ]
    for path in candidates:
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError:
            continue
    compat = UPDATE_DIR / "compat"
    try:
        if compat.is_dir() and compat.stat().st_mtime < cutoff:
            shutil.rmtree(compat, ignore_errors=True)
            removed += 1
    except OSError:
        pass
    return removed


def checksum_for(filename: str, contents: str) -> str | None:
    for line in contents.splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line.strip())
        if match and match.group(2).strip() == filename:
            return match.group(1).lower()
    return None


def verify_installer(path: Path, checksum_contents: str, filename: str = INSTALLER_NAME) -> bool:
    expected = checksum_for(filename, checksum_contents)
    if not expected:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower() == expected.lower()
