/*
 * Copyright 2020 Univention GmbH
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
/*global define,console*/

define([
	"dojo/_base/declare",
	"dijit/form/DropDownButton",
	"./Icon",
	"put-selector/put"
], function(declare, DropDownButton, Icon, put) {
	return declare("umc.widgets.DropDownButton", [ DropDownButton ], {
		// do not display button labels via the LabelPane
		displayLabel: false,

		iconClass: 'more-horizontal',

		buildRendering: function() {
			this.inherited(arguments);
			this.icon = new Icon({});
			put(this.iconNode, '+', this.icon.domNode);
			put(this.iconNode, '!');
		},

		_setIconClassAttr: function(iconClass) {
			this.icon.set('iconName', iconClass);
			this._set('iconClass', iconClass);
		}
	});
});
