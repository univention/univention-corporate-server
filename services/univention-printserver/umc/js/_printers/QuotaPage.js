/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._printers.QuotaPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.store");
dojo.require("umc.tools");

dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");

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
				callback: dojo.hitch(this, function(ids) {
					// TODO do something useful here
				})
			},
			{
				name:				'edit',
				label:				this._("Edit"),
				callback: dojo.hitch(this, function(ids) {
					// TODO do something useful here
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
    
	// Calling page passes args here. Arg is here the printer ID.
	setArgs: function(args) {
		
		this._printer_id = args;
		this._refresh_view();
	},
	
	onHide: function() {
		// force clean state
		this._head.set('content','');		// clear header text
		this._grid.filter();				// clear grid data
	},
	
	// called when the page is shown, but can equally be called
	// on a manual or automatic refresh.
	_refresh_view: function() {
		
		this._head.set('content',dojo.replace(this._("Quota entries for printer <b>{printer}</b>"),{printer:this._printer_id}));
		
		// read current quota list
		this._grid.filter({printer:this._printer_id});
	},
	
    // main module listens here to return to the detail page
    closeQuota: function(args) {
    }
});
