/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._updater.Form");

dojo.require("umc.widgets.Form");
dojo.require("umc.modules._updater._PollingMixin");

// Form with some useful additions:
//
//	-	add the capability of passing options to the 'put' method
//		of the underlying store
//	-	add the capability of passing back the results of a 'put'
//		call to the 'onSaved' event handlers.
//	-	add a method that takes a dict of 'field' -> 'text' mappings
//		that have to be turned into 'not valid' indicators at the
//		corresponding fields
//
dojo.declare("umc.modules._updater.Form", [
    umc.widgets.Form,
    umc.modules._updater._PollingMixin
	],
{
	// can be called in the onSave hook to set error flags and messages
	// for individual fields.
	// can be called without args to clear all error indicators
	//
	// as a side effect, sets the focus either to the first invalid field (if any)
	// or the first field at all.
	applyErrorIndicators: function(values) {
				
		var firstname = '';
		var errname = '';
		for (var field in this._widgets)
		{
			if (firstname == '')
			{
				firstname = field;
			}
			try
			{
				var widget = this._widgets[field];
				if (typeof(widget.setValid) == 'function')
				{
					if ((values) && (values[field]))
					{
						widget.setValid(false,values[field]);
						if (errname == '')
						{
							errname = field;
						}
					}
					else
					{
						widget.setValid(null);
					}
				}
			}
			catch(error)
			{
				console.error("applyErrorIndicators failed for field '" + field + "': " + error.message);
			}
		}
		// set the focus to the given field.
		var focus = errname;
		// not really useful: depending on NEW or EDIT we would
		// want a different field to be focused.
		//if (focus == '') { focus = firstname; }
		
		if (focus != '')
		{
			this._widgets[focus].focus();
// Our focus is not kept... we see it and then something takes control...
// Which event do we have to tack the focus() action on?
//			dojo.connect(this,'onWhichEvent?',dojo.hitch(this, function() {
//				this._widgets[focus].focus();
//			}));
		}
	},
	
	// can be deleted when the last built version contains this method.
    getWidget: function( /*String*/ widget_name) {
        // summary:
        //              Return a reference to the widget with the specified name.
        return this._widgets[widget_name]; // Widget|undefined
    },

    save: function(options) {
        // summary:
        //              Gather all form values and send them to the server via UMCP.
        //              For this, the field umcpSetCommand needs to be set.
                                        
        umc.tools.assert(this.moduleStore, 'In order to save form data to the server, the umc.widgets.Form.moduleStore needs to be set');
        
        // sending the data to the server
        var values = this.gatherFormValues();

    	// *** CHANGED *** propagate an 'options' dict to the 'put' call of the moduleStore
        // *** CHANGED *** propagate the result of the put operation to the 'onSaved' callback
        var deferred = this.moduleStore.put(values,options).then(dojo.hitch(this, function(result) {
            this.onSaved(true,result);
        }), dojo.hitch(this, function(result) {
            this.onSaved(false,result);
        }));
                
        return deferred;
    },
       
	buildRendering: function(args) {

		this.inherited(arguments);
		
		// It is important that error indicators get reset if data from
		// the store has been loaded, but also if setFormValues() is called
		// manually (e.g. to fill a 'new' form with initial values)
		dojo.connect(this,'setFormValues',dojo.hitch(this, function() {
			this.applyErrorIndicators({});
		}));

		dojo.connect(this,'onSaved',dojo.hitch(this, function(success,data) {
			
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
					this.applyErrorIndicators(result['object']);
				}
			}
		}));
	},

	// Two callbacks that are used by queries that want to propagate
	// their outcome to the main error handlers
	_query_error: function(subject,data) {
	},
	_query_success: function(subject) {
	}
});

