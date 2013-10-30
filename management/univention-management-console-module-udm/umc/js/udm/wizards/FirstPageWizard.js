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
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/widgets/Wizard",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, tools, Wizard, _) {

	return declare("umc.modules.udm.wizards.FirstPageWizard", [ Wizard ], {
		focusFirstWidget: function(pageName) {
			var buttons = this._pages[pageName]._footerButtons;
			buttons.finish.focus();
		},

		getFooterButtons: function() {
			var buttons = this.inherited(arguments);
			array.forEach(buttons, lang.hitch(this, function(button) {
				if (button.name === 'finish') {
					button.label = _('Next');
				}
			}));
			return buttons;
		}
	});
});

