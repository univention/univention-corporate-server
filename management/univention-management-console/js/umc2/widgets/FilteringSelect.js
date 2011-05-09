/*global dojo dijit dojox umc2 console window */

dojo.provide("umc2.widgets.FilteringSelect");

dojo.require("dijit.form.FilteringSelect");

dojo.declare("umc2.widgets.FilteringSelect", dijit.form.FilteringSelect, {
	// description:
	//		This class just an extension of dijit.form.FilteringSelect
	//		which provides a default item which is set on calling reset().
	defaultItem: null,
	reset: function() {
		this.inherited(arguments);
		if (this.defaultItem) {
			this.set('item', this.defaultItem);
		}
	}
});


