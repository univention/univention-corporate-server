/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"umc/widgets/Uploader",
	"umc/widgets/Text",
	"umc/i18n!"
], function(declare, Uploader, Text, _) {
	return declare("umc.widgets.InfoUploader", Uploader, {
		maxSize: 512000,

		_text: null,

		constructor: function() {
			this.buttonLabel = _( 'Upload' );
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			this.sizeClass = null;
		},

		buildRendering: function() {
			this.inherited(arguments);

			// create an image widget
			this._text = new Text({
				label: '',
				content: ''
			});
			this.addChild(this._text, 0);
		},

		updateView: function(value) {
			this._text.set( 'content', value );
		}
	});
});


