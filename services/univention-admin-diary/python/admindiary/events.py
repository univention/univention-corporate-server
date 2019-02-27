#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019 Univention GmbH
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

class DiaryEvent(object):
	_all_events = {}

	@classmethod
	def get(cls, name):
		return cls._all_events.get(name)

	@classmethod
	def names(cls):
		return sorted(cls._all_events.keys())

	def __init__(self, name, message, args=None, tags=None, icon=None):
		self.name = name
		self.message = message
		self.args = args or {}
		self.tags = tags or []
		self.icon = icon
		self._all_events[self.name] = self

APP_INSTALL_START = DiaryEvent('APP_INSTALL_START', {'en': 'Installation of {name} {version} started', 'de': 'Installation von {name} {version} wurde gestartet'}, args=['name', 'version'], icon='software')
APP_INSTALL_SUCCESS = DiaryEvent('APP_INSTALL_SUCCESS', {'en': 'Installation of {name} {version} was successful', 'de': 'Die Installation von {name} {version} war erfolgreich'}, args=['name', 'version'], icon='software')
APP_INSTALL_FAILURE = DiaryEvent('APP_INSTALL_FAILURE', {'en': 'Installation of {name} {version} failed. Error {error_code}', 'de': 'Die Installation von {name} {version} schlug fehl. Fehler {error_code}'}, args=['name', 'version', 'error_code'], tags=['error'], icon='software')

APP_UPGRADE_START = DiaryEvent('APP_UPGRADE_START', {'en': 'Upgrade of {name} {version} started', 'de': 'Aktualisierung von {name} {version} wurde gestartet'}, args=['name', 'version'], icon='software')
APP_UPGRADE_SUCCESS = DiaryEvent('APP_UPGRADE_SUCCESS', {'en': 'Upgrade to {name} {version} was successful', 'de': 'Die Aktualisierung auf {name} {version} war erfolgreich'}, args=['name', 'version'], icon='software')
APP_UPGRADE_FAILURE = DiaryEvent('APP_UPGRADE_FAILURE', {'en': 'Upgrade of {name} {version} failed. Error {error_code}', 'de': 'Die Aktualisierung von {name} {version} schlug fehl. Fehler {error_code}'}, args=['name', 'version', 'error_code'], tags=['error'], icon='software')

APP_REMOVE_START = DiaryEvent('APP_REMOVE_START', {'en': 'Removal of {name} {version} started', 'de': 'Deinstallation von {name} {version} wurde gestartet'}, args=['name', 'version'], icon='software')
APP_REMOVE_SUCCESS = DiaryEvent('APP_REMOVE_SUCCESS', {'en': 'Removal of {name} {version} was successful', 'de': 'Die Deinstallation von {name} {version} war erfolgreich'}, args=['name', 'version'], icon='software')
APP_REMOVE_FAILURE = DiaryEvent('APP_REMOVE_FAILURE', {'en': 'Removal of {name} {version} failed. Error {error_code}', 'de': 'Die Deinstallation von {name} {version} schlug fehl. Fehler {error_code}'}, args=['name', 'version', 'error_code'], tags=['error'], icon='software')

SERVER_PASSWORD_CHANGED = DiaryEvent('SERVER_PASSWORD_CHANGED', {'en': 'Machine account password of {hostname} changed successfully', 'de': 'Maschinenpasswort von {hostname} erfolgreich geändert'}, args=['hostname'], icon='devices')
SERVER_PASSWORD_CHANGED_FAILED = DiaryEvent('SERVER_PASSWORD_CHANGED_FAILED', {'en': 'Machine account password change of {hostname} failed', 'de': 'Änderung des Maschinenpassworts von {hostname} fehlgeschlagen'}, args=['hostname'], tags=['error'], icon='devices')

UPDATE_STARTED = DiaryEvent('UPDATE_STARTED', {'en': 'Started to update {hostname}', 'de': 'Aktualisierung von {hostname} begonnen'}, args=['hostname'], icon='software')
UPDATE_FINISHED_SUCCESS = DiaryEvent('UPDATE_FINISHED_SUCCESS', {'en': 'Successfully updated {hostname} to {version}', 'de': 'Aktualisierung von {hostname} auf {version} erfolgreich abgeschlossen'}, args=['hostname', 'version'], icon='software')
UPDATE_FINISHED_FAILURE = DiaryEvent('UPDATE_FINISHED_FAILURE', {'en': 'Failed to update {hostname}', 'de': 'Aktualisierung von {hostname} fehlgeschlagen'}, args=['hostname'], tags=['error'], icon='software')

JOIN_STARTED = DiaryEvent('JOIN_STARTED', {'en': 'Started to join {hostname} into the domain', 'de': 'Domänenbeitritt von {hostname} begonnen'}, args=['hostname'], icon='domain')
JOIN_FINISHED_SUCCESS = DiaryEvent('JOIN_FINISHED_SUCCESS', {'en': 'Successfully joined {hostname}', 'de': '{hostname} erfolgreich der Domäne beigetreten'}, args=['hostname'], icon='domain')
JOIN_FINISHED_FAILURE = DiaryEvent('JOIN_FINISHED_FAILURE', {'en': 'Failed to join {hostname}', 'de': 'Domänenbeitritt von {hostname} fehlgeschlagen'}, args=['hostname'], tags=['error'], icon='domain')
JOIN_SCRIPT_FAILED = DiaryEvent('JOIN_SCRIPT_FAILED', {'en': 'Running Joinscript {joinscript} failed', 'de': 'Ausführung des Joinscripts {joinscript} fehlgeschlagen'}, args=['joinscript'], tags=['error'], icon='domain')

UDM_GENERIC_CREATED = DiaryEvent('UDM_GENERIC_CREATED', {'en': '{module} object {id} created', 'de': '{module}-Objekt {id} angelegt'}, args=['module', 'id'], icon='domain')
UDM_GENERIC_MODIFIED = DiaryEvent('UDM_GENERIC_MODIFIED', {'en': '{module} object {id} modified', 'de': '{module}-Objekt {id} bearbeitet'}, args=['module', 'id'], icon='domain')
UDM_GENERIC_MOVED = DiaryEvent('UDM_GENERIC_MOVED', {'en': '{module} object {id} moved to {position}', 'de': '{module}-Objekt {id} verschoben nach {position}'}, args=['module', 'id', 'position'], icon='domain')
UDM_GENERIC_REMOVED = DiaryEvent('UDM_GENERIC_REMOVED', {'en': '{module} object {id} removed', 'de': '{module}-Objekt {id} gelöscht'}, args=['module', 'id'], icon='domain')

UDM_APPCENTER_APP_CREATED = DiaryEvent('UDM_APPCENTER_APP_CREATED', {'en': 'App Metadata {id} created', 'de': 'App-Metadaten {id} angelegt'}, args=['id'], icon='domain')
UDM_APPCENTER_APP_MODIFIED = DiaryEvent('UDM_APPCENTER_APP_MODIFIED', {'en': 'App Metadata {id} modified', 'de': 'App-Metadaten {id} bearbeitet'}, args=['id'], icon='domain')
UDM_APPCENTER_APP_MOVED = DiaryEvent('UDM_APPCENTER_APP_MOVED', {'en': 'App Metadata {id} moved to {position}', 'de': 'App-Metadaten {id} verschoben nach {position}'}, args=['id'], icon='domain')
UDM_APPCENTER_APP_REMOVED = DiaryEvent('UDM_APPCENTER_APP_REMOVED', {'en': 'App Metadata {id} removed', 'de': 'App-Metadaten {id} gelöscht'}, args=['id'], icon='domain')

UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_CREATED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_CREATED', {'en': 'DC Backup {name} created', 'de': 'DC Backup {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MODIFIED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MODIFIED', {'en': 'DC Backup {name} modified', 'de': 'DC Backup {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MOVED', {'en': 'DC Backup {name} moved to {position}', 'de': 'DC Backup {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_REMOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_REMOVED', {'en': 'DC Backup {name} removed', 'de': 'DC Backup {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_CREATED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_CREATED', {'en': 'DC Master {name} created', 'de': 'DC Master {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MODIFIED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MODIFIED', {'en': 'DC Master {name} modified', 'de': 'DC Master {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MOVED', {'en': 'DC Master {name} moved to {position}', 'de': 'DC Master {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_REMOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_REMOVED', {'en': 'DC Master {name} removed', 'de': 'DC Master {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_CREATED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_CREATED', {'en': 'DC Slave {name} created', 'de': 'DC Slave {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MODIFIED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MODIFIED', {'en': 'DC Slave {name} modified', 'de': 'DC Slave {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MOVED', {'en': 'DC Slave {name} moved to {position}', 'de': 'DC Slave {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_REMOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_REMOVED', {'en': 'DC Slave {name} removed', 'de': 'DC Slave {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_IPMANAGEDCLIENT_CREATED = DiaryEvent('UDM_COMPUTERS_IPMANAGEDCLIENT_CREATED', {'en': 'IP managed client {name} created', 'de': 'IP-Managed-Client {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_IPMANAGEDCLIENT_MODIFIED = DiaryEvent('UDM_COMPUTERS_IPMANAGEDCLIENT_MODIFIED', {'en': 'IP managed client {name} modified', 'de': 'IP-Managed-Client {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_IPMANAGEDCLIENT_MOVED = DiaryEvent('UDM_COMPUTERS_IPMANAGEDCLIENT_MOVED', {'en': 'IP managed client {name} moved to {position}', 'de': 'IP-Managed-Client {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_IPMANAGEDCLIENT_REMOVED = DiaryEvent('UDM_COMPUTERS_IPMANAGEDCLIENT_REMOVED', {'en': 'IP managed client {name} removed', 'de': 'IP-Managed-Client {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_LINUX_CREATED = DiaryEvent('UDM_COMPUTERS_LINUX_CREATED', {'en': 'Linux Computer {name} created', 'de': 'Linux-Rechner {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_LINUX_MODIFIED = DiaryEvent('UDM_COMPUTERS_LINUX_MODIFIED', {'en': 'Linux Computer {name} modified', 'de': 'Linux-Rechner {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_LINUX_MOVED = DiaryEvent('UDM_COMPUTERS_LINUX_MOVED', {'en': 'Linux Computer {name} moved to {position}', 'de': 'Linux-Rechner {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_LINUX_REMOVED = DiaryEvent('UDM_COMPUTERS_LINUX_REMOVED', {'en': 'Linux Computer {name} removed', 'de': 'Linux-Rechner {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_MACOS_CREATED = DiaryEvent('UDM_COMPUTERS_MACOS_CREATED', {'en': 'Mac OS X Client {name} created', 'de': 'Mac OS X Client {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_MACOS_MODIFIED = DiaryEvent('UDM_COMPUTERS_MACOS_MODIFIED', {'en': 'Mac OS X Client {name} modified', 'de': 'Mac OS X Client {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_MACOS_MOVED = DiaryEvent('UDM_COMPUTERS_MACOS_MOVED', {'en': 'Mac OS X Client {name} moved to {position}', 'de': 'Mac OS X Client {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_MACOS_REMOVED = DiaryEvent('UDM_COMPUTERS_MACOS_REMOVED', {'en': 'Mac OS X Client {name} removed', 'de': 'Mac OS X Client {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_MEMBERSERVER_CREATED = DiaryEvent('UDM_COMPUTERS_MEMBERSERVER_CREATED', {'en': 'Member Server {name} created', 'de': 'Member-Server {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_MEMBERSERVER_MODIFIED = DiaryEvent('UDM_COMPUTERS_MEMBERSERVER_MODIFIED', {'en': 'Member Server {name} modified', 'de': 'Member-Server {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_MEMBERSERVER_MOVED = DiaryEvent('UDM_COMPUTERS_MEMBERSERVER_MOVED', {'en': 'Member Server {name} moved to {position}', 'de': 'Member-Server {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_MEMBERSERVER_REMOVED = DiaryEvent('UDM_COMPUTERS_MEMBERSERVER_REMOVED', {'en': 'Member Server {name} removed', 'de': 'Member-Server {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_TRUSTACCOUNT_CREATED = DiaryEvent('UDM_COMPUTERS_TRUSTACCOUNT_CREATED', {'en': 'Domain trust account {name} created', 'de': 'Domain Trust Account {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_TRUSTACCOUNT_MODIFIED = DiaryEvent('UDM_COMPUTERS_TRUSTACCOUNT_MODIFIED', {'en': 'Domain trust account {name} modified', 'de': 'Domain Trust Account {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_TRUSTACCOUNT_MOVED = DiaryEvent('UDM_COMPUTERS_TRUSTACCOUNT_MOVED', {'en': 'Domain trust account {name} moved to {position}', 'de': 'Domain Trust Account {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_TRUSTACCOUNT_REMOVED = DiaryEvent('UDM_COMPUTERS_TRUSTACCOUNT_REMOVED', {'en': 'Domain trust account {name} removed', 'de': 'Domain Trust Account {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_UBUNTU_CREATED = DiaryEvent('UDM_COMPUTERS_UBUNTU_CREATED', {'en': 'Ubuntu Computer {name} created', 'de': 'Ubuntu-Rechner {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_UBUNTU_MODIFIED = DiaryEvent('UDM_COMPUTERS_UBUNTU_MODIFIED', {'en': 'Ubuntu Computer {name} modified', 'de': 'Ubuntu-Rechner {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_UBUNTU_MOVED = DiaryEvent('UDM_COMPUTERS_UBUNTU_MOVED', {'en': 'Ubuntu Computer {name} moved to {position}', 'de': 'Ubuntu-Rechner {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_UBUNTU_REMOVED = DiaryEvent('UDM_COMPUTERS_UBUNTU_REMOVED', {'en': 'Ubuntu Computer {name} removed', 'de': 'Ubuntu-Rechner {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_WINDOWS_CREATED = DiaryEvent('UDM_COMPUTERS_WINDOWS_CREATED', {'en': 'Windows Workstation/Server {name} created', 'de': 'Windows Workstation/Server {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_MODIFIED = DiaryEvent('UDM_COMPUTERS_WINDOWS_MODIFIED', {'en': 'Windows Workstation/Server {name} modified', 'de': 'Windows Workstation/Server {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_MOVED = DiaryEvent('UDM_COMPUTERS_WINDOWS_MOVED', {'en': 'Windows Workstation/Server {name} moved to {position}', 'de': 'Windows Workstation/Server {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_REMOVED = DiaryEvent('UDM_COMPUTERS_WINDOWS_REMOVED', {'en': 'Windows Workstation/Server {name} removed', 'de': 'Windows Workstation/Server {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_CREATED = DiaryEvent('UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_CREATED', {'en': 'Windows Domaincontroller {name} created', 'de': 'Windows Domänencontroller {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MODIFIED = DiaryEvent('UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MODIFIED', {'en': 'Windows Domaincontroller {name} modified', 'de': 'Windows Domänencontroller {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MOVED = DiaryEvent('UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MOVED', {'en': 'Windows Domaincontroller {name} moved to {position}', 'de': 'Windows Domänencontroller {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_REMOVED = DiaryEvent('UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_REMOVED', {'en': 'Windows Domaincontroller {name} removed', 'de': 'Windows Domänencontroller {name} gelöscht'}, args=['name'], icon='devices')

UDM_CONTAINER_CN_CREATED = DiaryEvent('UDM_CONTAINER_CN_CREATED', {'en': 'Container {name} created', 'de': 'Container {name} angelegt'}, args=['name'], icon='domain')
UDM_CONTAINER_CN_MODIFIED = DiaryEvent('UDM_CONTAINER_CN_MODIFIED', {'en': 'Container {name} modified', 'de': 'Container {name} bearbeitet'}, args=['name'], icon='domain')
UDM_CONTAINER_CN_MOVED = DiaryEvent('UDM_CONTAINER_CN_MOVED', {'en': 'Container {name} moved to {position}', 'de': 'Container {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_CONTAINER_CN_REMOVED = DiaryEvent('UDM_CONTAINER_CN_REMOVED', {'en': 'Container {name} removed', 'de': 'Container {name} gelöscht'}, args=['name'], icon='domain')

UDM_CONTAINER_DC_MODIFIED = DiaryEvent('UDM_CONTAINER_DC_MODIFIED', {'en': 'Domain Container {name} modified', 'de': 'Domänen-Container {name} bearbeitet'}, args=['name'], icon='domain')

UDM_CONTAINER_OU_CREATED = DiaryEvent('UDM_CONTAINER_OU_CREATED', {'en': 'Organisational Unit {name} created', 'de': 'Organisationseinheit {name} angelegt'}, args=['name'], icon='domain')
UDM_CONTAINER_OU_MODIFIED = DiaryEvent('UDM_CONTAINER_OU_MODIFIED', {'en': 'Organisational Unit {name} modified', 'de': 'Organisationseinheit {name} bearbeitet'}, args=['name'], icon='domain')
UDM_CONTAINER_OU_MOVED = DiaryEvent('UDM_CONTAINER_OU_MOVED', {'en': 'Organisational Unit {name} moved to {position}', 'de': 'Organisationseinheit {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_CONTAINER_OU_REMOVED = DiaryEvent('UDM_CONTAINER_OU_REMOVED', {'en': 'Organisational Unit {name} removed', 'de': 'Organisationseinheit {name} gelöscht'}, args=['name'], icon='domain')

UDM_DHCP_HOST_CREATED = DiaryEvent('UDM_DHCP_HOST_CREATED', {'en': 'DHCP host {host} created', 'de': 'DHCP-Rechner {host} angelegt'}, args=['host'], icon='domain')
UDM_DHCP_HOST_MODIFIED = DiaryEvent('UDM_DHCP_HOST_MODIFIED', {'en': 'DHCP host {host} modified', 'de': 'DHCP-Rechner {host} bearbeitet'}, args=['host'], icon='domain')
UDM_DHCP_HOST_REMOVED = DiaryEvent('UDM_DHCP_HOST_REMOVED', {'en': 'DHCP host {host} removed', 'de': 'DHCP-Rechner {host} gelöscht'}, args=['host'], icon='domain')

UDM_DHCP_POOL_CREATED = DiaryEvent('UDM_DHCP_POOL_CREATED', {'en': 'DHCP pool {name} created', 'de': 'DHCP-Pool {name} angelegt'}, args=['name'], icon='domain')
UDM_DHCP_POOL_MODIFIED = DiaryEvent('UDM_DHCP_POOL_MODIFIED', {'en': 'DHCP pool {name} modified', 'de': 'DHCP-Pool {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DHCP_POOL_REMOVED = DiaryEvent('UDM_DHCP_POOL_REMOVED', {'en': 'DHCP pool {name} removed', 'de': 'DHCP-Pool {name} gelöscht'}, args=['name'], icon='domain')

UDM_DHCP_SERVER_CREATED = DiaryEvent('UDM_DHCP_SERVER_CREATED', {'en': 'DHCP server {server} created', 'de': 'DHCP-Server {server} angelegt'}, args=['server'], icon='domain')
UDM_DHCP_SERVER_MODIFIED = DiaryEvent('UDM_DHCP_SERVER_MODIFIED', {'en': 'DHCP server {server} modified', 'de': 'DHCP-Server {server} bearbeitet'}, args=['server'], icon='domain')
UDM_DHCP_SERVER_REMOVED = DiaryEvent('UDM_DHCP_SERVER_REMOVED', {'en': 'DHCP server {server} removed', 'de': 'DHCP-Server {server} gelöscht'}, args=['server'], icon='domain')

UDM_DHCP_SERVICE_CREATED = DiaryEvent('UDM_DHCP_SERVICE_CREATED', {'en': 'DHCP service {service} created', 'de': 'DHCP-Dienst {service} angelegt'}, args=['service'], icon='domain')
UDM_DHCP_SERVICE_MODIFIED = DiaryEvent('UDM_DHCP_SERVICE_MODIFIED', {'en': 'DHCP service {service} modified', 'de': 'DHCP-Dienst {service} bearbeitet'}, args=['service'], icon='domain')
UDM_DHCP_SERVICE_REMOVED = DiaryEvent('UDM_DHCP_SERVICE_REMOVED', {'en': 'DHCP service {service} removed', 'de': 'DHCP-Dienst {service} gelöscht'}, args=['service'], icon='domain')

UDM_DHCP_SHARED_CREATED = DiaryEvent('UDM_DHCP_SHARED_CREATED', {'en': 'Shared network {name} created', 'de': 'Shared Network {name} angelegt'}, args=['name'], icon='domain')
UDM_DHCP_SHARED_MODIFIED = DiaryEvent('UDM_DHCP_SHARED_MODIFIED', {'en': 'Shared network {name} modified', 'de': 'Shared Network {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DHCP_SHARED_REMOVED = DiaryEvent('UDM_DHCP_SHARED_REMOVED', {'en': 'Shared network {name} removed', 'de': 'Shared Network {name} gelöscht'}, args=['name'], icon='domain')

UDM_DHCP_SHAREDSUBNET_CREATED = DiaryEvent('UDM_DHCP_SHAREDSUBNET_CREATED', {'en': 'Shared DHCP subnet {subnet} created', 'de': 'Shared DHCP-Subnetz {subnet} angelegt'}, args=['subnet'], icon='domain')
UDM_DHCP_SHAREDSUBNET_MODIFIED = DiaryEvent('UDM_DHCP_SHAREDSUBNET_MODIFIED', {'en': 'Shared DHCP subnet {subnet} modified', 'de': 'Shared DHCP-Subnetz {subnet} bearbeitet'}, args=['subnet'], icon='domain')
UDM_DHCP_SHAREDSUBNET_REMOVED = DiaryEvent('UDM_DHCP_SHAREDSUBNET_REMOVED', {'en': 'Shared DHCP subnet {subnet} removed', 'de': 'Shared DHCP-Subnetz {subnet} gelöscht'}, args=['subnet'], icon='domain')

UDM_DHCP_SUBNET_CREATED = DiaryEvent('UDM_DHCP_SUBNET_CREATED', {'en': 'DHCP subnet {subnet} created', 'de': 'DHCP-Subnetz {subnet} angelegt'}, args=['subnet'], icon='domain')
UDM_DHCP_SUBNET_MODIFIED = DiaryEvent('UDM_DHCP_SUBNET_MODIFIED', {'en': 'DHCP subnet {subnet} modified', 'de': 'DHCP-Subnetz {subnet} bearbeitet'}, args=['subnet'], icon='domain')
UDM_DHCP_SUBNET_REMOVED = DiaryEvent('UDM_DHCP_SUBNET_REMOVED', {'en': 'DHCP subnet {subnet} removed', 'de': 'DHCP-Subnetz {subnet} gelöscht'}, args=['subnet'], icon='domain')

UDM_DNS_ALIAS_CREATED = DiaryEvent('UDM_DNS_ALIAS_CREATED', {'en': 'Alias record {name} created', 'de': 'Alias Record {name} angelegt'}, args=['name'], icon='domain')
UDM_DNS_ALIAS_MODIFIED = DiaryEvent('UDM_DNS_ALIAS_MODIFIED', {'en': 'Alias record {name} modified', 'de': 'Alias Record {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DNS_ALIAS_REMOVED = DiaryEvent('UDM_DNS_ALIAS_REMOVED', {'en': 'Alias record {name} removed', 'de': 'Alias Record {name} gelöscht'}, args=['name'], icon='domain')

UDM_DNS_FORWARD_ZONE_CREATED = DiaryEvent('UDM_DNS_FORWARD_ZONE_CREATED', {'en': 'Forward lookup zone {zone} created', 'de': 'Forward Lookup Zone {zone} angelegt'}, args=['zone'], icon='domain')
UDM_DNS_FORWARD_ZONE_MODIFIED = DiaryEvent('UDM_DNS_FORWARD_ZONE_MODIFIED', {'en': 'Forward lookup zone {zone} modified', 'de': 'Forward Lookup Zone {zone} bearbeitet'}, args=['zone'], icon='domain')
UDM_DNS_FORWARD_ZONE_REMOVED = DiaryEvent('UDM_DNS_FORWARD_ZONE_REMOVED', {'en': 'Forward lookup zone {zone} removed', 'de': 'Forward Lookup Zone {zone} gelöscht'}, args=['zone'], icon='domain')

UDM_DNS_HOST_RECORD_CREATED = DiaryEvent('UDM_DNS_HOST_RECORD_CREATED', {'en': 'Host record {name} created', 'de': 'Host Record {name} angelegt'}, args=['name'], icon='domain')
UDM_DNS_HOST_RECORD_MODIFIED = DiaryEvent('UDM_DNS_HOST_RECORD_MODIFIED', {'en': 'Host record {name} modified', 'de': 'Host Record {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DNS_HOST_RECORD_REMOVED = DiaryEvent('UDM_DNS_HOST_RECORD_REMOVED', {'en': 'Host record {name} removed', 'de': 'Host Record {name} gelöscht'}, args=['name'], icon='domain')

UDM_DNS_NS_RECORD_CREATED = DiaryEvent('UDM_DNS_NS_RECORD_CREATED', {'en': 'Nameserver record {zone} created', 'de': 'Nameserver record {zone} angelegt'}, args=['zone'], icon='domain')
UDM_DNS_NS_RECORD_MODIFIED = DiaryEvent('UDM_DNS_NS_RECORD_MODIFIED', {'en': 'Nameserver record {zone} modified', 'de': 'Nameserver record {zone} bearbeitet'}, args=['zone'], icon='domain')
UDM_DNS_NS_RECORD_REMOVED = DiaryEvent('UDM_DNS_NS_RECORD_REMOVED', {'en': 'Nameserver record {zone} removed', 'de': 'Nameserver record {zone} gelöscht'}, args=['zone'], icon='domain')

UDM_DNS_PTR_RECORD_CREATED = DiaryEvent('UDM_DNS_PTR_RECORD_CREATED', {'en': 'Pointer record {address} created', 'de': 'Pointer Record {address} angelegt'}, args=['address'], icon='domain')
UDM_DNS_PTR_RECORD_MODIFIED = DiaryEvent('UDM_DNS_PTR_RECORD_MODIFIED', {'en': 'Pointer record {address} modified', 'de': 'Pointer Record {address} bearbeitet'}, args=['address'], icon='domain')
UDM_DNS_PTR_RECORD_REMOVED = DiaryEvent('UDM_DNS_PTR_RECORD_REMOVED', {'en': 'Pointer record {address} removed', 'de': 'Pointer Record {address} gelöscht'}, args=['address'], icon='domain')

UDM_DNS_REVERSE_ZONE_CREATED = DiaryEvent('UDM_DNS_REVERSE_ZONE_CREATED', {'en': 'Reverse lookup zone {subnet} created', 'de': 'Reverse Lookup Zone {subnet} angelegt'}, args=['subnet'], icon='domain')
UDM_DNS_REVERSE_ZONE_MODIFIED = DiaryEvent('UDM_DNS_REVERSE_ZONE_MODIFIED', {'en': 'Reverse lookup zone {subnet} modified', 'de': 'Reverse Lookup Zone {subnet} bearbeitet'}, args=['subnet'], icon='domain')
UDM_DNS_REVERSE_ZONE_REMOVED = DiaryEvent('UDM_DNS_REVERSE_ZONE_REMOVED', {'en': 'Reverse lookup zone {subnet} removed', 'de': 'Reverse Lookup Zone {subnet} gelöscht'}, args=['subnet'], icon='domain')

UDM_DNS_SRV_RECORD_CREATED = DiaryEvent('UDM_DNS_SRV_RECORD_CREATED', {'en': 'Service record {name} created', 'de': 'Service Record {name} angelegt'}, args=['name'], icon='domain')
UDM_DNS_SRV_RECORD_MODIFIED = DiaryEvent('UDM_DNS_SRV_RECORD_MODIFIED', {'en': 'Service record {name} modified', 'de': 'Service Record {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DNS_SRV_RECORD_REMOVED = DiaryEvent('UDM_DNS_SRV_RECORD_REMOVED', {'en': 'Service record {name} removed', 'de': 'Service Record {name} gelöscht'}, args=['name'], icon='domain')

UDM_DNS_TXT_RECORD_CREATED = DiaryEvent('UDM_DNS_TXT_RECORD_CREATED', {'en': 'TXT record {name} created', 'de': 'TXT Record {name} angelegt'}, args=['name'], icon='domain')
UDM_DNS_TXT_RECORD_MODIFIED = DiaryEvent('UDM_DNS_TXT_RECORD_MODIFIED', {'en': 'TXT record {name} modified', 'de': 'TXT Record {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DNS_TXT_RECORD_REMOVED = DiaryEvent('UDM_DNS_TXT_RECORD_REMOVED', {'en': 'TXT record {name} removed', 'de': 'TXT Record {name} gelöscht'}, args=['name'], icon='domain')

UDM_GROUPS_GROUP_CREATED = DiaryEvent('UDM_GROUPS_GROUP_CREATED', {'en': 'Group {name} created', 'de': 'Gruppe {name} angelegt'}, args=['name'], icon='users')
UDM_GROUPS_GROUP_MODIFIED = DiaryEvent('UDM_GROUPS_GROUP_MODIFIED', {'en': 'Group {name} modified', 'de': 'Gruppe {name} bearbeitet'}, args=['name'], icon='users')
UDM_GROUPS_GROUP_MOVED = DiaryEvent('UDM_GROUPS_GROUP_MOVED', {'en': 'Group {name} moved to {position}', 'de': 'Gruppe {name} verschoben nach {position}'}, args=['name'], icon='users')
UDM_GROUPS_GROUP_REMOVED = DiaryEvent('UDM_GROUPS_GROUP_REMOVED', {'en': 'Group {name} removed', 'de': 'Gruppe {name} gelöscht'}, args=['name'], icon='users')

UDM_KERBEROS_KDCENTRY_CREATED = DiaryEvent('UDM_KERBEROS_KDCENTRY_CREATED', {'en': 'KDC Entry {name} created', 'de': 'KDC-Eintrag {name} angelegt'}, args=['name'], icon='domain')
UDM_KERBEROS_KDCENTRY_MODIFIED = DiaryEvent('UDM_KERBEROS_KDCENTRY_MODIFIED', {'en': 'KDC Entry {name} modified', 'de': 'KDC-Eintrag {name} bearbeitet'}, args=['name'], icon='domain')
UDM_KERBEROS_KDCENTRY_MOVED = DiaryEvent('UDM_KERBEROS_KDCENTRY_MOVED', {'en': 'KDC Entry {name} moved to {position}', 'de': 'KDC-Eintrag {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_KERBEROS_KDCENTRY_REMOVED = DiaryEvent('UDM_KERBEROS_KDCENTRY_REMOVED', {'en': 'KDC Entry {name} removed', 'de': 'KDC-Eintrag {name} gelöscht'}, args=['name'], icon='domain')

UDM_MAIL_DOMAIN_CREATED = DiaryEvent('UDM_MAIL_DOMAIN_CREATED', {'en': 'Mail domain {name} created', 'de': 'Mail-Domäne {name} angelegt'}, args=['name'], icon='domain')
UDM_MAIL_DOMAIN_MODIFIED = DiaryEvent('UDM_MAIL_DOMAIN_MODIFIED', {'en': 'Mail domain {name} modified', 'de': 'Mail-Domäne {name} bearbeitet'}, args=['name'], icon='domain')
UDM_MAIL_DOMAIN_MOVED = DiaryEvent('UDM_MAIL_DOMAIN_MOVED', {'en': 'Mail domain {name} moved to {position}', 'de': 'Mail-Domäne {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_MAIL_DOMAIN_REMOVED = DiaryEvent('UDM_MAIL_DOMAIN_REMOVED', {'en': 'Mail domain {name} removed', 'de': 'Mail-Domäne {name} gelöscht'}, args=['name'], icon='domain')

UDM_MAIL_FOLDER_CREATED = DiaryEvent('UDM_MAIL_FOLDER_CREATED', {'en': 'IMAP mail folder {nameWithMailDomain} created', 'de': 'IMAP-Mail-Ordner {nameWithMailDomain} angelegt'}, args=['nameWithMailDomain'], icon='domain')
UDM_MAIL_FOLDER_MODIFIED = DiaryEvent('UDM_MAIL_FOLDER_MODIFIED', {'en': 'IMAP mail folder {nameWithMailDomain} modified', 'de': 'IMAP-Mail-Ordner {nameWithMailDomain} bearbeitet'}, args=['nameWithMailDomain'], icon='domain')
UDM_MAIL_FOLDER_REMOVED = DiaryEvent('UDM_MAIL_FOLDER_REMOVED', {'en': 'IMAP mail folder {nameWithMailDomain} removed', 'de': 'IMAP-Mail-Ordner {nameWithMailDomain} gelöscht'}, args=['nameWithMailDomain'], icon='domain')

UDM_MAIL_LISTS_CREATED = DiaryEvent('UDM_MAIL_LISTS_CREATED', {'en': 'Mailing list {name} created', 'de': 'Mailingliste {name} angelegt'}, args=['name'], icon='domain')
UDM_MAIL_LISTS_MODIFIED = DiaryEvent('UDM_MAIL_LISTS_MODIFIED', {'en': 'Mailing list {name} modified', 'de': 'Mailingliste {name} bearbeitet'}, args=['name'], icon='domain')
UDM_MAIL_LISTS_MOVED = DiaryEvent('UDM_MAIL_LISTS_MOVED', {'en': 'Mailing list {name} moved to {position}', 'de': 'Mailingliste {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_MAIL_LISTS_REMOVED = DiaryEvent('UDM_MAIL_LISTS_REMOVED', {'en': 'Mailing list {name} removed', 'de': 'Mailingliste {name} gelöscht'}, args=['name'], icon='domain')

UDM_NAGIOS_SERVICE_CREATED = DiaryEvent('UDM_NAGIOS_SERVICE_CREATED', {'en': 'Nagios service {name} created', 'de': 'Nagios-Dienst {name} angelegt'}, args=['name'], icon='devices')
UDM_NAGIOS_SERVICE_MODIFIED = DiaryEvent('UDM_NAGIOS_SERVICE_MODIFIED', {'en': 'Nagios service {name} modified', 'de': 'Nagios-Dienst {name} bearbeitet'}, args=['name'], icon='devices')
UDM_NAGIOS_SERVICE_REMOVED = DiaryEvent('UDM_NAGIOS_SERVICE_REMOVED', {'en': 'Nagios service {name} removed', 'de': 'Nagios-Dienst {name} gelöscht'}, args=['name'], icon='devices')

UDM_NAGIOS_TIMEPERIOD_CREATED = DiaryEvent('UDM_NAGIOS_TIMEPERIOD_CREATED', {'en': 'Nagios time period {name} created', 'de': 'Nagios-Zeitraum {name} angelegt'}, args=['name'], icon='devices')
UDM_NAGIOS_TIMEPERIOD_MODIFIED = DiaryEvent('UDM_NAGIOS_TIMEPERIOD_MODIFIED', {'en': 'Nagios time period {name} modified', 'de': 'Nagios-Zeitraum {name} bearbeitet'}, args=['name'], icon='devices')
UDM_NAGIOS_TIMEPERIOD_REMOVED = DiaryEvent('UDM_NAGIOS_TIMEPERIOD_REMOVED', {'en': 'Nagios time period {name} removed', 'de': 'Nagios-Zeitraum {name} gelöscht'}, args=['name'], icon='devices')

UDM_NETWORKS_NETWORK_CREATED = DiaryEvent('UDM_NETWORKS_NETWORK_CREATED', {'en': 'Network {name} ({netmask} {network}) created', 'de': 'Netzwerk {name} ({netmask} {network}) angelegt'}, args=['name', 'netmask', 'network'], icon='domain')
UDM_NETWORKS_NETWORK_MODIFIED = DiaryEvent('UDM_NETWORKS_NETWORK_MODIFIED', {'en': 'Network {name} ({netmask} {network}) modified', 'de': 'Netzwerk {name} ({netmask} {network}) bearbeitet'}, args=['name', 'netmask', 'network'], icon='domain')
UDM_NETWORKS_NETWORK_REMOVED = DiaryEvent('UDM_NETWORKS_NETWORK_REMOVED', {'en': 'Network {name} ({netmask} {network}) removed', 'de': 'Netzwerk {name} ({netmask} {network}) gelöscht'}, args=['name', 'netmask', 'network'], icon='domain')

UDM_POLICIES_ADMIN_CONTAINER_CREATED = DiaryEvent('UDM_POLICIES_ADMIN_CONTAINER_CREATED', {'en': 'Univention Directory Manager container settings policy {name} created', 'de': 'Univention Directory Manager Container Konfiguration-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_ADMIN_CONTAINER_MODIFIED = DiaryEvent('UDM_POLICIES_ADMIN_CONTAINER_MODIFIED', {'en': 'Univention Directory Manager container settings policy {name} modified', 'de': 'Univention Directory Manager Container Konfiguration-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_ADMIN_CONTAINER_REMOVED = DiaryEvent('UDM_POLICIES_ADMIN_CONTAINER_REMOVED', {'en': 'Univention Directory Manager container settings policy {name} removed', 'de': 'Univention Directory Manager Container Konfiguration-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_AUTOSTART_CREATED = DiaryEvent('UDM_POLICIES_AUTOSTART_CREATED', {'en': 'Autostart policy {name} created', 'de': 'Autostart-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_AUTOSTART_MODIFIED = DiaryEvent('UDM_POLICIES_AUTOSTART_MODIFIED', {'en': 'Autostart policy {name} modified', 'de': 'Autostart-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_AUTOSTART_REMOVED = DiaryEvent('UDM_POLICIES_AUTOSTART_REMOVED', {'en': 'Autostart policy {name} removed', 'de': 'Autostart-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DESKTOP_CREATED = DiaryEvent('UDM_POLICIES_DESKTOP_CREATED', {'en': 'Desktop policy {name} created', 'de': 'Desktop-Profil-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DESKTOP_MODIFIED = DiaryEvent('UDM_POLICIES_DESKTOP_MODIFIED', {'en': 'Desktop policy {name} modified', 'de': 'Desktop-Profil-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DESKTOP_REMOVED = DiaryEvent('UDM_POLICIES_DESKTOP_REMOVED', {'en': 'Desktop policy {name} removed', 'de': 'Desktop-Profil-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_BOOT_CREATED = DiaryEvent('UDM_POLICIES_DHCP_BOOT_CREATED', {'en': 'DHCP Boot policy {name} created', 'de': 'DHCP Boot-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_BOOT_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_BOOT_MODIFIED', {'en': 'DHCP Boot policy {name} modified', 'de': 'DHCP Boot-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_BOOT_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_BOOT_REMOVED', {'en': 'DHCP Boot policy {name} removed', 'de': 'DHCP Boot-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_DNS_CREATED = DiaryEvent('UDM_POLICIES_DHCP_DNS_CREATED', {'en': 'DHCP DNS policy {name} created', 'de': 'DHCP DNS-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_DNS_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_DNS_MODIFIED', {'en': 'DHCP DNS policy {name} modified', 'de': 'DHCP DNS-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_DNS_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_DNS_REMOVED', {'en': 'DHCP DNS policy {name} removed', 'de': 'DHCP DNS-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_DNSUPDATE_CREATED = DiaryEvent('UDM_POLICIES_DHCP_DNSUPDATE_CREATED', {'en': 'DHCP Dynamic DNS policy {name} created', 'de': 'DHCP DNS Aktualisierungs-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_DNSUPDATE_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_DNSUPDATE_MODIFIED', {'en': 'DHCP Dynamic DNS policy {name} modified', 'de': 'DHCP DNS Aktualisierungs-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_DNSUPDATE_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_DNSUPDATE_REMOVED', {'en': 'DHCP Dynamic DNS policy {name} removed', 'de': 'DHCP DNS Aktualisierungs-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_LEASETIME_CREATED = DiaryEvent('UDM_POLICIES_DHCP_LEASETIME_CREATED', {'en': 'DHCP lease time policy {name} created', 'de': 'DHCP Lease-Zeit-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_LEASETIME_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_LEASETIME_MODIFIED', {'en': 'DHCP lease time policy {name} modified', 'de': 'DHCP Lease-Zeit-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_LEASETIME_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_LEASETIME_REMOVED', {'en': 'DHCP lease time policy {name} removed', 'de': 'DHCP Lease-Zeit-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_NETBIOS_CREATED = DiaryEvent('UDM_POLICIES_DHCP_NETBIOS_CREATED', {'en': 'DHCP NetBIOS policy {name} created', 'de': 'DHCP NetBIOS-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_NETBIOS_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_NETBIOS_MODIFIED', {'en': 'DHCP NetBIOS policy {name} modified', 'de': 'DHCP NetBIOS-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_NETBIOS_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_NETBIOS_REMOVED', {'en': 'DHCP NetBIOS policy {name} removed', 'de': 'DHCP NetBIOS-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_ROUTING_CREATED = DiaryEvent('UDM_POLICIES_DHCP_ROUTING_CREATED', {'en': 'DHCP routing policy {name} created', 'de': 'DHCP Routing-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_ROUTING_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_ROUTING_MODIFIED', {'en': 'DHCP routing policy {name} modified', 'de': 'DHCP Routing-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_ROUTING_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_ROUTING_REMOVED', {'en': 'DHCP routing policy {name} removed', 'de': 'DHCP Routing-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_SCOPE_CREATED = DiaryEvent('UDM_POLICIES_DHCP_SCOPE_CREATED', {'en': 'DHCP Allow/Deny policy {name} created', 'de': 'DHCP Erlauben/Verbieten-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_SCOPE_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_SCOPE_MODIFIED', {'en': 'DHCP Allow/Deny policy {name} modified', 'de': 'DHCP Erlauben/Verbieten-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_SCOPE_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_SCOPE_REMOVED', {'en': 'DHCP Allow/Deny policy {name} removed', 'de': 'DHCP Erlauben/Verbieten-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_STATEMENTS_CREATED = DiaryEvent('UDM_POLICIES_DHCP_STATEMENTS_CREATED', {'en': 'DHCP statements policy {name} created', 'de': 'DHCP Verschiedenes-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_STATEMENTS_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_STATEMENTS_MODIFIED', {'en': 'DHCP statements policy {name} modified', 'de': 'DHCP Verschiedenes-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_STATEMENTS_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_STATEMENTS_REMOVED', {'en': 'DHCP statements policy {name} removed', 'de': 'DHCP Verschiedenes-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_LDAPSERVER_CREATED = DiaryEvent('UDM_POLICIES_LDAPSERVER_CREATED', {'en': 'LDAP server policy {name} created', 'de': 'LDAP-Server-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_LDAPSERVER_MODIFIED = DiaryEvent('UDM_POLICIES_LDAPSERVER_MODIFIED', {'en': 'LDAP server policy {name} modified', 'de': 'LDAP-Server-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_LDAPSERVER_REMOVED = DiaryEvent('UDM_POLICIES_LDAPSERVER_REMOVED', {'en': 'LDAP server policy {name} removed', 'de': 'LDAP-Server-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_MAINTENANCE_CREATED = DiaryEvent('UDM_POLICIES_MAINTENANCE_CREATED', {'en': 'Maintenance policy {name} created', 'de': 'Paketpflege-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_MAINTENANCE_MODIFIED = DiaryEvent('UDM_POLICIES_MAINTENANCE_MODIFIED', {'en': 'Maintenance policy {name} modified', 'de': 'Paketpflege-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_MAINTENANCE_REMOVED = DiaryEvent('UDM_POLICIES_MAINTENANCE_REMOVED', {'en': 'Maintenance policy {name} removed', 'de': 'Paketpflege-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_MASTERPACKAGES_CREATED = DiaryEvent('UDM_POLICIES_MASTERPACKAGES_CREATED', {'en': 'Master packages policy {name} created', 'de': 'Master Pakete-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_MASTERPACKAGES_MODIFIED = DiaryEvent('UDM_POLICIES_MASTERPACKAGES_MODIFIED', {'en': 'Master packages policy {name} modified', 'de': 'Master Pakete-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_MASTERPACKAGES_REMOVED = DiaryEvent('UDM_POLICIES_MASTERPACKAGES_REMOVED', {'en': 'Master packages policy {name} removed', 'de': 'Master Pakete-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_MEMBERPACKAGES_CREATED = DiaryEvent('UDM_POLICIES_MEMBERPACKAGES_CREATED', {'en': 'Member Server packages policy {name} created', 'de': 'Memberserver Pakete-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_MEMBERPACKAGES_MODIFIED = DiaryEvent('UDM_POLICIES_MEMBERPACKAGES_MODIFIED', {'en': 'Member Server packages policy {name} modified', 'de': 'Memberserver Pakete-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_MEMBERPACKAGES_REMOVED = DiaryEvent('UDM_POLICIES_MEMBERPACKAGES_REMOVED', {'en': 'Member Server packages policy {name} removed', 'de': 'Memberserver Pakete-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_NFSMOUNTS_CREATED = DiaryEvent('UDM_POLICIES_NFSMOUNTS_CREATED', {'en': 'NFS mounts policy {name} created', 'de': 'NFS-Freigaben-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_NFSMOUNTS_MODIFIED = DiaryEvent('UDM_POLICIES_NFSMOUNTS_MODIFIED', {'en': 'NFS mounts policy {name} modified', 'de': 'NFS-Freigaben-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_NFSMOUNTS_REMOVED = DiaryEvent('UDM_POLICIES_NFSMOUNTS_REMOVED', {'en': 'NFS mounts policy {name} removed', 'de': 'NFS-Freigaben-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_PRINT_QUOTA_CREATED = DiaryEvent('UDM_POLICIES_PRINT_QUOTA_CREATED', {'en': 'Print quota policy {name} created', 'de': 'Druck-Quota-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_PRINT_QUOTA_MODIFIED = DiaryEvent('UDM_POLICIES_PRINT_QUOTA_MODIFIED', {'en': 'Print quota policy {name} modified', 'de': 'Druck-Quota-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_PRINT_QUOTA_REMOVED = DiaryEvent('UDM_POLICIES_PRINT_QUOTA_REMOVED', {'en': 'Print quota policy {name} removed', 'de': 'Druck-Quota-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_PRINTSERVER_CREATED = DiaryEvent('UDM_POLICIES_PRINTSERVER_CREATED', {'en': 'Print server policy {name} created', 'de': 'Druckserver-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_PRINTSERVER_MODIFIED = DiaryEvent('UDM_POLICIES_PRINTSERVER_MODIFIED', {'en': 'Print server policy {name} modified', 'de': 'Druckserver-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_PRINTSERVER_REMOVED = DiaryEvent('UDM_POLICIES_PRINTSERVER_REMOVED', {'en': 'Print server policy {name} removed', 'de': 'Druckserver-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_PWHISTORY_CREATED = DiaryEvent('UDM_POLICIES_PWHISTORY_CREATED', {'en': 'Passwords policy {name} created', 'de': 'Passwort-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_PWHISTORY_MODIFIED = DiaryEvent('UDM_POLICIES_PWHISTORY_MODIFIED', {'en': 'Passwords policy {name} modified', 'de': 'Passwort-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_PWHISTORY_REMOVED = DiaryEvent('UDM_POLICIES_PWHISTORY_REMOVED', {'en': 'Passwords policy {name} removed', 'de': 'Passwort-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_REGISTRY_CREATED = DiaryEvent('UDM_POLICIES_REGISTRY_CREATED', {'en': 'Univention Configuration Registry policy {name} created', 'de': 'Univention Configuration Registry-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_REGISTRY_MODIFIED = DiaryEvent('UDM_POLICIES_REGISTRY_MODIFIED', {'en': 'Univention Configuration Registry policy {name} modified', 'de': 'Univention Configuration Registry-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_REGISTRY_REMOVED = DiaryEvent('UDM_POLICIES_REGISTRY_REMOVED', {'en': 'Univention Configuration Registry policy {name} removed', 'de': 'Univention Configuration Registry-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_RELEASE_CREATED = DiaryEvent('UDM_POLICIES_RELEASE_CREATED', {'en': 'Automatic updates policy {name} created', 'de': 'Automatische Updates-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_RELEASE_MODIFIED = DiaryEvent('UDM_POLICIES_RELEASE_MODIFIED', {'en': 'Automatic updates policy {name} modified', 'de': 'Automatische Updates-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_RELEASE_REMOVED = DiaryEvent('UDM_POLICIES_RELEASE_REMOVED', {'en': 'Automatic updates policy {name} removed', 'de': 'Automatische Updates-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_REPOSITORYSERVER_CREATED = DiaryEvent('UDM_POLICIES_REPOSITORYSERVER_CREATED', {'en': 'Repository server policy {name} created', 'de': 'Repository-Server-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_REPOSITORYSERVER_MODIFIED = DiaryEvent('UDM_POLICIES_REPOSITORYSERVER_MODIFIED', {'en': 'Repository server policy {name} modified', 'de': 'Repository-Server-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_REPOSITORYSERVER_REMOVED = DiaryEvent('UDM_POLICIES_REPOSITORYSERVER_REMOVED', {'en': 'Repository server policy {name} removed', 'de': 'Repository-Server-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_REPOSITORYSYNC_CREATED = DiaryEvent('UDM_POLICIES_REPOSITORYSYNC_CREATED', {'en': 'Repository synchronisation policy {name} created', 'de': 'Repository-Synchronisation-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_REPOSITORYSYNC_MODIFIED = DiaryEvent('UDM_POLICIES_REPOSITORYSYNC_MODIFIED', {'en': 'Repository synchronisation policy {name} modified', 'de': 'Repository-Synchronisation-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_REPOSITORYSYNC_REMOVED = DiaryEvent('UDM_POLICIES_REPOSITORYSYNC_REMOVED', {'en': 'Repository synchronisation policy {name} removed', 'de': 'Repository-Synchronisation-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_SHARE_USERQUOTA_CREATED = DiaryEvent('UDM_POLICIES_SHARE_USERQUOTA_CREATED', {'en': 'User quota policy {name} created', 'de': 'Benutzer-Quota-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_SHARE_USERQUOTA_MODIFIED = DiaryEvent('UDM_POLICIES_SHARE_USERQUOTA_MODIFIED', {'en': 'User quota policy {name} modified', 'de': 'Benutzer-Quota-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_SHARE_USERQUOTA_REMOVED = DiaryEvent('UDM_POLICIES_SHARE_USERQUOTA_REMOVED', {'en': 'User quota policy {name} removed', 'de': 'Benutzer-Quota-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_SLAVEPACKAGES_CREATED = DiaryEvent('UDM_POLICIES_SLAVEPACKAGES_CREATED', {'en': 'Slave packages policy {name} created', 'de': 'Slave Pakete-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_SLAVEPACKAGES_MODIFIED = DiaryEvent('UDM_POLICIES_SLAVEPACKAGES_MODIFIED', {'en': 'Slave packages policy {name} modified', 'de': 'Slave Pakete-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_SLAVEPACKAGES_REMOVED = DiaryEvent('UDM_POLICIES_SLAVEPACKAGES_REMOVED', {'en': 'Slave packages policy {name} removed', 'de': 'Slave Pakete-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_UMC_CREATED = DiaryEvent('UDM_POLICIES_UMC_CREATED', {'en': 'UMC policy {name} created', 'de': 'UMC-Richtlinie {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_UMC_MODIFIED = DiaryEvent('UDM_POLICIES_UMC_MODIFIED', {'en': 'UMC policy {name} modified', 'de': 'UMC-Richtlinie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_UMC_REMOVED = DiaryEvent('UDM_POLICIES_UMC_REMOVED', {'en': 'UMC policy {name} removed', 'de': 'UMC-Richtlinie {name} gelöscht'}, args=['name'], icon='domain')

UDM_SAML_IDPCONFIG_CREATED = DiaryEvent('UDM_SAML_IDPCONFIG_CREATED', {'en': 'SAML IdP configuration {id} created', 'de': 'SAML IdP-Konfiguration {id} angelegt'}, args=['id'], icon='domain')
UDM_SAML_IDPCONFIG_MODIFIED = DiaryEvent('UDM_SAML_IDPCONFIG_MODIFIED', {'en': 'SAML IdP configuration {id} modified', 'de': 'SAML IdP-Konfiguration {id} bearbeitet'}, args=['id'], icon='domain')
UDM_SAML_IDPCONFIG_REMOVED = DiaryEvent('UDM_SAML_IDPCONFIG_REMOVED', {'en': 'SAML IdP configuration {id} removed', 'de': 'SAML IdP-Konfiguration {id} gelöscht'}, args=['id'], icon='domain')

UDM_SAML_SERVICEPROVIDER_CREATED = DiaryEvent('UDM_SAML_SERVICEPROVIDER_CREATED', {'en': 'SAML service provider {Identifier} created', 'de': 'SAML service provider {Identifier} angelegt'}, args=['Identifier'], icon='domain')
UDM_SAML_SERVICEPROVIDER_MODIFIED = DiaryEvent('UDM_SAML_SERVICEPROVIDER_MODIFIED', {'en': 'SAML service provider {Identifier} modified', 'de': 'SAML service provider {Identifier} bearbeitet'}, args=['Identifier'], icon='domain')
UDM_SAML_SERVICEPROVIDER_REMOVED = DiaryEvent('UDM_SAML_SERVICEPROVIDER_REMOVED', {'en': 'SAML service provider {Identifier} removed', 'de': 'SAML service provider {Identifier} gelöscht'}, args=['Identifier'], icon='domain')

UDM_SETTINGS_DATA_CREATED = DiaryEvent('UDM_SETTINGS_DATA_CREATED', {'en': 'Data {name} created', 'de': 'Data {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_DATA_MODIFIED = DiaryEvent('UDM_SETTINGS_DATA_MODIFIED', {'en': 'Data {name} modified', 'de': 'Data {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_DATA_MOVED = DiaryEvent('UDM_SETTINGS_DATA_MOVED', {'en': 'Data {name} moved to {position}', 'de': 'Data {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_DATA_REMOVED = DiaryEvent('UDM_SETTINGS_DATA_REMOVED', {'en': 'Data {name} removed', 'de': 'Data {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_DEFAULT_MODIFIED = DiaryEvent('UDM_SETTINGS_DEFAULT_MODIFIED', {'en': 'Default preference {name} modified', 'de': 'Standard Einstellung {name} bearbeitet'}, args=['name'], icon='domain')

UDM_SETTINGS_DIRECTORY_MODIFIED = DiaryEvent('UDM_SETTINGS_DIRECTORY_MODIFIED', {'en': 'Default container {name} modified', 'de': 'Standard-Container {name} bearbeitet'}, args=['name'], icon='domain')

UDM_SETTINGS_EXTENDED_ATTRIBUTE_CREATED = DiaryEvent('UDM_SETTINGS_EXTENDED_ATTRIBUTE_CREATED', {'en': 'Extended attribute {name} created', 'de': 'Erweitertes Attribut {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_ATTRIBUTE_MODIFIED = DiaryEvent('UDM_SETTINGS_EXTENDED_ATTRIBUTE_MODIFIED', {'en': 'Extended attribute {name} modified', 'de': 'Erweitertes Attribut {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_ATTRIBUTE_MOVED = DiaryEvent('UDM_SETTINGS_EXTENDED_ATTRIBUTE_MOVED', {'en': 'Extended attribute {name} moved to {position}', 'de': 'Erweitertes Attribut {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_ATTRIBUTE_REMOVED = DiaryEvent('UDM_SETTINGS_EXTENDED_ATTRIBUTE_REMOVED', {'en': 'Extended attribute {name} removed', 'de': 'Erweitertes Attribut {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_EXTENDED_OPTIONS_CREATED = DiaryEvent('UDM_SETTINGS_EXTENDED_OPTIONS_CREATED', {'en': 'Extended option {name} created', 'de': 'Erweiterte Option {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_OPTIONS_MODIFIED = DiaryEvent('UDM_SETTINGS_EXTENDED_OPTIONS_MODIFIED', {'en': 'Extended option {name} modified', 'de': 'Erweiterte Option {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_OPTIONS_MOVED = DiaryEvent('UDM_SETTINGS_EXTENDED_OPTIONS_MOVED', {'en': 'Extended option {name} moved to {position}', 'de': 'Erweiterte Option {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_OPTIONS_REMOVED = DiaryEvent('UDM_SETTINGS_EXTENDED_OPTIONS_REMOVED', {'en': 'Extended option {name} removed', 'de': 'Erweiterte Option {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_LDAPACL_CREATED = DiaryEvent('UDM_SETTINGS_LDAPACL_CREATED', {'en': 'LDAP ACL Extension {name} created', 'de': 'LDAP ACL Erweiterung {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPACL_MODIFIED = DiaryEvent('UDM_SETTINGS_LDAPACL_MODIFIED', {'en': 'LDAP ACL Extension {name} modified', 'de': 'LDAP ACL Erweiterung {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPACL_MOVED = DiaryEvent('UDM_SETTINGS_LDAPACL_MOVED', {'en': 'LDAP ACL Extension {name} moved to {position}', 'de': 'LDAP ACL Erweiterung {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPACL_REMOVED = DiaryEvent('UDM_SETTINGS_LDAPACL_REMOVED', {'en': 'LDAP ACL Extension {name} removed', 'de': 'LDAP ACL Erweiterung {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_LDAPSCHEMA_CREATED = DiaryEvent('UDM_SETTINGS_LDAPSCHEMA_CREATED', {'en': 'LDAP Schema Extension {name} created', 'de': 'LDAP-Schemaerweiterung {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPSCHEMA_MODIFIED = DiaryEvent('UDM_SETTINGS_LDAPSCHEMA_MODIFIED', {'en': 'LDAP Schema Extension {name} modified', 'de': 'LDAP-Schemaerweiterung {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPSCHEMA_MOVED = DiaryEvent('UDM_SETTINGS_LDAPSCHEMA_MOVED', {'en': 'LDAP Schema Extension {name} moved to {position}', 'de': 'LDAP-Schemaerweiterung {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPSCHEMA_REMOVED = DiaryEvent('UDM_SETTINGS_LDAPSCHEMA_REMOVED', {'en': 'LDAP Schema Extension {name} removed', 'de': 'LDAP-Schemaerweiterung {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_LICENSE_REMOVED = DiaryEvent('UDM_SETTINGS_LICENSE_REMOVED', {'en': 'License {name} ({keyID}) removed', 'de': 'Lizenz {name} ({keyID}) gelöscht'}, args=['name', 'keyID'], icon='domain')

UDM_SETTINGS_LOCK_MODIFIED = DiaryEvent('UDM_SETTINGS_LOCK_MODIFIED', {'en': 'Lock {name} ({locktime}) modified', 'de': 'Sperrobjekt {name} ({locktime}) bearbeitet'}, args=['name', 'locktime'], icon='domain')
UDM_SETTINGS_LOCK_REMOVED = DiaryEvent('UDM_SETTINGS_LOCK_REMOVED', {'en': 'Lock {name} ({locktime}) removed', 'de': 'Sperrobjekt {name} ({locktime}) gelöscht'}, args=['name', 'locktime'], icon='domain')

UDM_SETTINGS_PACKAGES_CREATED = DiaryEvent('UDM_SETTINGS_PACKAGES_CREATED', {'en': 'Package List {name} created', 'de': 'Paketliste {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PACKAGES_MODIFIED = DiaryEvent('UDM_SETTINGS_PACKAGES_MODIFIED', {'en': 'Package List {name} modified', 'de': 'Paketliste {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PACKAGES_MOVED = DiaryEvent('UDM_SETTINGS_PACKAGES_MOVED', {'en': 'Package List {name} moved to {position}', 'de': 'Paketliste {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PACKAGES_REMOVED = DiaryEvent('UDM_SETTINGS_PACKAGES_REMOVED', {'en': 'Package List {name} removed', 'de': 'Paketliste {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PORTAL_CREATED = DiaryEvent('UDM_SETTINGS_PORTAL_CREATED', {'en': 'Portal {name} created', 'de': 'Portal {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_MODIFIED = DiaryEvent('UDM_SETTINGS_PORTAL_MODIFIED', {'en': 'Portal {name} modified', 'de': 'Portal {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_MOVED = DiaryEvent('UDM_SETTINGS_PORTAL_MOVED', {'en': 'Portal {name} moved to {position}', 'de': 'Portal {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_REMOVED = DiaryEvent('UDM_SETTINGS_PORTAL_REMOVED', {'en': 'Portal {name} removed', 'de': 'Portal {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PORTAL_CATEGORY_CREATED = DiaryEvent('UDM_SETTINGS_PORTAL_CATEGORY_CREATED', {'en': 'Portal category {name} created', 'de': 'Portal-Kategorie {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_CATEGORY_MODIFIED = DiaryEvent('UDM_SETTINGS_PORTAL_CATEGORY_MODIFIED', {'en': 'Portal category {name} modified', 'de': 'Portal-Kategorie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_CATEGORY_MOVED = DiaryEvent('UDM_SETTINGS_PORTAL_CATEGORY_MOVED', {'en': 'Portal category {name} moved to {position}', 'de': 'Portal-Kategorie {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_CATEGORY_REMOVED = DiaryEvent('UDM_SETTINGS_PORTAL_CATEGORY_REMOVED', {'en': 'Portal category {name} removed', 'de': 'Portal-Kategorie {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PORTAL_ENTRY_CREATED = DiaryEvent('UDM_SETTINGS_PORTAL_ENTRY_CREATED', {'en': 'Portal entry {name} created', 'de': 'Portal-Eintrag {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_ENTRY_MODIFIED = DiaryEvent('UDM_SETTINGS_PORTAL_ENTRY_MODIFIED', {'en': 'Portal entry {name} modified', 'de': 'Portal-Eintrag {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_ENTRY_MOVED = DiaryEvent('UDM_SETTINGS_PORTAL_ENTRY_MOVED', {'en': 'Portal entry {name} moved to {position}', 'de': 'Portal-Eintrag {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_ENTRY_REMOVED = DiaryEvent('UDM_SETTINGS_PORTAL_ENTRY_REMOVED', {'en': 'Portal entry {name} removed', 'de': 'Portal-Eintrag {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PRINTERMODEL_CREATED = DiaryEvent('UDM_SETTINGS_PRINTERMODEL_CREATED', {'en': 'Printer Driver List {name} created', 'de': 'Druckertreiberliste {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERMODEL_MODIFIED = DiaryEvent('UDM_SETTINGS_PRINTERMODEL_MODIFIED', {'en': 'Printer Driver List {name} modified', 'de': 'Druckertreiberliste {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERMODEL_MOVED = DiaryEvent('UDM_SETTINGS_PRINTERMODEL_MOVED', {'en': 'Printer Driver List {name} moved to {position}', 'de': 'Druckertreiberliste {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERMODEL_REMOVED = DiaryEvent('UDM_SETTINGS_PRINTERMODEL_REMOVED', {'en': 'Printer Driver List {name} removed', 'de': 'Druckertreiberliste {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PRINTERURI_CREATED = DiaryEvent('UDM_SETTINGS_PRINTERURI_CREATED', {'en': 'Printer URI List {name} created', 'de': 'Drucker-URI-Liste {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERURI_MODIFIED = DiaryEvent('UDM_SETTINGS_PRINTERURI_MODIFIED', {'en': 'Printer URI List {name} modified', 'de': 'Drucker-URI-Liste {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERURI_MOVED = DiaryEvent('UDM_SETTINGS_PRINTERURI_MOVED', {'en': 'Printer URI List {name} moved to {position}', 'de': 'Drucker-URI-Liste {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERURI_REMOVED = DiaryEvent('UDM_SETTINGS_PRINTERURI_REMOVED', {'en': 'Printer URI List {name} removed', 'de': 'Drucker-URI-Liste {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PROHIBITED_USERNAME_CREATED = DiaryEvent('UDM_SETTINGS_PROHIBITED_USERNAME_CREATED', {'en': 'Prohibited user name {name} created', 'de': 'Verbotener Benutzername {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PROHIBITED_USERNAME_MODIFIED = DiaryEvent('UDM_SETTINGS_PROHIBITED_USERNAME_MODIFIED', {'en': 'Prohibited user name {name} modified', 'de': 'Verbotener Benutzername {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PROHIBITED_USERNAME_MOVED = DiaryEvent('UDM_SETTINGS_PROHIBITED_USERNAME_MOVED', {'en': 'Prohibited user name {name} moved to {position}', 'de': 'Verbotener Benutzername {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PROHIBITED_USERNAME_REMOVED = DiaryEvent('UDM_SETTINGS_PROHIBITED_USERNAME_REMOVED', {'en': 'Prohibited user name {name} removed', 'de': 'Verbotener Benutzername {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_SAMBACONFIG_MODIFIED = DiaryEvent('UDM_SETTINGS_SAMBACONFIG_MODIFIED', {'en': 'Samba Configuration {name} modified', 'de': 'Samba-Konfiguration {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_SAMBACONFIG_MOVED = DiaryEvent('UDM_SETTINGS_SAMBACONFIG_MOVED', {'en': 'Samba Configuration {name} moved to {position}', 'de': 'Samba-Konfiguration {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_SAMBACONFIG_REMOVED = DiaryEvent('UDM_SETTINGS_SAMBACONFIG_REMOVED', {'en': 'Samba Configuration {name} removed', 'de': 'Samba-Konfiguration {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_SAMBADOMAIN_CREATED = DiaryEvent('UDM_SETTINGS_SAMBADOMAIN_CREATED', {'en': 'Samba Domain {name} ({SID}) created', 'de': 'Samba-Domänenname {name} ({SID}) angelegt'}, args=['name', 'SID'], icon='domain')
UDM_SETTINGS_SAMBADOMAIN_MODIFIED = DiaryEvent('UDM_SETTINGS_SAMBADOMAIN_MODIFIED', {'en': 'Samba Domain {name} ({SID}) modified', 'de': 'Samba-Domänenname {name} ({SID}) bearbeitet'}, args=['name', 'SID'], icon='domain')
UDM_SETTINGS_SAMBADOMAIN_MOVED = DiaryEvent('UDM_SETTINGS_SAMBADOMAIN_MOVED', {'en': 'Samba Domain {name} ({SID}) moved to {position}', 'de': 'Samba-Domänenname {name} ({SID}) verschoben nach {position}'}, args=['name', 'SID'], icon='domain')
UDM_SETTINGS_SAMBADOMAIN_REMOVED = DiaryEvent('UDM_SETTINGS_SAMBADOMAIN_REMOVED', {'en': 'Samba Domain {name} ({SID}) removed', 'de': 'Samba-Domänenname {name} ({SID}) gelöscht'}, args=['name', 'SID'], icon='domain')

UDM_SETTINGS_SERVICE_CREATED = DiaryEvent('UDM_SETTINGS_SERVICE_CREATED', {'en': 'Service {name} created', 'de': 'Dienstname {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_SERVICE_MODIFIED = DiaryEvent('UDM_SETTINGS_SERVICE_MODIFIED', {'en': 'Service {name} modified', 'de': 'Dienstname {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_SERVICE_MOVED = DiaryEvent('UDM_SETTINGS_SERVICE_MOVED', {'en': 'Service {name} moved to {position}', 'de': 'Dienstname {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_SERVICE_REMOVED = DiaryEvent('UDM_SETTINGS_SERVICE_REMOVED', {'en': 'Service {name} removed', 'de': 'Dienstname {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_SYNTAX_CREATED = DiaryEvent('UDM_SETTINGS_SYNTAX_CREATED', {'en': 'Syntax Definition {name} created', 'de': 'Syntax-Definition {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_SYNTAX_MODIFIED = DiaryEvent('UDM_SETTINGS_SYNTAX_MODIFIED', {'en': 'Syntax Definition {name} modified', 'de': 'Syntax-Definition {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_SYNTAX_MOVED = DiaryEvent('UDM_SETTINGS_SYNTAX_MOVED', {'en': 'Syntax Definition {name} moved to {position}', 'de': 'Syntax-Definition {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_SYNTAX_REMOVED = DiaryEvent('UDM_SETTINGS_SYNTAX_REMOVED', {'en': 'Syntax Definition {name} removed', 'de': 'Syntax-Definition {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_UDM_HOOK_CREATED = DiaryEvent('UDM_SETTINGS_UDM_HOOK_CREATED', {'en': 'UDM Hook {name} created', 'de': 'UDM Hook {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_HOOK_MODIFIED = DiaryEvent('UDM_SETTINGS_UDM_HOOK_MODIFIED', {'en': 'UDM Hook {name} modified', 'de': 'UDM Hook {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_HOOK_MOVED = DiaryEvent('UDM_SETTINGS_UDM_HOOK_MOVED', {'en': 'UDM Hook {name} moved to {position}', 'de': 'UDM Hook {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_HOOK_REMOVED = DiaryEvent('UDM_SETTINGS_UDM_HOOK_REMOVED', {'en': 'UDM Hook {name} removed', 'de': 'UDM Hook {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_UDM_MODULE_CREATED = DiaryEvent('UDM_SETTINGS_UDM_MODULE_CREATED', {'en': 'UDM Module {name} created', 'de': 'UDM-Modul {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_MODULE_MODIFIED = DiaryEvent('UDM_SETTINGS_UDM_MODULE_MODIFIED', {'en': 'UDM Module {name} modified', 'de': 'UDM-Modul {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_MODULE_MOVED = DiaryEvent('UDM_SETTINGS_UDM_MODULE_MOVED', {'en': 'UDM Module {name} moved to {position}', 'de': 'UDM-Modul {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_MODULE_REMOVED = DiaryEvent('UDM_SETTINGS_UDM_MODULE_REMOVED', {'en': 'UDM Module {name} removed', 'de': 'UDM-Modul {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_UDM_SYNTAX_CREATED = DiaryEvent('UDM_SETTINGS_UDM_SYNTAX_CREATED', {'en': 'UDM Syntax {name} created', 'de': 'UDM Syntax {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_SYNTAX_MODIFIED = DiaryEvent('UDM_SETTINGS_UDM_SYNTAX_MODIFIED', {'en': 'UDM Syntax {name} modified', 'de': 'UDM Syntax {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_SYNTAX_MOVED = DiaryEvent('UDM_SETTINGS_UDM_SYNTAX_MOVED', {'en': 'UDM Syntax {name} moved to {position}', 'de': 'UDM Syntax {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_SYNTAX_REMOVED = DiaryEvent('UDM_SETTINGS_UDM_SYNTAX_REMOVED', {'en': 'UDM Syntax {name} removed', 'de': 'UDM Syntax {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_UMC_OPERATIONSET_CREATED = DiaryEvent('UDM_SETTINGS_UMC_OPERATIONSET_CREATED', {'en': 'UMC operation set {name} created', 'de': 'UMC-Befehlssatz {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_UMC_OPERATIONSET_MODIFIED = DiaryEvent('UDM_SETTINGS_UMC_OPERATIONSET_MODIFIED', {'en': 'UMC operation set {name} modified', 'de': 'UMC-Befehlssatz {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_UMC_OPERATIONSET_MOVED = DiaryEvent('UDM_SETTINGS_UMC_OPERATIONSET_MOVED', {'en': 'UMC operation set {name} moved to {position}', 'de': 'UMC-Befehlssatz {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_UMC_OPERATIONSET_REMOVED = DiaryEvent('UDM_SETTINGS_UMC_OPERATIONSET_REMOVED', {'en': 'UMC operation set {name} removed', 'de': 'UMC-Befehlssatz {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_USERTEMPLATE_CREATED = DiaryEvent('UDM_SETTINGS_USERTEMPLATE_CREATED', {'en': 'User Template {name} created', 'de': 'Benutzervorlage {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_USERTEMPLATE_MODIFIED = DiaryEvent('UDM_SETTINGS_USERTEMPLATE_MODIFIED', {'en': 'User Template {name} modified', 'de': 'Benutzervorlage {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_USERTEMPLATE_MOVED = DiaryEvent('UDM_SETTINGS_USERTEMPLATE_MOVED', {'en': 'User Template {name} moved to {position}', 'de': 'Benutzervorlage {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_USERTEMPLATE_REMOVED = DiaryEvent('UDM_SETTINGS_USERTEMPLATE_REMOVED', {'en': 'User Template {name} removed', 'de': 'Benutzervorlage {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_XCONFIG_CHOICES_MODIFIED = DiaryEvent('UDM_SETTINGS_XCONFIG_CHOICES_MODIFIED', {'en': 'X Configuration Choice {name} modified', 'de': 'X-Konfigurations Auswahl {name} bearbeitet'}, args=['name'], icon='domain')

UDM_SHARES_PRINTER_CREATED = DiaryEvent('UDM_SHARES_PRINTER_CREATED', {'en': 'Printer {name} created', 'de': 'Drucker {name} angelegt'}, args=['name'], icon='domain')
UDM_SHARES_PRINTER_MODIFIED = DiaryEvent('UDM_SHARES_PRINTER_MODIFIED', {'en': 'Printer {name} modified', 'de': 'Drucker {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SHARES_PRINTER_MOVED = DiaryEvent('UDM_SHARES_PRINTER_MOVED', {'en': 'Printer {name} moved to {position}', 'de': 'Drucker {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SHARES_PRINTER_REMOVED = DiaryEvent('UDM_SHARES_PRINTER_REMOVED', {'en': 'Printer {name} removed', 'de': 'Drucker {name} gelöscht'}, args=['name'], icon='domain')

UDM_SHARES_PRINTERGROUP_CREATED = DiaryEvent('UDM_SHARES_PRINTERGROUP_CREATED', {'en': 'Printer share group {name} created', 'de': 'Druckerfreigabegruppe {name} angelegt'}, args=['name'], icon='domain')
UDM_SHARES_PRINTERGROUP_MODIFIED = DiaryEvent('UDM_SHARES_PRINTERGROUP_MODIFIED', {'en': 'Printer share group {name} modified', 'de': 'Druckerfreigabegruppe {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SHARES_PRINTERGROUP_MOVED = DiaryEvent('UDM_SHARES_PRINTERGROUP_MOVED', {'en': 'Printer share group {name} moved to {position}', 'de': 'Druckerfreigabegruppe {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SHARES_PRINTERGROUP_REMOVED = DiaryEvent('UDM_SHARES_PRINTERGROUP_REMOVED', {'en': 'Printer share group {name} removed', 'de': 'Druckerfreigabegruppe {name} gelöscht'}, args=['name'], icon='domain')

UDM_SHARES_SHARE_CREATED = DiaryEvent('UDM_SHARES_SHARE_CREATED', {'en': 'Share directory {name} created', 'de': 'Freigabe-Verzeichnis {name} angelegt'}, args=['name'], icon='domain')
UDM_SHARES_SHARE_MODIFIED = DiaryEvent('UDM_SHARES_SHARE_MODIFIED', {'en': 'Share directory {name} modified', 'de': 'Freigabe-Verzeichnis {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SHARES_SHARE_MOVED = DiaryEvent('UDM_SHARES_SHARE_MOVED', {'en': 'Share directory {name} moved to {position}', 'de': 'Freigabe-Verzeichnis {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SHARES_SHARE_REMOVED = DiaryEvent('UDM_SHARES_SHARE_REMOVED', {'en': 'Share directory {name} removed', 'de': 'Freigabe-Verzeichnis {name} gelöscht'}, args=['name'], icon='domain')

UDM_USERS_CONTACT_CREATED = DiaryEvent('UDM_USERS_CONTACT_CREATED', {'en': 'Contact {cn} created', 'de': 'Kontakt {cn} angelegt'}, args=['cn'], icon='users')
UDM_USERS_CONTACT_MODIFIED = DiaryEvent('UDM_USERS_CONTACT_MODIFIED', {'en': 'Contact {cn} modified', 'de': 'Kontakt {cn} bearbeitet'}, args=['cn'], icon='users')
UDM_USERS_CONTACT_MOVED = DiaryEvent('UDM_USERS_CONTACT_MOVED', {'en': 'Contact {cn} moved to {position}', 'de': 'Kontakt {cn} verschoben nach {position}'}, args=['cn'], icon='users')
UDM_USERS_CONTACT_REMOVED = DiaryEvent('UDM_USERS_CONTACT_REMOVED', {'en': 'Contact {cn} removed', 'de': 'Kontakt {cn} gelöscht'}, args=['cn'], icon='users')

UDM_USERS_LDAP_CREATED = DiaryEvent('UDM_USERS_LDAP_CREATED', {'en': 'Simple authentication account {username} created', 'de': 'Einfaches Authentisierungskonto {username} angelegt'}, args=['username'], icon='users')
UDM_USERS_LDAP_MODIFIED = DiaryEvent('UDM_USERS_LDAP_MODIFIED', {'en': 'Simple authentication account {username} modified', 'de': 'Einfaches Authentisierungskonto {username} bearbeitet'}, args=['username'], icon='users')
UDM_USERS_LDAP_MOVED = DiaryEvent('UDM_USERS_LDAP_MOVED', {'en': 'Simple authentication account {username} moved to {position}', 'de': 'Einfaches Authentisierungskonto {username} verschoben nach {position}'}, args=['username'], icon='users')
UDM_USERS_LDAP_REMOVED = DiaryEvent('UDM_USERS_LDAP_REMOVED', {'en': 'Simple authentication account {username} removed', 'de': 'Einfaches Authentisierungskonto {username} gelöscht'}, args=['username'], icon='users')

UDM_USERS_PASSWD_MODIFIED = DiaryEvent('UDM_USERS_PASSWD_MODIFIED', {'en': 'Password {username} modified', 'de': 'Passwort {username} bearbeitet'}, args=['username'], icon='users')

UDM_USERS_USER_CREATED = DiaryEvent('UDM_USERS_USER_CREATED', {'en': 'User {username} created', 'de': 'Benutzer {username} angelegt'}, args=['username'], icon='users')
UDM_USERS_USER_MODIFIED = DiaryEvent('UDM_USERS_USER_MODIFIED', {'en': 'User {username} modified', 'de': 'Benutzer {username} bearbeitet'}, args=['username'], icon='users')
UDM_USERS_USER_MOVED = DiaryEvent('UDM_USERS_USER_MOVED', {'en': 'User {username} moved to {position}', 'de': 'Benutzer {username} verschoben nach {position}'}, args=['username'], icon='users')
UDM_USERS_USER_REMOVED = DiaryEvent('UDM_USERS_USER_REMOVED', {'en': 'User {username} removed', 'de': 'Benutzer {username} gelöscht'}, args=['username'], icon='users')

UDM_UVMM_CLOUDCONNECTION_CREATED = DiaryEvent('UDM_UVMM_CLOUDCONNECTION_CREATED', {'en': 'Cloud Connection {name} created', 'de': 'Cloud Connection {name} angelegt'}, args=['name'], icon='domain')
UDM_UVMM_CLOUDCONNECTION_MODIFIED = DiaryEvent('UDM_UVMM_CLOUDCONNECTION_MODIFIED', {'en': 'Cloud Connection {name} modified', 'de': 'Cloud Connection {name} bearbeitet'}, args=['name'], icon='domain')
UDM_UVMM_CLOUDCONNECTION_REMOVED = DiaryEvent('UDM_UVMM_CLOUDCONNECTION_REMOVED', {'en': 'Cloud Connection {name} removed', 'de': 'Cloud Connection {name} gelöscht'}, args=['name'], icon='domain')

UDM_UVMM_CLOUDTYPE_CREATED = DiaryEvent('UDM_UVMM_CLOUDTYPE_CREATED', {'en': 'Cloud Type {name} created', 'de': 'Cloud Type {name} angelegt'}, args=['name'], icon='domain')
UDM_UVMM_CLOUDTYPE_MODIFIED = DiaryEvent('UDM_UVMM_CLOUDTYPE_MODIFIED', {'en': 'Cloud Type {name} modified', 'de': 'Cloud Type {name} bearbeitet'}, args=['name'], icon='domain')
UDM_UVMM_CLOUDTYPE_REMOVED = DiaryEvent('UDM_UVMM_CLOUDTYPE_REMOVED', {'en': 'Cloud Type {name} removed', 'de': 'Cloud Type {name} gelöscht'}, args=['name'], icon='domain')

UDM_UVMM_INFO_CREATED = DiaryEvent('UDM_UVMM_INFO_CREATED', {'en': 'Machine information {uuid} created', 'de': 'Machine information {uuid} angelegt'}, args=['uuid'], icon='domain')
UDM_UVMM_INFO_MODIFIED = DiaryEvent('UDM_UVMM_INFO_MODIFIED', {'en': 'Machine information {uuid} modified', 'de': 'Machine information {uuid} bearbeitet'}, args=['uuid'], icon='domain')
UDM_UVMM_INFO_REMOVED = DiaryEvent('UDM_UVMM_INFO_REMOVED', {'en': 'Machine information {uuid} removed', 'de': 'Machine information {uuid} gelöscht'}, args=['uuid'], icon='domain')

UDM_UVMM_PROFILE_CREATED = DiaryEvent('UDM_UVMM_PROFILE_CREATED', {'en': 'Profile {name} created', 'de': 'Profile {name} angelegt'}, args=['name'], icon='domain')
UDM_UVMM_PROFILE_MODIFIED = DiaryEvent('UDM_UVMM_PROFILE_MODIFIED', {'en': 'Profile {name} modified', 'de': 'Profile {name} bearbeitet'}, args=['name'], icon='domain')
UDM_UVMM_PROFILE_REMOVED = DiaryEvent('UDM_UVMM_PROFILE_REMOVED', {'en': 'Profile {name} removed', 'de': 'Profile {name} gelöscht'}, args=['name'], icon='domain')

