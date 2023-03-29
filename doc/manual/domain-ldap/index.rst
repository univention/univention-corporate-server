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

.. _domain-concept:

********************************
Domain services / LDAP directory
********************************

Univention Corporate Server offers a cross platform domain concept with a common
trust context between Linux and/or Windows systems. Within this domain a user is
known to all systems via their username and password stored in the |UCSUMS| and
can use all services which are authorized for them. The management system keeps
the account synchronized for the windows login, Linux/POSIX systems and
Kerberos. The management of user accounts is described in :ref:`users-general`.

All UCS and Windows systems within a UCS domain have a host domain account. This
allows system-to-system authentication. Domain joining is described in
:ref:`domain-join`.

The certificate authority (CA) of the UCS domain is operated on the
|UCSPRIMARYDN|. A SSL certificate is generated there for every system that has
joined the domain. Further information can be found in :ref:`domain-ssl`.

Every computer system which is a member of a UCS domain has a system role. This
system role represents different permissions and restrictions, which are
described in :ref:`system-roles`.

All domain-wide settings are stored in a directory service on the basis of
OpenLDAP. :ref:`domain-ldap` describes how to expand the managed attributes with
LDAP scheme expansions, how to set up an audit-compliant LDAP documentation
system and how to define access permissions to the LDAP directory.

Replication of the directory data within a UCS domain occurs via the Univention
Directory Listener / Notifier mechanism. Further information can be found in
:ref:`domain-listener-notifier`.

Kerberos is an authentication framework the purpose of which is to permit secure
identification in the potentially insecure connections of decentralized
networks. Every UCS domain operates its own Kerberos trust context (realm).
Further information can be found in :ref:`domain-kerberos`.

.. toctree::
   :caption: Chapter contents:

   domain-join
   system-roles
   ldap-directory
   listener-notifier
   ssl
   kerberos
   password-hashes
   saml
   oidc
   backup2master
   fault-tolerant-setup
   admin-diary
