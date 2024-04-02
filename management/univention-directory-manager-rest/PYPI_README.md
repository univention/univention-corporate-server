# UDM REST API Client

[![PyPI - Version](https://img.shields.io/pypi/v/udm-rest-api-client.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.python.org/pypi/udm-rest-api-client/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/udm-rest-api-client.svg?logo=python&label=Python&logoColor=gold)](https://pypi.python.org/pypi/udm-rest-api-client)
[![License - AGPLv3](https://img.shields.io/github/license/univention/univention-corporate-server)](https://github.com/univention/univention-corporate-server/blob/5.2-0/LICENSE)
[![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)

Client library and CLI to interact with the [Univention Directory Manager (UDM) REST API](https://docs.software-univention.de/developer-reference/latest/en/udm/rest-api.html).

## Features

* Asynchronous and synchronous Python functions
* Command line interface
* Automatic handling of HTTP(S) sessions
* Type annotations
* Python 3.7+

## Usage

### Synchronous Python code

```python
from univention.admin.rest.client import UDM

udm = UDM.http("https://10.20.30.40/univention/udm/", "Administrator", "s3cr3t")
module = udm.get("users/user")

# 1. create a user
obj = module.new()
obj.properties["username"] = "foo"
obj.properties["password"] = "univention"
obj.properties["lastname"] = "foo"
obj.save()

# 2. search for users
for result in module.search("uid=*"):
    obj = result.open()
    print(obj)
    print(obj.properties)
    print(obj.objects.groups)

# 3. get by dn
ldap_base = udm.get_ldap_base()
obj = module.get(f"uid=foo,cn=users,{ldap_base}")

# 4. get referenced objects e.g. groups
pg = obj.objects["primaryGroup"].open()
print(pg.dn, pg.properties)
print(obj.objects["groups"])

# 5. modify
obj.properties["description"] = "foo"
obj.save()

# 6. move to the ldap base
obj.move(ldap_base)

# 7. remove
obj.delete()
```

### Asynchronous Python code

```python
import asyncio
from univention.admin.rest.async_client import UDM

async def main():
    async with UDM.http("http://10.20.30.40./univention/udm/", "Administrator", "s3cr3t") as udm:
        module = await udm.get("users/user")

        # 1. create a user
        obj = await module.new()
        obj.properties["username"] = "foo"
        obj.properties["password"] = "univention"
        obj.properties["lastname"] = "foo"
        await obj.save()

        # 2. search for users
        async for result in module.search("uid=*"):
            obj = await result.open()
            print(obj)
            print(obj.properties)
            print(obj.objects.groups)

        # 3. get by dn
        ldap_base = await udm.get_ldap_base()
        obj = await module.get(f"uid=foo,cn=users,{ldap_base}")

        # 4. get referenced objects e.g. groups
        pg = await obj.objects["primaryGroup"].open()
        print(pg.dn, pg.properties)
        print(obj.objects["groups"])

        # 5. modify
        obj.properties["description"] = "foo"
        await obj.save()

        # 6. move to the ldap base
        await obj.move(ldap_base)

        # 7. remove
        await obj.delete()

asyncio.run(main())
```

### Command line interface

```shell
PASS_FILE="$HOME/pw-$(date +%Y%m%d%H%M%S)"
echo "s3cr3t" > "$PASS_FILE"

udm \
  --username Administrator \
  --bindpwdfile "$PASS_FILE" \
  --uri http://10.20.30.40/univention/udm/ \
  users/user list \
  --filter uid=Administrator

rm -f "$PASS_FILE"
```

Instead of using `udm`, the CLI can also be called using `python3 -m univention.admin.rest.client`.

### Error codes

Error codes and other details of the UDM REST API can be found in its [documentation](https://docs.software-univention.de/developer-reference/latest/en/udm/rest-api.html#api-error-codes).

## Installation

The dependencies for the CLI, synchronous and asynchronous clients differ.
They are available separately as "extra" dependencies, to reduce your projects total dependencies.
Without installing the "extra" requirements, only the common dependencies of the three interfaces will be installed, and none will be usable.

* `async`: installs `aiohttp`
* `sync`: installs `requests`
* `cli`: installs `python-ldap` and `requests`

To install the library including the dependencies for the asynchronous client via pip from PyPI run:

```shell
pip install udm-rest-api-client[async]
```

To install the CLI (incl. the required library and its dependencies):

```shell
pip install udm-rest-api-client[cli]
```

Multiple extras can be specified at the same time:

```shell
pip install udm-rest-api-client[async,cli,dev,sync]
```

### CLI and pipx

If you wish to use the `udm` command line interface from anywhere in your system,
without having to manually handle virtual environments,
install it using [pipx](https://pipx.pypa.io):

```shell
pipx install udm-rest-api-client[cli]
```

```shell
which udm
$HOME/.local/bin/udm
```

## License

The _UDM REST API Client_ is distributed under the terms of the [GNU Affero General Public License v3.0 only (AGPLv3)](https://spdx.org/licenses/AGPL-3.0-only.html) license.
