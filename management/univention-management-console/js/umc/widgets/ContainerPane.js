/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.ContainerPane");

dojo.require("dijit._Container");
dojo.require("dijit.layout.ContentPane");

dojo.declare("umc.widgets.ContainerPane", [dijit.layout.ContentPane, dijit._Container], {
	// description:
	//		Combination of ContentPane and Container class.
	// summary:
	//		Container class that is simply a combination of a ContainerPane and
	//		a Container. This class allows one to have a simple Pane (e.g., for
	//		tabs) in combination with the addChild() method and other container
	//		functionalities.
});


