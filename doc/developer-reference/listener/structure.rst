.. _listener-handler:

Structure of Listener Modules
=============================

Listener modules can be implemented using the :ref:`listener-handler-42` or the
:ref:`listener-handler-low`.

.. versionadded:: 4.2

   New implementations should be based on the newer high-level API, which is
   available since :uv:erratum:`4.2x311`.

Each listener module must declare several string constants. They are
required by the |UCSUDL| to handle each module.

.. py:currentmodule:: your_module

.. py:data:: name
   :type: str

   (required)

   This name is used to uniquely identify the module. This should match
   with the filename containing this listener module without the
   ``.py`` suffix. The name is used to keep track of
   the module state in :file:`/var/lib/univention-directory-listener/handlers/`.

.. py:function:: get_name()

   :rtype: str

   For description, see :py:data:`name`.

.. py:data:: description
   :type: str

   (required)

   A short description. It is currently unused and displayed nowhere.

.. py:function:: get_description()

   :rtype: str

   For description, see :py:data:`description`.


.. py:data:: filter
   :type: str

   (required)

   Defines a LDAP filter which is used to match the objects the listener
   is interested in. This filter is similar to the LDAP search filter as
   defined in :rfc:`2254`, but more restricted:

   * it is case sensitive

   * it only supports equal matches

.. py:function:: get_ldap_filter()

   :rtype: str

   For description, see :py:data:`filter`.

.. py:data:: ldap_filter
   :type: str

   (high-level API)

   For description, see :py:data:`filter`.

.. py:data:: attributes
   :type: List[str]

   (optional)

   A Python list of LDAP attribute names which further narrows down the
   condition under which the listener module gets called. By default the module
   is called on all attribute changes of objects matching the filter. If the
   list is specified, the module is only invoked when at least one of the listed
   attributes is changed.

.. py:function:: get_attributes()

   :rtype: List[str]

   For description, see :py:data:`attributes`.

.. py:data:: modrdn
   :type: str

   (low-level API, optional)

   Setting this variable to the string ``1`` changes the signature of the
   function :py:func:`handler`. It receives an additional 4th argument, which
   specifies the LDAP operation triggering the change.


.. py:data:: handle_every_delete
   :type: bool

   (low-level API, optional)

   The Listener uses its :ref:`cache <listener-details-cache>` to keep track of
   objects, especially their previous values and which modules handles which
   objects. The |UCSUCRV| :envvar:`listener/cache/filter` can be used to prevent
   certain objects from being stored in the cache. But then the Listener no
   longer knows which module must be called when such an object is deleted.
   Setting this variable to ``True`` will make the Listener call the function
   :py:func:`handler` of this module whenever any object is deleted. The function
   then must use other means to determine itself if the deleted object is of the
   appropriate type as ``old`` will be empty ``dict``.

.. py:data:: priority
   :type: float

   (optional)

   This variable can be used to explicitly overwrite the default order in which
   the modules are executed. By default modules are executed in random order.
   :file:`replication.py` defaults to ``0.0`` as it must be executed first, all
   other modules default to ``50.0``.

.. py:function:: get_priority()

   :rtype: float

   For description, see :py:data:`priority`.

Handle LDAP objects
-------------------

For handling changes to matching LDAP objects a *handler* must be implemented.
This function is called for different events:

* when the object is first created.

* when attributes of an existing object are changed.

* when the object is moved to a different location within the LDAP tree.

* when the object is finally removed.

* when a LDAP schema change happens.

The low-level API requires writing a single function :py:func:`handler` to
handle all those cases. The high-level API already splits this into separate
methods :py:func:`create`, :py:func:`modify` and :py:func:`remove`, which are
easier to overwrite.

Initialize and clean
--------------------

Each module gets initialized once by calling its function :py:func:`initialize`. This
state of each module is tracked in a file below
:file:`/var/lib/univention-directory-listener/handlers/`.

.. py:function:: initialize()

   :rtype: None

   (optional)

   The function :py:func:`initialize` is called once when the |UCSUDL| loads the
   module for the first time. This is recorded persistently in the file
   :file:`/var/lib/univention-directory-listener/{name}`, where ``name`` equals
   the value from the header.

   If for whatever reason the listener module should be reset and re-run for all
   matching objects, the state can be reset by running the following command:

   .. code-block:: console

      $ univention-directory-listener-ctrl resync $name

   In that case the function :py:func:`initialize` will be called again.

.. py:function:: clean

   :rtype: None

   (optional)

   The function :py:func:`clean` is only called when the |UCSUDL| is initialized
   for the first time or is forced to *re-initialize from scratch* using the
   option ``-g``, ``-i``, or ``-P``. The function should purge all previously
   generated files and return the module into a clean state.

   Afterwards the module will be re-initialized by calling the function
   :py:func:`initialize`.

Suspend and resume
------------------

For efficiency reasons the API provides two functions, which resumes and
suspends modules when no transactions are processed for 15 seconds. All modules
start in the state ``suspended``. Before a ``suspended`` modules is called to
handle a change, the function :py:func:`prerun` is called for that module. If no
transactions happen within a time span of 15 seconds the Listener suspends all
active modules by calling the function :py:func:`postrun`. This mechanism is
most often used to batch changes by collecting multiple changes and applying
them only on suspend.

.. py:function:: prerun

   :rtype: None

   (optional);

   For optimization the |UCSUDL| does not keep open an LDAP connection all time.
   Instead the connection is opened once at the beginning of a change and closed
   only if no new change arrives within 15 seconds. The opening is signaled by
   the invocation of the function :py:func:`prerun()` and the closing by
   :py:func:`postrun()`.

   The function :py:func:`postrun()` is most often used to restart services, as
   restarting a service takes some time and makes the service unavailable during
   that time. It's best practice to use the :py:func:`handler()` only to process
   the stream of changes, set UCR variables or generate new configuration files.
   Restarting associated services should be delayed to the :py:func:`postrun()`
   function.

.. py:function:: postrun

   :rytpe: None

   For description, see :py:func:`prerun`.

   .. warning::

      The function :py:func:`postrun` is only called, when no change happens for
      15 seconds. This is not on a per-module basis, but globally. In an ever
      changing system, where the stream of changes never pauses for 15 seconds,
      the functions may never be called!
