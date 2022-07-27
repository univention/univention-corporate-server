#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Univention GmbH
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

"""
|UDM| module for monitoring alerts
"""

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.syntax
import univention.admin.localization
import univention.admin.uexceptions

translation = univention.admin.localization.translation('univention.admin.handlers.monitoring.alert')
_ = translation.translate

module = 'monitoring/alert'
default_containers = ['cn=monitoring']

childs = False
short_description = _('Alert')
object_name = _('Alert')
object_name_plural = _('Alerts')
long_description = ''
operations = ['search', 'edit', 'add', 'remove']


options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionMonitoringAlert'],
	),
}


property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('Alert name'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description template'),
		long_description=_('Alert description, shown in alert dashboard and alert e-mail notifications.'),
		syntax=univention.admin.syntax.TextArea,
		include_in_default_search=True,
		size='Two',
	),
	'summary': univention.admin.property(
		short_description=_('Summary template'),
		long_description=_('Alert summary, shown in alert dashboard and alert e-mail notifications.'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		size='Two',
	),
	'query': univention.admin.property(
		short_description=_('Query expression'),
		long_description=_('Prometheus query expression, which causes the alert to fire. Alert fires when the given query returns a non-empty vector.'),
		syntax=univention.admin.syntax.string,
		required=True,
		size='OneAndAHalf',
	),
	'for': univention.admin.property(
		short_description=_('For clause'),
		long_description=_('The amount of time the result of the query expression must be non-empty until the alert fires.'),
		syntax=univention.admin.syntax.string,
		default='1m',
		size='Half',
	),
	'alertGroup': univention.admin.property(
		short_description=_('Alert group'),
		long_description=_('The group into which an alarm is inserted. Multiple alarms can belong to the same group.'),
		syntax=univention.admin.syntax.string,
		default='<name>',
	),
	'labels': univention.admin.property(
		short_description=_('Labels'),
		long_description=_('Labels will be attached to alerts. They can be used for querying alerts.'),
		multivalue=True,
		syntax=univention.admin.syntax.keyAndValue,
	),
	'assignedHosts': univention.admin.property(
		short_description=_('Assigned hosts'),
		long_description=_('Hosts where this alert is activated for.'),
		syntax=univention.admin.syntax.monitoringEnabledHosts,
		multivalue=True,
	),
	'templateValues': univention.admin.property(
		short_description=_('Template Values'),
		long_description=_('Values inserted into the query expression, description and summary. References can be done like %name%.'),
		syntax=univention.admin.syntax.keyAndValue,
		multivalue=True,
	),
}


layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General monitoring settings'), layout=[
			["name", "alertGroup"],
			["query", "for"],
			"templateValues",
			"summary",
			"description",
			"labels",
		]),
	]),
	Tab(_('Hosts'), _('Assigned hosts'), layout=[
		Group(_('Assigned hosts'), layout=[
			"assignedHosts"
		]),
	]),
]


def mapKeyAndValue(old, encoding=()):
	"""Map (key, value) list to key=value list.

	>>> mapKeyAndValue([("a", "b")])
	[b'a=b']
	"""
	return [u'='.join(entry).encode(*encoding) for entry in old]


def unmapKeyAndValue(old, encoding=()):
	"""Map (key=value) list to (key, value) list.

	>>> unmapKeyAndValue([b"a=b"])
	[['a', 'b']]
	"""
	return [entry.decode(*encoding).split(u'=', 1) for entry in old]


mapping = univention.admin.mapping.mapping()

mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('query', 'univentionMonitoringAlertQuery', None, univention.admin.mapping.ListToString)
mapping.register('alertGroup', 'univentionMonitoringAlertGroup', None, univention.admin.mapping.ListToString)
mapping.register('summary', 'univentionMonitoringAlertSummary', None, univention.admin.mapping.ListToString)
mapping.register('labels', 'univentionMonitoringAlertLabel', mapKeyAndValue, unmapKeyAndValue)
mapping.register('for', 'univentionMonitoringAlertFor', None, univention.admin.mapping.ListToString)
mapping.register('templateValues', 'univentionMonitoringAlertTemplateValue', mapKeyAndValue, unmapKeyAndValue)
mapping.register('assignedHosts', 'univentionMonitoringAlertHosts')


class object(univention.admin.handlers.simpleLdap):
	module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
