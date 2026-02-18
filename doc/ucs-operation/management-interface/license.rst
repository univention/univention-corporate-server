.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-license:

Activate UCS license
====================

The UCS license of a domain can be managed on the |UCSPRIMARYDN| via the
UMC module :guilabel:`Welcome!`.

The current license status can be shown by clicking the :guilabel:`License info`
button.

.. _umc-license:

.. figure:: /images/umc_coreedition.*
   :alt: Displaying the UCS license

   Displaying the UCS license

The button :guilabel:`Import a license` opens a dialogue in which a new license
key can be activated (otherwise the core edition license is used as default
license). A license file can be selected and imported via the button
:guilabel:`Import from file...`. Alternatively, the license key can also be
copied into the input field below and activated with :guilabel:`Import from text
field`.

Installation of most of the applications in the Univention App Center requires a
personalized license key. UCS core edition licenses can be converted by clicking
:guilabel:`Request a new license`. The current license key is sent to Univention
and the updated key returned to a specified email address within a few minutes.
The new key can be imported directly. The conversion does not affect the scope
of the license.

If the number of licensed user or computer objects is exceeded, it is not
possible to create any additional objects in UMC modules or edit any existing
ones unless an extended license is imported or no longer required users or
computers are deleted. A corresponding message is displayed when opening a UMC
module if the license is exceeded.
