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
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"umc/app",
	"umc/modules/lib/server",
	"dijit/MenuItem",
	"umc/dialog",
	"umc/widgets/Form",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/TextArea",
	"umc/i18n!umc/modules/reboot"
], function(declare, lang, array, on, app, libServer, MenuItem, dialog, Form, Module, Page, TextArea, _) {

//	var RebootPage = declare([Page], {
//		_form: null,
//		helpText: _("This module can be used to restart or shut down the system remotely. The optionally given message will be displayed on the console and written to the syslog."),
//		headerText: _("Reboot or shutdown the system"),
//
//		buildRendering: function() {
//			this.inherited(arguments);
//			var buttons = [{
//				name: 'halt',
//				label: _('Stop'),
//				'default': true,
//				callback: lang.hitch(this, 'shutdown', false)
//			}, {
//				name: 'reboot',
//				label: _('Reboot'),
//				'default': true,
//				callback: lang.hitch(this, 'shutdown', true)
//			}];
//
//			this._form = new Form({
//				region: 'main',
//				widgets: [{
//					type: TextArea,
//					rows: 4,
//					name: 'message',
//					label: _('Reason for this reboot/shutdown')
//				}],
//				buttons: buttons
//			});
//			this.addChild(this._form);
//		},
//
//		shutdown: function(reboot) {
//			var msg = this._form.getWidget('message').get('value');
//
//			var message;
//			if (reboot) {
//				message = _('Please confirm to reboot the computer');
//			} else {
//				message = _('Please confirm to shutdown the computer');
//			}
//
//			dialog.confirm(message, [{
//				label: _('OK'),
//				callback: lang.hitch(this, function() {
//					this.umcpCommand('reboot/reboot', {
//						action: reboot ? 'reboot' : 'halt',
//						message: msg
//					});
//				})
//			}, {
//				'default': true,
//				label: _('Cancel')
//			}]);
//		}
//	});

	//	once there was a module
//	var Reboot = declare("umc.modules.reboot", Module, {
//		buildRendering: function() {
//			this.inherited(arguments);
//			this.addChild(new RebootPage({}));
//		}
//	});

	var addRebootMenu = function() {
		app._header._headerMenu.addChild(new MenuItem({
			id: 'umcMenuShutdown',
			iconClass: 'icon24-umc-menu-shutdown',
			label: _('Shutdown server'),
			onClick: function() {
				libServer.askShutdown();
			}
		}));
		app._header._headerMenu.addChild(new MenuItem({
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
