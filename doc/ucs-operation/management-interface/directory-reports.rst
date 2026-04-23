.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _management-interface-directory-reports:

Directory reports
=================

Univention Directory Reports creates ready-made reports
for any object in the directory service.

You define report structure using templates.
The specification language lets you use wildcards
that you can replace with values from the LDAP directory.
You can create any number of report templates.
This enables you to generate detailed reports
or create basic address lists, for example.

You can create reports directly from the management modules
*Users*, *Groups*, and *Computers*.
Alternatively, you can use the command line program
:command:`univention-directory-reports`.

Univention Directory Reports includes six predefined report templates
for users, groups, and computers.
Three templates produce PDF documents
and three produce CSV files
that you can import into other programs.
You can also create and register additional templates.
For more information, see :ref:`management-interface-directory-reports-customize`.

.. seealso::

   For more information about the management modules,
   see :cite:t:`uv-nubus-manual`:

   * :external+uv-nubus-manual:ref:`nubus-user-management-users`
   * :external+uv-nubus-manual:ref:`nubus-groups-management`
   * :external+uv-nubus-manual:ref:`nubus-computer-management`

.. _management-interface-directory-reports-create-umc:

Create reports through management modules
-----------------------------------------

To create a report through the management modules, follow these steps:

#. Open the management module *Users*, *Groups*, or *Computers*.

#. Select all the objects you want to include in the report.
   You can select all objects by clicking the checkbox to the left of *Name*.
   For example, see :numref:`management-interface-directory-reports-create-figure`.

#. Click :menuselection:`More --> Create report`
   to choose between the *Standard Report* (PDF) and the *Standard CSV Report* (CSV).

#. Download and save the generated report file from the browser.

The system stores reports created through a management module for 12 hours,
then automatically deletes them through a cron job.
You can configure when the cron job runs and how long to store reports
using two :term:`UCR variables <UCR variable>`:

* :envvar:`directory/reports/cleanup/cron`
* :envvar:`directory/reports/cleanup/age`

.. _management-interface-directory-reports-create-figure:

.. figure:: /images/umc_report.*
   :alt: Create a report

   Create a report

.. _management-interface-directory-reports-create-cli:

Create reports on the command line
----------------------------------

You can also create reports on the command line with the
:command:`univention-directory-reports` command.
Run it with the ``--help`` option to view usage information.

To list the available report templates for a specific module,
run the command in :numref:`management-interface-directory-reports-create-cli-templates-listing`.

.. code-block:: console
   :caption: List available report templates
   :name: management-interface-directory-reports-create-cli-templates-listing

   $ univention-directory-reports -m users/user -l

To generate a report, run the command in
:numref:`management-interface-directory-reports-create-cli-report-listing`.

.. code-block:: console
   :caption: Generate a report
   :name: management-interface-directory-reports-create-cli-report-listing

   $ univention-directory-reports -m users/user -r "PDF Document" -f output.pdf

.. _management-interface-directory-reports-customize:

Customize reports
-----------------

You can generate reports with the default settings.
Some settings can be adapted using
:term:`UCR variables <UCR variable>`.

For example, you can replace the logo that appears in the header of each page
of a PDF report.
To do so, specify the name of an image file in the
:envvar:`directory/reports/logo` UCR variable.
You can use common image formats such as JPEG, PNG, and GIF.
The system scales the image to a fixed width of 5.0 cm.

You can also adapt the report contents by creating new report templates.
