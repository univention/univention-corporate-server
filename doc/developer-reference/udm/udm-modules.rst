.. _udm-modules:

UDM modules
===========

.. index::
   single: directory manager; custom modules

.. PMH: Bug #29525

|UCSUDM| uses a flexible and extensible structure of Python modules to manage
the directory service data. Additional modules are automatically recognized
after being saved to the file system and made available for use at the command
line and web interface. The development of custom modules enables the flexible
extension of the |UCSUDM| beyond the scope of extended attributes.

.. _udm-modules-overview:

Overview
--------

|UCSUDM| (UDM for short) uses its own module structure to map LDAP objects.
Usually one of these UDM modules corresponds to an LDAP object (for example a
user, a group or a container).

The modules are stored in the
:file:`/usr/lib/python3/dist-packages/univention/admin/handlers/` directory and
organized by task. The modules for managing the various computer objects are
located below the :file:`computers/` folder, for example. It can be addressed by
the command line interface through ``computers/windows``.

Custom modules should, if possible, be placed in their own subdirectory to avoid
conflicts with any standard modules that may later be integrated into UCS. For
the modules to be initialized, a :file:`__init__.py` file must exist in the
directory.

.. _udm-modules-structure:

Structure of a module
---------------------

Modules contain the definition of the UDM properties and the definition
of a class named ``object``, which is derived from
:py:class:`univention.admin.handlers.simpleLdap`.

.. note::

   The default name of the base class ``object`` has historical reasons. It must
   be kept despite the name collision with the
   :external+python-general:py:class:`Python type object <object>`.

This section will begin with a detailed description of the variables to be
defined. The :ref:`udm-modules-class` takes a closer look at the ``object``
class and lists necessary definitions and functions within the class.

.. _udm-modules-globals:

Global variables
~~~~~~~~~~~~~~~~

The global variables with specific meanings in a |UCSUDM| module are
described below. Mandatory and optional variables are separated into mandatory
variables and optional arguments.

.. py:module:: udm_modules_globals

.. _udm-modules-globals-mandatory:

Mandatory variables
~~~~~~~~~~~~~~~~~~~

.. py:data:: module

   A string matching the name of the UDM module, for example
   ``computers/computer``.

.. py:data:: operations

   A list of strings which contains all LDAP operations allowed with this
   object. Available operations are add, edit, remove, search, subtree_move,
   copy.

.. py:data:: short_description

   This description is displayed as the name in the |UCSUMC|. Within the UMC
   module LDAP navigation it is displayed in the selection list for possible
   object types.

.. py:data:: long_description

   A detailed description of the module.

.. py:data:: childs

   Indicates whether this LDAP object is a container. If so, this variable is
   set to the value ``True``, and otherwise to ``False``.

.. py:data:: options

   Variable ``options`` is a Python dictionary and defines various options that
   can either be set manually or left at default. These options can be changed
   later.

   For example through the web interface of the UDM using the
   :guilabel:`Options` tab. If an option is activated, one or more LDAP object
   classes (given by parameter ``objectClass``) are added to the object and
   further fields and/or tabs are activated in the |UCSUMC| tabs (for example
   the groupware option for users). The dictionary assigns a unique string to
   each option (as :py:data:`property_descriptions
   <udm_modules_globals.property_descriptions>`).

   Each instance has the following parameters:

   .. py:data:: options.short_description

      A short description of the option, used for example in the |UCSUMC| as
      descriptive text about the input fields.

   .. py:data:: options.long_description

      A longer description of the option.

   .. py:data:: options.default

      defines whether the option is enabled by default:
      ``True`` means active and
      ``False`` inactive.

   .. py:data:: options.editable

      Defines whether this option can be set and removed multiple times, or
      always remains set after having been activated once.

   .. py:data:: options.objectClasses

      A list of LDAP object classes, which the LDAP entry must consist of so
      that the option is enabled for the object.

   Example:

   .. code-block:: python

      options = {
          'opt1': univention.admin.option(
              short_description=_('short description'),
              default=True,
              objectClasses=['class1'],
          ),
      }

.. py:data:: property_descriptions

   This Python dictionary contains all UDM properties provided by the module.
   They are referenced using a unique string as a key (in this case as
   :py:class:`univention.admin.property` objects). Usually, this kind of UDM
   property corresponds to an LDAP attribute, but can also be obtained or
   calculated from other sources.

   Example:

   .. code-block:: python

      property_descriptions = {
          'prop1': univention.admin.property(
              short_description=_('name'),
              long_description=_('long description'),
              syntax=univention.admin.syntax.string,
              multivalue=False,
              required=True,
              may_change=True,
              identifies=False,
              dontsearch=True,
              default=('default value'),
              options=['opt1'],
          ),
      }

   A short explanation of the parameters seen above:

   .. py:data:: property_descriptions.short_description
      :type: str

      A short description used for instance in the |UCSUMC| as descriptive text
      to the input fields.

   .. py:data:: property_descriptions.long_description
      :type: str

      A detailed description used in the |UCSUMC| for the tooltips.

   .. py:data:: property_descriptions.syntax
      :type: type

      This parameter specifies the property type. Based on these type
      definitions, the |UCSUDM| can check the specified values for the property
      and provide a detailed error message in case of invalid values. A list of
      syntax classes is available in :ref:`udm-syntax-ldap`.

   .. py:data:: property_descriptions.multivalue
      :type: bool

      Accepts the values ``True`` or ``False``. If set to ``True`` the
      properties value is a list. In this case, the syntax parameter specifies
      the type of elements within this list.

   .. py:data:: property_descriptions.required
      :type: bool

      If this parameter is set to ``True``, a value must be specified for this
      property.

   .. py:data:: property_descriptions.may_change
      :type: bool

      If set to ``True``, the properties value can be modified at a later point,
      if not, it can only be specified once when the object is created.

   .. py:data:: property_descriptions.editable
      :type: bool

      If set to ``False``, the properties value can't even be specified when the
      object is created. This is usually only interesting or useful for
      automatically generated or calculated values.

   .. py:data:: property_descriptions.identifies
      :type: bool

      This option should be set to ``True`` if the property uniquely identifies
      the object (through the LDAP DN). In most cases it should be set for exactly
      one property of a module.

   .. py:data:: property_descriptions.dontsearch
      :type: bool

      If set to ``False``, the property is not searchable.

   .. py:data:: property_descriptions.default
      :type: Any

      The default value of a property, when the object is created through the
      |UCSUMC|.

   .. py:data:: property_descriptions.options
      :type: List[str]

      A list of keywords identifying options with which this property can be
      shown or hidden.

.. py:data:: layout

   The UDM properties of an object can be arranged in groups. They are
   represented as tabs in the |UCSUDM| for example. For each tab, an instance of
   ``univention.admin.layout#Tab`` must be created in the array ``layout``. The
   name, a description for the tab and a list of rows are expected as
   parameters. A line can contain up to two properties, for each of which an
   instance of ``univention.admin.layout#Group`` must be created. The UDM
   property name from :py:data:`property_descriptions
   <udm_modules_globals.property_descriptions>` is expected as a parameter for
   each instance.

   .. code-block:: python

      from univention.admin.layout import Tab, Group
      layout = [
          Tab(_('Tab header'), _('Tab description'), layout=[
              Group('Group', 'group description', [
                  ['prop1', 'prop2']
                  ['prop3', ]
              ]),
              ...
          ], advanced=True),
          ...
      ]

   The optional ``advanced=True`` setting controls whether the tab should be
   displayed on the :guilabel:`Advanced settings` by default.

.. py:data:: mapping

   Maps the UDM properties to LDAP attributes. Usually, a mapping is registered
   for each property, linking the name of a UDM property (``udm_name``) to the
   associated LDAP attribute (``ldap_name``):

   .. code-block:: python

      mapping.register(udm_name, ldap_name)
      mapping.register(udm_name, ldap_name, map_value, unmap_value)

   Two functions are available to convert the values between UDM properties and
   LDAP attribute. To convert from UDM → LDAP, :py:func:`map_value` is used,
   while :py:func:`unmap_value` is used to convert in the opposite direction
   (LDAP → UDM). The second function is necessary for all single-valued UDM
   properties, since these are always implemented as null or one-element lists
   within LDAP. The default implementation
   :py:func:`univention.admin.mapping.ListToString` always returns the first
   entry of the list and can therefore generally be specified as a
   :py:func:`unmap_value` function for all single-valued attributes. For
   :py:func:`map_value` (UDM → LDAP), it is sufficient to specify ``None``,
   which ensures that any existing value, if present, is converted to a
   single-element list.

   .. warning::

      UDM properties always contain either a string (single-valued
      attributes) or a list of strings (multi-valued attributes), never
      just a number or any other Python type!

.. _udm-modules-globals-optional:

Optional arguments
~~~~~~~~~~~~~~~~~~

The following specifications are optional and only need to be defined if
a module has these special properties:

.. py:data:: virtual

   Modules that set this variable to ``True`` are a kind of helper module for
   other modules that have no associated LDAP objects. An example of this is the
   ``computers/computer`` module, which is an auxiliary module for all types of
   computers.

.. py:data:: template

   A module that sets this variable to another UDM module (e.g.
   ``settings/usertemplate``), gains the ability to define default values for
   UDM properties from other modules. An example of this is the user template
   (more specifically the ``settings/usertemplate`` module). Such a template can
   for example be selected when creating a user so that the values defined in it
   are taken over as defaults in the input masks.

.. _udm-modules-class:

The Python class ``object``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python class ``object`` of a module provides the interface between
|UCSUDM| and the LDAP operations triggered when an object is created,
modified, moved or deleted. It supports the |UCSUDM| in mapping the UDM
module and its properties to LDAP objects and attributes.

This requires adhering to the predefined API of the class. The base
class ``univention.admin.handlers.simpleLdap`` provides the essential
functionality for simple LDAP objects, so usually only a few adjustments
are necessary. An instance (``self``) encapsulates all information of an
object, which can be accessed in various ways:

.. py:class:: object

``self.dn`` → String
   Distinguished Name in the LDAP DIT

``self.position`` → ``univention.admin.uldap#Position``
   Container element in the LDAP DIT

``self['UDM-property-name']`` → [values, ...]
   Wrapper around ``self.info`` which also checks the value against the syntax
   when assigned and returns default values when read.

``self.info['UDM-property-name']`` → [values, ...]
   Dictionary with the currently set values of the UDM properties. Direct access
   to it allows the initialization of ``editable=False`` properties and skips
   any syntax checks.

``self.oldinfo['UDM-property-name']`` → [values, ...]
   Dictionary of the originally read values converted to UDM property names. It
   is primarily needed to internally propagate changes to the Python object back
   to the corresponding entry in the LDAP.

``self.oldattr['LDAP-Attributname']`` → [values, ...]
   Dictionary of the attributes originally read from LDAP.

``self.oldpolicies`` → [``Policy-DNs``, ...]
   Copy of the list of DNs of the referenced ``univentionPolicyReference``

``self.policies`` → [``Policy-DNs``, ...]
   List of DNs of the referenced ``univentionPolicyReference``

``self.policyObjects[Policy-DN]`` → ``univention.admin.handlers#SimplePolicy``
   Dictionary of the loaded policies.

``self.extended_udm_attributes`` → [``univention.admin#Extended_attribute``, ...]
   Complete list of the objects ``extended attributes``

The :py:class:`simpleLdap` class also provides the possibility of additional
customization before and after the LDAP operation by calling functions. For
example, before creating an LDAP object the function
:py:func:`_ldap_pre_create()` is called and after the operation the function
:py:func:`_ldap_post_create()` is called. Such pre- and post-functions similarly
exist for the :py:func:`modify`, :py:func:`move` and :py:func:`remove`
functions. The following table lists all used functions in calling order from
top to bottom:

.. table:: LDAP actions and hooks
   :widths: 6 2 2 2
   :name: ldap-actions-hooks
   :class: border grid

   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   | Description                                                                                         | Create                             | Modify                           | Remove                           |
   +=====================================================================================================+====================================+==================================+==================================+
   | Before validation                                                                                   | :py:func:`_ldap_pre_ready`         |                                  |                                  |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   | Validates, that all required attributes are set                                                     | :py:func:`ready`                                                      |                                  |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   |                                                                                                     | :py:func:`_ldap_pre_create`        | :py:func:`_ldap_pre_modify`      | :py:func:`_ldap_pre_remove`      |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   | Policy Copy-on-Write                                                                                | :py:func:`_update_policies`        | :py:func:`_update_policies`      |                                  |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   | Extension point for Extended Attribute                                                              | :py:func:`hook_ldap_pre_create()`  | :py:func:`hook_ldap_pre_modify`  | :py:func:`hook_ldap_pre_remove`  |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   | Returns initial list of (LDAP-attribute-name, value)- resp. (LDAP-attribute-name, [values]) tuples  | :py:func:`_ldap_addlist`           |                                  |                                  |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   | Calculates difference between ``self.oldinfo`` and ``self.info``                                    | :py:func:`_ldap_modlist`                                              |                                  |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   | Extension point for Extended Attribute                                                              | :py:func:`hook_ldap_addlist`       | :py:func:`hook_ldap_modlist`     |                                  |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   | Real action                                                                                         | ADD                                | MODIFY                           | DELETE                           |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   |                                                                                                     | :py:func:`_ldap_post_create`       | :py:func:`_ldap_post_modify`     | :py:func:`_ldap_post_remove`     |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+
   | Extension point for Extended Attribute                                                              | :py:func:`hook_ldap_post_create`   | :py:func:`hook_ldap_post_modify` | :py:func:`hook_ldap_post_remove` |
   +-----------------------------------------------------------------------------------------------------+------------------------------------+----------------------------------+----------------------------------+

The functions ``hook_ldap_*`` are described in :ref:`udm-hook`.

.. _udm-modules-functions:

The :py:func:`identify` and :py:func:`lookup` functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These functions are used to find the corresponding objects for search queries
from the |UCSUMC| (:py:func:`lookup`) and to assign LDAP objects to a |UCSUDM|
module. For simple LDAP objects, no modifications are necessary. They can be
assigned to the ``generic objects`` class methods:

.. code-block:: python

   lookup = object.lookup
   lookup_filter = object.lookup_filter
   identify = object.identify

.. _udm-modules-example:

Example module
--------------

The following is an example module for the |UCSUDM| which is also available as a
package. (:program:`univention-directory-manager-module-example`) The complete
source code is available at
:uv:src:`packaging/univention-directory-manager-module-example/`.

The directory contains a source package in Debian format, from which two binary
packages are created during package build through :command:`./debian/rules
binary`: A schema package, which must be installed on the |UCSPRIMARYDN|, and
the package containing the UDM module itself. The sample code also includes a
:command:`ip-phone-tool` script that shows an example of using the UDM Python
API in a Python script.

A |UCSUDM| module almost always consists of two components:

* The Python module, which contains the implementation of the interface to the
  |UCSUDM|.

* A LDAP schema, which defines the LDAP object to be managed. Both parts are
  described below, with the focus lying on the creation of the Python module.

The following module for the |UCSUDM| demonstrates the rudimentary
administration of IP telephones. It tries to show as many possibilities of a
|UCSUDM| module as possible within a simple example.

.. _udm-modules-example-python:

Python code of the example module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before defining the actual module source code, some basic Python modules
need to be imported, which are always necessary:

.. code-block:: python

   import re

   import univention.admin.handlers
   import univention.admin.syntax
   import univention.admin.localization
   from univention.admin.layout import Tab

This list of Python modules can of course be extended. As described in
:ref:`udm-modules-globals`, some necessary global
variables are defined at the beginning of a |UCSUDM| module, which provide
a description of the module:

.. code-block:: python

   module = 'test/ip_phone'
   childs = False
   short_description = _('IP-Phone')
   long_description = _('An example module for the Univention Directory Manager')
   operations = ['add', 'edit', 'remove', 'search', 'move', 'copy']

Another global variable important for the |UCSUMC|, is
:py:data:`layout <udm_modules_globals.layout>`.

.. code-block:: python

   layout = [
       Tab(_('General'), _('Basic Settings'), layout=[
           ["name", "active"],
           ["ip", "protocol"],
           ["priuser"],
       ]),
       Tab(_('Advanced'), _('Advanced Settings'), layout=[
           ["users"],
       ], advanced=True),
       Tab(_('Redirect'), _('Redirect Option'), layout=[
           ["redirect_user"],
       ], advanced=True),
   ]

It structures the layout of the objects individual properties on the tabs. The
list consists of elements whose type is :py:class:`univention.admin.layout.Tab`,
each determining the content of a tab. In this case there are the ``General``,
``Advanced`` and ``Redirect`` tabs. Next, the options (:py:data:`options
<udm_modules_globals.options>`) and properties (:py:data:`property_descriptions
<udm_modules_globals.property_descriptions>`) of the module should be defined.
In this case, the ``default`` and ``redirection`` options are created, whose
functions will be explained later. To configure the parameters, the
:py:class:`univention.admin.option` object is passed to the
``short_description`` option for a short description. ``default`` defines the
preconfiguration. ``True`` activates the option while ``False`` deactivates it.

.. code-block:: python

   options = {
       'default': univention.admin.option(
           short_description=short_description,
           default=True,
           objectClasses=['top', 'testPhone'],
       ),
       'redirection': univention.admin.option(
           short_description=_('Call redirect option'),
           default=True,
           editable=True,
           objectClasses=['testPhoneCallRedirect'],
       ),
   }

After the modules options, its properties are defined. UDM properties are
defined through textual descriptions, syntax definitions and instructions for
the |UCSUMC|.

.. code-block:: python

   property_descriptions = {
       ...
   }

The ``name`` property defines the ``hostname`` of the IP phone. The ``syntax``
parameter tells the |UCSUDM| that valid values for this property must match the
syntax of a computer name. Additional predefined syntax definitions can be found
in the :py:data:`property_descriptions
<udm_modules_globals.property_descriptions>` section.

.. code-block:: python

   'name': univention.admin.property(
       short_description=_('Name'),
       long_description=_('ID of the IP-phone'),
       syntax=univention.admin.syntax.hostName,
       required=True,
       identifies=True,
   ),

The ``active`` is an example of a boolean/binary property which can only take
the values ``True`` or ``False``. In this example, it defines an
activation/blocking of the IP phone. The parameter ``default=True`` initially
unlocks the phone:

.. code-block:: python

   'active': univention.admin.property(
       short_description=_('active'),
       long_description=_('The IP-phone can be deactivated'),
       syntax=univention.admin.syntax.TrueFalseUp,
       default='TRUE',
   ),

The ``protocol`` property specifies which VoIP protocol is supported by the
phone. No standard syntax definition is used for this property, but a specially
declared ``SynVoIP_Protocols`` class. (The source code of this class follows in
a later section). The syntax of the class defines a selection list with a
predefined set of possibilities. The ``default`` parameter preselects the value
with the ``sip`` key.

.. code-block:: python

   'protocol': univention.admin.property(
       short_description=_('Protocol'),
       long_description=_('Supported VoIP protocols'),
       syntax=SynVoIP_Protocols
       default='sip',
   ),

The ``ip`` property specifies the phones IP address. The predefined class
:py:class:`univention.admin.syntax.ipAddress` is specified as the syntax
definition. Additionally, the ``required`` parameter enforces that setting this
property is mandatory.

.. code-block:: python

   'ip': univention.admin.property(
       short_description=_('IP-Address'),
       long_description=_('IP-Address of the IP-phone'),
       syntax=univention.admin.syntax.ipAddress,
       required=True,
   ),

The ``priuser`` property sets the primary user of the IP phone. A separate
syntax definition is again used, which in this case is a class that defines the
valid values by means of a regular expression. (The source code is shown later)

.. code-block:: python

   'priuser': univention.admin.property(
       short_description=_('Primary User'),
       long_description=_('The primary user of this IP-phone'),
       syntax=SynVoIP_Address,
       required=True,
   ),

The ``users`` property indicates that options are used. Since ``multivalue`` is
set to ``True`` in this example, the ``users`` object is a list of addresses.

.. code-block:: python

   'users': univention.admin.property(
       short_description=_('Additional Users'),
       long_description=_('Users, that may register with this phone'),
       syntax=SynVoIP_Address,
       multivalue=True,
   ),

The ``redirect_user`` property is used to redirect incoming calls to a different
phone number. It is only shown if the ``options=['redirection']`` is set.

.. code-block:: python

   'redirect_user': univention.admin.property(
       short_description=_('Redirection User'),
       long_description=_('Address for call redirection'),
       syntax=SynVoIP_Address,
       options=['redirection'],
   ),

The following two classes are the syntax definitions used for the ``protocols``,
``priuser`` and ``users`` properties. ``SynVoIP_Protocols`` is based on the
predefined ``univention.admin.syntax.select`` class, which provides the basic
functionality for select lists. Derived classes, as seen in the following class,
only need to define a name and the list of choices.

.. code-block:: python

   class SynVoIP_Protocols(univention.admin.syntax.select):
       name = _('VoIP_Protocol')
       choices = [('sip', _('SIP')), ('h323', _('H.323')), ('skype', _('Skype'))]

The other syntax definition (``SynVoIP_Address``) is based on the
:py:class:`univention.admin.syntax.simple` class, which provides basic
functionality for syntax definitions utilizing regular expressions. As with the
other definition, a name must be assigned. Additionally, the attributes
``min_length`` and ``max_length`` must be specified. If one of these attributes
is set to ``0``, it corresponds to a nonexistent limit in the respective
direction. In addition to the attributes mentioned, the :py:func:`parse`
function must also be defined, which passes the value to be checked as a
parameter. By means of the Python module :program:`re` it is in this case
checked whether the value corresponds to the pattern of a VoIP address, e.g.
``sip:hans@mustermann.de``.

.. code-block:: python

   class SynVoIP_Address(univention.admin.syntax.simple):
       name = _('VoIP_Address')
       min_length = 4
       max_length = 256
       _re = re.compile('((^(sip|h323|skype):)?([a-zA-Z])[a-zA-Z0-9._-]+)@[a-zA-Z0-9._-]+$')

       def parse(self, text):
           if self._re.match(text) is not None:
               return text
           raise univention.admin.uexceptions.valueError(_('Not a valid VoIP Address'))

Mapping the UDM module properties to the Attributes of the to be created LDAP
object is the next step. (:py:data:`mapping <udm_modules_globals.mapping>`). To
do this, the :py:class:`univention.admin.mapping.mapping` class is used, which
provides a simple way to register mappings for the individual LDAP attributes to
UDM properties with the :py:func:`register` function. This function's first
argument is the modules UDM property name and the second the LDAP attribute
name. The following two arguments of the :py:func:`register` function can be
used to specify mapping functions for conversion from the modules UDM property
to the LDAP attribute and vice versa.

.. code-block:: python

   mapping = univention.admin.mapping.mapping()
   mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
   mapping.register('active', 'testPhoneActive', None, univention.admin.mapping.ListToString)
   mapping.register('protocol', 'testPhoneProtocol', None, univention.admin.mapping.ListToString)
   mapping.register('ip', 'testPhoneIP', None, univention.admin.mapping.ListToString)
   mapping.register('priuser', 'testPhonePrimaryUser', None, univention.admin.mapping.ListToString)
   mapping.register('users', 'testPhoneUsers')
   mapping.register('redirect_user', 'testPhoneRedirectUser', None, univention.admin.mapping.ListToString)

Finally, :ref:`udm-modules-class` must be defined for the module that conforms
to the specifications defined in :ref:`udm-modules-structure`. For the IP phone,
the class would look like this:

.. code-block:: python

   class object(univention.admin.handlers.simpleLdap):

       module = module

       def open(self):
           super(object, self).open()
           self.save()

       def _ldap_pre_create(self):
           return super(object, self)._ldap_pre_create()

       def _ldap_post_create(self):
           return super(object, self)._ldap_post_create()

       def _ldap_pre_modify(self):
           return super(object, self)._ldap_pre_modify()

       def _ldap_post_modify(self):
           return super(object, self)._ldap_post_modify()

       def _ldap_pre_remove(self):
           return super(object, self)._ldap_pre_remove()

       def _ldap_post_remove(self):
           return super(object, self)._ldap_post_remove()

       def _ldap_modlist(self):
           ml = super(object, self)._ldap_modlist()
           return ml

To enable searching for objects managed by this module, two additional functions
are available: :py:func:`lookup` and :py:func:`identify`
(see :ref:`udm-modules-functions`). The functions provided here should be sufficient
for simple LDAP objects that can be identified by a single ``objectClass``.

.. code-block:: python

   lookup = object.lookup
   lookup_filter = object.lookup_filter
   identify = object.identify

.. _udm-modules-example-ldap:

LDAP schema extension for the example module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before the developed module can be used within the |UCSUDM|, the new
object class, in this case ``testPhone``, must be made known to the LDAP
server together with its attributes. Such object definitions are defined
via so-called schemas in LDAP. They are specified in files looking like
the following:

.. code-block::

   attributetype ( 1.3.6.1.4.1.10176.9999.1.1 NAME 'testPhoneActive'
       DESC 'state of the IP phone'
       EQUALITY caseIgnoreIA5Match
       SYNTAX 1.3.6.1.4.1.1466.115.121.1.26 SINGLE-VALUE )

   attributetype ( 1.3.6.1.4.1.10176.9999.1.2 NAME 'testPhoneProtocol'
       DESC 'The supported VoIP protocol'
       EQUALITY caseExactIA5Match
       SYNTAX 1.3.6.1.4.1.1466.115.121.1.26 SINGLE-VALUE )

   attributetype ( 1.3.6.1.4.1.10176.9999.1.3 NAME 'testPhoneIP'
       DESC 'The IP address of the phone'
       EQUALITY caseExactIA5Match
       SYNTAX 1.3.6.1.4.1.1466.115.121.1.26 SINGLE-VALUE )

   attributetype ( 1.3.6.1.4.1.10176.9999.1.4 NAME 'testPhonePrimaryUser'
       DESC 'The primary user of the phone'
       EQUALITY caseIgnoreIA5Match
       SYNTAX 1.3.6.1.4.1.1466.115.121.1.26 SINGLE-VALUE )

   attributetype ( 1.3.6.1.4.1.10176.9999.1.5 NAME 'testPhoneUsers'
       DESC 'A list of other users allowed to use the phone'
       EQUALITY caseIgnoreIA5Match
       SYNTAX 1.3.6.1.4.1.1466.115.121.1.26 )

   objectclass ( 1.3.6.1.4.1.10176.9999.2.1 NAME 'testPhone'
       DESC 'IP Phone'
       SUP top  STRUCTURAL
       MUST ( cn $ testPhoneActive $ testPhoneProtocol $ testPhoneIP $ testPhonePrimaryUser )
       MAY ( testPhoneUsers )
       )

Detailed documentation on creating LDAP schema files can be found on the
`OpenLDAP project website <openldap_>`_ and is not the focus of this
documentation.

.. _udm-modules-example-installation:

Installing the module
~~~~~~~~~~~~~~~~~~~~~

The last step is to install the Python module and LDAP schema,
documented in the following.

The Python module must be copied to the
:file:`/usr/lib/python2.7/dist-packages/univention/admin/handlers/` and
:file:`/usr/lib/python3/dist-packages/univention/admin/handlers/` directory for
the |UCSUDM| to find it. In this directory a subdirectory has to be created
corresponding to the first part of the module name. For example, if the module
name is ``test/ip-phone``, the directory should be named :file:`test/`. The
Python module must then be copied to this directory. Ideally, a UDM module is
integrated into a separate Debian package.

Documentation for this can be found in the :ref:`pkg-introduction` section. The
newly created package will now be included in the display when
:command:`univention-directory-manager modules` is called.

In principle, the file containing the LDAP schema can be copied to any
directory. Univention schema definitions, for example, are stored in the
:file:`/usr/share/univention-ldap/schema/` directory. For the LDAP server to
find this schema, it must be included in the :file:`/etc/ldap/slapd.conf`
configuration file. Since this file is under the control of the Univention
Configuration Registry, do not edit the file directly, but create a Univention
Configuration Registry template. (see :ref:`ucr-conffiles`)

.. _udm-modules-examples-download:

Downloading the sample code
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The latest version of the sample code can be found at
:uv:src:`packaging/univention-directory-manager-module-example/`.

It contains a source package in Debian format from which two binary packages are
created during package building through ``./debian/rules binary``: A schema
package that needs to be installed on the master and the package containing the
UDM module itself. The sample code also includes a script
:command:`ip-phone-tool`, which exemplifies the use of the UDM Python API in a
Python script.
