dojo.provide("dojox.charting.plot2d.StackedLines");

dojo.require("dojox.charting.plot2d.Stacked");

dojo.declare("dojox.charting.plot2d.StackedLines", dojox.charting.plot2d.Stacked, {
	constructor: function(){
		this.opt.lines = true;
	}
});
