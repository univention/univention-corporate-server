#!/usr/bin/python3
# SPDX-FileCopyrightText: 2006-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Handle parsing and writing :file:`/etc/fstab`.

See <http://linux.die.net/include/mntent.h>.
"""


import os
import re
from collections.abc import Container  # noqa: F401


class InvalidEntry(Exception):
    """Invalid entry in file system table"""


class File(list):
    """
    Handle lines of :file:`/etc/fstab`.

    :param str file: The name of the file.
    """

    _is_comment = re.compile('[ \t]*#').search
    _filesystems = ('ext2', 'xfs', 'nfs', 'proc', 'auto', 'swap')

    def __init__(self, file='/etc/fstab'):
        # type: (str) -> None
        list.__init__(self)
        self.__file = file
        self.load()

    def load(self):
        # type: () -> None
        """Load entries from file."""
        with open(self.__file) as fd:
            for _line in fd:
                line = self.__parse(_line)
                if not isinstance(line, Entry) and _line.strip() and not _line.strip().startswith('#'):
                    raise InvalidEntry('The following is not a valid fstab entry: %r' % (_line,))  # TODO:
                self.append(line)

    def find(self, **kargs):
        # type: (**str) -> Optional[Entry]
        """
        Search and return the entry matching the criteria.

        :param kwargs: A mapping of :py:class:`Entry` attributes to values.
        :returns: The first entry matching all criteria or `None`.
        :rtype: Entry or None
        """
        for entry in self:
            found = True
            for arg, value in kargs.items():
                if not hasattr(entry, arg) or getattr(entry, arg) != value:
                    found = False
                    break
            if found:
                return entry
        return None

    def get(self, filesystem=[], ignore_root=True):
        # type: (Container[str], bool) -> List[Entry]
        """
        Return list of entries matching a list of file system types.

        :param filesystem: A list of file system names.
        :type filesystem: List[str]
        :param bool ignore_root: Skip the root file system if `True`.
        :returns: A list of matching entries.
        :rtype: List[Entry]
        """
        result = []
        for entry in self:
            if isinstance(entry, str):
                continue
            if ignore_root and entry.mount_point == '/':
                continue
            if not filesystem or entry.type in filesystem:
                result.append(entry)
        return result

    def save(self, filename=None):
        # type: (Optional[str]) -> None
        """Save entries to file."""
        with open(filename or self.__file, 'w') as fd:
            fd.writelines('%s\n' % (line,) for line in self)

    def __parse(self, line):
        # type: (str) -> Union[Entry, str]
        """
        Parse file system table line.

        1. `fs_spec`
        2. `fs_file`
        3. `fs_vfstype`
        4. `fs_mntops`
        5. `fs_freq`
        6. `fs_passno`

        :param str line: A line.
        :returns: The parsed entry or a string with the raw contents if the entry is invalid.
        :rtype: Entry
        :raises InvalidEntry: if the line cannot be parsed.
        """
        line = line.lstrip().rstrip('\n')
        if line.startswith('#') or not line.strip():
            return line

        line, has_comment, comment = line.partition('#')
        fields = line.split(None, 5)
        rem = has_comment + comment if has_comment or line.endswith('\t') else None
        if len(fields) < 3 or (len(fields) < 6 and rem):
            return line + has_comment + comment

        return Entry(*fields, comment=rem)  # type: ignore


class Entry:
    """
    Mount table entry of :manpage:`fstab(5)`.

    :param str spec: This field describes the block special device or remote filesystem to be mounted.
    :param str mount_point: This field describes the mount point (target) for the filesystem.
    :param str type: The type of the filesystem.
    :param options: The list of mount options associated with the filesystem.
    :type options: List[str]
    :param int dump: Option for :manpage:`dump(8)`.
    :param int passno: Order information for `fsck(8)`.
    :param str comment: Optional comment from end of line.

    :ivar str uuid: The file system |UUID| if the file system is mounted by it. Otherwise `None`.
    """

    _quote_dict = {c: r'\%s' % oct(ord(c)) for c in ' \t\n\r\\'}
    _quote_re = re.compile(r'\\0([0-7]+)')

    def __init__(self, spec, mount_point, fs_type, options='', dump=None, passno=None, comment=None):
        # type: (str, str, str, Union[str,list], Optional[str], Optional[str], Optional[str]) -> None
        self.spec = self.unquote(spec.strip())
        if self.spec.startswith('UUID='):
            self.uuid = self.spec[5:]  # type: Optional[str]
            uuid_dev = os.path.join('/dev/disk/by-uuid', self.uuid)
            if os.path.exists(uuid_dev):
                self.spec = os.path.realpath(uuid_dev)
        else:
            self.uuid = None
        self.mount_point = self.unquote(mount_point.strip())
        self.type = self.unquote(fs_type.strip())
        self.options = self.unquote(options).split(',') if options and not isinstance(options, list) else (options or [])
        self.dump = int(dump) if dump is not None else None
        self.passno = int(passno) if passno is not None else None
        self.comment = comment

    def __str__(self, delim='\t'):
        # type: (str) -> str
        """
        Return the canonical string representation of the object.
        >>> str(Entry('proc', '/proc', 'proc', comment="#the comment"))
        >>> str(Entry('proc', '/proc', 'proc', 'defaults', 0, 0))
        'proc\\t/proc\\tproc\\tdefaults\\t0\\t0'
        >>> str(Entry('/dev/sda', '/', 'ext2,ext3', 'defaults,rw', 0, 0, '# comment'))
        '/dev/sda\\t/\\text2,ext3\\tdefaults,rw\\t0\\t0\\t# comment'
        """
        # If a line has a comment or any next field is non-empty, all previous one needs to be set
        h = [
            self.quote('UUID=%s' % self.uuid if self.uuid else self.spec),
            self.quote(self.mount_point),
            self.quote(self.type),
            self.quote(','.join(self.options or (['defaults'] if any([self.dump, self.passno, self.comment]) else []))) or None,
            str(self.dump or 0) if isinstance(self.dump, int) or any([self.passno, self.comment]) else self.dump,
            str(self.passno or 0) if isinstance(self.passno, int) or any([self.comment]) else self.passno,
            self.comment,
        ]
        return delim.join(e for e in h if e is not None)

    def __repr__(self):
        # type: () -> str
        """
        >>> Entry('proc', '/proc', 'proc', 'defaults', 0, 0)
        univention.lib.fstab.Entry('proc', '/proc', 'proc', options='defaults', freq=0, passno=0)
        """
        h = [
            "%r" % self.spec,
            "%r" % self.mount_point,
            "%r" % self.type,
            "options=%r" % ','.join(self.options),
            "freq=%r" % self.dump,
            "passno=%r" % self.passno,
        ]
        if self.comment is not None:
            h.append("comment=%r" % self.comment)
        return "univention.lib.fstab.Entry(%s)" % ', '.join(h)

    @classmethod
    def quote(cls, s):
        # type: (str) -> str
        """
        Quote string to octal.

        >>> Entry.quote('a b')
        'a\\\\040b'
        """
        return ''.join([cls._quote_dict.get(c, c) for c in s])

    @classmethod
    def unquote(cls, s):
        # type: (str) -> str
        """
        Unquote octal to string.

        >>> Entry.unquote('a\\040b')
        'a b'
        """
        return cls._quote_re.sub(lambda m: chr(int(m.group(1), 8)), s)

    def hasopt(self, opt):
        # type: (str) -> List[str]
        """
        Search for an option matching OPT.

        >>> Entry('/dev/sda', '/', 'ext3', 'default,ro,user_xattr,acl', 0, 0).hasopt('user')
        ['user_xattr']
        """
        return [o for o in self.options if o.startswith(opt)]


if __name__ == '__main__':
    import doctest
    doctest.testmod()
