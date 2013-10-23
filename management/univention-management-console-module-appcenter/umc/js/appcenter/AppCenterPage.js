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
/*global define require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/when",
	"dojo/dom-construct",
	"dojo/query",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojo/Deferred",
	"dojox/image/LightboxNano",
	"umc/app",
	"umc/dialog",
	"umc/tools",
	"umc/modules/lib/server",
	"umc/widgets/Page",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/Text",
	"umc/widgets/CheckBox",
	"umc/modules/appcenter/AppCenterGallery",
	"umc/widgets/LiveSearchSidebar",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, kernel, array, when, domConstruct, query, Memory, Observable, Deferred, Lightbox, UMCApplication, dialog, tools, libServer, Page, ConfirmDialog, Text, CheckBox, AppCenterGallery, LiveSearchSidebar, _) {

	return declare("umc.modules.appcenter.AppCenterPage", [ Page ], {

		standbyDuring: null, // parents standby method must be passed. weird IE-Bug (#29587)
		// class name of the widget as CSS class
		'class': 'umcAppCenter',

		liveSearch: true,
		addMissingAppButton: true,
		standbyDuringUpdateApplications: true,
		appQuery: null,

		title: _("App management"),
		headerText: _("Manage Applications for UCS"),
		helpText: _("This page lets you install and remove applications that enhance your UCS installation."),

		buildRendering: function() {
			this.inherited(arguments);

			if (this.addMissingAppButton) {
				var locale = kernel.locale.slice( 0, 2 ).toLowerCase();
				var href = 'https://www.univention.de/en/products/ucs/app-catalogue/vote-for-app/';
				if (locale == 'de') {
					href = 'https://www.univention.de/produkte/ucs/app-katalog/vote-for-app/';
				}
				var footerRight = this._footer.getChildren()[1];
				var voteForAppAnchor = domConstruct.create('a', {
					href: href,
					target: '_blank',
					style: {color: '#414142'},
					title: _('Let us know, if you you miss any application in Univention App Center!'),
					innerHTML: _('Suggest new app')
				});
				domConstruct.place(voteForAppAnchor, footerRight.domNode);
			}

			if (this.liveSearch) {
				this._searchSidebar = new LiveSearchSidebar({
					region: 'left',
					searchableAttributes: ['name', 'description', 'longdescription', 'categories']
				});
				this.addChild(this._searchSidebar);
				this._searchSidebar.on('search', lang.hitch(this, 'filterApplications'));
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

			when(this.getAppCenterSeen(), lang.hitch(this, function(appcenterSeen) {
				if (tools.isTrue(appcenterSeen)) {
					// load apps
					this.updateApplications();
				} else {
					dialog.confirmForm({
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
							this.updateApplications();
						}),
						lang.hitch(this, function() {
							this.updateApplications();
						})
					);
				}
			}), lang.hitch(this, function() {
				this.updateApplications();
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

		// inspired by PackagesPage._show_details
		showDetails: function(app) {
			this.onShowApp(app);
		},

		getApplications: function() {
			if (!this._applications) {
				return tools.umcpCommand('appcenter/query', {}).then(lang.hitch(this, function(data) {
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
			if (this.standbyDuringUpdateApplications) {
				this.standbyDuring(updating);
			}
			return updating;
		},

		filterApplications: function() {
			// query logic for search pattern
			var query = {};
			var searchPattern = lang.trim(this._searchSidebar.get('value'));
			if (searchPattern) {
				query.name = this._searchSidebar.getSearchQuery(searchPattern);
			}

			// query logic for categories
			var category = this._searchSidebar.get('category');
			if (category != _('All')) {
				query.categories = {
					test: function(categories) {
						return (array.indexOf(categories, category) >= 0);
					}
				};
			}

			// set query options and refresh grid
			this.set('appQuery', query);
		},

		_setAppQueryAttr: function(query) {
			this._grid.set('query', query);
			this._set('appQuery', query);
		},

		onShowApp: function(app) {
		}
	});
});
