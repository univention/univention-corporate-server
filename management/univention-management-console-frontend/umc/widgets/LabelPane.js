/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.LabelPane");

dojo.require("dijit._Widget");
dojo.require("dijit._Templated");
dojo.require("dijit._Container");

dojo.declare("umc.widgets.LabelPane", [ dijit._Widget, dijit._Templated, dijit._Container ], {
	// summary:
	//		Simple widget that displays a widget/HTML code with a label above.

	//TODO: don't use float, use display:inline-block; we need a hack for IE7 here, see:
	//      http://robertnyman.com/2010/02/24/css-display-inline-block-why-it-rocks-and-why-it-sucks/
	templateString: '<div style="display:inline-block;vertical-align:top;" class="umcLabelPane">' +
		'<div dojoAttachPoint="labelNode" class="umcLabelPaneLabelNode" style="display:block;"></div>' +
		'<div dojoAttachPoint="containerNode,contentNode" style="display:block;"></div>' +
		'</div>',

	// content: String|dijit._Widget
	//		String which contains the text (or HTML code) to be rendered or
	//		a dijit._Widget instance.
	content: '',

	// label: String
	label: '',

	labelNode: null,

	_setLabelAttr: function(label) {
		this.label = label;
		this.labelNode.innerHTML = label;
	},

	_setContentAttr: function(content) {
		this.content = content;

		// we have a string
		if (dojo.isString(content)) {
			this.contentNode.innerHTML = content;
		}
		// if we have a widget, clear the content and hook in the domNode directly
		else if (dojo.getObject('domNode', false, content) && dojo.getObject('declaredClass', false, content)) {
			this.contentNode.innerHTML = '';
			this.addChild(content);
		}
	}
});

