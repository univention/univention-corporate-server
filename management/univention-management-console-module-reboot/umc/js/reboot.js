/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
