/*
 * Copyright 2013 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"umc/modules/udm/wizards/CreateWizard",
	"umc/i18n!umc/modules/udm"
], function(declare, array, CreateWizard, _) {

	return declare("umc.modules.udm.wizards.computers.computer", [ CreateWizard ], {
		widgetPages: [
			{ // page one
				title: _('Computer information'),
				widgets: [
					['name']
					//['default_network'],
					//['mac', 'ip']
				]
			}
		],

		//buildWidget: function(widgetName, originalWidgetDefinition) {
		//	if (widgetName == 'default_network') {
		//		return {
		//			name: widgetName,
		//			sizeClass: 'One',
		//			label: _('Use default network'),
		//			required: false,
		//			value: true,
		//			type: 'CheckBox'
		//		};
		//	} else {
		//		return this.inherited(arguments);
		//	}
		//},

		getValues: function() {
			var values = this.inherited(arguments);
			var networkWidget = this.detailPage._form.getWidget('network');
			var value;
			array.some(networkWidget.store._getItemsArray(), function(item) {
				if (item.label[0] == 'default') {
					value = item.id[0];
					return true;
				}
				if (!value) {
					// first non empty element is fallback
					value = item.id[0];
				}
				return false;
			});
			if (value) {
				values.network = value;
			}
			return values;
		}

	});
});

