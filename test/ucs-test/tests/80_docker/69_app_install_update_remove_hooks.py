#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Test appcenter hooks
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from pathlib import Path
from shlex import quote
from tempfile import NamedTemporaryFile

import pytest

from dockertest import App, Appcenter, tiny_app


ACTIONS = ["install", "upgrade", "remove"]


def hook_setup(app_name: str, file_result: str) -> None:
    """
    the setup creates the necessary script hook folders and places a script in
    each of them with the filename being the action name. The script will
    append its own name to `file_result` when executed.
    """
    # the same script will be placed in all script hook folders, always named
    # after the action it is for.  It prints its filename into $result_file-
    # appends one line & that is the test condition.
    test_script = f'''#!/bin/sh
# This script prints the current date and its own name
date -Is
echo "$0" >>{quote(file_result)}'''

    for action in ACTIONS:
        script_hook_path = Path("/var/lib/univention-appcenter/apps") / app_name / "local" / "hooks" / f"post-{action}.d" / action
        script_hook_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        script_hook_path.write_text(test_script)
        script_hook_path.chmod(0o755)


def app_install(appcenter: Appcenter, app_name: str) -> App:
    app = tiny_app(app_name, '3.6')
    app.set_ini_parameter(DockerImage='docker-test.software-univention.de/alpine:3.6')

    app.add_to_local_appcenter()
    appcenter.update()

    app.install()
    app.verify(joined=False)
    return app


def app_upgrade(appcenter: Appcenter, app_name: str) -> App:
    app = tiny_app(app_name, '3.7')
    app.set_ini_parameter(DockerImage='docker-test.software-univention.de/alpine:3.7')

    app.add_to_local_appcenter()
    appcenter.update()

    app.upgrade()
    app.verify(joined=False)
    return app


@pytest.mark.exposure('dangerous')
def test_app_install_update_remove_hooks(appcenter: Appcenter, app_name: str) -> None:
    """
    This test tests three hook directories: install, update and remove. Each of
    these actions should then execute its hook scripts and if that works a
    resulting log file contains their script file names.
    """
    with NamedTemporaryFile("r+") as file_result:
        hook_setup(app_name, file_result.name)

        print("APP INSTALL")
        app = app_install(appcenter, app_name)
        try:
            print("APP UPGRADE")
            app = app_upgrade(appcenter, app_name)
        finally:
            app.uninstall()
            app.remove()

        result = file_result.read()

    assert all(action in result for action in ACTIONS), result


# vim: ft=python
