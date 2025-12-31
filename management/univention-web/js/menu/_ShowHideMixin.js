/*
 * SPDX-FileCopyrightText: 2017-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/dom-class"
], function(declare, domClass) {
	return declare('umc.menu._ShowHideMixin', [], {
		hide: function() {
			domClass.add(this.domNode, 'dijitDisplayNone');
			this._set('visible', false);
		},

		show: function() {
			domClass.remove(this.domNode, 'dijitDisplayNone');
			this._set('visible', true);
		},

		_getVisibleAttr: function() {
			return !domClass.contains(this.domNode, 'dijitDisplayNone');
		},

		_setVisibleAttr: function(visible) {
			if (visible) {
				this.show();
			} else {
				this.hide();
			}
		},

		isSeparator: function() {
			return domClass.contains(this.domNode, 'separator');
		}
	});
});
