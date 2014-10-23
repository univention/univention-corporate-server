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
	"dojo/on",
	"umc/app",
	"umc/modules/lib/server",
	"dijit/MenuItem",
	"umc/i18n!umc/modules/reboot"
], function(on, app, libServer, MenuItem, _) {

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

	on.once(app, 'ModulesLoaded', function() {
		addRebootMenu();
	});

	return null;
});
