.. _settings-udm-module:

Package UDM extension modules
=============================

.. index::
   single: directory manager; extension modules packaging

For some purposes, for example for app installation, it is convenient to be able
to deploy a new UDM module in the UCS domain from any system in the domain. For
this purpose, a UDM module can be stored as a special type of UDM object. The
module responsible for this type of objects is called ``settings/udm_module``.
As these objects are replicated throughout the UCS domain, the UCS servers
listen for modifications on these objects and integrate them into the local UDM.

The commands to create the UDM module objects in UDM may be put into any join
script (see :ref:`chap-join`). Like every UDM object a UDM module object can be
created by using the UDM command line interface
:command:`univention-directory-manager` or its alias :command:`udm`. UDM module
objects can be stored anywhere in the LDAP directory, but the recommended
location would be ``cn=udm_module,cn=univention,`` below the LDAP base. Since
the join script creating the attribute may be called on multiple hosts, it is a
good idea to add the ``--ignore_exists`` option, which suppresses the error exit
code in case the object already exists in LDAP.

The module ``settings/udm_module`` requires several parameters. Since many of
these are determined automatically by the :command:`ucs_registerLDAPExtension`
shell library function, it is recommended to use the shell library function to
create these objects (see :ref:`join-libraries-shell`).

``name`` (required)
   Name of the UDM module, e.g. ``newapp/someobject``.

``data`` (required)
   The actual UDM module data in bzip2 and base64 encoded format.

``filename`` (required)
   The filename the UDM module data should be written to by the
   listening servers. The filename may contain path elements and should
   conform to the name of the UDM module (e.g.
   ``newapp/someobject.py``).

``messagecatalog`` (optional)
   Multivalued property to supply message translation files (syntax:
   ``<language tag> <base64 encoded GNU message catalog>``).

``umcregistration`` (optional)
   XML definition required to make the UDM module available though the
   Univention Management Console (base64 encoded XML)

``icon`` (optional)
   Multivalued property to supply icons for the Univention Management
   Console (base64 encoded :file:`png`, :file:`jpeg` or :file:`svgz`).

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
   Minimal required UCS version. The UDM module is only activated by systems
   with a version higher than or equal to this.

``ucsversionend`` (optional)
   Maximal required UCS version. The UDM module is only activated by systems
   with a version lower than or equal to this. To specify validity for the whole
   5.0-x release range a value like ``5.0-99`` may be used.

``active`` (internal)
   A boolean flag used internally by the |UCSPRIMARYDN| to signal availability
   of the new UDM module on the |UCSPRIMARYDN| (default: ``FALSE``).

