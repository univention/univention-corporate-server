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

.. _chap-listener:

********
|UCSUDL|
********

.. index::
   single: directory listener
   see: listener; directory listener
   see: |UCSUDL|; directory listener

Replication of the directory data within a UCS domain is provided by the
Univention Directory Listener/Notifier mechanism:

* The |UCSUDL| service runs on all UCS systems.

* On the |UCSPRIMARYDN| (and possibly existing |UCSBACKUPDN| systems) the
  |UCSUDN_e| service monitors changes in the LDAP directory and makes the
  selected changes available to the |UCSUDL| services on all UCS systems joined
  into the domain.

The active |UCSUDL| instances in the domain connect to a |UCSUDN| service. If an
LDAP change is performed on the |UCSPRIMARYDN| (all other LDAP servers in the
domain are read-only), this is registered by the |UCSUDN| and reported to the
listener instances.

Each |UCSUDL| instance hosts a range of |UCSUDL| modules. These modules are
shipped by the installed applications; the print server package includes, for
example, listener modules which generate the CUPS configuration.

|UCSUDL| modules can be used to communicate domain changes to services which are
not LDAP-aware. The print server CUPS is an example of this: The printer
definitions are not read from the LDAP, but instead from the file
:file:`/etc/cups/printers.conf`. Now, if a printer is saved in the printer
management of the |UCSUMC|, it is stored in the LDAP directory. This change is
detected by the |UCSUDL| module *cups-printers* and an entry gets added to,
modified in or deleted from :file:`/etc/cups/printers.conf` based on the
modification in the LDAP directory.

By default the Listener loads all modules from the directory
:file:`/usr/lib/univention-directory-listener/system/`. Other directories can be
specified using the option ``-m`` when starting the
:command:`univention-directory-listener` daemon.

.. toctree::

   structure
   api
   module
   tasks-examples
   details
