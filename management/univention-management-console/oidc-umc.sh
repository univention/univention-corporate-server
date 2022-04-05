#!/bin/bash

touch /etc/umc-oidc.secret
chmod 0600 /etc/umc-oidc.secret
echo -en 'us8Upr7BQ9i2EjRUxjnkkNh1m3aAdl53' > /etc/umc-oidc.secret

wget https://keycloak.projekt21.ucs.intranet/realms/ucs/protocol/openid-connect/certs -O /usr/share/univention-management-console/oidc/https%3A%2F%2Fkeycloak.projekt21.ucs.intranet%2Frealms%2Fucs.jwks
ucr set umc/oidc/trusted/rp/projekt21.ucs.intranet=https://projekt21.ucs.intranet/univention/oidc/

ucr set \
	umc/oidc/default-op=default \
	umc/oidc/default/client-id=umc \
	umc/oidc/default/issuer=https://keycloak.projekt21.ucs.intranet/realms/ucs \
	umc/oidc/default/client-secret-file=/etc/umc-oidc.secret \
	umc/oidc/default/extra-parameter='kc_idp_hint'

systemctl restart slapd univention-management-console-server
# access https://projekt21.ucs.intranet/univention/oidc/?location=/univention/management/
