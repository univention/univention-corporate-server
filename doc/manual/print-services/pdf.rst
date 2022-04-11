.. _pdf-printer:

Generating PDF documents from print jobs
========================================

Installing the :program:`univention-printserver-pdf` package expands the print
server with a special *cups-pdf* printer type, which converts incoming print
jobs into PDF documents and adds them in a specified directory on the printer
server where they are readable for the respective user. After the installation
of the package, :command:`univention-run-join-scripts` must be run.

The ``cups-pdf:/`` protocol must be selected when creating a PDF printer
in the UMC module :guilabel:`Printers` (see :ref:`print-shares`); the
destination field remains empty.

``PDF`` must be selected as *Printer producer* and ``Generic CUPS-PDF Printer``
as *Printer model*.

The target directory for the generated PDF documents is set using the |UCSUCRV|
:envvar:`cups/cups-pdf/directory`. As standard it is set to
:file:`/var/spool/cups-pdf/%U` so that :program:`cups-pdf` uses a different
directory for each user.

Print jobs coming in anonymously are printed in the directory specified by the
|UCSUCRV| :envvar:`cups/cups-pdf/anonymous` (standard setting:
:file:`/var/spool/cups-pdf/`).

By default generated PDF documents are kept without any restrictions. If the
|UCSUCRV| :envvar:`cups/cups-pdf/cleanup/enabled` is set to ``true``, old PDF
print jobs are deleted via a Cron job. The storage time in days can be
configured using the |UCSUCRV| :envvar:`cups/cups-pdf/cleanup/keep`.
