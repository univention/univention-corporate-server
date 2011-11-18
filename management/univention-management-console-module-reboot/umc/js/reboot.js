/*
 * Copyright 2011 Univention GmbH
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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.reboot");

dojo.require("dijit.TitlePane");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TitlePane");

dojo.declare("umc.modules.reboot", [ umc.widgets.Module, umc.i18n.Mixin ], {

	_page: null,
	_form: null,

	i18nClass: 'umc.modules.reboot',

	buildRendering: function() {
		this.inherited(arguments);

		this._page = new umc.widgets.Page({
			helpText: this._("This module can be used to restart or shut down the system remotely. The optionally given message will be displayed on the console and written to the syslog."),
			headerText: this._("Reboot or shutdown the system")
		});
		this.addChild(this._page);

		var widgets = [{
			type: 'ComboBox',
			name: 'action',
			value: 'reboot',
			label: this._('Action'),
			staticValues: [
				{id: 'reboot', label: this._('Reboot')},
				{id: 'halt', label: this._('Stop')}
			]
		}, {
			type: 'TextBox',
			name: 'message',
			label: this._('Reason for this reboot/shutdown')
		}];

		var buttons = [{
			name: 'submit',
			label: this._('Execute'),
			callback: dojo.hitch(this, function() {
				var vals = this._form.gatherFormValues();
				this.shutdown(vals);
			})
		}];

		var layout = [['action'], ['message']];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});

		var container = new umc.widgets.ContainerWidget({
			scrollable: true
		});
		this._page.addChild(container);

		var titlePane = new dijit.TitlePane({
			title: this._('Actions'),
			content: this._form
		});

		container.addChild(titlePane);
	},

	shutdown: function(data) {
		if (data.action == 'reboot') {
			var message = this._('Please confirm to reboot the computer');
		} else {
			var message = this._('Please confirm to shutdown the computer');
		}

		umc.dialog.confirm(message, [{
			label: this._('OK'),
			callback: dojo.hitch(this, function() {
				this.umcpCommand('reboot/reboot', data);
			})
		}, {
			label: this._('Cancel')
		}]);
	}
});
