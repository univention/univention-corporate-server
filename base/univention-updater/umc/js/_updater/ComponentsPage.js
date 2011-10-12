/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._updater.ComponentsPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");

dojo.require("umc.modules._updater.Page");
dojo.require("umc.modules._updater.Grid");

dojo.declare("umc.modules._updater.ComponentsPage", umc.modules._updater.Page, {
	
	i18nClass: 		'umc.modules.updater',
	_query:			{ table: 'components' },
	
    postMixInProperties: function() {
        this.inherited(arguments);

        dojo.mixin(this, {
	    	title:			this._("Components"),
	        headerText:		this._("Additional components"),
	        helpText:		this._("On this page, you find all additional components defined for this system. You can enable/disable/edit/delete them, and you can add new ones here.")
        });
        this.moduleStore.idProperty = 'name';
    },

    buildRendering: function() {
		
    	this.inherited(arguments);
    	
		var actions = 
        [
         	{
                name:				'add',
                label:				this._( 'Add' ),
                description:		this._( 'Add a new component definition' ),
                iconClass:			'dijitIconNewTask',
                isContextAction:	false,
                isStandardAction:	true,
                callback: dojo.hitch(this, function() {
                	this.showDetail('');
                })
            },
         	{
                name:				'refresh',
                label:				this._( 'Refresh' ),
                description:		this._( 'Refresh display to see current values' ),
                iconClass:			'dijitIconSearch',
                isContextAction:	false,
                isStandardAction:	true,
                callback: dojo.hitch(this, function() {
                	this.refresh(true);
                })
            },
            {
            	name:				'onoff',
            	description:		this._("Enable/disable this component"),
            	label: dojo.hitch(this, function(values) {
            		if (typeof(values) == 'undefined')		// renders the header
            		{
            			return this._("On/Off");
            		}
            		else
            		{
	            		return (values['enabled'] ? this._("Disable") : this._("Enable") );
            		}
            	}),
//            	iconClass: dojo.hitch(this, function(values) {
//            		if (typeof(values) == 'undefined')
//            		{
//            			return "";
//            		}
//            		return (values['enabled'] ? 'dijitIconFolderClosed' : 'dijitIconFolderOpen');
//            	}),
            	isStandardAction:	false,
            	isMultiAction:		false,
            	isContextAction:	true,
                callback: dojo.hitch(this, function(id) {
                	// Multi action doesn't make sense here since the real action depends
                	// row-wise from the value of the 'enabled' property.
                	if (dojo.isArray(id)) { id = id[0]; }
            		try
            		{
                		var rowIndex = this._grid._grid.getItemIndex({name: id});
                		if (rowIndex != -1)
                		{
	                		var values = this._grid.getRowValues(rowIndex);
	               			this._enable_component(id,! values['enabled']);
                		}
            		}
            		catch(error)
            		{
            			console.error("On/Off id = '" + id + "' ERROR: " + error.message);
               		}
                })
            },
            {
            	name:				'install',
            	label:				this._("Install"),
            	description:		this._("Try to install the component's default package(s)"),
//            	iconClass:			'dijitIconPackage',
            	isStandardAction:	true,
            	isMultiAction:		false,
            	isContextAction:	true,
            	canExecute: dojo.hitch(this, function(values) {
            		// Knowledge is in the Python module!
            		return (values['installable'] === true);
            	}),
            	callback: dojo.hitch(this, function(id) {
            		if (dojo.isArray(id))
            		{
            			id = id[0];
            		}
            		this.installComponent(id);
            	})
            },
            {
                name:				'edit',
                label:				this._( 'Edit' ),
                description:		this._( 'Edit the detail information about this component' ),
                iconClass:			'dijitIconEdit',
                isStandardAction:	true,
                isMultiAction:		false,
                callback: dojo.hitch(this, function(ids) {
                	if (dojo.isArray(ids))
                	{
                		// Should never happen in our context, but if it does -> take the first element.
                		this.showDetail(ids[0]);
                	}
                	else
                	{
                		this.showDetail(ids);
                	}
                })
            },
            {
                name:				'delete',
                label:				this._( 'Delete' ),
                description:		this._( 'Delete the selected component definition' ),
                iconClass:			'dijitIconDelete',
                isStandardAction:	true,
                // FIXME Should we really allow multiple deletions here?
                isMultiAction:		true,
                callback: dojo.hitch(this, function(ids) {
                	this._delete_components(ids);
                })
            }
        ];
    	
    	var columns = 
		[
		 	{
				name:			'name',
				label:			this._("Component Name"),
				editable:		false,
				width:			'40%',
				formatter:
					// Convenience function: if description is set, we include it (in brackets).
					dojo.hitch(this, function(key, rowIndex) {
						var grid = this._grid;
	                	var tmp = grid.getRowValues(rowIndex);
	                    if ((typeof(tmp['description']) == 'string') && (tmp['description'] != ''))
	                    {
	                    	return dojo.replace('{name} ({description})',tmp);
	                    }
						return key;
					})
		 	},		        		 	
		 	// trying to translate the result of get_current_component_status(component). This
		 	// summarizes all status variables.
		 	// *** NOTE *** The knowledge about internal logic is kept in the Python module,
		 	//				especially the 'installed' state that is combined from different
		 	//				variables.
		 	{
		 		name:			'status',
		 		label:			this._("Status"),
		 		editable:		false,
		 		// If iconField is set -> my formatter is not called, so the raw status
		 		// keys would show up... but nevertheless, the code is already prepared
		 		// iconField:		'icon',
		 		formatter:
		 			dojo.hitch(this, function(key, rowIndex) {
		 				switch(key)
		 				{
		 					case 'disabled':			return this._("Disabled");
		 					case 'available':			return this._("Available");
		 					case 'not_found':			return this._("Not found");
		 					case 'permission_denied':	return this._("Permission denied");
		 					case 'unknown':				return this._("Unknown");
		 					case 'installed':			return this._("Installed");
		 				}
		 				return key;
		 			})
		 	}
		];
    	
    	this._grid = new umc.modules._updater.Grid({
    		region:			'center',
    		query:			this._query,
			moduleStore:	this.moduleStore,
			actions:		actions,
			columns:		columns,
			polling:	{
				interval:	5000,
				query:		'updater/components/serial',
				callback:	dojo.hitch(this, function() {
					this.refresh(true);
				})
			}
    	});
    	
    	this.addChild(this._grid);
	},
	
	// switch over to the detail edit form, along with this id (empty if 'add')
	showDetail: function(id) {
		// we don't have to do something here: our parent Module is connected to this event.
	},
	
	// overload our stub from umc.modules._updater.Page
	refreshPage: function() {
		this.refresh(false);
	},
	
	// refresh the grid.
	refresh: function(standby) {
		if (standby)
		{
			// show the user that we're refreshing.
			this._grid.filter(this._query);
		}
		else
		{
			// silently, without standby. onload hooks are called though.
			this._grid._grid.filter(this._query);
		}
	},
	
	// action callback for the 'enable' and 'disable' actions. Can now handle
	// arrays (well-prepared for isMultiAction). This is the only point where
	// the grid itself has to save something.
	_enable_component: function(name,enabled) {
		var args = [];
		if (dojo.isArray(name))
		{
			for (var n in name)
			{
				args.push({
					object:	{
						name: name[n],
						enabled: enabled
					},
					options: null
				});
			}
		}
		else
		{
			args.push({
				object: {
					name: name,
					enabled: enabled
				},
				options: null
			});
		}
		// the grid calls multiActions even if nothing is selected?
		if (args.length)
		{
			this.standby(true);
			this.moduleStore.umcpCommand('updater/components/put',args).then(
				dojo.hitch(this, function(data) {
					this.standby(false);
					this.refresh();				// refresh own grid
					this.dataChanged();			// propagate changes to listeners
				}),
				dojo.hitch(this, function(data) {
					this.standby(false);
				})
			);
		}
	},
	
	// removes a component
	_delete_components: function(ids) {

		var msg = dojo.replace(this._("Are you sure you want to delete the following components: [{ids}]"),{ids: ids});
		umc.dialog.confirm(msg,
		[
		 	// deleting a component: do we allow this without confirmation if the admin
		 	// has turned confirmations off? (for now, we do.)
		 	{
		 		label:		this._('Cancel')
		 	},
		 	{
		 		label:		this._('Delete!'),
		 		'default':	true,
		 		callback:	dojo.hitch(this,function() {
		 			this.standby(true);
		 			this.moduleStore.umcpCommand('updater/components/del',ids).then(
		 					dojo.hitch(this, function(data) {
		 						this.standby(false);
		 						this.refresh();
		 						this.dataChanged();
		 					}),
		 					dojo.hitch(this, function(data) {
		 						this.standby(false);
		 					})
		 				);
		 		})
		 	}
		]);
	},
	
	// gives a means to restart polling after reauthentication
	startPolling: function() {
		this._grid.startPolling();
	},
	
	// Will be dojo.connect()ed from the main page
	installComponent: function(id) {
	}
	
});
	
