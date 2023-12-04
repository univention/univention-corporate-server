#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Test SSO with supplement entityID
## tags: [saml]
## join: true
## exposure: dangerous
## roles: [domaincontroller_master, domaincontroller_backup]
## tags:
##  - skip_admember

import subprocess

import pytest
import requests

import samltest


@pytest.mark.skip(reason="not implemented in keycloak, see https://git.knut.univention.de/univention/components/keycloak-app/-/issues/182")
def test_sso_with_supplement_entity_id(ucr, saml_session):
    supplement = 'second_eID'
    try:
        with samltest.GuaranteedIdP('127.0.0.1'):
            umc_saml_idpserver = ucr.get('umc/saml/idp-server')
            ucr.handler_set([f'saml/idp/entityID/supplement/{supplement}=true', 'kerberos/defaults/rdns=false', 'saml/idp/authsource=univention-negotiate'])

            subprocess.call(['kdestroy'])
            subprocess.check_call(['kinit', '--password-file=/etc/machine.secret', ucr['hostname'] + '$'])  # get kerberos ticket

            subprocess.check_call(['systemctl', 'restart', 'apache2.service'])
            saml_root = 'https://{}/simplesamlphp/{}/'.format(ucr.get('ucs/server/sso/fqdn'), supplement)
            supplement_entityID = f'{saml_root}saml2/idp/metadata.php'
            print(f'supplement_entityID: "{supplement_entityID}"')
            ucr.handler_set([f'umc/saml/idp-server={supplement_entityID}'])
            metadata_req = requests.get(supplement_entityID)
            metadata_req.raise_for_status()
            assert f'entityID="{supplement_entityID}"' in metadata_req.text

            saml_session.login_with_new_session_at_IdP()
            saml_session.test_logged_in_status()
            saml_session.logout_at_IdP()
            saml_session.test_logout_at_IdP()
            saml_session.test_logout()
    finally:
        subprocess.call(['kdestroy'])
        subprocess.check_call(['systemctl', 'reload', 'apache2.service'])
        if umc_saml_idpserver:
            subprocess.check_call(['ucr', 'set', f'umc/saml/idp-server={umc_saml_idpserver}'])
