/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console */

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojox/html/entities",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, domClass, entities, _WidgetBase, _TemplatedMixin) {
	return declare("umc.widgets.Text", [_WidgetBase, _TemplatedMixin], {
		// summary:
		//		Simple widget that displays a given label, e.g., some text to
		//		be rendered in a form. Can also render HTML code.

		templateString: '<div dojoAttachPoint="contentNode">${content}</div>',

		labelPosition: 'top',

		// content: String
		//		String which contains the text (or HTML code) to be rendered.
		content: '',

		_tmpContent: null,

		// the widget's class name as CSS class
		baseClass: 'umcText',

		postMixInProperties: function() {
			this.inherited(arguments);
			// We need to temporary unset 'content'. See bug #28810 or #25635
			this._tmpContent = this.content;
			this.content = '';
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.set('content', this._tmpContent);
		},

		_setValueAttr: function(content) {
			this.set('content', entities.encode(content));
		},

		_setContentAttr: function(content) {
			this.contentNode.innerHTML = content;
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
