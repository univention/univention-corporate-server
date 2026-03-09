# univention-updater

System upgrade/update tool for UCS. Manages release upgrades, errata updates, and component updates. Includes a UMC web module.

## Binary Packages

- `univention-updater` -- main updater tool and scripts
- `python3-univention-updater` -- Python 3 library
- `univention-management-console-module-updater` -- UMC web module

## Key Directories

- `modules/` -- Python library (`univention.updater`)
- `umc/` -- UMC module (Python backend + JS frontend)
- `script/` -- updater scripts (preup, postup, etc.)
- `conffiles/` -- UCR templates
- `tests/` -- pytest test suite
- `doc/` -- documentation
- `appliance-hooks.d/` -- hooks for appliance updates
- `bash_completion.d/` -- bash completions

## Key Files

- `35univention-management-console-module-updater.inst` -- join script
- `setup.py`, `setup.cfg` -- setuptools configuration
- `conftest.py` -- pytest fixtures

## Notes

- Has extensive pytest-based tests
- Includes a UMC module
- Docker support for testing (`Dockerfile`, `docker-compose.yaml`)
