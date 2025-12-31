/*
 * SPDX-FileCopyrightText: 2015-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
], function(declare, domClass) {
	return declare("umc.modules.appcenter._AppDialogMixin", null, {
		app: null,
		noFooter: true,
		_initialBootstrapClasses: 'col-xs-12 col-sm-12 col-md-10 col-md-offset-1 col-lg-8 col-lg-offset-2',
		headerTextAllowHTML: false,
		helpTextAllowHTML: false,
		headerTextRegion: 'main',
		helpTextRegion: 'main',

		_clearWidget: function(attr) {
			if (!this[attr]) {
				// nothing to do
				return;
			}
			this[attr].destroyRecursive();
			this[attr] = null;
		},

		onUpdate: function() {
		},

		onShowUp: function() {
		},

		onNext: function() {
		},

		onBack: function() {
		}
	});
});

