.. _chap-udm:
.. _udm-intro:

**************
|UCSUDM| (UDM)
**************

.. index::
   see:  |UCSUDM|; directory manager
   single: directory manager
   see: UDM; directory manager

.. PMH: Bug #31269

The |UCSUDM| (UDM) is a wrapper for LDAP objects. Traditionally, LDAP stores
objects as a collection of attributes, which are defines by so called schemata.
Modifying entries is slightly complicated, as there are no high-level operations
to add or remove values from multi-valued attributes, or to keep the password
used by different authentication schemes such as Windows NTLM-hashes, Unix MD5
hashes, or Kerberos tickets in sync.


The command line client :command:`udm` provides different
modes of operation.

:command:`udm` :samp:`[--binddn {bind-dn} --bindpwd {bind-password}] [{module}] [{mode}] [{options}]`

Creating object
   :command:`udm` :samp:`{module} create --set {property}={value} …`

   .. code-block:: console

      $ eval "$(ucr shell)"
      $ udm container/ou create --position "$ldap_base" --set name="xxx"


   Multiple ``--set``\ s may be used to set the values of a multi-valued property.

   The equivalent LDAP command would look like this:

   .. code-block:: console

      $ eval "$(ucr shell)"
      $ ldapadd -D "cn=admin,$ldap_base" -y /etc/ldap.secret <<__EOT__
      dn: uid=xxx,$ldap_base
      objectClass: organizationalRole
      cn: xxx
      __EOT__


List object
   :command:`udm` :samp:`{module} list [--dn {dn} | --filter {property}={value}]`

   .. code-block:: console

      $ udm container/ou list --filter name="xxx"


   .. code-block:: console

      $ univention-ldapsearch cn=xxx


Modify object
   :command:`udm` :samp:`{module} modify [--dn {dn} | --filter {property}={value}] [--set {property}={value} | --append {property}={value} | --remove {property}={value} …]`

   .. code-block:: console

      $ udm container/ou modify --dn "cn=xxx,$ldap_base" --set name="xxx"


   For multi-valued attributes ``--append`` and ``--remove`` can be used to add
   additional values or remove existing values. ``--set`` overwrites any
   previous value, but can also be used multiple times to specify further
   values. ``--set`` and ``--append`` should not be mixed for any property in
   one invocation.

Delete object
   :command:`udm` :samp:`{module} remove [--dn {dn} | --filter {property}={value}]`

   .. code-block:: console

      $ udm container/ou delete --dn "cn=xxx,$ldap_base"


   If ``--filter`` is used, it must match exactly one object. Otherwise
   :command:`udm` refuses to delete any object.


This chapter has the following content:

.. toctree::

   udm-modules
   syntax
   package-extended-attributes
   package-hooks
   package-extension-modules
   package-syntax-extension
   rest-api
   python3-migration
