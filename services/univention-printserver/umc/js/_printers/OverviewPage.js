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

dojo.provide("umc.modules._printers.OverviewPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.tools");
dojo.require("umc.store");

dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.ExpandingTitlePane");

dojo.declare("umc.modules._printers.OverviewPage",
[
	umc.widgets.Page,
	umc.i18n.Mixin
], {

	i18nClass:              'umc.modules.printers',
	_last_filter:			{ key: 'printer', pattern: '*' },
	
	postMixInProperties: function() {
		
		dojo.mixin(this,{
            helpText:		this._("This module lets you manage the printers defined on your machine"),
            headerText:		this._("Printer administration")
		});
		
		this.inherited(arguments);
	},

    buildRendering: function() {

        this.inherited(arguments);
        
        var pane = new umc.widgets.ExpandingTitlePane({
        	title:				this._("Printer administration")
        });
        this.addChild(pane);
        
        this._form = new umc.widgets.SearchForm({
        	region:					'top',
        	widgets: [
	          {
	        	  name:				'key',
	        	  type:				'ComboBox',
	        	  label:			this._("Search key"),
	        	  staticValues: [
					 { id: 'printer',		label: this._("Printer name")},
					 { id: 'description',	label: this._("Description")},
					 { id: 'location',		label: this._("Location") }
	        	  ],
	        	  sortStaticValues:	false
	          },
	          {
	        	  name:				'pattern',
	        	  type:				'TextBox',
	        	  label:			this._("Pattern"),
	        	  value:			'*'
	          }
        	],
        	layout: [
        	   [ 'key', 'pattern', 'submit' ]
        	],
        	onSearch: dojo.hitch(this, function(values) {
        		this._enable_search_button(false);
        		this._last_filter = values;			// save for easy refresh
        		this._grid.filter(values);
        	})
        });        
        this._enable_search_button(false);
        pane.addChild(this._form);
        
        var columns =  [
			{
				name:		'server',
				label:		this._("Server")
			},
			{
				name:		'printer',
				label:		this._("Printer")
			},
			{
				name:		'status',
				label:		this._("Status"),
				// 'enabled'/'disabled' are kind of keywords, just as they're returned
				// from cups if invoked without locale (LANG=C).
				// Our wording for this is 'active'/'inactive'.
				formatter:	dojo.hitch(this,function(value) {
					switch(value)
					{
						case 'enabled': 	return this._("active");
						case 'disabled':	return this._("inactive");
					}
					return this._("unknown");
				})
			},
			{
				name:		'quota',
				label:		this._("Quota"),
				formatter:	dojo.hitch(this,function(value) {
					if (value)		// only true or false?
					{
						return this._("active");
					}
					return this._("inactive");
				})
			},
			{
				name:		'location',
				label:		this._("Location")
			},
			{
				name:		'description',
				label:		this._("Description")
			}
		];
        
        var actions = [
			{
				name:		'open',
				label:		this._("View details"),
				callback:	dojo.hitch(this,function(id,values) {
					// 2.4 uses the printer ID as key property, so we do that as well.
					this.openDetail(id[0]);
				})
			},
			{
				name:		'activate',
				label:		this._("Activate"),
				callback:	dojo.hitch(this, function(ids) {
					// no multi action for now, but who knows...
					for (var p in ids)
					{
						this.managePrinter(ids[p],'activate',
							dojo.hitch(this, function(success,message) {
								this._manage_callback(success,message);
							})
						);
					}
				}),
				canExecute: dojo.hitch(this, function(values) {
					return (values['status'] == 'disabled');
				})
			},
			{
				name:		'deactivate',
				label:		this._("Deactivate"),
				callback:	dojo.hitch(this, function(ids) {
					// no multi action for now, but who knows...
					for (var p in ids)
					{
						this.managePrinter(ids[p],'deactivate',
							dojo.hitch(this, function(success,message) {
								this._manage_callback(success,message);
							})
						);
					}
				}),
				canExecute: dojo.hitch(this, function(values) {
					return (values['status'] == 'enabled');
				})
			},
			{
				name:				'editquota',
				label:				this._("Edit quota"),
				isStandardAction:	false,
				callback:	dojo.hitch(this,function(ids) {
					this.editQuota(ids[0]);
				}),
				canExecute:	dojo.hitch(this,function(values) {
					return (values['quota']);	// true or false
				})
			},
			{
				name:				'refresh',
				label:				this._("Refresh printer list"),
				isContextAction:	false,
				callback: dojo.hitch(this, function() {
					this._refresh_view();
				})
			}
	    ];

        this._grid = new umc.widgets.Grid({
        	columns:			columns,
        	region:				'center',
        	actions:			actions,
        	defaultAction:		'open',
            moduleStore:		umc.store.getModuleStore('printer','printers'),
            // fill grid on first open
            query:				{key:'printer', pattern: '*'},
            onFilterDone: dojo.hitch(this, function(success) {
        		this._enable_search_button(true);
            })
        });
        pane.addChild(this._grid);
        
        
    },
    
    _enable_search_button: function(on) {
    	this._form._buttons['submit'].setDisabled(! on);
    },
    
    // refreshes the grid. can be called manually (pressing the refresh button)
    // or automatically (as response to the managePrinter() result)
    _refresh_view: function() {
		this._grid.filter(this._last_filter);
    },
    
    // will be called with the result of 'managePrinter'
    _manage_callback: function(success,message) {
    	
    	if (success)
    	{
    		this._refresh_view();
    	}
    	else
    	{
    		umc.dialog.alert(message);
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
