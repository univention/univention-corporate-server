/*
 * SPDX-FileCopyrightText: 2020-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/kernel",
	"dojo/_base/event",
	"dijit/Tooltip",
	"dojo/on",
	"dojox/html/entities",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/widgets/Icon"
], function(declare, kernel, dojoEvent, Tooltip, on, entities, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin) {
	return declare("umc.modules.appcenter.Badge", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppBadge',
		postMixInProperties: function() {
			this.inherited(arguments);
			this.name = entities.encode(this.name);
		},
		templateString: `
			<div class="umcAppRatingHelp umcAppRatingIcon umcAppRating\${name}" data-dojo-attach-event="onmouseenter:_onMouseEnter">
				<svg data-dojo-type="umc/widgets/Icon" data-dojo-props="iconName: 'star'"></svg>
			</div>
		`,
		_onMouseEnter: function(evt) {
			var node = evt.target;
			Tooltip.show(entities.encode(this.description), node);
			if (evt) {
				dojoEvent.stop(evt);
			}
			on.once(kernel.body(), 'click', function(evt) {
				Tooltip.hide(node);
				dojoEvent.stop(evt);
			});
		}
	});
});
