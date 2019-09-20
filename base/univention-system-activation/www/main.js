/*
 * Copyright 2013-2019 Univention GmbH
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
/*global define require console window */

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom",
	"dojo/on",
	"dojo/router",
	"dojo/topic",
	"put-selector/put",
	"./ActivationWizard",
	"umc/menu",
	"umc/json!./entries.json",
	"umc/i18n/tools",
	"umc/i18n!systemactivation"
], function(lang, array, dom, on, router, topic, put, ActivationWizard, menu, entries, i18nTools, _) {
	entries.appliance_name = entries.appliance_name || '';

	var hasLicenseRequested = Boolean(entries.license_requested);

	return {
		start: function() {
			this.registerRouter();
			this.setupLanguageMenu();
			this.createWizard();
			// check if license already requested
			if (hasLicenseRequested) {
				router.startup('upload');
			} else {
				router.startup('register');
			}
		},

		registerRouter: function() {
			router.register(":tab", lang.hitch(this, function(data){
				this._wizard.switchPage(data.params.tab);
			}));
		},

		setupLanguageMenu: function() {
			var languageMenu = {
				priority: 55,
				label: _('Switch language'),
				id: 'umcMenuLanguage',
			};
			array.forEach(i18nTools.availableLanguages, function(language) {
				menu.addEntry({
					parentMenuId: 'umcMenuLanguage',
					label: language.label,
					disabled: language.id === i18nTools.defaultLang(),
					onClick: function() {
						topic.publish('/umc/actions', 'menu', 'switch-language', language.id);
						i18nTools.setLanguage(language.id);
					}
				});
			});

			if (i18nTools.availableLanguages.length > 1) {
				menu.addSubMenu(languageMenu);
			}
		},

		createWizard: function() {
			this._wizard = new ActivationWizard({
				'class': 'umcInlineDialog',
				entries: entries
			});
			var contentNode = dom.byId('content');
			put(contentNode, this._wizard.domNode);
			this._wizard.startup();
			this._wizard.on('goTo', function(nextPage) {
				router.go(nextPage);
			});
		}
	};
});
