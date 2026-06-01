import contextlib
import subprocess
import time

from aiosmtpd.controller import Controller

import univention.testing.strings as uts
import univention.testing.udm as udm_test
from univention.testing import utils
from univention.testing.umc import Client


class SelfServiceUser:
    def __init__(self, username, password, language=None):
        self._client = Client(language=language)
        self.username = username
        self.password = password

    def request(self, uri, **kwargs):
        options = {'username': self.username, 'password': self.password}
        options.update(kwargs)
        return self._client.umc_command(uri, options)
        # TODO: kill all self-service UMC module processes because 1 process per request sums up and blocks resources for 15 minutes

    def get_contact(self):
        return {data['id']: data['value'] for data in self.request('passwordreset/get_contact').result}

    def set_contact(self, email='', mobile=''):
        return self.request('passwordreset/set_contact', email=email, mobile=mobile).result

    def get_reset_methods(self):
        return [x['id'] for x in self.request('passwordreset/get_reset_methods').result]

    def send_token(self, method):
        return self.request('passwordreset/send_token', method=method).result

    def set_password(self, token, password):
        return self.request('passwordreset/set_password', token=token, password=password).result

    def auth(self):
        self._client.umc_auth(self.username, self.password)

    def command(self, uri, **kwargs):
        return self._client.umc_command(uri, kwargs)


def do_create_user(udm, email=None, **kwargs):
    if 'mailPrimaryAddress' in kwargs:
        udm.create_object('mail/domain', ignore_exists=True, wait_for_replication=True, check_for_drs_replication=False, name=kwargs['mailPrimaryAddress'].split('@', 1)[1])
    if email:
        kwargs['PasswordRecoveryEmail'] = email
    password = kwargs.setdefault('password', uts.random_string())
    language = kwargs.pop('language', None)
    dn, username = udm.create_user(**kwargs)
    utils.verify_ldap_object(dn)
    return SelfServiceUser(username, password, language=language)


@contextlib.contextmanager
def self_service_user(email=None, **kwargs):
    with udm_test.UCSTestUDM() as udm:
        yield do_create_user(udm, email, **kwargs)


# copy pasted to 86_selenium/test_self_service.py
@contextlib.contextmanager
def capture_mails(timeout=5):
    class MailHandler:
        def __init__(self):
            self.data = []

        async def handle_DATA(self, server, session, envelope):
            content = envelope.content
            print(('receiving email with length=', len(content)))
            text = content.decode('utf-8', errors='replace')
            text = text.replace('\r\n', '\n').rstrip('\n')
            self.data.append(text)
            return '250 OK'

    class MailServer:
        def __init__(self):
            print('Starting mail server')
            self.handler = MailHandler()
            self.controller = Controller(
                self.handler,
                hostname='localhost',
                port=25,
                ready_timeout=timeout,
            )
            self.controller.start()

        def stop(self):
            print('Stopping mail server')
            self.controller.stop()

    subprocess.call(['invoke-rc.d', 'postfix', 'stop'], close_fds=True)
    time.sleep(3)

    server = None
    try:
        server = MailServer()
        yield server.handler
    finally:
        if server is not None:
            try:
                server.stop()
            except Exception:
                print('Warn: Could not close SMTP socket')

        print('(re)starting postfix')
        subprocess.call(['invoke-rc.d', 'postfix', 'start'], close_fds=True)
