.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _deployment-installation-vmware:

VMware-specific considerations
==============================

If you install Nubus for UCS as a guest in VMware,
select the option :menuselection:`Linux --> Debian` as the *Guest operating system*,
because Nubus for UCS bases on Debian GNU/Linux.

The Linux kernel in Nubus for UCS includes all the support drivers necessary for operation in VMware,
such as :file:`vmw_balloon`, :file:`vmw_pvsci`, :file:`vmw_vmci`, :file:`vmwgfx`, and :file:`vmxnet3`.

Nubus for UCS delivers the :program:`Open VM Tools`.
You can install them through the :program:`open-vm-tools` package.
The package is optional,
but necessary for features such as automatic time synchronization
between the virtualization server and the guest system.
