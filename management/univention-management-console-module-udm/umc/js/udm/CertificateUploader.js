/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"umc/widgets/Uploader",
	"umc/widgets/Text",
	"umc/i18n!umc/modules/udm"
], function(declare, Uploader, Text, _) {
	return declare("umc.modules.udm.CertificateUploader", [ Uploader ], {
		'class': 'umcInfoUploader',

		maxSize: 512000,

		_text: null,

		constructor: function() {
			this.buttonLabel = _( 'Upload certificate' );
			this.clearButtonLabel = _( 'Remove certificate' );
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			this.sizeClass = null;
		},

		buildRendering: function() {
			this.inherited(arguments);

			// create an text widget
			this._text = new Text({
				label: '',
				content: ''
			});
			this.addChild(this._text, 0);
		},

		updateView: function(value, data) {
			if ( null === data ) {
				this._text.set( 'content', '' );
			} else if ( data.content && data.filename ) {
				this._text.set( 'content', data.filename );
			} else {
				this._text.set( 'content', _( 'Failed to upload certificate' ) );
			}
		}
	});
});


