.. _ucr-python-migration:

Python 3 Migration
==================

In UCS 5.0 all UCR templates and UCR modules must be compatible with Python 2
and Python 3. This must also be the case for UCS 4.4 and newer, because during
the upgrade to UCS 5.0 UCR templates can be evaluated with either Python
version.

Many templates simply use the Python 2 ``print`` statement:

.. code:: python

   print configRegistry.get('my/variable')


In Python 3 ``print()`` is a function, which requires parenthesis to be added:

.. code:: python

   print(configRegistry.get('my/variable'))


This way the statement is both compatible with Python 2 and Python 3. But it
breaks if multiple arguments are supplied or extra arguments from the Python 3
syntax are used:

.. code:: python

   print("one", "two")
   # Python 2: ('one', 'two')
   # Python 3: one two
   print(configRegistry.get('my/variable'), file=sys.stderr)
   # Python 2: SyntaxError
   # Python 3: Okay


Using ``from __future__ import print_function`` is not allowed as |UCSUCR|
executes Python code before the template is imported.

The deprecated variable ``baseConfig`` has been removed, but ``configRegistry``
remains for using.

The API of ``ConfigRegistry`` works with ``str``. For Python 2 this equals
``bytes``, while for Python 3 this is a ``unicode`` string.

The test case
:file:`/usr/share/ucs-test/03_ucr/37check-ucr-templates-py3-migration-status.py`
from the package :program:`ucs-test-ucr` can be used to check if the UCR
template output works with both Python versions and is idempotent.

UCR modules and scripts have no API changes. They simply need to be migrated to
be Python 3 compatible.
