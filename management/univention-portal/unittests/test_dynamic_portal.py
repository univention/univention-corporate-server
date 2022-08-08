#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
#


import pytest


def test_get_dynamic_classes(dynamic_class):
	assert dynamic_class("Portal")
	with pytest.raises(KeyError):
		dynamic_class("NotExistingPortal...")


def test_arg_kwargs(portal_factory, mocker):
	import datetime

	mocker.patch.object(portal_factory, "get_dynamic_classes", return_value=datetime.timedelta)
	delta_def = {"type": "class", "class": "timedelta", "args": [{"type": "static", "value": 0}, {"type": "static", "value": 10}], "kwargs": {"microseconds": {"type": "static", "value": 500}}}
	delta = portal_factory.make_arg(delta_def)
	assert delta.days == 0
	assert delta.seconds == 10
	assert delta.microseconds == 500


def test_make_portal_standard(portal_factory, dynamic_class):
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
	portal = portal_factory.make_portal(portal_def)
	assert isinstance(portal, Portal)


def test_make_portal_unknown(portal_factory):
	portal_def = {
		"type": "unknown",
		"class": "Portal",
	}
	with pytest.raises(TypeError):
		portal_factory.make_portal(portal_def)
