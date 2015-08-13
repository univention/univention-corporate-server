/*
 * Copyright 2015 Univention GmbH
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
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TitlePane",
	"umc/widgets/Page",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, tools, Form, Text, TextBox, CheckBox, ComboBox, ContainerWidget, TitlePane, Page, _) {
	var endsWith = function(str, suffix) {
	    return str.indexOf(suffix, str.length - suffix.length) !== -1;
	};
	return declare("umc.modules.appcenter.AppConfigDialog", [ Page ], {
		app: null,
		_container: null,
		noFooter: true,

		title: _('App management'),

		showUp: function() {
			this.set('headerText', _('Configure %s', this.app.name));
			this.set('helpText', _('Here you can set configuration options as well as start and stop the application.'));

			this.set('headerButtons', [{
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Cancel'),
				callback: lang.hitch(this, 'onBack', false)
			}]);

			var buttons = [{
				name: 'cancel',
				'default': true,
				label: _('Cancel'),
				callback: lang.hitch(this, 'onBack', false)
			}, {
				name: 'submit',
				label: _('Apply'),
				callback: lang.hitch(this, function() {
					this.apply(this._serviceForm.get('value'), this._confForm.get('value'), this._advancedConfForm.get('value')).then(lang.hitch(this, 'onBack', true));
				})
			}];
			this.set('navButtons', buttons);

			if (this._container) {
				this.removeChild(this._container);
				this._container.destroyRecursive();
			}
			this._container = new ContainerWidget({});
			this.addChild(this._container);

			var statusMessage = _('The application is currently not running.') + ' <strong>' + _('It can only be configured while it is running.') + '</strong>';
			if (this.app.isRunning) {
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
				value: this.app.autoStart,
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
			buttons = [{
				name: 'start',
				visible: !this.app.isRunning,
				label: _('Start the application'),
				callback: lang.hitch(this, function() {
					this.startStop('start');
				})
			}, {
				name: 'stop',
				visible: this.app.isRunning,
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

			var addWidgets = function(conf, disabled, _widgets) {
				array.forEach(conf, function(variable) {
					var type = TextBox;
					var value = variable.value;
					if (variable.type === 'bool') {
						type = CheckBox;
						value = tools.isTrue(value);
					}
					widgets.push({
						name: variable.id,
						type: type,
						label: variable.description,
						disabled: disabled,
						value: value
					});
				});
			};

			widgets = [{
			}];
			addWidgets(array.filter(this.app.config, function(w) { return !w.advanced; }), !this.app.isRunning, widgets);
			this._confForm = new Form({
				widgets: widgets
			});
			var formTitlePane = new TitlePane({
				title: _('Settings')
			});
			formTitlePane.addChild(this._serviceForm);
			formTitlePane.addChild(this._confForm);
			this._container.addChild(formTitlePane);

			widgets = [];
			addWidgets(array.filter(this.app.config, function(w) { return w.advanced; }), !this.app.isRunning, widgets);
			this._advancedConfForm = new Form({
				widgets: widgets
			});
			if (widgets.length) {
				var advancedFormTitlePane = new TitlePane({
					title: _('Settings (advanced)'),
					open: false
				});
				advancedFormTitlePane.addChild(this._advancedConfForm);
				this._container.addChild(advancedFormTitlePane);
			}
			this.onShowUp();
		},

		startStop: function(mode) {
			this.standbyDuring(tools.umcpCommand('appcenter/service', {application: this.app.id, mode: mode}).then(lang.hitch(this, function() {
				this.onUpdate();
			})));
		},

		apply: function(serviceValues, confValues, advancedConfValues) {
			var autostart = serviceValues.autostart;
			var values = lang.mixin({}, confValues, advancedConfValues);
			return this.standbyDuring(tools.umcpCommand('appcenter/configure', {application: this.app.id, autostart: autostart, values: values}));
		},

		onUpdate: function() {
		},

		onShowUp: function() {
		},

		onBack: function(applied) {
		}

	});
});

