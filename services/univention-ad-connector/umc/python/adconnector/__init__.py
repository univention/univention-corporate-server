#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: AD connector
#
# Copyright 2011-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import univention.config_registry
from univention.lib import Translation, admember
from univention.management.console.base import Base, UMC_Error
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules.decorators import file_upload, sanitize, simple_response
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.modules.sanitizers import StringSanitizer

import notifier.popen
from ldap import explode_rdn

from contextlib import contextmanager
import fnmatch
import psutil
import os.path
import subprocess
import time
import pipes
import traceback
import ldb
import ldap.dn
import ldap.filter

from samba.param import LoadParm
from samba.samdb import SamDB
from samba.auth import system_session
from samba.credentials import Credentials

_ = Translation('univention-management-console-module-adconnector').translate

FN_BINDPW = '/etc/univention/connector/ad/bindpw'
DO_NOT_CHANGE_PWD = '********************'


class ADNotAvailable(Exception):
	pass


@contextmanager
def ucr_rollback(ucr, variables):
	ucr.load()
	old = {}
	for variable in variables:
		old[variable] = ucr.get(variable)
	try:
		yield
	except:
		univention.config_registry.frontend.ucr_update(ucr, old)
		raise


def test_connection():
	'''Search a query that should never fail: RDN of connector/ad/ldap/base'''
	base = ucr.get('connector/ad/ldap/base')
	rdn = explode_rdn(base)[0]
	p1, stdout, stderr = adsearch(rdn)
	if stderr:
		MODULE.warn(stderr)
	if p1.returncode != 0:
		raise ADNotAvailable()
	return True


def adsearch(query):
	cmd = ['/usr/sbin/univention-adsearch', query]
	p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p1.communicate()
	return p1, stdout, stderr


def guess_ad_domain_language():
	'''AD Connector supports "en" and "de", this check detects a German AD
	Domain and returns "en" as fallback.'''
	p1, stdout, stderr = adsearch('sAMAccountName=Domänen-Admins')
	if stderr:
		MODULE.warn('adsearch "sAMAccountName=Domänen-Admins" stderr: %s' % stderr)
	for line in stdout.split('\n'):
		line = line.lower().strip()
		if line == 'samaccountname: domänen-admins':
			return 'de'
	return 'en'


def get_ad_binddn_from_name(base, server, username, password):
	lp = LoadParm()
	creds = Credentials()
	creds.guess(lp)
	creds.set_username(username)
	creds.set_password(password)
	binddn = 'cn=%s,cn=users,%s' % (ldap.dn.escape_dn_chars(username), base)
	try:
		samdb = SamDB(url='ldap://%s' % server, session_info=system_session(), credentials=creds, lp=lp)
		res = samdb.search(
			base,
			scope=ldb.SCOPE_SUBTREE,
			expression=ldap.filter.filter_format('(samAccountName=%s)', [username, ]),
			attrs=['samaccountname'])
		if res.count == 1:
			binddn = res.msgs[0].get('dn', idx=0).extended_str()
	except ldb.LdbError as ex:
		MODULE.warn('get_dn_from_name() could not get binddn for user %s: %s' % (username, ex))
	return binddn


class Instance(Base, ProgressMixin):
	OPTION_MAPPING = (
		('LDAP_Host', 'connector/ad/ldap/host', ''),
		('LDAP_Base', 'connector/ad/ldap/base', ''),
		('LDAP_BindDN', 'connector/ad/ldap/binddn', ''),
		('KerberosDomain', 'connector/ad/mapping/kerberosdomain', ''),
		('PollSleep', 'connector/ad/poll/sleep', 5),
		('RetryRejected', 'connector/ad/retryrejected', 10),
		('DebugLevel', 'connector/debug/level', 2),
		('DebugFunction', 'connector/debug/function', False),
		('MappingSyncMode', 'connector/ad/mapping/syncmode', 'sync'),
		('MappingGroupLanguage', 'connector/ad/mapping/group/language', 'de')
	)

	def init(self):
		self.__update_status()

	def state(self, request):
		"""Retrieve current status of the Active Directory connection configuration and the service

		options: {}

		return: { 'configured' : (True|False), 'certificate' : (True|False), 'running' : (True|False) }
		"""

		self.__update_status()
		self.finished(request.id, {
			'ssl_enabled': self.status_ssl,
			'password_sync_enabled': self.status_password_sync,
			'running': self.status_running,
			'certificate': self.status_certificate,
			'mode_admember': self.status_mode_admember,
			'mode_adconnector': self.status_mode_adconnector,
			'configured': self.status_mode_adconnector or self.status_mode_admember,
			'server_role': ucr.get('server/role'),
		})

	def load(self, request):
		"""Retrieve current status of the Active Directory connection configuration and the service

		options: {}

		return: { <all AD connector UCR variables> }
		"""

		result = {}
		for option, var, default in Instance.OPTION_MAPPING:
			result[option] = ucr.get(var, default)

		pwd_file = ucr.get('connector/ad/ldap/bindpw')
		result['passwordExists'] = bool(pwd_file and os.path.exists(pwd_file))

		self.finished(request.id, result)

	@sanitize(LDAP_Host=StringSanitizer(required=True))
	def adconnector_save(self, request):
		"""Saves the Active Directory connection configuration

		options:
			Host_IP: IP address of the AD server
			LDAP_Host: hostname of the AD server
			LDAP_Base: LDAP base of the AD server
			LDAP_BindDN: LDAP DN to use for authentication
			KerberosDomain: kerberos domain
			PollSleep: time in seconds between polls
			RetryRejected: how many time to retry a synchronisation
			MappingSyncMode: synchronisation mode
			MappingGroupLanguage: language of the AD server

		return: { 'success' : (True|False), 'message' : <details> }
		"""

		self.required_options(request, 'Host_IP')
		self.required_options(request, *[x[0] for x in Instance.OPTION_MAPPING if x[2] == ''])

		for umckey, ucrkey, default in Instance.OPTION_MAPPING:
			val = request.options.get(umckey, default)
			if val:
				if isinstance(val, bool):
					val = val and 'yes' or 'no'
				MODULE.info('Setting %s=%s' % (ucrkey, val))
				univention.config_registry.handler_set([u'%s=%s' % (ucrkey, val)])

		ucr.load()
		if ucr.get('connector/ad/ldap/ldaps'):
			MODULE.info('Unsetting connector/ad/ldap/ldaps')
			univention.config_registry.handler_unset([u'connector/ad/ldap/ldaps'])
		if ucr.get('connector/ad/ldap/port') == '636':
			MODULE.info('Setting ldap port to 389')
			univention.config_registry.handler_set([u'connector/ad/ldap/port=389'])

		if not request.options.get('LDAP_Password') in (None, '', DO_NOT_CHANGE_PWD):
			fn = ucr.get('connector/ad/ldap/bindpw', FN_BINDPW)
			try:
				fd = open(fn, 'w')
				fd.write(request.options.get('LDAP_Password'))
				fd.close()
				os.chmod(fn, 0600)
				os.chown(fn, 0, 0)
				univention.config_registry.handler_set([u'connector/ad/ldap/bindpw=%s' % fn])
			except Exception as e:
				MODULE.info('Saving bind password failed (filename=%(fn)s ; exception=%(exception)s)' % {'fn': fn, 'exception': str(e.__class__)})
				self.finished(request.id, {'success': False, 'message': _('Saving bind password failed (filename=%(fn)s ; exception=%(exception)s)') % {'fn': fn, 'exception': str(e.__class__)}})
				return

		ssldir = '/etc/univention/ssl/%s' % request.options.get('LDAP_Host')
		if not os.path.exists(ssldir):
			self._create_certificate(request)
			return

		# enter a static host entry such that the AD server's FQDN can be resolved
		univention.config_registry.handler_set([u'hosts/static/%(Host_IP)s=%(LDAP_Host)s' % request.options])

		# check for SSL support on AD side
		if admember.server_supports_ssl(server=request.options.get('LDAP_Host')):
			MODULE.process('Enabling SSL...')
			admember.enable_ssl()
		else:
			MODULE.warn('SSL is not supported')
			admember.disable_ssl()

		# UCR variables are set, and now we can try to guess the language of
		# the AD domain
		ad_lang = guess_ad_domain_language()
		univention.config_registry.handler_set([u'connector/ad/mapping/group/language=%s' % ad_lang])

		self.finished(request.id, {'success': True, 'message': _('Active Directory connection settings have been saved.')})

	def _create_certificate(self, request):
		ssldir = '/etc/univention/ssl/%s' % request.options.get('LDAP_Host')

		def _return(pid, status, buffer, request):
			if not os.path.exists(ssldir):
				MODULE.error('Creation of certificate failed (%s)' % ssldir)
				self.finished(request.id, {'success': False, 'message': _('Creation of certificate failed (%s)') % ssldir})
			self.finished(request.id, {'success': True, 'message': _('Active Directory connection settings have been saved and a new certificate for the Active Directory server has been created.')})

		cmd = '/usr/sbin/univention-certificate new -name %s' % pipes.quote(request.options['LDAP_Host'])
		MODULE.info('Creating new SSL certificate: %s' % cmd)
		proc = notifier.popen.Shell(cmd, stdout=True)
		cb = notifier.Callback(_return, request)
		proc.signal_connect('finished', cb)
		proc.start()

	@file_upload
	def upload_certificate(self, request):
		def _return(pid, status, bufstdout, bufstderr, request, fn):
			success = True
			if status == 0:
				message = _('Certificate has been uploaded successfully.')
				MODULE.info('Certificate has been uploaded successfully. status=%s\nSTDOUT:\n%s\n\nSTDERR:\n%s' % (status, '\n'.join(bufstdout), '\n'.join(bufstderr)))
				try:
					self._enable_ssl_and_test_connection(fn)
				except UMC_Error:
					message = _('Could not establish connection. Either the certificate is wrong, the Active Directory server is unreachable or it does not support SSL.')
					success = False
			else:
				success = False
				message = _('Certificate upload or conversion failed.')
				MODULE.process('Certificate upload or conversion failed. status=%s\nSTDOUT:\n%s\n\nSTDERR:\n%s' % (status, '\n'.join(bufstdout), '\n'.join(bufstderr)))

			self.finished(request.id, [{'success': success, 'message': message}])

		upload = request.options[0]['tmpfile']
		now = time.strftime('%Y%m%d_%H%M%S', time.localtime())
		fn = '/etc/univention/connector/ad/ad_cert_%s.pem' % now
		cmd = '/usr/bin/openssl x509 -inform der -outform pem -in %s -out %s 2>&1' % (pipes.quote(upload), fn)

		MODULE.info('Converting certificate into correct format: %s' % cmd)
		proc = notifier.popen.Shell(cmd, stdout=True, stderr=True)
		cb = notifier.Callback(_return, request, fn)
		proc.signal_connect('finished', cb)
		proc.start()

	def service(self, request):
		MODULE.info('State: options=%s' % request.options)
		self.required_options(request, 'action')

		self.__update_status()
		action = request.options['action']

		MODULE.info('State: action=%s  status_running=%s' % (action, self.status_running))

		success = True
		message = None
		if self.status_running and action == 'start':
			message = _('Active Directory Connector is already running. Nothing to do.')
		elif not self.status_running and action == 'stop':
			message = _('Active Directory Connector is already stopped. Nothing to do.')
		elif action not in ('start', 'stop'):
			MODULE.process('State: unknown command: action=%s' % action)
			message = _('Unknown command ("%s") Please report error to your local administrator.') % action
			success = False

		if message is not None:
			self.finished(request.id, {'success': success, 'message': message})
			return

		def _run_it(action):
			return subprocess.call(('invoke-rc.d', 'univention-ad-connector', action))

		def _return(thread, result, request):
			success = not result
			if result:
				message = _('Switching running state of Active Directory Connector failed.')
				MODULE.info('Switching running state of Active Directory Connector failed. exitcode=%s' % result)
			else:
				if request.options.get('action') == 'start':
					message = _('Active Directory connection service has been started.')
				else:
					message = _('Active Directory connection service has been stopped.')

			self.finished(request.id, {'success': success, 'message': message})

		cb = notifier.Callback(_return, request)
		func = notifier.Callback(_run_it, action)
		thread = notifier.threads.Simple('service', func, cb)
		thread.run()

	def __update_status(self):
		ucr.load()
		fn = ucr.get('connector/ad/ldap/certificate')
		self.status_ssl = ucr.is_true('connector/ad/ldap/ssl')
		self.status_password_sync = ucr.is_true('connector/ad/mapping/user/password/kinit')
		self.status_certificate = bool(fn and os.path.exists(fn))
		self.status_running = self.__is_process_running('*python*univention/connector/ad/main.py*')
		self.status_mode_admember = admember.is_localhost_in_admember_mode(ucr)
		self.status_mode_adconnector = admember.is_localhost_in_adconnector_mode(ucr)

	def __is_process_running(self, command):
		for proc in psutil.process_iter():
			try:
				cmdline = proc.cmdline() if callable(proc.cmdline) else proc.cmdline
			except psutil.NoSuchProcess:
				continue
			if cmdline and fnmatch.fnmatch(' '.join(cmdline), command):
				return True
		return False

	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True),
		ad_server_address=StringSanitizer(required=True),
		mode=StringSanitizer(default='admember'),
	)
	@simple_response
	def check_domain(self, username, password, ad_server_address, mode):
		ad_domain_info = {}
		try:
			if mode == 'admember':
				admember.check_server_role()
			ad_domain_info = admember.lookup_adds_dc(ad_server_address)

			ad_server_ip = ad_domain_info['DC IP']
			if mode == 'admember':
				admember.check_domain(ad_domain_info)
			admember.check_connection(ad_domain_info, username, password)
			admember.check_ad_account(ad_domain_info, username, password)
		except admember.invalidUCSServerRole as exc:  # check_server_role()
			MODULE.warn('Failure: %s' % exc)
			raise UMC_Error(_('The AD member mode can only be configured on a DC master server.'))
		except admember.failedADConnect as exc:  # lookup_adds_dc()
			MODULE.warn('Failure: %s' % exc)
			raise UMC_Error(_('Could not connect to AD Server %s. Please verify that the specified address is correct. (%s)') % (ad_server_address, 'check_domain: %s' % (exc,)))
		except admember.domainnameMismatch as exc:  # check_domain()
			MODULE.warn('Failure: %s' % exc)
			raise UMC_Error(_('The domain name of the AD Server (%(ad_domain)s) does not match the local UCS domain name (%(ucs_domain)s). For the AD member mode, it is necessary to setup a UCS system with the same domain name as the AD Server.') % {'ad_domain': ad_domain_info.get("Domain"), 'ucs_domain': ucr['domainname']})
		except admember.connectionFailed as exc:  # check_connection()
			MODULE.warn('Failure: %s' % exc)
			raise UMC_Error(_('Could not connect to AD Server %s. Please verify that username and password are correct. (Details:\n%s)') % (ad_domain_info.get('DC DNS Name'), exc))
		except admember.notDomainAdminInAD as exc:  # check_ad_account()
			MODULE.warn('Failure: %s' % exc)
			raise UMC_Error(_('The given user is not member of the Domain Admins group in Active Directory. This is a requirement for the Active Directory domain join.'))

		# final info dict that is returned... replace spaces in the keys with '_'
		MODULE.info('Preparing info dict...')
		info = dict([(key.replace(' ', '_'), value) for key, value in ad_domain_info.iteritems()])
		info['ssl_supported'] = admember.server_supports_ssl(ad_server_ip)
		# try to get binddn
		info['LDAP_BindDN'] = get_ad_binddn_from_name(info['LDAP_Base'], ad_server_ip, username, password)
		MODULE.info(str(info))
		return info

	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True),
		ad_server_address=StringSanitizer(required=True),
	)
	@simple_response(with_progress=True)
	def admember_join(self, username, password, ad_server_address, progress):
		progress.title = _('Joining UCS into Active Directory domain')
		progress.total = 100.0
		progress.warnings = []
		overall_success = False
		MODULE.process(progress.title)

		def _progress(steps, msg):
			progress.current = float(steps)
			progress.message = msg
			MODULE.process(msg)
			time.sleep(0.2)

		def _err(exc=None, msg=None):

			exc_str = ''
			if exc is not None:
				exc_str = str(exc) or exc.__doc__  # if no message, take the doc string
				exc_class_name = exc.__class__.__name__
				MODULE.error('Join process failed [%s]: %s' % (exc_class_name, exc_str))

			if msg:
				MODULE.error(msg)
			else:
				msg = _('An unexpected error occurred: %s') % exc_str

			progress.finish_with_result({
				'success': False,
				'error': msg,
				'warnings': progress.warnings,
			})

		ad_domain_info = {}
		try:
			admember.check_server_role()
			ad_domain_info = admember.lookup_adds_dc(ad_server_address)
			ad_server_ip = ad_domain_info['DC IP']

			_progress(5, _('Configuring time synchronization...'))
			admember.time_sync(ad_server_ip)
			admember.set_timeserver(ad_server_ip)

			_progress(10, _('Configuring DNS server...'))
			admember.set_nameserver([ad_server_ip])
			admember.prepare_ucr_settings()

			_progress(15, _('Configuring Kerberos settings...'))
			admember.disable_local_heimdal()
			admember.disable_local_samba4()

			_progress(20, _('Configuring reverse DNS settings...'))
			admember.prepare_dns_reverse_settings(ad_domain_info)

			_progress(25, _('Configuring software components...'))

			_step_offset = 30.0
			_nsteps = 35.0

			def _step_handler(step):
				MODULE.process('Package manager progress: %.1f' % step)
				progress.current = (step / 100.0) * _nsteps + _step_offset

			def _err_handler(err):
				MODULE.warn(err)
				progress.warnings.append(err)

			success = admember.remove_install_univention_samba(info_handler=MODULE.process, error_handler=_err_handler, step_handler=_step_handler)
			if not success:
				raise RuntimeError(_('An error occurred while installing necessary software components.'))

			_progress(65, _('Configuring synchronization from AD...'))
			admember.prepare_connector_settings(username, password, ad_domain_info)
			admember.disable_ssl()

			_progress(70, _('Renaming well known SID objects...'))
			admember.rename_well_known_sid_objects(username, password)

			_progress(75, _('Configuring Administrator account...'))
			admember.prepare_administrator(username, password)

			_progress(80, _('Running Samba join script...'))
			admember.run_samba_join_script(username, password)

			_progress(85, _('Configuring DNS entries...'))
			admember.add_domaincontroller_srv_record_in_ad(ad_server_ip, username, password)
			admember.add_host_record_in_ad(uid=username, bindpw=password, sso=True)

			admember.make_deleted_objects_readable_for_this_machine(username, password)
			admember.synchronize_account_position(ad_domain_info, username, password)

			_progress(90, _('Starting Active Directory connection service...'))
			admember.start_service('univention-ad-connector')

			_progress(95, _('Registering LDAP service entry...'))
			admember.add_admember_service_to_localhost()

			overall_success = True
			_progress(100, _('Join has been finished successfully.'))

		# error handling...
		except admember.invalidUCSServerRole as exc:
			_err(exc, _('The AD member mode can only be configured on a DC master server.'))
		except admember.failedADConnect as exc:
			_err(exc, _('Could not connect to AD Server %s. Please verify that the specified address is correct. (%s)') % (ad_domain_info.get('DC DNS Name'), 'admember_join: %s' % (exc,)))
		except admember.domainnameMismatch as exc:
			_err(exc, _('The domain name of the AD Server (%(ad_domain)s) does not match the local UCS domain name (%(ucs_domain)s). For the AD member mode, it is necessary to setup a UCS system with the same domain name as the AD Server.') % {'ad_domain': ad_domain_info["Domain"], 'ucs_domain': ucr['domainname']})
		except admember.connectionFailed as exc:
			_err(exc, _('Could not connect to AD Server %s. Please verify that username and password are correct. (Details:\n%s)') % (ad_domain_info.get('DC DNS Name'), exc))
		except admember.failedToSetAdministratorPassword as exc:
			_err(exc, _('Failed to set the password of the UCS Administrator to the Active Directory Administrator password.'))
		except admember.failedToCreateAdministratorAccount as exc:
			_err(exc, _('Failed to create the Administrator account in UCS.'))
		except admember.sambaSidNotSetForAdministratorAccount as exc:
			_err(exc, _('The sambaSID could not set for the Administrator account in UCS.'))
		except admember.failedToSearchForWellKnownSid as exc:
			_err(exc, _('Failed to search for the well known SID.'))
		except admember.failedToAddAdministratorAccountToDomainAdmins as exc:
			_err(exc, _('Failed to add the Administrator account to the Domain Admins group.'))
		except admember.timeSyncronizationFailed as exc:
			_err(exc, _('Could not synchronize the time between the UCS system and the Active Directory domain controller: %s') % exc)
		except RuntimeError as exc:
			_err(exc)
		except Exception as exc:
			# catch all other errors that are unlikely to occur
			_err(exc)
			MODULE.error('Traceback:\n%s' % traceback.format_exc())

		if not overall_success:
			_progress(100, _('Join has been finished with errors.'))
			admember.revert_ucr_settings()
			admember.revert_connector_settings()

		if hasattr(progress, 'result'):
			# some error probably occurred -> return the result in the progress
			return progress.result

		return {'success': success}

	def _enable_ssl_and_test_connection(self, certificate_fname=None):
		with ucr_rollback(ucr, ['connector/ad/ldap/ssl', 'connector/ad/ldap/certificate']):
			if certificate_fname:
				univention.config_registry.handler_set([u'connector/ad/ldap/certificate=%s' % certificate_fname])
			server = ucr.get('connector/ad/ldap/host')
			if server:
				success = False
				if admember.server_supports_ssl(server):
					admember.enable_ssl()
					try:
						success = test_connection()
					except ADNotAvailable:
						success = False
				if not success:
					raise UMC_Error(_('Could not establish an encrypted connection. Either "%r" is not reachable or does not support encryption.') % server)
			else:
				MODULE.warn('connector is not configured yet, cannot test connection')

	@simple_response
	def enable_ssl(self):
		self._enable_ssl_and_test_connection()
		return subprocess.call(['invoke-rc.d', 'univention-ad-connector', 'restart'])

	@simple_response
	def password_sync_service(self, enable=True):
		# kinit=true  -> do not sync passwords, but use Kerberos authentication
		# kinit=false -> sync passwords
		value = str(not enable).lower()
		univention.config_registry.handler_set(['connector/ad/mapping/user/password/kinit=%s' % value])
		return subprocess.call(['invoke-rc.d', 'univention-ad-connector', 'restart'])

	def _check_dcmaster_srv_rec(self):
		if admember.get_domaincontroller_srv_record(ucr.get('domainname')):
			return True
		else:
			return False

	@simple_response
	def check_dcmaster_srv_rec(self):
		result = self._check_dcmaster_srv_rec()
		return {'success': result}
