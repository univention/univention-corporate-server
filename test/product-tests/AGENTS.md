# test/product-tests/

Not a Debian package. Contains shell-based product-level integration test scripts organized by UCS component.

## Structure

- `appcenter/` -- App Center product tests.
- `base/` -- Base system product tests.
- `component/` -- Component-level tests.
- `domain-join/` -- Domain join workflow tests.
- `samba/` -- Samba/AD product tests.
- `ucsschool/` -- UCS@school product tests.
- `umc/` -- UMC (Univention Management Console) product tests.

These scripts are typically invoked by CI scenarios defined in `test/scenarios/`.
