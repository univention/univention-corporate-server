#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Test appcenter hooks
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import os
import stat
import sys
import pytest

from dockertest import get_app_name, tiny_app


class AssertionFailed(Exception):
    pass


actions = ["install", "upgrade", "remove"]
# a log file to store the results (line based)...
file_result = "/tmp/69_app_install_update_remove_hooks.result"
# the path, where -by convention- script hooks have to be stored (app specific)
path_hooks = "/var/lib/univention-appcenter/apps/{appid}/local/hooks"

color_highlight = "\033[0;31m"
color_reset = "\033[0;0m"


def get_code_position(depth=1, line_length=80, fill_char='.', prefix="# ", color_start="", color_stop=""):
    """
    The function draws a fixed length line (80 columns) and displays the
    position in the code from where it is called. The rest of the line
    is filled with dots.

    @param depth: is usually `1` if this function is called directly, but if
    a wrapper function calls this function it would become `2`. It basically
    says how far away the code position is on the call stack.
    @param line_length: the output will have fixed length. @see: fill_char
    @param fill_char: fills up the remaining line with this character
    @param prefix: prepend the output line with this string
    @param color_start: Could be "\033[0;31m" for red or \033[0;32m for green
    @param color_stop: should reset the color to default, usually "\033[0;0m"
    """
    if hasattr(sys, '_getframe'):
        # not every Python version has a _getframe function. We will only
        # return a separator, if we cannot determine the position.
        return ((color_start + prefix + "%-*s" + color_stop) % (
                line_length - len(prefix),
                sys._getframe(depth).f_code.co_filename + ":" + str(sys._getframe(depth).f_lineno) + ' [' + sys._getframe(depth).f_code.co_name + ']')).replace('  ', fill_char + fill_char)
    else:
        return color_start + ("%80s" % '').replace(' ', '=') + color_stop


def setup(app_name):
    """
    the setup creates the necessary script hook folders and places a script in
    each of them with the filename being the action name. The script will
    append its own name to `file_result` when executed.
    """
    # try to create an empty result file...
    with open(file_result, "w") as f:
        f.close()

    # the same script will be placed in all script hook folders, always named
    # after the action it is for.  It prints its filename into $result_file-
    # appends one line & that is the test condition.
    test_script = '''#!/bin/sh
# This script prints the current date and its own name
date -Is
echo "$0" >> {file_result}'''.format(file_result=file_result)
    #   ^ NOTE: ticks are intentional!

    for action in actions:

        script_hook_path = '{hook_path}/post-{action}.d'.format(
            hook_path=path_hooks.format(appid=app_name),
            action=action,
        )

        script_hook_file = "{pathname}/{filename}".format(
            pathname=script_hook_path,
            filename=action,
        )

        # create the hook directory only if it does not exist yet
        try:
            os.makedirs(script_hook_path, mode=0o777)
        except Exception:
            # we know well enough what went wrong and can savely ignore it. In
            # python3 however os.makedirs has an `exist_ok`-parameter which should
            # be used instead of this block.
            pass

        try:
            # create a script file in the hook directory...
            with open(script_hook_file, 'w') as f:
                f.write(test_script)

            # add the executable flag to the file permissions...
            os.chmod(
                script_hook_file,
                os.stat(script_hook_file).st_mode | stat.S_IEXEC)

        except Exception as e:
            print("Error with file '{filename}': {error}".format(
                error=e,
                filename=script_hook_file),
            )


def app_install(appcenter, app_name):
    print(get_code_position(color_start=color_highlight, color_stop=color_reset))

    app = tiny_app(app_name, '3.6')
    app.set_ini_parameter(DockerImage='docker-test.software-univention.de/alpine:3.6')

    app.add_to_local_appcenter()
    appcenter.update()

    app.install()  # install the app
    app.verify(joined=False)
    return app


def app_upgrade(appcenter, app_name):
    print(get_code_position(color_start=color_highlight, color_stop=color_reset))

    app = tiny_app(app_name, '3.7')
    app.set_ini_parameter(DockerImage='docker-test.software-univention.de/alpine:3.7')

    app.add_to_local_appcenter()
    appcenter.update()

    app.upgrade()  # now upgrade the app
    app.verify(joined=False)
    return app


def app_remove(app):
    print(get_code_position(color_start=color_highlight, color_stop=color_reset))

    app.uninstall()
    app.remove()


def verify_test_results_and_exit():
    """
    function outputs all test results and checks if the result file contains
    the names of all actions (install/upgrade/remove).
    """
    with open(file_result) as f:

        # now check if all actions were executed and abort otherwise...
        for action in actions:
            f.seek(0)  # rewind before every new search
            if action not in f.read():
                raise (AssertionFailed(
                    "Expected to find '%s' in file '%s',"
                    " but it was not there." % (action, file_result)), 2)


@pytest.mark.exposure('dangerous')
def test_app_install_update_remove_hooks(appcenter, app_name):
    """
    This test tests three hook directories: install, update and remove. Each of
    these actions should then execute its hook scripts and if that works a
    resulting log file contains their script file names.
    """


    setup(app_name)

    app = app_install(appcenter, app_name)
    app = app_upgrade(appcenter, app_name)
    app_remove(app)

    verify_test_results_and_exit()


# vim: ft=python
