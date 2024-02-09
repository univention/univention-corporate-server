# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

import importlib.util
import os
import os.path


LISTENER_PATH = "./listener"


def load_listener(name):
    module_name = os.path.splitext(name)[0]
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(LISTENER_PATH, name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_portal_listener_uses_get_portal_call_update(mocker):
    # Avoid that unsetuid screws up the user during the test run
    mocker.patch("listener.__listener_uid", new=0)
    mocker.patch("subprocess.call")
    get_portal_update_call_mock = mocker.patch("univention.portal.util.get_portal_update_call")
    listener = load_listener("portal_server.py")

    listener.handler(dn="stub_dn", new={}, old={})

    get_portal_update_call_mock.assert_called()


def test_groups_listener_default_call(mocker):
    mocker.patch("subprocess.call")
    get_portal_update_call_mock = mocker.patch("univention.portal.util.get_portal_update_call")
    listener = load_listener("portal_groups.py")
    stub_config = listener.PortalGroups._get_configuration("stub_name")
    mocker.patch.object(listener.PortalGroups, "config", new=stub_config)

    instance = listener.PortalGroups()
    instance.post_run()

    get_portal_update_call_mock.assert_called()
