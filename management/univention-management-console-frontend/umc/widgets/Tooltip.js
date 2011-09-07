/*global dojo dijit dojox umc console setTimeout */

dojo.provide("umc.widgets.Tooltip");

dojo.require("dijit.Tooltip");
dojo.require("umc.tools");

/*dojo.extend(dijit._MasterTooltip, {
	buildRendering: function() {
		if(!this.domNode){
			// Create root node if it wasn't created by _Templated
			this.domNode = this.srcNodeRef || dojo.create('div');
		}

		// hide the tooltip
		this.connect(this.domNode, 'onclick', 'hide');
	}
});*/

// connect to the master tooltip's domNode onlick event in order to
// trigger the fade out animation.
(function() {
	var hdl = dojo.connect(dijit, 'showTooltip', function() {
		dojo.connect(dijit._masterTT.domNode, 'onclick', dijit._masterTT.fadeOut, 'play');

		// disconnect from 'showTooltip', we only need to register the handler once
		dojo.disconnect(hdl);
	});
})();

dojo.declare("umc.widgets.Tooltip", dijit.Tooltip, {
	// the widget's class name as CSS class
	'class': 'umcTooltip',

	_onHover: function(/*Event*/ e) {
		// only show the tooltip if the config cookie for this is not set or set to 'true'
		if (umc.tools.preferences('tooltips')) {
			this.inherited(arguments);
		}
	}

});


