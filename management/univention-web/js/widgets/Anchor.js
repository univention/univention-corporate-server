/*
 * SPDX-FileCopyrightText: 2019-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojox/html/entities",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, lang, domClass, entities, _WidgetBase, _TemplatedMixin) {
	return declare("umc.widgets.Anchor", [_WidgetBase, _TemplatedMixin], {
		// summary:
		//		Simple widget that displays a link.

		templateString: '<a href="${href}" title="${title}" dojoAttachPoint="contentNode">${content}</a>',

		labelPosition: 'top',

		// content: String
		//		String which contains the text (or HTML code) to be rendered.
		content: '',

		title: '',
		href: '#',

		// the widget's class name as CSS class
		baseClass: 'umcText',

		postCreate: function() {
			this.inherited(arguments);

			if (typeof this.callback === "function") {
				this.on('click', lang.hitch(this, 'callback'));
			}
		},

		_setContentAttr: function(content) {
			this.contentNode.innerHTML = entities.encode(content);
			this._set('content', content);
		},

		_setVisibleAttr: function(visible) {
			this._set('visible', visible);
			domClass.toggle(this.domNode, 'dijitDisplayNone', !visible);
		},

		isValid: function() {
			// text is always valid
			return true;
		}
	});
});
