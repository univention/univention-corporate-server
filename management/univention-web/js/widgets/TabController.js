/*
 * Copyright 2014-2019 Univention GmbH
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
	"dojo/_base/array",
	"dojo/dom-class",
	"dijit/layout/TabController",
	"umc/i18n!"
], function(declare, lang, array, domClass, TabController, _) {
	return declare("umc.widgets.TabController", [TabController], {
		setVisibilityOfChild: function(child, visible) {
			array.forEach(this.getChildren(), lang.hitch(this, function(ibutton) {
				if (ibutton.page == child) {
					ibutton.set('disabled', !visible);
					domClass.toggle(ibutton.domNode, 'dijitDisplayNone', !visible);
				}
			}));
		},

		hideChild: function(child) {
			this.setVisibilityOfChild(child, false);
		},

		showChild: function(child) {
			this.setVisibilityOfChild(child, true);
		}
	});
});
