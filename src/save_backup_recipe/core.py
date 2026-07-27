from __future__ import annotations

import shlex
from pathlib import Path


def validate_paths(source: Path, destination: Path) -> tuple[Path, Path]:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if source == destination:
        raise ValueError("source and destination must differ")
    if source in destination.parents:
        raise ValueError("destination cannot be inside the source folder")
    return source, destination


def _ps(value: Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def powershell_recipe(source: Path, destination: Path, mode: str) -> str:
    source, destination = validate_paths(source, destination)
    lines = [
        "$ErrorActionPreference = 'Stop'",
        f"$saveSource = {_ps(source)}",
        f"$backupTarget = {_ps(destination)}",
        "if (-not (Test-Path -LiteralPath $saveSource -PathType Container)) { throw 'Save folder not found.' }",
    ]
    if mode == "copy":
        lines.extend(
            [
                "if (Test-Path -LiteralPath $backupTarget) { throw 'Backup target already exists.' }",
                "Copy-Item -LiteralPath $saveSource -Destination $backupTarget -Recurse",
            ]
        )
    elif mode == "archive":
        lines.extend(
            [
                "if (Test-Path -LiteralPath $backupTarget) { throw 'Backup archive already exists.' }",
                "Compress-Archive -LiteralPath $saveSource -DestinationPath $backupTarget",
            ]
        )
    else:
        raise ValueError("mode must be copy or archive")
    lines.append("Write-Host 'Backup completed. Verify the result before relying on it.'")
    return "\n".join(lines) + "\n"


def bash_recipe(source: Path, destination: Path, mode: str) -> str:
    source, destination = validate_paths(source, destination)
    src, dst = shlex.quote(str(source)), shlex.quote(str(destination))
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"save_source={src}",
        f"backup_target={dst}",
        "[[ -d \"$save_source\" ]] || { echo 'Save folder not found.' >&2; exit 1; }",
        "[[ ! -e \"$backup_target\" ]] || { echo 'Backup target already exists.' >&2; exit 1; }",
    ]
    if mode == "copy":
        lines.append('cp -a -- "$save_source" "$backup_target"')
    elif mode == "archive":
        lines.append(
            'tar -czf "$backup_target" -C "$(dirname "$save_source")" "$(basename "$save_source")"'
        )
    else:
        raise ValueError("mode must be copy or archive")
    lines.append("echo 'Backup completed. Verify the result before relying on it.'")
    return "\n".join(lines) + "\n"


def generate(source: Path, destination: Path, shell: str, mode: str) -> str:
    if shell == "powershell":
        return powershell_recipe(source, destination, mode)
    if shell == "bash":
        return bash_recipe(source, destination, mode)
    raise ValueError("shell must be powershell or bash")
