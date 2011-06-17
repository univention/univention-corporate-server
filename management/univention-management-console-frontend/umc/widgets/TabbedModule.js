/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.TabbedModule");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.layout.TabContainer");
dojo.require("dojox.layout.TableContainer");
dojo.require("umc.widgets._ModuleMixin");
dojo.require("umc.widgets.StandbyMixin");

//TODO: parent ContentPane should be removed?!?
dojo.declare("umc.widgets.TabbedModule", [ dijit.layout.ContentPane, dijit.layout.TabContainer, umc.widgets.StandbyMixin, umc.widgets._ModuleMixin ], {
	// summary:
	//		Basis class for all module classes that offer sub tabs.

	postMixInProperties: function() {
		this.inherited(arguments);

		// initated the _ModuleMixin class
		this._moduleInit();
	},

	// layout
	nested: true,
	addTab: function ( title, content ) {
	    var child = null;
	    if ( dojo.isArray( content ) ) {
		child = new dojox.layout.TableContainer( {
		    cols: 1,
		    showLabels: true,
		    orientation: 'vert'
		});
		dojo.forEach( content, function( item ) { child.addChild( item );  } );
	    } else {
		child = content;
	    }

	    var pane = new dijit.layout.ContentPane( { title : title, content : child } );
	    this.addChild( pane );
	}
});


