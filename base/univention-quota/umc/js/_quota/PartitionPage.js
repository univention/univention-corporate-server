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
			iconClass: 'dijitIconNewTask',
			isContextAction: false,
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function() {
				this.onShowDetailPage();
			})
		}, {
			name: 'edit',
			label: this._('Configure'),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function() {
				var userQuota = this._grid.getSelectedItems()[0];
				this.onShowDetailPage(userQuota);
			})
		}, {
			name: 'remove',
			label: this._('Remove'),
			iconClass: 'dijitIconDelete',
			isStandardAction: true,
			isMultiAction: true,
			callback: dojo.hitch(this, function() {
				this.onRemoveUsers();
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
		this._grid.filter({
			filter: '*',
			partitionDevice: this.partitionDevice
		});
	},

	onShowDetailPage: function(data) {
		return true;
	},

	onClosePage: function() {
		return true;
	},

	onRemoveUsers: function() {
		var dialogMessage = '';
		var users = dojo.map(this._grid.getSelectedItems(), function(iitem) {
			return iitem.user;
		});
		if (users.length == 1) {
			dialogMessage = this._('Please confirm to remove the following user: %s', users);
		} else {
			dialogMessage = this._('Please confirm to remove the following %(length)s users: %(users)s', {'users': users, 'length': users.length});
		}
		umc.dialog.confirm(dialogMessage, [{
			label: this._('OK'),
			callback: dojo.hitch(this, function() {
				var transaction = this.moduleStore.transaction();
				dojo.forEach(this._grid.getSelectedIDs(), function(iid) {
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
						var message = this._('Could not remove the following user: %s', failed)
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
