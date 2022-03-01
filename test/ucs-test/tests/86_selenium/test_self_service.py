import asyncore
import contextlib
import fcntl
import subprocess
import time
from smtpd import SMTPServer
from threading import Thread


# copy pasted from 83_self_service/test_self_service.py
@contextlib.contextmanager
def capture_mails(timeout=5):

	class Mail(SMTPServer):

		def __init__(self, *args, **kwargs):
			SMTPServer.__init__(self, *args, **kwargs)
			self.set_reuse_addr()
			fcntl.fcntl(self.socket.fileno(), fcntl.F_SETFD, fcntl.fcntl(self.socket.fileno(), fcntl.F_GETFD) | fcntl.FD_CLOEXEC)
			self.data = []

		def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
			print('receiving email with length=', len(data))
			self.data.append(data)

	class MailServer(object):

		def __init__(self):
			print('Starting mail server')
			self.smtp = Mail(('localhost', 25), '')
			self.thread = Thread(target=asyncore.loop, kwargs={'timeout': timeout})
			self.thread.start()

		def stop(self):
			print('Stopping mail server')
			self.smtp.close()
			self.thread.join()

	subprocess.call(['invoke-rc.d', 'postfix', 'stop'], close_fds=True)
	time.sleep(3)
	try:
		server = MailServer()
		try:
			yield server.smtp
		finally:
			try:
				server.smtp.close()
			except Exception:
				print('Warn: Could not close SMTP socket')
			server.stop()
	finally:
		print('(re)starting postfix')
		subprocess.call(['invoke-rc.d', 'postfix', 'start'], close_fds=True)
