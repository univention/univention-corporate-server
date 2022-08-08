/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2020-2022 Univention GmbH
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
	"dojo/keys",
	"dojo/hash",
	"dojo/io-query",
	"dojo/dom-construct",
	"put-selector/put",
	"dojox/html/entities",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Button",
	"dompurify/purify",
	"./TextBox",
	"umc/i18n/tools",
	"umc/i18n!."
], function(lang, keys, dojoHash, ioQuery, domConstruct, put, entities, tools, dialog, Button, dompurify, TextBox, i18nTools, _) {

	return {
		hash: 'verifyaccount',
		enabledViaUcr: 'umc/self-service/account-verification/frontend/enabled',
		visible: true,

		title: _('Account verification'),
		contentContainer: null,
		_steps: null,
		_message: null,
		startup: function() {
			this._setMessage(null);
			this._fillInputFieldsFromHashes();
			if (this._canAutoVerify()) {
				this._verifyAccount(true);
			} else {
				this._focusFirstEmptyField();
			}
		},

		_focusFirstEmptyField: function() {
			// kinda not really focus first empty field
			if (this._username && !this._username.get('value')) {
				this._username.focus();
				return;
			}
			if (this._token) {
				this._token.focus();
				return;
			}
		},

		getTitle: function() {
			var locale = i18nTools.defaultLang().slice(0, 2);
			var ucrTitleKey = "umc/self-service/" + this.hash + "/title/" + locale;
			var ucrTitleKeyEnglish = "umc/self-service/" + this.hash + "/title/en";
			return tools.status(ucrTitleKey) || tools.status(ucrTitleKeyEnglish) || this.title;
		},

		getContent: function() {
			this.contentContainer = put('div.contentWrapper');
			put(this.contentContainer, 'h2', this.getTitle());
			this._createSteps();
			window.t = this;
			return this.contentContainer;
		},

		_setMessage: function(node) {
			if (this._message) {
				put(this._message, '!');
			}
			this._message = node;
			if (this._message) {
				put(this.contentContainer, this._message);
				put(this._steps, '.dijitDisplayNone');
			} else {
				put(this._steps, '!dijitDisplayNone');
			}
		},

		_fillInputFieldsFromHashes: function() {
			var hashes = this._getHashes();
			var username = hashes.username ? hashes.username : '';
			this._username.set('value', username);
			var token = hashes.token ? hashes.token : '';
			this._token.set('value', token);
		},

		_canAutoVerify: function() {
			return !!this._username.get('value') && !!this._token.get('value');
		},

		_createSteps: function() {
			this._steps = put(this.contentContainer, 'ol#VerifyContactSteps.PasswordOl');
			this._createUsername();
			this._createToken();
			this._createButtons();
		},

		_createUsername: function() {
			this._username = new TextBox({
				name: 'username'
			});
			this._username.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._verifyAccount(false);
				}
			}));
			this._username.startup();
			put(this._steps, 'li.step div.stepLabel $ +', _('Username'), this._username.domNode);
		},

		_createToken: function() {
			this._token = new TextBox({
				name: 'token'
			});
			this._token.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._verifyAccount(false);
				}
			}));
			this._token.startup();
			put(this._steps, 'li.step div.stepLabel $ +', _('Token'), this._token.domNode);
		},

		_createButtons: function() {
			var buttonRow = put(this._steps, 'div.umcPageFooter');
			var buttonsRight = put(buttonRow, 'div.umcPageFooterRight');

			this._requestNewTokenButton = new Button({
				label: _('Request new token'),
				onClick: lang.hitch(this, '_requestNewToken')
			});
			put(buttonsRight, this._requestNewTokenButton.domNode);

			this._verifyAccountButton = new Button({
				'class': 'dijitDefaultButton',
				label: _('Verify account'),
				onClick: lang.hitch(this, '_verifyAccount', false)
			});
			put(buttonsRight, this._verifyAccountButton.domNode);
		},

		_showVerificationMessage: function(res) {
			var msg = null;
			if (!res.success) {
				switch (res.failType) {
					case 'INVALID_INFORMATION':
						msg = _('The account could not be verified. Please verify your input.');
						dialog.alert(msg);
						this._setMessage(null);
						break;
				}
			} else {
				var status = '';
				switch (res.successType) {
					case 'VERIFIED':
						status = _('your account has been successfully verified');
						break;
					case 'ALREADY_VERIFIED':
						status = _('your account has already been verified');
						break;
				}
				msg = lang.replace('<div><p>{greeting}</p><p>{nextSteps}</p></div>', {
					greeting: _('Welcome <b>%s</b>, %s.', entities.encode(res.data.username), status),
					nextSteps: dompurify.sanitize(res.data.nextSteps)
				});
				msg = domConstruct.toDom(msg);
				this._setMessage(msg);
			}
		},

		_showRequestTokenMessage: function(res) {
			var msg = null;
			if (!res.success) {
				switch (res.failType) {
					case 'INVALID_INFORMATION':
						msg = _('A verification token could not be sent. Please verify your input.');
						dialog.alert(msg);
						this._setMessage(null);
						break;
				}
			} else {
				msg = _('Hello <b>%s</b>, we have sent you an email to your registered address. Please follow the instructions in the email to verify your account.', entities.encode(res.data.username));
				msg = domConstruct.toDom(msg);
				msg = put('p', msg);
				this._setMessage(msg);
			}
		},

		_requestNewToken: function() {
			var isValid = this._validateFields([this._username]);
			if (isValid) {
				var data = {
					'username': this._username.get('value')
				};
				var deferred = tools.umcpCommand('passwordreset/send_verification_token', data)
					.then(lang.hitch(this, function(res) {
						this._showRequestTokenMessage(res.result);
					}), lang.hitch(this, function(error) {
						this._setMessage(null);
					}));
				this.standbyDuring(deferred);
			} else {
				// fail-safe
				this._setMessage(null);
			}
		},

		_verifyAccount: function(autoVerify) {
			var isValid = this._validateFields([this._username, this._token]);
			if (isValid) {
				if (autoVerify) {
					var message = put('p', _('Your account is being verified.'));
					this._setMessage(message);
				}
				var data = {
					'username': this._username.get('value'),
					'token' : this._token.get('value'),
					'method': 'verify_email'
				};
				var deferred = tools.umcpCommand('passwordreset/verify_contact', data)
					.then(lang.hitch(this, function(res) {
						this._showVerificationMessage(res.result);
					}), lang.hitch(this, function() {
						this._setMessage(null);
					}));
				this.standbyDuring(deferred);
			} else {
				// fail-safe
				this._setMessage(null);
			}
		},

		_validateFields: function(fields) {
			// hacky. only the username is required for both _verifyAccount and _requestNewToken
			this._token.set('required', false);

			var firstInvalid = null;
			var isValid = true;
			fields.forEach(function(field) {
				field.set('required', true);
				isValid = isValid && field.validate();
				if (!isValid && !firstInvalid) {
					firstInvalid = field;
				}
			});
			if (firstInvalid) {
				firstInvalid.focusInvalid();
			}
			return isValid;
		},

		_getHashes: function() {
			return ioQuery.queryToObject(dojoHash());
		}
	};
});

