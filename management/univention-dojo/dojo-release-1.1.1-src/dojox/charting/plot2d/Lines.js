dojo.provide("dojox.charting.plot2d.Lines");

dojo.require("dojox.charting.plot2d.Default");

dojo.declare("dojox.charting.plot2d.Lines", dojox.charting.plot2d.Default, {
	constructor: function(){
		this.opt.lines = true;
	}
});
