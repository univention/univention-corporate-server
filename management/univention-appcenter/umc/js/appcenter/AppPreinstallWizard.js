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
	"./AppInstallDialogDependenciesPage",
	"./AppInstallDialogDockerWarningPage",
	"./AppSettings",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, lang, all, Deferred, tools, Wizard, ChooseHostPage, DependenciesPage, DockerWarningPage, AppSettings, _) {
	return declare('umc.modules.appcenter.AppPreinstallWizard', [Wizard], {
		pageMainBootstrapClasses: 'col-xs-12',
		pageNavBootstrapClasses: 'col-xs-12',
		autoHeight: true,

		apps: null,
		mainAppIdx: null,
		host: null,
		appcenterDockerSeen: null,
		_mainApp: null,
		_dependencies: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._mainApp = this.apps[this.mainAppIdx];
			this._dependencies = this.apps.filter(lang.hitch(this, function(app, idx) {
				return idx !== this.mainAppIdx;
			}));
			this.pages = this.getPages(this._mainApp, this._dependencies, this.appcenterDockerSeen);
		},

		getPages: function(app, dependencies, appcenterDockerSeen) {
			var pages = [];
			this.addDependenciesPage(app, dependencies, pages);
			this.addDockerWarningPage(app, dependencies, appcenterDockerSeen, pages);
			this.addChecksPage(app, pages);
			return pages;
		},

		addChooseHostPage: function(app, pages) {
			var pageConf = ChooseHostPage.getPageConf(app);
			if (pageConf) {
				pages.push(pageConf);
			}
		},

		addDependenciesPage: function(app, dependencies, pages) {
			var pageConf = DependenciesPage.getPageConf(app, dependencies);
			if (pageConf) {
				pages.push(pageConf);
			}
		},

		addDockerWarningPage: function(app, dependencies, appcenterDockerSeen, pages) {
			var pageConf = DockerWarningPage.getPageConf(app, dependencies, appcenterDockerSeen);
			if (pageConf) {
				pages.push(pageConf);
			}
		},
		
		addChecksPage: function(app, pages) {
			var pageConf = {
				name: 'checks',
				headerText: _('Installation of %s', app.name),
				helpText: _('Performing pre-install checks')
			};
			pages.push(pageConf);
		},

		setDockerUserPreference: function() {
			var values = this.getValues();
			if (Object.prototype.hasOwnProperty.call(values, 'dockerWarning_doNotShowAgain')) {
				tools.setUserPreference({appcenterDockerSeen: values.dockerWarning_doNotShowAgain ? 'true' : 'false'});
			}
		},

		next: function(pageName) {
			if (pageName === 'dockerWarning') {
				this.setDockerUserPreference();
			}
			return this.inherited(arguments);
		},

		switchPage: function(pageName) {
			this.inherited(arguments);
			if (pageName === 'checks') {
				this.performChecks();
			}
		},

		performChecks: function() {
			// TODO switch with backend call
			// tools.umcpCommand('appcenter/check', {
				// apps: [this.app].concat(this.dependencies)
			// }).then(lang.hitch(this, function(data) {

			// }));
			//
			// TODO standbyduring
			// TODO app is an App() atm, answer from backend probably not, or maybe dont neep app from backend
			var installInfo = [];

			var host = this.host;
			var isRemoteAction = host && tools.status('hostname') != host;

			var force = false;
			var func = 'install';
			var values = null;
			var apps = array.map(this.apps, function(app) {
				return {
					id: app.id,
					//version: app.version,
					only_master_packages: false,
					'function': func,
				};
			});
			var command = 'appcenter/run/do';
			var configCommand = 'appcenter/config_all';
			if (isRemoteAction) {
				command = 'appcenter/run_remote';
			}
			var commandArguments = {dry_run: true, apps: apps, host: host};
			var invokation = tools.umcpProgressCommand(null, command, commandArguments);
			var appSettings = tools.umcpCommand(configCommand, commandArguments);
			var actions = all({
				dryRun: invokation,
				appSettings: appSettings
			});
			this.standbyDuring(actions);
			actions.then(lang.hitch(this, function(r) {
				installInfo = apps.map(function(app) {
					var details = lang.clone(r.dryRun);
					details.invokation_forbidden_details = details.problems[app.id][0];
					details.invokation_warning_details = details.problems[app.id][1];
					var formConf = AppSettings.getFormConf(app, r.appSettings.result[app.id].values, 'Install', true);
					var info = {
						app: app,
						details: details,
						appSettingsFormConf: formConf
					};
					return info;
				});
				this.onChecksDone(host, installInfo);
			}));
		},

		onChecksDone: function(host, installInfo) {

		},

		getFooterButtons: function(pageName) {
			if (pageName === 'checks') {
				return [];
			}
			return this.inherited(arguments);
		}
	});
});

