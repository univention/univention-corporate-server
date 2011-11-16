/*
 * Copyright 2011 Univention GmbH
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

dojo.provide("umc.widgets.Button");

dojo.require("dijit.form.Button");

dojo.declare("umc.widgets.Button", dijit.form.Button, {
	// defaultButton: Boolean
	//		If set to 'true', button will be rendered as default, i.e., submit button.
	defaultButton: false,

	// callback: Function
	//		Convenience property for onClick callback handler.
	callback: null,

	// the widget's class name as CSS class
	'class': 'umcButton',

	type: 'button',

	constructor: function(props) {
		dojo.mixin(this, props);
		if (this.defaultButton) {
			this['class'] = 'umcSubmitButton';
		}
	},

	buildRendering: function() {
		this.inherited(arguments);

		this.set('iconClass', this.iconClass);
	},
	
	postCreate: function() {
		this.inherited(arguments);

		if (dojo.isFunction(this.callback)) {
			this.connect(this, 'onClick', 'callback');
		}
	}
});



