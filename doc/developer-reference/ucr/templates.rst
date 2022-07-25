.. _ucr-conffiles:

UCR Template files :file:`conffiles/{path/to/file}`
================================================================================

.. index::
   single: config registry; template file

For each file, which should be written, one or more template files need be to
created below the :file:`conffiles/` directory. For a single file template (see
:ref:`ucr-file`), the filename must match the filename given in the ``File:``
stanza of the *file* entry itself. For a multi file template (see
:ref:`ucr-multifile`), the filename must match the filename given in the
``File:`` stanza of the *subfile* entries.

Each template file is normally a text file, where certain sections get
substituted by computed values during the file commit. Each section
starts and ends with a special marker. UCR currently supports the
following kinds of markers:

``@%@`` variable reference
   Sections enclosed in ``@%@`` are simple references to |UCSUCRV|. The section
   is replaced inline by the current value of the variable. If the variable is
   unset, an empty string is used.

   :command:`ucr` scans all ``file``\ s and ``subfile``\ s on registration. All
   |UCSUCRV|\ s used in ``@%@`` are automatically extracted and registered for
   triggering the template mechanism. They don't need to be explicitly
   enumerated with ``Variables:`` statements in the file
   :file:`debian/{package}.univention-config-registry`.

``@!@`` Python code
   Sections enclosed in ``@!@`` contain Python code. Everything printed to
   ``STDOUT`` by these sections is inserted into the generated file. The Python
   code can access the ``configRegistry`` variable, which is an already loaded
   instance of ``ConfigRegistry``. Each section is evaluated separately, so no
   state is kept between different Python sections.

   All |UCSUCRV|\ s used in a ``@!@`` Python section must be manually matched by
   a ``Variables:`` statement in the
   :file:`debian/{package}.univention-config-registry` file. Otherwise the file
   is not updated on changes of the UCR variable.

``@%@UCRWARNING=%``\ :samp:`{PREFIX}`\ ``@%@``; ``@%@UCRWARNING_ASCII=%``\ :samp:`{PREFIX}`\ ``@%@``
   This variant of the variable reference inserts a warning text, which looks
   like this:

   .. code-block::

      # Warning: This file is auto-generated and might be overwritten by
      #          univention-config-registry.
      #          Please edit the following file(s) instead:
      # Warnung: Diese Datei wurde automatisch generiert und kann durch
      #          univention-config-registry überschrieben werden.
      #          Bitte bearbeiten Sie an Stelle dessen die folgende(n) Datei(en):
      #
      #       /etc/univention/templates/files/etc/hosts.d/00-base
      #       /etc/univention/templates/files/etc/hosts.d/20-static
      #       /etc/univention/templates/files/etc/hosts.d/90-ipv6defaults
      #


   It should be inserted once at the top to prevent the user from editing the
   generated file. For single File templates, it should be on the top of the
   template file itself. For multi file templates, it should only be on the top
   the first sub-file.

   Everything between the equal sign and the closing ``@%@`` defines the
   :samp:`{PREFIX}`, which is inserted at the beginning of each line of the warning
   text. For shell scripts, this should be ``#`` and a space character, but
   other files use different characters to start a comment. For files, which
   don't allow comments, the header should be skipped.

   .. warning::

      Several file formats require the file to start with some *magic data*. For
      example shell scripts must start with a hash-bang (``#!``) and XML files
      must start with ``<?xml version="1.0" encoding="UTF-8"?>`` (if used). Make
      sure to put the warning after these headers!

   The ``UCRWARNING_ASCII`` variant only emits 7-bit ASCII characters, which can
   be used for files, which are not 8 bit clean or unicode aware.
