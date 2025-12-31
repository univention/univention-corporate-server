/*
 * SPDX-FileCopyrightText: 2017-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/menu/_ShowHideMixin"
], function(declare, lang, domClass, _WidgetBase, _TemplatedMixin, _ShowHideMixin) {
	return declare('umc.menu.MenuItem', [_WidgetBase, _TemplatedMixin, _ShowHideMixin], {
		label: '',
		priority: 0,
		parentSlide: null,
		onClick: null,

		templateString: '' +
			'<div data-dojo-attach-point="contentNode" class="menuItem fullWidthTile">' +
				'${label}' +
			'</div>',

		buildRendering: function() {
			this.inherited(arguments);
			if (!this.onClick && !this.label) {
				domClass.add(this.domNode, 'separator');
			}
		}
	});
});
