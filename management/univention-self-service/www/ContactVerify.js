/*
 * Copyright 2020 Univention GmbH
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
	"dijit/form/Button",
	"put-selector/put",
	"dojox/html/entities",
	"umc/tools",
	"./TextBox",
	"umc/i18n!."
], function(lang, keys, dojoHash, ioQuery, domConstruct, Button, put, entities, tools, TextBox, _) {

	return {
		hash: 'contactverify',
		enabledViaUcr: false,
		visible: false,

		title: _('Account verification'),
		contentContainer: null,
		_steps: null,
		startup: function() {
			this._createSteps();
			if (this._username) {
				this._username.focus();
				return;
			}
			if (this._token) {
				this._token.focus();
				return;
			}
		},

		getTitle: function() {
			return this.title;
		},

		getContent: function() {
			this.contentContainer = put('div.contentWrapper');
			put(this.contentContainer, 'h2', this.getTitle());
			return this.contentContainer;
		},

		_createSteps: function() {
			this._clearSteps();
			var hashes = this._getHashes();
			if (hashes.verified) {
				this._createSuccessStep(hashes.username);
			} else {
				this._steps = put('ol#VerifyContactSteps.PasswordOl');
				var createButton = false;
				if (!hashes.username) {
					this._createUsername();
					createButton = true;
				}
				if (!hashes.token) {
					this._createToken();
					createButton = true;
				}
				if (createButton) {
					this._createVerifyAccountButton();
				} else {
					this._steps = put('p', _('Your account is being verified.'));
					this._verifyAccount();
				}
				put(this.contentContainer, this._steps);
			}
		},

		_createUsername: function() {
			this._username = new TextBox({
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			this._username.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._verifyAccount();
				}
			}));
			this._username.startup();
			put(this._steps, 'li.step div.stepLabel $ +', _('Username'), this._username.domNode);
		},

		_createToken: function() {
			this._token = new TextBox({
				isValid: function() {
					return !!this.get('value');
				},
				required: true
			});
			this._token.on('keyup', lang.hitch(this, function(evt) {
				if (evt.keyCode === keys.ENTER) {
					this._verifyAccount();
				}
			}));
			this._token.startup();
			put(this._steps, 'li.step div.stepLabel $ +', _('Token'), this._token.domNode);
		},

		_createVerifyAccountButton: function() {
			this._verifyAccountButton = new Button({
				label: _('Verify account'),
				onClick: lang.hitch(this, '_verifyAccount')
			});
			put(this._steps, 'div.buttonRow.umcPageFooter', this._verifyAccountButton.domNode);
		},

		_createSuccessStep: function(username) {
			var msg = _('<p>Welcome <b>%s</b>. Your account has been successfully verified.</p>', entities.encode(username));
			this._steps = domConstruct.toDom(msg);
			put(this.contentContainer, this._steps);
		},

		_clearSteps: function() {
			this._username = null;
			this._token = null;
			this._verifyAccountButton = null;
			if (this._steps) {
				put(this._steps, '!');
			}
		},

		_verifyAccount: function() {
			var credentials = this._getCredentials();
			var isUsernameAndTokenValid = this._validateAllValues();
			if (isUsernameAndTokenValid) {
				var data = {
					'username': credentials.username,
					'token' : credentials.token,
					'method': 'verify_email'
				};
				var deferred = tools.umcpCommand('passwordreset/verify_contact', data)
					.then(lang.hitch(this, function(data) {
						dojoHash(ioQuery.objectToQuery({
							page: this.hash,
							username: data.result,
							verified: true
						}));
					}));
				this.standbyDuring(deferred);
			}
		},

		_validateField: function(field) {
			if (field.isValid()) {
				return true;
			}
			field.focusInvalid();
			return false;
		},

		_validateAllValues: function() {
			var hashes = this._getHashes();
			if (!hashes.username && !this._validateField(this._username)) {
				return false;
			}
			if (!hashes.token && !this._validateField(this._token)) {
				return false;
			}
			return true;
		},

		_getHashes: function() {
			return ioQuery.queryToObject(dojoHash());
		},

		_getCredentials: function() {
			var hashes = this._getHashes();
			return {
				username: hashes.username || this._username.get('value'),
				token: hashes.token || this._token.get('value')
			};
		}
	};
});

