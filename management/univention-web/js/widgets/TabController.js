/*
 * SPDX-FileCopyrightText: 2014-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
	var _TabController =  declare("umc.widgets.TabController", [TabController], {
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
	_TabController.TabButton = TabController.TabButton;
	return _TabController;
});
