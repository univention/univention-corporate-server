/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Tooltip");

dojo.require("dijit.Tooltip");
dojo.require("umc.tools");

dojo.declare("umc.widgets.Tooltip", dijit.Tooltip, {

	_onHover: function(/*Event*/ e) {
		// only show the tooltip if the config cookie for this is not set or set to 'true'
		if (umc.tools.preferences('tooltips')) {
			this.inherited(arguments);
		}
	}

});


