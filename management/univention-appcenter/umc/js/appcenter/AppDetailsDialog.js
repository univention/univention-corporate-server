/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2013-2022 Univention GmbH
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
	"dojo/on",
	"dojo/topic",
	"dojo/Deferred",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"./_AppDialogMixin",
	"./AppDetailsContainer",
	"./AppSettings",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, on, topic, Deferred, Form, ContainerWidget, Page, _AppDialogMixin, AppDetailsContainer, AppSettings, _) {
	return declare("umc.modules.appcenter.AppDetailsDialog", [ Page, _AppDialogMixin ], {
		_container: null,
		_appSettingsForm: null,
		_confirmForm: null,
		_continueDeferred: null,
		_hasSeriousProblems: false,
		headerTextAllowHTML: false,
		helpTextAllowHTML: false,

		title: _('App management'),

		_getConfirmFormButtons: function(funcLabel, mayContinue) {
			var buttons = [{
				name: 'cancel',
				'default': true,
				label: _('Cancel'),
				callback: lang.hitch(this, 'cancelInstallation')
			}];
			if (mayContinue) {
				buttons.push({
					name: 'submit',
					label: funcLabel,
					callback: lang.hitch(this, function() {
						var values = {};
						if (this._appSettingsForm) {
							if (!this._appSettingsForm.validate()) {
								this._appSettingsForm.focusFirstInvalidWidget();
								return;
							}
							values = this._appSettingsForm.get('value');
						}
						this._continueDeferred.resolve(values);
						this.onBack();
					})
				});
			}
			return buttons;
		},

		reset: function(funcName, funcLabel, funcWarningLabel, details, host, appDetailsPage, mayContinue, title, text) {
			this._clearWidget('_container');
			this._clearWidget('_confirmForm');

			this._hasSeriousProblems = !mayContinue;
			this._continueDeferred = new Deferred();

			this.set('headerText', title);
			this.set('helpText', text);
			this.set('headerButtons', [{
				name: 'close',
				label: _('Cancel installation'),
				callback: lang.hitch(this, 'cancelInstallation')
			}]);

			this._container = new ContainerWidget({});
			var appDetailsContainer = new AppDetailsContainer({
				funcName: funcName,
				funcLabel: funcLabel,
				app: this.app,
				details: details,
				host: host,
				appDetailsPage: appDetailsPage,
			});
			this._confirmForm = new Form({
				buttons: this._getConfirmFormButtons(funcLabel, mayContinue),
				style: 'margin-top: 1.5em;'
			});

			on(appDetailsContainer, 'solutionClicked', function(stayAfterSolution) {
				if (!stayAfterSolution) {
					this.onBack();
				}
			});
			if (appDetailsContainer.doesShowWarnings) {
				this._confirmForm.getButton('submit').set('label', funcWarningLabel);
			}

			this._container.addChild(appDetailsContainer);
			this.addChild(this._container);
			this.addChild(this._confirmForm);
			if (mayContinue) {
				this.showConfiguration(funcName);
			}
		},

		showConfiguration: function(funcName) {
			if (funcName === 'install') {
				funcName = 'Install';
			} else if (funcName === 'update') {
				funcName = 'Upgrade';
			} else if (funcName === 'uninstall') {
				funcName = 'Remove';
			}
			this.standbyDuring(AppSettings.getFormDeferred(this.app, funcName).then(lang.hitch(this, function(form) {
				if (form) {
					this._appSettingsForm = form;
					this._container.addChild(this._appSettingsForm);
				}
			})));
		},

		showUp: function() {
			this.onShowUp();
			return this._continueDeferred;
		},

		cancelInstallation: function() {
			if (this._hasSeriousProblems) {
				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, 'user-cancel');
			}
			this.onBack();
		},

		onBack: function() {
			if (this._continueDeferred && !this._continueDeferred.isFulfilled()) {
				this._continueDeferred.reject();
			}
		}
	});
});

