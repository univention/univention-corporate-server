"""
Example for a listener module, which logs changes to users.
"""
__package__ = ""  # workaround for PEP 366
import listener
import os
import errno
import univention.debug as ud
from collections import namedtuple

name = 'printusers'
description = 'print all names/users/uidNumbers into a file'
filter = """\
(&
	(|
		(&
			(objectClass=posixAccount)
			(objectClass=shadowAccount)
		)
		(objectClass=univentionMail)
		(objectClass=sambaSamAccount)
		(objectClass=simpleSecurityObject)
		(objectClass=inetOrgPerson)
	)
	(!(objectClass=univentionHost))
	(!(uidNumber=0))
	(!(uid=*$))
)""".translate(None, '\t\n\r')
attributes = ['uid', 'uidNumber', 'cn']
_Rec = namedtuple('Rec', ' '.join(attributes))

USER_LIST = '/root/UserList.txt'


def handler(dn, new, old):
	"""
	Write all changes into a text file.
	This function is called on each change.
	"""
	if new and old:
		_handle_change(dn, new, old)
	elif new and not old:
		_handle_add(dn, new)
	elif old and not new:
		_handle_remove(dn, old)


def _handle_change(dn, new, old):
	"""
	Called when an object is modified.
	"""
	o_rec = _rec(old)
	n_rec = _rec(new)
	ud.debug(ud.LISTENER, ud.INFO, 'Edited user "%s"' % (o_rec.uid,))
	_writeit(o_rec, u'edited. Is now:')
	_writeit(n_rec, None)


def _handle_add(dn, new):
	"""
	Called when an object is newly created.
	"""
	n_rec = _rec(new)
	ud.debug(ud.LISTENER, ud.INFO, 'Added user "%s"' % (n_rec.uid,))
	_writeit(n_rec, u'added')


def _handle_remove(dn, old):
	"""
	Called when an previously existing object is removed.
	"""
	o_rec = _rec(old)
	ud.debug(ud.LISTENER, ud.INFO, 'Removed user "%s"' % (o_rec.uid,))
	_writeit(o_rec, u'removed')


def _rec(data):
	"""
	Retrieve symbolic, numeric ID and name from user data.
	"""
	return _Rec(*(data.get(attr, (None,))[0] for attr in attributes))


class AsRoot(object):

	"""
	Temporarily change effective UID to 'root'.
	"""

	def __enter__(self):
		listener.setuid(0)

	def __exit__(self, exc_type, exc_value, traceback):
		listener.unsetuid()


def _writeit(rec, comment):
	"""
	Append CommonName, symbolic and numeric User-IDentifier, and comment to file.
	"""
	nuid = u'*****' if rec.uid in ('root', 'spam') else rec.uidNumber
	indent = '\t' if comment is None else ''
	try:
		with AsRoot():
			with open(USER_LIST, 'a') as out:
				print >> out, u'%sName: "%s"' % (indent, rec.cn)
				print >> out, u'%sUser: "%s"' % (indent, rec.uid)
				print >> out, u'%sUID: "%s"' % (indent, nuid)
				if comment:
					print >> out, u'%s%s' % (indent, comment,)
	except IOError as ex:
		ud.debug(
			ud.LISTENER, ud.ERROR,
			'Failed to write "%s": %s' % (USER_LIST, ex))


def initialize():
	"""
	Remove the log file.
	This function is called when the module is forcefully reset.
	"""
	try:
		with AsRoot():
			os.remove(USER_LIST)
		ud.debug(
			ud.LISTENER, ud.INFO,
			'Successfully deleted "%s"' % (USER_LIST,))
	except OSError as ex:
		if errno.ENOENT == ex.errno:
			ud.debug(
				ud.LISTENER, ud.INFO,
				'File "%s" does not exist, will be created' % (USER_LIST,))
		else:
			ud.debug(
				ud.LISTENER, ud.WARN,
				'Failed to delete file "%s": %s' % (USER_LIST, ex))
