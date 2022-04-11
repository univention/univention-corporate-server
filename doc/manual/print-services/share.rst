.. _print-shares:

Creating a printer share
========================

Print shares are administrated in the UMC module :guilabel:`Printers` with the
*Printer share* object type (see :ref:`central-user-interface`).

.. _create-printershare:

.. figure:: /images/create_printershare.*
   :alt: Creating a printer share

   Creating a printer share

When adding/deleting/editing a printer share, the printer is automatically
configured in CUPS. CUPS does not have an LDAP interface for printer
configuration, instead the :file:`printers.conf` file is generated via a
listener module. If Samba is used, the printer shares are also automatically
provided for Windows clients.

.. _printer-shares-umc-general-tab:

Printers UMC module - General tab
---------------------------------

.. _printer-shares-umc-general-tab-table:

.. list-table:: *General* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Name (*)
     - This input field contains the name of the printer share, which is used by
       CUPS. The printer appears under this name in Linux and Windows. The name
       may contain alphanumeric characters (i.e., uppercase and lowercase
       letters a to z and numbers 0 to 9) as well as hyphens and underscores.
       Other characters (including blank spaces) are not permitted.

   * - Print server (*)
     - A print server manages the printer queue for the printers to be shared.
       It converts the data to be printed into a compatible print format when
       this is necessary. If the printer is not ready, the print server saves
       the print jobs temporarily and forwards them on to the printer
       subsequently. If more than one print server is specified, the print job
       from the client will be sent to the first print server to become
       available.

       Only UCS Directory Node and |UCSMANAGEDNODE|\ s on which the
       :program:`univention-printserver` package is installed are displayed in
       the list.

   * - Protocol and Destination (*)
     - These two input fields specify how the print server accesses the printer.

       The following list describes the syntax of the individual protocols for
       the configuration of printers connected locally to the server:

       * :samp:`parallel://{devicefile}`

         Example: ``parallel://dev/lp0``

       * :samp:`socket://{server}:{port}`

         Example: ``socket://printer_03:9100``

       * :samp:`usb://{devicefile}`

         Example: ``usb://dev/usb/lp0``

       The following list describes the syntax of the individual protocols for
       the configuration of network printers:

       * :samp:`http://{server}[:{port}]/{path}`

         Example: ``http://192.0.2.10:631/printers/remote``

       * :samp:`ipp://{server}/printers/{queue}`

         Example: ``ipp://printer_01/printers/xerox``

       * :samp:`lpd://{server}/{queue}`

         Example: ``lpd://192.0.2.30/bwdraft``

       The ``cups-pdf`` protocol is used for integrating a pseudo printer, which
       creates a PDF document from all the print jobs. The setup is documented
       in :ref:`pdf-printer`.

       The ``file:/`` protocol expects a file name as a target. The print job is
       then not sent to the printer, but instead written in this file, which can
       be useful for test purposes. The file is rewritten with every print job.

       The ``smb://`` protocol can be used to mount a Windows print share. For
       example, to integrate the ``laser01`` printer share from Windows system
       ``win01``, ``win01/laser01`` must be specified as destination. The
       manufacturer and model must be selected according to the printer in
       question. The print server uses the printer model settings to convert the
       print jobs where necessary and send these directly to the URI
       ``smb://win01/laser01``. No Windows drivers are used in this.

       Independent of these settings, the printer share can be mounted by other
       Windows systems with the corresponding printer drivers.

   * - Manufacturer
     - When the printer manufacturer is selected, the *Printer model* selection
       list updates automatically.

   * - Printer model (*)
     - This selection list shows all the printers PPD files available for the
       selected manufacturer. If the required printer model is not there, a
       similar model can be selected and a test print used to establish correct
       function. :ref:`print-ppdlisten` explains how to expand the list of
       printer models.

   * - Samba name
     - A printer can also be assigned an additional name by which it can be
       reached from Windows. Unlike the CUPS name (see *Name*), the Samba name
       may contain blank spaces and umlauts. The printer is then available to
       Windows under both the CUPS name and the Samba name.

       Using a Samba name in addition to the CUPS name is practical, for
       example, if the printer was already in use in Windows under a name which
       contains blank spaces or umlauts. The printer can then still be reached
       under this name without the need to reconfigure the Windows computers.

   * - Location
     - This data is displayed by some applications when selecting the printer.
       It can be filled with any text.

   * - Description
     - This is displayed by some applications when selecting the printer. It can
       be filled with any text.

.. _printer-shares-umc-access-control-tab:

Printers UMC module - Access control tab
----------------------------------------

.. _printer-shares-umc-access-control-tab-table:

.. list-table:: *Access control* tab
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Access control
     - Access rights for the printer can be specified here. Access can be
       limited to certain groups or users or generally allowed and certain
       groups or users blocked specifically. As standard, access is available
       for all groups and users. These rights are also adopted for the
       corresponding Samba printer shares, so that the same access rights apply
       when printing via Samba as when printing directly via CUPS.

       This access control is useful for the management of printers spread
       across several locations, so that the users at location A do not see the
       printers of location B.

   * - Allowed/denied users
     - This lists individual users for whom access should be controlled.

   * - Allowed/denied groups
     - This lists individual groups for whom access should be controlled.
