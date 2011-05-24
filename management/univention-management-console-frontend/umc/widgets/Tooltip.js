/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Tooltip");

dojo.require("dijit.Tooltip");
dojo.require("umc.app");

dojo.declare("umc.widgets.Tooltip", dijit.Tooltip, {

	_onHover: function(/*Event*/ e) {
		// only show the tooltip if the config cookie for this is not set or set to 'true'
		if (umc.app.preferences('tooltips')) {
			this.inherited(arguments);
		}
	}

});


