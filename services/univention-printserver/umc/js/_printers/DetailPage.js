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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._printers.DetailPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.store");
dojo.require("umc.tools");

dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");

dojo.declare("umc.modules._printers.DetailPage",
[
	umc.widgets.Page,
	umc.i18n.Mixin
], {

	i18nClass:              'umc.modules.printers',
	_printer_id:			'',
	
	postMixInProperties: function() {
		
		dojo.mixin(this,{
			helpText:		this._("You see the details of this printer and its print jobs. You can activate/deactivate the printer, edit its quota definitions if quota is enabled, and cancel print jobs."),
			headerText:		this._("Printer details")
		});
		
		this.inherited(arguments);
	},

    buildRendering: function() {

        this.inherited(arguments);

        var pane = new umc.widgets.ExpandingTitlePane({
        	title:				this._("Printer details")
        });
        this.addChild(pane);
        
        var f_widgets = [
			{
				name:				'message',
				type:				'Text',
				content:			'<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;',
				style:				'padding-bottom:.5em;'		// force bottom distance to the buttons
			}
        ];
        
        var f_layout = [
	        [ 'message' ],
	        [ 'activate', 'deactivate', 'editquota', 'submit' ]
        ];
        
        var f_buttons = [
			{
				name:		'activate',
				label:		this._("Activate"),
				title:		this._("Activate this printer"),
				onClick:	dojo.hitch(this, function() {
					this.managePrinter(this._printer_id,'activate',
						dojo.hitch(this, function(success,message) {
							this._manage_callback(success,message);
						})
					);
				})
			},
			{
				name:		'deactivate',
				label:		this._("Deactivate"),
				title:		this._("Deactivate this printer"),
				onClick:	dojo.hitch(this, function() {
					this.managePrinter(this._printer_id,'deactivate',
						dojo.hitch(this, function(success,message) {
							this._manage_callback(success,message);
						})
					);
				})
			},
			{
				name:		'editquota',
				label:		this._("Edit quota"),
				title:		this._("Edit quota related to this printer"),
				onClick:	dojo.hitch(this, function() {
					this.editQuota(this._printer_id);
				})
			},
			// only to stop the Form class from adding a hidden submit button into
			// an additional row, thus mangling my layout...
			{
				name:		'submit',
				label:		'nothing'
			}
		];
        
        // we make this a form so we can add buttons 
        this._head = new umc.widgets.Form({
        	region:			'top',
        	widgets:		f_widgets,
        	buttons:		f_buttons,
        	layout:			f_layout,
        	onSubmit:		function() {}		// don't want to have any kind of submit here!
        });
        pane.addChild(this._head);
        
        var columns = [
		   {
			   name:		'job',
			   label:		this._("Job")
		   },
		   {
			   name:		'owner',
			   label:		this._("Owner")
		   },
		   {
			   name:		'size',
			   label:		this._("Size")
		   },
		   {
			   name:		'date',
			   label:		this._("Submitted at")
		   }
        ];
        
        var actions = [
			{
				name:				'cancel',
				label:				this._("Cancel"),
				title:				this._("Cancel this job/these jobs"),
				isMultiAction:		true,
				isStandardAction:	true,
				callback: dojo.hitch(this, function(ids) {
					umc.tools.umcpCommand('printers/jobs/cancel',{jobs: ids, printer:this._printer_id}).then(
						dojo.hitch(this,function(data) {
							if (data.result)
							{
								umc.dialog.alert(data.result);
							}
							this._refresh_view();
						}),
						dojo.hitch(this,function(data) {
							umc.tools.alert(data.message);
							this._refresh_view();
						})
					);
				})
			},
			{
				name:				'back',
				label:				this._("Back to overview"),
				isContextAction:	false,
				callback: dojo.hitch(this, function() {
	        		this.closeDetail();
	        	})
			},
			{
				name:				'refresh',
				label:				this._("Refresh job list"),
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
        	moduleStore:	umc.store.getModuleStore('job','printers/jobs')
        });
        pane.addChild(this._grid);
                
	},
    
	// Overview page passes args here. Arg is here the printer ID.
	setArgs: function(args) {
		
		this._printer_id = args;				
		this._refresh_view();
	},
	
	// no matter where we came from: if the page is to be shown we
	// have to refresh all data elements.
	onShow: function() {
		this._refresh_view();
	},
	
	// called when the page is shown, but can equally be called
	// on a manual or automatic refresh.
	_refresh_view: function() {
		
		// if the function is called before setArgs has given us a valid printer name
		// then we should simply do nothing.
		if (! this._printer_id)
		{
			return;
		}
		
		umc.tools.umcpCommand('printers/get',{printer:this._printer_id}).then(
			dojo.hitch(this, function(data) {
				
				// Yes I know, I should have this done by the layout capabilities of
				// the Form class... but given the fact that this is only an informative
				// overview message I've decided to wrap it into a single 'Text' element,
				// containing a <p>..</p> and a <table>.
				var res = data.result;
				// styles
				var st_h = 'font-size:115%;text-decoration:underline;';	// header line
				var st_l = 'text-align:right;padding-left:1em;';		// left column
				var st_r = 'padding-left:.5em;';						// right column
				
				// status text must be translated in our official wording...
				var status = this._("unknown");
				switch(res['status'])
				{
					case 'enabled': status = this._("active"); break;
					case 'disabled':status = this._("inactive"); break;
				}
				
				var txt = "<p style='" + st_h + "'>" + dojo.replace(this._("Details for printer <b>{printer}</b>"),res) + '</p>';
				txt += "<table>\n";
				txt += "<tr><td style='" + st_l + "'>" + this._("Server")		+ ":</td><td style='" + st_r + "'>" + res['server']			+ "</td></tr>\n";
				txt += "<tr><td style='" + st_l + "'>" + this._("Status")		+ ":</td><td style='" + st_r + "'>" + status				+ "</td></tr>\n";
				// show this only if quota is enabled
				if (res['quota'])
				{
					txt += "<tr><td style='" + st_l + "'>" + this._("Quota")		+ ":</td><td style='" + st_r + "'>" + this._("active")		+ "</td></tr>\n";
				}
				txt += "<tr><td style='" + st_l + "'>" + this._("Location")		+ ":</td><td style='" + st_r + "'>" + res['location']		+ "</td></tr>\n";
				txt += "<tr><td style='" + st_l + "'>" + this._("Description")	+ ":</td><td style='" + st_r + "'>" + res['description']	+ "</td></tr>\n";
				txt += "</table>\n";
				
				this._head.getWidget('message').set('content',txt);
				
				// show/hide corresponding buttons
				
				this._show_button('activate',res['status'] == 'disabled');
				this._show_button('deactivate',res['status'] == 'enabled');
				this._show_button('editquota',res['quota']);
				this._show_button('submit',false);			// always invisible.
				
				this.layout();		// whenever you change a non-center region of a BorderLayout...
			}),
			dojo.hitch(this, function(data) {
				this._grid.filter();		// clears stale grid data
			})
		);
		
		// read job list
		this._grid.filter({printer:this._printer_id});
	},
	
	_show_button: function(button,on) {
		
		try
		{
			dojo.toggleClass(this._head._buttons[button].domNode,'dijitHidden',!on);
		}
		catch(ex)
		{
			console.error("show_button(" + button + "," + on + "): " + ex.message);
		}
	},
	
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
    
	// main module listens here, to carry out direct printer
	// management functions.
	managePrinter: function(printer,func,arg) {
	},
	
    // main module listens here to return to the overview.
	// args are passed back to the Overview page.
    closeDetail: function(args) {
		// force clean state
		this._head.getWidget('message').set('content','<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;');		// six empty lines
		this._grid.filter();
    },
    
    // main module listens here to open the quota page.
    editQuota: function(args) {
    }

    
});
