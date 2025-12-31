/*
 * SPDX-FileCopyrightText: 2020-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_Container",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/widgets/Icon"
], function(declare, lang, array, domClass, _WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin) {
	return declare("umc.modules.appcenter.SidebarElement", [_WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'appDetailsSidebarElement',
		templateString: `
			<div>
				<div class="mainHeader">
					<svg data-dojo-type="umc/widgets/Icon" data-dojo-props="iconName: this.icon"></svg>
					<span>\${header}</span>
				</div>
				<div class="mainContent" data-dojo-attach-point="containerNode">
				</div>
			</div>
		`
	});
});
