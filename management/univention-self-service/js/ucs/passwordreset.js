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
	"./i18n!."
], function(lang, array, on, keys, dom, json, xhr, Button, put, ContainerWidget, LabelPane, TextBox, RadioButton, _) {

	return {
		selectedTokenMethod: null,
		
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
			put(dom.byId('navigation'), '!');
			put(formNode, 'p', _('In order to reset your password please carry out the following steps: '));

			// step 1 username
			this.usernameNode = put(formNode, 'div.step');
			put(this.usernameNode, 'p > b', _('1. Enter your username.'));
			var stepContent = put(this.usernameNode, 'div.stepContent');
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
			put(stepContent, this._username.domNode);
			this._username.startup();
			this._usernameButton = new Button({
				label: _('Confirm username'),
				onClick: lang.hitch(this, '_getResetMethods')
			});
			put(stepContent, this._usernameButton.domNode);

			// step 2 token
			this.tokenNode = put(formNode, 'div.step.hide-step');
			put(this.tokenNode, 'p > b', _('2. Choose a method to receive a token.'));
			var stepContent = put(this.tokenNode, 'div.stepContent');
			this._tokenOptions = new ContainerWidget({});
			put(stepContent, this._tokenOptions.domNode);
			this._requestTokenButton = new Button({
				label: _('Request token'),
				onClick: lang.hitch(this, '_requestToken')
			});
			put(stepContent, this._requestTokenButton.domNode);

			// step 3 use the token to set a new password
			this.newPasswordNode = put(formNode, 'div.step.hide-step');
			put(this.newPasswordNode, 'p > b', _('3. Enter the token and a new password.'));
			var stepContent = put(this.newPasswordNode, 'div.stepContent');
			this._token = new TextBox({
				inlineLabel: _('Token'),
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			put(stepContent, this._token.domNode);
			this._token.startup();
			this._newPassword = new TextBox({
				inlineLabel: _('New password'),
				type: 'password',
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			put(stepContent, this._newPassword.domNode);
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
			this._verifyPassword.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._setPassword();
				}
			}));
			put(stepContent, this._verifyPassword.domNode);
			this._verifyPassword.startup();
			this._setPasswordButton = new Button({
				label: _('Change password'),
				onClick: lang.hitch(this, '_setPassword')
			});
			put(stepContent, this._setPasswordButton.domNode);
			
		},

		_getResetMethods: function() {
			this._removeMessage();
			this._username.set('disabled', true);
			this._usernameButton.set('disabled', true);

			if (this._username.isValid()) {
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
					this._buildTokenOptions(data.result);
				}), lang.hitch(this, function(err){
					var message = err.name + ": " + err.message;
					if (err.response && err.response.data && err.response.data.message) {
						message = err.response.data.message;
					}
					this._showMessage(message, '.error', this.usernameNode);
					this._usernameButton.set('disabled', false);
					this._username.set('disabled', false);
				}));
			} else {
				this._usernameButton.set('disabled', false);
				this._username.set('disabled', false);
			}
		},

		_buildTokenOptions: function(options) {
			array.forEach(options, lang.hitch(this, function(obj, idx){
				var radioButton = new RadioButton({
					name: 'button' + idx,
					label: obj.label,
					method: obj.id,
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
			if (options.length === 1) {
				this._requestToken();
			}
		},

		_requestToken: function() {
			this._removeMessage();

			// get selected method for requesting a token
			array.some(this._tokenOptions.getChildren(), lang.hitch(this, function(tokenLabel) {
				var radioButton = tokenLabel.getChildren()[0];
				if (radioButton.checked) {
					this.selectedTokenMethod = {
						label: radioButton.get('label'),
						method: radioButton.get('method')
					}
				}
			}));

			if (this.selectedTokenMethod) {
				this._requestTokenButton.set('disabled', true);
				data = json.stringify({
					'username': this._username.get('value'),
					'method': this.selectedTokenMethod.method
				});
				xhr.post('passwordreset/send_token', {
					handleAs: 'json',
					headers: {
						'Content-Type': 'application/json'
					},
					data: data
				}).then(lang.hitch(this, function(data) {
					this._showMessage(data.message, '.success', this.tokenNode);
					put(this.newPasswordNode, '!hide-step');
				}), lang.hitch(this, function(err){
					var message = err.name + ": " + err.message;
					if (err.response && err.response.data && err.response.data.message) {
						message = err.response.data.message;
					}
					this._showMessage(message, '.error', this.tokenNode);
					this._requestTokenButton.set('disabled', false);
				}));
			}
		},

		_setPassword: function() {
			this._removeMessage();
			this._setPasswordButton.set('disabled', true);

			var isTokenAndNewPassValid = this._token.isValid() &&
				this._newPassword.isValid() &&
				this._verifyPassword.isValid();

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
					var message = data.message;
					message += _("</br><a href='/'>Back to the overview.</a>");
					this._showMessage(message, '.success', this.newPasswordNode);
				}), lang.hitch(this, function(err){
					var message = err.name + ": " + err.message;
					if (err.response && err.response.data && err.response.data.message) {
						message = err.response.data.message;
					}
					this._showMessage(message, '.error', this.newPasswordNode);
					this._setPasswordButton.set('disabled', false);
				}));
			} else {
				this._setPasswordButton.set('disabled', false);
			}
		},

		_showMessage: function(msg, msgClass, targetNode) {
			targetNode = targetNode || dom.byId("form");
			var msgNode = dom.byId('msg');
			if (!msgNode) {
				msgNode = put('div[id=msg]');
				put(targetNode, 'div', msgNode);
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
