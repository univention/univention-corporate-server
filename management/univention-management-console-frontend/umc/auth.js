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
/*global define setTimeout*/

define([
	"dojo/_base/lang",
	"dojo/_base/window",
	"dojo/dom",
	"dojo/topic",
	"dojo/request/xhr",
	"dojo/request/iframe",
	"dojo/Deferred",
	"dojo/json",
	"dojox/html/entities",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/PasswordBox",
	"umc/i18n/tools",
	"umc/i18n!"
], function(lang, win, dom, topic, xhr, iframe, Deferred, json, entities, dialog, tools, Text, TextBox, PasswordBox, i18nTools, _) {
	/**
	 * Private utilities for authentication. Authentication must handle:
	 * * autologin into a current active session
	 * * autologin via Single-Sign-On
	 * * login via the login dialog
	 * * changing of expired password
	 * * autologin via query string
	 * * autologin during long polling
	 * * auhtentication failures e.g. PW wrong, server-down, disabled account, user unknown
	 * * pass credentials to modules if logged in via SSO
	 * */
	var auth = {

		_password_required: null,

		handleAuthenticationError: function(info) {
			//console.debug('auth error');
			var message = info.message;
			var result = info.result || {};

			if (this._password_required || result.password_required) {
				if (!this._password_required) {
					this._password_required = new Deferred();
					message = '';
				}
				this._requirePassword(message);
				return this._password_required;
			}

			dialog._loginDialog.updateForm(info);
			if (tools.status('authType') === 'SAML') {
				return this.passiveSingleSignOn({ timeout: 15000 }).otherwise(lang.hitch(dialog, 'login'));
			}
			return dialog.login();
		},

		start: function() {
			//console.debug('starting auth');

			dialog._initLoginDialog();
			dialog._loginDialog.standby(true);
			dialog._loginDialog.show();

			this.autologin().otherwise(lang.hitch(this, 'sessionlogin')).otherwise(lang.hitch(this, function() {
				//console.debug('no active session found');
				this.passiveSingleSignOn({ timeout: 3000 }).then(lang.hitch(this, 'sessionlogin')).otherwise(lang.hitch(dialog, 'login'));
			}));
		},

		sessioninfo: function() {
			return xhr.post('/univention-management-console/get/session-info', { handleAs: 'json' }).then(function(response) {
				tools.status('authType', response.result.auth_type);
				return response;
			});
		},

		sessionlogin: function() {
			// login with a currently existing session (if exists)
			return this.sessioninfo().then(lang.hitch(this, function(response) {
				//console.debug('using existing session');
				return this.authenticated(response.result.username);
			}));
		},

		authenticated: function(username) {
			topic.publish('/umc/actions', 'session', 'relogin');
			//console.debug('authenticated');
			return tools.umcpCommand('set', {
				locale: i18nTools.defaultLang().replace('-', '_')
			}).then(lang.hitch(this, function() {
				//console.debug('locale set');
				topic.publish('/umc/authenticated', username);
				return username;
			}), lang.hitch(function(error) {
				dialog.login();
				throw error;
			}));
		},

		autologin: function() {
			// if username and password are specified via the query string, try to authenticate directly
			var username = tools.status('username');
			var password = tools.status('password');
			if (username && password) {
				//console.debug('auto login');
				// try to authenticate via long polling... i.e., in case of an error try again until it works
				return tools.umcpCommand('auth', {
					username: username,
					password: password
				}, this.errorHandler(), undefined, {
					message: _('So far the authentification failed. Continuing nevertheless.'),
					noLogin: true
				}).then(lang.hitch(this, function(response) {
					//console.debug('autologin got response', response);
					return this.authenticated(response.result.username);
				}));
			}

			//console.debug('no autologin possible');
			// reject deferred to force login
			var deferred = new Deferred();
			deferred.then(null, function() { /* prevent logging of exception */ });
			deferred.reject();
			return deferred.promise;
		},

		authenticate: function(data) {
			//console.debug('dialog auth');
			return tools.umcpCommand('auth', data, this.errorHandler()).then(lang.hitch(this, function(data) {
				var username;
				try {
					username = data.result.username;
				} catch (error) {
					// if the umc-webserver is not restarted after a upgrade from UCS 4.0 the auth request doesn't return a username yet
					// TODO: remove in UCS 4.2
					username = tools.status('username') || '';
					try { username = username || dom.byId('umcLoginUsername').value; } catch (e) {}
				}
				//console.debug('auth via dialog successful');
				return this.authenticated(username);
			}));
		},

		errorHandler: function() {
			return {
				401: lang.hitch(this, function(info) {
					// in case we are coming from a (failed) authentication we must not return a deferred
					// otherwise the login is impossible as it waits for the currently existing login deferred
					// which would never be resolved if we return a deferred here
					// the authentication should also not be repeated after a successful authentication
					this.handleAuthenticationError(info);
				})
			};
		},

		passiveSingleSignOn: function(args) {
			var deferred = new Deferred();
			var iframeid = ('passive_single_sign_on_' + Math.random().toString(36).substring(7)).replace(/[\/\.\-]/g, '_');
			var i = 0;
			var _iframe;
			win.global[iframeid + '_onload'] = function() {
				// callback which is invoked if the iframe successfully loaded a site
				// the first time this is called it contains a <form> which is automatically submitted
				// the seconds time this is called it contains the response
				if (i++ > 0) {
					try {
						var data = json.parse(iframe.doc(_iframe).getElementsByTagName('textarea')[0].value);
						if (tools.parseError(data).status > 299) {
							deferred.reject(data);
						} else {
							deferred.resolve(data);
						}
					} catch(error) {
						deferred.reject(error);
					}
				}
			};
			_iframe = iframe.create(iframeid, entities.encode(iframeid + '_onload()'), 'saml/iframe/');
			if (args && args.timeout) {
				setTimeout(function() {
					deferred.cancel();
				}, args.timeout);
			}
			// deferred.promise.always(function() { TODO: howto remove the _iframe? });
			return deferred.promise;
		},

		_requirePassword: function(message) {
			var text = _('This action requires you to supply your password.');
			if (message) {
				text = message + '<br><br>' + text;
			}
			return dialog.confirmForm({
				title: _('Authentication required'),
				widgets: [{
					name: 'text',
					type: Text,
					content: text
				}, {
					name: 'username',
					type: TextBox,
					disabled: true,
					placeHolder: _('Username'),
					value: tools.status('username')
				}, {
					name: 'password',
					type: PasswordBox,
					placeHolder: _('Password')
				}],
				buttons: [{
					name: 'submit',
					label: _('Login')
				}]
			}).then(lang.hitch(this, function(data) {
				return this.authenticate(lang.mixin(data, {
					username: tools.status('username')
				})).then(lang.hitch(this, function() {
					this._password_required.resolve();
					this._password_required = null;
				}));
			}), lang.hitch(this, function() {
				this._password_required.reject();
				this._password_required = null;
			}));
		}
	};
	lang.setObject('umc.auth', auth);
	return auth;
});
