.. SPDX-FileCopyrightText: 2021 - 2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _system-administration-network-firewall:

Packet filter with Univention Firewall
======================================

Univention Corporate Server (UCS) includes Univention Firewall,
which integrates :program:`iptables` with :ref:`Univention Configuration Registry <system-administration-ucr>` (UCR).

You can use Univention Firewall to control incoming network traffic
by protocol, port, and action.
During installation,
UCS rejects incoming network traffic by default.

By default, UCS blocks incoming ports.
UCS packages can provide rules that open the ports that they require.
You primarily configure firewall rules through
:term:`UCR variables <UCR variable>`.

For information about packet filter rules,
see :external+uv-dev-ref:ref:`misc-nacl`
in :cite:t:`developer-reference`.

In addition, the :file:`/etc/security/packetfilter.d/` directory
contains scripts with firewall rules.
The :file:`50_local.sh` script runs after the UCR-defined standard rules.
The :program:`run-parts` command runs executable scripts
in lexicographic filename order.
Use a two-digit prefix as a convention to express the needed order.
The complete filename determines the order.

For information about configuring UCR-based firewall rules for IPv4 and IPv6,
see :external+uv-dev-ref:ref:`misc-nacl`
in :cite:t:`developer-reference`.

.. warning::

   Firewall changes can interrupt remote access to the system.
   Make sure that you have a fallback access method
   before you restart the :program:`univention-firewall` service.

After you change the packet filter settings,
restart the :program:`univention-firewall` service.
Test the affected TCP and UDP ports from a suitable host.

.. warning::

   Deactivating Univention Firewall reduces the protection of the system.
   Make sure that you understand the effect on the system's network access
   before you change the setting.

To deactivate Univention Firewall,
set the UCR variable
:envvar:`security/packetfilter/disabled` to ``true``.

To remove existing firewall rules,
run the command in :numref:`system-administration-network-firewall-remove-rules-listing`.
Verify the resulting network access from a suitable host.

.. code-block:: console
   :caption: Remove existing firewall rules
   :name: system-administration-network-firewall-remove-rules-listing

   $ service univention-firewall flush

.. seealso::

   `netfilter/iptables documentation <https://www.iptables.org/documentation/>`_
      provides an overview of the available :program:`iptables` documentation.

   `Iptables Tutorial <https://www.frozentux.net/iptables-tutorial/iptables-tutorial.html>`_
      provides a tutorial about :program:`iptables` by :spelling:word:`Oscar Andreasson`.

   `iptables(8) manpage <https://manpages.debian.org/bookworm/iptables/iptables.8.en.html>`_
      provides information about configuring firewall rules with :program:`iptables`.

   `Packet Filtering HOWTO <https://www.iptables.org/documentation/HOWTO/packet-filtering-HOWTO.html>`_
      explains packet filtering with :program:`iptables`.
