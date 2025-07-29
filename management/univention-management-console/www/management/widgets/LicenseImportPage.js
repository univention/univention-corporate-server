/*
 * SPDX-FileCopyrightText: 2014-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/*global define*/
define([
	"dojo/_base/lang",
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/Uploader",
	"umc/i18n!management"
], function(lang, Deferred, tools, Text, Uploader, _) {
	var pageConf = {
		name: 'licenseImport',
		headerText: _('License import'),
		'class': 'umcAppDialogPage umcAppDialogPage-licenseImport',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text1',
			content: _('<p><b>You have got mail!</b></p><p>A license file should have been sent to your email address. Upload the license file from the email to activate your UCS instance.</p>')
		}, {
			type : Uploader,
			name : 'licenseUpload',
			buttonLabel: _('Upload license file...'),
			command: 'udm/license/import',
			_progressDeferred: null,
			onUploadStarted: function() {
				this._progressDeferred = new Deferred();
				this._progressDeferred.progress(_('Importing license data...'));
				this.onImportLicense(this._progressDeferred);
			},
			onUploaded: function(result) {
				if (result.success) {
					this._progressDeferred.progress(_('Updating session data...'));
					tools.renewSession().then(lang.hitch(this, function() {
						this._progressDeferred.resolve();
						//dialog.alert(_('The license has been imported successfully.'));
					}));
				}
				else {
					this._progressDeferred.reject(result.message);
				}
			},
			onImportLicense: function(deferred) {
				// event stub
			}
		}, {
			type: Text,
			name: 'text2',
			content: '<p>' + _('You may as well import the license file at a later point in time via the user menu in the top right.') + '</p>'
		}],

		// the following values will be loaded via UCR
		hasLicense: null,
		hasLicenseRequested: null
	};

	var _ucrDeferred = null;
	var ucr = function() {
		if (!_ucrDeferred) {
			_ucrDeferred = tools.ucr(['uuid/license', 'ucs/web/license/requested']).then(function(ucr) {
				return {
					hasLicense: Boolean(ucr['uuid/license']),
					hasLicenseRequested: tools.isTrue(ucr['ucs/web/license/requested'])
				};
			});
		}
		return _ucrDeferred;
	};

	// return an AMD plugin that resolves when the UCR variables have been loaded
	return {
		load: function (params, req, load, config) {
			ucr().then(function(info) {
				load(lang.mixin(pageConf, info));
			});
		}
	};
});
