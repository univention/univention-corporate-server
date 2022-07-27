.. _translation-dev:

Translating a single Debian package
===================================

When creating a new package or updating an existing one, it is possible to
provide a translation for that package by following the workflow described in
this section. Examples in this section use the German translation, but they are
applicable to any other language as well.

.. _translation-dev-setup:

Setup of :command:`univention-l10n-build`
-----------------------------------------

The setup depends on the operating system developers use to develop the package.
A running UCS installation is recommended, where translators can set up the
tools with :command:`univention-install`, see :ref:`translation-dev-setup-ucs`.
Otherwise, follow the instructions in section
:ref:`translation-dev-setup-non-ucs`. Both setup variants provide the command
:command:`univention-l10n-build`.

.. _translation-dev-setup-ucs:

Setup on a UCS machine
~~~~~~~~~~~~~~~~~~~~~~

Install the package :command:`univention-l10n-dev` as root:

.. code-block:: console

   $ univention-install univention-l10n-dev


After the installation of :program:`univention-l10n-dev`, the command
:command:`univention-l10n-build` is available for the following steps.

Skip the next section and continue with :ref:`translation-dev-workflow`.

.. _translation-dev-setup-non-ucs:

Setup on a non-UCS machine
~~~~~~~~~~~~~~~~~~~~~~~~~~

First, install `Git <https://git-scm.com/downloads>`_, `Python 3.7 or later
<https://www.python.org/downloads/>`_ and ``pip``. For example, run the
following command on Ubuntu 20.04:

.. code-block:: console

   $ sudo apt-get install git python3 python3-pip


To checkout the latest version of the UCS Git repository, if not yet available,
use the following commands:

.. code-block:: console

   $ mkdir ~/translation
   $ cd ~/translation
   $ git clone \
      --single-branch --depth 1 --shallow-submodules \
      https://github.com/univention/univention-corporate-server


Install the python package ``univention-l10n`` with pip:

.. code-block:: console

   $ pip install ~/translation/univention-corporate-server/packaging/univention-l10n/


Pip installs all required Python packages and the command
:command:`univention-l10n-build`.

.. _translation-dev-workflow:

UCS package translation workflow
--------------------------------

The translation process is divided into the following steps:

1. :ref:`translation-dev-workflow-prepare` for translation.

2. :ref:`translation-dev-workflow-update`.

3. :ref:`translation-dev-workflow-build` for the package.

4. :ref:`translation-dev-workflow-translate` the strings by editing the :file:`.po` files.

The :file:`.po` files used in this section contain the German language code
``de`` in the file :file:`de.po`. Use the appropriate language code from the
`ISO-639-1 list <w-iso-639-1_>`_ for other languages.

.. _translation-dev-workflow-prepare:

Prepare the source code
~~~~~~~~~~~~~~~~~~~~~~~

Mark all strings that need translation within the source code. See the following
example for a Python file:

.. code:: python

   from univention.lib.i18n import Translation
   _ = Translation("<packagename>").translate
   example_string = _("Hello World!")


Replace :samp:`<packagename>` with the wanted *gettext* domain, for example the
name of the UCS Debian package like the existing package
:program:`univention-management-console-module-udm`.

For UMC XML files, the translatable XML elements are automatically added to
their associated ``de.po`` file. This includes XML elements like ``name``,
``description``, ``keywords``, and more.

For UMC JavaScript module files, include the translation function ``_`` in the
define function:

.. code:: js

   define([
       "umc/i18n!umc/modules/<module>"
   ], function(_) {
       var example_string = _("Hello World");
   })


Replace :samp:`<module>` with the module id (examples for existing packages:
``appcenter``, ``udm``).

.. _translation-dev-workflow-update:

Add and/or update supplementary files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The program :command:`univention-l10n-build` needs to know which source files
target which ``de.po`` file. ``de.po`` files associate translatable strings with
their translations and are meant to be edited manually. For more information,
see the `gettext <https://www.gnu.org/software/gettext/>`_ framework upon which
:command:`univention-l10n-build` is based. For a UMC package, :file:`de.po`
files are automatically created for its associated XML file, the JavaScript
files and the Python module, see :ref:`umc-modules` about UMC modules. Other
source files have to be declared with ``.univention-l10n`` files that are
located in the ``debian`` directory and structured like the following example
from the package ``univention-appcenter``:

.. code-block::

   [
           {
                   "input_files": [
                           "udm/.*"
                   ],
                   "po_subdir": "udm/handlers/appcenter",
                   "target_type": "mo",
                   "destination": "usr/share/locale/{lang}/LC_MESSAGES/univention-admin-handlers-appcenter.mo"
           }
   ]


This file instructs :command:`univention-l10n` to compile a :file:`de.po` file
in the directory :file:`udm/handlers/appcenter` which includes translations for
all files below the directory :file:`udm`. The name
``univention-admin-handlers-appcenter`` has to be replaced with the wanted
*gettext* domain, for example the name of the new or updated Debian package.
Additionally, if there are one or more ``.univention-l10n`` files, add
``univention-l10n`` to the add-on list in the :file:`debian/rules` file:

.. code-block:: console

   $ dh --with univention-l10n


As an example, refer to the following file tree of the
:program:`appcenter` package, which displays all relevant
files for the translation inside the package:

.. code-block::

   ├── debian
   │    ├── rules
   │    ├── univention-management-console-module-appcenter.umc-modules
   │    ├── univention-management-console-module-appcenter.univention-l10n
   │    └── ...
   ├── ...
   ├── udm
   │   └── handlers
   │       └── appcenter
   │           ├── de.po
   │           └── ...
   └── umc
       ├── appcenter.xml
       ├── de.po
       ├── ...
       ├── js
       │   ├── de.po
       │   ├── appcenter.js
       │   └── ...
       └── python
           └── appcenter
               ├── de.po
               ├── __init__.py
               └── ...


:file:`debian/rules`
   Add :command:`univention-l10n` add-on if non-UMC files have to be translated.

:file:`debian/univention-management-console-module-appcenter.umc-modules`
   See :ref:`umc-modules`.

:file:`debian/univention-management-console-module-appcenter.univention-l10`
   Instructions for translatable non-UMC files.

:file:`udm/handlers/appcenter/de.po`
   Only created/updated if defined in
   ``univention-management-console-module-appcenter.univention-l10n``.

:file:`umc/appcenter.xml`
   UMC standard XML file.

:file:`umc/de.po`
   UMC standard :file:`de.po` file for :file:`appcenter.xml`.

:file:`umc/js/de.po`
   UMC standard :file:`de.po` file for all JavaScript
   files.

:file:`umc/js/appcenter.js`
   One of the JavaScript files with translatable strings.

:file:`umc/python/appcenter/de.po`
   UMC standard :file:`de.po` file for all Python files.

:file:`umc/python/appcenter/__init__.py`
   One of the Python files with translatable strings.

.. _translation-dev-workflow-build:

Run :command:`univention-l10n-build`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the command :command:`univention-l10n-build` in the package directory. The
program finds all marked strings and either updates or creates the corresponding
:file:`de.po` file.

.. warning::

   :command:`univention-l10n-build` updates every package in the current working
   directory and below. Make sure to run the program from inside the package
   directory, if this is not the desired outcome.

.. _translation-dev-workflow-translate:

Translate
~~~~~~~~~

After :command:`univention-l10n-build` finished, the translation can start. Edit
the :file:`de.po` files with a text editor. Find all empty ``msgstr`` fields and enter
the translation of the corresponding ``msgid``. See :ref:`editing-translation-files` for details.

After the translation step, build and test the package on a UCS installation.
Repeat this workflow every time a marked string is changed or a new one is added
to the source files.
