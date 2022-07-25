.. _udm-syntax:

UDM syntax
==========

.. PMH: Bug #24236

Every UDM property has a syntax, which is used to check the value for
correctness. |UCSUCS| already provides several syntax types, which are defined
in the Python file
:file:`/usr/lib/python3/dist-packages/univention/admin/syntax.py`. The following
syntax list is not complete. For a complete overview, consult the file directly.

``string``; ``string64``; ``OneThirdString``; ``HalfString``; ``TwoThirdsString``; ``FourThirdsString``; ``OneAndAHalfString``; ``FiveThirdsString``; ``TextArea``
   Different string classes, which are mapped in |UCSUMC| to text input widgets
   with different widths and heights.

``string_numbers_letters_dots``; ``string_numbers_letters_dots_spaces``; ``IA5string``; ...
   Different string classes with restrictions on the allowed character set.

``Upload``; ``Base64Upload``; ``jpegPhoto``
   Binary data.

``integer``
   Positive integers.

``boolean``; ``booleanNone``; ``TrueFalse``; ``TrueFalseUpper``; ``TrueFalseUp``
   Different boolean types which map to ``yes`` and ``no`` or ``true`` and
   ``false``.

``hostName``; ``DNS_Name``; ``windowsHostName``; ``ipv4Address``; ``ipAddress``; ``hostOrIP``; ``v4netmask``; ``netmask``; ``IPv4_AddressRange``; ``IP_AddressRange``; ...
   Different classes for host names or addresses.

``unixTime``; ``TimeString``; ``iso8601Date``; ``date``
   Date and time.

``GroupDN``; ``UserDN``; ``UserID``; ``HostDN``; ``DomainController``; ``Windows_Server``; ``UCS_Server``; ...
   Dynamic classes, which do an LDAP search to provide a list of selectable
   values like users, groups and hosts.

``LDAP_Search``, ``UDM_Objects``, ``UDM_Attribute``
    These syntaxes do an LDAP search and display the result as a list. They are
    further described in :ref:`udm-syntax-ldap`.

Additional syntax classes can be added by placing a Python file in
:file:`/usr/lib/python2.7/dist-packages/univention/admin/syntax.d/` and
:file:`/usr/lib/python3/dist-packages/univention/admin/syntax.d/`. They're
automatically imported by UDM.

.. _udm-syntax-overwrite:

UDM syntax override
-------------------

.. index::
   single: directory manager; syntax override

Sometimes the predefined syntax is inappropriate in some scenarios. This can be
because of performance problems with LDAP searches or the need for more
restrictive or lenient value checking. The latter case might require a change to
the LDAP schema, since :command:`slapd` also checks the provided values for
correctness.

The syntax of UDM properties can be overwritten by using |UCSUCRV|\ s. For each
module and each property the variable
:samp:`directory/manager/web/modules/{module}/properties/{property}/syntax`
can be set to the name of a syntax class. For example
:samp:`directory/manager/web/modules/users/user/properties/username/syntax=uid`
would restrict the name of users to not contain umlauts.

Since UCR variables only affect the local system, the variables must be set on
all systems were UDM is used. This can be either done through a |UCSUCR| policy
or by setting the variable in the :file:`.postinst` script of some package,
which is installed on all hosts.

.. _udm-syntax-ldap:

UDM LDAP search
---------------

.. index::
   single: directory manager; LDAP search

It is often required to present a list of entries to the user, from which they
can select one or — in case of a multi-valued property — more entries. Several
syntax classes derived from ``select`` provide a fixed list of choices. If the
set of values is known and fixed, it's best to derive an own class from
``select`` and provide the Python file in
:file:`/usr/lib/python3/dist-packages/univention/admin/syntax.d/`.

If on the other hand the list is dynamic and is stored in LDAP, UDM provides
three methods to retrieve the values.

.. py:class:: UDM_Attribute

   This class does a UDM search. For each object found all values of a
   multi-valued property are returned.

   For a derived class the following class variables can be used to
   customize the search:

   .. py:attribute:: udm_module

      The name of the UDM module, which does the LDAP search and retrieves the
      properties.

   .. py:attribute:: udm_filter

      An LDAP search filter which is used by the UDM module to filter the
      search. The special value ``dn`` skips the search and directly returns the
      property of the UDM object specified by ``depends``.

   .. py:attribute:: attribute

      The name of a multi-valued UDM property which stores the values to be
      returned.

   .. py:attribute:: is_complex; key_index; label_index

      Some UDM properties consist of multiple parts, so called complex
      properties. These variables are used to define, which part is displayed as
      the label and which part is used to reference the entry.

   .. py:attribute:: label_format

      A Python format string, which is used to format the UDM properties to a
      label string presented to the user. :samp:`%({property-name})s` should
      be used to reference properties. The special property name ``$attribute$``
      is replaced by the value of variable ``attribute`` declared above.

   .. py:attribute:: regex

      This defines an optional regular expression, which is used in the front
      end to check the value for validity.

   .. py:attribute:: static_values

      A list of two-tuples ``(value, display-string)``, which are added as
      additional selection options.

   .. py:attribute:: empty_value

      If set to ``True``, the empty value is inserted before all other static
      and dynamic entries.

   .. py:attribute:: depends

      This variable may contain the name of another property, which this
      property depends on. This can be used to link two properties. For example,
      one property can be used to select a server, while the second dependent
      property then only lists the services provided by that selected host. For
      the dependent syntax ``attribute`` must be set to ``dn``.

   .. py:attribute:: error_message

      This error message is shown when the user enters a value which is not in
      the set of allowed values.

   The following example syntax would provide a list of all users with their
   telephone numbers:

   .. code-block:: python

      class DelegateTelephonedNumber(UDM_Attribute):
          udm_module = 'users/user'
          attribute = 'phone'
          label_format = '%(displayName)s: %($attribute$)s'


.. py:class:: UDM_Objects

   This class performs a UDM search returning each object found.

   For a derived class the following class variables can be used to customize
   the search:

   .. py:attribute:: udm_modules

      A List of one or more UDM modules, which do the LDAP search and retrieve
      the properties.

   .. py:attribute:: key

      A Python format string generating the key value used to identify the
      selected object. The default is ``dn``, which uses the distinguished name
      of the object.

   .. py:attribute:: label

      A Python format string generating the display label to represent the
      selected object. The default is ``None``, which uses the UDM specific
      ``description``. ``dn`` can be used to use the distinguished name.

   .. py:attribute:: regex

      This defines an optional regular expression, which is used in the front end
      to check the value for validity. By default only valid distinguished names
      are accepted.

   .. py:attribute:: simple

      By default a widget for selecting multiple entries is used. Setting this
      variable to ``True`` changes the widget to a combo-box widget, which only
      allows to select a single value. This should be in-sync with the
      ``multivalue`` property of UDM properties.

   .. py:attribute:: use_objects

      By default UDM opens each LDAP object through a UDM module implemented in
      Python. This can be a performance problem if many entries are returned.
      Setting this to ``False`` disables the Python code and directly uses the
      attributes returned by the LDAP search. Several properties can then no
      longer be used as key or label, as those are not explicitly stored in LDAP
      but are only calculated by the UDM module. For example, to get the fully
      qualified domain name of a host ``%(name)s.%(domain)s`` must be used
      instead of the calculated property ``%(fqdn)s``.

   .. py:attribute:: udm_filter; static_values; empty_value; depends; error_message

      Same as above with :py:class:`UDM_Attribute`.

   The following example syntax would provide a list of all servers providing a
   required service:

   .. code-block:: python

      class MyServers(UDM_Objects):
          udm_modules = (
              'computers/domaincontroller_master',
              'computers/domaincontroller_backup',
              'computers/domaincontroller_slave',
              'computers/memberserver',
              )
          label = '%(fqdn)s'
          udm_filter = 'service=MyService'


.. py:class:: LDAP_Search

   This is the old implementation, which should only be used, if
   :py:class:`UDM_Attribute` and :py:class:`UDM_Objects` are not sufficient. In
   addition to ease of use it has the drawback that |UCSUMC| can not do as much
   caching, which can lead to severe performance problems.

   LDAP search syntaxes can be declared in two equivalent ways:

   Python API
      By implementing a Python class derived from :py:class:`LDAP_Search` and
      providing that implementation in
      :file:`/usr/lib/python3/dist-packages/univention/admin/syntax.d/`.

   UDM API
      By creating a UDM object in LDAP using the module
      ``settings/syntax``.

.. py:class:: Python_API(LDAP_Search)

   The Python API uses the following variables:

   .. py:attribute:: syntax_name

      This variable stores the common name of the LDAP object, which is
      used to define the syntax. It is only used internally and should
      never be needed when creating syntaxes programmatically.

   .. py:attribute:: filter

      An LDAP filter to find the LDAP objects providing the list of
      choices.

   .. py:attribute:: attribute

      A list of UDM module property definitions like "``shares/share: dn``".
      They are used as the human readable label for each element of the choices.

   .. py:attribute:: value

      The UDM module attribute that will be stored to identify the selected
      element. The value is specified like ``shares/share: dn``

   .. py:attribute:: viewonly

      If set to ``True`` the values can not be changed.

   .. py:attribute:: addEmptyValue

      If set to ``True`` the empty value is add to the list of choices.

   .. py:attribute:: appendEmptyValue

      Same as ``addEmptyValue`` but added at the end. Used to automatically
      choose an existing entry in the front end.

   .. code-block:: python

      class MyServers(LDAP_Search):
          def __init__(self):
              LDAP_Search.__init__(self,
                  filter=('(&(univentionService=MyService)'
                      '(univentionServerRole=member))'),
                  attribute=(
                      'computers/memberserver: fqdn',
                      ),
                  value='computers/memberserver: dn'
              )
              self.name = 'LDAP_Search'  # required workaround

.. py:class:: LDAP_Search.UDM_API

   The UDM API uses the following properties:

   .. py:attribute:: name

      (required)

      The name for the syntax.

   .. py:attribute:: description

      (optional)

      Some descriptive text.

   .. py:attribute:: filter

      (required)

      An LDAP filter, which is used to find the objects.

   .. py:attribute:: base

      (optional)

      The LDAP base, where the search starts.

   .. py:attribute:: attribute

      (optional, multi-valued)

      The name of UDM properties, which are display as a label to the user.
      Alternatively LDAP attribute names may be used directly.

   .. py:attribute:: ldapattribute

      (optional, multi-valued)

      Description, see :py:attr:`attribute`.


   .. py:attribute:: value

      (optional);

      The name of the UDM property, which is used to reference the
      object. Alternatively an LDAP attribute name may be used directly.

   .. py:attribute:: ldapvalue

      (optional)

      Description, see :py:attr:`value`.


   .. py:attribute:: viewonly

      (optional)

      If set to ``True`` the values can not be changed.

   .. py:attribute:: addEmptyValue

      (optional)

      If set to ``True`` the empty value is add to the list of choices.

   .. code-block:: console

      $ eval "$(ucr shell)"
      $ udm settings/syntax create "$@" --ignore_exists \
      > --position "cn=custom attributes,cn=univention,$ldap_base" \
      > --set name="MyServers" \
      > --set filter='(&(univentionService=MyService)(univentionServerRole=member))' \
      > --set attribute='computers/memberserver: fqdn' \
      > --set value='computers/memberserver: dn'
