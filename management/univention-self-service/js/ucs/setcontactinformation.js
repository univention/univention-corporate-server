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
			var siteDescription = _('On this page you can set your contact information to reset your password in the future. This information are required to receive a token that is necessary to renew the password.');
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
		},

		_getFormNode: function() {
			var formNode = put('div[style="overflow: hidden;"]');

			// step 1 username and password
			this.usernameNode = put(formNode, 'div.step');
			put(this.usernameNode, 'p > b', _('Please enter your username and password to display your contact information.'));
			var stepContent = put(this.usernameNode, 'div.stepContent');

			this._username = new TextBox({
				label: _('Username'),
				'class': 'doubleLabelPane left',
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			this._username.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._getContactInformation();
				}
			}));
			put(stepContent, this._username.label.domNode);
			this._username.startup();

			this._password = new TextBox({
				label: _('Password'),
				'class': 'doubleLabelPane',
				isValid: function() {
					return !!this.get('value');
				},
				required: true,
				type: 'password'
			});
			this._password.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._getContactInformation();
				}
			}));
			put(stepContent, this._password.label.domNode);
			this._password.startup();

			this._showContactInformationButton = new Button({
				label: _('Show contact information'),
				onClick: lang.hitch(this, '_getContactInformation')
			});
			put(stepContent, this._showContactInformationButton.domNode);

			// step 2 show and set contact information
			this.contactInformationNode = put(formNode, 'div.step.hide-step');
			put(this.contactInformationNode, 'p', _('Feel free to change your contact information. Press "Save" to confirm your changes.'));
			stepContent = put(this.contactInformationNode, 'div.stepContent');

			this._email = new TextBox({
				label: _('EMail'),
				'class': 'doubleLabelPane left',
				id: 'email'
			});
			this._email.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._setContactInformation();
				}
			}));
			put(stepContent, this._email.label.domNode);

			this._mobile = new TextBox({
				label: _('Mobile'),
				'class': 'doubleLabelPane',
				id: 'mobile'
			});
			this._mobile.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._setContactInformation();
				}
			}));
			put(stepContent, this._mobile.label.domNode);

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

			var validCredentials = this._username.isValid() && this._password.isValid();
			if (validCredentials) {
				data = json.stringify({
					'username': this._username.get('value'),
					'password': this._password.get('value')
				});
				xhr.post('passwordreset/get_contact', {
					handleAs: 'json',
					headers: {
						'Content-Type': 'application/json',
						'Accept-Language': getQuery('lang') || 'en-US'
					},
					data: data
				}).then(lang.hitch(this, function(data) {
					lib._removeMessage();
					this._displayContactInformation(data.result);
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
					this._showContactInformationButton.set('disabled', false);
					this._username.set('disabled', false);
					this._password.set('disabled', false);
				}));
			} else {
				this._showContactInformationButton.set('disabled', false);
				this._username.set('disabled', false);
				this._password.set('disabled', false);
			}
		},

		_displayContactInformation: function(contactInformation) {
			var mappingIdAndInput = {
				'email': this._email,
				'mobile': this._mobile
			};

			array.forEach(contactInformation, lang.hitch(this, function(contact){
				var currentInput = mappingIdAndInput[contact.id];
				if (currentInput) {
					currentInput.set('value', contact.value);
					//currentInput._updateInlineLabelVisibility();
				}
			}));
			put(this.contactInformationNode, '!hide-step');
		},

		_setContactInformation: function() {
			this._cancelButton.set('disabled', true);
			this._saveButton.set('disabled', true);

			data = this._getNewContactInformation();
			var isValidMail = this._validateMail(data.email);
			if (isValidMail) {
				xhr.post('passwordreset/set_contact', {
						handleAs: 'json',
						headers: {
							'Content-Type': 'application/json',
							'Accept-Language': getQuery('lang') || 'en-US'
						},
						data: json.stringify(data)
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
							targetNode: this.contactInformationNode,
							'class': '.error'
						});
						this._cancelButton.set('disabled', false);
						this._saveButton.set('disabled', false);
					}));
			} else {
				this._cancelButton.set('disabled', false);
				this._saveButton.set('disabled', false);
			}
		},

		_getNewContactInformation: function() {
			var contactInformation = {
				'username': this._username.get('value'),
				'password': this._password.get('value'),
				'email': this._email.get('value'),
				'mobile': this._mobile.get('value')
			};
			return contactInformation;
		},

		_validateMail: function(email) {
			var reg = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
			var isValid = !email.length || reg.test(email);
			if(!isValid) {
				lib.showMessage({
					content: _('Please enter a valid email address.'),
					'class': '.error',
					targetNode: this.contactInformationNode
				});
			}
			return isValid;
		},

		_deleteContactInformationNode: function() {
			put(this.contactInformationNode, '.hide-step');
			this._showContactInformationButton.set('disabled', false);
			this._username.reset();
			this._password.reset();
		},

		start: function() {
			this._createTitle();
			this._createContent();
		}
	};
});
