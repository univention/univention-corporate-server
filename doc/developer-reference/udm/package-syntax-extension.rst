.. _settings-udm-syntax:

Package UDM syntax extension
============================

.. index::
   single: directory manager; UDM syntax extension packaging

For some purposes, for example for app installation, it is convenient to be able
to deploy a new UDM syntax in the UCS domain from any system in the domain. For
this purpose, a UDM syntax can be stored as a special type of UDM object. The
module responsible for this type of objects is called ``settings/udm_syntax``.
As these objects are replicated throughout the UCS domain, the UCS servers
listen for modifications on these objects and integrate them into the local UDM.

The commands to create the UDM syntax objects in UDM may be put into any join
script (see :ref:`chap-join`). Like every UDM object a UDM syntax object can be
created by using the UDM command line interface
:command:`univention-directory-manager` or its alias :command:`udm`. UDM syntax
objects can be stored anywhere in the LDAP directory, but the recommended
location would be ``cn=udm_syntax,cn=univention,`` below the LDAP base. Since
the join script creating the attribute may be called on multiple hosts, it is a
good idea to add the ``--ignore_exists`` option, which suppresses the error exit
code in case the object already exists in LDAP.

The module ``settings/udm_syntax`` requires several parameters. Since many of
these are determined automatically by the :command:`ucs_registerLDAPExtension`
shell library function, it is recommended to use the shell library function to
create these objects (see :ref:`join-libraries-shell`).

``name`` (required)
   Name of the UDM syntax.

``data`` (required)
   The actual UDM syntax data in bzip2 and base64 encoded format.

``filename`` (required)
   The filename the UDM syntax data should be written to by the listening
   servers. The filename must not contain any path elements.

``package`` (required)
   Name of the Debian package which creates the object.

``packageversion`` (required)
   Version of the Debian package which creates the object. For object
   modifications the version number needs to increase unless the package name is
   modified as well.

``appidentifier`` (optional)
   The identifier of the app which creates the object. This is important to
   indicate that the object is required as long as the app is installed anywhere
   in the UCS domain. Defaults to ``string``.

``ucsversionstart`` (optional)
   Minimal required UCS version. The UDM syntax is only activated by systems
   with a version higher than or equal to this.

``ucsversionend`` (optional)
   Maximal required UCS version. The UDM syntax is only activated by systems
   with a version lower than or equal to this. To specify validity for the whole
   5.0-x release range a value like ``5.0-99`` may be used.

``active`` (internal)
   A boolean flag used internally by the |UCSPRIMARYDN| to signal availability
   of the new UDM syntax on the |UCSPRIMARYDN| (default: ``FALSE``).
