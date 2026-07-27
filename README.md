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
