/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._updater.DetailsPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");

dojo.require("umc.modules._updater.Page");
dojo.require("umc.modules._updater.Form");

dojo.declare("umc.modules._updater.DetailsPage", umc.modules._updater.Page, {
	
	i18nClass: 		'umc.modules.updater',
	
    postMixInProperties: function() {
        this.inherited(arguments);

        dojo.mixin(this, {
			title:			this._("Components"),
	    	footerButtons:
    		[
            	{
    	            name:		'cancel',
    	            'default':	false,
    	            label:		this._("back to overview"),
    	            onClick: dojo.hitch(this, function() {
    	            	try
    	            	{
    	            		this.closeDetail();
    	            	}
    	            	catch(error)
    	            	{
    	            		console.error("onCancel: " + error.message);
    	            	}
    	            })
            	},
            	{
    	            name:		'submit',
    	            'default':	true,
    	            label:		this._("Apply changes"),
    	            onClick: dojo.hitch(this, function() {
    	            	this.standby(true);
                        this._form.save(this._save_options);
    	            })
            	}
    		]		        	
        });
    },

    buildRendering: function() {
		
    	this.inherited(arguments);
    	
    	var widgets = [
    		{
    			type:			'CheckBox',
    			name:			'enabled',
    			label:			this._("Enable this component")
    		},
	    	{
	    		type:			'TextBox',
	    		name:			'name',
	    		label:			this._("Component Name")
	    	},
	    	{
	    		type:			'TextBox',
	    		name:			'description',
	    		label:			this._("Description")
	    	},
	    	{
	    		type:			'TextBox',
	    		name:			'server',
	    		label:			this._("Repository Server")
	    	},
	    	{
	    		type:			'TextBox',
	    		name:			'prefix',
	    		label:			this._("Repository Prefix")
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
	    	{
	    		type:			'TextBox',
	    		name:			'username',
	    		label:			this._("Username")
	    	},
	    	{
	    		type:			'TextBox',
	    		name:			'password',
	    		label:			this._("Password")
	    	}
    	];
    
    	var layout = 
    	[
    	 	{
    	 		label:		this._("Basic settings"),
    	 		layout:
    	 		[
		    		['enabled'],
		    		['name','description'],
		    		['server','prefix']
		    	]
    	 	},
    	 	{
    	 		label:		this._("Advanced settings"),
    	 		layout:
	 			[
		    		['maintained','unmaintained'],
		    		['username','password'],
		    		['defaultpackages']
		    	]
    	 	}
    	];

    	this._form = new umc.modules._updater.Form({
    		widgets:		widgets,
    		layout:			layout,
    		//buttons:		buttons,
    		moduleStore:	this.moduleStore
    	});
    	this.addChild(this._form);
    	
    	dojo.connect(this._form,'onSaved',dojo.hitch(this, function(success,data) {
    		this.standby(false);
    		try
    		{
    			// really successful? close the form.
	    		if ((success) && (data['status'] == 0))
	    		{
	    			this.dataChanged();
	    			this.closeDetail();
	    		}
    		}
    		catch(error)
    		{
    			console.error("DetailsPage.onSaved: " + error.message);
    		}
    	}));
	},
	
	// Entry point for opening the edit page. API now changed, so the detail knowledge
	// is not in this page:
	//
	//	isnew ..... true -> we're adding, false -> we're editing
	//	data ...... if EDIT: the id of the record to load
	//				if ADD: a dict of default values
	startEdit: function(isnew,data) {
		
		if (isnew)
		{
			this.set('headerText',this._("Add a new component"));
			this.set('helpText',this._("Please enter the details for the new component."));
			
			this._form.setFormValues(data);

			// Component name editable and focused?
			var nam = this._form.getWidget('name');
			if (nam)
			{
				nam.setDisabled(false);
				nam.focus();
			}

			// this is passed to the 'save' function, from there to the 'options'
			// dictionary for the 'put' method, and it enables the 'put' method
			// to know that an already existing component with the same name should
			// not be overwritten (instead, return an error message)
			this._save_options = {
				failIfExists: true
			};
		}
		else
		{
			this.set('headerText',dojo.replace(this._("Edit component details [{component}]"),{component:data}));
			this.set('helpText',this._("You're editing the details of the component definition."));
			
			this._form.load(data);
			
			// If we're in EDIT mode: don't allow changes to the component name.
			this._form.getWidget('name').setDisabled(true);
			
			// let's suppose the SERVER field is a good focus start
			this._form.getWidget('server').focus();
			
			this._save_options = null;		// don't need options here
		}
	},
	
	// return to grid view
	closeDetail: function() {
	}
	

});
