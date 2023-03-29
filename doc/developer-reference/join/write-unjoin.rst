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

.. _join-unjoin:

Writing unjoin scripts
======================

.. index::
   single: domain join; unjoin

On package removal, packages should clean up the data in Univention directory
service. Removing data from LDAP also requires appropriate credentials, while
removing a package only requires local ``root`` privileges. Therefore, UCS
provides support for so-called unjoin scripts. In most cases it reverts the
changes of a corresponding join script.

.. warning::

   A domain is a distributed system. Just because one local system no longer
   wants to store some information in Univention directory service does not mean
   that the data should be deleted. There might still be other systems in the
   domain that still require the data.

   Therefore, *the first system to come* should setup the data, while only *the
   last system to go* may clean up the data.

Just like join scripts an unjoin script is prefixed with a two-digit number for
lexicographical ordering. To reverse the order of the unjoin scripts in
comparison to the corresponding join scripts, the number of the unjoin script
should be 100 minus the number of the corresponding join script. The suffix of
an unjoin script is ``.uinst`` and it should be installed in
:file:`/usr/lib/univention-uninstall/`.

On package removal the unjoin script would be deleted as well, while the
Univention directory service might still contain data managed by the package.
Therefore, the script must be copied from there to
:file:`/usr/lib/univention-install/` in the :file:`prerm` maintainer script.

Example:
   The package :program:`univention-fetchmail` provides both a join script
   :file:`/usr/lib/univention-install/91univention-fetchmail.inst` and the
   corresponding unjoin script as
   :file:`/usr/lib/univention-uninstall/09univention-fetchmail.uinst`.

As of UCS 3.1 :file:`.inst` and :file:`.uinst` are not distinguishable in the
*UMC Join module* by the user. Internally join scripts are always executed
before unjoin scripts and then ordered lexicographically by their prefix.

To decide if an unjoin script is the last instance and should remove the data
from LDAP, a service can be registered for each host where the package is
installed.

For example the package :program:`univention-fetchmail` uses
:command:`ucs_addServiceFromLocalhost "Fetchmail" "$@"` in the join script to
register and :command:`ucs_removeServiceFromLocalhost "Fetchmail" "$@"` in the
unjoin script to un-register a service for the host. The data is removed from
LDAP, when in the unjoin script :command:`ucs_isServiceUnused "Fetchmail" "$@"`
returns ``0``. As a side effect adding the service also allows using this
information to find and list those servers currently providing the Fetchmail
service.

:file:`50join-template.uinst`
   This unjoin script reverts the changes of the join script from
   :ref:`join-minimal`.

   .. code-block:: bash

      #!/bin/sh

      ## joinscript api: bindpwdfile

      # VERSION is needed for some tools to recognize that as a join script
      VERSION=1
      . /usr/share/univention-join/joinscripthelper.lib
      joinscript_init

      SERVICE="MyService"

      eval "$(ucr shell)"

      . /usr/share/univention-lib/ldap.sh
      ucs_removeServiceFromLocalhost "$SERVICE" "$@" || die
      if ucs_isServiceUnused "$SERVICE" "$@"
      then
      	# was last server to implement service. now the data
      	# may be removed
      	univention-directory-manager container/cn remove "$@" --dn \
      		"cn=myservice,cn=custom attributes,cn=univention,$ldap_base" || die

      	# Terminate UDM server to force module reload
      	. /usr/share/univention-lib/base.sh
      	stop_udm_cli_server
      fi

      # do NOT call "joinscript_save_current_version"
      # otherwise an entry will be appended to /var/univention-join/status
      # instead the join script needs to be removed from the status file
      joinscript_remove_script_from_status_file join-template

      exit 0

