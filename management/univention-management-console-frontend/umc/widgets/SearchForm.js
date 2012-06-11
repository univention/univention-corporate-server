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
/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.SearchForm");

dojo.require("umc.widgets.Form");
dojo.require("dijit.form.Form");
dojo.require("umc.i18n");

dojo.declare("umc.widgets.SearchForm", [ umc.widgets.Form, umc.i18n.Mixin ], {
	// summary:
	//		Encapsulates a complete search form with standard search and cancel
	//		buttons. This builds on top of umc.widget.Form.

	i18nClass: 'umc.app',

	// the widget's class name as CSS class
	'class': 'umcSearchForm',

	postMixInProperties: function() {
		// in case no buttons are defined, define the standard 'submit' button
		if (!this.buttons) {
			this.buttons = [ {
				name: 'submit',
				label: this._( 'Search' )
			}];
		}

		// add the buttons in a new row in case they have not been specified in the layout
		var buttonsExist = false;
		var stack = [this.layout];
		while (stack.length) {
			var el = stack.pop();
			if (dojo.isArray(el)) {
				dojo.forEach(el, function(i) {
					stack.push(i);
				});
			}
			else if ( 'submit' == el ) {
				buttonsExist = true;
				break;
			}
		}
		if (!buttonsExist) {
			this.layout.push( [ 'submit' ] );
		}

		this.inherited(arguments);
	},

	postCreate: function() {
		this.inherited(arguments);

		this.connect(this, 'onSubmit', function() {
			this.onSearch(this.gatherFormValues());
		});
	},

	onSearch: function(values) {
		// event stub
	}
});







