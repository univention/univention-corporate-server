/*
 * SPDX-FileCopyrightText: 2014-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/aspect",
	"dijit/registry"
], function(declare, aspect, registry) {
	return declare("umc.widget._RegisterOnShowMixin", [], {
		_registerAtParentOnShowEvents: function(callback) {
			// iterate up the DOM and register the given callback
			// at each ancestor widget that has a _onShow() method
			var node = this.domNode;
			while (node) {
				var widget = registry.getEnclosingWidget(node.parentNode);
				if (!widget) {
					node = null;
					continue;
				}
				if (widget._onShow) {
					this.own(aspect.after(widget, '_onShow', callback));
				}
				node = widget.domNode;
			}
		}
	});
});
