/*
 * SPDX-FileCopyrightText: 2020-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-construct",
	"dojox/html/entities",
	"dijit/_WidgetBase",
	"dijit/_Container",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/i18n!umc/modules/appcenter",
	"umc/modules/appcenter/SidebarElement"
], function(declare, lang, array, domConstruct, entities, _WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin, _) {
	return declare("umc.modules.appcenter.AppMoreInfo", [_WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppMoreInfo',

		_header: _("More information"),

		templateString: `
			<div>
				<div
					data-dojo-type="umc/modules/appcenter/SidebarElement"
					data-dojo-props="
						header: this._header,
						icon: 'info'
					"
				>
					<table data-dojo-attach-point="containerNode"></table>
				</div>
			</div>
		`,
		addInfo: function(key, value) {
			if (! value) {
				return;
			}
			var tr = domConstruct.create('tr', {}, this.containerNode);
			domConstruct.create('td', {innerHTML: entities.encode(key)}, tr);
			if (typeof value == 'string') {
				domConstruct.create('td', {innerHTML: value}, tr);
			} else {
				// value is a DOM node
				var td = domConstruct.create('td', {}, tr);
				domConstruct.place(value, td, 'only');
			}
		}
	});
});
