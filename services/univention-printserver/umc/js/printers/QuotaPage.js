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
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/when",
	"umc/dialog",
	"umc/store",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/Text",
	"umc/modules/printers/QuotaDialog",
	"umc/i18n!umc/modules/printers"
], function(declare, lang, when, dialog, store, tools, Page, Grid, Text, QuotaDialog, _) {

	return declare("umc.modules.printers.QuotaPage", [ Page ], {

		postMixInProperties: function() {
			lang.mixin(this,{
				helpText: _("Current quota records for printer"),
				headerText: _("Printer quota")
			});

			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._head = new Text({
				region: 'nav',
				content: '',
				style: 'padding-bottom:1em;font-size:115%;'
			});
			this.addChild(this._head);

			var columns = [{
				name: 'user',
				label: _("User")
			}, {
				name: 'used',
				label: _("Pages used")
			}, {
				name: 'soft',
				label: _("Soft limit")
			}, {
				name: 'hard',
				label: _("Hard limit")
			}, {
				name: 'total',
				label: _("Lifetime page counter")
			}];

			var actions = [{
				name: 'clear',
				label: _("Reset user quota"),
				isMultiAction: true,
				isStandardAction: true,
				callback: lang.hitch(this, function(ids,values) {
					this._reset_quota_entries(values);
				})
			}, {
				name: 'edit',
				label: _("Edit"),
				isStandardAction: true,
				callback: lang.hitch(this, function(ids,values) {
					// always use the first value since multiselect doesn't make sense.
					this._edit_quota_entry(values[0]);
				})
			}, {
				name: 'back',
				label: _("Back"),
				isContextAction: false,
				callback: lang.hitch(this, function() {
					this.closeQuota();
				})
			}, {
				name: 'refresh',
				label: _("Refresh"),
				isContextAction: false,
				callback: lang.hitch(this, function() {
					this._refresh_view();
				})
			}, {
				name: 'add',
				label: _("Add new record"),
				isContextAction: false,
				callback: lang.hitch(this, function(ids) {
					this._add_quota_entry();
				})
			}];

			this._grid = new Grid({
				region: 'main',
				columns: columns,
				actions: actions,
				moduleStore: store('user','printers/quota')
			});
			this.addChild(this._grid);
		},

		// Calling page passes args here. Arg is here the printer ID.
		setArgs: function(args) {
			this._printer_id = args;
			this._refresh_view();
		},

		onHide: function() {
			this.inherited(arguments);		// do I need this?

			// on next show(), the previous content
			// should not be visible anymore.
			this._head.set('content','');		// clear header text
			this._grid.filter();				// clear grid data
		},

		onShow: function() {
			this.inherited(arguments);		// do I need this?
		},

		// called when the page is shown, but can equally be called
		// on a manual or automatic refresh.
		_refresh_view: function() {

			this._head.set('content',lang.replace(_("Quota entries for printer <b>{printer}</b>"),{printer:this._printer_id}));

			// read current quota list
			this._grid.filter({printer:this._printer_id});

			// on first open: create the child dialog where we can edit one quota entry.
			if (!this._dialog) {
				this._dialog = new QuotaDialog();
				this.own(this._dialog);

				// listen to the events of the dialog
				this._dialog.on('Submit',lang.hitch(this, function(values) {
					this._set_quota_entry(values);
				}));
	//			this._dialog,on('Cancel',lang.hitch(this, function() {
	//				// nothing to do here.
	//			}));
			}

		},

		// called from different places: the function that sets
		// a quota entry. When called with soft=0 and hard=0 this
		// would effectively forbid the user from printing...
		_set_quota_entry: function(values) {
			tools.umcpCommand('printers/quota/set',values).then(
				lang.hitch(this,function(data) {
					if (data.result) {
						// an error message from the edpykota tool
						dialog.alert(data.result);
					} else {
						// success -> refresh view.
						this._refresh_view();
					}
				}),
				lang.hitch(this,function(data) {
					// error message from framework
					dialog.alert(data.message);
				})
			);
		},

		_getUserList: function() {
			if (!this._userList) {
				this._dialog.standby(true);
				return tools.umcpCommand('printers/users/query').then(
					lang.hitch(this, function(data) {
						this._dialog.standby(false);
						if (data.result.length)
						{
							// we keep this list unchanged; it will be fetched only once.
							// on open of 'add quota' dialog, we pass a userlist that
							// is cleaned up from users already having a quota entry.
							this._userList = data.result;
						}
						return data.result;
					}),
					lang.hitch(this, function(data) {
						this._dialog.standby(false);
						dialog.alert('Error fetching userlist: ' + data.message);
						return [];
					})
				);
			} else {
				return this._userList;
			}
		},

		// prepares everything to add a new quota entry.
		_add_quota_entry: function() {
			this._dialog.show();
			when(this._getUserList(), lang.hitch(this, function(userList) {
				this._dialog.setValues({
					printer: this._printer_id,
					soft: null,
					hard: null,
					users: this._cleaned_userlist(userList),
					title: _("Add quota entry")
				});
			}));
		},

		// prepares the edit dialog and shows it.
		// values is here a tuple of fields; this is always a single action.
		_edit_quota_entry: function(values) {

			try {
				var val = {
					printer: this._printer_id,
					title: _("Edit quota entry")
				};
				this._dialog.setValues(lang.mixin(val,values));
				this._dialog.show();
			} catch(ex) {
				console.error('edit_quota_entry(): ' + ex.message);
			}
		},

		// resets the 'used' counter on a list of users.
		// values is the array of field tuples of those users.
		_reset_quota_entries: function(values) {

			// if nothing is selected... why does the grid call the callback?
			if (values.length === 0) {
				return;
			}

			// ** NOTE ** we transfer the user names as an array since
			//			we can't know if some of them contain spaces or
			//			any other separator chars.
			var users = [];
			for (var u in values) {
				users.push(values[u]['user']);
			}

			tools.umcpCommand('printers/quota/reset',{
				printer: this._printer_id,
				users: users
			}).then(
				lang.hitch(this,function(data) {
					if (data.result) {
						// an error message from the edpykota tool
						dialog.alert(data.result);
					} else {
						// success -> refresh view.
						this._refresh_view();
					}
				}),
				lang.hitch(this,function(data) {
					// error message from framework
					dialog.alert(data.message);
				})
			);
		},

		// prepares the list of users eligible for adding a quota entry:
		// this is the list of all users minus those that already have
		// a quota entry for this printer.
		//
		// Will be called only directly before a 'add quota entry' dialog
		// will be shown.
		_cleaned_userlist: function(src) {

			var result = [];

			var usr = {};	// not an array: i want to to check for containedness!
			var items = this._grid.getAllItems();
			for (var i in items) {
				var u = items[i]['user'];
				usr[u] = u;
			}

			for (var s in src) {
				var sitem = src[s];

				// take this source item only if it is not contained
				// in the 'usr' dict.
				if (typeof(usr[sitem]) == 'undefined') {
					result.push(sitem);
				}
			}

			return result;
		},

		// main module listens here to return to the detail page
		closeQuota: function(args) {
		}
	});
});
