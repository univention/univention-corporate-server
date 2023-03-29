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

.. _umc-files:

UMC files
=========

.. index::
   single: management console; files

Files for building a UMC module.

.. _umc-modules:

:file:`debian/{package}.umc-modules`
--------------------------------------------------------------------------------------------------------------

.. index::
   single: management console; umc-modules

* :command:`univention-l10n-build` builds translation files.

* :command:`dh-umc-module-install` installs files.

Configured through
:file:`debian/{package}.umc-modules`.

``Module``
   Internal (?) name of the module.

``Python``
   Directory containing the Python code relative to top-level directory.

..   PMH: Bug #31151

``Definition``
   Path to an XML file, which describes the module. See :ref:`umc-xml` for more
   information.

``Javascript``
   Directory containing the Java-Script code relative to top-level directory.

.. PMH: Bug #31151

``Icons`` (deprecated)
   Directory containing the Icons relative to top-level directory. Must provide
   icons in sizes 16×16 (:file:`umc/icons/16x16/udm-{module}.png`) and 50×50
   (:file:`umc/icons/50x50/udm-{module}.png`) pixels.

.. _umc-xml:

UMC module declaration file
---------------------------

.. index::
   single: management console; XML

:file:`umc/{module}.xml`

.. PMH: Bug #26275

.. literalinclude:: module.xml
   :language: xml

:file:`umc/categories/{category}.xml`

.. literalinclude:: module-categories.xml
   :language: xml

