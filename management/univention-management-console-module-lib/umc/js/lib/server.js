/*
 * Copyright 2012 Univention GmbH
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
/*global define window setTimeout*/

define([
	"dojo/_base/lang",
	"dojo/dom-style",
	"dojo/Deferred",
	"dojo/topic",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ConfirmDialog",
	"dijit/Dialog",
	"dijit/ProgressBar",
	"umc/i18n!umc/modules/lib"
], function(lang, style, Deferred, topic, tools, dialog, Text, ContainerWidget, ConfirmDialog, DijitDialog, DijitProgressBar, _) {

	return {
		_askingForRestart: false,
		_keepSessionOpen: function() {
			if (!this._askingForRestart) {
				// stop when dialog has been closed
				return;
			}

			var timeout = 1000 * Math.min(tools.status('sessionTimeout') / 2, 30);
			setTimeout(lang.hitch(this, function() {
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
			this._keepSessionOpen();

			var msg = '';
			if (_msg) {
				msg += '<p>' + _msg + '</p>';
			}
			msg += '<p>' + _('Please confirm to restart UMC server components and the HTTP web server. This will take approximately 10 seconds.') + '</p>';
			msg += '<p>' + _('<b>Note:</b> After the restart you will be redirected to the login page.') + '</p>';
			var _dialog = new ConfirmDialog({
				title: _('Server restart'),
				message: msg,
				options: [{
					name: 'cancel',
					label: _('Cancel')
				}, {
					name: 'restart',
					'default': true,
					label: _('Restart')
				}]
			});

			// handle user feedback
			var deferred = new Deferred();
			_dialog.on('confirm', lang.hitch(this, function(response) {
				this._askingForRestart = false;
				if (response == 'restart') {
					deferred.resolve(this.restart());
				}
				// break the deferred chain
				deferred.cancel();
				_dialog.close();
			}));

			// in case the user clicks on 'x' button or hits escape
			_dialog.on('hide', lang.hitch(this, function() {
				this._askingForRestart = false;
				if (!deferred.isFulfilled()) {
					deferred.cancel();
				}
				_dialog.destroyRecursive();
			}));

			_dialog.show();
			return deferred;
		},

		restart: function() {
			topic.publish('/umc/actions', 'lib', 'server', 'restart');

			var container = new ContainerWidget({});
			container.addChild(new Text({
				content: '<p>' + _('Please wait while UMC server components and HTTP web server are being restarted.') + '</p>'
			}));
			container.addChild(new DijitProgressBar({
				indeterminate: true
			}));

			var _dialog = new DijitDialog({
				title: _('Restarting server'),
				content: container.domNode,
				closable: false,
				// overwrite _onKey to avoid closing via escape
				_onKey: function() {}
			});

			// hide the dialog's close button
			style.set(_dialog.closeButtonNode, 'display', 'none');

			// show the dialog
			_dialog.show();

			// sent the server request
			var deferred = new Deferred();
			tools.umcpCommand('lib/server/restart', { restart: true }).then(function() {
				// wait for 10sec before closing the session
				window.setTimeout(function() {
					// close the session and force the login dialog to appear
					tools.checkSession(false);
					tools.closeSession();
					deferred.resolve(true);
					window.location.reload();
				}, 10000);
			}, function() {
				// error handling
				_dialog.destroyRecursive();
				container.destroyRecursive();
				deferred.cancel();
			});

			return deferred;
		},

		ping: function() {
			// ignore errors from pinging
			return tools.umcpCommand('lib/server/ping', {}, false);
		}
	};

});
