.. _software-ucs-updates:

Updates of UCS systems
======================

There are two ways to update UCS systems; either on individual systems (via UMC
module :guilabel:`Software update` or command line) or via a computer policy for
larger groups of UCS systems.

.. _computers-update-strategy-in-environments-with-more-than-one-ucs-system:

Update strategy in environments with more than one UCS system
-------------------------------------------------------------

In environments with more than one UCS system, the update order of the
UCS systems must be borne in mind.

The authoritative version of the LDAP directory service is maintained on the
|UCSPRIMARYDN| and replicated on all the remaining LDAP servers of the UCS
domain. As changes to the LDAP schemes (see :ref:`domain-ldap-schema`) can occur
during release updates, the |UCSPRIMARYDN| **must always be the first system**
to be updated during a release update.

It is generally advisable to update all UCS systems in one maintenance
window whenever possible. If this is not possible, all not-updated UCS
systems should only be one release version older compared with the
|UCSPRIMARYDN|.

.. _computers-updating-individual-systems-via-the-umc:

Updating individual systems via |UCSUMC| module
-----------------------------------------------

The UMC module :guilabel:`Software update` allows the installation of release
updates and errata updates.

:numref:`software-umcupdate` shows the overview page of the module. The
currently installed version is displayed under :guilabel:`Release updates`.

.. _software-umcupdate:

.. figure:: /images/software_onlineupdate.*
   :alt: Updating a UCS system via UMC module 'Software update'

   Updating a UCS system via UMC module *Software update*


If a newer UCS version is available, a selection list is displayed.
After clicking on :guilabel:`Install release updates` and
confirmation all updates up to the respective version are installed.
Before the installation process is started, a message will be displayed
informing the user of possible restrictions of the server's services
during the update. Any intermediate versions are also installed
automatically.

Clicking on :guilabel:`Install available errata updates`
installs all the available errata updates for the current release and
all installed components.

:guilabel:`Check for package updates` activates an update of
the package sources currently entered. This can be used, for example, if
an updated version is provided for a component.

The messages created during the update are written to the file
:file:`/var/log/univention/updater.log`

.. _computers-updating-individual-systems-via-the-command-line:

Updating individual systems via the command line
------------------------------------------------

The following steps must be performed with ``root`` user rights.

An individual UCS system can be updated using the :command:`univention-upgrade`
command in the command line. A check is performed to establish whether new
release or application updates are available and these are then installed if a
prompt is confirmed. In addition, package updates are also performed (e.g., in
the scope of an errata update).

Remote updating over SSH is not advisable as this may result in the update
procedure being aborted. If updates should occur over a network connection
nevertheless, it must be verified that the update continues despite
disconnection from the network. This can be done, for example, using the tools
:program:`screen` and :program:`at`, which are installed on all system roles.

The messages created during the update are written to the file
:file:`/var/log/univention/updater.log`

.. _computers-softwaremanagement-releasepolicy:

Updating systems via a policy
-----------------------------

An update for more than one computer can be configured with an
:guilabel:`Automatic updates` policy in the UMC modules :guilabel:`Computers`
and :guilabel:`LDAP directory` (see :ref:`central-policies`).

.. _software-policyupdate:

.. figure:: /images/software_policy.*
   :alt: Updating UCS systems using an update policy

   Updating UCS systems using an update policy

A release update is only run when the *Activate release updates* selection field
is activated.

The *Update to this UCS version* input field includes the version number up to
which the system should be updated, for example ``5.0-0``. If no entry is made,
the system continues updating to the highest available version number.

The point at which the update should be performed is configured via a
:guilabel:`Maintenance` policy (see
:ref:`computers-softwaremanagement-maintenancepolicy`).

The messages created during the update are written to the file
:file:`/var/log/univention/updater.log`.

.. _computers-postprocessing-of-release-updates:

Postprocessing of release updates
---------------------------------

Once a release update has been performed successfully, a check should be
made for whether new or updated join scripts need to be run.

Either the UMC module :guilabel:`Domain join` or the command
line program :command:`univention-run-join-scripts` is used
for checking and starting the join scripts (see
:ref:`linux-domain-join`).

.. _computers-troubleshooting:

Troubleshooting in case of update problems
------------------------------------------

The messages generated during updates are written to the
:file:`/var/log/univention/updater.log` file, which can
be used for more in-depth error analysis.

The status of the |UCSUCR| variables before the release update is saved in
the :file:`/var/univention-backup/update-to-TARGETRELEASEVERSION/`
directory. This can then be used to check whether and which variables
have been changed during the update.
