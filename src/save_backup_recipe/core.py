from __future__ import annotations

import shlex
from pathlib import Path


def validate_paths(source: Path, destination: Path, verify: bool = False) -> tuple[Path, Path]:
    if type(verify) is not bool:
        raise TypeError("verify must be a boolean")
    if destination.expanduser().is_symlink():
        raise ValueError("destination already exists as a symbolic link")
    if verify:
        for path in (source.expanduser().absolute(), destination.expanduser().absolute()):
            for node in (path, *path.parents):
                if (
                    node.is_symlink()
                    or (hasattr(node, "is_junction") and node.is_junction())
                    or (node.exists() and getattr(node.lstat(), "st_file_attributes", 0) & 0x400)
                ):
                    raise ValueError("verification paths must not contain links or reparse points")
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if source == destination:
        raise ValueError("source and destination must differ")
    if source in destination.parents:
        raise ValueError("destination cannot be inside the source folder")
    return source, destination


def _ps(value: Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def powershell_recipe(source: Path, destination: Path, mode: str, verify: bool = False) -> str:
    if verify and mode != "copy":
        raise ValueError("verification requires copy mode; archive verification is unsupported")
    source, destination = validate_paths(source, destination, verify)
    lines = [
        "$ErrorActionPreference = 'Stop'",
        f"$saveSource = {_ps(source)}",
        f"$backupTarget = {_ps(destination)}",
        "if (-not (Test-Path -LiteralPath $saveSource -PathType Container)) { throw 'Save folder not found.' }",
    ]
    if verify:
        lines.extend(POWERSHELL_SNAPSHOT.splitlines())
        lines.append("$beforeCopy = Get-SaveSnapshot $saveSource")
        lines.append("Assert-SaveDirectoryPath $saveSource")
        lines.append("Assert-SaveDirectoryPath $backupTarget")
    if mode == "copy":
        lines.extend(
            [
                "if ((Test-Path -LiteralPath $backupTarget) -or (Get-Item -LiteralPath $backupTarget -Force -ErrorAction SilentlyContinue)) { throw 'Backup target already exists.' }",
                "Copy-Item -LiteralPath $saveSource -Destination $backupTarget -Recurse",
            ]
        )
    elif mode == "archive":
        lines.extend(
            [
                "if ((Test-Path -LiteralPath $backupTarget) -or (Get-Item -LiteralPath $backupTarget -Force -ErrorAction SilentlyContinue)) { throw 'Backup archive already exists.' }",
                "Compress-Archive -LiteralPath $saveSource -DestinationPath $backupTarget",
            ]
        )
    else:
        raise ValueError("mode must be copy or archive")
    if verify:
        lines = [line + " -Force" if line.startswith("Copy-Item ") else line for line in lines]
        lines.extend(POWERSHELL_VERIFY.splitlines())
    lines.append("Write-Host 'Backup completed. Verify the result before relying on it.'")
    return "\n".join(lines) + "\n"


def bash_recipe(source: Path, destination: Path, mode: str, verify: bool = False) -> str:
    if verify and mode != "copy":
        raise ValueError("verification requires copy mode; archive verification is unsupported")
    source, destination = validate_paths(source, destination, verify)
    src, dst = shlex.quote(str(source)), shlex.quote(str(destination))
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"save_source={src}",
        f"backup_target={dst}",
        "[[ -d \"$save_source\" ]] || { echo 'Save folder not found.' >&2; exit 1; }",
        '[[ ! -e "$backup_target" && ! -L "$backup_target" ]] || { echo \'Backup target already exists.\' >&2; exit 1; }',
    ]
    if verify:
        lines.extend(BASH_SNAPSHOT.splitlines())
        lines.append('before_copy=$(save_snapshot "$save_source")')
    if mode == "copy":
        if verify:
            lines.extend(
                ['save_snapshot "$save_source" guard', 'save_snapshot "$backup_target" guard']
            )
        lines.append('cp -a -- "$save_source" "$backup_target"')
    elif mode == "archive":
        lines.append(
            'tar -czf "$backup_target" -C "$(dirname "$save_source")" -- "$(basename "$save_source")"'
        )
    else:
        raise ValueError("mode must be copy or archive")
    if verify:
        lines.extend(
            [
                '[[ "$before_copy" == "$(save_snapshot "$save_source")" ]] || { echo "Source changed during copy." >&2; exit 1; }',
                '[[ "$before_copy" == "$(save_snapshot "$backup_target")" ]] || { echo "Backup verification failed (file count or SHA-256 mismatch)." >&2; exit 1; }',
            ]
        )
    lines.append("echo 'Backup completed. Verify the result before relying on it.'")
    return "\n".join(lines) + "\n"


def generate(source: Path, destination: Path, shell: str, mode: str, verify: bool = False) -> str:
    if shell == "powershell":
        return powershell_recipe(source, destination, mode, verify)
    if shell == "bash":
        return bash_recipe(source, destination, mode, verify)
    raise ValueError("shell must be powershell or bash")


BASH_SNAPSHOT = r"""# Verification requires Python 3. Symlinks and special files are rejected.
save_snapshot() {
python3 - "$1" "${2:-snapshot}" <<'VERIFY_PY'
import hashlib
import json
import os
import stat
import sys
root = os.path.abspath(sys.argv[1])
components = []
current = root
while True:
    components.append(current)
    parent = os.path.dirname(current)
    if parent == current:
        break
    current = parent
for component in reversed(components):
    try:
        mode = os.lstat(component).st_mode
    except FileNotFoundError:
        break
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise SystemExit("Verification requires directory paths without links in roots or ancestors.")
if sys.argv[2] == "guard":
    sys.exit(0)
if not os.path.isdir(root) or os.path.islink(root):
    raise SystemExit("Verification requires an existing regular directory.")
entries = {}
def fail_walk(error):
    raise error
for directory, folders, files in os.walk(root, followlinks=False, onerror=fail_walk):
    for name in folders + files:
        path = os.path.join(directory, name)
        mode = os.lstat(path).st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise SystemExit("Verification requires regular files and directories.")
    for name in files:
        path = os.path.join(directory, name)
        digest = hashlib.sha256()
        with open(path, 'rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        entries[os.path.relpath(path, root)] = digest.hexdigest()
print(json.dumps({'file_count': len(entries), 'sha256': entries}, sort_keys=True, ensure_ascii=True))
VERIFY_PY
}"""

POWERSHELL_SNAPSHOT = r"""# Inventory includes hidden and empty files; links fail closed.
function Assert-SaveDirectoryPath([string]$Path) {
    $components = [System.Collections.Generic.List[string]]::new()
    $current = [System.IO.Path]::GetFullPath($Path)
    while ($current) {
        $components.Insert(0, $current)
        $parent = [System.IO.Directory]::GetParent($current)
        $current = if ($null -eq $parent) { $null } else { $parent.FullName }
    }
    foreach ($component in $components) {
        try {
            $entry = Get-Item -LiteralPath $component -Force -ErrorAction Stop
        } catch [System.Management.Automation.ItemNotFoundException] {
            return
        }
        if (($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -or -not $entry.PSIsContainer) {
            throw 'Verification requires directory paths without links in roots or ancestors.'
        }
    }
}
function Get-SaveSnapshot([string]$Root) {
    Assert-SaveDirectoryPath $Root
    $snapshot = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
    foreach ($entry in Get-ChildItem -LiteralPath $Root -Force -Recurse) {
        if ($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            throw 'Verification requires regular files and directories.'
        }
        if (-not $entry.PSIsContainer) {
            $relative = $entry.FullName.Substring($Root.TrimEnd([char[]]'\/').Length + 1)
            $snapshot.Add($relative, (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash)
        }
    }
    return ,$snapshot
}
function Assert-SaveSnapshot($Expected, $Actual) {
    if ($Expected.Count -ne $Actual.Count) { throw 'Backup verification failed (file count mismatch).' }
    foreach ($name in $Expected.Keys) {
        if (-not $Actual.ContainsKey($name) -or $Actual[$name] -ne $Expected[$name]) {
            throw 'Backup verification failed (SHA-256 or relative-path mismatch).'
        }
    }
}"""

POWERSHELL_VERIFY = r"""Assert-SaveSnapshot $beforeCopy (Get-SaveSnapshot $saveSource)
Assert-SaveSnapshot $beforeCopy (Get-SaveSnapshot $backupTarget)"""
