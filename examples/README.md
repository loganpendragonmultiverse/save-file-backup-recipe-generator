# Examples

```bash
save-backup-recipe "C:\Games\Example\Saves" "D:\Save Backups\Example-2026-07-26" --shell powershell --mode copy --output backup.ps1
save-backup-recipe "$HOME/.local/share/example/saves" "/mnt/backup/example.tar.gz" --shell bash --mode archive --output backup.sh
```

Read the generated script and verify both paths before running it.
