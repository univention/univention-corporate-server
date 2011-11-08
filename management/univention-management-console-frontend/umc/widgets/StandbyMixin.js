/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.StandbyMixin");

dojo.require("dojox.widget.Standby");
dojo.require("dijit._Widget");

dojo.declare("umc.widgets.StandbyMixin", dijit._Widget, {
	// summary:
	//		Mixin class to make a widget "standby-able"

	_standbyWidget: null,

	standbyOpacity: 0.75,

	uninitialize: function() {
		this.inherited(arguments);

		this._standbyWidget.destroy();
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create a standby widget targeted at this module
		this._standbyWidget = new dojox.widget.Standby({
			target: this.domNode,
			duration: 200,
			//zIndex: 99999999,
			opacity: this.standbyOpacity,
			color: '#FFF'
		});
		this.domNode.appendChild(this._standbyWidget.domNode);
		this._standbyWidget.startup();
	},

	_updateContent: function(content) {
		// type check of the content
		if (dojo.isString(content)) {
			// string
			this._standbyWidget.set('text', content);
			this._standbyWidget.set('centerIndicator', 'text');
		}
		else if (dojo.isObject(content) && content.declaredClass && content.domNode) {
			// widget
			this._standbyWidget.set('text', '');
			this._standbyWidget.set('centerIndicator', 'text');

			// hook the given widget to the text node
			dojo.place(content.domNode, this._standbyWidget._textNode);
			content.startup();
		}
		else {
			// set default image
			this._standbyWidget.set('centerIndicator', 'image');
		}
	},

	standby: function(/*Boolean*/ doStandby, /*mixed?*/ content) {
		if (doStandby) {
			// update the content of the standby widget
			this._updateContent(content);

			// show standby widget
			this._standbyWidget.show();
		}
		else {
			// hide standby widget
			this._standbyWidget.hide();
		}
	}
});



