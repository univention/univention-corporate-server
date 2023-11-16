#!/usr/share/ucs-test/runner python3
## desc: Check if SNI can be configured for dovecot with one additional host/cert
## exposure: dangerous
## roles: [domaincontroller_master, domaincontroller_backup]
## packages: [univention-mail-dovecot]
## bugs: [48485]

import socket
import ssl
import subprocess

import OpenSSL.SSL

import univention.config_registry
import univention.testing.ucr as ucr_test
from univention.testing import utils


def check_if_correct_cert_is_served(fqdn, servername, port, must_fail=False):
    context = ssl.create_default_context()
    context.check_hostname = True
    try:
        context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=servername).connect((fqdn, port))
    except ssl.CertificateError as exc:
        if exc.verify_code != OpenSSL.SSL._lib.X509_V_ERR_HOSTNAME_MISMATCH:
            raise
        if must_fail:
            print('\nOK: Server was not configurd to deliver certificate for %s, the SSLContext.check_hostname failed as expected\n' % (servername))
        else:
            utils.fail('Incorrect certificate returned: Requested certificate from %s:%s for servername %s, error: %s' % (fqdn, port, servername, exc))


if __name__ == '__main__':
    # setup SNI certificate with another certificate
    with ucr_test.UCSTestConfigRegistry() as ucr:
        hostname = ucr['hostname']
        domain = ucr['domainname']
        sso_domain = ucr['ucs/server/sso/fqdn']
        fqdn = "%s.%s" % (hostname, domain)

        check_if_correct_cert_is_served(fqdn, sso_domain, 993, must_fail=True)

        univention.config_registry.handler_set([
            'mail/dovecot/ssl/sni/%(sso_domain)s/certificate=/etc/univention/ssl/%(sso_domain)s/cert.pem' % {'sso_domain': sso_domain},
            'mail/dovecot/ssl/sni/%(sso_domain)s/key=/etc/univention/ssl/%(sso_domain)s/private.key' % {'sso_domain': sso_domain},
        ])
        subprocess.call(['service', 'dovecot', 'restart'])

        print('\nTest if host %s returns a certificate for %s' % (fqdn, fqdn))
        utils.retry_on_error((lambda: check_if_correct_cert_is_served(fqdn, fqdn, 993)), exceptions=(Exception, ), retry_count=5)
        check_if_correct_cert_is_served(fqdn, fqdn, 995)
        print('Test if host %s returns a certificate for %s' % (fqdn, sso_domain))
        check_if_correct_cert_is_served(fqdn, sso_domain, 993)
        check_if_correct_cert_is_served(fqdn, sso_domain, 995)

        ucr.revert_to_original_registry()
        subprocess.call(['service', 'dovecot', 'restart'])
