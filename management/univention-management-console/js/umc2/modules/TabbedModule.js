/*global console MyError dojo dojox dijit umc2 */

dojo.provide("umc2.modules.TabbedModule");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.layout.TabContainer");
dojo.require("umc2.widgets.StandbyMixin");

dojo.declare("umc2.modules.TabbedModule", [ dijit.layout.ContentPane, dijit.layout.TabContainer, umc2.widgets.StandbyMixin ], {
	// summary:
	//		Basis class for all module classes.

	// layout
	nested: true,
	addTab: function ( title, content ) {
	    var pane = new dijit.layout.ContentPane( { title : title, content : content } );
		this.addChild( pane )
	}
});


