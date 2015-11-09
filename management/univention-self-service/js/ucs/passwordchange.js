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
	"dojo/on",
	"dojo/keys",
	"dojo/dom",
	"dojo/json",
	"dojo/request/xhr",
	"dijit/form/Button",
	"put-selector/put",
	"./TextBox",
	"./lib",
	"./i18n!."
], function(lang, on, keys, dom, json, xhr, Button, put, TextBox, lib, _) {

	return {
		_createTitle: function() {
			var title = _('Change Password');
			var siteDescription = lang.replace(_('On this page you can change your password. If you want to reset your password instead use this link to the <a href="/univention-self-service/{0}#passwordreset">password reset</a> page.', [lib.getCurrentLanguageQuery()]));
			document.title = title;
			var titleNode = dom.byId('title');
			put(titleNode, 'h1', title);
			put(titleNode, 'p', { innerHTML : siteDescription });
			put(titleNode, '!.dijitHidden');
		},

		_createContent: function() {
			var contentNode = dom.byId('content');
			var formNode = this._getFormNode();
			put(formNode, '[id=form]!dijitHidden');
			put(contentNode, formNode);
		},

		_getFormNode: function() {
			var formNode = put('div[style="overflow: hidden;"]');
			put(formNode, 'p > b', _('Please provide the required data to change your password.'));

			// create input field for username
			this._username = new TextBox({
				inlineLabel: _('Username'),
				isValid: function() {
					return !!this.get('value');
				},
				style: 'margin-top: 6px',
				required: true
			});
			put(formNode, '>', this._username.domNode);
			this._username.startup();

			// create input field for old password
			this._oldPassword = new TextBox({
				inlineLabel: _('Old password'),
				type: 'password',
				isValid: function() {
					return !!this.get('value');
				},
				style: 'margin-top: 6px',
				required: true
			});
			put(formNode, '>', this._oldPassword.domNode);
			this._oldPassword.startup();

			// create input fields for new password
			this._newPassword = new TextBox({
				inlineLabel: _('New password'),
				type: 'password',
				isValid: function() {
					return !!this.get('value');
				},
				style: 'margin-top: 12px',
				required: true
			});
			put(formNode, '>', this._newPassword.domNode);
			this._newPassword.startup();

			// create input fields for new password
			this._verifyPassword = new TextBox({
				inlineLabel: _('New password (retype)'),
				type: 'password',
				isValid: lang.hitch(this, function() {
					return this._newPassword.get('value') ===
						this._verifyPassword.get('value');
				}),
				invalidMessage: _('The passwords do not match, please retype again.'),
				style: 'margin-top: 6px',
				required: true
			});
			put(formNode, '>', this._verifyPassword.domNode);
			this._verifyPassword.startup();

			// create submit button
			this._submitButton = new Button({
				label: _('Change password'),
				style: 'margin-top: 12px',
				onClick: lang.hitch(this, '_submit')
			});
			put(formNode, '>', this._submitButton.domNode);

			// let the user submit form by pressing ENTER
			on(document, "keyup", lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER && !this._submitButton.get('disabled')) {
					this._submit();
				}
			}));

			return formNode;
		},

		_submit: function() {
			this._showValidStatusOfInputFields();
			this._submitButton.set('disabled', true);
			var allInputFieldsAreValid = this._username.isValid() &&
				this._oldPassword.isValid() &&
				this._newPassword.isValid() &&
				this._verifyPassword.isValid();

			if (allInputFieldsAreValid) {
				data = json.stringify({
					'username': this._username.get('value'),
					'password': this._oldPassword.get('value'),
					'new_password': this._newPassword.get('value')
				});

				xhr.post('passwordchange/', {
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
					this._clearAllInputFields();
				}), lang.hitch(this, function(err) {
					var message = err.name + ": " + err.message;
					if (err.response && err.response.data && err.response.data.message) {
						message = err.response.data.message;
					}
					lib.showMessage({content: message, 'class': '.error'});
				})).always(lang.hitch(this, function(){
					this._submitButton.set('disabled', false);
				}));
			} else {
				this._submitButton.set('disabled', false);
			}
		},

		_showValidStatusOfInputFields: function() {
			this._username.setValid(this._username.isValid());
			this._oldPassword.setValid(this._oldPassword.isValid());
			this._newPassword.setValid(this._newPassword.isValid());
			//this._verifyPassword.setValid(this._verifyPassword.isValid());
		},

		_clearAllInputFields: function() {
			this._username.reset();
			this._oldPassword.reset();
			this._newPassword.reset();
			this._verifyPassword.reset();
		},

		start: function() {
			this._createTitle();
			this._createContent();
		}
	};
});
