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
/*global define require console window */

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/keys",
	"dojo/dom",
	"dojo/json",
	"dojo/request/xhr",
	"dijit/form/Button",
	"put-selector/put",
	"./TextBox",
	"./RadioButton",
	"./i18n!"
], function(lang, array, on, keys, dom, json, xhr, Button, put, TextBox, RadioButton, _) {

	return {
		_createTitle: function() {
			var title = _('Password Reset');
			document.title = title;
			var titleNode = dom.byId('title');
			put(titleNode, 'h1', title);
			put(titleNode, '!.dijitHidden');
		},

		_createForm: function() {
			var contentNode = dom.byId('content');
			var formNode = put(contentNode, 'div[id=form]');
			put(formNode, 'p > b', _('Reset your password'));
			put(formNode, 'p', _('Please carry out the following steps: '));

			// step 1 username
			this.usernameNode = put(formNode, 'div.step');
			put(this.usernameNode, 'p', _('1. Enter your username.'));
			this._username = new TextBox({
				inlineLabel: _('Username'),
				isValid: function() {
					return !!this.get('value');
				},
				style: 'margin-top: 6px',
				required: true
			});
			this._username.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._getResetMethods();
				}
			}));
			put(this.usernameNode, this._username.domNode);
			this._username.startup();
			this._usernameButton = new Button({
				label: _('Submit'),
				onClick: lang.hitch(this, '_getResetMethods')
			});
			put(this.usernameNode, this._usernameButton.domNode);

			// step 2 token
			this.tokenNode = put(formNode, 'div.step.hide-step');
			put(this.tokenNode, 'p', _('2. Choose a method to receive a token.'));
			put(this.tokenNode, 'div#token-options');
			this._requestTokenButton = new Button({
				label: _('Submit'),
				onClick: lang.hitch(this, '_requestToken')
			});
			put(this.tokenNode, this._requestTokenButton.domNode);

			// step 3 use the token to set a new password
			this.newPasswordNode = put(formNode, 'div.step.hide-step');
			put(this.newPasswordNode, 'p', _('3. Enter the token and a new password.'));
			this._token = new TextBox({
				inlineLabel: _('Token'),
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			put(this.newPasswordNode, this._token.domNode);
			this._token.startup();
			this._newPassword = new TextBox({
				inlineLabel: _('New password'),
				type: 'password',
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			put(this.newPasswordNode, this._newPassword.domNode);
			this._newPassword.startup();
			this._verifyPassword = new TextBox({
				inlineLabel: _('New password (retype)'),
				type: 'password',
				isValid: lang.hitch(this, function() {
					return this._newPassword.get('value') ===
						this._verifyPassword.get('value');
				}),
				invalidMessage: _('The passwords do not match, please retype again.'),
				required: true
			});
			put(this.newPasswordNode, this._verifyPassword.domNode);
			this._verifyPassword.startup();
			this._setPasswordButton = new Button({
				label: _('Submit'),
				onClick: lang.hitch(this, '_setPassword')
			});
			put(this.newPasswordNode, this._setPasswordButton.domNode);
			
		},

		_getResetMethods: function() {
			//TODO
			put(this.tokenNode, '!hide-step');
			this._username.set('disabled', true);
			this._usernameButton.set('disabled', true);
			this._addTokenOptions(["sms", "email"]);
		},

		_requestToken: function() {
			//TODO
			put(this.newPasswordNode, '!hide-step');
			this._requestTokenButton.set('disabled', true);
		},

		_addTokenOptions: function(options) {
			var tokenOptionNode = dom.byId('token-options');
			array.forEach(options, function(item){
				var radioButton = new RadioButton({
					radioButtonGroup: 'token',
					name: '_tokenOption',
					label: '<strong>' + item + '</strong>',
					checked: false
				});
				put(tokenOptionNode, radioButton.domNode);
			});
		},

		_setPassword: function() {
			this._token.set('disabled', true);
			this._newPassword.set('disabled', true);
			this._verifyPassword.set('disabled', true);
			this._setPasswordButton.set('disabled', true);
		},

		_showMessage: function(msg, msgClass) {
			var formNode = dom.byId('form');
			var msgNode = dom.byId('msg');
			if (!msgNode) {
				msgNode = put('div[id=msg]');
				put(formNode, 'div', msgNode);
			}

			if (msgClass) {
				put(msgNode, msgClass);
			}
			// replace newlines with BR tags
			msg = msg.replace(/\n/g, '<br/>');
			msgNode.innerHTML = msg;
		},

		_removeMessage: function() {
			var msgNode = dom.byId('msg');
			if (msgNode) {
				put(msgNode, "!");
			}
		},

		start: function() {
			this._createTitle();
			this._createForm();
		}
	};
});
