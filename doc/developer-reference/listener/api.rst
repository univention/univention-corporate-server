.. _listener-handler-42:

High-level Listener modules API
===============================

.. py:currentmodule:: high_level

|UCSUDL| ships with a template in
:uv:src:`management/univention-directory-listener/examples/listener_module_template.py`.
This should be used as a starting point for new modules. The more complex
example in
:uv:src:`management/univention-directory-listener/examples/complex_handler.py`
can also be used.

Alternatively the implementation can start from scratch:

1. Create a subclass of :py:class:`univention.listener.ListenerModuleHandler`.

2. Add an inner class called ``Configuration`` which at least has the attributes
   :py:data:`name`, :py:data:`description` and :py:data:`ldap_filter`.

The inner class ``Configuration`` is used to configure global module
settings. For most properties a corresponding method exists, which just
returns the value of the property by default. The methods can be
overwritten if values should be computed once on module load.

.. py:function:: get_name

   :rtype: str

   (required)

   The internal name of the handler, see :py:data:`name <your_module.name>`.

.. py:data:: name
   :type: str

   The internal name of the handler, see :py:data:`name <your_module.name<`.


.. py:function:: get_description

   A descriptive text, see :py:data:`description <your_module.description>`.


.. py:data:: description
   :type: str

   A descriptive text, see :py:data:`description <your_module.description>`.

.. py:function:: get_ldap_filter

   The LDAP filter string, see :py:data:`filter <your_module.filter>`.

.. py:data:: ldap_filter
   :type: str

   The LDAP filter string, see :py:data:`filter <your_module.filter>`.

.. py:function:: get_attributes

   The list of attributes, for when they are changed, the module is called; see
   :py:data:`attributes <your_module.attributes>`.

.. py:data:: attributes
   :type: str

   The list of attributes, for when they are changed, the module is called; see
   :py:data:`attributes <your_module.attributes>`.

.. py:function:: get_priority

   The priority for ordering; see :py:data:`priority <your_module.priority>`.

.. py:data:: priority
   :type: float

   The priority for ordering; see :py:data:`priority <your_module.priority>`.

.. py:function:: get_listener_module_instance

   :rtype: ListenerModuleHandler

   This creates an instance of the handler module and returns it.

.. py:function:: get_listener_module_class

   :rtype: typing.List[ListenerModuleHandler]

   (optional)

   Class that implements the module. Will be set automatically by the handlers
   meta-class.

.. py:data:: listener_module_class
   :type: typing.List[ListenerModuleHandler]

.. py:function:: get_active

   :rtype: bool

   This returns the value of the |UCSUCRV|
   :samp:`listener/module/{name}/deactivate` as a boolean. Setting the variable
   to ``False`` will prevent the module from being called for all changes.

   .. note::

      Re-enabling the module will not result in the module being called for all
      previously missed changes. For this the module must be fully
      resynchronized.

The handler itself should inherit from
:py:class:`univention.listener.ListenerModuleHandler` and then overwrite some
methods to provide its own implementation:

.. py:function:: create(dn: str, new: typing.Dict[str, typing.List[bytes]])

   :param str dn:
   :param typing.Dict[str, typing.List[bytes]]) new:

   :rtype: None

   Called when a new object was created.

.. py:function:: modify(dn: str, new: typing.Dict[str, typing.List[bytes]], old: typing.Dict[str, typing.List[bytes]], old_dn: typing.Optional[str])

   :param str dn:
   :param typing.Dict[str, typing.List[bytes]] new:
   :param typing.Dict[str, typing.List[bytes]] old:
   :param typing.Optional[str]) old_dn:

   :rtype: None

   Called when a new object was modified or moved. In case of a move ``old_dn``
   is set. During a move attributes may be modified, too.

.. py:function:: remove(dn: str, old: typing.Dict[str, typing.List[bytes]])

   :param str dn:
   :param typing.Dict[str, typing.List[bytes]] old:

   :rtype: None

   Called when a new object was deleted.

.. py:function:: initialize

   :rtype: None

   Called once when the module is not initialized yet.

.. py:function:: clean

   :rtype: None

   Called once before a module is resynchronized.

.. py:function:: pre_run

   :rtype: None

   Called once each time before a batch of transactions is processed.

.. py:function:: post_run

   :rtype: None

   Called once each time after a batch of transactions is processed.

In addition to those handler functions the class also provides several
convenience functions:

.. py:function:: as_root

   :rtype: None

   A context manager to temporarily change the effective UID of the current to
   ``0``. Also see :py:func:`listener.SetUID` described in
   :ref:`listener-details-credentials`.

.. py:function:: diff(old: typing.Dict[str, typing.List[bytes]], new: typing.Dict[str, typing.List[bytes]], keys: typing.Optional[typing.Iterable[str]], ignore_metadata: bool)

   :param typing.Dict[str, typing.List[bytes]] old:
   :param typing.Dict[str, typing.List[bytes]] new:
   :param typing.Optional[typing.Iterable[str]]keys:
   :param bool ignore_metadata:

   :rtype: typing.Dict[str, typing.Tuple[typing.Optional[typing.List[bytes]], typing.Optional[typing.List[bytes]]]]

   Calculate difference between old and new LDAP attributes. By default all
   attributes are compared, but this can be limited by naming them via ``keys``.
   By default *operational attributes* are excluded unless ``ignore_metadata``
   is enabled.

.. py:function:: error_handler(dn: str, old: typing.Dict[str, typing.List[bytes]], new: typing.Dict[str, typing.List[bytes]], command: str, exc_type: typing.Optional[typing.Type[BaseException]], exc_value: typing.Optional[BaseException], exc_traceback: typing.Optional[types.TracebackType])

   :param str dn:
   :param typing.Dict[str, typing.List[bytes]] old:
   :param typing.Dict[str, typing.List[bytes]] new:
   :param str command:
   :param typing.Optional[typing.Type[BaseException]] exc_type:
   :param typing.Optional[BaseException] exc_value:
   :param typing.Optional[types.TracebackType] exc_traceback:

   :rtype: None

   This method will be called for unhandled exceptions in create/modify/remove.
   By default it logs the exception and re-raises it.

.. py:property:: lo
   :type: univention.uldap.access

   This property returns a LDAP connection object to access the local
   LDAP server.

.. py:property:: po
   :type: univention.uldap.position

   This property returns a LDAP position object for the LDAP base DN.

Any instance also has the following variables:

.. py:data:: logger
   :type: logging.Logger

   An instance of ``logging.Logger``.

.. py:data:: ucr
   :type: univention.config_registry.ConfigRegistry

   A reference to the shared instance :py:class:`listener.configRegistry`.
