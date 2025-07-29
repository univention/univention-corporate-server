/*
 * SPDX-FileCopyrightText: 2013-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
