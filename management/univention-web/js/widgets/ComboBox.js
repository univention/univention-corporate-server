/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2011-2022 Univention GmbH
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
	"dojo/query",
	"dijit/form/FilteringSelect",
	"umc/widgets/_SelectMixin",
	"umc/widgets/_FormWidgetMixin",
	"umc/widgets/Icon",
	"./Button",
	"put-selector/put"
], function(declare, lang, on, query, FilteringSelect, _SelectMixin, _FormWidgetMixin, Icon, Button, put) {
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

		buildRendering: function() {
			this.inherited(arguments);

			// exchange validation icon node
			var iconNode = Icon.createNode('alert-circle', 'umcTextBox__validationIcon');
			var validationContainerNode = query('.dijitValidationContainer', this.domNode)[0];
			put(validationContainerNode, '+', iconNode);
			put(validationContainerNode, '!');

			// exchange dropdown icon node
			var buttonNode = Button.simpleIconButtonNode('chevron-down', 'ucsIconButton umcTextBox__downArrowButton');
			put(this._buttonNode, '+', buttonNode);
			put(this._buttonNode, '!');
			this._buttonNode = buttonNode;
		},

		postCreate: function() {
			this.inherited(arguments);
			this.on('valuesLoaded', lang.hitch(this, '_updateVisibility'));
		}
	});
});

