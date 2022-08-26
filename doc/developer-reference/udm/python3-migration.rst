.. _udm-python-migration:

UCS 5.0: Python 3 migration of modules and extensions
=====================================================

.. index::
   single: Python 3; migration

UCS 5.0 switched from Python 2 to Python 3. This also affects |UCSUDM|. Starting
with UCS 5.0 the modules and extensions like syntax classes and hooks must be
compatible with both Python versions to ensure easier transition.

Python 2 support will be removed completely with UCS 5.1.

This chapter describes important aspects of the migration as well as changes to
the API.

.. _udm-python-migration-compatibility:

Compatibility with UCS 4.4
--------------------------

Most changes proposed in this chapter are compatible with UCS 4.4. One exception
is the registration of the mapping encoding. The changes suggested here should
already be included in the UDM modules for UCS 4.4 to make the update easier.

The changes suggested here should already be included for UCS 4.4. Otherwise,
the update to UCS 5.0 may be problematic. Apps that still install UDM modules
under UCS 4.4, while the |UCSPRIMARYDN| may already be UCS 5, must also contain
the customizations in the UDM modules or register 2 different variants,
otherwise the app will not be displayed on the |UCSPRIMARYDN| in |UCSUMC| /
|UCSUDM|, for example.

For the registration of UDM extensions the parameters to specify the compatible
starting and end UCS version are now mandatory. While a join script looked like:

.. code-block:: bash
   :caption: Example for deprecated join script

   . /usr/share/univention-lib/ldap.sh

   ucs_registerLDAPExtension "$@" \
       --udm_module /usr/lib/python3/dist-packages/univention/admin/handlers/foo/bar.py


it may now specify the compatible UCS versions:

.. code-block:: bash
   :caption: Example for join script that defines the compatible UCS versions

   . /usr/share/univention-lib/ldap.sh

   ucs_registerLDAPExtension "$@" \
       --ucsversionstart "4.4-0" \
       --ucsversionend "5.99-0" \
       --udm_module /usr/lib/python3/dist-packages/univention/admin/handlers/foo/bar.py


or register two separate versions compatible for each UCS version:

.. code-block:: bash
   :caption: Example for join script that defines two UCS versions

   . /usr/share/univention-lib/ldap.sh

   ucs_registerLDAPExtension "$@" \
       --ucsversionstart "4.4-0" \
       --ucsversionend "4.99-0" \
       --udm_module /usr/lib/python3/dist-packages/univention/admin/handlers/foo/bar.py

   ucs_registerLDAPExtension "$@" \
       --ucsversionstart "5.0-0" \
       --ucsversionend "5.99-0" \
       --udm_module /usr/lib/python3/dist-packages/univention/admin/handlers/foo/bar.py


.. _udm-python-migration-default-option:

Default option
--------------

If not already present, the module should define a ``default`` |UCSUDM| option:

.. code-block:: python

   options = {
       'default': univention.admin.option(
           short_description=short_description,
           default=True,
           objectClasses=['top', 'objectClassName'],
       )
   }
   class object(...):
       ...


This enables generic functionality like automatic creation of search filters,
automatic identification of objects and obsoletes the need to create the
add-list manually.

.. _udm-python-migration-mapping-functions:

Mapping functions
-----------------

The ``unmap`` functions must decode the given list of ``byte`` strings
(:py:class:`bytes`) into ``unicode`` strings (:py:class:`str`). The
``map`` functions must encode the result of the ``unmap``
functions (for example ``unicode`` strings ``str``) into a list of ``byte``
strings (:py:class:`bytes`). Both functions have a new optional parameter
``encoding``, which is a tuple consisting of the encoding (defaults to
``UTF-8``) and the error handling in case de/encoding fails (defaults to
``strict``).

Deprecated UCS 4 code most often looked like:

.. code-block:: python

   def map_function(value):
       return [value]


   def unmap_function(value):
       return value[0]


   mapping.register('property', 'attribute', map_function, unmap_function)


In UCS 5.0 the code has to look like:

.. code-block:: python

   def map_function(
       value: Union[Text, Sequence[Text]],
       encoding: Optional[Tuple[str, str]] = None,
   ) -> List[bytes]:
       return [value.encode(*encoding)]


   def unmap_function(
       value: Sequence[bytes],
       encoding: Optional[Tuple[str, str]] = None,
   ) -> Text:
       return value[0].decode(*encoding)


   mapping.register('property', 'attribute', map_function, unmap_function)


.. _udm-python-migration-mapping-encoding:

Mapping encoding
----------------

.. warning::

   Specifying the mapping encoding is incompatible with UCS 4.4.

The registration of the mapping of LDAP attributes to |UCSUDM| properties now
has to specify the correct encoding explicitly. The default encoding used is
``UTF-8``. As most LDAP data is stored in ``UTF-8`` the encoding parameter can
be left out for most properties.

The encoding can simply be specified in the registration of a mapping:

.. code-block:: python

   mapping.register('property', 'attribute', map_function, unmap_function, encoding='ASCII')


The encoding depends on the LDAP syntax of the corresponding LDAP attribute.
Syntaxes storing binary data should either be specified as ``ISO8859-1`` or
preferably should be decoded to an ``ASCII`` representation of ``base64``
through :py:func:`univention.admin.mapping.mapBase64` and
:py:func:`univention.admin.mapping.unmapBase64`. The attributes of the following
syntaxes for example should be set to ``ASCII`` as they consist of ASCII only
characters or a subset of ASCII (for example numbers).

* IA5 String (1.3.6.1.4.1.1466.115.121.1.26)

* Integer (1.3.6.1.4.1.1466.115.121.1.27)

* Printable String (1.3.6.1.4.1.1466.115.121.1.44)

* Boolean (1.3.6.1.4.1.1466.115.121.1.7)

* Numeric String (1.3.6.1.4.1.1466.115.121.1.36)

* Generalized Time (1.3.6.1.4.1.1466.115.121.1.24)

* Telephone Number (1.3.6.1.4.1.1466.115.121.1.50)

* UUID (1.3.6.1.1.16.1)

* Authentication Password (1.3.6.1.4.1.4203.1.1.2)

To find out the syntax of an LDAP attribute programmatically for example for the
attribute ``gecos``:

.. code-block:: bash

   python -c '
   from univention.uldap import getMachineConnection
   from ldap.schema import AttributeType
   conn = getMachineConnection()
   schema = conn.get_schema()
   attr = schema.get_obj(AttributeType, "gecos")
   print(atttr.syntax)'


.. _udm-python-migration-open:

``object.open()`` / ``object._post_unmap()``
--------------------------------------------

LDAP attributes contained in ``self.oldattr`` are usually transformed into
property values (in ``self.info``) by the mapping functions. In some cases this
can't be done automatically.

Instead this is done manually in the methods ``open()`` or ``_post_unmap()``.
These functions must consider transforming ``byte`` strings (:py:class:`bytes`
in ``self.oldattr``) into ``unicode`` strings (:py:class:`str` in
``self.info``).

.. _udm-python-migration-haskey:

``object.has_key()``
--------------------

The method ``has_key()`` has been renamed into ``has_property()``. The method
``has_property()`` is already present in UCS 4.4.

.. _udm-python-migration-identify:

``identify()``
--------------

The ``identify()`` function must now consider that the given attribute values
are ``byte`` strings. The code prior looked like:

.. code-block:: python

   def identify(dn, attr, canonical=False):
       return 'objectClassName' in attr.get('objectClass', [])


In UCS 5.0 the code have to look like:

.. code-block:: python

   class object(...):
       ...
       @classmethod
       def identify(cls, dn, attr, canonical=False):
           return b'objectClassName' in attr.get('objectClass', [])


   identify = object.identify


In most cases the ``identify()`` function only checks for the existence of a
specific LDAP ``objectClass``. The generic implementation can be used instead,
which requires the ``default`` UDM option to be set:

.. code-block:: python

   options = {
       'default': univention.admin.option(
           short_description=short_description,
           default=True,
           objectClasses=['top', 'objectClassName'],
       )
   }
   class object(...):
       ...


   identify = object.identify


.. _udm-python-migration-modlist:

``_ldap_modlist()``
-------------------

The methods ``_ldap_modlist()`` and ``_ldap_addlist()`` now must insert ``byte``
strings into the add/modlist. The code prior looked like:

.. code-block:: python

   class object(...):
       ...
       def _ldap_addlist(al):
           al = super(object, self)._ldap_addlist(al)
           al.append(('objectClass', ['top', 'objectClassName']))
           return al

       def _ldap_modlist(ml):
           ml = super(object, self)._ldap_modlist(ml)
           value = ...
           new = [value]
           ml.append(('attribute', self.oldattr.get('attribute', []), new))
           return ml


In UCS 5.0 the code have to look like:

.. code-block:: python

   class object(...):
       ...
       def _ldap_addlist(al):
           al = super(object, self)._ldap_addlist(al)
           al.append(('objectClass', [b'top', b'objectClassName']))
           return al

       def _ldap_modlist(ml):
           ml = super(object, self)._ldap_modlist(ml)
           value = ...
           new = [value.encode('UTF-8')]
           ml.append(('attribute', self.oldattr.get('attribute', []), new))
           return ml


The ``_ldap_addlist()`` is mostly not needed and should be replaced by
specifying a default option (see above).

.. _udm-python-migration-lookup:

``lookup()``
------------

The ``lookup()`` should be replaced by specifying a default option as described
above. The class method ``rewrite_filter()`` can be used to add additional
filter rules.

.. _udm-python-migration-syntax:

Syntax classes
--------------

Syntax classes now must ensure to return ``unicode`` strings.

.. _udm-python-migration-hooks:

Hooks
-----

For hooks the same rules as in ``_ldap_modlist()`` apply.
