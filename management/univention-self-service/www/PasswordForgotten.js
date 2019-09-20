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
	"dojo/hash",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/keys",
	"dojo/io-query",
	"dijit/form/Button",
	"put-selector/put",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane",
	"./TextBox",
	"umc/widgets/RadioButton",
	"umc/i18n!."
], function(hash, lang, array, on, keys, ioQuery, Button, put, tools, dialog, ContainerWidget, LabelPane, TextBox, RadioButton, _) {

	return {
		title: _("Password forgotten"),
		desc: _("Forgot your password? Set a new one: "),
		altDesc: _("Set a new password!"),
		hash: 'passwordreset',
		contentContainer: null,
		steps: null,
		selectedRenewOption: null,
		startup: function() {
			this._username.focus();
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
		 * Checks if the the query string contains credentials
		 * for setting a new password.
		 * True -Return a subpage to set a new password.
		 * False - Return a subpage to request a new password.
		 * */
		getContent: function() {
			this.contentContainer = put('div.contentWrapper');
			put(this.contentContainer, 'h2', this.getTitle());
			put(this.contentContainer, 'div.contentDesc', this.getRequestNewPassDesc());
			put(this.contentContainer, this._getRequestSteps());
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
		 * Creates input field for username and submit button.
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
					this._getResetMethods();
				}
			}));
			this._username.startup();
			put(step, this._username.domNode);

			this._usernameButton = new Button({
				label: _('Next'),
				onClick: lang.hitch(this, '_getResetMethods')
			});
			var buttonRow = put(step, 'div.buttonRow.umcPageFooter');
			put(buttonRow, this._usernameButton.domNode);
			put(this.steps, step);
		},

		/**
		 * Gets the available renew options for the user from
		 * the server.
		 * */
		_getResetMethods: function() {
			this._username.set('disabled', true);
			this._usernameButton.set('disabled', true);

			if (this._username.isValid()) {
				var data = {
					'username': this._username.get('value')
				};
				tools.umcpCommand('passwordreset/get_reset_methods', data).then(lang.hitch(this, function(data) {
					put(this._usernameButton.domNode, '.dijitDisplayNone');
					this._createRenewOptions(data.result);
				}), lang.hitch(this, function(){
					this._usernameButton.set('disabled', false);
					this._username.set('value', '');
					this._username.set('disabled', false);
				}));
			} else {
				this._usernameButton.set('disabled', false);
				this._username.set('disabled', false);
			}
		},

		/**
		 * Creates a list of all options which are
		 * available to request a new password.
		 * @param {array} options - List of password renew options.
		 * */
		_createRenewOptions: function(options) {
			var step = put('li.step.hide-step');
			var label = put('div.stepLabel', _('Please choose an option to renew your password.'));
			put(step, label);
			var renewOptions = this._renderRenewOptions(options);
			put(label, renewOptions);
			this._requestTokenButton = new Button({
				label: _('Next'),
				onClick: lang.hitch(this, '_requestToken')
			});
			var buttonRow = put(step, 'div.buttonRow.umcPageFooter');
			put(buttonRow, this._requestTokenButton.domNode);
			put(this.steps, step);
			var firstRenewOptions = renewOptions.firstChild.children[2].firstChild;
			firstRenewOptions.focus();
		},

		/**
		 * Renders a pair of label and radioButton for each
		 * renew option.
		 * */
		_renderRenewOptions: function(options) {
			this._tokenOptions = new ContainerWidget({});
			array.forEach(options, lang.hitch(this, function(obj, idx){
				var radioButton = new RadioButton({
					name: 'button' + idx,
					label: obj.label,
					method: obj.id,
					checked: idx === 0,
					radioButtonGroup: 'token',
					_categoryID: 'token'
				});
				radioButton.on('keyup', lang.hitch(this, function(evt) {
					if (evt.keyCode === keys.ENTER) {
						this._requestToken();
					}
				}));
				var label = new LabelPane({
					'class': 'ucsRadioButtonLabel',
					content: radioButton
				});
				this._tokenOptions.addChild(label);
			}));
			return this._tokenOptions.domNode;
		},

		/**
		 * Requests a mail or pin from the server to renew the
		 * password.
		 * */
		_requestToken: function() {
			//TODO: Display the renew option for mobilenumber
			//TODO: Add an option to request a new mail/sms
			if (this._getRenewOption()) {
				this._requestTokenButton.set('disabled', true);
				var data = {
					'username': this._username.get('value'),
					'method': this.selectedRenewOption.method
				};
				tools.umcpCommand('passwordreset/send_token', data).then(lang.hitch(this, function(data) {
					var username = this._username.get('value');
					dialog.alert(data.message);
					put(this.steps.children[1], "!");
					this._username.set('value', '');
					this._username.set('disabled', false);
					put(this._usernameButton.domNode, '!.dijitDisplayNone');
					this._usernameButton.set('disabled', false);
					hash(ioQuery.objectToQuery({page: "newpassword", username: username}));
				}), lang.hitch(this, function() {
					this._requestTokenButton.set('disabled', false);
				}));
			}
		},

		/**
		 * Gets the selected renew option.
		 * */
		_getRenewOption: function() {
			array.some(this._tokenOptions.getChildren(), lang.hitch(this, function(option) {
				var radioButton = option.getChildren()[0];
				if (radioButton.checked) {
					this.selectedRenewOption= {
						label: radioButton.get('label'),
						method: radioButton.get('method')
					};
				}
			}));
			return this.selectedRenewOption;
		},

		/**
		 * Creates a message with instructions about what
		 * todo next to renew the password.
		 * */
		_showNewPasswordHowTo: function() {
			// TODO: add option for sms
			var step = put('li.step');
			var label = put('div.stepLabel', _('You have mail!'));
			put(step, label);
			var msg = put('div.soloLabelPane', _('We have send you an e-mail to your alternative e-mail address, that you have provided on the page "Protect Account Access". Please check your mails and follow the link to renew your password.'));
			put(step, msg);
			var hint = put('div.soloLabelPane', _('If you did not received an e-mail please check your spam directory or use this link to go back to step 2.'));
			put(step, hint);
			put(this.steps, step);
		},
	};
});
