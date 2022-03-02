/*
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
	"umc/widgets/Page",
	"umc/widgets/ProgressBar",
	"./AppChooseHostWizard",
	"./AppInstallWizard",
	"./AppSettings",
	"./AppDetailsPage",
	"./_AppDialogMixin",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, domClass, topic, on, Deferred, all, Page, ProgressBar, AppChooseHostWizard, AppInstallWizard, AppSettings, AppDetailsPage, _AppDialogMixin, _) {
	return declare("umc.modules.appcenter.AppInstallDialog", [ Page, _AppDialogMixin ], {

		_installationDeferred: null,
		_hasSeriousProblems: false,

		constructor: function() {
			this.headerButtons = [{
				name: 'close',
				label: _('Cancel installation'),
				callback: lang.hitch(this, '_cancelInstallation')
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcAppCenterInstallDialog');
			domClass.remove(this.domNode, 'umcAppCenterDialog');
		},

		_show: function(widget) {
			this._removeAllChildren();
			this.addChild(widget);
			this.onShowUp();
		},

		_removeAllChildren: function() {
			array.forEach(this._main.getChildren(), lang.hitch(this, function(child) {
				this.removeChild(child);
				child.destroyRecursive();
			}));
		},

		_getHost: function(backpack) {
			var deferred = new Deferred();
			var appChooseHostWizard = new AppChooseHostWizard({
				app: backpack.app
			});
			lang.mixin(backpack, {
				chooseHostWizardWasVisible: appChooseHostWizard.needsToBeShown
			});
			appChooseHostWizard.startup(); // is normally called by addChild but we need it for getValues
			if (!appChooseHostWizard.needsToBeShown) {
				lang.mixin(backpack, {
					host: appChooseHostWizard.getValues().host,
				});
				deferred.resolve(backpack);
			} else {
				on(appChooseHostWizard, 'cancel', function() {
					deferred.reject();
				});
				on(appChooseHostWizard, 'finished', function(values) {
					lang.mixin(backpack, values);
					deferred.resolve(backpack);
				});
				this._show(appChooseHostWizard);
			}
			return deferred;
		},

		_getInstallInfo: function(backpack) {
			var progressBarContext = backpack.appDetailsPage;
			if (backpack.chooseHostWizardWasVisible) {
				// progressBarContext = new Page({
					// headerText: 'Installation of foo',
					// 'class': 'umcAppCenterDialog',
					// noFooter: true,
					// _initialBootstrapClasses: 'col-xs-12 col-sm-12 col-md-10 col-md-offset-1 col-lg-8 col-lg-offset-2',
					// headerTextRegion: 'main',
					// standbyDuring: lang.hitch(backpack.appDetailsPage.standbyDuring)
				// });
				// this.addChild(progressBarContext);
			}
			
			var progressBar = new ProgressBar({});
			var _all = all({
				appSettingsFormConf: AppSettings.getFormConfDeferred(backpack.app, 'Install', true),
				dryRunResults: AppDetailsPage.performDryRun(backpack.host, backpack.app, progressBar),
			}).then(lang.hitch(this, function(values) {
				this._hasSeriousProblems = values.dryRunResults.serious_problems;
				if (this._hasSeriousProblems) {
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, backpack.app.id, 'cannot-continue');
				}
				return lang.mixin(backpack, values);
			}));
			return progressBarContext.standbyDuring(_all, progressBar);
		},

		_showInstallWizard: function(backpack) {
			var deferred = new Deferred();
			var installWizard = new AppInstallWizard({
				host: backpack.host,
				app: backpack.app,
				appSettingsFormConf: backpack.appSettingsFormConf,
				dryRunResults: backpack.dryRunResults,
				appDetailsPage: backpack.appDetailsPage
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
			var values = {
				host: backpack.host,
				appSettings: backpack.appSettings_appSettings || {}
			};
			this._installationDeferred.resolve(values);
			this.onBack();
		},

		startInstallation: function(appDetailsPage) {
			this._installationDeferred = new Deferred();
			this._hasSeriousProblems = false;

			var backpack = {
				appDetailsPage: appDetailsPage,
				app: this.app
			};
			this._getHost(backpack)
				.then(lang.hitch(this, '_getInstallInfo'))
				.then(lang.hitch(this, '_showInstallWizard'))
				.then(lang.hitch(this, '_resolveBackpack'))
				.otherwise(lang.hitch(this, '_cancelInstallation'));
			return this._installationDeferred;
		},

		_cancelInstallation: function() {
			if (!this._hasSeriousProblems) {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, 'user-cancel');
			}
			this.onBack();
		},

		onBack: function() {
			if (this._installationDeferred && !this._installationDeferred.isFulfilled()) {
				this._installationDeferred.reject();
			}
		}
	});
});


