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

.. _appliance-use:

*********************
Using a UCS appliance
*********************

In addition to the traditional installation, there is also the possibility of
providing UCS via an appliance image. These appliance images can be used both
for simple commissioning in a virtualization solution such as VMware and for
providing a cloud instance.

Appliances can be created with minimal effort. This is described in
:ref:`create`.

Whilst some of the settings can be preconfigured globally in the image, it is
still necessary for the end user to make final adjustments to the configuration,
e.g., to set the computer name or the domain used. For this reason, a basic
system is installed for the appliance image and a component set up, which then
allows the end user to finalize the configuration. Alternatively, the
configuration can also be performed automatically without user interaction. This
is described in :ref:`use-auto`.

The interactive configuration can be performed in two ways:

* A graphic interface starts on the system, in which the web browser Firefox is
  started in full-screen mode and automatically accesses the configuration URL.
  This option is particularly suitable for images in virtualization solutions.

* The configuration can also be performed directly via an external web browser.
  In this case, the system's IP address must be known to the user (e.g., if it
  has been notified to him in advance in the scope of the provision of a cloud
  image).

In the scope of the initial configuration, the user can change the following
settings in the default setting:

* Selection of the language, time zone and keyboard layout

* Configuration of the network settings

* Setup of a new UCS domain or joining a UCS or Microsoft Active Directory
  domain

* Software selection of UCS key components. The user can install software from
  other vendors at a later point in time via the Univention App Center.
