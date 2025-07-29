/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojo/Deferred",
	"umc/widgets/ToggleButton",
	"umc/menu/Menu",
	"umc/headerButtons",
	"umc/i18n!"
], function(declare, domClass, Deferred, ToggleButton, Menu, headerButtons, _) {

	// require umc/menu here in order to avoid circular dependencies
	var menuDeferred = new Deferred();
	require(["umc/menu"], function(_menu) {
		menuDeferred.resolve(_menu);
	});

	var menuButtonDeferred = new Deferred();

	var MenuButton = declare('umc.menu.Button', [ToggleButton], {
		//// overwrites
		iconClass: 'menu',

		//// self
		// forward to Menu.js
		showLoginHeader: true,

		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'ucsIconButton umcMenuButton');

			this.watch('checked', function(_name, _oldChecked, checked) {
				menuDeferred.then(function(menu) {
					if (checked) {
						menu.open();
					} else {
						menu.close();
					}
				});
			});

			const menu = new Menu({
				showLoginHeader: this.showLoginHeader
			});
			headerButtons.createOverlay(menu.domNode);
			headerButtons.subscribe(this, 'menu', menu);
			menu.startup();

			menuButtonDeferred.resolve(this);
		}
	});

	MenuButton.menuButtonDeferred = menuButtonDeferred;
	return MenuButton;
});
