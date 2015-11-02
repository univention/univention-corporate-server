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
	"./ContainerWidget",
	"./LabelPane",
	"./TextBox",
	"./RadioButton",
	"./i18n!"
], function(lang, array, on, keys, dom, json, xhr, Button, put, ContainerWidget, LabelPane, TextBox, RadioButton, _) {

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
			this._tokenOptions = new ContainerWidget({});
			put(this.tokenNode, this._tokenOptions.domNode);
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
			this._removeMessage();
			this._usernameButton.set('disabled', true);

			if (this._username.isValid()) {
				// TODO delete mockup
				// this._buildTokenOptions(['sms', 'email']);

				data = json.stringify({
					'username': this._username.get('value')
				});
				xhr.post('passwordreset/get_reset_methods', {
					handleAs: 'json',
					headers: {
						'Content-Type': 'application/json'
					},
					data: data
				}).then(lang.hitch(this, function(data) {
					this._buildTokenOptions(data.message);
				}), lang.hitch(this, function(err){
					var message = err.name + ": " + err.message;
					if (err.response && err.response.data && error.response.data.message) {
						message = error.response.data.message;
					}
					this._showMessage(message, '.error');
					this._usernameButton.set('disabled', false);
				}));
			} else {
				this._usernameButton.set('disabled', false);
			}
		},

		_buildTokenOptions: function(options) {
			// TODO make the RadioButtons visible
			array.forEach(options, lang.hitch(this, function(item, idx){
				var radioButton = new RadioButton({
					name: 'button' + idx,
					label: item,
					value: item,
					checked: idx === 0,
					radioButtonGroup: 'token',
					_categoryID: 'token'
				});
				var label = new LabelPane({
					'class': 'ucsRadioButtonLabel',
					content: radioButton
				});
				this._tokenOptions.addChild(label);
			}));
			put(this.tokenNode, '!hide-step');
		},

		_requestToken: function() {
			this._removeMessage();
			this._requestTokenButton.set('disabled', true);

			// TODO check which RadioButton is selected
			// Make it possible for the user to select another option

			data = json.stringify({
				'username': this._username.get('value'),
				'method': 'foo' //TODO get the value of the checked RadioButton
			});
			xhr.post('passwordreset/send_token', {
				handleAs: 'json',
				headers: {
					'Content-Type': 'application/json'
				},
				data: data
			}).then(lang.hitch(this, function(data) {
				put(this.newPasswordNode, '!hide-step');
			}), lang.hitch(this, function(err){
				var message = err.name + ": " + err.message;
				if (err.response && err.response.data && error.response.data.message) {
					message = error.response.data.message;
				}
				this._showMessage(message, '.error');
				this._requestTokenButton.set('disabled', false);
			}));
		},

		_setPassword: function() {
			this._removeMessage();
			this._setPasswordButton.set('disabled', true);

			var isTokenAndNewPassValid = this._token.isValid() &&
				this._verifyPassword;

			if (isTokenAndNewPassValid) {
				data = json.stringify({
					'username': this._username.get('value'),
					'password': this._verifyPassword.get('value'),
					'token' : this._token.get('value')
				});
				xhr.post('passwordreset/set_password', {
					handleAs: 'json',
					headers: {
						'Content-Type': 'application/json'
					},
					data: data
				}).then(lang.hitch(this, function(data) {
					this._setPasswordButton.set('disabled', true);
					this._token.set('disabled', true);
					this._newPassword.set('disabled', true);
					this._verifyPassword.set('disabled', true);
					this._showMessage(data.message, '.success');
				}), lang.hitch(this, function(err){
					var message = err.name + ": " + err.message;
					if (err.response && err.response.data && error.response.data.message) {
						message = error.response.data.message;
					}
					this._showMessage(message, '.error');
					this._setPasswordButton.set('disabled', false);
				}));
			} else {
				this._setPasswordButton.set('disabled', false);
			}
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
