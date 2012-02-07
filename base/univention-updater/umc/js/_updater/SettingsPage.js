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

dojo.provide("umc.modules._updater.SettingsPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.store");

dojo.require("umc.modules._updater.Page");

dojo.declare("umc.modules._updater.SettingsPage", umc.modules._updater.Page, {
	
	i18nClass: 		'umc.modules.updater',
	
    postMixInProperties: function() {
        this.inherited(arguments);

        dojo.mixin(this, {
        	title:			this._("Settings"),
        	headerText:		this._("Settings for online updates"),
            helpText:		this._("This page lets you modify essential settings that affect where your system looks for updates, and which of them it will consider."),
        	footerButtons:
    		[
    	    	{
    	            name:		'reset',
    	            label:		this._( 'Reset' ),
    	            onClick: dojo.hitch(this, function() {
    	                this._form.load('server');		// ID doesn't matter here but must be nonempty
    	            })
    	    	},
    	    	{
    	            name:		'submit',
    	            'default':	true,
    	            label:		this._("Apply changes"),
    	            onClick: dojo.hitch(this, function() {
    	            	this.standby(true);
    	                this._form.save();
    	            })
    	    	}
    		]
        });
    },

    buildRendering: function() {
		
    	this.inherited(arguments);

    	var widgets =
		[
			{
				type:			'TextBox',
				name:			'server',
				label:			this._("Repository server")
			},
			{
				type:			'TextBox',
				name:			'prefix',
				label:			this._("Repository prefix")
			},
			{
				type:			'CheckBox',
				name:			'maintained',
				label:			this._("Use maintained repositories")
			},
			{
				type:			'CheckBox',
				name:			'unmaintained',
				label:			this._("Use unmaintained repositories")
			}
		];

    	var layout = 
    	[
    	 	{
    	 		label:		this._("Update-related settings"),
    	 		layout:
    	 		[
		    		['server','prefix'],
		    		['maintained','unmaintained']
		    	]
    	 	}
    	];

    	this._form = new umc.modules._updater.Form({
    		widgets:		widgets,
    		layout:			layout,
    		//buttons:		buttons,
    		moduleStore:	umc.store.getModuleStore('server','updater/settings'),
			scrollable: true,
    		onSaved: dojo.hitch(this, function(success,data) {
    			this.standby(false);
    			if (success)		// this is only Python module result, not data validation result!
    			{
    				var result = data;
    				if (dojo.isArray(data))
    				{
    					result = data[0];
    				}
    				if (result['status'])
    				{
    					if (result['message'])
    					{
    						// result['status'] is kind of error code:
    						//	1 ... invalid field input
    						//	2 ... error setting registry variable
    						//	3 ... error commiting UCR
    						//	4 ... any kind of 'repo not found' conditions
    						//	5 ... repo not found, but encountered without commit
    						var txt = this._("An unknown error with code %d occured.",result['status']);
    						var title = 'Error';
    						switch(result['status'])
    						{
    							case 1: txt = this._("Please correct the corresponding input fields:");
    									title = this._("Invalid data");
    									break;
    							case 2:
    							case 3:	txt = this._("The data you entered could not be saved correctly:");
    									title = this._("Error saving data");
    									break;
    							case 4: txt = this._("Using the data you entered, no valid repository could be found.<br/>Since this may be a temporary server problem as well, your data was saved though.<br/>The problem was:");
    									title = this._("Updater warning");
    									break;
    							case 5: txt = this._("With the current (unchanged) settings, the following problem was encountered:");
										title = this._("Updater warning");
										break;
    						}
    						
    						var message = dojo.replace('<p>{txt}</p><p><b>{msg}</b></p>',{txt:txt,msg:result['message']});
    						
    						// While our module is open, the first created dialog would retain its title over
    						// its whole lifetime... But we want the title to be changed on every invocation,
    						// so there's no chance but to reap a current instance of the dialog.

    						umc.dialog._alertDialog = null;
    						umc.dialog.alert(message,title);
    					}
    					// No, this is done in the Form class itself.
    					// this._form.applyErrorIndicators(result['object']);
    				}
    				else
    				{
    					this.dataChanged();
    					// nothing!
    					//this.closeDetail();
    				}
    			}
    		})
    	});
    	this.addChild(this._form);
    	
    	dojo.connect(this._form,'onSubmit',dojo.hitch(this,function() {
	    	this.standby(true);
	        this._form.save(this._save_options);
		}));
    	    	
    	this._form.load('server');		// ID doesn't matter here, but must be nonempty
    },
    
    // Returns defaults for a new component definition. 
    getComponentDefaults: function() {
    
    	return ({
    		// Behaviour: enable the component in first place
			enabled:			true,
			// Empty fields
			name:				'',		// TOOD wouldn't it be nice to get this field focused on NEW?
			description:		'',
			prefix:				'',
			username:			'',
			password:			'',
			defaultpackages:	'',
			server:				'',
			// TODO These have to be copied from the current settings
			maintained:			true,
			unmaintained:		false
    	});
    },
    
    // Let's fetch the current values again directly before we show the form.
    onShow: function() {

    	this._form.load('server');		// ID doesn't matter here but must be nonempty
    }
    
});
