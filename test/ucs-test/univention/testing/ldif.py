#!/usr/bin/python3
# coding: utf-8

"""
This program compares LDAP host entries with a local comparative ldif file.
All differences will be displayed at the console.
"""
from __future__ import print_function

import base64
import errno
import os
import re
import select
import signal
import subprocess
import sys
import time
import unicodedata
from optparse import SUPPRESS_HELP, OptionGroup, OptionParser, Values  # noqa: F401
from typing import Any, Dict, Iterable, Iterator, List, Set, Text, Tuple, NoReturn  # noqa: F401
try:
	from typing_extensions import Literal  # noqa: F401
except ImportError:
	pass

Entry = Dict[str, List[Text]]

USAGE = 'usage: %prog [option] <LDIF1> [[option] <LDIF2>]'
DESCRIPTION = '''
Compares the LDIF files.
LDIF can be wither a local LDIF file or
a hostname whose LDAP will be dumped using slapcat over ssh.
If LDIF2 is omitted, a local 'slapcat' is used.
'''.strip()


class LdifError(Exception):
	"""
	Error in input processing.
	"""


class SlapError(Exception):
	"""
	Error in slapcat processing.
	"""


class Ldif(object):
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
	OPERATIONAL = {
		"entryCSN",
		"modifiersName",
		"modifyTimestamp",
		"creatorsName",
		"entryUUID",
		"createTimestamp",
		'structuralObjectClass',
	}

	def __init__(self, src, exclude=OPERATIONAL):
		# type: (Iterable[bytes], Set[str]) -> None
		self.src = src
		self.exclude = exclude
		self.lno = 0

	def next_line(self):
		# type: () -> Iterator[str]
		"""
		Return line iterator.
		"""
		lines = []
		for lno, chunk in enumerate(self.src, start=1):
			line = chunk.decode('utf-8', 'replace')
			line = line.rstrip('\r\n')
			if line[:1] in (' ', '\t'):
				lines.append(line[1:])
			else:
				yield ''.join(lines)
				self.lno = lno
				lines[:] = [line]

		yield ''.join(lines)

	def split(self, line):
		# type: (str) -> Tuple[str, Text]
		r"""
		Split attribute and value.
		Options are stripped.
		Base64 encoded values are decoded.

		:param str line: The line to split.
		:return: A tuple (name, value).

		>>> Ldif(b'').split('a:') == ('a', u'')
		True
		>>> Ldif(b'').split('a: b') == ('a', u'b')
		True
		>>> Ldif(b'').split('a:: YWFh') == ('a', u'aaa')
		True
		>>> Ldif(b'').split('a;b:c') == ('a', u'c')
		True
		>>> Ldif(b'').split('a;b;c::YWFh') == ('a', u'aaa')
		True
		>>> Ldif(b'').split('a:: ACB/') == ('a', u'\\u0000 \\u007f')
		True
		"""
		match = self.RE.match(line)
		if not match:
			raise LdifError('%d: %s' % (self.lno, line))
		oid, attr, _opt, b64, plain = match.groups()
		key = attr or oid
		if plain:
			value = plain
		elif b64:
			value = base64.b64decode(b64).decode('utf-8', 'replace')
			value = self.printable(value)
		else:
			value = ""
		return (key, value)

	def __iter__(self):
		# type: () -> Iterator[Entry]
		"""
		Return line iterator.
		"""
		obj = {}   # type: Entry
		for line in self.next_line():
			if line.startswith('#'):
				continue
			if line:
				key, value = self.split(line)
				if key in self.exclude:
					continue
				obj.setdefault(key, []).append(value)
			elif obj:
				yield obj
				obj = {}

	@staticmethod
	def printable(value):
		# type: (Text) -> Text
		"""
		Convert binary data to printable string.
		"""
		# Py2 has no str.isprintable()
		return u''.join(
			u'\\u%04x' % (ord(c),) if c != u' ' and unicodedata.category(c)[0] in 'CZ' else c
			for c in value
		)


class LdifSource(object):
	@classmethod
	def create(cls, arg, options):
		# type: (str, Values) -> LdifFile
		raise NotImplementedError()

	def start_reading(self):
		# type: () -> Ldif
		"""
		Start reading the LDIF data.
		"""
		raise NotImplementedError()


class LdifFile(object):
	"""
	LDIF source from local file.
	"""

	@classmethod
	def create(cls, arg, options):
		# type: (str, Values) -> LdifFile
		return cls(arg)

	def __init__(self, filename):
		# type: (str) -> None
		super(LdifFile, self).__init__()
		self.filename = filename

	def start_reading(self):
		# type: () -> Ldif
		"""
		Start reading the LDIF data.
		"""
		try:
			return Ldif(open(self.filename, 'rb'))
		except IOError as ex:
			raise LdifError(ex)


class LdifSlapcat(object):
	"""
	LDIF source from local LDAP.
	"""

	@classmethod
	def create(cls, arg, options):
		# type: (Any, Values) -> LdifSlapcat
		return cls()

	def __init__(self):
		# type: () -> None
		super(LdifSlapcat, self).__init__()
		self.command = ['slapcat', '-d0']

	def start_reading(self):
		# type: () -> Ldif
		"""
		Start reading the LDIF data.
		"""
		try:
			proc = subprocess.Popen(self.command, stdout=subprocess.PIPE)
			assert proc.stdout
			self.wait_for_data(proc)
			return Ldif(proc.stdout)
		except OSError as ex:
			raise SlapError("Error executing", self.command, ex)

	def wait_for_data(self, proc):
		# type: (subprocess.Popen) -> None
		"""
		Wait for the remote process to send data.

		>>> LdifSlapcat().wait_for_data(subprocess.Popen(('echo',), stdout=subprocess.PIPE))
		>>> LdifSlapcat().wait_for_data(subprocess.Popen(('false',), stdout=subprocess.PIPE))  # doctest: +IGNORE_EXCEPTION_DETAIL
		Traceback (most recent call last):
		...
		SlapError: ('Error executing', ['slapcat', '-d0'], 1)
		"""
		while True:
			rlist = [proc.stdout]
			wlist = []  # type: List[int]
			xlist = []  # type: List[int]
			try:
				rlist, wlist, xlist = select.select(rlist, wlist, xlist)
				break
			except (OSError, select.error) as ex:
				if ex.errno == errno.EINTR:
					continue
				else:
					raise
		time.sleep(0.5)
		ret = proc.poll()
		if ret is not None and ret != 0:
			raise SlapError("Error executing", self.command, ret)


class LdifSsh(LdifSlapcat):
	"""
	LDIF source from remote LDAP.
	"""

	@classmethod
	def create(cls, hostname, options):
		# type: (str, Values) -> LdifSsh
		return cls(hostname, options.ssh)

	def __init__(self, hostname, ssh='ssh'):
		# type: (str, str) -> None
		super(LdifSsh, self).__init__()
		self.command = [ssh, hostname] + self.command


def __test(_option, _opt_str, _value, _parser):
	# type: (Values, str, None, OptionParser) -> NoReturn
	"""
	Run internal test suite.
	"""
	import doctest
	res = doctest.testmod()
	sys.exit(int(bool(res[0])))


def stream2object(ldif):
	# type: (Ldif) -> Dict[str, Entry]
	"""
	Convert LDIF stream to dictionary of objects.

	:param Ldif ldif: A LDIF stream.
	:return: A dictionary mapping distinguished names to a dictionary of key-values.

	>>> stream2object([{'dn': ['dc=test']}])
	{'dc=test': {}}
	"""
	objects = {}  # type: Dict[str, Entry]
	for obj in ldif:
		try:
			dname, = obj.pop('dn')
			objects[dname] = obj  # type: ignore
		except KeyError:
			print('Missing dn: %r' % (obj,), file=sys.stderr)
		except ValueError:
			print('Multiple dn: %r' % (obj,), file=sys.stderr)
	return objects


def sort_dn(dname):
	# type: (str) -> Tuple[Tuple[str, ...], ...]
	"""
	Sort by reversed dn.

	:param str dname: distinguished name.
	:return: tuple of relative distinguised names.

	>>> sort_dn('a=1')
	(('a=1',),)
	>>> sort_dn('b=1,a=1')
	(('a=1',), ('b=1',))
	>>> sort_dn('b=2+a=1')
	(('a=1', 'b=2'),)
	"""
	return tuple(reversed([tuple(sorted(_.split('+'))) for _ in dname.split(',')]))


def compare_ldif(lldif, rldif, options):
	# type: (Ldif, Ldif, Values) -> int
	"""
	Compare two LDIF files.

	:param ldif1: first LDIF to compare.
	:param ldif2: second LDIF to compare.
	:param options: command line options.
	"""

	lefts = stream2object(lldif)
	rights = stream2object(rldif)

	lkeys = sorted(lefts, key=sort_dn, reverse=True)
	rkeys = sorted(rights, key=sort_dn, reverse=True)

	ret = 0
	ldn = rdn = ""
	while True:
		if not ldn and lkeys:
			ldn = lkeys.pop(0)
		if not rdn and rkeys:
			rdn = rkeys.pop(0)
		if not ldn and not rdn:
			break

		lk, rk = sort_dn(ldn), sort_dn(rdn)
		if lk < rk:
			diffs = list(compare_keys({}, rights[rdn]))
			print('+dn: %s' % (rdn,))
			rdn = ""
		elif lk > rk:
			diffs = list(compare_keys(lefts[ldn], {}))
			print('-dn: %s' % (ldn,))
			ldn = ""
		else:
			diffs = list(compare_keys(lefts[ldn], rights[rdn]))
			if not options.objects and all(diff == 0 for diff, key, val in diffs):
				ldn = rdn = ""
				continue
			print(' dn: %s' % (rdn,))
			ldn = rdn = ""
		for diff, key, val in diffs:
			if options.attributes or diff:
				print('%s%s: %s' % (' +-'[diff], key, val))
		print()
		ret = 1
	return ret


def compare_keys(ldata, rdata):
	# type: (Entry, Entry) -> Iterator[Tuple[Literal[-1, 0, 1], str, Text]]
	"""
	Compare and return attributes of two LDAP objects.

	:param dict ldata: the first LDAP object.
	:param dict rdata: the second LDAP object.
	:return: an iterator of differences as 3-tuples (comparison, key, value).

	>>> list(compare_keys({}, {}))
	[]
	>>> list(compare_keys({'a': ['1']}, {}))
	[(-1, 'a', '1')]
	>>> list(compare_keys({}, {'a': ['1']}))
	[(1, 'a', '1')]
	>>> list(compare_keys({'a': ['1']}, {'a': ['1']}))
	[(0, 'a', '1')]
	>>> list(compare_keys({'a': ['1']}, {'a': ['2']}))
	[(1, 'a', '2'), (-1, 'a', '1')]
	"""
	lkeys = sorted(ldata, reverse=True)
	rkeys = sorted(rdata, reverse=True)

	lkey = rkey = ""
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
			rkey = ""
		elif lkey > rkey:
			for diff in compare_values(lkey, ldata[lkey], []):
				yield diff
			lkey = ""
		else:
			for diff in compare_values(lkey, ldata[lkey], rdata[rkey]):
				yield diff
			lkey = rkey = ""


def compare_values(attr, lvalues, rvalues):
	# type: (str, List[Text], List[Text]) -> Iterator[Tuple[Literal[-1, 0, 1], str, Text]]
	"""
	Compare and return values of two multi-valued LDAP attributes.

	:param list lvalues: the first values.
	:param list rvalues: the second values.
	:return: an iterator of differences as 3-tuples (comparison, key, value), where comparison<0 if key is missing in lvalues, comparison>0 if key is missing in rvalues, otherwise 0.

	>>> list(compare_values('attr', [], []))
	[]
	>>> list(compare_values('attr', ['1', '2'], ['2', '3']))
	[(1, 'attr', '3'), (0, 'attr', '2'), (-1, 'attr', '1')]
	"""
	lvalues.sort(reverse=True)
	rvalues.sort(reverse=True)

	lval = rval = ""
	while True:
		if not lval and lvalues:
			lval = lvalues.pop(0)
		if not rval and rvalues:
			rval = rvalues.pop(0)
		if not lval and not rval:
			break

		if lval < rval:
			yield (1, attr, rval)
			rval = ""
		elif lval > rval:
			yield (-1, attr, lval)
			lval = ""
		else:
			yield (0, attr, lval)
			lval = rval = ""


def parse_args():
	# type: () -> Tuple[LdifSource, LdifSource, Values]
	"""
	Parse command line arguments.
	"""
	parser = OptionParser(usage=USAGE, description=DESCRIPTION)
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
		dest="ssh",
		help="specify the remote shell to use [%default]")
	parser.add_option_group(group)

	group = OptionGroup(parser, "Attributes", "Ignore attributes")
	group.add_option(
		"--operational",
		action="store_true", dest="operational",
		help="also compare operational attributes")
	group.add_option(
		"--exclude", "-x",
		action="append", dest="exclude",
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

	try:
		options, args = parser.parse_args(args=sys.argv[1:])
		try:
			ldif1 = options.source.create(args.pop(0), options)
		except IndexError:
			parser.error("No arguments were given")
		options, args = parser.parse_args(args=args, values=options)
		ldif2 = options.source.create(args.pop(0), options) if args else LdifSlapcat.create(None, options)
		if args:
			parser.error("More than two LDIFs given.")
	except LdifError as ex:
		parser.error("Failed to parse LDIF: %s" % (ex,))

	return ldif1, ldif2, options


def main():
	# type: () -> None
	"""
	A main()-method with options.
	"""
	src1, src2, options = parse_args()

	try:
		ldif1, ldif2 = (src.start_reading() for src in (src1, src2))
	except (LdifError, SlapError) as ex:
		sys.exit("Failed to setup source: %s" % ex)

	exclude = set(options.exclude)
	if not options.operational:
		exclude |= Ldif.OPERATIONAL
	ldif1.exclude = ldif2.exclude = exclude

	run_compare(ldif1, ldif2, options)


def run_compare(ldif1, ldif2, options):
	# type: (Ldif, Ldif, Values) -> NoReturn
	"""
	UNIX correct error handling.
	Termination by signal is propagaed as signal.

	:param ldif1: first LDIF to compare.
	:param ldif2: second LDIF to compare.
	:param options: command line options.
	"""
	ret = 2
	try:
		ret = compare_ldif(ldif1, ldif2, options)
	except KeyboardInterrupt:
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		os.kill(os.getpid(), signal.SIGINT)
	except EnvironmentError as ex:
		if ex.errno == errno.EPIPE:
			signal.signal(signal.SIGPIPE, signal.SIG_DFL)
			os.kill(os.getpid(), signal.SIGPIPE)
		else:
			print('Error: %s' % (ex,), file=sys.stderr)
	except LdifError as ex:
		print('Invalid LDIF: %s' % (ex,), file=sys.stderr)
	sys.exit(ret)


if __name__ == '__main__':
	main()
