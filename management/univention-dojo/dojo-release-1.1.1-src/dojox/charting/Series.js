dojo.provide("dojox.charting.Series");

dojo.require("dojox.charting.Element");

dojo.declare("dojox.charting.Series", dojox.charting.Element, {
	constructor: function(chart, data, kwArgs){
		dojo.mixin(this, kwArgs);
		if(typeof this.plot != "string"){ this.plot = "default"; }
		this.data = data;
		this.dirty = true;
		this.clear();
	},
	clear: function(){
		this.dyn = {};
	}
});
