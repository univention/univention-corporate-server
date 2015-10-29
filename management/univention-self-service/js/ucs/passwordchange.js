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
	"dojo/dom",
	"dojo/json",
	"dojo/request/xhr",
	"dijit/form/Button",
	"put-selector/put",
	"./TextBox",
	"./PasswordBox",
	"./PasswordInputBox",
	"./i18n!"
], function(lang, on, dom, json, xhr, Button, put, TextBox, PasswordBox, PasswordInputBox, _) {
	return {
		_createTitle: function() {
			var title = _('Change Password');
			document.title = title;
			var titleNode = dom.byId('title');
			put(titleNode, 'h1', title);
			put(titleNode, '!.dijitHidden');
		},

		_createForm: function() {
			var contentNode = dom.byId('content');
			var tabNode = put(contentNode, 'div');
			put(tabNode, 'p > b', _('Change your password'));
			put(tabNode, 'p', _('Please follow this description I still have to write'));

			// create input field for username
			this._username = new TextBox({
				inlineLabel: _('Username'),
				required: true
			});
			put(tabNode, '>', this._username.domNode);
			this._username.startup();

			// create input field for old password
			this._oldPassword = new PasswordBox({
				inlineLabel: _('Old password'),
				required: true
			});
			put(tabNode, '>', this._oldPassword.domNode);
			this._oldPassword.startup();

			// create input fields for new password
			this._newPassword = new PasswordInputBox({
				inlineLabel: _('New password'),
				twoRows: true,
				required: true
			});
			put(tabNode, '>', this._newPassword.domNode);
			this._newPassword.startup();

			// create submit button
			this._submitButton = new Button({
				label: _('Submit'),
				onClick: lang.hitch(this, '_submit')
			});
			put(tabNode, '>', this._submitButton.domNode);
		},

		_submit: function() {
			var allInputFieldsValid = this._username.isValid() &&
				this._oldPassword.isValid() &&
				this._newPassword.isValid();
			
			if (allInputFieldsValid) {
				data = json.stringify({
					'username': this._username.get('value'),
					'password': this._oldPassword.get('value'),
					'new_password': this._newPassword.get('value')
				});

				xhr.post('passwordchange/', {
					handleAs: 'json',
					headers: {
						'Content-Type': 'application/json'
					},
					data: data
				}).then(function() {
					// TODO show msg
				}, lang.hitch(this, function(err) {
					// TODO show msg
				}));
			}
		},

		start: function() {
			this._createTitle();
			this._createForm();
		}
	};
});
