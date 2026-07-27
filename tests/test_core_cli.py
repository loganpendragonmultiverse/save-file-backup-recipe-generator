import pytest

from save_backup_recipe.cli import main
from save_backup_recipe.core import bash_recipe, generate, powershell_recipe, validate_paths


def test_powershell_and_bash_recipes(tmp_path):
    source = tmp_path / "Game Saves"
    destination = tmp_path / "Backups" / "save copy"
    ps = powershell_recipe(source, destination, "copy")
    assert "Copy-Item -LiteralPath" in ps
    assert "already exists" in ps
    bash = bash_recipe(source, destination.with_suffix(".tar.gz"), "archive")
    assert "tar -czf" in bash
    assert "'" in bash
    assert "Compress-Archive" in powershell_recipe(source, destination, "archive")
    assert "cp -a" in bash_recipe(source, destination, "copy")
    assert "cp -a" in generate(source, destination, "bash", "copy")


def test_validation_and_modes(tmp_path):
    source = tmp_path / "save"
    with pytest.raises(ValueError, match="differ"):
        validate_paths(source, source)
    with pytest.raises(ValueError, match="inside"):
        validate_paths(source, source / "backup")
    with pytest.raises(ValueError, match="mode"):
        powershell_recipe(source, tmp_path / "out", "bad")
    with pytest.raises(ValueError, match="mode"):
        bash_recipe(source, tmp_path / "out", "bad")
    with pytest.raises(ValueError, match="shell"):
        generate(source, tmp_path / "out", "fish", "copy")


def test_cli_output_safety(tmp_path, capsys):
    output = tmp_path / "backup.ps1"
    assert main([str(tmp_path / "save"), str(tmp_path / "backup"), "--output", str(output)]) == 0
    assert "$saveSource" in output.read_text(encoding="utf-8")
    assert main([str(tmp_path / "save"), str(tmp_path / "backup"), "--output", str(output)]) == 2
    assert "already exists" in capsys.readouterr().err
