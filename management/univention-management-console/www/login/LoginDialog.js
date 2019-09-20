/*
 * Copyright 2011-2019 Univention GmbH
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
/*global dojo, define, window, require, getQuery*/

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
	"dojo/dom-construct",
	"dojo/query",
	"dojo/dom-attr",
	"dojo/dom-class",
	"dojox/html/styles",
	"dojo/fx",
	"dojox/encoding/base64",
	"dojo/Deferred",
	"dijit/Dialog",
	"dijit/_WidgetBase",
	"dijit/DialogUnderlay",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/StandbyMixin",
	"umc/i18n!login",
	"dojo/domReady!",
	"dojo/NodeList-dom"
], function(declare, lang, array, win, aspect, when, has, on, dom, domConstruct, query, attr, domClass, styles, fx, base64, Deferred, Dialog, _WidgetBase, DialogUnderlay, entities, tools, Text, StandbyMixin, _) {

	_('Username');
	_('Password');
	_('New Password');
	_('New Password (retype)');
	_('Login');
	_('One time password');

	return declare("umc.dialog.LoginDialog", [_WidgetBase], {
		_form: null,
		_warning: null,
		_notice: null,

		_currentResult: null,

		_scrollPosY: 0,

		id: 'umcLoginWrapper',

		open: false,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._currentResult = {};
			this._replaceLabels();
			this.containerNode = dom.byId('umcLoginDialog');
			this.domNode = dom.byId('umcLoginWrapper');

			this._form = dom.byId('umcLoginForm');
			this._watchFormSubmits();
		},

		buildRendering: function() {
			this.inherited(arguments);

			// create the info text fields
			this._notice = new Text({
				class: 'umcLoginNotices',
				content: ''
			}, 'umcLoginNotices');

			this._warning = new Text({
				class: 'umcLoginWarnings',
				content: ''
			}, 'umcLoginWarnings');
		},

		_setLoginWarningAttr: function(content) {
			if (content) {
				content = '<p class="umcLoginWarning">' + entities.encode(content) + '</p>';
			}
			this._warning.set('content', content);
			query('.umcLoginWarnings').style('display', content ? 'block' : 'none');
		},

		_setLoginNoticeAttr: function(content) {
			if (content) {
				content = '<p class="umcLoginNotice">' + entities.encode(content) + '</p>';
			}
			this._notice.set('content', content);
			query('.umcLoginNotices').style('display', content ? 'block' : 'none');
		},

		updateForm: function(info) {
			var message = info.message;
			var result = info.result || {};
			this._updateView(result);

			var notice = false;
			var title = '';
			if (message) {
				if (message.slice(-1) !== '.') {
					message += '.';
				}
				title = info.title || '';
				if (result.missing_prompts || result.password_expired) {
					notice = true;
				}
				message = title + ' ' + message;
			}
			this.set('LoginWarning', notice ? '' : message);
			this.set('LoginNotice', notice ? message : '');
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
				 // important! If we failed to set a new password in the 'umcNewPasswordForm' we must reset the form content (new_password)
				 // so that this is not send along with the next authentication request
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
				query('input:not([type=submit])', dom.byId(name)).forEach(function(node) {
					attr.set(node, 'value', '');
				});
			});
			this.autoFill();
		},

		autoFill: function() {
			// if username is specified, we need to auto fill the username
			if (tools.status('username')) {
				attr.set('umcLoginUsername', 'value', tools.status('username'));
			}
		},

		disableForm: function(message) {
			array.forEach(['umcLoginForm', 'umcNewPasswordForm', 'umcCustomPromptForm'], function(name) {
				query('input', dom.byId(name)).forEach(function(node) {
					attr.set(node, 'disabled', 'disabled');
				});
				query('#' + name).style('display', 'none');
			});
			this.standby(true);
			setTimeout(lang.hitch(this, function() {
				this.set('LoginWarning', message);
			}, 1000));
		},

		_watchFormSubmits: function() {
			array.forEach(['umcLoginForm', 'umcNewPasswordForm', 'umcCustomPromptForm'], lang.hitch(this, function(name) {
				var form = dom.byId(name);
				if (!form) {
					return;
				}
				on(form, 'submit', lang.hitch(this, function(evt) {
					evt.preventDefault();
					// FIXME: if custom prompts and(!) new password is required we should just switch the view

					var data = this._getFormData(name);
					if (data) {
						this._authenticate(data);
					}
					return false;
				}));
			}));
		},

		_getFormData: function(name) {
			var newPasswordInput = dom.byId('umcLoginNewPassword');
			var newPasswordRetypeInput = dom.byId('umcLoginNewPasswordRetype');

			var data = {
				username: '',
				password: ''
			};

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
			if (name === 'umcNewPasswordForm' && newPasswordInput.value && newPasswordInput.value !== newPasswordRetypeInput.value) {
				this.set('LoginWarning', _('Changing password failed. The passwords do not match, please retype again.'));
				return;
			}
			// custom prompts
			array.forEach(this._currentResult.missing_prompts || [], function(prompt_) {
				data[prompt_] = dom.byId('umcLoginCustomPrompt').value;
			});
			// TODO: what if data is empty
			return data;
		},

		_replaceLabels: function() {
			// all submit buttons
			query('.umcLoginForm input[type=submit]').attr('value', _('Login'));
			query('input#umcNewPasswordSubmit').attr('value', _('Set password'));

			tools.forIn({
				'umcLoginUsername': _('Username'),
				'umcLoginPassword': _('Password'),
				'umcLoginNewPassword': _('New password'),
				'umcLoginNewPasswordRetype': _('New Password (retype)'),
				'umcLoginCustomPrompt': _('One time password')
			}, function(id, placeholder) {
				var node = dom.byId(id);
				if (!node) {
					return;  // the SAML single sign on page is shown
				}
				attr.set(node, 'placeholder', placeholder);
				if (!('placeholder' in node)) {
					this.fixIEPlaceholders(node);
				}
			});
			domClass.remove(document.body, 'umcLoginLoading', false);
		},

		fixIEPlaceholders: function(node) {
			var svg = lang.replace('<svg width="277px" height="20px" version="1.1" xmlns="http://www.w3.org/2000/svg">' +
					'<text fill="#ababab" font-size="18px" y="15" x="0" text-anchor="start">{0}</text></svg>', [attr.get(node, "placeholder")]);

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
			require('login').authenticate(data).then(
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

			// redirect the user back to the location where he came from.
			// CAUTION !!!: we must properly make sure that this is a valid url on the same origin. otherwise we would allow
			// XSS attacks by submitting e.g. ?location=javascript:alert('XSS') or mailto: links, etc.
			var uri = new dojo._Url(getQuery('location'));
			var path = uri.path;
			if (/\/\//.test(path)) {
				path = null;
			}
			window.location = (path || '/univention/management/') + (uri.fragment ? '#' + uri.fragment : window.location.hash);
		},

		_authentication_failed: function() {
			// the authentication failed and(!) was triggered by this dialog... we only need to show()+hide()
			// errors must be handled by the _updateView() functions!!
			// don't call _updateFormDeferred or _resetForm here!
			// It would break setting of new_password
			this.standby(false);
		},

		standby: function(standby) {
			domClass.toggle(document.body, 'umcLoginLoading', standby);
			if (!standby) {
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
			this.set('LoginWarning', '');
			this.set('LoginNotice', '');
			return this._show();
		},

		_show: function() {
			this._setFocus();
			if (has('ie') < 10) {
				// trigger IE9 workaround
				// a saved password/username contains a placeholder if we don't run this again
				this._replaceLabels();
			}
		},

		_setFocus: function() {
			if (has('touch')) {
				return;
			}
			if (!dom.byId('umcLoginUsername').value) {
				dom.byId('umcLoginUsername').focus();
			} else {
				dom.byId('umcLoginPassword').focus();
			}
		},

		focus: function() {
			this._setFocus();
		},

//		_getFocusItems: function() {
//		},

		onLogin: function(/*String username*/) {
			// event stub
		}
	});
});
