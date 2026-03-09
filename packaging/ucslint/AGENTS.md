# ucslint

Linter that checks Debian source packages against common UCS packaging mistakes. Runs a series of numbered check modules (e.g. copyright headers, UCR template correctness, debian/control validation).

## Binary Packages

- `ucslint`

## Directory Structure

- `univention/` -- Python package with check modules (`univention.ucslint.*`)
- `testframework/` -- Test infrastructure for ucslint checks
- `doc/` -- Documentation
- `ucslint` -- Main entry-point script
- `ucslint-pre-commit` -- Pre-commit hook wrapper
- `setup.py`, `setup.cfg` -- Python packaging
