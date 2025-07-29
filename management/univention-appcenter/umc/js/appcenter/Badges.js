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
	"umc/modules/appcenter/Badge",
	"umc/i18n!umc/modules/appcenter",
	"umc/modules/appcenter/SidebarElement"
], function(declare, lang, array, domConstruct, entities, _WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin, Badge, _) {
	return declare("umc.modules.appcenter.Badges", [_WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppBadges',
		buttonLabel: _("Manage installations"),

		_header: _('App Center Badges'),

		templateString: `
			<div>
				<div
					data-dojo-type="umc/modules/appcenter/SidebarElement"
					data-dojo-props="
						header: this._header,
						icon: 'bookmark'
					"
				>
					<div data-dojo-attach-point="containerNode"></div>
				</div>
			</div>
		`,

		addBadge: function(name, description) {
			var badge = new Badge({name: name, description: description});
			this.addChild(badge);
		}
	});
});
