/*
 * Copyright 2015 Univention GmbH
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

/*global define window*/

define([
	"dojo/_base/declare",
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/topic",
	"dojo/json",
	"dojox/html/entities",
	"umc/app",
	"umc/tools",
	"umc/i18n!umc/modules/appcenter"
], function(declare, kernel, lang, topic, json, entities, UMCApplication, tools, _) {
	var App = declare('umc.modules.appcenter.App', null, {
		constructor: function(props, page, host) {
			props = lang.clone(props);
			this.hostName = host || tools.status('hostname');
			this.fqdn = this.hostName + '.' + tools.status('domainname');
			if (this.isLocal()) {
				this.displayName = lang.replace('{fqdn} ({localhost})', {fqdn: this.fqdn, localhost: _('this computer')});
			} else {
				this.displayName = this.fqdn;
			}
			this.id = props.id;
			this.name = props.name;
			this.icon = props.icon;
			this.version = props.version;
			this.candidateVersion = props.candidate_version;
			this.website = props.website;
			this.description = props.description;
			this.longDescription = props.longdescription;
			this.supportURL = props.supporturl;
			this.contact = props.contact;
			this.vendor = props.vendor;
			this.websiteVendor = props.websitevendor;
			this.notifyVendor = props.notifyvendor;
			this.maintainer = props.maintainer;
			this.websiteMaintainer = props.websitemaintainer;
			this.screenshot = props.screenshot;
			this.withoutRepository = props.withoutrepository;
			this.isInstalled = props.is_installed;
			this.moduleName = props.umcmodulename;
			this.moduleFlavor = props.umcmoduleflavor;
			this.webInterface = entities.decode(props.webinterface);
			this.webInterfaceName = props.webinterfacename;
			this.webInterfacePortHTTP = props.webinterfaceporthttp;
			this.webInterfacePortHTTPS = props.webinterfaceporthttps;
			this.endOfLife = props.endoflife;
			this.isCurrent = props.is_current;
			this.allowedRoles = props.serverrole;
			this.role = props.local_role;
			this.componentID = props.component_id;
			this.candidateComponentID = props.candidate_component_id;
			this.licenseAgreement = props.licenseagreement;
			this.readme = props.readme;
			this.readmeInstall = props.readmeinstall;
			this.readmePostInstall = props.readmepostinstall;
			this.readmeUninstall = props.readmeuninstall;
			this.readmePostUninstall = props.readmepostuninstall;
			this.candidateReadmeUpdate = props.candidate_readmeupdate;
			this.candidateReadmePostUpdate = props.candidate_readmepostupdate;
			this.useShop = !!props.shopurl;
			this.shopURL = props.shopurl;
			this.isMaster = props.is_master;
			this.hostMaster = props.host_master;
			this.userActivationRequired = props.useractivationrequired;
			this.ipAddress = props.ip_address;
			this.installations = props.installations;
			this.installationData = null;
			if (this.installations) {
				this.installationData = [];
				tools.forIn(this.installations, lang.hitch(this, function(hostName, info) {
					var newProps = lang.clone(props);
					delete newProps.installations;
					newProps.version = info.version;
					newProps.candidate_version = null;
					if (info.version !== info.candidate_version) {
						newProps.candidate_version = info.candidate_version;
					}
					if (newProps.version === props.candidate_version) {
						newProps.candidate_version = null;
					} else if (newProps.version === props.version) {
						newProps.candidate_version = props.candidate_version;
					}
					var roles = {
						master: 'domaincontroller_master',
						backup: 'domaincontroller_backup',
						slave: 'domaincontroller_slave',
						member: 'memberserver'
					};
					newProps.local_role = roles[info.role] || info.role;
					newProps.ip_address = info.ip[0];
					newProps.is_installed = !!info.version;
					var installation = new App(newProps, page, hostName);
					this.installationData.push(installation);
				}));
				this.installationData.sort(function(a, b) {
					if (a.role == b.role) {
						return (a.name > b.name) - 0.5;
					}
					var roleWeights = {
						domaincontroller_master: 1,
						domaincontroller_backup: 2,
						domaincontroller_slave: 3,
						memberserver: 4
					};
					var roleA = roleWeights[a.role];
					var roleB = roleWeights[b.role];
					return roleA - roleB;
				});
			}
			var installHost = null;
			if (!this.isLocal()) {
				installHost = this.hostName;
			}
			this.install = lang.hitch(page, 'installAppDialog');
			this.upgrade = lang.hitch(page, 'upgradeApp', installHost);
			this.uninstall = lang.hitch(page, 'uninstallApp', installHost);
		},

		isLocal: function() {
			return this.hostName == tools.status('hostname');
		},

		hasMaintainer: function() {
			if (this.maintainer) {
				return this.maintainer !== this.vendor;
			}
			return false;
		},

		hasFittingRole: function() {
			return this.allowedRoles.length === 0 || this.allowedRoles.indexOf(this.role) !== -1;
		},

		getWebInterfaceURL: function() {
			if (this.isInstalled && this.webInterface) {
				if (this.webInterface.indexOf('/') !== 0) {
					return this.webInterface;
				}
				var webInterface = this.webInterface;
				var protocol = window.location.protocol;
				var host = window.location.host;
				if (!this.isLocal()) {
					// taken from: http://stackoverflow.com/a/9221063
					var _regIPv4 =  /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))$/;
					var _regIPv6 = /^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?$/;
					if (_regIPv4.test(host) || _regIPv6.test(host)) {
						host = this.ipAddress;
					} else {
						host = this.fqdn;
					}

				}
				var port = null;
				if (protocol == 'http:') {
					port = this.webInterfacePortHTTP;
					if (!port && this.webInterfacePortHTTPS) {
						port = this.webInterfacePortHTTPS;
						protocol = 'https:';
					}
				} else if (protocol == 'https:') {
					port = this.webInterfacePortHTTPS;
					if (!port && this.webInterfacePortHTTP) {
						port = this.webInterfacePortHTTP;
						protocol = 'http:';
					}
				}
				if (port == 80) {
					protocol = 'http:';
					port = null;
				} else if (port == 443) {
					protocol = 'https:';
					port = null;
				}
				if (port) {
					port = ':' + port;
				} else {
					port = '';
				}
				return lang.replace('{protocol}//{host}{port}{webInterface}', {
					protocol: protocol,
					host: host,
					port: port,
					webInterface: webInterface
				});
			}
		},

		getWebInterfaceTag: function() {
			var webInterface = this.getWebInterfaceURL();
			var webInterfaceName = this.webInterfaceName || this.name;
			if (webInterface) {
				return lang.replace('<a href="{webinterface}" target="_blank">{name}</a>', {
					webinterface: webInterface,
					name: webInterfaceName
				});
			}
		},

		getModule: function() {
			if (this.isInstalled) {
				return UMCApplication.getModule(this.moduleName, this.moduleFlavor);
			}
		},

		getModuleLink: function() {
			var module = this.getModule();
			if (module) {
				return lang.replace("<a href='javascript:void(0)' onclick='require(\"umc/app\").openModule({umcmodulename}, {umcmoduleflavor})'>{name}</a>", {
					umcmodulename: json.stringify(module.id),
					umcmoduleflavor: json.stringify(module.flavor),
					name: module.name
				});
			}
		},

		canDisable: function() {
			return this.isInstalled && this.endOfLife && this.isCurrent;
		},

		canUninstall: function() {
			return this.isInstalled;
		},

		canUpgrade: function() {
			return this.isInstalled && !!this.candidateVersion;
		},

		canInstall: function() {
			if (this.endOfLife) {
				// never install when app is outdated
				return false;
			}
			if (this.installations) {
				// always allow within the domain
				return true;
			}
			if (this.isInstalled) {
				// no need to install again
				return false;
			}
			return this.hasFittingRole();
		},

		open: function() {
			var module = this.getModule();
			var webInterface = this.getWebInterfaceURL();
			if (module) {
				topic.publish('/umc/modules/open', module.id, module.flavor);
			} else if (webInterface) {
				window.open(webInterface, '_blank');
			}
		},

		canOpen: function() {
			if (this.getWebInterfaceURL()) {
				return true;
			}
			if (this.isLocal()) {
				return !!this.getModule();
			} else {
				return !!this.umcModuleName;
			}
		},

		getOpenLabel: function() {
			var module = this.getModule();
			var webInterface = this.getWebInterfaceURL();
			if (module) {
				return _('Open module');
			} else if (webInterface) {
				return _('Open web site');
			}
		}
	});

	return App;
});

