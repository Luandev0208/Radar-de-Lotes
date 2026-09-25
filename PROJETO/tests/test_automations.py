from pathlib import Path

ROOT = Path(__file__).parents[2]
TOOLS = ROOT / "FERRAMENTAS_DESENVOLVIMENTO"
TEMPLATE = TOOLS / "RADAR_LOCAL_TEMPLATE.bat"
BOOTSTRAP = TOOLS / "INSTALAR_RADAR_LOCAL.bat"


def text():
    return TEMPLATE.read_text(encoding="utf-8")


def test_automations_are_local_and_gitignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "AUTOMACOES/" in ignore
    assert TEMPLATE.exists() and BOOTSTRAP.exists()


def test_menu_keeps_all_options():
    content = text()
    for option in range(1, 16):
        assert f"{option} -" in content
    assert "0 - Sair" in content


def test_inno_detection_includes_localappdata():
    assert "%LOCALAPPDATA%\\Programs\\Inno Setup 6\\ISCC.exe" in text()


def test_everything_prompts_publicar_once_and_does_not_repeat_builds():
    block = text().split("\n:tudo", 1)[1].split("\n:erro_version", 1)[0]
    assert block.count("PUBLICAR") == 1
    assert block.count("call :testes") == 1
    assert block.count("call :gerar_exe") == 1
    assert block.count("call :gerar_instalador") == 1


def test_no_force_push_and_release_validation_has_compat_asset():
    content = text().lower()
    assert "push --force" not in content
    assert "radar-de-lotes-instalador-compatibilidade.zip" in content


def test_pytest_uses_dedicated_unique_basetemp():
    content = text()
    assert "--basetemp" in content
    assert "RadarDeLotesDev" in content
