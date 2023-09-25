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

from dockertest import get_app_name, get_app_version, tiny_app


@pytest.fixture(autouse=True)
def cleanup_restart_firewall():
    yield
    # make sure that all ports used by mysql and postgres are properly closed
    print('restart_firewall')
    restart_firewall()


@pytest.mark.parametrize('database', ['mysql', 'postgresql'])
def test_database_integration(appcenter, database):
    try:
        app_name = get_app_name()
        app_version = get_app_version()
        app = tiny_app(app_name, app_version)
        app.set_ini_parameter(Database=database)
        app.add_script(uinst=dedent('''\
            #!/bin/bash
            VERSION=1
            . /usr/share/univention-join/joinscripthelper.lib
            joinscript_init
            mysql -u root -p$(cat /etc/mysql.secret) %s -e "DROP DATABASE IF EXISTS %s"
            su postgres -c "psql -c 'DROP DATABASE IF EXISTS %s'"
            joinscript_remove_script_from_status_file %s
            exit 0''' % (app_name, app_name, app_name, app_name)))
        app.add_to_local_appcenter()
        appcenter.update()
        for i in [1, 2]:
            print('#### ', i)
            app.install()
            if database == 'mysql':
                output = check_output(['mysql', '-u', 'root', '-p%s' % (open('/etc/mysql.secret').read().strip()), 'INFORMATION_SCHEMA', '-e', "SELECT SCHEMA_NAME FROM SCHEMATA WHERE SCHEMA_NAME = '%s'" % app_name], text=True)  # noqa: S608
            elif database == 'postgresql':
                output = check_output(['su', 'postgres', '-c', 'psql -l'], text=True)
            print(output)
            assert app_name in output, 'No %s database named %s found in run #%d' % (database, app_name, i)
            app.uninstall()
    except Exception:
        app.uninstall()
        raise
    finally:
        app.remove()
