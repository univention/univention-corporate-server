/*
 * Copyright 2011-2014 Univention GmbH
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
	"dojo/when",
	"dojo/Deferred",
	"dojo/topic",
	"umc/store",
	"umc/widgets/Module",
	"umc/modules/appcenter/AppCenterPage",
	"umc/modules/appcenter/AppDetailsPage",
	"umc/modules/appcenter/AppDetailsDialog",
	"umc/modules/appcenter/AppChooseHostDialog",
	"umc/modules/appcenter/PackagesPage",
	"umc/modules/appcenter/SettingsPage",
	"umc/modules/appcenter/DetailsPage",
	"umc/i18n!umc/modules/appcenter" // not needed atm
], function(declare, lang, array, when, Deferred, topic, store, Module, AppCenterPage, AppDetailsPage, AppDetailsDialog, AppChooseHostDialog, PackagesPage, SettingsPage, DetailsPage, _) {
	return declare("umc.modules.appcenter", [ Module ], {

		unique: true, // only one appcenter may be open at once
		idProperty: 'package',

		buildRendering: function() {
			this.inherited(arguments);

			if (this.moduleFlavor == 'components') {
				this._renderComponents();
			} else if (this.moduleFlavor == 'packages') {
				this._renderPackages();
			} else {
				this._renderAppcenter();
			}
		},

		_renderAppcenter: function() {
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
			this._appChooseHostDialog = new AppChooseHostDialog({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this._appDetailsPage = new AppDetailsPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				updateApplications: lang.hitch(this._appCenterPage, 'updateApplications'),
				detailsDialog: this._appDetailsDialog,
				hostDialog: this._appChooseHostDialog,
				udmAccessible: udmAccessible,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this.addChild(this._appCenterPage);
			this.addChild(this._appDetailsDialog);
			this.addChild(this._appDetailsPage);
			this.selectChild(this._appCenterPage);

			// share appCenterInformation among AppCenter and DetailPage
			//   needs to be specified in AppDetailsPage for apps.js
			this._appCenterPage.appCenterInformation = this._appDetailsPage.appCenterInformation;
			// switched from app center to app details and back
			this._appCenterPage.on('showApp', lang.hitch(this, function(app) {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, app.id, 'show');
				this._appDetailsPage.set('app', app);
				this._appChooseHostDialog.set('app', app);
				this.standbyDuring(this._appDetailsPage.appLoadingDeferred).then(lang.hitch(this, function() {
					this.selectChild(this._appDetailsPage);
				}));
			}));
			this._appDetailsPage.on('back', lang.hitch(this, function() {
				this.selectChild(this._appCenterPage);
			}));
			this._appDetailsDialog.on('showUp', lang.hitch(this, function() {
				this.selectChild(this._appDetailsDialog);
			}));
			this._appChooseHostDialog.on('showUp', lang.hitch(this, function() {
				this.selectChild(this._appChooseHostDialog);
			}));
			this._appChooseHostDialog.on('back', lang.hitch(this, function() {
				this.selectChild(this._appDetailsPage);
			}));
			this._appDetailsDialog.on('back', lang.hitch(this, function(continued) {
				var loadPage = true;
				if (!continued) {
					loadPage = this._appDetailsPage.reloadPage();
					this.standbyDuring(loadPage);
				}
				when(loadPage).then(lang.hitch(this, function() {
					this.selectChild(this._appDetailsPage);
				}));
			}));
		},

		_renderPackages: function() {
			this._packagesStore = store('package', 'appcenter/packages');
			this._packages = new PackagesPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				moduleStore: this._packagesStore,
				standby: lang.hitch(this, 'standby')
			});
			this.addChild(this._packages);
		},

		_renderComponents: function() {
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
						this.selectChild(this._packages);
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
