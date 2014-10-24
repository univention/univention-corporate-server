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
/*global define*/

define([
	"dojo/topic",
	"umc/app",
	"umc/tools",
	"umc/dialog",
	"umc/modules/lib/server",
	"dijit/MenuItem",
	"umc/i18n!umc/modules/reboot"
], function(topic, app, tools, dialog, libServer, MenuItem, _) {

	var addRebootMenu = function() {
		app.addMenuEntry(new MenuItem({
			id: 'umcMenuShutdown',
			iconClass: 'icon24-umc-menu-shutdown',
			label: _('Shutdown server'),
			onClick: function() {
				libServer.askShutdown();
			}
		}));
		app.addMenuEntry(new MenuItem({
			id: 'umcMenuReboot',
			iconClass: 'icon24-umc-menu-reboot',
			label: _('Reboot server'),
			onClick: function() {
				libServer.askReboot();
			}
		}));
	};

	var checkRebootRequired = function() {
		tools.ucr(['update/reboot/required']).then(function(_ucr) {
			if (tools.isTrue(_ucr['update/reboot/required'])) {
				dialog.notify(_('This system has been updated recently. Please reboot this system to finish the update.'));
				libServer.askReboot(_('This system has been updated recently. Please reboot this system to finish the update.'));
			}
		});
	};

	topic.subscribe('/umc/started', function() {
		addRebootMenu();
		checkRebootRequired();
	});

	return null;
});
