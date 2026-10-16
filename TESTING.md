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
