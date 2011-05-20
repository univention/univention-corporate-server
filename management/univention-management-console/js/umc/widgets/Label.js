/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.Label");

dojo.require("dijit._Widget");
dojo.require("dijit._Templated");

dojo.declare("umc.widgets.Label", [ dijit._Widget, dijit._Templated ], {
	// summary:
	//		Simple widget that displays a given label, e.g., some text to 
	//		be rendered in a form. Can also render HTML code.

	templateString: '<div dojoAttachPoint="contentNode">${content}</div>',

	// label: String
	//		String which contains the text (or HTML code) to be rendered.
	content: ''
});

