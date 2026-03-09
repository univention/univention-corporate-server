# univention-directory-manager-modules

UCS Directory Manager (UDM) core: Python modules implementing LDAP object types (users, groups, computers, policies, etc.), CLI tools (`univention-directory-manager`), and authorization framework.

## Binary packages

- `python3-univention-directory-manager` -- Core UDM Python library
- `python3-univention-directory-manager-cli` -- CLI client Python modules
- `univention-directory-manager-tools` -- Command-line tools (`udm`)

## Directory structure

- `modules/` -- UDM handler modules (`univention.admin.handlers.*`)
- `python-lib/` -- Shared Python library code
- `listener/` -- Directory Listener modules
- `conffiles/` -- UCR templates
- `scripts/` -- Helper and migration scripts
- `unittests/` -- Unit tests
- `doc/` -- Documentation
- `debian/` -- Debian packaging
