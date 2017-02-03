/*
 * Copyright 2011-2016 Univention GmbH
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
	"dojo/json",
	"dijit/form/ValidationTextBox",
	"./_FormWidgetMixin",
	"./LabelPane",
	"./lib",
	"umc/i18n!."
], function(declare, lang, array, when, json, ValidationTextBox, _FormWidgetMixin, LabelPane, lib, _) {
	return declare('umc.widgets.PasswordBox', [ ValidationTextBox, _FormWidgetMixin ], {
		label: null,
		type: 'password',
		required: true,
		missingMessage: _('This value is required.'),
		promptMessage: '',
		invalidMessage: '',
		tooltipPosition: ['below', 'after'],
		active_password_qualities: null,
		password_qualities: {
			'credit/digits': {
				reg: '.{%[0]}',
				promptMessage: _('Required length:')
			},
			'credit/lower': {
				reg: '^(.*?[a-z]){%[0],}',
				promptMessage: _('Required number of lower case letters:')
			},
			'credit/upper': {
				reg: '^(.*?[A-Z]){%[0],}',
				promptMessage: _('Required number of upper case letters:')
			},
			'credit/other': {
				reg: '^(.*?[^a-zA-Z0-9]){%[0],}',
				promptMessage: _('Required number of special characters (nor digit or letters):')
			},
			'forbidden/chars': {
				reg: "^((?![%[0]]).)*$",
				promptMessage: _('Forbidden chars:')
			},
			'required/chars': {
				reg: '[%[0]]',
				promptMessage: _('Required chars:')
			}
		},

		buildRendering: function() {
			this.inherited(arguments);
			if (this.label !== undefined) {
				this._createLabelNode();
			}
			when(lib.getBackendInformation()).then(lang.hitch(this, function(data) {
				var result = JSON.parse(data, true);
				this.active_password_qualities = result.password_quality;
				this.setPromptMessage(result.password_quality);
			}));
		},

		isValid: function() {
			return this.validator();
		},

		_hasValue: function(password) {
			if (password) {
				return true;
			} else {
				this.setPromptMessage();
				this.invalidMessage = _('This value is required.');
				return false;
			}
		},

		/** Checks if the password meets the active password qualities.
		 * @param {string} password - Current value of the input box.
		 * **/
		_hasValidPasswordQuality: function(password) {
			var result = array.filter(this.active_password_qualities, lang.hitch(this, function(iqual) {
				var quality = this.password_qualities[iqual.name];
				var reg_str = lang.replace(quality.reg, [iqual.value], /\%\[([^\]]+)\]/g);
				var reg = new RegExp(reg_str);
				if (reg.test(password)) {
					return true;
				} else {
					this.invalidMessage += lang.replace('{0} {1}{2}', [quality.promptMessage, iqual.value, '</br>']);
					this.promptMessage = this.invalidMessage;
					return false;
				}
			}));
			if (result.length === this.active_password_qualities.length) {
				this.setValid(true);
				return true;
			} else {
				return false;
			}
		},

		validator: function() {
			this.invalidMessage = '';
			this.promptMessage = '';
			var password = this.get('value');
			return this._hasValue(password) && this._hasValidPasswordQuality(password);
		},

		setPromptMessage: function(active_qualities) {
			var qualities = active_qualities || this.active_password_qualities;
			if (qualities && qualities.length) {
				this.promptMessage = _('The password must fullfill following conditions:');
				array.forEach(qualities, lang.hitch(this, function(iqual) {
					var quality = this.password_qualities[iqual.name];
					this.promptMessage += lang.replace('{0}{1} {2}', ['</br>', quality.promptMessage, iqual.value]);
				}));
			}
		},

		_createLabelNode: function() {
			this.label = new LabelPane({
				content: this,
				'class': this['class']
			});
			this.set('class', '');
		},

		reset: function() {
			this.set('value', '');
			this.set('disabled', false);
			this.setValid();
		}
	});
});
