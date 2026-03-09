# test/ucs-gui-tests/

Not a Debian package. Contains GUI-level automated tests for the UCS installation process.

## Structure

- `installation/` -- Python test scripts for validating the UCS installer UI.
  - `conftest.py` -- Pytest fixtures for VM-based GUI testing.
  - `test_*.py` -- Test cases for installation checks, screenshots, and application installation.
  - `vminstall/` -- VM installation automation helpers (VNC-based interaction).
