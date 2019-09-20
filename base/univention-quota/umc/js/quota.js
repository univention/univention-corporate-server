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
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojox/string/sprintf",
	"umc/dialog",
	"umc/tools",
	"umc/store",
	"umc/widgets/Grid",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/modules/quota/PartitionPage",
	"umc/modules/quota/DetailPage",
	"umc/i18n!umc/modules/quota"
], function(declare, lang, array, sprintf, dialog, tools, store, Grid, Module, Page, PartitionPage, DetailPage, _) {

	return declare("umc.modules.quota", [ Module ], {

		idProperty: 'partitionDevice',
		moduleStore: null,
		_overviewPage: null,
		_partitionPage: null,
		_detailPage: null,

		selectablePagesToLayoutMapping: {
			'_overviewPage': 'searchpage-grid',
			'_partitionPage': 'searchpage-grid',
			'_detailPage': ''
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.renderOverviewPage();
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this.moduleStore = store(this.idProperty, this.moduleID + '/partitions');
		},

		renderOverviewPage: function() {
			this._overviewPage = new Page({
				title: _('Partitions'),
				moduleStore: this.moduleStore,
				helpText: _('Set, unset and modify filesystem quota'),
				fullWidth: true
			});
			this.addChild(this._overviewPage);
			this.selectChild(this._overviewPage);

			var actions = [{
				name: 'activate',
				label: _('Activate'),
				isStandardAction: true,
				canExecute: function(item) { return !item.inUse; },
				callback: lang.hitch(this, 'activateQuota')
			}, {
				name: 'deactivate',
				label: _('Deactivate'),
				isStandardAction: true,
				canExecute: function(item) { return item.inUse; },
				callback: lang.hitch(this, 'activateQuota')
			}, {
				name: 'edit',
				label: _('Configure'),
				iconClass: 'umcIconEdit',
				isStandardAction: true,
				isMultiAction: false,
				canExecute: function(item) { return item.inUse; },
				callback: lang.hitch(this, function(partitionDevice) {
					this.editPartition(partitionDevice[0]);
				})
			}, {
				name: 'refresh',
				label: _('Refresh'),
				isContextAction: false,
				isStandardAction: true,
				isMultiAction: false,
				callback: lang.hitch(this, function() {
					this.refreshGrid();
				})
			}];

			var columns = [{
				name: 'partitionDevice',
				label: _('Partition'),
				width: 'auto'
			}, {
				name: 'mountPoint',
				label: _('Mount point'),
				width: 'auto'
			}, {
				name: 'inUse',
				label: _('Quota'),
				width: '85px',
				formatter: lang.hitch(this, function(value) {
					if (value === null) {
						return _('Unknown');
					} else if (value === true) {
						return _('Activated');
					} else {
						return _('Deactivated');
					}
				})
			}, {
				name: 'partitionSize',
				label: _('Size (GB)'),
				width: 'adjust',
				formatter: function(value) {
					if (value === null) {
						return '-';
					} else {
						return sprintf('%.1f', value);
					}
				}
			}, {
				name: 'freeSpace',
				label: _('Free (GB)'),
				width: 'adjust',
				formatter: function(value) {
					if (value === null) {
						return '-';
					} else {
						return sprintf('%.1f', value);
					}
				}
			}];

			var defaultAction = function(partitionName, partitionInfos) {
				if (partitionInfos[0].inUse) {
					return "edit";
				} else {
					return "activate";
				}
			};

			this._grid = new Grid({
				region: 'main',
				actions: actions,
				columns: columns,
				moduleStore: this.moduleStore,
				defaultAction: defaultAction,
				query: {
					dummy: 'dummy'
				}
			});

			this._grid.on('FilterDone', lang.hitch(this, function() {
				var gridItems = this._grid.getAllItems(); // TODO rename?
				array.forEach(gridItems, lang.hitch(this, function(item) {
					if (item.inUse === null) {
						this._grid.setDisabledItem(item.partitionDevice, true);
					}
				}));
			}));

			this._overviewPage.addChild(this._grid);
			this._overviewPage.startup();
		},

		activateQuota: function(partitionDevices, items) {
			var partitionDevice = partitionDevices[0];
			var item = items[0];
			var doActivate = !item.inUse;

			var dialogMessage = '';
			if (doActivate === true) {
				dialogMessage = _('Please confirm quota support activation on device: %s', [partitionDevice]);
			} else {
				dialogMessage = _('Please confirm quota support deactivation on device: %s', [partitionDevice]);
			}
			dialog.confirm(dialogMessage, [{
				label: _('Cancel'),
				'default': true
			}, {
				label: _('OK'),
				callback: lang.hitch(this, function() {
					var cmd = 'quota/partitions/' + (doActivate ? 'activate' : 'deactivate');
					var opts = {"partitionDevice" : partitionDevice};
					this.standbyDuring(tools.umcpCommand(cmd, opts)).then(lang.hitch(this, function(data) {
						if (data.result.success === true) {
							this.refreshGrid();
						} else {
							this._showActivateQuotaDialog(data.result, doActivate);
						}
					}));
				})
			}]);
		},

		refreshGrid: function() {
			this._grid.filter({'dummy': 'dummy'});
		},

		_showActivateQuotaDialog: function(result, doActivate) {
			var message = [];
			if (doActivate === true) {
				message = _('Failed to activate quota support: ');
			} else {
				message = _('Failed to deactivate quota support: ');
			}
			array.forEach(result.objects, function(item) {
				if (item.success === false) {
					message = message + item.message;
				}
			});
			dialog.confirm(message, [{
				label: _('OK')
			}]);
		},

		editPartition: function(partitionDevice) {
			this.renderPartitionPage(partitionDevice);
			this.renderDetailPage(partitionDevice);
			this.selectChild(this._partitionPage);
		},

		renderPartitionPage: function(partitionDevice) {
			this._partitionPage = new PartitionPage({
				partitionDevice: partitionDevice,
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring'),
				moduleStore: store('id', this.moduleID + '/users'),
				headerText: _('Partition: %s', partitionDevice),
				fullWidth: true
			});
			this.addChild(this._partitionPage);
			this._partitionPage.on('ShowDetailPage', lang.hitch(this, function(userQuota) {
				this._detailPage.init(userQuota);
				this.selectChild(this._detailPage);
			}));
			this._partitionPage.on('showOverview', lang.hitch(this, 'showOverview'));
		},

		renderDetailPage: function(partitionDevice) {
			this._detailPage = new DetailPage({
				partitionDevice: partitionDevice,
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring'),
				fullWidth: true
			});
			this.addChild(this._detailPage);
			this._detailPage.on('ClosePage', lang.hitch(this, function() {
				this.selectChild(this._partitionPage);
			}));
			this._detailPage.on('SetQuota', lang.hitch(this, function(values) {
				this.standbyDuring(tools.umcpCommand('quota/users/set', values)).then(lang.hitch(this, function(data) {
					if (data.result.success === true) {
						this.selectChild(this._partitionPage);
						this._partitionPage.filter();
					}
				}));
			}));
		},

		showOverview: function() {
			this.selectChild(this._overviewPage);
			this.removeChild(this._partitionPage);
			this.removeChild(this._detailPage);
			this._partitionPage.destroyRecursive();
			this._detailPage.destroyRecursive();
		}
	});
});
