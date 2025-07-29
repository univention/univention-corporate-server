/*
 * SPDX-FileCopyrightText: 2020-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/dom-construct",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/i18n!umc/modules/appcenter",
	"umc/modules/appcenter/SidebarElement",
	"umc/widgets/Button"
], function(declare, domConstruct, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, _) {
	return declare("umc.modules.appcenter.Vote", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppVote',

		_header: _("Vote for App"),
		_message: _("We are currently reviewing the admission of this app in the Univention App Center. Vote now and show us how relevant the availability of this app is for you."),
		_buttonLabel: _("Vote now"),

		templateString: `
			<div>
				<div
					data-dojo-type="umc/modules/appcenter/SidebarElement"
					data-dojo-props="
						header: this._header,
						icon: 'check-square'
					"
				>
					<p>
						\${_message}
					</p>
					<div class="umcAppSidebarButton ucsPrimaryButton"
						data-dojo-type="umc/widgets/Button"
						data-dojo-attach-point="buttonNode"
						data-dojo-attach-event="click:_onClick"
						data-dojo-props="
							name: 'vote',
							label: this._buttonLabel
						"
					></div>
				</div>
			</div>
		`,
		hideButton: function() {
			domConstruct.destroy(this.buttonNode.id);
		},
		_onClick: function() {
			this.callback();
		}
	});
});
