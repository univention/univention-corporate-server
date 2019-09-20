# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for share objects
#
# Copyright 2004-2019 Univention GmbH
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

import re
from ldap.filter import filter_format

from univention.admin.layout import Tab, Group
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.shares')
_ = translation.translate


class cscPolicy(univention.admin.syntax.select):
	name = 'cscPolicy'
	choices = [('manual', _('manual')), ('documents', _('documents')), ('programs', _('programs')), ('disable', _('disable'))]


module = 'shares/share'
operations = ['add', 'edit', 'remove', 'search', 'move']

childs = 0
short_description = _('Share: Directory')
object_name = _('Share directory')
object_name_plural = _('Share directories')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionShare'],
	),
	'samba': univention.admin.option(
		short_description=_('Export for Samba clients'),
		editable=True,
		default=1,
		objectClasses=('univentionShareSamba',),
	),
	'nfs': univention.admin.option(
		short_description=_('Export for NFS clients (NFSv3 and NFSv4)'),
		editable=True,
		default=1,
		objectClasses=('univentionShareNFS',),
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('Name of the share'),
		syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'printablename': univention.admin.property(
		short_description=_('Printable name'),
		long_description=_('Printable name'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'host': univention.admin.property(
		short_description=_('Host'),
		long_description=_('The computer that exports this share'),
		syntax=univention.admin.syntax.UCS_Server,
		include_in_default_search=True,
		required=True,
	),
	'path': univention.admin.property(
		short_description=_('Directory'),
		long_description=_('Directory that is exported.'),
		syntax=univention.admin.syntax.sharePath,
		required=True,
	),
	'owner': univention.admin.property(
		short_description=_('Directory owner of the share\'s root directory'),
		long_description=_('The owner of the exported root directory. If none is given root will be owner.'),
		syntax=univention.admin.syntax.UserID,
		default="0"
	),
	'group': univention.admin.property(
		short_description=_('Directory owner group of the share\'s root directory'),
		long_description=_('The primary group of the exported root directory, if none is given group 0 will be used.'),
		syntax=univention.admin.syntax.GroupID,
		default="0"
	),
	'directorymode': univention.admin.property(
		short_description=_('Permissions for the share\'s root directory'),
		long_description=_('Access rights to the exported root directory'),
		syntax=univention.admin.syntax.UNIX_AccessRight_extended,
		dontsearch=True,
		default="00755"
	),
	'writeable': univention.admin.property(
		short_description=_('NFS write access'),
		long_description=_('Define if the share is writable when accessed via NFS.'),
		syntax=univention.admin.syntax.boolean,
		options=['nfs'],
		default='1',
		size='Half',
	),
	'sync': univention.admin.property(
		short_description=_('NFS synchronisation'),
		long_description=_('Use synchronous or asynchronous mode for the NFS share.'),
		syntax=univention.admin.syntax.nfssync,
		options=['nfs'],
		default='sync',
		size='Half',
	),
	'subtree_checking': univention.admin.property(
		short_description=_('Subtree checking'),
		long_description=_('When only a subtree of a mounted filesystem is exported this option ensures that an accessed file really is in that subtree. (May cause complications with renamed files.)'),
		syntax=univention.admin.syntax.boolean,
		options=['nfs'],
		default='1',
		size='Two',
	),
	'root_squash': univention.admin.property(
		short_description=_('Modify user ID for root user (root squashing)'),
		long_description=_('Redirect root user access to a non-privileged uid.'),
		syntax=univention.admin.syntax.boolean,
		options=['nfs'],
		default='1',
		size='Two',
	),
	'nfs_hosts': univention.admin.property(
		short_description=_('Only allow access for this host, IP address or network'),
		long_description=_('May contain hostnames, IP addresses or networks (e.g. 10.1.1.1/24 or 10.1.1.1/255.255.255.0'),
		syntax=univention.admin.syntax.hostname_or_ipadress_or_network,
		multivalue=True,
		options=['nfs'],
	),
	'sambaWriteable': univention.admin.property(
		short_description=_('Samba write access'),
		long_description=_('Define if the share is writable when accessed via Samba.'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='1',
		size='One',
	),
	'sambaName': univention.admin.property(
		short_description=_('Windows name'),
		long_description=_('This is the NetBIOS name. Among other places, it appears in the Windows Network Neighborhood.'),
		syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
		options=['samba'],
		default='<name>',
	),
	'sambaBrowseable': univention.admin.property(
		short_description=_('Show in Windows network environment'),
		long_description=_('Share is browseable, i.e. it is listed in the Windows network environment'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='1',
		size='One',
	),
	'sambaPublic': univention.admin.property(
		short_description=_('Allow anonymous read-only access with a guest user'),
		long_description=_('Allow guest access'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='0',
		size='One',
	),
	'sambaDosFilemode': univention.admin.property(
		short_description=_('Users with write access may modify permissions'),
		long_description=_('Users who have write access to a file or directory are able to change the permissions '),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='0',
		size='One',
	),
	'sambaHideUnreadable': univention.admin.property(
		short_description=_('Hide unreadable files/directories'),
		long_description=_('Files and directories with no read access are hidden. New files and directories receive permissions of the superordinate directory.'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='0',
		size='One',
	),
	'sambaCreateMode': univention.admin.property(
		short_description=_('File mode'),
		long_description=_('When a file is created, the necessary permissions are calculated according to the mapping from DOS modes to UNIX permissions, and the resulting UNIX mode is then bit-wise \'AND\'ed with this parameter. This parameter may be thought of as a bit-wise MASK for the UNIX modes of a file. Any bit not set here will be removed from the modes set on a file when it is created.'),
		syntax=univention.admin.syntax.UNIX_AccessRight,
		options=['samba'],
		dontsearch=True,
		default='0744'
	),
	'sambaDirectoryMode': univention.admin.property(
		short_description=_('Directory mode'),
		long_description=_('When a directory is created, the necessary permissions are calculated  according to the mapping from DOS modes to UNIX permissions, and the resulting UNIX mode is then bit-wise \'AND\'ed with this parameter. This parameter may be thought of as a bit-wise MASK for the UNIX modes of a directory. Any bit not set here will be removed from the modes set on a directory when it is created.'),
		syntax=univention.admin.syntax.UNIX_AccessRight,
		options=['samba'],
		dontsearch=True,
		default='0755'
	),
	'sambaForceCreateMode': univention.admin.property(
		short_description=_('Force file mode'),
		long_description=_('This parameter specifies a set of UNIX mode bit permissions that will always be set on a file created by Samba. This is done by bitwise \'OR\'ing these bits onto the mode bits of a file that is being created or having its permissions changed. The modes in this parameter are bitwise \'OR\'ed onto the file mode after the mask set in the create mask parameter is applied.'),
		syntax=univention.admin.syntax.UNIX_AccessRight,
		options=['samba'],
		dontsearch=True,
		default='0'
	),
	'sambaForceDirectoryMode': univention.admin.property(
		short_description=_('Force directory mode'),
		long_description=_('This parameter specifies a set of UNIX mode bit permissions that will always be set on a directory created by Samba. This is done by bitwise \'OR\'ing these bits onto the mode bits of a directory that is being created or having its permissions changed. The modes in this parameter are bitwise \'OR\'ed onto the directory mode after the mask set in the create mask parameter is applied.'),
		syntax=univention.admin.syntax.UNIX_AccessRight,
		options=['samba'],
		dontsearch=True,
		default='0'
	),
	'sambaSecurityMode': univention.admin.property(
		short_description=_('Security mode'),
		long_description=_('This parameter controls what UNIX permission bits can be modified when an SMB client is manipulating the UNIX permission on a file using the native Windows security dialog box. This parameter is applied as a mask (AND\'ed with) to the changed permission bits, thus preventing any bits not in this mask from being modified. Essentially, zero bits in this mask may be treated as a set of bits the user is not allowed to change.'),
		syntax=univention.admin.syntax.UNIX_AccessRight,
		options=['samba'],
		dontsearch=True,
		default='0777'
	),
	'sambaDirectorySecurityMode': univention.admin.property(
		short_description=_('Directory security mode'),
		long_description=_('This parameter controls what UNIX permission bits can be modified when an SMB client is manipulating the UNIX permission on a directory using the native Windows security dialog box. This parameter is applied as a mask (AND\'ed with) to the changed permission bits, thus preventing any bits not in this mask from being modified. Essentially, zero bits in this mask may be treated as a set of bits the user is not allowed to change.'),
		syntax=univention.admin.syntax.UNIX_AccessRight,
		options=['samba'],
		dontsearch=True,
		default='0777'
	),
	'sambaForceSecurityMode': univention.admin.property(
		short_description=_('Force security mode'),
		long_description=_('This parameter controls what UNIX permission bits can be modified when an SMB client is manipulating the UNIX permission on a file using the native Windows security dialog box. This parameter is applied as a mask (OR\'ed with) to the changed permission bits, thus forcing any bits in this mask that the user may have modified to be on. Essentially, one bits in this mask may be treated as a set of bits that, when modifying security on a file, the user has always set to be \'on\'.'),
		syntax=univention.admin.syntax.UNIX_AccessRight,
		options=['samba'],
		dontsearch=True,
		default='0'
	),
	'sambaForceDirectorySecurityMode': univention.admin.property(
		short_description=_('Force directory security mode'),
		long_description=_('This parameter controls what UNIX permission bits can be modified when an SMB client is manipulating the UNIX permission on a directory using the native Windows security dialog box. This parameter is applied as a mask (OR\'ed with) to the changed permission bits, thus forcing any bits in this mask that the user may have modified to be on. Essentially, one bits in this mask may be treated as a set of bits that, when modifying security on a directory, the user has always set to be \'on\'.'),
		syntax=univention.admin.syntax.UNIX_AccessRight,
		options=['samba'],
		dontsearch=True,
		default='0'
	),
	'sambaLocking': univention.admin.property(
		short_description=_('Locking'),
		long_description=_('This controls whether or not locking will be performed by the server in response to lock requests from the client. Be careful about disabling locking, as lack of locking may result in data corruption.'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='1',
		size='Half',
	),
	'sambaBlockingLocks': univention.admin.property(
		short_description=_('Blocking locks'),
		long_description=_('This parameter controls the behavior of Samba when given a request by a client to obtain a byte range lock on a region of an open file, and the request has a time limit associated with it. If this parameter is set and the lock range requested cannot be immediately satisfied, samba will internally queue the lock request, and periodically attempt to obtain the lock until the timeout period expires.'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='1',
		size='Half',
	),
	'sambaStrictLocking': univention.admin.property(
		short_description=_('Strict locking'),
		long_description=_('This value controls the handling of file locking in the server. If strict locking is set to Auto (the default), the server performs file lock checks only on non-oplocked files. As most Windows redirectors perform file locking checks locally on oplocked files this is a good trade-off for improved performance. If set to yes, the server will check every read and write access for file locks, and deny access if locks exist. This can be slow on some systems. If strict locking is disabled, the server performs file lock checks only if the client explicitly asks for them.'),
		syntax=univention.admin.syntax.auto_one_zero,
		options=['samba'],
		default='Auto'
	),
	'sambaOplocks': univention.admin.property(
		short_description=_('Oplocks'),
		long_description=_('This boolean option tells Samba whether to issue oplocks (opportunistic locks) to file open requests on this share. The oplock code can dramatically (approx. 30% or more) improve the speed of access to files on Samba servers. It allows the clients to aggressively cache files locally and you may want to disable this option for unreliable network environments (it is turned on by default in Windows Servers).'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='1',
		size='Half',
	),
	'sambaLevel2Oplocks': univention.admin.property(
		short_description=_('Level 2 oplocks'),
		long_description=_('This parameter controls whether Samba supports level2 (read-only) oplocks on a share. Level2, or read-only oplocks allow SMB clients that have an oplock on a file to downgrade from a read-write oplock to a read-only oplock once a second client opens the file (instead of releasing all oplocks on a second open, as in traditional, exclusive oplocks). This allows all openers of the file that support level2 oplocks to cache the file for read-ahead only (ie. they may not cache writes or lock requests) and increases performance for many accesses of files that are not commonly written (such as application .EXE files). Once one of the clients which have a read-only oplock writes to the file all clients are notified (no  reply  is  needed or waited for) and told to break their oplocks to "none" and delete any read-ahead caches. It is recommended that this parameter be turned on to speed access to shared executables.'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='1',
		size='Half',
	),
	'sambaFakeOplocks': univention.admin.property(
		short_description=_('Fake oplocks'),
		long_description=_('Oplocks are the way that Samba clients get permission from a server to locally cache file operations.  If a server grants an oplock (opportunistic lock) then the client is free to assume that it is the only one accessing the file and it will aggressively cache file data. With some  oplock  types the client may even cache file open/close operations. This can give enormous performance benefits. When you activate this parameter, Samba will always grant oplock requests no matter how many clients are using the file. It is generally much better to use the real oplocks support rather than this parameter. If you enable this option on all read-only shares or shares that you know will only be accessed from one client at a time such as physically read-only media like CDROMs, you will see a big performance improvement on many operations. If you enable this option on shares where multiple clients may be accessing the files read-write at the same  time you can get data corruption. Use this option carefully!'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='0',
		size='Half',
	),
	'sambaBlockSize': univention.admin.property(
		short_description=_('Block size'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		options=['samba'],
	),
	'sambaCscPolicy': univention.admin.property(
		short_description=_('Client-side caching policy'),
		long_description=_('The way clients capable of offline caching will cache the files in the share.'),
		syntax=cscPolicy,
		options=['samba'],
		default='manual'
	),
	'sambaHostsAllow': univention.admin.property(
		short_description=_('Allowed host/network'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=['samba'],
	),
	'sambaHostsDeny': univention.admin.property(
		short_description=_('Denied host/network'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=['samba'],
	),
	'sambaValidUsers': univention.admin.property(
		short_description=_('Valid users or groups'),
		long_description='',
		syntax=univention.admin.syntax.string,
		options=['samba'],
	),
	'sambaInvalidUsers': univention.admin.property(
		short_description=_('Invalid users or groups'),
		long_description='',
		syntax=univention.admin.syntax.string,
		options=['samba'],
	),
	'sambaForceUser': univention.admin.property(
		short_description=_('Force user'),
		long_description=_('This specifies a UNIX user name that will be assigned as the default user for all users connecting to this service. This is useful for sharing files. You should also use it carefully as using it incorrectly can cause security problems.'),
		syntax=univention.admin.syntax.string,
		options=['samba'],
	),
	'sambaForceGroup': univention.admin.property(
		short_description=_('Force group'),
		long_description=_('This specifies a UNIX group name that will be assigned as the default primary group for all users connecting to this service. This is useful for sharing files by ensuring that all access to files on the service will use the named group for their permissions checking. Thus, by assigning permissions for this group to the files and directories within this service the Samba administrator can restrict or allow sharing of these files.'),
		syntax=univention.admin.syntax.string,
		options=['samba'],
	),
	'sambaHideFiles': univention.admin.property(
		short_description=_('Hide files'),
		long_description='',
		syntax=univention.admin.syntax.string,
		options=['samba'],
	),
	'sambaNtAclSupport': univention.admin.property(
		short_description=_('NT ACL support'),
		long_description=_('This boolean parameter controls whether Samba will attempt to map UNIX permissions into Windows NT access control lists.'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='1',
		size='Half',
	),
	'sambaInheritAcls': univention.admin.property(
		short_description=_('Inherit ACLs'),
		long_description=_('This parameter can be used to ensure that if default ACLs exist on parent directories, they are always honored when creating a subdirectory. The default behavior is to use the mode specified when creating the directory. Enabling this option sets the mode to 0777, thus guaranteeing that default directory ACLs are propagated.'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='1',
		size='Half',
	),
	'sambaPostexec': univention.admin.property(
		short_description=_('Postexec script'),
		long_description=_('This option specifies a command to be run whenever the service is disconnected. It takes the usual substitutions.'),
		syntax=univention.admin.syntax.string,
		options=['samba'],
	),
	'sambaPreexec': univention.admin.property(
		short_description=_('Preexec script'),
		long_description=_('This option specifies a command to be run whenever the service is connected to. It takes the usual substitutions.'),
		syntax=univention.admin.syntax.string,
		options=['samba'],
	),
	'sambaWriteList': univention.admin.property(
		short_description=_('Restrict write access to these users/groups'),
		long_description='',
		syntax=univention.admin.syntax.string,
		options=['samba'],
	),
	'sambaVFSObjects': univention.admin.property(
		short_description=_('VFS objects'),
		long_description=_('Specifies which VFS Objects to use.'),
		syntax=univention.admin.syntax.string,
		options=['samba'],
	),
	'sambaMSDFSRoot': univention.admin.property(
		short_description=_('MSDFS root'),
		long_description=_('Export share as MSDFS root. Please consult the "Fileshare management" chapter in the manual for more information'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='0',
		size='One',
	),
	'sambaInheritOwner': univention.admin.property(
		short_description=_('Create files/directories with the owner of the parent directory'),
		long_description=_('Ownership for new files and directories is controlled by the ownership of the parent directory.'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='0',
		size='Two',
	),
	'sambaInheritPermissions': univention.admin.property(
		short_description=_('Create files/directories with permissions of the parent directory'),
		long_description=_('New files and directories inherit the mode of the parent directory.'),
		syntax=univention.admin.syntax.boolean,
		options=['samba'],
		default='0',
		size='Two',
	),
	'sambaCustomSettings': univention.admin.property(
		short_description=_('Option name in smb.conf and its value'),
		long_description=_('Configure additional smb.conf settings for this share, which are added in the form key = value'),
		syntax=univention.admin.syntax.keyAndValue,
		multivalue=True,
		options=['samba'],
	),
	'nfsCustomSettings': univention.admin.property(
		short_description=_('Option name in exports file'),
		long_description=_('Configure additional settings for this share which are added to the /etc/exports file.'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=['nfs'],
	),
}

layout = [
	Tab(_('General'), _('General settings'), layout=[
		Group(_('General directory share settings'), layout=[
			'name',
			['host', 'path'],
			['owner', 'group'],
			'directorymode'
		]),
	]),
	Tab(_('NFS'), _('General NFS settings'), layout=[
		Group(_('NFS'), layout=[
			'writeable',
			'subtree_checking',
			'root_squash',
			'sync',
			'nfs_hosts',
		]),
	]),
	Tab(_('Samba'), _('General Samba settings'), layout=[
		Group(_('Samba'), layout=[
			'sambaName',
			'sambaWriteable',
			'sambaBrowseable',
			'sambaPublic',
			'sambaMSDFSRoot',
			'sambaDosFilemode',
			'sambaHideUnreadable',
			'sambaVFSObjects',
		]),
	]),
	Tab(_('Samba permissions'), _('Samba permission settings'), advanced=True, layout=[
		['sambaForceUser', 'sambaForceGroup'],
		['sambaValidUsers', 'sambaInvalidUsers'],
		['sambaWriteList'],
		['sambaHostsAllow', 'sambaHostsDeny'],
		['sambaNtAclSupport', 'sambaInheritAcls'],
		['sambaInheritOwner', 'sambaInheritPermissions'],
	]),
	Tab(_('Samba extended permissions'), _('Samba extended permission settings'), advanced=True, layout=[
		['sambaCreateMode', 'sambaDirectoryMode'],
		['sambaForceCreateMode', 'sambaForceDirectoryMode'],
		['sambaSecurityMode', 'sambaDirectorySecurityMode'],
		['sambaForceSecurityMode', 'sambaForceDirectorySecurityMode'],
	]),
	Tab(_('Samba options'), _('Samba options'), advanced=True, layout=[
		['sambaLocking', 'sambaBlockingLocks'],
		['sambaStrictLocking'],
		['sambaOplocks', 'sambaLevel2Oplocks', 'sambaFakeOplocks'],
		['sambaBlockSize', 'sambaCscPolicy'],
		['sambaHideFiles'],
		['sambaPostexec', 'sambaPreexec'],
	]),
	Tab(_('Samba custom settings'), _('Custom settings for Samba shares'), advanced=True, layout=[
		'sambaCustomSettings'
	]),
	Tab(_('NFS custom settings'), _('Custom settings for NFS shares'), advanced=True, layout=[
		'nfsCustomSettings'
	]),
]


def boolToString(value):
	if value == '1':
		return 'yes'
	else:
		return 'no'


def stringToBool(value):
	if value[0].lower() == 'yes':
		return '1'
	else:
		return '0'


def mapKeyAndValue(old):
	return [' = '.join(entry) for entry in old]


def unmapKeyAndValue(old):
	return [entry.split(' = ', 1) for entry in old]


def insertQuotes(value):
	'Turns @group name, user name into @"group name", "user name"'

	new_entries = []
	for entry in value.split(","):
		new_entry = entry.strip()
		if not new_entry:
			continue
		if new_entry.startswith("@"):
			is_group = True
			new_entry = new_entry[1:].strip()
		else:
			is_group = False
		if ' ' in new_entry:
			new_entry = '"%s"' % new_entry
		if is_group:
			new_entry = "@%s" % new_entry
		new_entries.append(new_entry)
	return ', '.join(new_entries)


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('host', 'univentionShareHost', None, univention.admin.mapping.ListToString)
mapping.register('path', 'univentionSharePath', None, univention.admin.mapping.ListToString)
mapping.register('owner', 'univentionShareUid', None, univention.admin.mapping.ListToString)
mapping.register('group', 'univentionShareGid', None, univention.admin.mapping.ListToString)
mapping.register('directorymode', 'univentionShareDirectoryMode', None, univention.admin.mapping.ListToString)
mapping.register('writeable', 'univentionShareWriteable', boolToString, stringToBool)
mapping.register('sync', 'univentionShareNFSSync', None, univention.admin.mapping.ListToString)
mapping.register('nfs_hosts', 'univentionShareNFSAllowed')
mapping.register('root_squash', 'univentionShareNFSRootSquash', boolToString, stringToBool)
mapping.register('subtree_checking', 'univentionShareNFSSubTree', boolToString, stringToBool)
mapping.register('sambaName', 'univentionShareSambaName', None, univention.admin.mapping.ListToString)
mapping.register('sambaBrowseable', 'univentionShareSambaBrowseable', boolToString, stringToBool)
mapping.register('sambaPublic', 'univentionShareSambaPublic', boolToString, stringToBool)
mapping.register('sambaDosFilemode', 'univentionShareSambaDosFilemode', boolToString, stringToBool)
mapping.register('sambaHideUnreadable', 'univentionShareSambaHideUnreadable', boolToString, stringToBool)
mapping.register('sambaCreateMode', 'univentionShareSambaCreateMode', None, univention.admin.mapping.ListToString)
mapping.register('sambaDirectoryMode', 'univentionShareSambaDirectoryMode', None, univention.admin.mapping.ListToString)
mapping.register('sambaForceCreateMode', 'univentionShareSambaForceCreateMode', None, univention.admin.mapping.ListToString)
mapping.register('sambaForceDirectoryMode', 'univentionShareSambaForceDirectoryMode', None, univention.admin.mapping.ListToString)
mapping.register('sambaSecurityMode', 'univentionShareSambaSecurityMode', None, univention.admin.mapping.ListToString)
mapping.register('sambaDirectorySecurityMode', 'univentionShareSambaDirectorySecurityMode', None, univention.admin.mapping.ListToString)
mapping.register('sambaForceSecurityMode', 'univentionShareSambaForceSecurityMode', None, univention.admin.mapping.ListToString)
mapping.register('sambaForceDirectorySecurityMode', 'univentionShareSambaForceDirectorySecurityMode', None, univention.admin.mapping.ListToString)
mapping.register('sambaLocking', 'univentionShareSambaLocking', None, univention.admin.mapping.ListToString)
mapping.register('sambaBlockingLocks', 'univentionShareSambaBlockingLocks', None, univention.admin.mapping.ListToString)
mapping.register('sambaStrictLocking', 'univentionShareSambaStrictLocking', None, univention.admin.mapping.ListToString)
mapping.register('sambaOplocks', 'univentionShareSambaOplocks', None, univention.admin.mapping.ListToString)
mapping.register('sambaLevel2Oplocks', 'univentionShareSambaLevel2Oplocks', None, univention.admin.mapping.ListToString)
mapping.register('sambaFakeOplocks', 'univentionShareSambaFakeOplocks', None, univention.admin.mapping.ListToString)
mapping.register('sambaBlockSize', 'univentionShareSambaBlockSize', None, univention.admin.mapping.ListToString)
mapping.register('sambaCscPolicy', 'univentionShareSambaCscPolicy', None, univention.admin.mapping.ListToString)
mapping.register('sambaValidUsers', 'univentionShareSambaValidUsers', None, univention.admin.mapping.ListToString)
mapping.register('sambaInvalidUsers', 'univentionShareSambaInvalidUsers', None, univention.admin.mapping.ListToString)
mapping.register('sambaHostsAllow', 'univentionShareSambaHostsAllow')
mapping.register('sambaHostsDeny', 'univentionShareSambaHostsDeny')
mapping.register('sambaForceUser', 'univentionShareSambaForceUser', None, univention.admin.mapping.ListToString)
mapping.register('sambaForceGroup', 'univentionShareSambaForceGroup', None, univention.admin.mapping.ListToString)
mapping.register('sambaHideFiles', 'univentionShareSambaHideFiles', None, univention.admin.mapping.ListToString)
mapping.register('sambaNtAclSupport', 'univentionShareSambaNtAclSupport', None, univention.admin.mapping.ListToString)
mapping.register('sambaInheritAcls', 'univentionShareSambaInheritAcls', None, univention.admin.mapping.ListToString)
mapping.register('sambaPostexec', 'univentionShareSambaPostexec', None, univention.admin.mapping.ListToString)
mapping.register('sambaPreexec', 'univentionShareSambaPreexec', None, univention.admin.mapping.ListToString)
mapping.register('sambaWriteable', 'univentionShareSambaWriteable', boolToString, stringToBool)
mapping.register('sambaWriteList', 'univentionShareSambaWriteList', insertQuotes, univention.admin.mapping.ListToString)
mapping.register('sambaVFSObjects', 'univentionShareSambaVFSObjects', None, univention.admin.mapping.ListToString)
mapping.register('sambaMSDFSRoot', 'univentionShareSambaMSDFS', boolToString, stringToBool)
mapping.register('sambaInheritOwner', 'univentionShareSambaInheritOwner', boolToString, stringToBool)
mapping.register('sambaInheritPermissions', 'univentionShareSambaInheritPermissions', boolToString, stringToBool)
mapping.register('sambaCustomSettings', 'univentionShareSambaCustomSetting', mapKeyAndValue, unmapKeyAndValue)
mapping.register('nfsCustomSettings', 'univentionShareNFSCustomSetting')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		if 'objectClass' in self.oldattr:
			try:
				# Attention: Because of performance reasons, the syntax
				#   class nfsShare uses '%(name)s (%(host)s)' as label, not
				#   '%(printablename)s' (may be looked up in ldap directly).
				#   If you change printablename here you probably want to change
				#   nfsShare.label, too.
				self['printablename'] = "%s (%s)" % (self['name'], self['host'])
			except:
				pass

		self.save()

	def _ldap_addlist(self):
		# TODO: move this validation into a syntax class
		dirBlackList = ["sys", "proc", "dev"]
		for dir in dirBlackList:
			if re.match("^/%s$|^/%s/" % (dir, dir), self['path']):
				raise univention.admin.uexceptions.invalidOperation(_('It is not valid to set %s as a share.') % self['path'])

		return []

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
		self.check_options_for_validity()
		return ml

	def _ldap_pre_remove(self):
		if not self.options:
			self.open()
		if 'nfs' in self.options:
			searchResult = self.lo.searchDn(base=self.position.getDomain(), filter=filter_format('(&(objectClass=person)(automountInformation=*%s:%s*))', [self['host'], self['path']]), scope='domain')
			if searchResult:
				numstring = ""
				userstring = ""
				usestring = _("uses")
				pluralstring = _("user")
				if len(searchResult) > 1:
					pluralstring = _("users")
					usestring = _("use")
					if len(searchResult) > 10:
						num = len(searchResult)
						searchResult = searchResult[:9]
						numstring = _(" and %s more") % str(num - 10)
					for i in range(0, len(searchResult) - 2):
						temp = searchResult[i].split(",")
						temp = temp[0]  # uid=...
						uid = temp[4:]
						userstring += "%s, " % uid
				temp = searchResult[-1].split(",")
				temp = temp[0]
				uid = temp[4:]
				userstring += uid

				exstr = _("The %(plural)s %(user)s%(num)s %(use)s this share as home share!") % {'plural': pluralstring, 'user': userstring, 'num': numstring, 'use': usestring}
				raise univention.admin.uexceptions.homeShareUsed(exstr)

	def description(self):
		return _('%(name)s (%(path)s on %(host)s)') % {'name': self['name'], 'path': self['path'], 'host': self['host']}

	def check_options_for_validity(self):
		if not set(self.options) & set(['samba', 'nfs']):
			raise univention.admin.uexceptions.invalidOptions(_('Need %(samba)s or %(nfs)s in options to create a share.') % {
				'samba': options['samba'].short_description,
				'nfs': options['nfs'].short_description})


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
