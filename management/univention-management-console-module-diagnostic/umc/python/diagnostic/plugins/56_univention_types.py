#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Warning, ProblemFixed

from univention.admin.uldap import getAdminConnection
from univention.admin.modules import identify, update

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('LDAP objects')
description = '\n'.join([
	_('Several services rely on the attribute "univentionObjectType" to search and identify objects in LDAP.'),
	_('Objects that implicitly satisfy the standards of a Univention Object but lack this attribute should be migrated.'),
])

_UPDATED = False


def udm_objects_without_type(lo):
	global _UPDATED
	if not _UPDATED:
		update()
		_UPDATED = True
	objs = []
	query = lo.search('(!(univentionObjectType=*))')
	for dn, attrs in query:
		if dn.endswith(',cn=temporary,cn=univention,%s' % ucr.get('ldap/base')):
			continue
		modules = identify(dn, attrs)
		if modules:
			for module in modules:  # Bug #47846
				if module.module == 'kerberos/kdcentry':
					break
			else:
				objs.append((dn, modules, attrs['objectClass']))
	return objs


def run(_umc_instance):
	if ucr.get('server/role') != 'domaincontroller_master':
		return

	lo, pos = getAdminConnection()
	objects = udm_objects_without_type(lo)
	if len(objects):
		counted_objects = {}
		details = '\n\n' + _('These objects were found:')
		for dn, modules, object_classes in objects:
			for module in modules:
				counted_objects.setdefault(module.short_description, 0)
				counted_objects[module.short_description] += 1
		for module_name in sorted(counted_objects.keys()):
			num_objs = counted_objects[module_name]
			details += '\n· ' + _('%d objects should be "%s"') % (num_objs, module_name)
		raise Warning(description + details, buttons=[{
			'action': 'migrate_objects',
			'label': _('Migrate %d LDAP objects') % len(objects),
		}])


def migrate_objects(_umc_instance):
	lo, pos = getAdminConnection()
	objects = udm_objects_without_type(lo)
	for dn, modules, object_classes in objects:
		new_object_classes = object_classes[:]
		if 'univentionObject' not in object_classes:
			new_object_classes.append('univentionObject')
		changes = [('objectClass', object_classes, new_object_classes), ('univentionObjectType', [], [module.module for module in modules])]
		lo.modify(dn, changes)
	raise ProblemFixed(buttons=[])


actions = {
	'migrate_objects': migrate_objects,
}


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
