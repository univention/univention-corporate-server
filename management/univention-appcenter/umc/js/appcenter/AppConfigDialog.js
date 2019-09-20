/*
 * Copyright 2015-2019 Univention GmbH
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
	"dojo/Deferred",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/ProgressBar",
	"umc/widgets/Form",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TitlePane",
	"umc/widgets/Page",
	"./_AppDialogMixin",
	"./AppSettings",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, Deferred, entities, tools, ProgressBar, Form, Text, TextBox, CheckBox, ComboBox, ContainerWidget, TitlePane, Page, _AppDialogMixin, AppSettings, _) {
	return declare("umc.modules.appcenter.AppConfigDialog", [ Page, _AppDialogMixin ], {
		_container: null,
		title: _('App management'),

		showUp: function() {
			this.standbyDuring(tools.umcpCommand('appcenter/config', {app: this.app.id, phase: 'Settings'}).then(lang.hitch(this, function(data) {
				this._showUp(data.result);
			})));
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this._progressBar = new ProgressBar({});
			this.own(this._progressBar);
		},


		_showUp: function(result) {
			this._clearWidget('_container', true);

			this.set('headerText', _('Configure %s', entities.encode(this.app.name)));

			this.set('headerButtons', [{
				name: 'submit',
				iconClass: 'umcSaveIconWhite',
				label: _('Apply changes'),
				callback: lang.hitch(this, function() {
					var serviceValues = {};
					var confValues = {};
					if (this._serviceForm) {
						if (! this._serviceForm.validate()) {
							return;
						}
						serviceValues = this._serviceForm.get('value');
					}
					if (this._settingsForm) {
						if (! this._settingsForm.validate()) {
							return;
						}
						tools.forIn(this._settingsForm.get('value'), lang.hitch(this, function(key, value) {
							if (! this._settingsForm.getWidget(key).get('disabled')) {
								confValues[key] = value;
							}
						}));
					}
					this.apply(serviceValues, confValues).then(lang.hitch(this, 'onBack', true));
				})
			}, {
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Cancel configuration'),
				callback: lang.hitch(this, 'onBack', false)
			}]);

			this._container = new ContainerWidget({});
			this.addChild(this._container);

			if (this.app.isDocker) {
				var statusMessage = _('The application is currently not running.') + ' <strong>' + _('It can only be configured while it is running.') + '</strong>';
				if (result.is_running) {
					statusMessage = _('The application is currently running.');
				}
				var widgets = [{
					name: 'status',
					type: Text,
					content: statusMessage
				}, {
					name: 'autostart',
					type: ComboBox,
					label: _('Autostart'),
					size: 'One',
					value: result.autostart,
					staticValues: [{
						id: 'yes',
						label: _('Started automatically')
					}, {
						id: 'manually',
						label: _('Started manually')
					}, {
						id: 'no',
						label: _('Starting is prevented')
					}]
				}];
				var buttons = [{
					name: 'start',
					'class': 'umcFlatButton',
					visible: !result.is_running,
					label: _('Start the application'),
					callback: lang.hitch(this, function() {
						this.startStop('start');
					})
				}, {
					name: 'stop',
					'class': 'umcFlatButton',
					visible: result.is_running,
					label: _('Stop the application'),
					callback: lang.hitch(this, function() {
						this.startStop('stop');
					})
				}];
				this._serviceForm = new Form({
					widgets: widgets,
					buttons: buttons,
					layout: [
						['status'],
						['start', 'stop'],
						['autostart']
					]
				});
				this._container.addChild(this._serviceForm);
			} else {
				this._serviceForm = null;
			}

			var form = AppSettings.getForm(this.app, result.values, 'Settings');
			if (form) {
					this._settingsForm = form;
					this._container.addChild(this._settingsForm);
			}
			this.onShowUp();
		},

		startStop: function(mode) {
			this.standbyDuring(tools.umcpCommand('appcenter/service', {app: this.app.id, mode: mode}).then(lang.hitch(this, function() {
				this.onUpdate();
			})));
		},

		apply: function(serviceValues, confValues) {
			var autostart = serviceValues.autostart;
			this._progressBar.reset(_('%s: Configuring', entities.encode(this.app.name)));
			this._progressBar._progressBar.set('value', Infinity); // TODO: Remove when this is done automatically by .reset()
			var deferred = new Deferred();
			tools.umcpProgressCommand(this._progressBar, 'appcenter/configure', {app: this.app.id, autostart: autostart, values: confValues}).then(
				lang.hitch(this, function() {
					this._progressBar.stop(function() {
						deferred.resolve();
					}, undefined, true);
				}),
				function() {
					deferred.reject();
				},
				lang.hitch(this, function(result) {
					this._progressBar._addErrors(result.errors);
					var errors = array.map(result.intermediate, function(res) {
						if (res.level == 'ERROR' || res.level == 'CRITICAL') {
							return res.message;
						}
					});
					this._progressBar._addErrors(errors);
				})
			);
			return this.standbyDuring(deferred, this._progressBar);
		}
	});
});

