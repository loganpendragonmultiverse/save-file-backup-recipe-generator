# Development

Use an isolated checkout and synthetic fixtures only. Generation never executes
recipes. Preserve default output, path quoting and collision guards.

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
