# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for share objects
#
# Copyright 2004-2011 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import re
import copy

from univention.admin.layout import Tab, Group
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.shares')
_=translation.translate

class cscPolicy(univention.admin.syntax.select):
	name='cscPolicy'
	choices=[('manual', _('manual')), ('documents', _('documents')), ('programs', _('programs')), ('disable', _('disable'))]

module='shares/share'
operations=['add','edit','remove','search','move']

usewizard=1
wizardmenustring=_("Shares")
wizarddescription=_("Add, edit and delete shares")
wizardoperations={"add":[_("Add"), _("Add share object")],"find":[_("Search"), _("Search share Object(s)")]}
syntax_filter=univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'univentionShare'),
	univention.admin.filter.expression('cn', '*'),
	univention.admin.filter.expression('writeable', '1'),
	])

childs=0
short_description=_('Share: Directory')
long_description=''
options={
	'samba': univention.admin.option(
			short_description=_('Export for Samba clients'),
			editable=1,
			default=1
		),
	'nfs': univention.admin.option(
			short_description=_('Export for NFS clients'),
			editable=1,
			default=1
		),
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description=_('Name'),
			syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
		),
	'printablename': univention.admin.property(
			short_description=_('Printable name'),
			long_description=_('Printable name'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'host': univention.admin.property(
			short_description=_('Host'),
			long_description=_('The computer that exports this share'),
			syntax=univention.admin.syntax.UCS_Server,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'path': univention.admin.property(
			short_description=_('Directory'),
			long_description=_('Directory that is exported.'),
			syntax=univention.admin.syntax.sharePath,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'owner': univention.admin.property(
			short_description=_('Directory owner'),
			long_description=_('The owner of the directory. If none is given root will be owner.'),
			syntax=univention.admin.syntax.UserID,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default="0"
		),
	'group': univention.admin.property(
			short_description=_('Directory owner group'),
			long_description=_('The primary group of the directory, if none give group 0 will be used.'),
			syntax=univention.admin.syntax.GroupID,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default="0"
		),
	'directorymode': univention.admin.property(
			short_description=_('Directory mode'),
			long_description=_('Mode of the directory.'),
			syntax=univention.admin.syntax.UNIX_AccessRight,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1,
			default="0755"
		),
	'writeable': univention.admin.property(
			short_description=_('NFS write access'),
			long_description=_('Define if the share is writable when accessed via NFS.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['nfs'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sync': univention.admin.property(
			short_description=_('NFS synchronisation'),
			long_description=_('Use synchronous or asynchronous mode for the NFS share.'),
			syntax=univention.admin.syntax.nfssync,
			multivalue=0,
			options=['nfs'],
			required=0,
			may_change=1,
			identifies=0,
		),
	'subtree_checking': univention.admin.property(
			short_description=_('Subtree checking'),
			long_description=_('When only a subtree of a mounted filesystem is exported this option ensures that an accessed file really is in that subtree. (May cause complications with renamed files.)'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['nfs'],
			required=0,
			may_change=1,
			identifies=0,
		),
	'root_squash': univention.admin.property(
			short_description=_('Redirect root access'),
			long_description=_('Redirect accesses to a non-privileged ID.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['nfs'],
			required=0,
			may_change=1,
			identifies=0,
		),
	'nfs_hosts': univention.admin.property(
			short_description=_('Allowed hosts'),
			long_description=_('A network or a selection of hosts that may mount this share.'),
			syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
			multivalue=1,
			options=['nfs'],
			required=0,
			may_change=1,
			identifies=0,
		),
	'sambaWriteable': univention.admin.property(
			short_description=_('Samba write access'),
			long_description=_('Define if the share is writable when accessed via Samba.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='1'
		),
	'sambaName': univention.admin.property(
			short_description=_('Samba name'),
			long_description=_('This is the NetBIOS name. Among other places, it appears in the Windows Network Neighborhood.'),
			syntax=univention.admin.syntax.string_numbers_letters_dots_spaces,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default= '<name>',
		),
	'sambaBrowseable': univention.admin.property(
			short_description=_('Browseable'),
			long_description=_('Share is listed in the Windows Network environment'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='1'
		),
	'sambaPublic': univention.admin.property(
			short_description=_('Public'),
			long_description=_('Allow guest access'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sambaDosFilemode': univention.admin.property(
			short_description=_('Users with write access may modify permissions'),
			long_description=_('users who have write access to a file or directory are able to change the permissions '),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sambaHideUnreadable': univention.admin.property(
			short_description=_('Hide unreadable files/directories'),
			long_description=_('Files and directories with no read access are hidden. New files and directories receive permissions of the superordinate directory.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sambaCreateMode': univention.admin.property(
			short_description=_('File mode'),
			long_description=_('When a file is created, the necessary permissions are calculated  according to the mapping from DOS modes to UNIX permissions, and the resulting UNIX mode is then bit-wise \'AND\'ed with this parameter. This parameter may be thought of as a bit-wise MASK for the UNIX modes of a file. Any bit not set here will be removed from the modes set on a file when it is created.'),
			syntax=univention.admin.syntax.UNIX_AccessRight,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1,
			default='0744'
		),
	'sambaDirectoryMode': univention.admin.property(
			short_description=_('Directory mode'),
			long_description=_('When a directory is created, the necessary permissions are calculated  according to the mapping from DOS modes to UNIX permissions, and the resulting UNIX mode is then bit-wise \'AND\'ed with this parameter. This parameter may be thought of as a bit-wise MASK for the UNIX modes of a directory. Any bit not set here will be removed from the modes set on a directory when it is created.'),
			syntax=univention.admin.syntax.UNIX_AccessRight,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1,
			default='0755'
		),
	'sambaForceCreateMode': univention.admin.property(
			short_description=_('Force file mode'),
			long_description=_('This parameter specifies a set of UNIX mode bit permissions that will always be set on a file created by Samba. This is done by bitwise \'OR\'ing these bits onto the mode bits of a file that is being created or having its permissions changed. The modes in this parameter are bitwise \'OR\'ed onto the file mode after the mask set in the create mask parameter is applied.'),
			syntax=univention.admin.syntax.UNIX_AccessRight,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1,
			default='0'
		),
	'sambaForceDirectoryMode': univention.admin.property(
			short_description=_('Force directory mode'),
			long_description=_('This parameter specifies a set of UNIX mode bit permissions that will always be set on a directory created by Samba. This is done by bitwise \'OR\'ing these bits onto the mode bits of a directory that is being created or having its permissions changed. The modes in this parameter are bitwise \'OR\'ed onto the directory mode after the mask set in the create mask parameter is applied.'),
			syntax=univention.admin.syntax.UNIX_AccessRight,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1,
			default='0'
		),
	'sambaSecurityMode': univention.admin.property(
			short_description=_('Security mode'),
			long_description=_('This parameter controls what UNIX permission bits can be modified when a Windows NT client is manipulating the UNIX permission on a file using the native NT security dialog box. This parameter is applied as a mask (AND\'ed with) to the changed permission bits, thus preventing any bits not in this mask from being modified. Essentially, zero bits in this mask may be treated as a set of bits the user is not allowed to change.'),
			syntax=univention.admin.syntax.UNIX_AccessRight,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1,
			default='0777'
		),
	'sambaDirectorySecurityMode': univention.admin.property(
			short_description=_('Directory security mode'),
			long_description=_('This parameter controls what UNIX permission bits can be modified when a Windows NT client is manipulating the UNIX permission on a directory using the native NT security dialog box. This parameter is applied as a mask (AND\'ed with) to the changed permission bits, thus preventing any bits not in this mask from being modified. Essentially, zero bits in this mask may be treated as a set of bits the user is not allowed to change.'),
			syntax=univention.admin.syntax.UNIX_AccessRight,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1,
			default='0777'
		),
	'sambaForceSecurityMode': univention.admin.property(
			short_description=_('Force security mode'),
			long_description=_('This parameter controls what UNIX permission bits can be modified when a Windows NT client is manipulating the UNIX permission on a file using the native NT security dialog box. This parameter is applied as a mask (OR\'ed with) to the changed permission bits, thus forcing any bits in this mask that the user may have modified to be on. Essentially, one bits in this mask may be treated as a set of bits that, when modifying security on a file, the user has always set to be \'on\'.'),
			syntax=univention.admin.syntax.UNIX_AccessRight,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1,
			default='0'
		),
	'sambaForceDirectorySecurityMode': univention.admin.property(
			short_description=_('Force directory security mode'),
			long_description=_('This parameter controls what UNIX permission bits can be modified when a Windows NT client is manipulating the UNIX permission on a directory using the native NT security dialog box. This parameter is applied as a mask (OR\'ed with) to the changed permission bits, thus forcing any bits in this mask that the user may have modified to be on. Essentially, one bits in this mask may be treated as a set of bits that, when modifying security on a directory, the user has always set to be \'on\'.'),
			syntax=univention.admin.syntax.UNIX_AccessRight,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			dontsearch=1,
			default='0'
		),
	'sambaLocking': univention.admin.property(
			short_description=_('Locking'),
			long_description=_('This controls whether or not locking will be performed by the server in response to lock requests from the client. Be careful about disabling locking, as lack of locking may result in data corruption.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='1'
		),
	'sambaBlockingLocks': univention.admin.property(
			short_description=_('Blocking locks'),
			long_description=_('This parameter controls the behavior of Samba when given a request by a client to obtain a byte range lock on a region of an open file, and the request has a time limit associated with it. If this parameter is set and the lock range requested cannot be immediately satisfied, samba will internally queue the lock request, and periodically attempt to obtain the lock until the timeout period expires.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='1'
		),
	'sambaStrictLocking': univention.admin.property(
			short_description=_('Strict locking'),
			long_description=_('This is a boolean that controls the handling of file locking in the server. When this is set to yes, the server will check every read and write access for file locks, and deny access if locks exist. This can be slow on some systems. When strict locking is disabled, the server performs file lock checks only when the client explicitly asks for them.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sambaOplocks': univention.admin.property(
			short_description=_('Oplocks'),
			long_description=_('This boolean option tells Samba whether to issue oplocks (opportunistic locks) to file open requests on this share. The oplock code can dramatically (approx. 30% or more) improve the speed of access to files on Samba servers. It allows the clients to aggressively cache files locally and you may want to disable this option for unreliable network environments (it is turned on by default in Windows NT Servers).'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='1'

		),
	'sambaLevel2Oplocks': univention.admin.property(
			short_description=_('Level 2 oplocks'),
			long_description=_('This parameter controls whether Samba supports level2 (read-only) oplocks on a share. Level2, or read-only oplocks allow Windows NT clients that have an oplock on a file to downgrade from a read-write oplock to a read-only oplock once a second client opens the file (instead of releasing all oplocks on a second open, as in traditional, exclusive oplocks). This allows all openers of the file that support level2 oplocks to cache the file for read-ahead only (ie. they may not cache writes or lock requests) and increases performance for many accesses of files that are not commonly written (such as application .EXE files). Once one of the clients which have a read-only oplock writes to the file all clients are notified (no  reply  is  needed or waited for) and told to break their oplocks to "none" and delete any read-ahead caches. It is recommended that this parameter be turned on to speed access to shared executables.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='1'
		),
	'sambaFakeOplocks': univention.admin.property(
			short_description=_('Fake oplocks'),
			long_description=_('Oplocks are the way that Samba clients get permission from a server to locally cache file operations.  If a server grants an oplock (opportunistic lock) then the client is free to assume that it is the only one accessing the file and it will aggressively cache file data. With some  oplock  types the client may even cache file open/close operations. This can give enormous performance benefits. When you activate this parameter, Samba will always grant oplock requests no matter how many clients are using the file. It is generally much better to use the real oplocks support rather than this parameter. If you enable this option on all read-only shares or shares that you know will only be accessed from one client at a time such as physically read-only media like CDROMs, you will see a big performance improvement on many operations. If you enable this option on shares where multiple clients may be accessing the files read-write at the same  time you can get data corruption. Use this option carefully!'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sambaBlockSize': univention.admin.property(
			short_description=_('Block size'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaCscPolicy': univention.admin.property(
			short_description=_('Client-side caching policy'),
			long_description=_('The way clients are capable of offline caching will cache the files in the share.'),
			syntax=cscPolicy,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='manual'
		),
	'sambaHostsAllow': univention.admin.property(
			short_description=_('Allowed hosts'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaHostsDeny': univention.admin.property(
			short_description=_('Denied hosts'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaValidUsers': univention.admin.property(
			short_description=_('Valid users'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaInvalidUsers': univention.admin.property(
			short_description=_('Invalid users'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaForceUser': univention.admin.property(
			short_description=_('Force user'),
			long_description=_('This specifies a UNIX user name that will be assigned as the default user for all users connecting to this service. This is useful for sharing files. You should also use it carefully as using it incorrectly can cause security problems.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaForceGroup': univention.admin.property(
			short_description=_('Force group'),
			long_description=_('This specifies a UNIX group name that will be assigned as the default primary group for all users connecting to this service. This is useful for sharing files by ensuring that all access to files on the service will use the named group for their permissions checking. Thus, by assigning permissions for this group to the files and directories within this service the Samba administrator can restrict or allow sharing of these files.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaHideFiles': univention.admin.property(
			short_description=_('Hide files'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaNtAclSupport': univention.admin.property(
			short_description=_('NT ACL support'),
			long_description=_('This boolean parameter controls whether Samba will attempt to map UNIX permissions into Windows NT access control lists.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='1'
		),
	'sambaInheritAcls': univention.admin.property(
			short_description=_('Inherit ACLs'),
			long_description=_('This parameter can be used to ensure that if default acls exist on parent directories, they are always honored when creating a subdirectory. The default behavior is to use the mode specified when creating the directory. Enabling this option sets the mode to 0777, thus guaranteeing that default directory acls are propagated.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sambaPostexec': univention.admin.property(
			short_description=_('Postexec script'),
			long_description=_('This option specifies a command to be run whenever the service is disconnected. It takes the usual substitutions.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaPreexec': univention.admin.property(
			short_description=_('Preexec script'),
			long_description=_('This option specifies a command to be run whenever the service is connected to. It takes the usual substitutions.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaWriteList': univention.admin.property(
			short_description=_('Users with write access'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaVFSObjects': univention.admin.property(
			short_description=_('VFS objects'),
			long_description=_('Specifies which VFS Objects to use.'),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0
		),
	'sambaMSDFSRoot': univention.admin.property(
			short_description=_('MSDFS root'),
			long_description=_('Export share as MSDFS root'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sambaInheritOwner': univention.admin.property(
			short_description=_('Inherit owner'),
			long_description=_('Ownership for new files and directories is controlled by the ownership of the parent directory.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sambaInheritPermissions': univention.admin.property(
			short_description=_('Inherit permissions'),
			long_description=_('New files and directories inherit the mode of the parent directory.'),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
			default='0'
		),
	'sambaCustomSettings': univention.admin.property(
			short_description=_('Custom share settings'),
			long_description=_('Set new custom share settings'),
			syntax=univention.admin.syntax.keyAndValue,
			multivalue=1,
			options=['samba'],
			required=0,
			may_change=1,
			identifies=0,
		),
}

layout = [
	Tab(_('General'),_('General settings'), layout = [
		Group( _( 'General' ), layout = [
			'name',
			['host', 'path'],
			['owner', 'group'],
			'directorymode'
		] ),
	] ),
	Tab(_('NFS general'),_('General NFS settings'), layout = [
		Group( _( 'NFS general' ), layout = [
			'writeable',
			'subtree_checking',
			'root_squash',
			'sync',
			'nfs_hosts',
		] ),
	] ),
	Tab( _( 'Samba general' ), _( 'General Samba settings' ), layout = [
		Group( _( 'Samba general' ), layout = [
			'sambaName',
			'sambaBrowseable',
			'sambaPublic',
			'sambaMSDFSRoot',
			[ 'sambaDosFilemode'],
			[ 'sambaHideUnreadable' ],
			[ 'sambaVFSObjects'],
			[ 'sambaPostexec', 'sambaPreexec'],
		] ),
	] ),
	Tab( _( 'Samba permissions' ), _( 'Samba permission settings' ), advanced = True, layout = [
		Group( _( 'Samba permissions' ), layout = [
			'sambaWriteable',
			[ 'sambaForceUser', 'sambaForceGroup' ],
			[ 'sambaValidUsers', 'sambaInvalidUsers' ],
			[ 'sambaHostsAllow', 'sambaHostsDeny' ],
			[ 'sambaWriteList', 'sambaHideFiles' ],
			[ 'sambaNtAclSupport', 'sambaInheritAcls' ],
			[ 'sambaInheritOwner', 'sambaInheritPermissions' ],
		] ),
	] ),
	Tab( _( 'Samba extended permissions' ), _( 'Samba extended permission settings' ), advanced = True, layout = [
		Group( _( 'Samba extended permissions' ), layout = [
			[ 'sambaCreateMode', 'sambaDirectoryMode' ],
			[ 'sambaForceCreateMode', 'sambaForceDirectoryMode' ],
			[ 'sambaSecurityMode', 'sambaDirectorySecurityMode' ],
			[ 'sambaForceSecurityMode', 'sambaForceDirectorySecurityMode' ],
		] ),
	] ),
	Tab( _( 'Samba performance' ), _( 'Samba performance settings' ), advanced = True, layout = [
		Group( _( 'Samba performance' ), layout = [
			[ 'sambaLocking', 'sambaBlockingLocks' ],
			[ 'sambaStrictLocking', 'sambaOplocks' ],
			[ 'sambaLevel2Oplocks', 'sambaFakeOplocks' ],
			[ 'sambaBlockSize', 'sambaCscPolicy' ],
		] ),
	] ),
	Tab( _( 'Samba custom settings' ), _( 'Custom settings for Samba shares' ), advanced = True, layout = [
		Group( _( 'Samba custom settings' ), layout = [
			'sambaCustomSettings'
		] ),
	] ),
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
	lst = []
	for entry in old:
		lst.append( '%s = %s' % (entry[0], entry[1]) )
	return lst

def unmapKeyAndValue(old):
	lst = []
	for entry in old:
		lst.append( entry.split(' = ', 1) )
	return lst


def insertQuotes(value):
	'Turns @group name, user name into @"group name", "user name"'

	entries=value.split(",")
	new_entries=""
	for entry in entries:
		new_entry=entry.strip()
		if new_entry[0]=="@":
			is_group=True
			new_entry=new_entry[1:].strip()
		else:
			is_group=False
		if new_entry.find(" ")>-1:
			new_entry='"%s"'%new_entry
		if is_group:
			new_entry="@%s"%new_entry
		new_entries+="%s, "%new_entry
	if new_entries[-2:]==", ":
		return new_entries[:-2]
	else:
		return new_entries

mapping=univention.admin.mapping.mapping()
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
mapping.register('sambaValidUsers', 'univentionShareSambaValidUsers', None, univention.admin.mapping.ListToString )
mapping.register('sambaInvalidUsers', 'univentionShareSambaInvalidUsers', None, univention.admin.mapping.ListToString )
mapping.register('sambaHostsAllow', 'univentionShareSambaHostsAllow' )
mapping.register('sambaHostsDeny', 'univentionShareSambaHostsDeny' )
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

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions
		global options

		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )

		self.options = []
		self._define_options( options )


	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		# copy the mapping table, we need this for the option handling
		self.mapping_list = {}
		for key in self.descriptions.keys():
			self.mapping_list[key] = mapping.mapName(key)

		if self.oldattr.has_key('objectClass'):
			global options
			self.options = []
			if 'univentionShareSamba' in self.oldattr['objectClass']:
				self.options.append( 'samba' )
			if 'univentionShareNFS' in self.oldattr['objectClass']:
				self.options.append( 'nfs' )
			try:
				self['printablename'] = "%s (%s)" % (self['name'], self['host'])
			except:
				pass

		self.old_options = copy.deepcopy( self.options )

		self.save()

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):

		dirBlackList = ["sys", "proc", "dev"]
		for dir in dirBlackList:
			if re.match("^/%s$|^/%s/" % (dir, dir), self['path']):
				raise univention.admin.uexceptions.invalidOperation, _('It is not valid to set %s as a share.')%self['path']

		ocs = ['top', 'univentionShare']
		if not ( 'samba' in self.options or 'nfs' in self.options):
			raise univention.admin.uexceptions.invalidOptions, _('Need  %s or %s in options to create a share.')%(
				options['samba'].short_description,
				options['nfs'].short_description)

		if 'samba' in self.options:
			ocs.append('univentionShareSamba')
		if 'nfs' in self.options:
			ocs.append('univentionShareNFS')
		return [
			('objectClass', ocs)
		]

	def _remove_attr(self, ml, attr):
		for m in ml:
			if m[0] == attr:
				ml.remove(m)
		if self.oldattr.get(attr, []):
			ml.insert(0, (attr, self.oldattr.get(attr, []), ''))
		return ml

	def _ldap_modlist(self):

		ml=univention.admin.handlers.simpleLdap._ldap_modlist(self)

		if not ( 'samba' in self.options or 'nfs' in self.options):
			raise univention.admin.uexceptions.invalidOptions, ('Need  %s or %s in options to create a share.')%(
				options['samba'].short_description,
				options['nfs'].short_description)

		if self.options != self.old_options:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'options: %s' % self.options)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'old_options: %s' % self.old_options)
			for option,objectClass in [ ('samba','univentionShareSamba'), ('nfs','univentionShareNFS') ]:

				if option in self.options and not option in self.old_options:
					ocs=self.oldattr.get('objectClass', [])
					if not objectClass in ocs:
						ml.insert(0, ('objectClass', '', objectClass))

				if not option in self.options and option in self.old_options:
					ocs=self.oldattr.get('objectClass', [])
					if objectClass in ocs:
						ml.insert(0, ('objectClass', objectClass, ''))
					for key in self.descriptions.keys():
						if self.descriptions[key].options == [option]:
							ml = self._remove_attr(ml, self.mapping_list[key] )

		return ml

	def _ldap_pre_remove(self):
		if not hasattr(self,"options"):
			self.open()
		if 'nfs' in self.options:
			ulist=[]
			searchstring="*"+self['host']+":"+self['path']+"*"
			searchResult=self.lo.searchDn(base=self.position.getDomain(), filter='(&(objectClass=person)(automountInformation=%s))'%searchstring, scope='domain')
			if searchResult:
				numstring=""
				userstring=""
				usestring=_("uses")
				pluralstring=_("user")
				if len(searchResult)>1:
					pluralstring=_("users")
					usestring=_("use")
					if len(searchResult)>10:
						num=len(searchResult)
						searchResult=searchResult[:9]
						numstring=_(" and %s more")%str(num-10)
					for i in range(0,len(searchResult)-2):
						temp=searchResult[i].split(",")
						temp=temp[0] #uid=...
						uid=temp[4:]
						userstring+="%s, "%uid
				temp=searchResult[-1].split(",")
				temp=temp[0]
				uid=temp[4:]
				userstring+=uid

				exstr=_("The %s %s%s %s this share as home share!")%(pluralstring,userstring,numstring,usestring)

				raise univention.admin.uexceptions.homeShareUsed,exstr

	def description(self):
		return _('%s (%s on %s)') % (self['name'], self['path'], self['host'])

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionShare'),
		univention.admin.filter.expression('cn', '*'),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn in lo.searchDn(unicode(filter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(dn, attr, canonical=0):

	return 'univentionShare' in attr.get('objectClass', [])
