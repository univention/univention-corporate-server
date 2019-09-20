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
	"umc/dialog",
	"umc/store",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/SearchForm",
	"umc/widgets/SearchBox",
	"umc/widgets/ComboBox",
	"umc/i18n!umc/modules/printers"
], function(declare, lang, dialog, store, Page, Grid, SearchForm, SearchBox, ComboBox, _) {
	return declare("umc.modules.printers.OverviewPage", [ Page ], {

		_last_filter: { key: 'printer', pattern: '' },

		postMixInProperties: function() {
			lang.mixin(this,{
				helpText: _("This module allows to manage print jobs of printers on your local machine."),
				headerText: _("Printer administration")
			});

			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._form = new SearchForm({
				region: 'nav',
				hideSubmitButton: true,
				widgets: [{
					name: 'key',
					type: ComboBox,
					label: _("Search for"),
					staticValues: [
					 	 { id: 'printer',		label: _("Printer name")},
					 	 { id: 'description',	label: _("Description")},
					 	 { id: 'location',		label: _("Location") }
					],
					sortStaticValues: false
				}, {
					name: 'pattern',
					type: SearchBox,
					inlineLabel: _('Search...'),
					value: '',
					onSearch: lang.hitch(this, function() {
						this._form.submit();
					})
				}],
				layout: [['key', 'pattern']],
				onSearch: lang.hitch(this, function(values) {
					this._enable_search_button(false);
					this._last_filter = values;			// save for easy refresh
					this._grid.filter(values);
				})
			});
			this._enable_search_button(false);
			this.addChild(this._form);

			var columns = [{
				name: 'server',
				label: _("Server")
			}, {
				name: 'printer',
				label: _("Printer")
			}, {
				name: 'status',
				label: _("Status"),
				// 'enabled'/'disabled' are kind of keywords, just as they're returned
				// from cups if invoked without locale (LANG=C).
				// Our wording for this is 'active'/'inactive'.
				formatter: lang.hitch(this,function(value) {
					switch(value)
					{
						case 'enabled': return _("active");
						case 'disabled': return _("inactive");
					}
					return _("unknown");
				})
			}, {
				name: 'quota',
				label: _("Quota"),
				formatter: lang.hitch(this,function(value) {
					if (value)		// only true or false?
					{
						return _("active");
					}
					return _("inactive");
				})
			}, {
				name: 'location',
				label: _("Location")
			}, {
				name: 'description',
				label: _("Description")
			}];

			var actions = [{
				name: 'open',
				label: _("View details"),
				isStandardAction: true,
				callback: lang.hitch(this,function(id, values) {
					// 2.4 uses the printer ID as key property, so we do that as well.
					this.openDetail(id[0]);
				})
			}, {
				name: 'activate',
				label: _("Activate"),
				isStandardAction: true,
				callback: lang.hitch(this, function(ids) {
					// no multi action for now, but who knows...
					for (var p in ids)
					{
						this.managePrinter(ids[p],'activate',
							lang.hitch(this, function(success,message) {
								this._manage_callback(success,message);
							})
						);
					}
				}),
				canExecute: lang.hitch(this, function(values) {
					return (values.status == 'disabled');
				})
			}, {
				name: 'deactivate',
				label: _("Deactivate"),
				isStandardAction: true,
				callback: lang.hitch(this, function(ids) {
					// no multi action for now, but who knows...
					for (var p in ids)
					{
						this.managePrinter(ids[p],'deactivate',
							lang.hitch(this, function(success,message) {
								this._manage_callback(success,message);
							})
						);
					}
				}),
				canExecute: lang.hitch(this, function(values) {
					return (values.status == 'enabled');
				})
			}, {
				name: 'editquota',
				label: _("Edit quota"),
				isStandardAction: false,
				callback: lang.hitch(this,function(ids) {
					this.editQuota(ids[0]);
				}),
				canExecute: lang.hitch(this,function(values) {
					return (values.quota);	// true or false
				})
			}, {
				name: 'refresh',
				label: _("Refresh printer list"),
				isContextAction: false,
				callback: lang.hitch(this, function() {
					this._refresh_view();
				})
			}];

			this._grid = new Grid({
				columns: columns,
				region: 'main',
				actions: actions,
				defaultAction: 'open',
				moduleStore: store('printer','printers'),
				// fill grid on first open
				query: {key:'printer', pattern: '*'},
				onFilterDone: lang.hitch(this, function(success) {
					this._enable_search_button(true);
				})
			});
			this.addChild(this._grid);
		},

		_enable_search_button: function(on) {
			this._form._buttons.submit.setDisabled(! on);
		},

		// refreshes the grid. can be called manually (pressing the refresh button)
		// or automatically (as response to the managePrinter() result)
		_refresh_view: function() {
			this._grid.filter(this._last_filter);
		},

		// will be called with the result of 'managePrinter'
		_manage_callback: function(success,message) {
			if (success) {
				this._refresh_view();
			} else {
				dialog.alert(message);
			}
		},

		// when we come back from any kind of detail view that
		// could have invoked some actions... refresh our view.
		onShow: function() {
			this._refresh_view();
		},

		// DetailPage gives results back here.
		setArgs: function(args) {
		},

		// main module listens here, to carry out direct printer
		// management functions.
		managePrinter: function(printer,func,callback) {
		},

		// main module listens here, to switch to the detail view.
		// args can propagate the id of the printer to show
		openDetail: function(args) {
		},

		// main module listens here to open the quota page.
		editQuota: function(args) {
		}
	});
});
