/*
 * Copyright 2015-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/lang",
	"dojo/on",
	"dojo/keys",
	"dijit/form/Button",
	"put-selector/put",
	"dojox/html/entities",
	"umc/tools",
	"umc/dialog",
	"./TextBox",
	"./PasswordBox",
	"./lib",
	"umc/i18n!."
], function(lang, on, keys, Button, put, entities, tools, dialog, TextBox, PasswordBox, lib, _) {

	return {
		title: _("Set new password"),
		desc: _("Set a new password: "),
		altDesc: _(""),
		hash: 'newpassword',
		contentContainer: null,
		steps: null,
		selectedRenewOption: null,
		startup: function() {
			if (!lib.getQuery('username')) {
				this._username.focus();
				return;
			} else if (this._username) {
				this._username.set('value', lib.getQuery('username'));
				this._username.set('disabled', true);
				return;
			}
			if (!lib.getQuery('token')) {
				this._token.focus();
				return;
			}
			this._newPassword.focus();
			return;
		},

		/**
		 * Returns the title of the subpage.
		 * */
		getTitle: function() {
			return _(this.title);
		},

		/**
		 * Returns the description for the subpage:
		 * Request New Password.
		 * */
		getRequestNewPassDesc: function() {
			return _(this.desc);
		},

		/**
		 * Returns the description for the subpage:
		 * Set New Password.
		 * */
		getSetNewPassDesc: function() {
			return _(this.altDesc);
		},

		/**
		 * Checks if the the query string contains credentials
		 * for setting a new password.
		 * True -Return a subpage to set a new password.
		 * False - Return a subpage to request a new password.
		 * */
		getContent: function() {
			this.contentContainer = put('div.contentWrapper');
			put(this.contentContainer, 'h2', this.getTitle());
			put(this.contentContainer, 'div.contentDesc', this.getSetNewPassDesc());
			put(this.contentContainer, this._getSetNewSteps());
			return this.contentContainer;
		},

		/**
		 * Return the steps for the subpage:
		 * Request New Password.
		 * If the steps do not exists, they will be generated.
		 * Note: Please call getContent for generating the steps.
		 * */
		_getRequestSteps: function() {
			if (!this.steps) {
				this.steps = put('ol#PasswordForgottenSteps.PasswordOl');
				this._createUsername();
			}
			return this.steps;
		},

		/**
		 * Return the steps for the subpage:
		 * Set New Password.
		 * If the steps do not exists, they will be generated.
		 * Note: Please call getContent for generating the steps.
		 * */
		_getSetNewSteps: function() {
			if (!this.steps) {
				this.steps = put('ol#PasswordForgottenSteps.PasswordOl');
				if (!lib.getQuery('username')) {
					this._createUsername();
				}
				if (!lib.getQuery('token')) {
					this._createToken();
				}
				this._createNewPassword();
				this._createSubmitNewPassword();
			}
			return this.steps;
		},

		/**
		 * Creates input field for username.
		 * */
		_createUsername: function() {
			var step = put('li.step');
			var label = put('div.stepLabel', _('Username'));
			put(step, label);
			this._username = new TextBox({
				'class': 'soloLabelPane',
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			this._username.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._setPassword();
				}
			}));
			this._username.startup();
			put(step, this._username.domNode);

			put(this.steps, step);
		},

		/**
		 * Creates input field for token.
		 * */
		_createToken: function() {
			var step = put('li.step');
			var label = put('div.stepLabel', _('Token'));
			put(step, label);
			this._token = new TextBox({
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
			this._token.startup();
			put(step, this._token.domNode);

			put(this.steps, step);
		},

		/**
		 * Creates input fields to set a new password.
		 */
		_createNewPassword: function() {
			var step = put('li.step');
			var label = put('div.stepLabel', _('New Password'));
			put(step, label);
			this._newPassword = new PasswordBox({
				'class': 'soloLabelPane'
			});
			this._newPassword.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._setPassword();
				}
			}));
			this._newPassword.startup();
			put(step, this._newPassword.domNode);
			put(this.steps, step);

			step = put('li.step');
			label = put('div.stepLabel', _('New Password (retype)'));
			put(step, label);
			this._verifyPassword = new TextBox({
				type: 'password',
				'class': 'soloLabelPane',
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
			this._verifyPassword.startup();
			put(step, this._verifyPassword.domNode);
			put(this.steps, step);
		},

		/**
		 * Creates submit button.
		 * */
		_createSubmitNewPassword: function() {
			var step = put('div.buttonRow.umcPageFooter');
			this._setPasswordButton = new Button({
				label: _('Change password'),
				onClick: lang.hitch(this, '_setPassword')
			});
			put(step, this._setPasswordButton.domNode);
			put(this.steps, step);
		},

		/**
		 * Sets the new password by sending it to the server.
		 */
		_setPassword: function() {
			var credentials = this._getCredentials();

			var isTokenAndNewPassValid = this.validateAllValues();
			if (isTokenAndNewPassValid) {
				this._disableInputs(true);
				var data = {
					'username': credentials.username,
					'password': credentials.password,
					'token' : credentials.token
				};
				tools.umcpCommand('passwordreset/set_password', data).then(lang.hitch(this, function(result) {
					dialog.confirm(entities.encode(result.message), [{label: _('OK'), name: 'submit'}]).then(function() {
						var redirectUrl = lib._getUrlForRedirect();
						if (redirectUrl) {
							window.open(redirectUrl, "_self");
						}
					});
				}), lang.hitch(this, function(){
					this._disableInputs(false);
				}));
			}
		},

		_validateField: function(field) {
			if (field.isValid()) {
				return true;
			}
			field._hasBeenBlurred = true;
			field.focus();
			field.validate();
			return false;
		},

		validateAllValues: function() {
			if (!lib.getQuery('username') && !this._validateField(this._username)) {
				return false;
			}
			if (!lib.getQuery('token') && !this._validateField(this._token)) {
				return false;
			}
			if (!this._validateField(this._newPassword)) {
				return false;
			}
			if (!this._validateField(this._verifyPassword)) {
				return false;
			}
			return true;
		},

		_disableInputs: function(/* boolean */ isDisabled) {
			this._setPasswordButton.set('disabled', isDisabled);
			if (this._username) {
				this._username.set('disabled', isDisabled);
			}
			if (this._token) {
				this._token.set('disabled', isDisabled);
			}
			this._newPassword.set('disabled', isDisabled);
			this._verifyPassword.set('disabled', isDisabled);
		},

		_resetInputs: function() {
			this._setPasswordButton.set('value', '');
			if (this._username) {
				this._username.set('value', '');
			}
			if (this._token) {
				this._token.set('value', '');
			}
			this._newPassword.set('value', '');
			this._verifyPassword.set('value', '');
			this._disableInputs(false);
		},

		/**
		 * Gets credentials (token and username).
		 * */
		_getCredentials: function() {
			var username = lib.getQuery('username') || this._username.get('value');
			var token = lib.getQuery('token') || this._token.get('value');
			var password = this._verifyPassword.get('value');

			return {
				username: username,
				token: token,
				password: password
			};
		}
	};
});
