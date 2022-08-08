/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2020-2022 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/topic",
	"dojo/on",
	"dojo/Deferred",
	"dojo/promise/all",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/ProgressBar",
	"./App",
	"./AppChooseHostWizard",
	"./AppInstallWizard",
	"./AppPostInstallWizard",
	"./_AppDialogMixin",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, domClass, topic, on, Deferred, all, tools, Page, ProgressBar, App, AppChooseHostWizard, AppInstallWizard, AppPostInstallWizard, _AppDialogMixin, _) {
	return declare("umc.modules.appcenter.AppInstallDialog", [ Page, _AppDialogMixin ], {
		_actionDeferred: null,

		constructor: function() {
			this.headerButtons = [{
				name: 'close',
				label: _('Cancel'),
				callback: lang.hitch(this, '_cancelAction')
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcAppCenterInstallDialog');
		},

		_show: function(widget) {
			this._removeAllChildren();
			this.addChild(widget);
		},

		_removeAllChildren: function() {
			array.forEach(this.getChildren('main'), lang.hitch(this, function(child) {
				this.removeChild(child);
				child.destroyRecursive();
			}));
		},

		_resolveApps: function(backpack) {
			var deferred = new Deferred();

			var progressBar = new ProgressBar({});
			progressBar.reset();
			progressBar.setInfo(_('Performing dependency checks'), '', Infinity);

			var command = tools.umcpCommand('appcenter/resolve', {
				apps: backpack.apps,
				action: backpack.action,
			}).then(function(data) {
				// TODO error handling
				backpack.apps = data.result.apps.map(app => new App(app));
				backpack.auto_installed = data.result.auto_installed;
				backpack.settings = data.result.settings;
				deferred.resolve(backpack);
			});

			this.standbyDuring(command, progressBar);
			return deferred;
		},

		_getHosts: function(backpack) {
			var deferred = new Deferred();
			if (backpack.hosts) {
				deferred.resolve(backpack);
				return deferred;
			}
			var appChooseHostWizard = new AppChooseHostWizard({
				apps: backpack.apps,
				auto_installed: backpack.auto_installed,
			});
			// lang.mixin(backpack, {
				// chooseHostWizardWasVisible: appChooseHostWizard.needsToBeShown
			// });
			appChooseHostWizard.startup(); // is normally called by addChild but we need it for getValues
			if (!appChooseHostWizard.needsToBeShown) {
				backpack.hosts = {};
				for (const [appId, host] of Object.entries(appChooseHostWizard.getValues())) {
					const apps = backpack.hosts[host] || [];
					apps.push(appId);
					backpack.hosts[host] = apps;
				}
				deferred.resolve(backpack);
			} else {
				on(appChooseHostWizard, 'cancel', function() {
					deferred.reject();
				});
				on(appChooseHostWizard, 'finished', function(values) {
					backpack.hosts = {};
					for (const [appId, host] of Object.entries(values)) {
						const apps = backpack.hosts[host] || [];
						apps.push(appId);
						backpack.hosts[host] = apps;
					}
					deferred.resolve(backpack);
				});
				this._show(appChooseHostWizard);
			}
			return deferred;
		},

		_performDryRun: function(backpack) {
			// if (backpack.chooseHostWizardWasVisible) {
				// progressBarContext = new Page({
					// headerText: 'Installation of foo',
					// 'class': 'umcAppCenterDialog',
					// noFooter: true,
					// _initialBootstrapClasses: 'col-xs-12 col-sm-12 col-md-10 col-md-offset-1 col-lg-8 col-lg-offset-2',
					// headerTextRegion: 'main',
					// standbyDuring: lang.hitch(backpack.page.standbyDuring)
				// });
				// this.addChild(progressBarContext);
			// }

			const progressBar = new ProgressBar({});
			progressBar.reset();
			progressBar.setInfo(_('Running tests'), '', Infinity);
			const settings = {};
			for (const app of backpack.apps) {
				settings[app.id] = {};
			}
			const command = tools.umcpProgressCommand(progressBar, 'appcenter/run', {
				apps: backpack.apps.map(app => app.id),
				auto_installed: backpack.auto_installed,
				action: backpack.action,
				hosts: backpack.hosts,
				settings: settings,
				dry_run: true
			}).then(function(results) {
				const dryRunResults = {};
				function getAppResults(appId, host) {
					const app = backpack.apps.find(app => app.id === appId) || {
						id: appId,
					};
					const key = `${appId}$$${host}`;
					dryRunResults[key] = dryRunResults[key] || {
						software_changes_computed: false,
						broken: [],
						install: [],
						remove: [],
						hosts_info: {},
						invokation_forbidden_details: {},
						invokation_warning_details: {},
						host,
						app,
					};
					return dryRunResults[key];
				}
				for (const host of Object.keys(results)) {
					const hostResults = results[host];
					if (hostResults.hasOwnProperty('unreachable')) {
						for (appId of hostResults.unreachable) {
							const appResults = getAppResults(appId, host);
							appResults.invokation_forbidden_details['must_be_reachable'] = false;
						}
						continue;
					}
					for (const [appId, packageChanges] of Object.entries(hostResults.packages)) {
						const appResults = getAppResults(appId, host);
						appResults.broken = packageChanges.broken;
						appResults.install = packageChanges.install;
						appResults.remove = packageChanges.remove;
						appResults.software_changes_computed = !!packageChanges.broken.length
							|| !!packageChanges.install.length
							|| !!packageChanges.remove.length;
					}
					for (const [errorId, errors] of Object.entries(hostResults.errors)) {
						for (const [appId, details] of Object.entries(errors)) {
							const appResults = getAppResults(appId, host);
							appResults.invokation_forbidden_details[errorId] = details;
						}
					}
					for (const [warningId, warnings] of Object.entries(hostResults.warnings)) {
						for (const [appId, details] of Object.entries(warnings)) {
							const appResults = getAppResults(appId, host);
							appResults.invokation_warning_details[warningId] = details;
						}
					}
				}
				backpack.dryRunResults = dryRunResults;
				return backpack;
			});

			// this._hasSeriousProblems = values.dryRunResults.serious_problems;
			// if (this._hasSeriousProblems) {
				// topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, backpack.app.id, 'cannot-continue');
			// }
			return this.standbyDuring(command, progressBar);
		},

		_showInstallWizard: function(backpack) {
			var deferred = new Deferred();
			var installWizard = new AppInstallWizard({
				// hosts: backpack.hosts,
				apps: backpack.apps,
				appSettings: backpack.settings,
				dryRunResults: backpack.dryRunResults,
				action: backpack.action,
			});
			if (!installWizard.needsToBeShown) {
				deferred.resolve(backpack);
			} else {
				on(installWizard, 'solutionClicked', function(stayAfterSolution) {
					if (!stayAfterSolution) {
						deferred.reject();
					}
				});
				on(installWizard, 'cancel', function() {
					deferred.reject();
				});
				on(installWizard, 'finished', function(values) {
					lang.mixin(backpack, values);
					deferred.resolve(backpack);
				});
				this._show(installWizard);
			}
			return deferred;
		},

		_resolveBackpack: function(backpack) {
			const apps = backpack.apps;
			const autoInstalled = backpack.auto_installed;
			const hosts = backpack.hosts;
			const action = backpack.action;
			const appSettings = {};
			for (const app of apps) {
				appSettings[app.id] = {};
				const _appSettings = backpack[`appSettings_appSettings_${app.id}`];
				if (_appSettings) {
					appSettings[app.id] = _appSettings;
				}
			}
			var values = {
				apps,
				hosts,
				autoInstalled,
				appSettings,
				action,
			};
			const deferred = new Deferred();
			deferred.resolve(values);
			return deferred;
		},

		_run: function(backpack) {
			const progressBar = new ProgressBar({});
			progressBar.reset();
			progressBar.setInfo(_('Validating input...'), '', Infinity);
			const command = tools.umcpProgressCommand(progressBar, 'appcenter/run', {
				apps: backpack.apps.map(app => app.id),
				auto_installed: backpack.autoInstalled,
				action: backpack.action,
				hosts: backpack.hosts,
				settings: backpack.appSettings,
				dry_run: false
			}).then(
				function(results) {
					backpack.result = results;
					backpack.errors = progressBar.getErrors().errors;
					return backpack;
				},
				function(errors) {
					deferred.resolve();
				},
				function(updates) {
					var errors = array.map(updates.intermediate, function(res) {
						if (res.level == 'ERROR' || res.level == 'CRITICAL') {
							return res.message;
						}
					});
					progressBar._addErrors(errors)
				});
			this.standbyDuring(command, progressBar);
			return command;
		},

		_aftermath: function(backpack) {
			const deferred = new Deferred();
			var installWizard = new AppPostInstallWizard({
				apps: backpack.apps,
				action: backpack.action,
				result: backpack.result,
				errorMessages: backpack.errors,
			});
			if (!installWizard.needsToBeShown) {
				deferred.resolve(backpack);
			} else {
				this.set('headerButtons', [{
					name: 'close',
					label: installWizard.hasErrors ? _('Cancel') : _('Back'),
					callback: function() {
						deferred.resolve();
					}
				}]);
				on(installWizard, 'finished', function() {
					deferred.resolve(backpack);
				});
				on(installWizard, 'cancel', function() {
					// don't cancel the deferred so that appcenter/run.js::afterRun runs
					deferred.resolve(backpack);
				});
				this._show(installWizard);
			}
			return deferred;
		},

		startAction: function(action, apps, hosts) {
			var backpack = {
				action,
				apps,
				hosts,
			};

			this._actionDeferred = this._resolveApps(backpack)
				.then(lang.hitch(this, '_getHosts'))
				.then(lang.hitch(this, '_performDryRun'))
				.then(lang.hitch(this, '_showInstallWizard'))
				.then(lang.hitch(this, '_resolveBackpack'))
				.then(lang.hitch(this, '_run'))
				.then(lang.hitch(this, '_aftermath'))
				.otherwise(lang.hitch(this, '_cancelAction'));
			return this._actionDeferred;
		},

		_cancelAction: function() {
			this._actionDeferred.cancel();
		}
	});
});


