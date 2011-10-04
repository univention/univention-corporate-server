/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._online.Module");

dojo.require("umc.i18n");
dojo.require("umc.widgets.TabbedModule");


// Module with some useful additions:
//
//	-	add a method that can exchange two tabs against each other
//
dojo.declare("umc.modules._online.Module", [
    umc.widgets.TabbedModule,
	umc.i18n.Mixin
	], 
{

	// exchange two tabs, preserve selectedness.
	exchangeChild: function(from,to) {
		var what = 'nothing';
		try
		{
			what = 'getting FROM selection';
			var is_selected = from.get('selected');
			what = 'hiding FROM';
			this.hideChild(from);
			what = 'showing TO';
			this.showChild(to);
			if (is_selected)
			{
				what = 'selecting TO';
				this.selectChild(to);
			}
		}
		catch(error)
		{
			console.error("exchangeChild: [" + what + "] " + error.message);
		}
	}

	// TODO hideChild() should check selectedness too, and
	// select a different tab when needed.
		
});

