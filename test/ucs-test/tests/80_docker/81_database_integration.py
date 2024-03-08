#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test Database integration of Docker Apps
## tags: [docker]
## bugs: [42690]
## exposure: dangerous
## packages:
##   - docker.io

from subprocess import check_output
from textwrap import dedent

import pytest

from univention.testing.utils import restart_firewall

from dockertest import tiny_app


@pytest.fixture(autouse=True)
def cleanup_restart_firewall():
    yield
    # make sure that all ports used by mysql and postgres are properly closed
    print('restart_firewall')
    restart_firewall()


@pytest.mark.parametrize('database', ['mysql', 'postgresql'])
def test_database_integration(appcenter, database, app_name, app_version):
    try:
        app = tiny_app(app_name, app_version)
        app.set_ini_parameter(Database=database)
        app.add_script(uinst=dedent(f'''\
            #!/bin/bash
            VERSION=1
            . /usr/share/univention-join/joinscripthelper.lib
            joinscript_init
            mysql -u root -p$(cat /etc/mysql.secret) {app_name} -e "DROP DATABASE IF EXISTS {app_name}"
            su postgres -c "psql -c 'DROP DATABASE IF EXISTS {app_name}'"
            joinscript_remove_script_from_status_file {app_name}
            exit 0'''))
        app.add_to_local_appcenter()
        appcenter.update()
        for i in [1, 2]:
            print('#### ', i)
            app.install()
            if database == 'mysql':
                output = check_output(['mysql', '-u', 'root', f'-p{open("/etc/mysql.secret").read().strip()}', 'INFORMATION_SCHEMA', '-e', f"SELECT SCHEMA_NAME FROM SCHEMATA WHERE SCHEMA_NAME = '{app_name}'"], text=True)  # noqa: S608
            elif database == 'postgresql':
                output = check_output(['su', 'postgres', '-c', 'psql -l'], text=True)
            print(output)
            assert app_name in output, f'No {database} database named {app_name} found in run #{i}'
            app.uninstall()
    except Exception:
        app.uninstall()
        raise
    finally:
        app.remove()
