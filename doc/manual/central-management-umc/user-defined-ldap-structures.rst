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
