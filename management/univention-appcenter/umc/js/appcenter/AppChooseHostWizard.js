/*
 * Copyright 2019 Univention GmbH
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
	"dojo/_base/array",
	"dojo/_base/lang",
	"dojo/promise/all",
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/Wizard",
	"./AppInstallDialogChooseHostPage",
	"./AppSettings",
	"./App",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, lang, all, Deferred, tools, Wizard, ChooseHostPage, AppSettings, App, _) {
	return declare('umc.modules.appcenter.AppPreinstallWizard', [Wizard], {
		pageMainBootstrapClasses: 'col-xs-12',
		pageNavBootstrapClasses: 'col-xs-12',
		autoHeight: true,

		app: null,
		appDetailsPage: null,
		_onlyOneHost: false,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.pages = this.getPages(this.app);
		},

		getPages: function(app) {
			var pages = [];
			this.addChooseHostPage(app, pages);
			this.addGetDependenciesPage(app, pages);
			return pages;
		},

		addChooseHostPage: function(app, pages) {
			var res = ChooseHostPage.getPageConf(app);
			this._onlyOneHost = res.onlyOneHost;
			pages.push(res.pageConf);
		},

		addGetDependenciesPage: function(app, pages) {
			var pageConf = {
				name: 'getDependencies',
				headerText: _('Installation of %s', app.name),
				helpText: _('Gathering installation data')
			};
			pages.push(pageConf);
		},

		switchPage: function(pageName) {
			if (pageName === 'chooseHost' && this._onlyOneHost) {
				this.switchPage(this.next(pageName));
			} else {
				this.inherited(arguments);
				if (pageName === 'getDependencies') {
					this.performChecks();
				}
			}
		},

		performChecks: function() {
			var deferred = new Deferred();
			this.standbyDuring(deferred);

			var loads = [];
			var host = this.getValues().chooseHost_host;
			var apps = [{id: this.app.id}];
			tools.umcpCommand('appcenter/resolve', {host: host, apps: apps}).then(lang.hitch(this, function(data) {
				array.forEach(data.result.apps, lang.hitch(this, function(dep) {
					var app = tools.umcpCommand('appcenter/get', {'application': dep.id}).then(lang.hitch(this, function(data) {
						return new App(data.result, this.appDetailsPage, host); // maybe we could use backend App?
					}));
					loads.push(app);
				}));
				all(loads).then(lang.hitch(this, function(res) {
					this.onGotHostAndApps(host, res);
				}));
			}));
		},

		onGotHostAndApps: function(host, apps) {

		},

		getFooterButtons: function(pageName) {
			if (pageName === 'getDependencies') {
				return [];
			}
			return this.inherited(arguments);
		}
	});
});

