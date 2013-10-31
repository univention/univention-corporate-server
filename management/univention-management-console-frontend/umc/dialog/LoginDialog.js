/*
 * Copyright 2011-2013 Univention GmbH
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
/*global define console window setTimeout */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/aspect",
	"dojo/has",
	"dojo/on",
	"dojo/mouse",
	"dojo/dom",
	"dojo/query",
	"dojo/dom-attr",
	"dojo/dom-class",
	"dojo/Deferred",
	"dijit/Dialog",
	"dijit/DialogUnderlay",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/LabelPane",
	"umc/widgets/ComboBox",
	"umc/widgets/StandbyMixin",
	"umc/i18n/tools",
	"umc/i18n!umc/app",
	"dojo/domReady!"
], function(declare, lang, array, win, aspect, has, on, mouse, dom, query, attr, domClass, Deferred, Dialog, DialogUnderlay, tools, Text, LabelPane, ComboBox, StandbyMixin, i18nTools, _) {
	return declare("umc.dialog.LoginDialog", [StandbyMixin], {
		// our own variables
		_connections: null,
		_iframe: null,
		_languageBox: null,
		_languageLabel: null,
		_text: null,

		_username: null,
		_password: null,
		_newPassword: null,
		_updateFormDeferred: null,

		// internal flag whether the dialog is rendered or not
		_isRendered: false,

		open: false,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.containerNode = dom.byId('umc_LoginDialog');
			this.domNode = dom.byId('umc_LoginWrapper');
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._updateFormDeferred = new Deferred();
			this._updateFormDeferred.resolve(false); // may update form, dont show new password

			// set the properties for the dialog underlay element
			this.underlayAttrs = {
				dialogId: this.id,
				'class': 'dijitDialogUnderlay'
			};

			this._iframe = dom.byId('umc_LoginDialog_Iframe');
			// initialize the iframe
			this._initForm();

			// create the upper info text
			this._text = new Text({
				style: 'margin-left: auto; margin-right: auto; margin-top: 1em; width: 280px;',
				content: ''
			});

			// create the language_combobox
			this._languageBox = new ComboBox({
				staticValues: i18nTools.availableLanguages,
				value: i18nTools.defaultLang(),
				sizeClass: null
			});
			this._languageLabel = new LabelPane({
				label: _('Language'),
				content: this._languageBox
			});

			// automatically resize the DialogUnderlay container
			this.own(on(win.global, 'resize', lang.hitch(this, function() {
				if (Dialog._DialogLevelManager.isTop(this)) {
					DialogUnderlay._singleton.layout();
				}
			})));
		},

		postCreate: function() {
			this.inherited(arguments);

			this._text.placeAt(this.containerNode, 'first');
			this._languageLabel.placeAt('umc_LoginDialog_FormContainer');
		},

		startup: function() {
			this.inherited(arguments);

			// we need to manually startup the widgets
			this._languageBox.startup();
			this._languageLabel.startup();

			// register onchange event
			// watch('value') will not be triggered when
			// the ComboBox has to take the first choice
			// while dojo wanted to use another locale
			// (e.g. because of navigator.language)
			this._languageBox.on('change', function(newLang) {
				i18nTools.setLanguage(newLang);
			});
		},

		updateForm: function(passwordExpired, statusMessage, detail) {
			this._passwordExpired = passwordExpired;
			var localisedMessage = statusMessage;
			if (detail) {
				// details are not localised. they are sent in English (if recognized in UMC-Server.Auth) or as the raw string returned from Kerberos!
				var newPasswordFailed;
				switch (detail) {
					// setting new password failed!
					case 'The password is too short':
						newPasswordFailed = _('The password is too short');
						break;
					case 'The password is too simple':
						newPasswordFailed = _('The password is too simple');
						break;
					case 'The password is a palindrome':
						newPasswordFailed = _('The password is a palindrome');
						break;
					case 'The password is based on a dictionary word':
						newPasswordFailed = _('The password is based on a dictionary word');
						break;
					case 'The password was already used':
						newPasswordFailed = _('The password was already used');
						break;
					case 'The password does not contain enough different characters':
						newPasswordFailed = _('The password does not contain enough different characters');
						break;
					case 'The authentication has failed':
						break;
					default:
						if (detail.slice(0, 2) === ': ') { // Kerberos error message starts with :
							newPasswordFailed = _('The reason could not be determined') + '. ' + _('In case it helps, the raw error message will be displayed') + detail;
						} else {
							//console.warn('Unknown error message', detail);
							if (this._newPassword) {
								// obviously we wanted to change the password
								newPasswordFailed = _('The reason could not be determined');
							}
						}
						break;
				}
				if (newPasswordFailed) {
					localisedMessage = _('The system does not allow changing the password') + '. ' + newPasswordFailed;
					this._passwordExpired = true;
				}
			}
			if (localisedMessage.slice(-1) !== '.') {
				localisedMessage += '.';
			}
			this._updateFormDeferred.resolve(this._passwordExpired);
			this.set('LoginMessage', localisedMessage);
		},

		_setLoginMessageAttr: function(message) {
			var logindialog = query('.umc_LoginMessage');
			logindialog[0].innerHTML = message;
			logindialog.style('display', 'block');
		},

		_initForm: function() {
			// wait until the iframe is completely loaded
			setTimeout(lang.hitch(this, function() {
				// check whether the form is available or not
				var state = lang.getObject('contentWindow.state', false, this._iframe);
				if (state === 'loaded') {
					this._updateFormDeferred.then(lang.hitch(this, function(showNewPassword) {
						// we are able to access the form
						win.withGlobal(this._iframe.contentWindow, lang.hitch(this, function() {
							// because of the iframe we need to manually translate the content
							attr.set(dom.byId('umc_LabelPane_Username'), 'innerHTML', _('Username'));
							attr.set(dom.byId('umc_LabelPane_Password'), 'innerHTML', _('Password'));
							attr.set(dom.byId('umc_LabelPane_NewPassword'), 'innerHTML', _('New Password'));
							attr.set(dom.byId('umc_LabelPane_NewPasswordRetype'), 'innerHTML', _('%(label)s (retype)', {label: _('New Password')}));
							attr.set(dom.byId('umc_SubmitButton_label'), 'innerHTML', _('Login'));
							if (showNewPassword) {
								domClass.add('umc_OuterLabelPane_Username', 'dijitHidden');
								domClass.add('umc_OuterLabelPane_Password', 'dijitHidden');
								domClass.remove('umc_OuterLabelPane_NewPassword', 'dijitHidden');
								domClass.remove('umc_OuterLabelPane_NewPasswordRetype', 'dijitHidden');
								if (this._username) {
									dom.byId('umc_UsernameInput').value = this._username;
									tools.status('username', this._username); // already set status, otherwise _setInitialFocus may cause problems
								}
								if (this._password) {
									dom.byId('umc_PasswordInput').value = this._password;
								}
								if (!has('touch')) {
									dom.byId('umc_NewPasswordInput').focus()
								}
							}
						}));
					}));

					// each time the page is loaded, we need to connect to the form events
					this._connectEvents();

					this._isRendered = true;
					lang.setObject('contentWindow.state', 'initialized', this._iframe);
					this._initForm();
				} else {
					// we can't access the form, or it has already been initialized
					// ... trigger the function again to monitor reloads
					this._initForm();
				}
			}), 100);
		},

		_connectEvents: function() {
			// TODO: cleanup?
			var form;
			var usernameInput;
			var usernameContainer;
			var passwordInput;
			var passwordContainer;
			var newPasswordInput;
			var newPasswordContainer;
			var newPasswordRetypeInput;
			var newPasswordRetypeContainer;

			win.withGlobal(this._iframe.contentWindow, lang.hitch(this, function() {
				form = dom.byId('umc_Form');
				usernameInput = dom.byId('umc_UsernameInput');
				usernameContainer = dom.byId('umc_UsernameContainer');
				passwordInput = dom.byId('umc_PasswordInput');
				passwordContainer = dom.byId('umc_PasswordContainer');
				newPasswordInput = dom.byId('umc_NewPasswordInput');
				newPasswordContainer = dom.byId('umc_NewPasswordContainer');
				newPasswordRetypeInput = dom.byId('umc_NewPasswordRetypeInput');
				newPasswordRetypeContainer = dom.byId('umc_NewPasswordRetypeContainer');
			}));

			this._connections = [];
			// register all events
			this._connections.push(
				on(form, 'submit', lang.hitch(this, function(evt) {
					if (newPasswordInput.value !== newPasswordRetypeInput.value) {
						this.set('LoginMessage', _('The passwords do not match, please retype again.'));
						evt.preventDefault();
						return;
					}
					var username = usernameInput.value;
					var password = passwordInput.value;
					var newPassword = newPasswordInput.value;
					this._authenticate(username, password, newPassword);
					this._isRendered = false;
					this._initForm();
				}))
			);

			var fields = [
				[usernameInput, usernameContainer],
				[passwordInput, passwordContainer],
				[newPasswordInput, newPasswordContainer],
				[newPasswordRetypeInput, newPasswordRetypeContainer]
			];
			var settingsArray = [
				[mouse.enter, this._setHover, true],
				[mouse.leave, this._setHover, false],
				['focus', this._setFocus, true],
				['blur', this._setFocus, false]
			];
			array.forEach(fields, lang.hitch(this, function(field) {
				var input = field[0];
				var container = field[1];
				array.forEach(settingsArray, lang.hitch(this, function(setting) {
					var evt = setting[0];
					var func = setting[1];
					var flag = setting[2];
					this._connections.push(on(input, evt, function(e) {
						func(container, flag);
					}));
				}));
			}));
		},

		_disconnectEvents: function() {
			array.forEach(this._connections, function(icon) {
				icon.remove();
			});
		},

		_setInitialFocus: function() {
			win.withGlobal(this._iframe.contentWindow, lang.hitch(this, function() {
				if (tools.status('username')) {
					// username is specified, we need to auto fill
					// the username and disable the textbox.
					attr.set('umc_UsernameInput', 'value', tools.status('username'));
					if (!has('touch')) {
						dom.byId('umc_PasswordInput').focus();
					}
					this._setFocus('umc_PasswordContainer', true);

					// disable the username field during relogin, i.e., when the GUI has been previously set up
					if (tools.status('setupGui')) {
						attr.set('umc_UsernameInput', 'disabled', true);
						domClass.add('umc_UsernameContainer', 'dijitTextBoxDisabled dijitValidationTextBoxDisabled dijitDisabled');
					}
				} else {
					// initial focus on username input
					if (!has('touch')) {
						dom.byId('umc_UsernameInput').focus();
					}
					this._setFocus('umc_UsernameContainer', true);
				}
			}));
		},

		_getFocusItems: function(domNode) {
			this._setInitialFocus();
		},

		_setFocus: function(obj, enable) {
			if (enable === true) {
				domClass.add(obj, 'dijitTextBoxFocused dijitValidationTextBoxFocused dijitFocused');
			} else if (enable === false) {
				domClass.remove(obj, 'dijitTextBoxFocused dijitValidationTextBoxFocused dijitFocused');
			}
		},

		_setHover: function(obj, enable) {
			if (enable === true) {
				domClass.add(obj, 'dijitTextBoxHover dijitValidationTextBoxHover dijitHover');
			} else if (enable === false) {
				domClass.remove(obj, 'dijitTextBoxHover dijitValidationTextBoxHover dijitHover');
			}
		},

		_authenticate: function(username, password, new_password) {
			this.standby(true);
			// save in case password expired and username and password have to be sent again
			this._username = username;
			this._password = password;
			args = {
				username: username,
				password: password
			};
			if (new_password) {
				this._newPassword = new_password;
				args.new_password = new_password;
			}
			this._updateFormDeferred = new Deferred();
			tools.umcpCommand('auth', args).then(lang.hitch(this, function(data) {
				// delete password ASAP. should not be stored
				this._username = null;
				this._password = null;
				this._newPassword = null;
				this._passwordExpired = false;
				this._updateFormDeferred.resolve(this._passwordExpired);

				// disable standby in any case
				this.standby(false);

				// make sure that we got data
				this.onLogin(username);
				this.hide();
			}), lang.hitch(this, function(error) {
				// disable standby in any case
				this.standby(false);
				this._setInitialFocus();
				Dialog._DialogLevelManager.show(this, this.underlayAttrs);
				Dialog._DialogLevelManager.hide(this);
			}));
		},

		show: function() {
			// only open the dialog if it has not been opened before
			if (this.get('open')) {
				return;
			}
			this.set('open', true);

			// update info text
			var msg = '';
			if (tools.status('setupGui')) {
				// user has already logged in before, show message for relogin
				msg = '<p>' + _('Your session has been closed due to inactivity. Please login again.') + '</p>';
			} else {
				msg = '<p>' + _('Welcome to Univention Management Console. Please enter your domain username and password for login.') + '</p>';

				// Show warning if connection is unsecured
				if (window.location.protocol === 'http:') {
					msg += '<p style="margin: 5px 0;"><b>' + _('Insecure Connection') + ': </b>';
					msg += _('This network connection is not encrypted. All personal or sensitive data will be transmitted in plain text. Please follow %s this link</a> to use a secure SSL connection.', '<a href="https://' + window.location.href.slice(7) + '">') + '</p>';
				}
			}
			// if login failed display a notification
			msg += '<p class="umc_LoginMessage" style="display: none; color: #ff0000;"></p>';

			this._text.set('content', msg);

			if (this._isRendered) {
				query('.umcShowHide').style('display', 'block');
				this._setInitialFocus();
				Dialog._DialogLevelManager.show(this, this.underlayAttrs);
			} else {
				var handle = aspect.after(this, '_connectEvents', lang.hitch(this, function() {
					query('.umcShowHide').style('display', 'block');
					this._setInitialFocus();
					Dialog._DialogLevelManager.show(this, this.underlayAttrs);
					handle.remove();
				}));
			}
		},

		hide: function() {
			// only close the dialog if it has not been closed already
			if (!this.get('open')) {
				return;
			}
			this.set('open', false);

			// hide the dialog
			query('.umcShowHide').style('display', 'none');
			Dialog._DialogLevelManager.hide(this);
		},

		onLogin: function(/*String*/ username) {
			// event stub
		}
	});
});

