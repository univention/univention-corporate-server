/*
 * SPDX-FileCopyrightText: 2012-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/on",
	"umc/widgets/Text",
], function(declare, lang, domClass, on, Text) {
	return declare("umc.modules.udm.NotificationText", [Text], {
		// summary:
		//		This class extends the normal Text widget in order to encapsulate
		//		some UDM specific notification behavior.

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'udmNewObjectDialog__successNotification');
			this.set('visible', false);
			on(this.domNode, 'click', lang.hitch(this, '_hideMessage'));
		},

		showSuccess: function(message) {
			this.set('visible', true);
			this.set('content', message);
		},

		_hideMessage: function(stopDeferred) {
			this.set('visible', false);
		},
	});
});
