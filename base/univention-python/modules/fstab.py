# -*- coding: utf-8 -*-
#
# Univention Python
"""
Handle parsing and writing /etc/fstab.

See <http://linux.die.net/include/mntent.h>.
"""
#
# Copyright 2002-2019 Univention GmbH
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


class mntent(object):

	"""Structure describing a mount table entry."""

	def __init__(self, fsname, dir, type, opts=None, freq=0, passno=0, comment=None):
		self.fsname = mntent.unquote(fsname)
		self.dir = mntent.unquote(dir)
		self.type = mntent.unquote(type)
		self.opts = mntent.unquote(opts).split(',')
		try:
			self.freq = int(freq)
		except ValueError:
			self.freq = 0
		try:
			self.passno = int(passno)
		except ValueError:
			self.passno = 0
		self.comment = comment

	def __repr__(self):
		"""
		Return the canonical string representation of the object.
		>>> mntent('proc', '/proc', 'proc', 'defaults', 0, 0)
		mntent('proc', '/proc', 'proc', opts='defaults', freq=0, passno=0)
		"""
		h = [
			"%r" % self.fsname,
			"%r" % self.dir,
			"%r" % self.type,
			"opts=%r" % ','.join(self.opts),
			"freq=%d" % self.freq,
			"passno=%d" % self.passno,
		]
		if self.comment:
			h.append("comment=%r" % self.comment)
		return "mntent(%s)" % ', '.join(h)

	def __str__(self, delim='\t'):
		"""
		Return a nice string representation of the object.
		>>> str(mntent('proc', '/proc', 'proc', 'defaults', 0, 0))
		'proc\\t/proc\\tproc\\tdefaults\\t0\\t0'
		>>> str(mntent('/dev/sda', '/', 'ext2,ext3', 'defaults,rw', 0, 0, '# comment'))
		'/dev/sda\\t/\\text2,ext3\\tdefaults,rw\\t0\\t0\\t# comment'
		"""
		h = [
			mntent.quote(self.fsname),
			mntent.quote(self.dir),
			mntent.quote(self.type),
			mntent.quote(','.join(self.opts)),
			str(self.freq),
			str(self.passno),
		]
		if self.comment:
			h.append(self.comment)
		return delim.join(h)

	@classmethod
	def quote(cls, s):
		"""
		Quote string to octal.
		>>> mntent.quote('a b')
		'a\\\\040b'
		"""
		try:
			t = cls.__quote_dict
		except AttributeError:
			t = cls.__quote_dict = dict([(c, '\\%s' % oct(ord(c))) for c in ' \t\n\r\\'])
		return ''.join([t.get(c, c) for c in s])

	@classmethod
	def unquote(cls, s):
		"""
		Unquote octal to string.
		>>> mntent.unquote('a\\040b')
		'a b'
		"""
		try:
			r = cls.__quote_re
		except AttributeError:
			import re
			r = cls.__quote_re = re.compile('\\\\0([0-7]+)')
		return r.sub(lambda m: chr(int(m.group(1), 8)), s)

	def hasopt(self, opt):
		"""
		Search for an option matching OPT.
		>>> mntent('/dev/sda', '/', 'ext3', 'default,ro,user_xattr,acl', 0, 0).hasopt('user')
		['user_xattr']
		"""
		return filter(lambda o: o.startswith(opt), self.opts)


class fstab(object):

	"""Handle parsing and writing /etc/fstab."""

	def __init__(self, fstab='/etc/fstab'):
		self.fn = fstab
		self.__load()

	def __getitem__(self, i):
		"""Get i-th line."""
		return self.__cache[i]

	def __delitem__(self, i):
		"""Remove i-th line."""
		del self.__cache[i]

	def __len__(self):
		"""Return number of entries."""
		return len(self.__cache)

	def __iter__(self):
		"""Get entries."""
		for line in self.__cache:
			if isinstance(line, mntent):
				yield line

	def remove(self, entry):
		"""Remove entry."""
		self.__cache.remove(entry)

	def append(self, entry):
		"""Add entry."""
		self.__cache.append(entry)

	def __load(self):
		"""Load and parse fstab."""
		f = open(self.fn, 'r')
		try:
			self.__cache = []
			for line in f:
				line = line.strip()
				if line.startswith('#'):
					self.__cache.append(line)
				else:
					fields = line.split(None, 6)
					ent = mntent(*fields)
					self.__cache.append(ent)
		finally:
			f.close()

	def save(self, fn=None):
		"""Save new fstab."""
		f = open(fn or self.fn, 'w')
		try:
			for line in self.__cache:
				f.write("%s\n" % line)
		finally:
			f.close()


if __name__ == '__main__':
	import doctest
	doctest.testmod()

	import tempfile
	fd, name = tempfile.mkstemp()
	import os
	os.write(fd, """# /etc/fstab: static file system information.
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
/dev/vda3       /       ext3    acl,errors=remount-ro   0       1
proc            /proc           proc    defaults        0       0
/dev/vda1  /boot        ext3    defaults,acl    0       0
/dev/vda2  none         swap    sw 0    0
192.168.0.81:/home             /home           nfs     defaults,timeo=21,retrans=9,wsize=8192,rsize=8192,nfsvers=3     1       2	# LDAP""")
	fs = fstab(name)
	assert fs[6].comment == '# LDAP'
