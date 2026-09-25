from pathlib import Path


ROOT = Path(__file__).parents[2]
AUTOMATIONS = ROOT / "AUTOMACOES"


def text(name):
    return (AUTOMATIONS / name).read_text(encoding="utf-8")


def test_all_required_automation_files_exist():
    required = {
        "RADAR.bat", "01_EXECUTAR_RADAR.bat", "02_RODAR_TESTES.bat",
        "03_GERAR_EXE.bat", "04_GERAR_INSTALADOR.bat",
        "05_PREPARAR_TESTE_COMPLETO.bat", "06_CRIAR_BRANCH_NOVA_VERSAO.bat",
        "07_VER_STATUS_GIT.bat", "08_CRIAR_BACKUP_MAIN_ANTIGA.bat",
        "09_PUBLICAR_VERSAO_APROVADA.bat", "10_PUBLICAR_RELEASE.bat",
        "11_ABRIR_ENTREGA.bat", "12_ABRIR_LOGS.bat",
        "14_VERIFICAR_AMBIENTE.bat", "TUDO_EM_UM_APOS_APROVACAO.bat",
        "README_AUTOMACOES.txt", "config.bat", "_comum.bat",
    }
    assert required <= {path.name for path in AUTOMATIONS.iterdir()}


def test_publish_flows_have_confirmation_tests_backup_and_no_secrets():
    publish = text("09_PUBLICAR_VERSAO_APROVADA.bat")
    release = text("10_PUBLICAR_RELEASE.bat")
    complete = text("TUDO_EM_UM_APOS_APROVACAO.bat")
    combined = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in AUTOMATIONS.glob("*.bat"))
    assert "PUBLICAR" in publish and "02_RODAR_TESTES.bat" in publish
    assert "08_CRIAR_BACKUP_MAIN_ANTIGA.bat" in publish
    assert "PUBLICAR" in complete and "10_PUBLICAR_RELEASE.bat" in complete
    assert "gh run watch" in release and "gh release view" in release
    assert "gh release create" not in release and "git tag" not in release
    assert "gh release upload" not in release
    assert "github_pat_" not in combined.lower() and "ghp_" not in combined.lower()


def test_test_build_does_not_publish_or_change_main():
    build = text("05_PREPARAR_TESTE_COMPLETO.bat").lower()
    assert "gh release" not in build
    assert "push origin main" not in build
    assert "switch main" not in build
    assert "checkout main" not in build
    assert "entrega_para_teste" not in build or "delivery_dir" in build


def test_github_actions_is_the_only_release_publisher():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "gh release create" in workflow
    assert "SHA256SUMS.txt" in workflow
    assert "branches: [main]" in workflow
    assert "concurrency:" in workflow


def test_dev_workflow_builds_artifact_without_publishing_release():
    workflow = (ROOT / ".github" / "workflows" / "test-build.yml").read_text(encoding="utf-8")
    assert "dev-v*" in workflow
    assert "actions/upload-artifact" in workflow
    assert "gh release" not in workflow


def test_windows_build_is_pinned_to_python_312_and_onefile():
    exe = text("03_GERAR_EXE.bat")
    common = text("_comum.bat")
    assert "--onefile" in exe
    assert "py -3.12" in common
    assert "--self-test" in exe
