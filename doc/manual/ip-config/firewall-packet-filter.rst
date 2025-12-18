.. SPDX-FileCopyrightText: 2021-2025 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _ip-config-packet-filter-with-univention-firewall:

Packet filter with Univention Firewall
======================================

Univention Firewall integrates a packet filter
based on :program:`iptables` in Univention Corporate Server.

It permits targeted filtering of undesired services
and the protection of computers during installations.
Furthermore, it provides the basis for complex scenarios,
such as firewall rules and application level gateways.
All UCS installations include Univention Firewall as standard.

By default, UCS blocks all incoming ports.
Every UCS package provides rules, which free up the ports required by the package again.
You primarily configure firewall rules through |UCSUCR| variables.
For information about the definition of packet file rules,
see :external+uv-dev-ref:ref:`misc-nacl`
in :cite:t:`developer-reference`.

In addition, the :file:`/etc/security/packetfilter.d/` directory
contains scripts with firewall rules.
The names of all scripts begin with two digits, which allows a
numbered order. The scripts require the executable bit so that UCS can run them.

After changing the packet filter settings,
you need to restart the :program:`univention-firewall` service.

You can deactivate Univention Firewall
by setting the |UCSUCRV|
:envvar:`security/packetfilter/disabled` to ``true``

.. seealso::

   `netfilter/iptables project homepage - Documentation about netfilter/iptables project <https://www.iptables.org/documentation/>`_
      for an overview about available documentation for :program:`iptables`.

   `Iptables Tutorial <https://www.frozentux.net/iptables-tutorial/iptables-tutorial.html>`_
      a tutorial about :program:`iptables` from :spelling:word:`Oscar Andreasson`.

   `iptables(8) manpage <https://manpages.debian.org/bookworm/iptables/iptables.8.en.html>`_
      for information about configuration of firewall rules with :program:`iptables`.

   `Packet Filtering HOWTO <https://www.iptables.org/documentation/HOWTO/packet-filtering-HOWTO.html>`_
      for a how-to about packet filtering with :program:`iptables`.
