/*
 * Copyright 2014-2017 Univention GmbH
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
	"umc/dialog",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/DropDownButton",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ComboBox",
	"umc/widgets/StandbyMixin",
	"umc/i18n/tools",
	"umc/i18n!",
	"dojo/domReady!",
	"dojo/NodeList-dom"
], function(declare, lang, array, tools, dialog, Menu, MenuItem, DropDownButton, ContainerWidget, ComboBox, StandbyMixin, i18nTools, _) {
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
					disabled: language.id === i18nTools.defaultLang(),
					onClick: function() {
						if (tools.status('loggedIn')) {
							dialog.confirm(_('<b>Warning</b>: The current session with all opened modules and unsaved settings gets lost and a page reload is done when switching the language.'), [{
								name: 'change',
								label: _('Switch language'),
								callback: function() {
									i18nTools.setLanguage(language.id);
								}
							}, {
								name: 'cancel',
								label: _('Cancel')
							}], _('Changing language'));
							return;
						}
						i18nTools.setLanguage(language.id);
					}
				}));
			}, this);

			this.addChild(this._languageButton);
		}
	});
});
