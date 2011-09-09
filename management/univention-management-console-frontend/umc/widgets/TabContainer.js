/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.TabContainer");

dojo.require("dijit.layout.TabContainer");
dojo.require("umc.tools");

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
	},

	startup: function() {
		this.inherited(arguments);

		// FIXME: Workaround for refreshing problems with datagrids when they are rendered
		//        on an inactive tab.

		// iterate over all tabs
		dojo.forEach(this.getChildren(), function(ipage) {
			// find all widgets that inherit from dojox.grid._Grid on the tab
			dojo.forEach(ipage.getDescendants(), function(iwidget) {
				if (umc.tools.inheritsFrom(iwidget, 'dojox.grid._Grid')) {
					// hook to onShow event
					this.connect(ipage, 'onShow', function() {
						iwidget.startup();
					});
				}
			}, this);
		}, this);
	}
});


