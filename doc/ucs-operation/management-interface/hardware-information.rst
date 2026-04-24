.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-hardware-information:

Hardware information
====================

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
