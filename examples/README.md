# Examples

```bash
save-backup-recipe "C:\Games\Example\Saves" "D:\Save Backups\Example-2026-07-26" --shell powershell --mode copy --output backup.ps1
save-backup-recipe "$HOME/.local/share/example/saves" "/mnt/backup/example.tar.gz" --shell bash --mode archive --output backup.sh
```

Read the generated script and verify both paths before running it.

Generate on the execution host path model. Prefer `--mode copy --verify` for saves containing hidden files; PowerShell archive mode can omit them. A source directory named `-saves` remains a positional tar member, not an option. Recipes are printed for deliberate review, never executed by the generator.
