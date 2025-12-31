#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#


import pytest


def test_get_dynamic_classes(dynamic_class):
    assert dynamic_class("Portal")
    with pytest.raises(KeyError):
        dynamic_class("NotExistingPortal...")


def test_arg_kwargs(mocker):
    import datetime

    from univention.portal import factory

    mocker.patch.object(factory, "get_dynamic_classes", return_value=datetime.timedelta)
    delta_def = {"type": "class", "class": "timedelta", "args": [{"type": "static", "value": 0}, {"type": "static", "value": 10}], "kwargs": {"microseconds": {"type": "static", "value": 500}}}
    delta = factory.make_arg(delta_def)
    assert delta.days == 0
    assert delta.seconds == 10
    assert delta.microseconds == 500


def test_make_portal_standard(dynamic_class):
    from univention.portal import factory

    # more or less `univention-portal add ""`
    Portal = dynamic_class("Portal")
    portal_def = {
        "class": "Portal",
        "kwargs": {
            "portal_cache": {
                "class": "PortalFileCache",
                "kwargs": {
                    "cache_file": {"type": "static", "value": "/var/cache/univention-portal/portal.json"},
                    "reloader": {
                        "class": "PortalReloaderUDM",
                        "kwargs": {
                            "cache_file": {"type": "static", "value": "/var/cache/univention-portal/portal.json"},
                            "portal_dn": {"type": "static", "value": "cn=domain,cn=portal,cn=portals,cn=univention,dc=intranet,dc=example,dc=de"},
                        },
                        "type": "class",
                    },
                },
                "type": "class",
            },
            "authenticator": {
                "class": "UMCAuthenticator",
                "type": "class",
                "kwargs": {
                    "auth_mode": {"type": "static", "value": "ucs"},
                    "umc_session_url": {"type": "static", "value": "http://127.0.0.1:8090/get/session-info"},
                    "group_cache": {
                        "class": "GroupFileCache",
                        "kwargs": {
                            "cache_file": {"type": "static", "value": "/var/cache/univention-portal/groups.json"},
                            "reloader": {
                                "class": "GroupsReloaderLDAP",
                                "kwargs": {
                                    "binddn": {"type": "static", "value": "cn=master,cn=dc,cn=computers,dc=intranet,dc=example,dc=de"},
                                    "cache_file": {"type": "static", "value": "/var/cache/univention-portal/groups.json"},
                                    "ldap_base": {"type": "static", "value": "dc=intranet,dc=example,dc=de"},
                                    "ldap_uri": {"type": "static", "value": "ldap://master.intranet.example.de:7389"},
                                    "password_file": {"type": "static", "value": "/etc/machine.secret"},
                                },
                                "type": "class",
                            },
                        },
                        "type": "class",
                    },
                },
            },
            "scorer": {"class": "Scorer", "type": "class"},
        },
        "type": "class",
    }
    portal = factory.make_portal(portal_def)
    assert isinstance(portal, Portal)


def test_make_portal_unknown():
    from univention.portal import factory

    portal_def = {
        "type": "unknown",
        "class": "Portal",
    }
    with pytest.raises(TypeError):
        factory.make_portal(portal_def)
