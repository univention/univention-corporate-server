.. _printer-groups:

Creating a printer group
========================

CUPS offers the possibility to group printers into classes. These are
implemented in UCS as *printer groups*. Printer groups appear to clients as
normal printers. The aim of such a printer group is to create a higher
availability of printer services. If the printer group is used to print, the job
is sent to the first printer in the printer group to become available. The
printers are selected based on the round robin principle so that the degree of
utilization is kept uniform.

.. _printergroup:

.. figure:: /images/printer_group.*

A printer group must have at least one printer as a member. Only printers from
the same server can be members of the group.

.. caution::

   The possibility of grouping printers shares from different printer servers in
   a printer group makes it possible to select printer groups as members of a
   printer group. This could result in a printer group adopting itself as a
   group member. This must not be allowed to happen.

Printer groups are administrated in the UMC module :guilabel:`Printers` with the
*Printer share* object type (see :ref:`central-user-interface`).

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name (*)
     - This input field contains the names of the printer group share, which is
       used by CUPS. The printer group appears under this name in Linux and
       Windows.

       The name may contain alphanumeric characters (i.e., uppercase and
       lowercase letters ``a`` to ``z`` and numbers ``0`` to ``9``) as well as
       hyphens and underscores. Other characters (including blank spaces) are
       not permitted.

   * - Print server (*)
     - A range of print servers (spoolers) can be specified here to expand the
       list of printers available for selection. Printers which are assigned to
       the servers specified here can then be adopted in the *Group members*
       list from the selection arranged below them.

   * - Samba name
     - A printer group can also be assigned an additional name by which it can
       reached from Windows. Unlike the CUPS name (see *Name*), the Samba name
       may contain blank spaces and umlauts. The printer is then available to
       Windows under both the CUPS name and the Samba name.

       Using a Samba name in addition to the CUPS name is practical, for
       example, if the printer group was already in use in Windows under a name
       which contains blank spaces or umlauts. The printer group can then still
       be reached under this name without the need to reconfigure the Windows
       computers.

   * - Group members
     - This list is used to assign printers to the printer group.
