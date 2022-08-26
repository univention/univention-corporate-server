.. _umc-module-python-migration:

Python 3 migration
==================

.. index::
   single: Python 3; migration

|UCSUMC| modules and the Python API for them support both Python 2 and Python 3.
The code of |UCSUMC| modules has to be migrated to Python 3. There is nothing
UMC specific regarding the implementation.

To include Python 3 modules for a |UCSUMC| Debian package the
:file:`debian/control` has to be adjusted: The
``Provides`` entry in package section has to contain
``${python3:Provides}`` for Python 3 and
``${python:Provides}`` for Python 2. Additionally, the
``Depends`` entry should contain
``${python3:Depends}``.

.. code-block::

   Package: univention-management-console-module-...
   Architecture: all
   Depends:
    python3-foo,
    ${python3:Depends},
   Provides:
    ${python3:Provides},
   Description: ...


By adjusting the XML definition of the module it can be specified that it is
executed with Python 3. The attribute :samp:`{python="3"}` has to be added to
the ``<module>`` tag:

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
   <umc version="2.0">
       <module id="..." priority="50" version="1.0" python="3">
           ...
       </module>
   </umc>
