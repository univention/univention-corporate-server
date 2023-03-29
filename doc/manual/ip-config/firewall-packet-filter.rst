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

.. _ip-config-packet-filter-with-univention-firewall:

Packet filter with Univention Firewall
======================================

Univention Firewall integrates a packet filter based on :program:`iptables` in
Univention Corporate Server.

It permits targeted filtering of undesired services and the protection of
computers during installations. Furthermore it provides the basis for complex
scenarios such as firewalls and application level gateways. Univention Firewall
is included in all UCS installations as standard.

By default all incoming ports are blocked. Every UCS package provides rules,
which free up the ports required by the package again.

The configuration is primarily performed via |UCSUCR| variables. The definition
of this type of packet filter rules is documented in
:cite:t:`developer-reference`.

In addition, the configuration scripts in the
:file:`/etc/security/packetfilter.d/` directory are listed in alphabetic order.
The names of all scripts begin with two digits, which allows a
numbered order. The scripts must be marked as executable.

After changing the packet filter settings, the :program:`univention-firewall`
service has to be restarted.

Univention Firewall can be deactivated by setting the |UCSUCRV|
:envvar:`security/packetfilter/disabled` to ``true``
