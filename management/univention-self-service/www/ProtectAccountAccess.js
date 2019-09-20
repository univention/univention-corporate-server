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
/*global define, dijit*/

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/keys",
	"dijit/form/Button",
	"put-selector/put",
	"login",
	"umc/tools",
	"umc/dialog",
	"./lib",
	"./PasswordBox",
	"./TextBox",
	"umc/i18n!."
], function(lang, array, on, keys, Button, put, login, tools, dialog, lib, PasswordBox, TextBox, _) {

	return {
		title: _('Protect account'),
		desc: _('Everyone forgets his password now and then. Protect yourself and activate the opportunity to set a new password.'),
		hash: 'setcontactinformation',
		contentContainer: null,
		steps: null,

		startup: function() {
			if (this._username.value !== '') {
				this._password.focus();
			} else {
				this._username.focus();
			}
		},

		/**
		 * Returns the title of the subpage.
		 * */
		getTitle: function() {
			return _(this.title);
		},

		/**
		 * Returns the description of the subpage.
		 * */
		getDesc: function() {
			return _(this.desc);
		},

		/**
		 * Return the content node of the subpage.
		 * If the content does not exists, it will be generated.
		 * */
		getContent: function() {
			if (!this.contentContainer) {
				this.contentContainer = put('div.contentWrapper');
				put(this.contentContainer, 'h2', this.getTitle());
				put(this.contentContainer, 'div.contentDesc', this.getDesc());
				put(this.contentContainer, this._getSteps());
			}
			return this.contentContainer;
		},

		/**
		 * Return the steps for the content node.
		 * If the steps do not exists, they will be generated.
		 * Note: Please call getContent for generating the steps.
		 * */
		_getSteps: function() {
			if (!this.steps) {
				this.steps = put('ol#PasswordProtectSteps.PasswordOl');
				this._createUsername();
				this._createPassword();
				this._createSubmit();
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
			login.onInitialLogin(lang.hitch(this, function(username) {
				this._username.set('value', tools.status('username'));
				this._username.set('disabled', true);
			}));
			this._username.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._getContactInformation();
				}
			}));
			this._username.startup();
			put(step, this._username.domNode);
			put(this.steps, step);
		},

		/**
		 * Creates input field for password.
		 * */
		_createPassword: function() {
			var step = put('li.step');
			var label = put('div.stepLabel', _('Password'));
			put(step, label);
			this._password = new PasswordBox({
				'class': 'soloLabelPane',
				required: true,
			});
			this._password.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._getContactInformation();
				}
			}));
			this._password.startup();
			put(step, this._password.domNode);
			put(this.steps, step);
		},

		/**
		 * Creates submit button.
		 * */
		_createSubmit: function() {
			var step = put('div.buttonRow.umcPageFooter');
			this._showContactInformationButton = new Button({
				label: _('Next'),
				onClick: lang.hitch(this, '_getContactInformation')
			});
			put(step, this._showContactInformationButton.domNode);
			put(this.steps, step);
		},

		/**
		 * Requests available renew options.
		 * */
		_getContactInformation: function() {
			this._username.set('disabled', true);
			this._password.set('disabled', true);
			this._showContactInformationButton.set('disabled', true);

			var validCredentials = this._username.isValid() && this._password.isValid();
			if (validCredentials) {
				var data = {
					'username': this._username.get('value'),
					'password': this._password.get('value')
				};
				tools.umcpCommand('passwordreset/get_contact', data).then(lang.hitch(this, function(data) {
					put(this._showContactInformationButton.domNode, '.dijitDisplayNone');
					this._createRenewOptions(data.result);
				}), lang.hitch(this, function(){
					this._showContactInformationButton.set('disabled', false);
					this._username.reset();
					this._username.set('disabled', false);
					//this._username.focus(); Not possible because the error dialog steals the focus
					this._password.reset();
					this._password.set('disabled', false);
				}));
			} else {
				this._showContactInformationButton.set('disabled', false);
				this._username.set('disabled', false);
				this._password.set('disabled', false);
				if (!this._username.isValid()) {
					this._username._hasBeenBlurred = true;
					this._username.focus();
					this._username.validate();
				} else if (!this._password.isValid()) {
					this._password._hasBeenBlurred = true;
					this._password.focus();
					this._password.validate();
				}
			}
		},

		/**
		 * Creates renew options.
		 * @param {array} renewOptions - List of renew options.
		 * */
		_createRenewOptions: function(renewOptions) {
			var options = renewOptions.length ? renewOptions : [{id: "email", value: '', label: "E-Mail"}];
			var step = put('li.step');
			this._renewOptions = step;
			var label = put('div.stepLabel', _('Activate renew options.'));
			put(step, label);
			this._renewInputs = array.map(options, lang.hitch(this, function(option) {
				var optionNode = put('div');
				var input = new TextBox({
					id: option.id + '_check',
					value: option.value
				});
				var inputRetype = new TextBox({
					value: option.value,
					id: option.id,
					isValid: function() {
						return input.get('value') === this.get('value');
					},
					invalidMessage: _('The entries do not match, please retype again.'),
				});
				inputRetype.on('keyup', lang.hitch(this, function(evt) {
					if (evt.keyCode === keys.ENTER) {
						this._setContactInformation();
					}
				}));
				input.on('keyup', lang.hitch(this, function(evt) {
					if (evt.keyCode === keys.ENTER) {
						this._setContactInformation();
					}
				}));
				inputRetype.startup();
				put(optionNode, 'label[for=' + option.id + '_check]', option.label);
				put(optionNode, input.domNode);
				put(optionNode, 'label[for=' + option.id + ']', option.label + _(' (retype)'));
				put(optionNode, inputRetype.domNode);
				put(step, optionNode);
				return {
					id: option.id,
					getValue: function() { return inputRetype.get('value');},
					isValid: function() { return inputRetype.isValid();},
					validate: function() { return inputRetype.validate();},
					focus: function() {return inputRetype.focus();},
					focusInput: function() {return input.focus();},
					reset: function() {input.reset(); inputRetype.reset();}
				};
			}));
			this._saveButton = new Button({
				label: _('Save'),
				onClick: lang.hitch(this, '_setContactInformation')
			});

			this._cancelButton = new Button({
				label: _('Cancel'),
				onClick: lang.hitch(this, '_deleteRenewOptions')
			});
			var buttonRow = put(step, 'div.buttonRow.umcPageFooter');
			put(buttonRow, this._cancelButton.domNode);
			put(buttonRow, this._saveButton.domNode);
			put(this.steps, step);
			this._renewInputs[0].focusInput();
		},

		/**
		 * Send renew options to the server.
		 * */
		_setContactInformation: function() {
			this._cancelButton.set('disabled', true);
			this._saveButton.set('disabled', true);

			var allOptionsAreValid = array.every(this._renewInputs, function(input){
				if (input.isValid()) {
					return true;
				} else {
					input.focus();
					input.validate();
					return false;
				}
			});

			if (allOptionsAreValid) {
				var data = this._getNewContactInformation();
				tools.umcpCommand('passwordreset/set_contact', data).then(lang.hitch(this, function() {
						var redirectUrl = lib._getUrlForRedirect();
						if (redirectUrl) {
							window.open(redirectUrl, "_self");
						}
					}), lang.hitch(this, function(){
						array.forEach(this._renewInputs, function(input){
							input.reset();
						});
						this._cancelButton.set('disabled', false);
						this._saveButton.set('disabled', false);
					}));
			} else {
				this._cancelButton.set('disabled', false);
				this._saveButton.set('disabled', false);
			}
		},

		/**
		 * Gets current renew options and credentials.
		 * */
		_getNewContactInformation: function() {
			var contactInformation = {
				'username': this._username.get('value'),
				'password': this._password.get('value')
			};
			array.forEach(this._renewInputs, function(input){
				contactInformation[input.id] = input.getValue();
			});

			// ugly hack because the backend urgently needs an empty string
			// for mail and for mobile
			array.forEach(['email', 'mobile'], function(key) {
				if (!contactInformation[key]) {
					contactInformation[key] = '';
				}
			});
			return contactInformation;
		},

		/**
		 * Deletes renew options node.
		 * */
		_deleteRenewOptions: function() {
			put(this._renewOptions, '!');
			put(this._showContactInformationButton.domNode, '!dijitDisplayNone');
			this._showContactInformationButton.set('disabled', false);
			this._username.reset();
			this._password.reset();
			this._password.set('disabled', false);
			// destroy email input widget
			array.forEach(this._renewInputs, function(renewInput) {
				var Input = dijit.byId(renewInput.id);
				Input.destroy();
				var inputCheck = dijit.byId(renewInput.id + '_check');
				inputCheck.destroy();
			});
			//this._username.focus();
		}
	};
});
