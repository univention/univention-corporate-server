.. _domain-saml:

SAML identity provider
======================

SAML (Security Assertion Markup Language) is an XML-based standard for
exchanging authentication information in order to allow single sign-on across
domain boundaries. UCS provides a fail-safe SAML identity provider on a
|UCSPRIMARYDN| as well as |UCSBACKUPDN|. The SAML identity provider is
registered at an external service with a cryptographic certificate and
establishes a trust relationship. The user then only needs to authenticate
himself against UCS and can use the service without renewed authentication.

.. _domain-saml-saml-login:

.. figure:: /images/sso_login.*
   :alt: The single sign-on login page

   The single sign-on login page

The SAML 2.0 compatible UCS identity provider is provided by the integration of
:program:`simplesamlphp`.

The UCS identity provider is tightly integrated into the UCS domain.
Clients that will be used to access the UCS identity provider have to be
able to resolve DNS records in the UCS domain. The domain DNS Servers
should therefore be configured on all clients in order to be able to
resolve the central DNS record, which by default is
:samp:`ucs-sso.{[Domain name]}`.

The UCS identity provider is automatically installed on |UCSPRIMARYDN| and
|UCSBACKUPDN|\ s. Further |UCSBACKUPDN|\ s can be made available in the domain
to increase fail-safe safety. The default DNS record :samp:`ucs-sso.{[Domain name]}`
is registered to increase fail-safe access to the UCS identity provider. The
SSL certificate for this record is kept on all participating systems in the
domain. It is advised to install the UCS domain root certificate on all clients
that are using *single sign-on*.

It is possible to associate the SAML authentication with the Kerberos
login. This means that users with a valid Kerberos ticket, for example
after logging on to Windows or Linux, can sign in to the identity
provider without having to manual re-authenticate.

To allow Kerberos authentication at the identity provider, the |UCSUCRV|
:envvar:`saml/idp/authsource` has to be changed from ``univention-ldap`` to
``univention-negotiate``. The web browsers must be configured to transfer the
Kerberos ticket to the SAML Identity Provider. Here are two examples for the
configuration of Firefox and Internet Explorer / Microsoft Edge:

Mozilla Firefox
   In the extended Firefox configuration, which can be reached by entering
   ``about:config`` in the Firefox address line, the address of the identity
   provider must be entered in the option
   ``network.negotiate-auth.trusted-uris``, which is :samp:`ucs-sso.{[Domain name]}`
   by default.

Microsoft Internet Explorer; Microsoft Edge
   In the Control Panel, the :guilabel:`Internet Options` must be opened,
   followed by :menuselection:`Security --> Local Intranet --> Sites -->
   Advanced`. The address of the identity provider has to be added, which is
   :samp:`ucs-sso.{[Domain name]}` by default.

The Kerberos authentication can be restricted to certain IP subnets by setting
the |UCSUCRV| :envvar:`saml/idp/negotiate/filter-subnets` for example to
``127.0.0.0/16,192.168.0.0/16``. This is especially useful to prevent a pop up
login box being shown for clients which are not part of the UCS domain.

.. _domain-saml-sso-login:

Login via single sign-on
------------------------

The activation of *single sign-on* for the portal is described in
:ref:`central-management-umc-login`. For this, :samp:`ucs-sso.{[Domain name]}`
must be reachable. To login the domain credentials must be provided. For the
login directly at the UCS system (i.e., without *single sign-on*), follow the
link :guilabel:`Login without Single Sign On`.

The design of the login dialog can be changed by editing
:file:`/usr/share/univention-management-console-login/css/custom.css`. This file
will never be altered or deleted during updates.

Other web services will redirect to the UCS identity provider login page in a
similar fashion in order to carry out a *single sign-on*. After authenticating,
the user will be forwarded back to the web service itself. These services need
to be registered as described in :ref:`domain-saml-additional-serviceprovider`.

The *single sign-on* for a particular service can be initiated from the UCS
identity provider, as well. This saves an extra visit at the external web
service which redirects to the authentication site. To do so, a link to the UCS
identity provider page needs to be provided in the form of
:samp:`https://ucs-sso.{[Domain name]}/simplesamlphp/saml2/idp/SSOService.php?spentityid={[Service provider
identifier]}`.

.. _domain-saml-additional-serviceprovider:

Adding a new external service provider
--------------------------------------

The UMC module :guilabel:`SAML identity provider` allows to manage all service
providers that are registered at the UCS identity provider. Users have to be
activated for a service provider, to be able to authenticate for it at the UCS
identity provider. The service provider can be activated for groups, to allow
authentication with that service provider for all users within that group. On
the user's *Account* tab or the group's *General* tab, the
service provider can to be added under *SAML settings*.

To register the UCS identity provider at an external service provider,
the public part of the SAML certificate is required by the service
provider. The certificate can be downloaded via a link in the UMC
module. Some service providers may require the UCS identity provider XML
metadata as a file upload. By default the XML file can be downloaded
from the URL
:samp:`https://ucs-sso.{[Domain name]}/simplesamlphp/saml2/idp/metadata.php`.

The following attributes can be configured when adding a new service provider.

.. list-table:: General options when configuring a service provider
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - Service provider activation status
     - If activated, the configuration for the service provider is activated and
       is ready for authentication.

   * - Service provider identifier
     - Defines the internal name of the service provider. The name is later
       selected at user objects, when giving them access to a service provider.
       The identifier cannot be changed later.

   * - Respond to this service provider URL after login
     - After successful authentication, the user’s browser is redirected to the
       service provider. The redirection is done to this provided URL.

   * - Single logout URL for service provider
     - Service providers can offer a URL endpoint at which the session at the
       service provider can be terminated. If a user logs out at the UCS
       identity provider, the browser will get redirected to the provided URL to
       terminate the session.

   * - Format of ``NameID`` attribute
     - The value ``NameIDFormat`` that the service provider
       receives. The service provider’s documentation should contain information
       about possible values. Example: ``urn:oasis:names:tc:SAML:2.0:nameid-format:transient`` or
       ``urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified``.

   * - Name of the attribute that is used as ``NameID``
     - The LDAP attribute that is used to uniquely identify the user is provided
       here, e.g., ``uid``.

   * - Name of the organization for service provider
     - The value provided here will be shown on the UCS single sign-on login
       page. It helps the user to identify for which service they enter
       credentials.

   * - Description of this service provider
     - The value provided here will be shown on the UCS single sign-on login
       page. A longer description about the service provider can be given here.
       The description will be shown on the login page in a separate paragraph.

.. list-table:: Advanced settings when configuring a service provider
   :header-rows: 1
   :widths: 3 9

   * - Attribute
     - Description

   * - URL to the service provider’s privacy policy
     - If a URL is entered here, the UCS identity provider login page will
       contain a link to this URL.

   * - Allow transmission of LDAP attributes to the service provider
     - By default, the UCS identity provider transmits only the ``NameID``
       attribute entered on the *General* page to the service provider. If
       additional LDAP user attributes are required by the service provider,
       this checkbox can be activated. The attributes that should be transmitted
       have to be entered in the *List of LDAP attributes to transmit*.

   * - Value for ``attribute format`` field
     - In case the transmitted attributes need to be sent in a particular format
       value, this format can be entered here. Example: ``urn:oasis:names
       :tc:SAML:2.0:nameid-format:transient`` or
       ``urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified``.

   * - List of LDAP attributes to transmit
     - Every LDAP attribute that should be transmitted to the service provider
       can be entered here. Additionally, one or more service attribute names
       can be added to each LDAP attribute in the field next to it. These
       service attribute names have the purpose to translate the LDAP Attribute
       names for the service provider. Multiple service attribute names have to
       be separated by commas. In order for the UCS identity provider to process
       these attributes, they need to be registered additionally via the LDAP
       object :samp:`id=default-saml-idp,cn=univention,{[LDAP base DN]}`. LDAP
       attributes entered at the object can be read and transferred by the
       Identity Provider.

.. _domain-saml-extended-configuration:

Extended Configuration
----------------------

Some environments may require the UCS Identity Provider to provide multiple
logical Identity Provider instances. Logical separation is achieved by offering
different URIs as Identity Provider endpoints.

The default endpoint is :samp:`https://ucs-sso.{[Domain
name]}/simplesamlphp/saml2/idp/metadata.php`. Further entries can be created by
setting |UCSUCRV|\ s in the form
:envvar:`saml/idp/entityID/supplement/[identifier]` to ``true`` on all servers
which serve the UCS Identity Provider. Typically that will be the |UCSPRIMARYDN|
and all |UCSBACKUPDN|\ s. The :program:`apache2` service must then be reloaded.

For example, to set up another entry under the URI :samp:`https://ucs-sso.{[Domain
name]}/simplesamlphp/{[secondIDP]}/saml2/idp/metadata.php``, the |UCSUCRV|
``saml/idp/entityID/supplement/secondIDP=true`` must be set.
