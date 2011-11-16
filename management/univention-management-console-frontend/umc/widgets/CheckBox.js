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

dojo.provide("umc.widgets.CheckBox");

dojo.require("dijit.form.CheckBox");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.tools");

dojo.declare("umc.widgets.CheckBox", [ dijit.form.CheckBox, umc.widgets._FormWidgetMixin ], {
	// by default, the checkbox is turned off
	value: false,

	// the widget's class name as CSS class
	'class': 'umcCheckBox',

	// a checkbox is always true
	valid: true,

	// internal cache of the initial value
	_initialValue: null,

	postMixInProperties: function() {
		this._initialValue = this.checked = this.value;
		this.inherited( arguments );
		this.sizeClass = null;
	},

	_setValueAttr: function(/*String|Boolean*/ newValue, /*Boolean*/ priorityChange){
		// based on the code from dijit.form.CheckBox
		this.value = newValue = umc.tools.isTrue( newValue );

		// this is important, otherwise the inital state is displayed wrong
		if(this._created){
			this.set('checked', newValue, priorityChange);
		}
	},

	_getValueAttr: function() {
		return this.get('checked');
	}
});



