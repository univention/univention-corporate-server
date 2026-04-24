.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-hardware-information:

Hardware information
====================

Univention collects data about hardware
that customers use with Nubus for UCS.
The *Hardware information* management module gathers this data.

Nubus for UCS sends the data only after you grant permission.
It doesn't attach any personal data to the transfer.

.. _management-interface-hardware-information-submit:

Submit hardware information
   To submit hardware information to Univention, follow these steps:

   #. Open the *Hardware information* management module
      in the *Management UI* at
      :menuselection:`System --> Hardware information`.

   #. Fill in the *Manufacturer* and *Model* fields.
      The module pre-fills these fields with values from your hardware's DMI data.
      You can adjust the values and add an optional *Comment*.
      For an example, see :numref:`management-interface-hardware-information-figure`.

   #. If the hardware information relates to a support case,
      activate :guilabel:`This is related to a support case`
      and enter the ticket number in the next field.

   #. Click :guilabel:`Next` to view the hardware information before you transfer it.
      Optionally, download a TAR archive of the hardware components by clicking :guilabel:`Archive with system information`.

   #. Click :guilabel:`Next` again and choose the transfer method:
      :guilabel:`Upload` sends the data through HTTPS,
      and :guilabel:`Send mail` lets you send the archive by email.

.. _management-interface-hardware-information-figure:

.. figure:: /images/umc_hardware-information.*
   :alt: The Hardware information management module start dialog

   The *Hardware information* management module start dialog
