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

dojo.provide("umc.modules._printers.QuotaPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.store");
dojo.require("umc.tools");

dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");

dojo.require("umc.modules._printers.QuotaDialog");

dojo.declare("umc.modules._printers.QuotaPage",
[
	umc.widgets.Page,
	umc.i18n.Mixin
], {

	i18nClass:              'umc.modules.printers',
	
	postMixInProperties: function() {
		
		dojo.mixin(this,{
			helpText:		this._("Current quota records for printer"),
			headerText:		this._("Printer quota")
		});
		
		this.inherited(arguments);
	},

    buildRendering: function() {

        this.inherited(arguments);

        var pane = new umc.widgets.ExpandingTitlePane({
        	title:				this._("Printer quota")
        });
        this.addChild(pane);
        
        this._head = new umc.widgets.Text({
        	region:			'top',
        	content:		'',
        	style:			'padding-bottom:1em;font-size:115%;'
        });
        pane.addChild(this._head);
        
        var columns = [
			{
				name:		'user',
				label:		this._("User")
			},
			{
				name:		'used',
				label:		this._("Pages used")
			},
			{
				name:		'soft',
				label:		this._("Soft limit")
			},
			{
				name:		'hard',
				label:		this._("Hard limit")
			},
			{
				name:		'total',
				label:		this._("Lifetime page counter")
			}
        ];
        
        var actions = [
			{
				name:				'clear',
				label:				this._("Reset user quota"),
				isMultiAction:		true,
				callback: dojo.hitch(this, function(ids,values) {
					this._reset_quota_entries(values);
				})
			},
			{
				name:				'edit',
				label:				this._("Edit"),
				callback: dojo.hitch(this, function(ids,values) {
					// always use the first value since multiselect doesn't make sense.
					this._edit_quota_entry(values[0]);
				})
			},
			{
				name:				'back',
				label:				this._("Back"),
				isContextAction:	false,
				callback: dojo.hitch(this, function() {
					this.closeQuota();
				})
			},
			{
				name:				'refresh',
				label:				this._("Refresh"),
				isContextAction:	false,
				callback: dojo.hitch(this, function() {
					this._refresh_view();
				})
			},
			{
				name:				'add',
				label:				this._("Add new record"),
				isContextAction:	false,
				callback: dojo.hitch(this, function(ids) {
					this._add_quota_entry();
				})
			}
        ];
        
        this._grid = new umc.widgets.Grid({
        	region:			'center',
        	columns:		columns,
        	actions:		actions,
        	moduleStore:	umc.store.getModuleStore('user','printers/quota')
        });
        pane.addChild(this._grid);
        
	},
	
	startup: function() {
		
		this.inherited(arguments);
		
        // fetch the userlist
		umc.tools.umcpCommand('printers/users/query').then(
			dojo.hitch(this, function(data) {
				if (data.result.length)
				{
					// we keep this list unchanged; it will be fetched only once.
					// on open of 'add quota' dialog, we pass a userlist that
					// is cleaned up from users already having a quota entry.
					this._userlist = data.result;
				}
			}),
			dojo.hitch(this, function(data) {
				umc.dialog.alert('Error fetching userlist: ' + data.message);
			})
		);
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
		
		this._head.set('content',dojo.replace(this._("Quota entries for printer <b>{printer}</b>"),{printer:this._printer_id}));
		
		// read current quota list
		this._grid.filter({printer:this._printer_id});

		// on first open: create the child dialog where we can edit one quota entry.
		if (! this._dialog)
		{
			this._dialog = new umc.modules._printers.QuotaDialog();

			// listen to the events of the dialog
	        dojo.connect(this._dialog,'onSubmit',dojo.hitch(this, function(values) {
	        	this._set_quota_entry(values);
	        }));
//	        dojo.connect(this._dialog,'onCancel',dojo.hitch(this, function() {
//	        	// nothing to do here.
//	        }));

		}
		
	},
	
	// called from different places: the function that sets
	// a quota entry. When called with soft=0 and hard=0 this
	// would effectively forbid the user from printing...
	_set_quota_entry: function(values) {
    	umc.tools.umcpCommand('printers/quota/set',values).then(
    		dojo.hitch(this,function(data) {
    			if (data.result)
    			{
    				// an error message from the edpykota tool
    				umc.dialog.alert(data.result);
    			}
    			else
    			{
    				// success -> refresh view.
    				this._refresh_view();
    			}
    		}),
    		dojo.hitch(this,function(data) {
    			// error message from framework
    			umc.dialog.alert(data.message);
    		})
		);
	},
	
	// prepares everything to add a new quota entry.
	_add_quota_entry: function() {
		this._dialog.setValues({
			printer: 		this._printer_id,
			soft:			null,
			hard:			null,
			users:			this._cleaned_userlist(),
			title:			this._("Add quota entry")
		});
		this._dialog.show();
	},
	
	// prepares the edit dialog and shows it.
	// values is here a tuple of fields; this is always a single action.
	_edit_quota_entry: function(values) {

		try
		{
			var val = {
				printer:	this._printer_id,
				title:		this._("Edit quota entry")
			};
			this._dialog.setValues(dojo.mixin(val,values));
			this._dialog.show();
		}
		catch(ex)
		{
			console.error('edit_quota_entry(): ' + ex.message);
		}
	},
	
	// resets the 'used' counter on a list of users.
	// values is the array of field tuples of those users.
	_reset_quota_entries: function(values) {
		
		// if nothing is selected... why does the grid call the callback?
		if (values.length == 0)
		{
			return;
		}
		
		// ** NOTE ** we transfer the user names as an array since
		//			we can't know if some of them contain spaces or
		//			any other separator chars.
		var users = [];
		for (var u in values)
		{
			users.push(values[u]['user']);
		}

		umc.tools.umcpCommand('printers/quota/reset',{
			printer:			this._printer_id,
			users:				users
		}).then(
    		dojo.hitch(this,function(data) {
    			if (data.result)
    			{
    				// an error message from the edpykota tool
    				umc.dialog.alert(data.result);
    			}
    			else
    			{
    				// success -> refresh view.
    				this._refresh_view();
    			}
    		}),
    		dojo.hitch(this,function(data) {
    			// error message from framework
    			umc.dialog.alert(data.message);
    		})
		);
	},

	// prepares the list of users eligible for adding a quota entry:
	// this is the list of all users minus those that already have
	// a quota entry for this printer.
	//
	// Will be called only directly before a 'add quota entry' dialog
	// will be shown.
	_cleaned_userlist: function() {
		
		var result = [];
		var src = this._userlist;
		
		var usr = {};	// not an array: i want to to check for containedness!
		var items = this._grid.getAllItems();
		for (var i in items)
		{
			var u = items[i]['user'];
			usr[u] = u;
		}
		
		for (var s in src)
		{
			var sitem = src[s];
			
			// take this source item only if it is not contained
			// in the 'usr' dict.
			if (typeof(usr[sitem]) == 'undefined')
			{
				result.push(sitem);
			}
		}
		
		return result;
	},
	
    // main module listens here to return to the detail page
    closeQuota: function(args) {
    }
});
