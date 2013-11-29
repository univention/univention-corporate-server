/*
 * Copyright 2011-2013 Univention GmbH
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
/*global define require console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/aspect",
	"dojo/when",
	"dojo/Deferred",
	"dojo/topic",
	"umc/app",
	"umc/store",
	"umc/widgets/Module",
	"umc/widgets/TabContainer",
	"umc/modules/appcenter/AppCenterPage",
	"umc/modules/appcenter/AppDetailsPage",
	"umc/modules/appcenter/AppDetailsDialog",
	"umc/modules/appcenter/PackagesPage",
	"umc/modules/appcenter/SettingsPage",
	"umc/modules/appcenter/DetailsPage",
	"umc/i18n!umc/modules/appcenter" // not needed atm
], function(declare, lang, array, aspect, when, Deferred, topic, UMCApplication, store, Module, TabContainer, AppCenterPage, AppDetailsPage, AppDetailsDialog, PackagesPage, SettingsPage, DetailsPage, _) {

	// TODO: ugly workaround for making the app center module unique
	//   (no two modules open at the same time). See Bug #31662.
	//   Maybe put generically in umc/app.js and state only unique: true here?
	aspect.before(UMCApplication, 'openModule', function(module, flavor, props) {
		var module_id = 'appcenter';
		if (typeof(module) == 'string') {
			module = this.getModule(module, flavor);
		}
		if (module && module.id != module_id) {
			// default behaviour for all modules except this one
			return arguments;
		}
		// check whether such a module has already been opened
		var sameModules = array.filter(UMCApplication._tabContainer.getChildren(), function(i) {
			return i.moduleID == module_id;
		});
		if (!sameModules.length) {
			// module is not open yet, open it
			return arguments;
		} else {
			UMCApplication.focusTab(sameModules[0]);
			return [];
		}
	});

	return declare("umc.modules.appcenter", [ Module ], {

		idProperty: 'package',

		buildRendering: function() {

			this.inherited(arguments);

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

			this._componentsStore = store('name', 'appcenter/components');
			this._packagesStore = store('package', 'appcenter/packages');

			this._tabContainer = new TabContainer({nested: true}); // simulate a TabbedModule. Weird IE-Bug prevents standby in TabbedModule
			this.addChild(this._tabContainer);

			this._appCenterPage = new AppCenterPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				addWarning: lang.hitch(this, 'addWarning'),
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this._appDetailsDialog = new AppDetailsDialog({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this._appDetailsPage = new AppDetailsPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				updateApplications: lang.hitch(this._appCenterPage, 'updateApplications'),
				detailsDialog: this._appDetailsDialog,
				udmAccessible: udmAccessible,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this._packages = new PackagesPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				moduleStore: this._packagesStore,
				standby: lang.hitch(this, 'standby')
			});
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

			this._tabContainer.addChild(this._appCenterPage);
			this._tabContainer.addChild(this._appDetailsDialog);
			this._tabContainer.addChild(this._appDetailsPage);
			this._tabContainer.addChild(this._packages);
			this._tabContainer.addChild(this._components);
			this._tabContainer.addChild(this._details);

			// share appCenterInformation among AppCenter and DetailPage
			//   needs to be specified in AppDetailsPage for apps.js
			this._appCenterPage.appCenterInformation = this._appDetailsPage.appCenterInformation;

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
							if (id == last_id) {
								deferred.resolve();
							}
						});
					}));
					when(deferred, lang.hitch(this, function() {
						this.standby(false);
						this._tabContainer.selectChild(this._packages);
						this._packages._call_installer('install', pkgs);
					}));
				} catch(error) {
					console.error("onInstallComponent: " + error.message);
					this.standby(false);
				}
			}));

			// switched from app center to app details and back
			this._appCenterPage.on('showApp', lang.hitch(this, function(app) {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, app.id, 'show');
				this._appDetailsPage.set('app', app);
				this.standbyDuring(this._appDetailsPage.appLoadingDeferred).then(lang.hitch(this, function() {
					this.exchangeChild(this._appCenterPage, this._appDetailsPage);
				}));
			}));
			this._appDetailsPage.on('back', lang.hitch(this, function() {
				this.exchangeChild(this._appDetailsPage, this._appCenterPage);
			}));
			this._appDetailsDialog.on('showUp', lang.hitch(this, function() {
				this.exchangeChild(this._appDetailsPage, this._appDetailsDialog);
			}));
			this._appDetailsDialog.on('back', lang.hitch(this, function(continued) {
				var loadPage = true;
				if (!continued) {
					loadPage = this._appDetailsPage.reloadPage();
					this.standbyDuring(loadPage);
				}
				when(loadPage).then(lang.hitch(this, function() {
					this.exchangeChild(this._appDetailsDialog, this._appDetailsPage);
				}));
			}));

			// switches from 'add' or 'edit' (components grid) to the detail form
			this._components.on('showdetail', lang.hitch(this, function(id) {
				this.exchangeChild(this._components, this._details);
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
				this.exchangeChild(this._details, this._components);
			}));

		},

		startup: function() {
			this.inherited(arguments);

			this._tabContainer.hideChild(this._details);
			this._tabContainer.hideChild(this._appDetailsPage);
			this._tabContainer.hideChild(this._appDetailsDialog);

		},

		// FIXME: this is quite cool. should go into TabbedModule
		// exchange two tabs, preserve selectedness.
		exchangeChild: function(from, to) {
			var what = 'nothing';
			try {
				what = 'getting FROM selection';
				var is_selected = from.get('selected');
				what = 'hiding FROM';
				this._tabContainer.hideChild(from);
				what = 'showing TO';
				this._tabContainer.showChild(to);
				if (is_selected) {
					what = 'selecting TO';
					this._tabContainer.selectChild(to);
				}
			} catch(error) {
				console.error("exchangeChild: [" + what + "] " + error.message);
			}
		}

	});
});

