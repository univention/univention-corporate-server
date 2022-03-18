.. _central-user-interface:

|UCSUMC| modules
================

.. _central-management-umc:

Introduction
------------

|UCSUMC| (UMC) modules are the web-based tool for administration of the UCS
domain. They are shown on the portal page (:ref:`central-portal`) for logged in
administrators. Depending on the system role, different UMC modules are
available. Additionally installed software components may bring their own new
UMC modules.

UMC modules for the administration of all the data included in the LDAP
directory (such as users, groups and computer accounts) are only provided on
|UCSPRIMARYDN|\ s and |UCSBACKUPDN| s. Changes made in these modules are applied
to the whole domain.

UMC modules for the configuration and administration of the local system are
provided on all system roles. These modules can for example be used to install
additional applications and updates, adapt the local configuration via |UCSUCR|
or start/stop services.

.. _central-license:

Activation of UCS license / license overview
--------------------------------------------

The UCS license of a domain can be managed on the |UCSPRIMARYDN| via the
UMC module :guilabel:`Welcome!`.

The current license status can be shown by clicking the :guilabel:`License info`
button.

.. _umc-license:

.. figure:: /images/umc_coreedition.*
   :alt: Displaying the UCS license

   Displaying the UCS license

The button :guilabel:`Import a license` opens a dialogue in which a new license
key can be activated (otherwise the core edition license is used as default
license). A license file can be selected and imported via the button
:guilabel:`Import from file...`. Alternatively, the license key can also be
copied into the input field below and activated with :guilabel:`Import from text
field`.

Installation of most of the applications in the Univention App Center requires a
personalized license key. UCS core edition licenses can be converted by clicking
:guilabel:`Request a new license`. The current license key is sent to Univention
and the updated key returned to a specified e-mail address within a few minutes.
The new key can be imported directly. The conversion does not affect the scope
of the license.

If the number of licensed user or computer objects is exceeded, it is not
possible to create any additional objects in UMC modules or edit any existing
ones unless an extended license is imported or no longer required users or
computers are deleted. A corresponding message is displayed when opening a UMC
module if the license is exceeded.

.. _central-management-umc-operating-instructions-for-domain-modules:

Operating instructions for modules to administrate LDAP directory data
----------------------------------------------------------------------

All UMC modules for managing LDAP directory objects such as user, group
and computer accounts or configurations for printers, shares, mail and
policies are controlled identically from a structural perspective. The
following examples are presented using the user management but apply
equally for all modules. The operation of the DNS and DHCP modules is
slightly different. Further information can be found in
:ref:`ip-config-dns-umc` and :ref:`networks-dhcp-general`.

.. _umc-modules:

.. figure:: /images/umc-favorites-tab.*
   :alt: Module overview

   Module overview

The configuration properties/possibilities of the modules are described in the
following chapters:

* Users - :ref:`users-general`

* Groups - :ref:`groups`

* Computers - :ref:`computers-general`

* Networks - :ref:`networks-introduction`

* DNS - :ref:`networks-dns`

* DHCP - :ref:`module-dhcp-dhcp`

* Shares - :ref:`shares-general`

* Printers - :ref:`print-general`

* E-mail - :ref:`mail-general`

* Nagios - :ref:`nagios-general`

The use of policies (:ref:`central-policies`) and the LDAP navigation
(:ref:`central-navigation`) are described separately.

.. _umc-usage-search:

Searching for objects
~~~~~~~~~~~~~~~~~~~~~

The module overview lists all the objects managed by this module. *Search*
performs a search for a selection of important attributes (e.g., for user
objects by first and last name, primary e-mail address, description, employee
number and user name). A wildcard search is also possible, e.g.,
``m*``.

Clicking on the :guilabel:`Advanced options` button (the filter icon) next to
the input field displays additional search options:

* The :guilabel:`Search in` field can be used to select whether the complete
  LDAP directory or only individual LDAP containers/OUs are searched. Further
  information on the structure of the LDAP directory service can be found in
  :ref:`central-cn-and-ous`.

* The :guilabel:`Property` field can be used to search for a certain attribute
  directly.

* The majority of the modules administrate a range of types of LDAP objects; the
  computer management for example administrates different objects for the
  individual system roles. The search can be limited to one type of LDAP object.

* Some of the internally used user groups and groups (e.g., for domain joins)
  are not shown by default. If the :guilabel:`Include hidden objects` option is
  enabled, these objects are also shown.

.. _umc-search:

.. figure:: /images/umc_user.*
   :alt: Searching for users

   Searching for users

.. _central-management-umc-create:

Creating objects
~~~~~~~~~~~~~~~~

At the top of the table that shows the objects is a toolbar which can be used to
create a new object using :guilabel:`Add`.

There are simplified wizards for some UMC modules (users, hosts), in which only
the most important settings are requested. All attributes can be shown by
clicking on :guilabel:`Advanced`.

.. _central-user-interface-edit:

Editing objects
~~~~~~~~~~~~~~~

Right-clicking on an LDAP object and selecting :guilabel:`Edit` allows to edit
the object. The individual attributes are described in the individual
documentation chapters. By clicking on :guilabel:`Save` at the top of the
module, all changes are written into the LDAP directory. The :guilabel:`Back`
button cancels the editing and returns to the previous search view.

In front of every item in the result list is a checkbox with which individual
objects can be selected. The selection status is also displayed in toolbar at
the top of the table, e.g., *2 users of 102 selected*. If more than one object
is selected, clicking on the :guilabel:`Edit` button in the toolbar activates
the multi edit mode. The same attributes are now shown as when editing an
individual object, but the changes are only accepted for the objects where the
:guilabel:`Overwrite` checkbox is activated. Only objects of the same type can
be edited at the same time.

.. _central-user-interface-remove:

Deleting objects
~~~~~~~~~~~~~~~~

Right-clicking on an LDAP object and selecting :guilabel:`Delete` allows to
delete the object. The prompt must be confirmed. Some objects use internal
references (e.g., a DNS or DHCP object can be associated with computer objects).
These can also be deleted by selecting the :guilabel:`Delete referring objects`
option.

Similar to editing multiple objects at once, multiple objects can be deleted at
once via the :guilabel:`Delete` button in the toolbar.

.. _central-user-interface-move:

Moving objects
~~~~~~~~~~~~~~

Right-clicking on an LDAP object and selecting :guilabel:`Move to...` allows to
to select an LDAP position to which the object should be moved.

Similar to editing multiple objects at once, multiple objects can be moved at
once by selecting :menuselection:`More --> Move to...` in the toolbar.

.. _central-management-umc-notifications:

Display of system notifications
-------------------------------

UMC modules can deploy system notifications to alert the user to potential
errors like join scripts which have not been run or necessary actions such as
available updates. These notifications are shown in the top right corner of the
screen and can be viewed again in the Notifications menu, which can be opened by
clicking the bell icon in the top right corner of the screen.
