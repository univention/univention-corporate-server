.. _umc-files:

UMC files
=========

.. index::
   single: management console; files

Files for building a UMC module.

.. _umc-modules:

:file:`debian/{package}.umc-modules`
--------------------------------------------------------------------------------------------------------------

.. index::
   single: management console; umc-modules

* :command:`univention-l10n-build` builds translation files.

* :command:`dh-umc-module-install` installs files.

Configured through
:file:`debian/{package}.umc-modules`.

``Module``
   Internal (?) name of the module.

``Python``
   Directory containing the Python code relative to top-level directory.

..   PMH: Bug #31151

``Definition``
   Path to an XML file, which describes the module. See :ref:`umc-xml` for more
   information.

``Javascript``
   Directory containing the Java-Script code relative to top-level directory.

.. PMH: Bug #31151

``Icons`` (deprecated)
   Directory containing the Icons relative to top-level directory. Must provide
   icons in sizes 16×16 (:file:`umc/icons/16x16/udm-{module}.png`) and 50×50
   (:file:`umc/icons/50x50/udm-{module}.png`) pixels.

.. _umc-xml:

UMC module declaration file
---------------------------

.. index::
   single: management console; XML

:file:`umc/{module}.xml`

.. PMH: Bug #26275

.. literalinclude:: module.xml
   :language: xml

:file:`umc/categories/{category}.xml`

.. literalinclude:: module-categories.xml
   :language: xml

