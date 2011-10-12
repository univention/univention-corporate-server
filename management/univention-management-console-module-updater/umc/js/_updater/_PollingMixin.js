/*global console MyError dojo dojox dijit umc window*/

dojo.provide('umc.modules._updater._PollingMixin');

dojo.require('umc.dialog');
dojo.require('umc.tools');

// Mixin that can be added to everything that has an attached
// moduleStore, to establish kind of polling for changes.
//
// The idea behind is that the store can return a kind of 'serial'
// value that will change if the underlying data has changed.

dojo.declare('umc.modules._updater._PollingMixin', [
       // currently nothing?
	], {
	
	postMixinProperties: function() {
		this.inherited(arguments);
		umc.tools.assert(this.moduleStore,"You can't use the _PollingMixin in a class that doesn't have a moduleStore");
	},
	
	buildRendering: function() {
		
		this.inherited(arguments);
		
		// Everything needed is kept in the 'polling' dictionary: constructor arguments
		// and all private status variables.
		//
		//	{
		//		// ------------ fields expected by our constructor ----------------
		//
		//		'interval':			some milliseconds
		//		'query':			an UMCP command to obtain the serial
		//		'callback':			the function (a method of 'this') to call if something has changed
		//
		//		// -------- fields maintained while polling is active -------------
		//
		//		'value':			the last seen value of our serial
		//		'function':			the function that fires the query
		//		'handler':			the function that handles the query result
		//		'timer':			the handle to the timeout (avoids double invocation)
		//	}
		//
		// All calls are wrapped into try/catch blocks. Errors cause a console error to be posted.
		// As we've set the 'handleErrors=false' flag, we can safely repeat the loop while errors
		// are encountered.
		//
		// If the class we're being mixed into contains the _query_error() and _query_success() functions
		// then they'll be called whenever a query returns.
		if (this.polling)
		{
			umc.tools.assert(this.polling['interval'],	"_PollingMixin does not work without 'interval' argument.");
			umc.tools.assert(this.polling['query'],		"_PollingMixin does not work without 'query' argument.");
			umc.tools.assert(this.polling['callback'],	"_PollingMixin does not work without 'callback' argument."); 
			
			this.polling['value'] = 0;		// initial values.
			this.polling['timer'] = '';
			
			// 'function' starts UMCP command and hands result over to 'handler'
			this.polling['function'] = dojo.hitch(this, function() {
				try
				{
					this.moduleStore.umcpCommand(this.polling['query'],{},false).then(
						dojo.hitch(this,function(data) {
							this._query_success(this.polling['query']);
							this.polling['handler'](data);
						}),
						dojo.hitch(this,function(data) {
							this._query_error(this.polling['query'],data);
							this.polling['handler'](null);
						})
						);
				}
				catch(error) 
				{
					console.error("Polling [function] error: " + error.message);
				}
			});

			// 'handler' checks for changedness, calls callback and reschedules 'function'
			this.polling['handler'] = dojo.hitch(this, function(data) {
				try
				{
					if (data != null)
					{
						if (data.result != this.polling['value'])
						{
							this.polling['value'] = data.result;
							this.polling['callback']();
						}
					}
					// on errors: reset the last seen value, so we ensure the next
					// sucessful callback will trigger the 'callback()' event.
					else
					{
						this.polling['value'] = 0;
					}
					if ((this.polling['interval']) && (! this.polling['timer']))
					{
						this.polling['timer'] = window.setTimeout(dojo.hitch(this,function() {
							this.polling['timer'] = '';
							this.polling['function']();
						}),this.polling['interval']);
					}
				}
				catch(error)
				{
					console.error("Polling [handler] error: " + error.message);
				}
			});
			
			this.startPolling();
		}
	},
	
	// public function to start polling
	startPolling: function() {
		if ((this.polling) && (this.polling['handler']) && (typeof(this.polling['handler']) == 'function'))
		{
			this.polling['handler'](null);
		}
	},
	
	// public function to stop polling
	stopPolling: function() {
		if (this.polling)
		{
			this.polling['interval'] = 0;
		}
	},
	
	// stops the timer if the object is destroyed.
	uninitialize: function() {

		this.stopPolling();
		this.inherited(arguments);
	}

});
