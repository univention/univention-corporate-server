#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019 Univention GmbH
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
APP_INSTALL_START = DiaryEvent(u'APP_INSTALL_START', {u'en': u'Installation of {name} {version} started', u'de': u'Installation von {name} {version} wurde gestartet'}, args=[u'name', u'version'], icon=u'software')
APP_INSTALL_SUCCESS = DiaryEvent(u'APP_INSTALL_SUCCESS', {u'en': u'Installation of {name} {version} was successful', u'de': u'Die Installation von {name} {version} war erfolgreich'}, args=[u'name', u'version'], icon=u'software')
APP_INSTALL_FAILURE = DiaryEvent(u'APP_INSTALL_FAILURE', {u'en': u'Installation of {name} {version} failed. Error {error_code}', u'de': u'Die Installation von {name} {version} schlug fehl. Fehler {error_code}'}, args=[u'name', u'version', u'error_code'], tags=[u'error'], icon=u'software')

APP_UPGRADE_START = DiaryEvent(u'APP_UPGRADE_START', {u'en': u'Upgrade of {name} {version} started', u'de': u'Aktualisierung von {name} {version} wurde gestartet'}, args=[u'name', u'version'], icon=u'software')
APP_UPGRADE_SUCCESS = DiaryEvent(u'APP_UPGRADE_SUCCESS', {u'en': u'Upgrade to {name} {version} was successful', u'de': u'Die Aktualisierung auf {name} {version} war erfolgreich'}, args=[u'name', u'version'], icon=u'software')
APP_UPGRADE_FAILURE = DiaryEvent(u'APP_UPGRADE_FAILURE', {u'en': u'Upgrade of {name} {version} failed. Error {error_code}', u'de': u'Die Aktualisierung von {name} {version} schlug fehl. Fehler {error_code}'}, args=[u'name', u'version', u'error_code'], tags=[u'error'], icon=u'software')

APP_REMOVE_START = DiaryEvent(u'APP_REMOVE_START', {u'en': u'Removal of {name} {version} started', u'de': u'Deinstallation von {name} {version} wurde gestartet'}, args=[u'name', u'version'], icon=u'software')
APP_REMOVE_SUCCESS = DiaryEvent(u'APP_REMOVE_SUCCESS', {u'en': u'Removal of {name} {version} was successful', u'de': u'Die Deinstallation von {name} {version} war erfolgreich'}, args=[u'name', u'version'], icon=u'software')
APP_REMOVE_FAILURE = DiaryEvent(u'APP_REMOVE_FAILURE', {u'en': u'Removal of {name} {version} failed. Error {error_code}', u'de': u'Die Deinstallation von {name} {version} schlug fehl. Fehler {error_code}'}, args=[u'name', u'version', u'error_code'], tags=[u'error'], icon=u'software')

SERVER_PASSWORD_CHANGED = DiaryEvent(u'SERVER_PASSWORD_CHANGED', {u'en': u'Machine account password of {hostname} changed successfully', u'de': u'Maschinenpasswort von {hostname} erfolgreich geändert'}, args=[u'hostname'], icon=u'devices')
SERVER_PASSWORD_CHANGED_FAILED = DiaryEvent(u'SERVER_PASSWORD_CHANGED_FAILED', {u'en': u'Machine account password change of {hostname} failed', u'de': u'Änderung des Maschinenpassworts von {hostname} fehlgeschlagen'}, args=[u'hostname'], tags=[u'error'], icon=u'devices')

UPDATE_STARTED = DiaryEvent(u'UPDATE_STARTED', {u'en': u'Started to update {hostname}', u'de': u'Aktualisierung von {hostname} begonnen'}, args=[u'hostname'], icon=u'software')
UPDATE_FINISHED_SUCCESS = DiaryEvent(u'UPDATE_FINISHED_SUCCESS', {u'en': u'Successfully updated {hostname} to {version}', u'de': u'Aktualisierung von {hostname} auf {version} erfolgreich abgeschlossen'}, args=[u'hostname', u'version'], icon=u'software')
UPDATE_FINISHED_FAILURE = DiaryEvent(u'UPDATE_FINISHED_FAILURE', {u'en': u'Failed to update {hostname}', u'de': u'Aktualisierung von {hostname} fehlgeschlagen'}, args=[u'hostname'], tags=[u'error'], icon=u'software')

JOIN_STARTED = DiaryEvent(u'JOIN_STARTED', {u'en': u'Started to join {hostname} into the domain', u'de': u'Domänenbeitritt von {hostname} begonnen'}, args=[u'hostname'], icon=u'domain')
JOIN_FINISHED_SUCCESS = DiaryEvent(u'JOIN_FINISHED_SUCCESS', {u'en': u'Successfully joined {hostname}', u'de': u'{hostname} erfolgreich der Domäne beigetreten'}, args=[u'hostname'], icon=u'domain')
JOIN_FINISHED_FAILURE = DiaryEvent(u'JOIN_FINISHED_FAILURE', {u'en': u'Failed to join {hostname}', u'de': u'Domänenbeitritt von {hostname} fehlgeschlagen'}, args=[u'hostname'], tags=[u'error'], icon=u'domain')
JOIN_SCRIPT_FAILED = DiaryEvent(u'JOIN_SCRIPT_FAILED', {u'en': u'Running Joinscript {joinscript} failed', u'de': u'Ausführung des Joinscripts {joinscript} fehlgeschlagen'}, args=[u'joinscript'], tags=[u'error'], icon=u'domain')

UDM_GENERIC_CREATED = DiaryEvent(u'UDM_GENERIC_CREATED', {u'en': u'{module} object {id} created', u'de': u'{module}-Objekt {id} angelegt'}, args=[u'module', u'id'], icon=u'domain')
UDM_GENERIC_MODIFIED = DiaryEvent(u'UDM_GENERIC_MODIFIED', {u'en': u'{module} object {id} modified', u'de': u'{module}-Objekt {id} bearbeitet'}, args=[u'module', u'id'], icon=u'domain')
UDM_GENERIC_MOVED = DiaryEvent(u'UDM_GENERIC_MOVED', {u'en': u'{module} object {id} moved to {position}', u'de': u'{module}-Objekt {id} verschoben nach {position}'}, args=[u'module', u'id', u'position'], icon=u'domain')
UDM_GENERIC_REMOVED = DiaryEvent(u'UDM_GENERIC_REMOVED', {u'en': u'{module} object {id} removed', u'de': u'{module}-Objekt {id} gelöscht'}, args=[u'module', u'id'], icon=u'domain')

UDM_APPCENTER_APP_CREATED = DiaryEvent(u'UDM_APPCENTER_APP_CREATED', {u'en': u'App Metadata {id} created', u'de': u'App-Metadaten {id} angelegt'}, args=[u'id'], icon=u'domain')
UDM_APPCENTER_APP_MODIFIED = DiaryEvent(u'UDM_APPCENTER_APP_MODIFIED', {u'en': u'App Metadata {id} modified', u'de': u'App-Metadaten {id} bearbeitet'}, args=[u'id'], icon=u'domain')
UDM_APPCENTER_APP_MOVED = DiaryEvent(u'UDM_APPCENTER_APP_MOVED', {u'en': u'App Metadata {id} moved to {position}', u'de': u'App-Metadaten {id} verschoben nach {position}'}, args=[u'id'], icon=u'domain')
UDM_APPCENTER_APP_REMOVED = DiaryEvent(u'UDM_APPCENTER_APP_REMOVED', {u'en': u'App Metadata {id} removed', u'de': u'App-Metadaten {id} gelöscht'}, args=[u'id'], icon=u'domain')

UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_CREATED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_CREATED', {u'en': u'DC Backup {name} created', u'de': u'DC Backup {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MODIFIED', {u'en': u'DC Backup {name} modified', u'de': u'DC Backup {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MOVED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_MOVED', {u'en': u'DC Backup {name} moved to {position}', u'de': u'DC Backup {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_REMOVED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_BACKUP_REMOVED', {u'en': u'DC Backup {name} removed', u'de': u'DC Backup {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_CREATED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_CREATED', {u'en': u'DC Master {name} created', u'de': u'DC Master {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MODIFIED', {u'en': u'DC Master {name} modified', u'de': u'DC Master {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MOVED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_MOVED', {u'en': u'DC Master {name} moved to {position}', u'de': u'DC Master {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_REMOVED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_MASTER_REMOVED', {u'en': u'DC Master {name} removed', u'de': u'DC Master {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_CREATED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_CREATED', {u'en': u'DC Slave {name} created', u'de': u'DC Slave {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MODIFIED', {u'en': u'DC Slave {name} modified', u'de': u'DC Slave {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MOVED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_MOVED', {u'en': u'DC Slave {name} moved to {position}', u'de': u'DC Slave {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_REMOVED = DiaryEvent(u'UDM_COMPUTERS_DOMAINCONTROLLER_SLAVE_REMOVED', {u'en': u'DC Slave {name} removed', u'de': u'DC Slave {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_IPMANAGEDCLIENT_CREATED = DiaryEvent(u'UDM_COMPUTERS_IPMANAGEDCLIENT_CREATED', {u'en': u'IP managed client {name} created', u'de': u'IP-Managed-Client {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_IPMANAGEDCLIENT_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_IPMANAGEDCLIENT_MODIFIED', {u'en': u'IP managed client {name} modified', u'de': u'IP-Managed-Client {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_IPMANAGEDCLIENT_MOVED = DiaryEvent(u'UDM_COMPUTERS_IPMANAGEDCLIENT_MOVED', {u'en': u'IP managed client {name} moved to {position}', u'de': u'IP-Managed-Client {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_IPMANAGEDCLIENT_REMOVED = DiaryEvent(u'UDM_COMPUTERS_IPMANAGEDCLIENT_REMOVED', {u'en': u'IP managed client {name} removed', u'de': u'IP-Managed-Client {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_LINUX_CREATED = DiaryEvent(u'UDM_COMPUTERS_LINUX_CREATED', {u'en': u'Linux Computer {name} created', u'de': u'Linux-Rechner {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_LINUX_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_LINUX_MODIFIED', {u'en': u'Linux Computer {name} modified', u'de': u'Linux-Rechner {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_LINUX_MOVED = DiaryEvent(u'UDM_COMPUTERS_LINUX_MOVED', {u'en': u'Linux Computer {name} moved to {position}', u'de': u'Linux-Rechner {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_LINUX_REMOVED = DiaryEvent(u'UDM_COMPUTERS_LINUX_REMOVED', {u'en': u'Linux Computer {name} removed', u'de': u'Linux-Rechner {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_MACOS_CREATED = DiaryEvent(u'UDM_COMPUTERS_MACOS_CREATED', {u'en': u'Mac OS X Client {name} created', u'de': u'Mac OS X Client {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_MACOS_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_MACOS_MODIFIED', {u'en': u'Mac OS X Client {name} modified', u'de': u'Mac OS X Client {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_MACOS_MOVED = DiaryEvent(u'UDM_COMPUTERS_MACOS_MOVED', {u'en': u'Mac OS X Client {name} moved to {position}', u'de': u'Mac OS X Client {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_MACOS_REMOVED = DiaryEvent(u'UDM_COMPUTERS_MACOS_REMOVED', {u'en': u'Mac OS X Client {name} removed', u'de': u'Mac OS X Client {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_MEMBERSERVER_CREATED = DiaryEvent(u'UDM_COMPUTERS_MEMBERSERVER_CREATED', {u'en': u'Member Server {name} created', u'de': u'Member-Server {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_MEMBERSERVER_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_MEMBERSERVER_MODIFIED', {u'en': u'Member Server {name} modified', u'de': u'Member-Server {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_MEMBERSERVER_MOVED = DiaryEvent(u'UDM_COMPUTERS_MEMBERSERVER_MOVED', {u'en': u'Member Server {name} moved to {position}', u'de': u'Member-Server {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_MEMBERSERVER_REMOVED = DiaryEvent(u'UDM_COMPUTERS_MEMBERSERVER_REMOVED', {u'en': u'Member Server {name} removed', u'de': u'Member-Server {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_TRUSTACCOUNT_CREATED = DiaryEvent(u'UDM_COMPUTERS_TRUSTACCOUNT_CREATED', {u'en': u'Domain trust account {name} created', u'de': u'Domain Trust Account {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_TRUSTACCOUNT_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_TRUSTACCOUNT_MODIFIED', {u'en': u'Domain trust account {name} modified', u'de': u'Domain Trust Account {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_TRUSTACCOUNT_MOVED = DiaryEvent(u'UDM_COMPUTERS_TRUSTACCOUNT_MOVED', {u'en': u'Domain trust account {name} moved to {position}', u'de': u'Domain Trust Account {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_TRUSTACCOUNT_REMOVED = DiaryEvent(u'UDM_COMPUTERS_TRUSTACCOUNT_REMOVED', {u'en': u'Domain trust account {name} removed', u'de': u'Domain Trust Account {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_UBUNTU_CREATED = DiaryEvent(u'UDM_COMPUTERS_UBUNTU_CREATED', {u'en': u'Ubuntu Computer {name} created', u'de': u'Ubuntu-Rechner {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_UBUNTU_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_UBUNTU_MODIFIED', {u'en': u'Ubuntu Computer {name} modified', u'de': u'Ubuntu-Rechner {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_UBUNTU_MOVED = DiaryEvent(u'UDM_COMPUTERS_UBUNTU_MOVED', {u'en': u'Ubuntu Computer {name} moved to {position}', u'de': u'Ubuntu-Rechner {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_UBUNTU_REMOVED = DiaryEvent(u'UDM_COMPUTERS_UBUNTU_REMOVED', {u'en': u'Ubuntu Computer {name} removed', u'de': u'Ubuntu-Rechner {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_WINDOWS_CREATED = DiaryEvent(u'UDM_COMPUTERS_WINDOWS_CREATED', {u'en': u'Windows Workstation/Server {name} created', u'de': u'Windows Workstation/Server {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_WINDOWS_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_WINDOWS_MODIFIED', {u'en': u'Windows Workstation/Server {name} modified', u'de': u'Windows Workstation/Server {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_WINDOWS_MOVED = DiaryEvent(u'UDM_COMPUTERS_WINDOWS_MOVED', {u'en': u'Windows Workstation/Server {name} moved to {position}', u'de': u'Windows Workstation/Server {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_WINDOWS_REMOVED = DiaryEvent(u'UDM_COMPUTERS_WINDOWS_REMOVED', {u'en': u'Windows Workstation/Server {name} removed', u'de': u'Windows Workstation/Server {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_CREATED = DiaryEvent(u'UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_CREATED', {u'en': u'Windows Domaincontroller {name} created', u'de': u'Windows Domänencontroller {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MODIFIED = DiaryEvent(u'UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MODIFIED', {u'en': u'Windows Domaincontroller {name} modified', u'de': u'Windows Domänencontroller {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MOVED = DiaryEvent(u'UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_MOVED', {u'en': u'Windows Domaincontroller {name} moved to {position}', u'de': u'Windows Domänencontroller {name} verschoben nach {position}'}, args=[u'name'], icon=u'devices')
UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_REMOVED = DiaryEvent(u'UDM_COMPUTERS_WINDOWS_DOMAINCONTROLLER_REMOVED', {u'en': u'Windows Domaincontroller {name} removed', u'de': u'Windows Domänencontroller {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_CONTAINER_CN_CREATED = DiaryEvent(u'UDM_CONTAINER_CN_CREATED', {u'en': u'Container {name} created', u'de': u'Container {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_CONTAINER_CN_MODIFIED = DiaryEvent(u'UDM_CONTAINER_CN_MODIFIED', {u'en': u'Container {name} modified', u'de': u'Container {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_CONTAINER_CN_MOVED = DiaryEvent(u'UDM_CONTAINER_CN_MOVED', {u'en': u'Container {name} moved to {position}', u'de': u'Container {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_CONTAINER_CN_REMOVED = DiaryEvent(u'UDM_CONTAINER_CN_REMOVED', {u'en': u'Container {name} removed', u'de': u'Container {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_CONTAINER_DC_MODIFIED = DiaryEvent(u'UDM_CONTAINER_DC_MODIFIED', {u'en': u'Domain Container {name} modified', u'de': u'Domänen-Container {name} bearbeitet'}, args=[u'name'], icon=u'domain')

UDM_CONTAINER_OU_CREATED = DiaryEvent(u'UDM_CONTAINER_OU_CREATED', {u'en': u'Organisational Unit {name} created', u'de': u'Organisationseinheit {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_CONTAINER_OU_MODIFIED = DiaryEvent(u'UDM_CONTAINER_OU_MODIFIED', {u'en': u'Organisational Unit {name} modified', u'de': u'Organisationseinheit {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_CONTAINER_OU_MOVED = DiaryEvent(u'UDM_CONTAINER_OU_MOVED', {u'en': u'Organisational Unit {name} moved to {position}', u'de': u'Organisationseinheit {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_CONTAINER_OU_REMOVED = DiaryEvent(u'UDM_CONTAINER_OU_REMOVED', {u'en': u'Organisational Unit {name} removed', u'de': u'Organisationseinheit {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_DHCP_HOST_CREATED = DiaryEvent(u'UDM_DHCP_HOST_CREATED', {u'en': u'DHCP host {host} created', u'de': u'DHCP-Rechner {host} angelegt'}, args=[u'host'], icon=u'domain')
UDM_DHCP_HOST_MODIFIED = DiaryEvent(u'UDM_DHCP_HOST_MODIFIED', {u'en': u'DHCP host {host} modified', u'de': u'DHCP-Rechner {host} bearbeitet'}, args=[u'host'], icon=u'domain')
UDM_DHCP_HOST_REMOVED = DiaryEvent(u'UDM_DHCP_HOST_REMOVED', {u'en': u'DHCP host {host} removed', u'de': u'DHCP-Rechner {host} gelöscht'}, args=[u'host'], icon=u'domain')

UDM_DHCP_POOL_CREATED = DiaryEvent(u'UDM_DHCP_POOL_CREATED', {u'en': u'DHCP pool {name} created', u'de': u'DHCP-Pool {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_DHCP_POOL_MODIFIED = DiaryEvent(u'UDM_DHCP_POOL_MODIFIED', {u'en': u'DHCP pool {name} modified', u'de': u'DHCP-Pool {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_DHCP_POOL_REMOVED = DiaryEvent(u'UDM_DHCP_POOL_REMOVED', {u'en': u'DHCP pool {name} removed', u'de': u'DHCP-Pool {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_DHCP_SERVER_CREATED = DiaryEvent(u'UDM_DHCP_SERVER_CREATED', {u'en': u'DHCP server {server} created', u'de': u'DHCP-Server {server} angelegt'}, args=[u'server'], icon=u'domain')
UDM_DHCP_SERVER_MODIFIED = DiaryEvent(u'UDM_DHCP_SERVER_MODIFIED', {u'en': u'DHCP server {server} modified', u'de': u'DHCP-Server {server} bearbeitet'}, args=[u'server'], icon=u'domain')
UDM_DHCP_SERVER_REMOVED = DiaryEvent(u'UDM_DHCP_SERVER_REMOVED', {u'en': u'DHCP server {server} removed', u'de': u'DHCP-Server {server} gelöscht'}, args=[u'server'], icon=u'domain')

UDM_DHCP_SERVICE_CREATED = DiaryEvent(u'UDM_DHCP_SERVICE_CREATED', {u'en': u'DHCP service {service} created', u'de': u'DHCP-Dienst {service} angelegt'}, args=[u'service'], icon=u'domain')
UDM_DHCP_SERVICE_MODIFIED = DiaryEvent(u'UDM_DHCP_SERVICE_MODIFIED', {u'en': u'DHCP service {service} modified', u'de': u'DHCP-Dienst {service} bearbeitet'}, args=[u'service'], icon=u'domain')
UDM_DHCP_SERVICE_REMOVED = DiaryEvent(u'UDM_DHCP_SERVICE_REMOVED', {u'en': u'DHCP service {service} removed', u'de': u'DHCP-Dienst {service} gelöscht'}, args=[u'service'], icon=u'domain')

UDM_DHCP_SHARED_CREATED = DiaryEvent(u'UDM_DHCP_SHARED_CREATED', {u'en': u'Shared network {name} created', u'de': u'Shared Network {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_DHCP_SHARED_MODIFIED = DiaryEvent(u'UDM_DHCP_SHARED_MODIFIED', {u'en': u'Shared network {name} modified', u'de': u'Shared Network {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_DHCP_SHARED_REMOVED = DiaryEvent(u'UDM_DHCP_SHARED_REMOVED', {u'en': u'Shared network {name} removed', u'de': u'Shared Network {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_DHCP_SHAREDSUBNET_CREATED = DiaryEvent(u'UDM_DHCP_SHAREDSUBNET_CREATED', {u'en': u'Shared DHCP subnet {subnet} created', u'de': u'Shared DHCP-Subnetz {subnet} angelegt'}, args=[u'subnet'], icon=u'domain')
UDM_DHCP_SHAREDSUBNET_MODIFIED = DiaryEvent(u'UDM_DHCP_SHAREDSUBNET_MODIFIED', {u'en': u'Shared DHCP subnet {subnet} modified', u'de': u'Shared DHCP-Subnetz {subnet} bearbeitet'}, args=[u'subnet'], icon=u'domain')
UDM_DHCP_SHAREDSUBNET_REMOVED = DiaryEvent(u'UDM_DHCP_SHAREDSUBNET_REMOVED', {u'en': u'Shared DHCP subnet {subnet} removed', u'de': u'Shared DHCP-Subnetz {subnet} gelöscht'}, args=[u'subnet'], icon=u'domain')

UDM_DHCP_SUBNET_CREATED = DiaryEvent(u'UDM_DHCP_SUBNET_CREATED', {u'en': u'DHCP subnet {subnet} created', u'de': u'DHCP-Subnetz {subnet} angelegt'}, args=[u'subnet'], icon=u'domain')
UDM_DHCP_SUBNET_MODIFIED = DiaryEvent(u'UDM_DHCP_SUBNET_MODIFIED', {u'en': u'DHCP subnet {subnet} modified', u'de': u'DHCP-Subnetz {subnet} bearbeitet'}, args=[u'subnet'], icon=u'domain')
UDM_DHCP_SUBNET_REMOVED = DiaryEvent(u'UDM_DHCP_SUBNET_REMOVED', {u'en': u'DHCP subnet {subnet} removed', u'de': u'DHCP-Subnetz {subnet} gelöscht'}, args=[u'subnet'], icon=u'domain')

UDM_DNS_ALIAS_CREATED = DiaryEvent(u'UDM_DNS_ALIAS_CREATED', {u'en': u'Alias record {name} created', u'de': u'Alias Record {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_DNS_ALIAS_MODIFIED = DiaryEvent(u'UDM_DNS_ALIAS_MODIFIED', {u'en': u'Alias record {name} modified', u'de': u'Alias Record {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_DNS_ALIAS_REMOVED = DiaryEvent(u'UDM_DNS_ALIAS_REMOVED', {u'en': u'Alias record {name} removed', u'de': u'Alias Record {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_DNS_FORWARD_ZONE_CREATED = DiaryEvent(u'UDM_DNS_FORWARD_ZONE_CREATED', {u'en': u'Forward lookup zone {zone} created', u'de': u'Forward Lookup Zone {zone} angelegt'}, args=[u'zone'], icon=u'domain')
UDM_DNS_FORWARD_ZONE_MODIFIED = DiaryEvent(u'UDM_DNS_FORWARD_ZONE_MODIFIED', {u'en': u'Forward lookup zone {zone} modified', u'de': u'Forward Lookup Zone {zone} bearbeitet'}, args=[u'zone'], icon=u'domain')
UDM_DNS_FORWARD_ZONE_REMOVED = DiaryEvent(u'UDM_DNS_FORWARD_ZONE_REMOVED', {u'en': u'Forward lookup zone {zone} removed', u'de': u'Forward Lookup Zone {zone} gelöscht'}, args=[u'zone'], icon=u'domain')

UDM_DNS_HOST_RECORD_CREATED = DiaryEvent(u'UDM_DNS_HOST_RECORD_CREATED', {u'en': u'Host record {name} created', u'de': u'Host Record {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_DNS_HOST_RECORD_MODIFIED = DiaryEvent(u'UDM_DNS_HOST_RECORD_MODIFIED', {u'en': u'Host record {name} modified', u'de': u'Host Record {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_DNS_HOST_RECORD_REMOVED = DiaryEvent(u'UDM_DNS_HOST_RECORD_REMOVED', {u'en': u'Host record {name} removed', u'de': u'Host Record {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_DNS_NS_RECORD_CREATED = DiaryEvent(u'UDM_DNS_NS_RECORD_CREATED', {u'en': u'Nameserver record {zone} created', u'de': u'Nameserver record {zone} angelegt'}, args=[u'zone'], icon=u'domain')
UDM_DNS_NS_RECORD_MODIFIED = DiaryEvent(u'UDM_DNS_NS_RECORD_MODIFIED', {u'en': u'Nameserver record {zone} modified', u'de': u'Nameserver record {zone} bearbeitet'}, args=[u'zone'], icon=u'domain')
UDM_DNS_NS_RECORD_REMOVED = DiaryEvent(u'UDM_DNS_NS_RECORD_REMOVED', {u'en': u'Nameserver record {zone} removed', u'de': u'Nameserver record {zone} gelöscht'}, args=[u'zone'], icon=u'domain')

UDM_DNS_PTR_RECORD_CREATED = DiaryEvent(u'UDM_DNS_PTR_RECORD_CREATED', {u'en': u'Pointer record {address} created', u'de': u'Pointer Record {address} angelegt'}, args=[u'address'], icon=u'domain')
UDM_DNS_PTR_RECORD_MODIFIED = DiaryEvent(u'UDM_DNS_PTR_RECORD_MODIFIED', {u'en': u'Pointer record {address} modified', u'de': u'Pointer Record {address} bearbeitet'}, args=[u'address'], icon=u'domain')
UDM_DNS_PTR_RECORD_REMOVED = DiaryEvent(u'UDM_DNS_PTR_RECORD_REMOVED', {u'en': u'Pointer record {address} removed', u'de': u'Pointer Record {address} gelöscht'}, args=[u'address'], icon=u'domain')

UDM_DNS_REVERSE_ZONE_CREATED = DiaryEvent(u'UDM_DNS_REVERSE_ZONE_CREATED', {u'en': u'Reverse lookup zone {subnet} created', u'de': u'Reverse Lookup Zone {subnet} angelegt'}, args=[u'subnet'], icon=u'domain')
UDM_DNS_REVERSE_ZONE_MODIFIED = DiaryEvent(u'UDM_DNS_REVERSE_ZONE_MODIFIED', {u'en': u'Reverse lookup zone {subnet} modified', u'de': u'Reverse Lookup Zone {subnet} bearbeitet'}, args=[u'subnet'], icon=u'domain')
UDM_DNS_REVERSE_ZONE_REMOVED = DiaryEvent(u'UDM_DNS_REVERSE_ZONE_REMOVED', {u'en': u'Reverse lookup zone {subnet} removed', u'de': u'Reverse Lookup Zone {subnet} gelöscht'}, args=[u'subnet'], icon=u'domain')

UDM_DNS_SRV_RECORD_CREATED = DiaryEvent(u'UDM_DNS_SRV_RECORD_CREATED', {u'en': u'Service record {name} created', u'de': u'Service Record {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_DNS_SRV_RECORD_MODIFIED = DiaryEvent(u'UDM_DNS_SRV_RECORD_MODIFIED', {u'en': u'Service record {name} modified', u'de': u'Service Record {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_DNS_SRV_RECORD_REMOVED = DiaryEvent(u'UDM_DNS_SRV_RECORD_REMOVED', {u'en': u'Service record {name} removed', u'de': u'Service Record {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_DNS_TXT_RECORD_CREATED = DiaryEvent(u'UDM_DNS_TXT_RECORD_CREATED', {u'en': u'TXT record {name} created', u'de': u'TXT Record {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_DNS_TXT_RECORD_MODIFIED = DiaryEvent(u'UDM_DNS_TXT_RECORD_MODIFIED', {u'en': u'TXT record {name} modified', u'de': u'TXT Record {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_DNS_TXT_RECORD_REMOVED = DiaryEvent(u'UDM_DNS_TXT_RECORD_REMOVED', {u'en': u'TXT record {name} removed', u'de': u'TXT Record {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_GROUPS_GROUP_CREATED = DiaryEvent(u'UDM_GROUPS_GROUP_CREATED', {u'en': u'Group {name} created', u'de': u'Gruppe {name} angelegt'}, args=[u'name'], icon=u'users')
UDM_GROUPS_GROUP_MODIFIED = DiaryEvent(u'UDM_GROUPS_GROUP_MODIFIED', {u'en': u'Group {name} modified', u'de': u'Gruppe {name} bearbeitet'}, args=[u'name'], icon=u'users')
UDM_GROUPS_GROUP_MOVED = DiaryEvent(u'UDM_GROUPS_GROUP_MOVED', {u'en': u'Group {name} moved to {position}', u'de': u'Gruppe {name} verschoben nach {position}'}, args=[u'name'], icon=u'users')
UDM_GROUPS_GROUP_REMOVED = DiaryEvent(u'UDM_GROUPS_GROUP_REMOVED', {u'en': u'Group {name} removed', u'de': u'Gruppe {name} gelöscht'}, args=[u'name'], icon=u'users')

UDM_KERBEROS_KDCENTRY_CREATED = DiaryEvent(u'UDM_KERBEROS_KDCENTRY_CREATED', {u'en': u'KDC Entry {name} created', u'de': u'KDC-Eintrag {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_KERBEROS_KDCENTRY_MODIFIED = DiaryEvent(u'UDM_KERBEROS_KDCENTRY_MODIFIED', {u'en': u'KDC Entry {name} modified', u'de': u'KDC-Eintrag {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_KERBEROS_KDCENTRY_MOVED = DiaryEvent(u'UDM_KERBEROS_KDCENTRY_MOVED', {u'en': u'KDC Entry {name} moved to {position}', u'de': u'KDC-Eintrag {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_KERBEROS_KDCENTRY_REMOVED = DiaryEvent(u'UDM_KERBEROS_KDCENTRY_REMOVED', {u'en': u'KDC Entry {name} removed', u'de': u'KDC-Eintrag {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_MAIL_DOMAIN_CREATED = DiaryEvent(u'UDM_MAIL_DOMAIN_CREATED', {u'en': u'Mail domain {name} created', u'de': u'Mail-Domäne {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_MAIL_DOMAIN_MODIFIED = DiaryEvent(u'UDM_MAIL_DOMAIN_MODIFIED', {u'en': u'Mail domain {name} modified', u'de': u'Mail-Domäne {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_MAIL_DOMAIN_MOVED = DiaryEvent(u'UDM_MAIL_DOMAIN_MOVED', {u'en': u'Mail domain {name} moved to {position}', u'de': u'Mail-Domäne {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_MAIL_DOMAIN_REMOVED = DiaryEvent(u'UDM_MAIL_DOMAIN_REMOVED', {u'en': u'Mail domain {name} removed', u'de': u'Mail-Domäne {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_MAIL_FOLDER_CREATED = DiaryEvent(u'UDM_MAIL_FOLDER_CREATED', {u'en': u'IMAP mail folder {nameWithMailDomain} created', u'de': u'IMAP-Mail-Ordner {nameWithMailDomain} angelegt'}, args=[u'nameWithMailDomain'], icon=u'domain')
UDM_MAIL_FOLDER_MODIFIED = DiaryEvent(u'UDM_MAIL_FOLDER_MODIFIED', {u'en': u'IMAP mail folder {nameWithMailDomain} modified', u'de': u'IMAP-Mail-Ordner {nameWithMailDomain} bearbeitet'}, args=[u'nameWithMailDomain'], icon=u'domain')
UDM_MAIL_FOLDER_REMOVED = DiaryEvent(u'UDM_MAIL_FOLDER_REMOVED', {u'en': u'IMAP mail folder {nameWithMailDomain} removed', u'de': u'IMAP-Mail-Ordner {nameWithMailDomain} gelöscht'}, args=[u'nameWithMailDomain'], icon=u'domain')

UDM_MAIL_LISTS_CREATED = DiaryEvent(u'UDM_MAIL_LISTS_CREATED', {u'en': u'Mailing list {name} created', u'de': u'Mailingliste {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_MAIL_LISTS_MODIFIED = DiaryEvent(u'UDM_MAIL_LISTS_MODIFIED', {u'en': u'Mailing list {name} modified', u'de': u'Mailingliste {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_MAIL_LISTS_MOVED = DiaryEvent(u'UDM_MAIL_LISTS_MOVED', {u'en': u'Mailing list {name} moved to {position}', u'de': u'Mailingliste {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_MAIL_LISTS_REMOVED = DiaryEvent(u'UDM_MAIL_LISTS_REMOVED', {u'en': u'Mailing list {name} removed', u'de': u'Mailingliste {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_NAGIOS_SERVICE_CREATED = DiaryEvent(u'UDM_NAGIOS_SERVICE_CREATED', {u'en': u'Nagios service {name} created', u'de': u'Nagios-Dienst {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_NAGIOS_SERVICE_MODIFIED = DiaryEvent(u'UDM_NAGIOS_SERVICE_MODIFIED', {u'en': u'Nagios service {name} modified', u'de': u'Nagios-Dienst {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_NAGIOS_SERVICE_REMOVED = DiaryEvent(u'UDM_NAGIOS_SERVICE_REMOVED', {u'en': u'Nagios service {name} removed', u'de': u'Nagios-Dienst {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_NAGIOS_TIMEPERIOD_CREATED = DiaryEvent(u'UDM_NAGIOS_TIMEPERIOD_CREATED', {u'en': u'Nagios time period {name} created', u'de': u'Nagios-Zeitraum {name} angelegt'}, args=[u'name'], icon=u'devices')
UDM_NAGIOS_TIMEPERIOD_MODIFIED = DiaryEvent(u'UDM_NAGIOS_TIMEPERIOD_MODIFIED', {u'en': u'Nagios time period {name} modified', u'de': u'Nagios-Zeitraum {name} bearbeitet'}, args=[u'name'], icon=u'devices')
UDM_NAGIOS_TIMEPERIOD_REMOVED = DiaryEvent(u'UDM_NAGIOS_TIMEPERIOD_REMOVED', {u'en': u'Nagios time period {name} removed', u'de': u'Nagios-Zeitraum {name} gelöscht'}, args=[u'name'], icon=u'devices')

UDM_NETWORKS_NETWORK_CREATED = DiaryEvent(u'UDM_NETWORKS_NETWORK_CREATED', {u'en': u'Network {name} ({netmask} {network}) created', u'de': u'Netzwerk {name} ({netmask} {network}) angelegt'}, args=[u'name', u'netmask', u'network'], icon=u'domain')
UDM_NETWORKS_NETWORK_MODIFIED = DiaryEvent(u'UDM_NETWORKS_NETWORK_MODIFIED', {u'en': u'Network {name} ({netmask} {network}) modified', u'de': u'Netzwerk {name} ({netmask} {network}) bearbeitet'}, args=[u'name', u'netmask', u'network'], icon=u'domain')
UDM_NETWORKS_NETWORK_REMOVED = DiaryEvent(u'UDM_NETWORKS_NETWORK_REMOVED', {u'en': u'Network {name} ({netmask} {network}) removed', u'de': u'Netzwerk {name} ({netmask} {network}) gelöscht'}, args=[u'name', u'netmask', u'network'], icon=u'domain')

UDM_POLICIES_ADMIN_CONTAINER_CREATED = DiaryEvent(u'UDM_POLICIES_ADMIN_CONTAINER_CREATED', {u'en': u'Univention Directory Manager container settings policy {name} created', u'de': u'Univention Directory Manager Container Konfiguration-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_ADMIN_CONTAINER_MODIFIED = DiaryEvent(u'UDM_POLICIES_ADMIN_CONTAINER_MODIFIED', {u'en': u'Univention Directory Manager container settings policy {name} modified', u'de': u'Univention Directory Manager Container Konfiguration-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_ADMIN_CONTAINER_REMOVED = DiaryEvent(u'UDM_POLICIES_ADMIN_CONTAINER_REMOVED', {u'en': u'Univention Directory Manager container settings policy {name} removed', u'de': u'Univention Directory Manager Container Konfiguration-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_AUTOSTART_CREATED = DiaryEvent(u'UDM_POLICIES_AUTOSTART_CREATED', {u'en': u'Autostart policy {name} created', u'de': u'Autostart-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_AUTOSTART_MODIFIED = DiaryEvent(u'UDM_POLICIES_AUTOSTART_MODIFIED', {u'en': u'Autostart policy {name} modified', u'de': u'Autostart-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_AUTOSTART_REMOVED = DiaryEvent(u'UDM_POLICIES_AUTOSTART_REMOVED', {u'en': u'Autostart policy {name} removed', u'de': u'Autostart-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_DESKTOP_CREATED = DiaryEvent(u'UDM_POLICIES_DESKTOP_CREATED', {u'en': u'Desktop policy {name} created', u'de': u'Desktop-Profil-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DESKTOP_MODIFIED = DiaryEvent(u'UDM_POLICIES_DESKTOP_MODIFIED', {u'en': u'Desktop policy {name} modified', u'de': u'Desktop-Profil-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DESKTOP_REMOVED = DiaryEvent(u'UDM_POLICIES_DESKTOP_REMOVED', {u'en': u'Desktop policy {name} removed', u'de': u'Desktop-Profil-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_DHCP_BOOT_CREATED = DiaryEvent(u'UDM_POLICIES_DHCP_BOOT_CREATED', {u'en': u'DHCP Boot policy {name} created', u'de': u'DHCP Boot-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_BOOT_MODIFIED = DiaryEvent(u'UDM_POLICIES_DHCP_BOOT_MODIFIED', {u'en': u'DHCP Boot policy {name} modified', u'de': u'DHCP Boot-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_BOOT_REMOVED = DiaryEvent(u'UDM_POLICIES_DHCP_BOOT_REMOVED', {u'en': u'DHCP Boot policy {name} removed', u'de': u'DHCP Boot-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_DHCP_DNS_CREATED = DiaryEvent(u'UDM_POLICIES_DHCP_DNS_CREATED', {u'en': u'DHCP DNS policy {name} created', u'de': u'DHCP DNS-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_DNS_MODIFIED = DiaryEvent(u'UDM_POLICIES_DHCP_DNS_MODIFIED', {u'en': u'DHCP DNS policy {name} modified', u'de': u'DHCP DNS-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_DNS_REMOVED = DiaryEvent(u'UDM_POLICIES_DHCP_DNS_REMOVED', {u'en': u'DHCP DNS policy {name} removed', u'de': u'DHCP DNS-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_DHCP_DNSUPDATE_CREATED = DiaryEvent(u'UDM_POLICIES_DHCP_DNSUPDATE_CREATED', {u'en': u'DHCP Dynamic DNS policy {name} created', u'de': u'DHCP DNS Aktualisierungs-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_DNSUPDATE_MODIFIED = DiaryEvent(u'UDM_POLICIES_DHCP_DNSUPDATE_MODIFIED', {u'en': u'DHCP Dynamic DNS policy {name} modified', u'de': u'DHCP DNS Aktualisierungs-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_DNSUPDATE_REMOVED = DiaryEvent(u'UDM_POLICIES_DHCP_DNSUPDATE_REMOVED', {u'en': u'DHCP Dynamic DNS policy {name} removed', u'de': u'DHCP DNS Aktualisierungs-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_DHCP_LEASETIME_CREATED = DiaryEvent(u'UDM_POLICIES_DHCP_LEASETIME_CREATED', {u'en': u'DHCP lease time policy {name} created', u'de': u'DHCP Lease-Zeit-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_LEASETIME_MODIFIED = DiaryEvent(u'UDM_POLICIES_DHCP_LEASETIME_MODIFIED', {u'en': u'DHCP lease time policy {name} modified', u'de': u'DHCP Lease-Zeit-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_LEASETIME_REMOVED = DiaryEvent(u'UDM_POLICIES_DHCP_LEASETIME_REMOVED', {u'en': u'DHCP lease time policy {name} removed', u'de': u'DHCP Lease-Zeit-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_DHCP_NETBIOS_CREATED = DiaryEvent(u'UDM_POLICIES_DHCP_NETBIOS_CREATED', {u'en': u'DHCP NetBIOS policy {name} created', u'de': u'DHCP NetBIOS-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_NETBIOS_MODIFIED = DiaryEvent(u'UDM_POLICIES_DHCP_NETBIOS_MODIFIED', {u'en': u'DHCP NetBIOS policy {name} modified', u'de': u'DHCP NetBIOS-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_NETBIOS_REMOVED = DiaryEvent(u'UDM_POLICIES_DHCP_NETBIOS_REMOVED', {u'en': u'DHCP NetBIOS policy {name} removed', u'de': u'DHCP NetBIOS-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_DHCP_ROUTING_CREATED = DiaryEvent(u'UDM_POLICIES_DHCP_ROUTING_CREATED', {u'en': u'DHCP routing policy {name} created', u'de': u'DHCP Routing-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_ROUTING_MODIFIED = DiaryEvent(u'UDM_POLICIES_DHCP_ROUTING_MODIFIED', {u'en': u'DHCP routing policy {name} modified', u'de': u'DHCP Routing-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_ROUTING_REMOVED = DiaryEvent(u'UDM_POLICIES_DHCP_ROUTING_REMOVED', {u'en': u'DHCP routing policy {name} removed', u'de': u'DHCP Routing-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_DHCP_SCOPE_CREATED = DiaryEvent(u'UDM_POLICIES_DHCP_SCOPE_CREATED', {u'en': u'DHCP Allow/Deny policy {name} created', u'de': u'DHCP Erlauben/Verbieten-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_SCOPE_MODIFIED = DiaryEvent(u'UDM_POLICIES_DHCP_SCOPE_MODIFIED', {u'en': u'DHCP Allow/Deny policy {name} modified', u'de': u'DHCP Erlauben/Verbieten-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_SCOPE_REMOVED = DiaryEvent(u'UDM_POLICIES_DHCP_SCOPE_REMOVED', {u'en': u'DHCP Allow/Deny policy {name} removed', u'de': u'DHCP Erlauben/Verbieten-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_DHCP_STATEMENTS_CREATED = DiaryEvent(u'UDM_POLICIES_DHCP_STATEMENTS_CREATED', {u'en': u'DHCP statements policy {name} created', u'de': u'DHCP Verschiedenes-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_STATEMENTS_MODIFIED = DiaryEvent(u'UDM_POLICIES_DHCP_STATEMENTS_MODIFIED', {u'en': u'DHCP statements policy {name} modified', u'de': u'DHCP Verschiedenes-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_DHCP_STATEMENTS_REMOVED = DiaryEvent(u'UDM_POLICIES_DHCP_STATEMENTS_REMOVED', {u'en': u'DHCP statements policy {name} removed', u'de': u'DHCP Verschiedenes-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_LDAPSERVER_CREATED = DiaryEvent(u'UDM_POLICIES_LDAPSERVER_CREATED', {u'en': u'LDAP server policy {name} created', u'de': u'LDAP-Server-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_LDAPSERVER_MODIFIED = DiaryEvent(u'UDM_POLICIES_LDAPSERVER_MODIFIED', {u'en': u'LDAP server policy {name} modified', u'de': u'LDAP-Server-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_LDAPSERVER_REMOVED = DiaryEvent(u'UDM_POLICIES_LDAPSERVER_REMOVED', {u'en': u'LDAP server policy {name} removed', u'de': u'LDAP-Server-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_MAINTENANCE_CREATED = DiaryEvent(u'UDM_POLICIES_MAINTENANCE_CREATED', {u'en': u'Maintenance policy {name} created', u'de': u'Paketpflege-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_MAINTENANCE_MODIFIED = DiaryEvent(u'UDM_POLICIES_MAINTENANCE_MODIFIED', {u'en': u'Maintenance policy {name} modified', u'de': u'Paketpflege-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_MAINTENANCE_REMOVED = DiaryEvent(u'UDM_POLICIES_MAINTENANCE_REMOVED', {u'en': u'Maintenance policy {name} removed', u'de': u'Paketpflege-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_MASTERPACKAGES_CREATED = DiaryEvent(u'UDM_POLICIES_MASTERPACKAGES_CREATED', {u'en': u'Master packages policy {name} created', u'de': u'Master Pakete-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_MASTERPACKAGES_MODIFIED = DiaryEvent(u'UDM_POLICIES_MASTERPACKAGES_MODIFIED', {u'en': u'Master packages policy {name} modified', u'de': u'Master Pakete-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_MASTERPACKAGES_REMOVED = DiaryEvent(u'UDM_POLICIES_MASTERPACKAGES_REMOVED', {u'en': u'Master packages policy {name} removed', u'de': u'Master Pakete-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_MEMBERPACKAGES_CREATED = DiaryEvent(u'UDM_POLICIES_MEMBERPACKAGES_CREATED', {u'en': u'Member Server packages policy {name} created', u'de': u'Memberserver Pakete-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_MEMBERPACKAGES_MODIFIED = DiaryEvent(u'UDM_POLICIES_MEMBERPACKAGES_MODIFIED', {u'en': u'Member Server packages policy {name} modified', u'de': u'Memberserver Pakete-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_MEMBERPACKAGES_REMOVED = DiaryEvent(u'UDM_POLICIES_MEMBERPACKAGES_REMOVED', {u'en': u'Member Server packages policy {name} removed', u'de': u'Memberserver Pakete-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_NFSMOUNTS_CREATED = DiaryEvent(u'UDM_POLICIES_NFSMOUNTS_CREATED', {u'en': u'NFS mounts policy {name} created', u'de': u'NFS-Freigaben-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_NFSMOUNTS_MODIFIED = DiaryEvent(u'UDM_POLICIES_NFSMOUNTS_MODIFIED', {u'en': u'NFS mounts policy {name} modified', u'de': u'NFS-Freigaben-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_NFSMOUNTS_REMOVED = DiaryEvent(u'UDM_POLICIES_NFSMOUNTS_REMOVED', {u'en': u'NFS mounts policy {name} removed', u'de': u'NFS-Freigaben-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_PRINT_QUOTA_CREATED = DiaryEvent(u'UDM_POLICIES_PRINT_QUOTA_CREATED', {u'en': u'Print quota policy {name} created', u'de': u'Druck-Quota-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_PRINT_QUOTA_MODIFIED = DiaryEvent(u'UDM_POLICIES_PRINT_QUOTA_MODIFIED', {u'en': u'Print quota policy {name} modified', u'de': u'Druck-Quota-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_PRINT_QUOTA_REMOVED = DiaryEvent(u'UDM_POLICIES_PRINT_QUOTA_REMOVED', {u'en': u'Print quota policy {name} removed', u'de': u'Druck-Quota-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_PRINTSERVER_CREATED = DiaryEvent(u'UDM_POLICIES_PRINTSERVER_CREATED', {u'en': u'Print server policy {name} created', u'de': u'Druckserver-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_PRINTSERVER_MODIFIED = DiaryEvent(u'UDM_POLICIES_PRINTSERVER_MODIFIED', {u'en': u'Print server policy {name} modified', u'de': u'Druckserver-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_PRINTSERVER_REMOVED = DiaryEvent(u'UDM_POLICIES_PRINTSERVER_REMOVED', {u'en': u'Print server policy {name} removed', u'de': u'Druckserver-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_PWHISTORY_CREATED = DiaryEvent(u'UDM_POLICIES_PWHISTORY_CREATED', {u'en': u'Passwords policy {name} created', u'de': u'Passwort-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_PWHISTORY_MODIFIED = DiaryEvent(u'UDM_POLICIES_PWHISTORY_MODIFIED', {u'en': u'Passwords policy {name} modified', u'de': u'Passwort-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_PWHISTORY_REMOVED = DiaryEvent(u'UDM_POLICIES_PWHISTORY_REMOVED', {u'en': u'Passwords policy {name} removed', u'de': u'Passwort-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_REGISTRY_CREATED = DiaryEvent(u'UDM_POLICIES_REGISTRY_CREATED', {u'en': u'Univention Configuration Registry policy {name} created', u'de': u'Univention Configuration Registry-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_REGISTRY_MODIFIED = DiaryEvent(u'UDM_POLICIES_REGISTRY_MODIFIED', {u'en': u'Univention Configuration Registry policy {name} modified', u'de': u'Univention Configuration Registry-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_REGISTRY_REMOVED = DiaryEvent(u'UDM_POLICIES_REGISTRY_REMOVED', {u'en': u'Univention Configuration Registry policy {name} removed', u'de': u'Univention Configuration Registry-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_RELEASE_CREATED = DiaryEvent(u'UDM_POLICIES_RELEASE_CREATED', {u'en': u'Automatic updates policy {name} created', u'de': u'Automatische Updates-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_RELEASE_MODIFIED = DiaryEvent(u'UDM_POLICIES_RELEASE_MODIFIED', {u'en': u'Automatic updates policy {name} modified', u'de': u'Automatische Updates-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_RELEASE_REMOVED = DiaryEvent(u'UDM_POLICIES_RELEASE_REMOVED', {u'en': u'Automatic updates policy {name} removed', u'de': u'Automatische Updates-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_REPOSITORYSERVER_CREATED = DiaryEvent(u'UDM_POLICIES_REPOSITORYSERVER_CREATED', {u'en': u'Repository server policy {name} created', u'de': u'Repository-Server-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_REPOSITORYSERVER_MODIFIED = DiaryEvent(u'UDM_POLICIES_REPOSITORYSERVER_MODIFIED', {u'en': u'Repository server policy {name} modified', u'de': u'Repository-Server-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_REPOSITORYSERVER_REMOVED = DiaryEvent(u'UDM_POLICIES_REPOSITORYSERVER_REMOVED', {u'en': u'Repository server policy {name} removed', u'de': u'Repository-Server-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_REPOSITORYSYNC_CREATED = DiaryEvent(u'UDM_POLICIES_REPOSITORYSYNC_CREATED', {u'en': u'Repository synchronisation policy {name} created', u'de': u'Repository-Synchronisation-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_REPOSITORYSYNC_MODIFIED = DiaryEvent(u'UDM_POLICIES_REPOSITORYSYNC_MODIFIED', {u'en': u'Repository synchronisation policy {name} modified', u'de': u'Repository-Synchronisation-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_REPOSITORYSYNC_REMOVED = DiaryEvent(u'UDM_POLICIES_REPOSITORYSYNC_REMOVED', {u'en': u'Repository synchronisation policy {name} removed', u'de': u'Repository-Synchronisation-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_SHARE_USERQUOTA_CREATED = DiaryEvent(u'UDM_POLICIES_SHARE_USERQUOTA_CREATED', {u'en': u'User quota policy {name} created', u'de': u'Benutzer-Quota-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_SHARE_USERQUOTA_MODIFIED = DiaryEvent(u'UDM_POLICIES_SHARE_USERQUOTA_MODIFIED', {u'en': u'User quota policy {name} modified', u'de': u'Benutzer-Quota-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_SHARE_USERQUOTA_REMOVED = DiaryEvent(u'UDM_POLICIES_SHARE_USERQUOTA_REMOVED', {u'en': u'User quota policy {name} removed', u'de': u'Benutzer-Quota-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_SLAVEPACKAGES_CREATED = DiaryEvent(u'UDM_POLICIES_SLAVEPACKAGES_CREATED', {u'en': u'Slave packages policy {name} created', u'de': u'Slave Pakete-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_SLAVEPACKAGES_MODIFIED = DiaryEvent(u'UDM_POLICIES_SLAVEPACKAGES_MODIFIED', {u'en': u'Slave packages policy {name} modified', u'de': u'Slave Pakete-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_SLAVEPACKAGES_REMOVED = DiaryEvent(u'UDM_POLICIES_SLAVEPACKAGES_REMOVED', {u'en': u'Slave packages policy {name} removed', u'de': u'Slave Pakete-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_POLICIES_UMC_CREATED = DiaryEvent(u'UDM_POLICIES_UMC_CREATED', {u'en': u'UMC policy {name} created', u'de': u'UMC-Richtlinie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_UMC_MODIFIED = DiaryEvent(u'UDM_POLICIES_UMC_MODIFIED', {u'en': u'UMC policy {name} modified', u'de': u'UMC-Richtlinie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_POLICIES_UMC_REMOVED = DiaryEvent(u'UDM_POLICIES_UMC_REMOVED', {u'en': u'UMC policy {name} removed', u'de': u'UMC-Richtlinie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SAML_IDPCONFIG_CREATED = DiaryEvent(u'UDM_SAML_IDPCONFIG_CREATED', {u'en': u'SAML IdP configuration {id} created', u'de': u'SAML IdP-Konfiguration {id} angelegt'}, args=[u'id'], icon=u'domain')
UDM_SAML_IDPCONFIG_MODIFIED = DiaryEvent(u'UDM_SAML_IDPCONFIG_MODIFIED', {u'en': u'SAML IdP configuration {id} modified', u'de': u'SAML IdP-Konfiguration {id} bearbeitet'}, args=[u'id'], icon=u'domain')
UDM_SAML_IDPCONFIG_REMOVED = DiaryEvent(u'UDM_SAML_IDPCONFIG_REMOVED', {u'en': u'SAML IdP configuration {id} removed', u'de': u'SAML IdP-Konfiguration {id} gelöscht'}, args=[u'id'], icon=u'domain')

UDM_SAML_SERVICEPROVIDER_CREATED = DiaryEvent(u'UDM_SAML_SERVICEPROVIDER_CREATED', {u'en': u'SAML service provider {Identifier} created', u'de': u'SAML service provider {Identifier} angelegt'}, args=[u'Identifier'], icon=u'domain')
UDM_SAML_SERVICEPROVIDER_MODIFIED = DiaryEvent(u'UDM_SAML_SERVICEPROVIDER_MODIFIED', {u'en': u'SAML service provider {Identifier} modified', u'de': u'SAML service provider {Identifier} bearbeitet'}, args=[u'Identifier'], icon=u'domain')
UDM_SAML_SERVICEPROVIDER_REMOVED = DiaryEvent(u'UDM_SAML_SERVICEPROVIDER_REMOVED', {u'en': u'SAML service provider {Identifier} removed', u'de': u'SAML service provider {Identifier} gelöscht'}, args=[u'Identifier'], icon=u'domain')

UDM_SETTINGS_DATA_CREATED = DiaryEvent(u'UDM_SETTINGS_DATA_CREATED', {u'en': u'Data {name} created', u'de': u'Data {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_DATA_MODIFIED = DiaryEvent(u'UDM_SETTINGS_DATA_MODIFIED', {u'en': u'Data {name} modified', u'de': u'Data {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_DATA_MOVED = DiaryEvent(u'UDM_SETTINGS_DATA_MOVED', {u'en': u'Data {name} moved to {position}', u'de': u'Data {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_DATA_REMOVED = DiaryEvent(u'UDM_SETTINGS_DATA_REMOVED', {u'en': u'Data {name} removed', u'de': u'Data {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_DEFAULT_MODIFIED = DiaryEvent(u'UDM_SETTINGS_DEFAULT_MODIFIED', {u'en': u'Default preference {name} modified', u'de': u'Standard Einstellung {name} bearbeitet'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_DIRECTORY_MODIFIED = DiaryEvent(u'UDM_SETTINGS_DIRECTORY_MODIFIED', {u'en': u'Default container {name} modified', u'de': u'Standard-Container {name} bearbeitet'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_EXTENDED_ATTRIBUTE_CREATED = DiaryEvent(u'UDM_SETTINGS_EXTENDED_ATTRIBUTE_CREATED', {u'en': u'Extended attribute {name} created', u'de': u'Erweitertes Attribut {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_EXTENDED_ATTRIBUTE_MODIFIED = DiaryEvent(u'UDM_SETTINGS_EXTENDED_ATTRIBUTE_MODIFIED', {u'en': u'Extended attribute {name} modified', u'de': u'Erweitertes Attribut {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_EXTENDED_ATTRIBUTE_MOVED = DiaryEvent(u'UDM_SETTINGS_EXTENDED_ATTRIBUTE_MOVED', {u'en': u'Extended attribute {name} moved to {position}', u'de': u'Erweitertes Attribut {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_EXTENDED_ATTRIBUTE_REMOVED = DiaryEvent(u'UDM_SETTINGS_EXTENDED_ATTRIBUTE_REMOVED', {u'en': u'Extended attribute {name} removed', u'de': u'Erweitertes Attribut {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_EXTENDED_OPTIONS_CREATED = DiaryEvent(u'UDM_SETTINGS_EXTENDED_OPTIONS_CREATED', {u'en': u'Extended option {name} created', u'de': u'Erweiterte Option {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_EXTENDED_OPTIONS_MODIFIED = DiaryEvent(u'UDM_SETTINGS_EXTENDED_OPTIONS_MODIFIED', {u'en': u'Extended option {name} modified', u'de': u'Erweiterte Option {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_EXTENDED_OPTIONS_MOVED = DiaryEvent(u'UDM_SETTINGS_EXTENDED_OPTIONS_MOVED', {u'en': u'Extended option {name} moved to {position}', u'de': u'Erweiterte Option {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_EXTENDED_OPTIONS_REMOVED = DiaryEvent(u'UDM_SETTINGS_EXTENDED_OPTIONS_REMOVED', {u'en': u'Extended option {name} removed', u'de': u'Erweiterte Option {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_LDAPACL_CREATED = DiaryEvent(u'UDM_SETTINGS_LDAPACL_CREATED', {u'en': u'LDAP ACL Extension {name} created', u'de': u'LDAP ACL Erweiterung {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_LDAPACL_MODIFIED = DiaryEvent(u'UDM_SETTINGS_LDAPACL_MODIFIED', {u'en': u'LDAP ACL Extension {name} modified', u'de': u'LDAP ACL Erweiterung {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_LDAPACL_MOVED = DiaryEvent(u'UDM_SETTINGS_LDAPACL_MOVED', {u'en': u'LDAP ACL Extension {name} moved to {position}', u'de': u'LDAP ACL Erweiterung {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_LDAPACL_REMOVED = DiaryEvent(u'UDM_SETTINGS_LDAPACL_REMOVED', {u'en': u'LDAP ACL Extension {name} removed', u'de': u'LDAP ACL Erweiterung {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_LDAPSCHEMA_CREATED = DiaryEvent(u'UDM_SETTINGS_LDAPSCHEMA_CREATED', {u'en': u'LDAP Schema Extension {name} created', u'de': u'LDAP-Schemaerweiterung {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_LDAPSCHEMA_MODIFIED = DiaryEvent(u'UDM_SETTINGS_LDAPSCHEMA_MODIFIED', {u'en': u'LDAP Schema Extension {name} modified', u'de': u'LDAP-Schemaerweiterung {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_LDAPSCHEMA_MOVED = DiaryEvent(u'UDM_SETTINGS_LDAPSCHEMA_MOVED', {u'en': u'LDAP Schema Extension {name} moved to {position}', u'de': u'LDAP-Schemaerweiterung {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_LDAPSCHEMA_REMOVED = DiaryEvent(u'UDM_SETTINGS_LDAPSCHEMA_REMOVED', {u'en': u'LDAP Schema Extension {name} removed', u'de': u'LDAP-Schemaerweiterung {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_LICENSE_REMOVED = DiaryEvent(u'UDM_SETTINGS_LICENSE_REMOVED', {u'en': u'License {name} ({keyID}) removed', u'de': u'Lizenz {name} ({keyID}) gelöscht'}, args=[u'name', u'keyID'], icon=u'domain')

UDM_SETTINGS_LOCK_MODIFIED = DiaryEvent(u'UDM_SETTINGS_LOCK_MODIFIED', {u'en': u'Lock {name} ({locktime}) modified', u'de': u'Sperrobjekt {name} ({locktime}) bearbeitet'}, args=[u'name', u'locktime'], icon=u'domain')
UDM_SETTINGS_LOCK_REMOVED = DiaryEvent(u'UDM_SETTINGS_LOCK_REMOVED', {u'en': u'Lock {name} ({locktime}) removed', u'de': u'Sperrobjekt {name} ({locktime}) gelöscht'}, args=[u'name', u'locktime'], icon=u'domain')

UDM_SETTINGS_PACKAGES_CREATED = DiaryEvent(u'UDM_SETTINGS_PACKAGES_CREATED', {u'en': u'Package List {name} created', u'de': u'Paketliste {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PACKAGES_MODIFIED = DiaryEvent(u'UDM_SETTINGS_PACKAGES_MODIFIED', {u'en': u'Package List {name} modified', u'de': u'Paketliste {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PACKAGES_MOVED = DiaryEvent(u'UDM_SETTINGS_PACKAGES_MOVED', {u'en': u'Package List {name} moved to {position}', u'de': u'Paketliste {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PACKAGES_REMOVED = DiaryEvent(u'UDM_SETTINGS_PACKAGES_REMOVED', {u'en': u'Package List {name} removed', u'de': u'Paketliste {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_PORTAL_CREATED = DiaryEvent(u'UDM_SETTINGS_PORTAL_CREATED', {u'en': u'Portal {name} created', u'de': u'Portal {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PORTAL_MODIFIED = DiaryEvent(u'UDM_SETTINGS_PORTAL_MODIFIED', {u'en': u'Portal {name} modified', u'de': u'Portal {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PORTAL_MOVED = DiaryEvent(u'UDM_SETTINGS_PORTAL_MOVED', {u'en': u'Portal {name} moved to {position}', u'de': u'Portal {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PORTAL_REMOVED = DiaryEvent(u'UDM_SETTINGS_PORTAL_REMOVED', {u'en': u'Portal {name} removed', u'de': u'Portal {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_PORTAL_CATEGORY_CREATED = DiaryEvent(u'UDM_SETTINGS_PORTAL_CATEGORY_CREATED', {u'en': u'Portal category {name} created', u'de': u'Portal-Kategorie {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PORTAL_CATEGORY_MODIFIED = DiaryEvent(u'UDM_SETTINGS_PORTAL_CATEGORY_MODIFIED', {u'en': u'Portal category {name} modified', u'de': u'Portal-Kategorie {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PORTAL_CATEGORY_MOVED = DiaryEvent(u'UDM_SETTINGS_PORTAL_CATEGORY_MOVED', {u'en': u'Portal category {name} moved to {position}', u'de': u'Portal-Kategorie {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PORTAL_CATEGORY_REMOVED = DiaryEvent(u'UDM_SETTINGS_PORTAL_CATEGORY_REMOVED', {u'en': u'Portal category {name} removed', u'de': u'Portal-Kategorie {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_PORTAL_ENTRY_CREATED = DiaryEvent(u'UDM_SETTINGS_PORTAL_ENTRY_CREATED', {u'en': u'Portal entry {name} created', u'de': u'Portal-Eintrag {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PORTAL_ENTRY_MODIFIED = DiaryEvent(u'UDM_SETTINGS_PORTAL_ENTRY_MODIFIED', {u'en': u'Portal entry {name} modified', u'de': u'Portal-Eintrag {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PORTAL_ENTRY_MOVED = DiaryEvent(u'UDM_SETTINGS_PORTAL_ENTRY_MOVED', {u'en': u'Portal entry {name} moved to {position}', u'de': u'Portal-Eintrag {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PORTAL_ENTRY_REMOVED = DiaryEvent(u'UDM_SETTINGS_PORTAL_ENTRY_REMOVED', {u'en': u'Portal entry {name} removed', u'de': u'Portal-Eintrag {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_PRINTERMODEL_CREATED = DiaryEvent(u'UDM_SETTINGS_PRINTERMODEL_CREATED', {u'en': u'Printer Driver List {name} created', u'de': u'Druckertreiberliste {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PRINTERMODEL_MODIFIED = DiaryEvent(u'UDM_SETTINGS_PRINTERMODEL_MODIFIED', {u'en': u'Printer Driver List {name} modified', u'de': u'Druckertreiberliste {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PRINTERMODEL_MOVED = DiaryEvent(u'UDM_SETTINGS_PRINTERMODEL_MOVED', {u'en': u'Printer Driver List {name} moved to {position}', u'de': u'Druckertreiberliste {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PRINTERMODEL_REMOVED = DiaryEvent(u'UDM_SETTINGS_PRINTERMODEL_REMOVED', {u'en': u'Printer Driver List {name} removed', u'de': u'Druckertreiberliste {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_PRINTERURI_CREATED = DiaryEvent(u'UDM_SETTINGS_PRINTERURI_CREATED', {u'en': u'Printer URI List {name} created', u'de': u'Drucker-URI-Liste {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PRINTERURI_MODIFIED = DiaryEvent(u'UDM_SETTINGS_PRINTERURI_MODIFIED', {u'en': u'Printer URI List {name} modified', u'de': u'Drucker-URI-Liste {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PRINTERURI_MOVED = DiaryEvent(u'UDM_SETTINGS_PRINTERURI_MOVED', {u'en': u'Printer URI List {name} moved to {position}', u'de': u'Drucker-URI-Liste {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PRINTERURI_REMOVED = DiaryEvent(u'UDM_SETTINGS_PRINTERURI_REMOVED', {u'en': u'Printer URI List {name} removed', u'de': u'Drucker-URI-Liste {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_PROHIBITED_USERNAME_CREATED = DiaryEvent(u'UDM_SETTINGS_PROHIBITED_USERNAME_CREATED', {u'en': u'Prohibited user name {name} created', u'de': u'Verbotener Benutzername {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PROHIBITED_USERNAME_MODIFIED = DiaryEvent(u'UDM_SETTINGS_PROHIBITED_USERNAME_MODIFIED', {u'en': u'Prohibited user name {name} modified', u'de': u'Verbotener Benutzername {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PROHIBITED_USERNAME_MOVED = DiaryEvent(u'UDM_SETTINGS_PROHIBITED_USERNAME_MOVED', {u'en': u'Prohibited user name {name} moved to {position}', u'de': u'Verbotener Benutzername {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_PROHIBITED_USERNAME_REMOVED = DiaryEvent(u'UDM_SETTINGS_PROHIBITED_USERNAME_REMOVED', {u'en': u'Prohibited user name {name} removed', u'de': u'Verbotener Benutzername {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_SAMBACONFIG_MODIFIED = DiaryEvent(u'UDM_SETTINGS_SAMBACONFIG_MODIFIED', {u'en': u'Samba Configuration {name} modified', u'de': u'Samba-Konfiguration {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_SAMBACONFIG_MOVED = DiaryEvent(u'UDM_SETTINGS_SAMBACONFIG_MOVED', {u'en': u'Samba Configuration {name} moved to {position}', u'de': u'Samba-Konfiguration {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_SAMBACONFIG_REMOVED = DiaryEvent(u'UDM_SETTINGS_SAMBACONFIG_REMOVED', {u'en': u'Samba Configuration {name} removed', u'de': u'Samba-Konfiguration {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_SAMBADOMAIN_CREATED = DiaryEvent(u'UDM_SETTINGS_SAMBADOMAIN_CREATED', {u'en': u'Samba Domain {name} ({SID}) created', u'de': u'Samba-Domänenname {name} ({SID}) angelegt'}, args=[u'name', u'SID'], icon=u'domain')
UDM_SETTINGS_SAMBADOMAIN_MODIFIED = DiaryEvent(u'UDM_SETTINGS_SAMBADOMAIN_MODIFIED', {u'en': u'Samba Domain {name} ({SID}) modified', u'de': u'Samba-Domänenname {name} ({SID}) bearbeitet'}, args=[u'name', u'SID'], icon=u'domain')
UDM_SETTINGS_SAMBADOMAIN_MOVED = DiaryEvent(u'UDM_SETTINGS_SAMBADOMAIN_MOVED', {u'en': u'Samba Domain {name} ({SID}) moved to {position}', u'de': u'Samba-Domänenname {name} ({SID}) verschoben nach {position}'}, args=[u'name', u'SID'], icon=u'domain')
UDM_SETTINGS_SAMBADOMAIN_REMOVED = DiaryEvent(u'UDM_SETTINGS_SAMBADOMAIN_REMOVED', {u'en': u'Samba Domain {name} ({SID}) removed', u'de': u'Samba-Domänenname {name} ({SID}) gelöscht'}, args=[u'name', u'SID'], icon=u'domain')

UDM_SETTINGS_SERVICE_CREATED = DiaryEvent(u'UDM_SETTINGS_SERVICE_CREATED', {u'en': u'Service {name} created', u'de': u'Dienstname {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_SERVICE_MODIFIED = DiaryEvent(u'UDM_SETTINGS_SERVICE_MODIFIED', {u'en': u'Service {name} modified', u'de': u'Dienstname {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_SERVICE_MOVED = DiaryEvent(u'UDM_SETTINGS_SERVICE_MOVED', {u'en': u'Service {name} moved to {position}', u'de': u'Dienstname {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_SERVICE_REMOVED = DiaryEvent(u'UDM_SETTINGS_SERVICE_REMOVED', {u'en': u'Service {name} removed', u'de': u'Dienstname {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_SYNTAX_CREATED = DiaryEvent(u'UDM_SETTINGS_SYNTAX_CREATED', {u'en': u'Syntax Definition {name} created', u'de': u'Syntax-Definition {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_SYNTAX_MODIFIED = DiaryEvent(u'UDM_SETTINGS_SYNTAX_MODIFIED', {u'en': u'Syntax Definition {name} modified', u'de': u'Syntax-Definition {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_SYNTAX_MOVED = DiaryEvent(u'UDM_SETTINGS_SYNTAX_MOVED', {u'en': u'Syntax Definition {name} moved to {position}', u'de': u'Syntax-Definition {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_SYNTAX_REMOVED = DiaryEvent(u'UDM_SETTINGS_SYNTAX_REMOVED', {u'en': u'Syntax Definition {name} removed', u'de': u'Syntax-Definition {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_UDM_HOOK_CREATED = DiaryEvent(u'UDM_SETTINGS_UDM_HOOK_CREATED', {u'en': u'UDM Hook {name} created', u'de': u'UDM Hook {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UDM_HOOK_MODIFIED = DiaryEvent(u'UDM_SETTINGS_UDM_HOOK_MODIFIED', {u'en': u'UDM Hook {name} modified', u'de': u'UDM Hook {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UDM_HOOK_MOVED = DiaryEvent(u'UDM_SETTINGS_UDM_HOOK_MOVED', {u'en': u'UDM Hook {name} moved to {position}', u'de': u'UDM Hook {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UDM_HOOK_REMOVED = DiaryEvent(u'UDM_SETTINGS_UDM_HOOK_REMOVED', {u'en': u'UDM Hook {name} removed', u'de': u'UDM Hook {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_UDM_MODULE_CREATED = DiaryEvent(u'UDM_SETTINGS_UDM_MODULE_CREATED', {u'en': u'UDM Module {name} created', u'de': u'UDM-Modul {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UDM_MODULE_MODIFIED = DiaryEvent(u'UDM_SETTINGS_UDM_MODULE_MODIFIED', {u'en': u'UDM Module {name} modified', u'de': u'UDM-Modul {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UDM_MODULE_MOVED = DiaryEvent(u'UDM_SETTINGS_UDM_MODULE_MOVED', {u'en': u'UDM Module {name} moved to {position}', u'de': u'UDM-Modul {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UDM_MODULE_REMOVED = DiaryEvent(u'UDM_SETTINGS_UDM_MODULE_REMOVED', {u'en': u'UDM Module {name} removed', u'de': u'UDM-Modul {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_UDM_SYNTAX_CREATED = DiaryEvent(u'UDM_SETTINGS_UDM_SYNTAX_CREATED', {u'en': u'UDM Syntax {name} created', u'de': u'UDM Syntax {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UDM_SYNTAX_MODIFIED = DiaryEvent(u'UDM_SETTINGS_UDM_SYNTAX_MODIFIED', {u'en': u'UDM Syntax {name} modified', u'de': u'UDM Syntax {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UDM_SYNTAX_MOVED = DiaryEvent(u'UDM_SETTINGS_UDM_SYNTAX_MOVED', {u'en': u'UDM Syntax {name} moved to {position}', u'de': u'UDM Syntax {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UDM_SYNTAX_REMOVED = DiaryEvent(u'UDM_SETTINGS_UDM_SYNTAX_REMOVED', {u'en': u'UDM Syntax {name} removed', u'de': u'UDM Syntax {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_UMC_OPERATIONSET_CREATED = DiaryEvent(u'UDM_SETTINGS_UMC_OPERATIONSET_CREATED', {u'en': u'UMC operation set {name} created', u'de': u'UMC-Befehlssatz {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UMC_OPERATIONSET_MODIFIED = DiaryEvent(u'UDM_SETTINGS_UMC_OPERATIONSET_MODIFIED', {u'en': u'UMC operation set {name} modified', u'de': u'UMC-Befehlssatz {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UMC_OPERATIONSET_MOVED = DiaryEvent(u'UDM_SETTINGS_UMC_OPERATIONSET_MOVED', {u'en': u'UMC operation set {name} moved to {position}', u'de': u'UMC-Befehlssatz {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_UMC_OPERATIONSET_REMOVED = DiaryEvent(u'UDM_SETTINGS_UMC_OPERATIONSET_REMOVED', {u'en': u'UMC operation set {name} removed', u'de': u'UMC-Befehlssatz {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_USERTEMPLATE_CREATED = DiaryEvent(u'UDM_SETTINGS_USERTEMPLATE_CREATED', {u'en': u'User Template {name} created', u'de': u'Benutzervorlage {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_USERTEMPLATE_MODIFIED = DiaryEvent(u'UDM_SETTINGS_USERTEMPLATE_MODIFIED', {u'en': u'User Template {name} modified', u'de': u'Benutzervorlage {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_USERTEMPLATE_MOVED = DiaryEvent(u'UDM_SETTINGS_USERTEMPLATE_MOVED', {u'en': u'User Template {name} moved to {position}', u'de': u'Benutzervorlage {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SETTINGS_USERTEMPLATE_REMOVED = DiaryEvent(u'UDM_SETTINGS_USERTEMPLATE_REMOVED', {u'en': u'User Template {name} removed', u'de': u'Benutzervorlage {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SETTINGS_XCONFIG_CHOICES_MODIFIED = DiaryEvent(u'UDM_SETTINGS_XCONFIG_CHOICES_MODIFIED', {u'en': u'X Configuration Choice {name} modified', u'de': u'X-Konfigurations Auswahl {name} bearbeitet'}, args=[u'name'], icon=u'domain')

UDM_SHARES_PRINTER_CREATED = DiaryEvent(u'UDM_SHARES_PRINTER_CREATED', {u'en': u'Printer {name} created', u'de': u'Drucker {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SHARES_PRINTER_MODIFIED = DiaryEvent(u'UDM_SHARES_PRINTER_MODIFIED', {u'en': u'Printer {name} modified', u'de': u'Drucker {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SHARES_PRINTER_MOVED = DiaryEvent(u'UDM_SHARES_PRINTER_MOVED', {u'en': u'Printer {name} moved to {position}', u'de': u'Drucker {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SHARES_PRINTER_REMOVED = DiaryEvent(u'UDM_SHARES_PRINTER_REMOVED', {u'en': u'Printer {name} removed', u'de': u'Drucker {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SHARES_PRINTERGROUP_CREATED = DiaryEvent(u'UDM_SHARES_PRINTERGROUP_CREATED', {u'en': u'Printer share group {name} created', u'de': u'Druckerfreigabegruppe {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SHARES_PRINTERGROUP_MODIFIED = DiaryEvent(u'UDM_SHARES_PRINTERGROUP_MODIFIED', {u'en': u'Printer share group {name} modified', u'de': u'Druckerfreigabegruppe {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SHARES_PRINTERGROUP_MOVED = DiaryEvent(u'UDM_SHARES_PRINTERGROUP_MOVED', {u'en': u'Printer share group {name} moved to {position}', u'de': u'Druckerfreigabegruppe {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SHARES_PRINTERGROUP_REMOVED = DiaryEvent(u'UDM_SHARES_PRINTERGROUP_REMOVED', {u'en': u'Printer share group {name} removed', u'de': u'Druckerfreigabegruppe {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_SHARES_SHARE_CREATED = DiaryEvent(u'UDM_SHARES_SHARE_CREATED', {u'en': u'Share directory {name} created', u'de': u'Freigabe-Verzeichnis {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_SHARES_SHARE_MODIFIED = DiaryEvent(u'UDM_SHARES_SHARE_MODIFIED', {u'en': u'Share directory {name} modified', u'de': u'Freigabe-Verzeichnis {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_SHARES_SHARE_MOVED = DiaryEvent(u'UDM_SHARES_SHARE_MOVED', {u'en': u'Share directory {name} moved to {position}', u'de': u'Freigabe-Verzeichnis {name} verschoben nach {position}'}, args=[u'name'], icon=u'domain')
UDM_SHARES_SHARE_REMOVED = DiaryEvent(u'UDM_SHARES_SHARE_REMOVED', {u'en': u'Share directory {name} removed', u'de': u'Freigabe-Verzeichnis {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_USERS_CONTACT_CREATED = DiaryEvent(u'UDM_USERS_CONTACT_CREATED', {u'en': u'Contact {cn} created', u'de': u'Kontakt {cn} angelegt'}, args=[u'cn'], icon=u'users')
UDM_USERS_CONTACT_MODIFIED = DiaryEvent(u'UDM_USERS_CONTACT_MODIFIED', {u'en': u'Contact {cn} modified', u'de': u'Kontakt {cn} bearbeitet'}, args=[u'cn'], icon=u'users')
UDM_USERS_CONTACT_MOVED = DiaryEvent(u'UDM_USERS_CONTACT_MOVED', {u'en': u'Contact {cn} moved to {position}', u'de': u'Kontakt {cn} verschoben nach {position}'}, args=[u'cn'], icon=u'users')
UDM_USERS_CONTACT_REMOVED = DiaryEvent(u'UDM_USERS_CONTACT_REMOVED', {u'en': u'Contact {cn} removed', u'de': u'Kontakt {cn} gelöscht'}, args=[u'cn'], icon=u'users')

UDM_USERS_LDAP_CREATED = DiaryEvent(u'UDM_USERS_LDAP_CREATED', {u'en': u'Simple authentication account {username} created', u'de': u'Einfaches Authentisierungskonto {username} angelegt'}, args=[u'username'], icon=u'users')
UDM_USERS_LDAP_MODIFIED = DiaryEvent(u'UDM_USERS_LDAP_MODIFIED', {u'en': u'Simple authentication account {username} modified', u'de': u'Einfaches Authentisierungskonto {username} bearbeitet'}, args=[u'username'], icon=u'users')
UDM_USERS_LDAP_MOVED = DiaryEvent(u'UDM_USERS_LDAP_MOVED', {u'en': u'Simple authentication account {username} moved to {position}', u'de': u'Einfaches Authentisierungskonto {username} verschoben nach {position}'}, args=[u'username'], icon=u'users')
UDM_USERS_LDAP_REMOVED = DiaryEvent(u'UDM_USERS_LDAP_REMOVED', {u'en': u'Simple authentication account {username} removed', u'de': u'Einfaches Authentisierungskonto {username} gelöscht'}, args=[u'username'], icon=u'users')

UDM_USERS_PASSWD_MODIFIED = DiaryEvent(u'UDM_USERS_PASSWD_MODIFIED', {u'en': u'Password {username} modified', u'de': u'Passwort {username} bearbeitet'}, args=[u'username'], icon=u'users')

UDM_USERS_USER_CREATED = DiaryEvent(u'UDM_USERS_USER_CREATED', {u'en': u'User {username} created', u'de': u'Benutzer {username} angelegt'}, args=[u'username'], icon=u'users')
UDM_USERS_USER_MODIFIED = DiaryEvent(u'UDM_USERS_USER_MODIFIED', {u'en': u'User {username} modified', u'de': u'Benutzer {username} bearbeitet'}, args=[u'username'], icon=u'users')
UDM_USERS_USER_MOVED = DiaryEvent(u'UDM_USERS_USER_MOVED', {u'en': u'User {username} moved to {position}', u'de': u'Benutzer {username} verschoben nach {position}'}, args=[u'username'], icon=u'users')
UDM_USERS_USER_REMOVED = DiaryEvent(u'UDM_USERS_USER_REMOVED', {u'en': u'User {username} removed', u'de': u'Benutzer {username} gelöscht'}, args=[u'username'], icon=u'users')

UDM_UVMM_CLOUDCONNECTION_CREATED = DiaryEvent(u'UDM_UVMM_CLOUDCONNECTION_CREATED', {u'en': u'Cloud Connection {name} created', u'de': u'Cloud Connection {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_UVMM_CLOUDCONNECTION_MODIFIED = DiaryEvent(u'UDM_UVMM_CLOUDCONNECTION_MODIFIED', {u'en': u'Cloud Connection {name} modified', u'de': u'Cloud Connection {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_UVMM_CLOUDCONNECTION_REMOVED = DiaryEvent(u'UDM_UVMM_CLOUDCONNECTION_REMOVED', {u'en': u'Cloud Connection {name} removed', u'de': u'Cloud Connection {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_UVMM_CLOUDTYPE_CREATED = DiaryEvent(u'UDM_UVMM_CLOUDTYPE_CREATED', {u'en': u'Cloud Type {name} created', u'de': u'Cloud Type {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_UVMM_CLOUDTYPE_MODIFIED = DiaryEvent(u'UDM_UVMM_CLOUDTYPE_MODIFIED', {u'en': u'Cloud Type {name} modified', u'de': u'Cloud Type {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_UVMM_CLOUDTYPE_REMOVED = DiaryEvent(u'UDM_UVMM_CLOUDTYPE_REMOVED', {u'en': u'Cloud Type {name} removed', u'de': u'Cloud Type {name} gelöscht'}, args=[u'name'], icon=u'domain')

UDM_UVMM_INFO_CREATED = DiaryEvent(u'UDM_UVMM_INFO_CREATED', {u'en': u'Machine information {uuid} created', u'de': u'Machine information {uuid} angelegt'}, args=[u'uuid'], icon=u'domain')
UDM_UVMM_INFO_MODIFIED = DiaryEvent(u'UDM_UVMM_INFO_MODIFIED', {u'en': u'Machine information {uuid} modified', u'de': u'Machine information {uuid} bearbeitet'}, args=[u'uuid'], icon=u'domain')
UDM_UVMM_INFO_REMOVED = DiaryEvent(u'UDM_UVMM_INFO_REMOVED', {u'en': u'Machine information {uuid} removed', u'de': u'Machine information {uuid} gelöscht'}, args=[u'uuid'], icon=u'domain')

UDM_UVMM_PROFILE_CREATED = DiaryEvent(u'UDM_UVMM_PROFILE_CREATED', {u'en': u'Profile {name} created', u'de': u'Profile {name} angelegt'}, args=[u'name'], icon=u'domain')
UDM_UVMM_PROFILE_MODIFIED = DiaryEvent(u'UDM_UVMM_PROFILE_MODIFIED', {u'en': u'Profile {name} modified', u'de': u'Profile {name} bearbeitet'}, args=[u'name'], icon=u'domain')
UDM_UVMM_PROFILE_REMOVED = DiaryEvent(u'UDM_UVMM_PROFILE_REMOVED', {u'en': u'Profile {name} removed', u'de': u'Profile {name} gelöscht'}, args=[u'name'], icon=u'domain')

