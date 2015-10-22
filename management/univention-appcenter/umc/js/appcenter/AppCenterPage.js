/*
 * Copyright 2011-2015 Univention GmbH
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

		title: _("App management"),
		headerText: _("Manage Applications for UCS"),
		//helpText: _("Install or remove applications on this or another UCS system."),

		navBootstrapClasses: 'col-xs-12 col-sm-12 col-md-12 col-lg-12',
		mainBootstrapClasses: 'col-xs-12 col-sm-12 col-md-12 col-lg-12',
		_initialBootstrapClasses: 'col-xs-12 col-sm-12 col-md-12 col-lg-12',

		buildRendering: function() {
			this.inherited(arguments);

			if (this.liveSearch) {
				this._searchSidebar = new AppLiveSearchSidebar({
					region: 'nav',
					searchLabel: _('Search applications...'),
					searchableAttributes: ['name', 'description', 'longdescription', 'categories']
				});
				this.addChild(this._searchSidebar);
				this._searchSidebar.on('search', lang.hitch(this, 'filterApplications'));
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
				if (tools.isTrue(appcenterSeen)) {
					// load apps
					return this.updateApplications();
				} else {
					return dialog.confirmForm({
						title: _('Univention App Center'),
						widgets: [
							{
								type: Text,
								name: 'help_text',
								content: '<div style="width: 535px">' + this.appCenterInformation + '</div>'
							},
							{
								type: CheckBox,
								name: 'show_again',
								label: _("Show this message again")
							}
						],
						buttons: [{
							name: 'submit',
							'default': true,
							label: _('Continue')
						}]
					}).then(
						lang.hitch(this, function(data) {
							tools.setUserPreference({appcenterSeen: data.show_again ? 'false' : 'true'});
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
			var assumedMetaCategories = [
			{
				label: _('Installed'),
				query: function(app) {
					return app.is_installed_anywhere;
				}
			},
			{
				label: _('Available'),
				query: function(app) {
					return !app.is_installed_anywhere;
				}
			}];

			array.forEach(assumedMetaCategories, lang.hitch(this, function(metaObj){
				var metaCategory = new AppCenterMetaCategory(metaObj);
				metaCategory.on('showApp', lang.hitch(this, 'onShowApp'));
				this.metaCategories.push(metaCategory);
				this.addChild(metaCategory);
				this.own(metaCategory);
				this.watch('appQuery', function(attr, oldval, newval) {
					metaCategory.set('filterQuery', newval);
				});
			}));
		},

		getAppCenterSeen: function() {
			var deferred = new Deferred();
			tools.getUserPreferences().then(
				function(data) {
					deferred.resolve(data.appcenterSeen);
				},
				function() {
					deferred.reject();
				}
			);
			return deferred;
		},

		getApplications: function() {
			if (!this._applications) {
				return tools.umcpCommand('appcenter/query', {}).then(lang.hitch(this, function(data) {
					tools.umcpCommand('appcenter/sync_ldap', {}, false).then(
						undefined,
						lang.hitch(this, function() {
							this.addWarning(_('Registration of the applications in the domain failed. It will be retried when opening this module again. This may also cause problems when installing applications.'));
						})
					);
					// sort by name
					this._applications = data.result;
					this._applications.sort(tools.cmpObjects({
						attribute: 'name',
						ignoreCase: true
					}));
					return this._applications;
				}));
			}
			return this._applications;
		},

		updateApplications: function() {
			// query all applications
			this._applications = null;
			var updating = when(this.getApplications()).then(lang.hitch(this, function(applications) {
				var metaLabels = [];
				array.forEach(this.metaCategories, function(metaObj) {
					metaObj.set('store', applications);
					metaLabels.push(metaObj.label);
				});
				metaLabels.push(''); // seperates meta and normal categories

				if (this.liveSearch) {
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

		onShowApp: function(app) {
		}
	});
});
