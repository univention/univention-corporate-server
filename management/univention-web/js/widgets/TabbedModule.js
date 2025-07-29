/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"umc/widgets/TabContainer",
	"dijit/layout/StackContainer",
	"umc/widgets/TabController",
	"umc/widgets/Page",
	"umc/widgets/Module"
], function(declare, TabContainer, StackContainer, TabController, Page, Module) {
	return declare("umc.widgets.TabbedModule", [Module], {
		// summary:
		//		Basis class for module classes.
		//		It extends dijit.layout.TabContainer and adds some module specific
		//		properties/methods.

		// subtabs should be displayed as nested tabs
		nested: true,

		pageClass: '',

		buildRendering: function() {
			this.inherited(arguments);

			this._tabs = new StackContainer({
				baseClass: StackContainer.prototype.baseClass + ' umcTabbedModuleTabs',
				nested: this._nested,
				doLayout: false
			});
			this._tabController = new TabController({
				baseClass: TabController.prototype.baseClass + ' umcTabbedModuleTabController',
				region: 'nav',
				containerId: this._tabs.id
			});
			var ctn = new Page({
				'class': this.pageClass,
				noFooter: true
			});
			ctn.addChild(this._tabController);
			ctn.addChild(this._tabs);
			this.addChild(ctn);
			//this._bottom.addChild(this._tabController);
		},

		onClose: function() {
			return this._tabs.onClose();
		},

		addTab: function(/*dijit/_WidgetBase*/ widget, /*int?*/ insertIndex) {
			return this._tabs.addChild(widget, insertIndex);
		},

		selectTab: function(/*dijit/_WidgetBase|String*/ page, /*Boolean*/ animate) {
			return this._tabs.selectChild(page, animate);
		},

		removeTab: function(/*dijit/_WidgetBase*/ page) {
			return this._tabs.removeChild(page);
		},

		hideTab: function(/*dijit/_WidgetBase*/ page) {
			return this._tabs.hideTab(page);
		},

		showTab: function(/*dijit/_WidgetBase*/ page) {
			return this._tabs.showTab(page);
		}
	});
});
