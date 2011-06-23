/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.ContainerWidget");

dojo.require("dijit._Widget");
dojo.require("dijit._Container");

dojo.declare("umc.widgets.ContainerWidget", [dijit._Widget, dijit._Container], {
	// description:
	//		Combination of Widget and Container class.
	style: 'overflow: auto;'
});


