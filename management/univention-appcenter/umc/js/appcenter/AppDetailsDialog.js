/*
 * Copyright 2013-2019 Univention GmbH
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
	"dojox/html/entities",
	"dojo/topic",
	"dojo/when",
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/TitlePane",
	"umc/widgets/Button",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/modules/appcenter/requirements",
	"./_AppDialogMixin",
	"./AppSettings",
	"./AppDetailsContainer",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, entities, topic, when, Deferred, tools, TitlePane, Button, Text, TextBox, CheckBox, ComboBox, Form, ContainerWidget, Page, requirements, _AppDialogMixin, AppSettings, AppDetailsContainer, _) {
	return declare("umc.modules.appcenter.AppDetailsDialog", [ Page, _AppDialogMixin ], {
		_appDetailsContainer: null,
		_continueDeferred: null,
		_configForm: null,
		_confirmForm: null,
		headerTextAllowHTML: false,
		helpTextAllowHTML: false,

		title: _('App management'),

		reset: function(funcName, funcLabel, details, host, appDetailsPage, mayContinue, title, text) {
			this._clearWidget('_appDetailsContainer', true);
			this._clearWidget('_confirmForm', true);

			if (this._continueDeferred) {
				this._continueDeferred.reject();
			}
			this._continueDeferred = new Deferred();

			this.set('headerText', title);
			this.set('helpText', text);

			var close = lang.hitch(this, function() {
				if (mayContinue) {
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, 'user-cancel');
				}
				this._continueDeferred.reject();
			});

			this.set('headerButtons', [{
				name: 'close',
				label: _('Cancel installation'),
				callback: close
			}]);

			var buttons = [{
				name: 'cancel',
				'default': true,
				label: _('Cancel'),
				callback: close
			}];
			if (mayContinue) {
				buttons.push({
					name: 'submit',
					label: funcLabel,
					callback: lang.hitch(this, function() {
						var values = {};
						if (this._appDetailsContainer && this._appDetailsContainer.configForm) {
							var configForm = this._appDetailsContainer.configForm;
							if (!configForm.validate()) {
								return;
							}
							tools.forIn(configForm.get('value'), function(key, value) {
								if (!configForm.getWidget(key).get('disabled')) {
									values[key] = value;
								}
							});
						}
						array.forEach(this.app.config, function(config) {
							if (values[config.id] === undefined) {
								values[config.id] = config.value;
							}
						});
						this._continueDeferred.resolve(values);
					})
				});
			}

			this._continueDeferred.then(lang.hitch(this, 'onBack', true), lang.hitch(this, 'onBack', false));
			this._appDetailsContainer = new AppDetailsContainer({
				app: this.app,
				funcName: funcName,
				funcLabel: funcLabel,
				details: details,
				host: host,
				appDetailsPage: appDetailsPage,
				mayShowAppSettings: true,
				onBack: lang.hitch(this, 'onBack'),
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this.addChild(this._appDetailsContainer);

			this._confirmForm = new Form({
				buttons: buttons,
				style: 'margin-top: 1.5em;'
			});
			this.addChild(this._confirmForm);
		},

		showUp: function() {
			this.onShowUp();
			return this._continueDeferred;
		},

		onBack: function(/*continued*/) {
			// make sure that the user does not want to continue
			//   (could be called by a requirement.solution(), not by the buttons)
			// if this is called by "Continue" button, it is resolved() anyway
			if (this._continueDeferred) {
				this._continueDeferred.reject();
			}
		}
	});
});

