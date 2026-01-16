.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _deployment-installation-text-mode:

Text mode installation
----------------------

On systems that show problems with the graphical Univention installer,
you can start the installation in text mode.
For text mode, select :ref:`deployment-installation-physical-install-mode-text-mode`
in the installation boot prompt.

During installation in text mode
the installer shows the same information and asks for the same settings.
After hard drive partitioning, the system is ready for the first boot
and the installer restarts the system.

After restart,
you can resume the configuration with the system setup in a web browser.
Open the URL :samp:`https://{SERVER-IP-ADDRESS}` in your web browser.
System setup requires authentication with the user ``root``.
It then asks for location and network setting.
You continue with the same steps as the graphical installer,
see :ref:`deployment-installation-physical-domain-settings`.
