# univention-portal

Central portal web page for a UCS domain. Provides a configurable, customizable overview of all installed apps and services. Includes a Vue.js frontend and a Tornado-based backend server.

## Binary packages

- `univention-portal` -- Portal server, listener modules, and CLI tools
- `python3-univention-portal` -- Python library

## Directory structure

- `python/` -- Python source (`univention.portal`)
- `frontend/` -- Vue.js frontend application
- `listener/` -- Directory Listener modules
- `conffiles/` -- UCR templates
- `udm/` -- UDM module extensions for portal entries
- `unittests/` -- Unit tests
- `docs/` -- Documentation
- `debian/` -- Debian packaging
