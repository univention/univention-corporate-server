/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.TitlePane");

dojo.require("dijit.TitlePane");
dojo.require("dijit._Container");

dojo.declare("umc.widgets.TitlePane", [ dijit.TitlePane, dijit._Container ], {
	// summary:
	//		Widget that extends dijit.TitlePane with methods of a container widget.

	// the widget's class name as CSS class
	'class': 'umcTitlePane'
});


