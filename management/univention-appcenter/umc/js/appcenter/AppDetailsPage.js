/*
 * Copyright 2013-2022 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/when",
	"dojo/io-query",
	"dojo/topic",
	"dojo/Deferred",
	"dojo/dom-construct",
	"dojo/dom-class",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojox/html/entities",
	"umc/app",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ProgressBar",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/widgets/Grid",
	"umc/modules/appcenter/AppInfo",
	"umc/modules/appcenter/AppMoreInfo",
	"umc/modules/appcenter/Buy",
	"umc/modules/appcenter/Badges",
	"umc/modules/appcenter/Vote",
	"umc/modules/appcenter/App",
	"umc/modules/appcenter/ImageGallery",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, kernel, array, when, ioQuery, topic, Deferred, domConstruct, domClass, Memory, Observable, entities, UMCApplication, tools, dialog, ContainerWidget, ProgressBar, Page, Text, Button, Grid, AppInfo, AppMoreInfo, Buy, Badges, Vote, App, ImageGallery, _) {

	return declare("umc.modules.appcenter.AppDetailsPage", [ Page ], {
		appLoadingDeferred: null,
		standbyDuring: null, // parents standby method must be passed. weird IE-Bug (#29587)
		standby: null,

		headerTextAllowHTML: false,
		helpTextAllowHTML: false,

		title: _("App management"),
		moduleTitle: null,
		noFooter: true,
		getAppCommand: 'appcenter/get',

		fullWidth: true,

		backLabel: _('Back to overview'),
		detailsDialog: null,
		configDialog: null,

		// For tracking of interaction with the "Suggestions based on installed apps" category
		fromSuggestionCategory: false,

		appCenterInformation: _('<p>Univention App Center is designed for easy and comfortable administration of Apps. It uses online services provided by Univention, for example, for downloading Apps, descriptions or graphics, or for the search function.</p><p>By using Univention App Center, you agree that originating user data may be stored and evaluated by Univention for product improvements as well as market research purposes. Usage data consists of information such as installing / uninstalling Apps or search queries. These will be transmitted to Univention together with a unique identification of the UCS system.</p><p>When installing and uninstalling some Apps, the App provider will be notified of the operation. The e-mail address used to activate the system is transferred to the provider. Other than that, no transfer of personal or individually assignable data is made to third parties.</p><p>'),
		appCenterInformationReadAgain: _('<p><b>Note:</b> This information has been updated. Please read it again.</p>'),

		postMixInProperties: function() {
			this.inherited(arguments);

			this.appLoadingDeferred = new Deferred();
			this._progressBar = new ProgressBar({});
			this.own(this._progressBar);
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcAppDetailsPage');
		},

		// The parameter "track" can be specified by adding an additional parameter
		// to the call of set(). e.g. "appDetailsPage.set('app', app, false);"
		_setAppAttr: function(app, track) {
			track = track !== false;
			this._set('app', app);
			if (this.appLoadingDeferred.isFulfilled()) {
				this.appLoadingDeferred = new Deferred();
			}
			var appLoaded = app;
			if (!app.fullyLoaded) {
				// app is just {id: '...'}!
				// we need to ask the server,
				// it is not yet known!
				appLoaded = tools.umcpCommand(this.getAppCommand, {'application': app.id}).then(function(data) {
					return new App(data.result);
				});
			}
			when(appLoaded).then(lang.hitch(this, function(loadedApp) {
				if (loadedApp === null) {
					this.onBack();
					this.appLoadingDeferred.reject();
					return;
				}
				if (track && !loadedApp.isInstalledInDomain()) {
					tools.umcpCommand('appcenter/track', {app: loadedApp.id, action: 'get'});
				} else {
					tools.umcpCommand('appcenter/ping');
				}
				this._set('app', loadedApp);
				this._configureDialogs(loadedApp);
				this._renderPage();
				this.set('moduleTitle', loadedApp.name);
				this.appLoadingDeferred.resolve();
			}));
		},

		_configureDialogs: function(app) {
			this.detailsDialog.set('app', app);
			this.configDialog.set('app', app);
			// this.installDialog.set('app', app);
		},

		_setModuleTitleAttr: function(name) {
			this._set('moduleTitle', name);
			this.moduleTitle = name;
		},

		_appIsInstalledInDomain: function() {
			return this._appCountInstallations() > 0;
		},

		_appCountInstallations: function() {
			var sum = 0;
			array.forEach(this.app.installationData, function(item) {
				sum += item.isInstalled;
			});
			return sum;
		},

		vote: function(voteElement) {
			tools.umcpCommand('appcenter/track', {app: this.app.id, action: 'vote'}).then(lang.hitch(this, function() {
				dialog.notify(_('Quick and easy – your ballot has been cast.'), _('Vote for App'));
				if (voteElement) {
					voteElement.hideButton();
				}
			}));
		},

		reloadPage: function() {
			return when(this.updateApplications(false), (apps) => {
				let app = {id: this.app.id}; // fallback: reset same app, but only pass the id => loads new from server
				app = apps.find((_app) => _app.id == app.id) || app
				this.set('app', app, false);
				return this.appLoadingDeferred;
			});
		},

		getButtons: function() {
			var buttons = [];
			if (this.app.canOpenInDomain() && this.app.isInstalled) {
				buttons.push({
					name: 'open',
					label: this.app.getOpenLabel(),
					defaultButton: true,
					'class': 'umcAppButton',
					callback: lang.hitch(this.app, 'open')
				});
			} else if (this.app.canInstall() && !this.app.isInstalled) {
				buttons.push({
					name: 'install',
					label: _('Install'),
					'class': 'umcAppButton',
					callback: lang.hitch(this, 'installAppDialog')
				});
			}

			if (this.app.useShop) {
				buttons.push({
					name: 'shop',
					label: _('Buy'),
					'class': 'umcAppButton',
					callback: lang.hitch(this, 'openShop')
				});
			}
			return buttons;
		},

		getHeaderButtons: function() {
			var buttons = [{
				name: 'close',
				label: this.backLabel,
				align: 'left',
				callback: lang.hitch(this, 'onBack')
			}];

			if (this.visibleApps && this.visibleApps.length) {
				var currentIndex = -1;
				array.some(this.visibleApps, lang.hitch(this, function(iapp, idx) {
					currentIndex = iapp.id === this.app.id ? idx : undefined;
					return currentIndex >= 0;
				}));
				var prevApp = this.visibleApps[currentIndex - 1];
				var nextApp = this.visibleApps[currentIndex + 1];
				if (nextApp || prevApp) {
					buttons.push({
						name: 'prev',
						label: _('Previous app'),
						align: 'left',
						disabled: !prevApp,
						callback: lang.hitch(this, 'set', 'app', prevApp)
					});
					buttons.push({
						name: 'next',
						label: _('Next app'),
						align: 'left',
						disabled: !nextApp,
						callback: lang.hitch(this, 'set', 'app', nextApp)
					});
				}
			}
			return buttons;
		},

		getActionButtons: function(additionalCallback) {
			var buttons = [];
			if (this.app.canInstallInDomain()) {
				buttons.push({
					name: 'install',
					label: _('Install'),
					'class': 'umcAppButton umcActionButton',
					isStandardAction: true,
					isContextAction: false,
					callback: lang.hitch(this, function() {
						additionalCallback();
						topic.publish('/appcenter/run/install', [this.app.id], null, this.fromSuggestionCategory, this);
					})
				});
			}
			if (this.app.canOpenInDomain()) {
				buttons.push({
					name: 'open',
					label: this.app.getOpenLabel(),
					'class': 'umcAppButton umcAppButtonFirstRow',
					isContextAction: true,
					isStandardAction: false,
					canExecute: lang.hitch(this, function(app) {
						return app.data.canOpen();
					}),
					callback: lang.hitch(this, function(host, app) {
						additionalCallback();
						app[0].data.open();
					})
				});
			}
			if (this.app.canDisableInDomain()) {
				buttons.push({
					name: 'disable',
					label: _('Continue using'),
					'class': 'umcAppButton umcActionButton',
					isContextAction: true,
					isStandardAction: false,
					canExecute: lang.hitch(this, function(app) {
						return app.data.canDisable();
					}),
					callback: lang.hitch(this, function(host, app) {
						additionalCallback();
						this.disableApp(host, app);
					})
				});
			}
			if (this.app.hasConfiguration()) {
				buttons.push({
					name: 'configure',
					label: _('App settings'),
					'class': 'umcAppButton umcActionButton',
					isContextAction: true,
					isStandardAction: false,
					canExecute: lang.hitch(this, function(app) {
						return app.data.canConfigure();
					}),
					callback: lang.hitch(this, function() {
						additionalCallback();
						this.configureApp();
					})
				});
			}
			var callback;
			if (this.app.canUninstallInDomain()) {
				callback = lang.hitch(this, function(host, rows) {
					additionalCallback();
					topic.publish('/appcenter/run/remove', [this.app.id], Object.fromEntries(rows.map((row) => [row.id, [row.data.id]])), null, this);
				});
				buttons.push({
					name: 'uninstall',
					label: _('Uninstall'),
					isContextAction: true,
					isMultiAction: true,
					isStandardAction: false,
					'class': 'umcAppButton umcActionButton',
					canExecute: lang.hitch(this, function(app) {
						return app.data.canUninstall();
					}),
					callback: callback
				});
			}
			if (this.app.canUpgradeInDomain()) {
				callback = lang.hitch(this, function(host, rows) {
					additionalCallback();
					topic.publish('/appcenter/run/upgrade', [this.app.id], Object.fromEntries(rows.map((row) => [row.id, [row.data.id]])), null, this);
				});
				buttons.push({
					name: 'update',
					label: _('Upgrade'),
					isContextAction: true,
					isMultiAction: true,
					isStandardAction: false,
					canExecute: lang.hitch(this, function(app) {
						return app.data.canUpgrade();
					}),
					callback: callback
				});
			}
			return buttons;
		},

		_renderPage: function() {
			this.set('headerButtons', this.getHeaderButtons());
			this._renderMainContainer();
		},

		_renderMainContainer: function() {
			if (this._mainRegionContainer) {
				this.removeChild(this._mainRegionContainer);
				this._mainRegionContainer.destroyRecursive();
				this._mainRegionContainer = null;
			}
			this._mainRegionContainer = new ContainerWidget({
				'class': 'umcAppDetailsPage__content'
			});
			this.addChild(this._mainRegionContainer);

			var isAppInstalled = this.app.isInstalled || this.app.getHosts().length > 0;
			this._renderContent(isAppInstalled);
		},

		_renderImageGallery: function(parentContainer) {
			if (this.app.thumbnails.length) {
				parentContainer.addChild(new ImageGallery({
					'class': 'umcAppDetailsPage__content__imageGallery',
					srcs: this.app.thumbnails
				}));
			}
		},

		_renderMainInfo: function(parentContainer, isAppInstalled) {
			var detailsContainer = new ContainerWidget({
				'class': 'umcAppDetailsPage__content__mainInfo'
			});
			if (isAppInstalled) {
				this._renderAppUsage(detailsContainer);
			}
			this._renderDescription(detailsContainer, isAppInstalled);
			parentContainer.addChild(detailsContainer);
		},

		_renderContent: function(isAppInstalled) {
			var parentContainer = this._mainRegionContainer;
			this._renderCallToAction(parentContainer);
			this._renderImageGallery(parentContainer);
			this._renderMainInfo(parentContainer, isAppInstalled);
			this._renderSupplementaryInfo(parentContainer);
		},

		_renderAppUsage: function(parentContainer) {
			var appUsageContainer = ContainerWidget({
				'style': 'margin-bottom: 2em'
			});

			var usage = this.app.readme;
			if (usage) {
				usage = lang.replace(usage, lang.hitch(this, function(p, id) { return entities.encode(this.app[id]); }));
			} else {
				usage = this._detailFieldCustomUsage();
			}
			if (usage) {
				var usageHeader = new Text({
					content: _('First steps'),
					'class': 'mainHeader'
				});
				appUsageContainer.addChild(usageHeader);

				var usagePane = new Text({
					content: usage,
				});
				appUsageContainer.addChild(usagePane);

				parentContainer.addChild(appUsageContainer);
			}
		},

		_renderInstallationManagement: function(parentContainer, additionalCallback) {
			var actions = this.getActionButtons(additionalCallback);
			this._renderDomainwideManagement(parentContainer, actions);
			return actions;
		},

		_renderDomainwideManagement: function(parentContainer, actions) {
			var columns = [{
				name: 'server',
				label: _('Server')
			}, {
				name: 'appStatus',
				label: _('Status')
			}];

			var myStore = new Observable(new Memory({
				data: this.app.getHosts()
			}));
			this._installedAppsGrid = new Grid({
				hideContextActionsWhenNoSelection: false,
				actions: actions,
				columns: columns,
				moduleStore: myStore,
				'class': 'umcGridOnContainer',
			});
			parentContainer.addChild(this._installedAppsGrid);
			parentContainer.own(this._installedAppsGrid);
		},

		_renderDescription: function(parentContainer, isAppInstalled) {
			if (isAppInstalled) {
				var header = new Text({
					content: _('Details'),
					'class': 'mainHeader'
				});
				parentContainer.addChild(header);
				parentContainer.own(header);
			}
			var descriptionContainer = new ContainerWidget({});
			domClass.add(domConstruct.create('div', {
				innerHTML: this.app.longDescription  // no HTML escape!
			}, descriptionContainer.domNode));
			parentContainer.addChild(descriptionContainer);

		},

		_renderSupplementaryInfo: function(parentContainer) {
			var container = new ContainerWidget({
				'class': 'umcAppDetailsPage__content__supplementaryInfo'
			});
			if (this.app.canVote()) {
				this._renderAppVote(container);
			} else {
				if (this.app.useShop) {
					container.addChild(new Buy({
						callback: lang.hitch(this, 'openShop')
					}));
				}
				this._renderAppDetails(container);
			}
			var hasRating = array.some(this.app.rating, function(rating) { return rating.value; });
			if (hasRating) {
				this._renderAppBadges(container);
			}
			parentContainer.addChild(container);
		},

		_renderCallToAction: function(parentContainer) {
			var isSingleServerDomain = this.app.installationData.length === 1;
			var buttonLabel = "";
			var callback;
			if (isSingleServerDomain) {
				if (this.app.canInstall()) {
					buttonLabel = _("Install");
					callback = lang.hitch(this, 'installAppDialog')
				} else if (this.app.isInstalled) {
					buttonLabel = _("Manage installation");
					callback = lang.hitch(this, '_openManageDialog');
				}
			} else {
				if (this.app.isInstalledInDomain()) {
					buttonLabel = _("Manage installations");
					callback = lang.hitch(this, '_openManageGridDialog');
				} else if (this.app.canInstallInDomain()) {
					buttonLabel = _("Install");
					callback = lang.hitch(this, 'installAppDialog');
				}
			}
			var info = new AppInfo({
				bgc: this.app.backgroundColor || "",
				logo: '/univention/js/dijit/themes/umc/icons/scalable/' + this.app.logoName,
				name: this.app.name,
				description: this.app.description,
				buttonLabel: buttonLabel,
				callback: callback,
				'class': 'umcAppDetailsPage__content__callToAction'
			});
			parentContainer.addChild(info);
		},

		_openManageDialog: function() {
			var container = new ContainerWidget({
				'class': 'umcManageAppInstallationsDialogButtons'
			});
			if (this.app.canUpgrade()) {
				container.addChild(new Button({
					label: _('Upgrade'),
					'class': 'ucsPrimaryButton',
					callback: lang.hitch(this, function() {
						deferred.dialog.onConfirm();
						const localhost = tools.status('fqdn');
						topic.publish('/appcenter/run/upgrade', [this.app.id], { [localhost]: [this.app.id] }, null, this);
					})
				}));
			}
			if (this.app.canOpen()) {
				if (this.canUpgrade) {
					classes = '';
				} else {
					classes = 'ucsPrimaryButton';
				}
				container.addChild(new Button({
					label: _('Open'),
					'class': classes,
					callback: lang.hitch(this, function() {
						deferred.dialog.onConfirm();
						this.app.open();
					})
				}));
			}
			if (this.app.canDisable()) {
				container.addChild(new Button({
					label: _('Continue using'),
					callback: lang.hitch(this, function() {
						deferred.dialog.onConfirm();
						this.disableApp();
					})
				}));
			}
			if (this.app.hasConfiguration()) {
				container.addChild(new Button({
					label: _('App settings'),
					callback: lang.hitch(this, function() {
						deferred.dialog.onConfirm();
						this.configureApp();
					})
				}));
			}
			if (this.app.canUninstall()) {
				container.addChild(new Button({
					label: _('Uninstall'),
					callback: lang.hitch(this, function() {
						deferred.dialog.onConfirm();
						const localhost = tools.status("fqdn");
						topic.publish('/appcenter/run/remove', [this.app.id], { [localhost]: [this.app.id] }, null, this);
					})
				}));
			}
			var options = [];
			var deferred = dialog.confirm(container, options, _("Manage installation"));
		},

		_openManageGridDialog: function() {
			var container = new ContainerWidget({});
			var options = [];
			var deferred = dialog.confirm(container, options, _("Manage installations"));
			var actions = this._renderInstallationManagement(container, deferred.dialog.onConfirm);
			deferred.dialog._position(); // FIXME use of private function. needed because content is added to dialog after creation
		},

		_renderAppVote: function(parentContainer) {
			var vote = new Vote({});
			vote.callback = lang.hitch(this, 'vote', vote);
			parentContainer.addChild(vote);
		},

		_addBuyableAppInfo: function(parentContainer) {
			// TODO: should go into Buy({})
			domConstruct.create('span', {
				'class': 'appDetailsSidebarText',
				innerHTML: _('Buy %(appName)s to install version %(candidateVersion)s.',
						{appName: this.app.name, candidateVersion: this.app.candidateVersion || this.app.version})
			}, parentContainer.domNode);

			if (this.app.candidateInstallPermissionMessage) {
				domConstruct.create('span', {
					'class': 'appDetailsSidebarText',
					innerHTML: this.app.candidateInstallPermissionMessage
				}, parentContainer.domNode);
			}
		},

		_renderAppDetails: function(parentContainer) {
			var moreInfo = new AppMoreInfo({});
			moreInfo.addInfo(_('Vendor'), this.detailsValue('Vendor'));
			moreInfo.addInfo(_('Provider'), this.detailsValue('Maintainer'));
			moreInfo.addInfo(_('Contact'), this.detailsValue('Contact'));
			moreInfo.addInfo(_('License'), this.detailsValue('License'));
			if (this.app.isInstalled) {
				moreInfo.addInfo(_('Version'), this.detailsValue('Version'));
				moreInfo.addInfo(_('Available'), this.detailsValue('CandidateVersion'));
			} else {
				moreInfo.addInfo(_('Version'), this.detailsValue('CandidateVersion'));
			}
			moreInfo.addInfo(_('Support'), this.detailsValue('SupportURL'));
			moreInfo.addInfo(_('Notification'), this.detailsValue('NotifyVendor'));
			parentContainer.addChild(moreInfo);
		},

		_renderAppBadges: function(parentContainer) {
			var badges = new Badges({});
			parentContainer.addChild(badges);
			array.forEach(this.app.rating, function(rating) {
				badges.addBadge(rating.name, rating.description);
			});
		},

		openShop: function() {
			var shopUrl = this.app.shopURL || 'https://shop.univention.com';
			var w = window.open(shopUrl, '_blank');
			tools.umcpCommand('appcenter/track', {app: this.app.id, action: 'buy'});
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

		disableApp: function(host, app) {
			var action = tools.umcpCommand('appcenter/enable_disable_app', {application: app[0].data.id, enable: false}).then(lang.hitch(this, 'reloadPage'));
			this.standbyDuring(action);
		},

		configureApp: function() {
			this.configDialog.showUp();
		},

		installAppDialog: function() {
			if (this.fromSuggestionCategory) {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, `installFromSuggestion`);
			} else {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, 'install');
			}

			topic.publish('/appcenter/run/install', [this.app.id], null, this.fromSuggestionCategory, this);
		},

		showReadme: function(readme, title, acceptButtonLabel, cancelButtonLabel) {
			var readmeDeferred = new Deferred();
			if (cancelButtonLabel === undefined) {
				cancelButtonLabel = _('Cancel');
			}
			if (!readme) {
				readmeDeferred.resolve();
			} else {
				var buttons;
				if (acceptButtonLabel) {
					buttons = [];
					if (cancelButtonLabel) {
						buttons.push({
							name: 'no',
							label: cancelButtonLabel,
							'default': true
						});
					}
					buttons.push({
						name: 'yes',
						label: acceptButtonLabel,
						'default': !cancelButtonLabel
					});
				} else {
					buttons = [{
						name: 'yes',
						label: _('Continue'),
						'default': true
					}];
				}
				var content = '<div style="max-height:250px; overflow:auto;">' +
						readme +  // no HTML escape!
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

		showLicenseAgreement: function() {
			return this.showReadme(this.app.licenseAgreement, _('License agreement'), _('Close'), null);
		},

		updateApplications: function() {
			// Is overwritten with AppCenterPage.updateApplications
			var deferred = new Deferred();
			deferred.resolve([]);
			return deferred;
		},

		_detailFieldCustomUsage: function() {
			var txts = [];
			var is_installed = this.app.isInstalled;
			var useractivationrequired = this.app.userActivationRequired;
			if (is_installed && useractivationrequired) {
				var domain_administration_link = _('Domain administration');
				if (UMCApplication.getModule('udm', 'users/user')) {
					domain_administration_link = lang.replace('<a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'udm\', \'users/user\')">{name}</a>', {name : domain_administration_link});
				}
				txts.push(_('Users need to be modified in the %s in order to use this service.', domain_administration_link));
			}
			var moduleLink = this.app.getModuleLink();
			if (moduleLink) {
				txts.push(_('A module for the administration of the app is available: %s.', moduleLink));
			}
			var webInterface = this.app.getWebInterfaceTag();
			if (webInterface) {
				txts.push(_('The app provides a web interface: %s.', webInterface));
			}
			if (this.app.isDocker) {
				txts.push(_('%(name)s uses a container technology for enhanced security and compatibility.', {name: entities.encode(this.app.name)}));
			}
			if (txts.length) {
				return txts.join(' ');
			}
		},

		_detailFieldCustomCandidateVersion: function() {
			var version = this.app.version;
			var candidate_version = this.app.candidateVersion;
			var is_installed = this.app.isInstalled;
			if (candidate_version) {
				return candidate_version;
			}
			if (! is_installed) {
				return version;
			}
		},

		_detailFieldCustomVersion: function() {
			var version = this.app.version;
			var is_installed = this.app.isInstalled;
			if (is_installed) {
				return entities.encode(version);
			}
		},

		_detailFieldCustomLicense: function() {
			var licenseAgreement = this.app.licenseAgreement;
			var license = this.app.licenseDescription;
			if (license) {
				license = entities.encode(license);
				if (licenseAgreement) {
					license += lang.replace(' (<a href="javascript:void(0)" onclick="require(\'dijit/registry\').byId(\'{id}\').showLicenseAgreement();">' + _('Read license agreement') + '</a>)', {
						id: this.id
					});
				}
			} else {
				if (licenseAgreement) {
					license = lang.replace('<a href="javascript:void(0)" onclick="require(\'dijit/registry\').byId(\'{id}\').showLicenseAgreement();">' + _('Read license agreement') + '</a>', {
						id: this.id
					});
				} else if (license === null) {
					license = _('The App does not provide any information about the license. Please contact the App provider for further details.');
				}
			}
			return license;
		},

		_detailFieldCustomWebsite: function() {
			var name = this.app.name;
			var website = this.app.website;
			if (name && website) {
				return '<a href="' + entities.encode(website) + '" target="_blank">' + entities.encode(name) + '</a>';
			}
		},

		_detailFieldCustomSupportURL: function() {
			var supportURL = this.app.supportURL;
			if (supportURL) {
				if (supportURL == 'None') {
					return _('No support option provided');
				}
				return '<a href="' + entities.encode(supportURL) + '" target="_blank">' + _('Available support options') + '</a>';
			} else {
				return _('Please contact the provider of the App');
			}
		},

		_detailFieldCustomVendor: function() {
			var vendor = this.app.vendor;
			var website = this.app.websiteVendor;
			if (vendor && website) {
				return '<div><a href="' + entities.encode(website) + '" target="_blank">' + entities.encode(vendor) + '</a></div>';
			} else if (vendor) {
				return '<div>' + entities.encode(vendor) + '</div>';
			}
		},

		_detailFieldCustomMaintainer: function() {
			var maintainer = this.app.maintainer;
			var website = this.app.websiteMaintainer;
			if (maintainer && website) {
				return '<a href="' + entities.encode(website) + '" target="_blank">' + entities.encode(maintainer) + '</a>';
			} else if (maintainer) {
				return '<div>' + entities.encode(maintainer) + '</div>';
			}
		},

		_detailFieldCustomContact: function() {
			var contact = this.app.contact;
			if (contact) {
				return '<a href="mailto:' + entities.encode(contact) + '">' + entities.encode(contact) + '</a>';
			}
		},

		_detailFieldCustomNotifyVendor: function() {
			if (this.app.withoutRepository) {
				// without repository: Uses UCS repository:
				//   strictly speaking, we get the information
				//   about installation by some access logs
				//   (although this is not sent on purpose)
				return null;
			}
			if (this.app.notifyVendor) {
				return _('This App will inform the App provider about an (un)installation. The app provider may contact you.');
			} else {
				return _('This App will not inform the App provider about an (un)installation directly.');
			}
		},

		_detailFieldCustomEndOfLife: function() {
			if (this.app.endOfLife) {
				var warning = _('This App will not get any further updates. We suggest to uninstall %(app)s and search for an alternative App.', {app: entities.encode(this.app.name)});
				if (this.app.isCurrent) {
					warning += ' ' + _('Click on "%(button)s" if you want to continue running this App at your own risk.', {button: _('Continue using')});
				}
				return warning;
			}
		},

		detailsValue: function(attribute) {
			var detailFunc = this['_detailFieldCustom' + attribute];
			if (detailFunc) {
				return lang.hitch(this, detailFunc)();
			}
		},

		onBack: function() {
		}
	});
});

