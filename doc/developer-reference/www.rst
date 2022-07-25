.. _chap-www:

************
Web services
************

.. index::
   single: web services
   see: apache; web services

.. _www-overview:

Extending the overview page
===========================

When users open ``http://localhost/`` or :samp:`http://{hostname}/` in a
browser, they are redirected to the UCS overview page.

Depending on the preferred language negotiated by the web browser the user is
either redirected to the German or English version. The overview page is split
between *Installed web services* and *Administration* entries.

The start page can be extended using |UCSUCR| variables. :samp:`{PACKAGE}` refers
to a unique identifier, typically the name of the package shipping the
extensions to the overview page. The configurable options are explained below:

* :envvar:`ucs/web/overview/entries/admin/PACKAGE/OPTION` variables extend the
  administrative section.

* :envvar:`ucs/web/overview/entries/service/PACKAGE/OPTION` variables extend the
  web services section.

To configure an extension of the overview page the following options must/can be
set using the pattern :envvar:`ucs/web/overview/entries/admin/PACKAGE/OPTION`\
``=*VALUE*`` (and likewise for services).

``link``
   defines a link to a URL representing the service (usually a web interface).

``label``
   specifies a title for an overview entry. The title can also be translated;
   for example ``label/de`` can be used for a title in German.

``description``
   configures a longer description of an overview entry. The description can
   also be translated; for example ``description/de`` can be used for a
   description in German. Should not exceed 60 characters, because of space
   limitations of the rendered box.

``icon``
   Optionally an icon can be displayed. Using ``icon``, either a filename or a
   URI can be provided. When specifying a filename, the name must be relative to
   the directory :file:`/var/www`, that is with a leading '/'. All file formats
   typically displayed by browsers can be used (for example PNG/JPG). All icons
   must be scaled to *50x50* pixels.

``priority``
   The display order can be specified using ``priority``. Depending on the
   values the entries are displayed in *lexicographical* order (i.e.
   ``100`` < ``50``).

