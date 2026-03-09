# univention-self-service

User self-service: password reset without administrator intervention, account invitations, and profile management.

## Binary packages

- `univention-self-service` -- Self-service meta package
- `univention-self-service-master` -- Dependencies for Primary Directory Node
- `univention-self-service-passwordreset-umc` -- UMC backend for password reset
- `univention-self-service-invitation` -- Invitation listener and daemon

## Directory structure

- `umc/` -- UMC module (Python backend + JS frontend)
- `listener/` -- Directory Listener modules
- `conffiles/` -- UCR templates
- `hook/` -- Hook scripts
- `portal/` -- Portal entry definitions
- `icons/` -- Icon assets
- `unittests/` -- Unit tests
- `doc/` -- Documentation
- `debian/` -- Debian packaging
