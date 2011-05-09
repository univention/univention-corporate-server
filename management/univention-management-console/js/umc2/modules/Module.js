/*global console MyError dojo dojox dijit umc2 */

dojo.provide("umc2.modules.Module");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.layout.BorderContainer");
dojo.require("umc2.widgets.StandbyMixin");

dojo.declare("umc2.modules.Module", [ dijit.layout.ContentPane, dijit.layout.BorderContainer, umc2.widgets.StandbyMixin ], {
	// summary:
	//		Basis class for all module classes.

	// layout
	//border: false,
	//autoScroll: true,
	//layout: 'fit'
	
});


