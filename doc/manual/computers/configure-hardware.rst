.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _computers-configuration-of-hardware-and-drivers:

Configuration of hardware and drivers
=====================================

.. _computers-available-kernel-variants:

Available kernel variants
-------------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-kernel-packages`
in :cite:t:`uv-ucs-operation`.

.. _computers-hardware-drivers-kernel-modules:

Hardware drivers / kernel modules
---------------------------------

The content of this section moved to the following locations in
in :cite:t:`uv-ucs-operation`:

* :external+uv-ucs-operation:ref:`system-administration-kernel-modules-loading`
* :external+uv-ucs-operation:ref:`system-administration-kernel-modules-detection`
* :external+uv-ucs-operation:ref:`system-administration-kernel-modules-standard`
* :external+uv-ucs-operation:ref:`system-administration-kernel-modules-external`

.. _grub:

GRUB boot manager
-----------------

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-boot-manager`
in :cite:t:`uv-ucs-operation`.

.. _hardware-network-configuration:

Network configuration
---------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-network`
in :cite:t:`uv-ucs-operation`.

.. _computers-ipv4:

Configuration of IPv4 addresses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-network-ipv4`
in :cite:t:`uv-ucs-operation`.

.. _computers-ipv6:

Configuration of IPv6 addresses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-network-ipv6`
in :cite:t:`uv-ucs-operation`.

.. _computers-configuring-the-name-servers:

Configuring the name servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-network-name-servers`
in :cite:t:`uv-ucs-operation`.

.. _computers-network-complex:

Bridges, bonding, VLANs
~~~~~~~~~~~~~~~~~~~~~~~

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-network-advanced`
in :cite:t:`uv-ucs-operation`.

.. _computers-network-complex-bridge:

Configure bridging
~~~~~~~~~~~~~~~~~~

.. index::
   single: network; bridge
   single: network; switch
   pair: bridge; network

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-network-bridge`
in :cite:t:`uv-ucs-operation`.

.. _computers-network-complex-bonding:

Configure bonding
~~~~~~~~~~~~~~~~~

.. index::
   single: network; bonding
   single: network; link aggregation
   pair: bonding; network
   single: network; etherchannel
   single: network; teaming
   single: network; trunking

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-network-bonding`
in :cite:t:`uv-ucs-operation`.

.. _computers-network-complex-vlan:

Configure VLAN
~~~~~~~~~~~~~~

.. index::
   pair: network; vlan
   single: network; 802.1q

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-network-vlan`
in :cite:t:`uv-ucs-operation`.

.. _computers-configuring-proxy-access:

Proxy access configuration
--------------------------

The content of this section moved to
:external+uv-ucs-operation:ref:`system-administration-proxy`
in :cite:t:`uv-ucs-operation`.

.. _computers-mounting-nfs-shares:

Mounting NFS shares
-------------------

The *NFS mounts* policy of the UMC computer management can be used to
configure NFS shares, which are mounted on the system. There is a *NFS
share* for selection, which is mounted in the file path specified under
*Mount point*.

.. _nfs-mount:

.. figure:: /images/computers_policy_nfsshare.*
   :alt: Mounting a NFS share

   Mounting a NFS share

.. _computers-hardware-sysinfo:

Collection of list of supported hardware
----------------------------------------

Univention collects information about hardware which is compatible with UCS and
in use by customers. The information processed for this is gathered by the UMC
module :guilabel:`Hardware information`.

All files are forwarded to Univention anonymously and only transferred once
permission has been received from the user.

The start dialogue contains the entry fields *Manufacturer* and *Model*, which
must be completed with the values determined from the DMI information of the
hardware. The fields can also be adapted and an additional
*Descriptive comment* added.

If the hardware information is transferred as part of a support request, the
:guilabel:`This is related to a support case` option should be activated. A
ticket number can be entered in the next field; this facilitates assignment and
allows quicker processing.

Clicking on :guilabel:`Next` offers an overview of the transferred hardware
information. In addition, a compressed TAR archive is created, which contains a
list of the hardware components used in the system and can be downloaded via
:guilabel:`Archive with system information`.

Clicking on :guilabel:`Next` again allows you to select the way the data are
transferred to Univention. :guilabel:`Upload` transmits the data via HTTPS,
:guilabel:`Send mail)` opens a dialogue, which lists the needed steps to send
the archive via email.

