/*
 * Copyright 2014-2015 Univention GmbH
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
/*global define console window setTimeout */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/DropDownButton",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane",
	"umc/widgets/ComboBox",
	"umc/widgets/StandbyMixin",
	"umc/i18n/tools",
	"umc/i18n!",
	"dojo/domReady!",
	"dojo/NodeList-dom"
], function(declare, lang, array, tools, Menu, MenuItem, DropDownButton, ContainerWidget, LabelPane, ComboBox, StandbyMixin, i18nTools, _) {
	return declare("umc.app.LanguageSwitch", [ContainerWidget], {
		_languageMenu: null,
		_languageButton: null,

		buildRendering: function() {
			this.inherited(arguments);

			this._languageMenu = new Menu({});
			this._languageButton = new DropDownButton({
				label: _('Language'),
				dropDown: this._languageMenu
			});

			array.forEach(i18nTools.availableLanguages, function(language) {
				this._languageMenu.addChild(new MenuItem({
					label: language.label,
					onClick: function() {
						i18nTools.setLanguage(language.id);
					}
				}));
			}, this);

			this.addChild(this._languageButton);
		}
	});
});
