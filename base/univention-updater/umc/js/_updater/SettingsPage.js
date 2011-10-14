/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._updater.SettingsPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");

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
    	                this._form.load('dummy');		// ID doesn't matter here but must be nonempty
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
			},
		];

    	var layout = 
    	[
    	 	{
    	 		label:		this._("Update-related settings"),
    	 		layout:
    	 		[
		    		['server','prefix'],
		    		['maintained','unmaintained'],
		    	]
    	 	}
    	];

    	this._form = new umc.modules._updater.Form({
    		widgets:		widgets,
    		layout:			layout,
    		//buttons:		buttons,
    		moduleStore:	this.moduleStore,
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
    						// not yet clear where I'll display this
    						umc.dialog.alert(result['message']);
    					}
    					this._form.applyErrorIndicators(result['object']);
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
    	
    	this._form.load('dummy');		// ID doesn't matter here, but must be nonempty
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
    }
    
});
