.. _computers-softwaremanagement:

*******************
Software deployment
*******************

The software deployment integrated in UCS offers extensive possibilities for the
rollout and updating of UCS installations. Security and version updates can be
installed via the UMC module :guilabel:`Software update`, a command line tool or
based on policies. This is described in the section :ref:`software-ucs-updates`.
The UCS software deployment does not support the updating of Microsoft Windows
systems. An additional Windows software distribution is required for this.

For larger installations, there is the possibility of establishing a local
repository server from which all further updates can be performed, see
:ref:`software-config-repo`.

The UCS software deployment is based on the underlying Debian package management
tools, which are expanded through UCS-specific tools. The different tools for
the installation of software are introduced in
:ref:`computers-softwaremanagement-install-software`. The installation of version
and errata updates can be automated via policies, see
:ref:`computers-softwaremanagement-maintenance-policy`

The software monitor provides a tool with which all package installations
statuses can be centrally stored in a database, see
:ref:`computers-software-monitor`.

The initial installation of UCS systems is not covered in this chapter, but is
documented in :ref:`installation-chapter` instead.

.. toctree::
   :caption: Chapter contents:

   ucs-versions
   app-center
   updates
   repository-server
   further-software
   package-maintenance-policy
   software-monitor
