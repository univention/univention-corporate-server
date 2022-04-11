.. _print-ppdlisten:

Integrating additional PPD files
================================

The technical capabilities of a printer are specified in so-called PPD files.
These files include for example whether a printer can print in color, whether
duplex printing is possible, whether there are several paper trays, which
resolutions are supported and which printer control languages are supported
(e.g., PCL or PostScript).

In addition to the PPD files already included in the standard scope, additional
ones can be added via UMC modules. The PPDs are generally provided by the
printer manufacturer and need to be copied into the :file:`/usr/share/ppd/`
directory on the print servers.

The printer driver lists are administrated in the UMC module :guilabel:`LDAP
directory`. There you need to switch to the ``univention`` container and then to
the ``cups`` subcontainer. Printer driver lists already exist for the majority
of printer manufacturers. These can be expanded or new ones can be added.

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name (*)
     - The name of the printer driver list. The name under which the list
       appears in the *Printer model* selection list on the
       *General* tab for printer shares (see :ref:`print-shares`).

   * - Driver
     - The path to the :file:`ppd` file or to the :file:`/usr/share/ppd/`
       directory. For example, if the :file:`/usr/share/ppd/laserjet.ppd`
       should be used, :file:`laserjet.ppd` must be entered here.
       :command:`gzip` compressed files (file ending :file:`.gz`) can also be
       entered here.

   * - Description
     - A description of the printer driver, under which it appears in the
       *Printer model* selection list on the *General* tab for printer shares.
