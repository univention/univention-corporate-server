/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/window",
	"dojo/window",
	"dojo/dom-class",
	"dojo/Evented",
	"dojo/topic",
	"umc/tools",
	"umc/menu/Menu",
	"umc/menu/Button"
], function(declare, lang, baseWin, win, domClass, Evented, topic, tools, Menu, Button) {
	var menu = new declare([Evented], {
		addSubMenu: function(/*Object*/ item) {
			return this.getMenuInstance().then(function(menu) {
				return menu.addSubMenu(item);
			});
		},

		addEntry: function(/*Object*/ item) {
			return this.getMenuInstance().then(function(menu) {
				return menu.addMenuEntry(item);
			});
		},

		addSeparator: function(/*Object*/ item) {
			return this.getMenuInstance().then(function(menu) {
				return menu.addMenuSeparator(item);
			});
		},

		open: function() {
			if (domClass.contains(baseWin.body(), 'mobileMenuActive')) {
				return;
			}
			domClass.add(baseWin.body(), 'mobileMenuActive');
			var hasScrollbar = baseWin.body().scrollHeight > win.getBox().h;
			domClass.toggle(baseWin.body(), 'hasScrollbar', hasScrollbar);
		},

		close: function() {
			if (!domClass.contains(baseWin.body(), 'mobileMenuActive')) {
				return;
			}
			domClass.remove(baseWin.body(), 'mobileMenuActive');
			domClass.remove(baseWin.body(), 'hasScrollbar');
			tools.defer(lang.hitch(this, function() {
				this.getMenuInstance().then(function(menuInstance) {
					menuInstance.closeOpenedSubMenus();
				});
			}), 260); // tied to transition duration in header.styl
		},

		getButtonInstance: function() {
			return Button.menuButtonDeferred;
		},

		getMenuInstance: function() {
			return Menu.mobileMenuDeferred;
		},

		hideEntry: function(entryDeferred) {
			entryDeferred.then(function(entry) {
				entry.hide();
			});
		},

		showEntry: function(entryDeferred) {
			entryDeferred.then(function(entry) {
				entry.show();
			});
		}
	})();
	return menu;
});
