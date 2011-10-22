/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._pkgdb.KeyTranslator");

dojo.require("umc.i18n");
dojo.require("umc.dialog");

// A helper mixin that is mixed into any instance of our umc.modules._pkgdb.Page class.
// Helps with i18n issues.

dojo.declare("umc.modules._pkgdb.KeyTranslator", [
//	umc.i18n.Mixin
	] , 
{

	// i18nClass is already defined in the class where we're being mixed in
	
	// This function accepts a field (column) name and returns any additional
	// options that are needed in construction of the data grid. Even if all
	// structural information is kept in the Python module, the design properties
	// of the frontend should be concentrated in the JS part.
	_field_options: function(key) {
		
		var t = {
			'inststate': {
				label:		this._("Installation<br/>state"),
				width:		'adjust'
			},
			'inventory_date': {
				label:		this._("Inventory date")
			},
			'pkgname': {
				label:		this._("Package name")
			},
			'vername': {
				label:		this._("Package version")
			},
			'currentstate': {
				label:		this._("Package<br/>state"),
				width:		'adjust'
			},
			'selectedstate': {
				label:		this._("Selection<br/>state"),
				width:		'adjust'
			},
			'sysname': {
				label:		this._("System name")
			},
			'sysrole': {
				label:		this._("System role")
			},
			'sysversion': {
				label:		this._("UCS Version")
			}
		};
		
		if (t[key]) { return t[key]; }
		
		return null;
	}

	
});