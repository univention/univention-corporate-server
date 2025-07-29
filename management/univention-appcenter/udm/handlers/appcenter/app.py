#
# Univention Directory Manager Modules
#  directory manager module for App Metadata
#
# SPDX-FileCopyrightText: 2013-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.appcenter')
_ = translation.translate


module = 'appcenter/app'
superordinate = 'settings/cn'
default_containers = ['cn=apps,cn=univention']
childs = True
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Appcenter: App Metadata')
object_name = _('App Metadata')
object_name_plural = _('App Metadata')
long_description = ''
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionApp'],
    ),
}
property_descriptions = {
    'id': univention.admin.property(
        short_description=_('App ID'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
        include_in_default_search=True,
        required=True,
    ),
    'version': univention.admin.property(
        short_description=_('Version'),
        long_description='',
        syntax=univention.admin.syntax.string,
        required=True,
    ),
    'shortDescription': univention.admin.property(
        short_description=_('Short description'),
        long_description='',
        syntax=univention.admin.syntax.TextArea,
        multivalue=True,
    ),
    'longDescription': univention.admin.property(
        short_description=_('Long description'),
        long_description='',
        syntax=univention.admin.syntax.TextArea,
        multivalue=True,
    ),
    'vendor': univention.admin.property(
        short_description=_('Vendor'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'contact': univention.admin.property(
        short_description=_('Contact'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'maintainer': univention.admin.property(
        short_description=_('Maintainer'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'website': univention.admin.property(
        short_description=_('Website'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'websiteVendor': univention.admin.property(
        short_description=_('Website Vendor'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'websiteMaintainer': univention.admin.property(
        short_description=_('Website Maintainer'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'icon': univention.admin.property(
        short_description=_('Icon'),
        long_description='',
        syntax=univention.admin.syntax.Base64Upload,
        dontsearch=True,
    ),
    'category': univention.admin.property(
        short_description=_('Category'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'webInterface': univention.admin.property(
        short_description=_('Web Interface'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'webInterfaceName': univention.admin.property(
        short_description=_('Web Interface Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'conflictingApps': univention.admin.property(
        short_description=_('Conflicting Apps'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'conflictingSystemPackages': univention.admin.property(
        short_description=_('Conflicting System Packages'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'defaultPackages': univention.admin.property(
        short_description=_('Default Packages'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'defaultPackagesMaster': univention.admin.property(
        short_description=_('Default Primary Node Packages'),
        long_description='',
        syntax=univention.admin.syntax.string,
        multivalue=True,
    ),
    'umcModuleName': univention.admin.property(
        short_description=_('UMC Module Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'umcModuleFlavor': univention.admin.property(
        short_description=_('UMC Module Flavor'),
        long_description='',
        syntax=univention.admin.syntax.string,
    ),
    'serverRole': univention.admin.property(
        short_description=_('Installable on Server Roles'),
        long_description='',
        syntax=univention.admin.syntax.UCSServerRole,
        multivalue=True,
    ),
    'server': univention.admin.property(
        short_description=_('Installed On Server'),
        long_description='',
        syntax=univention.admin.syntax.UCS_Server,
        multivalue=True,
        include_in_default_search=True,
    ),
}

layout = [
    Tab(_('General'), _('App Definition'), layout=[
        Group(_('General'), layout=[
            ["id"],
            ["name"],
            ["version"],
            ["shortDescription"],
            ["longDescription"],
        ]),
        Group(_('About'), layout=[
            ["vendor"],
            ["contact"],
            ["maintainer"],
            ["website"],
            ["websiteVendor"],
            ["websiteMaintainer"],
        ]),
        Group(_('Metadata'), layout=[
            ["icon"],
            ["category"],
            ["webInterface"],
            ["webInterfaceName"],
            ["conflictingApps"],
            ["conflictingSystemPackages"],
            ["defaultPackages"],
            ["defaultPackagesMaster"],
            ["umcModuleName"],
            ["umcModuleFlavor"],
            ["serverRole"],
            ["server"],
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('id', 'univentionAppID', None, univention.admin.mapping.ListToString)
mapping.register('name', 'univentionAppName')
mapping.register('version', 'univentionAppVersion', None, univention.admin.mapping.ListToString)
mapping.register('shortDescription', 'univentionAppDescription')
mapping.register('longDescription', 'univentionAppLongDescription')
mapping.register('vendor', 'univentionAppVendor', None, univention.admin.mapping.ListToString)
mapping.register('contact', 'univentionAppContact', None, univention.admin.mapping.ListToString)
mapping.register('maintainer', 'univentionAppMaintainer', None, univention.admin.mapping.ListToString)
mapping.register('website', 'univentionAppWebsite')
mapping.register('websiteVendor', 'univentionAppWebsiteVendor')
mapping.register('websiteMaintainer', 'univentionAppWebsiteMaintainer')
mapping.register('icon', 'univentionAppIcon', None, univention.admin.mapping.ListToString)
mapping.register('category', 'univentionAppCategory')
mapping.register('webInterface', 'univentionAppWebInterface', None, univention.admin.mapping.ListToString)
mapping.register('webInterfaceName', 'univentionAppWebInterfaceName', None, univention.admin.mapping.ListToString)
mapping.register('conflictingApps', 'univentionAppConflictingApps')
mapping.register('conflictingSystemPackages', 'univentionAppConflictingSystemPackages')
mapping.register('defaultPackages', 'univentionAppDefaultPackages')
mapping.register('defaultPackagesMaster', 'univentionAppDefaultPackagesMaster')
mapping.register('umcModuleName', 'univentionAppUMCModuleName', None, univention.admin.mapping.ListToString)
mapping.register('umcModuleFlavor', 'univentionAppUMCModuleFlavor', None, univention.admin.mapping.ListToString)
mapping.register('serverRole', 'univentionAppServerRole')
mapping.register('server', 'univentionAppInstalledOnServer')


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
