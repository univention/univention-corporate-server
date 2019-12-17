/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define,require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"dojo/Deferred",
	"dojo/topic",
	"dojo/promise/all",
	"dojox/html/entities",
	"umc/app",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"umc/widgets/Module",
	"umc/modules/appcenter/AppCenterPage",
	"umc/modules/appcenter/AppDetailsPage",
	"umc/modules/appcenter/AppDetailsDialog",
	"umc/modules/appcenter/AppConfigDialog",
	"umc/modules/appcenter/AppChooseHostDialog",
	"umc/modules/appcenter/PackagesPage",
	"umc/modules/appcenter/SettingsPage",
	"umc/modules/appcenter/DetailsPage",
	"umc/i18n!umc/modules/appcenter", // not needed atm
	"xstyle/css!umc/modules/appcenter.css"
], function(declare, lang, array, when, Deferred, topic, all, entities, app, tools, dialog, store, Module, AppCenterPage, AppDetailsPage, AppDetailsDialog, AppConfigDialog, AppChooseHostDialog, PackagesPage, SettingsPage, DetailsPage, _) {

	topic.subscribe('/umc/license/activation', function() {
		if (!app.getModule('udm', 'navigation'/*FIXME: 'license' Bug #36689*/)) {
			dialog.alert(_('Activation is not possible. Please login as Administrator on the DC master.'));
			return;
		}
	});

	app.registerOnStartup(function() {
		tools.umcpCommand("appcenter/ping", {}, false, "appcenter");
	});

	return declare("umc.modules.appcenter", [ Module ], {

		unique: true, // only one appcenter may be open at once
		idProperty: 'package',

		buildRendering: function() {
			this.inherited(arguments);

			if (this.moduleFlavor === 'components') {
				this._renderComponents();
			} else if (this.moduleFlavor === 'packages') {
				this._renderPackages();
			} else {
				this._renderAppcenter();
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			this.watch('selectedChildWidget', lang.hitch(this, '_updateModuleState'));
		},

		_updateModuleState: function() {
			tools.defer(lang.hitch(this, function() {
				this.set('moduleState', this.get('moduleState'));
			}), 0);
		},

		_setModuleStateAttr: function(_state) {
			var currentState = this.get('moduleState');
			if (this._created && _state === this.moduleState || currentState === _state) {
				this._set('moduleState', _state);
				return;
			}
			if (!_state) {
				if (this._appCenterPage) {
					this.selectChild(this._appCenterPage);
				}
			}
			else {
				var state = _state.split(':');
				if (state[0] === 'id' ) {
					var app = {id: state[1]};
					if (this._appCenterPage._applications && this._appCenterPage._applications.length) {
						var loadedApp = array.filter(this._appCenterPage._applications, function(iapp) {
							return iapp.id === app.id;
						});
						if (loadedApp.length) {
							app = loadedApp[0];
						}
					}
					this.showApp(app);
				} else {
					if (this._appCenterPage && state[0] === 'category') {
						this.set('title', 'App Center');
						this.selectChild(this._appCenterPage);
					}
				}
			}
			this._set('moduleState', _state);
		},

		_getModuleStateAttr: function() {
			var state = [];
			var _selectedWidget = lang.getObject('selectedChildWidget', false, this);
			if (this.moduleFlavor === 'appcenter') {
				var _app = lang.getObject('selectedChildWidget.app', false, this);
				if (_selectedWidget === this._appCenterPage) {
					state = ['category', this._appCenterPage._searchSidebar.get('category')];
				} else if (_app) {
					state = ['id', _app.id];
				}
			}
			return state.join(':');
		},

		udmAccessible: function() {
			// FIXME: this is a synchronous call and can
			// potentially fail although the module would
			// be loaded later on. this may not be of any
			// importance but it would be much cleaner
			// to extract the moduleInstalled('udm')
			// functionality from App to tools or
			// a dedicated module
			var udmAccessible = false;
			try {
				require('umc/modules/udm');
				udmAccessible = true;
			} catch(e) {
			}
			return udmAccessible;
		},

		_renderAppcenter: function() {

			this._componentsStore = store('name', 'appcenter/components');
			this._packagesStore = store('package', 'appcenter/packages');

			this._appCenterPage = new AppCenterPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				addWarning: lang.hitch(this, 'addWarning'),
				standbyDuring: lang.hitch(this, 'standbyDuring'),
				openApp: this.props && this.props.app,
				_scroll: lang.hitch(this, '_scroll'),
				_scrollTo: lang.hitch(this, '_scrollTo')
			});
			// switched from app center to app details and back
			this._appCenterPage.on('showApp', lang.hitch(this, 'showApp'));

			this.addChild(this._appCenterPage);
			this.selectChild(this._appCenterPage);

			// share appCenterInformation among AppCenter and DetailPage
			//   needs to be specified in AppDetailsPage for apps.js
			AppCenterPage.prototype.appCenterInformation = AppDetailsPage.prototype.appCenterInformation;
			AppCenterPage.prototype.appCenterInformationReadAgain = AppDetailsPage.prototype.appCenterInformationReadAgain;
		},

		_scroll: function() {
			return {
				bottomY: this._bottom.domNode.scrollTop,
				tabContainerY: lang.getObject('umc.app._tabContainer.domNode.scrollTop')
			};
		},

		_scrollTo: function(x, bottomY, tabContainerY) {
			this._bottom.domNode.scrollTo(x, bottomY);
			var tabContainer = lang.getObject('umc.app._tabContainer');
			if (tabContainer) {
				tabContainer.domNode.scrollTo(x, tabContainerY);
			}
		},

		showApp: function(app, fromSuggestionCategory = false) {
			var scroll = this._scroll();
			if (this._appDetailsPage) {
				this._appDetailsPage.destroyRecursive();
			}
			if (fromSuggestionCategory) {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, app.id, 'showFromSuggestion');
			} else {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, app.id, 'show');
			}
			var appDetailsDialog = new AppDetailsDialog({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this.addChild(appDetailsDialog);

			var appChooseHostDialog = new AppChooseHostDialog({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this.addChild(appChooseHostDialog);

			var appConfigDialog = new AppConfigDialog({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this.addChild(appConfigDialog);

			this._appDetailsPage = new AppDetailsPage({
				app: app,
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				updateApplications: lang.hitch(this._appCenterPage, 'updateApplications'),
				detailsDialog: appDetailsDialog,
				configDialog: appConfigDialog,
				hostDialog: appChooseHostDialog,
				visibleApps: this._appCenterPage.getVisibleApps(),
				udmAccessible: this.udmAccessible(),
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring'),
				fromSuggestionCategory: fromSuggestionCategory
			});
			this._appDetailsPage.own(appChooseHostDialog);
			this._appDetailsPage.own(appDetailsDialog);
			this._appDetailsPage.own(appConfigDialog);
			this._appDetailsPage.watch('moduleTitle', lang.hitch(this, function(attr, oldVal, newVal){
				if (newVal) {
					this.set('title', entities.encode(newVal));
				}
			}));
			this._appDetailsPage.watch('app', lang.hitch(this, function(){
				this._scrollTo(0, 0, 0);
			}));

			this.set('title', entities.encode(app.name) || 'App Center');
			this._appDetailsPage.on('back', lang.hitch(this, function() {
				this.set('title', 'App Center');
				this.selectChild(this._appCenterPage);
				tools.forIn(this._appCenterPage.metaCategories, function(metaKey, metaObj) {
					metaObj._centerApps();
				});
				this.removeChild(appDetailsDialog);
				this.removeChild(appChooseHostDialog);
				this.removeChild(this._appDetailsPage);
				this._appDetailsPage.destroyRecursive();
				this._scrollTo(0, scroll.bottomY, scroll.tabContainerY);
			}));
			this.addChild(this._appDetailsPage);

			this.standbyDuring(this._appDetailsPage.appLoadingDeferred).then(lang.hitch(this, function() {
				this.selectChild(this._appDetailsPage);
				this._scrollTo(0, 0, 0);
			}));

			appChooseHostDialog.on('showUp', lang.hitch(this, function() {
				this.selectChild(appChooseHostDialog);
			}));
			appDetailsDialog.on('showUp', lang.hitch(this, function() {
				this.selectChild(appDetailsDialog);
			}));
			appConfigDialog.on('showUp', lang.hitch(this, function() {
				this.selectChild(appConfigDialog);
			}));
			appChooseHostDialog.on('back', lang.hitch(this, function() {
				this.selectChild(this._appDetailsPage);
			}));
			appDetailsDialog.on('back', lang.hitch(this, function(continued) {
				var loadPage = true;
				if (!continued) {
					loadPage = this._appDetailsPage.reloadPage();
					this.standbyDuring(loadPage);
				}
				when(loadPage).then(lang.hitch(this, function() {
					this.selectChild(this._appDetailsPage);
				}));
			}));
			appConfigDialog.on('back', lang.hitch(this, function(applied) {
				var loadPage = true;
				if (applied) {
					loadPage = all([this._appDetailsPage.updateApplications(), this._appDetailsPage.reloadPage()]);
					this.standbyDuring(loadPage);
				}
				when(loadPage).then(lang.hitch(this, function() {
					this.selectChild(this._appDetailsPage);
				}));
			}));
			appConfigDialog.on('update', lang.hitch(this, function() {
				var loadPage = all([this._appDetailsPage.updateApplications(), this._appDetailsPage.reloadPage()]);
				loadPage = loadPage.then(function() {
					appConfigDialog.showUp();
				});
				this.standbyDuring(loadPage);
			}));
		},

		_renderPackages: function() {
			this._packagesStore = store('package', 'appcenter/packages');
			this._packages = new PackagesPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				moduleStore: this._packagesStore,
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this.addChild(this._packages);
		},

		_renderComponents: function() {
			this._renderPackages();

			this._componentsStore = store('name', 'appcenter/components');
			this._components = new SettingsPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				moduleStore: this._componentsStore,
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this._details = new DetailsPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				moduleStore: this._componentsStore,
				standby: lang.hitch(this, 'standby')
			});
			this.addChild(this._components);
			this.addChild(this._details);
			this.selectChild(this._components);

			this._packages.on('installed', lang.hitch(this._components, 'refresh', true));

			// install default component
			this._components.on('installcomponent', lang.hitch(this, function(ids) {
				this.standby(true);
				try {
					var last_id = ids[ids.length - 1];
					var deferred = new Deferred();
					var pkgs = [];
					array.forEach(ids, lang.hitch(this, function(id) {
						this._details._form.load(id).then(function(values) {
							if (values.installable) {
								pkgs = pkgs.concat(values.defaultpackages);
							}
							if (id === last_id) {
								deferred.resolve();
							}
						});
					}));
					when(deferred, lang.hitch(this, function() {
						this.standby(false);
						this._packages._call_installer('install', pkgs, true);
					}));
				} catch(error) {
					console.error("onInstallComponent: " + error.message);
					this.standby(false);
				}
			}));

			// switches from 'add' or 'edit' (components grid) to the detail form
			this._components.on('showdetail', lang.hitch(this, function(id) {
				this.selectChild(this._details);
				if (id) {
					// if an ID is given: pass it to the detail page and let it load
					// the corresponding component record
					this._details.startEdit(false, id);
				} else {
					// if ID is empty: ask the SETTINGS module for default values.
					this._details.startEdit(true, this._details.getComponentDefaults());
				}
			}));

			// closes detail form and returns to grid view.
			this._details.on('closedetail', lang.hitch(this, function() {
				this._details._form.clearFormValues();
				this.selectChild(this._components);
			}));
		}
	});
});
