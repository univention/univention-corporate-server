.. _domain-oidc:

OpenID Connect Provider
=======================

.. highlight:: console

UCS offers the possibility to install a *OpenID Connect Provider*,
which allows external web services to delegate the user login via the *OpenID
Connect (OIDC)* protocol to the UCS Identity Management. The :program:`OpenID
Connect Provider` App can be installed via the App Center. The service is
provided by the software :program:`Kopano Konnect`.

The app can be installed on all system roles. When installing on a UCS system
with the role |UCSPRIMARYDN| or |UCSBACKUPDN| the :program:`OpenID Connect
Provider` is made available under the DNS entry for the single sign-on,
normally this is :samp:`ucs-sso.{Domain name}`.

If the app is installed on a different system role, the provider can be reached
directly via the hostname instead. It should be ensured that the app is
installed on all other servers that are reachable at the ``ucs-sso`` DNS CNAME.

Session synchronization between multiple installed OIDC Providers in a domain is
not preconfigured. When experiencing login issues with Apps, we recommend to
only install the OIDC Provider on one system, and restrict the ``ucs-sso`` DNS
CNAME to that system, or contact Univention Support.

External Web services can be connected to UCS via :program:`OpenID Connect` by
creating a specific object of type ``oidc/rpservice`` for this service in the
UCS directory service. These can be created via the UMC module :guilabel:`LDAP
directory` in the container ``cn=oidc``, which is located below the container
``cn=univention``. Here the new service can be registered via the item Add and
the selection *OpenID Connect Relying Party Service*.

The same is also possible from the command line:

.. code-block::

   $ udm oidc/rpservice create --set name=$UCS_internal_identifier \
     --position="cn=oidc,cn=univention,$(ucr get ldap/base)" \
     --set clientid=$ClientID \
     --set clientsecret=$a_long_password \
     --set trusted=yes \
     --set applicationtype=web \
     --set redirectURI=$URL_from_services_documentation

The command parameters are:

``name``
   the service name displayed in the web interface during login.

``clientid``
   must be identical here and in the connected service (*shared
   secret*).

``secret``
   must be identical here and in the connected service (*shared
   secret*).

``trusted``
   should be set to ``yes`` by default. Otherwise, the
   user will be prompted for confirmation to transfer their user
   attributes to the service.

``applicationtype``
   should be set to ``web`` for internet services.

``redirectURI``
   URL of the login endpoint, which can be found in the documentation of
   the connected service. If a service is accessible via several URLs or
   should it also be accessible via IP address, all possible addresses
   must be added to the ``redirectURI`` attribute. The field can
   therefore be defined multiple times, whereby each individual value
   must contain a valid URL.

The connected web service still needs information about the *OpenID
Connect* endpoints of the provider app for its configuration. If the provider
app is installed, this information can be found at the URL
:samp:`https://ucs-sso{[Domain name]}/.well-known/openid-configuration`. If the
provider app was installed on a system other than |UCSPRIMARYDN| or
|UCSBACKUPDN|, use the FQDN of the respective server instead of
:samp:`ucs-sso.{Domain name}` as described above.

When using *OpenID Connect*, resolvable DNS names and verifiable
certificates are a prerequisite. This is especially true for client computers of
end users who need to access both the DNS resolvable host names of the Web
service and the OpenID Connect Provider. In addition, the externally
connected Web services must be able to establish a connection to the
OpenID Connect Provider in order to be able to retrieve the user
attributes.

In the special case where the DNS name of the OIDC provider is to be changed,
the corresponding value must first be adjusted in the app settings of the
:program:`OpenID Connect Provider` app. Since there are diverse scenarios for
the availability of the provider after changing the DNS name, the web server
configuration cannot be changed automatically. For example, depending on the
configured DNS name, the UCS Apache configuration has to be adapted. The
configuration file
:file:`/etc/apache2/conf-available/openid-connect-provider.conf` must be made
available under the set DNS name in a virtual host.

With version 2 of the OIDC-Provider App the authentication to
OpenID Connect works via the SAML Identity Provider of the UCS
domain. If the SAML Identity Provider is not reachable at the default URL
:samp:`https://ucs-sso.{[Domain name]}`, the correct URL under which the SAML IdP
metadata for the UCS domain can be retrieved must be entered correctly in the
app settings. If this URL is configured incorrectly, the OpenID
Connect Provider will not start.

With SAML authentication, the authorization for the use of the OpenID
Connect Provider and thus for all apps connected via OIDC can be controlled via
SAML authorizations. By default, the group ``Domain Users`` is enabled for
access when the app is installed. If this permission should be removed, the
corresponding option must also be activated in the app settings so that the
permission is not automatically added again.

The OpenID Connect Provider logs actions
via the Docker Daemon. The output can be viewed with the command
:command:`univention-app logs openid-connect-provider`.
