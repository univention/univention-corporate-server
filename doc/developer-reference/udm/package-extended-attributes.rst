.. _udm-ea:

Package extended attributes
===========================

.. index::
   single: extended attributes
   see: custom attributes; extended attributes
   single: directory manager; extended attributes

Each UDM module provides a set of mappings from LDAP attributes to properties.
This set is not complete, because LDAP objects can be extended with additional
*auxiliary objectClasses*. *Extended Attributes* can be used to extend modules
to show additional properties. These properties can be mapped to any already
defined LDAP attribute, but objects can also be extended by adding additional
auxiliary object classes, which can provide new attributes.

For packing purpose any additional LDAP schema needs to be registered on the
|UCSPRIMARYDN|, which is replicated from there to all other domain controllers
through the Listener/Notifier mechanism (see :ref:`chap-listener`). This is best
done trough a separate schema package, which should be installed on the
|UCSPRIMARYDN| and |UCSBACKUPDN|. Since *Extended Attributes* are declared in
LDAP, the commands to create them can be put into any join script (see
:ref:`chap-join`). To be convenient, the declaration should be also included
with the schema package, since installing it there does not require the
Administrator to provide additional LDAP credentials.

An *Extended Attribute* is created by using the UDM command line interface
:command:`univention-directory-manager` or its alias :command:`udm`. The module
is called ``settings/extended_attribute``. *Extended Attributes* can be stored
anywhere in the LDAP, but the default location would be ``cn=custom
attributes,cn=univention,`` below the LDAP base. Since the join script creating
the attribute may be called on multiple hosts, it is a good idea to add the
``--ignore_exists`` option, which suppresses the error exit code in case the
object already exists in LDAP.

The module ``settings/extended_attribute`` requires many parameters. They are
described in :ref:`central-extended-attrs` in :cite:t:`ucs-manual`.

``name`` (required)
   Name of the attribute.

``CLIName`` (required)
   An alternative name for the command line version of UDM.

``shortDescription`` (required)
   Default short description.

``translationShortDescription`` (optional, multiple)
   Translation of short description.

``longDescription`` (required)
   Default long description.

``translationLongDescription`` (optional, multiple)
   Translation of long description.

``objectClass`` (required)
   The name of an LDAP object class which is added to store this
   property.

``deleteObjectClass`` (optional)
   Remove the object class when the property is unset.

   .. PMH: this does only work for syntax=boolean or something like that

``ldapMapping`` (required)
   The name of the LDAP attribute the property matches to.

``syntax`` (optional)
   A syntax class, which also controls the visual representation in UDM.
   Defaults to ``string``.

``default`` (optional)
   The default value is used when a new UDM object is created.

   .. PMH: check next It is also used when for an object if the option is
      enabled, which only then activates the property.

``valueRequired`` (optional)
   A value must be entered for the property.

``multivalue`` (optional)
   Controls if only a single value or multiple values can be entered.
   This must be in sync with the ``SINGLE-VALUE``
   setting of the attribute in the LDAP schema.

``mayChange`` (optional)
   The property may be modified later.

``notEditable`` (optional)
   Disable all modification of the property, even when the object is
   first created. The property is only modified through hooks.

``copyable`` (optional)
   Copy the value of the property when the entry is cloned.

   .. PMH: check next. Otherwise, the value is reset to the default value.

``hook`` (optional)
   The name of a Python class implementing hook functions. See :ref:`udm-hook`
   for more information.

``doNotSearch`` (optional)
   If this is enabled, the property is not show in the drop-down list of
   properties when searching for UDM objects.

``tabName`` (optional)
   The name of the tab in the UMC where the property should be
   displayed. The name of existing tabs can be copied from UMC session
   with the ``English`` locale. A new tab is
   automatically created for new names.

   .. PMH: check next If no name is given, ???

``translationTabName`` (optional, multiple)
   Translation of tab name.

``tabPosition`` (optional)
   This setting is only relevant, when a new tab is created by using a
   ``tabName``, for which no tab exists. The integer
   value defines the position where the newly tab is inserted. By
   default the newly created tab is appended at the end, but before the
   *Extended settings* tab.

``overwriteTab`` (optional)
   If enabled, the tab declared by the UDM module with the name from the
   ``tabName`` settings is replaces by a new clean tab
   with only the properties defined by *Extended Attributes*.

``tabAdvanced`` (optional)
   If this setting is enabled, the tab is created inside the
   *Extended settings* tab instead of being a tab
   by its own.

``groupName`` (optional)
   The name of the group inside a tab where the property should be
   displayed. The name of existing groups can be copied from UMC session
   with the ``English`` locale. A new tab is
   automatically created for new names. If no name is given, the
   property is placed before the first tab.

``translationGroupName`` (optional, multiple)
   Translation of group name.

``groupPosition`` (optional)
   This setting is only relevant, when a new group is created by using a
   ``groupName``, for which no group exists. The
   integer value defines the position where the newly group is inserted.
   By default the newly created group is appended at the end.

``overwritePosition`` (optional)
   The name of an existing property this property wants to overwrite.

   .. PMH: In UCS-2.x this was the position number, in UCS-3.x it must be the
      name

``disableUDMWeb`` (optional)
   Disables showing this property in the UMC.

``fullWidth`` (optional)
   The widget for the property should span both columns.

``module`` (required, multiple)
   A list of module names where this *Extended Attribute* should be added
   to.

``options`` (required, multiple)
   A list of options, which enable this *Extended Attribute*.

``version`` (required)
   The version of the *Extended Attribute* format. The current version is
   ``2``.

.. tip::

   Create the *Extended Attribute* first through UMC-UDM. Modify it until
   you're satisfied. Only then dump it using :command:`udm
   settings/extended_attribute list` and convert the output to
   an equivalent shell script creating it.

The following example provides a simple LDAP schema called
:file:`extended-attribute.schema`, which declares one object class
``univentionExamplesUdmOC`` and one attribute
``univentionExamplesUdmAttribute``.

.. code-block::
   :caption: *Extended Attribute* for custom LDAP schema
   :name: udm-ea-with-schema

   #objectIdentifier univention 1.3.6.1.4.1.10176
   #objectIdentifier univentionCustomers univention:99999
   #objectIdentifier univentionExamples univentionCustomers:0
   objectIdentifier univentionExamples 1.3.6.1.4.1.10176:99999:0
   objectIdentifier univentionExmaplesUdm univentionExamples:1
   objectIdentifier univentionExmaplesUdmAttributeType univentionExmaplesUdm:1
   objectIdentifier univentionExmaplesUdmObjectClass univentionExmaplesUdm:2

   attributetype ( univentionExmaplesUdmAttributeType:1
   	NAME 'univentionExamplesUdmAttribute'
   	DESC 'An example attribute for UDM'
   	EQUALITY caseIgnoreMatch
   	SUBSTR caseIgnoreSubstringsMatch
   	SYNTAX 1.3.6.1.4.1.1466.115.121.1.15{42}
   	SINGLE-VALUE
   	)

   objectClass ( univentionExmaplesUdmObjectClass:1
   	NAME 'univentionExamplesUdmOC'
   	DESC 'An example object class for UDM'
   	SUP top
   	AUXILIARY
   	MUST ( univentionExamplesUdmAttribute )
   	)


The schema is shipped as
:file:`/usr/share/extended-attribute/extended-attribute.schema` and installed by
calling :command:`ucs_registerLDAPExtension` from the join-script
:file:`50extended-attribute.inst`.

.. code-block:: bash

   #!/bin/bash

   ## joinscript api: bindpwdfile

   VERSION=1
   . /usr/share/univention-join/joinscripthelper.lib
   . /usr/share/univention-lib/ldap.sh
   joinscript_init

   # register LDAP schema for new extended attribute
   ucs_registerLDAPExtension "$@" \
       --schema /usr/share/extended-attribute/extended-attribute.schema

   # Register new service entry for this host
   eval "$(ucr shell)"
   udm settings/extended_attribute create "$@" --ignore_exists \
       --position "cn=custom attributes,cn=univention,$ldap_base" \
       --set name="My Attribute" \
       --set CLIName="myAttribute" \
       --set shortDescription="Example attribute" \
       --append translationShortDescription='"de_DE" "Beispielattribut"' \
       --append translationShortDescription='"fr_FR" "Exemple d’attribut"' \
       --set longDescription="An example attribute" \
       --append translationLongDescription='"de_DE" "Ein Beispielattribut"' \
       --append translationLongDescription='"fr_FR" "Un exemple d’attribut"' \
       --set tabAdvanced=1 \
       --set tabName="Examples" \
       --append translationTabName='"de_DE" "Beispiele"' \
       --append translationTabName='"fr_FR" "Exemples"' \
       --set tabPosition=1 \
       --set module="groups/group" \
       --set module="computers/memberserver" \
       --set syntax=string \
       --set default="Lorem ipsum" \
       --set multivalue=0 \
       --set valueRequired=0 \
       --set mayChange=1 \
       --set doNotSearch=1 \
       --set objectClass=univentionExamplesUdmOC \
       --set ldapMapping=univentionExamplesUdmAttribute \
       --set deleteObjectClass=0
       # --set overwritePosition=
       # --set overwriteTab=
       # --set hook=
       # --set options=

   # Terminate UDM server to force module reload
   . /usr/share/univention-lib/base.sh
   stop_udm_cli_server

   joinscript_save_current_version
   exit 0

This example is deliberately missing an unjoin-script (see :ref:`join-unjoin`)
to keep this example simple. It should check if the *Extended Attribute* is no
longer used in the domain and then remove it.

.. _udm-ea-select:

Selection lists
---------------

.. index::
   single: extended attributes; selection list

Sometimes an *Extended Attribute* should show a list of options to choose from.
This list can either be static or dynamic. After defining such a new syntax it
can be used by referencing its name in the ``syntax`` property of an *Extended
Attribute*.

.. _udm-ea-select-static:

Static selections
~~~~~~~~~~~~~~~~~

The static list of available selections is defined once and can not be modified
interactively through UMC. Such a list is best implemented though a custom
syntax class. As the implementation must be available on all system roles, the
new syntax is best registered in LDAP. This can be done by using
:ref:`ucs_registerLDAPExtension <join-ucs-register-ldap-extension>` which is
described in :ref:`join-libraries-shell`.

As an alternative the file can be put into the directories
:file:`/usr/lib/python2.7/dist-packages/univention/admin/syntax.d/` and
:file:`/usr/lib/python3/dist-packages/univention/admin/syntax.d/`.

The following example is comparable to the default example in file
:file:`/usr/lib/python3/dist-packages/univention/admin/syntax.d/example.py`:

.. code-block:: python

   class StaticSelection(select):
       choices = [
           ('value1', 'Description for selection 1'),
           ('value2', 'Description for selection 2'),
           ('value3', 'Description for selection 3'),
       ]


.. _udm-ea-select-dynamic:

Dynamic selections
~~~~~~~~~~~~~~~~~~

A dynamic list is implemented as an LDAP search, which is described in
:ref:`udm-syntax-ldap`. For performance reason it is recommended to implement a
class derived from :py:class:`UDM_Attribute` or :py:class:`UDM_Objects` instead of using
:py:class:`LDAP_Search`. The file
:file:`/usr/lib/python3/dist-packages/univention/admin/syntax.py` contains
several examples.

The idea is to create a container with sub-entries for each selection. This
following listing declares a new syntax class for selecting a profession level.

.. code-block:: python
   :caption: Dynamic selection list for *Extended Attributes*
   :name: udm-ea-select-dynamic-example

   class DynamicSelection(UDM_Objects):
       udm_modules = ('container/cn',)
       udm_filter = '(&(objectClass=organizationalRole)(ou:dn:=DynamicSelection))'
       simple = True  # only one value is selected
       empty_value = True  # allow selecting nothing
       key = '%(name)s'  # this is stored
       label = '%(description)s'  # this is displayed
       regex = None  # no validation in frontend
       error_message = 'Invalid value'


The Python code should be put into a file named :file:`DynamicSelection.py`. The
following code registers this new syntax in LDAP and adds some values. It also
creates an *Extended Attribute* for user objects using this syntax.

.. code-block:: console

   $ syntax='DynamicSelection'
   $ base="cn=univention,$(ucr get ldap/base)"

   $udm container/ou create \
   > --position "$base" \
   > --set name="$syntax" \
   > --set description='UCS profession level'
   > dn="ou=$syntax,$base"

   $ udm container/cn create \
   > --position "$dn" \
   > --set name="value1" \
   > --set description='UCS Guru (> 5)'

   $ udm container/cn create \
   > --position "$dn" \
   > --set name="value2"
   > --set description='UCS Regular (1..5)'

   $ udm container/cn create \
   > --position "$dn" \
   > --set name="value3" \
   > --set description='UCS Beginner (< 1)'

   $ udm container/cn create \
   > --ignore_exists \
   > --position "$base" \
   > --set name='udm_syntax'
   > dn="cn=udm_syntax,$base"

   $ udm settings/udm_syntax create \
   > --position "$dn" \
   > --set name="$syntax" \
   > --set filename="DynamicSelection.py" \
   > --set data="$(bzip2 <DynamicSelection.py | base64)" \
   > --set package="$syntax" --set packageversion="1"

   $ udm settings/extended_attribute create \
   > --position "cn=custom attributes,$base" \
   > --set name='Profession' \
   > --set module='users/user' \
   > --set tabName='General' \
   > --set translationTabName='"de_DE" "Allgemein"' \
   > --set groupName='Personal information' \
   > --set translationGroupName='"de_DE" "Persönliche Informationen"' \
   > --set shortDescription='UCS profession level' \
   > --set translationShortDescription='"de_DE" "UCS Erfahrung"' \
   > --set longDescription='Select a level of UCS experience' \
   > --set translationLongDescription='"de_DE" "Wählen Sie den Level der Erfahrung mit UCS"' \
   > --set objectClass='univentionFreeAttributes' \
   > --set ldapMapping='univentionFreeAttribute1' \
   > --set syntax="$syntax" --set mayChange=1 --set valueRequired=0


.. _udm-ea-issues:

Known issues
------------

* The ``tabName`` and ``groupName`` values must exactly match the values already
  used in the modules. If they do not match, a new tab or group is added. This
  also applies to the translation: They must match the already translated
  strings and must be repeated for every *Extended Attribute* again and again. The
  untranslated strings are best extracted directly from the Python source code
  of the modules in
  :file:`/usr/lib/python3/dist-packages/univention/admin/handlers/*/*.py`. For
  the translated strings run :command:`msgunfmt
  /usr/share/locale/$language-code/LC_MESSAGES/univention-admin*.mo`.

* The ``overwritePosition`` values must exactly match the name of an already
  defined property. Otherwise UDM will crash.

* *Extended Attributes* may be removed, when matching data is still stored in
  LDAP. The schema on the other hand must only be removed when all matching data
  is removed. Otherwise the server :command:`slapd` will fail to start.

* Removing ``objectClass``\ es from LDAP objects must be done manually. Currently
  UDM does not provide any functionality to remove unneeded object classes or
  methods to force-remove an object class including all attributes, for which
  the object class is required.

.. _udm-ea-option:

Extended options
----------------

.. index::
   single: extended attributes; options

.. PMH: Bug #21912

UDM properties can be enabled and disabled through options. For example, all
properties of a user related to Samba can be switched *on* or *off* to reduce the
settings shown to an administrator. If many *Extended Attributes* are added to a
UDM module, it might proof necessary to also create new options. Options are per
UDM module.

Similar to *Extended Attributes* an *Extended Option* is created by using the UDM
command line interface :command:`univention-directory-manager` or its alias
:command:`udm`. The module is called ``settings/extended_options``. *Extended
Options* can be stored anywhere in the LDAP, but the default location would be
``cn=custom attributes,cn=univention,`` below the LDAP base. Since the join
script creating the option may be called on multiple hosts, it is a good idea to
add the ``--ignore_exists`` option, which suppresses the error exit code in case
the object already exists in LDAP.

The module ``settings/extended_options`` has the following properties:

``name`` (required)
   Name of the option.

``shortDescription`` (required)
   Default short description.

``translationShortDescription`` (optional, multiple)
   Translation of short description.

``longDescription`` (required)
   Default long description.

``translationLongDescription`` (optional, multiple)
   Translation of long description.

``default`` (optional)
   Enable the option by default.

``editable`` (optional)
   Option may be repeatedly turned on and off.

``module`` (required, multiple)
   A list of module names where this *Extended Option* should be added to.

``objectClass`` (optional, multiple)
   A list of LDAP object classes, which when found, enable this option.

.. code-block:: console
   :caption: *Extended Option*
   :name: udm-eo

   $ eval "$(ucr shell)"
   $ udm settings/extended_options create "$@" --ignore_exists \
   > --position "cn=custom attributes,cn=univention,$ldap_base" \
   > --set name="My Option" \
   > --set shortDescription="Example option" \
   > --set translationShortDescription='"de_DE" "Beispieloption"' \
   > --set longDescription="An example option" \
   > --set translationLongDescription='"de_DE" "Eine Beispieloption"' \
   > --set default=0 \
   > --set editable=0 \
   > --set module="users/user" \
   > --set objectClass=univentionExamplesUdmOC


.. _udm-hook:

Extended attribute hooks
------------------------

.. index::
   single: extended attributes; hooks

.. PMH: Bug #25053

Hooks provide a mechanism to pre- and post-process the values of *Extended
Attributes*. Normally, UDM properties are stored as-is in LDAP attributes. Hooks
can modify the LDAP operations when an object is created, modified, deleted or
retrieved. They are implemented in Python and the file must be placed in the
directory :file:`/usr/lib/python2.7/dist-packages/univention/admin/hooks.d/` and
:file:`/usr/lib/python3/dist-packages/univention/admin/hooks.d/`. The filename
must end with :file:`.py`.

The module :py:mod:`univention.admin.hook` provides the class :py:class:`simpleHook`,
which implements all required hook functions. By default they don't modify any
request, but do log all calls. This class should be used as a base class for
inheritance.

.. py:module:: univention.admin.hook

.. py:class:: simpleHook

   .. py:method:: hook_open(obj)

      :param univention.admin.handlers.simpleLdap obj:

      :rtype: None

      This method is called by the default ``open()`` handler just before the
      current state of all properties is saved.

   .. py:method:: hook_ldap_pre_create(obj)

      :param univention.admin.handlers.simpleLdap obj:

      :rtype: None

      This method is called before a UDM object is created. It is called after
      the module validated all properties, but before the *add-list* is created.

   .. py:method:: hook_ldap_addlist(obj, al:AddList = [])

      :param univention.admin.handlers.simpleLdap obj:
      :param AddList al:

      :rtype: AddList

      This method is called before a UDM object is created. It gets passed
      a list of two-tuples ``(ldap-attribute-name,
      list-of-values)``, which will be used to create the LDAP
      object. The method must return the (modified) list. Notice that
      :py:meth:`hook_ldap_modlist` will also be called next.

   .. py:method:: hook_ldap_post_create(obj)

      :param univention.admin.handlers.simpleLdap obj:

      :rtype: None

      This method is called after the object was created in LDAP.

   .. py:method:: hook_ldap_pre_modify(obj)

      :param univention.admin.handlers.simpleLdap obj:

      :rtype: None

      This method is called before a UDM object is modified. It is called after
      the module validated all properties, but before the *modification-list* is
      created.

   .. py:method:: hook_ldap_modlist(obj, ml:ModList = [])

      :param univention.admin.handlers.simpleLdap obj:
      :param ModList ml:

      :rtype: ModList

      This method is called before a UDM object is created or modified. It gets
      passed a list of tuples, which are either two-tuples
      ``(ldap-attribute-name, list-of-new-values)`` or three-tuples
      ``(ldap-attribute-name, list-of-old-values, list-of-new-values)``. It will
      be used to create or modify the LDAP object. The method must return the
      (modified) list.

   .. py:method: hook_ldap_post_modify(obj)

      :param univention.admin.handlers.simpleLdap obj:

      :rtype: None

      This method is called after the object was modified in LDAP.

   .. py:method:: hook_ldap_pre_remove(obj)

      :param univention.admin.handlers.simpleLdap obj:

      :rtype: None

      This method is called before a UDM object is removed.

   .. py:method:: hook_ldap_post_remove(obj)

      :param univention.admin.handlers.simpleLdap obj:

      :rtype: None

      This method is called after the object was removed from LDAP.

The following example implements a hook, which removes the object-class
``univentionFreeAttributes``, if the property ``isSampleUser`` is no longer set.

.. code-block:: python

   from univention.admin.hook import simpleHook

   class RemoveObjClassUnused(simpleHook):
       type = 'RemoveObjClassUnused'

       def hook_ldap_post_modify(self, obj):
           """Remove unused objectClass."""
           ext_attr_name = 'isSampleUser'
           class_name = 'univentionFreeAttributes'

           if obj.oldinfo.get(ext_attr_name) in ('1',) and \
                   obj.info.get(ext_attr_name) in ('0', None):
               if class_name in obj.oldattr.get('objectClass', []):
                   obj.lo.modify(obj.dn,
                       [('objectClass', class_name, '')])


After installing the file, the hook can be activated by setting the ``hook``
property of an *Extended Attribute* to ``RemoveObjClassUnused``:

.. code-block:: console

   $ udm settings/extended_attribute modify \
   > --dn ... \
   > --set hook=RemoveObjClassUnused

