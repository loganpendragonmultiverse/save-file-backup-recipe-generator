import os
import shutil
import subprocess
import tarfile

import pytest

from save_backup_recipe import core
from save_backup_recipe.cli import main


@pytest.mark.parametrize("verify", [1, "yes", [], None])
@pytest.mark.parametrize("shell", ["bash", "powershell"])
def test_verify_requires_boolean(tmp_path, verify, shell):
    with pytest.raises(TypeError, match="boolean"):
        core.generate(tmp_path / "source", tmp_path / "target", shell, "copy", verify)


def run(tmp_path, shell, script):
    if shell == "bash" and os.name == "nt":
        pytest.skip("native POSIX Bash required")
    executable = shutil.which("bash" if shell == "bash" else "pwsh")
    if not executable:
        pytest.skip(shell + " unavailable")
    path = tmp_path / ("run.sh" if shell == "bash" else "run.ps1")
    path.write_text(script, encoding="utf-8")
    args = (
        [executable, str(path)]
        if shell == "bash"
        else [executable, "-NoProfile", "-File", str(path)]
    )
    return subprocess.run(args, check=False, capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize("shell", ["bash", "powershell"])
@pytest.mark.parametrize("mode", ["copy", "archive"])
def test_default_recipe_rejects_dangling_target(tmp_path, shell, mode):
    source, target, missing = tmp_path / "source", tmp_path / "target", tmp_path / "missing"
    source.mkdir()
    (source / "save").write_bytes(b"synthetic")
    script = core.generate(source, target, shell, mode)
    try:
        target.symlink_to(missing, target_is_directory=mode == "copy")
    except OSError:
        pytest.skip("symlink unavailable")
    result = run(tmp_path, shell, script)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Backup completed" not in result.stdout
    assert target.is_symlink() and not missing.exists()
    assert (source / "save").read_bytes() == b"synthetic"


def test_bash_archive_dash_source(tmp_path):
    source = tmp_path / "-saves"
    source.mkdir()
    (source / ".hidden").write_bytes(b"hidden")
    (source / "slot").write_bytes(b"synthetic")
    target = tmp_path / "archive.tar.gz"
    result = run(tmp_path, "bash", core.generate(source, target, "bash", "archive"))
    assert result.returncode == 0, result.stdout + result.stderr
    with tarfile.open(target) as archive:
        assert archive.extractfile("-saves/slot").read() == b"synthetic"
        assert archive.extractfile("-saves/.hidden").read() == b"hidden"


@pytest.mark.parametrize("shell", ["bash", "powershell"])
@pytest.mark.parametrize("location", ["source", "ancestor", "destination"])
def test_existing_generation_links_rejected_for_verify(tmp_path, shell, location):
    real = tmp_path / "real"
    real.mkdir()
    source, target, link = real, tmp_path / "target", tmp_path / "link"
    if location == "ancestor":
        (real / "saves").mkdir()
        source = link / "saves"
    elif location == "source":
        source = link
    else:
        target = link
    try:
        link.symlink_to(real, target_is_directory=True)
    except OSError:
        pytest.skip("symlink unavailable")
    with pytest.raises(ValueError, match="link"):
        core.generate(source, target, shell, "copy", True)


def test_raced_report_is_preserved(tmp_path, monkeypatch):
    output = tmp_path / "recipe.sh"
    real = core.generate

    def raced(*a, **kw):
        recipe = real(*a, **kw)
        output.write_text("concurrent")
        return recipe

    monkeypatch.setattr("save_backup_recipe.cli.generate", raced)
    assert main([str(tmp_path / "source"), str(tmp_path / "target"), "--output", str(output)]) == 2
    assert output.read_text() == "concurrent"


def test_dangling_recipe_output_preserved(tmp_path):
    output, missing = tmp_path / "recipe", tmp_path / "missing"
    try:
        output.symlink_to(missing)
    except OSError:
        pytest.skip("symlink unavailable")
    assert main([str(tmp_path / "source"), str(tmp_path / "target"), "--output", str(output)]) == 2
    assert output.is_symlink() and not missing.exists()
