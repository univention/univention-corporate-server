# -*- coding: utf-8 -*-
#
# Univention Directory Manager modules
#  policy for the xorg configuration
#
# Copyright 2004-2012 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation=univention.admin.localization.translation('univention.admin.handlers.policies')
_=translation.translate

class xfreeFixedAttributes(univention.admin.syntax.select):
	name='xfreeFixedAttributes'
	choices=[
		('univentionXAutoDetect',_('Automatic detection')),
		('univentionXResolution',_('Resolution of primary display')),
		('univentionXResolutionSecondary',_('Resolution of secondary display')),
		('univentionXColorDepth',_('Color depth')),
		('univentionXMouseProtocol',_('Mouse protocol')),
		('univentionXMouseDevice',_('Mouse device')),
		('univentionXKeyboardDevice',_('Keyboard layout')),
		('univentionXKeyboardVariant',_('Keyboard variant')),
		('univentionXKeyboardLayout', _('Keyboard layout')),
		('univentionXHSync',_('Horizontal sync of primary display')),
		('univentionXHSyncSecondary',_('Horizontal sync of secondary display')),
		('univentionXVRefresh',_('Vertical refresh of primary display')),
		('univentionXVRefreshSecondary',_('Vertical refresh of secondary display')),
		('univentionXModule',_('Graphics adapter driver')),
		('univentionXDisplaySize',_('Display size of primary display')),
		('univentionXDisplaySizeSecondary',_('Display size of secondary display')),
		('univentionXVNCExportType',_('Enable VNC export')),
		('univentionXVNCExportViewonly',_('Viewonly VNC export')),
		('univentionXVideoRam',_('Amount of RAM on the graphics adapter')),
		('univentionXDisplayPrimary',_('Primary display')),
		('univentionXDisplaySecondary',_('Secondary display')),
		('univentionXDisplayPosition',_('Relative position of secondary display')),
		('univentionXDisplayVirtualSize',_('Virtual size of dual monitor desktop')),
		]

module='policies/xfree'
operations=['add','edit','remove','search']

policy_oc='univentionPolicyXConfiguration'
policy_apply_to=["computers/thinclient", "computers/managedclient", "computers/mobileclient"]
policy_position_dn_prefix="cn=xfree"
usewizard=1
childs=0
short_description=_('Policy: Display')
policy_short_description=_('Display settings')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=0,
			identifies=1,
		),
	'resolution': univention.admin.property(
			short_description=_('Resolution of primary display'),
			long_description='',
			syntax=univention.admin.syntax.XResolution,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXResolutionChoices'
		),
	'secondaryresolution': univention.admin.property(
			short_description=_('Resolution of secondary display'),
			long_description='',
			syntax=univention.admin.syntax.XResolution,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXResolutionSecondaryChoices'
		),
	'colorDepth': univention.admin.property(
			short_description=_('Color depth'),
			long_description='',
			syntax=univention.admin.syntax.XColorDepth,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXColorDepthChoices'
		),
	'mouseProtocol': univention.admin.property(
			short_description=_('Mouse protocol'),
			long_description='',
			syntax=univention.admin.syntax.XMouseProtocol,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXMouseProtocolChoices'
		),
	'mouseDevice': univention.admin.property(
			short_description=_('Mouse device'),
			long_description='',
			syntax=univention.admin.syntax.XMouseDevice,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXMouseDeviceChoices'
		),
	'keyboardLayout': univention.admin.property(
			short_description=_('Keyboard layout'),
			long_description='',
			syntax=univention.admin.syntax.XKeyboardLayout,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXKeyboardLayoutChoices'
		),
	'keyboardVariant': univention.admin.property(
			short_description=_('Keyboard variant'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXKeyboardVariantChoices'
		),
	'hSync': univention.admin.property(
			short_description=_('Horizontal sync of primary display'),
			long_description='',
			syntax=univention.admin.syntax.XSync,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXHSyncChoices'
		),
	'hSyncSecondary': univention.admin.property(
			short_description=_('Horizontal sync of secondary display'),
			long_description='',
			syntax=univention.admin.syntax.XSync,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXHSyncSecondaryChoices'
		),
	'vRefresh': univention.admin.property(
			short_description=_('Vertical refresh of primary display'),
			long_description='',
			syntax=univention.admin.syntax.XSync,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXVRefreshChoices'
		),
	'vRefreshSecondary': univention.admin.property(
			short_description=_('Vertical refresh of secondary display'),
			long_description='',
			syntax=univention.admin.syntax.XSync,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXVRefreshSecondaryChoices'
		),
	'xModule': univention.admin.property(
			short_description=_('Graphics adapter driver'),
			long_description='',
			syntax=univention.admin.syntax.XModule,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXModuleChoices'
		),
	'requiredObjectClasses': univention.admin.property(
			short_description=_('Required object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'prohibitedObjectClasses': univention.admin.property(
			short_description=_('Excluded object classes'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'fixedAttributes': univention.admin.property(
			short_description=_('Fixed attributes'),
			long_description='',
			syntax=xfreeFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'emptyAttributes': univention.admin.property(
			short_description=_('Empty Attributes'),
			long_description='',
			syntax=xfreeFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'displaySize': univention.admin.property(
			short_description=_('Display size (mm) of primary display'),
			long_description='',
			syntax=univention.admin.syntax.XResolution,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXDisplaySizeChoices'
		),
	'displaySizeSecondary': univention.admin.property(
			short_description=_('Display size (mm) of secondary display'),
			long_description='',
			syntax=univention.admin.syntax.XResolution,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			configObjectPosition='cn=xconfig choices,cn=univention',
			configAttributeName='univentionXDisplaySizeSecondaryChoices'
		),
	'vncExport': univention.admin.property(
			short_description=_('Enable VNC export'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('0', [])
		),
	'vncExportViewonly': univention.admin.property(
			short_description=_('Viewonly VNC export'),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('1', [])
		),
	'virtualsize': univention.admin.property(
			short_description=_('Virtual size of dual monitor desktop'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('', [])
		),
	'displayposition': univention.admin.property(
			short_description=_('Position of secondary display'),
			long_description='',
			syntax=univention.admin.syntax.XDisplayPosition,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('', [])
		),
	'primarydisplay': univention.admin.property(
			short_description=_('Name of primary display'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('', [])
		),
	'secondarydisplay': univention.admin.property(
			short_description=_('Name of secondary display'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
			default=('', [])
		),
	'videoRam': univention.admin.property(
			short_description=_('RAM on the graphics adapter in kB'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0,
		),
	'autodetect': univention.admin.property(
			short_description=_( 'Automatic detection' ),
			long_description='',
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			required=0,
			may_change=1,
			identifies=0,
		),
}

layout = [
	Tab(_('General'),_('Display settings'), layout = [
		Group( _( 'General' ), layout = [
			'name',
			'autodetect',
			'xModule',
			[ 'resolution', 'colorDepth' ],
			[ 'secondaryresolution', 'displayposition' ] ] ),
		Group( _( 'Input devices' ), layout = [
			[ 'mouseProtocol', 'mouseDevice' ],
			[ 'keyboardLayout', 'keyboardVariant' ] ] ),
		Group( _( 'Advanced settings' ), layout = [
			[ 'vncExport', 'vncExportViewonly' ],
			[ 'videoRam', 'virtualsize' ] ] ),
		Group( _( 'Advanced settings of primary display' ), layout = [
			[ 'primarydisplay','displaySize' ],
			[ 'hSync', 'vRefresh' ] ] ),
		Group( _( 'Advanced settings of secondary display' ), layout = [
			[ 'secondarydisplay','displaySizeSecondary' ],
			[ 'hSyncSecondary', 'vRefreshSecondary' ]
		] ),
	] ),
	Tab(_('Object'),_('Object'), advanced = True, layout = [
		[ 'requiredObjectClasses' , 'prohibitedObjectClasses' ],
		[ 'fixedAttributes', 'emptyAttributes' ]
	] ),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('xModule', 'univentionXModule', None, univention.admin.mapping.ListToString)
mapping.register('resolution', 'univentionXResolution', None, univention.admin.mapping.ListToString)
mapping.register('secondaryresolution', 'univentionXResolutionSecondary', None, univention.admin.mapping.ListToString)
mapping.register('colorDepth', 'univentionXColorDepth', None, univention.admin.mapping.ListToString)
mapping.register('mouseProtocol', 'univentionXMouseProtocol', None, univention.admin.mapping.ListToString)
mapping.register('mouseDevice', 'univentionXMouseDevice', None, univention.admin.mapping.ListToString)
mapping.register('keyboardLayout', 'univentionXKeyboardLayout', None, univention.admin.mapping.ListToString)
mapping.register('keyboardVariant', 'univentionXKeyboardVariant', None, univention.admin.mapping.ListToString)
mapping.register('hSync', 'univentionXHSync', None, univention.admin.mapping.ListToString)
mapping.register('vRefresh', 'univentionXVRefresh', None, univention.admin.mapping.ListToString)
mapping.register('displaySize', 'univentionXDisplaySize', None, univention.admin.mapping.ListToString)
mapping.register('vncExport', 'univentionXVNCExportType', None, univention.admin.mapping.ListToString)
mapping.register('videoRam', 'univentionXVideoRam', None, univention.admin.mapping.ListToString)
mapping.register('vncExportViewonly', 'univentionXVNCExportViewonly', None, univention.admin.mapping.ListToString)
mapping.register('autodetect', 'univentionXAutoDetect', None, univention.admin.mapping.ListToString)

mapping.register('primarydisplay', 'univentionXDisplayPrimary', None, univention.admin.mapping.ListToString)
mapping.register('secondarydisplay', 'univentionXDisplaySecondary', None, univention.admin.mapping.ListToString)
mapping.register('displayposition', 'univentionXDisplayPosition', None, univention.admin.mapping.ListToString)
mapping.register('virtualsize', 'univentionXDisplayVirtualSize', None, univention.admin.mapping.ListToString)

mapping.register('displaySizeSecondary', 'univentionXDisplaySizeSecondary', None, univention.admin.mapping.ListToString)
mapping.register('hSyncSecondary', 'univentionXHSyncSecondary', None, univention.admin.mapping.ListToString)
mapping.register('vRefreshSecondary', 'univentionXVRefreshSecondary', None, univention.admin.mapping.ListToString)

mapping.register('requiredObjectClasses', 'requiredObjectClasses')
mapping.register('prohibitedObjectClasses', 'prohibitedObjectClasses')
mapping.register('fixedAttributes', 'fixedAttributes')
mapping.register('emptyAttributes', 'emptyAttributes')

class object(univention.admin.handlers.simplePolicy):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simplePolicy.__init__(self, co, lo, position, dn, superordinate, attributes)

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionPolicy', 'univentionPolicyXConfiguration'])
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionPolicyXConfiguration'),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	try:
		for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
			res.append( object( co, lo, None, dn, attributes = attrs ) )
	except:
		pass
	return res

def identify(dn, attr, canonical=0):

	return 'univentionPolicyXConfiguration' in attr.get('objectClass', [])
