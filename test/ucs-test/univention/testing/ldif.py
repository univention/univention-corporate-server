#!/usr/bin/env python
# coding: utf-8

"""
This program compares LDAP host entries with a local comparative ldif file.
All differences will be displayed at the console.
"""

from optparse import OptionParser, OptionGroup, SUPPRESS_HELP
import re
import sys
import subprocess


USAGE = 'usage: %prog [option] LDIF1 [[option] LDIF2]'
DESCRIPTION = '''\
Compares the LDIF files.
LDIF can be:
 a local LDIF file
 a hostname whose LDAP will be dumped using slapcat over ssh.
If LDIF2 is omitted, a local 'slapcat' is used.
'''
VERSION = '%prof 1.0'


class LdifError(Exception):
	"""
	Error in input processing.
	"""
	pass


class LdifSource(object):
	"""
	Abstract class for LDIF source.
	"""
	# RFC2849: LDAP Data Interchange Format
	RE = re.compile(r'''
		^
		(?:
		  ([0-9]+(?:\.[0-9]+)*)	# ldap-oid
		 |([A-Za-z][\-0-9A-Za-z]*)	# AttributeType
		)	# AttributeDescription
		(;[\-0-9A-Za-z]+)*	# OPTIONS
		:
		(?:
		  $	# EMPTY
		 |:[ ]*([+/0-9=A-Za-z]+)	# BASE64-STRING
		 |[ ]*([\x01-\x09\x0b-\x0c\x0e-\x1f\x21-\x39\x3b\x3d-\x7f][\x01-\x09\x0b-\x0c\x0e-\x7f]*)	# SAFE-STRING
		)	# value-spec
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

	def __init__(self, src):
		self.src = src
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
		>>> LdifSource(None).split('')
		>>> LdifSource(None).split('a:')
		('a', None)
		>>> LdifSource(None).split('a: b')
		('a', 'b')
		>>> LdifSource(None).split('a:: YWFh')
		('a', 'aaa')
		>>> LdifSource(None).split('a;b:c')
		('a', 'c')
		>>> LdifSource(None).split('a;b;c::YWFh')
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
	def __init__(self, filename):
		try:
			src = open(filename, 'r+')
		except IOError, ex:
			raise LdifError(ex)
		super(LdifFile, self).__init__(src)


class LdifSlapcat(LdifSource):
	"""
	LDIF source from local LDAP.
	"""
	def __init__(self):
		cmd = ('slapcat', '-d0')
		try:
			proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		except IOError, ex:
			raise LdifError(ex)
		super(LdifSlapcat, self).__init__(proc.stdout)


class LdifSsh(LdifSource):
	"""
	LDIF source from remote LDAP.
	"""
	def __init__(self, hostname):
		cmd = ('ssh', hostname, 'slapcat', '-d0')
		try:
			proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		except IOError, ex:
			raise LdifError(ex)
		super(LdifSsh, self).__init__(proc.stdout)


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
	>>> stream2object([{'dn': ['dc=test']}])
	{'dc=test': {}}
	"""
	objects = {}
	for obj in ldif:
		try:
			dname, = obj.pop('dn')
			objects[dname] = obj
		except KeyError:
			print >> sys.stderr, 'Missing dn: %r' % (obj,)
		except ValueError:
			print >> sys.stderr, 'Multiple dn: %r' % (obj,)
	return objects


def sort_dn(dname):
	"""
	Sort by reversed dn.
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
			print '+dn: %s' % (rdn,)
			rdn = None
		elif order > 0:
			diffs = list(compare_keys(lefts[ldn], {}))
			print '-dn: %s' % (ldn,)
			ldn = None
		else:
			diffs = list(compare_keys(lefts[ldn], rights[rdn]))
			if not options.objects and all((diff == 0 for diff, key, val in diffs)):
				ldn = rdn = None
				continue
			print ' dn: %s' % (rdn,)
			ldn = rdn = None
		for diff, key, val in diffs:
			if options.attributes or diff:
				print '%s%s: %s' % (' +-'[diff], key, val)
		print
		ret = 1
	return ret


def compare_keys(ldata, rdata):
	"""
	Compare attributes of two LDAP objects.
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
	Compare values of two LDAP attributes.
	"""
	lvalues = sorted(lvalues, reverse=True)
	rvalues = sorted(rvalues, reverse=True)

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
	group.add_option("--file", "-f",
			action="store_const", dest="source", const=LdifFile,
			help="Next arguments are LDIF files")
	group.add_option("--host", "-H",
			action="store_const", dest="source", const=LdifSsh,
			help="Next arguments are LDAP hosts")
	parser.add_option_group(group)

	group = OptionGroup(parser, "Attributes", "Ignore attributes")
	group.add_option("--operational",
			action="store_true", dest="operational",
			help="Compare operational attributes")
	group.add_option("--exclude", "-x",
			action="append", dest="exclude", type="string",
			help="Ignore attribute", default=[])
	parser.add_option_group(group)

	group = OptionGroup(parser, "Output", "Control output")
	group.add_option("--objects", "-o",
			action="store_true", dest="objects",
			help="Show even unchanged objects")
	group.add_option("--attributes", "-a",
			action="store_true", dest="attributes",
			help="Show even unchanged attributes")
	parser.add_option_group(group)

	parser.add_option('--test-internal',
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
				ldif = options.source(src)
				sources.append(ldif)
			except LdifError, ex:
				parser.error(ex)

	try:
		ldif1 = sources.pop(0)
	except IndexError:
		parser.error("No arguments were given")
	try:
		ldif2 = sources.pop(0)
	except IndexError:
		ldif2 = LdifSlapcat()
	if sources:
		parser.error("More than two LDIFs given.")

	exclude = set(options.exclude)
	if not options.operational:
		exclude |= LdifSource.OPERATIONAL
	ldif1.exclude = ldif2.exclude = exclude
	try:
		ret = compare_ldif(ldif1, ldif2, options)
	except OSError, ex:
		print >> sys.stderr, 'Error: %s' % (ex,)
		ret = 2
	except LdifError, ex:
		print >> sys.stderr, 'Invalid LDIF: %s' % (ex,)
		ret = 2
	sys.exit(ret)


if __name__ == '__main__':
	main()
