/*
 * Copyright 2011-2012 Univention GmbH
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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Grid",
	"umc/i18n!umc/modules/packages"
], function(declare, lang, array, dialog, tools, Page, StandbyMixin, Grid, _) {
	return declare("umc.modules.packages.ComponentsPage", [ Page, StandbyMixin ], {

		moduleStore: null,
		_query: { table: 'components' },

		postMixInProperties: function() {
			this.inherited(arguments);

			lang.mixin(this, {
				title: _("Components"),
				headerText: _("Additional components"),
				helpText: _("On this page, you find all additional components defined for this system. You can enable/disable/edit/delete them, and you can add new ones here.")
			});
		},

		buildRendering: function() {

			this.inherited(arguments);

			var actions =
			[
				{
					name: 'add',
					label: _('Add'),
					description: _('Add a new component definition'),
					iconClass: 'umcIconAdd',
					isContextAction: false,
					isStandardAction: true,
					callback: lang.hitch(this, function() {
						this.onShowDetail(null);
					})
				},
				{
					name: 'refresh',
					label: _('Refresh'),
					description: _('Refresh display to see current values'),
					iconClass: 'umcIconRefresh',
					isContextAction: false,
					isStandardAction: true,
					callback: lang.hitch(this, function() {
						this.refresh(true);
					})
				},
				{
					name: 'onoff',
					description: _("Enable/disable this component"),
					label: lang.hitch(this, function(values) {
						if (values === undefined) {
							return _("On/Off");
						} else {
							return (values.enabled ? _("Disable") : _("Enable"));
						}
					}),
					// iconClass: lang.hitch(this, function(values) {
					// 	if (value === undefined) {
					// 		return "";
					// 	}
					// 	return (values['enabled'] ? 'dijitIconFolderClosed' : 'dijitIconFolderOpen');
					// }),
					isStandardAction: false,
					isMultiAction: false,
					isContextAction: true,
					callback: lang.hitch(this, function(ids) {
						// Multi action doesn't make sense here since the real action depends
						// row-wise from the value of the 'enabled' property.
						var id = ids[0];
						try {
							var rowIndex = this._grid._grid.getItemIndex({name: id});
							if (rowIndex != -1) {
								var values = this._grid.getRowValues(rowIndex);
								this._enable_component(id, ! values.enabled);
							}
						} catch(error) {
							console.error("On/Off id = '" + id + "' ERROR: " + error.message);
						}
					})
				},
				{
					name: 'install',
					label: _("Install"),
					description: _("Install the component's default package(s)"),
					// iconClass: 'umcIconRefresh',
					isStandardAction: true,
					isMultiAction: false,
					isContextAction: true,
					canExecute: lang.hitch(this, function(values) {
						// Knowledge is in the Python module!
						return (values.installable === true);
					}),
					callback: lang.hitch(this, function(ids) {
						this.onInstallComponent(ids);
					})
				},
				{
					name: 'edit',
					label: _('Edit'),
					description: _('Edit the detail information about this component'),
					iconClass: 'umcIconEdit',
					isStandardAction: true,
					isMultiAction: false,
					callback: lang.hitch(this, function(ids) {
						this.onShowDetail(ids[0]);
					})
				},
				{
					name: 'delete',
					label: _('Delete'),
					description: _('Delete the selected component definition'),
					iconClass: 'umcIconDelete',
					isStandardAction: true,
					// FIXME Should we really allow multiple deletions here?
					isMultiAction: true,
					callback: lang.hitch(this, function(ids) {
						this._delete_components(ids);
					})
				}
			];

			var columns =
			[
				{
					name: 'name',
					label: _("Component Name"),
					editable: false,
					width: '40%',
					formatter:
						// Convenience function: if description is set, we include it (in brackets).
						lang.hitch(this, function(key, rowIndex) {
							var grid = this._grid;
							var tmp = grid.getRowValues(rowIndex);
							if ((typeof(tmp.description) == 'string') && (tmp.description !== ''))
							{
								return lang.replace('{name} ({description})', tmp);
							}
							return key;
						})
				},
				// trying to translate the result of get_current_component_status(component). This
				// summarizes all status variables.
				// *** NOTE *** The knowledge about internal logic is kept in the Python module,
				//				especially the 'installed' state that is combined from different
				//				variables.
				{
					name: 'status',
					label: _("Status"),
					editable: false,
					// If iconField is set -> my formatter is not called, so the raw status
					// keys would show up... but nevertheless, the code is already prepared
					// iconField: 'icon',
					formatter:
						lang.hitch(this, function(key) {
							switch(key) {
								case 'disabled': return _("Disabled");
								case 'available': return _("Available");
								case 'not_found': return _("Not found");
								case 'permission_denied': return _("Permission denied");
								case 'unknown': return _("Unknown");
								case 'installed': return _("Installed");
							}
							return key;
						})
				}
			];

			this._grid = new Grid({
				region: 'center',
				query: this._query,
				moduleStore: this.moduleStore,
				actions: actions,
				columns: columns
			});

			this.addChild(this._grid);
		},

		// switch over to the detail edit form, along with this id (empty if 'add')
		onShowDetail: function(id) {
		},

		// overload our stub from umc.widgets.Page
		refreshPage: function() {
			this.refresh(false);
		},

		// refresh the grid.
		refresh: function(standby) {
			if (standby) {
				// show the user that we're refreshing.
				this._grid.filter(this._query);
			} else {
				// silently, without standby. onload hooks are called though.
				this._grid._grid.filter(this._query);
			}
		},

		// action callback for the 'enable' and 'disable' actions. Can now handle
		// arrays (well-prepared for isMultiAction). This is the only point where
		// the grid itself has to save something.
		_enable_component: function(ids, enabled) {
			var args = [];
			if (! (ids instanceof Array)) {
				ids = [ids];
			}
			array.forEach(ids, function(id) {
				args.push({
					object: {
						name: id,
						enabled: enabled
					},
					options: null
				});
			});
			// the grid calls multiActions even if nothing is selected?
			if (args.length) {
				this.standby(true);
				tools.umcpCommand('packages/components/put', args).then(
					lang.hitch(this, function() {
						this.standby(false);
						this.refresh(); // refresh own grid
					}),
					lang.hitch(this, function() {
						this.standby(false);
					})
				);
			}
		},

		// removes a component
		_delete_components: function(ids) {

			// multiAction callback is fired even if nothing
			// is selected?
			if (! ids.length) {
				return;
			}
			var msg = lang.replace(_("Are you sure you want to delete the following components: [{ids}]"), {ids: ids});
			dialog.confirm(msg,
			[
				// deleting a component: do we allow this without confirmation if the admin
				// has turned confirmations off? (for now, we do.)
				{
					label: _('Cancel')
				},
				{
					label: _('Delete'),
					'default': true,
					callback: lang.hitch(this, function() {
						this.standby(true);
						tools.umcpCommand('packages/components/del', ids).then(
								lang.hitch(this, function() {
									this.standby(false);
									this.refresh();
								}),
								lang.hitch(this, function() {
									this.standby(false);
								})
							);
					})
				}
			]);
		},

		onShow: function() {

			this.inherited(arguments);
			this.refresh();
		},

		// Will be used from the main page
		// ready for multiAction
		onInstallComponent: function(ids) {
		}

	});
});
