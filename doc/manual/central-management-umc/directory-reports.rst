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

.. _central-reports:

Evaluation of data from the LDAP directory with Univention Directory Reports
============================================================================

.. highlight:: console

Univention Directory Reports offers the possibility of creating predefined
reports for any objects to be managed in the directory service.

The structure of the reports is defined using templates. The specification
language developed for this purpose allows the use of wildcards, which can be
replaced with values from the LDAP directory. Any number of report templates
can be created. This allows users to select very detailed reports or just create
simple address lists, for example.

The creation of the reports is directly integrated in the UMC modules
:guilabel:`Users`, :guilabel:`Groups` and :guilabel:`Computers`. Alternatively,
the command line program :command:`univention-directory-reports` can be used.

Six report templates are already provided with the delivered Univention
Directory Reports, which can be used for users, groups and computers. Three
templates create PDF documents and three CSV files, which can be used as an
import source for other programs. Further templates can be created and
registered.

.. _central-reports-create:

Creating reports via |UCSUMC| modules
-------------------------------------

To create a report, you need to open the UMC module :guilabel:`Users`,
:guilabel:`Groups` or :guilabel:`Computers`. Then all the objects which should
be covered by the report must be selected (you can select all objects by
clicking the checkbox the left of *Name*). Clicking on :menuselection:`More -->
Create report` allows to choose between the *Standard Report* in PDF format and
the *Standard CSV Report* in CSV format.

.. _umc-report:

.. figure:: /images/umc_report.*
   :alt: Creating a report

   Creating a report

The reports created via a UMC module are stored for 12 hours and then deleted by
a cron job. The settings for when the cron job should run and how long the
reports should be stored for can be defined via two |UCSUCR| variables:

.. envvar:: directory/reports/cleanup/cron

   Defines when the cron job should be run.

.. envvar:: directory/reports/cleanup/age

   Defines the maximum age of a report document in seconds before it is deleted.

.. _central-management-umc-create-reports-cli:

Creating reports on the command line
------------------------------------

Reports can also be created via the command line with the
:command:`univention-directory-reports` program. Information on the use of the
program can be viewed using the ``--help`` option.

The following command can be used to list the report templates available to
users, for example:

.. code-block::

   $ univention-directory-reports -m users/user -l


.. _central-management-umc-adjustment-expansion-of-directory-reports:

Adjustment/expansion of Univention Directory Reports
----------------------------------------------------

Existing reports can be created directly with the presettings. Some presettings
can be adapted using |UCSUCR|. For example, it is possible to replace the logo
that appears in the header of each page of a PDF report. To do so, the value of
the |UCSUCRV| :envvar:`directory/reports/logo` can include the name of an image
file. The usual image formats such as JPEG, PNG and GIF can be used. The image
is automatically adapted to a fixed width of 5.0 cm.

In addition to the logo, the contents of the report can also be adapted by
defining new report templates.

