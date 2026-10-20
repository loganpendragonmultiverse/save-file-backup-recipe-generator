# Save-File Backup Recipe Generator

[![CI](https://github.com/loganpendragonmultiverse/save-file-backup-recipe-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/save-file-backup-recipe-generator/actions/workflows/ci.yml)

Save-File Backup Recipe Generator produces a transparent PowerShell or Bash script for copying or archiving a chosen game-save folder. It generates commands for review; it never executes the backup itself.

## Three-minute start

```bash
python -m pip install .
save-backup-recipe "C:\Games\Example\Saves" "D:\Backups\Example" --output backup.ps1
save-backup-recipe ~/.local/share/example/saves ~/backups/example.tar.gz --shell bash --mode archive
```

Generated recipes stop when the source folder is missing or the destination already exists. The generator rejects identical paths and destinations nested inside the source, quotes supplied paths for the selected shell, and reminds the operator to verify the result.

## Safety boundary

Generation does not prove that a game is closed, that cloud synchronization is idle, or that the selected folder contains every relevant save. Review the script, locate the authoritative save directory, run it deliberately, and test restoration before relying on a backup.

Requires Python 3.10 or newer. Development checks use Ruff, pytest with branch coverage, and package builds.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).

## Verify a copy before success

Use `--verify` with copy mode to inventory regular files before copying and compare
source and destination file counts, relative paths and SHA-256 hashes before the
success message. Hidden files and zero-byte files are included. Empty directories
are copied but are not part of the file inventory. Verification requires regular files and directories. Links are rejected;
special files such as devices and sockets are unsupported.

```bash
save-backup-recipe /tmp/example-saves /tmp/example-copy --shell bash --verify
```

This command only prints a recipe. Bash verification requires `python3` on the
execution host; PowerShell uses `Get-FileHash`. A mismatch or source change stops
the recipe and leaves the destination for manual review. No cleanup or restore
is performed. Verification is incompatible with archive mode. It compares the
copied files at that moment and does not establish that a live game or cloud sync
is idle; close them before running the reviewed recipe. Omit `--verify` to retain
the existing generated recipes.

Verification checks both source and destination roots and their existing ancestors
on the execution host. Symlinks and PowerShell reparse points (including junctions)
are rejected before inventory or copy and during post-copy checks. Destination
collisions still stop the recipe. These are point-in-time checks, not an atomic
filesystem operation: keep the game, sync software and other path-changing
processes stopped throughout execution. Do not run recipes against paths that
another process can replace concurrently.

## Path and recipe limits

Generate recipes on the same operating-system path model as the execution host. Paths are host-local and expanded/resolved at generation; this is not a Windows/POSIX path translator. Verification rejects existing root/ancestor symlinks and reparse points before generation can resolve away their spelling, and retains execution-host checks for links introduced later.

Version 1.1.1 protects new recipe outputs with exclusive creation and rejects dangling destination links. Generated Bash archive commands separate option parsing from source basenames, including names beginning with a dash. Bash copy/archive recipes reject dangling destination links at execution; PowerShell checks hidden/link entries as well as ordinary paths. Direct API `verify` must be a boolean.

Archive mode creates an unverified convenience archive: PowerShell Compress-Archive can omit hidden/system entries and has platform/size limits. For save folders with hidden data, prefer copy mode with `--verify`; no archive mode claims complete backup or restorability. The generator never runs a recipe, and does not schedule, sync, delete, restore or find save folders. Guards protect ordinary existing destinations, not hostile concurrent filesystem mutation.
