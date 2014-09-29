/*
 * Copyright 2014 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */

/*global define*/

define([
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/query",
	"dojo/dom-style",
	"dojo/topic",
	"umc/app",
	"umc/tools",
	"umc/i18n!umc/modules/appcenter"
], function(kernel, lang, array, query, style, topic, UMCApplication, tools, _) {
	var AppInstallationsItem = function(name, info, detailPage) {
		this.id = name;
		this.name = name;
		this.fqdn = this.name + '.' + tools.status('domainname');
		if (this.isLocal()) {
			this.displayName = lang.replace('{fqdn} ({localhost})', {fqdn: this.fqdn, localhost: _('this computer')});
		} else {
			this.displayName = this.fqdn;
		}
		this.ipAddress = info.ip[0];
		this.role = info.role;
		this.detailPage = detailPage;
		this.computer_description = info.description;
		this.version = info.version;
		this.candidateVersion = this.detailPage.app.candidate_version || this.detailPage.app.version;
		this.moduleName = this.detailPage.app.umcmodulename;
		this.moduleFlavor = this.detailPage.app.umcmoduleflavor;
		this.webInterface = this.detailPage.app.webinterface;
		this.allowedRoles = array.map(this.detailPage.app.serverrole, function(role) {
			if (role == 'domaincontroller_master') {
				return 'master';
			} else if (role == 'domaincontroller_backup') {
				return 'backup';
			} else if (role == 'domaincontroller_slave') {
				return 'slave';
			} else if (role == 'memberserver') {
				return 'member';
			}
		});
	};

	kernel.extend(AppInstallationsItem, {
		hasFittingRole: function() {
			return this.allowedRoles.length === 0 || this.allowedRoles.indexOf(this.role) !== -1;
		},

		canInstall: function() {
			return this.hasFittingRole() && !this.isInstalled();
		},

		canUpgrade: function() {
			return !!this.version && this.version != this.candidateVersion;
		},

		canUninstall: function() {
			return this.isInstalled();
		},

		isInstalled: function() {
			return !!this.version;
		},

		canOpen: function() {
			if (this.isInstalled()) {
				if (this.isLocal()) { // necessary because of Bug #36016
					return !!(this.moduleName || this.webInterface);
				} else {
					return !!this.webInterface;
				}
			}
			return false;
		},

		isLocal: function() {
			return this.name == tools.status('hostname');
		},

		install: function() {
			this.detailPage.installApp(this.name);
		},

		upgrade: function() {
			this.detailPage.upgradeApp(this.name);
		},

		uninstall: function() {
			this.detailPage.uninstallApp(this.name);
		},

		open: function() {
			var host = this.fqdn;
			var localHost = window.location.host;
			if (this.isLocal()) {
				host = localHost;
			} else {
				// taken from: http://stackoverflow.com/a/9221063
				var _regIPv4 =  /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))$/;
				var _regIPv6 = /^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?$/;
				if (_regIPv4.test(localHost) || _regIPv6.test(localHost)) {
					host = this.ipAddress;
				}
			}
			if (this.moduleName && this.isLocal()) { // && isLocal is necessary because of Bug #36016
				if (this.isLocal()) {
					var module = UMCApplication.getModule(this.moduleName, this.moduleFlavor);
					topic.publish('/umc/modules/open', this.moduleName, this.moduleFlavor);
				} else {
					tools.openRemoteSession(host);
				}
			}
			if (this.webInterface) {
				var url = this.webInterface;
				if (this.webInterface[0] == '/' && !this.isLocal()) {
					url = lang.replace('{protocol}//{host}{webInterface}', {
						protocol: window.location.protocol,
						host: host,
						webInterface: this.webInterface
					});
				}
				window.open(url, '_blank');
			}
		}
	});

	return AppInstallationsItem;
});

