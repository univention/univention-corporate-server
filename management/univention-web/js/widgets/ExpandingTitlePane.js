/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page"
], function(declare, lang, array, kernel, ContainerWidget, Page) {
	return declare("umc.widgets.ExpandingTitlePane", ContainerWidget, {
		// summary:
		//		Obsolete widget which adds itself to the parent and removes its domNode

		style: 'display: none;',
		parentWidget: null,

		constructor: function() {
			this.inherited(arguments);
			kernel.deprecated('umc.widgets.ExpandingTitlePane', 'do not use it anymore!');
			this._widgets = [];
		},

		getParentWidget: function() {
			// usually parentNode.parentNode should be a Page object
			var widget = this.getParent().getParent();
			if (!widget || !widget.isInstanceOf(Page)) {
				// no Page object -> fallback to the next parent widget
				widget = this.getParent();
			}
			return widget;
		},

		__addChild: function(child) {
			if (this.parentWidget && this.parentWidget.addChild) {
				this.parentWidget.addChild(child);
			}
		},

		addChild: function(child) {
			if (!this._started) {
				this._widgets.push(child);
			} else {
				this.__addChild(child);
			}
		},

		getChildren: function() {
			if (this.parentWidget && this.parentWidget.getChildren) {
				return this.parentWidget.getChildren();
			}
			return this.inherited(arguments);
		},

		startup: function() {
			this.inherited(arguments);

			if (this.parentWidget) {
				return;
			}
			// get the parent node and remove ourself from the DOM
			this.parentWidget = this.getParentWidget();
			this.domNode.parentNode.removeChild(this.domNode);
			this.domNode = null;
			this.parentWidget.own(this);

			// add all buffered child widgets to the DOM
			array.forEach(this._widgets, lang.hitch(this, '__addChild'));
			this._widgets = [];
		}
	});
});
