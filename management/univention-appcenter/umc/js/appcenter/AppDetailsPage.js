/*
 * Copyright 2013-2019 Univention GmbH
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
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/_base/event",
	"dojo/promise/all",
	"dojo/json",
	"dojo/when",
	"dojo/query",
	"dojo/io-query",
	"dojo/topic",
	"dojo/Deferred",
	"dojo/dom-construct",
	"dojo/dom-class",
	"dojo/on",
	"dojo/dom-style",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/Tooltip",
	"dojox/image/LightboxNano",
	"dojox/html/entities",
	"umc/app",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/TitlePane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ProgressBar",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/widgets/CheckBox",
	"umc/widgets/Grid",
	"umc/modules/appcenter/AppCenterGallery",
	"umc/modules/appcenter/App",
	"umc/modules/appcenter/ThumbnailGallery",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, kernel, array, dojoEvent, all, json, when, query, ioQuery, topic, Deferred, domConstruct, domClass, on, domStyle, Memory, Observable, Tooltip, Lightbox, entities, UMCApplication, tools, dialog, TitlePane, ContainerWidget, ProgressBar, Page, Text, Button, CheckBox, Grid, AppCenterGallery, App, ThumbnailGallery, _) {

	var adaptedGrid = declare([Grid], {
		_updateContextActions: function() {
			this.inherited(arguments);
			domStyle.set(this._contextActionsToolbar.domNode, 'visibility', 'visible');
		}
	});

	return declare("umc.modules.appcenter.AppDetailsPage", [ Page ], {
		appLoadingDeferred: null,
		standbyDuring: null, // parents standby method must be passed. weird IE-Bug (#29587)
		'class': 'umcAppDetailsPage',
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
		isSubPage: false,

		appCenterInformation: _('<p>Univention App Center is designed for easy and comfortable administration of Apps. It uses online services provided by Univention, for example, for downloading Apps, descriptions or graphics, or for the search function.</p><p>By using Univention App Center, you agree that originating user data may be stored and evaluated by Univention for product improvements as well as market research purposes. Usage data consists of information such as installing / uninstalling Apps or search queries. These will be transmitted to Univention together with a unique identification of the UCS system.</p><p>When installing and uninstalling some Apps, the App provider will be notified of the operation. The e-mail address used to activate the system is transferred to the provider. Other than that, no transfer of personal or individually assignable data is made to third parties.</p><p>'),
		appCenterInformationReadAgain: _('<p><b>Note:</b> This information has been updated. Please read it again.</p>'),

		postMixInProperties: function() {
			this.inherited(arguments);

			this.appLoadingDeferred = new Deferred();
			this._progressBar = new ProgressBar({});
			this.own(this._progressBar);
			this._grid = new AppCenterGallery({});
			this.own(this._grid);
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
				if (track && !loadedApp.is_installed_anywhere) {
					tools.umcpCommand('appcenter/track', {app: loadedApp.id, action: 'get'});
				} else {
					tools.umcpCommand('appcenter/ping');
				}
				var app = new App(loadedApp, this);
				this._set('app', app);
				this._configureDialogs(app);
				this.renderPage();
				this.set('moduleTitle', app.name);
				this.appLoadingDeferred.resolve();
			}));
		},

		_configureDialogs: function(app) {
			this.hostDialog.set('app', app);
			this.detailsDialog.set('app', app);
			this.configDialog.set('app', app);
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

		reloadPage: function() {
			// reset same app, but only pass the id => loads new from server
			this.set('app', {id: this.app.id}, false);
			return this.appLoadingDeferred;
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
			} else if (this.app.canInstall && !this.app.isInstalled) {
				buttons.push({
					name: 'install',
					label: _('Install'),
					'class': 'umcAppButton',
					callback: lang.hitch(this.app, 'install')
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

		getActionButtons: function(isSingleServerInstallation) {
			var buttons = [];
			if (this.app.canInstallInDomain()) {
				buttons.push({
					name: 'install',
					label: _('Install'),
					'class': 'umcAppButton umcActionButton',
					isStandardAction: true,
					isContextAction: false,
					callback: lang.hitch(this.app, 'install')
				});
			}
			if (this.app.canOpenInDomain() && !isSingleServerInstallation) {
				buttons.push({
					name: 'open',
					label: this.app.getOpenLabel(),
					'class': 'umcAppButton umcAppButtonFirstRow',
					isContextAction: true,
					isStandardAction: true,
					canExecute: lang.hitch(this, function(app) {
						return app.data.canOpen();
					}),
					callback: lang.hitch(this, function(host, app) {
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
					isStandardAction: true,
					canExecute: lang.hitch(this, function(app) {
						return app.data.canDisable();
					}),
					callback: lang.hitch(this, 'disableApp')
				});
			}
			if (this.app.hasConfiguration()) {
				buttons.push({
					name: 'configure',
					label: _('App settings'),
					'class': 'umcAppButton umcActionButton',
					isContextAction: true,
					isStandardAction: true,
					canExecute: lang.hitch(this, function(app) {
						return app.data.canConfigure();
					}),
					callback: lang.hitch(this, 'configureApp')
				});
			}
			var callback;
			if (this.app.canUninstallInDomain()) {
				if (isSingleServerInstallation) {
					callback = lang.hitch(this.app, 'uninstall');
				} else {
					callback = lang.hitch(this, function(host, app) {
						app[0].data.uninstall();
					});
				}
				buttons.push({
					name: 'uninstall',
					label: _('Uninstall'),
					isContextAction: true,
					isStandardAction: true,
					'class': 'umcAppButton umcActionButton',
					canExecute: lang.hitch(this, function(app) {
						return app.data.canUninstall();
					}),
					callback: callback
				});
			}
			if (this.app.canUpgradeInDomain()) {
				if (isSingleServerInstallation) {
					callback = lang.hitch(this.app, 'upgrade');
				} else {
					callback = lang.hitch(this, function(host, app) {
						app[0].data.upgrade();
					});
				}
				buttons.push({
					name: 'update',
					label: _('Upgrade'),
					isContextAction: true,
					isStandardAction: true,
					canExecute: lang.hitch(this, function(app) {
						return app.data.canUpgrade();
					}),
					callback: callback
				});
			}
			return buttons;
		},

		renderPage: function() {
			this._renderIcon();
			this._renderNavContainer();
			this._renderMainContainer();
			this._renderFooter();
		},

		_renderIcon: function() {
			if (this._icon) {
				this.removeChild(this._icon);
				this._icon.destroyRecursive();
				this._icon = null;
			}
			var iconName = this.app.logoDetailPageName || this.app.logoName;
			var icon_class = this._grid.getIconClass(iconName);
			if (icon_class) {
				this._icon = new ContainerWidget({
					region: 'nav',
					'class': icon_class + ' icon'
				});
				this.addChild(this._icon, 0);
			}
		},

		_renderNavContainer: function() {
			if (this._navContainer) {
				this.removeChild(this._navContainer);
				this._navContainer = null;
			}
			this._navContainer = new ContainerWidget({
				region: 'nav',
				'class': 'navContainer'
			});

			// build Text Widget for HeaderDetails
			var _navHeaderDetails = new Text({
				'class': 'umcAppStatusText'
			});

			// vendor
			var vendor = this._detailFieldCustomVendor();
			if (vendor) {
				_navHeaderDetails.set('content', vendor);
			}

			//Status of the App
			if (this.app.isInstalled || this.app.getHosts().length) {
				var text = _('Installed');
				if (this.app.endOfLife) {
					text = _('End of life');
					var tooltipText = this._detailFieldCustomEndOfLife();
					domConstruct.create('div', {
							'class': 'umcEndOfLifeHelp umcHelpIconSmall',
							onclick: function(evt) {
								var node = evt.target;
								Tooltip.show(tooltipText, node);
								if (evt) {
									dojoEvent.stop(evt);
								}
								on.once(kernel.body(), 'click', function(evt) {
									Tooltip.hide(node);
									dojoEvent.stop(evt);
								});
							}
						}, _navHeaderDetails.domNode
					);
				} else if (this.app.canUpgradeInDomain()) {
					text = _('Update available');
				}
				domConstruct.create('div', {
					textContent: text,
					'class': 'umcAppStatusText'
				}, _navHeaderDetails.domNode);
			} else {
			//Categories of the App
				var categoryButtons = this._detailFieldCustomCategories();
				if (categoryButtons) {
					_navHeaderDetails.domNode.appendChild(categoryButtons);
				}
			}

			this._navContainer.addChild(_navHeaderDetails);
			this.set('navButtons', this.getButtons());
			this.set('headerButtons', this.getHeaderButtons());
			this._navContainer.addChild(this._navButtons);

			this.addChild(this._navContainer);
			this.own(this._navContainer);
		},

		_renderMainContainer: function() {
			if (this._mainRegionContainer) {
				this.removeChild(this._mainRegionContainer);
				this._mainRegionContainer.destroyRecursive();
				this._mainRegionContainer = null;
			}
			this._mainRegionContainer = new ContainerWidget({});
			this.addChild(this._mainRegionContainer);
			this.own(this._mainRegionContainer);

			var isAppInstalled = this.app.isInstalled || this.app.getHosts().length > 0;
			if (isAppInstalled) {
				this._renderUsage();
				this._renderInstallationManagement();
			}
			this._renderDetailsPane(isAppInstalled);

			domStyle.set(this._main.domNode, 'margin-bottom', '2em');
		},

		_renderUsage: function() {
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
				this._mainRegionContainer.addChild(usageHeader);

				var usageClass = 'usage ' + this._getCSSClass4TextLength(usage);
				var usagePane = new Text({
					content: usage,
					'class': usageClass
				});
				this._mainRegionContainer.addChild(usagePane);
			}
		},

		_renderInstallationManagement: function() {
			var isSingleServerInstallation = this.app.isInstalled && this.app.installationData.length === 1;
			var actions = this.getActionButtons(isSingleServerInstallation);
			if (isSingleServerInstallation) {
				this._renderSingleManagement(actions);
			} else {
				this._renderDomainwideManagement(actions);
			}
		},

		_renderSingleManagement: function(actions) {
			var header = new Text({
				content: _('Manage local installation'),
				'class': 'mainHeader'
			});
			this._mainRegionContainer.addChild(header);
			this._mainRegionContainer.own(header);

			var actionButtonContainer = new ContainerWidget({
				'class': 'appDetailsPageActions'
			});
			array.forEach(actions, function(action) {
				var button = new Button(action);
				actionButtonContainer.addChild(button);
				actionButtonContainer.own(button);
			});
			this._mainRegionContainer.addChild(actionButtonContainer);
			this._mainRegionContainer.own(actionButtonContainer);
		},

		_renderDomainwideManagement: function(actions) {
			var header = new Text({
				content: _('Manage domain wide installations'),
				'class': 'mainHeader'
			});
			this._mainRegionContainer.addChild(header);
			this._mainRegionContainer.own(header);

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
			this._installedAppsGrid = new adaptedGrid({
				'class': 'appDetailsPageActions',
				actions: actions,
				columns: columns,
				moduleStore: myStore
			});
			this._mainRegionContainer.addChild(this._installedAppsGrid);
			this._mainRegionContainer.own(this._installedAppsGrid);
		},

		_renderDetailsPane: function(isAppInstalled) {
			this._detailsContainer = new ContainerWidget({
				'class': 'detailsContainer'
			});
			var descriptionContainer = new ContainerWidget({
				'class': 'descriptionContainer'
			});
			var longDescCSSClass = this._getCSSClass4TextLength(this.app.longDescription || '');
			domClass.add(domConstruct.create('div', {
				innerHTML: this.app.longDescription  // no HTML escape!
			}, descriptionContainer.domNode), longDescCSSClass);
			this._detailsContainer.addChild(descriptionContainer);

			if (this.app.thumbnails.length) {
				var styleContainer = new ContainerWidget({
					'class': 'carouselWrapper'
				});
				var urls = array.map(this.app.thumbnails, function(ithumb) {
					return {
						src: ithumb
					};
				});
				this.thumbnailGallery = new ThumbnailGallery({
					items: urls
				});
				styleContainer.addChild(this.thumbnailGallery);
				this._detailsContainer.addChild(styleContainer);
			}

			var detailsPane = new TitlePane({
				open: !isAppInstalled,
				//class: 'installedAppDetailsPane',
				title: _('Details'),
				content: this._detailsContainer,
				'class': 'appDetailsPane'
			});

			if (this.thumbnailGallery) {
				//handle behaviour of the thumbnailGallery based on wether
				//the titlepane is closed or not
				if (!detailsPane.open) {
					this.thumbnailGallery._stopFirstResize = true;
				}
				detailsPane.watch('open', lang.hitch(this, function(variable, oldVal, titlePaneIsOpen) {
					if (titlePaneIsOpen) {
						this.thumbnailGallery._handleResize();
					} else {
						if (this.thumbnailGallery.isBigThumbnails) {
							this.thumbnailGallery.toggleThumbSize();
						}
						this.thumbnailGallery.pauseAllVideos();
					}
				}));
			}
			this._mainRegionContainer.addChild(detailsPane, isAppInstalled ? null : 0);
		},

		_getCSSClass4TextLength: function(text) {
			var cssClass = '';
			array.forEach([400, 500, 600, 800], function(ilength) {
				if (text.length > ilength) {
					cssClass = 'textLongerThan' + ilength + 'Chars';
				}
			});
			return cssClass;
		},

		_renderFooter: function() {
			//TODO just for testing
			domConstruct.empty(this._footer.domNode);

			var footerClass = "appDetailsFooter col-xs-12 col-sm-6";

			var footerLeft = new ContainerWidget({
				'class': footerClass
			});
			this._footer.own(footerLeft);
			this._footer.addChild(footerLeft);
			var footerRight = new ContainerWidget({
				'class': footerClass
			});
			this._footer.own(footerRight);
			this._footer.addChild(footerRight);


			domConstruct.create('span', {
				innerHTML: _('More information'),
				'class': 'mainHeader'
			}, footerLeft.domNode);

			this._detailsTable = domConstruct.create('table', {
				style: {borderSpacing: '1em 0.1em'}
			});
			if (this.app.hasMaintainer()) {
				this.addToDetails(_('Vendor'), 'Vendor');
				this.addToDetails(_('App provider'), 'Maintainer');
			} else {
				this.addToDetails(_('App provider'), 'Vendor');
			}
			this.addToDetails(_('Contact'), 'Contact');
			this.addToDetails(_('More information'), 'Website');
			this.addToDetails(_('Support'), 'SupportURL');
			this.addToDetails(_('Installed version'), 'Version');
			this.addToDetails(_('Candidate version'), 'CandidateVersion');
			this.addToDetails(_('License'), 'License');
			this.addToDetails(_('Categories'), 'Categories');
			this.addToDetails(_('End of life'), 'EndOfLife');
			this.addToDetails(_('Notification'), 'NotifyVendor');

			domConstruct.place(this._detailsTable, footerLeft.domNode);

			var hasRating = array.some(this.app.rating, function(rating) { return rating.value; });
			if (hasRating) {
				domConstruct.create('span', {
					innerHTML: _('App Rating'),
					'class': 'mainHeader'
				}, footerRight.domNode);

				array.forEach(this.app.rating, function(rating) {
					var ratingText = new Text({
						'class': 'umcAppRating'
					});
					for (var i = 0; i < rating.value; i++) {
						domConstruct.create('div', {
								'class': 'umcAppRatingIcon'
							}, ratingText.domNode
						);
					}
					domConstruct.create('div', {
							'class': 'umcAppRatingText',
							textContent: rating.label
						}, ratingText.domNode
					);
					domConstruct.create('div', {
							'class': 'umcAppRatingHelp umcHelpIconSmall',
							onclick: function(evt) {
								// stolen from system-setup
								var node = evt.target;
								Tooltip.show(rating.description, node);  // TODO: html encode?
								if (evt) {
									dojoEvent.stop(evt);
								}
								on.once(kernel.body(), 'click', function(evt) {
									Tooltip.hide(node);
									dojoEvent.stop(evt);
								});
							}
						}, ratingText.domNode
					);
					footerRight.addChild(ratingText);
				});
			}
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

		uninstallApp: function(host) {
			// before installing, user must read uninstall readme
			this.showReadme(this.app.readmeUninstall, _('Uninstall Information'), _('Uninstall')).then(lang.hitch(this, function() {
				this.callInstaller('uninstall', host).then(
					lang.hitch(this, function() {
						this.showReadme(this.app.readmePostUninstall, _('Uninstall Information')).then(lang.hitch(this, 'markupErrors'));
					}), lang.hitch(this, function() {
						this.markupErrors();
					})
				);
			}));
		},


		installAppDialog: function() {
			this.showReadme(this.app.licenseAgreement, _('License agreement'), _('Accept license')).then(lang.hitch(this, function() {
				this.showReadme(this.app.readmeInstall, _('Install Information'), _('Install')).then(lang.hitch(this, function() {
					if (this.app.installationData) {
						var hosts = [];
						var removedDueToInstalled = [];
						var removedDueToRole = [];
						array.forEach(this.app.installationData, function(item) {
							if (item.canInstall()) {
								if (item.isLocal()) {
									hosts.unshift({
										label: item.displayName,
										id: item.hostName
									});
								} else {
									hosts.push({
										label: item.displayName,
										id: item.hostName
									});
								}
							} else {
								if (item.isInstalled) {
									removedDueToInstalled.push(item.displayName);
								} else if (!item.hasFittingRole()) {
									removedDueToRole.push(item.displayName);
								}
							}
						});
						this.hostDialog.reset(hosts, removedDueToInstalled, removedDueToRole);
						this.hostDialog.showUp().then(lang.hitch(this, function(values) {
							this.installApp(values.host);
						}));
					} else {
						this.installApp();
					}
				}));
			}));
		},

		installApp: function(host) {
			this.callInstaller('install', host).then(
				lang.hitch(this, function() {
					// put dedicated module of this app into favorites
					UMCApplication.addFavoriteModule('apps', this.app.id);
					this.showReadme(this.app.readmePostInstall, _('Install Information')).then(lang.hitch(this, 'markupErrors'));
				}), lang.hitch(this, function() {
					this.markupErrors();
				})
			);
		},

		upgradeApp: function(host) {
			// before installing, user must read update readme
			this.showReadme(this.app.candidateReadmeUpdate, _('Upgrade Information'), _('Upgrade')).then(lang.hitch(this, function() {
				this.callInstaller('update', host).then(
					lang.hitch(this, function() {
						this.showReadme(this.app.candidateReadmePostUpdate, _('Upgrade Information')).then(lang.hitch(this, 'markupErrors'));
					}), lang.hitch(this, function() {
						this.markupErrors();
					})
				);
			}));
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

		_showDockerWarning: function() {
			var prefDeferred = new Deferred();
			tools.getUserPreferences().then(
				function(data) {
					prefDeferred.resolve(data.appcenterDockerSeen);
				},
				function() {
					prefDeferred.resolve('true');
				}
			);
			return when(prefDeferred).always(lang.hitch(this, function(appcenterDockerSeen) {
				if (tools.isTrue(appcenterDockerSeen)) {
					return;
				} else {
					return dialog.confirmForm({
						title: _('App installation notes'),
						widgets: [
							{
								type: Text,
								name: 'help_text',
								content: '<div style="width: 535px">' +
									'<p>' + _('This App uses a container technology. Containers have to be downloaded once. After that they can be used multiple times.') + '</p>' +
									'<p>' + _('Depending on your internet connection and on your server performance, the download and the App installation may take up to 15 minutes') + '</p>' +
								'</div>'
							},
							{
								type: CheckBox,
								name: 'do_not_show_again',
								label: _("Do not show this message again")
							}
						],
						buttons: [{
							name: 'submit',
							'default': true,
							label: _('Continue')
						}]
					}).then(
						lang.hitch(this, function(data) {
							tools.setUserPreference({appcenterDockerSeen: data.do_not_show_again ? 'true' : 'false'});
						})
					);
				}
			}));
		},

		callInstaller: function(func, host, force, deferred, values) {
			var isRemoteAction = host && tools.status('hostname') != host;
			var warningDeferred = new Deferred();
			if (this.app.installsAsDocker() && !force && func != 'uninstall') {
				warningDeferred = this._showDockerWarning();
			} else {
				warningDeferred.resolve();
			}
			return warningDeferred.then(lang.hitch(this, function() {
				deferred = deferred || new Deferred();
				var nonInteractive = new Deferred();
				deferred.then(lang.hitch(nonInteractive, 'resolve'));
				var actionLabel = '';
				var progressMessage = '';
				var title = '';
				var text = '';
				switch(func) {
				case 'install':
					actionLabel = _('Install');
					title = _('Installation of %s', this.app.name);
					text = _('Please confirm to install the application %s on this host.', this.app.name);
					progressMessage = _('Installing %s on this host', this.app.name);
					if (isRemoteAction) {
						text = _('Please confirm to install the application %(name)s on host %(host)s.', {name: this.app.name, host: host});
						progressMessage = _('Installing %(name)s on host %(host)s', {name: this.app.name, host: host});
					}
					break;
				case 'uninstall':
					actionLabel = _('Uninstall');
					title = _('Removal of %s', this.app.name);
					text = _('Please confirm to uninstall the application %s on this host.', this.app.name);
					progressMessage = _('Uninstalling %s from this host', this.app.name);
					if (isRemoteAction) {
						text = _('Please confirm to uninstall the application %(name)s from host %(host)s.', {name: this.app.name, host: host});
						progressMessage = _('Uninstalling %(name)s from host %(host)s', {name: this.app.name, host: host});
					}
					break;
				case 'update':
					actionLabel = _('Upgrade');
					title = _('Upgrade of %s', this.app.name);
					text = _('Please confirm to upgrade the application %s on this host.', this.app.name);
					progressMessage = _('Upgrading %s on this host', this.app.name);
					if (isRemoteAction) {
						text = _('Please confirm to upgrade the application %(name)s on host %(host)s.', {name: this.app.name, host: host});
						progressMessage = _('Upgrading %(name)s on host %(host)s', {name: this.app.name, host: host});
					}
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
				if (this.app.installsAsDocker()) {
					command = 'appcenter/docker/invoke';
					if (isRemoteAction) {
						command = 'appcenter/docker/remote/invoke';
					}
				}
				var commandArguments = {
					'function': func,
					'application': this.app.id,
					'app': this.app.id,
					'host': host || '',
					'force': force === true,
					'values': values || {}
				};

				this._progressBar.reset(_('%s: Performing software tests on involved systems', this.app.name));
				this._progressBar._progressBar.set('value', Infinity); // TODO: Remove when this is done automatically by .reset()
				var invokation;
				if (this.app.installsAsDocker()) {
					invokation = tools.umcpProgressCommand(this._progressBar, command, commandArguments).then(
							undefined,
							undefined,
							lang.hitch(this, function(result) {
								var errors = array.map(result.intermediate, function(res) {
									if (res.level == 'ERROR' || res.level == 'CRITICAL') {
										return res.message;
									}
								});
								this._progressBar._addErrors(errors);
							})
					);
				} else {
					invokation = tools.umcpCommand(command, commandArguments);
				}
				invokation = invokation.then(lang.hitch(this, function(data) {
					if (!('result' in data)) {
						data = {'result': data};
					}
					var result = data.result;
					var mayContinue = true;

					if ('success' in result) {
						if (result.success) {
							deferred.resolve();
						} else {
							deferred.reject();
						}
					} else if (!result.can_continue) {
						mayContinue = !result.serious_problems;
						if (!mayContinue) {
							topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, 'cannot-continue');
							title = _('Error performing the action');
							text = _('The requested action cannot be carried out. Please consider the information listed below in order to resolve the problem and try again.');
						}
						this.detailsDialog.reset(mayContinue, title, text, actionLabel);
						if (mayContinue) {
							this.detailsDialog.showConfiguration(func);
						}
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
							lang.hitch(this, function(values) {
								this.callInstaller(func, host, true, deferred, values);
							}),
							function() {
								deferred.reject();
							}
						);
					} else {
						this.switchToProgressBar(progressMessage).then(
							function() {
								deferred.resolve();
							}, function() {
								deferred.reject();
							}
						);
					}
				}));
				this.standbyDuring(all([warningDeferred, invokation, deferred, nonInteractive]), this._progressBar);
				return deferred;
			}));
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
				if (this.app.isMaster) {
					var loginAsAdminTag = '<a href="javascript:void(0)" onclick="require(\'login\').relogin(\'Administrator\')">Administrator</a>';
					msg =
						'<p>' + _('You need to request and install a new license in order to use the Univention App Center.') + '</p>' +
						'<p>' + _('To do this please log in as %s and repeat the steps taken until this dialog. You will be guided through the installation.', loginAsAdminTag) + '</p>';
				} else {
					var hostLink;
					if (tools.status('username') == 'Administrator') {
						hostLink = '<a href="javascript:void(0)" onclick="require(\'umc/tools\').openRemoteSession(' + json.stringify(this.app.hostMaster) + ')">' + entities.encode(this.app.hostMaster) + '</a>';
					} else {
						hostLink = '<a target="_blank" href="https://' + entities.encode(this.app.hostMaster) + '/univention-management-console">' + entities.encode(this.app.hostMaster) + '</a>';
					}
					var dialogName = _('Activation of UCS');
					msg =
						'<p>' + _('You need to request and install a new license in order to use the Univention App Center.') + '</p>' +
						'<p>' + _('To do this please log in on %(host)s as an administrator. Open the menu in the top right corner of the screen and choose "License" > "%(dialogName)s". There you can request the new license.', {host: hostLink, dialogName: dialogName}) + '</p>' +
						'<p>' + _('After that you can "%(action)s" "%(app)s" here on this system.', {action: action, app: entities.encode(this.app.name)}) + '</p>';  // TODO: html escape action?
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
			var callback = lang.hitch(this, function() {
				if (this._progressBar.getErrors().errors.length) {
					deferred.reject();
				} else {
					deferred.resolve();
				}
			});
			this._progressBar.reset(msg);
			this._progressBar.auto('appcenter/progress',
				{},
				callback,
				undefined,
				undefined,
				true
			);
			return deferred;
		},

		markupErrors: function() {
			var installMasterPackagesOnHostFailedRegex = (/Installing extension of LDAP schema for (.+) seems to have failed on (DC Master|DC Backup) (.+)/);
			var logHintGiven = false;
			var errors = array.map(this._progressBar._errors, lang.hitch(this, function(error) {
				var match = installMasterPackagesOnHostFailedRegex.exec(error);
				if (match) {
					var component = match[1];
					var role = match[2];
					var host = match[3];
					error = '<p>' + _('Installing the extension of the LDAP schema on %s seems to have failed.', '<strong>' + entities.encode(host) + '</strong>') + '</p>';
					if (role === 'DC Backup') {
						error += '<p>' + _('If everything else went correct and this is just a temporary network problem, you should execute %s as root on that backup system.', '<pre>univention-app install ' + entities.encode(this.app.id) + ' --only-master-packages</pre>') + '</p>';
					}
					error += '<p>' + _('Further information can be found in the following log file on each of the involved systems: %s', '<br /><em>/var/log/univention/management-console-module-appcenter.log</em>') + '</p>';
				} else {
					error = entities.encode(error);
					if (! logHintGiven) {
						error += '<p>' + _('Further information can be found in the following log file on each of the involved systems: %s', '<br /><em>/var/log/univention/appcenter.log</em>') + '</p>';
						logHintGiven = true;
					}
				}
				return error;
			}));
			this._progressBar._errors = errors;
			this._progressBar.allowHTMLErrors = true;
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
				var deferred = tools.renewSession().then(lang.hitch(this, function() {
					var reloadPage = this.updateApplications().then(lang.hitch(this, 'reloadPage'));
					var reloadModules = UMCApplication.reloadModules();
					return all([reloadPage, reloadModules]).then(function() {
						tools.checkReloadRequired();
					});
				}));

				// show standby animation
				this._progressBar.reset(_('Updating session and module data...'));
				this._progressBar._progressBar.set('value', Infinity); // TODO: Remove when this is done automatically by .reset()
				this.standbyDuring(deferred, this._progressBar);
			}), 100);
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
				return _('Please contact the provider of the application');
			}
		},

		_detailFieldCustomVendor: function() {
			var vendor = this.app.vendor || this.app.maintainer;
			var website = this.app.websiteVendor;
			if (vendor && website) {
				return '<div><a href="' + entities.encode(website) + '" target="_blank">' + entities.encode(vendor) + '</a></div>';
			} else if (vendor) {
				return '<div>' + entities.encode(vendor) + '</div>';
			}
		},

		_detailFieldCustomMaintainer: function() {
			if (!this.app.hasMaintainer()) {
				return null;
			}
			var maintainer = this.app.maintainer;
			var website = this.app.websiteMaintainer;
			if (maintainer && website) {
				return '<a href="' + entities.encode(website) + '" target="_blank">' + entities.encode(maintainer) + '</a>';
			} else if (maintainer) {
				return maintainer;
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
				return _('This application will inform the App provider about an (un)installation. The app provider may contact you.');
			} else {
				return _('This application will not inform the App provider about an (un)installation directly.');
			}
		},

		_detailFieldCustomEndOfLife: function() {
			if (this.app.endOfLife) {
				var warning = _('This application will not get any further updates. We suggest to uninstall %(app)s and search for an alternative application.', {app: entities.encode(this.app.name)});
				if (this.app.isCurrent) {
					warning += ' ' + _('Click on "%(button)s" if you want to continue running this application at your own risk.', {button: _('Continue using')});
				}
				return warning;
			}
		},

		_detailFieldCustomCategories: function() {
			if (this.app.categories) {
				var categoriesContainerNode = domConstruct.create('div', {
					'class': 'categoryContainer'
				});
				if (this.moduleID === 'appcenter') {
					this.app.categories.forEach(lang.hitch(this, function(category) {
						var categoryButton = domConstruct.create('button', {
							textContent: _(category),
							onclick: lang.hitch(this, function() { this.onBack(category); }),
							'class': 'categoryButton'
						});
						domConstruct.place(categoryButton, categoriesContainerNode);
					}));
				} else {
					this.app.categories.forEach(lang.hitch(this, function(category) {
						var categoryButton = domConstruct.create('span', {
							textContent: _(category),
							'class': 'categorySpan'
						});
						domConstruct.place(categoryButton, categoriesContainerNode);
					}));
				}
				return categoriesContainerNode;
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
			domConstruct.create('td', {innerHTML: entities.encode(label), style: {verticalAlign: 'top'}}, tr);
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

