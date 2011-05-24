/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Toaster");

dojo.require("dojox.widget.Toaster");

// TODO: the css property box-shadow does not work since a clipping is set dynamically,
//		 this could be fixed...
dojo.declare("umc.widgets.Toaster", dojox.widget.Toaster, {
	// summary:
	//		Extension of dojox.widget.Toaster in order to allow centered notification.

	// positionDirection: String
	//		Position from which message slides into screen, one of
	//		["br-up", "br-left", "bl-up", "bl-right", "tr-down", "tr-left", "tl-down", "tl-right"]
	positionDirection: "tc-down",

	// positionDirectionTypes: Array
	//		Possible values for positionDirection parameter
	positionDirectionTypes: ["br-up", "br-left", "bc-up", "bl-up", "bl-right", "tr-down", "tr-left", "tc-down", "tl-down", "tl-right"],

	// extend internal method for placing elements
	_placeClip: function() {
		this.inherited(arguments);

		// get the viewport and node size
		var view = dojo.window.getBox();
		var nodeSize = dojo.marginBox(this.containerNode);

		// set up the position for a centered toaster
		var style = this.clipNode.style;
		var pd = this.positionDirection;
		if(pd.match(/^[tb]c-/)){
			style.left = ((view.w - nodeSize.w) / 2 - view.l)+"px";
		}
	}
});



