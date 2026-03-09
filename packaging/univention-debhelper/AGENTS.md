# univention-debhelper

Helper programs for `debian/rules` that automate common tasks related to building UCS Debian packages (installing UCR templates, join scripts, etc.). Transitional package; core functionality has moved to `univention-join-dev`.

## Binary Packages

- `univention-debhelper` -- Transitional metapackage (depends on `univention-join-dev`)
- `python3-univention-debhelper` -- Python 3 helper library for debian/rules

## Directory Structure

- `univention/` -- Python package (`univention.debhelper`)
- `setup.py` -- Python packaging
