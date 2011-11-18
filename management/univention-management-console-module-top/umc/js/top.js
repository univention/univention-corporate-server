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

dojo.provide("umc.modules.top");

dojo.require("dojox.string.sprintf");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");

dojo.declare("umc.modules.top", [ umc.widgets.Module, umc.i18n.Mixin ], {

	_grid: null,
	_store: null,
	_searchWidget: null,
	_contextVariable: null,
	_page: null,

	i18nClass: 'umc.modules.top',
	idProperty: 'pid',

	killProcesses: function(signal, pids) {
		var params = {
			signal: signal,
			pid: pids
		};
		if (pids.length == 1) {
			var msg = this._('Please confirm sending %s to the selected process!', signal);
		}
		else {
			var msg = this._('Please confirm sending %(sig)s to the %(pids)s selected processes!', {sig: signal, pid: pids.length});
		}
		umc.dialog.confirm(msg, [{
			label: this._('OK'),
			callback: dojo.hitch(this, function() {
				this.umcpCommand('top/kill', params).then(dojo.hitch(this, function() {
					umc.dialog.notify(this._('Signal (%s) sent successfully', signal));
				}));
			})
		}, {
			label: this._('Cancel')
		}]);
	},

	buildRendering: function() {
		this.inherited(arguments);

		this._page = new umc.widgets.Page({
			headerText: this._('Process overview'),
			helpText: this._('This module generates an overview of all running processes. The search function can reduce the number of results. Specified processes can be selected and terminated. If a process can\'t be normally terminated (using SIGTERM signal), the termination can be forced (using SIGKILL signal).')
		});
		this.addChild(this._page);

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Entries')
		});
		this._page.addChild(titlePane);

		var actions = [{
			name: 'terminate',
			label: this._('Terminate'),
			callback: dojo.hitch(this, 'killProcesses', 'SIGTERM'),
			isStandardAction: false,
			isMultiAction: true
		}, {
			name: 'kill',
			label: this._('Force terminate'),
			callback: dojo.hitch(this, 'killProcesses', 'SIGKILL'),
			isStandardAction: false,
			isMultiAction: true
		}];

		var columns = [{
			name: 'user',
			label: this._('User'),
            width: '100px'
		}, {
			name: 'pid',
			label: this._('PID'),
            width: '70px'
		}, {
			name: 'cpu',
			label: this._('CPU (%)'),
			width: 'adjust',
			formatter: function(value) {
				return dojox.string.sprintf('%.1f', value);
			}
		}, {
			name: 'mem',
			label: this._('Memory (%)'),
			width: 'adjust',
			formatter: function(value) {
				return dojox.string.sprintf('%.1f', value);
			}
		}, {
			name: 'command',
			label: this._('Command'),
            width: 'auto'
		}];

		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore,
			sortIndex: '-3',
			query: {
                category: 'all',
                filter: '*'
            }
		});
		titlePane.addChild(this._grid);

		var widgets = [{
			type: 'ComboBox',
			name: 'category',
			value: 'all',
			label: this._('Category'),
			staticValues: [
				{id: 'all', label: this._('All')},
				{id: 'user', label: this._('User')},
				{id: 'pid', label: this._('PID')},
				{id: 'command', label: this._('Command')}
			]
		}, {
			type: 'TextBox',
			name: 'filter',
			value: '*',
			label: this._('Keyword')
		}];

		this._searchWidget = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: [[ 'category', 'filter', 'submit', 'reset' ]],
			onSearch: dojo.hitch(this._grid, 'filter')
		});

		titlePane.addChild(this._searchWidget);

		this._page.startup();
    }
});
