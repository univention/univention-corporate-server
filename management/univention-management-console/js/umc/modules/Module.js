/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.Module");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.layout.BorderContainer");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.modules.Module", [ dijit.layout.ContentPane, dijit.layout.BorderContainer, umc.widgets.StandbyMixin ], {
	// summary:
	//		Basis class for all module classes.

	// layout
	//border: false,
	//autoScroll: true,
	//layout: 'fit'

	postMixInProperties: function() {
		// set the css class umcModulePane
		this.class = (this.class || '') + ' umcModulePane';
		this.liveSplitters = false;
	}
	
});


