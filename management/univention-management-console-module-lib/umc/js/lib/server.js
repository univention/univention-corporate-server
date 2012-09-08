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
/*global define window*/

define([
	"dojo/_base/lang",
	"dojo/dom-style",
	"dojo/Deferred",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"dijit/Dialog",
	"dijit/ProgressBar",
	"umc/i18n!umc/modules/lib"
], function(lang, style, Deferred, tools, dialog, Text, ContainerWidget, DijitDialog, DijitProgressBar, _) {

	return {
		askRestart: function(_msg) {
			// TODO: first call to: lib/server/restart/isNeeded
			//       if no restart is needed -> do not show any alert
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
				if (response == 'restart') {
					return this.restart();
				}
				// throw error two break the deferred chain
				throw new Error('restart canceled');
			}));
		},

		restart: function() {
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
		}
	};

});
