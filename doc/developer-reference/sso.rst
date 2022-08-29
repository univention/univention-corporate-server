.. _chap-sso:

*****************************************************
Single sign-on: Integrate a service provider into UCS
*****************************************************

.. index::
   single: single sign-on; SAML
   see: SSO; single sign-on

UCS provides *Single Sign-On* functionality with a SAML 2.0 compatible identity
provider based on :program:`simplesamlphp`. The identity provider is by default
installed on the |UCSPRIMARYDN| and all |UCSBACKUPDN| servers. A DNS Record for
all systems providing *single sign-on* services is registered for failover,
usually ``ucs-sso.domainname``. Clients are required to be able to resolve the
*single sign-on* DNS name.

.. _sso-register:

Register new service provider through :command:`udm`
====================================================

New service providers can be registered by using the |UCSUDM| module
``saml/serviceprovider``. To create a service provider entry in a *joinscript*,
see the following example:

.. code-block:: console

   $ eval "$(ucr shell)"
   $ udm saml/serviceprovider create "$@" \
     --ignore_exists \
     --position "cn=saml-serviceprovider,cn=univention,$ldap_base" \
     --set isActivated=TRUE \
     --set Identifier="MyServiceProviderIdentifier" \
     --set NameIDFormat="urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified" \
     --set simplesamlAttributes="false" \
     --set AssertionConsumerService="https://$hostname.$domainname/sso-login-page" \
     --set simplesamlNameIDAttribute="uid" \
     --set privacypolicyURL="https://example.com/policy.html" \
     --set serviceProviderOrganizationName="My Service Name" \
     --set serviceproviderdescription="A long description shown to the user on the Single Sign-On page." || die

.. _sso-idpinfo:

Get information required by the service provider
================================================

The service provider usually requires at least a public certificate or XML
metadata about the identity provider. The certificate can for example be
downloaded with the following call:

.. code-block:: console

   $ eval "$(ucr shell)"
   $ wget --ca-certificate /etc/univention/ssl/ucsCA/CAcert.pem \
     -O /etc/idp.cert \
     https://"${ucs_server_sso_fqdn:-ucs-sso.$domainname}"/simplesamlphp/saml2/idp/certificate

The XML metadata is available for example from

.. code-block:: console

   $ eval "$(ucr shell)"
   $ wget --ca-certificate /etc/univention/ssl/ucsCA/CAcert.pem \
     -O /etc/idp.metadata \
     https://"${ucs_server_sso_fqdn:-ucs-sso.$domainname}"/simplesamlphp/saml2/idp/metadata.php

The *single sign-on* login page to be configured in the service provider is
:samp:`https://ucs-sso.{domainname}/simplesamlphp/saml2/idp/SSOService.php`.

.. _sso-addlink:

Add direct login link to the UCS Portal page
============================================

To provide users with a convenient link to an identity provider initiated login,
the following :command:`ucr` command may be used:

.. code-block:: console

   $ fqdn="ucs-sso.domainname"
   $ myspi="MyServiceProviderIdentifier"
   $ ucr set ucs/web/overview/entries/service/SP/description="External Service Login" \
     ucs/web/overview/entries/service/SP/label="External Service SSO" \
     ucs/web/overview/entries/service/SP/link="https://$fqdn/simplesamlphp/saml2/idp/SSOService.php?spentityid=$myspi" \
     ucs/web/overview/entries/service/SP/description/de="Externer Dienst Login" \
     ucs/web/overview/entries/service/SP/label/de="Externer Dienst SSO" \
     ucs/web/overview/entries/service/SP/priority=50

where ``MyServiceProviderIdentifier`` is the identifier used when creating the
UDM service provider object.
