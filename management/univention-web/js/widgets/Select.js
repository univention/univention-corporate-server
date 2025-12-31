/*
 * SPDX-FileCopyrightText: 2020-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dijit/form/Select",
	"./Button",
	"put-selector/put"
], function(declare, domClass, Select, Button, put) {
	return declare("umc.widgets.Select", [ Select ], {
		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcSelect');
			put(this.titleNode, Button.simpleIconButtonNode('chevron-down', 'umcTextBox__downArrowButton'));
		}
	});
});
