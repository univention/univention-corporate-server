/*
 * Copyright 2012-2019 Univention GmbH
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
/*global define window require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/Deferred",
	"dojo/topic",
	"dojo/_base/xhr",
	"umc/tools",
	"umc/app",
	"umc/dialog",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"dijit/Dialog",
	"dijit/ProgressBar",
	"umc/i18n!umc/modules/lib"
], function(declare, lang, Deferred, topic, basexhr, tools, app, dialog, Text, ContainerWidget, DijitDialog, DijitProgressBar, _) {

	var _ProgressDialog = declare([DijitDialog], {
		_progressBar: null,
		postMixInProperties: function() {
			this.inherited(arguments);

			var container = new ContainerWidget({});
			container.addChild(this._message = new Text({}));
			container.addChild(this._progressBar = new DijitProgressBar({
				indeterminate: true
			}));

			this.content = container;
		},

		update: function(message) {
			this._message.set('content', '<p>' + message + '</p>');
			//this._progressBar.update({label: message});
		},

		close: function() {
			var hideDeferred = this.hide();
			if (hideDeferred) {
				return hideDeferred.then(lang.hitch(this, 'destroyRecursive'));
			}
		}
	});

	return {
		_askingForRestart: false,
		_keepSessionOpen: function() {
			if (!this._askingForRestart) {
				// stop when dialog has been closed
				return;
			}

			var timeout = 1000 * Math.min(tools.status('sessionTimeout') / 2, 30);
			window.setTimeout(lang.hitch(this, function() {
				this.ping().then(
					lang.hitch(this, '_keepSessionOpen'),
					lang.hitch(this, '_keepSessionOpen')
				); // ignore errors
			}), timeout);
		},

		askRestart: function(_msg) {
			// TODO: first call to: lib/server/restart/isNeeded
			//       if no restart is needed -> do not show any alert
			topic.publish('/umc/actions', 'lib', 'server', 'askRestart');

			this._askingForRestart = true;
			tools.status('ignorePageReload', true);
			this._keepSessionOpen();

			var msg = '';
			if (_msg) {
				msg += '<p>' + _msg + '</p>';
			}
			msg += '<p>' + _('Please confirm to restart UMC server components and the HTTP web server. This will take approximately 10 seconds.') + '</p>';
			msg += '<p>' + _('<b>Note:</b> After the restart you will be redirected to the login page.') + '</p>';
			return dialog.confirm(msg, [{
				name: 'cancel',
				label: _('Cancel')
			}, {
				name: 'restart',
				'default': true,
				label: _('Restart')
			}]).then(lang.hitch(this, function(response) {
				this._askingForRestart = false;
				if (response == 'restart') {
					return this.restart();
				}
				tools.status('ignorePageReload', false);
				// reload modules
				return app.reloadModules().always(function() {
					// throw error to break the deferred chain
					throw new Error('restart canceled');
				});
			})).then(function() {
				window.location.reload();
			});
		},

		restart: function() {
			topic.publish('/umc/actions', 'lib', 'server', 'restart');

			// send the server request
			var progress = new _ProgressDialog({
				title: _('Restarting server'),
				closable: false
			});
			progress.update(_('Please wait while UMC server components and HTTP web server are being restarted.'));
			progress.show();

			var deferred = new Deferred();
			tools.umcpCommand('lib/server/restart', { restart: true }).then(function() {
				// wait for 10sec before closing the session
				window.setTimeout(function() {
					// close the session and force the login dialog to appear
					tools.checkSession(false);
					tools.closeSession();
					progress.close();
					deferred.resolve(true);
				}, 10000);
			}, function() {
				progress.close();
			});

			return deferred.promise;
		},

		askReboot: function(_msg) {
			topic.publish('/umc/actions', 'lib', 'server', 'askReboot');
			tools.status('ignorePageReload', true);

			var msg = _msg ? '<p>' + _msg + '</p>' : '';
			msg += '<p>' + _('Please confirm to reboot this server. This may take a few minutes.') + '</p>';
			msg += '<p>' + _('<b>Note:</b> After the restart you will be redirected to the login page.') + '</p>';
			return dialog.confirm(msg, [{
				name: 'cancel',
				label: _('Cancel')
			}, {
				name: 'reboot',
				'default': true,
				label: _('Reboot')
			}]).then(lang.hitch(this, function(response) {
				if (response == 'reboot') {
					return this.reboot();
				}
				tools.status('ignorePageReload', false);
				// throw error to break the deferred chain
				throw new Error('restart canceled');
			})).then(function() {
				window.location.reload(true);
			});
		},

		reboot: function() {
			topic.publish('/umc/actions', 'lib', 'server', 'reboot');

			var progress = new _ProgressDialog({
				title: _('Rebooting server'),
				closable: false
			});
			progress.update(_('The server is being rebooted.'));
			progress.show();

			var offline = false;
			var timer = null;
			var milliseconds = 5000;
			var deferred = new Deferred();

			var start_pinging = function() {
				basexhr("HEAD", {url: require.toUrl("umc/").replace(/js_\$.*?\$/, 'js'), timeout: 3000}).then(function() {
					if (offline) {
						// online again
						progress.close(true);
						deferred.resolve(true);
						window.clearTimeout(timer);
						return;
					}
					timer = window.setTimeout(start_pinging, milliseconds);
				}, function() {
					offline = true;
					timer = window.setTimeout(start_pinging, milliseconds);
				});
			};

			tools.umcpCommand('lib/server/reboot').then(start_pinging, function() {
				progress.close();
			});

			return deferred.promise;
		},

		askShutdown: function(_msg) {
			topic.publish('/umc/actions', 'lib', 'server', 'askShutdown');
			tools.status('ignorePageReload', true);

			var msg = _msg ? '<p>' + _msg + '</p>' : '';
			msg += '<p>' + _('Please confirm to shutdown this server. This may take a few minutes.') + '</p>';
			return dialog.confirm(msg, [{
				name: 'cancel',
				label: _('Cancel')
			}, {
				name: 'shutdown',
				'default': true,
				label: _('Shutdown')
			}]).then(lang.hitch(this, function(response) {
				if (response == 'shutdown') {
					return this.shutdown();
				}
				tools.status('ignorePageReload', false);
				// throw error to break the deferred chain
				throw new Error('shutdown canceled');
			})).always(function() {
				tools.status('ignorePageReload', false);
			});
		},

		shutdown: function() {
			topic.publish('/umc/actions', 'lib', 'server', 'shutdown');

			var deferred = new Deferred();

			var progress = new _ProgressDialog({
				title: _('Shutting down server'),
				closable: false
			});
			progress.update(_('The server is shutting down.'));
			progress.show();

			var timer = null;
			var milliseconds = 5000;

			var start_pinging = function() {
				basexhr("HEAD", {url: require.toUrl("umc/").replace(/js_\$.*?\$/, 'js'), timeout: 3000}).then(function() {
					timer = window.setTimeout(start_pinging, milliseconds);
				}, function() {
					deferred.resolve();
					progress.close();
					tools.closeSession();
					window.clearTimeout(timer);
				});
			};

			tools.umcpCommand('lib/server/shutdown').then(start_pinging, function() {
				progress.close();
				deferred.reject();
			});
			return deferred.promise;
		},

		ping: function() {
			// ignore errors from pinging
			return tools.umcpCommand('lib/server/ping', {}, false);
		}
	};

});
