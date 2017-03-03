/*
 * Copyright 2015-2017 Univention GmbH
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
/*global define,setTimeout*/

define([
	"dojo/_base/lang",
	"dojo/_base/window",
	"dojo/dom",
	"dojo/topic",
	"dojo/query",
	"dojo/request/xhr",
	"dojo/request/iframe",
	"dojo/Deferred",
	"dojo/json",
	"dojox/html/entities",
	"umc/dialog",
	"login/LoginDialog",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/PasswordBox",
	"umc/i18n/tools",
	"umc/i18n!login/main"
], function(lang, win, dom, topic, query, xhr, iframe, Deferred, json, entities, dialog, LoginDialog, tools, Text, TextBox, PasswordBox, i18nTools, _) {
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
	var login = {

		_password_required: null,
		_loginDialog: null, // internal reference to the login dialog
		_loginDeferred: null,

		showLoginDialog: function() {
			// deprecated! only updater.js and tools.js renewSession still uses it.
			return this.sessionTimeout();
		},

		sessionTimeout: function() {
			// call when the session timed out, returns a deferred which resolves when the session is active again
			if (this._loginDeferred) {
				// a login attempt is currently running
				return this._loginDeferred;
			}

			topic.publish('/umc/actions', 'session', 'timeout');
			this._loginDeferred = this.autorelogin({ timeout: 15000 }).then(undefined, lang.hitch(this, function() {

				tools.checkReloadRequired();

				// FIXME: remove and show something else, e.g. a newly rendered login dialog
				//this._requirePassword(('The current session timed out. <a href="/univention/login/?location=%s">Please login again.</a>', entities.encode(encodeURIComponent(window.location.href))));
				this._requirePassword(_('The current session timed out. Please login again.'));

				return this._waitForNextAuthentication().then(lang.hitch(this, function() {
					// remove the reference to the login deferred object
					this._loginDeferred = null;
				}));
			}));
			return this._loginDeferred;
		},

		renderLoginDialog: function() {
			// summary:
			//		Show the login screen.
			// returns:
			//		A Deferred object that is called upon successful login.
			//		The callback receives the authorized username as parameter.

			this._loginDialog = new LoginDialog({});
			this._loginDialog.startup();
			this._loginDialog.show();

			// check if a page reload is required
			tools.checkReloadRequired();

			this.autologin().then(undefined, lang.hitch(this, function() {
				// auto authentication could not be executed or failed...
				return this._loginDialog.ask();
			}));

		},

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
				return this._password_required.promise;
			}

			// if we are at the login dialog only update the form (e.g. authentication failure, expired password, ...)
			if (this._loginDialog) {
				this._loginDialog.updateForm(info || {});
				return;
			}

			return this.sessionTimeout();
		},

		start: function(username, password) {
			//console.debug('starting auth');
			tools.status('username', username);
			tools.status('password', password);
			this.autologin().otherwise(lang.hitch(this, 'sessionlogin')).otherwise(lang.hitch(this, function() {
				//console.debug('no active session found');
				var passiveLogin = this.passiveSingleSignOn({ timeout: 3000 });
				return passiveLogin.then(lang.hitch(this, 'sessionlogin')).otherwise(lang.hitch(this, function() {
					var target = '/univention/login/?location=' + entities.encode(encodeURIComponent(window.location.href));
					if (!passiveLogin.isCanceled()) {
						target = '/univention/saml/';
					}
					window.location = target;
				}));
			}));

			return this._waitForNextAuthentication();
		},

		_waitForNextAuthentication: function() {
			// return a deferred upon the next authentication
			var authenticatedDeferred = new Deferred();
			var handle = topic.subscribe('/umc/authenticated', function(params) {
				handle.remove();
				var username = params[0];
				authenticatedDeferred.resolve(username);
			});
			return authenticatedDeferred;
		},

		sessioninfo: function() {
			return xhr.post('/univention/get/session-info', { handleAs: 'json' }).then(function(response) {
				tools.status('authType', response.result.auth_type);
				tools.status('loggedIn', true);
				return response;
			}, function(error) {
				if (tools.status('loggedIn')) {
					tools.status('loggedIn', false);
					try {
						topic.publish('/umc/unauthenticated');
					} catch (e) {
						// make sure the original error is propagated
					}
				}
				throw error;
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

			// save the username internally and as cookie
			tools.setUsernameCookie(username, { expires: 100, path: '/univention/' });
			tools.status('username', username);

			// start the timer for session checking
			tools.checkSession(true);

			try {
				topic.publish('/umc/authenticated', username);
			} catch (e) {
				// ignore all exceptions done here (e.g. by hooks) otherwise the login dialog is not closed anymore
			}
			return username;
		},

		autorelogin: function(args) {
			if (tools.status('authType') === 'SAML') {
				return this.passiveSingleSignOn(args);
			}
			return this.autologin();
		},

		autologin: function() {
			// if username and password are specified via the query string, try to authenticate directly
			var username = tools.status('username');
			var password = tools.status('password');
			if (username && password) {
				//Remove language selection
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
				var username = data.result.username;
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
				}),
				display503: lang.hitch(this, function(info) {
					// in case we login and Apache/UMC-Server/UMC-Webserver does not run
					if (this._loginDialog) {
						this._loginDialog.updateForm({message: info.title});
					}
					dialog.alert(entities.encode(info.message).replace(/\n/g, '<br>'), info.title);
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
			_iframe = iframe.create(iframeid, entities.encode(iframeid + '_onload()'), '/univention/saml/iframe/');
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
				text = entities.encode(message) + '<br><br>' + entities.encode(text);
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
		},

		logout: function() {
			this._askLogout().then(lang.hitch(this, function() {
				tools.checkSession(false);
				window.location = '/univention/logout';
			}));
		},

		relogin: function(username) {
			if (username === undefined) {
				return this.logout();
			}
			this._askLogout().then(function() {
				// TODO: we should do a real logout here. maybe the UMCUsername cookie can be set
				tools.checkSession(false);
				tools.closeSession();
				window.location.search = 'username=' + encodeURIComponent(username);
			});
		},

		_askLogout: function() {
			var deferred = new Deferred();
			dialog.confirm(_('Do you really want to logout?'), [{
				label: _('Cancel'),
				callback: function() {
					deferred.cancel();
				}
			}, {
				label: _('Logout'),
				'default': true,
				callback: lang.hitch(this, function() {
					topic.publish('/umc/actions', 'session', 'logout');
					deferred.resolve();
				})
			}]);
			return deferred;
		}
	};
	lang.setObject('umc.login', login);
	return login;
});
