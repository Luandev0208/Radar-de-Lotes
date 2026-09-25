"""Armazenamento do token no Windows Credential Manager, sem texto puro em disco."""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


CREDENTIAL_TARGET = "RadarDeLotes.GitHubReadToken"
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2


class CredentialError(RuntimeError):
    pass


class _CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def _advapi():
    if sys.platform != "win32":
        raise CredentialError("O Gerenciador de Credenciais está disponível somente no Windows.")
    return ctypes.WinDLL("Advapi32.dll", use_last_error=True)


def save_token(token: str) -> None:
    token = token.strip()
    if not token:
        raise CredentialError("Informe a credencial de leitura do GitHub.")
    raw = token.encode("utf-16-le")
    buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    credential = _CREDENTIALW(
        0, CRED_TYPE_GENERIC, CREDENTIAL_TARGET, "Radar de Lotes - atualizações privadas",
        wintypes.FILETIME(), len(raw), buffer, CRED_PERSIST_LOCAL_MACHINE,
        0, None, None, "Radar de Lotes",
    )
    api = _advapi()
    api.CredWriteW.argtypes = [ctypes.POINTER(_CREDENTIALW), wintypes.DWORD]
    api.CredWriteW.restype = wintypes.BOOL
    if not api.CredWriteW(ctypes.byref(credential), 0):
        raise CredentialError(f"Não foi possível salvar a credencial (erro {ctypes.get_last_error()}).")


def load_token() -> str | None:
    api = _advapi()
    pointer = ctypes.POINTER(_CREDENTIALW)()
    api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                              ctypes.POINTER(ctypes.POINTER(_CREDENTIALW))]
    api.CredReadW.restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    if not api.CredReadW(CREDENTIAL_TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
        if ctypes.get_last_error() == 1168:
            return None
        raise CredentialError(f"Não foi possível ler a credencial (erro {ctypes.get_last_error()}).")
    try:
        cred = pointer.contents
        raw = ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize)
        return raw.decode("utf-16-le")
    finally:
        api.CredFree(pointer)


def delete_token() -> None:
    api = _advapi()
    api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    api.CredDeleteW.restype = wintypes.BOOL
    if not api.CredDeleteW(CREDENTIAL_TARGET, CRED_TYPE_GENERIC, 0):
        error = ctypes.get_last_error()
        if error != 1168:
            raise CredentialError(f"Não foi possível remover a credencial (erro {error}).")

