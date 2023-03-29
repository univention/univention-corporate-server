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

.. _umc-modules-printer:

Administration of print jobs and print queues
=============================================

The UMC module :guilabel:`Print jobs` allows you to check the status of the
connected printers, restart paused printers and remove print jobs from the
queues on printer servers.

.. _printer-admin:

.. figure:: /images/umc-printer_administration.*
   :alt: Printer administration

   Printer administration

The start page of the module contains a search mask with which the available
printers can be selected. The result list displays the server, name, status,
location and description of the respective printer. The status of more than one
printer can be changed simultaneously by selecting the printers and running
either the *deactivate* or *activate* function.

Clicking on the printer name displays details of the selected printer. The
information displayed includes a list of the print jobs currently in the printer
queue. These print jobs can be deleted from the queue by selecting the jobs and
running the *Delete* function.
