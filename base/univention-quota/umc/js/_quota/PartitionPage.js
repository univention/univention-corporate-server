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

dojo.provide("umc.modules._quota.PartitionPage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.Text");

dojo.declare("umc.modules._quota.PartitionPage", [ umc.widgets.Page, umc.i18n.Mixin ], {

	moduleStore: null,
	partitionDevice: null,
	footerButtons: null,
	_grid: null,
	_partitionInfo: null,
	_searchForm: null,

	i18nClass: 'umc.modules.quota',

	_getPartitionInfo: function() {
		umc.tools.umcpCommand('quota/partitions/info', {'partitionDevice': this.partitionDevice}).then(dojo.hitch(this, function(data) {
			this._partitionInfo.set('content', dojo.replace('<p>' + this._('Mount point: ') + '{mountPoint} ' + this._('Filesystem: ') + '{filesystem} ' + this._('Options: ') + ' {options}' + '</p>', data.result));
		}));
	},

	buildRendering: function() {
		this.inherited(arguments);
		this.renderGrid();
		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Quota settings')
		});
		this.addChild(titlePane);
		this._partitionInfo = new umc.widgets.Text({
			region: 'top',
			content: '<p>' + this._('loading...') + '</p>'
		});
		this._getPartitionInfo();
		titlePane.addChild(this._partitionInfo);
		titlePane.addChild(this._searchForm);
		titlePane.addChild(this._grid);
	},

	postCreate: function() {
		this.inherited(arguments);
		this.startup();
	},

	renderGrid: function() {
		var widgets = [{
			type: 'TextBox',
			name: 'filter',
			value: '*',
			label: this._('User:')
		}];

		this._searchForm = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: [['filter', 'submit', 'reset']],
			onSearch: dojo.hitch(this, function(data) {
				data.partitionDevice = this.partitionDevice;
				this._grid.filter(data);
			})
		});

		var actions = [{
			name: 'add',
			label: this._('Add user'),
			iconClass: 'umcIconAdd',
			isContextAction: false,
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function() {
				this.onShowDetailPage();
			})
		}, {
			name: 'edit',
			label: this._('Configure'),
			iconClass: 'umcIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(data) {
				item = this._grid.getItem(data);
				this.onShowDetailPage(item);
			})
		}, {
			name: 'remove',
			label: this._('Remove'),
			iconClass: 'umcIconDelete',
			isStandardAction: true,
			isMultiAction: true,
			callback: dojo.hitch(this, function(data) {
				this.onRemoveUsers(data);
			})
		}];

		var columns = [{
			name: 'user',
			label: this._('User'),
			width: 'auto'
		}, {
			name: 'sizeLimitUsed',
			label: this._('Size used (MB)'),
			width: 'adjust'
		}, {
			name: 'sizeLimitSoft',
			label: this._('Soft (MB)'),
			width: 'adjust'
		}, {
			name: 'sizeLimitHard',
			label: this._('Hard (MB)'),
			width: 'adjust'
		}, {
			name: 'sizeLimitTime',
			label: this._('Grace'),
			width: 'adjust'
		}, {
			name: 'fileLimitUsed',
			label: this._('Files used'),
			width: 'adjust'
		}, {
			name: 'fileLimitSoft',
			label: this._('Soft'),
			width: 'adjust'
		}, {
			name: 'fileLimitHard',
			label: this._('Hard'),
			width: 'adjust'
		}, {
			name: 'fileLimitTime',
			label: this._('Grace'),
			width: 'adjust'
		}];

		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore,
			query: {
				filter: '*',
				partitionDevice: this.partitionDevice
			}
		});
	},

	filter: function() {
		var data = this._searchForm.gatherFormValues();
		data.partitionDevice = this.partitionDevice;
		this._grid.filter(data);
	},

	onShowDetailPage: function(data) {
		return true;
	},

	onClosePage: function() {
		return true;
	},

	onRemoveUsers: function(ids) {
		var dialogMessage = '';
		var usernames = dojo.map(ids, dojo.hitch(this, function(id) {
			item = this._grid.getItem(id);
			return item.user;
		}));
		if (usernames.length == 0) {
			return
		} else if (usernames.length == 1) {
			dialogMessage = this._('Please confirm to remove the following user: %s', usernames);
		} else {
			dialogMessage = this._('Please confirm to remove the following %(length)s users: %(usernames)s', {'usernames': usernames, 'length': usernames.length});
		}
		umc.dialog.confirm(dialogMessage, [{
			label: this._('OK'),
			callback: dojo.hitch(this, function() {
				var transaction = this.moduleStore.transaction();
				dojo.forEach(ids, function(iid) {
					this.moduleStore.remove(iid);
				}, this);
				transaction.commit().then(dojo.hitch(this, function(data) {
					if (data.success === false) {
						var failed = [];
						dojo.forEach(data.objects, function(item) {
							if (item.success === false) {
								var gridItem = this._grid.getItem(item.id);
								failed.push(gridItem.user);
							}
						});
						var message = this._('Could not remove the following user: %s', failed);
						umc.dialog.confirm(message, [{
							label: this._('OK')
						}]);
					}
				}));
			})
		}, {
			label: this._('Cancel')
		}]);
	}
});
