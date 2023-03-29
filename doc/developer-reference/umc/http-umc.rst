.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

.. _umc-http:
.. _umc-http-example:

Protocol HTTP for UMC
=====================

With the new generation of UMC there is also an HTTP server available that can
be used to access the UMC server. The web server is implemented as a front end to
the UMC server and translates HTTP POST requests to UMCP commands.

.. code-block::
   :caption: Authentication request
   :name: umc-http-example-auth

   POST http://192.0.2.31/univention/auth HTTP/1.1

   {"options": {"username": "root", "password": "univention"}}


Request:

.. code-block::
   :caption: Search for users
   :name: umc-http-example-user

   POST http://192.0.2.31/univention/command/udm/query HTTP/1.1

   {"options": {"container": "all",
               "objectType":"users/user",
               "objectProperty":"username",
               "objectPropertyValue":"test1*1"},
    "flavor":"users/user"}


Response:

.. code-block:: javascript
   :caption: Response
   :name: umc-http-example-response

   {"status": 200,
    "message": null,
    "options": {"objectProperty": "username",
                "container": "all",
                "objectPropertyValue": "test1*1",
                "objectType": "users/user"},
    "result": [{"ldap-dn": "uid=test11,cn=users,dc=univention,dc=qa",
                "path": "univention.qa:/users",
                "name": "test11",
                "objectType": "users/user"},
   ...
               {"ldap-dn": "uid=test191,cn=users,dc=univention,dc=qa",
                "path": "univention.qa:/users",
                "name": "test191",
                "objectType": "users/user"}]}
