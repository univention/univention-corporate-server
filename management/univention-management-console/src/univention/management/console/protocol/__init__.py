#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#
# Copyright 2006-2019 Univention GmbH
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

"""
This new generation of UMCP is based on the version 1.0 but is not
compatible.

This protocol is used by the UMC server for external clients and between
the UMC server and its UMC module processes.

---------
Data flow
---------

The protocol is based on a server/client model. The client sends
requests to the server that will be answered with a response message by
the server.

With a status code in the response message the client can determine the
type of result of its request:

* An error occurred during the processing of the request. The status
	code contains details of the error

* The command was processed successfully. A status message may contain
	details about the performed task

--------------
Authentication
--------------

Before a client may send request messages to the server that contain
commands to execute, the client has to authenticate. After a successful
authentication the UMC server determines the permissions for the user
defined by policies in the LDAP directory. If the LDAP server is not
reachable a local cache is checked for previously discovered
permissions. If none of these sources is available the user is
prohibited to use any command.

The authentication process within the UMC server uses the PAM service
univention-management-console. By default, this service uses a cache for
credentials if the LDAP server is not available to provide the
possibility to access the UMC server also in case of problems with the
LDAP server.

--------------
Message format
--------------

The messages, request and response, have the same format that consists
of a single header line, one empty line and the body.

The header line contains control information that allows the UMC server
to verify the correctness of the message without reading the rest of the
message.

Message header
==============

The header defines the message type, a unique identifier, the length of
the message body in bytes, the command and the mime type of the body. ::

	(REQUEST|RESPONSE)/<id>/<length of body>[/<mime-type>]: <command>[ <arguments>]

By the first keyword the message type is defined. Supported message
types are *REQUEST* and *RESPONSE*. Any other type will be
ignored. Separated by a ''/'' the message id follows that must be unique
within a communication channel. By default it consists of a timestamp
and a counter. The next field is a number defining the length of the
body in bytes. Starting to count after the empty line. Since *UMCP 2.0*
there is as another field specifying the mime type of the body. If not
given the guessed value for the mime type is application/json. If
the body can not be decoded using a json parser the message is invalid.

The last two fields define the UMCP command that should be executed by
the server. The following commands are supported:

AUTH
	sends an authentication request. It must be the first command send
	by the client. All commands send before a successful authentication
	are rejected.

GET
	is used to retrieve information from the UMC server, e.g. a list of
	all UMC modules available in this session.

SET
	is used to define settings for the session, e.g. the language.

COMMAND
	This command is used to pass requests to UMC modules. Each
	module defines a set of commands that it implements. The UMC module
	command is defined by the first argument in the UMCP header, e.g. a
	request like ::

		REQUEST/123423423-01/42/application/json: COMMAND ucr/query

	passes on the module command ucr/query to a UMC module.


Message body
============

The message body may contain one object of any type, e.g. an image, an
open office document or JSON, which is the default type and is the only
supported mime type for request messages. It contains a dictionary that
has a few pre-defined keys (for both message types):

options
	contains the arguments for the command.

status
	defines the status code in response messages. The codes are
	similar to the HTTP status codes , e.g. 200 defines a successful
	execution of the command. The appendix contains a detailed list
	[[#Status-Codes]].

message
	may contain a human readable description of the status code. This
	may contain details to explain the user the situation.

flavor
	is an optional field. If given in a request message the module may
	act differently than without the flavor.

--------
Examples
--------

This section contains a few example messages of UMCP 2.0

Authentication request
======================

::

	REQUEST/130928961341733-1/147/application/json: AUTH
	{"username": "root", "password": "univention"}

Request: Search for users
=========================

::

	REQUEST/130928961341726-0/125/application/json: COMMAND udm/query
	{"flavor": "users/user", "options": {"objectProperty": "name", "objectPropertyValue": "test1*1", "objectType": "users/user"}}

Response: Search for users
==========================

::

	RESPONSE/130928961341726-0/1639/application/json: COMMAND udm/query
	{"status": 200, "message": null, "options": {"objectProperty": "name", "objectPropertyValue": "test1*1", "objectType": "users/user"}, "result": [{"ldap-dn": "uid=test11,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test11", "objectType": "users/user"}, {"ldap-dn": "uid=test101,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test101", "objectType": "users/user"}, {"ldap-dn": "uid=test111,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test111", "objectType": "users/user"}, {"ldap-dn": "uid=test121,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test121", "objectType": "users/user"}, {"ldap-dn": "uid=test131,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test131", "objectType": "users/user"}, {"ldap-dn": "uid=test141,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test141", "objectType": "users/user"}, {"ldap-dn": "uid=test151,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test151", "objectType": "users/user"}, {"ldap-dn": "uid=test161,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test161", "objectType": "users/user"}, {"ldap-dn": "uid=test171,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test171", "objectType": "users/user"}, {"ldap-dn": "uid=test181,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test181", "objectType": "users/user"}, {"ldap-dn": "uid=test191,cn=users,dc=univention,dc=qa", "path": "univention.qa:/users", "name": "test191", "objectType": "users/user"}]}
"""

from .message import *  # noqa: F403,F401
from .session import *  # noqa: F403,F401
from .server import *  # noqa: F403,F401
from .client import *  # noqa: F403,F401
from .definitions import *  # noqa: F403,F401
from .version import *  # noqa: F403,F401
from .modserver import *  # noqa: F403,F401
