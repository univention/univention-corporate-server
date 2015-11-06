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
			var title = _('Contact information for Password reset');
			document.title = title;
			var titleNode = dom.byId('title');
			put(titleNode, 'h1', title);
			put(titleNode, '!.dijitHidden');
		},

		_createContent: function() {
			var contentNode = dom.byId('content');
			var formNode = this._getFormNode();
			put(formNode, '[id=form].step!dijitHidden');
			put(contentNode, formNode);
		},

		_getFormNode: function() {
			var formNode = put('div[style="overflow: hidden;"]');
			put(formNode, 'p', _('If you want to reset your password in the future it is necessary to provide contact information. This information are required to automatically receive a token for setting a new password.'));

			// step 1 username and password
			this.usernameNode = put(formNode, 'div.step');
			put(this.usernameNode, 'p > b', _('Please enter your username and password to display your contact information.'));
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
					this._getContactInformation();
				}
			}));
			put(stepContent, this._username.domNode);
			this._username.startup();

			this._password = new TextBox({
				inlineLabel: _('Password'),
				isValid: function() {
					return !!this.get('value');
				},
				style: 'margin-top: 6px',
				required: true,
				type: 'password'
			});
			this._password.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._getContactInformation();
				}
			}));
			put(stepContent, this._password.domNode);
			this._password.startup();

			this._showContactInformationButton = new Button({
				label: _('Show contact information'),
				onClick: lang.hitch(this, '_getContactInformation')
			});
			put(stepContent, this._showContactInformationButton.domNode);

			// step 2 show and set contact information
			this.contactInformationNode = put(formNode, 'div.step.hide-step');
			put(this.contactInformationNode, 'p > b', _('Feel free to change your contact information. Press "Save" to confirm your changes.'));
			var stepContent = put(this.contactInformationNode, 'div.stepContent');
			this._contactInformation = new ContainerWidget({});
			put(stepContent, this._contactInformation.domNode);
			this._saveButton = new Button({
				label: _('Save'),
				onClick: lang.hitch(this, '_setContactInformation')
			});
			put(stepContent, this._saveButton.domNode);
			this._cancelButton = new Button({
				label: _('Cancel'),
				onClick: lang.hitch(this, '_deleteContactInformationNode')
			});
			put(stepContent, this._cancelButton.domNode);

			return formNode;
		},

		_getContactInformation: function() {
			this._username.set('disabled', true);
			this._password.set('disabled', true);
			this._showContactInformationButton.set('disabled', true);

			var validCredentials = 	this._username.isValid() && this._password.isValid();
			if (validCredentials) {
				this._buildContactInformation([{
					label: 'Email',
					id: 'email',
					value: 'keiser@univention.de'
				}, {
					label: 'SMS',
					id: 'sms',
					value: '0815'
				}]);
				//data = json.stringify({
				//	'username': this._username.get('value'),
				//	'password': this._password.get('value')
				//});
				//xhr.post('passwordreset/get_contact', {
				//	handleAs: 'json',
				//	headers: {
				//		'Content-Type': 'application/json'
				//	},
				//	data: data
				//}).then(lang.hitch(this, function(data) {
				//	lib._removeMessage();
				//	this._buildContactInformation(data.result);
				//}), lang.hitch(this, function(err){
				//	var message = err.name + ": " + err.message;
				//	if (err.response && err.response.data && err.response.data.message) {
				//		message = err.response.data.message;
				//	}
				//	lib.showMessage({
				//		content: message,
				//		targetNode: this.usernameNode,
				//		'class': '.error'
				//	});
				//	this._showContactInformationButton.set('disabled', false);
				//	this._username.set('disabled', false);
				//	this._password.set('disabled', false);
				//}));
			} else {
				this._showContactInformationButton.set('disabled', false);
				this._username.set('disabled', false);
				this._password.set('disabled', false);
			}

		},

		_buildContactInformation: function(options) {
			array.forEach(options, lang.hitch(this, function(obj, idx){
				var textBox = new TextBox({
					label: obj.label,
					value: obj.value,
					id: obj.id
				});
				this._contactInformation.addChild(textBox);
			}));
			put(this.contactInformationNode, '!hide-step');
		},

		_setContactInformation: function() {

		},

		_deleteContactInformationNode: function() {
			this._contactInformation.destroyDescendants();
			put(this.contactInformationNode, '.hide-step');
			this._showContactInformationButton.set('disabled', false);
			this._username.reset();
			this._password.reset();
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
						'Content-Type': 'application/json'
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
						'Content-Type': 'application/json'
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
					lib.fadeOutNode({
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
					this._token.set('disabled', true);
					this._newPassword.set('disabled', true);
					this._verifyPassword.set('disabled', true);
				}));
			} else {
				this._setPasswordButton.set('disabled', false);
				this._token.set('disabled', true);
				this._newPassword.set('disabled', true);
				this._verifyPassword.set('disabled', true);
			}
		},

		start: function() {
			this._createTitle();
			this._createContent();
		}
	};
});
