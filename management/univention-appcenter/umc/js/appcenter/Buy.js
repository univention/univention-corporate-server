/*
 * SPDX-FileCopyrightText: 2020-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/i18n!umc/modules/appcenter",
	"umc/modules/appcenter/SidebarElement",
	"umc/widgets/Button"
], function(declare, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, _) {
	return declare("umc.modules.appcenter.Buy", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppBuy',

		_header: _("Buy in App Center"),
		_butonLabel: _("Buy now"),

		templateString: `
			<div>
				<div
					data-dojo-type="umc/modules/appcenter/SidebarElement"
					data-dojo-props="
						header: this._header,
						icon: 'shopping-cart'
					"
				>
					<div class="umcAppSidebarButton ucsPrimaryButton"
						data-dojo-type="umc/widgets/Button"
						data-dojo-attach-event="click:_onClick"
						data-dojo-props="
							name: 'shop',
							label: this._butonLabel
						"
					></div>
				</div>
			</div>
		`,
		_onClick: function() {
			this.callback();
		}
	});
});
