/*
 * Copyright 2011-2014 Univention GmbH
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
	"dojo/dom",
	"dojo/query",
	"dojo/dom-attr",
	"dojo/dom-class",
	"dojox/html/styles",
	"dojo/fx",
	"dojo/_base/fx",
	"dojox/encoding/base64",
	"dojo/Deferred",
	"dijit/Dialog",
	"dijit/DialogUnderlay",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/StandbyMixin",
	"umc/i18n!",
	"dojo/domReady!",
	"dojo/NodeList-dom"
], function(declare, lang, array, win, aspect, has, on, dom, query, attr, domClass, styles, fx, baseFx, base64, Deferred, Dialog, DialogUnderlay, tools, Text, StandbyMixin, _) {

	_('Username');
	_('Password');
	_('New Password');
	_('New Password (retype)');
	_('Login');

	return declare("umc.dialog.LoginDialog", [StandbyMixin], {
		// our own variables
		_connections: null,
		_iframe: null,
		_text: null,

		_username: null,
		_password: null,
		_newPassword: null,
		_updateFormDeferred: null,
		_nLogins: 0,

		id: 'umcLoginWrapper',

		// internal flag whether the dialog is rendered or not
		_isRendered: false,

		open: false,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._replaceLabels();
			this.containerNode = dom.byId('umcLoginDialog');
			this.domNode = dom.byId('umcLoginWrapper');
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._updateFormDeferred = new Deferred();
			this._updateFormDeferred.resolve(false); // may update form, dont show new password

			// set the properties for the dialog underlay element
			this.underlayAttrs = {
				dialogId: this.id,
				'class': 'dijitDialogUnderlay umcLoginDialogUnderlay'
			};

			// initialize the form+iframe
			this._iframe = dom.byId('umcLoginIframe');
			this._form = dom.byId('umcLoginForm');
			this._initForm();

			// create the info text
			this._text = new Text({
				id: 'umcLoginMessages',
				content: ''
			});
			this._text.placeAt(this.domNode, 'last');

			// automatically resize the DialogUnderlay container
			this.own(on(win.global, 'resize', lang.hitch(this, function() {
				if (Dialog._DialogLevelManager.isTop(this)) {
					DialogUnderlay._singleton.layout();
				}
			})));
		},

		updateForm: function(passwordExpired, message) {
			this._passwordExpired = passwordExpired;
			this._updateFormDeferred.resolve(this._passwordExpired);
			if (message.slice(-1) !== '.') {
				message += '.';
			}
			this.set('LoginMessage', message);
		},

		_setLoginMessageAttr: function(message) {
			this._text.set('content', '<h1>' + _('Authentication failure') + '</h1><p>' + message + '</p>');
			this._wipeInMessage();
		},

		_wipeInMessage: function() {
			setTimeout(function() {
				fx.wipeIn({node: 'umcLoginMessages', onEnd: function() {
					query('#umcLoginMessages').style('display', 'block');
				}}).play();
			}, 200);
		},

		_initForm: function() {
			// FIXME: remove this endless loop
			// wait until the iframe is completely loaded
			setTimeout(lang.hitch(this, function() {
				// check whether the form is available or not
				var state = lang.getObject('contentWindow.state', false, this._iframe);
				if (state === 'loaded') {
					// each time the page is loaded, we need to connect to the form events
					this._updateFormDeferred.then(lang.hitch(this, '_updateView'));
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

		_updateView: function(showNewPassword) {
			query('#umcLoginForm').style('display', showNewPassword ? 'none' : 'block');
			query('#umcNewPasswordForm').style('display', showNewPassword ? 'block' : 'none');
			if (showNewPassword) {
				if (this._username) {
					attr.set(dom.byId('umcLoginUsername'), 'value', this._username);
					tools.status('username', this._username); // already set status, otherwise _setInitialFocus may cause problems
				}
				if (this._password) {
					attr.set(dom.byId('umcLoginPassword'), 'value', this._password);
				}
				attr.set(dom.byId('umcLoginNewPassword'), 'value', '');
				attr.set(dom.byId('umcLoginNewPasswordRetype'), 'value', '');
				if (!has('touch')) {
					dom.byId('umcLoginNewPassword').focus();
				}
			} else if (this._nLogins || tools.status('setupGui')) {
				attr.set(dom.byId('umcLoginPassword'), 'value', '');
			}
		},

		_resetForm: function() {
			// reset all hidden values in the iframe
			win.withGlobal(this._iframe.contentWindow, lang.hitch(this, function() {
				query('input').forEach(function(node) {
					attr.set(node, 'value', '');
				});
			}));
			query('input', this._form).forEach(function(node) {
				attr.set(node, 'value', '');
			});
		},

		_connectEvents: function() {
			//this._disconnectEvents();
			this._connections = [];
			var iframeLoginForm, usernameInput, passwordInput, newPasswordInput, newPasswordRetypeInput;

			win.withGlobal(this._iframe.contentWindow, lang.hitch(this, function() {
				iframeLoginForm = dom.byId('umcLoginForm');
				usernameInput = dom.byId('umcLoginUsername');
				passwordInput = dom.byId('umcLoginPassword');
				newPasswordInput = dom.byId('umcLoginNewPassword');
				newPasswordRetypeInput = dom.byId('umcLoginNewPasswordRetype');
			}));

			var iframe = this._iframe.contentWindow.document;
			var forms = [[dom.byId('umcLoginForm'), dom.byId('umcLoginForm', iframe)], [dom.byId('umcNewPasswordForm'), dom.byId('umcNewPasswordForm', iframe)]];
			// register all events
			array.forEach(forms, lang.hitch(this, function(ff) {
				var form = ff[0];
				var iform = ff[1];

				if (iform) {
					this._connections.push(on(iform, 'submit', lang.hitch(this, function(evt) {
						var username = usernameInput.value;
						var password = passwordInput.value;
						var newPassword;

						if (iform !== iframeLoginForm) {
							if (newPasswordInput.value !== newPasswordRetypeInput.value) {
								this.set('LoginMessage', _('The passwords do not match, please retype again.'));
								evt.preventDefault();
								return;
							}
							newPassword = newPasswordInput.value;
						}

						this._authenticate(username, password, newPassword);
						this._isRendered = false;
						this._initForm();
					})));
				}

				if (form) {
					this._connections.push(on(form, 'submit', lang.hitch(this, function(evt) {
						evt.preventDefault();

						query('.umcLoginForm input').forEach(lang.hitch(this, function(node) {
							var iframeNode = dom.byId(node.id, iframe);
							if (iframeNode) {
								iframeNode.value = node.value;
							}
						}));
						iform.submit.click();
					})));
				}
			}));
		},

		_disconnectEvents: function() {
			array.forEach(this._connections, function(con) {
				con.remove();
			});
			this._connections = [];
		},

		_replaceLabels: function() {
			query('.umcLoginForm', this.domNode).forEach(lang.hitch(this, function(form) {
				query('input', form).forEach(lang.hitch(this, function(node) {
					if (attr.get(node, 'placeholder')) {
						attr.set(node, 'placeholder', _(attr.get(node, 'placeholder')));

						if (!('placeholder' in node)) {
							this.fixIEPlaceholders(node);
						}
					}
				}));
			}));
			domClass.toggle(dom.byId('umcLoginDialog'), 'umcLoginLoading', false);
		},

		fixIEPlaceholders: function(node) {
			var svg = lang.replace('<svg width="277px" height="20px" version="1.1" xmlns="http://www.w3.org/2000/svg">' +
					'<text fill="#ababab" font-size="18px" y="15" x="0" text-anchor="start">{0}</text></svg>', [_(attr.get(node, "placeholder"))]);

			var bits = [];
			for (var i=0; i<svg.length; i++) {
				bits.push(svg.charCodeAt(i));
			}
			styles.insertCssRule('.background-' + node.id, lang.replace("background-image: url(\"data:image/svg+xml;base64,{0}\")!important; background-repeat: no-repeat!important;", [base64.encode(bits)]));
			styles.insertCssRule('.background-' + node.id + ':focus', "background-image: none!important");
			domClass.toggle(node, 'background-' + node.id, !node.value);

			this.own(on(node, 'change', function() {
				domClass.toggle(node, 'background-' + node.id, !node.value);
			}));
		},

		_authenticate: function(username, password, new_password) {
			// count number of login trials
			++this._nLogins;

			// save in case password expired and username and password have to be sent again
			this._username = username;
			this._password = password;
			var args = {
				username: username,
				password: password
			};
			if (new_password) {
				this._newPassword = new_password;
				args.new_password = new_password;
			}
			this._updateFormDeferred = new Deferred();
			this.standby(true);
			tools.umcpCommand('auth', args).then(lang.hitch(this, function(data) {
				// delete password ASAP. should not be stored
				this._username = null;
				this._password = null;
				this._newPassword = null;
				this._passwordExpired = false;
				this._updateFormDeferred.resolve(this._passwordExpired);
				this._resetForm();

				// make sure that we got data
				this.onLogin(username);
				if (tools.status('setupGui')) {
					// the module loading bar was already triggered
					this.hide();
				}
			}), lang.hitch(this, function(error) {
				// don't call _updateFormDeferred or _resetForm here!
				// It would break setting of new_password
				this.standby(false);
				this._setInitialFocus();
				Dialog._DialogLevelManager.show(this, this.underlayAttrs);
				Dialog._DialogLevelManager.hide(this);
			}));
		},

		standby: function(standby) {
			domClass.toggle(dom.byId('umcLoginDialog'), 'umcLoginLoading', standby);
			if (standby && this._text.get('content')) {
				fx.wipeOut({node: this._text.id, properties: { duration: 500 }}).play();
			}
		},

		show: function() {
			// only open the dialog if it has not been opened before
			if (this.get('open')) {
				return;
			}
			this.set('open', true);

			// update info text
			var msg = '';

			// Show warning if connection is unsecured
			if (window.location.protocol === 'http:') {
				var link = '<a href="https://' + window.location.href.slice(7) + '">';
				msg += '<h1>' + _('Insecure Connection') + '</h1>';
				msg += '<p>' + _('This network connection is not encrypted. All personal or sensitive data will be transmitted in plain text. Please follow %s this link</a> to use a secure SSL connection.', link) + '</p>';
			}
			
			if (has('ie') < 9 || has('ff') < 24) {
			// supported browsers are Chrome >= 33, FF >= 24, IE >=9 and Safari >= 7
			// they should work with UMC. albeit, they are
			// VERY slow and escpecially IE 8 may take minutes (!)
			// to load a heavy UDM object (on a slow computer at least).
			// IE 8 is also known to cause timeouts when under heavy load
			// (presumably because of many async requests to the server
			// during UDM-Form loading)
			msg += '<h1>' + _('Your Browser is outdated') + '</h1>';
			msg += '<p>' + _('Your Browser is outdated and should be updated. You may continue to use Univention Management Console but you may experience performance issues and other problems.') + '</p>';
			}

			if (tools.status('setupGui')) {
				// user has already logged in before, show message for relogin
				msg = '<h1>' + _('Session timeout')  + '</h1><p>' + _('Your session has been closed due to inactivity. Please login again.') + '</p>';

				// remove language selection after first successful login
				query('#umcLanguageSwitch').style('display', 'none');
				query('#umcFakeLoginLogo').style('display', 'none');
			}

			query('#umcLoginMessages').style('display', 'none');
			this._text.set('content', msg);

			if (this._isRendered) {
				this._show();
			} else {
				var handle = aspect.after(this, '_connectEvents', lang.hitch(this, function() {
					this._show();
					handle.remove();
				}));
			}
		},

		_show: function() {
			query('#umcLoginWrapper').style('display', 'block');
			query('#umcLoginDialog').style('opacity', '1');  // baseFx.fadeOut sets opacity to 0
			this._setInitialFocus();
			Dialog._DialogLevelManager.show(this, this.underlayAttrs);
			if (this._text.get('content')) {
				this._wipeInMessage();
			}
			// display the body background (hides rendering of GUI) the first time
			if (!tools.status('setupGui')) {
				if (has('ie')) {
					// a saved password/username contains a placeholder if we don't run this again
					this._replaceLabels();
				}
				try {
					styles.insertCssRule('.umcBackground', 'background: inherit!important;');
					domClass.toggle(dom.byId('dijit_DialogUnderlay_0'), 'umcBackground', true);
				} catch (e) {
					// guessed the ID
					console.log('dialogUnderlay', e);
				}
			}
		},

		_setInitialFocus: function() {
			//win.withGlobal(this._iframe.contentWindow, lang.hitch(this, function() {
				if (tools.status('username')) {
					// username is specified, we need to auto fill
					// the username and disable the textbox.
					attr.set('umcLoginUsername', 'value', tools.status('username'));
					if (!has('touch')) {
						dom.byId('umcLoginPassword').focus();
					}

					// disable the username field during relogin, i.e., when the GUI has been previously set up
					attr.set('umcLoginUsername', 'disabled', tools.status('setupGui'));
				} else {
					// initial focus on username input
					if (!has('touch')) {
						dom.byId('umcLoginUsername').focus();
					}
				}
			//}));
		},

		hide: function() {
			// only close the dialog if it has not been closed already
			if (!this.get('open')) {
				return;
			}
			this.set('open', false);

			var deferred = new Deferred();
			// hide the dialog
			var hide = lang.hitch(this, function() {
				query('#umcLoginWrapper').style('display', 'none');
				Dialog._DialogLevelManager.hide(this);
				this.standby(false);
				try {
					domClass.toggle(dom.byId('dijit_DialogUnderlay_0'), 'umcBackground', false);
				} catch (e) {
					// guessed the ID
					console.log('dialogUnderlay', e);
				}
				deferred.resolve();
			});
			baseFx.fadeOut({node: 'umcLoginDialog', duration: 300, onEnd: hide}).play();
			return deferred;
		},

		__debug: function() {
			query('#umcLoginLogo').style('display', 'none');
			win.withGlobal(this._iframe.contentWindow, lang.hitch(this, function() {
				query('.umcLoginForm').style('display', 'block');
			}));
			query('.umcLoginForm').style('display', 'block');
			query('#umcLoginIframe').style('display', 'block');
			query('#umcLoginIframe').style('width', 'inherit');
			query('#umcLoginIframe').style('height', 'inherit');
			query('#umcLoginDialog').style('height', 'inherit');
		},

		focus: function() {
		},

		_getFocusItems: function() {
		},

		onLogin: function(/*String*/ username) {
			// event stub
		}
	});
});
