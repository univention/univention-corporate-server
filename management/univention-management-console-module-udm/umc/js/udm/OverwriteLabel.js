/*
 * Copyright 2011-2015 Univention GmbH
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
	"umc/widgets/LabelPane",
	"umc/widgets/CheckBox",
	"umc/i18n!umc/modules/udm"
], function(declare, LabelPane, CheckBox, _) {
	return declare('umc.modules.udm.OverwriteLabel', [ LabelPane ], {
		// summary:
		//		Class that provides a widget in the form "[ ] overwrite" for multi-edit mode.

		style: 'display:block; margin-top:-3px; font-style:italic;',

		postMixInProperties: function() {
			// force label and content
			this.content = new CheckBox({
				label: _('Overwrite'),
				value: false
			});

			this.inherited(arguments);
		},

		_setValueAttr: function(newVal) {
			this.content.set('value', newVal);
		},

		_getValueAttr: function() {
			return this.content.get('value');
		}
	});
});
