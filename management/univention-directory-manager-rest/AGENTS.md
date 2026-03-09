# univention-directory-manager-rest

REST API service for UCS Directory Manager, providing HTTP access to UDM objects via a Tornado-based web service.

## Binary packages

- `univention-directory-manager-rest` -- Service package
- `python3-univention-directory-manager-rest` -- Server-side Python library
- `python3-univention-directory-manager-rest-client` -- Synchronous Python client library
- `python3-univention-directory-manager-rest-async-client` -- Async Python client library

## Directory structure

- `src/` -- Python source code (server and client)
- `conffiles/` -- UCR templates
- `listener/` -- Directory Listener modules
- `templates/` -- Jinja2/Genshi templates
- `usr/`, `var/` -- Installed file layouts
- `debian/` -- Debian packaging
