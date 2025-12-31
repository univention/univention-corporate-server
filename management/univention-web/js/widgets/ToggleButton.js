/*
 * SPDX-FileCopyrightText: 2020-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dijit/form/ToggleButton",
	"./Icon",
	"put-selector/put"
], function(declare, domClass, domConstruct, ToggleButton, Icon, put) {
	return declare("umc.widgets.ToggleButton", [ ToggleButton ], {
		//// overwrites
		iconClass: '',
		_setIconClassAttr: function(iconClass) {
			if (iconClass) {
				if (this.iconNode) {
					Icon.setIconOfNode(this.iconNode, iconClass);
				} else {
					this.iconNode = Icon.createNode(iconClass, 'umcToggleButton__icon umcToggleButton__icon--notchecked');
					domConstruct.place(this.iconNode, this.titleNode, 'first');
				}
			} else {
				if (this.iconNode) {
					iconNode.remove();
					this.iconNode = null;
				}
			}
			this._set('iconClass', iconClass);
		},

		_setCheckedAttr: function(checked) {
			if (this.checkedIconClass) {
				if (checked) {
					this._beforeCheckedIconClass = this.iconClass || '';
					this.set('iconClass', this.checkedIconClass);
				} else {
					this.set('iconClass', this._beforeCheckedIconClass);
				}
			}
			this.inherited(arguments);
		},


		//// self
		_beforeCheckedIconClass: '',
		checkedIconClass: '',


		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'ucsButton');
			put(this.iconNode, '!');
			this.iconNode = null;
		}
	});
});

