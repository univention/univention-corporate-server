/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/dom-construct",
	"dojo/query",
	"dijit/form/NumberSpinner",
	"./_FormWidgetMixin",
	"./Icon",
	"put-selector/put"
], function(declare, domConstruct, query, NumberSpinner, _FormWidgetMixin, Icon, put) {
	return declare("umc.widgets.NumberSpinner", [ NumberSpinner, _FormWidgetMixin ], {
		buildRendering: function() {
			this.inherited(arguments);

			// exchange spinner icon nodes
			domConstruct.empty(this.upArrowNode);
			var upIcon = new Icon({
				iconName: 'chevron-up'
			});
			put(this.upArrowNode, upIcon.domNode);
			domConstruct.empty(this.downArrowNode);
			var downIcon = new Icon({
				iconName: 'chevron-down'
			});
			put(this.downArrowNode, downIcon.domNode);

			// exchange validation icon node
			var icon = new Icon({
				'class': 'umcTextBox__validationIcon',
				iconName: 'alert-circle'
			});
			var validationContainerNode = query('.dijitValidationContainer', this.domNode)[0];
			put(validationContainerNode, '+', icon.domNode);
			put(validationContainerNode, '!');
		}
	});
});
