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

.. _product-components:

******************
Product components
******************

In this part of the document, you learn about the second, medium, detail level of
the architecture of |UCS|. You learn about UCS product components that you face
directly when you use UCS. The product components typically act as entry points
for your tasks.

The description of the product components is for administrators and solution
architects. For software developers and system engineers it provides the context
for the architectural details to UCS. Make sure you are familiar with the
:ref:`concepts` behind UCS.

For architecture notation, this part of the document uses ArchiMate® 3.1, a
visual language with a set of default iconography for describing, analyzing, and
communicating many concerns of enterprise architectures. For more information
about how the document uses the notation, refer to
:ref:`architecture-notation-archimate`.

The following product components from :numref:`product-components-model`
introduce themselves in the order you most likely encounter them when you work
with UCS:

#. :ref:`component-portal`
#. :ref:`component-management-system`
#. :ref:`component-app-center`

..
   #. :ref:`component-file-print`
   #. :ref:`component-command-line`

.. _product-components-model:

.. figure:: /images/product-components.*
   :alt: UCS Product components with UCS Management System, UCS Portal, App
         Center, File and Print, and Command-line

   User facing product components of UCS

.. hint::

   The section is work in progress. Later updates of the document explain the
   concepts *Command line* and *File and print*. For the sake of completeness
   :numref:`product-components-model` already shows them.

.. TODO : Remove or change hint, once Command line and File and print are
   explained.

.. toctree::
   :maxdepth: 2
   :hidden:

   portal
   management-system
   app-center
