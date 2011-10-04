/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._online.Grid");

dojo.require("umc.widgets.Grid");
dojo.require("umc.modules._online._PollingMixin");

// Grid with some useful additions:
//
//	-	add capability to poll for changes in the store, and
//		to refresh the whole grid if something has changed.
//
dojo.declare("umc.modules._online.Grid", [
	umc.widgets.Grid,
	umc.modules._online._PollingMixin
	],
{
	buildRendering: function() {
		
		this.inherited(arguments);
		
	},
	
	// Two callbacks that are used by queries that want to propagate
	// their outcome to the main error handlers
	_query_error: function(subject,data) {
	},
	_query_success: function(subject) {
	}
});
