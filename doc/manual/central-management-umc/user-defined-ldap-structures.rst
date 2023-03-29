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

.. _central-cn-and-ous:

Structuring of the domain with user-defined LDAP structures
===========================================================

Containers and organizational units (OU) are used to structure the data in the
LDAP directory. There is no technical difference between the two types, just in
their application:

* Organizational units usually represent real, existing units such as a
  department in a company or an institution

* Containers are usually used for fictitious units such as all the computers
  within a company

Containers and organizational units are managed in the UMC module
:guilabel:`LDAP directory` and are created with :guilabel:`Add` and the object
types *Container: Container* and *Container: Organisational unit*.

Containers and OUs can in principle be added at any position in the LDAP;
however, OUs cannot be created below containers.

.. _central-cn-and-ous-general-tab:

General tab
-----------

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name
     - A random name for the container / organizational unit.

   * - Description
     - A random description for the container / organizational unit.

.. _central-cn-and-ous-avanced-tab:

Advanced settings tab
---------------------

.. list-table:: *Advanced settings* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Add to standard ``[object type]`` containers
     - If this option is activated, the container or organizational unit will be
       regarded as a standard container for a certain object type. If the
       current container is declared the standard user container, for example,
       this container will also be displayed in users search and create masks.

.. _central-cn-and-ous-policies-tab:

Policies tab
------------

The *Policies* tab is described in :ref:`central-policies-assign`.
