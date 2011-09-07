/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.TabContainer");

dojo.require("dijit.layout.TabContainer");

dojo.declare("umc.widgets.TabContainer", dijit.layout.TabContainer, {
	// summary:
	//		An extended version of the dijit TabContainer that can hide/show tabs.

	_setVisibilityOfChild: function( child, visible ) {
		umc.tools.assert( child.controlButton !== undefined, 'The widget is not attached to a TabContainer' );
		// we iterate over the children of the container to ensure the given widget is attached to THIS TabContainer
		dojo.forEach( this.getChildren(), function( item ) {
			if ( item == child ) {
				dojo.toggleClass( item.controlButton.domNode, 'dijitHidden', ! visible );
				return false;
			}
		} );
	},

	hideChild: function( child ) {
		this._setVisibilityOfChild( child, false );
	},

	showChild: function( child ) {
		this._setVisibilityOfChild( child, true );
	}
});


