dojo.provide("dojox.charting.plot2d.Scatter");

dojo.require("dojox.charting.plot2d.Default");

dojo.declare("dojox.charting.plot2d.Scatter", dojox.charting.plot2d.Default, {
	constructor: function(){
		this.opt.lines   = false;
		this.opt.markers = true;
	}
});
