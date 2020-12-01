/*
 * Copyright 2011-2020 Univention GmbH
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
	"dojo/dom-construct",
	"dojo/query",
	"dijit/form/NumberSpinner",
	"./_FormWidgetMixin",
	"./Icon",
	"put-selector/put"
], function(declare, domConstruct, query, NumberSpinner, _FormWidgetMixin, Icon, put) {
	return declare("umc.widgets.NumberSpinner", [ NumberSpinner, _FormWidgetMixin ], {
		buildRendering: function() {
			this.inherited(arguments);

			// exchange spinner icon nodes
			domConstruct.empty(this.upArrowNode);
			var upIcon = new Icon({
				iconName: 'chevron-up'
			});
			put(this.upArrowNode, upIcon.domNode);
			domConstruct.empty(this.downArrowNode);
			var downIcon = new Icon({
				iconName: 'chevron-down'
			});
			put(this.downArrowNode, downIcon.domNode);

			// exchange validation icon node
			var icon = new Icon({
				'class': 'umcTextBox__validationIcon',
				iconName: 'alert-circle'
			});
			var validationContainerNode = query('.dijitValidationContainer', this.domNode)[0];
			put(validationContainerNode, '+', icon.domNode);
			put(validationContainerNode, '!');
		}
	});
});
