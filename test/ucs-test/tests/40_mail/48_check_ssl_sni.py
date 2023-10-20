#!/usr/share/ucs-test/runner python3
## desc: Check if SNI can be configured for dovecot with one additional host/cert
## exposure: dangerous
## roles: [domaincontroller_master, domaincontroller_backup]
## packages: [univention-mail-dovecot]
## bugs: [48485]
import socket
import ssl
import subprocess

import univention.config_registry
import univention.testing.ucr as ucr_test
from univention.testing import utils


def get_certificate_from_ssl_connection(fqdn, servername, port):
    context = ssl.create_default_context()
    context.check_hostname = False
    conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=servername)
    conn.connect((fqdn, port))
    return conn.getpeercert()


def check_if_correct_cert_is_served(fqdn, servername, port, must_fail=False):
    cert = get_certificate_from_ssl_connection(fqdn, servername, port)
    if not cert:
        utils.fail(f'Empty certificate from {fqdn}:{port} with servername {servername}')

    try:
        ssl.match_hostname(cert, servername)
    except ssl.CertificateError as e:
        if must_fail:
            print(f'\nOK: Server was not configurd to deliver certificate for {(servername)}, the ssl.match_hostname() failed as expected\n')
        else:
            utils.fail(f'Incorrect certificate returned: Requested certificate from {fqdn}:{port} for servername {servername}, error: {e}')


if __name__ == '__main__':
    # setup SNI certificate with another certificate
    with ucr_test.UCSTestConfigRegistry() as ucr:
        hostname = ucr.get('hostname')
        domain = ucr.get('domainname')
        fqdn = f"{hostname}.{domain}"

        check_if_correct_cert_is_served(fqdn, f'ucs-sso.{domain}', 993, must_fail=True)

        univention.config_registry.handler_set([
            'mail/dovecot/ssl/sni/ucs-sso.%(domain)s/certificate=/etc/univention/ssl/ucs-sso.%(domain)s/cert.pem' % {'domain': domain},
            'mail/dovecot/ssl/sni/ucs-sso.%(domain)s/key=/etc/univention/ssl/ucs-sso.%(domain)s/private.key' % {'domain': domain},
        ])
        subprocess.call(['service', 'dovecot', 'restart'])

        print(f'\nTest if host {fqdn} returns a certificate for {fqdn}')
        utils.retry_on_error((lambda: check_if_correct_cert_is_served(fqdn, fqdn, 993)), exceptions=(Exception, ), retry_count=5)
        check_if_correct_cert_is_served(fqdn, fqdn, 995)
        print(f'Test if host {fqdn} returns a certificate for ucs-sso.{domain}')
        check_if_correct_cert_is_served(fqdn, f'ucs-sso.{domain}', 993)
        check_if_correct_cert_is_served(fqdn, f'ucs-sso.{domain}', 995)

        ucr.revert_to_original_registry()
        subprocess.call(['service', 'dovecot', 'restart'])
