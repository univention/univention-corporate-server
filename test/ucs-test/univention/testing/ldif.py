#!/usr/bin/env python
# coding: utf-8

"""
This program compares LDAP host entries with a local comparative ldif file.
All differences will be displayed at the console.
"""
from __future__ import print_function

from optparse import OptionParser, OptionGroup, SUPPRESS_HELP
import re
import os
import sys
import signal
import subprocess
import select
import errno
import time


USAGE = 'usage: %prog [option] LDIF1 [[option] LDIF2]'
DESCRIPTION = '''\
Compares the LDIF files.
LDIF can be:
 a local LDIF file
 a hostname whose LDAP will be dumped using slapcat over ssh.
If LDIF2 is omitted, a local 'slapcat' is used.
'''
VERSION = '%prog 1.0'


class LdifError(Exception):
	"""
	Error in input processing.
	"""


class SlapError(Exception):
	"""
	Error in slapcat processing.
	"""


class LdifSource(object):
	"""
	Abstract class for LDIF source.
	"""
	# RFC2849: LDAP Data Interchange Format
	RE = re.compile(r'''
		^
		(?:
		  ([0-9]+(?:\.[0-9]+)*)  # ldap-oid
		 |([A-Za-z][\-0-9A-Za-z]*)  # AttributeType
		)  # AttributeDescription
		(;[\-0-9A-Za-z]+)*  # OPTIONS
		:
		(?:
		  $  # EMPTY
		 |:[ ]*([+/0-9=A-Za-z]+)  # BASE64-STRING
		 |[ ]*([\x01-\x09\x0b-\x0c\x0e-\x1f\x21-\x39\x3b\x3d-\x7f][\x01-\x09\x0b-\x0c\x0e-\x7f]*)  # SAFE-STRING
		)  # value-spec
		$
		''', re.VERBOSE)

	# Operational LDAP attributes
	OPERATIONAL = frozenset((
		"entryCSN",
		"modifiersName",
		"modifyTimestamp",
		"creatorsName",
		"entryUUID",
		"createTimestamp",
		'structuralObjectClass',
	))

	def __init__(self):
		self.src = None
		self.lno = 0
		self.exclude = LdifSource.OPERATIONAL

	def next_line(self):
		"""
		Return line iterator.
		"""
		for line in self.src:
			self.lno += 1
			if not line.startswith('#'):
				break
		else:
			return
		line = line.rstrip()  # pylint: disable=W0631
		try:
			for line2 in self.src:
				self.lno += 1
				if line2.startswith('#'):
					continue
				line2 = line2.rstrip()
				if line2[:1] in (' ', '\t'):
					line += line2[1:]
				else:
					yield self.split(line)
					line = line2
		except StopIteration:
			pass
		yield self.split(line)

	def split(self, line):
		"""
		Split attribute and value.
		Options are stripped.
		Base64 encoded values are decoded.

		:param str line: The line to split.
		:return: A tuple (name, value).
		:rtype: tuple

		>>> LdifSource().split('')
		>>> LdifSource().split('a:')
		('a', None)
		>>> LdifSource().split('a: b')
		('a', 'b')
		>>> LdifSource().split('a:: YWFh')
		('a', 'aaa')
		>>> LdifSource().split('a;b:c')
		('a', 'c')
		>>> LdifSource().split('a;b;c::YWFh')
		('a', 'aaa')
		"""
		if not line:
			return None
		match = self.RE.match(line)
		if not match:
			raise LdifError('%d: %s' % (self.lno, line))
		oid, attr, _opt, b64, plain = match.groups()
		return (attr or oid, plain or (b64.decode('base64') if b64 else None))

	def __iter__(self):
		"""
		Return line iterator.
		"""
		obj = {}
		for key_value in self.next_line():
			if key_value:
				key, value = key_value
				if key in self.exclude:
					continue
				obj.setdefault(key, []).append(value)
			else:
				yield obj
				obj = {}


class LdifFile(LdifSource):
	"""
	LDIF source from local file.
	"""

	@classmethod
	def create(cls, arg, options):
		return cls(arg)

	def __init__(self, filename):
		super(LdifFile, self).__init__()
		self.filename = filename

	def start_reading(self):
		"""
		Start reading the LDIF data.
		"""
		try:
			self.src = open(self.filename, 'r+')
		except IOError as ex:
			raise LdifError(ex)


class LdifSlapcat(LdifSource):
	"""
	LDIF source from local LDAP.
	"""

	@classmethod
	def create(cls, arg, options):
		return cls()

	def __init__(self):
		super(LdifSlapcat, self).__init__()
		self.command = ('slapcat', '-d0')
		self.proc = None

	def start_reading(self):
		"""
		Start reading the LDIF data.
		"""
		self.run_command()
		self.src = self.proc.stdout

	def run_command(self):
		"""
		Run command to dump LDIF.
		"""
		try:
			self.proc = subprocess.Popen(self.command, stdout=subprocess.PIPE)
		except OSError as ex:
			raise SlapError("Error executing", self.command, ex)


class LdifSsh(LdifSlapcat):
	"""
	LDIF source from remote LDAP.
	"""

	@classmethod
	def create(cls, hostname, options):
		return cls(hostname, options.ssh)

	def __init__(self, hostname, ssh='ssh'):
		super(LdifSsh, self).__init__()
		self.command = (ssh, hostname) + self.command

	def start_reading(self):
		"""
		Start reading the LDIF data.
		"""
		super(LdifSsh, self).start_reading()
		self.wait_for_data()

	def wait_for_data(self):
		"""
		Wait for the remote process to send data.

		>>> x=LdifSsh('', 'echo');x.start_reading();x.wait_for_data()
		>>> x=LdifSsh('', 'false');x.start_reading();x.wait_for_data()
		Traceback (most recent call last):
		...
		SlapError: ('Error executing', ('false', '', 'slapcat', '-d0'), 1)
		"""
		while True:
			rlist = [self.proc.stdout]
			wlist = []
			xlist = []
			try:
				rlist, wlist, xlist = select.select(rlist, wlist, xlist)
				break
			except select.error as ex:
				if ex[0] == errno.EINTR:
					continue
				else:
					raise
		time.sleep(0.5)
		ret = self.proc.poll()
		if ret is not None and ret != 0:
			raise SlapError("Error executing", self.command, ret)


def __test(_option, _opt_str, _value, _parser):
	"""
	Run internal test suite.
	"""
	import doctest
	res = doctest.testmod()
	sys.exit(int(bool(res[0])))


def stream2object(ldif):
	"""
	Convert LDIF stream to dictionary of objects.

	:param LdifSource ldif: A LDIF stream.
	:return: A dictionary mapping distinguished names to a dictionary of key-values.
	:rtype: dict(str, dict(str, list[str])

	>>> stream2object([{'dn': ['dc=test']}])
	{'dc=test': {}}
	"""
	objects = {}
	for obj in ldif:
		try:
			dname, = obj.pop('dn')
			objects[dname] = obj
		except KeyError:
			print('Missing dn: %r' % (obj,), file=sys.stderr)
		except ValueError:
			print('Multiple dn: %r' % (obj,), file=sys.stderr)
	return objects


def sort_dn(dname):
	"""
	Sort by reversed dn.

	:param str dname: distinguished name.
	:return: tuple of relative distinguised names.
	:rtype: tuple(tuple[str])

	>>> sort_dn('a=1')
	(('a=1',),)
	>>> sort_dn('b=1,a=1')
	(('a=1',), ('b=1',))
	>>> sort_dn('b=2+a=1')
	(('a=1', 'b=2'),)
	"""
	return tuple(reversed([tuple(sorted(_.split('+'))) for _ in dname.split(',')]))


def compare_ldif(lldif, rldif, options):
	"""
	Compare two LDIF files.

	:param LdifSource ldif1: first LDIF to compare.
	:param LdifSource ldif2: second LDIF to compare.
	:param Namespace options: command line options.
	"""

	lefts = stream2object(lldif)
	rights = stream2object(rldif)

	lkeys = sorted(lefts.keys(), key=sort_dn, reverse=True)
	rkeys = sorted(rights.keys(), key=sort_dn, reverse=True)

	ret = 0
	ldn = rdn = None
	while True:
		if not ldn and lkeys:
			ldn = lkeys.pop(0)
		if not rdn and rkeys:
			rdn = rkeys.pop(0)
		if not ldn and not rdn:
			break

		order = cmp(sort_dn(ldn) if ldn else None, sort_dn(rdn) if rdn else None)
		if order < 0:
			diffs = list(compare_keys({}, rights[rdn]))
			print('+dn: %s' % (rdn,))
			rdn = None
		elif order > 0:
			diffs = list(compare_keys(lefts[ldn], {}))
			print('-dn: %s' % (ldn,))
			ldn = None
		else:
			diffs = list(compare_keys(lefts[ldn], rights[rdn]))
			if not options.objects and all((diff == 0 for diff, key, val in diffs)):
				ldn = rdn = None
				continue
			print(' dn: %s' % (rdn,))
			ldn = rdn = None
		for diff, key, val in diffs:
			if options.attributes or diff:
				print('%s%s: %s' % (' +-'[diff], key, val))
		print()
		ret = 1
	return ret


def compare_keys(ldata, rdata):
	"""
	Compare and return attributes of two LDAP objects.

	:param dict ldata: the first LDAP object.
	:param dict rdata: the second LDAP object.
	:return: an iterator of differences as 3-tuples (comparison, key, value).

	>>> list(compare_keys({}, {}))
	[]
	>>> list(compare_keys({'a': [1]}, {}))
	[(-1, 'a', 1)]
	>>> list(compare_keys({}, {'a': [1]}))
	[(1, 'a', 1)]
	>>> list(compare_keys({'a': [1]}, {'a': [1]}))
	[(0, 'a', 1)]
	>>> list(compare_keys({'a': [1]}, {'a': [2]}))
	[(1, 'a', 2), (-1, 'a', 1)]
	"""
	lkeys = sorted(ldata.keys(), reverse=True)
	rkeys = sorted(rdata.keys(), reverse=True)

	lkey = rkey = None
	while True:
		if not lkey and lkeys:
			lkey = lkeys.pop(0)
		if not rkey and rkeys:
			rkey = rkeys.pop(0)
		if not lkey and not rkey:
			break

		if lkey < rkey:
			for diff in compare_values(rkey, [], rdata[rkey]):
				yield diff
			rkey = None
		elif lkey > rkey:
			for diff in compare_values(lkey, ldata[lkey], []):
				yield diff
			lkey = None
		else:
			for diff in compare_values(lkey, ldata[lkey], rdata[rkey]):
				yield diff
			lkey = rkey = None


def compare_values(attr, lvalues, rvalues):
	"""
	Compare and return values of two multi-valued LDAP attributes.

	:param list lvalues: the first values.
	:param list rvalues: the second values.
	:return: an iterator of differences as 3-tuples (comparison, key, value), where comparison<0 if key is missing in lvalues, comparison>0 if key is missing in rvalues, otherwise 0.

	>>> list(compare_values('attr', [], []))
	[]
	>>> list(compare_values('attr', [1, 2], [2, 3]))
	[(1, 'attr', 3), (0, 'attr', 2), (-1, 'attr', 1)]
	"""
	lvalues.sort(reverse=True)
	rvalues.sort(reverse=True)

	lval = rval = None
	while True:
		if not lval and lvalues:
			lval = lvalues.pop(0)
		if not rval and rvalues:
			rval = rvalues.pop(0)
		if not lval and not rval:
			break

		if lval < rval:
			yield (1, attr, rval)
			rval = None
		elif lval > rval:
			yield (-1, attr, lval)
			lval = None
		else:
			yield (0, attr, lval)
			lval = rval = None


def commandline():
	"""
	Parse command line arguments.
	"""
	parser = OptionParser(usage=USAGE, version=VERSION)
	parser.description = DESCRIPTION
	parser.disable_interspersed_args()
	parser.set_defaults(source=LdifFile, verbose=1)
	group = OptionGroup(parser, "Source", "Source for LDIF")
	group.add_option(
		"--file", "-f",
		action="store_const", dest="source", const=LdifFile,
		help="next arguments are LDIF files")
	group.add_option(
		"--host", "-H",
		action="store_const", dest="source", const=LdifSsh,
		help="next arguments are LDAP hosts")
	group.add_option(
		"--ssh", "-s", default="ssh",
		action="store", dest="ssh", type="string",
		help="specify the remote shell to use [%default]")
	parser.add_option_group(group)

	group = OptionGroup(parser, "Attributes", "Ignore attributes")
	group.add_option(
		"--operational",
		action="store_true", dest="operational",
		help="also compare operational attributes")
	group.add_option(
		"--exclude", "-x",
		action="append", dest="exclude", type="string",
		help="ignore attribute", default=[])
	parser.add_option_group(group)

	group = OptionGroup(parser, "Output", "Control output")
	group.add_option(
		"--objects", "-o",
		action="store_true", dest="objects",
		help="show even unchanged objects")
	group.add_option(
		"--attributes", "-a",
		action="store_true", dest="attributes",
		help="show even unchanged attributes")
	parser.add_option_group(group)

	parser.add_option(
		'--test-internal',
		action='callback', callback=__test,
		help=SUPPRESS_HELP)

	return parser


def main():
	"""
	A main()-method with options.
	"""
	parser = commandline()
	sources = []
	options = None
	args = sys.argv[1:]
	while args:
		options, args = parser.parse_args(args=args, values=options)
		if args:
			try:
				src = args.pop(0)
				ldif = options.source.create(src, options)
				sources.append(ldif)
			except LdifError as ex:
				parser.error(ex)

	try:
		ldif1 = sources.pop(0)
	except IndexError:
		parser.error("No arguments were given")
	try:
		ldif2 = sources.pop(0)
	except IndexError:
		ldif2 = LdifSlapcat.create(None, options)
	if sources:
		parser.error("More than two LDIFs given.")

	exclude = set(options.exclude)
	if not options.operational:
		exclude |= LdifSource.OPERATIONAL
	ldif1.exclude = ldif2.exclude = exclude

	try:
		for ldif in (ldif1, ldif2):
			ldif.start_reading()
	except (LdifError, SlapError) as ex:
		parser.error("Failed to setup source: %s" % ex)

	run_compare(ldif1, ldif2, options)


def run_compare(ldif1, ldif2, options):
	"""
	UNIX correct error handling.
	Termination by signal is propagaed as signal.

	:param LdifSource ldif1: first LDIF to compare.
	:param LdifSource ldif2: second LDIF to compare.
	:param Namespace options: command line options.
	"""
	ret = 2
	try:
		ret = compare_ldif(ldif1, ldif2, options)
	except KeyboardInterrupt:
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		os.kill(os.getpid(), signal.SIGINT)
	except IOError as ex:
		if ex.errno == errno.EPIPE:
			signal.signal(signal.SIGPIPE, signal.SIG_DFL)
			os.kill(os.getpid(), signal.SIGPIPE)
		else:
			print('Error: %s' % (ex,), file=sys.stderr)
	except OSError as ex:
		print('Error: %s' % (ex,), file=sys.stderr)
	except LdifError as ex:
		print('Invalid LDIF: %s' % (ex,), file=sys.stderr)
	sys.exit(ret)


if __name__ == '__main__':
	main()
