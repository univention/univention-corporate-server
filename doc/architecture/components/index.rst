.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _product-components:

******************
Product components
******************

In this part of the document, you learn about the second, medium, and detail
level of the architecture of |UCS|. You learn about UCS product components that
you face directly when you use UCS. The product components typically act as
entry points for your tasks.

The product components descriptions are intended for administrators and solution
architects. For software developers and system engineers, it provides the context
for the architectural details of UCS. Make sure you are familiar with the
:ref:`concepts` behind UCS.

.. include:: /archimate.txt

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
