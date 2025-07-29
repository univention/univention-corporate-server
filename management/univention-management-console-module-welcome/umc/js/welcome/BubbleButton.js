/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
], function(declare, _WidgetBase, _TemplatedMixin) {
	return declare("umc.modules.welcome.BubbleButton", [_WidgetBase, _TemplatedMixin], {
		baseClass: 'umcBubbleButton',
		clickCallback: null,
		templateString: `
			<div data-dojo-attach-event="click:_onClick">
				<div class="umcBubbleButton__header">
					<h3>\${header}</h3>
				</div>
				<div class="umcBubbleButton__description">
					\${description}
				</div>
			</div>
		`,
		_onClick: function() {
			this.onClick();
		}
	});
});
