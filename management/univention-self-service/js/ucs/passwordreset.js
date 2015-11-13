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
	"./lib",
	"./i18n!."
], function(lang, array, on, keys, dom, json, xhr, Button, put, ContainerWidget, LabelPane, TextBox, RadioButton, lib, _) {

	return {
		selectedTokenMethod: null,
		
		_createTitle: function() {
			var title = _('Password Reset');
			var siteDescription = _('On this page you can reset your password or provide contact information for setting a new password in the future.');
			document.title = title;
			var titleNode = dom.byId('title');
			put(titleNode, 'h1', title);
			put(titleNode, 'p', siteDescription);
			put(titleNode, '!.dijitHidden');
		},

		_createContent: function() {
			var contentNode = dom.byId('content');
			var formNode = this._getFormNode();
			put(formNode, '[id=form].step!dijitHidden');
			put(contentNode, formNode);
			this._fillContentByUrl();
		},

		_getFormNode: function() {
			var formNode = put('div[style="overflow: hidden;"]');

			// step 1 username and link to contact information
			this.usernameNode = put(formNode, 'div.step');
			put(this.usernameNode, 'p > b', _('Reset your password.'));
			put(this.usernameNode, 'p', _('Please provide your username to receive a token that is required to reset your password.'));
			var stepContent = put(this.usernameNode, 'div.stepContent');
			this._username = new TextBox({
				label: _('Username'),
				'class': 'soloLabelPane',
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			this._username.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._getResetMethods();
				}
			}));
			put(stepContent, this._username.label.domNode);
			this._username.startup();
			this._usernameButton = new Button({
				label: _('Confirm username'),
				onClick: lang.hitch(this, '_getResetMethods')
			});
			put(stepContent, this._usernameButton.domNode);

			// contact information
			this.contactNode = put(formNode, 'div.step');
			put(this.contactNode, 'p > b', _('Provide your contact information.'));
			put(this.contactNode, 'p', {
				innerHTML: lang.replace(_('Please click the following link to <a href="/univention-self-service/{0}#setcontactinformation">change your contact information</a> for resetting the password in the future.', [lib.getCurrentLanguageQuery()]))
			});

			// step 2 token
			this.tokenNode = put(formNode, 'div.step.hide-step');
			var skipStep = function() { 
				put(this.newPasswordNode, '!hide-step');
				this._requestTokenButton.set('disabled', true);
			};
			var descRequestToken = put(this.tokenNode, 'p', _('Please choose a method to receive the token.'));
			put(descRequestToken, 'span', {
				innerHTML: _(' If you already have a token you can <a>skip this step</a>.'),
				onclick: lang.hitch(this, skipStep)
			});
			stepContent = put(this.tokenNode, 'div.stepContent');
			this._tokenOptions = new ContainerWidget({});
			put(stepContent, this._tokenOptions.domNode);
			this._requestTokenButton = new Button({
				label: _('Request token'),
				onClick: lang.hitch(this, '_requestToken')
			});
			put(stepContent, this._requestTokenButton.domNode);

			// step 3 use the token to set a new password
			this.newPasswordNode = put(formNode, 'div.step.hide-step');
			var prevStep = function() { 
				put(this.newPasswordNode, '.hide-step');
				put(this.tokenNode, '!dijitHidden');
				put(this.tokenNode, '!hide-step');
				this._requestTokenButton.set('disabled', false);
			};
			var descNewPassword = put(this.newPasswordNode, 'p', _('Please enter the token and your new password.'));
			put(descNewPassword, 'span', {
				innerHTML: _(' If your token is expired you can <a>go back one step to request a new one</a>.'),
				onclick: lang.hitch(this, prevStep)
			});
			stepContent = put(this.newPasswordNode, 'div.stepContent');
			this._token = new TextBox({
				label: _('Token'),
				'class': 'soloLabelPane',
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			this._token.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._setPassword();
				}
			}));
			put(stepContent, this._token.label.domNode);
			this._token.startup();

			this._newPassword = new TextBox({
				label: _('New password'),
				type: 'password',
				'class': 'doubleLabelPane left',
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			this._newPassword.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._setPassword();
				}
			}));
			put(stepContent, this._newPassword.label.domNode);
			this._newPassword.startup();

			this._verifyPassword = new TextBox({
				label: _('New password (retype)'),
				type: 'password',
				'class': 'doubleLabelPane',
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
			put(stepContent, this._verifyPassword.label.domNode);
			this._verifyPassword.startup();
			this._setPasswordButton = new Button({
				label: _('Change password'),
				onClick: lang.hitch(this, '_setPassword')
			});
			put(stepContent, this._setPasswordButton.domNode);
			return formNode;
		},

		_getResetMethods: function() {
			this._username.set('disabled', true);
			this._usernameButton.set('disabled', true);

			if (this._username.isValid()) {
				data = json.stringify({
					'username': this._username.get('value')
				});
				xhr.post('passwordreset/get_reset_methods', {
					handleAs: 'json',
					headers: {
						'Content-Type': 'application/json',
						'Accept-Language': getQuery('lang') || 'en-US'
					},
					data: data
				}).then(lang.hitch(this, function(data) {
					lib._removeMessage();
					put(this.contactNode, '!');
					this._buildTokenOptions(data.result);
				}), lang.hitch(this, function(err){
					var message = err.name + ": " + err.message;
					if (err.response && err.response.data && err.response.data.message) {
						message = err.response.data.message;
					}
					lib.showMessage({
						content: message,
						targetNode: this.usernameNode,
						'class': '.error'
					});
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
		},

		_requestToken: function() {
			// get selected method for requesting a token
			array.some(this._tokenOptions.getChildren(), lang.hitch(this, function(tokenLabel) {
				var radioButton = tokenLabel.getChildren()[0];
				if (radioButton.checked) {
					this.selectedTokenMethod = {
						label: radioButton.get('label'),
						method: radioButton.get('method')
					};
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
						'Content-Type': 'application/json',
						'Accept-Language': getQuery('lang') || 'en-US'
					},
					data: data
				}).then(lang.hitch(this, function(data) {
					lib.showMessage({
						content: data.message,
						targetNode: this.tokenNode,
						'class': '.success'
					});
					put(this.newPasswordNode, '!hide-step');
				}), lang.hitch(this, function(err){
					var message = err.name + ": " + err.message;
					if (err.response && err.response.data && err.response.data.message) {
						message = err.response.data.message;
					}
					lib.showMessage({
						content: message,
						targetNode: this.tokenNode,
						'class': '.error'
					});
					this._requestTokenButton.set('disabled', false);
				}));
			}
		},

		_setPassword: function() {
			this._setPasswordButton.set('disabled', true);
			this._token.set('disabled', true);
			this._newPassword.set('disabled', true);
			this._verifyPassword.set('disabled', true);

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
						'Content-Type': 'application/json',
						'Accept-Language': getQuery('lang') || 'en-US'
					},
					data: data
				}).then(lang.hitch(this, function(data) {
					lib._removeMessage();
					var callback = function() {
						lib.showLastMessage({
							content: data.message,
							'class': '.success'
						});
					};
					lib.wipeOutNode({
						node: dom.byId('form'),
						callback: callback
					});
				}), lang.hitch(this, function(err){
					var message = err.name + ": " + err.message;
					if (err.response && err.response.data && err.response.data.message) {
						message = err.response.data.message;
					}
					lib.showMessage({
						content: message,
						targetNode: this.newPasswordNode,
						'class': '.error'
					});
					this._setPasswordButton.set('disabled', false);
					this._token.set('disabled', false);
					this._newPassword.set('disabled', false);
					this._verifyPassword.set('disabled', false);
				}));
			} else {
				this._setPasswordButton.set('disabled', false);
				this._token.set('disabled', false);
				this._newPassword.set('disabled', false);
				this._verifyPassword.set('disabled', false);
			}
		},

		_fillContentByUrl: function() {
			// checks if the url contains a username and a token
			// show and fill the corresponding input fields if true
			var token = getQuery('token');
			var username = getQuery('username');
			if (token && username) {
				this._username.set('value', username);
				this._token.set('value', token);
				put(this.contactNode, '!');
				this._getResetMethods();
				this._requestTokenButton.set('disabled', true);
				put(this.tokenNode, '.dijitHidden');
				put(this.newPasswordNode, '!hide-step');
			}
		},

		start: function() {
			this._createTitle();
			this._createContent();
		}
	};
});
