from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import requests

from .credentials import load_token
from .version import __version__


REPOSITORY = "Luandev0208/Radar-de-Lotes"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"
INSTALLER_NAME = "Instalar Radar de Lotes.exe"
INSTALLER_ASSET_NAMES = (INSTALLER_NAME, "Instalar.Radar.de.Lotes.exe")
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


def version_tuple(value: str) -> tuple[int, ...]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", value.strip())
    if not match:
        raise UpdateError(f"Versão inválida recebida: {value!r}")
    return tuple(int(part) for part in match.groups())


def is_newer(candidate: str, installed: str = __version__) -> bool:
    return version_tuple(candidate) > version_tuple(installed)


def update_check_due(last_check: str | None, now: datetime | None = None) -> bool:
    if not last_check:
        return True
    try:
        previous = datetime.fromisoformat(last_check)
    except (TypeError, ValueError):
        return True
    return (now or datetime.now()) - previous >= timedelta(hours=24)


def parse_release(payload: dict) -> ReleaseInfo:
    tag = str(payload.get("tag_name", ""))
    assets = {asset.get("name"): asset.get("url") for asset in payload.get("assets", [])}
    installer_asset = next((name for name in INSTALLER_ASSET_NAMES if name in assets), None)
    if not installer_asset or CHECKSUM_NAME not in assets:
        raise UpdateError("A Release não contém o instalador e o arquivo SHA256SUMS.txt esperados.")
    return ReleaseInfo(tag.removeprefix("v"), payload.get("name") or tag,
                       payload.get("body") or "", assets[installer_asset], assets[CHECKSUM_NAME])


class GitHubUpdater:
    def __init__(self, token_loader: Callable[[], str | None] = load_token,
                 session: requests.Session | None = None):
        self.token_loader = token_loader
        self.session = session or requests.Session()

    def _headers(self, binary=False) -> dict[str, str]:
        token = self.token_loader()
        if not token:
            raise UpdateError("Credencial do GitHub não configurada. Abra Configurações → Atualizações.")
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream" if binary else "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Radar-de-Lotes-Updater",
        }

    def latest(self) -> ReleaseInfo:
        try:
            response = self.session.get(f"{API_ROOT}/releases/latest", headers=self._headers(), timeout=20)
            response.raise_for_status()
            return parse_release(response.json())
        except requests.RequestException as exc:
            raise UpdateError("Não foi possível consultar atualizações. Verifique a internet e a credencial.") from exc

    def verify_credential(self) -> None:
        try:
            response = self.session.get(API_ROOT, headers=self._headers(), timeout=20)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise UpdateError("A credencial não conseguiu acessar o repositório privado.") from exc

    def _download(self, url: str, target: Path) -> None:
        try:
            with self.session.get(url, headers=self._headers(binary=True), timeout=60, stream=True) as response:
                response.raise_for_status()
                with target.open("wb") as output:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            output.write(chunk)
        except requests.RequestException as exc:
            target.unlink(missing_ok=True)
            raise UpdateError("Falha ao baixar a atualização.") from exc

    def download_verified(self, release: ReleaseInfo) -> Path:
        UPDATE_DIR.mkdir(parents=True, exist_ok=True)
        checksum_path = UPDATE_DIR / CHECKSUM_NAME
        installer_path = UPDATE_DIR / INSTALLER_NAME
        self._download(release.checksum_url, checksum_path)
        self._download(release.installer_url, installer_path)
        if not verify_installer(installer_path, checksum_path.read_text(encoding="utf-8")):
            installer_path.unlink(missing_ok=True)
            checksum_path.unlink(missing_ok=True)
            raise UpdateError("A verificação de integridade falhou. A atualização não será instalada.")
        return installer_path

    @staticmethod
    def launch_installer(path: Path) -> None:
        if sys.platform == "win32":
            resolved = path.resolve()
            if resolved.parent != UPDATE_DIR.resolve() or resolved.name != INSTALLER_NAME:
                raise UpdateError("O instalador não pertence à pasta temporária controlada pelo Radar.")
            cleanup = UPDATE_DIR / "instalar_e_limpar.cmd"
            cleanup.write_text(
                "@echo off\r\n"
                f'start "" /wait "{resolved}" /SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS\r\n'
                f'del /q "{resolved}"\r\n'
                f'del /q "{UPDATE_DIR / CHECKSUM_NAME}"\r\n'
                'del /q "%~f0"\r\n',
                encoding="utf-8",
            )
            subprocess.Popen(["cmd.exe", "/d", "/c", str(cleanup)], close_fds=True,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        else:
            subprocess.Popen([str(path), "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"], close_fds=True)


def cleanup_stale_updates(max_age_days: int = 7) -> int:
    """Remove apenas instaladores antigos da pasta temporária controlada pelo Radar."""
    if not UPDATE_DIR.exists():
        return 0
    cutoff = datetime.now().timestamp() - max_age_days * 86400
    removed = 0
    candidates = list(UPDATE_DIR.glob("Instalar*Radar*Lotes*.exe"))
    candidates += [UPDATE_DIR / CHECKSUM_NAME, UPDATE_DIR / "instalar_e_limpar.cmd"]
    for path in candidates:
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError:
            continue
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
