# Changelog

## 1.1.1 - 2026-10-20

- Protect recipe outputs with exclusive creation and dangling-link guards.
- Preserve verification link rejection before generation-time path resolution and validate boolean controls.
- Reject dangling backup targets in generated recipes and protect dash-leading archive source names.
- Document host-local path generation and unverified archive/hidden-file limitations.

## 1.1.0 - 2026-10-16

- Added opt-in copy verification using file counts, relative paths and SHA-256.
- Reject linked source/destination roots and existing ancestors at runtime, including PowerShell junctions.
- Added disposable fixture execution tests and kept default recipes unchanged.

## 1.0.0 - 2026-07-26

- Added PowerShell and Bash backup recipe generation.
- Added copy and compressed-archive modes with safe path quoting.
- Added existing-target, identical-path, and nested-destination guards.
