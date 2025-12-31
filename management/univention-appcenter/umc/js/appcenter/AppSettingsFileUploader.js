/*
 * SPDX-FileCopyrightText: 2017-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojox/html/entities",
	"umc/widgets/Uploader",
	"umc/widgets/Text",
	"umc/tools",
	"umc/i18n!umc/modules/appcenter"
], function(declare, entities, Uploader, Text, tools, _) {
	return declare("umc.modules.appcenter.AppSettingsFileUploader", Uploader, {
		size: 'Two',
		buttonLabel: _('Upload file'),
		clearButtonLabel: _('Delete file'),
		fileName: null,

		buildRendering: function() {
			this.inherited(arguments);

			this._content = new Text({
				content: ''
			});
			this.addChild(this._content, 0);
			this._originalValue = null;
			if (this.data && this.data.content) {
				this._originalValue = this.data.content;
			}
		},

		_getValueAttr: function() {
			return this._uploadedValue;
		},

		validate: function() {
			if (this.required && !this._uploadedValue) {
				return false;
			}
			return true;
		},

		updateView: function(value) {
			var lengthContent = '';
			if (this._originalValue) {
				lengthContent += _('A file is present.') + ' ';
			} else {
				lengthContent += _('No file was uploaded yet.') + ' ';
			}
			if (value) {
				this._uploadedValue = value;
				lengthContent += _('After saving, the new file will be uploaded.');
			} else {
				this._uploadedValue = null;
				if (this._originalValue) {
					lengthContent += _('After saving, the file will be deleted.');
				}
			}
			this._content.set('content', _('File will be uploaded to %s.', '<em>' + entities.encode(this.fileName) + '</em>') + ' ' + lengthContent);
		}
	});
});


