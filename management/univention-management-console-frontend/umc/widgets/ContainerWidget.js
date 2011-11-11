/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.ContainerWidget");

dojo.require("dijit._Widget");
dojo.require("dijit._Container");

dojo.declare("umc.widgets.ContainerWidget", [dijit._Widget, dijit._Container], {
	// description:
	//		Combination of Widget and Container class.
	style: '',

	'class': 'umcContainerWidget',

	// scrollable: Boolean
	//		If set to true, the container will set its width/height to 100% in order
	//		to enable scrollbars.
	scrollable: false,

	buildRendering: function() {
		this.inherited(arguments);

		if (this.scrollable) {
			dojo.style(this.containerNode, {
				width: '100%',
				height: '100%',
				overflow: 'auto'
			});
		}
	}
});


