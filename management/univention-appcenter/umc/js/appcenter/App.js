/*
 * Copyright 2015-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */

/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/topic",
	"dojo/json",
	"dojox/html/entities",
	"umc/app",
	"umc/tools",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, kernel, lang, topic, json, entities, UMCApplication, tools, _) {
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
			this.voteForApp = props.vote_for_app;
			this.logoName = props.logo_name;
			this.logoDetailPageName = props.logo_detail_page_name;
			this.version = props.version;
			this.candidateVersion = props.candidate_version;
			this.candidateHasNoInstallPermissions = props.candidate_needs_install_permissions;
			this.candidateInstallPermissionMessage = props.candidate_install_permissions_message;
			this.licenseDescription = props.license_description;
			this.categories = props.categories;
			this.website = props.website;
			this.description = props.description;
			this.longDescription = props.long_description;
			this.supportURL = props.support_url;
			this.contact = props.contact;
			this.vendor = props.vendor;
			this.websiteVendor = props.website_vendor;
			this.notifyVendor = props.notify_vendor;
			this.maintainer = props.maintainer;
			this.websiteMaintainer = props.website_maintainer;
			this.thumbnails = props.thumbnails;
			this.withoutRepository = props.without_repository;
			this.isInstalled = props.is_installed;
			this.moduleName = props.umc_module_name;
			this.moduleFlavor = props.umc_module_flavor;
			this.webInterface = entities.decode(props.web_interface);
			this.webInterfaceName = props.web_interface_name;
			this.webInterfacePortHTTP = props.web_interface_port_http;
			this.webInterfacePortHTTPS = props.web_interface_port_https;
			this.endOfLife = props.end_of_life;
			this.ucsVersion = props.ucs_version;
			this.isCurrent = props.is_current;
			this.allowedRoles = props.server_role;
			this.role = props.local_role;
			this.componentID = props.component_id;
			this.candidateComponentID = props.candidate_component_id;
			this.licenseAgreement = props.license_agreement;
			this.readme = props.readme;
			this.readmeInstall = props.readme_install;
			this.readmePostInstall = props.readme_post_install;
			this.readmeUninstall = props.readme_uninstall;
			this.readmePostUninstall = props.readme_post_uninstall;
			this.candidateReadmeUpdate = props.candidate_readme_update;
			this.candidateReadmePostUpdate = props.candidate_readme_post_update;
			this.useShop = !!props.shop_url;
			this.shopURL = props.shop_url;
			this.rating = props.rating;
			this.isMaster = props.is_master;
			this.isUCSComponent = props.is_ucs_component;
			this.isDocker = !!props.docker_image || !!props.docker_main_service;
			this.candidateIsDocker = !!props.candidate_docker;
			this.dockerMigrationLink = props.docker_migration_link;
			this.autoModProxy = props.auto_mod_proxy;
			this.pluginOf = props.plugin_of;
			this.hostMaster = props.host_master;
			this.userActivationRequired = props.user_activation_required || props.generic_user_activation;
			this.settings = props.settings;
			this.ipAddress = props.ip_address;
			this.updateAvailable = props.update_available;
			this.installations = props.installations;
			this.installationData = null;
			if (this.installations) {
				this.installationData = [];
				tools.forIn(this.installations, lang.hitch(this, function(hostName, info) {
					var newProps = lang.clone(props);
					delete newProps.installations;
					newProps.version = info.version;
					newProps.candidate_version = null;
					newProps.ucs_version = info.ucs_version;
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
					newProps.update_available = info.update_available;
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
				if (this.autoModProxy && port) {
					// webinterface of a docker app
					// lives behind our standard proxy
					if (protocol == 'http:') {
						port = 80;
					} else if (protocol == 'https:') {
						port = 443;
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
					webinterface: entities.encode(webInterface),
					name: entities.encode(webInterfaceName)
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
					name: entities.encode(module.name)
				});
			}
		},

		canDisable: function() {
			return this.isInstalled && this.endOfLife && this.isCurrent;
		},

		hasConfiguration: function() {
			return this.isDocker || !!this.settings.length;
		},

		canConfigure: function() {
			return this.hasConfiguration() && this.isInstalled && this.isLocal();
		},

		canDisableInDomain: function() {
			return array.some(this.getHosts(), lang.hitch(this, function(app) {
				return app.data.canDisable();
			}));
		},

		canUninstall: function() {
			return this.isInstalled;
		},

		canUninstallInDomain: function() {
			return array.some(this.getHosts(), lang.hitch(this, function(app) {
				return app.data.canUninstall();
			}));
		},


		canUpgrade: function() {
			if (this.candidateHasNoInstallPermissions) {
				// never upgrade app without permission
				return false;
			}
			return this.updateAvailable;
		},

		canUpgradeInDomain: function() {
			return array.some(this.getHosts(), lang.hitch(this, function(app) {
				return app.data.canUpgrade();
			}));
		},

		canVote: function() {
			return !!this.voteForApp;
		},

		canInstall: function() {
			if (this.endOfLife) {
				// never install when app is outdated
				return false;
			}
			if (this.candidateHasNoInstallPermissions) {
				// never install app without permission
				return false;
			}
			if (this.voteForApp) {
				// never install a 'Vote for App' app
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

		canInstallInDomain: function() {
			if (!!this.installationData) {
				return array.some(this.installationData, lang.hitch(this, function(app) {
					return app.canInstall();
				}));
			} else {
				return false;
			}
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

		canOpenInDomain: function() {
			return array.some(this.getHosts(), lang.hitch(this, function(app) {
				return app.data.canOpen();
			}));
		},

		getOpenLabel: function() {
			var module = array.some(this.installationData, function(app) {
				return app.getModule();
			});
			var webInterface = array.some(this.installationData, function(app) {
				return app.getWebInterfaceURL();
			});
			if (module || webInterface) {
				return _('Open');
			}
		},

		installsAsDocker: function() {
			return this.isDocker || this.candidateIsDocker;
		},

		getHosts: function() {
			var hosts = [];
			if (!!this.installationData) {
				array.forEach(this.installationData, lang.hitch(this, function(item) {
					if (item.isInstalled) {
						var appStatus = '';
						if (item.version) {
							appStatus = _('%s installed', item.version);
							if (item.canUpgrade()) {
								appStatus += '. ' + _('Upgrade to %s available', item.candidateVersion);
							}
						}
						var ihost = {
							server: item.displayName,
							id: item.hostName,
							data: item,
							appStatus: appStatus
						};
						if (!item.isLocal() && item.ucsVersion != tools.status('version/version')) {
							ihost.appStatus = _('Different UCS Version. Limited manageability');
						}
						hosts.push(ihost);
					}
				}));
			} else {
				if (this.isInstalled) {
					var appStatus = '';
					if (this.version) {
						appStatus = _('%s installed', this.version);
						if (this.canUpgrade()) {
							appStatus += '. ' + _('Upgrade to %s available', this.candidateVersion);
						}
					}
					hosts.push({
						server: this.displayName,
						id: this.hostName,
						data: this,
						appStatus: appStatus
					});
				}
			}
			return hosts;
		}
	});

	return App;
});

