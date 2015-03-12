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
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojo/Deferred",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/CheckBox",
	"umc/modules/appcenter/AppCenterGallery",
	"umc/widgets/LiveSearchSidebar",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, when, domConstruct, Memory, Observable, Deferred, dialog, tools, Page, Text, CheckBox, AppCenterGallery, LiveSearchSidebar, _) {

	return declare("umc.modules.appcenter.AppCenterPage", [ Page ], {

		standbyDuring: null, // parents standby method must be passed. weird IE-Bug (#29587)
		// class name of the widget as CSS class
		'class': 'umcAppCenter',

		liveSearch: true,
		addMissingAppButton: true,
		appQuery: null,

		title: _("App management"),
		headerText: _("Manage Applications for UCS"),
		helpText: _("Install or remove applications on this or another UCS system."),

		buildRendering: function() {
			this.inherited(arguments);

			if (this.liveSearch) {
				this._searchSidebar = new LiveSearchSidebar({
					region: 'nav',
					searchLabel: _('Search applications...'),
					searchableAttributes: ['name', 'description', 'longdescription', 'categories']
				});
				this.addChild(this._searchSidebar);
				this._searchSidebar.on('search', lang.hitch(this, 'filterApplications'));
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

			this._grid = new AppCenterGallery({
				actions: [{
					name: 'open',
					isDefaultAction: true,
					isContextAction: false,
					label: _('Open'),
					callback: lang.hitch(this, function(id, item) {
						this.showDetails(item);
					})
				}]
			});
			this.addChild(this._grid);

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
			})));
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

		// inspired by PackagesPage._show_details
		showDetails: function(app) {
			this.onShowApp(app);
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

		_discriminateApps: function(applications) {
			var installedApps = [];
			var otherApps = [];
			array.forEach(applications, function(app) {
				var installed = app.is_installed;
				if (app.installations) {
					tools.forIn(app.installations, function(server, info) {
						if (info.version) {
							installed = true;
						}
					});
				}
				if (installed) {
					installedApps.push(app);
				} else {
					otherApps.push(app);
				}
			});
			return {
				installedApps: installedApps,
				otherApps: otherApps
			};
		},

		updateApplications: function() {
			// query all applications
			this._applications = null;
			var updating = when(this.getApplications()).then(lang.hitch(this, function(applications) {
				var discriminatedApps = this._discriminateApps(applications);
				var installedApps = discriminatedApps.installedApps;
				var otherApps = discriminatedApps.otherApps;
				if (installedApps.length && otherApps.length) {
					applications = [];
					applications.push({
						isSeparator: true,
						id: '_installed',
						name: _('Installed Applications')
					});
					applications = applications.concat(installedApps);
					applications.push({
						isSeparator: true,
						id: '_other',
						name: _('Available Applications')
					});
					applications = applications.concat(otherApps);
				}
				this._grid.set('store', new Observable(new Memory({
					data: applications
				})));

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
					categories.unshift(_('All'));
					this._searchSidebar.set('categories', categories);
					this._searchSidebar.set('allCategory', categories[0]);
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

			var query = function(object) {
				// query logic for search pattern
				if (searchPattern) {
					if (!searchPattern.test(object.name, object)) {
						return false;
					}
				}

				// query logic for categories
				if (category != _('All')) {
					if (array.indexOf(object.categories, category) === -1) {
						return false;
					}
				}

				return true;
			};

			var actualQuery = query;

			var filteredApplications = this._grid.store.query(query);
			var discriminatedApps = this._discriminateApps(filteredApplications);

			if (discriminatedApps.installedApps.length && discriminatedApps.otherApps.length) {
				actualQuery = function(object) {
					return object.isSeparator || query(object);
				};
			}

			// set query options and refresh grid
			this.set('appQuery', actualQuery);
		},

		_setAppQueryAttr: function(query) {
			this._grid.set('query', query);
			this._set('appQuery', query);
		},

		onShowApp: function(app) {
		}
	});
});
