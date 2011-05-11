/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.TabbedModule");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.layout.TabContainer");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.modules.TabbedModule", [ dijit.layout.ContentPane, dijit.layout.TabContainer, umc.widgets.StandbyMixin ], {
	// summary:
	//		Basis class for all module classes.

	// layout
	nested: true,
	addTab: function ( title, content ) {
	    var pane = new dijit.layout.ContentPane( { title : title, content : content } );
		this.addChild( pane );
	}
});


