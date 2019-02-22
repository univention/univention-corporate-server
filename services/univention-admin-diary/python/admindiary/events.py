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
APP_INSTALL_FAILURE = DiaryEvent('APP_INSTALL_FAILURE', {'en': 'Installation of {name} {version} failed. Error {error_code}', 'de': 'Installation von {name} {version} schlug fehl. Fehler {error_code}'}, args=['name', 'version', 'error_code'], tags=['error'], icon='software')

SERVER_PASSWORD_CHANGED = DiaryEvent('SERVER_PASSWORD_CHANGED', {'en': 'Machine account password changed successfully', 'de': 'Maschinenpasswort erfolgreich geändert'}, icon='devices')
SERVER_PASSWORD_CHANGED_FAILED = DiaryEvent('SERVER_PASSWORD_CHANGED_FAILED', {'en': 'Machine account password change failed', 'de': 'Änderung des Maschinenpassworts fehlgeschlagen'}, tags=['error'], icon='devices')

UPDATE_STARTED = DiaryEvent('UPDATE_STARTED', {'en': 'Started to update {hostname}', 'de': 'Aktualisierung von {hostname} begonnen'}, args=['hostname'], icon='software')
UPDATE_FINISHED_SUCCESS = DiaryEvent('UPDATE_FINISHED_SUCCESS', {'en': 'Successfully updated {hostname} to {version}', 'de': 'Aktualisierung von {hostname} auf {version} erfolgreich abgeschlossen'}, args=['hostname', 'version'], icon='software')
UPDATE_FINISHED_FAILURE = DiaryEvent('UPDATE_FINISHED_FAILURE', {'en': 'Failed to update {hostname}', 'de': 'Aktualisierung von {hostname} fehlgeschlagen'}, args=['hostname'], tags=['error'], icon='software')

JOIN_STARTED = DiaryEvent('JOIN_STARTED', {'en': 'Started to join {hostname} into the domain', 'de': 'Domänenbeitritt von {hostname} begonnen'}, args=['hostname'], icon='domain')
JOIN_FINISHED_SUCCESS = DiaryEvent('JOIN_FINISHED_SUCCESS', {'en': 'Successfully joined {hostname}', 'de': '{hostname} erfolgreich der Domöne beigetreten'}, args=['hostname'], icon='domain')
JOIN_FINISHED_FAILURE = DiaryEvent('JOIN_FINISHED_FAILURE', {'en': 'Failed to join {hostname}', 'de': 'Domänenbeitritt von {hostname} fehlgeschlagen'}, args=['hostname'], tags=['error'], icon='domain')
JOIN_SCRIPT_FAILED = DiaryEvent('JOIN_SCRIPT_FAILED', {'en': 'Running Joinscript {joinscript} failed', 'de': 'Ausführung des Joinscripts {joinscript} fehlgeschlagen'}, tags=['error'], icon='domain')

UDM_APPCENTER_APP_CREATED = DiaryEvent('UDM_APPCENTER_APP_CREATED', {'en': 'Appcenter: App Metadata {id} created', 'de': 'Appcenter: App Metadaten {id} angelegt'}, args=['id'], icon='domain')
UDM_APPCENTER_APP_MODIFIED = DiaryEvent('UDM_APPCENTER_APP_MODIFIED', {'en': 'Appcenter: App Metadata {id} modified', 'de': 'Appcenter: App Metadaten {id} bearbeitet'}, args=['id'], icon='domain')
UDM_APPCENTER_APP_MOVED = DiaryEvent('UDM_APPCENTER_APP_MOVED', {'en': 'Appcenter: App Metadata {id} moved to {position}', 'de': 'Appcenter: App Metadaten {id} verschoben nach {position}'}, args=['id'], icon='domain')
UDM_APPCENTER_APP_REMOVED = DiaryEvent('UDM_APPCENTER_APP_REMOVED', {'en': 'Appcenter: App Metadata {id} removed', 'de': 'Appcenter: App Metadaten {id} gelöscht'}, args=['id'], icon='domain')

UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_CREATED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_CREATED', {'en': 'Computer: Domain Controller Backup {name} created', 'de': 'Rechner: Domänencontroller Backup {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MODIFIED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MODIFIED', {'en': 'Computer: Domain Controller Backup {name} modified', 'de': 'Rechner: Domänencontroller Backup {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MOVED', {'en': 'Computer: Domain Controller Backup {name} moved to {position}', 'de': 'Rechner: Domänencontroller Backup {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_REMOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_REMOVED', {'en': 'Computer: Domain Controller Backup {name} removed', 'de': 'Rechner: Domänencontroller Backup {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_CREATED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_CREATED', {'en': 'Computer: Domain Controller Master {name} created', 'de': 'Rechner: Domänencontroller Master {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MODIFIED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MODIFIED', {'en': 'Computer: Domain Controller Master {name} modified', 'de': 'Rechner: Domänencontroller Master {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MOVED', {'en': 'Computer: Domain Controller Master {name} moved to {position}', 'de': 'Rechner: Domänencontroller Master {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_REMOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_REMOVED', {'en': 'Computer: Domain Controller Master {name} removed', 'de': 'Rechner: Domänencontroller Master {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_CREATED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_CREATED', {'en': 'Computer: Domain Controller Slave {name} created', 'de': 'Rechner: Domänencontroller Slave {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MODIFIED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MODIFIED', {'en': 'Computer: Domain Controller Slave {name} modified', 'de': 'Rechner: Domänencontroller Slave {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MOVED', {'en': 'Computer: Domain Controller Slave {name} moved to {position}', 'de': 'Rechner: Domänencontroller Slave {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_REMOVED = DiaryEvent('UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_REMOVED', {'en': 'Computer: Domain Controller Slave {name} removed', 'de': 'Rechner: Domänencontroller Slave {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_IPMANAGEDCLIENT_CREATED = DiaryEvent('UDM_COMPUTERS_IPMANAGEDCLIENT_CREATED', {'en': 'Computer: IP managed client {name} created', 'de': 'Rechner: IP-Managed-Client {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_IPMANAGEDCLIENT_MODIFIED = DiaryEvent('UDM_COMPUTERS_IPMANAGEDCLIENT_MODIFIED', {'en': 'Computer: IP managed client {name} modified', 'de': 'Rechner: IP-Managed-Client {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_IPMANAGEDCLIENT_MOVED = DiaryEvent('UDM_COMPUTERS_IPMANAGEDCLIENT_MOVED', {'en': 'Computer: IP managed client {name} moved to {position}', 'de': 'Rechner: IP-Managed-Client {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_IPMANAGEDCLIENT_REMOVED = DiaryEvent('UDM_COMPUTERS_IPMANAGEDCLIENT_REMOVED', {'en': 'Computer: IP managed client {name} removed', 'de': 'Rechner: IP-Managed-Client {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_LINUX_CREATED = DiaryEvent('UDM_COMPUTERS_LINUX_CREATED', {'en': 'Computer: Linux {name} created', 'de': 'Rechner: Linux {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_LINUX_MODIFIED = DiaryEvent('UDM_COMPUTERS_LINUX_MODIFIED', {'en': 'Computer: Linux {name} modified', 'de': 'Rechner: Linux {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_LINUX_MOVED = DiaryEvent('UDM_COMPUTERS_LINUX_MOVED', {'en': 'Computer: Linux {name} moved to {position}', 'de': 'Rechner: Linux {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_LINUX_REMOVED = DiaryEvent('UDM_COMPUTERS_LINUX_REMOVED', {'en': 'Computer: Linux {name} removed', 'de': 'Rechner: Linux {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_MACOS_CREATED = DiaryEvent('UDM_COMPUTERS_MACOS_CREATED', {'en': 'Computer: Mac OS X Client {name} created', 'de': 'Rechner: Mac OS X Client {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_MACOS_MODIFIED = DiaryEvent('UDM_COMPUTERS_MACOS_MODIFIED', {'en': 'Computer: Mac OS X Client {name} modified', 'de': 'Rechner: Mac OS X Client {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_MACOS_MOVED = DiaryEvent('UDM_COMPUTERS_MACOS_MOVED', {'en': 'Computer: Mac OS X Client {name} moved to {position}', 'de': 'Rechner: Mac OS X Client {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_MACOS_REMOVED = DiaryEvent('UDM_COMPUTERS_MACOS_REMOVED', {'en': 'Computer: Mac OS X Client {name} removed', 'de': 'Rechner: Mac OS X Client {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_MEMBERSERVER_CREATED = DiaryEvent('UDM_COMPUTERS_MEMBERSERVER_CREATED', {'en': 'Computer: Member Server {name} created', 'de': 'Rechner: Member-Server {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_MEMBERSERVER_MODIFIED = DiaryEvent('UDM_COMPUTERS_MEMBERSERVER_MODIFIED', {'en': 'Computer: Member Server {name} modified', 'de': 'Rechner: Member-Server {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_MEMBERSERVER_MOVED = DiaryEvent('UDM_COMPUTERS_MEMBERSERVER_MOVED', {'en': 'Computer: Member Server {name} moved to {position}', 'de': 'Rechner: Member-Server {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_MEMBERSERVER_REMOVED = DiaryEvent('UDM_COMPUTERS_MEMBERSERVER_REMOVED', {'en': 'Computer: Member Server {name} removed', 'de': 'Rechner: Member-Server {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_TRUSTACCOUNT_CREATED = DiaryEvent('UDM_COMPUTERS_TRUSTACCOUNT_CREATED', {'en': 'Computer: Domain trust account {name} created', 'de': 'Rechner: Domain Trust Account {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_TRUSTACCOUNT_MODIFIED = DiaryEvent('UDM_COMPUTERS_TRUSTACCOUNT_MODIFIED', {'en': 'Computer: Domain trust account {name} modified', 'de': 'Rechner: Domain Trust Account {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_TRUSTACCOUNT_MOVED = DiaryEvent('UDM_COMPUTERS_TRUSTACCOUNT_MOVED', {'en': 'Computer: Domain trust account {name} moved to {position}', 'de': 'Rechner: Domain Trust Account {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_TRUSTACCOUNT_REMOVED = DiaryEvent('UDM_COMPUTERS_TRUSTACCOUNT_REMOVED', {'en': 'Computer: Domain trust account {name} removed', 'de': 'Rechner: Domain Trust Account {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_UBUNTU_CREATED = DiaryEvent('UDM_COMPUTERS_UBUNTU_CREATED', {'en': 'Computer: Ubuntu {name} created', 'de': 'Rechner: Ubuntu {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_UBUNTU_MODIFIED = DiaryEvent('UDM_COMPUTERS_UBUNTU_MODIFIED', {'en': 'Computer: Ubuntu {name} modified', 'de': 'Rechner: Ubuntu {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_UBUNTU_MOVED = DiaryEvent('UDM_COMPUTERS_UBUNTU_MOVED', {'en': 'Computer: Ubuntu {name} moved to {position}', 'de': 'Rechner: Ubuntu {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_UBUNTU_REMOVED = DiaryEvent('UDM_COMPUTERS_UBUNTU_REMOVED', {'en': 'Computer: Ubuntu {name} removed', 'de': 'Rechner: Ubuntu {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_WINDOWS_CREATED = DiaryEvent('UDM_COMPUTERS_WINDOWS_CREATED', {'en': 'Computer: Windows Workstation/Server {name} created', 'de': 'Rechner: Windows Workstation/Server {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_MODIFIED = DiaryEvent('UDM_COMPUTERS_WINDOWS_MODIFIED', {'en': 'Computer: Windows Workstation/Server {name} modified', 'de': 'Rechner: Windows Workstation/Server {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_MOVED = DiaryEvent('UDM_COMPUTERS_WINDOWS_MOVED', {'en': 'Computer: Windows Workstation/Server {name} moved to {position}', 'de': 'Rechner: Windows Workstation/Server {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_REMOVED = DiaryEvent('UDM_COMPUTERS_WINDOWS_REMOVED', {'en': 'Computer: Windows Workstation/Server {name} removed', 'de': 'Rechner: Windows Workstation/Server {name} gelöscht'}, args=['name'], icon='devices')

UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_CREATED = DiaryEvent('UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_CREATED', {'en': 'Computer: Windows Domaincontroller {name} created', 'de': 'Rechner: Windows Domänencontroller {name} angelegt'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MODIFIED = DiaryEvent('UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MODIFIED', {'en': 'Computer: Windows Domaincontroller {name} modified', 'de': 'Rechner: Windows Domänencontroller {name} bearbeitet'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MOVED = DiaryEvent('UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MOVED', {'en': 'Computer: Windows Domaincontroller {name} moved to {position}', 'de': 'Rechner: Windows Domänencontroller {name} verschoben nach {position}'}, args=['name'], icon='devices')
UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_REMOVED = DiaryEvent('UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_REMOVED', {'en': 'Computer: Windows Domaincontroller {name} removed', 'de': 'Rechner: Windows Domänencontroller {name} gelöscht'}, args=['name'], icon='devices')

UDM_CONTAINER_CN_CREATED = DiaryEvent('UDM_CONTAINER_CN_CREATED', {'en': 'Container: Container {name} created', 'de': 'Container: Container {name} angelegt'}, args=['name'], icon='domain')
UDM_CONTAINER_CN_MODIFIED = DiaryEvent('UDM_CONTAINER_CN_MODIFIED', {'en': 'Container: Container {name} modified', 'de': 'Container: Container {name} bearbeitet'}, args=['name'], icon='domain')
UDM_CONTAINER_CN_MOVED = DiaryEvent('UDM_CONTAINER_CN_MOVED', {'en': 'Container: Container {name} moved to {position}', 'de': 'Container: Container {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_CONTAINER_CN_REMOVED = DiaryEvent('UDM_CONTAINER_CN_REMOVED', {'en': 'Container: Container {name} removed', 'de': 'Container: Container {name} gelöscht'}, args=['name'], icon='domain')

UDM_CONTAINER_DC_MODIFIED = DiaryEvent('UDM_CONTAINER_DC_MODIFIED', {'en': 'Container: Domain {name} modified', 'de': 'Container: Domäne {name} bearbeitet'}, args=['name'], icon='domain')

UDM_CONTAINER_OU_CREATED = DiaryEvent('UDM_CONTAINER_OU_CREATED', {'en': 'Container: Organisational Unit {name} created', 'de': 'Container: Organisationseinheit {name} angelegt'}, args=['name'], icon='domain')
UDM_CONTAINER_OU_MODIFIED = DiaryEvent('UDM_CONTAINER_OU_MODIFIED', {'en': 'Container: Organisational Unit {name} modified', 'de': 'Container: Organisationseinheit {name} bearbeitet'}, args=['name'], icon='domain')
UDM_CONTAINER_OU_MOVED = DiaryEvent('UDM_CONTAINER_OU_MOVED', {'en': 'Container: Organisational Unit {name} moved to {position}', 'de': 'Container: Organisationseinheit {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_CONTAINER_OU_REMOVED = DiaryEvent('UDM_CONTAINER_OU_REMOVED', {'en': 'Container: Organisational Unit {name} removed', 'de': 'Container: Organisationseinheit {name} gelöscht'}, args=['name'], icon='domain')

UDM_DHCP_HOST_CREATED = DiaryEvent('UDM_DHCP_HOST_CREATED', {'en': 'DHCP: Host {host} created', 'de': 'DHCP: Rechner {host} angelegt'}, args=['host'], icon='domain')
UDM_DHCP_HOST_MODIFIED = DiaryEvent('UDM_DHCP_HOST_MODIFIED', {'en': 'DHCP: Host {host} modified', 'de': 'DHCP: Rechner {host} bearbeitet'}, args=['host'], icon='domain')
UDM_DHCP_HOST_REMOVED = DiaryEvent('UDM_DHCP_HOST_REMOVED', {'en': 'DHCP: Host {host} removed', 'de': 'DHCP: Rechner {host} gelöscht'}, args=['host'], icon='domain')

UDM_DHCP_POOL_CREATED = DiaryEvent('UDM_DHCP_POOL_CREATED', {'en': 'DHCP: Pool {name} created', 'de': 'DHCP: Pool {name} angelegt'}, args=['name'], icon='domain')
UDM_DHCP_POOL_MODIFIED = DiaryEvent('UDM_DHCP_POOL_MODIFIED', {'en': 'DHCP: Pool {name} modified', 'de': 'DHCP: Pool {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DHCP_POOL_REMOVED = DiaryEvent('UDM_DHCP_POOL_REMOVED', {'en': 'DHCP: Pool {name} removed', 'de': 'DHCP: Pool {name} gelöscht'}, args=['name'], icon='domain')

UDM_DHCP_SERVER_CREATED = DiaryEvent('UDM_DHCP_SERVER_CREATED', {'en': 'DHCP: Server {server} created', 'de': 'DHCP: Server {server} angelegt'}, args=['server'], icon='domain')
UDM_DHCP_SERVER_MODIFIED = DiaryEvent('UDM_DHCP_SERVER_MODIFIED', {'en': 'DHCP: Server {server} modified', 'de': 'DHCP: Server {server} bearbeitet'}, args=['server'], icon='domain')
UDM_DHCP_SERVER_REMOVED = DiaryEvent('UDM_DHCP_SERVER_REMOVED', {'en': 'DHCP: Server {server} removed', 'de': 'DHCP: Server {server} gelöscht'}, args=['server'], icon='domain')

UDM_DHCP_SERVICE_CREATED = DiaryEvent('UDM_DHCP_SERVICE_CREATED', {'en': 'DHCP: Service {service} created', 'de': 'DHCP: Service {service} angelegt'}, args=['service'], icon='domain')
UDM_DHCP_SERVICE_MODIFIED = DiaryEvent('UDM_DHCP_SERVICE_MODIFIED', {'en': 'DHCP: Service {service} modified', 'de': 'DHCP: Service {service} bearbeitet'}, args=['service'], icon='domain')
UDM_DHCP_SERVICE_REMOVED = DiaryEvent('UDM_DHCP_SERVICE_REMOVED', {'en': 'DHCP: Service {service} removed', 'de': 'DHCP: Service {service} gelöscht'}, args=['service'], icon='domain')

UDM_DHCP_SHARED_CREATED = DiaryEvent('UDM_DHCP_SHARED_CREATED', {'en': 'DHCP: Shared network {name} created', 'de': 'DHCP: Shared Network {name} angelegt'}, args=['name'], icon='domain')
UDM_DHCP_SHARED_MODIFIED = DiaryEvent('UDM_DHCP_SHARED_MODIFIED', {'en': 'DHCP: Shared network {name} modified', 'de': 'DHCP: Shared Network {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DHCP_SHARED_REMOVED = DiaryEvent('UDM_DHCP_SHARED_REMOVED', {'en': 'DHCP: Shared network {name} removed', 'de': 'DHCP: Shared Network {name} gelöscht'}, args=['name'], icon='domain')

UDM_DHCP_SHAREDSUBNET_CREATED = DiaryEvent('UDM_DHCP_SHAREDSUBNET_CREATED', {'en': 'DHCP: Shared subnet {subnet} created', 'de': 'DHCP: Shared Subnet {subnet} angelegt'}, args=['subnet'], icon='domain')
UDM_DHCP_SHAREDSUBNET_MODIFIED = DiaryEvent('UDM_DHCP_SHAREDSUBNET_MODIFIED', {'en': 'DHCP: Shared subnet {subnet} modified', 'de': 'DHCP: Shared Subnet {subnet} bearbeitet'}, args=['subnet'], icon='domain')
UDM_DHCP_SHAREDSUBNET_REMOVED = DiaryEvent('UDM_DHCP_SHAREDSUBNET_REMOVED', {'en': 'DHCP: Shared subnet {subnet} removed', 'de': 'DHCP: Shared Subnet {subnet} gelöscht'}, args=['subnet'], icon='domain')

UDM_DHCP_SUBNET_CREATED = DiaryEvent('UDM_DHCP_SUBNET_CREATED', {'en': 'DHCP: Subnet {subnet} created', 'de': 'DHCP: Subnetz {subnet} angelegt'}, args=['subnet'], icon='domain')
UDM_DHCP_SUBNET_MODIFIED = DiaryEvent('UDM_DHCP_SUBNET_MODIFIED', {'en': 'DHCP: Subnet {subnet} modified', 'de': 'DHCP: Subnetz {subnet} bearbeitet'}, args=['subnet'], icon='domain')
UDM_DHCP_SUBNET_REMOVED = DiaryEvent('UDM_DHCP_SUBNET_REMOVED', {'en': 'DHCP: Subnet {subnet} removed', 'de': 'DHCP: Subnetz {subnet} gelöscht'}, args=['subnet'], icon='domain')

UDM_DNS_ALIAS_CREATED = DiaryEvent('UDM_DNS_ALIAS_CREATED', {'en': 'DNS: Alias record {name} created', 'de': 'DNS: Alias Record {name} angelegt'}, args=['name'], icon='domain')
UDM_DNS_ALIAS_MODIFIED = DiaryEvent('UDM_DNS_ALIAS_MODIFIED', {'en': 'DNS: Alias record {name} modified', 'de': 'DNS: Alias Record {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DNS_ALIAS_REMOVED = DiaryEvent('UDM_DNS_ALIAS_REMOVED', {'en': 'DNS: Alias record {name} removed', 'de': 'DNS: Alias Record {name} gelöscht'}, args=['name'], icon='domain')

UDM_DNS_FORWARD_ZONE_CREATED = DiaryEvent('UDM_DNS_FORWARD_ZONE_CREATED', {'en': 'DNS: Forward lookup zone {zone} created', 'de': 'DNS: Forward Lookup Zone {zone} angelegt'}, args=['zone'], icon='domain')
UDM_DNS_FORWARD_ZONE_MODIFIED = DiaryEvent('UDM_DNS_FORWARD_ZONE_MODIFIED', {'en': 'DNS: Forward lookup zone {zone} modified', 'de': 'DNS: Forward Lookup Zone {zone} bearbeitet'}, args=['zone'], icon='domain')
UDM_DNS_FORWARD_ZONE_REMOVED = DiaryEvent('UDM_DNS_FORWARD_ZONE_REMOVED', {'en': 'DNS: Forward lookup zone {zone} removed', 'de': 'DNS: Forward Lookup Zone {zone} gelöscht'}, args=['zone'], icon='domain')

UDM_DNS_HOST_RECORD_CREATED = DiaryEvent('UDM_DNS_HOST_RECORD_CREATED', {'en': 'DNS: Host Record {name} created', 'de': 'DNS: Host Record {name} angelegt'}, args=['name'], icon='domain')
UDM_DNS_HOST_RECORD_MODIFIED = DiaryEvent('UDM_DNS_HOST_RECORD_MODIFIED', {'en': 'DNS: Host Record {name} modified', 'de': 'DNS: Host Record {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DNS_HOST_RECORD_REMOVED = DiaryEvent('UDM_DNS_HOST_RECORD_REMOVED', {'en': 'DNS: Host Record {name} removed', 'de': 'DNS: Host Record {name} gelöscht'}, args=['name'], icon='domain')

UDM_DNS_NS_RECORD_CREATED = DiaryEvent('UDM_DNS_NS_RECORD_CREATED', {'en': 'DNS: NS Record {zone} created', 'de': 'DNS: NS Record {zone} angelegt'}, args=['zone'], icon='domain')
UDM_DNS_NS_RECORD_MODIFIED = DiaryEvent('UDM_DNS_NS_RECORD_MODIFIED', {'en': 'DNS: NS Record {zone} modified', 'de': 'DNS: NS Record {zone} bearbeitet'}, args=['zone'], icon='domain')
UDM_DNS_NS_RECORD_REMOVED = DiaryEvent('UDM_DNS_NS_RECORD_REMOVED', {'en': 'DNS: NS Record {zone} removed', 'de': 'DNS: NS Record {zone} gelöscht'}, args=['zone'], icon='domain')

UDM_DNS_PTR_RECORD_CREATED = DiaryEvent('UDM_DNS_PTR_RECORD_CREATED', {'en': 'DNS: Pointer record {address} created', 'de': 'DNS: Pointer Record {address} angelegt'}, args=['address'], icon='domain')
UDM_DNS_PTR_RECORD_MODIFIED = DiaryEvent('UDM_DNS_PTR_RECORD_MODIFIED', {'en': 'DNS: Pointer record {address} modified', 'de': 'DNS: Pointer Record {address} bearbeitet'}, args=['address'], icon='domain')
UDM_DNS_PTR_RECORD_REMOVED = DiaryEvent('UDM_DNS_PTR_RECORD_REMOVED', {'en': 'DNS: Pointer record {address} removed', 'de': 'DNS: Pointer Record {address} gelöscht'}, args=['address'], icon='domain')

UDM_DNS_REVERSE_ZONE_CREATED = DiaryEvent('UDM_DNS_REVERSE_ZONE_CREATED', {'en': 'DNS: Reverse lookup zone {subnet} created', 'de': 'DNS: Reverse Lookup Zone {subnet} angelegt'}, args=['subnet'], icon='domain')
UDM_DNS_REVERSE_ZONE_MODIFIED = DiaryEvent('UDM_DNS_REVERSE_ZONE_MODIFIED', {'en': 'DNS: Reverse lookup zone {subnet} modified', 'de': 'DNS: Reverse Lookup Zone {subnet} bearbeitet'}, args=['subnet'], icon='domain')
UDM_DNS_REVERSE_ZONE_REMOVED = DiaryEvent('UDM_DNS_REVERSE_ZONE_REMOVED', {'en': 'DNS: Reverse lookup zone {subnet} removed', 'de': 'DNS: Reverse Lookup Zone {subnet} gelöscht'}, args=['subnet'], icon='domain')

UDM_DNS_SRV_RECORD_CREATED = DiaryEvent('UDM_DNS_SRV_RECORD_CREATED', {'en': 'DNS: Service record {name} created', 'de': 'DNS: Service Record {name} angelegt'}, args=['name'], icon='domain')
UDM_DNS_SRV_RECORD_MODIFIED = DiaryEvent('UDM_DNS_SRV_RECORD_MODIFIED', {'en': 'DNS: Service record {name} modified', 'de': 'DNS: Service Record {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DNS_SRV_RECORD_REMOVED = DiaryEvent('UDM_DNS_SRV_RECORD_REMOVED', {'en': 'DNS: Service record {name} removed', 'de': 'DNS: Service Record {name} gelöscht'}, args=['name'], icon='domain')

UDM_DNS_TXT_RECORD_CREATED = DiaryEvent('UDM_DNS_TXT_RECORD_CREATED', {'en': 'DNS: TXT Record {name} created', 'de': 'DNS: TXT Record {name} angelegt'}, args=['name'], icon='domain')
UDM_DNS_TXT_RECORD_MODIFIED = DiaryEvent('UDM_DNS_TXT_RECORD_MODIFIED', {'en': 'DNS: TXT Record {name} modified', 'de': 'DNS: TXT Record {name} bearbeitet'}, args=['name'], icon='domain')
UDM_DNS_TXT_RECORD_REMOVED = DiaryEvent('UDM_DNS_TXT_RECORD_REMOVED', {'en': 'DNS: TXT Record {name} removed', 'de': 'DNS: TXT Record {name} gelöscht'}, args=['name'], icon='domain')

UDM_GROUPS_GROUP_CREATED = DiaryEvent('UDM_GROUPS_GROUP_CREATED', {'en': 'Group {name} created', 'de': 'Gruppe {name} angelegt'}, args=['name'], icon='users')
UDM_GROUPS_GROUP_MODIFIED = DiaryEvent('UDM_GROUPS_GROUP_MODIFIED', {'en': 'Group {name} modified', 'de': 'Gruppe {name} bearbeitet'}, args=['name'], icon='users')
UDM_GROUPS_GROUP_MOVED = DiaryEvent('UDM_GROUPS_GROUP_MOVED', {'en': 'Group {name} moved to {position}', 'de': 'Gruppe {name} verschoben nach {position}'}, args=['name'], icon='users')
UDM_GROUPS_GROUP_REMOVED = DiaryEvent('UDM_GROUPS_GROUP_REMOVED', {'en': 'Group {name} removed', 'de': 'Gruppe {name} gelöscht'}, args=['name'], icon='users')

UDM_KERBEROS_KDCENTRY_CREATED = DiaryEvent('UDM_KERBEROS_KDCENTRY_CREATED', {'en': 'Kerberos: KDC Entry {name} created', 'de': 'Kerberos: KDC-Eintrag {name} angelegt'}, args=['name'], icon='domain')
UDM_KERBEROS_KDCENTRY_MODIFIED = DiaryEvent('UDM_KERBEROS_KDCENTRY_MODIFIED', {'en': 'Kerberos: KDC Entry {name} modified', 'de': 'Kerberos: KDC-Eintrag {name} bearbeitet'}, args=['name'], icon='domain')
UDM_KERBEROS_KDCENTRY_MOVED = DiaryEvent('UDM_KERBEROS_KDCENTRY_MOVED', {'en': 'Kerberos: KDC Entry {name} moved to {position}', 'de': 'Kerberos: KDC-Eintrag {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_KERBEROS_KDCENTRY_REMOVED = DiaryEvent('UDM_KERBEROS_KDCENTRY_REMOVED', {'en': 'Kerberos: KDC Entry {name} removed', 'de': 'Kerberos: KDC-Eintrag {name} gelöscht'}, args=['name'], icon='domain')

UDM_MAIL_DOMAIN_CREATED = DiaryEvent('UDM_MAIL_DOMAIN_CREATED', {'en': 'Mail domain {name} created', 'de': 'Mail-Domäne {name} angelegt'}, args=['name'], icon='domain')
UDM_MAIL_DOMAIN_MODIFIED = DiaryEvent('UDM_MAIL_DOMAIN_MODIFIED', {'en': 'Mail domain {name} modified', 'de': 'Mail-Domäne {name} bearbeitet'}, args=['name'], icon='domain')
UDM_MAIL_DOMAIN_MOVED = DiaryEvent('UDM_MAIL_DOMAIN_MOVED', {'en': 'Mail domain {name} moved to {position}', 'de': 'Mail-Domäne {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_MAIL_DOMAIN_REMOVED = DiaryEvent('UDM_MAIL_DOMAIN_REMOVED', {'en': 'Mail domain {name} removed', 'de': 'Mail-Domäne {name} gelöscht'}, args=['name'], icon='domain')

UDM_MAIL_FOLDER_CREATED = DiaryEvent('UDM_MAIL_FOLDER_CREATED', {'en': 'Mail folder (IMAP) {nameWithMailDomain} created', 'de': 'Mail-Ordner (IMAP) {nameWithMailDomain} angelegt'}, args=['nameWithMailDomain'], icon='domain')
UDM_MAIL_FOLDER_MODIFIED = DiaryEvent('UDM_MAIL_FOLDER_MODIFIED', {'en': 'Mail folder (IMAP) {nameWithMailDomain} modified', 'de': 'Mail-Ordner (IMAP) {nameWithMailDomain} bearbeitet'}, args=['nameWithMailDomain'], icon='domain')
UDM_MAIL_FOLDER_REMOVED = DiaryEvent('UDM_MAIL_FOLDER_REMOVED', {'en': 'Mail folder (IMAP) {nameWithMailDomain} removed', 'de': 'Mail-Ordner (IMAP) {nameWithMailDomain} gelöscht'}, args=['nameWithMailDomain'], icon='domain')

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

UDM_NETWORKS_NETWORK_CREATED = DiaryEvent('UDM_NETWORKS_NETWORK_CREATED', {'en': 'Networks: Network {name} ({netmask} {network}) created', 'de': 'Netze: Netz {name} ({netmask} {network}) angelegt'}, args=['name', 'netmask', 'network'], icon='domain')
UDM_NETWORKS_NETWORK_MODIFIED = DiaryEvent('UDM_NETWORKS_NETWORK_MODIFIED', {'en': 'Networks: Network {name} ({netmask} {network}) modified', 'de': 'Netze: Netz {name} ({netmask} {network}) bearbeitet'}, args=['name', 'netmask', 'network'], icon='domain')
UDM_NETWORKS_NETWORK_REMOVED = DiaryEvent('UDM_NETWORKS_NETWORK_REMOVED', {'en': 'Networks: Network {name} ({netmask} {network}) removed', 'de': 'Netze: Netz {name} ({netmask} {network}) gelöscht'}, args=['name', 'netmask', 'network'], icon='domain')

UDM_POLICIES_ADMIN_CONTAINER_CREATED = DiaryEvent('UDM_POLICIES_ADMIN_CONTAINER_CREATED', {'en': 'Policy: Univention Directory Manager container settings {name} created', 'de': 'Richtlinie: Univention Directory Manager Container Konfiguration {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_ADMIN_CONTAINER_MODIFIED = DiaryEvent('UDM_POLICIES_ADMIN_CONTAINER_MODIFIED', {'en': 'Policy: Univention Directory Manager container settings {name} modified', 'de': 'Richtlinie: Univention Directory Manager Container Konfiguration {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_ADMIN_CONTAINER_REMOVED = DiaryEvent('UDM_POLICIES_ADMIN_CONTAINER_REMOVED', {'en': 'Policy: Univention Directory Manager container settings {name} removed', 'de': 'Richtlinie: Univention Directory Manager Container Konfiguration {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_AUTOSTART_CREATED = DiaryEvent('UDM_POLICIES_AUTOSTART_CREATED', {'en': 'Policy: Autostart {name} created', 'de': 'Richtlinie: Autostart {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_AUTOSTART_MODIFIED = DiaryEvent('UDM_POLICIES_AUTOSTART_MODIFIED', {'en': 'Policy: Autostart {name} modified', 'de': 'Richtlinie: Autostart {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_AUTOSTART_REMOVED = DiaryEvent('UDM_POLICIES_AUTOSTART_REMOVED', {'en': 'Policy: Autostart {name} removed', 'de': 'Richtlinie: Autostart {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DESKTOP_CREATED = DiaryEvent('UDM_POLICIES_DESKTOP_CREATED', {'en': 'Policy: Desktop {name} created', 'de': 'Richtlinie: Desktop {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DESKTOP_MODIFIED = DiaryEvent('UDM_POLICIES_DESKTOP_MODIFIED', {'en': 'Policy: Desktop {name} modified', 'de': 'Richtlinie: Desktop {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DESKTOP_REMOVED = DiaryEvent('UDM_POLICIES_DESKTOP_REMOVED', {'en': 'Policy: Desktop {name} removed', 'de': 'Richtlinie: Desktop {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_BOOT_CREATED = DiaryEvent('UDM_POLICIES_DHCP_BOOT_CREATED', {'en': 'Policy: DHCP Boot {name} created', 'de': 'Richtlinie: DHCP Boot {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_BOOT_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_BOOT_MODIFIED', {'en': 'Policy: DHCP Boot {name} modified', 'de': 'Richtlinie: DHCP Boot {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_BOOT_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_BOOT_REMOVED', {'en': 'Policy: DHCP Boot {name} removed', 'de': 'Richtlinie: DHCP Boot {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_DNS_CREATED = DiaryEvent('UDM_POLICIES_DHCP_DNS_CREATED', {'en': 'Policy: DHCP DNS {name} created', 'de': 'Richtlinie: DHCP DNS {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_DNS_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_DNS_MODIFIED', {'en': 'Policy: DHCP DNS {name} modified', 'de': 'Richtlinie: DHCP DNS {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_DNS_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_DNS_REMOVED', {'en': 'Policy: DHCP DNS {name} removed', 'de': 'Richtlinie: DHCP DNS {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_DNSUPDATE_CREATED = DiaryEvent('UDM_POLICIES_DHCP_DNSUPDATE_CREATED', {'en': 'Policy: DHCP Dynamic DNS {name} created', 'de': 'Richtlinie: DHCP DNS Aktualisierung {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_DNSUPDATE_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_DNSUPDATE_MODIFIED', {'en': 'Policy: DHCP Dynamic DNS {name} modified', 'de': 'Richtlinie: DHCP DNS Aktualisierung {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_DNSUPDATE_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_DNSUPDATE_REMOVED', {'en': 'Policy: DHCP Dynamic DNS {name} removed', 'de': 'Richtlinie: DHCP DNS Aktualisierung {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_LEASETIME_CREATED = DiaryEvent('UDM_POLICIES_DHCP_LEASETIME_CREATED', {'en': 'Policy: DHCP lease time {name} created', 'de': 'Richtlinie: DHCP Lease-Zeit {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_LEASETIME_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_LEASETIME_MODIFIED', {'en': 'Policy: DHCP lease time {name} modified', 'de': 'Richtlinie: DHCP Lease-Zeit {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_LEASETIME_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_LEASETIME_REMOVED', {'en': 'Policy: DHCP lease time {name} removed', 'de': 'Richtlinie: DHCP Lease-Zeit {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_NETBIOS_CREATED = DiaryEvent('UDM_POLICIES_DHCP_NETBIOS_CREATED', {'en': 'Policy: DHCP NetBIOS {name} created', 'de': 'Richtlinie: DHCP NetBIOS {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_NETBIOS_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_NETBIOS_MODIFIED', {'en': 'Policy: DHCP NetBIOS {name} modified', 'de': 'Richtlinie: DHCP NetBIOS {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_NETBIOS_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_NETBIOS_REMOVED', {'en': 'Policy: DHCP NetBIOS {name} removed', 'de': 'Richtlinie: DHCP NetBIOS {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_ROUTING_CREATED = DiaryEvent('UDM_POLICIES_DHCP_ROUTING_CREATED', {'en': 'Policy: DHCP routing {name} created', 'de': 'Richtlinie: DHCP Routing {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_ROUTING_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_ROUTING_MODIFIED', {'en': 'Policy: DHCP routing {name} modified', 'de': 'Richtlinie: DHCP Routing {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_ROUTING_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_ROUTING_REMOVED', {'en': 'Policy: DHCP routing {name} removed', 'de': 'Richtlinie: DHCP Routing {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_SCOPE_CREATED = DiaryEvent('UDM_POLICIES_DHCP_SCOPE_CREATED', {'en': 'Policy: DHCP Allow/Deny {name} created', 'de': 'Richtlinie: DHCP Erlauben/Verbieten {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_SCOPE_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_SCOPE_MODIFIED', {'en': 'Policy: DHCP Allow/Deny {name} modified', 'de': 'Richtlinie: DHCP Erlauben/Verbieten {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_SCOPE_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_SCOPE_REMOVED', {'en': 'Policy: DHCP Allow/Deny {name} removed', 'de': 'Richtlinie: DHCP Erlauben/Verbieten {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_DHCP_STATEMENTS_CREATED = DiaryEvent('UDM_POLICIES_DHCP_STATEMENTS_CREATED', {'en': 'Policy: DHCP statements {name} created', 'de': 'Richtlinie: DHCP Verschiedenes {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_STATEMENTS_MODIFIED = DiaryEvent('UDM_POLICIES_DHCP_STATEMENTS_MODIFIED', {'en': 'Policy: DHCP statements {name} modified', 'de': 'Richtlinie: DHCP Verschiedenes {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_DHCP_STATEMENTS_REMOVED = DiaryEvent('UDM_POLICIES_DHCP_STATEMENTS_REMOVED', {'en': 'Policy: DHCP statements {name} removed', 'de': 'Richtlinie: DHCP Verschiedenes {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_LDAPSERVER_CREATED = DiaryEvent('UDM_POLICIES_LDAPSERVER_CREATED', {'en': 'Policy: LDAP server {name} created', 'de': 'Richtlinie: LDAP-Server {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_LDAPSERVER_MODIFIED = DiaryEvent('UDM_POLICIES_LDAPSERVER_MODIFIED', {'en': 'Policy: LDAP server {name} modified', 'de': 'Richtlinie: LDAP-Server {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_LDAPSERVER_REMOVED = DiaryEvent('UDM_POLICIES_LDAPSERVER_REMOVED', {'en': 'Policy: LDAP server {name} removed', 'de': 'Richtlinie: LDAP-Server {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_MAINTENANCE_CREATED = DiaryEvent('UDM_POLICIES_MAINTENANCE_CREATED', {'en': 'Policy: Maintenance {name} created', 'de': 'Richtlinie: Paketpflege {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_MAINTENANCE_MODIFIED = DiaryEvent('UDM_POLICIES_MAINTENANCE_MODIFIED', {'en': 'Policy: Maintenance {name} modified', 'de': 'Richtlinie: Paketpflege {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_MAINTENANCE_REMOVED = DiaryEvent('UDM_POLICIES_MAINTENANCE_REMOVED', {'en': 'Policy: Maintenance {name} removed', 'de': 'Richtlinie: Paketpflege {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_MASTERPACKAGES_CREATED = DiaryEvent('UDM_POLICIES_MASTERPACKAGES_CREATED', {'en': 'Policy: Master packages {name} created', 'de': 'Richtlinie: Master Pakete {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_MASTERPACKAGES_MODIFIED = DiaryEvent('UDM_POLICIES_MASTERPACKAGES_MODIFIED', {'en': 'Policy: Master packages {name} modified', 'de': 'Richtlinie: Master Pakete {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_MASTERPACKAGES_REMOVED = DiaryEvent('UDM_POLICIES_MASTERPACKAGES_REMOVED', {'en': 'Policy: Master packages {name} removed', 'de': 'Richtlinie: Master Pakete {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_MEMBERPACKAGES_CREATED = DiaryEvent('UDM_POLICIES_MEMBERPACKAGES_CREATED', {'en': 'Policy: Member Server packages {name} created', 'de': 'Richtlinie: Memberserver Pakete {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_MEMBERPACKAGES_MODIFIED = DiaryEvent('UDM_POLICIES_MEMBERPACKAGES_MODIFIED', {'en': 'Policy: Member Server packages {name} modified', 'de': 'Richtlinie: Memberserver Pakete {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_MEMBERPACKAGES_REMOVED = DiaryEvent('UDM_POLICIES_MEMBERPACKAGES_REMOVED', {'en': 'Policy: Member Server packages {name} removed', 'de': 'Richtlinie: Memberserver Pakete {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_NFSMOUNTS_CREATED = DiaryEvent('UDM_POLICIES_NFSMOUNTS_CREATED', {'en': 'Policy: NFS mounts {name} created', 'de': 'Richtlinie: NFS-Freigaben {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_NFSMOUNTS_MODIFIED = DiaryEvent('UDM_POLICIES_NFSMOUNTS_MODIFIED', {'en': 'Policy: NFS mounts {name} modified', 'de': 'Richtlinie: NFS-Freigaben {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_NFSMOUNTS_REMOVED = DiaryEvent('UDM_POLICIES_NFSMOUNTS_REMOVED', {'en': 'Policy: NFS mounts {name} removed', 'de': 'Richtlinie: NFS-Freigaben {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_PRINT_QUOTA_CREATED = DiaryEvent('UDM_POLICIES_PRINT_QUOTA_CREATED', {'en': 'Policy: Print quota {name} created', 'de': 'Richtlinie: Druck-Quota {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_PRINT_QUOTA_MODIFIED = DiaryEvent('UDM_POLICIES_PRINT_QUOTA_MODIFIED', {'en': 'Policy: Print quota {name} modified', 'de': 'Richtlinie: Druck-Quota {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_PRINT_QUOTA_REMOVED = DiaryEvent('UDM_POLICIES_PRINT_QUOTA_REMOVED', {'en': 'Policy: Print quota {name} removed', 'de': 'Richtlinie: Druck-Quota {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_PRINTSERVER_CREATED = DiaryEvent('UDM_POLICIES_PRINTSERVER_CREATED', {'en': 'Policy: Print server {name} created', 'de': 'Richtlinie: Druckserver {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_PRINTSERVER_MODIFIED = DiaryEvent('UDM_POLICIES_PRINTSERVER_MODIFIED', {'en': 'Policy: Print server {name} modified', 'de': 'Richtlinie: Druckserver {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_PRINTSERVER_REMOVED = DiaryEvent('UDM_POLICIES_PRINTSERVER_REMOVED', {'en': 'Policy: Print server {name} removed', 'de': 'Richtlinie: Druckserver {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_PWHISTORY_CREATED = DiaryEvent('UDM_POLICIES_PWHISTORY_CREATED', {'en': 'Policy: Passwords {name} created', 'de': 'Richtlinie: Passwort {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_PWHISTORY_MODIFIED = DiaryEvent('UDM_POLICIES_PWHISTORY_MODIFIED', {'en': 'Policy: Passwords {name} modified', 'de': 'Richtlinie: Passwort {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_PWHISTORY_REMOVED = DiaryEvent('UDM_POLICIES_PWHISTORY_REMOVED', {'en': 'Policy: Passwords {name} removed', 'de': 'Richtlinie: Passwort {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_REGISTRY_CREATED = DiaryEvent('UDM_POLICIES_REGISTRY_CREATED', {'en': 'Policy: Univention Configuration Registry {name} created', 'de': 'Richtlinie: Univention Configuration Registry {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_REGISTRY_MODIFIED = DiaryEvent('UDM_POLICIES_REGISTRY_MODIFIED', {'en': 'Policy: Univention Configuration Registry {name} modified', 'de': 'Richtlinie: Univention Configuration Registry {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_REGISTRY_REMOVED = DiaryEvent('UDM_POLICIES_REGISTRY_REMOVED', {'en': 'Policy: Univention Configuration Registry {name} removed', 'de': 'Richtlinie: Univention Configuration Registry {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_RELEASE_CREATED = DiaryEvent('UDM_POLICIES_RELEASE_CREATED', {'en': 'Policy: Automatic updates {name} created', 'de': 'Richtlinie: Automatische Updates {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_RELEASE_MODIFIED = DiaryEvent('UDM_POLICIES_RELEASE_MODIFIED', {'en': 'Policy: Automatic updates {name} modified', 'de': 'Richtlinie: Automatische Updates {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_RELEASE_REMOVED = DiaryEvent('UDM_POLICIES_RELEASE_REMOVED', {'en': 'Policy: Automatic updates {name} removed', 'de': 'Richtlinie: Automatische Updates {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_REPOSITORYSERVER_CREATED = DiaryEvent('UDM_POLICIES_REPOSITORYSERVER_CREATED', {'en': 'Policy: Repository server {name} created', 'de': 'Richtlinie: Repository-Server {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_REPOSITORYSERVER_MODIFIED = DiaryEvent('UDM_POLICIES_REPOSITORYSERVER_MODIFIED', {'en': 'Policy: Repository server {name} modified', 'de': 'Richtlinie: Repository-Server {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_REPOSITORYSERVER_REMOVED = DiaryEvent('UDM_POLICIES_REPOSITORYSERVER_REMOVED', {'en': 'Policy: Repository server {name} removed', 'de': 'Richtlinie: Repository-Server {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_REPOSITORYSYNC_CREATED = DiaryEvent('UDM_POLICIES_REPOSITORYSYNC_CREATED', {'en': 'Policy: Repository synchronisation {name} created', 'de': 'Richtlinie: Repository-Synchronisation {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_REPOSITORYSYNC_MODIFIED = DiaryEvent('UDM_POLICIES_REPOSITORYSYNC_MODIFIED', {'en': 'Policy: Repository synchronisation {name} modified', 'de': 'Richtlinie: Repository-Synchronisation {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_REPOSITORYSYNC_REMOVED = DiaryEvent('UDM_POLICIES_REPOSITORYSYNC_REMOVED', {'en': 'Policy: Repository synchronisation {name} removed', 'de': 'Richtlinie: Repository-Synchronisation {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_SHARE_USERQUOTA_CREATED = DiaryEvent('UDM_POLICIES_SHARE_USERQUOTA_CREATED', {'en': 'Policy: User quota {name} created', 'de': 'Richtlinie: Benutzer-Quota {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_SHARE_USERQUOTA_MODIFIED = DiaryEvent('UDM_POLICIES_SHARE_USERQUOTA_MODIFIED', {'en': 'Policy: User quota {name} modified', 'de': 'Richtlinie: Benutzer-Quota {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_SHARE_USERQUOTA_REMOVED = DiaryEvent('UDM_POLICIES_SHARE_USERQUOTA_REMOVED', {'en': 'Policy: User quota {name} removed', 'de': 'Richtlinie: Benutzer-Quota {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_SLAVEPACKAGES_CREATED = DiaryEvent('UDM_POLICIES_SLAVEPACKAGES_CREATED', {'en': 'Policy: Slave packages {name} created', 'de': 'Richtlinie: Slave Pakete {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_SLAVEPACKAGES_MODIFIED = DiaryEvent('UDM_POLICIES_SLAVEPACKAGES_MODIFIED', {'en': 'Policy: Slave packages {name} modified', 'de': 'Richtlinie: Slave Pakete {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_SLAVEPACKAGES_REMOVED = DiaryEvent('UDM_POLICIES_SLAVEPACKAGES_REMOVED', {'en': 'Policy: Slave packages {name} removed', 'de': 'Richtlinie: Slave Pakete {name} gelöscht'}, args=['name'], icon='domain')

UDM_POLICIES_UMC_CREATED = DiaryEvent('UDM_POLICIES_UMC_CREATED', {'en': 'Policy: UMC {name} created', 'de': 'Policy: UMC {name} angelegt'}, args=['name'], icon='domain')
UDM_POLICIES_UMC_MODIFIED = DiaryEvent('UDM_POLICIES_UMC_MODIFIED', {'en': 'Policy: UMC {name} modified', 'de': 'Policy: UMC {name} bearbeitet'}, args=['name'], icon='domain')
UDM_POLICIES_UMC_REMOVED = DiaryEvent('UDM_POLICIES_UMC_REMOVED', {'en': 'Policy: UMC {name} removed', 'de': 'Policy: UMC {name} gelöscht'}, args=['name'], icon='domain')

UDM_SAML_IDPCONFIG_CREATED = DiaryEvent('UDM_SAML_IDPCONFIG_CREATED', {'en': 'SAML IdP configuration {id} created', 'de': 'SAML IdP configuration {id} angelegt'}, args=['id'], icon='domain')
UDM_SAML_IDPCONFIG_MODIFIED = DiaryEvent('UDM_SAML_IDPCONFIG_MODIFIED', {'en': 'SAML IdP configuration {id} modified', 'de': 'SAML IdP configuration {id} bearbeitet'}, args=['id'], icon='domain')
UDM_SAML_IDPCONFIG_REMOVED = DiaryEvent('UDM_SAML_IDPCONFIG_REMOVED', {'en': 'SAML IdP configuration {id} removed', 'de': 'SAML IdP configuration {id} gelöscht'}, args=['id'], icon='domain')

UDM_SAML_SERVICEPROVIDER_CREATED = DiaryEvent('UDM_SAML_SERVICEPROVIDER_CREATED', {'en': 'SAML service provider {Identifier} created', 'de': 'SAML service provider {Identifier} angelegt'}, args=['Identifier'], icon='domain')
UDM_SAML_SERVICEPROVIDER_MODIFIED = DiaryEvent('UDM_SAML_SERVICEPROVIDER_MODIFIED', {'en': 'SAML service provider {Identifier} modified', 'de': 'SAML service provider {Identifier} bearbeitet'}, args=['Identifier'], icon='domain')
UDM_SAML_SERVICEPROVIDER_REMOVED = DiaryEvent('UDM_SAML_SERVICEPROVIDER_REMOVED', {'en': 'SAML service provider {Identifier} removed', 'de': 'SAML service provider {Identifier} gelöscht'}, args=['Identifier'], icon='domain')

UDM_SETTINGS_DATA_CREATED = DiaryEvent('UDM_SETTINGS_DATA_CREATED', {'en': 'Data {name} created', 'de': 'Data {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_DATA_MODIFIED = DiaryEvent('UDM_SETTINGS_DATA_MODIFIED', {'en': 'Data {name} modified', 'de': 'Data {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_DATA_MOVED = DiaryEvent('UDM_SETTINGS_DATA_MOVED', {'en': 'Data {name} moved to {position}', 'de': 'Data {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_DATA_REMOVED = DiaryEvent('UDM_SETTINGS_DATA_REMOVED', {'en': 'Data {name} removed', 'de': 'Data {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_DEFAULT_MODIFIED = DiaryEvent('UDM_SETTINGS_DEFAULT_MODIFIED', {'en': 'Preferences: Default {name} modified', 'de': 'Einstellungen: Vorgabe {name} bearbeitet'}, args=['name'], icon='domain')

UDM_SETTINGS_DIRECTORY_MODIFIED = DiaryEvent('UDM_SETTINGS_DIRECTORY_MODIFIED', {'en': 'Preferences: Default Container {name} modified', 'de': 'Einstellungen: Standard-Container {name} bearbeitet'}, args=['name'], icon='domain')

UDM_SETTINGS_EXTENDED_ATTRIBUTE_CREATED = DiaryEvent('UDM_SETTINGS_EXTENDED_ATTRIBUTE_CREATED', {'en': 'Settings: Extended attribute {name} created', 'de': 'Einstellungen: Erweitertes Attribut {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_ATTRIBUTE_MODIFIED = DiaryEvent('UDM_SETTINGS_EXTENDED_ATTRIBUTE_MODIFIED', {'en': 'Settings: Extended attribute {name} modified', 'de': 'Einstellungen: Erweitertes Attribut {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_ATTRIBUTE_MOVED = DiaryEvent('UDM_SETTINGS_EXTENDED_ATTRIBUTE_MOVED', {'en': 'Settings: Extended attribute {name} moved to {position}', 'de': 'Einstellungen: Erweitertes Attribut {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_ATTRIBUTE_REMOVED = DiaryEvent('UDM_SETTINGS_EXTENDED_ATTRIBUTE_REMOVED', {'en': 'Settings: Extended attribute {name} removed', 'de': 'Einstellungen: Erweitertes Attribut {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_EXTENDED_OPTIONS_CREATED = DiaryEvent('UDM_SETTINGS_EXTENDED_OPTIONS_CREATED', {'en': 'Settings: Extended options {name} created', 'de': 'Einstellungen: Erweiterte Optionen {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_OPTIONS_MODIFIED = DiaryEvent('UDM_SETTINGS_EXTENDED_OPTIONS_MODIFIED', {'en': 'Settings: Extended options {name} modified', 'de': 'Einstellungen: Erweiterte Optionen {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_OPTIONS_MOVED = DiaryEvent('UDM_SETTINGS_EXTENDED_OPTIONS_MOVED', {'en': 'Settings: Extended options {name} moved to {position}', 'de': 'Einstellungen: Erweiterte Optionen {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_EXTENDED_OPTIONS_REMOVED = DiaryEvent('UDM_SETTINGS_EXTENDED_OPTIONS_REMOVED', {'en': 'Settings: Extended options {name} removed', 'de': 'Einstellungen: Erweiterte Optionen {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_LDAPACL_CREATED = DiaryEvent('UDM_SETTINGS_LDAPACL_CREATED', {'en': 'Settings: LDAP ACL Extension {name} created', 'de': 'Einstellungen: LDAP ACL Erweiterung {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPACL_MODIFIED = DiaryEvent('UDM_SETTINGS_LDAPACL_MODIFIED', {'en': 'Settings: LDAP ACL Extension {name} modified', 'de': 'Einstellungen: LDAP ACL Erweiterung {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPACL_MOVED = DiaryEvent('UDM_SETTINGS_LDAPACL_MOVED', {'en': 'Settings: LDAP ACL Extension {name} moved to {position}', 'de': 'Einstellungen: LDAP ACL Erweiterung {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPACL_REMOVED = DiaryEvent('UDM_SETTINGS_LDAPACL_REMOVED', {'en': 'Settings: LDAP ACL Extension {name} removed', 'de': 'Einstellungen: LDAP ACL Erweiterung {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_LDAPSCHEMA_CREATED = DiaryEvent('UDM_SETTINGS_LDAPSCHEMA_CREATED', {'en': 'Settings: LDAP Schema Extension {name} created', 'de': 'Einstellungen: LDAP-Schemaerweiterung {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPSCHEMA_MODIFIED = DiaryEvent('UDM_SETTINGS_LDAPSCHEMA_MODIFIED', {'en': 'Settings: LDAP Schema Extension {name} modified', 'de': 'Einstellungen: LDAP-Schemaerweiterung {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPSCHEMA_MOVED = DiaryEvent('UDM_SETTINGS_LDAPSCHEMA_MOVED', {'en': 'Settings: LDAP Schema Extension {name} moved to {position}', 'de': 'Einstellungen: LDAP-Schemaerweiterung {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_LDAPSCHEMA_REMOVED = DiaryEvent('UDM_SETTINGS_LDAPSCHEMA_REMOVED', {'en': 'Settings: LDAP Schema Extension {name} removed', 'de': 'Einstellungen: LDAP-Schemaerweiterung {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_LICENSE_REMOVED = DiaryEvent('UDM_SETTINGS_LICENSE_REMOVED', {'en': 'Settings: License {name} ({keyID}) removed', 'de': 'Einstellungen: Lizenz {name} ({keyID}) gelöscht'}, args=['name', 'keyID'], icon='domain')

UDM_SETTINGS_LOCK_MODIFIED = DiaryEvent('UDM_SETTINGS_LOCK_MODIFIED', {'en': 'Settings: Lock {name} ({locktime}) modified', 'de': 'Einstellungen: Sperrung {name} ({locktime}) bearbeitet'}, args=['name', 'locktime'], icon='domain')
UDM_SETTINGS_LOCK_REMOVED = DiaryEvent('UDM_SETTINGS_LOCK_REMOVED', {'en': 'Settings: Lock {name} ({locktime}) removed', 'de': 'Einstellungen: Sperrung {name} ({locktime}) gelöscht'}, args=['name', 'locktime'], icon='domain')

UDM_SETTINGS_PACKAGES_CREATED = DiaryEvent('UDM_SETTINGS_PACKAGES_CREATED', {'en': 'Settings: Package List {name} created', 'de': 'Einstellungen: Paketliste {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PACKAGES_MODIFIED = DiaryEvent('UDM_SETTINGS_PACKAGES_MODIFIED', {'en': 'Settings: Package List {name} modified', 'de': 'Einstellungen: Paketliste {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PACKAGES_MOVED = DiaryEvent('UDM_SETTINGS_PACKAGES_MOVED', {'en': 'Settings: Package List {name} moved to {position}', 'de': 'Einstellungen: Paketliste {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PACKAGES_REMOVED = DiaryEvent('UDM_SETTINGS_PACKAGES_REMOVED', {'en': 'Settings: Package List {name} removed', 'de': 'Einstellungen: Paketliste {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PORTAL_CREATED = DiaryEvent('UDM_SETTINGS_PORTAL_CREATED', {'en': 'Portal: Portal {name} created', 'de': 'Portal: Portal {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_MODIFIED = DiaryEvent('UDM_SETTINGS_PORTAL_MODIFIED', {'en': 'Portal: Portal {name} modified', 'de': 'Portal: Portal {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_MOVED = DiaryEvent('UDM_SETTINGS_PORTAL_MOVED', {'en': 'Portal: Portal {name} moved to {position}', 'de': 'Portal: Portal {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_REMOVED = DiaryEvent('UDM_SETTINGS_PORTAL_REMOVED', {'en': 'Portal: Portal {name} removed', 'de': 'Portal: Portal {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PORTAL_CATEGORY_CREATED = DiaryEvent('UDM_SETTINGS_PORTAL_CATEGORY_CREATED', {'en': 'Portal: Category {name} created', 'de': 'Portal: Kategorie {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_CATEGORY_MODIFIED = DiaryEvent('UDM_SETTINGS_PORTAL_CATEGORY_MODIFIED', {'en': 'Portal: Category {name} modified', 'de': 'Portal: Kategorie {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_CATEGORY_MOVED = DiaryEvent('UDM_SETTINGS_PORTAL_CATEGORY_MOVED', {'en': 'Portal: Category {name} moved to {position}', 'de': 'Portal: Kategorie {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_CATEGORY_REMOVED = DiaryEvent('UDM_SETTINGS_PORTAL_CATEGORY_REMOVED', {'en': 'Portal: Category {name} removed', 'de': 'Portal: Kategorie {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PORTAL_ENTRY_CREATED = DiaryEvent('UDM_SETTINGS_PORTAL_ENTRY_CREATED', {'en': 'Portal: Entry {name} created', 'de': 'Portal: Eintrag {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_ENTRY_MODIFIED = DiaryEvent('UDM_SETTINGS_PORTAL_ENTRY_MODIFIED', {'en': 'Portal: Entry {name} modified', 'de': 'Portal: Eintrag {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_ENTRY_MOVED = DiaryEvent('UDM_SETTINGS_PORTAL_ENTRY_MOVED', {'en': 'Portal: Entry {name} moved to {position}', 'de': 'Portal: Eintrag {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PORTAL_ENTRY_REMOVED = DiaryEvent('UDM_SETTINGS_PORTAL_ENTRY_REMOVED', {'en': 'Portal: Entry {name} removed', 'de': 'Portal: Eintrag {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PRINTERMODEL_CREATED = DiaryEvent('UDM_SETTINGS_PRINTERMODEL_CREATED', {'en': 'Settings: Printer Driver List {name} created', 'de': 'Einstellungen: Druckertreiberliste {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERMODEL_MODIFIED = DiaryEvent('UDM_SETTINGS_PRINTERMODEL_MODIFIED', {'en': 'Settings: Printer Driver List {name} modified', 'de': 'Einstellungen: Druckertreiberliste {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERMODEL_MOVED = DiaryEvent('UDM_SETTINGS_PRINTERMODEL_MOVED', {'en': 'Settings: Printer Driver List {name} moved to {position}', 'de': 'Einstellungen: Druckertreiberliste {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERMODEL_REMOVED = DiaryEvent('UDM_SETTINGS_PRINTERMODEL_REMOVED', {'en': 'Settings: Printer Driver List {name} removed', 'de': 'Einstellungen: Druckertreiberliste {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PRINTERURI_CREATED = DiaryEvent('UDM_SETTINGS_PRINTERURI_CREATED', {'en': 'Settings: Printer URI List {name} created', 'de': 'Einstellungen: Drucker-URI-Liste {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERURI_MODIFIED = DiaryEvent('UDM_SETTINGS_PRINTERURI_MODIFIED', {'en': 'Settings: Printer URI List {name} modified', 'de': 'Einstellungen: Drucker-URI-Liste {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERURI_MOVED = DiaryEvent('UDM_SETTINGS_PRINTERURI_MOVED', {'en': 'Settings: Printer URI List {name} moved to {position}', 'de': 'Einstellungen: Drucker-URI-Liste {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PRINTERURI_REMOVED = DiaryEvent('UDM_SETTINGS_PRINTERURI_REMOVED', {'en': 'Settings: Printer URI List {name} removed', 'de': 'Einstellungen: Drucker-URI-Liste {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_PROHIBITED_USERNAME_CREATED = DiaryEvent('UDM_SETTINGS_PROHIBITED_USERNAME_CREATED', {'en': 'Settings: Prohibited user names {name} created', 'de': 'Einstellungen: Verbotene Benutzernamen {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_PROHIBITED_USERNAME_MODIFIED = DiaryEvent('UDM_SETTINGS_PROHIBITED_USERNAME_MODIFIED', {'en': 'Settings: Prohibited user names {name} modified', 'de': 'Einstellungen: Verbotene Benutzernamen {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_PROHIBITED_USERNAME_MOVED = DiaryEvent('UDM_SETTINGS_PROHIBITED_USERNAME_MOVED', {'en': 'Settings: Prohibited user names {name} moved to {position}', 'de': 'Einstellungen: Verbotene Benutzernamen {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_PROHIBITED_USERNAME_REMOVED = DiaryEvent('UDM_SETTINGS_PROHIBITED_USERNAME_REMOVED', {'en': 'Settings: Prohibited user names {name} removed', 'de': 'Einstellungen: Verbotene Benutzernamen {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_SAMBACONFIG_MODIFIED = DiaryEvent('UDM_SETTINGS_SAMBACONFIG_MODIFIED', {'en': 'Settings: Samba Configuration {name} modified', 'de': 'Einstellungen: Samba-Konfiguration {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_SAMBACONFIG_MOVED = DiaryEvent('UDM_SETTINGS_SAMBACONFIG_MOVED', {'en': 'Settings: Samba Configuration {name} moved to {position}', 'de': 'Einstellungen: Samba-Konfiguration {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_SAMBACONFIG_REMOVED = DiaryEvent('UDM_SETTINGS_SAMBACONFIG_REMOVED', {'en': 'Settings: Samba Configuration {name} removed', 'de': 'Einstellungen: Samba-Konfiguration {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_SAMBADOMAIN_CREATED = DiaryEvent('UDM_SETTINGS_SAMBADOMAIN_CREATED', {'en': 'Settings: Samba Domain {name} ({SID}) created', 'de': 'Einstellungen: Samba-Domäne {name} ({SID}) angelegt'}, args=['name', 'SID'], icon='domain')
UDM_SETTINGS_SAMBADOMAIN_MODIFIED = DiaryEvent('UDM_SETTINGS_SAMBADOMAIN_MODIFIED', {'en': 'Settings: Samba Domain {name} ({SID}) modified', 'de': 'Einstellungen: Samba-Domäne {name} ({SID}) bearbeitet'}, args=['name', 'SID'], icon='domain')
UDM_SETTINGS_SAMBADOMAIN_MOVED = DiaryEvent('UDM_SETTINGS_SAMBADOMAIN_MOVED', {'en': 'Settings: Samba Domain {name} ({SID}) moved to {position}', 'de': 'Einstellungen: Samba-Domäne {name} ({SID}) verschoben nach {position}'}, args=['name', 'SID'], icon='domain')
UDM_SETTINGS_SAMBADOMAIN_REMOVED = DiaryEvent('UDM_SETTINGS_SAMBADOMAIN_REMOVED', {'en': 'Settings: Samba Domain {name} ({SID}) removed', 'de': 'Einstellungen: Samba-Domäne {name} ({SID}) gelöscht'}, args=['name', 'SID'], icon='domain')

UDM_SETTINGS_SERVICE_CREATED = DiaryEvent('UDM_SETTINGS_SERVICE_CREATED', {'en': 'Settings: Service {name} created', 'de': 'Einstellungen: Dienst {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_SERVICE_MODIFIED = DiaryEvent('UDM_SETTINGS_SERVICE_MODIFIED', {'en': 'Settings: Service {name} modified', 'de': 'Einstellungen: Dienst {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_SERVICE_MOVED = DiaryEvent('UDM_SETTINGS_SERVICE_MOVED', {'en': 'Settings: Service {name} moved to {position}', 'de': 'Einstellungen: Dienst {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_SERVICE_REMOVED = DiaryEvent('UDM_SETTINGS_SERVICE_REMOVED', {'en': 'Settings: Service {name} removed', 'de': 'Einstellungen: Dienst {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_SYNTAX_CREATED = DiaryEvent('UDM_SETTINGS_SYNTAX_CREATED', {'en': 'Settings: Syntax Definition {name} created', 'de': 'Einstellungen: Syntax-Definition {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_SYNTAX_MODIFIED = DiaryEvent('UDM_SETTINGS_SYNTAX_MODIFIED', {'en': 'Settings: Syntax Definition {name} modified', 'de': 'Einstellungen: Syntax-Definition {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_SYNTAX_MOVED = DiaryEvent('UDM_SETTINGS_SYNTAX_MOVED', {'en': 'Settings: Syntax Definition {name} moved to {position}', 'de': 'Einstellungen: Syntax-Definition {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_SYNTAX_REMOVED = DiaryEvent('UDM_SETTINGS_SYNTAX_REMOVED', {'en': 'Settings: Syntax Definition {name} removed', 'de': 'Einstellungen: Syntax-Definition {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_UDM_HOOK_CREATED = DiaryEvent('UDM_SETTINGS_UDM_HOOK_CREATED', {'en': 'Settings: UDM Hook {name} created', 'de': 'Einstellungen: UDM Hook {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_HOOK_MODIFIED = DiaryEvent('UDM_SETTINGS_UDM_HOOK_MODIFIED', {'en': 'Settings: UDM Hook {name} modified', 'de': 'Einstellungen: UDM Hook {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_HOOK_MOVED = DiaryEvent('UDM_SETTINGS_UDM_HOOK_MOVED', {'en': 'Settings: UDM Hook {name} moved to {position}', 'de': 'Einstellungen: UDM Hook {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_HOOK_REMOVED = DiaryEvent('UDM_SETTINGS_UDM_HOOK_REMOVED', {'en': 'Settings: UDM Hook {name} removed', 'de': 'Einstellungen: UDM Hook {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_UDM_MODULE_CREATED = DiaryEvent('UDM_SETTINGS_UDM_MODULE_CREATED', {'en': 'Settings: UDM Module {name} created', 'de': 'Einstellungen: UDM Modul {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_MODULE_MODIFIED = DiaryEvent('UDM_SETTINGS_UDM_MODULE_MODIFIED', {'en': 'Settings: UDM Module {name} modified', 'de': 'Einstellungen: UDM Modul {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_MODULE_MOVED = DiaryEvent('UDM_SETTINGS_UDM_MODULE_MOVED', {'en': 'Settings: UDM Module {name} moved to {position}', 'de': 'Einstellungen: UDM Modul {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_MODULE_REMOVED = DiaryEvent('UDM_SETTINGS_UDM_MODULE_REMOVED', {'en': 'Settings: UDM Module {name} removed', 'de': 'Einstellungen: UDM Modul {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_UDM_SYNTAX_CREATED = DiaryEvent('UDM_SETTINGS_UDM_SYNTAX_CREATED', {'en': 'Settings: UDM Syntax {name} created', 'de': 'Einstellungen: UDM Syntax {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_SYNTAX_MODIFIED = DiaryEvent('UDM_SETTINGS_UDM_SYNTAX_MODIFIED', {'en': 'Settings: UDM Syntax {name} modified', 'de': 'Einstellungen: UDM Syntax {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_SYNTAX_MOVED = DiaryEvent('UDM_SETTINGS_UDM_SYNTAX_MOVED', {'en': 'Settings: UDM Syntax {name} moved to {position}', 'de': 'Einstellungen: UDM Syntax {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_UDM_SYNTAX_REMOVED = DiaryEvent('UDM_SETTINGS_UDM_SYNTAX_REMOVED', {'en': 'Settings: UDM Syntax {name} removed', 'de': 'Einstellungen: UDM Syntax {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_UMC_OPERATIONSET_CREATED = DiaryEvent('UDM_SETTINGS_UMC_OPERATIONSET_CREATED', {'en': 'Settings: UMC operation set {name} created', 'de': 'Einstellungen: UMC-Operationen {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_UMC_OPERATIONSET_MODIFIED = DiaryEvent('UDM_SETTINGS_UMC_OPERATIONSET_MODIFIED', {'en': 'Settings: UMC operation set {name} modified', 'de': 'Einstellungen: UMC-Operationen {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_UMC_OPERATIONSET_MOVED = DiaryEvent('UDM_SETTINGS_UMC_OPERATIONSET_MOVED', {'en': 'Settings: UMC operation set {name} moved to {position}', 'de': 'Einstellungen: UMC-Operationen {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_UMC_OPERATIONSET_REMOVED = DiaryEvent('UDM_SETTINGS_UMC_OPERATIONSET_REMOVED', {'en': 'Settings: UMC operation set {name} removed', 'de': 'Einstellungen: UMC-Operationen {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_USERTEMPLATE_CREATED = DiaryEvent('UDM_SETTINGS_USERTEMPLATE_CREATED', {'en': 'Settings: User Template {name} created', 'de': 'Einstellungen: Benutzervorlage {name} angelegt'}, args=['name'], icon='domain')
UDM_SETTINGS_USERTEMPLATE_MODIFIED = DiaryEvent('UDM_SETTINGS_USERTEMPLATE_MODIFIED', {'en': 'Settings: User Template {name} modified', 'de': 'Einstellungen: Benutzervorlage {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SETTINGS_USERTEMPLATE_MOVED = DiaryEvent('UDM_SETTINGS_USERTEMPLATE_MOVED', {'en': 'Settings: User Template {name} moved to {position}', 'de': 'Einstellungen: Benutzervorlage {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SETTINGS_USERTEMPLATE_REMOVED = DiaryEvent('UDM_SETTINGS_USERTEMPLATE_REMOVED', {'en': 'Settings: User Template {name} removed', 'de': 'Einstellungen: Benutzervorlage {name} gelöscht'}, args=['name'], icon='domain')

UDM_SETTINGS_XCONFIG_CHOICES_MODIFIED = DiaryEvent('UDM_SETTINGS_XCONFIG_CHOICES_MODIFIED', {'en': 'Preferences: X Configuration Choices {name} modified', 'de': 'Einstellungen: X-Konfigurationsauswahl {name} bearbeitet'}, args=['name'], icon='domain')

UDM_SHARES_PRINTER_CREATED = DiaryEvent('UDM_SHARES_PRINTER_CREATED', {'en': 'Printer share: Printer {name} created', 'de': 'Druckerfreigabe: Drucker {name} angelegt'}, args=['name'], icon='domain')
UDM_SHARES_PRINTER_MODIFIED = DiaryEvent('UDM_SHARES_PRINTER_MODIFIED', {'en': 'Printer share: Printer {name} modified', 'de': 'Druckerfreigabe: Drucker {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SHARES_PRINTER_MOVED = DiaryEvent('UDM_SHARES_PRINTER_MOVED', {'en': 'Printer share: Printer {name} moved to {position}', 'de': 'Druckerfreigabe: Drucker {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SHARES_PRINTER_REMOVED = DiaryEvent('UDM_SHARES_PRINTER_REMOVED', {'en': 'Printer share: Printer {name} removed', 'de': 'Druckerfreigabe: Drucker {name} gelöscht'}, args=['name'], icon='domain')

UDM_SHARES_PRINTERGROUP_CREATED = DiaryEvent('UDM_SHARES_PRINTERGROUP_CREATED', {'en': 'Printer share: Printer group {name} created', 'de': 'Druckerfreigabe: Druckergruppe {name} angelegt'}, args=['name'], icon='domain')
UDM_SHARES_PRINTERGROUP_MODIFIED = DiaryEvent('UDM_SHARES_PRINTERGROUP_MODIFIED', {'en': 'Printer share: Printer group {name} modified', 'de': 'Druckerfreigabe: Druckergruppe {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SHARES_PRINTERGROUP_MOVED = DiaryEvent('UDM_SHARES_PRINTERGROUP_MOVED', {'en': 'Printer share: Printer group {name} moved to {position}', 'de': 'Druckerfreigabe: Druckergruppe {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SHARES_PRINTERGROUP_REMOVED = DiaryEvent('UDM_SHARES_PRINTERGROUP_REMOVED', {'en': 'Printer share: Printer group {name} removed', 'de': 'Druckerfreigabe: Druckergruppe {name} gelöscht'}, args=['name'], icon='domain')

UDM_SHARES_SHARE_CREATED = DiaryEvent('UDM_SHARES_SHARE_CREATED', {'en': 'Share: Directory {name} created', 'de': 'Freigabe: Verzeichnis {name} angelegt'}, args=['name'], icon='domain')
UDM_SHARES_SHARE_MODIFIED = DiaryEvent('UDM_SHARES_SHARE_MODIFIED', {'en': 'Share: Directory {name} modified', 'de': 'Freigabe: Verzeichnis {name} bearbeitet'}, args=['name'], icon='domain')
UDM_SHARES_SHARE_MOVED = DiaryEvent('UDM_SHARES_SHARE_MOVED', {'en': 'Share: Directory {name} moved to {position}', 'de': 'Freigabe: Verzeichnis {name} verschoben nach {position}'}, args=['name'], icon='domain')
UDM_SHARES_SHARE_REMOVED = DiaryEvent('UDM_SHARES_SHARE_REMOVED', {'en': 'Share: Directory {name} removed', 'de': 'Freigabe: Verzeichnis {name} gelöscht'}, args=['name'], icon='domain')

UDM_USERS_CONTACT_CREATED = DiaryEvent('UDM_USERS_CONTACT_CREATED', {'en': 'Contact {cn} created', 'de': 'Kontakt {cn} angelegt'}, args=['cn'], icon='users')
UDM_USERS_CONTACT_MODIFIED = DiaryEvent('UDM_USERS_CONTACT_MODIFIED', {'en': 'Contact {cn} modified', 'de': 'Kontakt {cn} bearbeitet'}, args=['cn'], icon='users')
UDM_USERS_CONTACT_MOVED = DiaryEvent('UDM_USERS_CONTACT_MOVED', {'en': 'Contact {cn} moved to {position}', 'de': 'Kontakt {cn} verschoben nach {position}'}, args=['cn'], icon='users')
UDM_USERS_CONTACT_REMOVED = DiaryEvent('UDM_USERS_CONTACT_REMOVED', {'en': 'Contact {cn} removed', 'de': 'Kontakt {cn} gelöscht'}, args=['cn'], icon='users')

UDM_USERS_LDAP_CREATED = DiaryEvent('UDM_USERS_LDAP_CREATED', {'en': 'Simple authentication account {username} created', 'de': 'Einfaches Authentisierungskonto {username} angelegt'}, args=['username'], icon='users')
UDM_USERS_LDAP_MODIFIED = DiaryEvent('UDM_USERS_LDAP_MODIFIED', {'en': 'Simple authentication account {username} modified', 'de': 'Einfaches Authentisierungskonto {username} bearbeitet'}, args=['username'], icon='users')
UDM_USERS_LDAP_MOVED = DiaryEvent('UDM_USERS_LDAP_MOVED', {'en': 'Simple authentication account {username} moved to {position}', 'de': 'Einfaches Authentisierungskonto {username} verschoben nach {position}'}, args=['username'], icon='users')
UDM_USERS_LDAP_REMOVED = DiaryEvent('UDM_USERS_LDAP_REMOVED', {'en': 'Simple authentication account {username} removed', 'de': 'Einfaches Authentisierungskonto {username} gelöscht'}, args=['username'], icon='users')

UDM_USERS_PASSWD_MODIFIED = DiaryEvent('UDM_USERS_PASSWD_MODIFIED', {'en': 'User: Password {username} modified', 'de': 'Benutzer: Passwort {username} bearbeitet'}, args=['username'], icon='users')

UDM_USERS_USER_CREATED = DiaryEvent('UDM_USERS_USER_CREATED', {'en': 'User {username} created', 'de': 'Benutzer {username} angelegt'}, args=['username'], icon='users')
UDM_USERS_USER_MODIFIED = DiaryEvent('UDM_USERS_USER_MODIFIED', {'en': 'User {username} modified', 'de': 'Benutzer {username} bearbeitet'}, args=['username'], icon='users')
UDM_USERS_USER_MOVED = DiaryEvent('UDM_USERS_USER_MOVED', {'en': 'User {username} moved to {position}', 'de': 'Benutzer {username} verschoben nach {position}'}, args=['username'], icon='users')
UDM_USERS_USER_REMOVED = DiaryEvent('UDM_USERS_USER_REMOVED', {'en': 'User {username} removed', 'de': 'Benutzer {username} gelöscht'}, args=['username'], icon='users')

UDM_UVMM_CLOUDCONNECTION_CREATED = DiaryEvent('UDM_UVMM_CLOUDCONNECTION_CREATED', {'en': 'UVMM: Cloud Connection {name} created', 'de': 'UVMM: Cloud Connection {name} angelegt'}, args=['name'], icon='domain')
UDM_UVMM_CLOUDCONNECTION_MODIFIED = DiaryEvent('UDM_UVMM_CLOUDCONNECTION_MODIFIED', {'en': 'UVMM: Cloud Connection {name} modified', 'de': 'UVMM: Cloud Connection {name} bearbeitet'}, args=['name'], icon='domain')
UDM_UVMM_CLOUDCONNECTION_REMOVED = DiaryEvent('UDM_UVMM_CLOUDCONNECTION_REMOVED', {'en': 'UVMM: Cloud Connection {name} removed', 'de': 'UVMM: Cloud Connection {name} gelöscht'}, args=['name'], icon='domain')

UDM_UVMM_CLOUDTYPE_CREATED = DiaryEvent('UDM_UVMM_CLOUDTYPE_CREATED', {'en': 'UVMM: Cloud Type {name} created', 'de': 'UVMM: Cloud Type {name} angelegt'}, args=['name'], icon='domain')
UDM_UVMM_CLOUDTYPE_MODIFIED = DiaryEvent('UDM_UVMM_CLOUDTYPE_MODIFIED', {'en': 'UVMM: Cloud Type {name} modified', 'de': 'UVMM: Cloud Type {name} bearbeitet'}, args=['name'], icon='domain')
UDM_UVMM_CLOUDTYPE_REMOVED = DiaryEvent('UDM_UVMM_CLOUDTYPE_REMOVED', {'en': 'UVMM: Cloud Type {name} removed', 'de': 'UVMM: Cloud Type {name} gelöscht'}, args=['name'], icon='domain')

UDM_UVMM_INFO_CREATED = DiaryEvent('UDM_UVMM_INFO_CREATED', {'en': 'UVMM: Machine information {uuid} created', 'de': 'UVMM: Machine information {uuid} angelegt'}, args=['uuid'], icon='domain')
UDM_UVMM_INFO_MODIFIED = DiaryEvent('UDM_UVMM_INFO_MODIFIED', {'en': 'UVMM: Machine information {uuid} modified', 'de': 'UVMM: Machine information {uuid} bearbeitet'}, args=['uuid'], icon='domain')
UDM_UVMM_INFO_REMOVED = DiaryEvent('UDM_UVMM_INFO_REMOVED', {'en': 'UVMM: Machine information {uuid} removed', 'de': 'UVMM: Machine information {uuid} gelöscht'}, args=['uuid'], icon='domain')

UDM_UVMM_PROFILE_CREATED = DiaryEvent('UDM_UVMM_PROFILE_CREATED', {'en': 'UVMM: Profile {name} created', 'de': 'UVMM: Profile {name} angelegt'}, args=['name'], icon='domain')
UDM_UVMM_PROFILE_MODIFIED = DiaryEvent('UDM_UVMM_PROFILE_MODIFIED', {'en': 'UVMM: Profile {name} modified', 'de': 'UVMM: Profile {name} bearbeitet'}, args=['name'], icon='domain')
UDM_UVMM_PROFILE_REMOVED = DiaryEvent('UDM_UVMM_PROFILE_REMOVED', {'en': 'UVMM: Profile {name} removed', 'de': 'UVMM: Profile {name} gelöscht'}, args=['name'], icon='domain')

