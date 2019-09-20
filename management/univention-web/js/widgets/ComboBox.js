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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"dijit/form/FilteringSelect",
	"umc/widgets/_SelectMixin",
	"umc/widgets/_FormWidgetMixin"
], function(declare, lang, on, FilteringSelect, _SelectMixin, _FormWidgetMixin) {
	return declare("umc.widgets.ComboBox", [ FilteringSelect , _SelectMixin, _FormWidgetMixin ], {
		// search for the substring when typing
		queryExpr: '*${0}*',

		// no auto completion, otherwise this gets weird in combination with the '*${0}*' search
		autoComplete: false,

		// autoHide: Boolean
		//		If true, the ComboBox will only be visible if there it lists more than
		//		one element.
		autoHide: false,

		_firstClick: true,

		postMixInProperties: function() {
			this.inherited(arguments);

			if (this.autoHide) {
				// autoHide is set, by default the widget will be hidden
				this.visible = false;
			}
		},

		_updateVisibility: function() {
			if (this.autoHide) {
				// show the widget in case there are more than 1 values
				var values = this.getAllItems();
				this.set('visible', values.length > 1);
			}
		},

		postCreate: function() {
			this.inherited(arguments);
			this.on('valuesLoaded', lang.hitch(this, '_updateVisibility'));
		}
	});
});

