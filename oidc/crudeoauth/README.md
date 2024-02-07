# crudeoauth - A SASL plugin and PAM implementation of OAUTHBEARER

This is `crudeoauth`, a PAM and SASL plugin implementation of [RFC 7628](https://datatracker.ietf.org/doc/rfc7628/) OAUTHBEARER.

The artifacts can be used
* by user facing services:
    * to validate OAuth 2.0 access tokens using PAM
    * to perform SASL binds using the OAUTHBEARER mechanism, sending an OAuth 2.0 access token
* by protected resources:
    * to accept SASL binds using the OUTHBEARER mechanism and validate OAuth 2.0 access tokens.

In [UCS](https://www.univention.com/products/ucs/) the user facing service could be the Univention Management Console and
the protected resource could be the OpenLDAP slapd.

Configuration of the SASL plugin is done via a sasl.conf file (e.g. `/etc/ldap/sasl2/slapd.conf` in UCS/Debian).
Configuration of the PAM is done via parameters of the library call in the PAM stack.

The implementation has been tested with Keycloak 23.0.x.
The PAM and SASL plugin check the `aud` claim as requested by
[RFC 9068](https://datatracker.ietf.org/doc/html/rfc9068).
Keycloak 23 currently doesn't automatically put `aud` into the token.

The PAM and SASL plugin can additionally check the `azp` claim if
configured accordingly.

## User notes

The repository also holds Debian maintainer files in the `debian/` folder, which
can be used to build the binary packages `libpam-oauthbearer` and `libsasl2-modules-oauthbearer`.

The SASL plugin is suitable to be used the openldap server via the
`/etc/ldap/sasl2/slapd.conf` configuration file.
It provides configuration options like:
```
mech_list: … OAUTHBEARER
oauthbearer_grace: 3
oauthbearer_userid: preferred_username
oauthbearer_trusted_jwks0: /usr/share/oidc/file_containing_the_authorization_server_certificates_as.jwks
oauthbearer_trusted_iss0: https://sso.example.org/realms/master
oauthbearer_trusted_aud0: ldaps://example.org/
oauthbearer_trusted_azp0: https:/client.example.org/oidc/
oauthbearer_required_scope0: openid
```
The `azp` check (last line) is optional and may provide additional security.

The username is read from the access token and used as `authcid`.
A optional `authzid` might be provided, and is used if the LDAP server allows it.

After successfull SASL bind e.g. to OpenLDAP slapd
the user arrives with a bind DN that is specific to the SASL bind mechanism.
In OpenLDAP it can be mapped to some DN in a DIT by putting
a `authz-regexp` statement to the `slapd.conf` as usual:
```
authz-regexp
    uid=([^,]*),cn=oauthbearer,cn=auth
    ldap:///dc=example,dc=org??sub?uid=$1
```

The PAM library `pam_oauthbearer.so` is provided by the package `libpam-oauthbearer`,
doing the same validations and having equivalent configuration options via the PAM stack definition.
```
auth sufficient pam_oauthbearer.so grace=3 userid=preferred_username \
    iss=https://sso.example.org/realms/master \
    jwks=/usr/share/oidc/file_containing_the_authorization_server_certificates_as.jwks \
    trusted_aud=ldaps://example.org/ trusted_azp=https:/client.example.org/oidc/ \
    required_scope=openid
```

## Developer notes

The code is currently maintained [here](https://github.com/univention/univention-corporate-server/tree/5.0-6/oidc/crudeoauth) in the [Univention Corporate Server](https://www.univention.com/products/ucs/) (UCS) product mono repository.

The code uses the [rhonabwy](https://babelouest.github.io/rhonabwy/) library
for handling of JWT and JWKS structures.

The project name `crudeoauth` has been chosen as tribute to the project [crudesaml](https://github.com/univention/crudesaml),
which provided a blueprint for creating a combined PAM and SASL plugin.
