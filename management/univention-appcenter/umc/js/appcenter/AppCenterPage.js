/*
 * Copyright 2011-2019 Univention GmbH
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
	"dojo/_base/array",
	"dojo/when",
	"dojo/dom-construct",
	"dojo/dom-style",
	"dojo/Deferred",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/CheckBox",
	"umc/modules/appcenter/AppLiveSearchSidebar",
	"umc/modules/appcenter/AppCenterMetaCategory",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, when, domConstruct, domStyle, Deferred, dialog, tools, Page, Text, CheckBox, AppLiveSearchSidebar, AppCenterMetaCategory, _) {

	return declare("umc.modules.appcenter.AppCenterPage", [ Page ], {

		standbyDuring: null, // parents standby method must be passed. weird IE-Bug (#29587)
		// class name of the widget as CSS class
		'class': 'umcAppCenter',

		openApp: null, // if set, this app is opened on module opening

		metaCategories: null,

		liveSearch: true,
		addMissingAppButton: false,
		appQuery: null,
		_sendSearchStringDeferred: null,

		title: _("App management"),
		headerTextAllowHTML: false,
		helpTextAllowHTML: false,
		//helpText: _("Install or remove applications on this or another UCS system."),

		fullWidth: true,

		metaCategoryClass: AppCenterMetaCategory,

		buildRendering: function() {
			this.inherited(arguments);

			if (this.liveSearch) {
				this._searchSidebar = new AppLiveSearchSidebar({
					region: 'nav',
					searchLabel: _('Search applications...'),
					searchableAttributes: ['name', 'description', 'long_description', 'categories', 'vendor', 'maintainer']
				});
				this.addChild(this._searchSidebar);
				this._searchSidebar.on('search', lang.hitch(this, 'filterApplications'));
				this._searchSidebar.on('search', lang.hitch(this, 'trackSearchString'));
				this._searchSidebar.on('categorySelected', lang.hitch(this, 'toggleGridSize'));
			}

			if (this.addMissingAppButton) {
				var voteForAppAnchor = domConstruct.create('a', {
					href: _('https://www.univention.com/products/univention-app-center/vote-for-app/'),
					target: '_blank',
					style: {color: '#414142'},
					title: _('Let us know if you you miss any application in Univention App Center!'),
					innerHTML: _('Suggest new app')
				});
				this.addChild(new Text({
					content: voteForAppAnchor.outerHTML,
					region: 'nav'
				}));
			}

			this.createMetaCategories();

			this.standbyDuring(when(this.getAppCenterSeen()).then(lang.hitch(this, function(appcenterSeen) {
				if (appcenterSeen >= 2) {
					// load apps
					return this.updateApplications();
				} else {
					var msg = this.appCenterInformation;
					if (appcenterSeen === 1) {
						// show an additional hint that the user should read this information again
						msg = this.appCenterInformationReadAgain + this.appCenterInformation;
					}
					return dialog.confirmForm({
						title: _('Univention App Center'),
						widgets: [
							{
								type: Text,
								name: 'help_text',
								content: '<div style="width: 535px">' + msg + '</div>'
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
							tools.setUserPreference({appcenterSeen: data.do_not_show_again ? 2 : 'false'});
							return this.updateApplications();
						}),
						lang.hitch(this, function() {
							return this.updateApplications();
						})
					);
				}
			}), lang.hitch(this, function() {
				return this.updateApplications();
			}))).then(lang.hitch(this ,function() {
				if (this.openApp) {
					this.onShowApp({id: this.openApp});
				}
			}));
		},

		createMetaCategories: function() {
			this.metaCategories = [];

			var assumedMetaCategories = this.getMetaCategoryDefinition();
			array.forEach(assumedMetaCategories, lang.hitch(this, function(metaObj){
				var metaCategory = new this.metaCategoryClass(metaObj);
				metaCategory.on('showApp', lang.hitch(this, 'onShowApp'));
				metaCategory.set('visible', false);
				this.metaCategories.push(metaCategory);
				this.addChild(metaCategory);
				this.own(metaCategory);
				this.watch('appQuery', function(attr, oldval, newval) {
					metaCategory.set('filterQuery', newval);
				});
			}));
		},

		getMetaCategoryDefinition: function() {
			return [
			{
				label: _('Installed'),
				query: function(app) {
					var considerInstalled = false;
					tools.forIn(app.installations, function(host, installation) {
						if (installation.version && host == tools.status('hostname')) {
							considerInstalled = true;
							return false;
						}
					});
					return considerInstalled;
				}
			},
			{
				label: _('Installed in domain'),
				query: function(app) {
					var considerInstalled = false;
					tools.forIn(app.installations, function(host, installation) {
						if (installation.version && host != tools.status('hostname')) {
							considerInstalled = true;
							return false;
						}
					});
					return considerInstalled;
				}
			},
			{
				label: _('Available'),
				query: function(app) {
					return !app.is_installed_anywhere;
				}
			}];
		},

		getAppCenterSeen: function() {
			// final value that is returned by this function:
			//   0 -> user has never seen the App Center info dialog
			//   1 -> user has seen the App Center dialog in its first version
			//        appcenterSeen == "true"
			//   2 -> user has seen the App Center dialog in its second version
			//        (since January 2017)
			//        appcenterSeen == "2"
			var deferred = new Deferred();
			tools.getUserPreferences().then(
				function(data) {
					var val = parseInt(data.appcenterSeen);
					if (isNaN(val)) {
						// should be "false" or "true"
						val = tools.isTrue(data.appcenterSeen) ? 1 : 0;
					}
					deferred.resolve(val);
				},
				function() {
					deferred.reject();
				}
			);
			return deferred;
		},

		getVisibleApps: function() {
			// to show prev or next app on the AppDetailsPage
			// we need all currently visible apps
			var visibleApps = [];
			array.forEach(this.metaCategories, function(metaCategory) {
				if (metaCategory.grid.store) { // undefined if reloading AppDetailsPage
					var apps = metaCategory.grid.store.query(metaCategory.filterQuery);
					visibleApps = visibleApps.concat(apps);
				}
			});
			return visibleApps;
		},

		getApplications: function(quick) {
			if (!this._applications) {
				return tools.umcpCommand('appcenter/query', {'quick': quick}).then(lang.hitch(this, function(data) {
					if (quick) {
						tools.umcpCommand('appcenter/sync_ldap', {}, false).then(
							lang.hitch(this, function() {
								this.updateApplications(false);
							}),
							lang.hitch(this, function(err) {
								err = tools.parseError(err);
								if (err.status === 400) {
									this.addWarning(err.message);
									return;
								}
								this.addWarning(_('Registration of the applications in the domain failed. It will be retried when opening this module again. This may also cause problems when installing applications.'));
							})
						);
					}
					this._applications = data.result;
					return this._applications;
				}));
			}
			return this._applications;
		},

		updateApplications: function(quick) {
			// query all applications
			quick = quick !== false;
			this._applications = null;
			var updating = when(this.getApplications(quick)).then(lang.hitch(this, function(applications) {
				var metaLabels = [];
				array.forEach(this.metaCategories, function(metaObj) {
					metaObj.set('store', applications);
					metaObj.set('visible', true);
					metaLabels.push(metaObj.label);
				});
				metaLabels.push(''); // seperates meta and normal categories

				if (quick && this.liveSearch) {
					var categories = [];
					array.forEach(applications, function(application) {
						array.forEach(application.categories, function(category) {
							if (array.indexOf(categories, category) < 0) {
								categories.push(category);
							}
						});
					});
					categories.sort();
					categories = metaLabels.concat(categories);
					categories.unshift(_('All'));
					this._searchSidebar.set('categories', categories);
				}
			}));
			return updating;
		},

		trackSearchString: function() {
			// is called upon each key press... identify the whole words

			var _sendSearchString = function(searchString) {
				tools.umcpCommand('appcenter/track', {action: 'search', value: searchString});
			};

			if (this._sendSearchStringDeferred && !this._sendSearchStringDeferred.isFulfilled()) {
				// cancel Deferred as a new keypress event has been send before the timeout
				this._sendSearchStringDeferred.cancel();
			}

			// start new timeout after which the search string is send to the backend
			var searchPattern = lang.trim(this._searchSidebar.get('value'));
			this._sendSearchStringDeferred = tools.defer(lang.hitch(this, _sendSearchString, searchPattern), 1000).then(null, function() {});
		},

		filterApplications: function() {
			var searchPattern = lang.trim(this._searchSidebar.get('value'));
			if (searchPattern) {
				searchPattern = this._searchSidebar.getSearchQuery(searchPattern);
			}
			var category = this._searchSidebar.get('category');
			var selectedMeta = array.filter(this.metaCategories, function(metaObj) {
				return metaObj.label === category;
			});

			var query = function(app) {
				// returns true if
				// (a) the searchPattern matches
				// AND
				// (b) a meta category (incl. 'All') was picked
				//     or the category matches

				var matchesSearchPattern = searchPattern ? searchPattern.test(app.name, app) : true;
				var isMetaCategory = selectedMeta.length || category === _('All');
				var matchesCategory = array.indexOf(app.categories, category) >= 0;

				return matchesSearchPattern && (isMetaCategory || matchesCategory);
			};

			if (selectedMeta.length) {
				array.forEach(this.metaCategories, function(metaObj) {
					if (metaObj !== selectedMeta[0]) {
						domStyle.set(metaObj.domNode, 'display', 'none');
					} else {
						domStyle.set(metaObj.domNode, 'display', 'block');
					}
				});
			} else {
				array.forEach(this.metaCategories, function(metaObj) {
					domStyle.set(metaObj.domNode, 'display', 'block');
				});
			}
 
			// set query options and refresh grid
			this.set('appQuery', query);
		},

		toggleGridSize: function() {
			var category = this._searchSidebar.get('category');
			array.forEach(this.metaCategories, function(metaObj) {
				if (metaObj.label === category) {
					metaObj.showAllApps();
				} else {
					metaObj.showOneRowOfApps();
				}
			});
		},

		onShowApp: function(/*app*/) {
		}
	});
});
