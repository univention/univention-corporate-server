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
					this._buildContactInformation(data.result);
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
			this._cancelButton.set('disabled', true);
			this._saveButton.set('disabled', true);
			// also alle Input fields
			// does isValid make Sense?
			data = this._getNewContactInformation();
			xhr.post('passwordreset/set_contact', {
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
						targetNode: this.contactInformationNode,
						'class': '.error'
					});
					this._cancelButton.set('disabled', false);
					this._saveButton.set('disabled', false);
				}));
		},

		_getNewContactInformation: function() {
			var contactInformation = {
				'username': this._username.get('value'),
				'password': this._password.get('value')
			};
			array.forEach(this._contactInformation.getChildren(), function(child) {
				var key = child.get('id');
				contactInformation[key] = child.get('value');
			});
			return json.stringify(contactInformation);
		},

		_deleteContactInformationNode: function() {
			this._contactInformation.destroyDescendants();
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
