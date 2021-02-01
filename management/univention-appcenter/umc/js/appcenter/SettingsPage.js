/*
 * Copyright 2011-2021 Univention GmbH
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
	"dojo/dom-class",
	"dojox/html/entities",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/TitlePane",
	"umc/widgets/Form",
	"umc/store",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, domClass, entities, dialog, tools, Page, Grid, TitlePane, Form, store, _) {
	return declare("umc.modules.appcenter.SettingsPage", [ Page ], {

		moduleStore: null,
		standby: null, // parents standby method must be passed. weird IE-Bug (#29587)
		standbyDuring: null,
		_query: { table: 'components' },
		headerTextAllowHTML: false,
		helpTextAllowHTML: false,
		helpText: _("This module shows all repositories settings defined for this system."),
		fullWidth: true,

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcAppCenterRepositorySettingsPage');


			var formWidgets = [{
				type: 'TextBox',
				name: 'server',
				label: _("Repository server")
			}, {
				type: 'TextBox',
				name: 'prefix',
				label: _("Repository prefix")
			}, {
				type: 'CheckBox',
				name: 'unmaintained',
				label: _("Use unmaintained repositories")
			}];

			var formLayout = [
				['server', 'prefix'],
				['unmaintained'],
				['submit']
			];

			var formButtons = [{
			/*	name: 'reset',
				label: _('Reset'),
				callback: lang.hitch(this, function() {
					this._form.load({}); // ID does not matter here but must be dict
					tools.forIn(this._form._widgets, function(iname, iwidget) {
						iwidget.setValid(true);
					});
				})
			}, {*/
				name: 'submit',
				'default': true,
				label: _("Apply changes"),
				callback: lang.hitch(this, function() {
					this.standby(true);
					this._form.save();
				})
			}];

			this._form = new Form({
				widgets: formWidgets,
				layout: formLayout,
				buttons: formButtons,
				style: 'margin-bottom:0;',
				moduleStore: store('server', 'appcenter/settings'),
				onSaved: lang.hitch(this, '_onSavedRepositorySettings')
			});
			this._form.load({}); // ID does not matter here but must be dict

			var titlePaneForm = new TitlePane({
				title: _("General repository settings")
			});

			titlePaneForm.addChild(this._form);
			this.addChild(titlePaneForm);

			var actions =
			[
				{
					name: 'add',
					label: _('Add'),
					description: _('Add a new component definition'),
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
					isContextAction: false,
					isStandardAction: true,
					callback: lang.hitch(this, function() {
						this.refresh(true);
					})
				},
				{
					name: 'enable',
					description: _("Enable this component"),
					label: _("Enable"),
					isStandardAction: false,
					isMultiAction: false,
					isContextAction: true,
					callback: lang.hitch(this, function(ids) {
						this._enable_component(ids, true);
					})
				},
				{
					name: 'disable',
					description: _("Disable this component"),
					label: _("Disable"),
					isStandardAction: false,
					isMultiAction: false,
					isContextAction: true,
					callback: lang.hitch(this, function(ids) {
						this._enable_component(ids, false);
					})
				},
				{
					name: 'install',
					label: _("Install"),
					description: _("Install the component's default package(s)"),
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
					label: _("Component name"),
					editable: false,
					width: '40%',
					formatter:
						// Convenience function: if description is set, we include it (in brackets).
						lang.hitch(this, function(key, rowIndex) {
							var grid = this._grid;
							var tmp = grid.getRowValues(rowIndex);
							if ((typeof(tmp.description) === 'string') && (tmp.description !== ''))
							{
								return lang.replace('{name} ({description})', tmp);
							}
							return key;
						})
				},
				// trying to translate the result of component(component).status(). This
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
				query: this._query,
				moduleStore: this.moduleStore,
				_publishPrefix: 'components',
				actions: actions,
				columns: columns
			});
			var titlePaneGrid = new TitlePane({
				title: _("Additional repositories")
			});
			titlePaneGrid.addChild(this._grid);
			this.addChild(titlePaneGrid);
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
				// show the user that we are refreshing.
				this._grid.filter(this._query);
			} else {
				// silently, without standby. onload hooks are called though.
				this._grid._grid.filter(this._query);
			}
		},

		// action callback for the 'enable' and 'disable' actions.
		_enable_component: function(ids, enabled) {
			var args = array.map(ids, function(id) {
				return {
					object: {
						name: id,
						enabled: enabled
					},
					options: null
				};
			});
			this.standbyDuring(tools.umcpCommand('appcenter/components/put', args)).then(lang.hitch(this, function() {
				this.refresh(); // refresh own grid
			}));
		},

		// removes a component
		_delete_components: function(ids) {

			var msg = lang.replace(_("Are you sure you want to delete the following components: [{ids}]"), {ids: array.map(ids, function(id) { return entities.encode(id); })});
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
						tools.umcpCommand('appcenter/components/del', ids).then(
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

		_onSavedRepositorySettings: function(success, data) {
			this.standby(false);
			if (!success) {
				return;
			}

			// this is only Python module result, not data validation result!
			var result = data;
			if (data instanceof Array) {
				result = data[0];
			}

			if (!(result.status && result.message)) {
				return;
			}

			// result['status'] is kind of error code:
			//	1 ... invalid field input
			//	2 ... error setting registry variable
			//	3 ... error committing UCR
			//	4 ... any kind of 'repo not found' conditions
			//	5 ... repo not found, but encountered without commit
			var txt = _("An unknown error with code %d occurred.", result.status);
			switch(result.status) {
				case 1: txt = _("Please correct the corresponding input fields.");
						break;
				case 2:
				case 3: txt = _("The data you entered could not be saved correctly.");
						break;
				case 4: txt = _("Using the data you entered, no valid repository could be found.<br/>Since this may be a temporary server problem as well, your data was saved though.<br/>The problem was:");
						break;
				case 5: txt = _("With the current (already changed) settings, the following problem was encountered:");
						break;
			}

			var message = lang.replace('<p>{txt}</p><p><strong>{msg}</strong></p>', {txt : txt, msg : result.message});
			dialog.alert(message);
		},

		onShow: function() {
			this.inherited(arguments);
			this.refresh();
			this._form.load({});
		},

		// Will be used from the main page
		// ready for multiAction
		onInstallComponent: function(ids) {
		}

	});
});
