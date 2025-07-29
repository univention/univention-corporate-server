/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/on",
	"umc/widgets/Uploader",
	"umc/widgets/Image",
	"umc/tools",
	"put-selector/put",
	"umc/i18n!"
], function(declare, lang, domClass, on, Uploader, Image, tools, put, _) {
	return declare("umc.widgets.ImageUploader", Uploader, {
		baseClass: 'umcImageUploader',

		// imageType: String
		//		Image type: '*', 'jpeg', 'png', 'svg+xml'
		imageType: '*',

		maxSize: 262400,

		size: 'Two',

		_image: null,

		constructor: function() {
			// this.buttonLabel = _('Upload new image');
			// this.clearButtonLabel = _('Clear image data');
		},

		buildRendering: function() {
			this.inherited(arguments);

			// create an image widget
			this._image = new Image({
				imageType: this.imageType,
				noImageMessage: _('Select file')
			});
			this.addChild(this._image, 0);
		},

		_hideStandby: null,
		_updateLabel: function() {
			this.inherited(arguments);
			this._hideStandby = tools.standby(this._image, {
				opacity: 1
			});
		},

		_resetLabel: function() {
			this.inherited(arguments);
			if (this._hideStandby) {
				this._hideStandby();
				this._hideStandby = null;
			}
		},

		updateView: function(value) {
			this._image.set('value', value);
		},

		getDataUri: function(base64String) {
			return this._image.getDataUri(base64String);
		}
	});
});


