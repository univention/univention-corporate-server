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

	standby: function(/*Boolean*/ doStandby) {
		if (doStandby) {
			// show standby widget
			this._standbyWidget.show();
		}
		else {
			// hide standby widget
			this._standbyWidget.hide();
		}
	}
});



