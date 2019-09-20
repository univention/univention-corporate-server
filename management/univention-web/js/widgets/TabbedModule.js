/*
 * Copyright 2011-2019 Univention GmbH
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
			var ctn = new Page({noFooter: true});
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
