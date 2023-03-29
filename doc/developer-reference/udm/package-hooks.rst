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

.. _settings-udm-hook:

Package UDM hooks
=================

.. index::
   single: directory manager; hooks packaging

For some purposes, for example for app installation, it is convenient to be able
to deploy a new UDM hook in the UCS domain from any system in the domain. For
this purpose, a UDM hook can be stored as a special type of UDM object. The
module responsible for this type of objects is called ``settings/udm_hook``. As
these objects are replicated throughout the UCS domain, the UCS servers listen
for modifications on these objects and integrate them into the local UDM.

The commands to create the UDM hook objects in UDM may be put into any join
script (see :ref:`chap-join`). Like every UDM object a UDM hook object can be
created by using the UDM command line interface
:command:`univention-directory-manager` or its alias :command:`udm`. UDM hook
objects can be stored anywhere in the LDAP directory, but the recommended
location would be ``cn=udm_hook,cn=univention,`` below the LDAP base. Since the
join script creating the attribute may be called on multiple hosts, it is a good
idea to add the ``--ignore_exists`` option, which suppresses the error exit code
in case the object already exists in LDAP.

The module ``settings/udm_hook`` requires several parameters. Since many of
these are determined automatically by the :command:`ucs_registerLDAPExtension`
shell library function, it is recommended to use the shell library function to
create these objects (see :ref:`join-libraries-shell`).

``name`` (required)
   Name of the UDM hook.

``data`` (required)
   The actual UDM hook data in bzip2 and base64 encoded format.

``filename`` (required)
   The filename the UDM hook data should be written to by the listening servers.
   The filename must not contain any path elements.

``package`` (required)
   Name of the Debian package which creates the object.

``packageversion`` (required)
   Version of the Debian package which creates the object. For object
   modifications the version number needs to increase unless the package name is
   modified as well.

``appidentifier`` (optional)
   The identifier of the app which creates the object. This is important to
   indicate that the object is required as long as the app is installed anywhere
   in the UCS domain. Defaults to ``string``.

``ucsversionstart`` (optional)
   Minimal required UCS version. The UDM hook is only activated by systems with
   a version higher than or equal to this.

``ucsversionend`` (optional)
   Maximal required UCS version. The UDM hook is only activated by systems with
   a version lower than or equal to this. To specify validity for the whole
   5.0-x release range a value like ``5.0-99`` may be used.

``active`` (internal)
   A boolean flag used internally by the |UCSPRIMARYDN| to signal availability
   of the new UDM hook on the |UCSPRIMARYDN| (default: ``FALSE``).
