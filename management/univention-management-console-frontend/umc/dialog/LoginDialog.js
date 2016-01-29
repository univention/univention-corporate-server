/*
 * Copyright 2011-2015 Univention GmbH
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
/*global define console window setTimeout require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/aspect",
	"dojo/when",
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
], function(declare, lang, array, win, aspect, when, has, on, dom, query, attr, domClass, styles, fx, baseFx, base64, Deferred, Dialog, DialogUnderlay, tools, Text, StandbyMixin, _) {

	_('Username');
	_('Password');
	_('New Password');
	_('New Password (retype)');
	_('Login');
	_('One time password');

	return declare("umc.dialog.LoginDialog", [StandbyMixin], {
		_iframe: null,
		_form: null,
		_text: null,

		_currentResult: null,

		id: 'umcLoginWrapper',

		open: false,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._currentResult = {};
			this._replaceLabels();
			this.containerNode = dom.byId('umcLoginDialog');
			this.domNode = dom.byId('umcLoginWrapper');

			this._iframe = dom.byId('umcLoginIframe');
			this._form = dom.byId('umcLoginForm');
			this._watchFormSubmits();

			// hide the login dialog. but wait for the GUI to be rendered.
			tools.status('app.loaded').then(lang.hitch(this, function() {
				// display the UCS logo animation some time
				setTimeout(lang.hitch(this, 'hide'), 1500);
			}));
		},

		buildRendering: function() {
			this.inherited(arguments);

			// set the properties for the dialog underlay element
			this.underlayAttrs = {
				dialogId: this.id,
				'class': 'dijitDialogUnderlay umcLoginDialogUnderlay'
			};

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

		updateForm: function(info) {
			var message = info.message;
			var result = info.result || {};
			this._updateView(result);

			if (message) {
				if (message.slice(-1) !== '.') {
					message += '.';
				}
				var title = info.title || _('Authentication failure');
				if (result.password_expired) {
					title = _('The password is expired');
				} else if (result.missing_prompts) {
					title = _('One time password required');
				}
				message = '<h1>' + title + '</h1><p>' + message + '</p>';
			}
			this.set('LoginMessage', message);
		},

		_setLoginMessageAttr: function(content) {
			this._text.set('content', content);
			if (content) {
				this._wipeInMessage();
			} else {
				query('#umcLoginMessages').style('display', 'none');
			}
		},

		_wipeInMessage: function() {
			var deferred = new Deferred();
			setTimeout(lang.hitch(this, function() {
				// It is possible to get into a race condition where the login message is deleted by
				// an 401 error after _wipeInMessage was started by a session timeout. If that happens we should not
				// show #umcLoginMessages because it would be empty.
				if (!this._text.get('content')) {
					deferred.resolve();
					return;
				}
				fx.wipeIn({node: 'umcLoginMessages', onEnd: function() {
					deferred.resolve();
					query('#umcLoginMessages').style('display', 'block');
				}}).play();
			}), 200);
			return deferred.promise;
		},

		_updateView: function(result) {
			this._currentResult = result;
			var showLogin = true, showNewPassword = false, showCustomPrompt = false;
			if (result.password_expired) {
				showLogin = false;
				showNewPassword = true;
				showCustomPrompt = false;
			} else if (result.missing_prompts) {
				showLogin = false;
				showNewPassword = false;
				showCustomPrompt = true;
			}

			query('#umcLoginForm').style('display', showLogin ? 'block' : 'none');
			query('#umcNewPasswordForm').style('display', showNewPassword ? 'block' : 'none');
			query('#umcCustomPromptForm').style('display', showCustomPrompt ? 'block' : 'none');

			if (showLogin) {
				this._resetForm();
			}
			this._setFocus();
			if (!has('touch')) {
				if (showNewPassword) {
					dom.byId('umcLoginNewPassword').focus();
				} else if (showCustomPrompt) {
					dom.byId('umcLoginCustomPrompt').focus();
				}
			}
		},

		_resetForm: function() {
			array.forEach(['umcLoginForm', 'umcNewPasswordForm', 'umcCustomPromptForm'], function(name) {
				query('input', dom.byId(name)).forEach(function(node) {
					attr.set(node, 'value', '');
				});
			});
			// if username is specified, we need to auto fill the username
			if (tools.status('username')) {
				attr.set('umcLoginUsername', 'value', tools.status('username'));
			};
		},

		_watchFormSubmits: function() {
			array.forEach(['umcLoginForm', 'umcNewPasswordForm', 'umcCustomPromptForm'], lang.hitch(this, function(name) {
				var form = dom.byId(name);
				on(form, 'submit', lang.hitch(this, function(evt) {
					evt.preventDefault();
					if (name == 'umcLoginForm') {
						this._submitFakeForm();
					}
					// FIXME: if custom prompts and(!) new password is required we should just switch the view

					var data = this._getFormData(name);
					if (data) {
						this._authenticate(data);
					}
				}));
			}));
		},

		_getFormData: function(name) {
			var newPasswordInput = dom.byId('umcLoginNewPassword');
			var newPasswordRetypeInput = dom.byId('umcLoginNewPasswordRetype');

			var data = {};

			tools.forIn({
				username: dom.byId('umcLoginUsername'),
				password: dom.byId('umcLoginPassword'),
				new_password: newPasswordInput
			}, function(key, node) {
				if (node.value) {
					data[key] = node.value;
				}
			});

			// validate new password form
			if (name == 'umcNewPasswordForm' && newPasswordInput.value && newPasswordInput.value !== newPasswordRetypeInput.value) {
				this.set('LoginMessage', '<h1>' + _('Changing password failed') + '</h1><p>' +  _('The passwords do not match, please retype again.') + '</p>');
				return;
			}
			// custom prompts
			array.forEach(this._currentResult.missing_prompts || [], function(prompt_) {
				data[prompt_] = dom.byId('umcLoginCustomPrompt').value;
			});
			// TODO: what if data is empty
			return data;
		},

		_submitFakeForm: function() {
			try {
				if (!this._iframe) {
					return;  // iframe not yet loaded
				}
				var fakeDoc = this._iframe.contentWindow ? this._iframe.contentWindow.document : this._iframe.contentDocument;
				if (!fakeDoc) {
					// iframe reloading just in this second
					return;
				}
				// set all current form values into the fake iframe form
				query('.umcLoginForm input').forEach(lang.hitch(this, function(node) {
					var iframeNode = dom.byId(node.id, fakeDoc);
					if (iframeNode) {
						iframeNode.value = node.value;
					}
				}));

				// submit the fake form to show a password save dialog
				var iform = dom.byId('umcLoginForm', fakeDoc);
				iform.submit.click();
			} catch(e) {
				// just for the case...
				console.error('error in submitting fake iframe:', e);
			}
		},

		_disconnectEvents: function(connections) {
			array.forEach(connections, function(con) {
				con.remove();
			});
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

		_authenticate: function(data) {
			this.standby(true);
			tools.status('username', data.username);
			require('umc/auth').authenticate(data).then(
				lang.hitch(this, '_authenticated'),
				lang.hitch(this, '_authentication_failed')
			);
		},

		_authenticated: function(username) {
			// delete password ASAP. should not be stored
			this._resetForm();
			this._currentResult = {};

			// make sure that we got data
			this.onLogin(username);

			// hide login dialog
			if (tools.status('app.loaded').isFulfilled()) {
				this.hide();
			}
		},

		_authentication_failed: function(error) {
			// the authentication failed and(!) was triggered by this dialog... we only need to show()+hide()
			// errors must be handled by the _updateView() functions!!
			// don't call _updateFormDeferred or _resetForm here!
			// It would break setting of new_password
			this.standby(false);
			Dialog._DialogLevelManager.show(this, this.underlayAttrs);
			Dialog._DialogLevelManager.hide(this);
		},

		standby: function(standby) {
			domClass.toggle(dom.byId('umcLoginDialog'), 'umcLoginLoading', standby);
			if (standby && this._text.get('content')) {
				fx.wipeOut({node: this._text.id, properties: { duration: 500 }}).play();
			} else if (!standby) {
				// only non hidden input fields can be focused
				this._setFocus();
			}
		},

		ask: function() {
			// show dialog
			this.show();
			this.standby(false);
			tools.status('loggingIn', true);

			// connect to the dialog's onLogin event
			var deferred = new Deferred();
			on.once(this, 'login', function(username) {
				// update loggingIn status
				tools.status('loggingIn', false);

				// submit the username to the deferred callback
				deferred.resolve(username);
			});
			return deferred.promise;
		},

		show: function() {
			// only open the dialog if it has not been opened before
			if (this.get('open')) {
				return when();
			}
			this.set('open', true);

			// update info text
			var msg = '';
			var title = '';

			// Show warning if connection is unsecured
			if (window.location.protocol === 'http:') {
				var link = '<a href="https://' + window.location.href.slice(7) + '">';
				title = _('Insecure Connection');
				msg = _('This network connection is not encrypted. All personal or sensitive data will be transmitted in plain text. Please follow %s this link</a> to use a secure SSL connection.', link);
			}

			if (has('ie') < 11 || has('ff') < 38 || has('chrome') < 37 || has('safari') < 9) {
			// by umc (4.1.0) supported browsers are Chrome >= 33, FF >= 24, IE >=9 and Safari >= 7
			// they should work with UMC. albeit, they are
			// VERY slow and escpecially IE 8 may take minutes (!)
			// to load a heavy UDM object (on a slow computer at least).
			// IE 8 is also known to cause timeouts when under heavy load
			// (presumably because of many async requests to the server
			// during UDM-Form loading).
			// By browser vendor supported versions:
			// The oldest supported Firefox ESR version is 38 (2016-01-27).
			// Microsoft is ending the support for IE < 11 (2016-01-12).
			// Chrome has no long term support version. Chromium 37 is supported through
			// Ubuntu 12.04 LTS (2016-01-27).
			// Apple has no long term support for safari. The latest version is 9 (2016-01-27)
				title = _('Your Browser is outdated') + ((title == '') ? title : '<br>' + title);
				msg = _('Your Browser is outdated and should be updated. You may continue to use Univention Management Console but you may experience performance issues and other problems.') + ((msg == '') ? msg : '<br>' + msg);
			}

			if (tools.status('setupGui')) {
				// user has already logged in before, show message for relogin
				title = _('Session timeout');
				msg = _('Your session has been closed due to inactivity. Please login again.');

				// remove language selection and SSO button after first successful login
				query('#umcLoginHeaderRight').style('display', 'none');
				query('#umcFakeLoginLogo').style('display', 'none');
			}

			query('#umcLoginMessages').style('display', 'none');
			this.updateForm({message: msg, title: title});

			return this._show();
		},

		_show: function() {
			var deferred;
			query('#umcLoginWrapper').style('display', 'block');
			query('#umcLoginDialog').style('opacity', '1');  // baseFx.fadeOut sets opacity to 0
			this._setFocus();
			if (has('ie') < 10) {
				// trigger IE9 workaround
				this._replaceLabels();
			}
			Dialog._DialogLevelManager.show(this, this.underlayAttrs);
			if (this._text.get('content')) {
				deferred = this._wipeInMessage();
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
			return when(deferred);
		},

		_setFocus: function() {
			// disable the username field during relogin, i.e., when the GUI has been previously set up
			attr.set('umcLoginUsername', 'disabled', tools.status('setupGui'));

			if (has('touch')) {
				return;
			}
			if (!dom.byId('umcLoginUsername').value) {
				dom.byId('umcLoginUsername').focus();
			} else {
				dom.byId('umcLoginPassword').focus();
			}
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
			query('#umcLoginIframe').style('position', 'absolute');
			query('#umcLoginIframe').style('z-index', '1000000');
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
