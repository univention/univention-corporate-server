/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/widgets/Text",
	"umc/widgets/Icon",
	"umc/widgets/ContainerWidget"
], function(declare, domClass, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, Text, Icon, ContainerWidget) {
	return declare('umc.menu.Slide', [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		isSubMenu: true,
		label: '',
		_setLabelAttr: { node: 'labelNode', type: 'innerHTML' },

		templateString: `
			<div class="menuSlide hiddenSlide">
				<div
					data-dojo-attach-point="headerNode"
					class="menuSlideHeader fullWidthTile"
				>
					${Icon.asHTMLString('chevron-left')}
					<div data-dojo-attach-point="labelNode"></div>
				</div>
				<div
					data-dojo-type="umc/widgets/ContainerWidget"
					data-dojo-attach-point="itemsContainer"
					class="menuSlideItemsContainer"
				></div>
			</div>
		`.trim(),

		buildRendering: function() {
			this.inherited(arguments);
			if (this.isSubMenu) {
				domClass.add(this.headerNode, 'subMenu');
			}
		}
	});
});
