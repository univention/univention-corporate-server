# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -x
set -e

dovecot_server_setup () {
	univention-certificate new -name dovecot.ucs.test
	ucr set mail/dovecot/ssl/certificate=/etc/univention/ssl/dovecot.ucs.test/cert.pem
	ucr set mail/dovecot/ssl/key=/etc/univention/ssl/dovecot.ucs.test/private.key

	cat <<- EOF > /etc/dovecot/conf.d/99-test.conf
#hostname = dovecot.ucs.test
doveadm_password = secretpassword
doveadm_api_key = key
service doveadm {
   unix_listener doveadm-server {
      user = dovemail
   }
   inet_listener {
       port = 2425
   }
   inet_listener http {
       port = 8080
       ssl = yes # uncomment to enable https
   }
}

#auth_debug = yes
#auth_debug_passwords = yes
#auth_verbose_passwords = yes
EOF

	service dovecot restart
	service univention-firewall stop
}
