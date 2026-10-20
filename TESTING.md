# Testing

Run `python -m pip install -e ".[dev]"`, `ruff format --check .`,
`ruff check .`, `pytest`, and `python -m build`.

Execution tests create disposable fixture trees and run generated Bash/PowerShell
recipes only there. They cover Unicode and shell metacharacters, hidden and empty
files, missing sources, target collisions, mismatches and source preservation.
A missing shell skips its execution cases; verify both shell suites before release.

Root and ancestor link fixtures are created after recipe generation to exercise
execution-host checks. Destination replacements after copy must fail verification.
Windows-only junction fixtures complement portable directory symlink cases.

## Path and recipe limits

Generate recipes on the same operating-system path model as the execution host. Paths are host-local and expanded/resolved at generation; this is not a Windows/POSIX path translator. Verification rejects existing root/ancestor symlinks and reparse points before generation can resolve away their spelling, and retains execution-host checks for links introduced later.

Version 1.1.1 protects new recipe outputs with exclusive creation and rejects dangling destination links. Generated Bash archive commands separate option parsing from source basenames, including names beginning with a dash. Bash copy/archive recipes reject dangling destination links at execution; PowerShell checks hidden/link entries as well as ordinary paths. Direct API `verify` must be a boolean.

Archive mode creates an unverified convenience archive: PowerShell Compress-Archive can omit hidden/system entries and has platform/size limits. For save folders with hidden data, prefer copy mode with `--verify`; no archive mode claims complete backup or restorability. The generator never runs a recipe, and does not schedule, sync, delete, restore or find save folders. Guards protect ordinary existing destinations, not hostile concurrent filesystem mutation.

Installed distributions must include README, DEVELOPMENT, TESTING, CHANGELOG, LICENSE and the example guide under share/doc. Inspect both wheel metadata/data payload and source-distribution contents before release.
