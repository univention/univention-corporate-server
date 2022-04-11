.. _print-services-configuration:

Setting the local configuration properties of a print server
============================================================

The configuration of the CUPS print server is performed via settings from the
LDAP directory service and |UCSUCR|. If the |UCSUCRV|
:envvar:`cups/include/local` is set to ``true``, the
:file:`/etc/cups/cupsd.local.conf` file is included, in which arbitrary options
can be defined. Changes in this file require :command:`ucr commit
/etc/cups/cupsd.conf` to get applied.

If an error occurs when working through a printer queue (e.g., because the
connected printer is switched off), the further processing of the queue is
stopped by default. This must then be reactivated by the administrator (see
:ref:`umc-modules-printer`). If the |UCSUCRV| :envvar:`cups/errorpolicy` is set
to ``retry-job``, CUPS automatically attempts to process unsuccessful print jobs
again every 30 seconds.
