"""Execute recipes only inside pytest's disposable synthetic fixture trees."""

import hashlib
import os
import shutil
import subprocess

import pytest

from save_backup_recipe.cli import main
from save_backup_recipe.core import generate


def hashes(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def fixture(root):
    root.mkdir()
    (root / "nested").mkdir()
    for name in [".hidden", "empty", "quote' $dollar; [bracket] & ünicode", "nested/slot"]:
        (root / name).write_bytes(b"" if name == "empty" else b"synthetic save")


def run_recipe(tmp_path, shell, script):
    if shell == "bash" and os.name == "nt":
        pytest.skip("Bash fixtures require a native POSIX host")
    executable = shutil.which("bash" if shell == "bash" else "pwsh")
    if not executable:
        pytest.skip(f"{shell} unavailable")
    path = tmp_path / ("recipe.sh" if shell == "bash" else "recipe.ps1")
    path.write_text(script, encoding="utf-8")
    args = (
        [executable, str(path)]
        if shell == "bash"
        else [executable, "-NoProfile", "-File", str(path)]
    )
    return subprocess.run(args, check=False, capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize("shell", ["bash", "powershell"])
@pytest.mark.parametrize(
    "condition", ["success", "missing", "collision", "hash", "count", "source-change"]
)
def test_disposable_execution(tmp_path, shell, condition):
    source = tmp_path / "source ' $x; [ü]"
    target = tmp_path / "target ' $x; [ü]"
    if condition != "missing":
        fixture(source)
    if condition == "collision":
        target.mkdir()
        (target / "keep").write_text("untouched")
    original = hashes(source)
    script = generate(source, target, shell, "copy", True)
    # Inject controlled corruption after the real copy to prove verification fails before success.
    if condition in {"hash", "count", "source-change"}:
        if shell == "bash":
            mutation = (
                'printf corrupt > "$backup_target/nested/slot"'
                if condition == "hash"
                else 'printf extra > "$backup_target/extra"'
                if condition == "count"
                else 'printf changed > "$save_source/nested/slot"'
            )
            script = script.replace(
                'cp -a -- "$save_source" "$backup_target"',
                'cp -a -- "$save_source" "$backup_target"\n' + mutation,
            )
        else:
            mutation = (
                "[IO.File]::WriteAllText((Join-Path $backupTarget 'nested/slot'), 'corrupt')"
                if condition == "hash"
                else "[IO.File]::WriteAllText((Join-Path $backupTarget 'extra'), 'extra')"
                if condition == "count"
                else "[IO.File]::WriteAllText((Join-Path $saveSource 'nested/slot'), 'changed')"
            )
            script = script.replace("-Recurse -Force", "-Recurse -Force\n" + mutation)
    result = run_recipe(tmp_path, shell, script)
    assert (result.returncode == 0) is (condition == "success"), result.stdout + result.stderr
    assert ("Backup completed" in result.stdout) is (condition == "success")
    if condition != "source-change":
        assert hashes(source) == original
    if condition == "success":
        assert hashes(target) == original
    if condition == "collision":
        assert (target / "keep").read_text() == "untouched"


@pytest.mark.parametrize("shell", ["bash", "powershell"])
def test_opt_in_and_archive_rejection(tmp_path, shell):
    source, target = tmp_path / "in", tmp_path / "out"
    assert generate(source, target, shell, "copy") == generate(source, target, shell, "copy", False)
    assert "SHA-256" not in generate(source, target, shell, "copy")
    with pytest.raises(ValueError, match="copy mode"):
        generate(source, target, shell, "archive", True)
    assert main([str(source), str(target), "--shell", shell, "--verify"]) == 0
    assert main([str(source), str(target), "--mode", "archive", "--verify"]) == 2


@pytest.mark.parametrize("shell", ["bash", "powershell"])
def test_empty_tree_and_link_rejection(tmp_path, shell):
    source, target = tmp_path / "in", tmp_path / "out"
    source.mkdir()
    script = generate(source, target, shell, "copy", True)
    assert run_recipe(tmp_path, shell, script).returncode == 0
    other = tmp_path / "linked-out"
    try:
        (source / "link").symlink_to(tmp_path / "missing")
    except OSError:
        pytest.skip("symlink unavailable")
    result = run_recipe(tmp_path, shell, generate(source, other, shell, "copy", True))
    assert result.returncode != 0
    assert "Backup completed" not in result.stdout
