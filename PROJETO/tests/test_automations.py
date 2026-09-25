from pathlib import Path


ROOT = Path(__file__).parents[2]
AUTOMATIONS = ROOT / "AUTOMACOES"
RADAR = AUTOMATIONS / "RADAR.bat"


def radar_text():
    return RADAR.read_text(encoding="utf-8")


def test_radar_is_the_only_batch_entrypoint():
    assert RADAR.exists()
    assert [path.name for path in AUTOMATIONS.glob("*.bat")] == ["RADAR.bat"]


def test_menu_has_all_options_and_embedded_help():
    content = radar_text()
    for option in range(1, 16):
        assert f"{option} -" in content
    assert "0 - Sair" in content
    assert ":ajuda" in content
    assert "Seguras antes da aprovacao" in content


def test_automation_is_version_independent():
    content = radar_text().lower()
    assert "projeto\\version" in content
    assert "dev-v!version!" in content
    assert "remote get-url origin" in content
    assert "1.4.1" not in content and "1.4.2" not in content


def test_test_preparation_does_not_publish_or_change_main():
    content = radar_text().lower()
    block = content.rsplit("\n:preparar_teste", 1)[1].split("\n:nova_versao", 1)[0]
    assert "push origin main" not in block
    assert "switch main" not in block
    assert "gh release" not in block
    assert "main, tag e release nao foram alterados" in block


def test_publish_flow_is_protected_and_actions_is_only_release_publisher():
    content = radar_text()
    lower = content.lower()
    assert "PUBLICAR" in content
    assert ":git_limpo" in lower and ":backup_main" in lower
    assert "merge --ff-only" in lower
    assert "push origin main" in lower
    assert "push --force" not in lower and "force push" not in lower
    assert "gh release create" not in lower and "gh release upload" not in lower
    assert "gh run watch" in lower and "gh release view" in lower
    assert "github_pat_" not in lower and "ghp_" not in lower


def test_everything_flow_stops_on_critical_errors():
    block = radar_text().lower().rsplit("\n:tudo", 1)[1]
    assert "digite exatamente publicar" in block
    assert block.count("|| exit /b 1") >= 8
    assert "acompanhar_release" in block


def test_github_actions_is_the_only_final_release_publisher():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "gh release create" in workflow
    assert "SHA256SUMS.txt" in workflow
    assert "branches: [main]" in workflow
    assert "concurrency:" in workflow


def test_windows_build_is_pinned_to_python_312_and_onefile():
    content = radar_text()
    assert "py -3.12" in content
    assert "--onefile" in content
    assert "--self-test" in content
