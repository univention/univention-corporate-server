dojo.provide("dojox.charting.plot2d.StackedAreas");

dojo.require("dojox.charting.plot2d.Stacked");

dojo.declare("dojox.charting.plot2d.StackedAreas", dojox.charting.plot2d.Stacked, {
	constructor: function(){
		this.opt.lines = true;
		this.opt.areas = true;
	}
});
