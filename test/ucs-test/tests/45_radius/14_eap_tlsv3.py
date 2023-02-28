#!/usr/share/ucs-test/runner pytest-3
## desc: check if client with PEAP is working
## tags: [apptest, radius]
## bugs: [55247]
## packages:
##   - univention-radius
## join: true
## exposure: dangerous
import subprocess
from tempfile import NamedTemporaryFile


UNIVENTION_CACERT = "/etc/univention/ssl/ucsCA/CAcert.pem"
DEFAULT_CACERT = "/etc/default/cacert"


def get_wpa_config(username, password, ca_cert):
    if ca_cert == "":
        comment = "#"
    else:
        comment = ""
    wpa_config = '''
network={{
    ssid="DoesNotMatterForThisTest"
    key_mgmt=WPA-EAP
    eap=PEAP
    identity="{username}"
    password="{password}"
    {comment}ca_cert="{ca_cert}"
    eapol_flags=3
    phase1="tls_disable_tlsv1_3=0"
}}
    '''.format(username=username, password=password, comment=comment, ca_cert=ca_cert)
    return wpa_config


def test_eap(udm):
    password = 'univention'
    username = udm.create_user(networkAccess=1)[1]
    ca_cert = UNIVENTION_CACERT
    with NamedTemporaryFile() as tmp_file:
        wpa_config = get_wpa_config(username, password, ca_cert)
        tmp_file.write(wpa_config.encode("UTF-8"))
        tmp_file.seek(0)
        print("wpa_config:")
        print(tmp_file.read().decode("UTF-8"))
        subprocess.check_call([
            'eapol_test',
            '-c',
            tmp_file.name,
            '-a',
            '127.0.0.1',
            '-p',
            '1812',
            '-s',
            'testing123',
            '-r0',
        ])
