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

.. _windows-trust:

Trust relationships
===================

Trust relationships between domains make it possible for users from one domain
to sign in to computers from another domain.

In general, Windows trust relations can be *unidirectional* or *bidirectional*.
Technically a bidirectional trust is simply realized as two unidirectional
trusts, one in each direction.

The terminology of unidirectional trusts depends on the perspective of either
the trusting or trusted domain: From the perspective of the trusting domain, the
trust is called *outgoing*. From the perspective of the trusted domain, the
trust is called *incoming*.

In UCS, outgoing trust (UCS trusts Windows) is not supported. As a consequence,
bidirectional trust is not supported either.

When setting up and using the trust relationship the domain controllers of both
domains must be able to reach each other over the network and identify each
other via DNS. At least the fully qualified DNS names of the domain controllers
of the respective remote domain must be resolvable to allow communication
between both domains to work. This can be achieved by configuring conditional
DNS forwarding in both domains.

The following example assumes, that the UCS Samba/AD DC |UCSPRIMARYDN|
``primary.ucsdom.example`` has the IP address ``192.0.2.10`` and that the Active
Directory domain controller ``dc1.addom.example`` of the remote domain has the
IP address ``192.0.2.20``.

On the UCS side the conditional forwarding of DNS queries can be set up as
``root`` with the following commands:

.. code-block:: console

   $ cat >>/etc/bind/local.conf.samba4 <<__EOT__
   zone "addom.example" {
     type forward;
     forwarders { 192.0.2.20; };
   };
   __EOT__
   $ systemctl restart bind9

The success can be checked by running:

.. code-block:: console

   $ host dc1.addom.example

In addition, it may be useful to create a static entry for the domain controller
of the remote Active Directory domain in the file :file:`/etc/hosts`:

.. code-block:: console

   $ ucr set hosts/static/192.0.2.20=dc1.addom.example


On a Windows AD DC, a so-called *conditional forwarding* can be set up for the
UCS domain via the DNS server console.

Trust relationships can only be configured on domain controllers but
they affect the whole domain.

After this preliminary work, the trust relationship can be established directly
from the command line of the UCS Samba/AD DC using the tool
:command:`samba-tool`:

.. code-block:: console

   $ samba-tool domain trust create addom.example \
     -k no -UADDOM\\Administrator%ADAdminPassword \
     --type=external --direction=incoming

The trust can be checked using the following commands:

.. code-block:: console

   $ samba-tool domain trust list
   $ wbinfo --ping-dc –domain=addom.example
   $ wbinfo --check-secret –domain=addom.example


After the setup, a UCS user should be able to sign in to systems of the remote
Active Directory domain. Users must either use the format ``UCSDOM\username`` as
login name or their Kerberos principal in the notation
``username@ucsdom.example``.
