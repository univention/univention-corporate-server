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
	templateString: '<div style="display:inline-block;vertical-align:top;zoom:1;*display:inline;" class="umcLabelPane">' +
		'<div dojoAttachPoint="labelNode" class="umcLabelPaneLabelNode" style="display:block;"></div>' +
		'<div dojoAttachPoint="containerNode,contentNode" style="display:block;"></div>' +
		'</div>',

	// content: String|dijit._Widget
	//		String which contains the text (or HTML code) to be rendered or
	//		a dijit._Widget instance.
	content: '',

	// the widget's class name as CSS class
	'class': 'umcLabelPane',

	// label: String
	label: null,

	labelNode: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		// if we have a widget as content and label is not specified, use the widget's 
		// label attribute and watch it for changes
		if (null === this.label && this.content && dojo.isString(this.content.label)) {
			this.label = this.content.label || '';
			if (this.content.watch) {
				this.content.watch('label', dojo.hitch(this, function(attr, oldVal, newVal) {
					this.set('label', newVal || '');
				}));
			}
		} 
		else if (!dojo.isString(this.label)) {
			this.label = '';
		}
	},

	_setLabelAttr: function(_label) {
		var label = _label;

		// if we have a widget which is required, add the string ' (*)' to the label
		if (dojo.getObject('domNode', false, this.content) && 
				dojo.getObject('declaredClass', false, this.content) && 
				dojo.getObject('required', false, this.content)) {
			label = label + ' (*)';
		}
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

