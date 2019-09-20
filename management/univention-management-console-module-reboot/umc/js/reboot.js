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
/*global define*/

define([
	"dojo/topic",
	"umc/app",
	"umc/menu",
	"umc/tools",
	"umc/dialog",
	"umc/modules/lib/server",
	"umc/i18n!umc/modules/reboot"
], function(topic, app, menu, tools, dialog, libServer, _) {

	var addRebootMenu = function() {
		menu.addSubMenu({
			priority: 70,
			label: _('Server'),
			id: 'umcMenuServer'
		});
		menu.addEntry({
			parentMenuId: 'umcMenuServer',
			id: 'umcMenuShutdown',
			label: _('Shutdown server'),
			onClick: function() {
				topic.publish('/umc/actions', 'menu', 'server', 'shutdown');
				libServer.askShutdown();
			}
		});
		menu.addEntry({
			parentMenuId: 'umcMenuServer',
			id: 'umcMenuReboot',
			label: _('Reboot server'),
			onClick: function() {
				topic.publish('/umc/actions', 'menu', 'server', 'reboot');
				libServer.askReboot();
			}
		});
	};

	var checkRebootRequired = function() {
		tools.ucr(['update/reboot/required']).then(function(_ucr) {
			if (tools.isTrue(_ucr['update/reboot/required'])) {
				dialog.notify(_('This system has been updated recently. Please reboot this system to finish the update.'));
			//	libServer.askReboot(_('This system has been updated recently. Please reboot this system to finish the update.'));
			}
		});
	};

	app.registerOnStartup(function() {
		addRebootMenu();
		checkRebootRequired();
	});

	return null;
});
