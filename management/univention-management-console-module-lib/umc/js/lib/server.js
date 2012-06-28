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
/*global console dojo dojox dijit umc setTimeout*/

dojo.provide("umc.modules.lib.server");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.dialog");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("dijit.Dialog");
dojo.require("dijit.ProgressBar");

dojo.mixin(umc.modules.lib.server, new umc.i18n.Mixin({
	// use the lib wide translation file
	i18nClass: [ 'umc.modules.lib' ]
}), {
	askRestart: function(_msg) {
		// TODO: first call to: lib/server/restart/isNeeded
		//       if no restart is needed -> do not show any alert
		var msg = '';
		if (_msg) {
			msg += '<p>' + _msg + '</p>';
		}
		msg += '<p>' + this._('Please confirm to restart UMC server components and the HTTP web server.') + '</p>';
		msg += '<p>' + this._('<b>Note:</b> After the restart you will be redirected to the login page.') + '</p>';
		return umc.dialog.confirm(msg, [{
			name: 'cancel',
			label: this._('Cancel')
		}, {
			name: 'restart',
			'default': true,
			label: this._('Restart')
		}]).then(dojo.hitch(this, function(response) {
			if (response == 'restart') {
				return this.restart();
			}
			// throw error two break the deferred chain
			throw new Error('restart canceled');
		}));
	},

	restart: function() {
		var container = new umc.widgets.ContainerWidget({});
		container.addChild(new umc.widgets.Text({
			content: '<p>' + this._('Please wait while UMC server components and HTTP web server are being restarted.') + '</p>'
		}));
		container.addChild(new dijit.ProgressBar({
			indeterminate: true
		}));

		var dialog = new dijit.Dialog({
			title: this._('Restarting server'),
			content: container.domNode,
			closable: false,
			// overwrite _onKey to avoid closing via escape
			_onKey: function() {}
		});

		// hide the dialog's close button
		dojo.style(dialog.closeButtonNode, 'display', 'none');

		// show the dialog
		dialog.show();

		// sent the server request
		var deferred = new dojo.Deferred();
		umc.tools.umcpCommand('lib/server/restart', { restart: true }).then(function() {
			// wait for 10sec before closing the session
			setTimeout(function() {
				// close the session and force the login dialog to appear
				umc.tools.checkSession(false);
				umc.tools.closeSession();
				deferred.resolve(true);
				window.location.reload();
			}, 10000);
		}, function() {
			// error handling
			dialog.destroyRecursive();
			container.destroyRecursive();
			deferred.cancel();
		});

		return deferred;
	}
});





