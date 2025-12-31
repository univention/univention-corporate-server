/*
 * SPDX-FileCopyrightText: 2019-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, lang, domClass, _WidgetBase, _TemplatedMixin) {
	return declare("umc.modules.setup.ChooseRoleBox", [_WidgetBase, _TemplatedMixin], {
		// summary:
		//		Simple widget that displays a link.

		templateString: '<div><div class="umcChooseRoleBox__headline">${headline}<div class="umcChooseRoleBox__tag">${tag}</div></div><div class="umcChooseRoleBox__content">${content}</div></div>',

		// headline: String
		//		String which contains the role text.
		headline: '',

		// tag: String
		//		Small hints regarding this role.
		tag: '',

		// content: String
		//		String which contains the description text.
		content: '',

		// the widget's class name as CSS class
		baseClass: 'umcChooseRoleBox',

		// value: bool
		//		Active?
		value: false,

		// callback: function
		//		What happens if a user actually chooses the role by clicking the box?
		callback: null,

		postCreate: function() {
			this.inherited(arguments);

			this.on('click', lang.hitch(this, function() {
				this.set('value', !this.get('value'));
				if (this.callback) {
					this.callback(this.name);
				};
			}));
		},

		_setValueAttr: function(newVal) {
			domClass.toggle(this.domNode, 'umcChooseRoleBox--selected', newVal);
			this._set('value', newVal);
		}
	});
});
