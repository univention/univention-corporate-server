/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dijit/_WidgetBase",
	"dijit/_Container",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin"
], function(declare, _WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin) {
	return declare('umc.modules.welcome.Bubble', [
		_WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin
	], {
		//// overwrites
		baseClass: 'umcBubble',
		templateString: `
			<div>
				<div class="umcBubble__header">
					<h2>\${header}</h2>
				</div>
				<div class="umcBubble__content">
					<img class="umcBubble__img \${subClass}" src="\${icon}">
					<div class="umcBubble__description">\${description}</div>
					<div class="umcBubble__buttons" data-dojo-attach-point="containerNode"></div>
				</div>
			</div>
		`
	});
});
