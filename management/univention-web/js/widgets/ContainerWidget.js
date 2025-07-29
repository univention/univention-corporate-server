/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console,require*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_Container"
], function(declare, domClass, _WidgetBase, _Container) {
	return declare("umc.widgets.ContainerWidget", [_WidgetBase, _Container], {
		// description:
		//		Combination of Widget and Container class.
		baseClass: 'umcContainerWidget',

		_setVisibleAttr: function(visible) {
			this._set('visible', visible);
			domClass.toggle(this.domNode, 'dijitDisplayNone', !visible);
		}
	});
});

