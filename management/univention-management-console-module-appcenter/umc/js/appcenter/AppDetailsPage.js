/*
 * Copyright 2013-2014 Univention GmbH
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
/*global define console window*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/promise/all",
	"dojo/when",
	"dojo/query",
	"dojo/io-query",
	"dojo/topic",
	"dojo/Deferred",
	"dojo/dom-construct",
	"dojox/image/LightboxNano",
	"umc/app",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/TitlePane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/widgets/ProgressBar",
	"umc/widgets/Page",
	"umc/modules/appcenter/AppCenterGallery",
	"umc/modules/appcenter/AppInstallationsItem",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, kernel, array, all, when, query, ioQuery, topic, Deferred, domConstruct, Lightbox, UMCApplication, tools, dialog, TitlePane, ContainerWidget, Button, ProgressBar, Page, AppCenterGallery, AppInstallationsItem, _) {
	return declare("umc.modules.appcenter.AppDetailsPage", [ Page ], {
		appLoadingDeferred: null,
		standbyDuring: null, // parents standby method must be passed. weird IE-Bug (#29587)

		title: _("App management"),
		noFooter: true,
		getAppCommand: 'appcenter/get',

		backLabel: _('Back to overview'),
		detailsDialog: null,

		appCenterInformation:
			'<p>' + _('Univention App Center is the simplest method to install or uninstall applications on Univention Corporate Server.') + '</p>' +
			'<p>' + _('Univention always receives an estranged notification for statistical purposes upon installation and uninstallation of an application in Univention App Center that is only saved at Univention for data processing and will not be forwarded to any third party.') + '</p>' +
			'<p>' + _('Depending on the guideline of the respective application vendor an updated UCS license key with so-called key identification (Key ID) is required for the installation of an application. In this case, the Key ID will be sent to Univention together with the notification. As a result the application vendor receives a message from Univention with the following information:') +
				'<ul>' +
					'<li>' + _('Name of the installed application') + '</li>' +
					'<li>' + _('Registered email address') + '</li>' +
				'</ul>' +
			_('The description of every application includes a respective indication for such cases.') + '</p>' +
			'<p>' + _('If your UCS environment does not have such a key at it\'s disposal (e.g. UCS Free-for-personal-Use Edition) and the vendor requires a Key ID, you will be asked to request an updated license key directly from Univention. Afterwards the new key can be applied.') + '</p>' +
			'<p>' + _('The sale of licenses, maintenance or support for the applications uses the default processes of the respective vendor and is not part of Univention App Center.') + '</p>',

		postMixInProperties: function() {
			this.inherited(arguments);

			this.appLoadingDeferred = new Deferred();
			this._progressBar = new ProgressBar({});
			this.own(this._progressBar);
			this._grid = new AppCenterGallery({});
			this.own(this._grid);

			this.headerButtons = [{
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: this.backLabel,
				align: 'left',
				callback: lang.hitch(this, 'onBack')
			}];
		},

		_setAppAttr: function(app) {
			this._set('app', app);
			if (this.appLoadingDeferred.isFulfilled()) {
				this.appLoadingDeferred = new Deferred();
			}
			var appLoaded = app;
			if (!app.fully_loaded) {
				// app is just {id: '...'}!
				// we need to ask the server,
				// it is not yet known!
				appLoaded = tools.umcpCommand(this.getAppCommand, {'application': app.id}).then(function(data) {
					return data.result;
				});
			}
			when(appLoaded).then(lang.hitch(this, function(loadedApp) {
				if (loadedApp === null) {
					this.onBack();
					this.appLoadingDeferred.reject();
					return;
				}
				this._set('app', loadedApp);
				this.hostDialog.set('app', app);
				this.detailsDialog.set('app', loadedApp);
				this.set('headerText', loadedApp.name);
				this.set('helpText', this.app.longdescription);
				this._installationData = null;
				if (this.app.installations) {
					this._installationData = [];
					tools.forIn(this.app.installations, lang.hitch(this, function(name, info) {
						var installation = new AppInstallationsItem(name, info, this);
						this._installationData.push(installation);
					}));
					this._installationData.sort(function(a, b) {
						if (a.role == b.role) {
							return (a.name > b.name) - 0.5;
						}
						var roleWeights = {
							master: 1,
							backup: 2,
							slave: 3,
							member: 4
						};
						var roleA = roleWeights[a.role];
						var roleB = roleWeights[b.role];
						return roleA - roleB;
					});
				}
				this.buildInnerPage();
				this.appLoadingDeferred.resolve();
			}));
		},

		_appIsInstalledInDomain: function() {
			return this._appCountInstallations() > 0;
		},

		_appCountInstallations: function() {
			var sum = 0;
			array.forEach(this._installationData, function(item) {
				sum += item.isInstalled();
			});
			return sum;
		},

		reloadPage: function() {
			// reset same app, but only pass the id => loads new from server
			this.set('app', {id: this.app.id});
			return this.appLoadingDeferred;
		},

		getButtons: function() {
			var buttons = [];
			if (this.app.useshop) {
				buttons.push({
					name: 'shop',
					label: _('Buy'),
					iconClass: 'umcShopIcon',
					align: 'right',
					callback: lang.hitch(this, 'openShop')
				});
			}
			if (this.app.is_installed) {
				var umcmodulename = this.app.umcmodulename;
				var umcmoduleflavor = this.app.umcmoduleflavor;
				var module = UMCApplication.getModule(umcmodulename, umcmoduleflavor);
				var webinterface = this.app.webinterface;
				if (module || webinterface) {
					buttons.push({
						name: 'open',
						label: _('Open'),
						align: 'right',
						callback: lang.hitch(this, function() {
							if (module) {
								topic.publish('/umc/modules/open', umcmodulename, umcmoduleflavor);
							} else {
								window.open(webinterface, '_blank');
							}
						})
					});
				}
			}
			if (this.app.is_installed && this.app.endoflife) {
				if (this.app.is_current) {
					buttons.push({
						name: 'disable',
						label: _('Continue using'),
						align: 'right',
						callback: lang.hitch(this, 'disableApp')
					});
				}
			}
			if (this.app.is_installed) {
				buttons.push({
					name: 'uninstall',
					label: _('Uninstall'),
					align: 'right',
					defaultButton: this.app.endoflife,
					callback: lang.hitch(this, 'uninstallApp', null)
				});
			}
			if (this.app.is_installed && this.app.candidate_version) {
				buttons.push({
					name: 'update',
					label: _('Upgrade'),
					defaultButton: true,
					callback: lang.hitch(this, 'upgradeApp', null)
				});
			}
			if (!this.app.endoflife && (!this.app.is_installed || this.app.installations)) {
				buttons.push({
					name: 'install',
					label: _('Install'),
					defaultButton: true,
					callback: lang.hitch(this, 'installAppDialog')
				});
			}
			return buttons;
		},

		buildInnerPage: function() {
			if (this._container) {
				this.removeChild(this._container);
				this._container.destroyRecursive();
				this._container = null;
			}
			if (this._icon) {
				this.removeChild(this._icon);
				this._icon.destroyRecursive()
				this._icon = null;
			}
			this._container = new ContainerWidget({});
			this.addChild(this._container);
			this.own(this._container);
			this.set('navButtons', this.getButtons());
			this._detailsTable = domConstruct.create('table', {
				style: {borderSpacing: '1em 0.1em'}
			});
			var detailsPane = new TitlePane({
				title: _('Details'),
				content: this._detailsTable
			});
			this._container.addChild(detailsPane);
			var iconClass = this._grid.getIconClass(this.app);
			if (iconClass) {
				this._icon = new ContainerWidget({
					region: 'nav',
					'class': iconClass,
					'style': 'margin-bottom: 1em;'
				});
				this.addChild(this._icon, 1);
			}

			this.addToDetails(_('Vendor'), 'Vendor');
			this.addToDetails(_('Maintainer'), 'Maintainer');
			this.addToDetails(_('Contact'), 'Contact');
			this.addToDetails(_('More information'), 'Website');
			this.addToDetails(_('Support'), 'SupportURL');
			this.addToDetails(_('Installed version'), 'Version');
			this.addToDetails(_('Candidate version'), 'CandidateVersion');
			this.addToDetails(_('Screenshot'), 'Screenshot');
			this.addToDetails(_('Notification'), 'NotifyVendor');
			this.addToDetails(_('End of life'), 'EndOfLife');

			query('.umcScreenshot', this._detailsTable).forEach(function(imgNode) {
				new Lightbox({ href: imgNode.src }, imgNode);
			});

			var usage = this.app.readme;
			if (usage) {
				usage = lang.replace(usage, this.app);
			} else {
				usage = this._detailFieldCustomUsage();
			}
			if (usage) {
				var usagePane = new TitlePane({
					title: _('Notes on using'),
					content: usage
				});
				this._container.addChild(usagePane);
			}

			if (this._appIsInstalledInDomain()) {
				var installationTable = domConstruct.create('table', {
					style: {borderSpacing: '1em 0.1em'}
				});
				array.forEach(this._installationData, lang.hitch(this, function(item) {
					if (!item.isInstalled()) {
						return;
					}
					var tr;
					if (item.isLocal()) {
						if (this._appCountInstallations() > 1) {
							domConstruct.create('tr', {style: {height: '4ex'}}, installationTable, 'first');
						}
						tr = domConstruct.create('tr', {}, installationTable, 'first');
					} else {
						tr = domConstruct.create('tr', {}, installationTable);
					}
					domConstruct.create('td', {innerHTML: item.displayName}, tr);
					// value is a DOM node
					var td = domConstruct.create('td', {}, tr);
					var _addButton = lang.hitch(this, function(buttonConf) {
						var button = new Button(buttonConf);
						this.own(button);
						domConstruct.place(button.domNode, td);
					});
					if (item.canOpen()) {
						_addButton({
							label: _('Open'),
							callback: function() {
								item.open();
							},
							name: 'open'
						});
					}
					if (item.canUninstall()) {
						_addButton({
							label: _('Uninstall'),
							callback: function() {
								item.uninstall();
							},
							name: 'uninstall'
						});
					}
					if (item.canUpgrade()) {
						_addButton({
							label: _('Upgrade'),
							callback: function() {
								item.upgrade();
							},
							defaultButton: true,
							name: 'upgrade'
						});
					}
					if (item.canInstall()) {
						_addButton({
							label: _('Install'),
							callback: function() {
								item.install();
							},
							defaultButton: true,
							name: 'install'
						});
					}
				}));
				var installationPane = new TitlePane({
					title: _('Installations throughout the domain'),
					open: false,
					content: installationTable
				});
				this._container.addChild(installationPane);
			}
		},

		openShop: function() {
			var shopUrl = this.app.shopurl || 'https://shop.univention.com';
			var w = window.open(shopUrl, '_blank');
			tools.umcpCommand('appcenter/buy', {application: this.app.id}).then(
				function(data) {
					var params = data.result;
					params.locale = kernel.locale.slice( 0, 2 ).toLowerCase();
					w.location = shopUrl + '?' + ioQuery.objectToQuery(params);
					w.focus();
				},
				function() {
					w.close();
				}
			);
		},

		disableApp: function() {
			var action = tools.umcpCommand('appcenter/enable_disable_app', {application: this.app.id, enable: false}).then(lang.hitch(this, 'reloadPage'));
			this.standbyDuring(action);
		},

		uninstallApp: function(host) {
			// before installing, user must read uninstall readme
			this.showReadme(this.app.readmeuninstall, _('Uninstall Information'), _('Uninstall')).then(lang.hitch(this, function() {
				this.callInstaller('uninstall', host).then(lang.hitch(this, function() {
					this.showReadme(this.app.readmepostuninstall, _('Uninstall Information')).then(lang.hitch(this, 'markupErrors'));
				}));
			}));
		},

		installAppDialog: function() {
			if (this._installationData) {
				var hosts = [];
				var removedDueToInstalled = [];
				var removedDueToRole = [];
				array.forEach(this._installationData, function(item) {
					if (item.canInstall()) {
						if (item.isLocal()) {
							hosts.unshift({
								label: item.displayName,
								id: item.name
							});
						} else {
							hosts.push({
								label: item.displayName,
								id: item.name
							});
						}
					} else {
						if (item.isInstalled()) {
							removedDueToInstalled.push(item.displayName);
						} else if (!item.hasFittingRole()) {
							removedDueToRole.push(item.displayName);
						}
					}
				});
				var title =_("Do you really want to %(verb)s %(ids)s?",
					{verb: _('install'), ids: this.app.name});
				this.hostDialog.reset(title, hosts, removedDueToInstalled, removedDueToRole);
				this.hostDialog.showUp().then(lang.hitch(this, function(values) {
					this.installApp(values.host);
				}));
			} else {
				this.installApp();
			}
		},

		installApp: function(host) {
			this.showReadme(this.app.licenseagreement, _('License agreement'), _('Accept license')).then(lang.hitch(this, function() {
				this.showReadme(this.app.readmeinstall, _('Install Information'), _('Install')).then(lang.hitch(this, function() {
					this.callInstaller('install', host).then(lang.hitch(this, function() {
						// put dedicated module of this app into favorites
						UMCApplication.addFavoriteModule(this.app.umc_module, this.app.umc_flavor);
						this.showReadme(this.app.readmepostinstall, _('Install Information')).then(lang.hitch(this, 'markupErrors'));
					}));
				}));
			}));
		},

		upgradeApp: function(host) {
			// before installing, user must read update readme
			this.showReadme(this.app.candidate_readmeupdate, _('Upgrade Information'), _('Upgrade')).then(lang.hitch(this, function() {
				this.callInstaller('update', host).then(lang.hitch(this, function() {
					this.showReadme(this.app.candidate_readmepostupdate, _('Upgrade Information')).then(lang.hitch(this, 'markupErrors'));
				}));
			}));
		},

		showReadme: function(readme, title, acceptButtonLabel) {
			var readmeDeferred = new Deferred();
			if (!readme) {
				readmeDeferred.resolve();
			} else {
				var buttons;
				if (acceptButtonLabel) {
					buttons = [{
						name: 'no',
						label: _('Cancel'),
						'default': true
					}, {
						name: 'yes',
						label: acceptButtonLabel
					}];
				} else {
					buttons = [{
						name: 'yes',
						label: _('Continue'),
						'default': true
					}];
				}
				var content = '<h1>' + title + '</h1>';
				content += '<div style="max-height:250px; overflow:auto;">' +
						readme +
					'</div>';
				dialog.confirm(content, buttons, title).then(function(response) {
					if (response == 'yes') {
						readmeDeferred.resolve();
					} else {
						readmeDeferred.reject();
					}
				});
			}
			return readmeDeferred;
		},

		callInstaller: function(func, host, force, deferred) {
			deferred = deferred || new Deferred();
			var nonInteractive = new Deferred();
			deferred.then(lang.hitch(nonInteractive, 'resolve'));
			var verb = '';
			var verb1 = '';
			switch(func) {
			case 'install':
				verb = _("install");
				verb1 = _("Installing");
				break;
			case 'uninstall':
				verb = _("uninstall");
				verb1 = _("Uninstalling");
				break;
			case 'update':
				verb = _("upgrade");
				verb1 = _("Upgrading");
				break;
			default:
				console.warn(func, 'is not a known function');
				break;
			}

			if (!force) {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, func);
			}

			var command = 'appcenter/invoke';
			if (!force) {
				command = 'appcenter/invoke_dry_run';
			}
			var commandArguments = {
				'function': func,
				'application': this.app.id,
				'host': host || '',
				'force': force === true
			};

			this._progressBar.reset(_('%s: Performing software tests on involved systems', this.app.name));
			this._progressBar._progressBar.set('value', Infinity); // TODO: Remove when this is done automatically by .reset()
			var invokation = tools.umcpCommand(command, commandArguments).then(lang.hitch(this, function(data) {
				var result = data.result;
				var headline = '';
				var actionLabel = tools.capitalize(verb);
				var mayContinue = true;

				if (!result.can_continue) {
					mayContinue = !result.serious_problems;
					if (mayContinue) {
						headline = _("Do you really want to %(verb)s %(ids)s?",
									{verb: verb, ids: this.app.name});
					} else {
						topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, 'cannot-continue');
						headline = _('You cannot continue');
					}
					this.detailsDialog.reset(mayContinue, headline, actionLabel);
					this.detailsDialog.showHardRequirements(result.invokation_forbidden_details, this);
					this.detailsDialog.showSoftRequirements(result.invokation_warning_details, this);
					if (result.software_changes_computed) {
						if (result.unreachable.length) {
							this.detailsDialog.showUnreachableHint(result.unreachable, result.master_unreachable);
						}
						var noHostInfo = tools.isEqual({}, result.hosts_info);
						if (func == 'update') {
							this.detailsDialog.showErrataHint();
						}
						this.detailsDialog.showPackageChanges(result.install, result.remove, result.broken, false, noHostInfo, host);
						tools.forIn(result.hosts_info, lang.hitch(this, function(host, host_info) {
							this.detailsDialog.showPackageChanges(host_info.result.install, host_info.result.remove, host_info.result.broken, !host_info.compatible_version, false, host);
						}));
					}
					nonInteractive.reject();
					this.detailsDialog.showUp().then(
						lang.hitch(this, function() {
							this.callInstaller(func, host, true, deferred);
						}),
						function() {
							deferred.reject();
						}
					);
				} else {
					var progressMessage = _("%(verb)s %(ids)s on %(host)s", {verb: verb1, ids: this.app.name, host: host || _('this host')});

					this.switchToProgressBar(progressMessage).then(function() {
						deferred.resolve();
					});
				}
			}));
			this.standbyDuring(all([invokation, deferred, nonInteractive]), this._progressBar);
			return deferred;
		},

		showLicenseRequest: function(action) {
			topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'request-license');
			if (this.udmAccessible) {
				topic.publish('/umc/license/activation');
			} else {
				// UDM is not present. Either because this is
				// not the DC Master or because the user is no
				// Administrator
				var msg;
				if (this.app.is_master) {
					var loginAsAdminTag = '<a href="javascript:void(0)" onclick="require(\'umc/app\').relogin(\'Administrator\')">Administrator</a>';
					msg =
						'<p>' + _('You need to request and install a new license in order to use the Univention App Center.') + '</p>' +
						'<p>' + _('To do this please log in as %s and repeat the steps taken until this dialog. You will be guided through the installation.', loginAsAdminTag) + '</p>';
				} else {
					var hostLink;
					if (tools.status('username') == 'Administrator') {
						hostLink = '<a href="javascript:void(0)" onclick="require(\'umc/tools\').openRemoteSession(\'' + this.app.host_master + '\')">' + this.app.host_master + '</a>';
					} else {
						hostLink = '<a target="_blank" href="https://' + this.app.host_master + '/univention-management-console">' + this.app.host_master + '</a>';
					}
					var dialogName = _('Activation of UCS');
					msg =
						'<p>' + _('You need to request and install a new license in order to use the Univention App Center.') + '</p>' +
						'<p>' + _('To do this please log in on %(host)s as an administrator. Click on the gear-wheel symbol in the top right line of the screen and choose "%(dialogName)s". There you can request the new license.', {host: hostLink, dialogName: dialogName}) + '</p>' +
						'<p>' + _('After that you can "%(action)s" "%(app)s" here on this system.', {action: action, app: this.app.name}) + '</p>';
				}
				dialog.alert(msg);
			}
		},

		switchToProgressBar: function(msg, keepAlive) {
			var deferred = new Deferred();
			// One request needs to be active otherwise
			// module might be killed if user logs out
			// during installation: dpkg will be in a
			// broken state, Bug #30611.
			// dont handle any errors. a timeout is not
			// important. this command is just for the module
			// to stay alive
			if (keepAlive !== false) {
				tools.umcpCommand('appcenter/keep_alive', {}, false);
			}
			msg = msg || _('Another package operation is in progress.');
			this._progressBar.reset(msg);
			this._progressBar.auto('appcenter/progress',
				{},
				lang.hitch(deferred, 'resolve'),
				undefined,
				undefined,
				true
			);
			return deferred;
		},

		markupErrors: function() {
			var installMasterPackagesOnHostFailedRegex = (/Installing extension of LDAP schema for (.+) seems to have failed on (DC Master|DC Backup) (.+)/);
			var errors = array.map(this._progressBar._errors, function(error) {
				var match = installMasterPackagesOnHostFailedRegex.exec(error);
				if (match) {
					var component = match[1];
					var role = match[2];
					var host = match[3];
					error = '<p>' + _('Installing the extension of the LDAP schema on %s seems to have failed.', '<strong>' + host + '</strong>') + '</p>';
					if (role == 'DC Backup') {
						error += '<p>' + _('If everything else went correct and this is just a temporary network problem, you should execute %s as root on that backup system.', '<pre>univention-add-app ' + component + ' -m</pre>') + '</p>';
					}
					error += '<p>' + _('Further information can be found in the following log file on each of the involved systems: %s', '<br /><em>/var/log/univention/management-console-module-appcenter.log</em>') + '</p>';
				}
				return error;
			});
			this._progressBar._errors = errors;
			this._progressBar.stop(lang.hitch(this, 'restartOrReload'), undefined, true);
		},

		updateApplications: function() {
			// Is overwritten with AppCenterPage.updateApplications
			var deferred = new Deferred();
			deferred.resolve();
			return deferred;
		},

		restartOrReload: function() {
			tools.defer(lang.hitch(this, function() {
				// update the list of apps
				if (this.udmAccessible) {
					require(['umc/modules/udm/cache'], function(cache) {
						cache.reset();
					});
				}
				var reloadPage = this.updateApplications().then(lang.hitch(this, function() {
					return this.reloadPage();
				}));
				var reloadModules = UMCApplication.reloadModules();
				this.standbyDuring(all([reloadPage, reloadModules]));
			}), 100);
			tools.askToReload();
		},

		_detailFieldCustomUsage: function() {
			var txts = [];
			var is_installed = this.app.is_installed;
			var useractivationrequired = this.app.useractivationrequired;
			var webinterface = this.app.webinterface;
			var webinterfacename = this.app.webinterfacename || this.app.name;
			var umcmodulename = this.app.umcmodulename;
			var umcmoduleflavor = this.app.umcmoduleflavor;
			var module = UMCApplication.getModule(umcmodulename, umcmoduleflavor);
			if (is_installed && useractivationrequired) {
				var domain_administration_link = _('Domain administration');
				if (UMCApplication.getModule('udm', 'users/user')) {
					domain_administration_link = lang.replace('<a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'udm\', \'users/user\')">{name}</a>', {name : domain_administration_link});
				}
				txts.push(_('Users need to be modified in the %s in order to use this service.', domain_administration_link));
			}
			if (module) {
				var module_link = lang.replace('<a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'{umcmodulename}\', {umcmoduleflavor})">{name}</a>', {
					umcmodulename: umcmodulename,
					umcmoduleflavor: umcmoduleflavor ? '\'' + umcmoduleflavor + '\'' : 'undefined',
					name: module.name
				});
				txts.push(_('A module for the administration of the app is available: %s.', module_link));
			}
			if (is_installed && webinterface) {
				var webinterface_link = lang.replace('<a href="{webinterface}" target="_blank">{name}</a>', {
					webinterface: webinterface,
					name: webinterfacename
				});
				txts.push(_('The app provides a web interface: %s.', webinterface_link));
			}
			if (txts.length) {
				return txts.join(' ');
			}
		},

		_detailFieldCustomCandidateVersion: function() {
			var version = this.app.version;
			var candidate_version = this.app.candidate_version;
			var is_installed = this.app.is_installed;
			if (candidate_version) {
				return candidate_version;
			}
			if (! is_installed) {
				return version;
			}
		},

		_detailFieldCustomVersion: function() {
			var version = this.app.version;
			var is_installed = this.app.is_installed;
			if (is_installed) {
				return version;
			}
		},

		_detailFieldCustomWebsite: function() {
			var name = this.app.name;
			var website = this.app.website;
			if (name && website) {
				return '<a href="' + website + '" target="_blank">' + name + '</a>';
			}
		},

		_detailFieldCustomSupportURL: function() {
			var supportURL = this.app.supporturl;
			if (supportURL) {
				if (supportURL == 'None') {
					return _('No support option provided');
				}
				return '<a href="' + supportURL + '" target="_blank">' + _('Available support options') + '</a>';
			} else {
				if (this.app.maintainer && this.app.maintainer !== this.app.vendor) {
					return _('Please contact the maintainer of the application');
				} else {
					return _('Please contact the vendor of the application');
				}
			}
		},

		_detailFieldCustomVendor: function() {
			var vendor = this.app.vendor;
			var website = this.app.websitevendor;
			if (vendor && website) {
				return '<a href="' + website + '" target="_blank">' + vendor + '</a>';
			} else if (vendor) {
				return vendor;
			}
		},

		_detailFieldCustomMaintainer: function() {
			var maintainer = this.app.maintainer;
			var vendor = this.app.vendor;
			if (vendor == maintainer) {
				return null;
			}
			var website = this.app.websitemaintainer;
			if (maintainer && website) {
				return '<a href="' + website + '" target="_blank">' + maintainer + '</a>';
			} else if (maintainer) {
				return maintainer;
			}
		},

		_detailFieldCustomContact: function() {
			var contact = this.app.contact;
			if (contact) {
				return '<a href="mailto:' + contact + '">' + contact + '</a>';
			}
		},

		_detailFieldCustomNotifyVendor: function() {
			if (this.app.withoutrepository) {
				// without repository: Uses UCS repository:
				//   strictly speaking, we get the information
				//   about installation by some access logs
				//   (although this is not sent on purpose)
				return null;
			}
			var maintainer = this.app.maintainer && this.app.maintainer != this.app.vendor;
			if (this.app.notifyvendor) {
				if (maintainer) {
					return _('This application will inform the maintainer if you (un)install it.');
				} else {
					return _('This application will inform the vendor if you (un)install it.');
				}
			} else {
				if (maintainer) {
					return _('This application will not inform the maintainer if you (un)install it.');
				} else {
					return _('This application will not inform the vendor if you (un)install it.');
				}
			}
		},

		_detailFieldCustomEndOfLife: function() {
			if (this.app.endoflife) {
				var warning = _('This application will not get any further updates. We suggest to uninstall %(app)s and search for an alternative application.', {app: this.app.name});
				if (this.app.is_current) {
					warning += ' ' + _('Click on "%(button)s" if you want to continue running this application at your own risk.', {button: _('Continue using')});
				}
				return warning;
			}
		},

		_detailFieldCustomScreenshot: function() {
			if (this.app.screenshot) {
				return lang.replace('<img src="{url}" style="max-width: 90%; height:200px;" class="umcScreenshot" />', {
					url: this.app.screenshot,
					id: this.id
				});
			}
		},

		addToDetails: function(label, attribute) {
			var value;
			var detailFunc = this['_detailFieldCustom' + attribute];
			if (detailFunc) {
				value = lang.hitch(this, detailFunc)();
			}
			if (! value) {
				return;
			}
			var tr = domConstruct.create('tr', {}, this._detailsTable);
			domConstruct.create('td', {innerHTML: label, style: {verticalAlign: 'top'}}, tr);
			if (typeof value == 'string') {
				domConstruct.create('td', {innerHTML: value}, tr);
			} else {
				// value is a DOM node
				var td = domConstruct.create('td', {}, tr);
				domConstruct.place(value, td, 'only');
			}
		},

		onBack: function() {
		}

	});
});

