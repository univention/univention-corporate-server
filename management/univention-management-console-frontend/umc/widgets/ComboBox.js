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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"dojo/aspect",
	"dojo/has",
	"dojo/dom",
	"dijit/focus",
	"dijit/form/FilteringSelect",
	"umc/widgets/_SelectMixin",
	"umc/widgets/_FormWidgetMixin"
], function(declare, lang, on, aspect, has, dom, focusUtil, FilteringSelect, _SelectMixin, _FormWidgetMixin) {
	// monitor the last clicked DOM node... for special handling of touch devices
	var clickedNode = null;
	aspect.before(focusUtil, '_onTouchNode', function(node, by) {
		clickedNode = node;
		return [node, by];
	});

	return declare("umc.widgets.ComboBox", [ FilteringSelect , _SelectMixin, _FormWidgetMixin ], {
		// the widget's class name as CSS class
		'class': 'umcComboBox',

		// search for the substring when typing
		queryExpr: '*${0}*',

		// no auto completion, otherwise this gets weired in combination with the '*${0}*' search
		autoComplete: false,

		// autoHide: Boolean
		//		If true, the ComboBox will only be visible if there it lists more than
		//		one element.
		autoHide: false,

		_firstClick: true,

		postMixInProperties: function() {
			this.inherited(arguments);

			if (this.autoHide) {
				// autoHide ist set, by default the widget will be hidden
				this.visible = false;
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			on.once(this, 'valuesLoaded', function(values) {
				if (this.autoHide) {
					// show the widget in case there are more than 1 values
					this.set('visible', values.length > 1);
				}
			});
		},

		_onFocus: function() {
			if (has('touch')) {
				// special handling for touch devices...
				var isButtonClicked = dom.isDescendant(clickedNode, this._buttonNode);
				if (!this.textbox.disabled && (this._firstClick || isButtonClicked)) {
					// disable focusing the input box on touch devices
					// in order to avoid the keyboard from showing
					this.textbox.disabled = true;
					if (this._firstClick && !isButtonClicked) {
						this.toggleDropDown();
					}
					this._firstClick = false;
					setTimeout(lang.hitch(this, function() {
						this.textbox.disabled = false;
						clickedNode = null;
					}), 1000);
				}
			}
			this.inherited(arguments);
		}
	});
});

