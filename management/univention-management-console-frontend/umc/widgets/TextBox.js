/*
 * Copyright 2011-2012 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define console*/

dojo.provide("umc.widgets.TextBox");

dojo.require("dijit.form.ValidationTextBox");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("tools");

/*REQUIRE:"dojo/_base/declare"*/ /*TODO*/return declare([ dijit.form.ValidationTextBox, umc.widgets._FormWidgetMixin ], {
	// the widget's class name as CSS class
	'class': 'umcTextBox',

	// dynamicValue: String|Function
	//		Either an UMCP command to query a value from or a javascript function.
	//		The javascript function may return a String or a /*REQUIRE:"dojo/Deferred"*/ Deferred object.
	dynamicValue: null,

	// depends: String?|String[]?
	//		Specifies that values need to be loaded dynamically depending on
	//		other form fields.
	depends: null,

	// umcpCommand:
	//		Reference to the umcpCommand the widget should use.
	//		In order to make the widget send information such as module flavor
	//		etc., it can be necessary to specify a module specific umcpCommand
	//		method.
	umcpCommand: tools.umcpCommand,

	//FIXME: the name should be different from _loadValues, e.g., _dependencyUpdate,
	//       and the check for all met dependencies should be done in the Form
	_loadValues: function(/*Object?*/ params) {
		// mixin additional options for the UMCP command
		if (this.dynamicOptions && typeof this.dynamicOptions == "object") {
			/*REQUIRE:"dojo/_base/lang"*/ lang.mixin(params, this.dynamicOptions);
		}

		// get the dynamic values, block concurrent events for value loading
		var func = tools.stringOrFunction(this.dynamicValue, this.umcpCommand);
		var deferredOrValues = func(params);

		// make sure we have an array or a /*REQUIRE:"dojo/Deferred"*/ Deferred object
		if (deferredOrValues) {
			/*REQUIRE:"dojo/when"*/ when(deferredOrValues, /*REQUIRE:"dojo/_base/lang"*/ lang.hitch(this, function(res) {
				this.set('value', res);
			}));
		}
	}
});



