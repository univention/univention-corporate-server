/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/when",
	"dijit/form/SimpleTextarea",
	"umc/tools",
	"umc/widgets/_FormWidgetMixin"
], function(declare, lang, when, SimpleTextarea, tools, _FormWidgetMixin) {
	return declare("umc.widgets.TextArea", [ SimpleTextarea, _FormWidgetMixin ], {
		// dynamicValue: String|Function
		//		Either an UMCP command to query a value from or a javascript function.
		//		The javascript function may return a String or a dojo/Deferred object.
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
		umcpCommand: lang.hitch(tools, 'umcpCommand'),

		// display the labe above the widget
		labelPosition: 'top',

		//FIXME: the name should be different from _loadValues, e.g., _dependencyUpdate,
		//       and the check for all met dependencies should be done in the Form
		_loadValues: function(/*Object?*/ params) {
			// mixin additional options for the UMCP command
			if (this.dynamicOptions && typeof this.dynamicOptions == "object") {
				lang.mixin(params, this.dynamicOptions);
			}

			// get the dynamic values, block concurrent events for value loading
			var func = tools.stringOrFunction(this.dynamicValue, this.umcpCommand);
			var deferredOrValues = func(params);

			// make sure we have an array or a dojo/Deferred object
			if (deferredOrValues) {
				when(deferredOrValues, lang.hitch(this, function(res) {
					this.set('value', res);
				}));
			}
		}
	});
});


