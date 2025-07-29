/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

/**
 * @module umc/widgets/MobileTabsButton
 */
define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"umc/widgets/ToggleButton",
	"umc/headerButtons",
	"umc/tools",
	"put-selector/put",
	"umc/i18n!"
], function(declare, domClass, ToggleButton, headerButtons, tools, put) {
	return declare("umc.widgets.MobileTabsButton", [ToggleButton], {
		showLabel: false,
		iconClass: 'square',

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcMobileTabsToggleButton ucsIconButton dijitDisplayNone');
			this.counterNode = put(this.domNode, 'div.umcHeaderButton__counter');

			this.mobileTabsContainer = put('div.umcMobileTabs');
			headerButtons.createOverlay(this.mobileTabsContainer);
			headerButtons.subscribe(this, 'tabs');
		},

		_setCheckedAttr: function(checked) {
			domClass.toggle(this.mobileTabsContainer, 'umcMobileTabs--visible', checked);
			this.inherited(arguments);
		}
	});
});

