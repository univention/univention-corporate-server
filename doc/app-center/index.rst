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

************
Introduction
************

This document is for app providers who want to place their product
clearly visible for a broad, professional and growing user group. It
covers the steps on how to make the product available as an app for
|UCSAPPC|.

.. _introduction-start:

What is |UCSAPPC|?
==================

|UCSAPPC| is an ecosystem similar to the app stores known from mobile
platforms like Apple or Google. It provides an infrastructure to build,
deploy and run enterprise applications on |UCSUCS| (UCS). The App Center
uses well-known technologies like `Docker <docker_>`_.

.. _infrastructure:

App Center infrastructure
=========================

The ecosystem consists of the following components:

The App
   is the software plus the collection of metadata like
   configuration, text description, logo, screenshots and more for the
   presentation.

The App Center Repository
   is a central server infrastructure
   managed by Univention that stores the files and data for the app. It
   is the installation source for the app.

The App Center Module on UCS
   is part of the web-based management
   system on UCS. It is the place where UCS administrators install,
   update and uninstall apps in their UCS environment.

The App Catalog
   presents the app portfolio on the `Univention
   website <univention-app-catalog_>`_.

The App Provider Portal
   is the self-service portal for app
   providers where they can create and maintain their app.

The Test App Center
   is the "staging area" for app providers to
   develop and test their apps.

|UCSUCR|
   is the target platform for the app. UCS is technically
   a derivative of Debian GNU/Linux.

For building an app the app developer works with UCS, the app, the App
Provider Portal and the Test App Center.

