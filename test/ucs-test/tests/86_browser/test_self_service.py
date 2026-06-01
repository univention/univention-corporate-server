import contextlib
import subprocess
import time

from aiosmtpd.controller import Controller

from univention.testing.browser import logger


# copy pasted from 83_self_service/test_self_service.py
@contextlib.contextmanager
def capture_mails(timeout=5):
    class MailHandler:
        def __init__(self):
            self.data = []

        async def handle_DATA(self, server, session, envelope):
            content = envelope.content
            logger.info('receiving email with length=%d' % len(content))
            text = content.decode('utf-8', errors='replace')
            text = text.replace('\r\n', '\n').rstrip('\n')
            self.data.append(text)
            return '250 OK'

    class MailServer:
        def __init__(self):
            logger.info('Starting mail server')
            self.handler = MailHandler()
            self.controller = Controller(
                self.handler,
                hostname='localhost',
                port=25,
                ready_timeout=timeout,
            )
            self.controller.start()

        def stop(self):
            logger.info('Stopping mail server')
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
                logger.warning('Could not close SMTP socket')

        logger.info('(re)starting postfix')
        subprocess.call(['invoke-rc.d', 'postfix', 'start'], close_fds=True)
