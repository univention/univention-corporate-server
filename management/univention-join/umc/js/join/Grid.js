/*
 * Copyright 2013 Univention GmbH
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
	"umc/dialog",
	"umc/tools",
	"umc/store",
	"umc/widgets/Grid",
	"umc/i18n!umc/modules/join"
], function(declare, lang, array, dialog, tools, store, Grid, _) {
	return declare("umc.modules.join.Grid", [ Grid ], {
		moduleStore: null,
		_serverRole: null,

		postMixInProperties: function() {
			this.moduleStore = store('script', 'join/scripts');
			this.inherited(arguments);

			this.actions = [{
				name: 'run',
				label: _('Execute'),
				description: _('Execute this join script'),
				isContextAction: true,
				isStandardAction: true,
				isMultiAction: true,
				canExecute: function(values) {
					return (!values.configured);
				},
				callback: lang.hitch(this, function(ids) {
					ids = array.filter(ids, lang.hitch(this, function(id) { return !this.getItem(id).configured; }));
					if (ids.length === 0) {
						dialog.alert(_('You can only execute join scripts which are not successfully configured. To execute the selected scripts anyway use the force execution option.'));
						return;
					}
					this.onRunScripts(ids);
				})
			}, {
				name: 'force',
				label: _('Force execution'),
				description: _('Force execution of selected join scripts'),
				isContextAction: true,
				isMultiAction: true,
				isStandardAction: false,
				callback: lang.hitch(this, function(ids) {
					return this.onRunScripts(ids, true);
				})
			}, {
				name: 'execute_pending',
				label: 'Execute all pending scripts',
				description: _('Execute join scripts which are not properly configured.'),
				isContextAction: false,
				isMultiAction: true,
				isStandardAction: false,
				callback: lang.hitch(this, function() {
					var ids = this.getPendingIds();
					if (ids.length === 0) {
						dialog.alert(_('There are no pending join script to execute.'));
						return;
					}
					return this.onRunScripts(ids);
				})
			}, {
				name: 'rejoin',
				label: _('Rejoin'),
				description: _('Rejoins the system'),
				isContextAction: false,
				isStandardAction: false,
				canExecute: lang.hitch(this, function() { return this._serverRole != 'domaincontroller_master'; }),
				callback: lang.hitch(this, 'onRejoin')
			}, {
				name: 'logfile',
				label: _('View join log'),
				description: _('Shows the join log'),
				isContextAction: false,
				isStandardAction: false,
				callback: lang.hitch(this, 'onShowLogfile')
			}];

			this.columns = [{
				name: 'script',
				label: _("Script (package)"),
				description: _("Script name (the same as the package it belongs to)"),
				editable: false
				//width: '50%'
			}, {
				name: 'configured',
				label: _("State"),
				description: _("Status of this package"),
				editable: false,
				formatter: function(value) {
					return value ? _('successful') : _('pending');
				},
				width: '14%'
			}];
		},

		getPendingItems: function() {
			return array.filter(this.getAllItems(), function(item) { return !item.configured; });
		},

		getPendingIds: function() {
			return array.map(this.getPendingItems(), function(item) { return item.script; });
		},

		getConfiguredItems: function() {
			return array.filter(this.getAllItems(), function(item) { return item.configured; });
		},

		getConfiguredIds: function() {
			return array.map(this.getConfiguredItems(), function(item) { return item.script; });
		},

		reload_grid: function() {
			this._grid.filter({'*': '*'});
		},

		buildRendering: function() {
			this.inherited(arguments);

			tools.ucr('server/role').then(lang.hitch(this, function(values) {
				this._serverRole = values['server/role'];
			}));

			this.on('filterDone', lang.hitch(this, function() {
				this.footerFormatter(0, 0);
			}));
		},

		footerFormatter: function(nItems, nItemsTotal) {
			var nItemsSelected = array.filter(this.getSelectedItems(), function(item) { return !item.configured; }).length;
			if (nItemsSelected) {
				return nItems === 1 ? _('1 script selected') : _('%d scripts selected', nItems);
			}

			var nItemsPending = this.getPendingItems().length;
			if (nItemsPending === 0) {
				return _('Join status ok, nothing to do.');
			}

			return nItemsPending === 1 ? _("One script is pending to be run.") : _('%d scripts are pending to be run.', nItemsPending);
		},

		onShow: function() {
			this.reload_grid();
		},

		onRunScripts: function(scripts, force) {
			// event stub
		},

		onRejoin: function() {
			// event stub
		},

		onShowLogfile: function() {
			// event stub
		}
	});
});
