/*
 * SPDX-FileCopyrightText: 2020-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dijit/form/DropDownButton",
	"./Icon",
	"put-selector/put"
], function(declare, domClass, domConstruct, DropDownButton, Icon, put) {
	return declare("umc.widgets.DropDownButton", [ DropDownButton ], {
		//// overwrites
		iconClass: 'more-horizontal',
		_setIconClassAttr: function(iconClass) {
			if (iconClass) {
				if (this.iconNode) {
					Icon.setIconOfNode(this.iconNode, iconClass);
				} else {
					this.iconNode = Icon.createNode(iconClass);
					domConstruct.place(this.iconNode, this.titleNode, 'first');
				}
			} else {
				if (this.iconNode) {
					this.iconNode.remove();
					this.iconNode = null;
				}
			}
			this._set('iconClass', iconClass);
		},


		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'ucsButton');
			put(this.iconNode, '!');
			this.iconNode = null;
		}
	});
});
